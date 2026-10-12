"""Circuit Tracks 4486 — SC32D2 (DIAGNOSTIC) = SC32D corrected after SC32D / SC32D.1 on the device (2026-10-08) + a MIDI dump of the flags.

SC32D.1 showed that the DSP's external memory keeps 16 bits per word (the low byte reads back 0) and that M0 = $FFFF at the hook: SC32D's write test (pattern $5A5A00 + k)
failed everywhere but zone 0 for that reason, and its 32 reads stayed inside a 64 K window.  Here (probe32_dsp.V2): pattern $5A5A00 + (k << 8), M0 linear during the probe,
the flags also in Y:STF; the LED pages of SC32D with a real red (0x53; 0x05 is grey); pad 9 of the source view sends the flags of the 38 areas as MIDI CC on channel 16
(tools/probe32c.py; reader tools/sc32d1_reader.html).  See firmware/sc32d2/PRUEBA.md.  Use with a test project; nothing is saved.
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
import probe32  # noqa: E402
import probe32c  # noqa: E402
import probe32_dsp  # noqa: E402
linein3.N_MODES = 7
b191.b182.b18.b6.b5.s15.N_MODES = 7
linein3.FX_GAIN_SHIFT = 3
linein3.METER = True
srcview.METER = True
probe32_dsp.V2 = True
probe32.STATE_COL[probe32_dsp.S_FAIL] = 0x53     # the real red (RGB table B, G, R: 0x53 = 255, 0, 0)
probe32_dsp.install_dsp(build_sc16)

NAME = "SC32D2"
b182 = b191.b182


def extra(img, report):
    b191.extra(img, report)
    probe32_dsp.patch_dsp(img, report)
    ext = (len(img) + b182.b18.BASE + 3) & ~3
    labels, code = probe32.install(img, report, ext)
    ext2 = (len(img) + b182.b18.BASE + 3) & ~3
    labels2, code2 = probe32c.install(img, report, ext2, labels["c_dtick32"])
    report["probe32"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, areas=[hex(x) for x in probe32_dsp.AREAS],
                             listing=b182.b18.sc.disasm(bytes(code), ext))
    report["probe32c"] = dict(arm_start=hex(ext2), labels={k: hex(v) for k, v in labels2.items()}, listing=b182.b18.sc.disasm(bytes(code2), ext2))


if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=extra)
