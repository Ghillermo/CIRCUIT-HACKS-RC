"""Circuit Tracks 4486 - SC55.9 = SC55.8 + patmut.use_v2() (the user, 2026-11-10: «make 8 amounts and mutated patterns end the scene, like
Remix just did»): Amount in eight steps on the settings page; a mutating track's chain ends with its list's last slot (Remix's RH88)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc55_8 as S  # noqa: E402
import linein3  # noqa: E402
import patmut  # noqa: E402
import tabpack  # noqa: E402

NAME = "SC55.9"
B = S.B
extra = S.extra


if __name__ == "__main__":
    tabpack.use()
    patmut.use_v2()
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
