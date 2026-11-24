"""Alpha 7.49 test (novasec.use_famcol), from emu_novasec4's set-up (novasec.use_v8) through the controller and the LED task, on Synth 1's alt page:
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
    N.use_famcol(); fam = N.fam_tab()
    names = {0: "-", V.FAM_ENV: "env", V.FAM_LFO: "lfo", V.FAM_VCA: "vca", V.FAM_VCF: "vcf", V.FAM_FX: "fx"}
    for p_, nm in ((3, "VCA"), (4, "VCF"), (5, "FX"), (6, "Mod sources")):
        f = pad(p_)
        got = [names.get(col(f, k), hex(col(f, k))) for k in range(8)]
        want = [names[fam[8 * p_ + k]] for k in range(8)]
        check(page() == p_ and got == want, f"{nm} page: {got}")
    f = pad(1); got = [col(f, k) for k in range(8)]
    check(page() == 1 and all(c not in (V.FAM_ENV, V.FAM_LFO, V.FAM_VCF, V.FAM_FX) for c in got), f"OSC 1 page: its page colour ({[hex(c) for c in got]})")
    print(f"{man.get('marker')} NSFAM RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:]) else 0)
