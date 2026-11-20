"""Circuit Tracks 4486 - Alpha 7.17 (marker "A7.17") = Alpha 7.16 + build_sc17.use_trimslc() (unused code out: the old FX sequencer's slot
colour, 106 B; the user: «Drop unused code first») + patchain.use_keep46() (Clear + pattern keeps the settings bytes 4..6, unused with the group
chains) + gmview.use_rows() (the global macro view's pads 9-16 / 17-24 / 25-32 = each track's Mixer level / reverb send / delay send; the user:
«Add level, reverb, delay»)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import build_sc17
    import patchain
    import gmview
    build_sc17.use_trimslc()
    patchain.use_keep46()
    gmview.use_rows()
    import build_a7_16 as A16
    src = Path(A16.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.16"') == 2, "A7.16 marker lines"
    src = src.replace('"A7.16"', '"A7.17"')
    sys.argv = [A16.__file__] + sys.argv[1:]
    exec(compile(src, A16.__file__, "exec"), {"__name__": "__main__", "__file__": A16.__file__})
