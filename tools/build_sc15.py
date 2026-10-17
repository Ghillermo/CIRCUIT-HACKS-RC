"""Circuit Tracks 4486 — SC15 = SC14.2 + line input instead of the synth noise source.

Per synth, the noise oscillator can be replaced by audio input 1 or 2 (mono, line level): the
input then goes through the synth voice exactly like the noise would (noise level knob / mod
matrix, filter, envelopes, FX).  Every voice of that synth hears the same input.

DSP core 0 (stock voice mixer, P:$9A5..$9D8): per sample
    a = osc1*l0 + osc2*l1 + ... + noise*l5,  noise = y:(r2)+n2,  r2 = Y:$F7D + voice offset, n2 = 4
(the noise table Y:$F7F.. is regenerated every block at P:$19FD).  The input ring is
Y:$1000..$13FF (modulo $3FF), frames [in1, in2]; y:$FFD = first frame of the current block,
64-word aligned so a block never wraps.

  P:$9C3/$9C4  move (r2)+n2 ; move #4,n2   ->  jmp li_hook
  li_hook: mode = X:$3A01 (Synth 1) / X:$3A02 (Synth 2) chosen by x:$cc (voice slot word 7 = synth,
           copied by func_00077f at P:$77F in both voice passes)
           mode 0 -> stock two instructions;  mode 1/2 -> r2 = y:$FFD + mode-1, n2 = 2
           then jmp $9C5 (no stack used)
  P:$10B       jsr init_hook (SC10)  ->  jsr li_init: clears X:$3A00..$3A02, r0 = $2028
X:$3A00..$3A02 lie in X:$3339..$3BFF (tools/dsp_free_scan.py).

ARM (state in SC14's reserved RAM block, bytes 18..20, via SC14's c_gst; not saved):
  Synth Preset view (vtable 0x0805AC9C, track byte +0x24 = 0x68 / 0x69):
    slot 0 -> c_spad : Shift + pad 25 / 26 / 27 (row 4) = Noise / In 1 / In 2, then the
                       Audio In group is marked dirty; anything else = stock (patch select)
    slot 7 -> c_sleds: while Shift is held, pads 25-27 show the mode (selected bright);
                       on release the stock view is repainted (0x0804D3C2)
  H9 (Audio In group handler, SC10 hook) -> c_h9b: writes X:$3A01 / X:$3A02, then SC10 c_h9
"""
from __future__ import annotations

import json
import os
import struct
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct_fw  # noqa: E402
import build_shared_channels as sc  # noqa: E402
import dsp56 as D  # noqa: E402
import build_sc14_2 as s142  # noqa: E402   (sets build_sc10.FLAGS = $3A00)
import build_sc10 as s10  # noqa: E402
from thumb import (Asm, b, b_cond, b_w, bl, cbz, cmp_imm, ldr_imm, ldrb_imm, lsls_imm, mov_reg, movs_imm,  # noqa: E402
                   movt, movw, orrs_reg, bics_reg, tst_reg, strb_imm, strh_imm, subs_imm3, subs_imm8, adds_reg,
                   push_list, pop_list, raw, h, ldrb_w)

BASE = ct_fw.APP_BASE
NAME = "SC15"
MARKER = b"SC15"
import sys as _sys; _sys.path.insert(0, __import__("os").path.dirname(__file__))
from dsptool_path import TOOL  # noqa: E402

MODE_S1, MODE_S2 = 0x3A01, 0x3A02
SYNTH = 0xCC                         # x:$cc = voice slot word 7 (synth 0/1), set by func_00077f / $281 (x:$cb is stale)
HOOK_AT, HOOK_RET = 0x9C3, 0x9C5
DSP_FREE_END = 0x100                 # SC10 code ends at P:$D9; P:$D9..$FF free

