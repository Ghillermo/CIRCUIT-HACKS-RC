"""Circuit Tracks 4486 - Alpha 7.23 (marker "A7.23") = Alpha 7.22 + vcf21.use_fold2() (flash room, nothing new in use: the CC editor's LED
clearing in loops)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import vcf21
    vcf21.use_fold2()
    import build_a7_22 as A22
    src = Path(A22.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.22"') == 2, "A7.22 marker lines"
    src = src.replace('"A7.22"', '"A7.23"')
    sys.argv = [A22.__file__] + sys.argv[1:]
    exec(compile(src, A22.__file__, "exec"), {"__name__": "__main__", "__file__": A22.__file__})
