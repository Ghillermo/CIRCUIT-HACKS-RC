"""Part 3 of the 8-operator FM: where its patches live (the user, 2026-11-04 / 05, after the device and Components tests on 21_PACK).

Patches: own-synth slot n (mpatch: bank n >> 3, record n & 7) keeps its FM in an extra record of the same bank file, past the stock's 8:
4096 + 512 (n & 7) (the content API refuses Patches index 16+, status 5; a bank longer than 8 records reads / writes and the stock and Components'
reads leave it alone).  The record: "FM8" 1, the 216 parameters (fm8.PLEN), a 16-bit sum, 224 bytes written; a shorter bank is filled with 0xFF up
to it (0xFF records = empty for the stock and Components).  fm8ui's c_fmgath / c_fmappl call c_fsput / c_fsget through mpatch's IO, so
projsyn's virtual slot (0xFF) lands in RAM too: c_f8io in front of mp_io sends an offset >= 4096 there to FMIMG[track].

Projects: FMIMG[track] (224 bytes) in bytes 8..39 of the settings of Synth 1 / 2's patterns 0..7 (the user: «Synth 1/2 pattern bytes»; free in
every session of the copy but 02_Shadow Child's: a signature, the track / block and the record's own sum): 8 blocks = 0xC8, t << 4 | k, 30
bytes.  Written in front of the stock's save when projsyn has gathered; read before projsyn's restore (its LED call), so the apply finds them.

Components (the user: «can we tell the Circuit to ignore the overwrite on Own bits?» -> ok): «Send patches» / «Send pack» rebuild every bank
from Components' library and cut it after the last patch.  Around the stock's own file protocol, for banks (kind 3) of a pack other than 0:
  * the start of a write deletes the old file (0x08039828): first its own bytes (the 172-byte paddings, the FM records) are kept in RAM;
  * the end of that write (0x080396E0): when the new file holds no own bytes (a host that wrote them, the SD app, wins), they are written back;
  * a delete of the bank (0x08039B94): the own bytes kept, the file deleted, then made again: 8 empty records + the own bytes.
A pack-0 or non-bank call goes straight to the stock's delete (its LR kept: rodisk's guard sees the stock's caller).
psave's swap (Duplicate + A + B) and xpatch's copy between packs move the FM records too (their padding moved = the records follow).

RAM (free: S514D, 0x2004A3C0-0x2004FC00; fm8arm's ends at 0x2004D000): FMIMG 0x2004D000 + 0x100 t, EXTB, FFB, the swap's buffers, IOP, KEEP
(+ 0 "OWK1", + 4 pending, + 5 pack, + 6 bank, + 8 the paddings 8 x 172, + K_EXT the records 8 x 224) to 0x2004E468."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fm8 as F  # noqa: E402
import packio as PK  # noqa: E402
import mpatch as MP  # noqa: E402
import projsyn as PS  # noqa: E402
from fm8arm import RET, pushw, popw  # noqa: E402
from thumb import (adds_imm8, adds_reg, b, b_cond, b_w, bl, blx_reg, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, ldrb_reg, lsls_imm, lsrs_imm,  # noqa: E402
                   mov_reg, movs_imm, muls, pop_list, push_list, raw, str_imm, strb_imm, strb_reg, subs_imm8, subs_reg, add_sp_imm,
                   sub_sp_imm, ldrh_reg, strh_reg, h)

FMIMG, EXTB, FFB = 0x2004D000, 0x2004D200, 0x2004D300
SWA, SWB, SWP, IOP, SLOT = 0x2004D500, 0x2004D600, 0x2004D700, 0x2004D740, 0x2004D744
OCT = False                             # (fm8ui.use_v2) the LED task's head also lights Octave for pad 7's pages
KEEP = 0x2004D800
K_SIG, K_PEND, K_PACK, K_BANK = 0, 4, 5, 6
K_PAD = 8
K_EXT = K_PAD + 8 * MP.LEN
K_END = K_EXT + 8 * 224
KSIG = 0x314B574F                         # "OWK1"
EXT0, RECN, HDR = 4096, 224, 0x01384D46   # "FM8" 1
SUM0 = 0x5A38
PSIG = 0xC8
SYN_AREA, PSIZE, PSET, PBYTE0, PBLEN, PNBLK = 0x2E4, 0xCA8, 0x380, 8, 30, 8
SESSION_OBJ = PS.SESSION_OBJ
VREL = EXT0 + 512 * (PS.SLOT & 7)          # an mp_io offset of projsyn's virtual slot's record - VREL = the offset in FMIMG
T_BANK = 4                                # the protocol's type of a patch bank
START_DEL, ITEM_DEL, END_CALL, END_FN = 0x08039828, 0x08039B94, 0x080396E0, 0x080399FE
assert F.PLEN + 6 <= RECN and RECN <= PNBLK * PBLEN and FMIMG + 0x200 <= EXTB and KEEP + K_END <= 0x2004FC00
assert (F.REC_HDR, F.REC_SUM0, F.REC_N) == (struct.pack("<I", HDR), SUM0, RECN)          # fm8.record (the card app's import) writes these records


def code(c, T, L, prev):
    E, imm32, bc, lab = c.E, c.imm32, c.bc, c.L
    def padofs(rd, rs):                                                               # rd = 512 (slot & 7) + 340; clobbers r3
        E(lsls_imm, rd, rs, 29); E(lsrs_imm, rd, rd, 20); imm32(3, MP.OFF); E(adds_reg, rd, rd, 3)
    def extofs(rd, rs):                                                               # rd = 4096 + 512 (slot & 7); clobbers r3
        E(lsls_imm, rd, rs, 29); E(lsrs_imm, rd, rd, 20); E(movs_imm, 3, 1); E(lsls_imm, 3, 3, 12); E(adds_reg, rd, rd, 3)
    def ffb():                                                                        # FFB = 512 x 0xFF
        imm32(0, FFB); E(movs_imm, 1, 1); E(lsls_imm, 1, 1, 9); E(movs_imm, 2, 0xFF); E(bl, PK.MEMSET)

    # ---- c_fsnff(r0 = bytes, r1 = n) -> r0 = 1 when one is not 0xFF; clobbers r2, r3
    lab("c_fsnff")
    E(movs_imm, 2, 0)
    lab("nf_l"); E(cmp_reg, 2, 1); E(b_cond, "nf_0", "hs"); E(ldrb_reg, 3, 0, 2); E(adds_imm8, 2, 1); E(cmp_imm, 3, 0xFF); E(b_cond, "nf_l", "eq")
    E(movs_imm, 0, 1); E(raw, RET)
    lab("nf_0"); E(movs_imm, 0, 0); E(raw, RET)

    # ---- c_fseq(r0 = a, r1 = b, r2 = n) -> r0 = 1 when equal; clobbers r3, r12 (via r2 count down)
    lab("c_fseq")
    E(push_list, [4], lr=False)
    lab("eq_l"); E(cmp_imm, 2, 0); E(b_cond, "eq_1", "eq"); E(subs_imm8, 2, 1); E(ldrb_reg, 3, 0, 2); E(ldrb_reg, 4, 1, 2); E(cmp_reg, 3, 4); E(b_cond, "eq_l", "eq")
    E(movs_imm, 0, 0); E(pop_list, [4]); E(raw, RET)
    lab("eq_1"); E(movs_imm, 0, 1); E(pop_list, [4]); E(raw, RET)

    # ---- c_fssum(r0 = a record) -> r0 = SUM0 + its bytes 4 .. 4 + PLEN, 16 bits; clobbers r1-r3
    lab("c_fssum")
    E(movs_imm, 1, 4); imm32(2, SUM0)
    lab("sm_l"); E(ldrb_reg, 3, 0, 1); E(adds_reg, 2, 2, 3); E(adds_imm8, 1, 1); E(cmp_imm, 1, 4 + F.PLEN); E(b_cond, "sm_l", "lo")
    E(lsls_imm, 0, 2, 16); E(lsrs_imm, 0, 0, 16); E(raw, RET)

    # ---- c_fsvalid(r0 = a record) -> r0 = 1 when its header and sum hold; clobbers r1-r3
    lab("c_fsvalid")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(ldr_imm, 1, 4, 0); imm32(2, HDR); E(cmp_reg, 1, 2); E(b_cond, "va_0", "ne")
    E(bl, "c_fssum"); E(movs_imm, 2, 4 + F.PLEN); E(ldrh_reg, 1, 4, 2); E(cmp_reg, 0, 1); E(b_cond, "va_0", "ne")
    E(movs_imm, 0, 1); E(pop_list, [4], pc=True)
    lab("va_0"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_fsxw(r0 = slot, r1 = 224 bytes): the slot's FM record written (the loaded pack, mpatch's IO); the bank filled with 0xFF up to it
    #      first; nothing when the bytes are all 0xFF and the bank does not reach the record
    lab("c_fsxw")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    extofs(6, 4)
    E(lsrs_imm, 0, 4, 3); E(bl, L["c_mpsz"]); E(mov_reg, 7, 0)
    E(cmp_reg, 7, 6); E(b_cond, "xw_w", "hs")
    E(mov_reg, 0, 5); E(movs_imm, 1, RECN); E(bl, "c_fsnff"); E(cmp_imm, 0, 0); bc("xw_x", "eq")
    ffb()
    lab("xw_f")
    E(cmp_reg, 7, 6); E(b_cond, "xw_w", "hs")
    E(subs_reg, 3, 6, 7); E(movs_imm, 0, 1); E(lsls_imm, 0, 0, 9); E(cmp_reg, 3, 0); E(b_cond, "xw_n", "ls"); E(mov_reg, 3, 0)
    lab("xw_n"); E(push_list, [3, 4]); E(lsrs_imm, 0, 4, 3); E(mov_reg, 1, 7); imm32(2, FFB); E(bl, L["c_mpw"]); E(pop_list, [3, 4])
    E(cmp_imm, 0, 0); bc("xw_x", "ne"); E(adds_reg, 7, 7, 3); E(b, "xw_f")
    lab("xw_w")
    E(lsrs_imm, 0, 4, 3); E(mov_reg, 1, 6); E(mov_reg, 2, 5); E(movs_imm, 3, RECN); E(bl, L["c_mpw"])
    lab("xw_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_fsxr(r0 = slot, r1 = 224 bytes): the slot's FM record read (0xFF where the bank has none)
    lab("c_fsxr")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(mov_reg, 0, 5); E(movs_imm, 1, RECN); E(movs_imm, 2, 0xFF); E(bl, PK.MEMSET)
    E(lsrs_imm, 0, 4, 3); extofs(1, 4); E(mov_reg, 2, 5); E(movs_imm, 3, RECN); E(bl, L["c_mpr"])
    E(pop_list, [4, 5], pc=True)

    # ---- c_fsput(r0 = the track's block, r1 = slot): the record made in EXTB, then written
    lab("c_fsput")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    imm32(2, EXTB); imm32(0, HDR); E(str_imm, 0, 2, 0)
    E(movs_imm, 1, 0)
    lab("pu_l"); E(ldrb_reg, 0, 4, 1); E(adds_imm8, 1, 4); E(strb_reg, 0, 2, 1); E(subs_imm8, 1, 3); E(cmp_imm, 1, F.PLEN); E(b_cond, "pu_l", "lo")
    E(mov_reg, 0, 2); E(bl, "c_fssum"); imm32(2, EXTB); E(movs_imm, 1, 4 + F.PLEN); E(strh_reg, 0, 2, 1)
    E(movs_imm, 0, 0xFF); E(movs_imm, 1, 4 + F.PLEN + 2)
    lab("pu_f"); E(strb_reg, 0, 2, 1); E(adds_imm8, 1, 1); E(cmp_imm, 1, RECN); E(b_cond, "pu_f", "lo")
    E(mov_reg, 0, 5); E(mov_reg, 1, 2); E(bl, "c_fsxw")
    E(pop_list, [4, 5], pc=True)

    # ---- c_fsget(r0 = the track's block, r1 = slot) -> r0 = 1 when the slot's record held, then its parameters in the block
    lab("c_fsget")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0)
    E(mov_reg, 0, 1); imm32(1, EXTB); E(bl, "c_fsxr")
    imm32(0, EXTB); E(bl, "c_fsvalid"); E(cmp_imm, 0, 0); E(b_cond, "ge_x", "eq")
    imm32(2, EXTB); E(movs_imm, 1, 0)
    lab("ge_l"); E(adds_imm8, 1, 4); E(ldrb_reg, 0, 2, 1); E(subs_imm8, 1, 4); E(strb_reg, 0, 4, 1); E(adds_imm8, 1, 1); E(cmp_imm, 1, F.PLEN); E(b_cond, "ge_l", "lo")
    E(movs_imm, 0, 1)
    lab("ge_x"); E(pop_list, [4, 5], pc=True)

    # ---- c_f8io (mp_io's head: r4 = the read / write, r0 bank, r1 offset, r2 buffer, r3 length; c_mpr / c_mpw pushed r4-r7, lr): projsyn's
    #      virtual slot past 4096 = FMIMG[track]; else the head before (projsyn's c_ysio)
    lab("c_f8io")
    imm32(5, PS.STR); E(ldr_imm, 6, 5, PS.O_SIG); imm32(7, PS.STSIG); E(cmp_reg, 6, 7); E(b_cond, "fi_old", "ne")
    E(ldrb_imm, 5, 5, PS.O_VS); E(cmp_imm, 5, 0); E(b_cond, "fi_old", "eq")
    E(movs_imm, 6, 1); E(lsls_imm, 6, 6, 12); E(cmp_reg, 1, 6); E(b_cond, "fi_go", "hs")
    lab("fi_old"); E(b_w, prev["mpio"])
    lab("fi_go")
    E(subs_imm8, 5, 1); E(lsls_imm, 5, 5, 8); imm32(6, FMIMG); E(adds_reg, 6, 6, 5)
    imm32(5, VREL); E(subs_reg, 1, 1, 5); E(b_cond, "fi_bad", "mi")
    E(adds_reg, 5, 1, 3); E(movs_imm, 7, 1); E(lsls_imm, 7, 7, 8); E(cmp_reg, 5, 7); E(b_cond, "fi_bad", "hi")
    E(adds_reg, 6, 6, 1); E(movs_imm, 1, 0)
    imm32(5, PK.WRITE | 1); E(cmp_reg, 4, 5); E(b_cond, "fi_r", "ne")
    lab("fi_w"); E(cmp_reg, 1, 3); E(b_cond, "fi_x", "hs"); E(ldrb_reg, 0, 2, 1); E(strb_reg, 0, 6, 1); E(adds_imm8, 1, 1); E(b, "fi_w")
    lab("fi_r"); E(cmp_reg, 1, 3); E(b_cond, "fi_x", "hs"); E(ldrb_reg, 0, 6, 1); E(strb_reg, 0, 2, 1); E(adds_imm8, 1, 1); E(b, "fi_r")
    lab("fi_x"); E(movs_imm, 0, 0); E(pop_list, [4, 5, 6, 7], pc=True)
    lab("fi_bad"); E(movs_imm, 0, 1); E(movs_imm, 1, 0); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_fsblk(r0 = track, r1 = block) -> r0 = its 32 bytes in the RAM record (Synth 1 / 2's pattern k settings + 8), 0 = no record; clobbers r1-r3
    lab("c_fsblk")
    imm32(2, SESSION_OBJ); E(ldr_imm, 2, 2, 0x14); E(cmp_imm, 2, 0); E(b_cond, "fb_0", "eq")
    E(lsls_imm, 0, 0, 3); E(adds_reg, 0, 0, 1); imm32(1, PSIZE); E(muls, 0, 1)
    imm32(1, SYN_AREA + PSET + PBYTE0); E(adds_reg, 0, 0, 1); E(adds_reg, 0, 0, 2); E(raw, RET)
    lab("fb_0"); E(movs_imm, 0, 0); E(raw, RET)

    # ---- c_fsprj(r0 = track, r1 = 0 put / 1 get): FMIMG[t] <-> the 8 blocks; a get with a wrong block = FMIMG[t]'s header 0
    lab("c_fsprj")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 7, 1)
    E(lsls_imm, 5, 4, 8); imm32(0, FMIMG); E(adds_reg, 5, 5, 0); E(movs_imm, 6, 0)
    lab("pj_b")
    E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(bl, "c_fsblk"); E(cmp_imm, 0, 0); E(b_cond, "pj_bad", "eq")
    E(lsls_imm, 1, 4, 4); E(adds_reg, 1, 1, 6); E(movs_imm, 2, PBLEN); E(muls, 2, 6); E(adds_reg, 2, 2, 5)      # r1 = the id, r2 = FMIMG + 30 k
    E(cmp_imm, 7, 0); E(b_cond, "pj_g", "ne")
    E(movs_imm, 3, PSIG); E(strb_imm, 3, 0, 0); E(strb_imm, 1, 0, 1); E(adds_imm8, 0, 2); E(movs_imm, 1, 0)
    lab("pj_p"); E(ldrb_reg, 3, 2, 1); E(strb_reg, 3, 0, 1); E(adds_imm8, 1, 1); E(cmp_imm, 1, PBLEN); E(b_cond, "pj_p", "lo"); E(b, "pj_n")
    lab("pj_g")
    E(ldrb_imm, 3, 0, 0); E(cmp_imm, 3, PSIG); E(b_cond, "pj_bad", "ne"); E(ldrb_imm, 3, 0, 1); E(cmp_reg, 3, 1); E(b_cond, "pj_bad", "ne")
    E(adds_imm8, 0, 2); E(movs_imm, 1, 0)
    lab("pj_q"); E(ldrb_reg, 3, 0, 1); E(strb_reg, 3, 2, 1); E(adds_imm8, 1, 1); E(cmp_imm, 1, PBLEN); E(b_cond, "pj_q", "lo")
    lab("pj_n"); E(adds_imm8, 6, 1); E(cmp_imm, 6, PNBLK); E(b_cond, "pj_b", "lo")
    E(pop_list, [4, 5, 6, 7], pc=True)
    lab("pj_bad"); E(cmp_imm, 7, 0); E(b_cond, "pj_x", "eq"); E(movs_imm, 0, 0); E(str_imm, 0, 5, 0)
    lab("pj_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_f8save (the bl to the stock save): FMIMG into the records' blocks when projsyn has gathered since the load, then the chain
    lab("c_f8save")
    E(raw, pushw([0, 1, 2, 3, 12], lr=True))
    imm32(0, PS.STR); E(ldr_imm, 1, 0, PS.O_SIG); imm32(2, PS.STSIG); E(cmp_reg, 1, 2); E(b_cond, "fs_n", "ne")
    E(ldrb_imm, 1, 0, PS.O_VALID); E(cmp_imm, 1, 0); E(b_cond, "fs_n", "eq")
    E(movs_imm, 0, 0); E(movs_imm, 1, 0); E(bl, "c_fsprj"); E(movs_imm, 0, 1); E(movs_imm, 1, 0); E(bl, "c_fsprj")
    lab("fs_n"); E(raw, popw([0, 1, 2, 3, 12], lr=True)); E(b_w, prev["save"])

    # ---- c_f8led (the LED task's call: ctrl, frame): a project load's restore pending (projsyn's, after its 3 s) = FMIMG read first; the chain
    lab("c_f8led")
    E(raw, pushw([0, 1, 2, 3, 12], lr=True))
    imm32(0, PS.STR); E(ldr_imm, 1, 0, PS.O_SIG); imm32(2, PS.STSIG); E(cmp_reg, 1, 2); E(b_cond, "fl_n", "ne")
    E(ldrb_imm, 1, 0, PS.O_PEND); E(cmp_imm, 1, 0); E(b_cond, "fl_n", "eq")
    c.now(0); imm32(1, PS.BOOT_MS); E(cmp_reg, 0, 1); E(b_cond, "fl_n", "lo")
    E(movs_imm, 0, 0); E(movs_imm, 1, 1); E(bl, "c_fsprj"); E(movs_imm, 0, 1); E(movs_imm, 1, 1); E(bl, "c_fsprj")
    lab("fl_n"); E(raw, popw([0, 1, 2, 3, 12], lr=True))
    if OCT:                                                                     # (fm8ui.use_v2) the chain, then the Octave LEDs of pad 7's pages
        E(push_list, [1, 4], lr=True); E(bl, prev["ledtask"])
        E(raw, h(0x9800)); E(bl, "c_fmoct"); E(pop_list, [1, 4], pc=True)
    else:
        E(b_w, prev["ledtask"])

    # ================================================================ Components: the own bytes of a bank kept through the file protocol
    # ---- c_okio(r0 = the API's read / write, r1 = offset, r2 = buffer, r3 = length): kind 3, IOP's pack and bank -> r0 status, r1 moved
    lab("c_okio")
    E(push_list, [4, 5, 6, 7], lr=True); E(sub_sp_imm, 32); E(mov_reg, 7, 13)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2); E(str_imm, 3, 7, 28)
    E(movs_imm, 2, PK.KIND_PATCH); E(str_imm, 2, 7, 16); imm32(2, IOP); E(ldrb_imm, 0, 2, 1); E(str_imm, 0, 7, 20); E(ldrb_imm, 0, 2, 0); E(str_imm, 0, 7, 24)
    E(movs_imm, 0, 0); E(str_imm, 0, 7, 0); E(str_imm, 0, 7, 4); E(str_imm, 0, 7, 12)
    E(mov_reg, 0, 7); E(adds_imm8, 0, 12); E(str_imm, 0, 7, 8)
    E(mov_reg, 0, 7); E(adds_imm8, 0, 16); E(mov_reg, 1, 5); E(mov_reg, 2, 6); E(ldr_imm, 3, 7, 28); E(blx_reg, 4)
    E(ldr_imm, 1, 7, 12)
    E(add_sp_imm, 32); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_oksz() -> r0 = the size of IOP's bank (0: none)
    lab("c_oksz")
    E(push_list, [4, 5], lr=True); E(sub_sp_imm, 16); E(mov_reg, 4, 13)
    E(movs_imm, 1, PK.KIND_PATCH); E(str_imm, 1, 4, 0); imm32(2, IOP); E(ldrb_imm, 1, 2, 1); E(str_imm, 1, 4, 4); E(ldrb_imm, 1, 2, 0); E(str_imm, 1, 4, 8)
    E(mov_reg, 0, 4); E(bl, PK.SIZE)
    E(add_sp_imm, 16); E(pop_list, [4, 5], pc=True)

    def each(prefix, body):                                                           # for r6 = 0..7: body (r7 = the size)
        lab(prefix); body(); E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, prefix, "lo")

    def rd_part(base_of, n_max, dst_of, nz):                                          # read min(n_max, size - off) at off = base_of(r6) when off < size
        base_of(4); E(cmp_reg, 4, 7); E(b_cond, nz, "hs")
        dst_of(2); E(subs_reg, 3, 7, 4); E(cmp_imm, 3, n_max); E(b_cond, nz + "m", "ls"); E(movs_imm, 3, n_max)
        lab(nz + "m"); E(mov_reg, 1, 4); imm32(0, PK.READ | 1); E(bl, "c_okio")
        lab(nz)
    def pad_at(rd):                                                                   # rd = 512 r6 + 340
        E(lsls_imm, rd, 6, 9); imm32(3, MP.OFF); E(adds_reg, rd, rd, 3)
    def ext_at(rd):                                                                   # rd = 4096 + 512 r6
        E(lsls_imm, rd, 6, 9); E(movs_imm, 3, 1); E(lsls_imm, 3, 3, 12); E(adds_reg, rd, rd, 3)
    def kpad(rd):                                                                     # rd = KEEP + K_PAD + 172 r6
        E(movs_imm, rd, MP.LEN); E(muls, rd, 6); imm32(3, KEEP + K_PAD); E(adds_reg, rd, rd, 3)
    def kext(rd):                                                                     # rd = KEEP + K_EXT + 224 r6
        E(movs_imm, rd, RECN); E(muls, rd, 6); imm32(3, KEEP + K_EXT); E(adds_reg, rd, rd, 3)

    # ---- c_okcap() -> r0 = 1 when IOP's bank holds own bytes (then they are in KEEP)
    lab("c_okcap")
    E(push_list, [4, 5, 6, 7], lr=True)
    imm32(0, KEEP + K_PAD); imm32(1, K_END - K_PAD); E(movs_imm, 2, 0xFF); E(bl, PK.MEMSET)
    E(bl, "c_oksz"); E(mov_reg, 7, 0)
    E(movs_imm, 6, 0); each("kc_p", lambda: rd_part(pad_at, MP.LEN, kpad, "kc_pn"))
    E(movs_imm, 6, 0); each("kc_e", lambda: rd_part(ext_at, RECN, kext, "kc_en"))
    imm32(0, KEEP + K_PAD); imm32(1, K_END - K_PAD); E(bl, "c_fsnff")
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_oknew() -> r0 = 1 when IOP's bank (just written) holds own bytes of its own: longer than 4096, or a padding not 0xFF
    lab("c_oknew")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(bl, "c_oksz"); E(mov_reg, 7, 0)
    E(movs_imm, 0, 1); E(lsls_imm, 0, 0, 12); E(cmp_reg, 7, 0); E(b_cond, "kn_1", "hi")
    E(movs_imm, 6, 0)
    lab("kn_p")
    pad_at(4); E(cmp_reg, 4, 7); E(b_cond, "kn_0", "hs")
    E(subs_reg, 3, 7, 4); E(cmp_imm, 3, MP.LEN); E(b_cond, "kn_m", "ls"); E(movs_imm, 3, MP.LEN)
    lab("kn_m"); E(mov_reg, 5, 3); imm32(2, FFB); E(mov_reg, 1, 4); imm32(0, PK.READ | 1); E(bl, "c_okio")
    imm32(0, FFB); E(mov_reg, 1, 5); E(bl, "c_fsnff"); E(cmp_imm, 0, 0); E(b_cond, "kn_1", "ne")
    E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "kn_p", "lo")
    lab("kn_0"); E(movs_imm, 0, 0); E(pop_list, [4, 5, 6, 7], pc=True)
    lab("kn_1"); E(movs_imm, 0, 1); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_okput(): KEEP's own bytes into IOP's bank: 0xFF up to the last of them, then each padding / record that holds some
    lab("c_okput")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(movs_imm, 5, 0); E(movs_imm, 6, 0)                                              # r5 = the end needed
    lab("kp_e1"); kpad(0); E(movs_imm, 1, MP.LEN); E(bl, "c_fsnff"); E(cmp_imm, 0, 0); E(b_cond, "kp_e1n", "eq")
    E(lsls_imm, 5, 6, 9); E(movs_imm, 0, 1); E(lsls_imm, 0, 0, 9); E(adds_reg, 5, 5, 0)
    lab("kp_e1n"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "kp_e1", "lo")
    E(movs_imm, 6, 0)
    lab("kp_e2"); kext(0); E(movs_imm, 1, RECN); E(bl, "c_fsnff"); E(cmp_imm, 0, 0); E(b_cond, "kp_e2n", "eq")
    ext_at(5); E(adds_imm8, 5, RECN)
    lab("kp_e2n"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "kp_e2", "lo")
    E(cmp_imm, 5, 0); bc("kp_x", "eq")
    ffb(); E(bl, "c_oksz"); E(mov_reg, 7, 0)
    lab("kp_f"); E(cmp_reg, 7, 5); E(b_cond, "kp_w", "hs")
    E(subs_reg, 3, 5, 7); E(movs_imm, 0, 1); E(lsls_imm, 0, 0, 9); E(cmp_reg, 3, 0); E(b_cond, "kp_n", "ls"); E(mov_reg, 3, 0)
    lab("kp_n"); E(mov_reg, 4, 3); E(mov_reg, 1, 7); imm32(2, FFB); imm32(0, PK.WRITE | 1); E(bl, "c_okio")
    E(cmp_imm, 0, 0); bc("kp_x", "ne"); E(adds_reg, 7, 7, 4); E(b, "kp_f")
    lab("kp_w"); E(movs_imm, 6, 0)
    lab("kp_wp"); kpad(4); E(mov_reg, 0, 4); E(movs_imm, 1, MP.LEN); E(bl, "c_fsnff"); E(cmp_imm, 0, 0); E(b_cond, "kp_wpn", "eq")
    pad_at(1); E(mov_reg, 2, 4); E(movs_imm, 3, MP.LEN); imm32(0, PK.WRITE | 1); E(bl, "c_okio")
    lab("kp_wpn"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "kp_wp", "lo")
    E(movs_imm, 6, 0)
    lab("kp_we"); kext(4); E(mov_reg, 0, 4); E(movs_imm, 1, RECN); E(bl, "c_fsnff"); E(cmp_imm, 0, 0); E(b_cond, "kp_wen", "eq")
    ext_at(1); E(mov_reg, 2, 4); E(movs_imm, 3, RECN); imm32(0, PK.WRITE | 1); E(bl, "c_okio")
    lab("kp_wen"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "kp_we", "lo")
    lab("kp_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_okitem(r0 = an item of the API) -> r0 = 1 when it is a bank of a pack 1..31 (then IOP = its pack and bank); clobbers r1-r3
    lab("c_okitem")
    E(ldr_imm, 1, 0, 0); E(cmp_imm, 1, PK.KIND_PATCH); E(b_cond, "ki_0", "ne")
    E(ldr_imm, 1, 0, 4); E(cmp_imm, 1, 16); E(b_cond, "ki_0", "hs")
    E(ldrb_imm, 2, 0, 8); E(cmp_imm, 2, 0); E(b_cond, "ki_0", "eq"); E(cmp_imm, 2, 32); E(b_cond, "ki_0", "hs")
    imm32(3, IOP); E(strb_imm, 2, 3, 0); E(strb_imm, 1, 3, 1); E(movs_imm, 0, 1); E(raw, RET)
    lab("ki_0"); E(movs_imm, 0, 0); E(raw, RET)

    # ---- c_okkeep() -> r0 = KEEP: its signature, the pending flag = c_okcap(), the pack / bank of IOP
    lab("c_okkeep")
    E(push_list, [4], lr=True)
    E(bl, "c_okcap"); imm32(4, KEEP); E(strb_imm, 0, 4, K_PEND)
    imm32(1, KSIG); E(str_imm, 1, 4, K_SIG); imm32(2, IOP); E(ldrb_imm, 1, 2, 0); E(strb_imm, 1, 4, K_PACK); E(ldrb_imm, 1, 2, 1); E(strb_imm, 1, 4, K_BANK)
    E(mov_reg, 0, 4); E(pop_list, [4], pc=True)

    # ---- c_okresel(): the storage task back on the loaded pack (after another pack's file)
    lab("c_okresel")
    E(push_list, [4], lr=True); E(bl, L["c_curpack"]); E(bl, L["c_resel"]); E(pop_list, [4], pc=True)

    # ---- c_okdel1 (the delete at the start of a write: r0 = the item, r1 = r2 = 0): a bank's own bytes kept (pending), then the stock's delete
    #      with the stock's LR
    lab("c_okdel1")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 12], lr=True))
    E(bl, "c_okitem"); E(cmp_imm, 0, 0); E(b_cond, "d1_n", "eq")
    E(bl, "c_okkeep")
    lab("d1_n"); E(raw, popw([0, 1, 2, 3, 4, 5, 12], lr=True)); E(b_w, PK.DEL_FN)

    # ---- c_okdel2 (the protocol's delete of an item): a bank's own bytes kept, the stock's delete, the file made again with them
    lab("c_okdel2")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 12], lr=True))
    E(bl, "c_okitem"); E(cmp_imm, 0, 0); E(b_cond, "d2_s", "ne")
    E(raw, popw([0, 1, 2, 3, 4, 5, 12], lr=True)); E(b_w, PK.DEL_FN)                 # not ours: the stock's delete, with the stock's LR
    lab("d2_s")
    E(raw, popw([0, 1, 2, 3, 4, 5, 12], lr=True))
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0)
    E(bl, "c_okkeep"); E(ldrb_imm, 5, 0, K_PEND); E(movs_imm, 1, 0); E(strb_imm, 1, 0, K_PEND)
    E(mov_reg, 0, 4); E(movs_imm, 1, 0); E(movs_imm, 2, 0); E(bl, PK.DEL_FN); E(mov_reg, 6, 0)
    E(cmp_imm, 5, 0); E(b_cond, "d2_r", "eq")
    E(cmp_imm, 6, 0); E(b_cond, "d2_p", "eq"); E(cmp_imm, 6, 5); E(b_cond, "d2_r", "ne")
    lab("d2_p"); E(bl, "c_okput")
    lab("d2_r"); E(bl, "c_okresel"); E(mov_reg, 0, 6); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_okend (the bl to the end of a write: r0 = the protocol object, r1 = the message): the stock's end, then a kept bank's own bytes
    #      written back when the new file holds none
    lab("c_okend")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0)
    E(bl, END_FN)
    imm32(5, KEEP); E(ldr_imm, 0, 5, K_SIG); imm32(1, KSIG); E(cmp_reg, 0, 1); bc("ke_x", "ne")
    E(ldrb_imm, 0, 5, K_PEND); E(cmp_imm, 0, 0); bc("ke_x", "eq")
    E(ldrb_imm, 0, 4, 0x1C); E(cmp_imm, 0, T_BANK); bc("ke_x", "ne")
    E(ldrb_imm, 0, 4, 0x1D); E(ldrb_imm, 1, 5, K_PACK); E(cmp_reg, 0, 1); bc("ke_x", "ne")
    E(ldrb_imm, 0, 4, 0x1E); E(ldrb_imm, 1, 5, K_BANK); E(cmp_reg, 0, 1); bc("ke_x", "ne")
    E(movs_imm, 0, 0); E(strb_imm, 0, 5, K_PEND)
    imm32(2, IOP); E(ldrb_imm, 0, 5, K_PACK); E(strb_imm, 0, 2, 0); E(ldrb_imm, 0, 5, K_BANK); E(strb_imm, 0, 2, 1)
    E(bl, "c_oknew"); E(cmp_imm, 0, 0); E(b_cond, "ke_r", "ne")
    E(bl, "c_okput")
    lab("ke_r"); E(bl, "c_okresel")
    lab("ke_x"); E(pop_list, [4, 5], pc=True)

    # ================================================================ psave's swap and xpatch's copy: the FM records follow
    # ---- c_fsswap(r0 = slot A, r1 = slot B) (the call of psave's c_psxswap): A's padding remembered, both records read, the swap, then (B's
    #      padding = A's: it happened) the records exchanged
    lab("c_fsswap")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    imm32(0, SWP); E(movs_imm, 1, MP.DATA); E(movs_imm, 2, 0xFF); E(bl, PK.MEMSET)
    E(lsrs_imm, 0, 4, 3); padofs(1, 4); imm32(2, SWP); E(movs_imm, 3, MP.DATA); E(bl, L["c_mpr"])
    E(mov_reg, 0, 4); imm32(1, SWA); E(bl, "c_fsxr"); E(mov_reg, 0, 5); imm32(1, SWB); E(bl, "c_fsxr")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, prev["psxswap"])
    E(lsrs_imm, 0, 5, 3); padofs(1, 5); imm32(2, EXTB); E(movs_imm, 3, MP.DATA); E(bl, L["c_mpr"])
    imm32(0, EXTB); imm32(1, SWP); E(movs_imm, 2, MP.DATA); E(bl, "c_fseq"); E(cmp_imm, 0, 0); E(b_cond, "sw_x", "eq")
    E(mov_reg, 0, 5); imm32(1, SWA); E(bl, "c_fsxw"); E(mov_reg, 0, 4); imm32(1, SWB); E(bl, "c_fsxw")
    lab("sw_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_fsxcopy(r0 = the pack of A, r1 = slot A, r2 = slot B of the loaded pack) (the call of xpatch's c_xqcopy): A's padding and record read
    #      from its pack, the copy, then (B's padding = A's) the record written
    lab("c_fsxcopy")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    imm32(3, IOP); E(strb_imm, 4, 3, 0); E(lsrs_imm, 0, 5, 3); E(strb_imm, 0, 3, 1)
    imm32(0, SWP); E(movs_imm, 1, MP.DATA); E(movs_imm, 2, 0xFF); E(bl, PK.MEMSET)
    imm32(0, SWA); E(movs_imm, 1, RECN); E(movs_imm, 2, 0xFF); E(bl, PK.MEMSET)
    padofs(1, 5); imm32(2, SWP); E(movs_imm, 3, MP.DATA); imm32(0, PK.READ | 1); E(bl, "c_okio")
    extofs(1, 5); imm32(2, SWA); E(movs_imm, 3, RECN); imm32(0, PK.READ | 1); E(bl, "c_okio")
    E(bl, "c_okresel")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(mov_reg, 2, 6); E(bl, prev["xqcopy"])
    E(lsrs_imm, 0, 6, 3); padofs(1, 6); imm32(2, EXTB); E(movs_imm, 3, MP.DATA); E(bl, L["c_mpr"])
    imm32(0, EXTB); imm32(1, SWP); E(movs_imm, 2, MP.DATA); E(bl, "c_fseq"); E(cmp_imm, 0, 0); E(b_cond, "xc_x", "eq")
    E(mov_reg, 0, 6); imm32(1, SWA); E(bl, "c_fsxw")
    lab("xc_x"); E(pop_list, [4, 5, 6], pc=True)


def find_bl(img, base, target, lo=None, hi=None):
    """every bl to target in the image (4-byte aligned or not)"""
    import fxdiag as FD
    out = []
    lo = lo or base; hi = hi or base + len(img) - 4
    for at in range(lo, hi, 2):
        h1, h2 = struct.unpack_from("<HH", img, at - base)
        if h1 & 0xF800 == 0xF000 and h2 & 0xD000 == 0xD000 and FD.bl_target(img, at, base) == target:
            out.append(at)
    return out


def prev_of(img, report):
    """what the hooks chain to, read before they are placed"""
    import ct_fw
    import fxdiag as FD
    BASE = ct_fw.APP_BASE
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    import persist19 as P19
    mpio = lab("mpatch", "mp_io")
    p = dict(mpio=MP.bw_target(img, mpio, BASE), save=FD.bl_target(img, P19.SAVE_CALL, BASE), ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE),
             psxswap=lab("psave", "c_psxswap"), xqcopy=lab("xpatch", "c_xqcopy"))
    assert FD.bl_target(img, PK.LED_CALLS[1], BASE) == p["ledtask"]
    assert p["mpio"] == lab("projsyn", "c_ysio"), "mp_io's head: projsyn's c_ysio expected"
    return p


def hooks(img, report, labels, own):
    """mp_io's head, the save call, the LED task's calls, the protocol's three sites, psave's / xpatch's calls (each found once)."""
    import ct_fw
    import fxdiag as FD
    import hole
    import persist19 as P19
    BASE = ct_fw.APP_BASE
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    def put(at, enc):
        img[at - BASE:at - BASE + 4] = enc; hole.rehash(img, report, at)
    mpio = lab("mpatch", "mp_io")
    put(mpio, b_w(mpio, labels["c_f8io"]))
    put(P19.SAVE_CALL, bl(P19.SAVE_CALL, labels["c_f8save"]))
    for c_ in PK.LED_CALLS: put(c_, bl(c_, labels["c_f8led"]))
    for at, tgt, ours in ((START_DEL, PK.DEL_FN, "c_okdel1"), (ITEM_DEL, PK.DEL_FN, "c_okdel2"), (END_CALL, END_FN, "c_okend")):
        assert FD.bl_target(img, at, BASE) == tgt, hex(at)
        put(at, bl(at, labels[ours]))
    for tgt, ours in ((lab("psave", "c_psxswap"), "c_fsswap"), (lab("xpatch", "c_xqcopy"), "c_fsxcopy")):
        sites = [a_ for a_ in find_bl(img, BASE, tgt) if not own[0] <= a_ < own[1]]
        assert len(sites) == 1, (ours, [hex(s) for s in sites])
        put(sites[0], bl(sites[0], labels[ours]))