# ARM
SP_VT = 0x0805AC9C                   # synth Preset view vtable (instances 0x20042980 / 0x20042A34)
SP_PRESS, SP_LEDS, SP_REPAINT = 0x0804D242, 0x08047592, 0x0804D3C2
SP_TRACK, SP_TRACK0 = 0x24, 0x68
PAD0 = 24                            # pads 25 / 26 / 27 (index 24..26) = Noise / In 1 / In 2
N_MODES = 3                          # SC16.1 / SC17.1: 5 (+ In 1 / In 2 phase-inverted)
CTX = 0x200069E4
PARAM_GET = 0x0803542C
DSP_WRITE = 0x080292F8
MARK_DIRTY = 0x0803BDCC
H9_HOOK = 0x08028EEC
S_MODE, S_PAINT = 18, 20             # SC14 state block: mode[2] at +18, painted bits at +20
COLORS = ((0x32, 0x38), (0x20, 0x26))   # (on, dim): Synth 1 / Synth 2 colours


def popw(regs, lr=False):
    return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, c_gst, c_h9):
    a = Asm(base)
    # ---- c_shift: r0 = Shift held (clobbers r1-r3)
    a.label("c_shift")
    a.emit(push_list, [3], lr=True)
    a.emit(movw, 0, CTX & 0xFFFF); a.emit(movt, 0, CTX >> 16)
    a.emit(ldr_imm, 0, 0, 0); a.emit(ldr_imm, 0, 0, 0x40); a.emit(ldr_imm, 0, 0, 0x0C)
    a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
    a.emit(pop_list, [3], pc=True)

    # ---- c_synth: r0 = view -> r0 = synth 0/1, or 0xFF (clobbers r1)
    a.label("c_synth")
    a.emit(ldrb_w, 0, 0, SP_TRACK); a.emit(subs_imm8, 0, SP_TRACK0)
    a.emit(cmp_imm, 0, 1); a.emit(b_cond, "sy_ok", "ls"); a.emit(movs_imm, 0, 0xFF)
    a.label("sy_ok"); a.emit(raw, h(0x4770))

    # ---- c_spad (view, pad, vel): Shift + pad 25-27 -> mode; else stock
    a.label("c_spad")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2)
    a.emit(subs_imm8, 1, PAD0); a.emit(cmp_imm, 1, N_MODES - 1); a.emit(b_cond, "sp_stock", "hi")
    a.emit(bl, "c_shift"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sp_stock", "eq")
    a.emit(mov_reg, 0, 4); a.emit(bl, "c_synth"); a.emit(cmp_imm, 0, 1); a.emit(b_cond, "sp_stock", "hi")
    a.emit(mov_reg, 7, 0)                                                      # r7 = synth
    a.emit(bl, c_gst); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sp_stock", "eq")
    a.emit(adds_reg, 0, 0, 7); a.emit(mov_reg, 1, 5); a.emit(subs_imm8, 1, PAD0)
    a.emit(strb_imm, 1, 0, S_MODE)
    a.emit(movs_imm, 0, 0x20); a.emit(movs_imm, 1, 48); a.emit(bl, MARK_DIRTY)   # resend Audio In group (H9)
    a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("sp_stock")
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6)
    a.emit(raw, popw([4, 5, 6, 7], lr=True))
    a.emit(b_w, SP_PRESS)

    # ---- c_sleds (view) -> LED buffer; Shift held: pads 25-27 show the mode
    a.label("c_sleds")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0)
    a.emit(bl, SP_LEDS); a.emit(mov_reg, 5, 0)                                 # r5 = stock buffer
    a.emit(bl, c_gst); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sl_out", "eq")
    a.emit(mov_reg, 6, 0)                                                      # r6 = state
    a.emit(mov_reg, 0, 4); a.emit(bl, "c_synth"); a.emit(cmp_imm, 0, 1); a.emit(b_cond, "sl_out", "hi")
    a.emit(mov_reg, 7, 0)                                                      # r7 = synth
    a.emit(bl, "c_shift")
    a.emit(movs_imm, 2, 1); a.emit(raw, h(0x40BA))                             # lsls r2,r7 -> bit
    a.emit(ldrb_imm, 3, 6, S_PAINT)
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sl_held", "ne")
    a.emit(tst_reg, 3, 2); a.emit(b_cond, "sl_out", "eq")                      # released: repaint once
    a.emit(bics_reg, 3, 2); a.emit(strb_imm, 3, 6, S_PAINT)
    a.emit(mov_reg, 0, 4); a.emit(bl, SP_REPAINT); a.emit(b, "sl_out")
    a.label("sl_held")
    a.emit(orrs_reg, 3, 2); a.emit(strb_imm, 3, 6, S_PAINT)
    a.emit(adds_reg, 3, 6, 7); a.emit(ldrb_imm, 3, 3, S_MODE)                   # r3 = mode
    a.emit(cmp_imm, 7, 0); a.emit(b_cond, "sl_s2", "ne")
    a.emit(movs_imm, 0, COLORS[0][0]); a.emit(movs_imm, 1, COLORS[0][1]); a.emit(b, "sl_paint")
    a.label("sl_s2"); a.emit(movs_imm, 0, COLORS[1][0]); a.emit(movs_imm, 1, COLORS[1][1])
    a.label("sl_paint")
    for i in range(N_MODES):
        a.emit(cmp_imm, 3, i); a.emit(b_cond, f"sl_d{i}", "ne")
        a.emit(strh_imm, 0, 5, 2 * (PAD0 + i)); a.emit(b, f"sl_n{i}")
        a.label(f"sl_d{i}"); a.emit(strh_imm, 1, 5, 2 * (PAD0 + i))
        a.label(f"sl_n{i}")
    a.label("sl_out")
    a.emit(mov_reg, 0, 5)
    a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_h9b: Audio In group -> X:$3A01 / X:$3A02 = modes, then SC10's c_h9 (r0 preserved)
    a.label("c_h9b")
    a.emit(push_list, [0, 4, 5], lr=True)
    a.emit(bl, c_gst); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "h9_out", "eq")
    a.emit(mov_reg, 4, 0)
    for k, addr in enumerate((MODE_S1, MODE_S2)):
        a.emit(ldrb_imm, 1, 4, S_MODE + k); a.emit(lsls_imm, 1, 1, 8)
        a.emit(movw, 2, addr); a.emit(movs_imm, 0, 0); a.emit(bl, DSP_WRITE)
    a.label("h9_out")
    a.emit(raw, popw([0, 4, 5], lr=True))
    a.emit(b_w, c_h9)
    return a.assemble()


