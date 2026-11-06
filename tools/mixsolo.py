"""SC50.5 / Beta 5.8 (the user, 2026-11-02: «pad 16 de mixer función sólo. Mantener este pad y cualquier combinación de pads mutea el resto», «Se queda así»): solo in the Mixer view.

The stock's pads 10-16 of the Mixer do nothing.  Pad 16 held ([MGR + 0x84], a bit per held pad) + pads 1-8: those tracks sound, every other track muted, through the stock's own
toggle (0x08046626, so the pads show it as always); the choice starts anew with each press of pad 16 and adds up while it is held; letting it go leaves the mutes as they are.
Not on the Master FX page of the view.  The pad: dim white, bright while held; with Shift the row is the scene's repeats.  RAM: modmx.MXR + 0x2210, the tracks chosen (read only
after pad 16 cleared it).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, add_sp_imm, adds_imm8, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, lsls_imm, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list,  # noqa: E402
                   push_list, raw, strb_imm, strh_imm)
from thumb import bl as bl_enc  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import modmx as MX  # noqa: E402
import qmute as Q  # noqa: E402

RAM = MX.MXR + 0x2210
PAD_SOLO = 15
HELD = 0x84                                                  # [MGR + 0x84]: the pads held, bit = pad
COL_DIM, COL_ON = 0x02, 0x01


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    # ---- c_sopad (the Mixer view's slot 0: view, pad, velocity)
    a.label("c_sopad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, L["c_gact"]); E(cmp_imm, 0, 0); E(b_cond, "so_f", "ne")                        # Master FX: its pads
    imm32(6, RAM)
    E(cmp_imm, 5, PAD_SOLO); E(b_cond, "so_t", "ne")
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, 0); E(b, "so_f")                                # pad 16: the choice anew
    a.label("so_t")
    E(cmp_imm, 5, 8); E(b_cond, "so_f", "hs")
    imm32(0, Q.MGR); E(raw, h(0xF8D0) + h(0 << 12 | HELD)); E(lsls_imm, 0, 0, 16); E(b_cond, "so_f", "pl")   # ldr.w r0, [r0, #0x84]: bit 15
    E(ldrb_imm, 7, 6, 0); E(movs_imm, 0, 1); E(raw, h(0x40A8)); E(orrs_reg, 7, 0); E(strb_imm, 7, 6, 0)      # lsls r0, r5
    E(movs_imm, 5, 0)
    a.label("so_l")                                                                      # r5 = a track, r7 = the chosen ones
    E(ldr_imm, 0, 4, 0x60); E(muls, 0, 5); E(ldr_imm, 1, 4, 0x68); E(raw, h(0x5808)); E(movs_imm, 1, 0); E(bl, Q.PARAM_GET); E(ldrb_imm, 0, 0, 0)   # ldr r0, [r1, r0]
    E(mov_reg, 1, 7); E(raw, h(0x40E9)); E(movs_imm, 2, 1); E(raw, h(0x4011))            # lsrs r1, r5; ands r1, r2: 1 = chosen
    E(cmp_reg, 0, 1); E(b_cond, "so_n", "ne")                                            # (muted 1, chosen 1) or (0, 0): the stock's toggle
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, Q.MIX_PAD)
    a.label("so_n"); E(adds_imm8, 5, 1); E(cmp_imm, 5, 8); E(b_cond, "so_l", "lo")
    E(add_sp_imm, 12); E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("so_f"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["pad"])

    # ---- c_soled (the LED task calls: ctrl, frame): pad 16 of the Mixer
    a.label("c_soled")
    E(push_list, [3, 4], lr=True); E(mov_reg, 4, 1); E(bl, prev["ledtask"])
    imm32(0, Q.MGR); E(ldr_imm, 0, 0, 0x6C); imm32(1, Q.MIX_VIEW); E(cmp_reg, 0, 1); E(b_cond, "sl_x", "ne")
    E(bl, L["c_gact"]); E(cmp_imm, 0, 0); E(b_cond, "sl_x", "ne")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "sl_x", "ne")
    E(movs_imm, 1, COL_DIM); imm32(0, Q.MGR); E(raw, h(0xF8D0) + h(0 << 12 | HELD)); E(lsls_imm, 0, 0, 16); E(b_cond, "sl_w", "pl"); E(movs_imm, 1, COL_ON)
    a.label("sl_w"); E(strh_imm, 1, 4, 2 * PAD_SOLO)
    a.label("sl_x"); E(pop_list, [3, 4], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    L = dict(c_shift=int(report["sc15"]["labels"]["c_shift"], 16), c_gact=int(report["sc17"]["labels"]["c_gact"], 16))
    prev = dict(pad=u(Q.MIX_VT) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, L, prev)
    at_end = base_addr - BASE >= len(img)                    # (SC52.7) or in hole.py's hole: the tail goes there and the image is cut back
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000 or not at_end
    struct.pack_into("<I", img, Q.MIX_VT - BASE, labels["c_sopad"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_soled"])
    return labels, code, prev


# ---------------------------------------------------------------- v2: solo latched + solo flip (SC50.9 / Beta 5.12)
"""SC50.9 / Beta 5.12 (the user, 2026-11-03): pad 16 of the Mixer becomes a toggle.
  * Solo: pad 16 held + track pads = the mixer's mutes saved, those tracks solo (as before), pad 16 lit white; held again with other track pads = those
    solo, the rest muted (the saved state stays the first one).  Pad 16 tapped alone = the mutes before the solo come back.
  * Flip: pad 16 tapped alone with no solo = flip mode, pad 16 orange (tapped again = off).  In flip, holding track pads = those sound, the rest muted,
    until they are let go: the mixer as it was.  Pad 16 held + track pads in flip = solo (flip off).
  * Loading a project leaves either mode without restoring (the saved mutes were the other project's).
Installed after dspz in its freed flash (dspz.add): the head of the Mixer's slot 0 in front of v1's predecessor (v1's code is skipped), the LED task
calls in front of v1's predecessor, the end of «apply session».  Pad 16 let go and the flip pads let go are seen by the LED task from [MGR + 0x84].
RAM: MXR + 0x2220: + 0 'SOL2', + 4 mode (0 off, 1 solo, 2 flip), + 5 the saved mutes (bit = track), + 6 pad 16 (bit 0 down, bit 1 used with a track),
+ 7 the flip pads held, + 8 the solo's choice in this press.
"""
RAM2 = MX.MXR + 0x2220
MAGIC2 = 0x324C4F53                                          # 'SOL2'
COL_FLIP = 0x45                                              # orange (the user, 2026-11-03)


def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code2(base, L, prev):
    from thumb import ands_reg, bx_lr, eors_reg, str_imm, tst_reg
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def held(rd, rs):                                        # ldr.w rd, [rs, #0x84]
        E(raw, h(0xF8D0 | rs) + h(rd << 12 | HELD))
    # ---- c_sost: r0 = the state (signed, cleared the first time); clobbers r1, r2
    a.label("c_sost")
    imm32(0, RAM2); E(ldr_imm, 1, 0, 0); imm32(2, MAGIC2); E(cmp_reg, 1, 2); E(b_cond, "ss_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0); E(str_imm, 1, 0, 4); E(str_imm, 1, 0, 8)
    a.label("ss_x"); E(bx_lr)
    # ---- c_somute: r0 = track -> r0 = 1 muted / 0 (r4 = the Mixer view)
    a.label("c_somute")
    E(push_list, [3], lr=True)
    E(mov_reg, 1, 0); E(ldr_imm, 0, 4, 0x60); E(muls, 0, 1); E(ldr_imm, 1, 4, 0x68); E(raw, h(0x5808))   # ldr r0, [r1, r0]
    E(movs_imm, 1, 0); E(bl, Q.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(cmp_imm, 0, 0); E(b_cond, "sm_x", "eq"); E(movs_imm, 0, 1)
    a.label("sm_x"); E(pop_list, [3], pc=True)
    # ---- c_soget: r0 = the mutes (bit = track)
    a.label("c_soget")
    E(push_list, [3, 4, 5, 6], lr=True); imm32(4, Q.MIX_VIEW); E(movs_imm, 5, 0); E(movs_imm, 6, 0)
    a.label("sg_l"); E(mov_reg, 0, 5); E(bl, "c_somute"); E(raw, h(0x40A8)); E(orrs_reg, 6, 0)       # lsls r0, r5
    E(adds_imm8, 5, 1); E(cmp_imm, 5, 8); E(b_cond, "sg_l", "lo")
    E(mov_reg, 0, 6); E(pop_list, [3, 4, 5, 6], pc=True)
    # ---- c_soset(r0 = the mutes wanted): each track that differs through the stock's toggle
    a.label("c_soset")
    E(push_list, [3, 4, 5, 7], lr=True); E(mov_reg, 7, 0); imm32(4, Q.MIX_VIEW); E(movs_imm, 5, 0)
    a.label("se_l"); E(mov_reg, 0, 5); E(bl, "c_somute")
    E(mov_reg, 1, 7); E(raw, h(0x40E9)); E(movs_imm, 2, 1); E(ands_reg, 1, 2)                         # lsrs r1, r5
    E(cmp_reg, 0, 1); E(b_cond, "se_n", "eq")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(movs_imm, 2, 127); E(bl, Q.MIX_PAD)
    a.label("se_n"); E(adds_imm8, 5, 1); E(cmp_imm, 5, 8); E(b_cond, "se_l", "lo")
    E(pop_list, [3, 4, 5, 7], pc=True)

    # ---- c_sopad2 (the Mixer view's slot 0: view, pad, velocity)
    a.label("c_sopad2")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, L["c_gact"]); E(cmp_imm, 0, 0); E(b_cond, "sp_f", "ne")                       # Master FX: its pads
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "sp_f", "ne")                      # Shift: the repeats, the queued mutes
    E(bl, "c_sost"); E(mov_reg, 6, 0)
    E(cmp_imm, 5, PAD_SOLO); E(b_cond, "sp_t", "ne")
    E(movs_imm, 0, 1); E(strb_imm, 0, 6, 6); E(movs_imm, 0, 0); E(strb_imm, 0, 6, 8); E(b, "sp_f")   # pad 16 down: the choice anew
    a.label("sp_t")
    E(cmp_imm, 5, 8); E(b_cond, "sp_f", "hs")
    imm32(0, Q.MGR); held(0, 0); E(lsls_imm, 0, 0, 16); E(b_cond, "sp_nh", "pl")       # bit 15: pad 16 held
    E(ldrb_imm, 0, 6, 6); E(movs_imm, 1, 2); E(orrs_reg, 0, 1); E(strb_imm, 0, 6, 6)   # pad 16 used
    E(ldrb_imm, 0, 6, 4); E(cmp_imm, 0, 1); E(b_cond, "sp_ns", "eq")                   # solo already: the first saved state stays
    E(cmp_imm, 0, 2); E(b_cond, "sp_sv", "ne")
    E(ldrb_imm, 1, 6, 7); E(cmp_imm, 1, 0); E(b_cond, "sp_ns", "ne")                   # flip with pads held: saved already
    a.label("sp_sv"); E(bl, "c_soget"); E(strb_imm, 0, 6, 5)
    a.label("sp_ns"); E(movs_imm, 0, 1); E(strb_imm, 0, 6, 4); E(movs_imm, 0, 0); E(strb_imm, 0, 6, 7)
    E(ldrb_imm, 7, 6, 8); E(movs_imm, 0, 1); E(raw, h(0x40A8)); E(orrs_reg, 7, 0); E(strb_imm, 7, 6, 8)   # lsls r0, r5
    E(mov_reg, 0, 7); E(b, "sp_ap")
    a.label("sp_nh")                                                                    # flip: the pads held sound
    E(ldrb_imm, 0, 6, 4); E(cmp_imm, 0, 2); E(b_cond, "sp_f", "ne")
    E(ldrb_imm, 7, 6, 7); E(cmp_imm, 7, 0); E(b_cond, "sp_fh", "ne")
    E(bl, "c_soget"); E(strb_imm, 0, 6, 5)
    a.label("sp_fh"); E(movs_imm, 0, 1); E(raw, h(0x40A8)); E(orrs_reg, 7, 0); E(strb_imm, 7, 6, 7); E(mov_reg, 0, 7)
    a.label("sp_ap"); E(movs_imm, 1, 0xFF); E(eors_reg, 0, 1); E(bl, "c_soset")
    E(add_sp_imm, 12); E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("sp_f"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["pad"])

    # ---- c_soled2 (the LED task calls: ctrl, frame): pad 16 let go, the flip pads let go, pad 16's LED
    a.label("c_soled2")
    E(push_list, [3, 4, 5, 6, 7], lr=True); E(mov_reg, 4, 1); E(bl, prev["ledtask"])
    E(bl, "c_sost"); E(mov_reg, 6, 0)
    imm32(0, Q.MGR); held(7, 0)
    E(ldrb_imm, 0, 6, 6); E(movs_imm, 1, 1); E(tst_reg, 0, 1); E(b_cond, "sl_r", "eq")  # pad 16 down?
    E(lsls_imm, 1, 7, 16); E(b_cond, "sl_r", "mi")                                     # still held
    E(movs_imm, 1, 0); E(strb_imm, 1, 6, 6)
    E(movs_imm, 1, 2); E(tst_reg, 0, 1); E(b_cond, "sl_r", "ne")                       # used with a track: nothing more
    E(ldrb_imm, 0, 6, 4); E(cmp_imm, 0, 0); E(b_cond, "sl_lv", "ne")
    E(movs_imm, 0, 2); E(strb_imm, 0, 6, 4); E(b, "sl_r")                              # a tap with nothing on: flip
    a.label("sl_lv"); E(cmp_imm, 0, 1); E(b_cond, "sl_rs", "eq")
    E(ldrb_imm, 1, 6, 7); E(cmp_imm, 1, 0); E(b_cond, "sl_of", "eq")
    a.label("sl_rs"); E(ldrb_imm, 0, 6, 5); E(bl, "c_soset")                            # the mutes before
    a.label("sl_of"); E(movs_imm, 0, 0); E(strb_imm, 0, 6, 4); E(strb_imm, 0, 6, 7)
    a.label("sl_r")
    E(ldrb_imm, 0, 6, 4); E(cmp_imm, 0, 2); E(b_cond, "sl_l", "ne")                    # flip: pads let go
    E(ldrb_imm, 5, 6, 7); E(cmp_imm, 5, 0); E(b_cond, "sl_l", "eq")
    E(mov_reg, 0, 5); E(ands_reg, 0, 7); E(cmp_reg, 0, 5); E(b_cond, "sl_l", "eq")
    E(strb_imm, 0, 6, 7); E(cmp_imm, 0, 0); E(b_cond, "sl_pt", "ne")
    E(ldrb_imm, 0, 6, 5); E(b, "sl_st")                                                 # the last one: the mixer as it was
    a.label("sl_pt"); E(movs_imm, 1, 0xFF); E(eors_reg, 0, 1)
    a.label("sl_st"); E(bl, "c_soset")
    a.label("sl_l")
    imm32(0, Q.MGR); E(ldr_imm, 0, 0, 0x6C); imm32(1, Q.MIX_VIEW); E(cmp_reg, 0, 1); E(b_cond, "sl_x2", "ne")
    E(bl, L["c_gact"]); E(cmp_imm, 0, 0); E(b_cond, "sl_x2", "ne")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "sl_x2", "ne")
    E(movs_imm, 1, COL_ON); E(lsls_imm, 0, 7, 16); E(b_cond, "sl_w2", "mi")            # held: bright white
    E(ldrb_imm, 0, 6, 4); E(cmp_imm, 0, 1); E(b_cond, "sl_w2", "eq")                   # solo: white
    E(movs_imm, 1, COL_FLIP); E(cmp_imm, 0, 2); E(b_cond, "sl_w2", "eq")               # flip: orange
    E(movs_imm, 1, COL_DIM)
    a.label("sl_w2"); E(strh_imm, 1, 4, 2 * PAD_SOLO)
    a.label("sl_x2"); E(pop_list, [3, 4, 5, 6, 7], pc=True)

    # ---- c_soload (the end of the stock's «apply session»): either mode off, nothing restored
    a.label("c_soload")
    E(raw, pushw([0, 1, 2, 3, 12], lr=True))
    E(bl, "c_sost"); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 4); E(strb_imm, 1, 0, 6); E(strb_imm, 1, 0, 7)
    E(raw, popw([0, 1, 2, 3, 12], lr=True)); E(b_w, prev["load"])
    return a.assemble()


def install2(img, report, base_addr):
    """After dspz (dspz.add): v2 in front of what v1 chained to; v1's code stays, unreachable."""
    import ct_fw
    import mpatch as MP
    import persist19 as P19
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    v1 = {k: int(v, 16) for k, v in report["mixsolo"]["labels"].items()}
    p1 = {k: int(v, 16) for k, v in report["mixsolo"]["prev"].items()}
    assert u(Q.MIX_VT) == v1["c_sopad"] | 1, "the Mixer's slot 0: v1 is not the head"
    L = dict(c_shift=int(report["sc15"]["labels"]["c_shift"], 16), c_gact=int(report["sc17"]["labels"]["c_gact"], 16))
    prev = dict(pad=p1["pad"], ledtask=p1["ledtask"], load=MP.bw_target(img, P19.LOAD_END, BASE))
    code, labels = arm_code2(base_addr, L, prev)
    img += code
    while len(img) % 4:
        img += bytes([0xFF])
    struct.pack_into("<I", img, Q.MIX_VT - BASE, labels["c_sopad2"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, v1["c_soled"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_soled2"])
    img[P19.LOAD_END - BASE:P19.LOAD_END - BASE + 4] = b_w(P19.LOAD_END, labels["c_soload"])
    return labels, code, prev


class V2:
    """dspz.add takes a module: install = install2."""
    install = staticmethod(install2)
