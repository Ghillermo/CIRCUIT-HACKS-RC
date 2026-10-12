"""Circuit Tracks 4486 — SC38.1 = SC38 + vcf21.use_stretch() (the user, 2026-10-11: «sample stretch que altera el tempo / duración pero no el pitch»): a third
note mode of the granular engine (Shift + K6: pitch / slicer / stretch); in the stretch mode the sample lasts K3 = 1..64 steps of the transport whatever the
pitch (ARM only: the position goes to core 1 every 4 ms, the scan frozen, the zone the smallest)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc38 as B  # noqa: E402  (configures everything as SC38)
import vcf21  # noqa: E402
import linein3  # noqa: E402
vcf21.use_stretch()

NAME = "SC38.1"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
