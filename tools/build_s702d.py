"""Circuit Tracks 4486 - S702D (diagnostic, marker "S702D") = Alpha 7.02 without the FM algorithm map (room, as S564D4) + blackbox.use_memrd
(live memory reads over USB: tools/bbread.py / tools/perfread.py): the Cortex-M7 cache state (SCB CCR), the flash wait states / ART (FLASH ACR),
the clocks (RCC), for the performance study (the user, 2026-11-17: «is there other performance options we could check?»)."""
import runpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_beta5_65 as A  # noqa: E402
import build_sc56_3  # noqa: E402

NAME = "S702D"

if __name__ == "__main__":
    A.S.options()
    build_sc56_3.DROP_FMMAP = True
    import blackbox
    blackbox.use_showall()
    blackbox.use_memrd()
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
            dspz.add(img, report, "patpass", patpass, gap=1)
        return _real(NAME, build, s15, argv, extra=ext)
    linein3.main = _named
    sys.argv = [str(Path(__file__).resolve().parent / "build_beta5_63.py")] + sys.argv[1:]
    runpy.run_path(sys.argv[0], run_name="__main__")
