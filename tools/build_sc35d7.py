"""Circuit Tracks 4486 — SC35D7 (DIAGNOSTIC): SC35D6 with the write-back on pads 17-24 (red; probe35s.WB_PADS) instead of Shift + pad: SC35D6 on the device
never wrote (16 read-only dumps, Shift apparently held for the second 8).  Pads 9-16 = SC35D5's read-only probe.  Built on SC35D6 (comment kept below):
SC35D6 (DIAGNOSTIC): SC35D5 + probe35s.WRITEBACK: Shift + pad 9-16 writes the first 21 bytes of PCM item 0-7 back UNCHANGED through the
stock write (op 7, in place), then reads the size and the bytes again (a pad without Shift = SC35D5's read-only probe).  SC35D5 on the device: the 8 sizes and the
RIFF headers are those of 00_808.wav .. 07_Noise FX.wav (the stock finds NN_*.wav by the prefix).  Built on SC35D5 (comment kept below):
SC35D5 (DIAGNOSTIC, READ-ONLY on the SD card): SC35D4 with the item kind 4 (PCM).  SC35D4 on the device: the API works from the UI
task (exists 1, status 0, 21 bytes) but kind 2 read session 0 (160 780 B, "USER..."): the storage task numbers 0 global, 1 pack, 2..6 = the pack folders
(Sessions, Patches, PCM, meta, the effects folder).  Pads 9-16 of the synth source view = PCM items 0-7 of the current pack.  See firmware/sc35d5/PRUEBA.md.
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
probe35s.KIND = 4
probe35s.WRITEBACK = True
probe35s.WB_PADS = True
linein3.N_MODES = 7
b191.b182.b18.b6.b5.s15.N_MODES = 7
linein3.FX_GAIN_SHIFT = 3
linein3.METER = True
srcview.METER = True

NAME = "SC35D7"
b182 = b191.b182


def extra(img, report):
    b191.extra(img, report)
    ext = (len(img) + b182.b18.BASE + 3) & ~3
    labels, code = probe35s.install(img, report, ext)
    report["probe35s"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, listing=b182.b18.sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=extra)
