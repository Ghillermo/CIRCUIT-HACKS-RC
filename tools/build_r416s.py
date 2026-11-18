"""Circuit Tracks 4486 - RC4.16S (marker "R416S") = RC4.15S + sampler_dsp.use_noplayrec() (the user, 2026-11-18: «Fix sample capture and playback»,
«A for the RC»): while pad 32 records, nothing starts the sample's playback (pad 7, a latched loop, a Master FX slot, the FX sequencer): it used to
play the take being written, its start and end moving with it."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sampler_dsp  # noqa: E402
sampler_dsp.use_noplayrec()
import fixes704  # noqa: E402
fixes704.rc()                                             # + the pending fixes: patchain's LED-task stack, the scene clear (sclear2)
import build_r415s as S  # noqa: E402
import linein3  # noqa: E402

NAME = "R416S"
B = S.B

if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    def ext(img, report):
        S.S.extra(img, report)
        fixes704.extra_rc(img, report)
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=ext)
