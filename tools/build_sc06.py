"""Circuit Tracks 4486 — SC06 = SC05 + Patch Flip mode for MIDI 1 / MIDI 2.

In the MIDI track Preset (Template) view the bottom row was empty; pad 25
(bottom-left) is now the PATCH FLIP toggle for the selected MIDI track:
  purple bright = on, purple dim = off (stock PGM-toggle colours).
When on, a Note On of that MIDI track (pads or sequencer) is sent as a Program
Change with program = note number on the track's channel, instead of a note:
  * externally (MIDI OUT/USB) if PGM Tx is enabled;
  * internally (SC05 loopback) if the channel equals the Synth 1 / Synth 2 /
    Drums program-receive channel (respects PGM Rx);
  * Note Off is suppressed.
Stored in settings param 2, bit 26 (MIDI 1) / bit 27 (MIDI 2); copied on every
settings apply into tx flags byte [X+0x18] bits 5 / 6.

Settings are reached through a fixed global: [[0x200069E4]] = settings-apply
object L; [L+0x54] = settings store (verified in the live RAM dump).
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
import build_sc05 as s5  # noqa: E402
from thumb import (Asm, b, b_cond, b_w, bl, bx_lr, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, ldrb_reg,  # noqa: E402
                   lsls_imm, lsls_reg, lsrs_imm, mov_reg, movs_imm, movt, movw, orrs_reg, bics_reg, pop_list,
                   push_list, raw, strb_imm, subs_imm3, add_sp_imm, sub_sp_imm, ands_reg, eors_reg, str_imm,
                   strh_imm, ldrh_reg, it, adds_imm8, subs_imm8, cbz)

BASE = ct_fw.APP_BASE
MARKER = b"SC06"
CTX_PTR = s5.CTX_PTR
PARAM_GET, PARAM_PTR, COMMIT = 0x0803542C, 0x080354FA, 0x080353C0
T_PAD, T_PAD_STOCK, T_PAD_RET = 0x0804D59E, 0x0804D5A4, 0x0804D5C0
T_DRAW_HOOK, T_DRAW = 0x0804D5F0, 0x0804D5CA
TXF_HOOK = 0x08035066
PF_PAD = 24                      # pad 25 = bottom-left
PF_ON_COL, PF_OFF_COL = 0x02, 0x12   # palette byte offsets (stock PGM toggle on/off)
PALETTE = 0x08056464
# --- SC07 fixes (v2)
VT_TLEDS = 0x0805AE78            # template vtable slot 7: get-LED-buffer (stock 0x08047593)
SAVE_M1, SAVE_M2 = 0x0802D348, 0x0802D352   # "settings changed?" (0x0802D300): param-2 compare mask (stock bits 0-18)
SAVE_MASK = 0x0F07FFFF           # SC07: bits 0-18 as stock + 24-27 (Ch16, patch flip)


def ext_code(base: int, stock: bytes, v2: bool = False):
    a = Asm(base)
    # ----------------------------------------------------------- shared helpers
    a.label("c_inject")                        # (r0 = msg) internal dispatch, recorder-gated
    a.emit(push_list, [4, 5], lr=True)
    a.emit(mov_reg, 5, 0)
    a.emit(movw, 1, s5.MIDI_IN_FLAG & 0xFFFF); a.emit(movt, 1, s5.MIDI_IN_FLAG >> 16)
    a.emit(ldr_imm, 1, 1, 0)
    a.emit(lsls_imm, 1, 1, 29)
    a.emit(b_cond, "inj_out", "mi")
    a.emit(movw, 4, CTX_PTR & 0xFFFF); a.emit(movt, 4, CTX_PTR >> 16)
    a.emit(ldr_imm, 4, 4, 0)
    a.emit(cmp_imm, 4, 0)
    a.emit(b_cond, "inj_out", "eq")
    a.emit(ldrb_imm, 1, 4, 0x14); a.emit(movs_imm, 2, 0x20); a.emit(orrs_reg, 1, 2); a.emit(strb_imm, 1, 4, 0x14)
    a.emit(mov_reg, 1, 5); a.emit(mov_reg, 0, 4)
    a.emit(bl, s5.DISPATCH)
    a.emit(ldrb_imm, 1, 4, 0x14); a.emit(movs_imm, 2, 0x20); a.emit(bics_reg, 1, 2); a.emit(strb_imm, 1, 4, 0x14)
    a.label("inj_out")
    a.emit(pop_list, [4, 5], pc=True)

    a.label("c_injB")                          # (r0 = msg) inject if channel is a Synth1/Synth2/Drums CC/PC-rx channel
    a.emit(push_list, [4], lr=True)
    a.emit(mov_reg, 4, 0)
    a.emit(ldrb_imm, 0, 4, 0)
    a.emit(lsls_imm, 0, 0, 28); a.emit(lsrs_imm, 0, 0, 28)
    a.emit(movw, 1, CTX_PTR & 0xFFFF); a.emit(movt, 1, CTX_PTR >> 16)
    a.emit(ldr_imm, 1, 1, 0)
    a.emit(cmp_imm, 1, 0)
    a.emit(b_cond, "injb_out", "eq")
    for off in (9, 10):
        a.emit(ldrb_imm, 2, 1, off); a.emit(cmp_reg, 0, 2); a.emit(b_cond, "injb_go", "eq")
    a.emit(ldrb_imm, 2, 1, 11); a.emit(cmp_reg, 0, 2); a.emit(b_cond, "injb_out", "ne")
    a.label("injb_go")
    a.emit(mov_reg, 0, 4)
    a.emit(bl, "c_inject")
    a.label("injb_out")
    a.emit(pop_list, [4], pc=True)

    a.label("c_settings")                      # -> r0 = settings store or 0 (clobbers r0)
    a.emit(movw, 0, CTX_PTR & 0xFFFF); a.emit(movt, 0, CTX_PTR >> 16)
    a.emit(ldr_imm, 0, 0, 0)
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "set_out", "eq")
    a.emit(ldr_imm, 0, 0, 0)                   # L
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "set_out", "eq")
    a.emit(ldr_imm, 0, 0, 0x54)                # settings store
    a.label("set_out")
    a.emit(bx_lr)

    # ----------------------------------------------------------- note wrappers
    for name, orig, status in (("c_non", s5.NOTE_ON, 0x90), ("c_noff", s5.NOTE_OFF, 0x80)):
        a.label(name)
        a.emit(push_list, [4, 5, 6, 7], lr=True)
        a.emit(sub_sp_imm, 12)
        a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2); a.emit(mov_reg, 7, 3)
        # patch-flip mode?
        a.emit(subs_imm3, 0, 5, 2)
        a.emit(cmp_imm, 0, 1)
        a.emit(b_cond, f"{name}_normal", "hi")
        a.emit(ldrb_imm, 1, 4, 0x18)
        a.emit(adds_imm8, 0, 5)                # bit 5 (MIDI 1) / 6 (MIDI 2)
        a.emit(movs_imm, 2, 1); a.emit(lsls_reg, 2, 0)
        a.emit(ands_reg, 1, 2)
        a.emit(b_cond, f"{name}_normal", "eq")
        if status == 0x80:
            a.emit(b, f"{name}_done")          # PF: note off suppressed
        else:
            a.emit(ldr_imm, 0, 4, 0x0C)
            a.emit(ldrb_reg, 1, 0, 5)          # channel of the MIDI track
            a.emit(mov_reg, 3, 13)
            a.emit(movs_imm, 0, 0xC0); a.emit(orrs_reg, 0, 1)
            a.emit(strb_imm, 0, 3, 0)
            a.emit(movs_imm, 0, 0x7F); a.emit(ands_reg, 0, 6)
            a.emit(strb_imm, 0, 3, 1)          # program = note
            a.emit(ldrb_imm, 2, 4, 0x18)
            a.emit(lsls_imm, 2, 2, 29)         # PGM Tx (bit 2) -> N
            a.emit(b_cond, "pf_noext", "pl")
            a.emit(movs_imm, 0, 7); a.emit(mov_reg, 1, 13)
            a.emit(bl, s5.SEND)
            a.label("pf_noext")
            a.emit(mov_reg, 0, 13)
            a.emit(bl, "c_injB")
            a.emit(b, f"{name}_done")
        a.label(f"{name}_normal")              # ---- SC05 behaviour
        a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6); a.emit(mov_reg, 3, 7)
        a.emit(bl, orig)
        a.emit(subs_imm3, 0, 5, 2)
        a.emit(cmp_imm, 0, 1)
        a.emit(b_cond, f"{name}_done", "hi")
        a.emit(ldr_imm, 0, 4, 0x0C)
        a.emit(ldrb_reg, 1, 0, 5)
        a.emit(ldrb_imm, 2, 0, 0); a.emit(cmp_reg, 1, 2); a.emit(b_cond, f"{name}_go", "eq")
        a.emit(ldrb_imm, 2, 0, 1); a.emit(cmp_reg, 1, 2); a.emit(b_cond, f"{name}_done", "ne")
        a.label(f"{name}_go")
        a.emit(mov_reg, 3, 13)
        a.emit(movs_imm, 0, status); a.emit(orrs_reg, 0, 1)
        a.emit(strb_imm, 0, 3, 0); a.emit(strb_imm, 6, 3, 1); a.emit(strb_imm, 7, 3, 2)
        a.emit(mov_reg, 0, 3)
        a.emit(bl, "c_inject")
        a.label(f"{name}_done")
        a.emit(add_sp_imm, 12)
        a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ----------------------------------------------------------- template CC helper (as SC05)
    a.label("c_cc")
    a.emit(push_list, [4], lr=True)
    a.emit(sub_sp_imm, 8)
    a.emit(orrs_reg, 0, 1)
    a.emit(mov_reg, 4, 13)
    a.emit(strb_imm, 0, 4, 0); a.emit(strb_imm, 2, 4, 1); a.emit(strb_imm, 3, 4, 2)
    a.emit(mov_reg, 1, 4); a.emit(movs_imm, 0, 7)
    a.emit(bl, s5.SEND)
    a.emit(mov_reg, 0, 4)
    a.emit(bl, "c_injB")
    a.emit(add_sp_imm, 8)
    a.emit(pop_list, [4], pc=True)

    # ----------------------------------------------------------- recorder gates (as SC05)
    for addr in s5.GATES:
        name = f"c_gate_{addr:x}"
        a.label(name)
        a.emit(push_list, [0, 1])
        a.emit(movw, 0, CTX_PTR & 0xFFFF); a.emit(movt, 0, CTX_PTR >> 16)
        a.emit(ldr_imm, 0, 0, 0)
        a.emit(cmp_imm, 0, 0); a.emit(b_cond, f"{name}_rec", "eq")
        a.emit(ldrb_imm, 0, 0, 0x14)
        a.emit(lsls_imm, 0, 0, 26)
        a.emit(b_cond, f"{name}_rec", "pl")
        a.emit(pop_list, [0, 1]); a.emit(movs_imm, 0, 1); a.emit(bx_lr)
        a.label(f"{name}_rec")
        a.emit(pop_list, [0, 1])
        a.emit(raw, stock[addr - BASE:addr - BASE + 4])
        a.emit(b_w, addr + 4)

    # ----------------------------------------------------------- tx flags (replaces SC04 c_txf)
    a.label("c_txf2")                          # bl from 0x08035066; r1 flags, r5 -> param2, r4 apply obj
    for shift, bit in ((6, 0x10), (5, 0x20), (4, 0x40)):   # bit25 -> 0x10, bit26 -> 0x20, bit27 -> 0x40
        lab = f"txf_{bit:x}"
        a.emit(ldr_imm, 3, 5, 0)
        a.emit(lsls_imm, 3, 3, shift)
        a.emit(b_cond, lab, "pl")
        a.emit(movs_imm, 3, bit); a.emit(orrs_reg, 1, 3)
        a.label(lab)
    a.emit(ldr_imm, 0, 4, 0x1C)
    a.emit(strb_imm, 1, 0, 0x18)
    a.emit(bx_lr)

    # ----------------------------------------------------------- template view: pad handler
    a.label("c_tpad")                          # b.w from 0x0804D59E; r0 this, r5 pad (r4,r5 saved by host)
    a.emit(mov_reg, 4, 0)
    a.emit(cmp_imm, 5, 8)
    a.emit(b_cond, "tpad_hi", "hs")
    a.emit(b_w, T_PAD_STOCK)                   # stock template selection
    a.label("tpad_hi")
    a.emit(cmp_imm, 5, PF_PAD)
    a.emit(b_cond, "tpad_tog", "eq")
    a.label("tpad_ret")
    a.emit(b_w, T_PAD_RET)
    a.label("tpad_tog")
    a.emit(bl, "c_settings")
    a.emit(cmp_imm, 0, 0)
    a.emit(b_cond, "tpad_ret", "eq")
    a.emit(movs_imm, 1, 2)
    a.emit(bl, PARAM_PTR)
    a.emit(ldr_imm, 1, 0, 0)
    a.emit(ldrb_imm, 2, 4, 0x10)
    a.emit(movs_imm, 3, 1); a.emit(ands_reg, 2, 3)      # 0 = MIDI 1, 1 = MIDI 2
    a.emit(movs_imm, 3, 1); a.emit(lsls_imm, 3, 3, 26); a.emit(lsls_reg, 3, 2)
    a.emit(eors_reg, 1, 3)
    a.emit(str_imm, 1, 0, 0)
    a.emit(bl, "c_settings")
    a.emit(bl, COMMIT)                         # notify listeners -> apply -> tx flags
    a.emit(mov_reg, 0, 4)
    a.emit(bl, T_DRAW)                         # redraw the view
    a.emit(b_w, T_PAD_RET)

    if not v2:
        # ----------------------------------------------------------- template view: draw (bl from 0x0804D5F0)
        a.label("c_tdraw")                         # r4 this, r5 palette, r0 = template-index ptr (keep)
        a.emit(push_list, [1], lr=True)            # r1 dead in host after the hook
        a.emit(mov_reg, 6, 0)                      # r6 free in host
        a.emit(bl, "c_settings")
        a.emit(cmp_imm, 0, 0)
        a.emit(b_cond, "tdraw_out", "eq")
        a.emit(movs_imm, 1, 2)
        a.emit(bl, PARAM_GET)
        a.emit(ldr_imm, 0, 0, 0)
        a.emit(ldrb_imm, 2, 4, 0x10)
        a.emit(movs_imm, 3, 1); a.emit(ands_reg, 2, 3)
        a.emit(movs_imm, 3, 5); a.emit(raw, bytes.fromhex("9b1a"))    # subs r3, r3, r2
        a.emit(lsls_reg, 0, 3)                     # bit (26 + track) -> N
        a.emit(it, "mi", "e")
        a.emit(movs_imm, 1, PF_ON_COL)
        a.emit(movs_imm, 1, PF_OFF_COL)
        a.emit(ldrh_reg, 1, 5, 1)
        a.emit(ldr_imm, 3, 4, 4); a.emit(ldr_imm, 3, 3, 0)
        a.emit(strh_imm, 1, 3, PF_PAD * 2)
        a.label("tdraw_out")
        a.emit(mov_reg, 0, 6)
        a.emit(raw, stock[T_DRAW_HOOK - BASE:T_DRAW_HOOK - BASE + 4])   # ldrh r2,[r4,#0x18]; ldr r3,[r4,#4]
        a.emit(pop_list, [1], pc=True)
    else:
        a.label("c_tpaint")                    # (r0 = view) paint pad 24 from param 2; keeps r4-r7
        a.emit(push_list, [4], lr=True)
        a.emit(mov_reg, 4, 0)
        a.emit(bl, "c_settings")
        a.emit(cmp_imm, 0, 0)
        a.emit(b_cond, "tpaint_out", "eq")
        a.emit(movs_imm, 1, 2)
        a.emit(bl, PARAM_GET)
        a.emit(ldr_imm, 0, 0, 0)
        a.emit(ldrb_imm, 2, 4, 0x10)
        a.emit(movs_imm, 3, 1); a.emit(ands_reg, 2, 3)
        a.emit(movs_imm, 3, 5); a.emit(raw, bytes.fromhex("9b1a"))    # subs r3, r3, r2
        a.emit(lsls_reg, 0, 3)                 # bit (26 + track) -> N
        a.emit(movw, 2, PALETTE & 0xFFFF); a.emit(movt, 2, PALETTE >> 16)
        a.emit(it, "mi", "e")
        a.emit(movs_imm, 1, PF_ON_COL)
        a.emit(movs_imm, 1, PF_OFF_COL)
        a.emit(ldrh_reg, 1, 2, 1)
        a.emit(ldr_imm, 3, 4, 4); a.emit(ldr_imm, 3, 3, 0)
        a.emit(strh_imm, 1, 3, PF_PAD * 2)
        a.label("tpaint_out")
        a.emit(pop_list, [4], pc=True)

        a.label("c_tleds")                     # vtable slot 7: paint, then return the LED buffer
        a.emit(push_list, [4], lr=True)
        a.emit(mov_reg, 4, 0)
        a.emit(bl, "c_tpaint")
        a.emit(ldr_imm, 0, 4, 4); a.emit(ldr_imm, 0, 0, 0)
        a.emit(pop_list, [4], pc=True)

        a.label("c_tdraw")                     # bl from 0x0804D5F0: r4 this, r0 kept
        a.emit(push_list, [1], lr=True)
        a.emit(mov_reg, 6, 0)
        a.emit(mov_reg, 0, 4)
        a.emit(bl, "c_tpaint")
        a.emit(mov_reg, 0, 6)
        a.emit(raw, stock[T_DRAW_HOOK - BASE:T_DRAW_HOOK - BASE + 4])
        a.emit(pop_list, [1], pc=True)

        a.label("c_m1")                        # bl from 0x0802D348: r1 = r2 & mask (r2 reloaded by host)
        a.emit(movw, 1, SAVE_MASK & 0xFFFF); a.emit(movt, 1, SAVE_MASK >> 16)
        a.emit(ands_reg, 1, 2)
        a.emit(bx_lr)
        a.label("c_m2")                        # bl from 0x0802D352: r2 &= mask (r3 dead in host)
        a.emit(movw, 3, SAVE_MASK & 0xFFFF); a.emit(movt, 3, SAVE_MASK >> 16)
        a.emit(ands_reg, 2, 3)
        a.emit(bx_lr)
    return a.assemble()


def build(stock: bytes, listing: Path, v2: bool = False):
    img4, report = s4.build(stock, listing)
    img = bytearray(img4)
    marker = b"SC07" if v2 else MARKER
    img[sc.MARK_OFF:sc.MARK_OFF + 4] = marker
    ext_base = (len(img4) + BASE + 3) & ~3
    code, labels = ext_code(ext_base, stock, v2)

    def text(addr, n, src=stock):
        return "|".join(sc.disasm(bytes(src[addr - BASE:addr - BASE + n]), addr))
    checks = dict(s5.GATES)
    checks[s5.CC_HELPER] = "push {r7, lr}|orrs r0, r1"
    checks[T_PAD] = "cmp r5, #8|mov r4, r0"
    checks[T_DRAW_HOOK] = "ldrh r2, [r4, #0x18]|ldr r3, [r4, #4]"
    if v2:
        checks[SAVE_M1] = "ubfx r1, r2, #0, #0x13"
        checks[SAVE_M2] = "ubfx r2, r2, #0, #0x13"
        assert struct.unpack_from("<I", stock, VT_TLEDS - BASE)[0] == 0x08047593
    for addr, want in checks.items():
        if text(addr, 4) != want:
            raise SystemExit(f"{addr:#x}: '{text(addr, 4)}' != '{want}'")
    if text(TXF_HOOK, 4, img) != f"bl #{report['cave']['labels']['c_txf']}":
        raise SystemExit("SC04 tx-flags hook not found: " + text(TXF_HOOK, 4, img))
    for vt, fn in ((s5.VT_NOTE_ON, s5.NOTE_ON), (s5.VT_NOTE_OFF, s5.NOTE_OFF)):
        assert struct.unpack_from("<I", stock, vt - BASE)[0] == fn | 1
    targets = s4.branch_targets(listing)
    for addr in list(checks):
        for x in range(addr + 1, addr + 4):
            if x in targets:
                raise SystemExit(f"branch into patched bytes at {x:#x}")
    for addr in s5.GATES:
        img[addr - BASE:addr - BASE + 4] = b_w(addr, labels[f"c_gate_{addr:x}"])
    img[s5.CC_HELPER - BASE:s5.CC_HELPER - BASE + 4] = b_w(s5.CC_HELPER, labels["c_cc"])
    img[T_PAD - BASE:T_PAD - BASE + 4] = b_w(T_PAD, labels["c_tpad"])
    img[T_DRAW_HOOK - BASE:T_DRAW_HOOK - BASE + 4] = bl(T_DRAW_HOOK, labels["c_tdraw"])
    img[TXF_HOOK - BASE:TXF_HOOK - BASE + 4] = bl(TXF_HOOK, labels["c_txf2"])
    struct.pack_into("<I", img, s5.VT_NOTE_ON - BASE, labels["c_non"] | 1)
    struct.pack_into("<I", img, s5.VT_NOTE_OFF - BASE, labels["c_noff"] | 1)
    if v2:
        img[SAVE_M1 - BASE:SAVE_M1 - BASE + 4] = bl(SAVE_M1, labels["c_m1"])
        img[SAVE_M2 - BASE:SAVE_M2 - BASE + 4] = bl(SAVE_M2, labels["c_m2"])
        struct.pack_into("<I", img, VT_TLEDS - BASE, labels["c_tleds"] | 1)
    img += b"\xFF" * (ext_base - BASE - len(img)) + code
    while len(img) % 4:
        img += b"\xFF"
    assert len(img) <= 0x70000
    report["D"]["marker"] = marker.decode()
    report["sc06"] = dict(start=hex(ext_base), size=len(code), labels={k: hex(v) for k, v in labels.items()},
                          listing=sc.disasm(code, ext_base))
    return bytes(img), report


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("stock_bin", type=Path)
    ap.add_argument("--listing", type=Path, default=Path(__file__).resolve().parents[1] / "re/app.asm")
    ap.add_argument("-o", "--outdir", type=Path)
    ap.add_argument("--v2", action="store_true", help="SC07: SC06 + LED on view entry + save bits 24-27")
    args = ap.parse_args()
    stock = args.stock_bin.read_bytes()
    img, report = build(stock, args.listing, args.v2)
    name = "SC07" if args.v2 else "SC06"
    args.outdir = args.outdir or Path("build") / name.lower()
    syx = ct_fw.encode(img)
    info = ct_fw.decode(syx)
    assert info["image"] == img
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / f"circuittracks-4486-{name}.bin").write_bytes(img)
    (args.outdir / f"circuittracks-4486-{name}.syx").write_bytes(syx)
    manifest = dict(base="circuittracks-firmware-4486 (1.2.1)", marker=name, image_size=hex(len(img)),
                    image_sha256=ct_fw.sha256(img), syx_sha256=ct_fw.sha256(syx), crc32=hex(info["crc"]), report=report)
    (args.outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("ext", report["sc06"]["start"], report["sc06"]["size"], "bytes; image", hex(len(img)))
    print("syx sha", manifest["syx_sha256"], "crc", manifest["crc32"])
