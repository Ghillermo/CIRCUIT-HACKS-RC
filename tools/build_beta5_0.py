"""Circuit Tracks 4486 - Beta 5.0 (marker "B5.0"; the user, 2026-10-29: «betas that expand RC4 get 5.xx version») = SC49.7 under the beta's
name (Beta 3.49 + the drums' automation view (dautov), the chromatic drum pads recording hit + pitch (chromfix), the project save waiting for
the transport to stop (savedefer, packio.use_svskip), the flash freed (gentab, build_sc17.use_novtab))."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc49_7 as B  # noqa: E402
import linein3  # noqa: E402

NAME = "B5.0"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
