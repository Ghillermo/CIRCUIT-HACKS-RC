"""Circuit Tracks 4486 - SC57.9 = SC57.8 + the FX sequencer's mute step (masterfx_dsp / build_sc17 / vcf21 use_fsqmute()) and the fix of the 5.63
chain crash (fixes564); = Beta 5.64 with the SC marker.

Built on top of tools/build_sc57_8.py by import (its main block runs here with this marker), so any later change to it follows."""
import runpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc57_8 as S  # noqa: E402
import build_beta5_64 as B64  # noqa: E402

NAME = "SC57.9"
B = S.B


if __name__ == "__main__":
    B64.options()
    import linein3
    _real = linein3.main                                   # the parent's main block wraps linein3.main with its own marker: ours goes underneath
    def _named(name, build, s15, argv, extra=None): return _real(NAME, build, s15, argv, extra=extra)
    linein3.main = _named
    sys.argv = [str(Path(__file__).resolve().parent / "build_sc57_8.py")] + sys.argv[1:]
    runpy.run_path(sys.argv[0], run_name="__main__")
