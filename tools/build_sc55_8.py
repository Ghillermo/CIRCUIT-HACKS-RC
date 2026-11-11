"""Circuit Tracks 4486 - SC55.8 = SC55.7 + tools/tabpack.py (room in the flash; the user, 2026-11-10: «Both»: the curve tables and the FM tables
packed, rebuilt at power-up) + tools/patmut.py (the pattern mutate, ported from mefisme's Rhythm Plus, MIT)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc55_7 as S  # noqa: E402
import linein3  # noqa: E402
import tabpack  # noqa: E402

NAME = "SC55.8"
B = S.B
MUTATE = True


def extra(img, report):
    import build_sc41_5 as B5
    S.extra(img, report)
    if MUTATE:
        import patmut
        B5.add(img, report, "patmut", patmut)
    B5.add(img, report, "tabpack", tabpack)


if __name__ == "__main__":
    if "--nomut" in sys.argv: sys.argv.remove("--nomut"); MUTATE = False
    tabpack.use()
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
