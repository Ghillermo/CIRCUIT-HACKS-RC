"""Alpha 7.42 (the user, 2026-11-24: «then keep working on macros2»; chosen earlier: Macros 2 gets automation lanes «Like the macros», «Two:
start and middle»): Synth 1 / 2's eight Macros 2 knobs (novasec.use_v2: each set straight to one Nova parameter) recorded and played like the
stock macros' automation.

  * Record armed and the transport running: a Macros 2 knob turned = its value into the playing pattern's step, the half of the step it falls in
    (the first half or the second: 2 values a step, start and middle); played back at micro steps 0 and 3 of each step (the stock's setter, as a
    received NRPN: novasec / macroed's c_mcset); a value already there is not sent again; the knob just turned by hand (256 ms) is not played over.
  * A step held (the macro handler's [handler + 0x3C] p0, the stock's own test) + a Macros 2 knob = its value into the held steps of the edited
    pattern (pads 1-16 held, + 16 on the 17-32 page), both halves; the parameter moves too (novasec has already set it).
  * Clear + a Macros 2 knob (novasec.use_v9's kn_m2c; before: nothing): turned left = that knob's lane cleared in the edited pattern; right = the
    parameter back to the patch's value (the patch in the session record, read with the stock's row getter 0x0803BD00).
  * The pattern copy / clear of the stock (the dispatcher's paste and clear) and the Nudge (playmode / xlanes) take the lanes along.
  * Nothing plays while a project's lanes are not in place (after a load, until the LED task has read them).

Where (8 KB: 2 synths x 8 patterns x 8 knobs x 32 steps x 2 values; 0xFF = none):
  * the ITCM 0x2000-0x3FFF, block b = 8 synth + pattern at 0x2000 + 512 b, knob k at + 64 k, step s / half h at + 2 s + h.  The ITCM is dspz's
    window while the DSP programs are sent: with factcut that is the power-up only (0x0801F568).  The backup SRAM holds the state (M2): a head of
    the bl to main (0x0805B9B0) zeroes it at every reset (it survives a warm one), a head of the power-up send (0x0801F568) fills the 8 KB with 0xFF
    afterwards and says the ITCM is ours (+ 0); until then nothing touches it (the LED task waits).  Only the CPU reads the ITCM (DMA does not reach
    it): the card's transfers go through the shared 4 KB buffer.
  * on the card, after the scene chains (scrules: 186 812 + 580 = 187 392): 16 B ("M2L1", version 1, the blocks' bitmap, the length, the checksum
    of Synth 1 / 2's 16 patterns in the record) + the 8 KB.  Written by the LED task after a save (blocks with data, or the file already that
    long; never pack 0), read after a load when the checksum matches (else no lanes).  A Components write of the session drops it.
State M2 (0x40024100): + 0 (unused), + 1 flags (save, load, new), + 2 the lanes in place, + 3 tries, + 4 / + 5 the slot / pack to save,
+ 6 the blocks with data (u16), + 8 / + 12 the checksum at the save / load, + 16 the time of the last hand-recorded value, + 20 its knob
(0x80 | synth << 3 | knob), + 24 "M2S1" = the ITCM ours.  The stock uses the backup SRAM as its USB drive buffer (Easy Start): a state
overwritten there loses the signature (no lanes until the next power-up) and a save is written only for a pack 1..31 and a slot 0..63."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, add_sp_imm, ands_reg, b, b_cond, b_w, bics_reg, bl, cbz, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp,  # noqa: E402
                   ldrb_imm, ldrh_imm, lsls_imm, lsls_reg, lsrs_reg, mov_reg, movs_imm, movt, movw, orrs_reg, pop_list, push_list, raw, str_imm,
                   str_sp, strb_imm, strh_imm, sub_sp_imm, subs_imm8, subs_reg, tst_reg)
from build_sc14 import udiv  # noqa: E402
import packio as PK  # noqa: E402
import persist19 as P19  # noqa: E402
import mpatch as MP  # noqa: E402
import fxdiag as FD  # noqa: E402
import patchain as PC  # noqa: E402
import xlanes as XL  # noqa: E402
import scrules as SR  # noqa: E402
import recinst as RI  # noqa: E402
import novasec as N  # noqa: E402

INV = {"eq": "ne", "ne": "eq", "hs": "lo", "lo": "hs", "hi": "ls", "ls": "hi", "mi": "pl", "pl": "mi"}
M2 = 0x40024100                                # the backup SRAM (novasec: 0x40024000..)
O_RDY, O_FL, O_VAL, O_TRY, O_SIDX, O_SPK, O_MAP, O_SSUM, O_LSUM, O_RT, O_RK, O_SIG = 0, 1, 2, 3, 4, 5, 6, 8, 12, 16, 20, 24
ST_LEN = 28
SSIG = 0x3153_324D                             # "M2S1" at + 24: the ITCM ours (the power-up head writes it, the reset head zeroes it)
IT0, BLK, NBLK = 0x2000, 512, 16
DATA = BLK * NBLK                              # 8 192 B
HDR = 16
SECT = HDR + DATA
OFF = SR.OFF + SR.SECT                         # 187 392: after the scene chains
MAGIC = 0x314C_324D                            # "M2L1"
CH1 = 4096 - HDR                               # the first transfer: the header + 4 080 B
F_SAVE, F_LOAD, F_NEW = 1, 2, 4
TRIES = 8
RST_AT, BOOT_AT = 0x0805B9B0, 0x0801F568       # the bl to main; the power-up DSP send (0x08029260(0))
SYN_AREA, PSIZE = N.SYN_AREA, N.PSIZE          # Synth s's pattern p at record + SYN_AREA + PSIZE (8 s + p)
NSUMW = 16 * PSIZE // 4
REC_SYN, SYN_SZ = 0x26D14, 0x154               # Synth s's patch in the record (autorel), in the bank's format
ROWTAB, ROWGET = 0x0805454C, 0x0803BD00        # the parameter table (8 B rows: u16 byte, kind, 3 range, MIDI type, number); its getter (row, &&patch)
PAT_OBJ, PAT_SZ, PAT_N = XL.PAT_OBJ, XL.PAT_SZ, XL.PAT_N
PLAYER0, PLAYER_SZ, PLAYER_VT = XL.PLAYER0, XL.PLAYER_SZ, XL.PLAYER_VT
ENG, TICKS_TAB, REC_ON = XL.ENG, XL.TICKS_TAB, XL.REC_ON
STEP_OBJ0, STEP_SZ, STEP_PAGE = RI.STEP_OBJ0, RI.STEP_SZ, RI.STEP_PAGE
MGR, HAL_TICK = N.MGR, N.HAL_TICK
HELD_STORE = 0x3C                              # the macro handler: [+ 0x3C] p0 = a step held (0x0804C07E)
RECENT = 255                                   # ms: a knob turned by hand is not played over
assert OFF == 187392 and DATA == 8192 and IT0 + DATA == 0x4000


HELPERS = ("c_m2ok", "c_m2adr", "c_m2bit", "c_m2trk", "c_m2ff", "c_m2cpy", "c_m2sum")


X2 = False                                       # Alpha 7.52 (use_x2)


def use_x2():
    """Alpha 7.52 (novasec.use_v12): the playback of a Macros 2 lane also sets the knob's second destination (novasec.c_nsx2)."""
    global X2
    X2 = True

