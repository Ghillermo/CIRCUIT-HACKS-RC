"""Circuit Tracks 4486 - Alpha 7.02 (marker "A7.02") = Alpha 7.01 + pattern data that follows the pattern that plays, with chains and pattern
mutate (the user, 2026-11-17: «Make pattern related data, like lanex, follows the current pattern at play, even with pattern chain and pattern
mutate»; «Dead code + tables», «Alpha 7.02 only», «Apply late»):
  * drumpat.use_patpass(): the drums' frequency («1 in N») counts the passes of each pattern (before: one count a drum, back to 0 at every
    pattern change, so a chain A -> B -> A played A's «1 in 2» every time);
  * xlanes.use_late(): MIDI 1 / 2's extra lanes of a pattern that has just started play on the micro step after their block is read from the DSP,
    not half a step later;
  * lanex.use_patmask(): the drum extra lane's pattern & 7.
Built on top of tools/build_a7_01.py (its options, its chain) with this marker."""
import runpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_beta5_65 as A  # noqa: E402

NAME = "A7.02"

if __name__ == "__main__":
    A.S.options()
    import blackbox
    blackbox.use_showall()
    import drumpat
    import lanex
    import xlanes
    drumpat.use_patpass()
    lanex.use_patmask()
    xlanes.use_late()
    import linein3
    _real = linein3.main
    def _named(name, build, s15, argv, extra=None):
        def ext(img, report):
            if extra: extra(img, report)
            A.extra_565(img, report)
            import dspz
            import patpass
            dspz.add(img, report, "patpass", patpass, gap=1)   # drumpat's per-pattern counts reset
        return _real(NAME, build, s15, argv, extra=ext)
    linein3.main = _named
    sys.argv = [str(Path(__file__).resolve().parent / "build_beta5_63.py")] + sys.argv[1:]
    runpy.run_path(sys.argv[0], run_name="__main__")
