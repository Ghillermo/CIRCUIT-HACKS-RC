"""Alpha 7.37 test (novasec.use_v8) through the controller and the LED task, on Synth 1's alt page:
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
    check(f[0] == S1 and f[8] == 0 and f[16] == 0 and f[24] == 0, f"no macro moved: pad 1 = Macros, pads 9 / 17 / 25 dark ({[hex(f[k]) for k in (0, 8, 16, 24)]})")
    m0 = get(N.MAC0 - 1 + 17 * 2); f = knob(2, 1)
    want = [S1 if slot(2, s_)[3] != 64 else S1D for s_ in range(4)]
    check([f[k] for k in (0, 8, 16, 24)] == want and get(N.MAC0 - 1 + 17 * 2) != m0, f"K3 moved on Macros: macro 3's slots on pads 1 / 9 / 17 / 25 ({[hex(f[k]) for k in (0, 8, 16, 24)]}, depths {[slot(2, s_)[3] for s_ in range(4)]})")
    f = quiet(2100)
    check(f[0] == S1 and f[8] == 0, "2.1 s later: the pads back")
    m1 = get(N.MAC0 - 1 + 17 * 2); f = knob(2, 3, padheld=8)
    check(f[8] == WHITE and get(N.MAC0 - 1 + 17 * 2) == m1, f"pad 9 held + K3: slot 2 of macro 3 picked (pad 9 {f[8]:#x}), the macro not moved")
    f = quiet(3000); check(f[8] == WHITE, "the picked slot stays on the pads")
    pad(1); f = knob(0, 1, held=ID_DUP)
    check(slot(2, 1) == [7, 0, 127, 127] and col(f, 2) == WHITE and f[8] == S1, f"OSC 1, Duplicate + K1: slot 2 of macro 3 = {slot(2, 1)}; K3 white ({col(f, 2):#x}), pad 9 in use ({f[8]:#x})")
    quiet(); x0 = [xrow(k) for k in range(8)]; f = knob(0, 1, held=ID_DUP); k_free = x0.index(0xFF) if 0xFF in x0 else None
    check(k_free is not None and xrow(k_free) == 12 and col(f, k_free) == WHITE, f"again, no pick: Macros 2's knob {k_free + 1 if k_free is not None else '-'} = row 12 ({[xrow(k) for k in range(8)]})")
    quiet(); knob(2, 1, padheld=16); pad(5); f = knob(7, 1, held=ID_DUP)
    check(slot(2, 2) == [N.DROW.index(29), 0, 127, 64 + 15], f"pad 17 held + K3, FX, Duplicate + K8 (post-FX level 52..82): slot 3 = {slot(2, 2)} (depth 79)")
    quiet(3000); pad(0); knob(2, 1); f = pad(8, held=ID_CLEAR)
    check(slot(2, 1) == [0, 0, 127, 64] and f[8] == S1D, f"Clear + pad 9 with macro 3 on the pads: slot 2 unused ({slot(2, 1)}), pad 9 dim ({f[8]:#x})")
    quiet(3000); pad(1); knob(4, 1, padheld=0); f = frame()
    check(page() == 1 and f[0] == WHITE and e.r8(N.NS + 4 + N.O_PK) & 0x3F == 0x20 | 4, f"pad 1 held + K5 from OSC 1: slot 1 of macro 5 picked ({e.r8(N.NS + 4 + N.O_PK):#x}), the page OSC 1 again ({page()})")
    f = pad(24); check(page() == 1 and f[1] != 0, "pad 25 alone: nothing")
    f = pad(25); check(all(f[k] == 0 for k in range(1, 8)), f"pad 26 = the macro editor (the row hidden: {[hex(x) for x in f[:8]]})")
    f = pad(25); check(f[1] != 0, "pad 26 again: the editor off")
    pad(0, shift=True); quiet(3000)
    kx = next(k for k in range(8) if xrow(k) != 0xFF); f = knob(kx, 1, padheld=0)
    check(xrow(kx) == 0xFF and page() == 8 and col(f, kx) == RED, f"Macros 2 on the knobs, pad 1 held + K{kx + 1}: that Macros 2 knob freed, K{kx + 1} red ({col(f, kx):#x})")
    print("NOVASEC4 RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
