"""Circuit Tracks 4486 - SC56.4 = SC56.3 + morphz.use_four() (the user, 2026-11-11: «Make it up to 4 patches»): the patch morph takes up to four
held patches (cache 0, the present sound that use_nocur never reaches, holds the 4th)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc56_3 as S  # noqa: E402
import linein3  # noqa: E402
import morphz  # noqa: E402
import patmut  # noqa: E402
import tabpack  # noqa: E402

NAME = "SC56.4"
B = S.B
extra = S.extra


if __name__ == "__main__":
    tabpack.use()
    patmut.use_v2()
    S.S.S.S.room()
    S.S.S.cpu()
    morphz.use_four()
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
