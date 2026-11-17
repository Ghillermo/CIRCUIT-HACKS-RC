"""Chains per scene (the user, 2026-11-13: «We need a rule per scene» -> «Scenes hold up to 16 different chains.  Whether each track gets custom
chain or stock chain is selected per track» -> «Instead of chaining patterns, we chain consecutive pattern groups», «Scene save: Save current
chain to the scene»).

patchain.use_groups(): a track's chain = one word (groups A, B, C: start, length, repeats; bits 30 / 31 = B / C there), the tracks with a chain
in a mask.  This module keeps them and gives each scene its own:
  * Shift + a scene pad (the stock's scene save, its first write 0x0802DC90, the outermost head) = the eight tracks' chains into the scene
    (a track without a chain = the stock chain there);
  * the scene copy (0x0802DE42) copies them;
  * a scene starting while playing (the track advance's choice of the next pattern, 0x0802CD4A, the outermost head: a scene change, not the
    look-ahead) puts that track's chain of the scene in place before patchain reads it; stopped, the LED task does the eight tracks when the
    current scene changes (the Mixer's scene pads); a scene saved before this build changes nothing.

Where:
  * RAM: the ITCM (free from 0x0DDA, after xlanes' two playing blocks, to 0x18A3, tabpack's group): RB = 0x0E00 (patchain.G_RB): "SCR3",
    + 4 the bitmap of the scenes saved, + 6 flags, + 7 tries, + 8 / 9 the slot / pack to save, + 10 the scene applied last + 1, + 12 the
    scenes' checksum at the save, + 16 at the load; + 20 the tracks with a chain, + 24 their words; + 56 each scene's mask, + 72 its eight
    words (32 B a scene): 584 B.  Only the CPU uses it (the card's reads go through the shared buffer: DMA does not reach the ITCM).
  * on the card, after the extra lanes' area (xlanes: 160 780 + 16 + 26 016 = 186 812 B): 16 B ("SCN3", version 3, the scenes' bitmap, the
    length, the checksum of the record's 16 scenes (40 B each at record + 0x40, as words)) + the 564 B from RB + 20.  Written by the LED task
    after a save (any chain or scene, or the file already that long), read after a load when the scenes' checksum matches.  A Components write
    of the session drops it (the extra lanes are held and written back; these are not)."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bics_reg, bl, cbz, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, ldrh_imm,  # noqa: E402
                   lsls_imm, lsls_reg, lsrs_imm, lsrs_reg, mov_reg, movs_imm, movt, movw, orrs_reg, pop_list, push_list, raw, str_imm,
                   strb_imm, strb_reg, strh_imm, sub_sp_imm, add_sp_imm, tst_reg, subs_imm8, ands_reg, h)
import packio as PK  # noqa: E402
import persist19 as P19  # noqa: E402
import mpatch as MP  # noqa: E402
import fxdiag as FD  # noqa: E402
import patchain as PC  # noqa: E402
import xlanes as XL  # noqa: E402

INV = {"eq": "ne", "ne": "eq", "hs": "lo", "lo": "hs", "hi": "ls", "ls": "hi", "mi": "pl", "pl": "mi", "cc": "cs", "cs": "cc"}
RB = PC.G_RB                                   # the ITCM
SIG = PC.G_SIG                                 # "SCR3"
MAGIC = 0x334E_4353                            # "SCN3"
H_MAP, H_FL, H_TRY, H_SIDX, H_SPK, H_LAST, H_SCN, H_LSCN = 4, 6, 7, 8, 9, 10, 12, 16
O_CURM, O_CURW, O_SCM, O_SCW = PC.G_CURM, PC.G_CURW, PC.G_SCM, PC.G_SCW
NS, NT = 16, 8
O_DATA = O_CURM
DATA = O_SCW + NS * NT * 4 - O_DATA            # 564 B: the current chains, the scenes'
END = RB + O_DATA + DATA
HDR = 16
SECT = HDR + DATA
OFF = XL.SZ0 + XL.HDR + XL.DATA                # 186 812: after the extra lanes' area
F_SAVE, F_LOAD, F_NEW = 1, 2, 4
TRIES = 8
SCN0, SCN_N = 0x40, NS * 40 // 4               # the record's 16 scenes, as words
ENG = 0x20038EC0                               # + 0x2C: the scene store (p0 = the current scene)
TRANSPORT = 0x20011034                         # the transport store: p0 playing
POP_LR = PC.POP_LR
assert END <= 0x18A4 and RB >= XL.IC0 + XL.ICS + XL.BLK and H_LSCN + 4 <= O_CURM and DATA % 4 == 0
SC_CLEAR = 0x0802DFC6                          # the stock scene clear (Clear + scene pad): the first of its eight bl 0x0802B2CC(store, r1 = r4 = the scene, ...)

# Beta 5.63, the 2026-11-14 bug hunt (options: the builds before stay byte-identical)
SVFIX = False       # SCR-1 / XC-1: the save head noted the pack as the slot and the slot as the pack (the section went to project <pack> of pack
                    # <slot>, the chains were lost on every save); and a save in pack 0 (internal, read-only for the mod) writes nothing
SCLEAR = False      # SCR-3: Clear + a scene pad (the stock's scene clear) = the scene's chains gone too (its bit in the bitmap, its mask)


def use_svfix():
    global SVFIX
    SVFIX = True


def use_sclear():
    global SCLEAR
    SCLEAR = True


def ldr_reg(rt, rn, rm): return h(0x5800 | rm << 6 | rn << 3 | rt)
def str_reg(rt, rn, rm): return h(0x5000 | rm << 6 | rn << 3 | rt)


def arm_code(base, L, prev, part="A"):
    """part A: the hooks (in a dspz gap); part B: the LED task's work, the card (at the end of the image; L holds part A's labels)"""
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_s{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    def ldrb_sp(rt, off): return PC.ldrb_sp(rt, off)

    # ---- c_srap(r0 = RB, r1 = scene, r2 = track): a saved scene = the track's chain of that scene in place (none there = the stock chain);
    #      clobbers r1-r3
    a.label("c_srap")
    E(push_list, [4, 5], lr=True)
    E(ldrh_imm, 3, 0, H_MAP); E(lsrs_reg, 3, 1); E(lsrs_imm, 3, 3, 1); E(b_cond, "ap_x", "cc")
    E(lsls_imm, 3, 1, 5); E(lsls_imm, 4, 2, 2); E(adds_reg, 3, 3, 4); E(adds_reg, 3, 3, 0); E(ldr_imm, 3, 3, O_SCW)    # its word
    E(adds_reg, 4, 0, 4); E(str_imm, 3, 4, O_CURW)
    E(adds_reg, 3, 0, 1); E(adds_imm8, 3, O_SCM); E(ldrb_imm, 3, 3, 0); E(lsrs_reg, 3, 2); E(movs_imm, 4, 1); E(ands_reg, 3, 4)            # its bit
    E(lsls_reg, 4, 2); E(ldrb_imm, 5, 0, O_CURM); E(bics_reg, 5, 4); E(lsls_reg, 3, 2); E(orrs_reg, 5, 3); E(strb_imm, 5, 0, O_CURM)
    a.label("ap_x"); E(pop_list, [4, 5], pc=True)

    # ---- c_srscn() -> r0 = the record's 16 scenes summed as words (0 without a record); clobbers r1-r3
    a.label("c_srscn")
    imm32(1, P19.SESSION_OBJ + 0x14); E(ldr_imm, 1, 1, 0); E(movs_imm, 0, 0); E(cmp_imm, 1, 0); E(b_cond, "sc_x", "eq")
    E(adds_imm8, 1, SCN0); E(movs_imm, 2, SCN_N)
    a.label("sc_l"); E(ldr_imm, 3, 1, 0); E(adds_reg, 0, 0, 3); E(adds_imm8, 1, 4); E(subs_imm8, 2, 1); E(b_cond, "sc_l", "ne")
    a.label("sc_x"); E(raw, PC.BX_LR)

    # ---- c_srcur() -> r0 = the current scene; clobbers r1-r3
    a.label("c_srcur")
    E(push_list, [], lr=True); imm32(0, ENG + 0x2C); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(pop_list, [], pc=True)

    # ---- c_srss (the scene save's first write, the outermost head: r1 = the scene): the eight tracks' chains into the scene
    a.label("c_srss")
    E(push_list, [0, 1, 2, 3, 4, 5], lr=True)
    E(mov_reg, 4, 1); E(cmp_imm, 4, NS); E(b_cond, "ss_x", "hs")
    E(bl, L["c_srst"]); E(mov_reg, 5, 0)
    E(ldrb_imm, 1, 5, O_CURM); E(adds_reg, 2, 5, 4); E(adds_imm8, 2, O_SCM); E(strb_imm, 1, 2, 0)
    E(lsls_imm, 2, 4, 5); E(adds_reg, 2, 2, 5); E(adds_imm8, 2, O_SCW); E(mov_reg, 1, 5); E(adds_imm8, 1, O_CURW); E(movs_imm, 3, 32)
    a.label("ss_c"); E(subs_imm8, 3, 4); E(raw, ldr_reg(0, 1, 3)); E(raw, str_reg(0, 2, 3)); E(cmp_imm, 3, 0); E(b_cond, "ss_c", "ne")
    E(ldrh_imm, 0, 5, H_MAP); E(movs_imm, 1, 1); E(lsls_reg, 1, 4); E(orrs_reg, 0, 1); E(strh_imm, 0, 5, H_MAP)
    E(adds_imm8, 4, 1); E(strb_imm, 4, 5, H_LAST)                                      # (the scene saved = the chains on screen)
    a.label("ss_x"); E(pop_list, [0, 1, 2, 3, 4, 5]); E(raw, POP_LR); E(b_w, prev["ssave"])

    # ---- c_srsc (the scene copy's first write, the outermost head: r1 = the destination, [r7, #1] = the source): its chains copied
    a.label("c_srsc")
    E(push_list, [0, 1, 2, 3, 4, 5, 6], lr=True)
    E(mov_reg, 4, 1); E(ldrb_imm, 6, 7, 1); E(cmp_imm, 4, NS); E(b_cond, "sy_x", "hs"); E(cmp_imm, 6, NS); E(b_cond, "sy_x", "hs")
    E(bl, L["c_srst"]); E(mov_reg, 5, 0)
    E(ldrh_imm, 2, 5, H_MAP); E(mov_reg, 0, 2); E(lsrs_reg, 0, 6); E(movs_imm, 1, 1); E(ands_reg, 0, 1)
    E(lsls_reg, 1, 4); E(bics_reg, 2, 1); E(lsls_reg, 0, 4); E(orrs_reg, 2, 0); E(strh_imm, 2, 5, H_MAP)
    E(adds_reg, 0, 5, 6); E(adds_imm8, 0, O_SCM); E(ldrb_imm, 0, 0, 0); E(adds_reg, 1, 5, 4); E(adds_imm8, 1, O_SCM); E(strb_imm, 0, 1, 0)
    E(lsls_imm, 1, 6, 5); E(adds_reg, 1, 1, 5); E(adds_imm8, 1, O_SCW); E(lsls_imm, 2, 4, 5); E(adds_reg, 2, 2, 5); E(adds_imm8, 2, O_SCW)
    E(movs_imm, 3, 32)
    a.label("sy_c"); E(subs_imm8, 3, 4); E(raw, ldr_reg(0, 1, 3)); E(raw, str_reg(0, 2, 3)); E(cmp_imm, 3, 0); E(b_cond, "sy_c", "ne")
    a.label("sy_x"); E(pop_list, [0, 1, 2, 3, 4, 5, 6]); E(raw, POP_LR); E(b_w, prev["scopy"])

    # ---- c_srnx (the track advance's choice of the next pattern, the outermost head; the stock's frame at sp: [sp] = the track,
    #      [sp, #0x44] = a scene change, [sp, #0x48] = the scene, fp = 1 the look-ahead): a scene starting = the track's chain of that scene
    F = 24
    a.label("c_srnx")
    E(push_list, [0, 1, 2, 3, 4], lr=True)
    E(mov_reg, 0, 11); E(cmp_imm, 0, 0); E(b_cond, "nx_x", "ne")
    E(raw, ldrb_sp(0, F + 0x44)); E(cmp_imm, 0, 0); E(b_cond, "nx_x", "eq")
    E(raw, ldrb_sp(4, F)); E(cmp_imm, 4, NT); E(b_cond, "nx_x", "hs")
    E(bl, L["c_srst"]); E(raw, ldrb_sp(1, F + 0x48)); E(cmp_imm, 1, NS); E(b_cond, "nx_x", "hs")
    E(adds_imm8, 1, 1); E(strb_imm, 1, 0, H_LAST); E(subs_imm8, 1, 1); E(mov_reg, 2, 4); E(bl, "c_srap")
    a.label("nx_x"); E(pop_list, [0, 1, 2, 3, 4]); E(raw, POP_LR); E(b_w, prev["next"])

    # ---- c_srsv (in place of the bl at 0x0802FE5E, the outermost head: r0 = the session manager, r5 = the slot, [manager + 0x60] p0 = the
    #      pack, as the stock's own item at 0x0802FE6A..0x0802FE88): the chain, then the slot, the pack and the scenes' checksum noted (the LED
    #      task writes).  (Before SVFIX the two were stored the wrong way round: the section went to project <pack> of pack <slot>.)
    a.label("c_srsv")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 6, 5)
    E(bl, prev["save"]); E(push_list, [0])
    E(bl, L["c_srst"]); E(mov_reg, 5, 0)
    E(ldr_imm, 0, 4, 0x60); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    if SVFIX:
        E(strb_imm, 0, 5, H_SPK); E(strb_imm, 6, 5, H_SIDX)
        E(cbz, "sv_x", 0)                                                   # pack 0 (internal, read-only for the mod): nothing to write
    else:
        E(strb_imm, 0, 5, H_SIDX); E(strb_imm, 6, 5, H_SPK)
    E(bl, "c_srscn"); E(str_imm, 0, 5, H_SCN)
    E(ldrb_imm, 0, 5, H_FL); E(movs_imm, 1, F_SAVE); E(orrs_reg, 0, 1); E(strb_imm, 0, 5, H_FL)
    if SVFIX: a.label("sv_x")
    E(pop_list, [0]); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_srld (the end of "apply session", 0x0802F5B8, the outermost head): nothing until the card is read; the scenes' checksum
    a.label("c_srld")
    E(push_list, [0, 1, 2, 3, 4], lr=True)
    E(bl, L["c_srst"]); E(mov_reg, 4, 0)
    E(movs_imm, 0, 0); E(strh_imm, 0, 4, H_MAP); E(strb_imm, 0, 4, O_CURM); E(strb_imm, 0, 4, H_TRY)
    E(bl, "c_srscn"); E(str_imm, 0, 4, H_LSCN)
    E(ldrb_imm, 0, 4, H_FL); E(movs_imm, 1, F_LOAD); E(orrs_reg, 0, 1); E(strb_imm, 0, 4, H_FL)
    E(raw, PC.popw([0, 1, 2, 3, 4], lr=True)); E(b_w, prev["load"])

    # ---- c_srnew (the tail of "new project", 0x0802F5FA): nothing
    a.label("c_srnew")
    E(push_list, [0, 1, 2, 3, 4], lr=True)
    E(bl, L["c_srst"])
    E(movs_imm, 1, 0); E(strh_imm, 1, 0, H_MAP); E(strb_imm, 1, 0, O_CURM); E(ldrb_imm, 1, 0, H_FL); E(movs_imm, 2, F_NEW); E(orrs_reg, 1, 2)
    E(strb_imm, 1, 0, H_FL)
    E(raw, PC.popw([0, 1, 2, 3, 4], lr=True)); E(b_w, prev["new"])

    if SCLEAR:
        # ---- c_srscl (the stock scene clear's first bl 0x0802B2CC, the outermost head: r1 = r4 = the scene, [sp] = its fifth argument): the
        #      scene's bit in the bitmap and its mask cleared (c_srap / c_srnx then leave the current chains alone, c_pcchained says no);
        #      r0-r3 and [sp] as they were for the call (r6, set to 0 by the stock just before, untouched)
        a.label("c_srscl")
        E(push_list, [0, 1, 2, 3, 4], lr=True)
        E(cmp_imm, 1, NS); E(b_cond, "cl_x", "hs")
        E(movs_imm, 3, 1); E(lsls_reg, 3, 1); E(mov_reg, 4, 1); E(adds_imm8, 4, O_SCM)       # (c_srst clobbers r0-r2)
        E(bl, L["c_srst"])
        E(ldrh_imm, 1, 0, H_MAP); E(bics_reg, 1, 3); E(strh_imm, 1, 0, H_MAP)
        E(movs_imm, 1, 0); E(strb_reg, 1, 0, 4)                                                   # RB + O_SCM + the scene
        a.label("cl_x"); E(pop_list, [0, 1, 2, 3, 4]); E(raw, POP_LR); E(b_w, prev["sclear"])

    if part == "A":
        return a.assemble()
    a = Asm(base)
    E = a.emit
    # ---- c_srled (the LED task's calls, the outermost head): the work, then the chain with nothing on the stack
    a.label("c_srled")
    E(push_list, [0, 1, 2, 3, 4, 5, 6], lr=True); E(bl, "c_srwork")
    E(raw, PC.popw([0, 1, 2, 3, 4, 5, 6], lr=True)); E(b_w, prev["ledtask"])

    # ---- c_srwork(): frame r7 = sp (28 B): [0] cb 0 [4] ctx 0 [8] &done [12] done [16..27] the item
    W = 28
    a.label("c_srwork")
    E(push_list, [4, 5, 6, 7], lr=True); E(sub_sp_imm, W); E(mov_reg, 7, 13)
    E(bl, L["c_srst"]); E(mov_reg, 4, 0)
    E(movs_imm, 1, 0)
    for o in range(0, W, 4): E(str_imm, 1, 7, o)
    E(mov_reg, 1, 7); E(adds_imm8, 1, 12); E(str_imm, 1, 7, 8)
    E(ldrb_imm, 0, 4, H_FL); E(movs_imm, 1, F_NEW); E(tst_reg, 0, 1); E(b_cond, "wk_s", "eq")
    E(movs_imm, 1, F_NEW | F_LOAD); E(bics_reg, 0, 1); E(strb_imm, 0, 4, H_FL); E(b, "wk_cur")      # a new project: nothing to read
    a.label("wk_s")
    E(movs_imm, 1, F_SAVE); E(tst_reg, 0, 1); E(b_cond, "wk_l", "eq")
    E(b, "sr_save"); a.label("wk_svd")
    E(ldrb_imm, 0, 4, H_FL); E(movs_imm, 1, F_SAVE); E(bics_reg, 0, 1); E(strb_imm, 0, 4, H_FL)
    a.label("wk_l")
    E(ldrb_imm, 0, 4, H_FL); E(movs_imm, 1, F_LOAD); E(tst_reg, 0, 1); E(b_cond, "wk_p", "eq")
    E(b, "sr_load"); a.label("wk_ldr"); E(cmp_imm, 0, 0); E(b_cond, "wk_ld", "eq")
    E(ldrb_imm, 0, 4, H_TRY); E(adds_imm8, 0, 1); E(strb_imm, 0, 4, H_TRY); E(cmp_imm, 0, TRIES); bc("wk_x", "lo")
    a.label("wk_ld")
    E(ldrb_imm, 0, 4, H_FL); E(movs_imm, 1, F_LOAD); E(bics_reg, 0, 1); E(strb_imm, 0, 4, H_FL)
    a.label("wk_cur"); E(bl, "c_srcur"); E(adds_imm8, 0, 1); E(strb_imm, 0, 4, H_LAST); E(b, "wk_x")   # loaded: the chains on screen stay
    a.label("wk_p")                                                                    # stopped: a scene picked = its chains
    imm32(0, TRANSPORT); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(cmp_imm, 0, 0); bc("wk_x", "ne")
    E(bl, "c_srcur"); E(mov_reg, 6, 0); E(adds_imm8, 0, 1); E(ldrb_imm, 1, 4, H_LAST); E(cmp_reg, 0, 1); bc("wk_x", "eq")
    E(strb_imm, 0, 4, H_LAST)
    E(cmp_imm, 6, NS); bc("wk_x", "hs")
    E(movs_imm, 5, 0)
    a.label("wk_t"); E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(mov_reg, 2, 5); E(bl, "c_srap")
    E(adds_imm8, 5, 1); E(cmp_imm, 5, NT); E(b_cond, "wk_t", "lo")
    a.label("wk_x"); E(add_sp_imm, W); E(pop_list, [4, 5, 6, 7], pc=True)

    def item(idx_from, pack_from):
        E(movs_imm, 0, XL.KIND_SES); E(str_imm, 0, 7, 16); E(movs_imm, 0, 0); E(str_imm, 0, 7, 20); E(str_imm, 0, 7, 24)
        idx_from(); E(strb_imm, 0, 7, 20); pack_from(); E(strb_imm, 0, 7, 24)
    def iptr(rd): E(mov_reg, rd, 7); E(adds_imm8, rd, 16)
    def copy_words(tag, n):                            # r0 = dst, r1 = src, n words; clobbers r0-r3
        E(movs_imm, 2, n)
        a.label(f"_cw{tag}"); E(ldr_imm, 3, 1, 0); E(str_imm, 3, 0, 0); E(adds_imm8, 0, 4); E(adds_imm8, 1, 4); E(subs_imm8, 2, 1)
        E(b_cond, f"_cw{tag}", "ne")

    # ---- sr_save (inline in c_srwork; r4 = RB): the section, when any track or scene holds a chain or the file already reaches it
    a.label("sr_save")
    item(lambda: E(ldrb_imm, 0, 4, H_SIDX), lambda: E(ldrb_imm, 0, 4, H_SPK))
    iptr(0); E(bl, PK.SIZE); E(mov_reg, 5, 0)
    E(ldrh_imm, 0, 4, H_MAP); E(ldrb_imm, 1, 4, O_CURM); E(orrs_reg, 0, 1); E(cmp_imm, 0, 0); E(b_cond, "sv_go", "ne")
    imm32(1, OFF); E(cmp_reg, 5, 1); bc("sv_d", "ls")
    a.label("sv_go")
    E(movs_imm, 0, 5); E(bl, PK.BUF_LOCK)
    imm32(6, PK.BUF)
    imm32(0, MAGIC); E(str_imm, 0, 6, 0); E(movs_imm, 0, 3); E(strh_imm, 0, 6, 4); E(ldrh_imm, 0, 4, H_MAP); E(strh_imm, 0, 6, 6)
    imm32(0, DATA); E(str_imm, 0, 6, 8); E(ldr_imm, 0, 4, H_SCN); E(str_imm, 0, 6, 12)
    E(mov_reg, 0, 6); E(adds_imm8, 0, HDR); E(mov_reg, 1, 4); E(adds_imm8, 1, O_DATA); copy_words("s", DATA // 4)
    iptr(0); imm32(1, OFF); E(mov_reg, 2, 6); imm32(3, SECT); E(bl, PK.WRITE)
    E(bl, PK.BUF_UNLOCK)
    a.label("sv_d"); E(b, "wk_svd")

    # ---- sr_load (inline in c_srwork; r4 = RB) -> r0 = 0 done (the chains or none), else a transfer failed (try again)
    a.label("sr_load")
    def proj():
        imm32(0, XL.PROJ_OBJ + 0x20); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 8); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    item(proj, lambda: E(movs_imm, 0, 0xFF))
    iptr(0); E(bl, PK.SIZE); imm32(1, OFF + SECT); E(cmp_reg, 0, 1); bc("lo_0", "lo")
    E(movs_imm, 0, 5); E(bl, PK.BUF_LOCK)
    iptr(0); imm32(1, OFF); imm32(2, PK.BUF); imm32(3, SECT); E(bl, PK.READ); E(cmp_imm, 0, 0); bc("lo_f", "ne")
    imm32(6, PK.BUF)
    E(ldr_imm, 0, 6, 0); imm32(1, MAGIC); E(cmp_reg, 0, 1); bc("lo_u", "ne")
    E(ldrh_imm, 0, 6, 4); E(cmp_imm, 0, 3); bc("lo_u", "ne")
    E(ldr_imm, 0, 6, 8); imm32(1, DATA); E(cmp_reg, 0, 1); bc("lo_u", "ne")
    E(ldr_imm, 0, 6, 12); E(ldr_imm, 1, 4, H_LSCN); E(cmp_reg, 0, 1); bc("lo_u", "ne")
    E(mov_reg, 0, 4); E(adds_imm8, 0, O_DATA); E(mov_reg, 1, 6); E(adds_imm8, 1, HDR); copy_words("l", DATA // 4)
    E(ldrh_imm, 0, 6, 6); E(strh_imm, 0, 4, H_MAP)
    a.label("lo_u"); E(bl, PK.BUF_UNLOCK)
    a.label("lo_0"); E(movs_imm, 0, 0); E(b, "wk_ldr")
    a.label("lo_f"); E(bl, PK.BUF_UNLOCK); E(movs_imm, 0, 1); E(b, "wk_ldr")
    return a.assemble(external={k: L[k] for k in ("c_srap", "c_srcur")})


def install(img, report, base_addr):
    """Part A, appended at the end (dspz.add moves it into a gap): the outermost heads of the scene save / copy, the next-pattern choice, the save
    call, the load end, the new-project tail.  Part B (IO.install, appended at the end of the image afterwards): the LED task's work."""
    import ct_fw
    from thumb import bl as bl_enc
    BASE = ct_fw.APP_BASE
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_srst=lab("patchain", "c_pcgi"))
    prev = dict(ssave=FD.bl_target(img, PC.SC_SAVE, BASE), scopy=FD.bl_target(img, PC.SC_COPY, BASE), next=FD.bl_target(img, PC.NEXT_HOOK, BASE),
                save=FD.bl_target(img, P19.SAVE_CALL, BASE), load=MP.bw_target(img, P19.LOAD_END, BASE), new=MP.bw_target(img, P19.NEW_TAIL, BASE))
    if SCLEAR:
        prev["sclear"] = FD.bl_target(img, SC_CLEAR, BASE)                  # (the stock's 0x0802B2CC, or a head already there)
    assert prev["save"] == lab("xlanes", "c_xlsv"), prev
    code, labels = arm_code(base_addr, L, prev, "A")
    img += code
    while len(img) % 4:
        img += bytes([0xFF])
    for at, ours in ((PC.SC_SAVE, "c_srss"), (PC.SC_COPY, "c_srsc"), (PC.NEXT_HOOK, "c_srnx"), (P19.SAVE_CALL, "c_srsv")) + (((SC_CLEAR, "c_srscl"),) if SCLEAR else ()):
        img[at - BASE:at - BASE + 4] = bl_enc(at, labels[ours])
    img[P19.LOAD_END - BASE:P19.LOAD_END - BASE + 4] = b_w(P19.LOAD_END, labels["c_srld"])
    img[P19.NEW_TAIL - BASE:P19.NEW_TAIL - BASE + 4] = b_w(P19.NEW_TAIL, labels["c_srnew"])
    return labels, code, prev


