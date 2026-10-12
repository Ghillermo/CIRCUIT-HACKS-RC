"""Circuit Tracks 4486 — SC25 = SC24 + (2026-10-07, from the conversation about CC and the sequencer):
  * the template row (pads 1-8) of the MIDI Preset view comes back when the VCA-VCF mode is turned off with pad 27 (SC24 left it dark: the page row had overwritten it);
  * MIDI out: every value of the mode that a knob changes (and Clear) goes out as CC on the channel of the track: the CC numbers of the stock synth where the function is the same
    (CC 74 filter, 71 resonance, 79 env -> filter, 73 / 75 / 70 / 72 ADSR, 91 FX amount, 59 gain, 26 / 27 tune / fine, 20 / 21 wave / pulse width, 37 / 39 / 30 / 31 / 52 / 54 of the second
    oscillator, mix and ring), NRPN 4:code (and the stock 0:76 of the LFO rate) for the rest; through the stock template CC helper, so the Setup CC Tx filter and the internal loopback of
    SC05 apply;
  * MIDI in: the same CC / NRPN on the channel of a MIDI track whose mode is on set the values (Setup CC Rx on);
  * automation: 8 values are recorded by the sequencer and played back through the macro lanes 0..7 of the track (lane 0 = TUNE, then REL, ENVA, ENVF, FILT, RES, LRATE, FXAMT).
No new RAM: the tables are in flash, the NRPN select state of the incoming CCs is kept in the stock record of the 'other' channels."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc24 as b24  # noqa: E402
import vcf21  # noqa: E402
import linein3  # noqa: E402
vcf21.use_tdraw()
vcf21.use_ccio()

NAME = "SC25"
extra = b24.extra

if __name__ == "__main__":
    b5 = b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
