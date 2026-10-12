"""Circuit Tracks 4486 — SC04 = SC02 + single Ch16 (non-PC) Rx+Tx toggle on the red channel-16 pad.

SC04 changes vs SC03: pads 22/23 back to stock (unused); channel pad 16
(row 2, col 8) toggles BOTH bits 24/25 together; the pad shows stock red
when enabled and is unlit when blocked.

(Original SC03 notes follow.)

New Setup View pads (row 3, pads 22 and 23 — unused in stock):
  pad 22  Ch16 Rx  : receive channel-16 messages other than Program Change
  pad 23  Ch16 Tx  : transmit channel-16 messages other than Program Change
Lit like the CC toggles (on = stock colour for "enabled"). Default: both ON
(stock behaviour). Stored in settings param 2, bits 24/25 (1 = blocked).

Code lives in a cave appended after the stock image end (0x0805CDDC); the
image grows (bootloader accepts up to 0x70000 bytes).  Hooks:
  H1 0x08046E82  Setup pad handler: pads 0x15/0x16 toggle bits 24/25
  H2 0x080472E0  Setup LED routine tail: draw pads 22/23
  H3 0x08034F9E  settings->MIDI apply: Rx flag bit4 = param2 bit24
  H4 0x08035066  settings->MIDI apply: Tx flag bit4 = param2 bit25
  H5 0x08051722  MIDI receive dispatcher entry: drop ch16 non-PC if Rx bit4
  H6 0x0802A002  CC/NRPN transmit gate: block track ids 0x20/0x21 if Tx bit4
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct_fw  # noqa: E402
import build_shared_channels as sc  # noqa: E402
from thumb import (Asm, b_cond, b_w, bl, bx_lr, cmp_imm, eors_reg, it, ldr_imm, ldrb_imm,  # noqa: E402
                   ldrh_reg, lsls_imm, lsrs_imm, mov_reg, movs_imm, orrs_reg, raw, adds_imm8,
                   str_imm, strh_imm, subs_imm8)

BASE = ct_fw.APP_BASE
MARKER = b"SC04"
CAVE = 0x0805CDE0

PARAM_GET = 0x0803542C
PARAM_PTR = 0x080354FA

HOOKS = {   # addr: (stock bytes as capstone text, replaced length)
    0x08046E82: ("subs r5, #0x17|cmp r5, #8", 4),
    0x0804746E: ("cmp.w r8, #0xf|it eq|moveq r6, #0xcf|nop|nop", 12),
    0x08034F9E: ("orr r1, r1, #8", 4),
    0x08035066: ("ldr r0, [r4, #0x1c]|strb r1, [r0, #0x18]", 4),
    0x08051722: ("mov r4, r0|mov r5, r1", 4),
    0x0802A002: ("ldrb r4, [r0, #0x18]|lsls r5, r4, #0x1e", 4),
}


from thumb import lsls_reg, strb_imm, bics_reg, push_lr, pop_pc, cmp_w_imm, nop, b  # noqa: E402


def assemble_cave(stock: bytes):
    pop_led = stock[0x080472E0 - BASE:0x080472E0 - BASE + 4]
    a = Asm(CAVE)
    a.label("c_pad")                           # from H1, r5 = pad index (15 or >= 0x15)
    a.emit(cmp_imm, 5, 0x0F)
    a.emit(b_cond, "c_pad_16", "eq")
    a.emit(subs_imm8, 5, 0x17)
    a.emit(cmp_imm, 5, 8)
    a.emit(b_cond, "c_pad_ign", "hi")
    a.emit(b_w, 0x08046E88)                    # stock tbb (pads 24..32)
    a.label("c_pad_ign")
    a.emit(b_w, 0x08046E64)                    # pads 22/23 etc: refresh only (stock)
    a.label("c_pad_16")
    a.emit(ldr_imm, 0, 4, 0x0C)
    a.emit(movs_imm, 1, 2)
    a.emit(bl, PARAM_PTR)                      # r0 = writable param 2
    a.emit(ldr_imm, 1, 0, 0)
    a.emit(movs_imm, 2, 3)
    a.emit(lsls_imm, 2, 2, 24)                 # mask bits 24|25
    a.emit(lsls_imm, 3, 1, 7)                  # bit24 (blocked) -> N
    a.emit(b_cond, "c_pad_en", "mi")
    a.emit(orrs_reg, 1, 2)                     # enabled -> block Rx+Tx
    a.emit(b, "c_pad_st")
    a.label("c_pad_en")
    a.emit(bics_reg, 1, 2)                     # blocked -> enable Rx+Tx
    a.label("c_pad_st")
    a.emit(str_imm, 1, 0, 0)
    a.emit(b_w, 0x08046E5E)                    # stock commit + refresh tail

    a.label("c_led16")                         # bleq from channel-LED loop when r8 == 15
    a.emit(push_lr)
    a.emit(ldr_imm, 0, 7, 0x0C)
    a.emit(movs_imm, 1, 2)
    a.emit(bl, PARAM_GET)
    a.emit(ldr_imm, 0, 0, 0)
    a.emit(lsls_imm, 0, 0, 7)                  # bit24 -> N
    a.emit(it, "mi", "e")
    a.emit(movs_imm, 6, 0x00)                  # blocked: unlit
    a.emit(movs_imm, 6, 0xCF)                  # enabled: stock project red
    a.emit(pop_pc)

    a.label("c_rxf")
    a.emit(movs_imm, 3, 8)
    a.emit(orrs_reg, 1, 3)
    a.emit(ldr_imm, 3, 5, 0)
    a.emit(lsls_imm, 3, 3, 7)
    a.emit(b_cond, "c_rxf_end", "pl")
    a.emit(movs_imm, 3, 0x10)
    a.emit(orrs_reg, 1, 3)
    a.label("c_rxf_end")
    a.emit(bx_lr)

    a.label("c_txf")
    a.emit(ldr_imm, 3, 5, 0)
    a.emit(lsls_imm, 3, 3, 6)
    a.emit(b_cond, "c_txf_st", "pl")
    a.emit(movs_imm, 3, 0x10)
    a.emit(orrs_reg, 1, 3)
    a.label("c_txf_st")
    a.emit(ldr_imm, 0, 4, 0x1C)
    a.emit(strb_imm, 1, 0, 0x18)
    a.emit(bx_lr)

    a.label("c_rx")                            # bl from H5 (after push in dispatcher)
    a.emit(mov_reg, 4, 0)
    a.emit(mov_reg, 5, 1)
    a.emit(ldrb_imm, 0, 4, 0x14)
    a.emit(lsls_imm, 0, 0, 27)                 # Rx flag bit4 -> N
    a.emit(b_cond, "c_rx_ok", "pl")
    a.emit(ldrb_imm, 0, 5, 0)                  # status byte
    a.emit(cmp_imm, 0, 0xF0)
    a.emit(b_cond, "c_rx_ok", "hs")            # system messages untouched
    a.emit(lsrs_imm, 1, 0, 4)
    a.emit(cmp_imm, 1, 0x0C)
    a.emit(b_cond, "c_rx_ok", "eq")            # Program Change untouched
    a.emit(cmp_imm, 1, 0x08)
    a.emit(b_cond, "c_rx_ok", "lo")            # not a status byte
    a.emit(adds_imm8, 0, 1)
    a.emit(lsls_imm, 0, 0, 28)                 # low nibble == 0xF ?
    a.emit(b_cond, "c_rx_ok", "ne")
    a.emit(b_w, 0x080518F0)                    # drop: dispatcher epilogue
    a.label("c_rx_ok")
    a.emit(bx_lr)

    a.label("c_tx")                            # bl from H6; r0 tx obj, r2 track id
    a.emit(ldrb_imm, 4, 0, 0x18)
    a.emit(lsls_imm, 5, 4, 30)                 # stock: CC Tx flag -> N
    a.emit(b_cond, "c_tx_end", "pl")
    a.emit(cmp_imm, 2, 0x20)
    a.emit(b_cond, "c_tx_chk", "eq")
    a.emit(cmp_imm, 2, 0x21)
    a.emit(b_cond, "c_tx_end", "ne")
    a.label("c_tx_chk")
    a.emit(lsls_imm, 5, 4, 27)                 # Ch16 Tx block flag -> N
    a.emit(b_cond, "c_tx_on", "pl")
    a.emit(movs_imm, 5, 0)                     # N=0 -> caller skips the send
    a.emit(bx_lr)
    a.label("c_tx_on")
    a.emit(lsls_imm, 5, 4, 30)                 # restore N from CC Tx flag
    a.label("c_tx_end")
    a.emit(bx_lr)
    return a.assemble()


def hook_bytes(labels):
    return {
        0x08046E82: b_w(0x08046E82, labels["c_pad"]),
        0x0804746E: cmp_w_imm(8, 0x0F) + it("eq") + bl(0x08047474, labels["c_led16"]) + nop(),
        0x08034F9E: bl(0x08034F9E, labels["c_rxf"]),
        0x08035066: bl(0x08035066, labels["c_txf"]),
        0x08051722: bl(0x08051722, labels["c_rx"]),
        0x0802A002: bl(0x0802A002, labels["c_tx"]),
    }


def branch_targets(listing_path: Path):
    t = set()
    for line in listing_path.read_text().splitlines():
        m = re.match(r"([0-9a-f]{8}): +(b\S*|cb\S*|bl\S*) +#0x([0-9a-f]+)$", line)
        if m:
            t.add(int(m.group(3), 16))
    return t


def build(stock: bytes, listing: Path):
    img2, report, _ = sc.build(stock)           # SC02 code (regions A, B, C + SC02 marker)
    img = bytearray(img2[:len(stock)])
    # replace marker
    img[sc.MARK_OFF:sc.MARK_OFF + 4] = MARKER
    code, labels = assemble_cave(stock)
    targets = branch_targets(listing)
    for addr, (stock_text, n) in HOOKS.items():
        got = "|".join(sc.disasm(bytes(img[addr - BASE:addr - BASE + n]), addr))
        if got != stock_text:
            raise SystemExit(f"hook {addr:#x}: base is '{got}', expected '{stock_text}'")
        for x in range(addr + 1, addr + n):
            if x in targets and addr != 0x0804746E:
                raise SystemExit(f"hook {addr:#x}: something branches into {x:#x}")
    for addr, hb in hook_bytes(labels).items():
        assert len(hb) == HOOKS[addr][1]
        img[addr - BASE:addr - BASE + len(hb)] = hb
    # cave after the stock image (0xFF gap up to CAVE)
    end = BASE + len(stock)
    assert CAVE >= end and CAVE % 4 == 0
    img += b"\xFF" * (CAVE - end) + code
    while len(img) % 4:
        img += b"\xFF"
    assert len(img) <= 0x70000
    report["cave"] = dict(start=hex(CAVE), size=len(code),
                          labels={k: hex(v) for k, v in labels.items()},
                          listing=sc.disasm(code, CAVE))
    report["hooks"] = {hex(a): sc.disasm(b, a) for a, b in hook_bytes(labels).items()}
    report["D"]["marker"] = MARKER.decode()
    return bytes(img), report


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("stock_bin", type=Path)
    ap.add_argument("--listing", type=Path, default=Path(__file__).resolve().parents[1] / "re/app.asm")
    ap.add_argument("-o", "--outdir", type=Path, default=Path("build/sc04"))
    args = ap.parse_args()
    stock = args.stock_bin.read_bytes()
    img, report = build(stock, args.listing)
    syx = ct_fw.encode(img)
    info = ct_fw.decode(syx)
    assert info["image"] == img
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / "circuittracks-4486-SC04.bin").write_bytes(img)
    (args.outdir / "circuittracks-4486-SC04.syx").write_bytes(syx)
    manifest = dict(base="circuittracks-firmware-4486 (1.2.1)", marker=MARKER.decode(),
                    image_size=hex(len(img)), image_sha256=ct_fw.sha256(img),
                    syx_sha256=ct_fw.sha256(syx), crc32=hex(info["crc"]), report=report)
    (args.outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    for a, l in report["hooks"].items():
        print("hook", a, l)
    print("cave", report["cave"]["start"], report["cave"]["size"], "bytes")
    for l in report["cave"]["listing"]:
        print("   ", l)
    print("image size", hex(len(img)), "sha", manifest["image_sha256"])
    print("syx sha", manifest["syx_sha256"], "crc", manifest["crc32"])
