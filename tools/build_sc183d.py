"""Circuit Tracks 4486 — SC183D = SC18.3 + the persistence probe v2 (tools/probe20.py).  DIAGNOSTIC build, not for normal use.

Master FX view: Shift + pad 8 writes the next generation number into reserved bytes of the session blobs, Shift + pad 7 clears them,
pads 9-23 / knob LEDs / the slot row show what the stores or the session record buffer hold and the save / load events.
See firmware/sc183d/PRUEBA.md.  Everything up to SC18.3 is unchanged (tools/verify_builds.py).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc18_3 as b183  # noqa: E402  (applies the SC18.3 options)
import build_sc17 as s17  # noqa: E402
import build_sc14 as s14  # noqa: E402
import linein3  # noqa: E402
import probe20  # noqa: E402

NAME = "SC183D"
s17.GFX_SIZE += probe20.EXTRA        # 4 extra bytes of the Master FX block for the probe (reservation 224 B, 16 B of margin)
s14.ST -= probe20.EXTRA
b182 = b183.b182


def extra(img, report):
    assert s17.GFX_SIZE == 184
    b182.extra(img, report)
    st = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    def text(addr, n): return "|".join(b182.b18.sc.disasm(bytes(st[addr - b182.b18.BASE:addr - b182.b18.BASE + n]), addr))
    ext = (len(img) + b182.b18.BASE + 3) & ~3
    labels, code, orig = probe20.install(img, report, ext, text)
    report["probe20"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()},
                             listing=b182.b18.sc.disasm(bytes(code), ext + len(probe20.table())),
                             orig={k: hex(v) for k, v in orig.items()},
                             probes=[(hex(c), o, hex(m)) for c, o, m in probe20.PROBES])


if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=extra)
