"""Circuit Tracks 4486 - SC53 = SC52.9 + the FM instruments' second page (the user, 2026-11-07: «Pon algunos parches demo del FM más largos, como
strings y winds, también algún piano»; «Segunda página con Octave»; «Cuerdas, Vientos, Pianos, Alargar los actuales»): fm8ui.use_inst2 (pad 8 held +
Octave = page 1 / 2; the 48 records packed, unpacked into the ITCM) with fm8inst.use_v2 (24 new: pianos, strings, winds, long ones; longer releases on
page 1).  («SC52.10» would be cut to «SC52.1».)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc52_9 as S  # noqa: E402
import linein3  # noqa: E402

NAME = "SC53"
B = S.B
extra = S.extra
import fm8ui  # noqa: E402
fm8ui.use_inst2()


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
