"""Circuit Tracks 4486 — SC19.1 = SC19 + the synth source switch (noise / input 1 / 2 / inverted) moves out of Shift + Preset pads.

Pressing Synth 1 / Synth 2 a second time (while its own track view is showing) opens a view of the synth Preset pads: pads 25-29 =
noise, input 1, input 2, input 1 inverted, input 2 inverted (selected bright, the others dim, every other pad dark).  Any button closes it
(tools/srcview.py).  Shift + pads of the Preset view are stock again (choosing the patch that is already chosen resets it).
Everything up to SC19 is unchanged (tools/verify_builds.py).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc19 as b19  # noqa: E402  (applies the SC19 options)
import linein3  # noqa: E402
import srcview  # noqa: E402

NAME = "SC19.1"
b183 = b19.b183
b182 = b19.b182


def extra(img, report):
    b19.extra(img, report)
    st = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    def text(addr, n): return "|".join(b182.b18.sc.disasm(bytes(st[addr - b182.b18.BASE:addr - b182.b18.BASE + n]), addr))
    ext = (len(img) + b182.b18.BASE + 3) & ~3
    labels, code = srcview.install(img, report, ext, text)
    report["srcview"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()},
                             listing=b182.b18.sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=extra)
