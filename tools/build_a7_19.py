"""Circuit Tracks 4486 - Alpha 7.19 (marker "A7.19") = Alpha 7.18 with more flash room (the user, 2026-11-20: «Keep cleaning up unused code,
optimizing repeating code and compressing/packing to make more flash room»), nothing new in use: unrolled code folded into loops
(packio.use_zloop / xlanes.use_zloop: the request frames zeroed by a loop; vcf21.use_defloop: the default values from the t_def table; vcf21.use_fold: the Clear LEDs, the destination rows' first fill and the state bytes as loops; build_sc17.use_fold: c_slotbits' slot tests as a loop, c_f_leds' palette chain as a table)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import packio
    import xlanes
    import vcf21
    import build_sc17
    packio.use_zloop()
    xlanes.use_zloop()
    vcf21.use_defloop()
    vcf21.use_fold()
    build_sc17.use_fold()
    import build_a7_18 as A18
    src = Path(A18.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.18"') == 2, "A7.18 marker lines"
    src = src.replace('"A7.18"', '"A7.19"')
    sys.argv = [A18.__file__] + sys.argv[1:]
    exec(compile(src, A18.__file__, "exec"), {"__name__": "__main__", "__file__": A18.__file__})
