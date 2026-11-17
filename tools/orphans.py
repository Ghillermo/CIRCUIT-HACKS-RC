"""Stock code that nothing reaches any more in a build (the user, 2026-11-13: «audit Code to find more» room in the flash).

    python tools/orphans.py BUILD.bin manifest.json [--all]

A function of the stock = a target of a bl / b.w in the stock image, or a code pointer (odd word) in it.  In the build, the same targets are counted
over the whole image (the stock part as patched, and our code).  A stock function whose every reference is gone (our hooks replaced the calls, or
the code that called it is itself gone) is listed with its size up to the next stock function, and only when no reference to anything inside it
remains (a b / b<cond> from outside into it counts).  The candidates must be checked by hand before anything is reused: a function can be entered
through a computed jump (tbb / tbh tables, a register) that this does not see."""
from __future__ import annotations
import bisect
import json
import struct
import sys
from pathlib import Path
import capstone
from capstone import arm as CA

BASE = 0x08010000
STOCK_END = 0x0805CDDC
CODE_LO = 0x0801855A                                  # past the old DSP program copies (the hole)


def refs(img, lo, hi, md=None, kinds=("bl", "bw", "b")):
    """targets of bl / b.w (32-bit, every halfword tried) and b (16-bit) in [lo, hi), as raw decodes"""
    out = set()
    for a in range(lo, hi - 3, 2):
        h1, h2 = struct.unpack_from("<HH", img, a - BASE)
        if h1 & 0xF800 == 0xF000 and (("bl" in kinds and h2 & 0xD000 == 0xD000) or ("bw" in kinds and h2 & 0xD000 == 0x9000)):
            s_ = (h1 >> 10) & 1; j1 = (h2 >> 13) & 1; j2 = (h2 >> 11) & 1
            i1, i2 = 1 - (j1 ^ s_), 1 - (j2 ^ s_)
            off = s_ << 24 | i1 << 23 | i2 << 22 | (h1 & 0x3FF) << 12 | (h2 & 0x7FF) << 1
            if off & (1 << 24): off -= 1 << 25
            out.add(a + 4 + off)
        elif "b" in kinds and h1 & 0xF800 == 0xE000:
            off = (h1 & 0x7FF) << 1
            if off & 0x800: off -= 0x1000
            out.add(a + 4 + off)
    return out


def main(a):
    img = Path(a[0]).read_bytes()
    stock = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    ptr = lambda b, lo, hi: {struct.unpack_from("<I", b, o)[0] & ~1 for o in range(0, len(b) - 3, 4) if struct.unpack_from("<I", b, o)[0] & 1
                              and lo <= struct.unpack_from("<I", b, o)[0] & ~1 < hi}
    calls = {x for x in refs(stock, CODE_LO, STOCK_END, kinds=("bl",)) if CODE_LO <= x < STOCK_END}
    sp = ptr(stock, CODE_LO, STOCK_END)
    funcs = sorted(calls | sp)
    b_refs = refs(img, CODE_LO, BASE + len(img)) | ptr(img, CODE_LO, STOCK_END)
    out = []
    for i, f in enumerate(funcs):
        if f in b_refs: continue
        end = funcs[i + 1] if i + 1 < len(funcs) else STOCK_END
        if any(f < r < end for r in b_refs):                    # something still enters it
            continue
        out.append((end - f, f))
    tot = sum(n for n, _ in out)
    print(f"stock functions {len(funcs)}; orphaned {len(out)}, {tot} B")
    for n, f in sorted(out, reverse=True)[:60 if "--all" not in a else None]:
        print(f"  {n:5d} B at {f:#x}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
