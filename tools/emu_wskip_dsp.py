"""SC56.1 DSP test (vcf21_dsp.use_wskip: the oscillator skips the waves at weight 0), on the emulated core 0 (emu_blep4_dsp's harness, MIDI 1), against
the build before it (SC56):
  * core 0 still ends before gentab's tables;
  * one oscillator at the morph's pure positions (sine 0, triangle 42, saw 84, pulse 126), between them (21, 63, 105) and with the supersaw (saw,
    SHAPE 100): the output words bit for bit as PREV's;
  * two oscillators (saw + pulse, sine + saw with FM, the hard sync): bit for bit;
  * the cost: the median instructions a block, against PREV.

    python tools/emu_wskip_dsp.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json      (SC56.1 / SC56)
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_blep4_dsp as B4  # noqa: E402
import vcf21_dsp as VD  # noqa: E402

O2 = VD.OS2B0 - VD.OSB0


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    import gentab as G
    G.use_xtab()
    if hasattr(G, 'use_xtf'): G.use_xtf()                                         # (SC52.8) TF in X: the tables from $3F4E
    dw, pw = int(man["report"]["sc16"]["dsp_words"], 16), int(pman["report"]["sc16"]["dsp_words"], 16)
    check(dw <= G.GEN_TATK, f"core 0 ends at P:${dw:x} (PREV ${pw:x}: {dw - pw:+d} words; the tables from ${G.GEN_TATK:x})")
    nb = 24
    new, old = B4.renderer(img, man, nb), B4.renderer(prev, pman, nb)
    cost = []
    for what, wave, shape, ex in (("sine", 0, 50, None), ("sine / triangle", 21, 50, None), ("triangle", 42, 50, None), ("triangle / saw", 63, 50, None),
                                  ("saw", 84, 50, None), ("supersaw", 84, 100, None), ("saw / pulse", 105, 50, None), ("pulse 20", 126, 20, None),
                                  ("folded sine", 0, 90, None),
                                  ("two: saw + pulse", 84, 50, {VD.DFLAGS_OFF: 2, VD.NOTE2_OFF: 79, O2 + 2: 126, O2 + 3: 50, O2 + 4: 64, O2 + 6: 64}),
                                  ("two: sine + saw, FM 80", 0, 50, {VD.DFLAGS_OFF: 2, VD.NOTE2_OFF: 72, O2 + 2: 84, O2 + 3: 50, O2 + 6: 80}),
                                  ("two: hard sync (saws)", 84, 0, {VD.DFLAGS_OFF: 2, VD.NOTE2_OFF: 84, O2 + 2: 84, O2 + 3: 0, O2 + 4: 127, O2 + 5: 1, O2 + 8: 40, O2 + 6: 64})):
        x, i_new, ra = new(72, wave, shape, ex); xo, i_old, rb = old(72, wave, shape, ex)
        check(ra == rb and max(abs(v) for v in x) > 0.05, f"{what}: bit for bit as PREV ({len(ra)} words); {i_new} instructions a block (PREV {i_old}, {100 * (i_new - i_old) / i_old:+.0f} %)")
        cost.append((what, i_new, i_old))
    print("cost: " + "; ".join(f"{w} {a} / {b} ({100 * (a - b) / b:+.0f} %)" for w, a, b in cost))
    print(f"{man.get('marker', '?')} WSKIP DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text()), Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text())) else 0)
