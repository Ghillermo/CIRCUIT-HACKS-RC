"""Circuit Tracks 4486 — SC10 = SC09 + FX returns through mixer strips 3/4.

Setup View pads 22 / 23 (bottom row of the Tx/Rx block area, free in stock):
  pad 22 -> reverb return goes through mixer strip 3 (Audio In 1)
  pad 23 -> delay  return goes through mixer strip 4 (Audio In 2)
With a toggle on, that strip's input is muted (dry and both sends) and its
level x pan x side-chain envelope is applied to the FX return instead
(x16, i.e. level 127 = unity, level 100 = about -2 dB).
Stored in settings param 2 bits 28 / 29 (saved, mask extended to 0x3F07FFFF);
sent to DSP core 0 as X:$EC bit 0 / 1 from the Audio In group handler (H9).

DSP core 0 patches (program in flash at 0x080101F0, words at P:p):
  P:$10B  jsr init_hook   (clears X:$EC at DSP start)
  P:$23C  jsr premix      (zero input 1 / 2 samples of this block when flagged)
  P:$D21  jsr returns ; jmp $D32   (scale reverb / delay returns by strip gains,
                                    then the stock delay+reverb summation)
  new code in the unused interrupt vectors P:$80..$FF
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
import build_sc09 as s9  # noqa: E402
import dsp56 as D  # noqa: E402
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, ldr_imm, lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw,  # noqa: E402
                   pop_list, push_list, str_imm, adds_imm8, ands_reg, eors_reg, ldrh_reg, strh_imm, it, ldrb_imm)

BASE = ct_fw.APP_BASE
MARKER = b"SC10"
DSP0 = 0x080101F0                  # core 0 main program bootstrap block
DSP0_WORDS = 0x2A5E
FLAGS = 0xEC                       # X:$EC  bit0 reverb->strip3, bit1 delay->strip4
CODE_BASE, CODE_END = 0x80, 0x100
PALETTE = 0x08056464
PARAM_GET, PARAM_PTR, COMMIT = 0x0803542C, 0x080354FA, 0x080353C0
DSP_WRITE = 0x080292F8             # (core, value<<8, address)
MARK_DIRTY = 0x0803BDCC            # (kind, index)
H9_HOOK = 0x08028EEC               # mov r1,r0 ; movs r2,#0x59  (last Audio In write)
SETUP_REFRESH = 0x08046E64
SETUP_VT_LEDS = 0x0805A98C + 0x1C
BIT_REV, BIT_DLY = 28, 29
RET_COLS = None                    # SC37.4 (use_retcols): {bit: (on, off)} LED codes of pads 22 / 23 instead of Synth 1's palette entries


def use_retcols():
    """SC37.4 (the user, 2026-10-10: «cambia el color de los toggles return reverb delay por sus respectivos colores»): pad 22 (reverb) in cream, pad 23
    (delay) in peach, the colours of the reverb / delay pads of the FX view (0x29 / 0x6A selected, 0x2A / 0x6B not); the same code size."""
    global RET_COLS
    RET_COLS = {BIT_REV: (0x29, 0x2A), BIT_DLY: (0x6A, 0x6B)}
ADVLEDS = False                    # SC38.8 (use_advleds): pads 22 / 23 left to the stock in the Advanced Setup view


def use_advleds():
    """SC38.8 (the user, 2026-10-11: «dos pads se encienden durante el reinicio en modo setup avanzado»): c_setleds painted pads 22 / 23 (the returns
    through strips 3 / 4) in every Setup view, the Advanced one too (byte +0x24 of the Setup view set).  Only the LEDs: the stock's pad handler
    (0x08046DF0) ignores every pad in the Advanced view (`ldrb r0, [r4, #0x24]; cbnz`) before our pad hooks.  Now the Advanced view keeps the stock's."""
    global ADVLEDS
    ADVLEDS = True


SAVE_MASK = 0x3F07FFFF


def p_off(p):                      # image offset of DSP P word p
    return DSP0 - BASE + 6 + 3 * p