def dasm(lines):
    import dspasm_cache
    if D.SHORTX: return D.mark(list(zip(lines, dspasm_cache.assemble(lines))))   # (SHORTX) the moves x:(Rn+d) marked
    return [w for ws in dspasm_cache.assemble(lines) for w in ws]


def T(text):
    return dasm([text])


def dsp_code(base):
    a = D.Asm(base)
    a.label("li_init")                                   # replaces SC10 init_hook at P:$10B
    a.emit(T("clr a"))
    a.emit(D.st_abs, 'x', 'a', s10.FLAGS)
    a.emit(D.st_abs, 'x', 'a', MODE_S1)
    a.emit(D.st_abs, 'x', 'a', MODE_S2)
    a.emit(D.move_imm_r, 0, 0x2028)
    a.emit(D.RTS)
    a.label("li_hook")                                   # from P:$9C3 (jmp); a, b free here
    a.emit(D.ld_abs, 'x', 'a', SYNTH)                    # synth of this voice: 0 / 1
    a.emit(D.ld_abs, 'x', 'b', MODE_S1)
    a.emit(T("tst a"))
    a.emit(lambda t: [0x0AF0A2, t], "li_s2")             # jne li_s2
    a.label("li_mode")
    a.emit(T("tst b"))
    a.emit(lambda t: [0x0AF0AA, t], "li_stock")          # jeq li_stock
    a.emit(D.ld_abs, 'y', 'a', 0xFFD)                    # a = first input frame of this block
    a.emit(T("sub #1,b"))
    a.emit(T("add b,a"))                                 # + 0 (input 1) / + 1 (input 2)
    a.emit(T("move a,r2"))
    a.emit(T("move #2,n2"))
    a.emit(lambda t: [0x0AF080, t], HOOK_RET)            # jmp $9C5
    a.label("li_s2")
    a.emit(D.ld_abs, 'x', 'b', MODE_S2)
    a.emit(lambda t: [0x0AF080, t], "li_mode")
    a.label("li_stock")
    a.emit(T("move (r2)+n2"))
    a.emit(T("move #4,n2"))
    a.emit(lambda t: [0x0AF080, t], HOOK_RET)
    return a.assemble()


