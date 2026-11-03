"""Circuit Tracks 4486 - S494D2 (DIAGNOSTIC) = S494D + rdiag.ITEXEC: order 15 (ctremote.py itexec) writes a 3-instruction routine at the end of the ITCM,
runs it with blx and puts the two words back, so the PC sees whether the ITCM can hold code (Arrhythmia, llcoolkm, MIT, loads its modules there on
the Circuit Rhythm).  ("S494D.2" would be cut to "S494D." : S494D2.)  See firmware/s494d2/PRUEBA.md."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_s494d as S  # noqa: E402
import rdiag  # noqa: E402
rdiag.ITEXEC = True
import linein3  # noqa: E402

NAME = "S494D2"

if __name__ == "__main__":
    B = S.B
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=S.extra)
