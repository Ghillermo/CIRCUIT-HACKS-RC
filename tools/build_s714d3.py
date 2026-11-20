"""Circuit Tracks 4486 - S714D3 (diagnostic, marker "S714D3") = S714D2 + blackbox.use_keepstall(400): a pause of the panel's main loop longer than
400 ms freezes the black box and stays (with the running task's PC / LR every 50 ms), to see where the stress run's ~1 s pauses go."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import blackbox
    blackbox.use_keepstall(400)
    import build_s714d2 as S
    src = Path(S.__file__).read_text(encoding="utf-8")
    assert src.count('"S714D2"') == 2, "S714D2 marker lines"
    src = src.replace('"S714D2"', '"S714D3"')
    sys.argv = [S.__file__] + sys.argv[1:]
    exec(compile(src, S.__file__, "exec"), {"__name__": "__main__", "__file__": S.__file__})
