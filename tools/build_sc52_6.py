"""Circuit Tracks 4486 - SC52.6 = SC52.5 + (the user, 2026-11-06): Duplicate + an empty slot = save (psave.use_dupsave); the page row's pad 1 / pad 4
exchanged (tools/rowswap.py: 1 the assigned knobs, Shift + 1 the non-sequenceable ones, 4 VCA / VCF); the bipolar knobs' left half in the lighter
shade of their colour and a dim centre (vcf21.use_bipcol, persist19.use_leftcol, build_sc17.LEFTCOL, oscmod.LEFT), K5 (FM) coloured by mode;
wavetable patches' slots in sand (fm8ui.WTCOL); the wavetable's level chosen for the warp's steeper slope (vcf21_dsp.use_wtaa); Jankó: keys held in rows 2 and 4 = Octave moves rows 1 and 3 (janko.use_v4); Advanced Setup K3 = the external inputs' gain, 0..+24 dB (ingain); Clear + pad 7 = the frame back to its table's (wtui.use_wtdef); oscmod / autolane moved to the
hole for room."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc52_5 as S  # noqa: E402
import linein3  # noqa: E402

NAME = "SC52.6"
B = S.B


def extra(img, report):
    S.extra(img, report)
    import hole
    import rowswap
    hole.add(img, report, "rowswap", rowswap)              # the outermost heads of the template view's slots 0 / 1 / 7
    hole.add(img, report, "ingain", ingain)                # Advanced Setup K3 = the inputs' gain


import build_sc52_4  # noqa: E402
build_sc52_4.IN_HOLE = True
import vcf21  # noqa: E402
vcf21.use_bipcol()
import persist19  # noqa: E402
persist19.use_leftcol()
import build_sc17  # noqa: E402
build_sc17.LEFTCOL = True
import oscmod  # noqa: E402
oscmod.LEFT = True
import psave  # noqa: E402
psave.use_dupsave()
import fm8ui  # noqa: E402
fm8ui.WTCOL = True
import wtui  # noqa: E402
wtui.use_wtdef()
import vcf21_dsp  # noqa: E402
vcf21_dsp.use_wtaa()
import janko  # noqa: E402
janko.use_v4()
import ingain  # noqa: E402
vcf21_dsp.use_ingain(ingain.GAIN)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
