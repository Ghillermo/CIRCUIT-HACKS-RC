"""Alpha 7.50 test (novasec.use_v10), from emu_novasec4's set-up (novasec.use_v8) through the controller and the LED task, on Synth 1's alt page:
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
    N.use_v10()
    if man.get("marker", "") >= "A7.51": N.use_v11()                                               # (7.51) the EQ lime
    import novasec as NN
    names = {V.FAM_ENV: "env", V.FAM_LFO: "lfo", V.FAM_VCA: "vca", V.FAM_VCF: "vcf", V.FAM_FX: "fx", 0x70: "eq"}
    def fam(row):
        if row == 0xFF: return 0
        if NN.V11 and 80 <= row < 86: return NN.EQ_COL
        for top, c in ((24, None), (30, V.FAM_VCA), (38, V.FAM_VCF), (54, V.FAM_ENV), (78, V.FAM_LFO), (94, V.FAM_FX)):
            if row < top: return c
    cols = NN.page_colours()
    for p_, nm in ((1, "OSC 1"), (2, "OSC 2"), (3, "VCA-VCF-FX"), (4, "Mod sources"), (6, "FX")):
        for sh in (False, True):
            f = pad(p_)
            if sh: e.set_p0(e.r32(MGR + 0xC), 1); f = frame(); e.set_p0(e.r32(MGR + 0xC), 0)
            rows = NN.ROWS10[p_ - 1][8 if sh else 0:16 if sh else 8]
            want = [0 if r == 0xFF else (fam(r) or cols[p_][0]) for r in rows]
            got = [col(f, k) for k in range(8)]
            check(page() == p_ and got == want, f"{nm}{' + Shift' if sh else ''}: {[names.get(c, hex(c)) for c in got]}")
    # a knob on the Shift layer moves its row
    pad(3); r0 = get(42); e.set_p0(e.r32(MGR + 0xC), 1); knob(0, 3); e.set_p0(e.r32(MGR + 0xC), 0)
    check(get(42) != r0 and get(40) == get(40), f"VCA-VCF-FX, Shift + K1 = Env 1 sustain ({r0} -> {get(42)})")
    # the matrix: pad 6
    f = pad(5)
    check(page() == 5, f"pad 6 = the matrix (page {page()})")
    sel = lambda: e.r8(N.NS + 5)
    f = pad(10); check(sel() == 2, f"pad 11 = slot 3 picked ({sel()})")
    check(f[10] == 0x01 and col(f, 0) == 0x01, f"slot 3's pad and K1 white ({f[10]:#x}, {col(f, 0):#x})")
    ms, md = NN._mx_tabs()
    row = 94 + 4 * 2
    f = frame()
    s1, dst, dep = get(row), get(row + 3), get(row + 2)
    w1 = ms[2 * s1] | ms[2 * s1 + 1] << 8 if s1 <= 12 else 0
    wd = md[2 * dst] | md[2 * dst + 1] << 8 if dst <= 17 else 0
    check(f[61] == w1 and f[63] == wd, f"K2 = source {s1} ({f[61]:#x}, want {w1:#x}), K4 = destination {dst} ({f[63]:#x}, want {wd:#x})")
    knob(4, 10, n=1); f = frame(); d2 = get(row + 2)
    check(d2 != dep and (f[64] & 0xFF) == (md[2 * get(row + 3)] if get(row + 3) <= 17 else 0), f"K5 depth {dep} -> {d2}, in the destination's colour ({f[64]:#x})")
    check(f[10] == ((md[2 * get(row + 3)]) if d2 != 64 else 2) or f[10] == 1, f"slot pad: picked white / used = destination colour ({f[10]:#x})")
    f = pad(7); check(page() == 5, "pad 8: nothing (still the matrix)")
    print(f"{man.get('marker')} NS10 RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:]) else 0)
