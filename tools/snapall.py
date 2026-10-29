"""SC48.9 (the user, 2026-10-28: «how do we save all changed parameters into automation step?», «is it the same for stock synt/drums?» -> «yes»;
«mixer and fx are already stored in scenes, keep them, don't add or subtract them»): Record held + a step = the snapshot (recinst's, MIDI 1 / 2's
own synth) on Synth 1 / 2 and the drums too; knobs only, the Mixer / FX lanes untouched.

  * Synth 1 / 2: their track view's step pads are recinst's objects (class 0x0805ADB4, 0x20041EB0 + 0x170 t, t = 0 / 1): a head of slot 0 in
    front of recinst's.  Each of the 8 macros whose position (0x08036192(s, 174 + 17 m)) is not the one saved in the patch the synth plays (the
    pack's record read again, as Clear + Synth does: mpatch.c_mpr under the shared buffer's lock; byte 30 + parameter) goes into its lane m on
    that step's 6 micro steps (the pattern of the track that is selected / plays: vcf21.c_sdpat(2 + s); lane m = + 0x3A8 + 192 m + 6 step).
  * The drums: a drum's Note view (sub-mode 37 + 8 d); its pads come through the track views' container (0x20040DB8, slot 0): a head.  Pads 1-16
    = steps 1-16 or 17-32 by the page of the drum views' store ([0x20043094 + 0x58] parameter 2).  Each of the 4 stock knobs (pitch, decay,
    distortion, EQ: the drum's macro handler store [h + 0xC] parameters 0..3) not at its default (DRUM_DEF, Clear + knob right) goes into its
    lane 0..3 of the drum's pattern (drumarp.c_dapat; + 0xA8 + 192 k + 6 step).
  * recinst's state (its RAM, c_rist): + 0 Record held (no Shift), + 1 a snapshot taken (Record's state back on its release), + 3 the swallowed
    pad + 1 (recinst's slot 1 swallows a step object's release); a drum pad's release (the container's slot 1) is swallowed by + 3 = pad + 0x41.
Not in the hole (full): at the end of the image."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrb_reg, lsls_imm, lsrs_imm, mov_reg,  # noqa: E402
                   movs_imm, movt, movw, muls, pop_list, push_list, raw, strb_imm, subs_imm8, tst_reg)
import packio as PK  # noqa: E402
import recinst as RI  # noqa: E402

STEP_VT, STEP_OBJ0, STEP_SZ, STEP_PAGE = RI.STEP_VT, RI.STEP_OBJ0, RI.STEP_SZ, RI.STEP_PAGE
CONT, CONT_VT, SYN_VT = 0x20040DB8, 0x0805A62C, 0x0805AC9C   # the track views' container; Synth s's Preset view = [CONT + 0x78 + 4 s]
GETTER, MACRO_P0, MACRO_STEP, PATCH_OFF = 0x08036192, 174, 17, 30
MGR, S_CUR, DRUM_NOTE0 = 0x20040B10, 0x152, 37
DGRID = 0x20043094
DRUM_DEF = (64, 127, 0, 64)                       # the stock drum knobs' defaults: pitch, decay, distortion, EQ (Clear + knob right)
LANES, DLANES, LANE_BYTES, DPAT_SZ = 0x3A8, 0xA8, 192, 0x6A8


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    RET = h(0x4770)
    E(raw, bytes(DRUM_DEF)); t_def = base

    # ---- c_sastore(r0 = lane bytes of the step, r1 = value): the 6 micro steps; clobbers r2
    a.label("c_sastore")
    E(movs_imm, 2, 6)
    a.label("ss_l"); E(subs_imm8, 2, 1); E(raw, h(0x5481)); E(b_cond, "ss_l", "ne"); E(raw, RET)       # strb r1, [r0, r2]

    # ---- c_saheld() -> r0 = 1 when recinst's Record is held; clobbers r1-r3
    a.label("c_saheld")
    E(push_list, [4], lr=True); E(bl, L["c_rist"]); E(ldrb_imm, 0, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_sadone(r0 = the swallowed pad mark): recinst's «a snapshot taken» and the mark; clobbers r1, r2
    a.label("c_sadone")
    imm32(1, RI.RAM); E(movs_imm, 2, 1); E(strb_imm, 2, 1, 1); E(strb_imm, 0, 1, 3); E(raw, RET)

    # ---- c_sapad (slot 0 of the step objects: obj, pad, velocity): Record held + a step of Synth 1 / 2 = its macros
    a.label("c_sapad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 6, 0); E(mov_reg, 5, 1)
    E(cmp_imm, 5, 15); E(b_cond, "sp_prev", "hi")
    imm32(1, STEP_OBJ0); E(movs_imm, 4, 0); E(cmp_reg, 6, 1); E(b_cond, "sp_s", "eq")
    imm32(1, STEP_OBJ0 + STEP_SZ); E(movs_imm, 4, 1); E(cmp_reg, 6, 1); E(b_cond, "sp_prev", "ne")
    a.label("sp_s")
    E(bl, "c_saheld"); E(cmp_imm, 0, 0); E(b_cond, "sp_prev", "eq")
    E(raw, h(0xF8D6) + h(0 << 12 | STEP_PAGE))                                     # ldr.w r0, [r6, #0xC4]: the page
    E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "sp_q", "eq"); E(adds_imm8, 5, 16)
    a.label("sp_q")
    # the patch the synth plays, read again from the pack
    imm32(0, CONT + 0x78); E(lsls_imm, 1, 4, 2); E(adds_reg, 0, 0, 1); E(ldr_imm, 6, 0, 0)          # r6 = its Preset view
    E(ldr_imm, 0, 6, 0); imm32(1, SYN_VT); E(cmp_reg, 0, 1); E(b_cond, "sp_d", "ne")
    E(ldr_imm, 0, 6, 0x14); E(movs_imm, 1, 10); E(bl, PK.PARAM_GET); E(ldrb_imm, 6, 0, 0)            # r6 = the patch
    E(cmp_imm, 6, 127); E(b_cond, "sp_d", "hi")
    E(movs_imm, 0, 5); E(bl, PK.BUF_LOCK)
    E(lsrs_imm, 0, 6, 3); E(lsls_imm, 1, 6, 29); E(lsrs_imm, 1, 1, 20); imm32(2, PK.BUF); imm32(3, PK.PATCH_SZ); E(bl, L["c_mpr"])
    E(cmp_imm, 0, 0); E(b_cond, "sp_u", "ne")
    E(movs_imm, 7, 0)
    a.label("sp_m")
    E(movs_imm, 1, MACRO_STEP); E(muls, 1, 7); E(adds_imm8, 1, MACRO_P0); E(mov_reg, 0, 4); E(bl, GETTER)
    E(cmp_imm, 0, 127); E(b_cond, "sp_c", "ls"); E(movs_imm, 0, 127)
    a.label("sp_c"); E(mov_reg, 6, 0)                                                                  # r6 = its position now
    E(movs_imm, 1, MACRO_STEP); E(muls, 1, 7); E(adds_imm8, 1, MACRO_P0 + PATCH_OFF); imm32(2, PK.BUF); E(ldrb_reg, 2, 2, 1)
    E(cmp_reg, 6, 2); E(b_cond, "sp_n", "eq")
    E(mov_reg, 0, 4); E(adds_imm8, 0, 2); E(bl, L["c_sdpat"])
    E(movs_imm, 1, LANE_BYTES); E(muls, 1, 7); E(adds_reg, 0, 0, 1); E(movw, 1, LANES); E(adds_reg, 0, 0, 1)
    E(movs_imm, 1, 6); E(muls, 1, 5); E(adds_reg, 0, 0, 1); E(mov_reg, 1, 6); E(bl, "c_sastore")
    a.label("sp_n"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 8); E(b_cond, "sp_m", "lo")
    a.label("sp_u"); E(bl, PK.BUF_UNLOCK)
    a.label("sp_d"); E(raw, h(0x9801)); E(adds_imm8, 0, 1); E(bl, "c_sadone")                        # ldr r0, [sp, #4]: the pad + 1
    E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("sp_prev"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["spad"])

    # ---- c_sacpad (slot 0 of the track views' container: cont, pad, velocity): Record held + a step of a drum's Note view = its stock knobs
    a.label("c_sacpad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(cmp_imm, 5, 15); E(b_cond, "cp_prev", "hi")
    imm32(0, MGR); E(ldr_imm, 1, 0, 0x6C); E(ldr_imm, 2, 0, 0x2C); E(cmp_reg, 1, 2); E(b_cond, "cp_prev", "ne")
    E(raw, h(0xF890) + h(1 << 12 | S_CUR)); E(subs_imm8, 1, DRUM_NOTE0); E(cmp_imm, 1, 31); E(b_cond, "cp_prev", "hi")   # ldrb.w r1, [r0, #S_CUR]
    E(movs_imm, 2, 7); E(tst_reg, 1, 2); E(b_cond, "cp_prev", "ne"); E(lsrs_imm, 4, 1, 3)                     # r4 = the drum
    E(bl, "c_saheld"); E(cmp_imm, 0, 0); E(b_cond, "cp_prev", "eq")
    imm32(0, DGRID); E(ldr_imm, 0, 0, 0x58); E(movs_imm, 1, 2); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(cmp_imm, 0, 0); E(b_cond, "cp_s", "eq"); E(adds_imm8, 5, 16)
    a.label("cp_s")
    E(mov_reg, 0, 4); E(bl, L["c_mh"]); E(cmp_imm, 0, 0); E(b_cond, "cp_d", "eq"); E(ldr_imm, 6, 0, 0xC)     # r6 = its knobs' store
    E(mov_reg, 0, 4); E(bl, L["c_dapat"]); E(mov_reg, 7, 0)
    imm32(0, L["DP0"]); E(movs_imm, 1, L["DP_SZ"]); E(muls, 1, 4); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0x48)
    E(movw, 1, DPAT_SZ); E(muls, 1, 7); E(adds_reg, 7, 0, 1)
    E(movs_imm, 0, 6); E(muls, 0, 5); E(adds_reg, 7, 7, 0); E(adds_imm8, 7, DLANES)                         # r7 = lane 0 of the step
    E(movs_imm, 4, 0)                                                                                   # r4 = the knob
    a.label("cp_k")
    E(mov_reg, 0, 6); E(mov_reg, 1, 4); E(bl, PK.PARAM_GET); E(ldrb_imm, 1, 0, 0)
    imm32(2, t_def); E(ldrb_reg, 2, 2, 4); E(cmp_reg, 1, 2); E(b_cond, "cp_n", "eq")
    E(mov_reg, 0, 7); E(bl, "c_sastore")
    a.label("cp_n"); E(adds_imm8, 7, LANE_BYTES); E(adds_imm8, 4, 1); E(cmp_imm, 4, 4); E(b_cond, "cp_k", "lo")
    a.label("cp_d"); E(raw, h(0x9801)); E(adds_imm8, 0, 0x41); E(bl, "c_sadone")                       # the pad + 0x41: the container's
    E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("cp_prev"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["cpad"])

    # ---- c_sacrel (slot 1 of the container: cont, pad): the release of a swallowed drum step swallowed too
    a.label("c_sacrel")
    imm32(3, RI.RAM); E(ldrb_imm, 2, 3, 3); E(subs_imm8, 2, 0x41); E(cmp_reg, 2, 1); E(b_cond, "cr_prev", "ne")
    E(movs_imm, 2, 0); E(strb_imm, 2, 3, 3); E(raw, RET)
    a.label("cr_prev"); E(b_w, prev["crel"])
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr; heads of slot 0 of the step objects' class and slots 0 / 1 of the track views' container."""
    import ct_fw
    import drumarp as DA
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_rist=lab("recinst", "c_rist"), c_sdpat=lab("vcf20", "c_sdpat"), c_mpr=lab("mpatch", "c_mpr"), c_mh=lab("sc18", "c_mh"),
             c_dapat=lab("drumarp", "c_dapat"), DP0=DA.DP0, DP_SZ=DA.DP_SZ)
    prev = dict(spad=u(STEP_VT) & ~1, cpad=u(CONT_VT) & ~1, crel=u(CONT_VT + 4) & ~1)
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000, f"snapall: the image is full ({len(img):#x})"
    struct.pack_into("<I", img, STEP_VT - BASE, labels["c_sapad"] | 1)
    struct.pack_into("<I", img, CONT_VT - BASE, labels["c_sacpad"] | 1)
    struct.pack_into("<I", img, CONT_VT + 4 - BASE, labels["c_sacrel"] | 1)
    return labels, code, prev
