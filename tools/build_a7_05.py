"""Circuit Tracks 4486 - Alpha 7.05 (marker "A7.05") = Alpha 7.04 + poly.use_quarter() (with 4+ FM voices on a track, each voice updated every 4 ms
instead of 2: fewer SPI writes to the DSP; the user, 2026-11-18: «do it all»)."""
import runpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import poly  # noqa: E402

if __name__ == "__main__":
    poly.use_quarter()
    import dspz
    dspz.use_move("jumprnd", 1)                            # (room: gap 1 is full: with dspz.use_spill it goes to the image's end)
    import build_a7_04 as A4
    src = Path(A4.__file__).read_text(encoding="utf-8")
    src = src.replace("Path(A3.__file__).read_text(encoding=\"utf-8\").replace('NAME = \"A7.03\"', 'NAME = \"A7.04\"')",
                      "Path(A3.__file__).read_text(encoding=\"utf-8\").replace('NAME = \"A7.03\"', 'NAME = \"A7.05\"')")
    assert '"A7.05"' in src
    sys.argv = [A4.__file__] + sys.argv[1:]
    exec(compile(src, A4.__file__, "exec"), {"__name__": "__main__", "__file__": A4.__file__})
