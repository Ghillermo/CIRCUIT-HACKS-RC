"""Regenera re/app.asm (desensamblado lineal Thumb del stock) para los builders.

    python tools/gen_listing.py [stock/circuittracks-firmware-4486-STOCK.bin]
"""
import sys
from pathlib import Path

import capstone

ROOT = Path(__file__).resolve().parents[1]
src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "stock/circuittracks-firmware-4486-STOCK.bin"
out = ROOT / "re/app.asm"
out.parent.mkdir(exist_ok=True)
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB | capstone.CS_MODE_MCLASS)
md.skipdata = True
with out.open("w") as f:
    for i in md.disasm(src.read_bytes(), 0x08010000):
        f.write(f"{i.address:08x}: {i.mnemonic:<8} {i.op_str}".rstrip() + "\n")
print(out)
