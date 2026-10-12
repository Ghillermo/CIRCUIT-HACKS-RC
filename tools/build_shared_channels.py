"""Circuit Tracks 4486 — "Shared MIDI channels" patch.

Goal: MIDI 1 / MIDI 2 tracks may use a MIDI channel already used by Synth 1,
Synth 2 or Drums (and vice-versa), so a MIDI track can drive an internal synth
through a MIDI loop (knobs -> CC, pads -> notes).

Uniqueness is still enforced among Synth 1, Synth 2 and Drums, the only tracks
that *receive* MIDI (receive routing at 0x08035004..0x080350FE only configures
ids 0, 1 and 0x10), so the receive side never sees an ambiguous channel.

Three in-place rewrites (no new code space, image size unchanged):

  A  0x08046E00..0x08046E5E  Setup View channel-pad handler.
     Stock: reject if channel == any of the 5 track channels.
     New:   if the selected track is MIDI 1/2 -> no check;
            otherwise reject only if channel == Synth1/Synth2/Drums channel.
            Then the stock store + commit + refresh (tail at 0x08046E5E kept).
  B  0x080473FA..0x0804747A  Setup View LED colour per channel pad.
     New: the selected track's own channel is drawn first (bright), so a
          shared channel still shows which channel the selected track uses.
          Other owners keep the stock dim colours; ch16 keeps colour 0xCF.
  C  0x08046D7A..0x08046DA6  Settings validator (on load).
     Stock: any duplicate -> reset all channels to factory defaults.
     New:   duplicates allowed only for MIDI 1/2; range checks unchanged.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import capstone

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct_fw  # noqa: E402
from thumb import (Asm, adds_imm3, adds_imm8, b, b_cond, bl, cbz, cmp_imm, cmp_reg,  # noqa: E402
                   cmp_w_imm, it, ldr_imm, ldr_sp, ldrb_imm, lsls_reg, mov_reg, movs_imm,
                   nop, orrs_reg, str_sp, strb_imm, subs_imm3, subs_imm8, tst_reg)

BASE = ct_fw.APP_BASE
STOCK_IMAGE_SHA256 = ct_fw.STOCK_4486["image_sha256"]

# helpers in stock 4486
PARAM_GET = 0x0803542C          # const byte* get(store, index)
TRACK_CH_GET = 0x080514B4       # const byte* channel(store, track_id)   (0,1,2,3,0x10)
TRACK_CH_PTR = 0x080514EA       # byte* channel_for_write(store, track_id)

# region A
A_START, A_END = 0x08046E00, 0x08046E5E
A_COMMIT_TAIL = 0x08046E5E      # ldr r0,[r4,#0x20]; bl commit; b refresh  (also jumped to from 0x08046EEE)
A_REJECT = 0x08046E64           # b 0x080470EA (refresh only)
# region B
B_START, B_END = 0x080473FA, 0x0804747A
B_DONE = 0x0804747A
# region C
C_START, C_END = 0x08046D7A, 0x08046DA6
C_RESET = 0x08046DA6
C_DONE = 0x08046DE2

# version block compared by the bootloader before installing (image offset 0x1C8, 0x26 bytes)
INFO_OFF, INFO_LEN = 0x1C8, 0x26
MARK_OFF = INFO_OFF + 0x20          # inside the zero padding, after the version string
MARKER = b"SC02"                    # Shared Channels, build 2 — bump for every new build


def region_a():
    a = Asm(A_START)
    a.emit(ldr_imm, 0, 4, 0x10)          # r0 = selection store
    a.emit(movs_imm, 1, 0)
    a.emit(bl, PARAM_GET)
    a.emit(ldrb_imm, 0, 0)               # r0 = selected pad index 0..8
    a.emit(cmp_imm, 0, 4)
    a.emit(it, "hs")
    a.emit(movs_imm, 0, 0x10)            # drums 1-4 -> track id 0x10 (same as stock table)
    a.emit(str_sp, 0, 0)                 # keep track id in the saved-r3 stack slot
    a.emit(subs_imm8, 0, 2)
    a.emit(cmp_imm, 0, 1)
    a.emit(b_cond, "assign", "ls")       # MIDI 1 / MIDI 2: no uniqueness check
    for idx in (3, 4, 7):                # Synth 1, Synth 2, Drums channels
        a.emit(ldr_imm, 0, 4, 0x0C)
        a.emit(movs_imm, 1, idx)
        a.emit(bl, PARAM_GET)
        a.emit(ldrb_imm, 0, 0)
        a.emit(cmp_reg, 5, 0)
        a.emit(b_cond, A_REJECT, "eq")
    a.label("assign")
    a.emit(ldr_sp, 1, 0)                 # r1 = track id
    a.emit(ldr_imm, 0, 4, 0x0C)
    a.emit(bl, TRACK_CH_PTR)
    a.emit(strb_imm, 5, 0)               # store new channel (stock)
    a.emit(b, A_COMMIT_TAIL)
    return a


def region_b():
    a = Asm(B_START)
    a.emit(ldr_imm, 0, 7, 0x0C)
    a.emit(mov_reg, 1, 4)                # r1 = selected track id
    a.emit(bl, TRACK_CH_GET)
    a.emit(cbz, "chain", 0)              # unknown id -> stock behaviour
    a.emit(ldrb_imm, 0, 0)
    a.emit(cmp_reg, 8, 0)
    a.emit(b_cond, "chain", "ne")
    a.emit(cmp_imm, 4, 0x10)
    a.emit(it, "eq", "e")
    a.emit(movs_imm, 6, 5)               # drums bright
    a.emit(adds_imm3, 6, 4, 1)           # synth1..midi2 bright = id + 1
    a.emit(b, B_DONE)
    a.label("chain")
    for idx, dim in ((3, 0x09), (4, 0x0A), (5, 0x0B), (6, 0x0C), (7, 0x0D)):
        a.emit(ldr_imm, 0, 7, 0x0C)
        a.emit(movs_imm, 1, idx)
        a.emit(bl, PARAM_GET)
        a.emit(ldrb_imm, 0, 0)
        a.emit(cmp_reg, 8, 0)
        a.emit(it, "eq")
        a.emit(movs_imm, 6, dim)
        a.emit(b_cond, B_DONE, "eq")
    a.emit(cmp_w_imm, 8, 0x0F)           # channel 16 = project colour (stock)
    a.emit(it, "eq")
    a.emit(movs_imm, 6, 0xCF)
    return a


def region_c():
    a = Asm(C_START)
    a.label("loop")
    a.emit(cmp_imm, 7, 4)
    a.emit(it, "eq", "e")
    a.emit(movs_imm, 1, 0x10)
    a.emit(mov_reg, 1, 7)
    a.emit(mov_reg, 0, 9)                # sb = settings store
    a.emit(bl, TRACK_CH_GET)
    a.emit(ldrb_imm, 0, 0)
    a.emit(cmp_imm, 0, 15)
    a.emit(b_cond, C_RESET, "hs")        # out of range or project channel
    a.emit(movs_imm, 1, 1)
    a.emit(lsls_reg, 1, 0)
    a.emit(subs_imm3, 2, 7, 2)
    a.emit(cmp_imm, 2, 1)
    a.emit(b_cond, "next", "ls")         # MIDI 1 / MIDI 2: allowed to share
    a.emit(tst_reg, 6, 1)
    a.emit(b_cond, C_RESET, "ne")        # duplicate among Synth1/Synth2/Drums
    a.emit(orrs_reg, 6, 1)
    a.label("next")
    a.emit(adds_imm8, 7, 1)
    a.emit(cmp_imm, 7, 4)
    a.emit(b_cond, "loop", "ls")
    a.emit(b, C_DONE)
    return a


EXPECTED = {
    # capstone text of the new code (mnemonic + operands), checked after assembly
    "A": """ldr r0, [r4, #0x10]|movs r1, #0|bl #0x803542c|ldrb r0, [r0]|cmp r0, #4|it hs|movhs r0, #0x10|str r0, [sp]|subs r0, #2|cmp r0, #1|bls #0x8046e42|ldr r0, [r4, #0xc]|movs r1, #3|bl #0x803542c|ldrb r0, [r0]|cmp r5, r0|beq #0x8046e64|ldr r0, [r4, #0xc]|movs r1, #4|bl #0x803542c|ldrb r0, [r0]|cmp r5, r0|beq #0x8046e64|ldr r0, [r4, #0xc]|movs r1, #7|bl #0x803542c|ldrb r0, [r0]|cmp r5, r0|beq #0x8046e64|ldr r1, [sp]|ldr r0, [r4, #0xc]|bl #0x80514ea|strb r5, [r0]|b #0x8046e5e""",
    "C": """cmp r7, #4|ite eq|moveq r1, #0x10|movne r1, r7|mov r0, sb|bl #0x80514b4|ldrb r0, [r0]|cmp r0, #0xf|bhs #0x8046da6|movs r1, #1|lsls r1, r0|subs r2, r7, #2|cmp r2, #1|bls #0x8046d9e|tst r6, r1|bne #0x8046da6|orrs r6, r1|adds r7, #1|cmp r7, #4|bls #0x8046d7a|b #0x8046de2""",
}