def dsp_code():
    a = D.Asm(CODE_BASE)
    a.label("init_hook")
    a.emit(D.move_imm_x, 'x0', 0); a.emit(D.st_abs, 'x', 'x0', FLAGS)
    a.emit(D.move_imm_r, 0, 0x2028); a.emit(D.RTS)

    a.label("premix")                                   # r5 = input frame pointer on exit
    a.emit(D.ld_abs, 'x', 'a', FLAGS)
    a.emit(D.jclr_a1, 0, "pm_in2")
    a.emit(D.ld_abs, 'y', 'r5', 0xFFD); a.emit(D.CLR_B)
    a.emit(D.do_x, 0x3A, "pm_l1")
    a.emit(D.st_ind, 'y', 'b', 5)
    a.label("pm_l1"); a.emit(D.inc_r, 5)
    a.label("pm_in2")
    a.emit(D.jclr_a1, 1, "pm_done")
    a.emit(D.ld_abs, 'y', 'r5', 0xFFD); a.emit(D.CLR_B); a.emit(D.inc_r, 5)
    a.emit(D.do_x, 0x3A, "pm_l2")
    a.emit(D.st_ind, 'y', 'b', 5)
    a.label("pm_l2"); a.emit(D.inc_r, 5)
    a.label("pm_done")
    a.emit(D.ld_abs, 'y', 'r5', 0xFFD); a.emit(D.RTS)

    a.label("returns")
    for flag, buf, gains, lab in ((0, 0x880, 0x20C, "rt_a"), (1, 0x9C0, 0x24C, "rt_b")):
        a.emit(D.ld_abs, 'x', 'a', FLAGS)
        a.emit(D.jclr_a1, flag, lab + "_skip")
        a.emit(D.move_imm_r, 6, buf); a.emit(D.move_imm_r, 0, gains)
        a.emit(D.do_x, 0x3A, lab + "_end")
        for last in (False, True):                       # L then R of one frame
            a.emit(D.ld_ind, 'x', 'x0', 0)
            a.emit(D.ld_ind, 'y', 'y0', 6, '')
            a.emit(D.MPY_Y0X0_A); a.emit([0x0C1D08])     # asl #4,a,a
            if last:
                a.label(lab + "_end")
            a.emit(D.st_ind, 'y', 'a', 6)
        a.label(lab + "_skip")
    # stock summation (P:$D21..$D31): returns = (delay + reverb) >> x:$18b -> Y:$880
    a.emit(D.move_imm_r, 6, 0x9C0); a.emit(D.move_imm_r, 7, 0x880)
    a.emit(D.ld_abs, 'x', 'x0', 0x18B)
    a.emit(D.do_x, 0x3A, "rt_sum_end")
    a.emit(D.ld_ind, 'y', 'a', 6); a.emit(D.ld_ind, 'y', 'b', 6); a.emit(D.ld_ind, 'y', 'y0', 7)
    a.emit([0x4ED750])                                   # add y0,a  y:(r7)-,y0
    a.emit(D.ADD_Y0_B); a.emit(D.ASR_X0_A); a.emit(D.ASR_X0_B)
    a.emit(D.st_ind, 'y', 'a', 7)
    a.label("rt_sum_end"); a.emit(D.st_ind, 'y', 'b', 7)
    a.emit(D.RTS)
    words, labels = a.assemble()
    assert CODE_BASE + len(words) <= CODE_END, hex(len(words))
    return words, labels


