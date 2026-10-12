"""Circuit Tracks 4486 — SC20D (DIAGNOSTIC) = SC19.1 + the synth source modes 5 / 6 (delay / reverb return) + a capture meter in the source view.

Why: the modes 5 / 6 of SC17.5-SC17.7 (delay / reverb return as the synth's noise source) never sounded on the hardware although they work in emulation.
SC20D tells apart "the capture is empty" / "the capture works but the voice does not play it" / "the DSP read path does not work":
  * the pads 30 / 31 of the source view (SC19.1) are the modes 5 (delay) and 6 (reverb) again (capture gain x8, as SC17.7);
  * the DSP captures the delay and reverb returns EVERY block (not only while a synth uses them) and keeps their mean |L + R| in Y:$3B00 / Y:$3B01;
  * while the source view is open the pad rows 2 (delay, peach) and 3 (reverb, cream) show that level as a bar of 8 pads (12 dB per pad, about
    -102 .. -18 dB FS); if a check constant does not read back from the DSP both rows turn red (the meter itself is not working).
Use a test project.  Everything else is SC19.1 (tools/meter20.py, tools/linein3.py METER, tools/srcview.py METER).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc19_1 as b191  # noqa: E402  (applies the SC19 / SC19.1 options)
import linein3  # noqa: E402
import srcview  # noqa: E402
import meter20  # noqa: E402

linein3.N_MODES = 7                  # modes 0-4 + delay / reverb return (the pads 30 / 31 of the source view)
b191.b182.b18.b6.b5.s15.N_MODES = 7  # build_sc17_5 applied linein3.install (N_MODES = 5, set by build_sc19) at import time: the UI count lives in build_sc15
linein3.FX_GAIN_SHIFT = 3            # x8 on L + R, as SC17.7
linein3.METER = True                 # capture every block + meter words in Y:$3B00..$3B02
srcview.METER = True                 # rows 2 / 3 of the source view are the meter's

NAME = "SC20D"
b182 = b191.b182


def extra(img, report):
    b191.extra(img, report)
    st = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    def text(addr, n): return "|".join(b182.b18.sc.disasm(bytes(st[addr - b182.b18.BASE:addr - b182.b18.BASE + n]), addr))
    ext = (len(img) + b182.b18.BASE + 3) & ~3
    labels, code = meter20.install(img, report, ext, text)
    report["meter20"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, meter_y=[hex(x) for x in linein3.METER_Y],
                             check_y=hex(linein3.METER_CHECK), magic=hex(linein3.METER_MAGIC), views=[hex(v) for v in meter20.VIEWS],
                             listing=b182.b18.sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=extra)
