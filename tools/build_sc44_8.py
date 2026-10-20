"""Circuit Tracks 4486 - SC44.8 = SC44.7 + vcf21_dsp / vcf21 use_lfosync() + tools/lfosync.py in the dead DSP blocks of the stock image (hole.py)
(the user, 2026-10-19: «en los lfo rate, hazlo bipolar (manten 0 dim y lados bright) hacia la derecha, lfo libre, izquierda, lfo a tempo con sync en
beat 1»; the divisions with their triplets, 1/16T .. 8 bars): the own engine's LFO rate of MIDI 1 / 2 bipolar, and the matrix's LFO 2
(modmx.use_sync: each shape's zone, the lower half synced), the drums' (drums2_dsp.use_lfosync) and Master FX's Auto-Filter / Phaser
(build_sc17.use_lfosync); modmx and split4 move to the hole too (flash for what follows)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc41_5 as B5  # noqa: E402
B5.HOLE |= {"modmx", "split4"}                       # (no card writes, no settings save: hole.py)
import build_sc44_7 as B  # noqa: E402
import vcf21_dsp  # noqa: E402
import vcf21  # noqa: E402
vcf21_dsp.use_lfosync()
import drums2_dsp  # noqa: E402
drums2_dsp.use_lfosync()
vcf21.use_lfosync()                                  # (after the chain: use_neutral sets DEFAULTS)
import modmx  # noqa: E402
modmx.use_sync()
import build_sc17 as S17  # noqa: E402
import lfosync as LF0  # noqa: E402
S17.use_lfosync(LF0.RAM + 48)                       # the Auto-Filter's and the Phaser's rates (after lfosync's 6 slots)
import countin  # noqa: E402
countin.use_bpm0()                                   # (a fix: the count-in from the project's tempo, p0)
import hole  # noqa: E402
import lfosync  # noqa: E402
import linein3  # noqa: E402

NAME = "SC44.8"


def extra(img, report):
    B.extra(img, report)
    hole.add(img, report, "lfosync", lfosync)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
