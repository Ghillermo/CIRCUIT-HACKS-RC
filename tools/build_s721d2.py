"""Circuit Tracks 4486 - S721D2 (diagnostic, marker "S721D2") = S721D without the traps on code the boot reaches through its
self-relative tables (stocktrap.use_boot(): the C runtime's zero-init 0x0801A7EA, where S721D trapped and never came up on USB, and the C++
static constructors with what they call): 8 runs, 348 B + the cut disk handler's end, 36 B."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import stocktrap
    stocktrap.use_boot()
    import build_s721d as D
    src = Path(D.__file__).read_text(encoding="utf-8")
    assert src.count('"S721D"') == 2, "S721D marker lines"
    src = src.replace('"S721D"', '"S721D2"')
    sys.argv = [D.__file__] + sys.argv[1:]
    exec(compile(src, D.__file__, "exec"), {"__name__": "__main__", "__file__": D.__file__})
