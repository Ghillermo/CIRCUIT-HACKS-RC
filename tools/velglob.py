"""SC51 / Beta 5.13 (the user, 2026-11-03: «Discard pad sensitivity. Add two new global controls on k1,k2, give them light: velocity to AMP and velocity
to filter. On patches without a velocity to AMP or velocity to mod Matrix, these route velocity to AMP and filter cutoff»; chosen: Advanced Setup, off
by default, each on its own, white LEDs, for the stock synths and the own synth): global velocity -> amp / filter.

  * Advanced Setup K1 = velocity -> amp, K2 = velocity -> filter, 0..127 (0 = off, the stock's), one step a knob event; saved with the unit's settings
    (parameter 6 bytes 2 / 3 = 0x80 | value, both copies, the save asked of lazysave: gmdrum's c_gmp / c_gmsave; nothing else uses them).  Their LEDs
    (panel 60 / 61) white, the brightness = the value, while Advanced Setup is on the screen.  The pads' velocity curve (velcurve) goes: the
    controller's pad entry back to the stock's (velcurve's code stays, unreachable).
  * Synth 1 / 2 (stock, read in the firmware and the emulator): the amp envelope's velocity (parameter 39, patch byte 69; 64 = none) is read at every
    note-on by 0x0802712E (0x08027142: bl 0x080360B2, the macro-aware getter) -> c_vgamp: a 64 there with K1 > 0 = 64 + K1 / 2.  The mod matrix
    (parameters 94 + 4 slot + 0 source 1, 1 source 2, 2 depth (64 = 0), 3 destination; source 4 = velocity, destination 12 = filter frequency) is sent
    by 0x0802853C..0x080285DC (six calls of 0x080360B2) -> c_vgmx: a patch with no velocity in its matrix (no slot with a source 4 and a depth
    other than 64) and K2 > 0 shows its last unused slot (depth 64) as velocity -> filter frequency, depth 64 + K2 / 2.  A change of K2 marks
    parameter 96 of both synths (MARK_DIRTY from the knob handler, the interface task) so the matrix goes out again; K1 takes effect at the next note.
  * The own synth of MIDI 1 / 2 (modmx): with its velocity source off (K1 of its matrix page at 0), the value sent for code 15 (envelope -> level) and
    code 1 (filter) is lowered by (127 - velocity) x K1 / 256 and (127 - velocity) x K2 / 256 (velocity 127 = no change): c_vgoff in place of
    c_mxfx's call of c_mxoff; a head of the DSP service chain marks both codes when the velocity or K1 / K2 change (c_vmark, RAM only).
RAM: modmx.MXR + 0x2230: + 0 "VGL1", + 4 K1, + 5 K2 (the cache, from the settings every LED frame), + 6 / + 9 track 0 / 1's last (velocity, K1, K2).
Installed after dspz in its freed flash (dspz.add).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, ldr_sp, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrb_w, ldrh_imm, lsls_imm, lsrs_imm,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, muls, pop_list, push_list, raw, str_imm, strb_imm, strh_reg, subs_imm8, subs_reg)
from thumb import bl as bl_enc  # noqa: E402
import modmx as MX  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import pgmch as PG  # noqa: E402
import mpatch as MP  # noqa: E402
import build_sc14 as S14  # noqa: E402
import velcurve as VC  # noqa: E402

RAM = MX.MXR + 0x2230
RSIG = 0x314C4756                                       # "VGL1"
PARAM, BYTE_AMP, BYTE_FLT, TAG = 6, 2, 3, 0x80
GET_MACRO, MARK_DIRTY, PARAM_RAW = 0x080360B2, 0x0803BDCC, 0x08036192
AMP_CALL = 0x08027142                                   # bl 0x080360B2 (parameter 39) in 0x0802712E
MX_CALLS = (0x0802854C, 0x0802856A, 0x08028592, 0x0802859C, 0x080285CA, 0x080285D8)   # the matrix sender's six calls
PATCH0, PATCH_SZ = 0x20010044, 344                     # Synth 1's patch in RAM (bank format), Synth 2 + 344
P_MX, SLOTS, SRC_VEL, DST_FILT, DEPTH0 = 124, 20, 4, 12, 64
LED_K = 60                                              # panel LEDs 60 / 61 = K1 / K2
COL = 0x01                                              # white
CODE_AMP, CODE_FLT = 15, 1                              # the own synth: envelope -> level, filter
SETUP = False


def use_setup():
    """SC51.2 / Beta 5.15 (the user, 2026-11-04: «k1 y k2 tienen que ir en setup, no Advanced Setup»): K1 / K2 and their LEDs in the normal Setup view
    (its K1 / K2 are free: gmdrum has K4..K8); in Advanced Setup K1 does nothing (velcurve's K1 would show a curve that no longer acts)."""
    global SETUP
    SETUP = True


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    RET = h(0x4770)

    # ---- c_vgram() -> r0 = our RAM (cleared the first time); clobbers r1, r2
    a.label("c_vgram")
    imm32(0, RAM); E(ldr_imm, 1, 0, 0); imm32(2, RSIG); E(cmp_reg, 1, 2); E(b_cond, "vr_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0); E(str_imm, 1, 0, 4); E(str_imm, 1, 0, 8)
    a.label("vr_x"); E(raw, RET)

    # ---- c_vgk(r0 = 0 K1 / 1 K2) -> r0 = 0..127 from the cache; clobbers r1-r3
    a.label("c_vgk")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, "c_vgram"); E(adds_reg, 0, 0, 4); E(ldrb_imm, 0, 0, 4); E(pop_list, [4], pc=True)

    # ---- c_vgset(r0 = 0 / 1) -> r0 = the settings' value 0..127; clobbers r1-r3
    a.label("c_vgset")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(movs_imm, 0, PARAM); E(movs_imm, 1, 0); E(bl, L["c_gmp"]); E(adds_reg, 0, 0, 4); E(ldrb_imm, 0, 0, BYTE_AMP)
    E(lsls_imm, 1, 0, 24); E(b_cond, "vs_0", "pl"); E(lsls_imm, 0, 0, 25); E(lsrs_imm, 0, 0, 25); E(pop_list, [4], pc=True)
    a.label("vs_0"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_vgamp (in place of 0x0802712E's bl 0x080360B2: r0 = synth, r1 = 39) -> r0 = the amp velocity; K1 when the patch has none
    a.label("c_vgamp")
    E(push_list, [4], lr=True)
    E(bl, GET_MACRO); E(cmp_imm, 0, DEPTH0); E(b_cond, "va_x", "ne")
    E(movs_imm, 0, 0); E(bl, "c_vgk"); E(lsrs_imm, 0, 0, 1); E(adds_imm8, 0, DEPTH0)
    a.label("va_x"); E(pop_list, [4], pc=True)

    # ---- c_vgmx (in place of the matrix sender's bl 0x080360B2: r0 = synth, r1 = the parameter): K2's virtual slot
    a.label("c_vgmx")
    E(push_list, [0, 1, 4, 5, 6, 7], lr=True)
    E(movs_imm, 0, 1); E(bl, "c_vgk"); E(cmp_imm, 0, 0); E(b_cond, "vm_n", "eq"); E(mov_reg, 7, 0)            # r7 = K2
    E(ldr_sp, 0, 0); E(movw, 1, PATCH_SZ); E(muls, 0, 1); imm32(1, PATCH0 + P_MX); E(adds_reg, 4, 0, 1)   # r4 = the matrix in RAM
    E(movs_imm, 5, 0); E(movs_imm, 6, 0xFF)                                                                  # r5 = slot, r6 = the last unused
    a.label("vm_l")
    E(lsls_imm, 0, 5, 2); E(adds_reg, 0, 0, 4); E(ldrb_imm, 1, 0, 2); E(cmp_imm, 1, DEPTH0); E(b_cond, "vm_u", "eq")
    E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, SRC_VEL); E(b_cond, "vm_n", "eq")                                    # velocity in the matrix: as it is
    E(ldrb_imm, 1, 0, 1); E(cmp_imm, 1, SRC_VEL); E(b_cond, "vm_n", "eq"); E(b, "vm_c")
    a.label("vm_u"); E(mov_reg, 6, 5)
    a.label("vm_c"); E(adds_imm8, 5, 1); E(cmp_imm, 5, SLOTS); E(b_cond, "vm_l", "lo")
    E(cmp_imm, 6, 0xFF); E(b_cond, "vm_n", "eq")
    E(ldr_sp, 0, 4); E(subs_imm8, 0, 94); E(lsrs_imm, 1, 0, 2); E(cmp_reg, 1, 6); E(b_cond, "vm_n", "ne")   # not that slot
    E(movs_imm, 1, 3); E(ands_reg, 0, 1)
    E(movs_imm, 1, SRC_VEL); E(cmp_imm, 0, 0); E(b_cond, "vm_r", "eq")
    E(movs_imm, 1, 0); E(cmp_imm, 0, 1); E(b_cond, "vm_r", "eq")
    E(movs_imm, 1, DST_FILT); E(cmp_imm, 0, 3); E(b_cond, "vm_r", "eq")
    E(lsrs_imm, 1, 7, 1); E(adds_imm8, 1, DEPTH0)                                                            # the depth
    a.label("vm_r"); E(mov_reg, 0, 1); E(raw, popw([2, 3, 4, 5, 6, 7], lr=True)); E(raw, RET)               # (r0 / r1 slots dropped)
    a.label("vm_n"); E(raw, popw([0, 1, 4, 5, 6, 7], lr=True)); E(b_w, GET_MACRO)

    # ---- c_vgoff (in place of c_mxfx's bl c_mxoff: r0 = track, r1 = code) -> r0 = the matrix's offset, lowered by K1 / K2 on soft notes
    a.label("c_vgoff")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, L["c_mxoff"]); E(mov_reg, 6, 0)
    E(movs_imm, 0, 0); E(cmp_imm, 5, CODE_AMP); E(b_cond, "vo_k", "eq")
    E(movs_imm, 0, 1); E(cmp_imm, 5, CODE_FLT); E(b_cond, "vo_x", "ne")
    a.label("vo_k"); E(bl, "c_vgk"); E(cmp_imm, 0, 0); E(b_cond, "vo_x", "eq"); E(mov_reg, 7, 0)              # r7 = K
    E(mov_reg, 0, 4); E(bl, L["c_mxblk"]); E(ldrh_imm, 1, 0, MX.B_POS); E(cmp_imm, 1, 0); E(b_cond, "vo_x", "ne")   # its velocity source on: as it is
    E(ldrb_w, 1, 0, MX.B_VEL); E(movs_imm, 0, 0x7F); E(ands_reg, 1, 0); E(subs_reg, 0, 0, 1)                   # 127 - velocity
    E(muls, 0, 7); E(lsrs_imm, 0, 0, 8); E(subs_reg, 6, 6, 0)
    a.label("vo_x"); E(mov_reg, 0, 6); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_vgtick: the head of the DSP service chain (RAM only): the own synth's codes 15 / 1 marked when the velocity or K1 / K2 change
    a.label("c_vgtick")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7, 8], lr=True))
    E(bl, "c_vgram"); E(mov_reg, 8, 0); E(movs_imm, 4, 0)
    a.label("vt_l")
    E(mov_reg, 0, 4); E(bl, L["c_mxblk"]); E(ldrb_w, 5, 0, MX.B_VEL); E(movs_imm, 0, 0x7F); E(ands_reg, 5, 0)    # r5 = velocity
    E(mov_reg, 0, 8); E(ldrb_imm, 1, 0, 4); E(ldrb_imm, 2, 0, 5); E(lsls_imm, 1, 1, 8); E(lsls_imm, 2, 2, 16)
    E(raw, h(0x4329)); E(raw, h(0x4311))                                                                     # orrs r1, r5; orrs r1, r2: r1 = vel | K1 << 8 | K2 << 16
    E(movs_imm, 2, 3); E(muls, 2, 4); E(adds_reg, 2, 2, 0); E(adds_imm8, 2, 6)                               # r2 = the track's last
    E(ldrb_imm, 3, 2, 0); E(ldrb_imm, 6, 2, 1); E(lsls_imm, 6, 6, 8); E(raw, h(0x4333))                        # orrs r3, r6
    E(ldrb_imm, 6, 2, 2); E(lsls_imm, 6, 6, 16); E(raw, h(0x4333)); E(cmp_reg, 3, 1); E(b_cond, "vt_n", "eq")
    E(strb_imm, 1, 2, 0); E(lsrs_imm, 3, 1, 8); E(strb_imm, 3, 2, 1); E(lsrs_imm, 3, 1, 16); E(strb_imm, 3, 2, 2)
    E(mov_reg, 0, 4); E(movs_imm, 1, CODE_AMP); E(bl, L["c_vmark"])
    E(mov_reg, 0, 4); E(movs_imm, 1, CODE_FLT); E(bl, L["c_vmark"])
    a.label("vt_n"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 2); E(b_cond, "vt_l", "lo")
    E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7, 8], lr=True)); E(b_w, prev["svc"])

    # ---- c_vgknob (the Setup view's slot 4: view, knob, delta): Advanced Setup K1 / K2
    a.label("c_vgknob")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(ldrb_w, 0, 0, PG.ADV_OFF); E(cmp_imm, 0, 0)
    if SETUP:                                                                                                # Setup: ours; Advanced: K1 swallowed
        E(b_cond, "vk_s", "eq"); E(cmp_imm, 5, 0); E(b_cond, "vk_x", "eq"); E(b, "vk_f")
        a.label("vk_s")
    else:
        E(b_cond, "vk_f", "eq")
    E(cmp_imm, 5, 1); E(b_cond, "vk_f", "hi")
    E(mov_reg, 0, 5); E(bl, "c_vgset"); E(adds_reg, 0, 0, 6)                                                 # + delta
    E(cmp_imm, 0, 0); E(b_cond, "vk_l", "ge"); E(movs_imm, 0, 0)
    a.label("vk_l"); E(cmp_imm, 0, 127); E(b_cond, "vk_h", "le"); E(movs_imm, 0, 127)
    a.label("vk_h"); E(mov_reg, 7, 0)
    E(bl, "c_vgram"); E(adds_reg, 0, 0, 5); E(strb_imm, 7, 0, 4)                                            # the cache
    E(movs_imm, 4, TAG); E(raw, h(0x433C))                                                                   # orrs r4, r7
    for cp in (0, 1):                                                                                        # both copies, no commit
        E(movs_imm, 0, PARAM); E(movs_imm, 1, cp); E(bl, L["c_gmp"]); E(adds_reg, 0, 0, 5); E(strb_imm, 4, 0, BYTE_AMP)
    E(bl, L["c_gmsave"])
    E(cmp_imm, 5, 1); E(b_cond, "vk_x", "ne")
    for s in (0, 1):                                                                                         # K2: both synths' matrix out again
        E(movs_imm, 0, s); E(movs_imm, 1, 96); E(bl, PARAM_RAW); E(mov_reg, 2, 0); E(movs_imm, 0, s); E(movs_imm, 1, 96); E(bl, MARK_DIRTY)
    a.label("vk_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("vk_f"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["knob"])

    # ---- c_vgled (the LED task calls: ctrl, frame): the chain; the cache from the settings; in Advanced Setup K1 / K2 white, brightness = value
    a.label("c_vgled")
    E(push_list, [3, 4, 5, 6], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    E(movs_imm, 4, 0)
    a.label("vl_c"); E(mov_reg, 0, 4); E(bl, "c_vgset"); E(mov_reg, 6, 0); E(bl, "c_vgram"); E(adds_reg, 0, 0, 4); E(strb_imm, 6, 0, 4)
    E(adds_imm8, 4, 1); E(cmp_imm, 4, 2); E(b_cond, "vl_c", "lo")
    E(bl, L["c_gmsetup"] if SETUP else L["c_vcadv"]); E(cmp_imm, 0, 0); E(b_cond, "vl_x", "eq")
    E(movs_imm, 4, 0)
    a.label("vl_l"); E(mov_reg, 0, 4); E(bl, "c_vgk"); E(adds_imm8, 0, 2); E(cmp_imm, 0, 127); E(b_cond, "vl_b", "ls"); E(movs_imm, 0, 127)
    a.label("vl_b"); E(lsls_imm, 0, 0, 8); E(adds_imm8, 0, COL)
    E(movs_imm, 1, 2 * LED_K); E(lsls_imm, 2, 4, 1); E(adds_reg, 1, 1, 2); E(strh_reg, 0, 5, 1)
    E(adds_imm8, 4, 1); E(cmp_imm, 4, 2); E(b_cond, "vl_l", "lo")
    a.label("vl_x"); E(pop_list, [3, 4, 5, 6], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """After dspz (dspz.add): the pad entry back to the stock's, the Setup view's slot 4, the LED task calls, the DSP service chain, the note-on's amp
    velocity, the matrix sender's six calls, c_mxfx's call of c_mxoff."""
    import ct_fw
    import hole
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_gmp=lab("gmdrum", "c_gmp"), c_gmsave=lab("gmdrum", "c_gmsave"), c_gmsetup=lab("gmdrum", "c_gmsetup"), c_vcadv=lab("velcurve", "c_vcadv"), c_mxoff=lab("modmx", "c_mxoff"),
             c_mxblk=lab("modmx", "c_mxblk"), c_vmark=lab("vcf20", "c_vmark"))
    prev = dict(knob=u(PG.SETUP_VT + 16) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE), svc=MP.bw_target(img, S14.SVC_HOOK, BASE))
    for c in (AMP_CALL,) + MX_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, GET_MACRO), hex(c)
    mxfx = lab("modmx", "c_mxfx")
    site = next(x for x in range(mxfx, mxfx + 0x40, 2) if bytes(img[x - BASE:x - BASE + 4]) == bl_enc(x, L["c_mxoff"]))
    code, labels = arm_code(base_addr, L, prev)
    img += code
    while len(img) % 4:
        img += bytes([0xFF])
    struct.pack_into("<I", img, VC.CTRL_VT - BASE, VC.PAD_ENTRY | 1)                      # the pad curve gone
    struct.pack_into("<I", img, PG.SETUP_VT + 16 - BASE, labels["c_vgknob"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_vgled"])
    img[S14.SVC_HOOK - BASE:S14.SVC_HOOK - BASE + 4] = b_w(S14.SVC_HOOK, labels["c_vgtick"])
    img[AMP_CALL - BASE:AMP_CALL - BASE + 4] = bl_enc(AMP_CALL, labels["c_vgamp"])
    for c in MX_CALLS:
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_vgmx"])
    img[site - BASE:site - BASE + 4] = bl_enc(site, labels["c_vgoff"])
    hole.rehash(img, report, site)
    return labels, code, prev
