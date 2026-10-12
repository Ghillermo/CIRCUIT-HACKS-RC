"""Circuit Tracks 4486 — SC12 = SC11 + drum fine tuning in cents.

Per drum fine tune (signed cents, -100..+100) in byte +0x53 of the drum Preset view
(zeroed by the constructor since SC11). Applied by the drum DSP-update handlers:
DSP pitch word = semitone table[Pitch] * 2^(cents/1200), so it affects every hit of
that drum (pads, sequencer, chromatic mode). Not saved (0 after power-up).

Control, with the drum in chromatic mode (Shift + Preset):
  * Pitch knob (macro 2)          -> fine tune, 1 cent per knob step (no Pitch write)
  * Shift + Pitch knob            -> semitone bias as in SC11 (stock Pitch + bias)
The drum's DSP group is re-sent on every change so the tuning is heard at once.
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct_fw  # noqa: E402
import build_shared_channels as sc  # noqa: E402
import build_sc11 as s11  # noqa: E402
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, ldr_imm, lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw,  # noqa: E402
                   pop_list, push_list, adds_reg, subs_imm8, adds_imm8, ldrb_w, strb_w, orrs_reg, raw, h)

BASE = ct_fw.APP_BASE
MARKER = b"SC12"
CONV = 0x0802878C
CALLS = (0x080287FA, 0x08028896, 0x0802892A, 0x080289BE)      # bl CONV in drum 1..4 DSP handlers
DK_VT_SLOT4 = 0x0805AADC + 0x10
DK_STOCK = 0x0804FCC4
MARK_DIRTY = 0x0803BDCC
PARAM_GET = 0x0803542C
CTX_PTR = 0x200069E4
FLAG, FINE = 0x51, 0x53
MAXC = 100
SWAP = False                      # SC20.1: in the chromatic view the plain Pitch knob is the semitone bias (SC11) and Shift + Pitch the fine tune in cents


def sxtb(rd, rm): return h(0xB240 | rm << 3 | rd)
def umull(lo, hi, rn, rm): return h(0xFBA0 | rn) + h(lo << 12 | hi << 8 | rm)


def fine_table():
    return [round(65536 * 2 ** (c / 1200)) for c in range(-MAXC, MAXC + 1)]


def arm_code(base, L):
    a = Asm(base)
    for d in range(4):                                   # per-drum conversion wrappers
        a.label(f"c_conv{d}")
        a.emit(push_list, [4], lr=True)
        a.emit(bl, CONV); a.emit(mov_reg, 4, 0)          # r4 = semitone word
        a.emit(movs_imm, 0, d); a.emit(bl, L["c_dview"])
        a.emit(b, "cv_tail")
    a.label("cv_tail")                                   # r0 = view or 0, r4 = word
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "cv_out", "eq")
    a.emit(ldrb_w, 1, 0, FINE); a.emit(raw, sxtb(1, 1))
    a.emit(cmp_imm, 1, 0); a.emit(b_cond, "cv_out", "eq")
    a.emit(adds_imm8, 1, MAXC)                           # 0..200
    a.emit(cmp_imm, 1, 2 * MAXC); a.emit(b_cond, "cv_out", "hi")
    a.emit(lsls_imm, 1, 1, 2)
    a.emit(movw, 2, 0); a.emit(movt, 2, 0)               # patched below: fine table address
    a.label("cv_tab_fix")
    a.emit(raw, h(0x5852))                               # ldr r2,[r2,r1]
    a.emit(raw, umull(0, 1, 4, 2))                       # r1:r0 = word * mult
    a.emit(lsrs_imm, 0, 0, 16); a.emit(lsls_imm, 1, 1, 16); a.emit(orrs_reg, 0, 1)
    a.emit(movw, 1, 0xFFFF); a.emit(movt, 1, 0x7F)       # clamp to 0x7FFFFF
    a.emit(raw, h(0x4288))                               # cmp r0,r1
    a.emit(b_cond, "cv_ret", "ls"); a.emit(mov_reg, 0, 1); a.emit(b, "cv_ret")
    a.label("cv_out"); a.emit(mov_reg, 0, 4)
    a.label("cv_ret"); a.emit(pop_list, [4], pc=True)

    # -------- knob: chromatic mode -> fine cents (Shift: SC11 semitone bias)
    a.label("c_dknob3")
    a.emit(cmp_imm, 1, 1); a.emit(b_cond, "dk_p", "eq")
    a.emit(b_w, DK_STOCK)
    a.label("dk_p")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2)
    a.emit(ldrb_w, 0, 4, 0x30); a.emit(subs_imm8, 0, 40); a.emit(movs_imm, 7, 0)
    a.label("dk_div"); a.emit(cmp_imm, 0, 5); a.emit(b_cond, "dk_d", "lo")
    a.emit(subs_imm8, 0, 5); a.emit(adds_imm8, 7, 1); a.emit(b, "dk_div")
    a.label("dk_d"); a.emit(cmp_imm, 7, 3); a.emit(b_cond, "dk_sc11", "hi")
    a.emit(mov_reg, 0, 7); a.emit(bl, L["c_dview"]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "dk_sc11", "eq")
    a.emit(ldrb_w, 1, 0, FLAG); a.emit(lsls_imm, 1, 1, 31); a.emit(b_cond, "dk_sc11", "eq")
    a.emit(mov_reg, 5, 0)                                                         # r5 = view (knob is 1)
    # shift held? [ [[A]+0x40] +0xC ] param 0
    a.emit(movw, 0, CTX_PTR & 0xFFFF); a.emit(movt, 0, CTX_PTR >> 16)
    a.emit(ldr_imm, 0, 0, 0); a.emit(ldr_imm, 0, 0, 0x40); a.emit(ldr_imm, 0, 0, 0x0C)
    a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_w, 0, 0, 0)
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "dk_shift", "eq" if SWAP else "ne")
    # fine: cents += delta, clamp
    a.emit(ldrb_w, 1, 5, FINE); a.emit(raw, sxtb(1, 1)); a.emit(adds_reg, 1, 1, 6)
    a.emit(raw, h(0xF111) + h(0x0F64))                                           # cmn.w r1,#100
    a.emit(b_cond, "dk_c1", "ge"); a.emit(movs_imm, 1, 0); a.emit(subs_imm8, 1, MAXC)
    a.label("dk_c1"); a.emit(cmp_imm, 1, MAXC); a.emit(b_cond, "dk_c2", "le"); a.emit(movs_imm, 1, MAXC)
    a.label("dk_c2"); a.emit(strb_w, 1, 5, FINE)
    a.emit(lsls_imm, 1, 7, 3); a.emit(raw, h(0x1BC9)); a.emit(adds_imm8, 1, 2)    # subs r1,r1,r7 -> 7d ; +2
    a.emit(movs_imm, 0, 0x10); a.emit(bl, MARK_DIRTY)                           # resend this drum's group
    a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("dk_shift")
    a.label("dk_sc11")                                                            # SC11 behaviour
    a.emit(mov_reg, 0, 4); a.emit(movs_imm, 1, 1); a.emit(mov_reg, 2, 6)
    a.emit(bl, L["c_dknob"])
    a.emit(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


def build(stock: bytes, listing: Path):
    img11, report = s11.build(stock, listing)
    img = bytearray(img11)
    img[sc.MARK_OFF:sc.MARK_OFF + 4] = MARKER
    L = {k: int(v, 16) for k, v in report["sc11"]["labels"].items()}
    for c in CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, CONV)
    assert struct.unpack_from("<I", img, DK_VT_SLOT4 - BASE)[0] == L["c_dknob"] | 1
    ext = (len(img) + BASE + 3) & ~3
    code, labels = arm_code(ext, L)
    tab = (ext + len(code) + 3) & ~3
    fix = labels["cv_tab_fix"] - 8                                                # movw/movt r2 before the label
    code = bytearray(code)
    code[fix - ext:fix - ext + 8] = movw(2, tab & 0xFFFF) + movt(2, tab >> 16)
    for d, c in enumerate(CALLS):
        img[c - BASE:c - BASE + 4] = bl(c, labels[f"c_conv{d}"])
    struct.pack_into("<I", img, DK_VT_SLOT4 - BASE, labels["c_dknob3"] | 1)
    img += b"\xFF" * (ext - BASE - len(img)) + bytes(code)
    img += b"\xFF" * (tab - BASE - len(img)) + struct.pack(f"<{2 * MAXC + 1}I", *fine_table())
    while len(img) % 4:
        img += b"\xFF"
    assert len(img) <= 0x70000
    report["D"]["marker"] = MARKER.decode()
    report["sc12"] = dict(start=hex(ext), table=hex(tab), labels={k: hex(v) for k, v in labels.items()},
                          listing=sc.disasm(bytes(code), ext))
    return bytes(img), report


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("stock_bin", type=Path)
    ap.add_argument("--listing", type=Path, default=Path(__file__).resolve().parents[1] / "re/app.asm")
    ap.add_argument("-o", "--outdir", type=Path, default=Path("build/sc12"))
    args = ap.parse_args()
    stock = args.stock_bin.read_bytes()
    img, report = build(stock, args.listing)
    syx = ct_fw.encode(img)
    info = ct_fw.decode(syx)
    assert info["image"] == img
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / "circuittracks-4486-SC12.bin").write_bytes(img)
    (args.outdir / "circuittracks-4486-SC12.syx").write_bytes(syx)
    manifest = dict(base="circuittracks-firmware-4486 (1.2.1)", marker="SC12", image_size=hex(len(img)),
                    image_sha256=ct_fw.sha256(img), syx_sha256=ct_fw.sha256(syx), crc32=hex(info["crc"]), report=report)
    (args.outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("arm", report["sc12"]["start"], "table", report["sc12"]["table"], "image", hex(len(img)))
    print("syx sha", manifest["syx_sha256"], "crc", manifest["crc32"])
