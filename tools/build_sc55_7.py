"""Circuit Tracks 4486 - SC55.7 = SC55.6 + tools/fm8dest.py (the user, 2026-11-10: «assign pertinent macro destinations to new and existing patches»): loading
one of the 48 instruments of the 8-operator FM from the pad 8 list sets page 4 (sequenceable knobs) and Shift + pad 4 (non-sequenceable) to the
destinations of its family (make_examples.FAM_DEST)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc55_6 as S  # noqa: E402
import linein3  # noqa: E402

NAME = "SC55.7"
B = S.B


def extra(img, report):
    import build_sc41_5 as B5
    import fm8dest
    S.extra(img, report)
    B5.add(img, report, "fm8dest", fm8dest)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
