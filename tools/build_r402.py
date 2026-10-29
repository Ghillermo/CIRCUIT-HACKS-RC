"""Circuit Tracks 4486 - RC4.02 (marker "R402") = RC4.01 + the fixes since (the user, 2026-10-29): chromfix (a chromatic drum pad recorded
while playing = a hit with its pitch at its own step; quantize moves the pitch with its hit), savedefer + packio.use_svskip (the project save
waits for the transport to stop, one DSP read instead of 65), masterfx_dsp.use_novinyl (Digitise's K4 envelope works again)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import autorel  # noqa: E402
autorel.use_init()
import masterfx_dsp  # noqa: E402
masterfx_dsp.use_novinyl()                           # the Vinyl's routine and its call: Digitise's K4 envelope works again
import packio  # noqa: E402
packio.use_svskip()                                  # the project save reads the slots' bits only when nothing is pending
import build_sc48_7 as B  # noqa: E402
import chromfix  # noqa: E402
import savedefer  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402

NAME = "R402"


def extra(img, report):
    B.extra(img, report)
    import build_sc41_5
    build_sc41_5.add(img, report, "chromfix", chromfix)          # a chromatic drum pad recorded = a hit with its pitch (recording, quantize)
    build_sc41_5.add(img, report, "savedefer", savedefer)        # the project save while playing: kept until the transport stops
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
