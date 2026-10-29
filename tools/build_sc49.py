"""Circuit Tracks 4486 - SC49 = SC48.9 with the mod's dead code left out, to make room for the extra drum lane (the user, 2026-10-28: «Do it»:
the flash pass).  Found on SC48.9's image (no branch, word or movw / movt pair reaches them, not even from other dead code): packio's old
cross-pack swaps (c_xswap, c_xswap2; c_xcopy2 replaced them), SC08's c_dpad / c_shbtn (SC11's c_dpad2 / c_shbtn2 took both hooks), the CC editor
v1 (c_edfield, c_edknob, c_edcyc; v2 runs), Nudge v1 (c_pmnudge; c_pmnudge2 runs), drums18's c_dtick / c_dleds18 (persist19 took both hooks).
«SC48.10» would be cut to «SC48.1»: SC49."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc48_9 as B  # noqa: E402
import packio  # noqa: E402
import build_sc08  # noqa: E402
import vcf21  # noqa: E402
import playmode  # noqa: E402
import drums18  # noqa: E402
packio.use_trimx()                                   # the old cross-pack swaps
build_sc08.use_trim()                                # SC08's c_dpad / c_shbtn
vcf21.use_trimed()                                   # the CC editor v1
playmode.use_trimnu()                                # Nudge v1
drums18.use_trim()                                   # drums18's c_dtick / c_dleds18
import linein3  # noqa: E402

NAME = "SC49"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
