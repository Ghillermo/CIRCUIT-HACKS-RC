"""A7PROT (the user, 2026-11-19): the Mixer's pads 15 / 16, a prototype on top of mixsolo v2.
  * Pad 16 as v2 (held + track pads = solo, latched, white; tapped alone = the mutes before / flip mode, orange), but its flip is a mute flip: a
    track pad held flips that track (muted -> sounding, sounding -> muted) until it is let go; the tracks not held stay as they are.
  * Pad 15 tapped = the solo group, pad 15 white (the mutes saved): each track pad pressed toggles that track in the group, which sounds alone (the
    first press = a solo of that track; taking the last one out = everything muted).  Pad 15 tapped again = the mutes from before, dim.
  * Pad 15 held + track pads = v2's solo flip (only the pads held sound, while held; the last let go = the mixer as it was); pad 15 let go = the
    flip ends (the mixer as it was).  Pad 15 used with a track pad is not a tap.
  * The modes exclude each other: entering one leaves the other (a solo's saved mutes come back first).  A project load leaves every mode.
Installed as v2's replacement: b.w at the entries of c_sopad2 / c_soled2 / c_soload (v2's code stays, unreachable; its c_soget / c_soset are used).
RAM: mixsolo.RAM2 = MXR + 0x2220: + 0 'SOL3', + 4 mode (0 off, 1 solo, 2 mute flip, 3 group), + 5 the saved mutes (1 / 2 / 3), + 6 pad 16 (bit 0
down, bit 1 used), + 7 the mute-flip pads held, + 8 the solo's choice in this press, + 9 pad 15's flip: the mutes before, + 10 its pads held, + 11
pad 15 (bit 0 down, bit 1 used), + 12 the group (bit = track).
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, add_sp_imm, ands_reg, b, b_cond, b_w, bl, bx_lr, cmp_imm, cmp_reg, eors_reg, h, ldr_imm, ldrb_imm, lsls_imm, mov_reg,  # noqa: E402
                   movs_imm, movt, movw, orrs_reg, pop_list, push_list, raw, str_imm, strb_imm, strh_imm, tst_reg)
import mixsolo as M  # noqa: E402
import qmute as Q  # noqa: E402

RAM = M.RAM2
MAGIC3 = 0x334C4F53                                          # 'SOL3'
PAD_SOLO = M.PAD_SOLO                                        # pad 16
PAD_GRP = 14                                                 # pad 15
COL_DIM, COL_ON, COL_FLIP = M.COL_DIM, M.COL_ON, M.COL_FLIP
HELD = M.HELD
popw, pushw = M.popw, M.pushw


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def held(rd, rs): E(raw, h(0xF8D0 | rs) + h(rd << 12 | HELD))      # ldr.w rd, [rs, #0x84]
    def bit5(rd):                                                       # rd |= 1 << r5 (r0 clobbered)
        E(movs_imm, 0, 1); E(raw, h(0x40A8)); E(orrs_reg, rd, 0)        # lsls r0, r5
    # ---- c_s3st: r0 = the state (cleared the first time); clobbers r1, r2
    a.label("c_s3st")
    imm32(0, RAM); E(ldr_imm, 1, 0, 0); imm32(2, MAGIC3); E(cmp_reg, 1, 2); E(b_cond, "s3_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0); E(str_imm, 1, 0, 4); E(str_imm, 1, 0, 8); E(str_imm, 1, 0, 12)
    a.label("s3_x"); E(bx_lr)
    # ---- c_s3leave (r6 = the state): a solo's / a group's / a held mute flip's saved mutes back, mode off
    a.label("c_s3leave")
    E(push_list, [3], lr=True)
    E(ldrb_imm, 0, 6, 4); E(cmp_imm, 0, 0); E(b_cond, "lv_x", "eq")
    E(cmp_imm, 0, 2); E(b_cond, "lv_r", "ne")
    E(ldrb_imm, 1, 6, 7); E(cmp_imm, 1, 0); E(b_cond, "lv_o", "eq")
    a.label("lv_r"); E(ldrb_imm, 0, 6, 5); E(bl, prev["soset"])
    a.label("lv_o"); E(movs_imm, 0, 0); E(strb_imm, 0, 6, 4); E(strb_imm, 0, 6, 7)
    a.label("lv_x"); E(pop_list, [3], pc=True)

    # ---- c_s3pad (the Mixer view's slot 0: view, pad, velocity)
    a.label("c_s3pad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, L["c_gact"]); E(cmp_imm, 0, 0); E(b_cond, "p3_f", "ne")                      # Master FX: its pads
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "p3_f", "ne")                     # Shift: the repeats, the queued mutes
    E(bl, "c_s3st"); E(mov_reg, 6, 0)
    E(cmp_imm, 5, PAD_SOLO); E(b_cond, "p3_15", "ne")
    E(movs_imm, 0, 1); E(strb_imm, 0, 6, 6); E(movs_imm, 0, 0); E(strb_imm, 0, 6, 8); E(b, "p3_f")   # pad 16 down: the choice anew
    a.label("p3_15")
    E(cmp_imm, 5, PAD_GRP); E(b_cond, "p3_t", "ne")
    E(movs_imm, 0, 1); E(strb_imm, 0, 6, 11); E(b, "p3_f")                             # pad 15 down
    a.label("p3_t")
    E(cmp_imm, 5, 8); E(b_cond, "p3_f", "hs")
    imm32(0, Q.MGR); held(7, 0)
    E(lsls_imm, 0, 7, 16); E(b_cond, "p3_nh", "pl")                                    # bit 15: pad 16 held -> solo
    E(ldrb_imm, 0, 6, 6); E(movs_imm, 1, 2); E(orrs_reg, 0, 1); E(strb_imm, 0, 6, 6)
    E(ldrb_imm, 0, 6, 4); E(cmp_imm, 0, 1); E(b_cond, "p3_ns", "eq")                   # solo / group: the first saved state stays
    E(cmp_imm, 0, 3); E(b_cond, "p3_ns", "eq")
    E(cmp_imm, 0, 2); E(b_cond, "p3_sv", "ne")
    E(ldrb_imm, 1, 6, 7); E(cmp_imm, 1, 0); E(b_cond, "p3_ns", "ne")                   # mute flip with pads held: saved already
    a.label("p3_sv"); E(bl, prev["soget"]); E(strb_imm, 0, 6, 5)
    a.label("p3_ns"); E(movs_imm, 0, 1); E(strb_imm, 0, 6, 4); E(movs_imm, 0, 0); E(strb_imm, 0, 6, 7); E(strb_imm, 0, 6, 12)
    E(ldrb_imm, 7, 6, 8); bit5(7); E(strb_imm, 7, 6, 8)
    E(mov_reg, 0, 7); E(b, "p3_inv")
    a.label("p3_nh")
    E(lsls_imm, 0, 7, 17); E(b_cond, "p3_ng", "pl")                                    # bit 14: pad 15 held -> solo flip
    E(ldrb_imm, 0, 6, 11); E(movs_imm, 1, 2); E(orrs_reg, 0, 1); E(strb_imm, 0, 6, 11)
    E(ldrb_imm, 7, 6, 10); E(cmp_imm, 7, 0); E(b_cond, "p3_fh", "ne")
    E(bl, prev["soget"]); E(strb_imm, 0, 6, 9)
    a.label("p3_fh"); bit5(7); E(strb_imm, 7, 6, 10); E(mov_reg, 0, 7); E(b, "p3_inv")
    a.label("p3_ng")
    E(ldrb_imm, 0, 6, 4); E(cmp_imm, 0, 3); E(b_cond, "p3_mf", "ne")                   # group: the track in / out
    E(ldrb_imm, 7, 6, 12); E(movs_imm, 0, 1); E(raw, h(0x40A8)); E(eors_reg, 7, 0); E(strb_imm, 7, 6, 12)
    E(mov_reg, 0, 7); E(b, "p3_inv")
    a.label("p3_mf")
    E(cmp_imm, 0, 2); E(b_cond, "p3_f", "ne")                                          # mute flip: the track flipped while held
    E(ldrb_imm, 7, 6, 7); E(cmp_imm, 7, 0); E(b_cond, "p3_mh", "ne")
    E(bl, prev["soget"]); E(strb_imm, 0, 6, 5)
    a.label("p3_mh"); bit5(7); E(strb_imm, 7, 6, 7)
    E(ldrb_imm, 0, 6, 5); E(eors_reg, 0, 7); E(b, "p3_ap")
    a.label("p3_inv"); E(movs_imm, 1, 0xFF); E(eors_reg, 0, 1)
    a.label("p3_ap"); E(bl, prev["soset"])
    E(add_sp_imm, 12); E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("p3_f"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["pad"])

    # ---- c_s3led (the LED task calls: ctrl, frame): pads 15 / 16 let go, the flip pads let go, the two LEDs
    a.label("c_s3led")
    E(push_list, [3, 4, 5, 6, 7], lr=True); E(mov_reg, 4, 1); E(bl, prev["ledtask"])
    E(bl, "c_s3st"); E(mov_reg, 6, 0)
    imm32(0, Q.MGR); held(7, 0)
    # pad 16 let go
    E(ldrb_imm, 0, 6, 6); E(movs_imm, 1, 1); E(tst_reg, 0, 1); E(b_cond, "l3_g", "eq")
    E(lsls_imm, 1, 7, 16); E(b_cond, "l3_g", "mi")
    E(movs_imm, 1, 0); E(strb_imm, 1, 6, 6)
    E(movs_imm, 1, 2); E(tst_reg, 0, 1); E(b_cond, "l3_g", "ne")                       # used with a track
    E(ldrb_imm, 0, 6, 4); E(cmp_imm, 0, 0); E(b_cond, "l3_lv", "ne")
    E(movs_imm, 0, 2); E(strb_imm, 0, 6, 4); E(b, "l3_g")                              # a tap with nothing on: mute flip
    a.label("l3_lv"); E(bl, "c_s3leave")
    # pad 15 let go
    a.label("l3_g")
    E(ldrb_imm, 0, 6, 11); E(movs_imm, 1, 1); E(tst_reg, 0, 1); E(b_cond, "l3_fr", "eq")
    E(lsls_imm, 1, 7, 17); E(b_cond, "l3_fr", "mi")
    E(movs_imm, 1, 0); E(strb_imm, 1, 6, 11)
    E(movs_imm, 1, 2); E(tst_reg, 0, 1); E(b_cond, "l3_gt", "eq")
    E(ldrb_imm, 1, 6, 10); E(cmp_imm, 1, 0); E(b_cond, "l3_fr", "eq")                  # used: the flip ends
    E(movs_imm, 1, 0); E(strb_imm, 1, 6, 10); E(ldrb_imm, 0, 6, 9); E(bl, prev["soset"]); E(b, "l3_fr")
    a.label("l3_gt")                                                                   # a tap: the group on / off
    E(ldrb_imm, 0, 6, 4); E(cmp_imm, 0, 3); E(b_cond, "l3_gon", "ne")
    E(bl, "c_s3leave"); E(b, "l3_fr")
    a.label("l3_gon")
    E(cmp_imm, 0, 1); E(b_cond, "l3_gk", "eq")                                         # solo: its saved mutes back, kept
    E(cmp_imm, 0, 2); E(b_cond, "l3_gs", "ne")
    E(ldrb_imm, 1, 6, 7); E(cmp_imm, 1, 0); E(b_cond, "l3_gs", "eq")
    a.label("l3_gk"); E(ldrb_imm, 0, 6, 5); E(bl, prev["soset"]); E(b, "l3_gm")
    a.label("l3_gs"); E(bl, prev["soget"]); E(strb_imm, 0, 6, 5)
    a.label("l3_gm"); E(movs_imm, 0, 3); E(strb_imm, 0, 6, 4); E(movs_imm, 0, 0); E(strb_imm, 0, 6, 7); E(strb_imm, 0, 6, 12)
    # pad 15's flip: pads let go
    a.label("l3_fr")
    E(ldrb_imm, 5, 6, 10); E(cmp_imm, 5, 0); E(b_cond, "l3_mr", "eq")
    E(mov_reg, 0, 5); E(ands_reg, 0, 7); E(cmp_reg, 0, 5); E(b_cond, "l3_mr", "eq")
    E(strb_imm, 0, 6, 10); E(cmp_imm, 0, 0); E(b_cond, "l3_fp", "ne")
    E(ldrb_imm, 0, 6, 9); E(b, "l3_fs")                                                # the last one: the mixer as it was
    a.label("l3_fp"); E(movs_imm, 1, 0xFF); E(eors_reg, 0, 1)
    a.label("l3_fs"); E(bl, prev["soset"])
    # the mute flip: pads let go
    a.label("l3_mr")
    E(ldrb_imm, 0, 6, 4); E(cmp_imm, 0, 2); E(b_cond, "l3_l", "ne")
    E(ldrb_imm, 5, 6, 7); E(cmp_imm, 5, 0); E(b_cond, "l3_l", "eq")
    E(mov_reg, 0, 5); E(ands_reg, 0, 7); E(cmp_reg, 0, 5); E(b_cond, "l3_l", "eq")
    E(strb_imm, 0, 6, 7); E(ldrb_imm, 1, 6, 5); E(eors_reg, 0, 1); E(bl, prev["soset"])
    # the LEDs
    a.label("l3_l")
    imm32(0, Q.MGR); E(ldr_imm, 0, 0, 0x6C); imm32(1, Q.MIX_VIEW); E(cmp_reg, 0, 1); E(b_cond, "l3_x", "ne")
    E(bl, L["c_gact"]); E(cmp_imm, 0, 0); E(b_cond, "l3_x", "ne")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "l3_x", "ne")
    E(ldrb_imm, 5, 6, 4)
    E(movs_imm, 1, COL_ON); E(lsls_imm, 0, 7, 16); E(b_cond, "l3_w", "mi")             # pad 16 held: bright white
    E(cmp_imm, 5, 1); E(b_cond, "l3_w", "eq")                                          # solo: white
    E(movs_imm, 1, COL_FLIP); E(cmp_imm, 5, 2); E(b_cond, "l3_w", "eq")                # mute flip: orange
    E(movs_imm, 1, COL_DIM)
    a.label("l3_w"); E(strh_imm, 1, 4, 2 * PAD_SOLO)
    E(movs_imm, 1, COL_ON); E(lsls_imm, 0, 7, 17); E(b_cond, "l3_w2", "mi")            # pad 15 held: white
    E(cmp_imm, 5, 3); E(b_cond, "l3_w2", "eq")                                         # group: white
    E(movs_imm, 1, COL_DIM)
    a.label("l3_w2"); E(strh_imm, 1, 4, 2 * PAD_GRP)
    a.label("l3_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)

    # ---- c_s3load (the end of the stock's «apply session»): every mode off, nothing restored
    a.label("c_s3load")
    E(raw, pushw([0, 1, 2, 3, 12], lr=True))
    E(bl, "c_s3st"); E(movs_imm, 1, 0)
    for o in (4, 6, 7, 10, 11, 12): E(strb_imm, 1, 0, o)
    E(raw, popw([0, 1, 2, 3, 12], lr=True)); E(b_w, prev["load"])
    return a.assemble()


def install(img, report, base_addr):
    """After v2 (dspz.add): v3's code; b.w at v2's three entries."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    v2 = {k: int(v, 16) for k, v in report["mixsolo2"]["labels"].items()}
    p2 = {k: int(v, 16) for k, v in report["mixsolo2"]["prev"].items()}
    L = dict(c_shift=int(report["sc15"]["labels"]["c_shift"], 16), c_gact=int(report["sc17"]["labels"]["c_gact"], 16))
    prev = dict(pad=p2["pad"], ledtask=p2["ledtask"], load=p2["load"], soget=v2["c_soget"], soset=v2["c_soset"])
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    for old, new in (("c_sopad2", "c_s3pad"), ("c_soled2", "c_s3led"), ("c_soload", "c_s3load")):
        o = v2[old] - BASE
        assert img[o + 1] in (0xB5, 0xE9), f"{old}: not a push ({img[o]:#x} {img[o + 1]:#x})"   # v2's entry: push / push.w
        img[o:o + 4] = b_w(v2[old], labels[new])
    return labels, code, prev
