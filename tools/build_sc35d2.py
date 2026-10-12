"""Circuit Tracks 4486 — SC35D2 (DIAGNOSTIC): SC35D with probe35_dsp.V3: a read-only map of which external DSP memory the stock firmware writes after boot (24
addresses from $337000 to $8F0000, one per block), the longest gather list of core 1 and its idle passes per block, all core-1 words at the top of the shared
memory.  Same chain and MIDI dump (pad 9 of the synth source view; reader tools/sc32d1_reader.html).  The marker is SC35D2: "SC35D.2" would share the 6-byte
marker "SC35D." with SC35D.1.  See firmware/sc35d2/PRUEBA.md.
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
probe35_dsp.V3 = True
linein3.N_MODES = 7
b191.b182.b18.b6.b5.s15.N_MODES = 7
linein3.FX_GAIN_SHIFT = 3
linein3.METER = True
srcview.METER = True
probe35_dsp.install_dsp(build_sc16)
probe32b_dsp.MAGIC = probe35_dsp.MAGIC3         # the ARM display / dump: green pad 9 once core 1 has answered
assert probe32b_dsp.YM == probe35_dsp.YM and probe32b_dsp.NW == probe35_dsp.NW

NAME = "SC35D2"
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
