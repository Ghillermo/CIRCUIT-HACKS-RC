"""Circuit Tracks 4486 - SC55.6 = SC55.5 + tools/loadcache.py (a fix, the user, 2026-11-09: «play violet sometimes when loading new patches», «custom engine patches»: loading an own-synth patch read the card once per part of the patch (about twelve synchronous reads in the pad press: the sequencer's clock late, S555D2 Play white); loadcache.py reads the slot's padding and FM record once into RAM and serves the load's reads from there)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc55_5 as S  # noqa: E402
import linein3  # noqa: E402

NAME = "SC55.6"
B = S.B


def extra(img, report):
    import build_sc41_5 as B5
    import loadcache
    S.extra(img, report)
    B5.add(img, report, "loadcache", loadcache)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
