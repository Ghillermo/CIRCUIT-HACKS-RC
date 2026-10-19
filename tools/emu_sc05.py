"""Emulation tests for SC05 internal loopback + recorder gating (live RAM dump)."""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
from unicorn import *
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
FL = (ROOT / "ctre/Firmware-Analysis/dumpCT_flash_0x08000000.bin").read_bytes()
RA = (ROOT / "ctre/Firmware-Analysis/ram_dump_firmware_0x08037988.bin").read_bytes()
TX = 0x20011334          # tx interface (vtable 0x08059FC4)
CTX = 0x20044CB8         # receiver A
REC_STORE = 0x20011034   # transport store read by recorder gates
STOP = 0x0807FFF0          # erased flash past the image (SC44.5 reaches 0x0807FFC4; was 0x0807FF00), inside the mod zone (rodisk / lazysave LR checks)


class E:
    def __init__(self, image):
        uc = self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
        fl = bytearray(FL); fl[0x10000:0x10000 + len(image)] = image
        uc.mem_map(0x08000000, 0x80000); uc.mem_write(0x08000000, bytes(fl))
        uc.mem_map(0x20000000, 0x50000); uc.mem_write(0x20000000, RA.ljust(0x50000, b"\0"))
        uc.mem_map(0x20060000, 0x10000); uc.mem_map(0x40000000, 0x20000000); uc.mem_map(0xE0000000, 0x100000)
        uc.mem_map(0x60000000, 0x10000000); uc.mem_map(0xC0000000, 0x4000000); uc.mem_map(0x0, 0x100000)
        self.ev = []
        self.stubs = {0x08031DA4: "sound", 0x08021064: "dsp", 0x0803FC20: "rec_param"}
        self.marks = {0x0802E5BC: ("rec_note_on", 0x0802E5CA), 0x0802E61C: ("rec_note_off", 0x0802E628)}
        uc.hook_add(UC_HOOK_CODE, self._code)

    def _code(self, uc, a, s, d):
        if a == STOP:
            uc.emu_stop(); return
        if a == 0x0803BEDA:
            r1 = uc.reg_read(UC_ARM_REG_R1)
            self.ev.append(("ext", bytes(uc.mem_read(r1, 3)).hex()))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1); return
        if a in self.stubs:
            self.ev.append((self.stubs[a],))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1); return
        if a in self.marks:
            name, out = self.marks[a]
            self.ev.append((name,)); uc.reg_write(UC_ARM_REG_PC, out | 1); return

    def w32(self, a, v): self.uc.mem_write(a, struct.pack("<I", v))
    def r32(self, a): return struct.unpack("<I", self.uc.mem_read(a, 4))[0]
    def r8(self, a): return self.uc.mem_read(a, 1)[0]

    def recording(self, on=True):
        for buf in (self.r32(REC_STORE + 0xC), self.r32(REC_STORE + 0x10)):
            self.w32(buf + 0, 1 if on else 0); self.w32(buf + 4, 1 if on else 0); self.w32(buf + 8, 0)

    def set_tx_chan(self, track, ch):
        tbl = self.r32(TX + 0xC); self.uc.mem_write(tbl + track, bytes([ch]))

    def call(self, fn, *args, maxins=3_000_000):
        uc = self.uc
        uc.reg_write(UC_ARM_REG_SP, 0x2006F000)
        for i, v in enumerate(args):
            uc.reg_write(UC_ARM_REG_R0 + i, v)
        uc.reg_write(UC_ARM_REG_LR, STOP | 1)
        uc.emu_start(fn | 1, 0xFFFFFFFF, count=maxins)
        return [e for e in self.ev]


def names(ev): return [e[0] for e in ev]


