"""Circuit Tracks 4486 - S725D2 (diagnostic, marker "S725D2") = S725D with usbtrap.use_live(): the drive class's DeInit (called by the USB stack
when the connection is set up, also in MIDI mode: S725D trapped there) left as it is."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import usbtrap
    usbtrap.use_live()
    src = (Path(__file__).resolve().parent / "build_s725d.py").read_text(encoding="utf-8")
    assert src.count('"S725D"') == 2
    src = src.replace('"S725D"', '"S725D2"')
    exec(compile(src, str(Path(__file__).resolve().parent / "build_s725d.py"), "exec"), {"__name__": "__main__", "__file__": str(Path(__file__).resolve().parent / "build_s725d.py")})
