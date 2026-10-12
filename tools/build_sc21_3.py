"""Circuit Tracks 4486 — SC21.3 = SC21.2 + the four drum squares of the drum Note view also at the start of the bottom row (tools/drumnote.py).

The pads 25-28 play / record the drums 1-4 like the pads 29-32 and show the same colours.  Everything else is SC21.2.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc21_2 as b212  # noqa: E402
import drumnote  # noqa: E402
import linein3  # noqa: E402

NAME = "SC21.3"
b182 = b212.b182


def extra(img, report):
    b212.extra(img, report)
    st = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    def text(addr, n): return "|".join(b182.b18.sc.disasm(bytes(st[addr - b182.b18.BASE:addr - b182.b18.BASE + n]), addr))
    ext = (len(img) + b182.b18.BASE + 3) & ~3
    labels, code = drumnote.install(img, report, ext, text)
    report["drumnote"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, listing=b182.b18.sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=extra)
