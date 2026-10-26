"""Circuit Tracks 4486 - S47D (DIAGNOSTIC) = SC47 + tools/rdiag.py (DSPX / DSPW: the DSP's internal X / Y words read and one X word written from the PC,
tools/ctremote.py dspr / dspw; no delete).  The user, 2026-10-26, on Beta 3.27: «sigue oyéndose por los dos lados lo mismo» (the stereo sample mode):
in the emulation of the whole core 0 the two samples come out on their own sides; this reads the live side buffer, the levels and the VCA gain on
the device while a note sounds.  See firmware/s47d/PRUEBA.md."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc47 as B  # noqa: E402
import rdiag  # noqa: E402
rdiag.DSPX = True
rdiag.DSPW = True
rdiag.DELETE = False
import linein3  # noqa: E402

NAME = "S47D"


def extra(img, report):
    B.extra(img, report)
    import build_shared_channels as sc
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code = rdiag.install(img, report, ext)
    report["rdiag"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, listing=sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
