"""Circuit Tracks 4486 - SC51 = SC50.9 + mutate39.use_acc64 (the mutate's accent up to + 64, ghost - 32) + velglob (Advanced Setup K1 / K2 = global velocity
-> amp / filter for the stock synths and the own synth; the pads' curve gone; the user, 2026-11-03).  («SC50.10» would be cut to «SC50.1».)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc50_9 as B  # noqa: E402
import mutate39  # noqa: E402
mutate39.use_acc64()
import dspz  # noqa: E402
import velglob  # noqa: E402
import linein3  # noqa: E402

NAME = "SC51"


def extra(img, report):
    B.extra(img, report)
    dspz.add(img, report, "velglob", velglob)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
