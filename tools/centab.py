"""SC50 / Beta 5.3 (flash for jumpseq): SC12's table of the drums' cents (201 words at 0x0805D7D0, one reader) in 16 bits: half the value, read with a halfword load and
one shift less: the same multiplication within 0.03 cents.  The 400 B freed in the middle of the image take a module, as hole.add does in the old DSP blocks."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import lsls_imm, lsrs_imm
import build_sc12 as S12  # noqa: E402

BASE = 0x08010000
N = 2 * S12.MAXC + 1


def shrink(img, report):
    tab = int(report["sc12"]["table"], 16)
    old = [round(65536 * 2 ** (c / 1200)) for c in range(-S12.MAXC, S12.MAXC + 1)]
    assert list(struct.unpack_from(f"<{N}I", img, tab - BASE)) == old
    struct.pack_into(f"<{N}H", img, tab - BASE, *[(v + 1) >> 1 for v in old])
    at = int(report["sc12"]["labels"]["cv_tab_fix"], 16)
    def put(a, was, new):
        assert bytes(img[a - BASE:a - BASE + 2]) == was, hex(a)
        img[a - BASE:a - BASE + 2] = new
    put(at - 10, lsls_imm(1, 1, 2), lsls_imm(1, 1, 1))
    put(at, bytes.fromhex("5258"), bytes.fromhex("525a"))                 # ldr r2, [r2, r1] -> ldrh
    put(at + 6, lsrs_imm(0, 0, 16), lsrs_imm(0, 0, 15))
    put(at + 8, lsls_imm(1, 1, 16), lsls_imm(1, 1, 17))
    low = (tab + 2 * N + 3) & ~3
    report["centab"] = dict(next=hex(low), end=hex(tab + 4 * N))
    img[low - BASE:tab + 4 * N - BASE] = bytes([0xFF]) * (tab + 4 * N - low)


def add(img, report, name, mod):
    """mod's code in the freed bytes"""
    import build_shared_channels as sc
    c = report["centab"]
    at = (int(c["next"], 16) + 3) & ~3
    n0 = len(img)
    labels, code, prev = mod.install(img, report, at)
    blob = bytes(img[n0:])
    assert blob[:len(code)] == bytes(code), f"{name}: install did not append its code at the end"
    del img[n0:]
    end = at + len(blob)
    assert end <= int(c["end"], 16), f"{name}: no room ({end:#x})"
    img[at - BASE:end - BASE] = blob
    c["next"] = hex(end)
    report[name] = dict(arm_start=hex(at), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()}, listing=sc.disasm(bytes(code), at))
