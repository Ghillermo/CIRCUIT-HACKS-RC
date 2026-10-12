"""Circuit Tracks 4486 — SC32D (DIAGNOSTIC) = SC21D's chain (SC20D.1, proven on the device, as SC21D) with the probe replaced by the external Y memory probe
(tools/probe32_dsp.py, tools/probe32.py) and without the NRPN monitor.

Reads the 30 zones of the stock map of the DSP's external memory (from Y:$100000) and 8 addresses past it, one area per audio block; writes one word per area once (saved, written,
read back, restored with the interrupts masked).  Open the synth source view (Synth 1 / 2 pressed twice) and read pads 9-24 (four 4-second pages, each marked by a white pad
during its first half second), see firmware/sc32d/PRUEBA.md.  Use with a test project; nothing is saved.  Picks the zone of the captured sample (docs/NOTAS.md).
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
import probe32  # noqa: E402
import probe32_dsp  # noqa: E402
linein3.N_MODES = 7                  # as SC20D / SC21D: modes 0-4 + delay / reverb return
b191.b182.b18.b6.b5.s15.N_MODES = 7
linein3.FX_GAIN_SHIFT = 3
linein3.METER = True                 # the SC20D capture (its words Y:$3B00..$3B02 stay unused)
srcview.METER = True                 # rows 2 / 3 of the source view belong to the display of the probe
probe32_dsp.install_dsp(build_sc16)

NAME = "SC32D"
b182 = b191.b182


def extra(img, report):
    b191.extra(img, report)
    probe32_dsp.patch_dsp(img, report)
    ext = (len(img) + b182.b18.BASE + 3) & ~3
    labels, code = probe32.install(img, report, ext)
    report["probe32"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, areas=[hex(x) for x in probe32_dsp.AREAS],
                             listing=b182.b18.sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=extra)
