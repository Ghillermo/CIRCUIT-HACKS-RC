"""Circuit Tracks 4486 — SC35D4 (DIAGNOSTIC, READ-ONLY on the SD card): the stock content API of the storage task (tools/probe35s.py: exists / size / read of
the PCM items 0-7 of the current pack, pads 9-16 of the synth source view, dumped as the SC32D.1 MIDI CC; reader tools/sc32d1_reader.html), on the chain of
SC35D without its DSP probe.  The way to save the captured sample into the pack's PCM folder.  See firmware/sc35d4/PRUEBA.md.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import persist19  # noqa: E402
persist19.FIX_LOCK = True
import build_sc19_1 as b191  # noqa: E402
import build_sc16  # noqa: E402
import linein3  # noqa: E402
import srcview  # noqa: E402
import probe35s  # noqa: E402
linein3.N_MODES = 7
b191.b182.b18.b6.b5.s15.N_MODES = 7
linein3.FX_GAIN_SHIFT = 3
linein3.METER = True
srcview.METER = True

NAME = "SC35D4"
b182 = b191.b182


def extra(img, report):
    b191.extra(img, report)
    ext = (len(img) + b182.b18.BASE + 3) & ~3
    labels, code = probe35s.install(img, report, ext)
    report["probe35s"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, listing=b182.b18.sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=extra)
