"""Circuit Tracks 4486 - RC4.01 (marker "R401") = RC4 + the fixes since: SC48.7 (the own synth's knobs send its own CC / NRPN map, no CC editor
while it is on (issue #15); the VA-drum's pad 31 only with the VA-drum; the engine row's VA-drum + pad 31) + autorel.use_init() (the user,
2026-10-29, on RC4: «the shift step doesn't revert previous automation back to init», «the cleared automation must go to Project init»: a marked
step brings the lanes back to the project's values)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import autorel  # noqa: E402
autorel.use_init()
import build_sc48_7 as B  # noqa: E402
import linein3  # noqa: E402

NAME = "R401"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