def disasm(code: bytes, addr: int) -> list[str]:
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB | capstone.CS_MODE_MCLASS)
    out, consumed = [], 0
    while True:
        for i in md.disasm(code[consumed:], addr + consumed):
            out.append(f"{i.mnemonic} {i.op_str}".strip())
            consumed += i.size
        if consumed >= len(code):
            return out
        if len(code) - consumed < 2:
            raise ValueError(f"undecodable bytes at {addr + consumed:#x}")
        out.append(".hword %#06x" % int.from_bytes(code[consumed:consumed + 2], "little"))   # data (a table) that is not an instruction
        consumed += 2


def build(stock: bytes):
    if hashlib.sha256(stock).hexdigest() != STOCK_IMAGE_SHA256:
        raise SystemExit("stock image hash mismatch — refusing to patch")
    img = bytearray(stock)
    report = {}
    for name, fn, start, end in (("A", region_a, A_START, A_END),
                                 ("B", region_b, B_START, B_END),
                                 ("C", region_c, C_START, C_END)):
        code, labels = fn().assemble()
        if len(code) > end - start:
            raise SystemExit(f"region {name} overflow: {len(code)} > {end - start}")
        pad = (end - start - len(code)) // 2
        full = code + nop() * pad
        assert len(full) == end - start
        text = disasm(code, start)
        if name in EXPECTED and "|".join(text) != EXPECTED[name]:
            print("\n".join(text))
            raise SystemExit(f"region {name}: disassembly does not match the intended code")
        off = start - BASE
        report[name] = dict(start=hex(start), end=hex(end), used=len(code), nops=pad,
                            stock_sha256=hashlib.sha256(stock[off:off + len(full)]).hexdigest(),
                            listing=text)
        img[off:off + len(full)] = full
    # Version-block marker.  The bootloader (0x08003BE4) only installs a staged
    # image if the 0x26-byte block at image offset 0x1C8 differs from the
    # installed one.  We write a marker into its zero padding (after the
    # NUL-terminated "GB1.1.5143.4486" string); build number, product id and
    # version string are untouched.
    blk = bytes(img[INFO_OFF:INFO_OFF + INFO_LEN])
    assert blk[:6] == bytes.fromhex("010186110164") and blk[6:21] == b"GB1.1.5143.4486"
    assert blk[21:] == bytes(INFO_LEN - 21), "info block padding not zero"
    img[MARK_OFF:MARK_OFF + len(MARKER)] = MARKER
    report["D"] = dict(start=hex(BASE + MARK_OFF), marker=MARKER.decode(),
                       note="version-block padding so the bootloader sees a different image")
    # nothing outside the declared regions may change
    diff = [i for i in range(len(stock)) if stock[i] != img[i]]
    allowed = [(s - BASE, e - BASE) for s, e in ((A_START, A_END), (B_START, B_END), (C_START, C_END))]
    allowed.append((MARK_OFF, MARK_OFF + len(MARKER)))
    assert all(any(s <= i < e for s, e in allowed) for i in diff)
    return bytes(img), report, len(diff)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("stock_bin", type=Path)
    ap.add_argument("-o", "--outdir", type=Path, default=Path("build/shared-channels"))
    args = ap.parse_args()
    stock = args.stock_bin.read_bytes()
    img, report, nchanged = build(stock)
    syx = ct_fw.encode(img)
    info = ct_fw.decode(syx)
    assert info["image"] == img and info["size"] == len(stock)
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / "circuittracks-4486-shared-channels.bin").write_bytes(img)
    (args.outdir / "circuittracks-4486-shared-channels.syx").write_bytes(syx)
    manifest = dict(base="circuittracks-firmware-4486 (1.2.1)", stock_image_sha256=STOCK_IMAGE_SHA256,
                    image_sha256=ct_fw.sha256(img), syx_sha256=ct_fw.sha256(syx), crc32=hex(info["crc"]),
                    size=hex(len(img)), changed_bytes=nchanged, regions=report)
    (args.outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    for k, r in report.items():
        print(f"region {k}: {r}") if 'end' not in r else print(f"region {k}: {r['start']}..{r['end']} used {r['used']} bytes (+{r['nops']} nop)")
        for line in r.get("listing", []):
            print("    ", line)
    print("changed bytes:", nchanged)
    print("image sha256:", manifest["image_sha256"])
    print("syx   sha256:", manifest["syx_sha256"], "crc", manifest["crc32"])
