"""Circuit Tracks 4486 - Alpha 7.04 (marker "A7.04") = Alpha 7.03 + overdub on the captured sample (the user, 2026-11-18: «Overdub in all cases
(even if the sample is mangled)» → «1 with decay»): sampler_dsp.use_overdub(): recording on pad 32 no longer stops the sample on pad 7; the new take =
the live mix + 0.7 x the sample as it plays (pitch, reverse, loop region, gate printed); one buffer, so a loop that plays over what is being recorded
fades by 0.7 a pass.  + tools/fixes704.py (the pending fixes: jumpseq signature, patchain's LED-task stack and chain-map check, scene clear)."""
import runpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sampler_dsp  # noqa: E402

if __name__ == "__main__":
    sampler_dsp.use_overdub()
    import fixes704
    fixes704.alpha()
    import build_a7_03 as A3
    src = Path(A3.__file__).read_text(encoding="utf-8").replace('NAME = "A7.03"', 'NAME = "A7.04"')
    ic = '            dspz.add(img, report, "icache", icache)'
    src = src.replace(ic, ic + "\n            fixes704.extra_alpha(img, report)")
    assert "fixes704.extra_alpha" in src
    sys.argv = [A3.__file__] + sys.argv[1:]
    exec(compile(src, A3.__file__, "exec"), {"__name__": "__main__", "__file__": A3.__file__, "fixes704": fixes704})