def arm_code(base, c_settings):
    a = Asm(base)
    # H9 tail: write the last Audio In value, then the FX-return flags to X:$EC
    a.label("c_h9")
    a.emit(mov_reg, 1, 0); a.emit(movs_imm, 2, 0x59); a.emit(movs_imm, 0, 0); a.emit(bl, DSP_WRITE)
    a.emit(bl, c_settings); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "h9_zero", "eq")
    a.emit(movs_imm, 1, 2); a.emit(bl, PARAM_GET); a.emit(ldr_imm, 0, 0, 0)
    a.emit(lsrs_imm, 0, 0, BIT_REV); a.emit(movs_imm, 1, 3); a.emit(ands_reg, 0, 1)
    a.emit(b, "h9_wr")
    a.label("h9_zero"); a.emit(movs_imm, 0, 0)
    a.label("h9_wr")
    a.emit(lsls_imm, 1, 0, 8); a.emit(*((movs_imm, 2, FLAGS) if FLAGS <= 0xFF else (movw, 2, FLAGS)))
    a.emit(movs_imm, 0, 0); a.emit(bl, DSP_WRITE)
    a.emit(pop_list, [3], pc=True)

    # Setup pads 22 / 23 (from SC04 c_pad "ignore" path: r5 = pad - 0x17, r4 = Setup view)
    a.label("c_fxpad")
    a.emit(adds_imm8, 5, 0x17)
    a.emit(cmp_imm, 5, 0x15); a.emit(b_cond, "fx_rev", "eq")
    a.emit(cmp_imm, 5, 0x16); a.emit(b_cond, "fx_dly", "eq")
    a.emit(b_w, SETUP_REFRESH)
    a.label("fx_rev"); a.emit(movs_imm, 5, 1); a.emit(lsls_imm, 5, 5, BIT_REV); a.emit(b, "fx_tog")
    a.label("fx_dly"); a.emit(movs_imm, 5, 1); a.emit(lsls_imm, 5, 5, BIT_DLY)
    a.label("fx_tog")
    a.emit(ldr_imm, 0, 4, 0x0C); a.emit(movs_imm, 1, 2); a.emit(bl, PARAM_PTR)
    a.emit(ldr_imm, 1, 0, 0); a.emit(eors_reg, 1, 5); a.emit(str_imm, 1, 0, 0)
    a.emit(ldr_imm, 0, 4, 0x0C); a.emit(bl, COMMIT)
    a.emit(movs_imm, 0, 0x20); a.emit(movs_imm, 1, 48); a.emit(bl, MARK_DIRTY)   # resend Audio In group (H9)
    a.emit(b_w, SETUP_REFRESH)

    # Setup view get-LEDs (vtable slot 7): paint pads 22 / 23
    a.label("c_setleds")
    a.emit(push_list, [4], lr=True); a.emit(mov_reg, 4, 0)
    if ADVLEDS:                                          # the Advanced Setup view (+0x24 set): the stock's LEDs
        a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 0x24); a.emit(ldrb_imm, 0, 0, 0); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sl_out", "ne")
    a.emit(bl, c_settings); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sl_out", "eq")
    a.emit(movs_imm, 1, 2); a.emit(bl, PARAM_GET); a.emit(ldr_imm, 0, 0, 0)
    a.emit(ldr_imm, 3, 4, 4); a.emit(ldr_imm, 3, 3, 0)
    a.emit(movw, 2, PALETTE & 0xFFFF); a.emit(movt, 2, PALETTE >> 16)
    for bit, pad in ((BIT_REV, 0x15), (BIT_DLY, 0x16)):
        a.emit(lsls_imm, 1, 0, 31 - bit)
        if RET_COLS:
            a.emit(it, "mi", "e"); a.emit(movs_imm, 1, RET_COLS[bit][0]); a.emit(movs_imm, 1, RET_COLS[bit][1])
            a.emit(mov_reg, 1, 1); a.emit(strh_imm, 1, 3, pad * 2)
        else:
            a.emit(it, "mi", "e"); a.emit(movs_imm, 1, 0x02); a.emit(movs_imm, 1, 0x12)
            a.emit(ldrh_reg, 1, 2, 1); a.emit(strh_imm, 1, 3, pad * 2)
    a.label("sl_out")
    a.emit(ldr_imm, 0, 4, 4); a.emit(ldr_imm, 0, 0, 0)
    a.emit(pop_list, [4], pc=True)
    return a.assemble()


