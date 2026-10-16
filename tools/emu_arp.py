"""SC41.9 ARM tests: the arpeggiator (arp.py), through the controller, the players' own per-tick calls and the real LED task call.

    python tools/emu_arp.py NEW.bin NEW_manifest.json
  * Pattern Settings of Synth 1: Shift + pad 25 = the arpeggiator of the pattern it plays on / off; Shift + pads 27-32 = its order; with Shift pad 25
    yellow / green and the order's pad green, the others yellow; without Shift pad 25 green while on; without Shift pad 25 still opens mode 2;
  * the sequence: a chord of 3 notes (unsorted, 3 steps long) played by Synth 1's player tick by tick (0x0804A684 / 0x0804A714, sync rate 1/16):
    off = the stock's three note-ons at once; up / down / ping-pong (4 notes, 6 steps) / fractal / deconstructed = one note a step, a step long,
    with its own velocity, at the chord's micro step; the chord's other units never start;
  * the input (Synth 1's track view, pads through the controller): one note = as always; a second one = no note-on of its own, the recorder's gate
    called (the chord), and, stopped, from the LED task one note every 125 ms at 120 BPM (the first note stopped, each note stopped before the next)
    through the player's note interface; letting go of all: the last note off; playing: the player's micro step 0 plays the next note (stock note-on);
  * the stock's apply puts the running states to 0; a block without its signature = every arpeggiator off.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import MGR  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
from emu_sc08 import CONT  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import emu_sc40_8 as T8  # noqa: E402
import arp as A  # noqa: E402
import mutate39 as MU  # noqa: E402

PLAYER, VIEW, VIEW_IFC = 0x20040200, 0x200412E0, 0x200413F0
IFC_ON, IFC_OFF = 0x0801D38E, 0x0801D942
TICK_BUILD, TICK_PLAY = 0x0804A684, 0x0804A714


class EA(T8.E8):
    def __init__(self, img, man):
        super().__init__(img, man, {k: int(v, 16) for k, v in man["report"]["patchain"]["labels"].items()})
        self.A = {k: int(v, 16) for k, v in man["report"]["arp"]["labels"].items()}
        self.ons, self.ifc, self.rec_on = [], [], []
        def skip(uc, a, s, d): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        # the note-on, the note interface and the recorder's gate are logged and skipped (in emulation the sound path waits for the DSP)
        def non(uc, a, s, d):
            self.ons.append((self.r32(TICK_HOLD), uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3))); skip(uc, a, s, d)
        def ifc(uc, a, s, d): self.ifc.append(("on" if a == IFC_ON else "off", uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1))); skip(uc, a, s, d)
        def rec(uc, a, s, d): self.rec_on.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R3))); skip(uc, a, s, d)
        self.uc.hook_add(UC_HOOK_CODE, non, begin=A.NOTE_ON, end=A.NOTE_ON)
        for f in (IFC_ON, IFC_OFF): self.uc.hook_add(UC_HOOK_CODE, ifc, begin=f, end=f)
        self.uc.hook_add(UC_HOOK_CODE, rec, begin=A.REC_ON, end=A.REC_ON)
        for f in (0x0801BE78, 0x08029A00): self.uc.hook_add(UC_HOOK_CODE, skip, begin=f, end=f)
        self.w32(TICK_HOLD, 0)

    def setp(self, store, k, data):
        for f in (0x080354FA, 0x0803542C):
            self.call(f, store, k); self.uc.mem_write(self.uc.reg_read(UC_ARM_REG_R0), data)
    def cfg(self, t, p):
        self.call(self.A["c_arcfg"], t, p); return self.uc.reg_read(UC_ARM_REG_R0)
    def press(self, i): self.call(0x08033320, MGR, i, maxins=8_000_000)
    def release(self, i): self.call(0x0803381A, MGR, i, maxins=8_000_000)
    def pad(self, q, shift=False, up=True):
        if shift: self.set_p0(self.r32(MGR + 0xC), 1)
        self.call(PRESS, MGR, q, 100, maxins=8_000_000)
        if up: self.call(RELEASE, MGR, q, maxins=8_000_000)
        if shift: self.set_p0(self.r32(MGR + 0xC), 0)
    def unpad(self, q): self.call(RELEASE, MGR, q, maxins=8_000_000)
    def pads(self, shift=False):
        if shift: self.set_p0(self.r32(MGR + 0xC), 1)
        self.call(0x08034196, MGR, 0x2006E000, maxins=8_000_000)
        if shift: self.set_p0(self.r32(MGR + 0xC), 0)
        return list(struct.unpack("<32H", bytes(self.uc.mem_read(0x2006E000, 64))))
    def ledtask(self):
        self.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); self.uc.reg_write(UC_ARM_REG_R4, MGR)
        self.call(0x08033B3E, maxins=30_000_000)
    def transport(self, on): self.setp(A.TRANSPORT, 0, bytes([on]))
    def run(self, pat, steps, tps=6):
        """Synth 1's player through the stock's per-tick calls: the pattern from step 0, steps x tps ticks"""
        st = self.r32(A.ENG + 0x30)
        self.setp(st, 0, bytes([pat]))
        for s in range(steps):
            self.setp(st, 1, bytes([s]))
            for t in range(tps):
                self.setp(st, 2, struct.pack("<I", t)); self.w32(TICK_HOLD, s * tps + t)
                self.call(TICK_BUILD, PLAYER, maxins=3_000_000); self.call(TICK_PLAY, PLAYER, maxins=3_000_000)
TICK_HOLD = 0x2006E800                     # (scratch) the tick the test is at, for the log


def chord_steps(units, n=8):
    """step 0 = the units (note, length, micro step, velocity), probability 7; the other steps empty"""
    out = bytearray()
    for s in range(n):
        us = units if s == 0 else []
        mask = sum(1 << i for i in range(len(us)))
        out += bytes([mask, 7, 0, 0]) + b"".join(bytes(u) for u in us) + bytes([0, 0, 0, 0x60]) * (6 - len(us))
    return bytes(out)


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = EA(img, man)
    T = 0
    e.set_p0(e.r32(CONT + 0x188), T); e.press(T); e.release(T); e.press(12); e.release(12)
    pat = e.playing(T)
    check(e.cfg(T, pat) == 0, "a project without the block: the arpeggiator off")
    f0 = e.pads(shift=True)
    e.pad(A.PS_PAD_ARP, shift=True); on = e.cfg(T, pat); f1 = e.pads(shift=True); f1n = e.pads()
    Y, G = A.COL_AV, A.COL_ON
    check(on == 0x80 and e.r8(MGR + 0x152) == 4, f"Shift + pad 25: on (setting {on:#x}), the view stays")
    check(f0[24] == Y and f0[26:32] == [Y, Y, G, Y, Y, Y], f"with Shift, off: pad 25 yellow, up (pad 29) green, the others yellow ({[hex(x) for x in f0[24:]]})")
    check(f1[24] == G and f1n[24] == G, f"on: pad 25 green with and without Shift ({f1[24]:#x}, {f1n[24]:#x})")
    seen = []
    for q, m in zip(range(26, 32), A.ORD_OF_PAD):
        e.pad(q, shift=True); c = e.cfg(T, pat); seen.append((c, e.pads(shift=True)[q]))
    check(seen == [(0x80 | m, G) for m in A.ORD_OF_PAD], f"Shift + pads 27-32: the order (fractal, deconstructed, up, down, ping-pong, random), its pad green ({seen})")
    e.pad(A.PS_PAD_ARP, shift=True); off = e.cfg(T, pat)
    check(off == A.M_RND, f"Shift + pad 25 again: off, the order kept ({off:#x})")
    e.pad(A.PS_PAD_ARP)
    check(e.r8(MGR + 0x152) == 5 and e.cfg(T, pat) == A.M_RND, "pad 25 without Shift: mode 2 as before, the setting untouched")
    e.press(12); e.release(12)
    del e; gc.collect()

    # ---- the sequence
    chord = [(64, 18, 0, 100), (60, 18, 0, 90), (67, 12, 0, 80)]
    def seq(setting, units=chord, steps=5):
        e = EA(img, man)
        p = e.playing(0); base = e.settings(0, p) - 0x380
        e.uc.mem_write(base, chord_steps(units)); e.setpat(0, p, 0, 7)
        e.setp(e.r32(PLAYER + 0x10), 1, bytes([3]))
        if setting is not None: e.call(e.A["c_arset"], 0, p, setting)
        e.transport(1); e.ons.clear(); e.run(p, steps)
        out = [(t, n, v, d) for t, n, v, d in e.ons]; del e; gc.collect(); return out
    s_off = seq(None)
    check(sorted(s_off) == [(0, 60, 90, 18), (0, 64, 100, 18), (0, 67, 80, 12)], f"off: the stock's three note-ons at once ({s_off})")
    s_up = seq(0x80 | A.M_UP)
    check(s_up == [(0, 60, 90, 6), (6, 64, 100, 6), (12, 67, 80, 6)], f"up: one note a step, a step long, its velocity; nothing after the chord ({s_up})")
    s_dn = seq(0x80 | A.M_DOWN)
    check([n for _, n, _, _ in s_dn] == [67, 64, 60], f"down ({s_dn})")
    four = [(64, 36, 0, 100), (60, 36, 0, 90), (67, 36, 0, 80), (72, 30, 0, 70)]
    s_pp = seq(0x80 | A.M_PP, four, 7)
    check([n for _, n, _, _ in s_pp] == [60, 64, 67, 72, 67, 64] and [t for t, *_ in s_pp] == [0, 6, 12, 18, 24, 30], f"ping-pong, 4 notes, 6 steps ({s_pp})")
    s_fr = seq(0x80 | A.M_FRAC, four, 7)
    check([n for _, n, _, _ in s_fr] == [60, 60, 64, 60, 64, 67], f"fractal ({s_fr})")
    s_de = seq(0x80 | A.M_DEC, four, 7)
    check([n for _, n, _, _ in s_de] == [60, 67, 64, 72, 60, 67], f"deconstructed: even places, then odd ({s_de})")
    late = [(64, 12, 2, 100), (60, 12, 2, 90)]
    s_late = seq(0x80 | A.M_UP, late, 3)
    check(s_late == [(2, 60, 90, 6), (8, 64, 100, 6)], f"a chord at micro step 2: its notes at micro step 2 of each step ({s_late})")
    s_one = seq(0x80, [(64, 12, 0, 100)], 3)
    check(s_one == [(0, 64, 100, 12)], f"one note: the stock's ({s_one})")

    # ---- the input
    e = EA(img, man)
    p = e.playing(0); e.call(e.A["c_arset"], 0, p, 0x80 | A.M_UP)
    e.set_p0(e.r32(CONT + 0x188), 0); e.press(0); e.release(0); e.press(9); e.release(9)          # Synth 1, Note: its track view
    e.transport(0); e.w32(A.HAL_TICK, 100000); e.ifc.clear(); e.rec_on.clear()
    e.pad(20, up=False)
    first = [x for x in e.ifc if x[0] == "on"]
    check(len(first) == 1 and first[0][1] == VIEW_IFC, f"one pad: its note-on as always ({e.ifc})")
    na = first[0][2]; e.ifc.clear(); n_rec = len(e.rec_on)
    e.pad(17, up=False)
    check(not any(x[0] == "on" for x in e.ifc) and len(e.rec_on) == n_rec + 1, f"a second pad: no note-on of its own, the recorder gets it ({e.ifc}, {e.rec_on})")
    nb = e.rec_on[-1][0]; lo, hi = min(na, nb), max(na, nb)
    pifc = e.r32(PLAYER + 0x4C)
    e.ifc.clear(); e.ledtask(); s0 = list(e.ifc)
    e.ifc.clear(); e.w32(A.HAL_TICK, 100124); e.ledtask(); s1 = list(e.ifc)
    e.w32(A.HAL_TICK, 100125); e.ledtask(); s2 = list(e.ifc)
    check(s0 == [("off", pifc, na), ("on", pifc, lo)], f"stopped, the LED task: the first note off, the lowest on ({s0})")
    check(s1 == [] and s2 == [("off", pifc, lo), ("on", pifc, hi)], f"125 ms later (120 BPM, 1/16): the next one ({s1}, {s2})")
    e.ifc.clear(); e.unpad(17); e.unpad(20)
    check(("off", pifc, hi) in e.ifc, f"both let go: the last note off ({e.ifc})")
    e.ifc.clear(); e.w32(A.HAL_TICK, 101000); e.ledtask()
    check(e.ifc == [], "then nothing more")
    # playing: the player's micro step 0
    e.pad(20, up=False); e.pad(17, up=False); e.transport(1); e.ons.clear(); e.ifc.clear()
    e.ledtask()
    st = e.r32(A.ENG + 0x30); e.setp(st, 0, bytes([p])); e.setp(st, 1, bytes([3])); e.setp(st, 2, struct.pack("<I", 0))
    e.call(TICK_BUILD, PLAYER, maxins=3_000_000); e.call(TICK_PLAY, PLAYER, maxins=3_000_000)
    check([x[1] for x in e.ons] == [lo] and e.ons[0][3] == 6 and ("off", pifc, na) in e.ifc, f"playing: micro step 0 plays the next note, a step long ({e.ons}, {e.ifc})")
    e.unpad(17); e.unpad(20)
    # the stock's apply
    e.uc.mem_write(e.tail + A.O_SEQ, bytes([3, 4, 18, 1, 0, 0]) + bytes(range(60, 66)) + bytes([100] * 6) + bytes([0, 1]))
    e.call(0x0802EEFE, A.SESSION_OBJ, 1, maxins=30_000_000)
    z = bytes(e.uc.mem_read(e.tail + A.O_SEQ, A.O_END - A.O_SEQ))
    check(z == bytes(len(z)) and e.cfg(0, p) == 0x80 | A.M_UP, "the stock's apply: the running states to 0, the setting kept")
    e.uc.mem_write(e.tail + A.O_BLK, b"ARPX")
    check(e.cfg(0, p) == 0, "a block without its signature: off")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
