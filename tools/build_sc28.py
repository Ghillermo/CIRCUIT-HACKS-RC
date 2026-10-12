"""Circuit Tracks 4486 — SC28 = SC27 + MIDI for the parameters of our patches that had none (2026-10-07; tools/nrpn28.py):
  * drums: the knobs added by SC18.1 / SC19.9 go out and come in as NRPN on the drums channel: MSB 5..8 = Drum 1..4, LSB 1..8 = pitch envelope, ring mod frequency, LFO amount, LFO speed,
    env -> cutoff, resonance, envelope shape, ring mod amount; 9 = filter mode (0..4), 10 = start point (0..15), 11 = bitcrush (0..15), 12 = distortion type (0..3);
  * Master FX: the 20 parameters (5 sets x 4 knobs) as NRPN MSB 9, LSB = 4 x set + knob on channel 16.
The stock NRPN handler ignores those numbers.  Out through the template CC helper (the Setup CC Tx filter applies), in behind the Setup CC Rx filter.  No RAM, no DSP change."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc27 as b27  # noqa: E402
import nrpn28  # noqa: E402
import linein3  # noqa: E402

NAME = "SC28"


def extra(img, report):
    b27.extra(img, report)
    import ct_fw
    ext = (len(img) + ct_fw.APP_BASE + 3) & ~3
    labels, code = nrpn28.install(img, report, ext)
    report["nrpn28"] = dict(arm_start=hex(ext), size=len(code), labels={k: hex(v) for k, v in labels.items()})


if __name__ == "__main__":
    b5 = b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
