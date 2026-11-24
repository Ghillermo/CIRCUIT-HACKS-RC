"""Circuit Tracks 4486 - RC4.23 (marker "R423") = RC4.22 + tools/noinapp.py (a fix: the running firmware ignores an install; only the
bootloader takes one. Installs sent to a running unit wrote over the internal file system on the user's Circuit, 2026-11-24)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import noinapp
    noinapp.use()
    import build_r422 as R
    src = Path(R.__file__).read_text(encoding="utf-8")
    assert src.count('"R422"') == 2, "R422 marker strings"
    src = src.replace('"R422"', '"R423"')
    sys.argv = [R.__file__] + sys.argv[1:]
    exec(compile(src, R.__file__, "exec"), {"__name__": "__main__", "__file__": R.__file__})
