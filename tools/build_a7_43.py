"""Circuit Tracks 4486 - Alpha 7.43 (marker "A7.43") = Alpha 7.42 + tools/noinapp.py (a fix: the running firmware ignores an install; only
the bootloader takes one. Installs sent to a running unit wrote over the internal file system on the user's Circuit, 2026-11-24)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import noinapp
    noinapp.use()
    import build_a7_42 as A42
    src = Path(A42.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.42"') == 2, "A7.42 marker strings"
    src = src.replace('"A7.42"', '"A7.43"')
    sys.argv = [A42.__file__] + sys.argv[1:]
    exec(compile(src, A42.__file__, "exec"), {"__name__": "__main__", "__file__": A42.__file__})
