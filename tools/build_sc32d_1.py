"""Circuit Tracks 4486 — SC32D.1 (DIAGNOSTIC) = SC32D's chain with the raw probe (tools/probe32b_dsp.py, tools/probe32b.py) instead of the zone survey.

SC32D said that only zone 0 writes and reads back.  This build records, once, the raw words of a few accesses (SR, OMR, M0, the address register, zone 1 / 0 / 14 read
before / after a write, by register and by absolute address, after a delay, the internal Y:$000000) and sends them as MIDI CC on channel 16 when pad 9 of the synth source
view is pressed (Synth 1 / 2 pressed twice; pad 9 green = the probe ran).  See firmware/sc32d.1/PRUEBA.md.  Use with a test project; nothing is saved.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import persist19  # noqa: E402
persist19.FIX_LOCK = True            # before persist19.install builds the code (main time)
import build_sc19_1 as b191  # noqa: E402  (applies the SC19 / SC19.1 options)
import build_sc16  # noqa: E402
import linein3  # noqa: E402
import srcview  # noqa: E402
import probe32b  # noqa: E402
import probe32b_dsp  # noqa: E402
linein3.N_MODES = 7                  # as SC20D / SC21D: modes 0-4 + delay / reverb return
b191.b182.b18.b6.b5.s15.N_MODES = 7
linein3.FX_GAIN_SHIFT = 3
linein3.METER = True                 # the SC20D capture (its words Y:$3B00..$3B02 stay unused)
srcview.METER = True                 # rows 2 / 3 of the source view belong to the display of the probe
probe32b_dsp.install_dsp(build_sc16)

NAME = "SC32D.1"
b182 = b191.b182


def extra(img, report):
    b191.extra(img, report)
    probe32b_dsp.patch_dsp(img, report)
    ext = (len(img) + b182.b18.BASE + 3) & ~3
    labels, code = probe32b.install(img, report, ext)
    report["probe32b"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, names=probe32b_dsp.NAMES,
                             listing=b182.b18.sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=extra)
