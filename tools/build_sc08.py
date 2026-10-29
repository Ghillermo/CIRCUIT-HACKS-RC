"""Circuit Tracks 4486 — SC08 = SC07 + chromatic drum Preset view.

Shift + Preset (with a drum track selected) toggles, for that drum track, a
chromatic/scale keyboard in the drum Preset view:
  * the 32 pads play the track's current sample transposed, following the
    project's scale and root (Scales view);
      - 7/6/5-note scales: 4 rows, bottom row = one octave below the root,
        each row = 8 consecutive scale degrees (like the synth Note view);
      - Chromatic: piano layout, white keys on the lower row of each pair,
        black keys above, two octaves (lower pair = octave below the root);
  * the pitch is set through the stock drum Pitch parameter (64 = original,
    1 step = 1 semitone; sample assumed tuned to C) via the same setter the
    Preset view uses for sample selection, so it is recorded as Pitch
    automation while recording; the hit is the stock Preset-view note.
  * LEDs: root = bright track colour, other scale notes = dim track colour,
    unused pads off.
Flag: bit 0 of byte +0x51 of each drum Preset view object (padding inside the
0x54-byte allocation, zeroed by turning the constructor's strb #1 to +0x50
into strh). Not persistent (off after power-up).
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
import build_sc06 as s6  # noqa: E402
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, lsls_imm, lsrs_imm, mov_reg,  # noqa: E402
                   movs_imm, movt, movw, pop_list, push_list, strb_imm, subs_imm3, subs_imm8, adds_imm8, adds_imm3,
                   ands_reg, eors_reg, lsrs_reg, muls, blx_reg, adds_reg, subs_reg, ldrh_imm, ldrh_reg, strb_reg,
                   strh_reg, strh_w_imm, add_sp_imm, sub_sp_imm, raw, ldrb_reg, ldrb_w, strb_w)

BASE = ct_fw.APP_BASE
MARKER = b"SC08"
PALETTE = 0x08056464
PARAM_GET = 0x0803542C
ROUTER_VT = 0x0805B840          # vtable of the sequencer object at [[view+0xC]+0x3C] (sanity check)
DP_VT = 0x0805ABBC              # drum Preset view vtable (slot 0 pad press, slot 7 get-LEDs)
DP_PAD = 0x0804D934             # stock pad press
NOTE_OFF_PREV = 0x0804E0E8      # end pending Preset-view note
NOTE_ON = 0x0804E0BA            # (view, pad, vel): stock Preset-view hit
DRAW_PAD = 0x0804DAEC           # (view, sample, colour index): paint one sample pad if on current page
CTOR_STRB = 0x0804D89C          # strb.w r0,[r5,#0x50] in the constructor -> strh.w (zeroes +0x51)
SHIFT_BTN = 0x080333B2          # controller button handler, Shift-held path: ldr.w r1,=0x07DBBE00
SHIFT_MASK = 0x07DBBE00
SHIFT_NEXT, PRESET_CASE = 0x080333B6, 0x080334B2
TRACK_OF = 0x0805011E           # (track-view container) -> selected track 0..7
FLAG = 0x51
TRIM = False                    # SC49 (use_trim): c_dpad / c_shbtn not emitted (build_sc11 replaces both hooks with c_dpad2 / c_shbtn2)
ROWS3 = False                   # SC20.1: the scale keyboards use the three bottom rows only (the top row, pads 1-8, is dark and does nothing)


def use_trim():
    """SC49 (flash for the extra drum lane): build_sc11 puts c_dpad2 / c_shbtn2 on the two hooks, and nothing calls c_dpad / c_shbtn (checked on
    SC48.9's image): not emitted, their hooks left to build_sc11."""
    global TRIM
    TRIM = True


def ext_code(base: int):
    a = Asm(base)
    # -------- c_scale(view, ctx): ctx[0]=root, ctx[1]=N, ctx[2..]=intervals; r0=0 ok
    a.label("c_scale")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 7, 1)
    a.emit(ldr_imm, 0, 0, 0x0C)
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sc_fail", "eq")
    a.emit(ldr_imm, 1, 0, 0x3C)
    a.emit(movw, 2, ROUTER_VT & 0xFFFF); a.emit(movt, 2, ROUTER_VT >> 16)
    a.emit(cmp_reg, 1, 2); a.emit(b_cond, "sc_fail", "ne")
    a.emit(ldr_imm, 2, 0, 0x48); a.emit(ldrb_imm, 2, 2, 0); a.emit(strb_imm, 2, 7, 0)   # root
    a.emit(ldr_imm, 3, 0, 0x44); a.emit(ldr_imm, 6, 3, 4)                                # scale mask
    a.emit(movs_imm, 4, 0); a.emit(movs_imm, 5, 0)
    a.label("sc_loop")
    a.emit(lsls_imm, 2, 4, 1); a.emit(mov_reg, 3, 6); a.emit(lsrs_reg, 3, 2)
    a.emit(movs_imm, 2, 3); a.emit(ands_reg, 3, 2); a.emit(b_cond, "sc_skip", "ne")
    a.emit(adds_imm3, 2, 5, 2); a.emit(strb_reg, 4, 7, 2); a.emit(adds_imm8, 5, 1)
    a.label("sc_skip")
    a.emit(adds_imm8, 4, 1); a.emit(cmp_imm, 4, 12); a.emit(b_cond, "sc_loop", "lo")
    a.emit(strb_imm, 5, 7, 1)
    a.emit(cmp_imm, 5, 0); a.emit(b_cond, "sc_fail", "eq")
    a.emit(movs_imm, 0, 0); a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("sc_fail")
    a.emit(movs_imm, 0, 1); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # -------- c_padval(ctx, pad): r0 = pitch value 0..127 or 0xFF (unused), r1 = is root
    a.label("c_padval")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 7, 0)
    a.emit(lsrs_imm, 2, 1, 3); a.emit(movs_imm, 3, 3); a.emit(subs_reg, 4, 3, 2)          # r4 = row from bottom
    a.emit(movs_imm, 3, 7); a.emit(ands_reg, 1, 3); a.emit(mov_reg, 5, 1)                # r5 = column
    a.emit(ldrb_imm, 6, 7, 1)                                                            # N
    a.emit(cmp_imm, 6, 12); a.emit(b_cond, "pv_chroma", "eq")
    if ROWS3:
        a.emit(cmp_imm, 4, 3); a.emit(b_cond, "pv_unused", "eq")                        # scale keyboard: no top row
    # scale keyboard: d = (row-1)*N + col
    a.emit(subs_imm3, 0, 4, 1); a.emit(muls, 0, 6); a.emit(adds_reg, 0, 0, 5)
    a.emit(movs_imm, 4, 0)
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "pv_pos", "ge")
    a.emit(adds_reg, 0, 0, 6); a.emit(subs_imm8, 4, 1); a.emit(b, "pv_mod")
    a.label("pv_pos")
    a.emit(cmp_reg, 0, 6); a.emit(b_cond, "pv_mod", "lt")
    a.emit(subs_reg, 0, 0, 6); a.emit(adds_imm8, 4, 1); a.emit(b, "pv_pos")
    a.label("pv_mod")                                                                    # r0 idx, r4 octave
    a.emit(movs_imm, 1, 0); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "pv_nr", "ne"); a.emit(movs_imm, 1, 1)
    a.label("pv_nr")
    a.emit(adds_imm3, 2, 0, 2); a.emit(ldrb_reg, 2, 7, 2)                                # interval
    a.emit(b, "pv_combine")
    a.label("pv_chroma")                                                                 # piano layout
    a.emit(movs_imm, 3, 1); a.emit(ands_reg, 3, 4)                                       # r3 = black row
    a.emit(lsrs_imm, 4, 4, 1); a.emit(subs_imm8, 4, 1)                                   # octave
    a.emit(cmp_imm, 3, 0); a.emit(b_cond, "pv_black", "ne")
    a.emit(movw, 0, 0x0200); a.emit(movt, 0, 0x0504); a.emit(movw, 1, 0x0907); a.emit(movt, 1, 0x0C0B)
    a.emit(b, "pv_sel")
    a.label("pv_black")
    a.emit(movw, 0, 0x01FF); a.emit(movt, 0, 0xFF03); a.emit(movw, 1, 0x0806); a.emit(movt, 1, 0xFF0A)
    a.label("pv_sel")
    a.emit(cmp_imm, 5, 4); a.emit(b_cond, "pv_lo", "lt")
    a.emit(mov_reg, 0, 1); a.emit(subs_imm8, 5, 4)
    a.label("pv_lo")
    a.emit(lsls_imm, 5, 5, 3); a.emit(lsrs_reg, 0, 5); a.emit(movs_imm, 3, 0xFF); a.emit(ands_reg, 0, 3)
    a.emit(mov_reg, 2, 0)
    a.emit(cmp_imm, 2, 0xFF); a.emit(b_cond, "pv_unused", "eq")
    a.emit(movs_imm, 1, 0)
    a.emit(cmp_imm, 2, 0); a.emit(b_cond, "pv_root", "eq")
    a.emit(cmp_imm, 2, 12); a.emit(b_cond, "pv_combine", "ne")
    a.label("pv_root")
    a.emit(movs_imm, 1, 1)
    a.label("pv_combine")                                                                # r2 semis, r4 oct, r1 root
    a.emit(movs_imm, 0, 12); a.emit(muls, 0, 4); a.emit(adds_reg, 0, 0, 2)
    a.emit(ldrb_imm, 3, 7, 0); a.emit(adds_reg, 0, 0, 3); a.emit(adds_imm8, 0, 64)
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "pv_c1", "ge"); a.emit(movs_imm, 0, 0)
    a.label("pv_c1")
    a.emit(cmp_imm, 0, 127); a.emit(b_cond, "pv_c2", "le"); a.emit(movs_imm, 0, 127)
    a.label("pv_c2")
    a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("pv_unused")
    a.emit(movs_imm, 0, 0xFF); a.emit(movs_imm, 1, 0); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    if not TRIM:
        # -------- c_dpad: drum Preset view vtable slot 0 (view, pad, vel)
        a.label("c_dpad")
        a.emit(ldrb_w, 3, 0, FLAG); a.emit(lsls_imm, 3, 3, 31); a.emit(b_cond, "dp_chrom", "ne")
        a.emit(b_w, DP_PAD)
        a.label("dp_chrom")
        a.emit(push_list, [4, 5, 6], lr=True); a.emit(sub_sp_imm, 16)
        a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2)
        a.emit(mov_reg, 1, 13); a.emit(bl, "c_scale"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "dp_out", "ne")
        a.emit(mov_reg, 0, 13); a.emit(mov_reg, 1, 5); a.emit(bl, "c_padval")
        a.emit(cmp_imm, 0, 0xFF); a.emit(b_cond, "dp_out", "eq")
        a.emit(mov_reg, 2, 0)
        a.emit(ldr_imm, 0, 4, 0x0C); a.emit(ldrb_w, 1, 4, 0x24); a.emit(subs_imm8, 1, 4)   # pitch id = patch id - 4
        a.emit(ldr_imm, 3, 0, 0); a.emit(ldr_imm, 3, 3, 0); a.emit(blx_reg, 3)               # set (and record) Pitch
        a.emit(mov_reg, 0, 4); a.emit(bl, NOTE_OFF_PREV)
        a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6); a.emit(bl, NOTE_ON)
        a.label("dp_out")
        a.emit(add_sp_imm, 16); a.emit(pop_list, [4, 5, 6], pc=True)

    # -------- c_dleds: drum Preset view vtable slot 7 (get LED buffer)
    a.label("c_dleds")
    a.emit(push_list, [4, 5, 6, 7], lr=True); a.emit(sub_sp_imm, 20)
    a.emit(mov_reg, 4, 0)
    a.emit(ldrb_w, 3, 4, FLAG); a.emit(lsls_imm, 3, 3, 31); a.emit(b_cond, "dl_done", "eq")
    a.emit(mov_reg, 1, 13); a.emit(mov_reg, 0, 4); a.emit(bl, "c_scale")
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "dl_done", "ne")
    a.emit(movs_imm, 5, 0)
    a.label("dl_loop")
    a.emit(mov_reg, 0, 13); a.emit(mov_reg, 1, 5); a.emit(bl, "c_padval")
    a.emit(movs_imm, 2, 0)
    a.emit(cmp_imm, 0, 0xFF); a.emit(b_cond, "dl_col", "eq")
    a.emit(ldrh_imm, 2, 4, 0x26)
    a.emit(cmp_imm, 1, 0); a.emit(b_cond, "dl_col", "ne"); a.emit(adds_imm8, 2, 2)
    a.label("dl_col")
    a.emit(lsls_imm, 2, 2, 1); a.emit(movw, 3, PALETTE & 0xFFFF); a.emit(movt, 3, PALETTE >> 16)
    a.emit(ldrh_reg, 2, 3, 2)
    a.emit(ldr_imm, 3, 4, 4); a.emit(ldr_imm, 3, 3, 0); a.emit(lsls_imm, 1, 5, 1); a.emit(strh_reg, 2, 3, 1)
    a.emit(adds_imm8, 5, 1); a.emit(cmp_imm, 5, 32); a.emit(b_cond, "dl_loop", "lo")
    a.label("dl_done")
    a.emit(ldr_imm, 0, 4, 4); a.emit(ldr_imm, 0, 0, 0)
    a.emit(add_sp_imm, 20); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # -------- c_dstock(view): repaint the stock Preset view (as the constructor does)
    a.label("c_dstock")
    a.emit(push_list, [4, 5, 6], lr=True)
    a.emit(mov_reg, 4, 0)
    a.emit(ldrh_imm, 2, 4, 0x26); a.emit(adds_imm8, 2, 2); a.emit(lsls_imm, 2, 2, 1)
    a.emit(movw, 3, PALETTE & 0xFFFF); a.emit(movt, 3, PALETTE >> 16); a.emit(ldrh_reg, 2, 3, 2)
    a.emit(ldr_imm, 3, 4, 4); a.emit(ldr_imm, 3, 3, 0)
    a.emit(movs_imm, 5, 0)
    a.label("ds_loop")
    a.emit(lsls_imm, 1, 5, 1); a.emit(strh_reg, 2, 3, 1)
    a.emit(adds_imm8, 5, 1); a.emit(cmp_imm, 5, 32); a.emit(b_cond, "ds_loop", "lo")
    a.emit(ldr_imm, 0, 4, 0x2C); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET)
    a.emit(ldrb_imm, 1, 0, 0); a.emit(cmp_imm, 1, 0xFF); a.emit(b_cond, "ds_out", "eq")
    a.emit(ldrh_imm, 2, 4, 0x26); a.emit(adds_imm8, 2, 1)
    a.emit(mov_reg, 0, 4); a.emit(bl, DRAW_PAD)
    a.label("ds_out")
    a.emit(pop_list, [4, 5, 6], pc=True)

    if not TRIM:
        # -------- c_shbtn: b.w from 0x080333B2 (Shift held), r4 = controller, r5 = button
        a.label("c_shbtn")
        a.emit(cmp_imm, 5, 8); a.emit(b_cond, "sb_stock", "ne")                              # 8 = Preset
        a.emit(ldr_imm, 0, 4, 0x2C); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sb_stock", "eq")
        a.emit(bl, TRACK_OF)
        a.emit(subs_imm3, 1, 0, 4); a.emit(cmp_imm, 1, 3); a.emit(b_cond, "sb_stock", "hi")    # drums only
        a.emit(ldr_imm, 0, 4, 0x2C); a.emit(lsls_imm, 1, 1, 2); a.emit(adds_reg, 0, 0, 1)
        a.emit(adds_imm8, 0, 0x8C); a.emit(ldr_imm, 0, 0, 0)                                 # drum Preset view
        a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sb_stock", "eq")
        a.emit(ldr_imm, 1, 0, 0); a.emit(movw, 2, DP_VT & 0xFFFF); a.emit(movt, 2, DP_VT >> 16)
        a.emit(cmp_reg, 1, 2); a.emit(b_cond, "sb_stock", "ne")
        a.emit(ldrb_w, 1, 0, FLAG); a.emit(movs_imm, 2, 1); a.emit(eors_reg, 1, 2); a.emit(strb_w, 1, 0, FLAG)
        a.emit(lsls_imm, 1, 1, 31); a.emit(b_cond, "sb_preset", "ne")                       # turned on: slot 7 paints
        a.emit(bl, "c_dstock")                                                               # turned off: stock colours
        a.label("sb_preset")
        a.emit(b_w, PRESET_CASE)                                                             # open the Preset view
        a.label("sb_stock")                                                                  # stock: Shift+button mask
        a.emit(movw, 1, SHIFT_MASK & 0xFFFF); a.emit(movt, 1, SHIFT_MASK >> 16)
        a.emit(b_w, SHIFT_NEXT)
    return a.assemble()


