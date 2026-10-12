"""SC23.5: the brightness of drum K8 (distortion to the right, bitcrush to the left): max(distortion, bitcrush), dimmest with no effect.

    python tools/emu_sc23_5_drums.py SC23.5.bin SC23.5_manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc19_8 import EW  # noqa: E402
from emu_sc19_6 import DCODE  # noqa: E402


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    gc.collect(); n = EW(img, man)
    for d in (0, 2):
        n.sel(d); n.track(4 + d)
        k8 = lambda: (lambda f: f[60 + 7])(n.frame())
        lvl = lambda: (k8() >> 8) - 2
        nib = lambda: (n.dext(d) >> 4) & 15
        check(nib() == 0 and lvl() == 0 and (k8() & 0xFF) == DCODE[d], f"drum {d + 1}: no effect: the dimmest ({lvl()}), the drum colour ({k8() & 0xFF:#x})")
        n.knob19(7, 40)
        check(lvl() == 40 and nib() == 0, f"distortion 40 to the right: brightness {lvl()}")
        n.knob19(7, 87)
        check(lvl() == 127, f"distortion at the maximum: the brightest ({lvl()})")
        n.knob19(7, -127)
        check(lvl() == 0 and nib() == 0, f"back to the centre: the dimmest again ({lvl()})")
        got = []
        for k in range(1, 17):
            n.knob19(7, -1); got.append((nib(), lvl()))
        want = [(min(i, 15), min(i, 15) * 8 + min(i, 15) // 2) for i in range(1, 17)]
        check(got == want and lvl() == 127, f"bitcrush to the left: brightness nibble * 8 + nibble / 2 (15 -> 127): {got[:4]} ... {got[-2:]}")
        n.knob19(7, 3)
        check(lvl() == nib() * 8 + nib() // 2, f"turning back: follows the bitcrush ({nib()} -> {lvl()})")
        n.knob19(7, 40)
        n.knob19(7, 127)
    # ---- Clear + a plain knob also resets the Shift layer of that knob (with Shift the Clear button has no function)
    import persist19 as P
    MGR = 0x20040B10
    clr_dn = lambda: n.call(0x08033320, MGR, 23, maxins=900000)
    clr_up = lambda: n.call(0x0803381A, MGR, 23, maxins=900000)
    for d in (1, 3):
        n.sel(d); n.track(4 + d)
        # K2: ring mod frequency (plain, code 2) / amount (Shift, code 8); K4: env -> cutoff (5) / env shape (7); K7: LFO amount (3) / speed (4); K5: filter mode (shift, code 9)
        n.knob19(1, 12); n.knob19(1, 20, True); n.knob19(3, 9); n.knob19(3, 14, True); n.knob19(6, 7); n.knob19(6, 11, True)
        for _ in range(2): n.knob19(4, 1, True)
        n.knob19(0, 6, True)
        before = {c: n.dval(d, c) for c in range(1, 9)}
        check(before[2] and before[8] and before[5] and before[7] and before[3] and before[4] and before[1], f"drum {d + 1}: values set in both layers {before}")
        clr_dn(); n.knob19(1, 1); clr_up()
        check(n.dval(d, 2) == 0 and n.dval(d, 8) == 0 and n.dval(d, 5) == before[5] and n.dval(d, 7) == before[7], f"Clear + K2: ring mod frequency and amount both back to 0, K4 untouched ({n.dval(d, 2)}, {n.dval(d, 8)})")
        clr_dn(); n.knob19(3, 1); n.knob19(6, 1); clr_up()
        check(all(n.dval(d, c) == 0 for c in (3, 4, 5, 7)), f"Clear + K4 and K7: both layers back to 0 ({[n.dval(d, c) for c in (3, 4, 5, 7)]})")
        mode = n.xm(P.XM_DRUMS + 9 * d + 8) & 7
        clr_dn(); n.knob19(4, 1); clr_up()
        check((n.xm(P.XM_DRUMS + 9 * d + 8) & 7) == 0 and mode != 0, f"Clear + K5: the filter mode (Shift layer) back to 0 (was {mode})")
        n.knob19(0, 6, True); had = n.dval(d, 1)
        clr_dn(); n.knob19(0, 1); clr_up()
        check(had != 0 and n.dval(d, 1) == 0, f"Clear + K1: the pitch envelope (Shift layer) back to 0 (was {had})")
        for _ in range(2): n.knob19(7, 1, True)
        xt = lambda: sum(((n.xm(P.XT_BITS[3 * d + j][0]) & P.XT_BITS[3 * d + j][1]) != 0) << j for j in range(3))
        t0 = xt()
        clr_dn(); n.knob19(7, 1); clr_up()
        check(t0 != 0 and xt() == 0, f"Clear + K8: the distortion type (Shift layer) back to 0 (was {t0})")
    print("SC23.5 DRUM K8 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