def patch_dsp(img: bytearray):
    P = [int.from_bytes(img[s10.p_off(p):s10.p_off(p) + 3], 'big') for p in range(s10.DSP0_WORDS)]
    assert P[HOOK_AT:HOOK_AT + 2] == [0x204A00, 0x3A0400], [hex(x) for x in P[HOOK_AT:HOOK_AT + 2]]
    assert P[0x9A5:0x9A7] == [0x62F400, 0x000F7D]
    init_jsr = P[0x10B:0x10D]
    assert init_jsr[0] == 0x0BF080 and init_jsr[1] == 0x80, [hex(x) for x in init_jsr]   # SC10 jsr init_hook
    base = max(p for p in range(0x80, DSP_FREE_END) if P[p]) + 1
    assert base == 0xD9, hex(base)
    words, labels = dsp_code(base)
    assert base + len(words) <= DSP_FREE_END, hex(base + len(words))
    assert all(x == 0 for x in P[base:base + len(words)])
    P[base:base + len(words)] = words
    P[0x10B:0x10D] = D.jsr(labels["li_init"])
    P[HOOK_AT:HOOK_AT + 2] = [0x0AF080, labels["li_hook"]]
    for p in range(s10.DSP0_WORDS):
        img[s10.p_off(p):s10.p_off(p) + 3] = P[p].to_bytes(3, 'big')
    return words, labels, base


def build(stock: bytes, listing: Path):
    img, report = s142.build(stock, listing)
    img = bytearray(img)
    img[sc.MARK_OFF:sc.MARK_OFF + 6] = MARKER.ljust(6, b"\0")
    words, dlabels, dbase = patch_dsp(img)
    # ARM
    c_gst = int(report["sc14"]["labels"]["c_gst"], 16)
    c_h9 = int(report["sc10"]["labels"]["c_h9"], 16)
    assert bytes(img[H9_HOOK - BASE:H9_HOOK - BASE + 4]) == b_w(H9_HOOK, c_h9)
    assert [struct.unpack_from("<I", img, SP_VT + 4 * i - BASE)[0] for i in (0, 7)] == [SP_PRESS | 1, SP_LEDS | 1]
    ext = (len(img) + BASE + 3) & ~3
    code, labels = arm_code(ext, c_gst, c_h9)
    img[H9_HOOK - BASE:H9_HOOK - BASE + 4] = b_w(H9_HOOK, labels["c_h9b"])
    struct.pack_into("<I", img, SP_VT - BASE, labels["c_spad"] | 1)
    struct.pack_into("<I", img, SP_VT + 0x1C - BASE, labels["c_sleds"] | 1)
    img += b"\xFF" * (ext - BASE - len(img)) + code
    while len(img) % 4:
        img += b"\xFF"
    assert len(img) <= 0x70000
    report["D"]["marker"] = MARKER.decode()
    report["sc15"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()},
                          listing=sc.disasm(code, ext), dsp_base=hex(dbase), dsp_words=len(words), dsp_labels={k: hex(v) for k, v in dlabels.items()},
                          dsp_listing=__import__("dspasm_cache").dis_listing(words, dbase))
    return bytes(img), report


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("stock_bin", type=Path)
    ap.add_argument("--listing", type=Path, default=Path(__file__).resolve().parents[1] / "re/app.asm")
    ap.add_argument("-o", "--outdir", type=Path, default=Path("build/sc15"))
    args = ap.parse_args()
    stock = args.stock_bin.read_bytes()
    img, report = build(stock, args.listing)
    syx = ct_fw.encode(img)
    info = ct_fw.decode(syx)
    assert info["image"] == img
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / f"circuittracks-4486-{NAME}.bin").write_bytes(img)
    (args.outdir / f"circuittracks-4486-{NAME}.syx").write_bytes(syx)
    manifest = dict(base="circuittracks-firmware-4486 (1.2.1)", marker=NAME, image_size=hex(len(img)),
                    image_sha256=ct_fw.sha256(img), syx_sha256=ct_fw.sha256(syx), crc32=hex(info["crc"]), report=report)
    (args.outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("\n".join(report["sc15"]["dsp_listing"]))
    print("image", hex(len(img)), "syx sha", manifest["syx_sha256"], "crc", manifest["crc32"])
