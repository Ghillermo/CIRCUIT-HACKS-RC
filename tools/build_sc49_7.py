"""Circuit Tracks 4486 - SC49.7 = SC49.6 + room in the flash (the user, 2026-10-29: «Both»): gentab (six core-0 tables built at DSP start, not loaded),
build_sc17.use_novtab (the Vinyl's dead knob tables out)
+ fixes (the user, 2026-10-29): chromfix (a chromatic pad's pitch goes with the nearest hit; quantize moves it with its hit), the project save
during playback (packio.use_svskip: one DSP read instead of 65; savedefer: the save waits for the transport to stop)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc49_6 as B  # noqa: E402
import build_sc16  # noqa: E402
import gentab  # noqa: E402
gentab.use()                                         # the two tables' users read them at their generated addresses
gentab.install_dsp(build_sc16)                       # the generator, the last of the DSP code; P:$10B -> init2
import build_sc17  # noqa: E402
build_sc17.use_novtab()                              # the Vinyl's four knob tables out (nothing reads them since SC39.7): 2 KB
import packio  # noqa: E402
packio.use_svskip()                                  # the project save reads the slots' bits only when nothing is pending
import chromfix  # noqa: E402
import savedefer  # noqa: E402
import dautov  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402

NAME = "SC49.7"


def extra(img, report):
    B.extra(img, report)
    import build_sc41_5
    build_sc41_5.add(img, report, "chromfix", chromfix)          # the chromatic pitch with its hit (recording, quantize)
    build_sc41_5.add(img, report, "savedefer", savedefer)        # the project save while playing: kept until the transport stops
    build_sc41_5.add(img, report, "dautov", dautov)              # the drums' automation view: yellow / red steps, Shift preview, marks, Clear + step
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
