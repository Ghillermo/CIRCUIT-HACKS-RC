"""Circuit Tracks 4486 — SC09 = SC08 + drum Pitch in semitones.

Stock drum Pitch (0..127, 64 = original) is a LINEAR playback-rate change:
DSP word = (256 + 2*trunc(1.5*(v-64))) << 8, ratio = word / 0x10000 (0.25x .. 1.73x).
The DSP drum voice computes increment = base_inc * word (X:$A3+10d+1, func_0020b3),
so any ratio is possible; only the ARM conversion limits it.

SC09 replaces the conversion (0x0802878C, only used by the 4 drum DSP-update
handlers) with an exponential table: word = round(0x10000 * 2^((v-64)/12)),
i.e. one knob step = one semitone, v = 64 unchanged, range -64..+63 semitones.
The 4 callers' `lsls r1, r0, #8` become `mov r1, r0` so the full 24-bit word is
sent (precision 1/65536 instead of 1/256).
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct_fw  # noqa: E402
import build_shared_channels as sc  # noqa: E402
import build_sc04 as s4  # noqa: E402
import build_sc08 as s8  # noqa: E402
from thumb import ands_reg, h, lsls_imm, movs_imm, movt, movw, nop, bx_lr  # noqa: E402

BASE = ct_fw.APP_BASE
MARKER = b"SC09"
CONV = 0x0802878C
CONV_END = 0x080287A0
CALLERS = (0x080287FE, 0x0802889A, 0x0802892E, 0x080289C2)   # lsls r1, r0, #8 after bl CONV


def table():
    return [min(0x7FFFFF, round(0x10000 * 2 ** ((v - 64) / 12))) for v in range(128)]


def stock_word(v):
    d = v - 64
    t = d + int(d / 2)                      # trunc toward zero, as the ARM code
    return (((t + 128) * 2) & 0xFFFF) << 8


def build(stock: bytes, listing: Path):
    img8, report = s8.build(stock, listing)
    img = bytearray(img8)
    img[sc.MARK_OFF:sc.MARK_OFF + 4] = MARKER
    tab_addr = (len(img8) + BASE + 3) & ~3

    def text(addr, n):
        return "|".join(sc.disasm(bytes(stock[addr - BASE:addr - BASE + n]), addr))
    want = ("subs r0, #0x40|sxth r1, r0|add.w r1, r1, r1, lsr #31|add.w r0, r0, r1, asr #1|adds r0, #0x80|"
            "lsls r0, r0, #0x11|lsrs r0, r0, #0x10|bx lr")
    if text(CONV, CONV_END - CONV) != want:
        raise SystemExit("conversion mismatch: " + text(CONV, CONV_END - CONV))
    for c in CALLERS:
        if text(c - 4, 6) != f"bl #{CONV:#x}|lsls r1, r0, #8":
            raise SystemExit(f"caller mismatch at {c:#x}: {text(c - 4, 6)}")
    targets = s4.branch_targets(listing)
    for x in range(CONV + 1, CONV_END):
        if x in targets:
            raise SystemExit(f"branch into conversion at {x:#x}")
    code = (movs_imm(1, 0x7F) + ands_reg(0, 1) + lsls_imm(0, 0, 2) + movw(1, tab_addr & 0xFFFF)
            + movt(1, tab_addr >> 16) + h(0x5808) + bx_lr())          # ldr r0,[r1,r0]
    code += nop() * ((CONV_END - CONV - len(code)) // 2)
    assert len(code) == CONV_END - CONV
    img[CONV - BASE:CONV_END - BASE] = code
    for c in CALLERS:
        img[c - BASE:c - BASE + 2] = h(0x4601)                          # mov r1, r0
    tab = table()
    img += b"\xFF" * (tab_addr - BASE - len(img)) + struct.pack("<128I", *tab)
    assert len(img) <= 0x70000
    report["D"]["marker"] = MARKER.decode()
    report["sc09"] = dict(table=hex(tab_addr), conv=sc.disasm(code, CONV))
    return bytes(img), report


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("stock_bin", type=Path)
    ap.add_argument("--listing", type=Path, default=Path(__file__).resolve().parents[1] / "re/app.asm")
    ap.add_argument("-o", "--outdir", type=Path, default=Path("build/sc09"))
    args = ap.parse_args()
    stock = args.stock_bin.read_bytes()
    img, report = build(stock, args.listing)
    syx = ct_fw.encode(img)
    info = ct_fw.decode(syx)
    assert info["image"] == img
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / "circuittracks-4486-SC09.bin").write_bytes(img)
    (args.outdir / "circuittracks-4486-SC09.syx").write_bytes(syx)
    manifest = dict(base="circuittracks-firmware-4486 (1.2.1)", marker="SC09", image_size=hex(len(img)),
                    image_sha256=ct_fw.sha256(img), syx_sha256=ct_fw.sha256(syx), crc32=hex(info["crc"]), report=report)
    (args.outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("table", report["sc09"]["table"], "image", hex(len(img)))
    print("conv", report["sc09"]["conv"])
    print("syx sha", manifest["syx_sha256"], "crc", manifest["crc32"])
