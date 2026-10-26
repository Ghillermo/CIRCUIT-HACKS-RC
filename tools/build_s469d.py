"""Circuit Tracks 4486 - S469D (DIAGNOSTIC) = SC46.9 + granular_dsp.DIAG_SIDES + tools/rdiag.py (DSPX / DSPW).  The user, 2026-10-26: the stereo
sample mode «sigue mezclando los dos samples a los dos canales por igual» and the granular's width «tampoco se aprecia gran diferencia»; in the
emulation of the whole core 0 both come out wide.  Every block core0_sides (the sides into the mix before the master filter) copies what it sees for
MIDI 1 to X:$3F40: SOUT's address, the gain g, SOUT[0], the mix L / R before and after, the block counter CNT, a count of its own calls (read
with tools/ctremote.py dspr X 0x3f40 9).  See firmware/s469d/PRUEBA.md."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc46_9 as B  # noqa: E402
import granular_dsp  # noqa: E402
granular_dsp.DIAG_SIDES = 0x3F40
import rdiag  # noqa: E402
rdiag.DSPX = True
rdiag.DSPW = True
rdiag.DELETE = False
import linein3  # noqa: E402

NAME = "S469D"


def extra(img, report):
    B.extra(img, report)
    import build_shared_channels as sc
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code = rdiag.install(img, report, ext)
    report["rdiag"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, listing=sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