class IO:
    """Part B at the end of the image: the LED task's work (the card), the outermost head of the LED task's calls."""
    @staticmethod
    def install(img, report):
        import ct_fw
        from thumb import bl as bl_enc
        BASE = ct_fw.APP_BASE
        A = {k: int(v, 16) for k, v in report["scrules"]["labels"].items()}
        L = {k: A[k] for k in ("c_srap", "c_srcur")}
        L["c_srst"] = int(report["patchain"]["labels"]["c_pcgi"], 16)
        prev = dict(ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
        assert prev["ledtask"] == int(report["xlanes"]["labels"]["c_xlled"], 16), prev
        prev.update({k: int(v, 16) for k, v in report["scrules"]["prev"].items()})       # (part A is assembled again and dropped)
        base = BASE + len(img)
        code, labels = arm_code(base, L, prev, "B")
        img += code
        while len(img) % 4:
            img += bytes([0xFF])
        for c in PK.LED_CALLS:
            assert FD.bl_target(img, c, BASE) == prev["ledtask"], hex(c)
            img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_srled"])
        report["scrules"]["io"] = dict(arm_start=hex(base), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()})
        return labels


def pack(groups):
    """A chain word from [(start 0-7, end 0-7, repeats 1-16)] for A [, B [, C]] (the tests)."""
    w = 0
    for g, (s, e, r) in enumerate(groups):
        w |= (s | (e - s) << 3 | (r - 1) << 6) << 10 * g
        if g: w |= 1 << (29 + g)
    return w
