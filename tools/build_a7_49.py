"""Circuit Tracks 4486 - Alpha 7.49 (marker "A7.49") = Alpha 7.48 + vcf21.use_famcol() + novasec.use_famcol() (the user, 2026-11-24: colour families
on the synth pages: envelopes and what they modulate pink, LFOs and what they modulate violet; VCA yellow, VCF gold, FX lemon)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import vcf21, novasec
    vcf21.use_famcol()
    novasec.use_famcol()
    import build_a7_48 as A48
    src = Path(A48.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.48"') == 2, "A7.48 marker strings"
    src = src.replace('"A7.48"', '"A7.49"')
    sys.argv = [A48.__file__] + sys.argv[1:]
    exec(compile(src, A48.__file__, "exec"), {"__name__": "__main__", "__file__": A48.__file__})