def build(stock: bytes, listing: Path):
    img7, report = s6.build(stock, listing, v2=True)
    img = bytearray(img7)
    img[sc.MARK_OFF:sc.MARK_OFF + 4] = MARKER
    ext_base = (len(img7) + BASE + 3) & ~3
    code, labels = ext_code(ext_base)

    def text(addr, n):
        return "|".join(sc.disasm(bytes(stock[addr - BASE:addr - BASE + n]), addr))
    checks = {CTOR_STRB: "strb.w r0, [r5, #0x50]", SHIFT_BTN: "ldr.w r1, [pc, #0xa30]"}
    for addr, want in checks.items():
        if text(addr, 4) != want:
            raise SystemExit(f"{addr:#x}: '{text(addr, 4)}' != '{want}'")
    assert struct.unpack_from("<I", stock, ((0x080333B2 + 4) & ~3) + 0xA30 - BASE)[0] == SHIFT_MASK
    assert struct.unpack_from("<I", stock, DP_VT - BASE)[0] == DP_PAD | 1
    assert struct.unpack_from("<I", stock, DP_VT + 0x1C - BASE)[0] == 0x08047593
    targets = s4.branch_targets(listing)
    for addr in checks:
        for x in range(addr + 1, addr + 4):
            if x in targets:
                raise SystemExit(f"branch into patched bytes at {x:#x}")
    img[CTOR_STRB - BASE:CTOR_STRB - BASE + 4] = strh_w_imm(0, 5, 0x50)
    if not TRIM:
        img[SHIFT_BTN - BASE:SHIFT_BTN - BASE + 4] = b_w(SHIFT_BTN, labels["c_shbtn"])
        struct.pack_into("<I", img, DP_VT - BASE, labels["c_dpad"] | 1)
    struct.pack_into("<I", img, DP_VT + 0x1C - BASE, labels["c_dleds"] | 1)
    img += b"\xFF" * (ext_base - BASE - len(img)) + code
    while len(img) % 4:
        img += b"\xFF"
    assert len(img) <= 0x70000
    report["D"]["marker"] = MARKER.decode()
    report["sc08"] = dict(start=hex(ext_base), size=len(code), labels={k: hex(v) for k, v in labels.items()},
                          listing=sc.disasm(code, ext_base))
    return bytes(img), report


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("stock_bin", type=Path)
    ap.add_argument("--listing", type=Path, default=Path(__file__).resolve().parents[1] / "re/app.asm")
    ap.add_argument("-o", "--outdir", type=Path, default=Path("build/sc08"))
    args = ap.parse_args()
    stock = args.stock_bin.read_bytes()
    img, report = build(stock, args.listing)
    syx = ct_fw.encode(img)
    info = ct_fw.decode(syx)
    assert info["image"] == img
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / "circuittracks-4486-SC08.bin").write_bytes(img)
    (args.outdir / "circuittracks-4486-SC08.syx").write_bytes(syx)
    manifest = dict(base="circuittracks-firmware-4486 (1.2.1)", marker="SC08", image_size=hex(len(img)),
                    image_sha256=ct_fw.sha256(img), syx_sha256=ct_fw.sha256(syx), crc32=hex(info["crc"]), report=report)
    (args.outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("ext", report["sc08"]["start"], report["sc08"]["size"], "bytes; image", hex(len(img)))
    print("syx sha", manifest["syx_sha256"], "crc", manifest["crc32"])
