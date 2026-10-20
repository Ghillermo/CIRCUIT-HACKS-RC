"""SC44.9 (the user, 2026-10-19: «Add a shortcut to "record instance" into the sequencers. This fills the automation rails with all the parameters
that differ from the init»; with him: «Hold record + step (solo se guardan valores que hayan cambiado)», more than the lanes hold or without a
lane: «Reasignar carriles»): Record held + a step pad of MIDI 1 / 2's track view (own engine on) = a snapshot of the engine into that step's lanes.

  * The parameters: the matrix's list (modmx's dcode: every code of the knob pages, 33); one differs when its value is not its default (vcf21's
    t_def, the value of Clear + knob).
  * The lanes (the track's row of page 4, vcf21.use_p4dest): a lane whose code differs keeps it; a differing code without a lane takes the first
    lane whose code does not differ (in lane order; the list's order decides who gets one when they run out), and that lane is cleared in the
    pattern first (its old values meant another parameter).  Then each lane whose code differs gets its value (c_vtou: 0..127) on the step's 6
    micro steps, written into the pattern as the step-drummer writes its pairs (c_sdpat + 0x3A8 + 192 lane + 6 step).
  * The step pads: the track view's steps are objects of class 0x0805ADB4 (0x20041EB0 + 0x170 t, t = Synth 1, Synth 2, MIDI 1, MIDI 2), slot 0
    (obj, pad 0..15, velocity), the step = pad + 16 when [obj + 0xC4] p0 (the 1-16 / 17-32 page); the press and its release are swallowed.
  * Record (button 16) is not one of the stock's held buttons: heads of the button press 0x08033320 and release 0x0803381A keep a flag (not with
    Shift); the press arms / disarms recording as always (the transport's p1, saved first) and, when a snapshot was taken, the release puts p1
    back: Record held for a snapshot leaves the recording state as it was.
RAM: modmx.MXR + 0x180: + 0 Record held, + 1 a snapshot taken, + 2 p1 at the press, + 3 the swallowed pad + 1."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldrb_imm, ldrb_reg, lsls_imm, lsrs_imm, mov_reg,  # noqa: E402
                   movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, strb_imm, strb_reg, subs_imm8, tst_reg)
import vcf21 as V  # noqa: E402
import mpatch as MP  # noqa: E402
import packio as PK  # noqa: E402
import modmx as MX  # noqa: E402

RAM = MX.MXR + 0x180
BTN, BTN_REL, REC_ID = 0x08033320, 0x0803381A, 16
STEP_VT, STEP_OBJ0, STEP_SZ, STEP_PAGE = 0x0805ADB4, 0x20041EB0, 0x170, 0xC4
TRANSPORT, PARAM_WPTR, COMMIT = 0x20011034, 0x080354FA, 0x080353C0
LANES, LANE_BYTES = 0x3A8, 192
INV = V.INV


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def ldrsb_reg(rt, rn, rm): return h(0x5600 | rm << 6 | rn << 3 | rt)


def arm_code(base, L, prev, nd):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_r{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    def p1(rd):                                                                    # rd = the transport's p1 byte (r0-r3 clobbered)
        imm32(0, TRANSPORT); E(movs_imm, 1, 1); E(bl, PK.PARAM_GET); E(ldrb_imm, rd, 0, 0)

    # ---- c_ripress (the head of the button press: ctrl, id): Record without Shift = held, no snapshot yet, p1 kept
    a.label("c_ripress")
    E(push_list, [0, 1, 2, 3, 4], lr=True)
    E(cmp_imm, 1, REC_ID); E(b_cond, "rp_x", "ne")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "rp_x", "ne")
    p1(4); imm32(0, RAM); E(strb_imm, 4, 0, 2); E(movs_imm, 1, 1); E(strb_imm, 1, 0, 0); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 1)
    a.label("rp_x"); E(raw, popw([0, 1, 2, 3, 4], lr=True)); E(b_w, prev["press"])

    # ---- c_rirel (the head of the button release: ctrl, id): Record let go; after a snapshot p1 back to what it was before the press
    a.label("c_rirel")
    E(push_list, [0, 1, 2, 3, 4], lr=True)
    E(cmp_imm, 1, REC_ID); E(b_cond, "rr_x", "ne")
    imm32(4, RAM); E(ldrb_imm, 0, 4, 0); E(movs_imm, 1, 0); E(strb_imm, 1, 4, 0); E(cmp_imm, 0, 0); E(b_cond, "rr_x", "eq")
    E(ldrb_imm, 0, 4, 1); E(cmp_imm, 0, 0); E(b_cond, "rr_x", "eq"); E(movs_imm, 1, 0); E(strb_imm, 1, 4, 1)
    imm32(0, TRANSPORT); E(movs_imm, 1, 1); E(bl, PARAM_WPTR); E(ldrb_imm, 1, 4, 2); E(strb_imm, 1, 0, 0)
    imm32(0, TRANSPORT); E(bl, COMMIT)
    a.label("rr_x"); E(raw, popw([0, 1, 2, 3, 4], lr=True)); E(b_w, prev["release"])

    # ---- c_ristrk(r0 = step object) -> r0 = MIDI 1 / 2 = 0 / 1, else 0xFF
    a.label("c_ristrk")
    imm32(1, STEP_OBJ0 + 2 * STEP_SZ); E(cmp_reg, 0, 1); E(b_cond, "st_0", "eq")
    imm32(1, STEP_OBJ0 + 3 * STEP_SZ); E(cmp_reg, 0, 1); E(b_cond, "st_1", "eq")
    E(movs_imm, 0, 0xFF); E(raw, h(0x4770))
    a.label("st_0"); E(movs_imm, 0, 0); E(raw, h(0x4770))
    a.label("st_1"); E(movs_imm, 0, 1); E(raw, h(0x4770))

    # ---- c_ripad (slot 0 of the step objects: obj, pad, velocity): Record held + a step of MIDI 1 / 2 with the engine on = the snapshot
    a.label("c_ripad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    imm32(3, RAM); E(ldrb_imm, 3, 3, 0); E(cmp_imm, 3, 0); bc("rd_prev", "eq")
    E(cmp_imm, 1, 15); bc("rd_prev", "hi"); E(mov_reg, 5, 1); E(mov_reg, 6, 0)
    E(bl, "c_ristrk"); E(cmp_imm, 0, 1); bc("rd_prev", "hi"); E(mov_reg, 4, 0)
    E(bl, L["c_von"]); E(cmp_imm, 0, 0); bc("rd_prev", "eq")
    E(raw, h(0xF8D6) + h(0 << 12 | STEP_PAGE))                                     # ldr.w r0, [r6, #0xC4]: the page
    E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "rd_s", "eq"); E(adds_imm8, 5, 16)
    a.label("rd_s")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_riinst")
    imm32(0, RAM); E(movs_imm, 1, 1); E(strb_imm, 1, 0, 1)
    E(raw, h(0x9901))                                                               # ldr r1, [sp, #4]: the pad
    E(adds_imm8, 1, 1); E(strb_imm, 1, 0, 3)
    E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("rd_prev"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["spad"])

    # ---- c_rirelp (slot 1 of the step objects: obj, pad): the release of a swallowed press swallowed too
    a.label("c_rirelp")
    imm32(3, RAM); E(ldrb_imm, 2, 3, 3); E(cmp_imm, 2, 0); E(b_cond, "rl_prev", "eq")
    E(subs_imm8, 2, 1); E(cmp_reg, 2, 1); E(b_cond, "rl_prev", "ne")
    E(movs_imm, 2, 0); E(strb_imm, 2, 3, 3); E(raw, h(0x4770))
    a.label("rl_prev"); E(b_w, prev["srel"])

    # ---- c_ridiff(r0 = track, r1 = code) -> r0 = 1 when the value is not the default; clobbers r1-r3
    a.label("c_ridiff")
    E(push_list, [4], lr=True); E(mov_reg, 4, 1)
    E(bl, L["c_vvaddr"]); E(movs_imm, 1, 0); E(raw, ldrsb_reg(0, 0, 1))
    imm32(2, L["t_def"]); E(raw, ldrsb_reg(1, 2, 4))
    E(cmp_reg, 0, 1); E(b_cond, "df_0", "eq"); E(movs_imm, 0, 1); E(pop_list, [4], pc=True)
    a.label("df_0"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_rilane(r0 = track, r1 = lane) -> r0 = the lane's 192 bytes in the track's pattern; clobbers r1-r3
    a.label("c_rilane")
    E(push_list, [4], lr=True); E(mov_reg, 4, 1)
    E(bl, L["c_sdpat"]); E(movs_imm, 1, LANE_BYTES); E(muls, 1, 4); E(adds_reg, 0, 0, 1)
    E(movw, 1, LANES); E(adds_reg, 0, 0, 1); E(pop_list, [4], pc=True)

    # ---- c_riinst(r0 = track, r1 = step): the snapshot
    a.label("c_riinst")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, L["c_vrow"]); E(mov_reg, 6, 0)                                            # r6 = the row
    E(movs_imm, 7, 0)                                                               # r7 = the lanes to write (a bit each)
    # the lanes whose code differs keep it
    for k in range(8):
        E(ldrb_imm, 1, 6, k); E(mov_reg, 0, 4); E(bl, "c_ridiff"); E(cmp_imm, 0, 0); E(b_cond, f"ik_{k}", "eq")
        E(movs_imm, 0, 1 << k); E(orrs_reg, 7, 0)
        a.label(f"ik_{k}")
    # every other differing code: the first free lane, cleared
    E(push_list, [5]); E(movs_imm, 5, 0)                                            # r5 = the index in the list
    a.label("in_l")
    imm32(0, L["t_dcode"]); E(ldrb_reg, 1, 0, 5); E(push_list, [1])
    E(mov_reg, 0, 4); E(bl, "c_ridiff"); E(pop_list, [1]); E(cmp_imm, 0, 0); bc("in_n", "eq")
    E(push_list, [1]); E(mov_reg, 0, 4); E(bl, L["c_vlane"]); E(pop_list, [1]); E(cmp_imm, 0, 0xFF); bc("in_n", "ne")
    E(movs_imm, 2, 0)                                                               # r2 = the lane tried
    a.label("in_f"); E(movs_imm, 3, 1)
    E(raw, h(0x4093))                                                               # lsls r3, r2
    E(tst_reg, 7, 3); E(b_cond, "in_g", "eq")
    E(adds_imm8, 2, 1); E(cmp_imm, 2, 8); E(b_cond, "in_f", "lo"); E(b, "in_x")       # no free lane: done
    a.label("in_g")
    E(orrs_reg, 7, 3); E(strb_reg, 1, 6, 2)
    E(mov_reg, 0, 4); E(mov_reg, 1, 2); E(bl, "c_rilane"); E(movs_imm, 1, LANE_BYTES); E(movs_imm, 2, 0xFF); E(bl, PK.MEMSET)
    a.label("in_n"); E(adds_imm8, 5, 1); E(cmp_imm, 5, nd); bc("in_l", "lo")
    a.label("in_x"); E(pop_list, [5])
    # the values
    for k in range(8):
        E(movs_imm, 0, 1 << k); E(tst_reg, 7, 0); bc(f"iw_{k}", "eq")
        E(mov_reg, 0, 4); E(ldrb_imm, 1, 6, k); E(bl, L["c_vvaddr"]); E(movs_imm, 1, 0); E(raw, ldrsb_reg(1, 0, 1))
        E(ldrb_imm, 0, 6, k); E(bl, L["c_vtou"]); E(push_list, [0])
        E(mov_reg, 0, 4); E(movs_imm, 1, k); E(bl, "c_rilane"); E(movs_imm, 1, 6); E(muls, 1, 5); E(adds_reg, 0, 0, 1); E(pop_list, [1])
        for i in range(6): E(strb_imm, 1, 0, i)
        a.label(f"iw_{k}")
    E(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the heads of the button press / release, slots 0 / 1 of the step objects' class."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("vcf20", k) for k in ("c_vrow", "c_vlane", "c_vvaddr", "c_vtou", "c_sdpat", "c_von", "t_def")}
    L["c_shift"] = lab("sc15", "c_shift")
    L["t_dcode"] = lab("modmx", "t_dcode")
    nd = int(report["modmx"]["prev"]["pmax"], 16) // MX.ZONE
    prev = dict(press=MP.bw_target(img, BTN, BASE), release=MP.bw_target(img, BTN_REL, BASE), spad=u(STEP_VT) & ~1, srel=u(STEP_VT + 4) & ~1)
    code, labels = arm_code(base_addr, L, prev, nd)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000 or base_addr < 0x08018800          # in the hole: hole.add moves it back
    img[BTN - BASE:BTN - BASE + 4] = b_w(BTN, labels["c_ripress"])
    img[BTN_REL - BASE:BTN_REL - BASE + 4] = b_w(BTN_REL, labels["c_rirel"])
    struct.pack_into("<I", img, STEP_VT - BASE, labels["c_ripad"] | 1)
    struct.pack_into("<I", img, STEP_VT + 4 - BASE, labels["c_rirelp"] | 1)
    prev.update(nd=nd)
    return labels, code, prev
