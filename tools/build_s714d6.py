"""Circuit Tracks 4486 - S714D6 (diagnostic, marker "S714D6") = S714D3 + blackbox.use_safeclear() (the clear no longer zeroes the LED head's live
LR / frame: the stress runs' «crashes» at PC 0 were the tool's own clears)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import blackbox
    blackbox.use_safeclear()
    import build_s714d3 as S
    src = Path(S.__file__).read_text(encoding="utf-8")
    assert src.count('"S714D3"') == 2, "S714D3 marker lines"
    src = src.replace('"S714D3"', '"S714D6"')
    sys.argv = [S.__file__] + sys.argv[1:]
    exec(compile(src, S.__file__, "exec"), {"__name__": "__main__", "__file__": S.__file__})
