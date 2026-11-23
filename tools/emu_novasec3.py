"""Alpha 7.32 test (novasec.use_v3) through the controller (Shift / Clear / Duplicate / pad 1 really held) and the LED task, on Synth 1's alt page:
  * pad 1 in Synth 1's colour: bright on Macros (0x32), dim elsewhere (0x38);
  * Clear + knob on Macros = the stock's (macroed / novasec leave the macro's slot 1 alone); on OSC 1 = nothing (the value stays);
  * pad 1 held + K3 on Macros = macro 3's slot 1 freed (depth 64), K3's LED red;
  * Duplicate + K1 on OSC 1 = the first free macro (3) gets it: K3's LED white, pad 1 bright (Macros' colour) on the blink, dim off it;
    again = the same hint (already there);  Duplicate + K3 (wave, no free macro) = extra knob 1: K1 white, pad 1 in Macros 2's colour;
  * Macros 2: K1's LED lit (the wave), K2 dark; pad 1 held (the page before = Macros 2) + K1 = the extra knob freed, Macros 2 shown, K1 red;
  * Duplicate + a knob with every macro and extra knob taken = that knob orange.
    (7.33) pad 1 held + a knob on Macros resets the macro's four slots; (7.34) Macros' knob LEDs in the synth's colour by value;
    (7.35) a free macro wins over an extra knob that already had the parameter (that extra knob freed).
    python tools/emu_novasec3.py firmware/a7.32 | firmware/a7.33
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
    N.use_v2(); N.use_fix(); N.use_v3()
    e = S.ET(img, man)
    t = [500000]
    def at(ms): t[0] += ms; e.w32(A.HAL_TICK, t[0])
    def frame(): at(20); X.frame(e); return X.frame(e)
    def quiet(): at(1000); return frame()                                                 # past the hint
    def pad(q, shift=False):
        if shift: e.set_p0(e.r32(MGR + 0xC), 1)
        e.call(PRESS, MGR, q, 100, maxins=8_000_000); e.call(RELEASE, MGR, q, maxins=8_000_000)
        if shift: e.set_p0(e.r32(MGR + 0xC), 0)
        quiet()
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
    def page():
        return e.r8(N.NS + 4) & 15
    def xrow(k):
        rec = e.r32(N.SESSION + 0x14)
        b = lambda j: e.r8(rec + N.SYN_AREA + N.PSIZE * (j >> 1) + N.PSET + N.XB + (j & 1))
        return b(k + 2) if b(0) == N.XSIG else 0xFF
    depth = lambda m: get(N.MAC0 + 17 * m + 3)
    col = lambda f, k: f[60 + k] & 0xFF
    at(0)
    for _ in range(5):
        if alt(): break
        e.btn(0); quiet()
    check(alt(), "Synth 1's alt page reached")
    f = quiet()
    check(page() == 0 and f[0] == S1, f"Macros: pad 1 in Synth 1's colour ({f[0]:#x})")
    pad(1); f = quiet()
    check(page() == 1 and f[0] == S1D, f"OSC 1: pad 1 in Synth 1's dim colour ({f[0]:#x})")
    w0 = get(12); knob(0, 1, n=4, held=ID_CLEAR)
    check(get(12) == w0, f"Clear + K1 on OSC 1: nothing ({w0} -> {get(12)})")
    pad(0); d2 = depth(2)
    if "kl_m0" in man["report"]["novasec"]["labels"]:                                         # (7.34) Macros' knob LEDs drawn: Synth 1's colour, the macro's value
        f = quiet(); want = [S1 | (get(N.MAC0 - 1 + 17 * k) + 2) << 8 for k in range(8)]
        check(list(f[60:68]) == want, f"(7.34) OSC 1 -> Macros: the knob LEDs in Synth 1's colour by value ({[hex(x) for x in f[60:68]]})")
    knob(2, -1, n=4, held=ID_CLEAR)
    check(depth(2) == d2, f"Clear + K3 on Macros: the stock's (macro 3's slot 1 depth kept: {d2} -> {depth(2)})")
    f = knob(2, 1, padheld=0)
    check(depth(2) == 64 and page() == 0 and col(f, 2) == RED, f"pad 1 held + K3 on Macros: macro 3 freed ({depth(2)}), K3 red ({col(f, 2):#x})")
    if "kn_cl4" in man["report"]["novasec"]["labels"]:                                         # (7.33) all four slots of macro 3
        sl = [[get(N.MAC0 + 17 * 2 + 4 * k + j) for j in range(4)] for k in range(4)]
        check(sl == [[0, 0, 127, 64]] * 4, f"(7.33) macro 3's four slots reset ({sl})")
    at(140); f = frame()
    check(col(f, 2) != RED, f"the blink's off phase ({col(f, 2):#x})")
    free = [m for m in range(8) if depth(m) == 64]
    pad(1)
    f = knob(0, 1, held=ID_DUP); mf = free[0]
    check(get(N.MAC0 + 17 * mf) == 7 and depth(mf) == 127 and col(f, mf) == WHITE and f[0] == S1,
          f"Duplicate + K1 (semitones) on OSC 1: macro {mf + 1} = destination 7; K{mf + 1} white ({col(f, mf):#x}), pad 1 Macros' colour ({f[0]:#x})")
    at(140); f = frame()
    check(f[0] == S1D, f"pad 1 dim on the off phase ({f[0]:#x})")
    quiet(); f = knob(0, 1, held=ID_DUP)
    check(col(f, mf) == WHITE and [m for m in range(8) if depth(m) == 64] == [m for m in free if m != mf], f"again: the same hint, nothing more ({col(f, mf):#x})")
    quiet()
    rest = [m for m in range(8) if depth(m) == 64]
    for m in rest:                                                                             # fill the other free macros (if any) with OSC 1 rows
        knob(3 + rest.index(m), 1, held=ID_DUP); quiet()
    f = knob(2, 1, held=ID_DUP)
    check(xrow(0) == 6 and col(f, 0) == WHITE and f[0] == V.NS_COL, f"Duplicate + K3 (wave): extra knob 1 = row 6 ({xrow(0)}), K1 white, pad 1 Macros 2's colour ({f[0]:#x})")
    if "d6_a" in man["report"]["novasec"]["labels"]:                                           # (7.35) a free macro before an extra knob that has it
        pad(1); quiet(); knob(1, 1, held=ID_DUP); quiet()
        check(xrow(1) == 13, f"(7.35) no free macro: Duplicate + K2 (cents) = extra knob 2 ({xrow(1)})")
        pad(0); knob(4, 1, padheld=0); quiet()
        pad(1); f = knob(1, 1, held=ID_DUP)
        check(get(N.MAC0 + 17 * 4) == N.DROW.index(13) and depth(4) == 127 and xrow(1) == 0xFF and col(f, 4) == WHITE and f[0] == S1,
              f"(7.35) macro 5 freed, Duplicate + K2 again = macro 5 ({get(N.MAC0 + 17 * 4)}), extra knob 2 freed ({xrow(1):#x}), K5 white, pad 1 magenta")
        quiet()
    pad(0, shift=True); f = quiet()
    check(page() == 8 and f[60] & 0xFF == V.NS_COL and f[61] == 0, f"Macros 2: K1 lit ({f[60]:#x}), K2 dark ({f[61]:#x})")
    f = knob(0, 1, padheld=0)
    check(xrow(0) == 0xFF and page() == 8 and col(f, 0) == RED, f"pad 1 held + K1 on Macros 2: extra knob 1 freed ({xrow(0):#x}), Macros 2 kept, K1 red ({col(f, 0):#x})")
    pad(2)                                                                                     # OSC 2: fill every extra knob, then no room
    for k in range(8):
        knob(k, 1, held=ID_DUP); quiet()
    full = all(xrow(k) != 0xFF for k in range(8))
    pad(3)
    f = knob(5, 1, held=ID_DUP)
    rows_now = [xrow(k) for k in range(8)]
    check(full and col(f, 5) in (ORANGE, WHITE), f"every extra knob taken ({rows_now}); Duplicate + K6 on VCA = K6 orange or an existing holder white ({col(f, 5):#x})")
    if "c_nsfw" in man["report"]["novasec"]["labels"]:                                         # (7.36) the section page follows into the other views
        quiet(); pad(1); quiet()
        e.btn(0); quiet()
        check(not alt(), f"(7.36) out of the alt page (sub-view {e.r8(MGR + 0x152)})")
        s0, m0 = get(12), get(N.MAC0 - 1); knob(0, 5); quiet()
        check(get(12) == min(s0 + 5, 127) and get(N.MAC0 - 1) == m0, f"(7.36) Note view, K1 = OSC 1's semitones ({s0} -> {get(12)}), the macro stays ({m0} -> {get(N.MAC0 - 1)})")
        f = quiet()
        check(f[60] & 0xFF == N.page_colours()[1][0], f"(7.36) K1's LED in OSC 1's colour ({f[60]:#x})")
        f = knob(6, 1, held=ID_DUP)
        check(any(col(f, k) in (WHITE, ORANGE) for k in range(8)), f"(7.36) Duplicate + K7 there: a hint ({[hex(col(f, k)) for k in range(8)]})")
        quiet(); s1 = get(12); dd = [depth(m) for m in range(8)]; knob(0, -2, padheld=0); quiet()
        check([depth(m) for m in range(8)] == dd, "(7.36) pad 1 held + knob outside the alt page: nothing freed")
        for _ in range(5):
            if alt(): break
            e.btn(0); quiet()
        pad(0); e.btn(0); quiet()
        m1 = get(N.MAC0 - 1); knob(0, -3); quiet()
        check(not alt() and get(N.MAC0 - 1) != m1, f"(7.36) Macros picked: the Note view's K1 = macro 1 again ({m1} -> {get(N.MAC0 - 1)})")
    print("NOVASEC3 RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
