"""Circuit Tracks 4486 - RC4.21 (marker "R421") = RC4.20 + patchain.use_rangefix() (a fix, found on the device by S715D3: c_pcnext chose the
pattern after the current one when the current one was outside the track's stock chain, so a track left on pattern 7 by a chain rule went to a
pattern 8 that does not exist; the advance then wrote a play step of 240 and the stock view code wrote past its array: the Beta 5.63 crash)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import patchain
    patchain.use_rangefix()
    import build_r420 as R
    src = Path(R.__file__).read_text(encoding="utf-8").replace('"R420"', '"R421"')
    sys.argv = [R.__file__] + sys.argv[1:]
    exec(compile(src, R.__file__, "exec"), {"__name__": "__main__", "__file__": R.__file__})
