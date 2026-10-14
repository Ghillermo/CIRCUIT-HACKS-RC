"""Circuit Tracks 4486 - SC40.8 = SC40.7 + tools/playmode.py (the user, 2026-10-13 / 14): pads 26-28 of the Pattern Settings view of the note tracks = Nudge (the
pattern rotated so that its first step is step 1) and the fractal / deconstructed play orders."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc40_7 as B  # noqa: E402  (configures everything as SC40.7)
import playmode  # noqa: E402
import linein3  # noqa: E402

NAME = "SC40.8"


def extra(img, report):
    B.extra(img, report)
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code, prev = playmode.install(img, report, ext)
    import build_shared_channels as sc
    report["playmode"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()},
                          listing=sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
