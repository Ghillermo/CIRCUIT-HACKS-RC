"""Circuit Tracks 4486 — SC23.3 = SC23.2 + the neutral default state of the VCA / VCF and oscillator modes, Clear + knob, and the Octave LEDs of the CC editor.

  * defaults (`vcf21.use_neutral()`): filter open, no resonance, envelope -> VCA at the maximum scaled by the velocity, sustain maximum, attack / decay / release 0 (release 0 = ~2 ms: `vcf21_dsp.use_gaterel()`),
    no LFO, no FX, the VCA closed without the envelope: pressing a key opens the sound, releasing it closes it, unchanged (a basic gate); the oscillator a plain sine at the pitch of the note, no modulation;
  * Clear + a knob of the VCA / VCF and oscillator pages puts the value back to its default, the knob red while Clear is held (`vcf21.use_clearknob()`);
  * FX view: with the Setup's reverb -> strip 3 / delay -> strip 4 on, the sends of MIDI 1 / MIDI 2 are capped at half and move at half speed (`vcf21.use_fxcap()`, `install_fxcap`);
  * CC editor: the pads of the numbers are cleaned when they go away (`vcf21.use_ledclean()`);
  * CC editor: Octave v lights while a next field exists, Octave ^ while a previous one exists (`vcf21.use_octleds()`).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vcf21  # noqa: E402
import vcf21_dsp  # noqa: E402
import build_sc23_2 as b232  # noqa: E402
import linein3  # noqa: E402
vcf21_dsp.use_gaterel()
vcf21_dsp.use_sinefix()
vcf21.use_neutral()
vcf21.use_clearknob()
vcf21.use_octleds()
vcf21.use_ledclean()
vcf21.use_fxcap()
b231 = b232.b231
b223 = b232.b223

NAME = "SC23.3"


def extra(img, report):
    b223.b22.b214.b213.extra(img, report)
    import ct_fw
    ext = (len(img) + ct_fw.APP_BASE + 3) & ~3
    labels, code = vcf21.install_fxcap(img, report, ext)
    report["fxcap"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()})

if __name__ == "__main__":
    linein3.main(NAME, b223.b22.b182.b18.b6.b5.build, b223.b22.b182.b18.b6.b5.s15, sys.argv[1:], extra=extra)