def ldr_reg(rt, rn, rm): return h(0x5800 | rm << 6 | rn << 3 | rt)
def ldrb_reg(rt, rn, rm): return h(0x5C00 | rm << 6 | rn << 3 | rt)


def arm_code(base, L, prev, part="A"):
    """part A: the hooks (factcut's gap; L holds part H's labels); part H: the helpers, the players' slot 2, the knob's two calls (at the end of
    the image, appended first); part B: the LED task's work, the card (at the end of the image; L holds part H's labels)"""
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_m{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    def pget(p):                                    # r0 = a store -> r0 = byte p of its parameter
        E(movs_imm, 1, p); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    def it0(rd): E(movs_imm, rd, 1); E(lsls_imm, rd, rd, 13)

    if part == "A":
        # ---- c_m2rst (in place of the bl to main, 0x0805B9B0): the state zeroed (the ITCM not ours yet), then main
        a.label("c_m2rst")
        imm32(0, M2); E(movs_imm, 1, 0)
        for o in range(0, ST_LEN, 4): E(str_imm, 1, 0, o)
        E(b_w, prev["rst"])

        # ---- c_m2boot (in place of the bl 0x08029260 at 0x0801F568, the power-up DSP send): the send, then the 8 KB ours (0xFF)
        a.label("c_m2boot")
        E(push_list, [4], lr=True); E(bl, prev["boot"])
        it0(0); it0(1); E(bl, "c_m2ff")
        imm32(0, M2); imm32(1, SSIG); E(str_imm, 1, 0, O_SIG)
        E(pop_list, [4], pc=True)

    if part == "H":
        # ---- c_m2ff(r0 = destination, r1 = bytes, a multiple of 4): 0xFF; clobbers r0-r2
        a.label("c_m2ff")
        E(movs_imm, 2, 0); E(subs_imm8, 2, 1)
        a.label("ff_l"); E(str_imm, 2, 0, 0); E(adds_imm8, 0, 4); E(subs_imm8, 1, 4); E(b_cond, "ff_l", "ne"); E(raw, PC.BX_LR)

        # ---- c_m2cpy(r0 = destination, r1 = source, r2 = bytes, a multiple of 4); clobbers r0-r3
        a.label("c_m2cpy")
        a.label("cy_l"); E(ldr_imm, 3, 1, 0); E(str_imm, 3, 0, 0); E(adds_imm8, 0, 4); E(adds_imm8, 1, 4); E(subs_imm8, 2, 4)
        E(b_cond, "cy_l", "ne"); E(raw, PC.BX_LR)

        # ---- c_m2sum() -> r0 = Synth 1 / 2's 16 patterns in the record summed as words (0 without a record); clobbers r1-r3
        a.label("c_m2sum")
        imm32(1, P19.SESSION_OBJ + 0x14); E(ldr_imm, 1, 1, 0); E(movs_imm, 0, 0); E(cmp_imm, 1, 0); E(b_cond, "su_x", "eq")
        imm32(2, SYN_AREA); E(adds_reg, 1, 1, 2); imm32(2, NSUMW)
        a.label("su_l"); E(ldr_imm, 3, 1, 0); E(adds_reg, 0, 0, 3); E(adds_imm8, 1, 4); E(subs_imm8, 2, 1); E(b_cond, "su_l", "ne")
        a.label("su_x"); E(raw, PC.BX_LR)

        # ---- c_m2ok() -> r0 = 1 when the ITCM is ours and the lanes in place, else 0; clobbers r1, r2
        a.label("c_m2ok")
        imm32(1, M2); E(ldr_imm, 0, 1, O_SIG); imm32(2, SSIG); E(cmp_reg, 0, 2); E(movs_imm, 0, 0); E(b_cond, "ok_x", "ne")
        E(ldrb_imm, 0, 1, O_VAL); E(movs_imm, 2, 1); E(ands_reg, 0, 2)
        a.label("ok_x"); E(raw, PC.BX_LR)

        # ---- c_m2adr(r0 = block) -> r0 = its address; clobbers r1
        a.label("c_m2adr")
        E(lsls_imm, 0, 0, 9); it0(1); E(adds_reg, 0, 0, 1); E(raw, PC.BX_LR)

        # ---- c_m2bit(r0 = block): it holds data; clobbers r1-r3
        a.label("c_m2bit")
        imm32(1, M2); E(ldrh_imm, 2, 1, O_MAP); E(movs_imm, 3, 1); E(lsls_reg, 3, 0); E(orrs_reg, 2, 3); E(strh_imm, 2, 1, O_MAP); E(raw, PC.BX_LR)

        # ---- c_m2trk(r0 = a note track's pattern object) -> r0 = 0 / 1 for Synth 1 / 2, else 0xFF; clobbers r1
        a.label("c_m2trk")
        imm32(1, PAT_OBJ); E(cmp_reg, 0, 1); E(b_cond, "tk_0", "eq")
        imm32(1, PAT_OBJ + PAT_SZ); E(cmp_reg, 0, 1); E(b_cond, "tk_1", "eq")
        E(movs_imm, 0, 0xFF); E(raw, PC.BX_LR)
        a.label("tk_0"); E(movs_imm, 0, 0); E(raw, PC.BX_LR)
        a.label("tk_1"); E(movs_imm, 0, 1); E(raw, PC.BX_LR)

        # ---- c_m2ed(r4 = synth) -> r0 = the edited pattern's block; clobbers r1-r3
        a.label("c_m2ed")
        E(push_list, [], lr=True)
        imm32(0, PAT_OBJ + 0x24); E(cmp_imm, 4, 0); E(b_cond, "ed_o", "eq"); imm32(0, PAT_OBJ + PAT_SZ + 0x24)
        a.label("ed_o"); E(ldr_imm, 0, 0, 0); pget(0); E(movs_imm, 1, 7); E(ands_reg, 0, 1); E(lsls_imm, 1, 4, 3); E(adds_reg, 0, 0, 1)
        E(pop_list, [], pc=True)

    if part == "A":
        # ---- c_m2sv (in place of the bl at 0x0802FE5E, the outermost head: r0 = the session manager, r5 = the slot, [manager + 0x60] p0 = the
        #      pack): the chain, then the slot, the pack and the checksum noted (the LED task writes); pack 0 (read-only for the mod): nothing
        a.label("c_m2sv")
        E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 6, 5)
        E(bl, prev["save"]); E(push_list, [0, 1])
        E(ldr_imm, 0, 4, 0x60); pget(0); E(cbz, "sv_x", 0)
        imm32(4, M2); E(strb_imm, 0, 4, O_SPK); E(strb_imm, 6, 4, O_SIDX)
        E(bl, "c_m2sum"); E(str_imm, 0, 4, O_SSUM)
        E(ldrb_imm, 0, 4, O_FL); E(movs_imm, 1, F_SAVE); E(orrs_reg, 0, 1); E(strb_imm, 0, 4, O_FL)
        a.label("sv_x"); E(pop_list, [0, 1]); E(pop_list, [4, 5, 6], pc=True)

        # ---- c_m2ld / c_m2new (the end of "apply session" 0x0802F5B8 / the tail of "new project" 0x0802F5FA, the outermost heads): the lanes not
        #      in place until the LED task has read them (a load: the checksum of what was loaded); the blocks' bitmap stays for a pending save
        for lab, fl, key in (("c_m2ld", F_LOAD, "load"), ("c_m2new", F_NEW, "new")):
            a.label(lab)
            E(push_list, [0, 1, 2, 3, 4], lr=True)
            imm32(4, M2); E(movs_imm, 0, 0); E(strb_imm, 0, 4, O_VAL); E(strb_imm, 0, 4, O_TRY)
            if fl == F_LOAD: E(bl, "c_m2sum"); E(str_imm, 0, 4, O_LSUM)
            E(ldrb_imm, 0, 4, O_FL); E(movs_imm, 1, fl); E(orrs_reg, 0, 1); E(strb_imm, 0, 4, O_FL)
            E(raw, PC.popw([0, 1, 2, 3, 4], lr=True)); E(b_w, prev[key])

        # ---- c_m2cp (in place of the dispatcher's bl to the paste, the outermost head: obj, the source pattern's pointer, the destination): the
        #      chain, then Synth 1 / 2 <- Synth 1 / 2 = the source block copied; <- another track = none
        a.label("c_m2cp")
        E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
        E(bl, prev["copy"])
        E(bl, "c_m2ok"); E(cmp_imm, 0, 0); E(b_cond, "cp_x", "eq")
        E(mov_reg, 0, 4); E(bl, "c_m2trk"); E(cmp_imm, 0, 1); E(b_cond, "cp_x", "hi")
        E(lsls_imm, 7, 0, 3); E(movs_imm, 1, 7); E(ands_reg, 6, 1); E(adds_reg, 7, 7, 6)            # r7 = the destination block
        E(movs_imm, 6, 0)
        a.label("cp_m")
        imm32(0, PAT_OBJ + 4); E(cmp_imm, 6, 0); E(b_cond, "cp_o", "eq"); imm32(0, PAT_OBJ + PAT_SZ + 4)
        a.label("cp_o"); E(ldr_imm, 0, 0, 0); E(subs_reg, 1, 5, 0); E(b_cond, "cp_n", "lo")
        imm32(2, 8 * PAT_N); E(cmp_reg, 1, 2); E(b_cond, "cp_n", "hs")
        imm32(2, PAT_N); E(raw, udiv(0, 1, 2)); E(lsls_imm, 6, 6, 3); E(adds_reg, 6, 6, 0); E(b, "cp_s")
        a.label("cp_n"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 2); E(b_cond, "cp_m", "lo")
        E(mov_reg, 0, 7); E(bl, "c_m2adr"); E(movs_imm, 1, 2); E(lsls_imm, 1, 1, 8); E(bl, "c_m2ff"); E(b, "cp_x")   # not from Synth 1 / 2: none
        a.label("cp_s"); E(cmp_reg, 6, 7); E(b_cond, "cp_x", "eq")
        E(mov_reg, 0, 6); E(bl, "c_m2adr"); E(mov_reg, 5, 0); E(mov_reg, 0, 7); E(bl, "c_m2adr"); E(mov_reg, 1, 5)
        E(movs_imm, 2, 2); E(lsls_imm, 2, 2, 8); E(bl, "c_m2cpy")
        imm32(1, M2); E(ldrh_imm, 2, 1, O_MAP); E(lsrs_reg, 2, 6); E(lsls_imm, 2, 2, 31); E(b_cond, "cp_x", "pl")
        E(mov_reg, 0, 7); E(bl, "c_m2bit")
        a.label("cp_x"); E(pop_list, [4, 5, 6, 7], pc=True)

        # ---- c_m2cl (in place of the dispatcher's bl to the clear, the outermost head: obj, pattern): the chain, then that block none
        a.label("c_m2cl")
        E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
        E(bl, prev["clear"])
        E(bl, "c_m2ok"); E(cmp_imm, 0, 0); E(b_cond, "cl_x", "eq")
        E(mov_reg, 0, 4); E(bl, "c_m2trk"); E(cmp_imm, 0, 1); E(b_cond, "cl_x", "hi")
        E(lsls_imm, 0, 0, 3); E(movs_imm, 1, 7); E(ands_reg, 5, 1); E(adds_reg, 0, 0, 5); E(bl, "c_m2adr")
        E(movs_imm, 1, 2); E(lsls_imm, 1, 1, 8); E(bl, "c_m2ff")
        a.label("cl_x"); E(pop_list, [4, 5, 6], pc=True)

        # ---- c_m2nu (in place of the bl to xlanes' c_xlnu: view, track, pattern, 0 back / 1 forward): the chain, then Synth 1 / 2's eight
        #      lanes of that block rotated the same way (first .. last by one step)
        a.label("c_m2nu")
        E(push_list, [1, 2, 3, 4, 5, 6, 7], lr=True); E(bl, prev["nudge"])
        E(bl, "c_m2ok"); E(cmp_imm, 0, 0); E(b_cond, "nu_x", "eq")
        E(ldr_sp, 4, 0); E(cmp_imm, 4, 1); E(b_cond, "nu_x", "hi")
        E(ldr_sp, 0, 0); E(ldr_sp, 1, 4); E(bl, L["c_pcrule"]); E(cmp_imm, 0, 0); E(b_cond, "nu_x", "eq")
        E(subs_imm8, 0, 4); E(ldrb_imm, 5, 0, 1); E(ldrb_imm, 6, 0, 0); E(cmp_reg, 5, 6); E(b_cond, "nu_x", "hs")   # r5 = first, r6 = last
        E(subs_reg, 6, 6, 5); E(adds_imm8, 6, 1)                                            # r6 = the count
        E(ldr_sp, 0, 4); E(movs_imm, 1, 7); E(ands_reg, 0, 1); E(lsls_imm, 1, 4, 3); E(adds_reg, 0, 0, 1); E(bl, "c_m2adr")
        E(lsls_imm, 5, 5, 1); E(adds_reg, 5, 5, 0)                                          # r5 = knob 0's first pair
        E(movs_imm, 7, 0)
        a.label("nu_l")
        E(mov_reg, 0, 5); E(movs_imm, 1, 2); E(mov_reg, 2, 6); E(movs_imm, 3, 1); E(ldr_sp, 4, 8); E(cmp_imm, 4, 0)
        E(b_cond, "nu_k", "eq"); E(subs_imm8, 3, 1); E(adds_reg, 3, 3, 6); E(subs_imm8, 3, 1)  # forward: count - 1 to the left
        a.label("nu_k"); E(bl, L["c_pmrot"])
        E(adds_imm8, 5, 64); E(adds_imm8, 7, 1); E(cmp_imm, 7, 8); E(b_cond, "nu_l", "lo")
        a.label("nu_x"); E(pop_list, [1, 2, 3, 4, 5, 6, 7], pc=True)

    if part == "H":
        # ---- c_m2pl (the note players' slot 2, the head: this, pattern, step, micro step): Synth 1 / 2 at micro steps 0 / 3 = the eight knobs'
        #      values of that half step set (an extra knob without a row, a value already there, the knob just turned by hand: nothing), then the chain
        a.label("c_m2pl")
        E(push_list, [0, 1, 2, 3, 4, 5, 6, 7], lr=True); E(sub_sp_imm, 4)                  # [sp] scratch, [sp + 4] this, + 8 pattern, + 12 step
        imm32(1, PLAYER0); E(movs_imm, 4, 0); E(cmp_reg, 0, 1); E(b_cond, "pl_s", "eq")
        imm32(1, PLAYER0 + PLAYER_SZ); E(movs_imm, 4, 1); E(cmp_reg, 0, 1); bc("pl_x", "ne")
        a.label("pl_s"); E(movs_imm, 6, 0); E(cmp_imm, 3, 0); E(b_cond, "pl_h", "eq"); E(movs_imm, 6, 1); E(cmp_imm, 3, 3); bc("pl_x", "ne")
        a.label("pl_h"); E(bl, "c_m2ok"); E(cmp_imm, 0, 0); bc("pl_x", "eq")
        E(ldr_sp, 0, 8); E(movs_imm, 1, 7); E(ands_reg, 0, 1); E(lsls_imm, 1, 4, 3); E(adds_reg, 5, 0, 1)      # r5 = the block
        imm32(1, M2); E(ldrh_imm, 0, 1, O_MAP); E(lsrs_reg, 0, 5); E(lsls_imm, 0, 0, 31); bc("pl_x", "pl")
        E(mov_reg, 0, 5); E(bl, "c_m2adr"); E(ldr_sp, 1, 12); E(movs_imm, 2, 31); E(ands_reg, 1, 2); E(lsls_imm, 1, 1, 1)
        E(adds_reg, 0, 0, 1); E(adds_reg, 6, 6, 0)                                            # r6 = knob 0's value
        E(movs_imm, 5, 0)                                                                     # r5 = the knob
        a.label("pl_l")
        E(ldrb_imm, 7, 6, 0); E(cmp_imm, 7, 0xFF); E(b_cond, "pl_n", "eq")
        imm32(0, M2); E(ldrb_imm, 1, 0, O_RK); E(lsls_imm, 2, 4, 3); E(orrs_reg, 2, 5); E(adds_imm8, 2, 0x80); E(cmp_reg, 1, 2); E(b_cond, "pl_g", "ne")
        E(ldr_imm, 1, 0, O_RT); imm32(2, HAL_TICK); E(ldr_imm, 2, 2, 0); E(subs_reg, 2, 2, 1); E(cmp_imm, 2, RECENT); E(b_cond, "pl_n", "ls")
        a.label("pl_g")
        E(mov_reg, 1, 5); E(bl, L["c_nsxrow"]); E(cmp_imm, 0, 0xFE); E(b_cond, "pl_n", "hs")
        E(str_sp, 0, 0); E(mov_reg, 1, 0); E(bl, L["c_nsget"]); E(cmp_reg, 0, 7); E(b_cond, "pl_n", "eq")
        E(mov_reg, 0, 4); E(ldr_sp, 1, 0); E(mov_reg, 2, 7); E(bl, L["c_mcset"])
        if X2: E(mov_reg, 1, 5); E(ldr_sp, 2, 0); E(mov_reg, 3, 7); E(bl, L["c_nsx2"])              # (X2) novasec.use_v12: the knob's second destination
        a.label("pl_n"); E(adds_imm8, 6, 64); E(adds_imm8, 5, 1); E(cmp_imm, 5, 8); E(b_cond, "pl_l", "lo")
        a.label("pl_x"); E(add_sp_imm, 4); E(raw, PC.popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(b_w, prev["play"])

        # ---- c_m2rec (novasec's kn_m2: r0 = synth, r1 = knob, r2 = the value, r3 = the macro handler): a step held = its value into the held
        #      steps of the edited pattern (both halves); else recording while playing = into the playing step's half
        a.label("c_m2rec")
        E(push_list, [3, 4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)   # [sp] = the handler
        E(cmp_imm, 4, 1); bc("rc_x", "hi"); E(cmp_imm, 5, 7); bc("rc_x", "hi")
        E(bl, "c_m2ok"); E(cmp_imm, 0, 0); bc("rc_x", "eq")
        E(ldr_sp, 0, 0); E(ldr_imm, 0, 0, HELD_STORE); pget(0); E(cmp_imm, 0, 0); E(b_cond, "rc_p", "eq")
        E(bl, "c_m2ed"); E(mov_reg, 7, 0); E(bl, "c_m2bit")                                  # a step held: the edited pattern
        E(mov_reg, 0, 7); E(bl, "c_m2adr"); E(lsls_imm, 1, 5, 6); E(adds_reg, 7, 0, 1)        # r7 = the knob's step 0
        imm32(0, STEP_OBJ0 + STEP_PAGE); E(cmp_imm, 4, 0); E(b_cond, "rc_g", "eq"); imm32(0, STEP_OBJ0 + STEP_SZ + STEP_PAGE)
        a.label("rc_g"); E(ldr_imm, 0, 0, 0); pget(0); E(movs_imm, 4, 0); E(cmp_imm, 0, 0); E(b_cond, "rc_q", "eq"); E(movs_imm, 4, 16)
        a.label("rc_q"); imm32(0, MGR + 0x84); E(ldr_imm, 5, 0, 0); E(movs_imm, 0, 0)         # r5 = the held pads, r4 = the page's first step
        a.label("rc_l"); E(movs_imm, 1, 1); E(lsls_reg, 1, 0); E(tst_reg, 5, 1); E(b_cond, "rc_n", "eq")
        E(adds_reg, 1, 0, 4); E(lsls_imm, 1, 1, 1); E(adds_reg, 1, 1, 7); E(strb_imm, 6, 1, 0); E(strb_imm, 6, 1, 1)
        a.label("rc_n"); E(adds_imm8, 0, 1); E(cmp_imm, 0, 16); E(b_cond, "rc_l", "lo"); E(b, "rc_x")
        a.label("rc_p")                                                                       # playing and recording
        for prm in (0, 1):
            imm32(0, REC_ON); pget(prm); E(cmp_imm, 0, 0); bc("rc_x", "eq")
        imm32(0, PLAYER0 + 0x10); E(cmp_imm, 4, 0); E(b_cond, "rc_r", "eq"); imm32(0, PLAYER0 + PLAYER_SZ + 0x10)
        a.label("rc_r"); E(ldr_imm, 0, 0, 0); pget(1); E(cmp_imm, 0, 7); E(b_cond, "rc_t", "ls"); E(movs_imm, 0, 3)
        a.label("rc_t"); E(lsls_imm, 0, 0, 2); imm32(1, TICKS_TAB); E(adds_reg, 0, 0, 1); E(ldr_imm, 7, 0, 0)   # r7 = ticks a step
        imm32(0, ENG + 0x30); E(lsls_imm, 1, 4, 2); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0); E(str_sp, 0, 0)    # [sp] = the store that plays
        E(movs_imm, 1, 2); E(bl, PK.PARAM_GET); E(ldr_imm, 0, 0, 0); E(lsls_imm, 0, 0, 1)
        E(movs_imm, 1, 0); E(cmp_reg, 0, 7); E(b_cond, "rc_h", "lo"); E(movs_imm, 1, 1)
        a.label("rc_h"); E(mov_reg, 7, 1)                                                      # r7 = the half
        E(ldr_sp, 0, 0); pget(1); E(movs_imm, 1, 31); E(ands_reg, 0, 1); E(lsls_imm, 0, 0, 1); E(adds_reg, 7, 7, 0)   # + 2 step
        E(ldr_sp, 0, 0); pget(0); E(movs_imm, 1, 7); E(ands_reg, 0, 1); E(lsls_imm, 1, 4, 3); E(adds_reg, 0, 0, 1)
        E(str_sp, 0, 0); E(bl, "c_m2bit"); E(ldr_sp, 0, 0); E(bl, "c_m2adr"); E(lsls_imm, 1, 5, 6); E(adds_reg, 0, 0, 1)
        E(adds_reg, 0, 0, 7); E(strb_imm, 6, 0, 0)
        imm32(0, M2); E(lsls_imm, 1, 4, 3); E(orrs_reg, 1, 5); E(adds_imm8, 1, 0x80); E(strb_imm, 1, 0, O_RK)
        imm32(1, HAL_TICK); E(ldr_imm, 1, 1, 0); E(str_imm, 1, 0, O_RT)
        a.label("rc_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)

        # ---- c_m2clr (novasec's kn_m2c: r0 = synth, r1 = knob, r2 = the delta, r3 = the knob's row or 0xFF): left = the knob's lane in the edited
        #      pattern cleared; right = the parameter back to the patch's value
        a.label("c_m2clr")
        E(push_list, [3, 4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)   # [sp] = the row
        E(cmp_imm, 4, 1); E(b_cond, "cr_x", "hi"); E(cmp_imm, 5, 7); E(b_cond, "cr_x", "hi")
        E(cmp_imm, 6, 0); E(b_cond, "cr_x", "eq"); E(b_cond, "cr_l", "mi")
        E(ldr_sp, 7, 0); E(cmp_imm, 7, 0xFE); E(b_cond, "cr_x", "hs")
        imm32(1, P19.SESSION_OBJ + 0x14); E(ldr_imm, 1, 1, 0); E(cmp_imm, 1, 0); E(b_cond, "cr_x", "eq")
        imm32(2, REC_SYN); E(adds_reg, 1, 1, 2); E(cmp_imm, 4, 0); E(b_cond, "cr_p", "eq"); imm32(2, SYN_SZ); E(adds_reg, 1, 1, 2)
        a.label("cr_p"); E(str_sp, 1, 0)                                                      # [sp] = the patch in the record
        E(lsls_imm, 0, 7, 3); imm32(2, ROWTAB); E(adds_reg, 0, 0, 2); E(mov_reg, 1, 13); E(bl, ROWGET)
        E(mov_reg, 2, 0); E(mov_reg, 0, 4); E(mov_reg, 1, 7); E(bl, L["c_mcset"]); E(b, "cr_x")
        a.label("cr_l"); E(bl, "c_m2ok"); E(cmp_imm, 0, 0); E(b_cond, "cr_x", "eq")
        E(bl, "c_m2ed"); E(bl, "c_m2adr"); E(lsls_imm, 1, 5, 6); E(adds_reg, 0, 0, 1); E(movs_imm, 1, 64); E(bl, "c_m2ff")
        a.label("cr_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)
        return a.assemble()
    if part == "A":
        return a.assemble(external={k: L[k] for k in HELPERS})

    # ---- part B
    # ---- c_m2led (the LED task's calls, the outermost head): the work, then the chain with nothing on the stack
    a.label("c_m2led")
    E(push_list, [0, 1, 2, 3, 4, 5, 6], lr=True); E(bl, "c_m2work")
    E(raw, PC.popw([0, 1, 2, 3, 4, 5, 6], lr=True)); E(b_w, prev["ledtask"])

    # ---- c_m2work(): nothing until the ITCM is ours; a save, then a new project or a load.  Frame r7 = sp (28 B): [0] cb 0 [4] ctx 0 [8] &done
    #      [12] done [16..27] the item
    W = 28
    a.label("c_m2work")
    E(push_list, [4, 5, 6, 7], lr=True); E(sub_sp_imm, W); E(mov_reg, 7, 13)
    imm32(4, M2); E(ldr_imm, 0, 4, O_SIG); imm32(1, SSIG); E(cmp_reg, 0, 1); bc("wk_x", "ne")
    E(ldrb_imm, 0, 4, O_FL); E(cmp_imm, 0, 0); bc("wk_x", "eq")
    E(movs_imm, 1, 0)
    for o in range(0, W, 4): E(str_imm, 1, 7, o)
    E(mov_reg, 1, 7); E(adds_imm8, 1, 12); E(str_imm, 1, 7, 8)
    E(movs_imm, 1, F_SAVE); E(tst_reg, 0, 1); E(b_cond, "wk_n", "eq")
    E(b, "m2_save"); a.label("wk_svd")
    E(ldrb_imm, 0, 4, O_FL); E(movs_imm, 1, F_SAVE); E(bics_reg, 0, 1); E(strb_imm, 0, 4, O_FL)
    a.label("wk_n")
    E(ldrb_imm, 0, 4, O_FL); E(movs_imm, 1, F_NEW); E(tst_reg, 0, 1); E(b_cond, "wk_l", "eq")
    E(movs_imm, 1, F_NEW | F_LOAD); E(bics_reg, 0, 1); E(strb_imm, 0, 4, O_FL); E(b, "wk_none")    # a new project: no lanes
    a.label("wk_l")
    E(movs_imm, 1, F_LOAD); E(tst_reg, 0, 1); bc("wk_x", "eq")
    E(b, "m2_load")
    a.label("wk_try")                                                                  # a transfer failed: again next frame (8 times)
    E(ldrb_imm, 0, 4, O_TRY); E(adds_imm8, 0, 1); E(strb_imm, 0, 4, O_TRY); E(cmp_imm, 0, TRIES); bc("wk_x", "lo")
    a.label("wk_none")
    it0(0); it0(1); E(bl, L["c_m2ff"]); E(movs_imm, 0, 0); E(strh_imm, 0, 4, O_MAP)
    a.label("wk_ok")
    E(ldrb_imm, 0, 4, O_FL); E(movs_imm, 1, F_LOAD); E(bics_reg, 0, 1); E(strb_imm, 0, 4, O_FL); E(movs_imm, 0, 1); E(strb_imm, 0, 4, O_VAL)
    a.label("wk_x"); E(add_sp_imm, W); E(pop_list, [4, 5, 6, 7], pc=True)

    def item(idx_from, pack_from):
        E(movs_imm, 0, XL.KIND_SES); E(str_imm, 0, 7, 16); E(movs_imm, 0, 0); E(str_imm, 0, 7, 20); E(str_imm, 0, 7, 24)
        idx_from(); E(strb_imm, 0, 7, 20); pack_from(); E(strb_imm, 0, 7, 24)
    def iptr(rd): E(mov_reg, rd, 7); E(adds_imm8, rd, 16)
    def xfer(fn, off, n):                               # r6 = the buffer
        iptr(0); imm32(1, off); E(mov_reg, 2, 6); imm32(3, n); E(bl, fn)
    def cpy(dst, src, n): dst(); src(); imm32(2, n); E(bl, L["c_m2cpy"])
    buf0 = lambda r: E(mov_reg, r, 6)
    def buf16(r): E(mov_reg, r, 6); E(adds_imm8, r, HDR)
    def itat(o): return lambda r: imm32(r, IT0 + o)

    # ---- m2_save (inline; r4 = M2): blocks with data, or the file already reaching the section: the header and the 8 KB in three transfers
    a.label("m2_save")
    item(lambda: E(ldrb_imm, 0, 4, O_SIDX), lambda: E(ldrb_imm, 0, 4, O_SPK))
    E(ldrb_imm, 0, 4, O_SPK); E(subs_imm8, 0, 1); E(cmp_imm, 0, 30); bc("sv_d", "hi")              # a pack 1..31, a slot 0..63 only
    E(ldrb_imm, 0, 4, O_SIDX); E(cmp_imm, 0, 63); bc("sv_d", "hi")
    iptr(0); E(bl, PK.SIZE); E(mov_reg, 5, 0)
    E(ldrh_imm, 0, 4, O_MAP); E(cmp_imm, 0, 0); E(b_cond, "sv_go", "ne")
    imm32(1, OFF); E(cmp_reg, 5, 1); bc("sv_d", "ls")
    a.label("sv_go")
    E(movs_imm, 0, 5); E(bl, PK.BUF_LOCK)
    imm32(6, PK.BUF)
    imm32(0, MAGIC); E(str_imm, 0, 6, 0); E(movs_imm, 0, 1); E(strh_imm, 0, 6, 4); E(ldrh_imm, 0, 4, O_MAP); E(strh_imm, 0, 6, 6)
    imm32(0, DATA); E(str_imm, 0, 6, 8); E(ldr_imm, 0, 4, O_SSUM); E(str_imm, 0, 6, 12)
    cpy(lambda: buf16(0), lambda: itat(0)(1), CH1); xfer(PK.WRITE, OFF, 4096)
    cpy(lambda: buf0(0), lambda: itat(CH1)(1), 4096); xfer(PK.WRITE, OFF + 4096, 4096)
    cpy(lambda: buf0(0), lambda: itat(CH1 + 4096)(1), HDR); xfer(PK.WRITE, OFF + 8192, HDR)
    E(bl, PK.BUF_UNLOCK)
    a.label("sv_d"); E(b, "wk_svd")

    # ---- m2_load (inline; r4 = M2): the loaded project's section, when its header and checksum match; else no lanes
    a.label("m2_load")
    def proj():
        imm32(0, XL.PROJ_OBJ + 0x20); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 8); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    item(proj, lambda: E(movs_imm, 0, 0xFF))
    iptr(0); E(bl, PK.SIZE); imm32(1, OFF + SECT); E(cmp_reg, 0, 1); bc("wk_none", "lo")
    E(movs_imm, 0, 5); E(bl, PK.BUF_LOCK)
    imm32(6, PK.BUF)
    xfer(PK.READ, OFF, 4096); E(cmp_imm, 0, 0); bc("ld_f", "ne")
    E(ldr_imm, 0, 6, 0); imm32(1, MAGIC); E(cmp_reg, 0, 1); bc("ld_u", "ne")
    E(ldrh_imm, 0, 6, 4); E(cmp_imm, 0, 1); bc("ld_u", "ne")
    E(ldr_imm, 0, 6, 8); imm32(1, DATA); E(cmp_reg, 0, 1); bc("ld_u", "ne")
    E(ldr_imm, 0, 6, 12); E(ldr_imm, 1, 4, O_LSUM); E(cmp_reg, 0, 1); bc("ld_u", "ne")
    E(ldrh_imm, 5, 6, 6); E(cmp_imm, 5, 0); bc("ld_u", "eq")                            # r5 = the blocks' bitmap
    cpy(lambda: itat(0)(0), lambda: buf16(1), CH1)
    xfer(PK.READ, OFF + 4096, 4096); E(cmp_imm, 0, 0); bc("ld_f", "ne")
    cpy(lambda: itat(CH1)(0), lambda: buf0(1), 4096)
    xfer(PK.READ, OFF + 8192, HDR); E(cmp_imm, 0, 0); bc("ld_f", "ne")
    cpy(lambda: itat(CH1 + 4096)(0), lambda: buf0(1), HDR)
    E(bl, PK.BUF_UNLOCK); E(strh_imm, 5, 4, O_MAP); E(b, "wk_ok")
    a.label("ld_u"); E(bl, PK.BUF_UNLOCK); E(b, "wk_none")
    a.label("ld_f"); E(bl, PK.BUF_UNLOCK); E(b, "wk_try")
    return a.assemble()


def install(img, report, base_addr):
    """Part A, appended at the end (dspz.add moves it into a gap): the heads of the reset, the power-up DSP send, the save call, the load end,
    the new-project tail, the pattern paste / clear, the Nudge, the players' slot 2; novasec's two calls pointed here.  Part B (IO.install,
    appended at the end of the image afterwards): the LED task's work."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_pcrule=lab("patchain", "c_pcrule"), c_pmrot=lab("playmode", "c_pmrot"))
    Hl = {k: int(v, 16) for k, v in report["m2lanes_h"]["labels"].items()}
    L.update({k: Hl[k] for k in HELPERS})
    xlnu = lab("xlanes", "c_xlnu")
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    prev = dict(rst=FD.bl_target(img, RST_AT, BASE), boot=FD.bl_target(img, BOOT_AT, BASE), save=FD.bl_target(img, P19.SAVE_CALL, BASE),
                load=MP.bw_target(img, P19.LOAD_END, BASE), new=MP.bw_target(img, P19.NEW_TAIL, BASE), copy=FD.bl_target(img, XL.COPY_AT, BASE),
                clear=FD.bl_target(img, XL.CLEAR_AT, BASE), nudge=xlnu, play=u(PLAYER_VT + 8) & ~1)
    assert prev["rst"] == 0x0801D3C8 and prev["boot"] == 0x08029260, {k: hex(v) for k, v in prev.items()}
    assert prev["copy"] == lab("xlanes", "c_xlcp") and prev["clear"] == lab("xlanes", "c_xlclr"), prev
    code, labels = arm_code(base_addr, L, prev, "A")
    img += code
    while len(img) % 4:
        img += bytes([0xFF])
    labels = dict(labels, **{k: v for k, v in Hl.items() if k not in labels})     # (the report: one label list)
    def bl_to(at):
        h1, h2 = struct.unpack_from("<HH", img, at - BASE)
        return FD.bl_target(img, at, BASE) if h1 & 0xF800 == 0xF000 and h2 & 0xD000 == 0xD000 else None
    sites = [o + BASE for o in range(0, len(img) - 4, 2) if bl_to(o + BASE) == xlnu and o + BASE != xlnu]
    sites = [s for s in sites if not (base_addr <= s < base_addr + len(code))]
    assert 1 <= len(sites) <= 2, [hex(x) for x in sites]
    for at, ours in ((RST_AT, "c_m2rst"), (BOOT_AT, "c_m2boot"), (P19.SAVE_CALL, "c_m2sv"), (XL.COPY_AT, "c_m2cp"), (XL.CLEAR_AT, "c_m2cl"),
                     *((s, "c_m2nu") for s in sites)):
        img[at - BASE:at - BASE + 4] = bl(at, labels[ours])
    img[P19.LOAD_END - BASE:P19.LOAD_END - BASE + 4] = b_w(P19.LOAD_END, labels["c_m2ld"])
    img[P19.NEW_TAIL - BASE:P19.NEW_TAIL - BASE + 4] = b_w(P19.NEW_TAIL, labels["c_m2new"])
    assert u(PLAYER_VT + 8) & ~1 == prev["play"]
    struct.pack_into("<I", img, PLAYER_VT + 8 - BASE, labels["c_m2pl"] | 1)
    for k, ours in (("kn_m2", "c_m2rec"), ("kn_m2c", "c_m2clr")):                   # novasec's two calls (bl c_nsret until now)
        at = lab("novasec", k)
        assert FD.bl_target(img, at, BASE) == lab("novasec", "c_nsret"), (k, hex(at))
        img[at - BASE:at - BASE + 4] = bl(at, labels[ours])
    prev["sites"] = sites[0]
    return labels, code, prev


class H:
    """Part H, appended at the end of the image before part A: the helpers, the players' slot 2 (c_m2pl, chaining to the slot as it is now),
    novasec's two calls (c_m2rec, c_m2clr).  Part A's install points the stock's slot and novasec's calls at them."""
    @staticmethod
    def install(img, report):
        import ct_fw
        BASE = ct_fw.APP_BASE
        lab = lambda m, k: int(report[m]["labels"][k], 16)
        L = dict(c_mcset=lab("macroed", "c_mcset"), c_nsxrow=lab("novasec", "c_nsxrow"), c_nsget=lab("novasec", "c_nsget"))
        if X2: L["c_nsx2"] = lab("novasec", "c_nsx2")
        prev = dict(play=struct.unpack_from("<I", img, PLAYER_VT + 8 - BASE)[0] & ~1)
        base = (BASE + len(img) + 3) & ~3
        img += bytes([0xFF]) * (base - BASE - len(img))
        code, labels = arm_code(base, L, prev, "H")
        img += code
        while len(img) % 4:
            img += bytes([0xFF])
        assert len(img) <= 0x70000, f"m2lanes part H: {len(img) - 0x70000} B over the flash"
        report["m2lanes_h"] = dict(arm_start=hex(base), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()})
        return labels


class IO:
    """Part B at the end of the image: the LED task's work (the card), the outermost head of the LED task's calls."""
    @staticmethod
    def install(img, report):
        import ct_fw
        BASE = ct_fw.APP_BASE
        A = {k: int(v, 16) for k, v in report["m2lanes"]["labels"].items()}
        L = {k: A[k] for k in ("c_m2ff", "c_m2cpy")}
        prev = dict(ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
        base = (BASE + len(img) + 3) & ~3
        img += bytes([0xFF]) * (base - BASE - len(img))
        code, labels = arm_code(base, L, prev, "B")
        img += code
        while len(img) % 4:
            img += bytes([0xFF])
        assert len(img) <= 0x70000, f"m2lanes part B: {len(img) - 0x70000} B over the flash"
        for c in PK.LED_CALLS:
            assert FD.bl_target(img, c, BASE) == prev["ledtask"], hex(c)
            img[c - BASE:c - BASE + 4] = bl(c, labels["c_m2led"])
        report["m2lanes"]["io"] = dict(arm_start=hex(base), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()})
        return labels
