"""Circuit Tracks 4486 — SC11 = SC10 + Pitch knob as tuning bias in the chromatic drum Preset view.

In chromatic mode (SC08) each pad sets Pitch = 64 + bias + root + scale offset.
  * bias (signed semitones) lives in byte +0x52 of the drum Preset view (padding);
  * when chromatic mode is switched on, bias = current Pitch - 64 (the knob
    position becomes the keyboard's reference);
  * turning the Pitch knob (macro 2) of a drum whose Preset view is in chromatic
    mode works as in stock (Pitch changes, recordable) AND adds the applied change
    to bias, so later pad notes keep the new tuning.
Container lookup from the knob handler: [[[0x200069E4]+0x40]+0x2C] (controller ->
track-view container), drum view = [cont + 0x8C + 4*d], checked by vtable.
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct_fw  # noqa: E402
import build_shared_channels as sc  # noqa: E402
import build_sc10 as s10  # noqa: E402
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, lsls_imm, mov_reg, movs_imm, movt, movw,  # noqa: E402
                   pop_list, push_list, adds_reg, subs_reg, subs_imm8, adds_imm8, ldrb_w, strb_w, eors_reg,
                   strb_imm, blx_reg, sub_sp_imm, add_sp_imm, raw, h)

BASE = ct_fw.APP_BASE
MARKER = b"SC11"
CTX_PTR = 0x200069E4
DP_VT = 0x0805ABBC
DK_VT_SLOT4 = 0x0805AADC + 0x10          # drum macro handler: knob turn (obj, knob, delta)
DK_STOCK = 0x0804FCC4
GETTER = 0x08036192                      # (kind 0x10, index) -> DSP-mirror value
NOTE_OFF_PREV, NOTE_ON = 0x0804E0E8, 0x0804E0BA
PRESET_CASE, SHIFT_NEXT, SHIFT_MASK, TRACK_OF = 0x080334B2, 0x080333B6, 0x07DBBE00, 0x0805011E
SHIFT_BTN = 0x080333B2
FLAG, BIAS = 0x51, 0x52


def sxtb(rd, rm):                        # SXTB Rd,Rm (T1)
    return h(0xB240 | rm << 3 | rd)


def arm_code(base, L):
    a = Asm(base)
    # -------- c_pitchnow(drum 0..3 in r0) -> r0 = current Pitch (DSP mirror)
    a.label("c_pitchnow")
    a.emit(push_list, [4], lr=True)
    a.emit(lsls_imm, 1, 0, 3); a.emit(subs_reg, 1, 1, 0); a.emit(adds_imm8, 1, 2)        # 7*d + 2
    a.emit(movs_imm, 0, 0x10); a.emit(bl, GETTER)
    a.emit(pop_list, [4], pc=True)

    # -------- c_dview(drum 0..3 in r0) -> r0 = drum Preset view or 0
    a.label("c_dview")
    a.emit(movw, 1, CTX_PTR & 0xFFFF); a.emit(movt, 1, CTX_PTR >> 16)
    a.emit(ldr_imm, 1, 1, 0); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "dv_no", "eq")       # A
    a.emit(ldr_imm, 1, 1, 0x40); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "dv_no", "eq")    # controller
    a.emit(ldr_imm, 1, 1, 0x2C); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "dv_no", "eq")    # container
    a.emit(lsls_imm, 0, 0, 2); a.emit(adds_reg, 1, 1, 0); a.emit(adds_imm8, 1, 0x8C)
    a.emit(ldr_imm, 0, 1, 0); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "dv_no", "eq")
    a.emit(ldr_imm, 1, 0, 0); a.emit(movw, 2, DP_VT & 0xFFFF); a.emit(movt, 2, DP_VT >> 16)
    a.emit(cmp_reg, 1, 2); a.emit(b_cond, "dv_ok", "eq")
    a.label("dv_no"); a.emit(movs_imm, 0, 0)
    a.label("dv_ok"); a.emit(raw, h(0x4770))                                              # bx lr

    # -------- c_dknob: drum macro handler slot 4 (mh, knob, delta)
    a.label("c_dknob")
    a.emit(cmp_imm, 1, 1); a.emit(b_cond, "dk_pitch", "eq")
    a.emit(b_w, DK_STOCK)
    a.label("dk_pitch")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2)
    a.emit(ldrb_w, 0, 4, 0x30); a.emit(subs_imm8, 0, 40)                                 # 0,5,10,15
    a.emit(movs_imm, 7, 0)
    a.label("dk_div"); a.emit(cmp_imm, 0, 5); a.emit(b_cond, "dk_dived", "lo")
    a.emit(subs_imm8, 0, 5); a.emit(adds_imm8, 7, 1); a.emit(b, "dk_div")
    a.label("dk_dived")                                                                   # r7 = drum 0..3
    a.emit(cmp_imm, 7, 3); a.emit(b_cond, "dk_plain", "hi")
    a.emit(mov_reg, 0, 7); a.emit(bl, "c_pitchnow"); a.emit(sub_sp_imm, 8)
    a.emit(raw, h(0x9000))                                                                # str r0,[sp,#0] (before)
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6); a.emit(bl, DK_STOCK)
    a.emit(mov_reg, 0, 7); a.emit(bl, "c_pitchnow")
    a.emit(raw, h(0x9900))                                                                # ldr r1,[sp,#0]
    a.emit(subs_reg, 6, 0, 1)                                                             # applied change
    a.emit(add_sp_imm, 8)
    a.emit(mov_reg, 0, 7); a.emit(bl, "c_dview"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "dk_out", "eq")
    a.emit(ldrb_w, 1, 0, FLAG); a.emit(lsls_imm, 1, 1, 31); a.emit(b_cond, "dk_out", "eq")
    a.emit(ldrb_w, 1, 0, BIAS); a.emit(raw, sxtb(1, 1)); a.emit(adds_reg, 1, 1, 6)
    a.emit(strb_w, 1, 0, BIAS)
    a.label("dk_out"); a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("dk_plain"); a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6)
    a.emit(bl, DK_STOCK); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # -------- c_dpad2: chromatic pad press with bias
    a.label("c_dpad2")
    a.emit(ldrb_w, 3, 0, FLAG); a.emit(lsls_imm, 3, 3, 31); a.emit(b_cond, "dp_chrom", "ne")
    a.emit(b_w, 0x0804D934)
    a.label("dp_chrom")
    a.emit(push_list, [4, 5, 6], lr=True); a.emit(sub_sp_imm, 16)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2)
    a.emit(mov_reg, 1, 13); a.emit(bl, L["c_scale"]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "dp_out", "ne")
    a.emit(mov_reg, 0, 13); a.emit(mov_reg, 1, 5); a.emit(bl, L["c_padval"])
    a.emit(cmp_imm, 0, 0xFF); a.emit(b_cond, "dp_out", "eq")
    a.emit(ldrb_w, 2, 4, BIAS); a.emit(raw, sxtb(2, 2)); a.emit(adds_reg, 2, 0, 2)
    a.emit(cmp_imm, 2, 0); a.emit(b_cond, "dp_c1", "ge"); a.emit(movs_imm, 2, 0)
    a.label("dp_c1"); a.emit(cmp_imm, 2, 127); a.emit(b_cond, "dp_c2", "le"); a.emit(movs_imm, 2, 127)
    a.label("dp_c2")
    a.emit(ldr_imm, 0, 4, 0x0C); a.emit(ldrb_w, 1, 4, 0x24); a.emit(subs_imm8, 1, 4)
    a.emit(ldr_imm, 3, 0, 0); a.emit(ldr_imm, 3, 3, 0); a.emit(blx_reg, 3)
    a.emit(mov_reg, 0, 4); a.emit(bl, NOTE_OFF_PREV)
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6); a.emit(bl, NOTE_ON)
    a.label("dp_out"); a.emit(add_sp_imm, 16); a.emit(pop_list, [4, 5, 6], pc=True)

    # -------- c_shbtn2: as SC08 c_shbtn, plus bias = Pitch - 64 when switching on
    a.label("c_shbtn2")                                                                   # r4 controller, r5 button
    a.emit(cmp_imm, 5, 8); a.emit(b_cond, "sb_stock", "ne")
    a.emit(ldr_imm, 0, 4, 0x2C); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sb_stock", "eq")
    a.emit(bl, TRACK_OF)
    a.emit(subs_imm8, 0, 4); a.emit(cmp_imm, 0, 3); a.emit(b_cond, "sb_stock", "hi")
    a.emit(mov_reg, 5, 0)                                                                 # r5 = drum (restored to 8 below)
    a.emit(bl, "c_dview"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sb_none", "eq")
    a.emit(ldrb_w, 1, 0, FLAG); a.emit(movs_imm, 2, 1); a.emit(eors_reg, 1, 2); a.emit(strb_w, 1, 0, FLAG)
    a.emit(lsls_imm, 1, 1, 31); a.emit(b_cond, "sb_on", "ne")
    a.emit(bl, L["c_dstock"]); a.emit(b, "sb_go")
    a.label("sb_on")
    a.emit(push_list, [0])
    a.emit(mov_reg, 0, 5); a.emit(bl, "c_pitchnow"); a.emit(subs_imm8, 0, 64)
    a.emit(pop_list, [1]); a.emit(strb_w, 0, 1, BIAS)
    a.label("sb_go")
    a.emit(movs_imm, 5, 8); a.emit(b_w, PRESET_CASE)
    a.label("sb_none")
    a.emit(movs_imm, 5, 8)
    a.label("sb_stock")
    a.emit(movw, 1, SHIFT_MASK & 0xFFFF); a.emit(movt, 1, SHIFT_MASK >> 16)
    a.emit(b_w, SHIFT_NEXT)
    return a.assemble()


def build(stock: bytes, listing: Path):
    img10, report = s10.build(stock, listing)
    img = bytearray(img10)
    img[sc.MARK_OFF:sc.MARK_OFF + 4] = MARKER
    L = {k: int(v, 16) for k, v in report["sc08"]["labels"].items()}
    assert struct.unpack_from("<I", img, DK_VT_SLOT4 - BASE)[0] == DK_STOCK | 1
    import build_sc08
    if not build_sc08.TRIM:
        assert struct.unpack_from("<I", img, DP_VT - BASE)[0] == L["c_dpad"] | 1
        assert bytes(img[SHIFT_BTN - BASE:SHIFT_BTN - BASE + 4]) == b_w(SHIFT_BTN, L["c_shbtn"])
    ext = (len(img) + BASE + 3) & ~3
    code, labels = arm_code(ext, L)
    struct.pack_into("<I", img, DK_VT_SLOT4 - BASE, labels["c_dknob"] | 1)
    struct.pack_into("<I", img, DP_VT - BASE, labels["c_dpad2"] | 1)
    img[SHIFT_BTN - BASE:SHIFT_BTN - BASE + 4] = b_w(SHIFT_BTN, labels["c_shbtn2"])
    ctor = 0x0804D89C                                   # SC08 strh.w -> str.w r0,[r5,#0x50]: also zeroes the bias
    assert bytes(img[ctor - BASE:ctor - BASE + 4]) == bytes.fromhex("a5f85000")
    img[ctor - BASE:ctor - BASE + 4] = h(0xF8C5) + h(0x0050)
    img += b"\xFF" * (ext - BASE - len(img)) + code
    while len(img) % 4:
        img += b"\xFF"
    assert len(img) <= 0x70000
    report["D"]["marker"] = MARKER.decode()
    report["sc11"] = dict(start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, listing=sc.disasm(code, ext))
    return bytes(img), report


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("stock_bin", type=Path)
    ap.add_argument("--listing", type=Path, default=Path(__file__).resolve().parents[1] / "re/app.asm")
    ap.add_argument("-o", "--outdir", type=Path, default=Path("build/sc11"))
    args = ap.parse_args()
    stock = args.stock_bin.read_bytes()
    img, report = build(stock, args.listing)
    syx = ct_fw.encode(img)
    info = ct_fw.decode(syx)
    assert info["image"] == img
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / "circuittracks-4486-SC11.bin").write_bytes(img)
    (args.outdir / "circuittracks-4486-SC11.syx").write_bytes(syx)
    manifest = dict(base="circuittracks-firmware-4486 (1.2.1)", marker="SC11", image_size=hex(len(img)),
                    image_sha256=ct_fw.sha256(img), syx_sha256=ct_fw.sha256(syx), crc32=hex(info["crc"]), report=report)
    (args.outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("arm", report["sc11"]["start"], "image", hex(len(img)))
    print("syx sha", manifest["syx_sha256"], "crc", manifest["crc32"])
