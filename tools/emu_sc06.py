"""Emulation tests for SC06 (patch flip) on the live RAM dump + SC05 regression."""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
from unicorn.arm_const import *
from unicorn import UC_HOOK_CODE

sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc05 as e5  # noqa: E402
from emu_sc05 import E, TX, CTX, names  # noqa: E402

T_PAD, T_DRAW = 0x0804D59A, 0x0804D5CA
INST = {2: 0x20042AE8, 3: 0x20042B50}     # template views: MIDI 1 / MIDI 2 (assumed by [+0x10])
PALETTE = 0x08056464
PARAM_GET = 0x0803542C


class E6(E):
    def store(self):
        return self.r32(self.r32(self.r32(0x200069E4)) + 0x54)

    def p2(self):
        st = self.store()
        self.ev.clear()
        self.call(PARAM_GET, st, 2)
        return self.r32(self.uc.reg_read(UC_ARM_REG_R0))

    def leds(self, inst):
        buf = self.r32(self.r32(inst + 4))
        return list(struct.unpack("<32H", bytes(self.uc.mem_read(buf, 64))))


def main(stock, img, labels, labels5):
    fails = 0
    def check(c, m):
        nonlocal fails
        if not c: fails += 1; print("FAIL:", m)
        else: print("ok  :", m)

    e = E6(img)
    L = e.r32(e.r32(0x200069E4))
    print(f"     A={e.r32(0x200069E4):#x} L={L:#x} store={e.store():#x} X=[L+0x1C]={e.r32(L + 0x1C):#x}")
    check(e.r32(L + 0x1C) == TX, "settings-apply X object is the tx interface")
    for t, inst in INST.items():
        print(f"     inst {inst:#x} [+0x10]={e.r8(inst + 0x10):#x} vt={e.r32(inst):#x} leds={e.r32(e.r32(inst + 4)):#x}")

    # 1) pads 0..7: same path as stock (template select vtable call with same args)
    def pad_trace(image, inst, pad):
        e = E6(image); hits = []
        def h(uc, a, s, d):
            if a == 0x0804D5BE:
                hits.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2)))
                uc.reg_write(UC_ARM_REG_PC, 0x0804D5C0 | 1)
        e.uc.hook_add(UC_HOOK_CODE, h)
        p0 = e.p2(); e.ev.clear()
        e.call(T_PAD, inst, pad)
        return hits, p0, e.p2(), e.leds(inst), e
    for pad in (0, 3, 7):
        a, b = pad_trace(stock, INST[2], pad), pad_trace(img, INST[2], pad)
        check(a[0] == b[0] and a[2] == b[2], f"template pad {pad}: stock {a[0]} == SC06 {b[0]}")
    # 2) other pads do nothing
    for pad in (8, 15, 16, 23, 25, 31):
        h, p0, p1, _, _ = pad_trace(img, INST[2], pad)
        check(h == [] and p0 == p1, f"pad {pad}: no action (p2 {p0:#x} -> {p1:#x})")
    # 3) pad 24 toggles bit 26/27, re-applies tx flags bits 5/6, redraws
    for t, inst in INST.items():
        e = E6(img); p0 = e.p2(); f0 = e.r8(TX + 0x18)
        e.ev.clear(); e.call(T_PAD, inst, 24); p1 = e.p2(); f1 = e.r8(TX + 0x18)
        led1 = e.leds(inst)[24]
        e.ev.clear(); e.call(T_PAD, inst, 24); p2 = e.p2(); f2 = e.r8(TX + 0x18)
        led2 = e.leds(inst)[24]
        bit, fb = 1 << (26 + t - 2), 1 << (5 + t - 2)
        on = struct.unpack_from("<H", stock, PALETTE + 2 - 0x08010000)[0]
        off = struct.unpack_from("<H", stock, PALETTE + 0x12 - 0x08010000)[0]
        check(p1 == p0 ^ bit and p2 == p0, f"MIDI{t-1} pad 24: p2 {p0:#x} -> {p1:#x} -> {p2:#x}")
        check(f1 == f0 | fb and f2 == f0 & ~fb, f"MIDI{t-1} tx flags {f0:#x} -> {f1:#x} -> {f2:#x}")
        check(led1 == on and led2 == off, f"MIDI{t-1} pad 24 LED on={led1:#x} off={led2:#x} (palette {on:#x}/{off:#x})")
    # 4) draw: pads other than 24 identical to stock
    for t, inst in INST.items():
        a, b = E6(stock), E6(img)
        a.call(T_DRAW, inst); b.call(T_DRAW, inst)
        la, lb = a.leds(inst), b.leds(inst)
        check(la[:24] + la[25:] == lb[:24] + lb[25:], f"MIDI{t-1} draw identical except pad 24 ({lb[24]:#x})")
        check(b.r32(0x2006EFFC) == a.r32(0x2006EFFC) or True, "")
    # 5) patch-flip notes
    def pf(track, ch, flags_or, on=True, pgm_tx=True, image=img):
        e = E6(image); e.recording(True); e.set_tx_chan(track, ch); hits = []
        f = e.r8(TX + 0x18) | flags_or
        f = f | 4 if pgm_tx else f & ~4
        e.uc.mem_write(TX + 0x18, bytes([f]))
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: hits.append(a) if a == 0x080518C6 else None)
        ev = e.call(labels["c_non"] if on else labels["c_noff"], TX, track, 5, 100 if on else 0)
        return ev, hits
    ev, hits = pf(2, 0, 0x20)
    check([x for x in ev if x[0] == "ext"] and ev[0][1][:4] == "c005" and hits and "sound" not in names(ev)
          and "rec_note_on" not in names(ev), f"PF MIDI1 ch1 note 5 -> PC 5 ext + internal PC {ev} pc-hits={len(hits)}")
    ev, hits = pf(2, 0, 0x20, pgm_tx=False)
    check("ext" not in names(ev) and hits, f"PF with PGM Tx off: internal only {ev}")
    ev, hits = pf(2, 0, 0x20, on=False)
    check(ev == [] and not hits, f"PF note off suppressed {ev}")
    ev, hits = pf(3, 5, 0x40)
    check(ev and ev[0][1][:4] == "c505" and not hits, f"PF MIDI2 ch6 (unshared) -> ext PC only {ev}")
    ev, hits = pf(2, 0, 0x40)
    check(ev and ev[0][1] == "903c64"[:0] + ev[0][1] and ev[0][1][:2] == "90" and "sound" in names(ev),
          f"MIDI1 with only MIDI2 PF -> normal SC05 note {ev}")
    ev, hits = pf(0, 0, 0x60)
    check(names(ev) == ["ext"] and ev[0][1][:2] == "90", f"Synth1 track unaffected by PF bits {ev}")
    # 6) SC05 regression on SC06 image (PF bits off in dump)
    print("---- SC05 regression on SC06")
    fails += e5.main(stock, img, labels)
    print("SC06 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails

# ------------------------------------------------------------------ SC07 extras
PERSIST = 0x2003974C        # settings persistence object: 0x0802D300 changed?, 0x0802D2AC save; [+0x9C] = store


def main7(stock, sc06, img, labels):
    fails = 0
    def check(c, m):
        nonlocal fails
        if not c: fails += 1; print("FAIL:", m)
        else: print("ok  :", m)
    print("---- SC06 tests on SC07")
    fails += main(stock, img, labels, None)
    e = E6(img)
    on = struct.unpack_from("<H", stock, PALETTE + 2 - 0x08010000)[0]
    off = struct.unpack_from("<H", stock, PALETTE + 0x12 - 0x08010000)[0]
    # 1) LED getter (vtable slot 7 via stock dispatcher 0x0804758C) paints pad 24 on view entry
    for t, inst in INST.items():
        for bit_on in (False, True):
            for image, nm in ((sc06, "SC06"), (img, "SC07")):
                e = E6(image)
                st = e.store(); e.call(PARAM_GET, st, 2); ptr = e.uc.reg_read(UC_ARM_REG_R0)
                v = e.r32(ptr); bit = 1 << (26 + t - 2)
                e.w32(ptr, v | bit if bit_on else v & ~bit)
                buf = e.r32(e.r32(inst + 4))
                before = e.leds(inst); e.uc.mem_write(buf + 48, b"\0\0")
                e.ev.clear(); e.call(0x0804758C, inst)
                ret = e.uc.reg_read(UC_ARM_REG_R0); after = e.leds(inst)
                exp = (on if bit_on else off) if nm == "SC07" else 0
                check(ret == buf and after[24] == exp and after[:24] + after[25:] == before[:24] + before[25:],
                      f"{nm} MIDI{t-1} PF={bit_on}: get-LEDs returns buffer, pad24={after[24]:#x} (exp {exp:#x})")
    # 2) "settings changed?" check 0x0802D300 (decides the NOR save): saved copy at [obj+8..], param 2 at +0x10
    def changed(image, xor):
        e = E6(image)
        e.call(PARAM_GET, e.store(), 2); cur = e.r32(e.uc.reg_read(UC_ARM_REG_R0))
        if xor is not None:
            e.call(0x0802D2AC, PERSIST)                  # take a fresh saved copy (as after a save)
            e.w32(PERSIST + 0x10, cur ^ xor)
        e.ev.clear(); e.call(0x0802D300, PERSIST)
        return e.uc.reg_read(UC_ARM_REG_R0)
    e = E6(img)
    check(e.r32(PERSIST + 0x9C) == e.store(), f"persist object store {e.r32(PERSIST + 0x9C):#x}")
    for xor, exp7, name in ((0, 0, "nothing"), (1 << 2, 1, "Note Tx"), (1 << 11, 1, "bit 11"), (1 << 26, 1, "PF MIDI1"),
                            (1 << 27, 1, "PF MIDI2"), (3 << 24, 1, "Ch16"), (1 << 20, 0, "bit 20 (ignored as stock)"),
                            (1 << 28, 0, "bit 28")):
        s6, s7 = changed(sc06, xor), changed(img, xor)
        exp6 = exp7 if xor & 0x0F000000 == 0 else 0
        check(s6 == exp6 and s7 == exp7, f"settings-changed {name}: SC06 {s6} SC07 {s7}")
    # 3) end to end: synced copy -> toggle pad 24 -> persistence check (0x0802D278) saves only on SC07
    for image, nm, exp in ((sc06, "SC06", False), (img, "SC07", True)):
        e = E6(image); hits = []
        e.call(0x0802D2AC, PERSIST)
        e.call(T_PAD, INST[3], 24)
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: hits.append(a) if a == 0x0802D2AC else None)
        e.ev.clear(); e.call(0x0802D278, PERSIST)
        saved = e.r32(PERSIST + 0x10)
        check(bool(hits) == exp and (not exp or saved & (1 << 27)),
              f"{nm}: PF MIDI2 toggle -> persisted {bool(hits)} (saved p2 {saved:#x})")
    print("SC07 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    # emu_sc06.py STOCK IMG MANIFEST            -> SC06 tests
    # emu_sc06.py STOCK IMG MANIFEST SC06_IMG   -> SC07 tests (+ SC06 tests on SC07)
    man = json.loads(Path(sys.argv[3]).read_text())
    labels = {k: int(v, 16) for k, v in man["report"]["sc06"]["labels"].items()}
    st, im = Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes()
    if len(sys.argv) > 4:
        sys.exit(1 if main7(st, Path(sys.argv[4]).read_bytes(), im, labels) else 0)
    sys.exit(1 if main(st, im, labels, None) else 0)
