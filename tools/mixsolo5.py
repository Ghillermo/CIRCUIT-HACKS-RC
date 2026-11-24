"""Alpha 7.45 = mixsolo4 (Alpha 7.44) with flip on top of a solo (the user, 2026-11-24). From 7.44 (the user, 2026-11-24; roadmap «one solo mode on pad 16, flip becomes a toggle on pad 15»: «Toggle in / out, tap 16 ends», «Held
tracks invert mute»).  Replaces A7PROT's mixsolo3 on top of mixsolo v2 (the same three entries):
  * Pad 16 tapped = solo armed (white, the mutes saved, nothing changes yet); each track pad tapped then puts that track in / out of the solo group,
    which sounds alone (the group emptied = the saved mutes again, still armed); pad 16 tapped again = the mutes from before, dim.
  * Pad 16 held + track pads = the group anew: the pads tapped during that hold (the solo stays on after letting go).
  * Pad 15 tapped = flip on / off (orange): with it on, a track pad held flips that track (muted <-> sounding) while held, the others as they are.
  * Flip works on top of a solo (the user, 2026-11-24): its base = the mixer when the first pad is held (the solo's result); turning flip on / off
    leaves the solo as it is.  A project load leaves both, nothing restored.
RAM: mixsolo.RAM2 = MXR + 0x2220 ('SOL5'): + 4 solo (0 / 1), + 5 the saved mutes, + 6 pad 16 (bit 0 down, bit 1 used), + 7 the flip's pads held,
+ 8 the group chosen in this hold, + 9 flip on, + 10 the flip's base, + 11 pad 15 down, + 12 the group (bit = track).
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
MAGIC = 0x354C4F53                                           # 'SOL5' (7.45: flip on top of a solo)
PAD_SOLO = M.PAD_SOLO                                        # pad 16
PAD_FLIP = 14                                                # pad 15
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
    # ---- c_s5st: r0 = the state (cleared the first time); clobbers r1, r2
    a.label("c_s5st")
    imm32(0, RAM); E(ldr_imm, 1, 0, 0); imm32(2, MAGIC); E(cmp_reg, 1, 2); E(b_cond, "s5_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0); E(str_imm, 1, 0, 4); E(str_imm, 1, 0, 8); E(str_imm, 1, 0, 12)
    a.label("s5_x"); E(bx_lr)
    # ---- c_s5leave (r6 = the state): solo off, its saved mutes back (a flip's held pads dropped)
    a.label("c_s5leave")
    E(push_list, [3], lr=True)
    E(ldrb_imm, 0, 6, 4); E(cmp_imm, 0, 0); E(b_cond, "lv_x", "eq")
    E(ldrb_imm, 0, 6, 5); E(bl, prev["soset"])
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, 4); E(strb_imm, 0, 6, 7); E(strb_imm, 0, 6, 12)
    a.label("lv_x"); E(pop_list, [3], pc=True)
    # ---- c_s5solo (r6): solo on with an empty group (the mutes saved)
    a.label("c_s5solo")
    E(push_list, [3], lr=True)
    E(bl, prev["soget"]); E(strb_imm, 0, 6, 5)
    E(movs_imm, 0, 1); E(strb_imm, 0, 6, 4); E(movs_imm, 0, 0); E(strb_imm, 0, 6, 12); E(strb_imm, 0, 6, 7)
    E(pop_list, [3], pc=True)
    # ---- c_s5grp (r6): the group applied: empty = the saved mutes, else every track but the group muted
    a.label("c_s5grp")
    E(push_list, [3], lr=True)
    E(ldrb_imm, 0, 6, 12); E(cmp_imm, 0, 0); E(b_cond, "gp_s", "ne")
    E(ldrb_imm, 0, 6, 5); E(b, "gp_a")
    a.label("gp_s"); E(movs_imm, 1, 0xFF); E(eors_reg, 0, 1)
    a.label("gp_a"); E(bl, prev["soset"]); E(pop_list, [3], pc=True)

    # ---- c_s5pad (the Mixer view's slot 0: view, pad, velocity)
    a.label("c_s5pad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, L["c_gact"]); E(cmp_imm, 0, 0); E(b_cond, "p4_f", "ne")                      # Master FX: its pads
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "p4_f", "ne")                     # Shift: the repeats, the queued mutes
    E(bl, "c_s5st"); E(mov_reg, 6, 0)
    E(cmp_imm, 5, PAD_SOLO); E(b_cond, "p4_15", "ne")
    E(movs_imm, 0, 1); E(strb_imm, 0, 6, 6); E(movs_imm, 0, 0); E(strb_imm, 0, 6, 8); E(b, "p4_sw")   # pad 16 down
    a.label("p4_15")
    E(cmp_imm, 5, PAD_FLIP); E(b_cond, "p4_t", "ne")
    E(movs_imm, 0, 1); E(strb_imm, 0, 6, 11); E(b, "p4_sw")                            # pad 15 down
    a.label("p4_t")
    E(cmp_imm, 5, 8); E(b_cond, "p4_f", "hs")
    imm32(0, Q.MGR); held(7, 0)
    E(lsls_imm, 0, 7, 16); E(b_cond, "p4_nh", "pl")                                    # bit 15: pad 16 held -> the group anew
    E(ldrb_imm, 0, 6, 6); E(movs_imm, 1, 2); E(orrs_reg, 0, 1); E(strb_imm, 0, 6, 6)
    E(ldrb_imm, 0, 6, 4); E(cmp_imm, 0, 0); E(b_cond, "p4_on", "ne")
    E(bl, "c_s5solo")
    a.label("p4_on")
    E(ldrb_imm, 7, 6, 8); bit5(7); E(strb_imm, 7, 6, 8); E(strb_imm, 7, 6, 12)
    E(b, "p4_ap")
    a.label("p4_nh")
    E(ldrb_imm, 0, 6, 9); E(cmp_imm, 0, 0); E(b_cond, "p4_mf", "ne")                   # flip on: the track flipped (on top of a solo)
    E(ldrb_imm, 0, 6, 4); E(cmp_imm, 0, 0); E(b_cond, "p4_f", "eq")                    # nothing on: the stock's mute
    E(ldrb_imm, 7, 6, 12); E(movs_imm, 0, 1); E(raw, h(0x40A8)); E(eors_reg, 7, 0); E(strb_imm, 7, 6, 12)   # solo: in / out
    a.label("p4_ap"); E(bl, "c_s5grp"); E(b, "p4_sw")
    a.label("p4_mf")
    E(ldrb_imm, 7, 6, 7); E(cmp_imm, 7, 0); E(b_cond, "p4_mh", "ne")
    E(bl, prev["soget"]); E(strb_imm, 0, 6, 10)                                        # the flip's base = the mixer now
    a.label("p4_mh"); bit5(7); E(strb_imm, 7, 6, 7)
    E(ldrb_imm, 0, 6, 10); E(eors_reg, 0, 7); E(bl, prev["soset"])
    a.label("p4_sw"); E(add_sp_imm, 12); E(pop_list, [4, 5, 6, 7], pc=True)          # swallowed
    a.label("p4_f"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["pad"])

    # ---- c_s5led (the LED task calls: ctrl, frame): pads 15 / 16 let go, the flip pads let go, the two LEDs
    a.label("c_s5led")
    E(push_list, [3, 4, 5, 6, 7], lr=True); E(mov_reg, 4, 1); E(bl, prev["ledtask"])
    E(bl, "c_s5st"); E(mov_reg, 6, 0)
    imm32(0, Q.MGR); held(7, 0)
    # pad 16 let go: a tap = solo on (armed) / off
    E(ldrb_imm, 0, 6, 6); E(movs_imm, 1, 1); E(tst_reg, 0, 1); E(b_cond, "l4_g", "eq")
    E(lsls_imm, 1, 7, 16); E(b_cond, "l4_g", "mi")
    E(movs_imm, 1, 0); E(strb_imm, 1, 6, 6)
    E(movs_imm, 1, 2); E(tst_reg, 0, 1); E(b_cond, "l4_g", "ne")                       # used with a track: the group stays
    E(ldrb_imm, 0, 6, 4); E(cmp_imm, 0, 0); E(b_cond, "l4_son", "eq")
    E(bl, "c_s5leave"); E(b, "l4_g")
    a.label("l4_son"); E(bl, "c_s5solo")
    # pad 15 let go: flip on / off (a solo stays)
    a.label("l4_g")
    E(ldrb_imm, 0, 6, 11); E(cmp_imm, 0, 0); E(b_cond, "l4_mr", "eq")
    E(lsls_imm, 1, 7, 17); E(b_cond, "l4_mr", "mi")
    E(movs_imm, 1, 0); E(strb_imm, 1, 6, 11)
    E(ldrb_imm, 0, 6, 9); E(movs_imm, 1, 1); E(eors_reg, 0, 1); E(strb_imm, 0, 6, 9)
    E(ldrb_imm, 1, 6, 7); E(cmp_imm, 1, 0); E(b_cond, "l4_mr", "eq")                   # pads still flipped: back to the base
    E(movs_imm, 1, 0); E(strb_imm, 1, 6, 7); E(ldrb_imm, 0, 6, 10); E(bl, prev["soset"])
    # the flip: pads let go
    a.label("l4_mr")
    E(ldrb_imm, 5, 6, 7); E(cmp_imm, 5, 0); E(b_cond, "l4_l", "eq")
    E(mov_reg, 0, 5); E(ands_reg, 0, 7); E(cmp_reg, 0, 5); E(b_cond, "l4_l", "eq")
    E(strb_imm, 0, 6, 7); E(ldrb_imm, 1, 6, 10); E(eors_reg, 0, 1); E(bl, prev["soset"])
    # the LEDs
    a.label("l4_l")
    imm32(0, Q.MGR); E(ldr_imm, 0, 0, 0x6C); imm32(1, Q.MIX_VIEW); E(cmp_reg, 0, 1); E(b_cond, "l4_x", "ne")
    E(bl, L["c_gact"]); E(cmp_imm, 0, 0); E(b_cond, "l4_x", "ne")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "l4_x", "ne")
    E(movs_imm, 1, COL_ON); E(lsls_imm, 0, 7, 16); E(b_cond, "l4_w", "mi")             # pad 16 held: white
    E(ldrb_imm, 5, 6, 4); E(cmp_imm, 5, 0); E(b_cond, "l4_w", "ne")                    # solo: white
    E(movs_imm, 1, COL_DIM)
    a.label("l4_w"); E(strh_imm, 1, 4, 2 * PAD_SOLO)
    E(movs_imm, 1, COL_FLIP); E(ldrb_imm, 5, 6, 9); E(cmp_imm, 5, 0); E(b_cond, "l4_w2", "ne")   # flip on: orange
    E(movs_imm, 1, COL_DIM)
    a.label("l4_w2"); E(strh_imm, 1, 4, 2 * PAD_FLIP)
    a.label("l4_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)

    # ---- c_s5load (the end of the stock's «apply session»): both modes off, nothing restored
    a.label("c_s5load")
    E(raw, pushw([0, 1, 2, 3, 12], lr=True))
    E(bl, "c_s5st"); E(movs_imm, 1, 0)
    for o in (4, 6, 7, 8, 9, 11, 12): E(strb_imm, 1, 0, o)
    E(raw, popw([0, 1, 2, 3, 12], lr=True)); E(b_w, prev["load"])
    return a.assemble()


def install(img, report, base_addr):
    """After v2 (dspz.add): v4's code; b.w at v2's three entries."""
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
    for old, new in (("c_sopad2", "c_s5pad"), ("c_soled2", "c_s5led"), ("c_soload", "c_s5load")):
        o = v2[old] - BASE
        assert img[o + 1] in (0xB5, 0xE9), f"{old}: not a push ({img[o]:#x} {img[o + 1]:#x})"   # v2's entry: push / push.w
        img[o:o + 4] = b_w(v2[old], labels[new])
    return labels, code, prev
