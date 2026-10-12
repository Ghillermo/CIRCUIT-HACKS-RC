"""Circuit Tracks 4486 — SC16.1 = SC16 + line input v2 (+6 dB, phase-inverted modes): see linein2.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc15 as s15  # noqa: E402
import build_sc16 as s16  # noqa: E402
import linein2  # noqa: E402

linein2.install(s15, s16)

if __name__ == "__main__":
    linein2.main("SC16.1", s16.build, s15, sys.argv[1:])
