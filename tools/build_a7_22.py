"""Circuit Tracks 4486 - Alpha 7.22 (marker "A7.22") = Alpha 7.21 + projinit.use_clear() (the user, 2026-11-21: Clear + Synth 1 / 2 or MIDI 1 / 2
= the sound saved in the project; Shift + Preset = the preset's initial state: the swap of the two)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import projinit
    import clrtrk
    projinit.use_clear()
    clrtrk.use_callable()
    import build_a7_21 as A21
    src = Path(A21.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.21"') == 2, "A7.21 marker lines"
    src = src.replace('"A7.21"', '"A7.22"')
    sys.argv = [A21.__file__] + sys.argv[1:]
    exec(compile(src, A21.__file__, "exec"), {"__name__": "__main__", "__file__": A21.__file__})