def main(stock, sc05, labels):
    fails = 0
    def check(c, m):
        nonlocal fails
        if not c: fails += 1; print("FAIL:", m)
        else: print("ok  :", m)

    # 1) stock: external note on ch1 while recording -> sound + recorded
    e = E(stock); e.recording(True)
    m = 0x20060100; e.uc.mem_write(m, bytes([0x90, 60, 100, 0]))
    ev = names(e.call(0x08051720, CTX, m))
    check("sound" in ev and "rec_note_on" in ev, f"stock external note on ch1 while recording -> sound+record {ev}")

    # 2) SC05 MIDI1 shares ch1 with Synth1: note on via vtable wrapper
    def note(image, track, ch, on=True, rec=True):
        e = E(image); e.recording(rec); e.set_tx_chan(track, ch) if track in (2, 3) else None
        fn = labels["c_non"] if on else labels["c_noff"]
        flags_before = e.r8(CTX + 0x14)
        ev = e.call(fn, TX, track, 60, 100 if on else 0)
        return ev, flags_before, e.r8(CTX + 0x14)
    ev, fb, fa = note(sc05, 2, 0)
    n = names(ev)
    check(("ext", "903c64") in ev and "sound" in n and "rec_note_on" not in n,
          f"MIDI1 on ch1: external send + Synth1 sounds + NOT recorded {ev}")
    check(fb == fa, f"internal bit restored (flags {fb:#x} -> {fa:#x})")
    ev, _, _ = note(sc05, 2, 0, on=False)
    n = names(ev)
    check(("ext", "803c00") in ev and "rec_note_off" not in n, f"MIDI1 note off on ch1: external + not recorded {ev}")
    # 3) MIDI2 on Synth2 channel
    ev, _, _ = note(sc05, 3, 1); n = names(ev)
    check(("ext", "913c64") in ev and "sound" in n and "rec_note_on" not in n, f"MIDI2 on ch2 (Synth2): {ev}")
    # 4) not shared -> no injection
    ev, _, _ = note(sc05, 2, 2); n = names(ev)
    check(n == ["ext"], f"MIDI1 on its own ch3: only external {ev}")
    # 5) drums channel -> no note injection (feedback guard)
    ev, _, _ = note(sc05, 2, 9); n = names(ev)
    check(n == ["ext"], f"MIDI1 on drums ch10: no note injection {ev}")
    # 6) synth's own echo (track 0) -> no injection
    ev, _, _ = note(sc05, 0, 0); n = names(ev)
    check(n == ["ext"], f"Synth1 echo (track 0): only external {ev}")
    # 7) stock vtable behaviour unchanged for track 2 not shared, compare with stock function
    e = E(stock); e.set_tx_chan(2, 2); evs = e.call(0x08029EFE, TX, 2, 60, 100)
    check(evs == [("ext", "923c64")], f"stock note on MIDI1 ch3: {evs}")

    # 8) template CC helper: MIDI track CC on Synth1 CC-rx ch (0) while recording
    def cc(image, ch, ccn=74, val=10, rec=True, fn=None):
        e = E(image); e.recording(rec)
        ev = e.call(fn or labels["c_cc"], ch, 0xB0, ccn, val)
        return ev, e.r8(CTX + 0x14)
    ev, fa = cc(sc05, 0); n = names(ev)
    check(("ext", "b04a0a") in ev and "rec_param" not in n and fa == RA[CTX + 0x14 - 0x20000000],
          f"template CC74 ch1: external + internal, not recorded {ev}")
    # external CC on ch1 while recording in stock: does it record? (reference)
    e = E(stock); e.recording(True); e.uc.mem_write(m, bytes([0xB0, 74, 10, 0]))
    ref = names(e.call(0x08051720, CTX, m))
    print("     reference: stock external CC74 ch1 while recording ->", ref)
    # internal delivery actually reaches the param handler: trace that 0x08052854 is hit
    e = E(sc05); e.recording(True)
    hit = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: hit.append(a) if a == 0x08052854 else None)
    e.call(labels["c_cc"], 0, 0xB0, 74, 10)
    check(len(hit) == 1, f"template CC reaches the CC/param handler internally ({len(hit)})")
    ev, _ = cc(sc05, 5); n = names(ev)
    check(n == ["ext"], f"template CC on unshared ch6: only external {ev}")
    ev, _ = cc(stock, 0, fn=0x0804A356)
    check(names(ev) == ["ext"], f"stock helper: only external {ev}")

    # 9) gates directly: with internal bit set -> no record; clear -> record
    for flag, exp in ((0x2F, False), (0x0F, True)):
        e = E(sc05); e.recording(True); e.uc.mem_write(CTX + 0x14, bytes([flag]))
        rec_obj = 0x2003C168
        ev = names(e.call(0x0802E56A, rec_obj, 60, 100, 0))
        check(("rec_note_on" in ev) == exp, f"gate note-on internal={flag & 0x20 != 0}: {ev}")

    # 10) injected note-off really reaches the note-off handler
    e = E(sc05); e.recording(True); e.set_tx_chan(2, 0); hits = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: hits.append(a) if a == 0x08034D56 else None)
    e.call(labels["c_noff"], TX, 2, 60, 0)
    check(hits == [0x08034D56], "injected note-off reaches Synth note-off handler")
    # 11) macro CCs: stock records external ones; SC05 internal ones apply but are not recorded
    for ccn in (80, 81, 85):
        e = E(stock); e.recording(True); e.uc.mem_write(m, bytes([0xB0, ccn, 90, 0]))
        st = names(e.call(0x08051720, CTX, m))
        ev, _ = cc(sc05, 0, ccn, 90); n = names(ev)
        check("rec_param" in st and "dsp" in st and "rec_param" not in n and "dsp" in n,
              f"macro CC{ccn}: stock ext {st} | SC05 internal {n}")
    print("SC05 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    man = json.loads(Path(sys.argv[3]).read_text())
    labels = {k: int(v, 16) for k, v in man["report"]["sc05"]["labels"].items()}
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes(), labels) else 0)
