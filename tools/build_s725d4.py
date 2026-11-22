"""Circuit Tracks 4486 - S725D4 (diagnostic, marker "S725D4") = S725D3 with usbtrap.use_prologue(): the drive transport's first 20 B (called by
the main loop in MIDI mode too; they return when no drive is active) left as they are."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import usbtrap
    usbtrap.use_prologue()
    here = Path(__file__).resolve().parent / "build_s725d3.py"
    src = here.read_text(encoding="utf-8")
    assert src.count('"S725D3"') == 2
    src = src.replace('"S725D3"', '"S725D4"')
    exec(compile(src, str(here), "exec"), {"__name__": "__main__", "__file__": str(here)})
