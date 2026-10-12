"""Circuit Tracks 4486 — SC361S = SC36.1 without anything of ours that writes the SD card (the "safer" build, the user, 2026-10-09):
no tools/packio.py (Save writing captures into the pack, swapping samples, deleting packs) and no remote diagnostics (tools/rdiag.py: SD read / write / delete over USB).
Our settings still travel in the reserved bytes of the stock project format (persist19), saved by the stock Save as before.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc36_1  # noqa: E402,F401  (configures everything as SC36.1)
import build_sc36 as B36  # noqa: E402
import granular_dsp  # noqa: E402
import linein3  # noqa: E402

NAME = "SC361S"


def extra(img, report):
    B36.B.b342.extra(img, report)                                                 # SC34.2's extra: no packio, no rdiag
    report["granular"] = granular_dsp.patch_core1(img)
    report["safe"] = "no packio, no rdiag"


if __name__ == "__main__":
    b5 = B36.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
