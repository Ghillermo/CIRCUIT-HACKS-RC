"""SC48 / Beta 3.37 (the user, 2026-10-27: «only when a cue listen is active, synth patch selection goes to the Cue Channel only.  Sample patch
with shift (silent selection) now goes to the Cue»; his choices: «Track to cue while previewing», «Do both for synth patch selection»): in the
cue mode (cue.py: the left output = the main mix, the right = the cue) the previews of the Preset views are heard in the cue only.

The stock's previews:
  * the synths' Preset view (0x0804D242, slot 0 of 0x0805AC9C; Synth 1 / 2 = 0x20042980 / 0x20042A34): a chosen patch schedules its preview
    note (0x0803C432(4, 0, 10, 0x0804D549, view) at 0x0804D2D8) unless recording or [view + 0x1C] p0 (Shift: the silent selection, read with the
    getter at 0x0804D2BE);
  * a drum's note-on of the Preset view (0x0804E0BA(view, pad, velocity)): nothing while [view + 0x1C] p0 (Shift, read at 0x0804E0C6).
Ours (only in the cue mode):
  * the synths' Shift read of the preview (0x0804D2BE) -> "no Shift" (a zero byte): the normal press and the Shift press (on stock the silent
    selection) both preview; the preview's scheduling (the bl at 0x0804D2D8) sets the synth's bit first;
  * a drum's Shift read, for the four drum Preset views only ([[ctrl + 0x2C] + 0x8C + 4 d]): with Shift held -> "no Shift" (the silent selection
    previews) and the drum's bit set; a normal press as always (the main);
  * a bit set = cue.c_cqg routes that track to the cue only (L 0, R its level, no sends; cue.use_preview), its groups marked (cue.c_cqdirty);
  * live playing stays on the main (the user: «make sure drumpads can still be played live»): the preview's own hit is let through (a byte of
    pending drums), and any later hit of that drum (its pads, MIDI, the pattern) at the drums' funnel (0x08049826, stpair's c_sttrig after us; the
    DSP semaphore held: no MARK_DIRTY) clears its bit first and flushes its group (0x080214D0: the level / pan through c_cqg again) and marks its
    sends (0x08021FDC): the new hit cuts the preview (a drum plays one sample at a time) and sounds on the main;
  * the pad let go (slot 1 of both Preset views): the bits cleared CLEAR_MS later from the LED task (the preview's tail), the groups marked again;
    the cue mode left: cleared at once.  While a track previews, its pattern is heard in the cue only too (one mixer strip a track).
RAM: cue.PVR (modmx.MXR + 0x1AB0, 12 B: + 0 "CQP1", + 4 the bits (Synth 1 / 2 = 0 / 1, Drum d = 4 + d), + 5 the drums whose preview hit
is still to come (bit d), + 8 the time to clear, 0 = none).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, b, b_cond, b_w, bl, bics_reg, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, lsls_imm, mov_reg, movs_imm, movt, movw,  # noqa: E402
                   orrs_reg, pop_list, push_list, raw, str_imm, strb_imm, subs_reg, tst_reg)
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import cue as CQ  # noqa: E402
import vcf21 as V  # noqa: E402

PARAM_GET, TIMER = 0x0803542C, 0x0803C432
SYN_SHIFT, SYN_SCHED, DRM_SHIFT = 0x0804D2BE, 0x0804D2D8, 0x0804E0C6
SYN_VT, DRM_VT = 0x0805AC9C, 0x0805ABBC
SYN_VIEWS = (0x20042980, 0x20042A34)
FUNNEL, FLUSH, MARK = 0x08049826, 0x080214D0, 0x08021FDC
MGR = 0x20040B10
CLEAR_MS = 800


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def now(rd): imm32(rd, V.HAL_TICK); E(ldr_imm, rd, rd, 0)
    RET = h(0x4770)
    a.label("cp_zero"); E(raw, bytes(4))

    # ---- c_cpram() -> r0 = cue.PVR, set up the first time; clobbers r1, r2
    a.label("c_cpram")
    imm32(0, CQ.PVR); E(ldr_imm, 1, 0, 0); imm32(2, CQ.PVSIG); E(cmp_reg, 1, 2); E(b_cond, "cr_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0); E(str_imm, 1, 0, 4); E(str_imm, 1, 0, 8)
    a.label("cr_x"); E(raw, RET)

    # ---- c_cpset(r0 = track): its bit, no clear pending, its groups marked; clobbers r0-r3
    a.label("c_cpset")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(bl, "c_cpram"); E(movs_imm, 1, 1); E(raw, h(0x40A1)); E(ldrb_imm, 2, 0, 4); E(orrs_reg, 2, 1); E(strb_imm, 2, 0, 4)   # lsls r1, r4
    E(movs_imm, 1, 0); E(str_imm, 1, 0, 8)
    E(mov_reg, 0, 4); E(bl, L["c_cqdirty"])
    E(pop_list, [4], pc=True)

    # ---- c_cpsysh (the synths' Shift read: store, 0) -> r0 = the byte's address; in the cue mode a zero byte
    a.label("c_cpsysh")
    E(push_list, [0, 1], lr=True); E(bl, L["c_cqon"]); E(cmp_imm, 0, 0); E(b_cond, "ss_p", "eq")
    E(pop_list, [0, 1]); E(raw, h(0xF85D) + h(0xEB04)); imm32(0, base); E(raw, RET)            # ldr.w lr, [sp], #4: cp_zero
    a.label("ss_p"); E(pop_list, [0, 1]); E(raw, h(0xF85D) + h(0xEB04)); E(b_w, PARAM_GET)

    # ---- c_cpsyn (the bl of the synth preview's scheduling: 0x0803C432's arguments, r4 = the view): in the cue mode its synth to the cue first
    a.label("c_cpsyn")
    E(push_list, [0, 1, 2, 3, 4, 5], lr=True)
    E(bl, L["c_cqon"]); E(cmp_imm, 0, 0); E(b_cond, "sy_p", "eq")
    imm32(1, SYN_VIEWS[1]); E(movs_imm, 0, 1); E(cmp_reg, 4, 1); E(b_cond, "sy_t", "eq"); E(movs_imm, 0, 0)
    a.label("sy_t"); E(bl, "c_cpset")
    a.label("sy_p"); E(raw, popw([0, 1, 2, 3, 4, 5], lr=True)); E(b_w, TIMER)

    # ---- c_cpdrum(r0 = a view) -> r0 = its drum 0..3, or 4; clobbers r1, r2
    a.label("c_cpdrum")
    imm32(1, MGR); E(ldr_imm, 1, 1, 0x2C); E(adds_imm8, 1, 0x8C); E(movs_imm, 2, 0)
    a.label("cd_l"); E(raw, h(0xF851) + h(0x3022)); E(cmp_reg, 3, 0); E(b_cond, "cd_x", "eq")  # ldr.w r3, [r1, r2, lsl #2]
    E(adds_imm8, 2, 1); E(cmp_imm, 2, 4); E(b_cond, "cd_l", "lo")
    a.label("cd_x"); E(mov_reg, 0, 2); E(raw, RET)

    # ---- c_cpdrsh (the drum note-on's Shift read: store, 0; r4 = the view) -> r0 = the byte's address: a drum Preset view, the cue mode,
    #      Shift held = a zero byte and the drum to the cue
    a.label("c_cpdrsh")
    E(push_list, [5, 6], lr=True)
    E(bl, PARAM_GET); E(mov_reg, 5, 0)                                                          # r5 = the Shift byte's address
    E(ldrb_imm, 0, 5, 0); E(cmp_imm, 0, 0); E(b_cond, "ds_x", "eq")
    E(mov_reg, 0, 4); E(bl, "c_cpdrum"); E(cmp_imm, 0, 4); E(b_cond, "ds_x", "hs"); E(mov_reg, 6, 0)
    E(bl, L["c_cqon"]); E(cmp_imm, 0, 0); E(b_cond, "ds_x", "eq")
    E(mov_reg, 0, 6); E(adds_imm8, 0, 4); E(bl, "c_cpset")
    E(bl, "c_cpram"); E(movs_imm, 1, 1); E(raw, h(0x40B1)); E(ldrb_imm, 2, 0, 5); E(orrs_reg, 2, 1); E(strb_imm, 2, 0, 5)   # lsls r1, r6: its hit to come
    imm32(5, base)                                                                              # cp_zero: the note-on plays
    a.label("ds_x"); E(mov_reg, 0, 5); E(pop_list, [5, 6], pc=True)

    # ---- c_cptrig (the drums' funnel: r0 = drum, r1 = velocity; the DSP semaphore held): a hit of a previewing drum after its preview's own =
    #      back to the main first
    a.label("c_cptrig")
    E(push_list, [0, 1, 2, 3, 4, 5], lr=True)
    E(mov_reg, 4, 0); E(cmp_imm, 4, 3); E(b_cond, "tg_p", "hi")
    E(bl, "c_cpram"); E(mov_reg, 5, 0)
    E(movs_imm, 1, 1); E(raw, h(0x40A1)); E(ldrb_imm, 2, 5, 5); E(tst_reg, 2, 1); E(b_cond, "tg_n", "eq")   # lsls r1, r4
    E(bics_reg, 2, 1); E(strb_imm, 2, 5, 5); E(b, "tg_p")                                        # the preview's own hit
    a.label("tg_n"); E(lsls_imm, 1, 1, 4); E(ldrb_imm, 2, 5, 4); E(tst_reg, 2, 1); E(b_cond, "tg_p", "eq")
    E(bics_reg, 2, 1); E(strb_imm, 2, 5, 4)
    E(mov_reg, 0, 4); E(bl, FLUSH)
    E(mov_reg, 1, 4); E(adds_imm8, 1, 4); E(movs_imm, 0, 0x20); E(bl, MARK)
    E(mov_reg, 1, 4); E(adds_imm8, 1, 15); E(movs_imm, 0, 0x20); E(bl, MARK)
    a.label("tg_p"); E(raw, popw([0, 1, 2, 3, 4, 5], lr=True)); E(b_w, prev["trig"])

    # ---- c_cprel (slot 1 of the Preset views: view, pad): a preview going on = its clear after CLEAR_MS
    for nm, pv in (("c_cprels", "srel"), ("c_cpreld", "drel")):
        a.label(nm)
        E(push_list, [0, 1, 2, 3], lr=True)
        E(bl, "c_cpram"); E(ldrb_imm, 1, 0, 4); E(cmp_imm, 1, 0); E(b_cond, f"{nm}_p", "eq")
        E(mov_reg, 2, 0); now(1); E(movw, 3, CLEAR_MS); E(raw, h(0x18C9)); E(str_imm, 1, 2, 8)      # adds r1, r1, r3
        a.label(f"{nm}_p"); E(raw, popw([0, 1, 2, 3], lr=True)); E(b_w, prev[pv])

    # ---- c_cpled (the LED task calls: ctrl, frame): the chain; the time passed or the cue mode left: the bits cleared, the groups marked
    a.label("c_cpled")
    E(push_list, [3, 4, 5], lr=True)
    E(bl, prev["ledtask"])
    E(bl, "c_cpram"); E(mov_reg, 5, 0); E(ldrb_imm, 4, 5, 4); E(cmp_imm, 4, 0); E(b_cond, "cl_x", "eq")
    E(bl, L["c_cqon"]); E(cmp_imm, 0, 0); E(b_cond, "cl_c", "eq")
    E(ldr_imm, 1, 5, 8); E(cmp_imm, 1, 0); E(b_cond, "cl_x", "eq")
    now(0); E(subs_reg, 0, 0, 1); E(b_cond, "cl_x", "mi")
    a.label("cl_c"); E(movs_imm, 0, 0); E(strb_imm, 0, 5, 4); E(str_imm, 0, 5, 8)
    E(movs_imm, 5, 0)
    a.label("cl_l"); E(mov_reg, 0, 4); E(raw, h(0x40E8)); E(movs_imm, 1, 1); E(raw, h(0x4208)); E(b_cond, "cl_n", "eq")   # lsrs r0, r5; tst r0, r1
    E(mov_reg, 0, 5); E(bl, L["c_cqdirty"])
    a.label("cl_n"); E(adds_imm8, 5, 1); E(cmp_imm, 5, 8); E(b_cond, "cl_l", "lo")
    a.label("cl_x"); E(pop_list, [3, 4, 5], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the two Shift reads, the synth preview's scheduling, slot 1 of both Preset views, the LED task calls."""
    import ct_fw
    from thumb import bl as bl_enc
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    assert CQ.PREV, "cue.use_preview first"
    L = {k: lab("cue", k) for k in ("c_cqon", "c_cqdirty", "c_cqpv")}
    for at, tgt in ((SYN_SHIFT, PARAM_GET), (SYN_SCHED, TIMER), (DRM_SHIFT, PARAM_GET)):
        assert bytes(img[at - BASE:at - BASE + 4]) == bl_enc(at, tgt), hex(at)
    import mpatch as MP
    prev = dict(trig=MP.bw_target(img, FUNNEL, BASE), srel=u(SYN_VT + 4) & ~1, drel=u(DRM_VT + 4) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    img[SYN_SHIFT - BASE:SYN_SHIFT - BASE + 4] = bl_enc(SYN_SHIFT, labels["c_cpsysh"])
    img[SYN_SCHED - BASE:SYN_SCHED - BASE + 4] = bl_enc(SYN_SCHED, labels["c_cpsyn"])
    img[DRM_SHIFT - BASE:DRM_SHIFT - BASE + 4] = bl_enc(DRM_SHIFT, labels["c_cpdrsh"])
    from thumb import b_w as bw_enc
    img[FUNNEL - BASE:FUNNEL - BASE + 4] = bw_enc(FUNNEL, labels["c_cptrig"])
    struct.pack_into("<I", img, SYN_VT + 4 - BASE, labels["c_cprels"] | 1)
    struct.pack_into("<I", img, DRM_VT + 4 - BASE, labels["c_cpreld"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_cpled"])
    return labels, code, prev