def build(stock: bytes, listing: Path):
    img9, report = s9.build(stock, listing)
    img = bytearray(img9)
    img[sc.MARK_OFF:sc.MARK_OFF + 4] = MARKER

    # ---------------- DSP core 0
    hdr = img[DSP0 - BASE:DSP0 - BASE + 6]
    assert int.from_bytes(hdr[:3], 'big') == DSP0_WORDS and int.from_bytes(hdr[3:], 'big') == 0
    P = [int.from_bytes(img[p_off(p):p_off(p) + 3], 'big') for p in range(DSP0_WORDS)]
    expect = {0x10B: [0x60F400, 0x002028], 0x23C: [0x6DF000, 0x000FFD], 0xD21: [0x66F400, 0x0009C0, 0x67F400, 0x000880]}
    for p, ws in expect.items():
        assert P[p:p + len(ws)] == ws, (hex(p), [hex(x) for x in P[p:p + len(ws)]])
    assert all(x == 0 for x in P[CODE_BASE:CODE_END])
    dwords, dlabels = dsp_code()
    P[CODE_BASE:CODE_BASE + len(dwords)] = dwords
    P[0x10B:0x10D] = D.jsr(dlabels["init_hook"])
    P[0x23C:0x23E] = D.jsr(dlabels["premix"])
    P[0xD21:0xD25] = D.jsr(dlabels["returns"]) + D.jmp(0xD32)
    for p in range(DSP0_WORDS):
        img[p_off(p):p_off(p) + 3] = P[p].to_bytes(3, 'big')

    # ---------------- ARM
    def text(addr, n):
        return "|".join(sc.disasm(bytes(stock[addr - BASE:addr - BASE + n]), addr))
    assert text(H9_HOOK, 4) == "mov r1, r0|movs r2, #0x59", text(H9_HOOK, 4)
    assert struct.unpack_from("<I", stock, SETUP_VT_LEDS - BASE)[0] == 0x08047593
    targets = s4.branch_targets(listing)
    for x in range(H9_HOOK + 1, H9_HOOK + 4):
        assert x not in targets
    c_settings = int(report["sc06"]["labels"]["c_settings"], 16)
    c_pad_ign = int(report["cave"]["labels"]["c_pad_ign"], 16)
    assert bytes(img[c_pad_ign - BASE:c_pad_ign - BASE + 4]) == b_w(c_pad_ign, SETUP_REFRESH)
    ext = (len(img) + BASE + 3) & ~3
    code, labels = arm_code(ext, c_settings)
    img[H9_HOOK - BASE:H9_HOOK - BASE + 4] = b_w(H9_HOOK, labels["c_h9"])
    img[c_pad_ign - BASE:c_pad_ign - BASE + 4] = b_w(c_pad_ign, labels["c_fxpad"])
    struct.pack_into("<I", img, SETUP_VT_LEDS - BASE, labels["c_setleds"] | 1)
    for lab, reg in (("c_m1", 1), ("c_m2", 3)):            # SC07 save mask: + bits 28/29
        addr = int(report["sc06"]["labels"][lab], 16) + 4
        assert bytes(img[addr - BASE:addr - BASE + 4]) == movt(reg, 0x0F07)
        img[addr - BASE:addr - BASE + 4] = movt(reg, SAVE_MASK >> 16)
    img += b"\xFF" * (ext - BASE - len(img)) + code
    while len(img) % 4:
        img += b"\xFF"
    assert len(img) <= 0x70000
    report["D"]["marker"] = MARKER.decode()
    report["sc10"] = dict(dsp_labels={k: hex(v) for k, v in dlabels.items()}, dsp_words=len(dwords),
                          arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()},
                          listing=sc.disasm(code, ext))
    return bytes(img), report


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("stock_bin", type=Path)
    ap.add_argument("--listing", type=Path, default=Path(__file__).resolve().parents[1] / "re/app.asm")
    ap.add_argument("-o", "--outdir", type=Path, default=Path("build/sc10"))
    args = ap.parse_args()
    stock = args.stock_bin.read_bytes()
    img, report = build(stock, args.listing)
    syx = ct_fw.encode(img)
    info = ct_fw.decode(syx)
    assert info["image"] == img
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / "circuittracks-4486-SC10.bin").write_bytes(img)
    (args.outdir / "circuittracks-4486-SC10.syx").write_bytes(syx)
    manifest = dict(base="circuittracks-firmware-4486 (1.2.1)", marker="SC10", image_size=hex(len(img)),
                    image_sha256=ct_fw.sha256(img), syx_sha256=ct_fw.sha256(syx), crc32=hex(info["crc"]), report=report)
    (args.outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("dsp", report["sc10"]["dsp_words"], "words", report["sc10"]["dsp_labels"])
    print("arm", report["sc10"]["arm_start"], "image", hex(len(img)))
    print("syx sha", manifest["syx_sha256"], "crc", manifest["crc32"])
