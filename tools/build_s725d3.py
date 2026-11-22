"""Circuit Tracks 4486 - S725D3 (diagnostic, marker "S725D3") = S725D (Alpha 7.25 + usbtrap: all of the USB drive's leftover code trapped, the
backup SRAM probe, memrd, sxpanel) + msdcut.use_midionly() (the fix: USB MIDI only, the drive class never registered).  No capture = the drive
code is dead now."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import msdcut
    msdcut.use_midionly()
    here = Path(__file__).resolve().parent / "build_s725d.py"
    src = here.read_text(encoding="utf-8")
    assert src.count('"S725D"') == 2
    src = src.replace('"S725D"', '"S725D3"')
    exec(compile(src, str(here), "exec"), {"__name__": "__main__", "__file__": str(here)})
