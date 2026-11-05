"""Circuit Tracks 4486 - SC52.1 = SC52 + the wavetable engine (the user, 2026-11-05: «Select wavetables in engine mode. Knob layout on osc1 and osc2
views»; see docs/NOTAS.md): room on core 0 first (gentab.use_xtab: TINC / TLFO in core 0's X)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc52 as S  # noqa: E402
import gentab  # noqa: E402
import linein3  # noqa: E402
import vcf21_dsp  # noqa: E402
import granular_dsp  # noqa: E402
import packio  # noqa: E402

NAME = "SC52.1"
B = S.B
gentab.use_xtab()
vcf21_dsp.use_wavetable()
granular_dsp.use_wtcopy()
packio.IMP_HI = 0x520000                     # the imports' free memory ends where the two tables start (Y:$520000 / $548800)
import psave  # noqa: E402
import xpatch  # noqa: E402
psave.XLEN = xpatch.XLEN = 163                             # psave's swap / xpatch's copy carry the wavetable's record (padding + 150..162)
psave.XBUF = packio.BUF + 256                # (fix) the swap's second patch past the first: XLEN > 128 since SC47.5 overwrote A's bytes 128.. before A was written to B


def extra(img, report):
    S.extra(img, report)
    import dspz
    import wtui
    dspz.add(img, report, "wtui", wtui)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
