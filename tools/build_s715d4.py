"""Circuit Tracks 4486 - S715D4 (diagnostic, marker "S715D4") = S715D3 + patchain.use_rangefix(): the fix of the root cause S715D3 found (c_pcnext
chose pattern 8 for a track playing outside its stock chain).  stepcatch and the DWT watch stay: a scene stress run on the device should now
capture nothing."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import patchain
    patchain.use_rangefix()
    import build_s715d3 as S
    src = Path(S.__file__).read_text(encoding="utf-8")
    assert src.count('"S715D3"') == 2, "S715D3 marker lines"
    src = src.replace('"S715D3"', '"S715D4"')
    sys.argv = [S.__file__] + sys.argv[1:]
    exec(compile(src, S.__file__, "exec"), {"__name__": "__main__", "__file__": S.__file__})
