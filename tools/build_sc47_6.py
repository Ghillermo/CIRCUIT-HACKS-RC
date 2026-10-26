"""Circuit Tracks 4486 - SC47.6 = SC47.5 + the unison's modes and six FM voices (the user, 2026-10-26: «Add uni retrig, uni portamento and uni
glide, increase FM polyphony to six shared voices if possible»): poly.use_v5() (seven voice modes: uni retrig, uni portamento, uni glide; a
unison note over a held one only moves the voices; six records a track: six FM voices to a track alone, 3 + 3 with both), vcf21_dsp.use_glide2()
(the track's glide under the unison's voices; the jump of uni glide), vcf21_dsp.use_poly6() (the six-voice layout), fmeng.use_wc6() (the cache's
ranges), vmode.use_v2() (seven modes on pads 17-23)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc47_5 as B  # noqa: E402
import vcf21_dsp  # noqa: E402
vcf21_dsp.use_glide2()
vcf21_dsp.use_poly6()
import fmeng  # noqa: E402
fmeng.use_wc6()
import poly  # noqa: E402
poly.use_v5()
import vmode  # noqa: E402
vmode.use_v2()
import linein3  # noqa: E402

NAME = "SC47.6"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
