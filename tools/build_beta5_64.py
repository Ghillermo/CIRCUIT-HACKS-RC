"""Circuit Tracks 4486 - Beta 5.64 (marker "B5.64") = Beta 5.63 + the FX sequencer's mute step (the user, 2026-11-15: «add one option to the fx
sequencer: mute» -> «mute whole master per step»; masterfx_dsp / build_sc17 / vcf21 use_fsqmute(): the eighth value of the selector knob = FX_ON bit 7
= the master output faded to silence for the step, 2 ms edges, red LED) and the fix of the 5.63 crash when making a pattern-group chain (fixes564,
see docs/NOTAS.md, «Beta 5.64»).

Built on top of tools/build_beta5_63.py by import (its main block runs here with this marker), so any later change to it follows."""
import runpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_beta5_63 as S  # noqa: E402
import masterfx_dsp  # noqa: E402
import build_sc17  # noqa: E402
import vcf21  # noqa: E402
import fixes564  # noqa: E402

NAME = "B5.64"
B = S.B


def options():
    masterfx_dsp.use_fsqmute(); build_sc17.use_fsqmute(); vcf21.use_fsqmute()
    fixes564.beta()


if __name__ == "__main__":
    options()
    import linein3
    _real = linein3.main                                   # the parent's main block wraps linein3.main with its own marker: ours goes underneath
    def _named(name, build, s15, argv, extra=None): return _real(NAME, build, s15, argv, extra=extra)
    linein3.main = _named
    sys.argv = [str(Path(__file__).resolve().parent / "build_beta5_63.py")] + sys.argv[1:]
    runpy.run_path(sys.argv[0], run_name="__main__")
