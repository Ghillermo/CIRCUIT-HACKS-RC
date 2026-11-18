"""Circuit Tracks 4486 - Alpha 7.03 (marker "A7.03") = Alpha 7.02 + the instruction cache on at power-up (the user, 2026-11-18: S702D3 on the
device, «doesnt seem to slow down now»: the tempo drag with 6 voices of the 8-operator FM gone; «lets make room»):
  * tools/icache.py: the Cortex-M7's I-cache on in the stock's FPU set-up at reset (S702D read it off at 120 MHz; the app runs from flash over
    AXI, so every fetch waited for the flash);
  * room for it: morphz.use_trimnc() (the morph's initial-patch place code, never run with use_nocur: 120 B);
  * no external input to the Nova synths (the user: «erase 25,26,27,28 and 29, and their corresponding code», «drop external input to nova»):
    build_sc15 / srcview / linein3 use_nosrc(): the source view's pads 25-29 dark and inert, the DSP's input hook and its ARM mode writes gone
    (the Setup's FX-return capture for the MIDI tracks' feedback stays).
Built on top of tools/build_a7_02.py's options and chain with this marker."""
import runpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_beta5_65 as A  # noqa: E402

NAME = "A7.03"

if __name__ == "__main__":
    A.S.options()
    import blackbox
    blackbox.use_showall()
    import drumpat
    import lanex
    import xlanes
    import morphz
    drumpat.use_patpass()
    lanex.use_patmask()
    xlanes.use_late()
    morphz.use_trimnc()
    import build_sc15, srcview, linein3 as LI3
    build_sc15.use_nosrc(); srcview.use_nosrc(); LI3.use_nosrc()
    import dspz
    dspz.use_spill()
    import linein3
    _real = linein3.main
    def _named(name, build, s15, argv, extra=None):
        def ext(img, report):
            if extra: extra(img, report)
            A.extra_565(img, report)
            import dspz
            import patpass
            import icache
            dspz.add(img, report, "patpass", patpass, gap=1)   # drumpat's per-pattern counts reset
            dspz.add(img, report, "icache", icache)
        return _real(NAME, build, s15, argv, extra=ext)
    linein3.main = _named
    sys.argv = [str(Path(__file__).resolve().parent / "build_beta5_63.py")] + sys.argv[1:]
    runpy.run_path(sys.argv[0], run_name="__main__")
