"""Circuit Tracks 4486 — SC23.5 = SC23.4 + (2026-10-06, after testing):
  * the Save button of the top row (panel LED 57) blinks with the Save pad at the save step of the CC editor (`vcf21.use_saveled()`);
  * Master FX pad 8 is exactly the FX view's bypass pad (`build_sc17.use_clear_copy()`);
  * the song pointer playhead comes from the sequencer tick hook, 16 steps linearly (`build_sc17.use_spcache()`);
  * mailbox: at most one message per voice every 2 ms (`vcf21.use_ratelimit()`: the DSP reads once per block, only the last write of a block survives);
  * gate path robustness: heartbeat of ACT / NOTE / VEL / GATE from the ARM (`vcf21.use_heartbeat()`), a high gate with the envelope idle starts it (`vcf21_dsp.use_gatefix()`);
  * Clear + a knob resets both layers of the knob (`vcf21.use_clearboth()`);
  * drum K8: brightness = max(distortion, bitcrush): dimmest with no effect, brighter either way (`persist19.K8_BRIGHT`).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc23_4 as b234  # noqa: E402
import vcf21  # noqa: E402
import vcf21_dsp  # noqa: E402
import build_sc17 as B17  # noqa: E402
import persist19  # noqa: E402
import linein3  # noqa: E402
vcf21.use_saveled()
vcf21.use_ratelimit()
vcf21.use_heartbeat()
vcf21.use_clearboth()
vcf21_dsp.use_gatefix()
B17.use_clear_copy()
B17.use_spcache()
persist19.K8_BRIGHT = True
persist19.CLEAR_BOTH = True
b223 = b234.b223

NAME = "SC23.5"
extra = b234.extra

if __name__ == "__main__":
    linein3.main(NAME, b223.b22.b182.b18.b6.b5.build, b223.b22.b182.b18.b6.b5.s15, sys.argv[1:], extra=extra)
