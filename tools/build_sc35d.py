"""Circuit Tracks 4486 — SC35D (DIAGNOSTIC): DSP core 1 (tools/probe35_dsp.py) on the chain of SC32D / SC32D.1 (SC20D.1, proven on the device), with the MIDI dump of
SC32D.1 (tools/probe32b.py: pad 9 of the synth source view, 72 CC on channel 16; reader tools/sc32d1_reader.html).

Core 1 runs our code inside its stock loop (P:$12A -> c1loop -> P:$10E): its program RAM, its X / Y, the external memory shared with core 0, its idle passes per audio
block; core 0 copies the answers to Y:$3B10.. for the ARM.  Decides whether the granular engine can live on core 1.  See firmware/sc35d/PRUEBA.md.
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
import probe32b  # noqa: E402
import probe32b_dsp  # noqa: E402
import probe35_dsp  # noqa: E402
linein3.N_MODES = 7
b191.b182.b18.b6.b5.s15.N_MODES = 7
linein3.FX_GAIN_SHIFT = 3
linein3.METER = True
srcview.METER = True
probe35_dsp.install_dsp(build_sc16)
probe32b_dsp.MAGIC = probe35_dsp.MAGIC          # the ARM display / dump: green pad 9 once core 1 has answered
assert probe32b_dsp.YM == probe35_dsp.YM and probe32b_dsp.NW == probe35_dsp.NW

NAME = "SC35D"
b182 = b191.b182


def extra(img, report):
    b191.extra(img, report)
    c1 = probe35_dsp.patch(img, report)
    ext = (len(img) + b182.b18.BASE + 3) & ~3
    labels, code = probe32b.install(img, report, ext)
    report["probe35"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, **c1,
                             listing=b182.b18.sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=extra)
