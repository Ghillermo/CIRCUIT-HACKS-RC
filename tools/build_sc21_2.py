"""Circuit Tracks 4486 — SC21.2 = SC21.1 + Shift + knob in the FX view = the reverb / delay parameters (tools/fxparams.py).

Reverb page: K1 type, K2 decay, K3 damping.  Delay page: K1 time, K2 time sync, K3 feedback, K4 width, K5 left-right ratio, K6 slew rate (the page = Octave up / down as in SC17.5).
The knob LEDs show the values as brightness while Shift is held.  Everything else is SC21.1.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc21_1 as b211  # noqa: E402
import fxparams  # noqa: E402
import linein3  # noqa: E402

NAME = "SC21.2"
b182 = b211.b182


def extra(img, report):
    b211.b21.extra(img, report)
    st = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    def text(addr, n): return "|".join(b182.b18.sc.disasm(bytes(st[addr - b182.b18.BASE:addr - b182.b18.BASE + n]), addr))
    ext = (len(img) + b182.b18.BASE + 3) & ~3
    labels, code = fxparams.install(img, report, ext, text)
    report["fxparams"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, delay=fxparams.DELAY, reverb=fxparams.REVERB,
                              listing=b182.b18.sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=extra)
