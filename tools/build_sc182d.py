"""Circuit Tracks 4486 — SC182D = SC18.2 + the persistence probe (tools/probe19.py).  DIAGNOSTIC build, not for normal use.

Master FX view: Shift + pad 8 writes marker bytes into the reserved bytes of the session blobs (or clears them); pads 9-24 and the
knob LEDs show what survived a Save / power-off / Load or a patch change.  See firmware/sc182d/PRUEBA.md.
Everything up to SC18.2 is unchanged (tools/verify_builds.py).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc18_2 as b182  # noqa: E402  (applies the SC18.2 options)
import linein3  # noqa: E402
import probe19  # noqa: E402

NAME = "SC182D"


def extra(img, report):
    b182.extra(img, report)
    st = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    def text(addr, n): return "|".join(b182.b18.sc.disasm(bytes(st[addr - b182.b18.BASE:addr - b182.b18.BASE + n]), addr))
    ext = (len(img) + b182.b18.BASE + 3) & ~3
    labels, code, orig = probe19.install(img, report, ext, text)
    report["probe19"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()},
                             listing=b182.b18.sc.disasm(bytes(code), ext), orig={k: hex(v) for k, v in orig.items()},
                             probes=[(hex(c), o, hex(m)) for c, o, m in probe19.PROBES])


if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=extra)
