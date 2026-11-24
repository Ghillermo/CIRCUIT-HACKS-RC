"""Circuit Tracks 4486 - Alpha 7.50 (marker "A7.50") = Alpha 7.49 + novasec.use_v10() + modmx.use_famcol() (the user, 2026-11-24: Synth 1 / 2's section
pages laid out like the own synth's (pads 2 OSC 1, 3 OSC 2, 4 VCA-VCF-FX, 5 Mod sources, 6 matrix, 7 FX), Shift layers, colours by family; the
matrix: each source / destination its own colour and brightness step, the depth in the destination's colour, pads 9-24 = the slots; the own synth's
matrix destinations in their family colours)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import novasec, modmx, mixsolo
    novasec.use_v10()
    modmx.use_famcol()
    mixsolo.use_trim2()                                # (room) the old solo's three bodies, dead since mixsolo4 / 5
    import build_a7_49 as A49
    src = Path(A49.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.49"') == 2, "A7.49 marker strings"
    src = src.replace('"A7.49"', '"A7.50"')
    sys.argv = [A49.__file__] + sys.argv[1:]
    exec(compile(src, A49.__file__, "exec"), {"__name__": "__main__", "__file__": A49.__file__})
