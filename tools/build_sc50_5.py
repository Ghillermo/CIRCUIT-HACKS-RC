"""Circuit Tracks 4486 - SC50.5 = SC50.4 + mixsolo (pad 16 of the Mixer held + pads 1-8: the other tracks muted; the user, 2026-11-02) + build_sc17.use_nogoff (room: 512 B) + drumpat.use_repeat (pad 32 of the drums' mutate: a repeat, not a delay)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc17  # noqa: E402
build_sc17.use_nogoff()
import drumpat  # noqa: E402
drumpat.use_repeat()
import build_sc50_4 as B  # noqa: E402
import build_sc41_5 as A  # noqa: E402
import mixsolo  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402

NAME = "SC50.5"


def extra(img, report):
    B.extra(img, report)
    A.add(img, report, "mixsolo", mixsolo)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
