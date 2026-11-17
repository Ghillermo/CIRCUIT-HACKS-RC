"""Circuit Tracks 4486 - RC4.15 (marker "R415S") = RC4.14 + the slot-7 vtable guards of the 2026-11-15 crash hunt (rollers / drumnote use_vtguard: the
drum Note view's slot 7, called by a store commit through a listener whose vtable word had been overwritten, no longer touches [[this + 4]]) and the
SC49 / SC49.3 dead-code trims the RC chain never had (packio.use_trimx, drums18.use_trim, vcf21.use_trimed, playmode.use_trimnu, build_sc15.use_trim:
unreachable code, nothing changes in use; about 2 KB of flash back) (RC4.15S: nothing of ours writes to the card).  tools/fixes564.rc()."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_r414s as S  # noqa: E402
import fixes564  # noqa: E402
import linein3  # noqa: E402

NAME = "R415S"
B = S.B
fixes564.rc()                                             # (before the build: the trims and the guards are module flags)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=S.extra)
