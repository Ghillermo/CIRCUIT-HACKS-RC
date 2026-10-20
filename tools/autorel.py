"""SC45 (the user, 2026-10-19: «En velocity view, shift+pad hace que deje de aplicarse automatización (posición de knob + init en lugar de posición +
valor previo de automatización)»; with him: Synth 1 / 2 and MIDI 1 / 2; the 8 lanes): a step that lets go of the automation.

The stock's playback of the automation (found 2026-10-19: 0x08031AFC, a listener of the object 0x2003EBDC; with the transport running
([obj + 0x48] = 0x20011034 p0), on each step of a note track t (0..3 = Synth 1, Synth 2, MIDI 1, MIDI 2: the editor [[obj + 0x38] + 4 t], its
step store + 0xC p1) it takes, for each lane 0..7, the first byte <> 0xFF of the step's 6 micro steps (ldrb.w fp, [r0, #0x3a8] at 0x08031B8E;
r4 = t, r6 = the lane, sl = the micro step, r5 = the object) into p[lane] of the track's macro store [[obj + 0x2C] + 4 t] and commits it (the
macros of Synth 1 / 2 move; MIDI 1 / 2's own engine through vcf21's c_vplay); a lane with no byte at that step leaves the store as it is.  The
value it sets replaces the knob's, so there is no knob position to go back to.  (0x0804BA8C / 0x0804BB02, which smpick guards, only play the
step pressed on the step pads: the preview.)  Here:
  * the mark: bit 7 of byte [3] of the step (stepmod uses bits 0-2 / 4-6); **Velocity view (subview 2: [ctrl + 0x152] = 9 t + 2), Shift + a step
    pad** (pads 1-16, + 16 on the 17-32 page) toggles it; the press and its release are swallowed; with Shift the step pads are yellow, the marked
    ones red (the LED task chain);
  * the playback's read (0x08031B8E -> c_arread): the first value a lane plays (its flag clear) keeps the value it is about to replace (the base,
    as a lane value: Synth 1 / 2 the macro position GETTER(t, 174 + 17 k); MIDI 1 / 2 with the engine on c_vtou(code, value) of the row's code)
    and sets the flag; at a marked step no lane plays (0xFF) and a flagged lane gets its base back in the store (committed by the stock after
    the lanes), flag cleared;
  * a knob turned by hand clears its lane's flag (the knob's value is the base from then on): Synth 1 / 2 by the head of slot 4 of the macro
    handlers (the handler = [[[CTX] + 0x40] + 0x2C] + 0x148 + 4 t), MIDI 1 / 2 by vcf21's three calls of c_vsync (the lane of the code, c_vlane).
RAM: modmx.MXR + 0x1B0: + 0 the flags (bit 8 t + k), + 4 the bases (8 t + k), + 36 the swallowed pad + 1, + 40 "AR01" (the flags cleared
the first time: that RAM holds the power-up pattern)."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bics_reg, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrb_reg,  # noqa: E402
                   lsls_imm, lsls_reg, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, str_imm, strb_imm, strb_reg,
                   strh_reg, subs_imm8, subs_reg, tst_reg, blx_reg)
import vcf21 as V  # noqa: E402
import mpatch as MP  # noqa: E402
import packio as PK  # noqa: E402
import modmx as MX  # noqa: E402
from build_sc14 import udiv  # noqa: E402
PARAM_WPTR = 0x080354FA

RAM = MX.MXR + 0x1B0
OBJ0, OSZ, PAGE_OFF = 0x20041EB0, 0x170, 0xC4
MGR, CONT = 0x20040B10, 0x20040DB8
SUB_VEL = 2
PB_READ, PB_OLD = 0x08031B8E, bytes.fromhex("90f8a8b3")      # ldrb.w fp, [r0, #0x3a8]
MARK = 0x80
COL_AV, COL_MARK = 0x2D, 0x53
SIG = 0x31305241                     # "AR01" at RAM + 40: the flags are cleared the first time (the RAM holds the power-up pattern)
INV = V.INV


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def ldrb_w(rt, rn, imm12): return h(0xF890 | rn) + h(rt << 12 | imm12)
def ldrsb_reg(rt, rn, rm): return h(0x5600 | rm << 6 | rn << 3 | rt)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_a{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)

    # ---- c_arst() -> r0 = RAM, the flags cleared the first time; clobbers r1, r2
    a.label("c_arst")
    imm32(0, RAM); E(ldr_imm, 1, 0, 40); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "as_x", "eq")
    E(str_imm, 2, 0, 40); E(movs_imm, 1, 0); E(str_imm, 1, 0, 0)
    a.label("as_x"); E(raw, h(0x4770))

    # ---- c_artrk(r0 = a step / lane object) -> r0 = 0..3, or 0xFF; clobbers r1
    a.label("c_artrk")
    imm32(1, OBJ0)
    for t in range(4):
        E(cmp_reg, 0, 1); E(b_cond, f"tk_{t}", "eq")
        if t < 3: imm32(1, OBJ0 + OSZ * (t + 1))
    E(movs_imm, 0, 0xFF); E(raw, h(0x4770))
    for t in range(4):
        a.label(f"tk_{t}"); E(movs_imm, 0, t); E(raw, h(0x4770))

    # ---- c_arpat(r0 = track 0..3) -> r0 = the pattern of the track (c_sdpat numbers MIDI 1 / 2 = 0 / 1, the synths 2 / 3); clobbers r1-r3
    a.label("c_arpat")
    E(adds_imm8, 0, 2); E(cmp_imm, 0, 4); E(b_cond, "ap_g", "lo"); E(subs_imm8, 0, 4)
    a.label("ap_g"); E(b_w, L["c_sdpat"])

    # ---- c_arvel(r0 = track) -> r0 = 1 when that track's Velocity view shows; clobbers r1-r3
    a.label("c_arvel")
    imm32(1, MGR); E(ldr_imm, 2, 1, 0x6C); imm32(3, CONT); E(cmp_reg, 2, 3); E(b_cond, "av_0", "ne")
    E(raw, h(0xF891) + h(2 << 12 | 0x152))                                                 # ldrb.w r2, [r1, #0x152]
    E(movs_imm, 3, 9); E(muls, 3, 0); E(adds_imm8, 3, SUB_VEL); E(cmp_reg, 2, 3); E(b_cond, "av_0", "ne")
    E(movs_imm, 0, 1); E(raw, h(0x4770))
    a.label("av_0"); E(movs_imm, 0, 0); E(raw, h(0x4770))

    # ---- c_arpage(r0 = step object) -> r0 = 16 on the 17-32 page, else 0; clobbers r1-r3
    a.label("c_arpage")
    E(push_list, [], lr=True)
    E(raw, h(0xF8D0) + h(0 << 12 | PAGE_OFF)); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(cmp_imm, 0, 0); E(b_cond, "pg_x", "eq"); E(movs_imm, 0, 16)
    a.label("pg_x"); E(pop_list, [], pc=True)

    # ---- c_arpad (slot 0 of the step objects: obj, pad, velocity): Velocity view + Shift = the step's mark
    a.label("c_arpad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(cmp_imm, 1, 15); bc("pd_prev", "hi"); E(mov_reg, 5, 1); E(mov_reg, 6, 0)
    E(bl, "c_artrk"); E(cmp_imm, 0, 3); bc("pd_prev", "hi"); E(mov_reg, 4, 0)
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); bc("pd_prev", "eq")
    E(mov_reg, 0, 4); E(bl, "c_arvel"); E(cmp_imm, 0, 0); bc("pd_prev", "eq")
    E(mov_reg, 0, 6); E(bl, "c_arpage"); E(adds_reg, 5, 5, 0)                              # r5 = the step
    E(mov_reg, 0, 4); E(bl, "c_arpat"); E(movs_imm, 1, 28); E(muls, 1, 5); E(adds_reg, 0, 0, 1)
    E(ldrb_imm, 1, 0, 3); E(movs_imm, 2, MARK); E(raw, h(0x4051)); E(strb_imm, 1, 0, 3)     # eors r1, r2
    imm32(0, RAM + 36); E(raw, h(0x9901)); E(adds_imm8, 1, 1); E(strb_imm, 1, 0, 0)            # ldr r1, [sp, #4]: the pad
    E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("pd_prev"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["spad"])

    # ---- c_arrelp (slot 1 of the step objects: obj, pad): the release of a swallowed press swallowed too
    a.label("c_arrelp")
    imm32(3, RAM + 36); E(ldrb_imm, 2, 3, 0); E(cmp_imm, 2, 0); E(b_cond, "rl_prev", "eq")
    E(subs_imm8, 2, 1); E(cmp_reg, 2, 1); E(b_cond, "rl_prev", "ne")
    E(movs_imm, 2, 0); E(strb_imm, 2, 3, 0); E(raw, h(0x4770))
    a.label("rl_prev"); E(b_w, prev["srel"])

    # ---- c_arled (the LED task calls: ctrl, frame): the chain, then Shift in a Velocity view = the steps yellow, the marked ones red
    a.label("c_arled")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 5, 1)
    E(bl, prev["ledtask"])
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "le_x", "eq")
    E(movs_imm, 4, 0)
    a.label("le_t"); E(mov_reg, 0, 4); E(bl, "c_arvel"); E(cmp_imm, 0, 0); E(b_cond, "le_f", "ne")
    E(adds_imm8, 4, 1); E(cmp_imm, 4, 4); E(b_cond, "le_t", "lo"); E(b, "le_x")
    a.label("le_f")
    E(movs_imm, 0, OSZ >> 4); E(lsls_imm, 0, 0, 4); E(muls, 0, 4); imm32(1, OBJ0); E(adds_reg, 0, 0, 1); E(bl, "c_arpage"); E(mov_reg, 6, 0)
    E(mov_reg, 0, 4); E(bl, "c_arpat"); E(movs_imm, 1, 28); E(muls, 1, 6); E(adds_reg, 6, 0, 1)   # r6 = the page's first step
    E(movs_imm, 7, 0)
    a.label("le_l")
    E(movs_imm, 1, COL_AV); E(ldrb_imm, 0, 6, 3); E(movs_imm, 2, MARK); E(tst_reg, 0, 2); E(b_cond, "le_c", "eq"); E(movs_imm, 1, COL_MARK)
    a.label("le_c"); E(lsls_imm, 0, 7, 1); E(strh_reg, 1, 5, 0)
    E(adds_imm8, 6, 28); E(adds_imm8, 7, 1); E(cmp_imm, 7, 16); E(b_cond, "le_l", "lo")
    a.label("le_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_arbase(r0 = track 0..3, r1 = lane) -> r0 = the lane value the track has now, or 0xFF (MIDI with the engine off); clobbers r1-r3
    a.label("c_arbase")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(cmp_imm, 0, 2); E(b_cond, "bs_m", "hs")
    E(movs_imm, 1, 17); E(muls, 1, 5); E(adds_imm8, 1, 174); E(bl, V.GETTER); E(pop_list, [4, 5], pc=True)
    a.label("bs_m")
    E(subs_imm8, 4, 2); E(mov_reg, 0, 4); E(bl, L["c_von"]); E(cmp_imm, 0, 0); E(b_cond, "bs_n", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_vrow"]); E(ldrb_reg, 5, 0, 5)                               # r5 = the lane's code
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, L["c_vvaddr"]); E(movs_imm, 1, 0); E(raw, ldrsb_reg(1, 0, 1))
    E(mov_reg, 0, 5); E(bl, L["c_vtou"]); E(pop_list, [4, 5], pc=True)
    a.label("bs_n"); E(movs_imm, 0, 0xFF); E(pop_list, [4, 5], pc=True)

    # ---- c_arread (in place of the playback's ldrb.w fp, [r0, #0x3a8]; r4 = the track, r6 = the lane, sl = the micro step, r5 = the object)
    a.label("c_arread")
    E(push_list, [1, 2, 3, 4, 5, 6, 7], lr=True)
    E(raw, ldrb_w(7, 0, 0x3A8))                                                              # r7 = the byte
    E(cmp_imm, 4, 3); E(b_cond, "rd_x", "hi"); E(cmp_imm, 6, 8); E(b_cond, "rd_x", "hs")
    E(raw, h(0x4651))                                                                        # mov r1, sl
    E(movs_imm, 2, 6); E(raw, udiv(1, 1, 2))                                                 # r1 = the step
    E(push_list, [1]); E(mov_reg, 0, 4); E(bl, "c_arpat"); E(pop_list, [1])
    E(movs_imm, 2, 28); E(muls, 1, 2); E(adds_reg, 0, 0, 1); E(ldrb_imm, 0, 0, 3)              # r0 = byte [3] of the step
    E(lsls_imm, 1, 4, 3); E(adds_reg, 1, 1, 6); E(movs_imm, 2, 1); E(lsls_reg, 2, 1)           # r1 = 8 t + k, r2 = its bit
    E(push_list, [0, 1, 2]); E(bl, "c_arst"); E(ldr_imm, 3, 0, 0); E(pop_list, [0, 1, 2])      # r3 = the flags
    E(movs_imm, 6, MARK); E(tst_reg, 0, 6); E(b_cond, "rd_nm", "eq")
    E(movs_imm, 7, 0xFF)                                                                      # a marked step: nothing plays
    E(tst_reg, 3, 2); E(b_cond, "rd_x", "eq")
    E(bics_reg, 3, 2); imm32(0, RAM); E(str_imm, 3, 0, 0)
    imm32(0, RAM + 4); E(ldrb_reg, 6, 0, 1); E(cmp_imm, 6, 0xFF); E(b_cond, "rd_x", "eq")      # r6 = the base
    E(movs_imm, 0, 7); E(ands_reg, 1, 0)                                                     # r1 = k
    E(ldr_imm, 0, 5, 0x2C); E(lsls_imm, 2, 4, 2)
    E(adds_reg, 0, 0, 2); E(ldr_imm, 0, 0, 0); E(bl, PARAM_WPTR); E(strb_imm, 6, 0, 0)        # p[k] of the track's macro store = the base
    E(b, "rd_x")
    a.label("rd_nm")                                                                          # a value about to play: the base, the first time
    E(cmp_imm, 7, 0xFF); E(b_cond, "rd_x", "eq"); E(tst_reg, 3, 2); E(b_cond, "rd_x", "ne")
    E(orrs_reg, 3, 2); imm32(0, RAM); E(str_imm, 3, 0, 0)
    E(push_list, [1]); E(mov_reg, 0, 4); E(movs_imm, 2, 7); E(ands_reg, 1, 2); E(bl, "c_arbase"); E(pop_list, [1])
    imm32(2, RAM + 4); E(strb_reg, 0, 2, 1)
    a.label("rd_x"); E(raw, h(0x46BB))                                                       # mov fp, r7
    E(pop_list, [1, 2, 3, 4, 5, 6, 7], pc=True)

    # ---- c_arknob (slot 4 of the macro handlers: obj, knob, delta): a synth's macro turned by hand = its lane's flag cleared
    a.label("c_arknob")
    E(push_list, [0, 1, 2, 3, 4], lr=True)
    imm32(3, V.CTX_PTR); E(ldr_imm, 3, 3, 0); E(cmp_imm, 3, 0); E(b_cond, "kn_x", "eq")
    E(ldr_imm, 3, 3, 0x40); E(cmp_imm, 3, 0); E(b_cond, "kn_x", "eq")
    E(ldr_imm, 3, 3, 0x2C); E(cmp_imm, 3, 0); E(b_cond, "kn_x", "eq")
    E(movs_imm, 4, 0)
    E(raw, h(0xF8D3) + h(2 << 12 | 0x148)); E(cmp_reg, 2, 0); E(b_cond, "kn_f", "eq")        # ldr.w r2, [r3, #0x148]: Synth 1's
    E(movs_imm, 4, 8)
    E(raw, h(0xF8D3) + h(2 << 12 | 0x14C)); E(cmp_reg, 2, 0); E(b_cond, "kn_x", "ne")        # Synth 2's
    a.label("kn_f")
    E(movs_imm, 2, 7); E(ands_reg, 1, 2); E(adds_reg, 1, 1, 4); E(movs_imm, 2, 1); E(lsls_reg, 2, 1)
    E(push_list, [2]); E(bl, "c_arst"); E(pop_list, [2]); E(ldr_imm, 1, 0, 0); E(bics_reg, 1, 2); E(str_imm, 1, 0, 0)
    a.label("kn_x"); E(raw, popw([0, 1, 2, 3, 4], lr=True)); E(b_w, prev["knob"])

    # ---- c_arsync (in place of vcf21's bl c_vsync: track 0 / 1, code, value): the lane of the code, its flag cleared; then c_vsync
    a.label("c_arsync")
    E(push_list, [0, 1, 2, 4], lr=True); E(mov_reg, 4, 0)
    E(bl, L["c_vlane"]); E(cmp_imm, 0, 8); E(b_cond, "sy_x", "hs")
    E(lsls_imm, 1, 4, 3); E(adds_reg, 0, 0, 1); E(adds_imm8, 0, 16); E(movs_imm, 1, 1); E(lsls_reg, 1, 0)   # bit 8 (t + 2) + k
    E(mov_reg, 3, 1); E(bl, "c_arst"); E(ldr_imm, 1, 0, 0); E(bics_reg, 1, 3); E(str_imm, 1, 0, 0)
    a.label("sy_x"); E(raw, popw([0, 1, 2, 4], lr=True)); E(b_w, L["c_vsync"])
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the heads of slots 0 / 1 of the step objects, of slot 4 of the macro handlers and of the LED task chain;
    the playback's lane read; vcf21's calls of c_vsync."""
    import ct_fw
    import fxdiag as FD
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("vcf20", k) for k in ("c_sdpat", "c_von", "c_vrow", "c_vvaddr", "c_vtou", "c_vlane", "c_vsync")}
    L["c_shift"] = lab("sc15", "c_shift")
    KN = V.AC64_VT
    import recinst as RI
    prev = dict(spad=u(RI.STEP_VT) & ~1, srel=u(RI.STEP_VT + 4) & ~1, knob=u(KN + 16) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, L, prev)
    end0 = BASE + len(img)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    struct.pack_into("<I", img, RI.STEP_VT - BASE, labels["c_arpad"] | 1)
    struct.pack_into("<I", img, RI.STEP_VT + 4 - BASE, labels["c_arrelp"] | 1)
    struct.pack_into("<I", img, KN + 16 - BASE, labels["c_arknob"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_arled"])
    assert bytes(img[PB_READ - BASE:PB_READ - BASE + 4]) == PB_OLD, bytes(img[PB_READ - BASE:PB_READ - BASE + 4]).hex()
    img[PB_READ - BASE:PB_READ - BASE + 4] = bl(PB_READ, labels["c_arread"])
    sites = MX.bl_sites(img, 0x0805CDDC, end0, L["c_vsync"], BASE)
    assert len(sites) == 3, [hex(s) for s in sites]
    for s in sites: img[s - BASE:s - BASE + 4] = bl(s, labels["c_arsync"])
    return labels, code, prev
