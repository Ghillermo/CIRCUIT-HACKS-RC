"""Circuit Tracks 4486 - SC55.4 = SC55.3 + morphz.use_svc (fix, the user, 2026-11-08, on Synth 1: «entering morph mode stops the playback, and
resets the unit after a few seconds»: Synth 1 / 2's morph writes from the DSP service's head, no wait on its semaphore) + packio.use_catswap (the
user: «switch red Category with magenta», «and also make current magenta red»: Bass and SFX swap colours)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc55_3 as S  # noqa: E402
import linein3  # noqa: E402
import morphz  # noqa: E402
import packio  # noqa: E402

morphz.use_svc()
packio.use_catswap()
NAME = "SC55.4"
B = S.B
extra = S.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
