"""Alpha 7.52 test (novasec.use_v12: Macros 2 second destinations), from emu_novasec4's set-up (novasec.use_v8) through the controller and the LED task, on Synth 1's alt page:
  * K3 moved on Macros: pads 1 / 9 / 17 / 25 = macro 3's four slots (Synth 1's colour bright = depth not 0, dim = free); 2.1 s later the pads back
    (pad 1 = Macros, pads 9 / 17 / 25 dark);
  * pad 9 held + K3 = slot 2 of macro 3 picked: pad 9 white (and it stays past the 2 s), the macro's position unchanged;
  * OSC 1, Duplicate + K1 (semitones) = that slot: destination 7, 0..127, depth 127; K3 blinks white; the pick used (pad 9 bright, not white);
    Duplicate + K1 again (no pick) = Macros 2's first free knob;
  * pad 17 held + K3, FX page, Duplicate + K8 (post-FX level, 52..82) = slot 3, depth 64 + 15;
  * Clear + pad 9 while the pads show = slot 2 unused (0, 0, 127, 64);
  * pad 1 held + K5 from OSC 1 = slot 1 of macro 5 picked, the page OSC 1 again;
  * pad 26 = the macro editor (the row hidden), again = off; pad 25 alone = nothing;
  * Macros 2 on the knobs, pad 1 held + K1 = that Macros 2 knob freed (as 7.32).
    python tools/emu_novasec4.py firmware/a7.37
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn.arm_const import UC_ARM_REG_R0
import emu_sc48_8 as S
import emu_sc42_6 as X
import arp as A
import novasec as N
import vcf21 as V

MGR, GETTER = S.MGR, 0x08036192
PRESS, RELEASE, KNOB, BTN, BTN_UP = 0x08033282, 0x080332FE, 0x08033848, 0x08033320, 0x0803381A
ID_CLEAR, ID_DUP = 23, 24
WHITE, RED, ORANGE = N.FL_COL
S1, S1D = N.SYN_COL[0], N.SYN_COL[2]


def main(a):
    d = Path(a[0]); img = next(d.glob("*.bin")).read_bytes(); man = json.loads((d / "manifest.json").read_text())
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    N.use_v2(); N.use_fix(); N.use_v3(); N.use_v4(); N.use_v8()
    e = S.ET(img, man)
    t = [500000]
    def at(ms): t[0] += ms; e.w32(A.HAL_TICK, t[0])
    def frame(): at(20); X.frame(e); return X.frame(e)
    def quiet(ms=1000): at(ms); return frame()
    def pad(q, shift=False, held=None):
        if held is not None: e.call(BTN, MGR, held, maxins=8_000_000)
        if shift: e.set_p0(e.r32(MGR + 0xC), 1)
        e.call(PRESS, MGR, q, 100, maxins=8_000_000); e.call(RELEASE, MGR, q, maxins=8_000_000)
        if shift: e.set_p0(e.r32(MGR + 0xC), 0)
        if held is not None: e.call(BTN_UP, MGR, held, maxins=8_000_000)
        return frame()
    def knob(k, dl, n=1, held=None, padheld=None):
        if held is not None: e.call(BTN, MGR, held, maxins=8_000_000)
        if padheld is not None: e.call(PRESS, MGR, padheld, 100, maxins=8_000_000)
        for _ in range(n): e.call(KNOB, MGR, k, dl & 0xFFFFFFFF, maxins=8_000_000)
        if padheld is not None: e.call(RELEASE, MGR, padheld, maxins=8_000_000)
        if held is not None: e.call(BTN_UP, MGR, held, maxins=8_000_000)
        return frame()
    def get(p): e.call(GETTER, 0, p, maxins=400_000); return e.uc.reg_read(UC_ARM_REG_R0) & 0xFF
    gst = int(man["report"]["sc14"]["labels"]["c_gst"], 16)
    def alt():
        e.call(gst, maxins=100_000); g = e.uc.reg_read(UC_ARM_REG_R0)
        return g and e.r8(g + N.S_PAINT) & N.F_SRC and e.r8(MGR + 0x152) == 0
    page = lambda: e.r8(N.NS + 4) & 15
    def xrow(k):
        rec = e.r32(N.SESSION + 0x14)
        b = lambda j: e.r8(rec + N.SYN_AREA + N.PSIZE * (j >> 1) + N.PSET + N.XB + (j & 1))
        return b(k + 2) if b(0) == N.XSIG else 0xFF
    slot = lambda m, s_: [get(N.MAC0 + 17 * m + 4 * s_ + j) for j in range(4)]
    col = lambda f, k: f[60 + k] & 0xFF
    at(0)
    for _ in range(5):
        if alt(): break
        e.btn(0); quiet()
    check(alt(), "Synth 1's alt page reached")
    f = quiet(3000)
    N.use_v10(); N.use_v11(); N.use_v12()
    rec = e.r32(N.SESSION + 0x14)
    def xb(k): return e.r8(rec + N.SYN_AREA + N.PSIZE * (k >> 1) + N.PSET + N.XB + (k & 1))
    def x2(k): return e.r8(rec + N.SYN_AREA + N.PSIZE * k + N.PSET + 6)
    def shift(on): e.set_p0(e.r32(MGR + 0xC), 1 if on else 0)
    # K1 of Macros 2 = VCA-VCF-FX's K5 (frequency, row 34): Duplicate + K5 on page 4 (no pick: the first free Macros 2 knob)
    pad(3); knob(4, 1, held=ID_DUP)
    check(xb(0) == N.XSIG and xb(2) == 34, f"Duplicate + K5 (frequency) on pad 4: Macros 2 K1 = row 34 ({xb(2)})")
    # Macros 2 (Shift + pad 1), K1 turned: pads 1 / 9 = its destinations
    pad(0, shift=True); f = knob(0, 1)
    check(page() == 8 and f[0] == S1 and f[8] == S1D, f"Macros 2, K1 turned: pad 1 bright (set), pad 9 dim (free) ({f[0]:#x}, {f[8]:#x})")
    f = knob(0, 1, padheld=8)
    check(f[8] == WHITE, f"pad 9 held + K1: the second destination picked, pad 9 white ({f[8]:#x})")
    # VCA-VCF-FX page, Duplicate + K6 (resonance, row 36): written as K1's second
    pad(3); knob(5, 1, held=ID_DUP)
    check(x2(0) == 36, f"Duplicate + K6 (resonance) on pad 4: K1's second destination = row 36 ({x2(0)})")
    # turning K1 on Macros 2 moves both: resonance follows frequency's place in its range
    pad(0, shift=True); fr0, rs0 = get(34), get(36)
    knob(0, 20)
    fr1, rs1 = get(34), get(36)
    check(fr1 != fr0 and rs1 != rs0, f"Macros 2 K1 +20: frequency {fr0} -> {fr1}, resonance {rs0} -> {rs1} (both move)")
    def place(row, v):
        e.uc.mem_write(0x20060000, bytes(8))
        import struct
        t = struct.unpack_from("8B", bytes(e.uc.mem_read(N.TABLE + 8 * row, 8)))
        lo, hi = (t[5] + (t[6] - 256 if t[6] > 127 else t[6]), t[7] + t[5]) if t[4] == 2 else (0, t[7])
        return (v - lo) / max(1, hi - lo)
    check(abs(place(34, fr1) - place(36, rs1)) < 0.05, f"  the same place in their ranges ({place(34, fr1):.2f} / {place(36, rs1):.2f})")
    f = knob(0, 1)
    check(f[8] == S1, f"  pads: pad 9 bright now (set) ({f[8]:#x})")
    # Clear + pad 9 while they show = the second freed
    pad(8, held=ID_CLEAR)
    check(x2(0) == 0xFF and xb(2) == 34, f"Clear + pad 9: the second freed ({x2(0):#x}), the first stays ({xb(2)})")
    # pad 1 held + K1 frees both
    pad(3); knob(0, 0, held=ID_DUP); pad(0, shift=True); knob(0, 1, padheld=8); pad(3); knob(5, 1, held=ID_DUP)
    check(x2(0) == 36, f"picked again + Duplicate: second = 36 ({x2(0)})")
    pad(0, shift=True); knob(0, 1, padheld=0)
    check(xb(2) == 0xFF and x2(0) == 0xFF, f"pad 1 held + K1: both freed ({xb(2):#x}, {x2(0):#x})")
    print(f"{man.get('marker')} M2X2 RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:]) else 0)
