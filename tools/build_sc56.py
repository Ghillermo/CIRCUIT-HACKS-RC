"""Circuit Tracks 4486 - SC56 = SC55.9 with more room in the flash and nothing changed in use (the user, 2026-11-10: «build 1 and then 2»;
«SC55.10» would be cut to «SC55.1»):
  * dspz.use_v2(): the two DSP programs packed with LZ + range coding instead of LZSS (32 646 -> about 26 800 B; the decoder 792 B);
  * code that nothing reached any more left out: mixsolo v1 (use_trim1), velcurve's knob, number and curve helpers (use_trimall; c_vcadv stays),
    the morph's panel Octave (morphz.use_trimpanel, never called with use_nocur)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc55_9 as S  # noqa: E402
import linein3  # noqa: E402
import patmut  # noqa: E402
import tabpack  # noqa: E402

NAME = "SC56"
B = S.B
extra = S.extra


def room():
    import dspz, mixsolo, velcurve, morphz
    dspz.use_v2(); mixsolo.use_trim1(); velcurve.use_trimall()
    morphz.use_nocur(); morphz.use_trimpanel()


if __name__ == "__main__":
    tabpack.use()
    patmut.use_v2()
    room()
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
