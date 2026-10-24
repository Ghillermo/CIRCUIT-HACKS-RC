"""Circuit Tracks 4486 - SC46.1 = SC46 + two fixes: (1, also in RC2.07) the fixed length of step entry (stepgate.use_v4): the Micro Step view redrawn by the stock after the selector (its LEDs were left as the
selector had drawn them), and the length set as each note is added (all of a chord's notes, whatever pad is let go first); (2, the beta only:
the synced LFO is the beta's) vcf21_dsp / modmx use_shsync(): the sample & hold shapes of the engine's LFO and of the matrix's LFO 2 take new values
with the LFO synced and the transport running (the cycle's start set by the tick was not seen as a wrap)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc46 as B  # noqa: E402
import stepgate  # noqa: E402
stepgate.use_v4()
import vcf21_dsp  # noqa: E402
vcf21_dsp.use_shsync()
import modmx  # noqa: E402
modmx.use_shsync()
import linein3  # noqa: E402

NAME = "SC46.1"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
