"""Circuit Tracks 4486 - Alpha 7.26 (marker "A7.26") = Alpha 7.25 + msdcut.use_midionly() (a fix: Alpha 7.21-7.25 forced Easy Start ON, the
Tracks showing up as MIDI + a USB drive without its disk handler; now USB MIDI only, the stock's Easy Start off path; S725D4 on the device)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import msdcut
    msdcut.use_midionly()
    import build_a7_25 as A25
    src = Path(A25.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.25"') == 2, "A7.25 marker lines"
    src = src.replace('"A7.25"', '"A7.26"')
    sys.argv = [A25.__file__] + sys.argv[1:]
    exec(compile(src, A25.__file__, "exec"), {"__name__": "__main__", "__file__": A25.__file__})
