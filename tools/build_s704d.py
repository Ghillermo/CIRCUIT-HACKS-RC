"""Circuit Tracks 4486 - S704D (diagnostic, marker "S704D") = Alpha 7.04 + S703D's study (the user, 2026-11-18: «flash and test»): live reads
(blackbox.use_memrd / use_memrdw: tools/hwdiag.py), the cycle counter (icache.use_dwt), the SysTick task sampler (blackbox.use_samp) and
S579D's watcher of the drum velocity bars' vtables (tools/cwatch.py).  DROP_FMMAP = True drops the FM algorithm map for room when it does not fit."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sampler_dsp  # noqa: E402

DROP_FMMAP = "--dropmap" in sys.argv

if __name__ == "__main__":
    if DROP_FMMAP: sys.argv.remove("--dropmap")
    sampler_dsp.use_overdub()
    import fixes704, blackbox, icache
    fixes704.alpha()
    blackbox.use_memrd(); blackbox.use_memrdw(); blackbox.use_samp(); icache.use_dwt()
    if DROP_FMMAP:
        import build_sc56_3
        build_sc56_3.DROP_FMMAP = True
    import build_a7_03 as A3
    src = Path(A3.__file__).read_text(encoding="utf-8").replace('NAME = "A7.03"', 'NAME = "S704D"')
    ic = '            dspz.add(img, report, "icache", icache)'
    src = src.replace(ic, ic + "\n            fixes704.extra_alpha(img, report)\n            import cwatch\n            dspz.add(img, report, \"cwatch\", cwatch)")
    assert "cwatch" in src
    sys.argv = [A3.__file__] + sys.argv[1:]
    exec(compile(src, A3.__file__, "exec"), {"__name__": "__main__", "__file__": A3.__file__, "fixes704": fixes704})
