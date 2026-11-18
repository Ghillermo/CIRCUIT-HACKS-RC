"""Circuit Tracks 4486 - S703D (diagnostic, marker "S703D") = Alpha 7.03 without the FM algorithm map (room, as S702D) + the hardware study
(the user, 2026-11-18: «make a diag build for all those»: clock tree, DMA / data cache, cycle counter, CRC, RNG, backup SRAM, NOR):
  * blackbox.use_memrd() + use_memrdw(): live reads, also whole words (peripheral registers without their data registers): tools/hwdiag.py;
  * icache.use_dwt(): the cycle counter on at power-up;
  * blackbox.use_samp(): at every SysTick the running task and the interrupted PC (task shares, hot code);
  * tools/cwatch.py (as S579D, the user: «Bake it into s703D»): the black box frozen (Save violet) the moment a drum velocity bar's vtable word
    changes: the gestures before the Beta 5.63 one-byte write."""
import runpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_beta5_65 as A  # noqa: E402

NAME = "S703D"

if __name__ == "__main__":
    A.S.options()
    import blackbox
    blackbox.use_showall()
    blackbox.use_memrd(); blackbox.use_memrdw(); blackbox.use_samp()
    import build_sc56_3, icache
    build_sc56_3.DROP_FMMAP = True
    icache.use_dwt()
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
            import cwatch
            dspz.add(img, report, "cwatch", cwatch)              # S579D's watcher of the drum velocity bars' vtables (the 5.63 byte)
        return _real(NAME, build, s15, argv, extra=ext)
    linein3.main = _named
    sys.argv = [str(Path(__file__).resolve().parent / "build_beta5_63.py")] + sys.argv[1:]
    runpy.run_path(sys.argv[0], run_name="__main__")
