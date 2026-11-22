"""Circuit Tracks 4486 - Alpha 7.24 (marker "A7.24") = Alpha 7.23 + build_sc17.use_fold2(), drumstore / throw / modmx use_fold() (flash room,
nothing new in use: unrolled code as loops / tables: c_fsqfx's Glitch-knob copies, c_s_leds' copy, c_gleds' colours, the drum edit-store
sync of rollers / drumarp, c_thon's sends, c_mxst's defaults)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import vcf21, build_sc17, drumstore, throw, modmx
    vcf21.use_fold2()                                  # (Alpha 7.23)
    build_sc17.use_fold2()
    drumstore.use_fold()
    throw.use_fold()
    modmx.use_fold()
    # persist19.use_fold(): written (c_mhleds19's Clear feedback, c_dk19's lookups as a table: ~110 B), not tested yet
    import build_a7_22 as A22
    src = Path(A22.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.22"') == 2, "A7.22 marker lines"
    src = src.replace('"A7.22"', '"A7.24"')
    sys.argv = [A22.__file__] + sys.argv[1:]
    exec(compile(src, A22.__file__, "exec"), {"__name__": "__main__", "__file__": A22.__file__})
