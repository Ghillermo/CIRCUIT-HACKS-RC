"""Extra automation lanes of the own synth of MIDI 1 / 2, phase 1: the storage (the user, 2026-11-13: 25 more lanes, every destination its own lane,
2 values a step; «Every one has its lane», «Start and middle», «Both full, as today»; see the memory note extra-lanes-spec and docs/NOTAS.md).

Where the lanes live:
  * on the card: after the session file's 160 780 bytes (the stock loads only its 0x2740C and its save does not cut the file: tested on the device,
    2026-11-13, tools/sesstail.py): a 16-byte header ("XLN1", version 1, the bitmap of the blocks that hold data, a checksum of MIDI 1 / 2's 16
    patterns as the stock saved them, the data's length) and 16 blocks (MIDI 1 / 2 x 8 patterns) of BLK bytes;
  * in the DSP's external memory (Y $337000-$33FFFF, free: S557D, 2026-11-13; 16 bits a word, as the samples): the 16 blocks, XB + block x BLKW.
  * a block (BLK = 1 626 B): 25 slots, each a destination code (0 = free) + 32 steps x 2 values (0xFF = none), the codes first, then the values.

When (the card and the DSP's window need the shared 4 KB buffer, whose lock must never be taken inside the stock's save / load: the hooks only note,
the LED task does the work right after):
  * the save (the bl at 0x0802FE5E, the outermost head): after the stock's preparation, the slot it writes (r5 at the call) and the pack
    (byte 0 of [session + 0x60]) and the checksum (before use_svfix the two were stored the wrong way round); the LED task then writes the header and, with any block holding data, the 16 blocks; a project without
    lanes and a file without a tail: nothing written (the file stays 160 780 B);
  * the load (the end of the stock's "apply session", 0x0802F5B8: a load, a new project, the power-up): the checksum of the patterns just loaded;
    the LED task reads the header of the loaded project (the Projects view's param 8) and, when it matches (magic, length, checksum), the blocks into
    the DSP; else no lanes (the bitmap 0); a transfer that fails is tried again (8 times, one a frame: the DSP may not run yet at power-up);
  * a new project (0x0802F5FA): no lanes.
  * the Projects view's check of a session (0x080404B4: the header's size = 0x2740C and = the file's size) accepts a file at least that long
    (10 bytes at 0x080404B6), so a project with lanes is not shown dim.
RAM: XLR (0x2004C540, 64 B, signed "XLR1": in the free bytes between fm8arm's write cache, 0x2004C540, and its state at 0x2004C600).
The internal pack (pack 0) is read-only for the mod (rodisk): its projects keep no lanes."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, strb_w, adds_imm8, adds_reg, add_sp_imm, ands_reg, b, b_cond, b_w, bics_reg, bl, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, ldrb_reg, ldrh_imm,  # noqa: E402
                   lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw, orrs_reg, pop_list, push_list, raw, str_imm, str_sp, strb_imm, strb_reg, strh_imm, strh_reg,
                   sub_sp_imm, subs_imm8, subs_reg)
import packio as PK  # noqa: E402
import persist19 as P19  # noqa: E402
import mpatch as MP  # noqa: E402
import fxdiag as FD  # noqa: E402

INV = {"eq": "ne", "ne": "eq", "hs": "lo", "lo": "hs", "hi": "ls", "ls": "hi", "ge": "lt", "lt": "ge", "gt": "le", "le": "gt", "mi": "pl", "pl": "mi"}
SESSION_OBJ, PROJ_OBJ = 0x2003D71C, 0x20044324
SZ0 = 0x2740C                                  # the stock part of a session file
PAT0, PATLEN = 0x1A27C, 2 * 8 * 0xCA8          # MIDI 1 / 2's patterns in the session record: the checksum
NSLOT, NSTEP, VPS = 25, 32, 2
BLK = (NSLOT + NSLOT * NSTEP * VPS + 1) & ~1    # 1 626 B
BLKW, NBLK = BLK // 2, 16
DATA = BLK * NBLK                              # 26 016 B
HDR = 16
XB = 0x337000                                  # the DSP's external Y: the 16 blocks
XLR = 0x2004C540
SIG = 0x3152_4C58                              # "XLR1"
MAGIC = 0x314E_4C58                            # "XLN1"
O_FL, O_SIDX, O_SPK, O_TRY, O_SSUM, O_LSUM, O_MAP, O_HOLD = 4, 5, 6, 7, 8, 12, 16, 20
O_QN, O_Q, QMAX = 24, 25, 4                    # the queued block copies: count, then (source, destination) pairs
O_HV, O_HPS, O_HHDR = 18, 34, 40              # Components: a held tail (valid; pack | slot << 8, a halfword) and its header
O_CM = 56                                      # the playing blocks' cache, per track (+ m): + 0 the block cached + 1 (0 none), + 2 changed, + 4 wanted + 1
ST_LEN = 64                                    # the state's bytes made at the first use
IC0, ICS = 0x100, 0x680                        # the ITCM (free once the FM instruments are gone): MIDI m's playing block at IC0 + ICS m
PLAYER0, PLAYER_SZ, PLAYER_VT = 0x20040200, 0x184, 0x0805B750   # the note players; slot 2 = a micro step (this, pattern, step, micro step)
ENG = 0x20038EC0                               # the engine: + 0x30 + 4 id = the store that plays (pattern, step, tick)
TICKS_TAB = 0x0805B8B8                         # the stock's ticks per step, by sync rate (u32)
REC_ON = 0x20011034                            # the transport store: p0 playing, p1 Record
VOFF, VSTEP = NSLOT, NSTEP * VPS               # a block: the 25 codes, then slot s's values at VOFF + VSTEP s + 2 step + half
XH = XB + 0x3400                               # the DSP's external Y: a session's blocks held through a Components write
TB, TBN = 0x2004D500, 512                      # fm8store's swap buffers (SWA..SWP: patch swaps from the panel only; blocked during a Components session):
                                               # the Components path's transfer buffer (not the ITCM: the card's reads may use DMA)
T_SES = 3                                      # the file protocol's type of a session
START_DEL, END_CALL = 0x08039828, 0x080396E0   # Components' write: the delete at its start, the bl to its end (fm8store's c_okdel1 / c_okend there)
F_SAVE, F_LOAD, F_NEW = 1, 2, 4
PAT_OBJ, PAT_SZ, PAT_N = 0x20039E50, 0x3A0, 0xCA8   # the note tracks' pattern objects (vtable 0x0805C114): [+ 4] = the track's 8 patterns
COPY_AT, COPY_FN = 0x0802DC3C, 0x0803D2B0      # the stock's pattern dispatcher (0x0802DBC0): paste (obj, source pointer, destination pattern)
CLEAR_AT, CLEAR_FN = 0x0802DC60, 0x0803D310    # ... clear (obj, pattern)
TRIES = 8
KIND_SES = 2
VALID_AT = 0x080404B6                           # the stock's session check: ldr r2, [r0, #4]; cmp r2, r1; itt eq; ldreq r1, [pc, #0x20]; cmpeq r2, r1
VALID_OLD = bytes.fromhex("42688a4204bf08498a42")


RELOAD = False
ZLOOP = False                                   # Alpha 7.19 (use_zloop)


def use_zloop():
    """Alpha 7.19 (flash room): the API frames zeroed by packio.zloop (12 B) instead of one str per word, with r2 / r3 (dead there)."""
    global ZLOOP
    ZLOOP = True
O_RQ, O_NB = 19, 33                            # use_reload(): a block to read again from the card + 1 (0 none); the project is new and never saved


def use_reload():
    """SC57.5 / Beta 5.60 (tools/patrev.py: Clear + Duplicate twice in a track view = the pattern back as the card has it): one block read again
    from the card when patrev asks (XLR + O_RQ = block + 1), in the LED task's work after the queue and a pending load: the file's header must
    match (magic, version, length, and the checksum of the last load or of the last save); the block's bit set = its 1 626 bytes into the DSP,
    else the block emptied; the cached copy of a playing block dropped (cached and changed: the work fills it again).  A failed transfer is tried
    again (8 times, as the load).  Also XLR + O_NB: 1 after a new project, 0 after a load or a save (patrev refuses a new project: the slot's
    file is another project's)."""
    global RELOAD
    RELOAD = True


MEMFIX = False


def use_memfix():
    """SC57.8 / Beta 5.63 (a fix; the user, 2026-11-14, Beta 5.62's black box: «crash grabando knobs de VA», a UsageFault UNALIGNED at
    0x0801A9D2): the stock's memset 0x0801A9BC stores with stm and needs a word-aligned destination (any length); c_xlput made an empty block
    with memset(block + VOFF, ...) = block + 25 (odd: recording a knob without a stock lane into an empty block crashed the unit), and the
    auto-clear head (Clear + knob) erased a slot's values with memset(block + 64 slot + 25, ...).  Now c_xlput fills from block + 24 (aligned:
    the values and the last code, 0xFF) and then the 25 codes with 0 from block; the auto-clear fills its 64 bytes with its own byte loop."""
    global MEMFIX
    MEMFIX = True
    # (also, since the 2026-11-14 bug hunt's XL-3, before any build used it: the auto-clear head skips a block whose bitmap bit is clear, so
    #  stale ITCM content of a block that holds no data is never edited nor marked changed)


SVFIX = False


def use_svfix():
    """SC57.8 / Beta 5.63 (a fix, the 2026-11-14 bug hunt XL-1 / SCR-2 / XC-1; the user's report (c): the lanes gone after a Save + reload): the
    save hook stored the slot and the pack the wrong way round (at the bl at 0x0802FE5E r5 = the project slot, [manager + 0x60] p0 = the pack: the
    stock's own item 0x0802FE6A..0x0802FE88 is {2, r5, p0}), so the tail went to project <pack> of pack <slot>.  Now pack = p0, slot = r5; and a
    project of the internal pack (pack 0, read-only for the mod: rodisk) writes no tail instead of flashing Save red."""
    global SVFIX
    SVFIX = True


FILLFIX = False


def use_fillfix():
    """SC57.8 / Beta 5.63 (a fix, XL-5): c_xlfill marked a block cached (= wanted) before copying it from the DSP, so while the LED task filled it
    (tens of ms) c_xlpl played the new pattern's codes with the old block's values and a value recorded meanwhile was overwritten.  Now cached = 0
    while it fills and = the block filled only once every word is in; a failed DSP copy leaves cached = 0 (tried again the next frame).  c_xlflush:
    a failed copy back marks the block changed again (written back the next frame)."""
    global FILLFIX
    FILLFIX = True


EDITCACHE = False


def use_editcache():
    """SC57.8 / Beta 5.63 (a fix, XL-4): every edit of the extra lanes (Record + step = c_xlsn, Nudge = c_xlnu, Clear + knob = c_xlca) applies to
    the cached block only, and the cache followed the block that plays (c_xlpl): with the transport stopped (after a load, or another pattern
    edited) the edits were lost and a Nudge left the lanes out of step with the notes.  Now, with the transport stopped, the block wanted is the
    edited pattern of MIDI 1 / 2 ([PAT_OBJ + PAT_SZ (2 + m) + 0x24] p0), cached by the LED task's next frame; playing: as before (the playing one)."""
    global EDITCACHE
    EDITCACHE = True


LATE = False
LATE_RAM = 0x2004FB80                          # (use_late) + m: MIDI m's block has just been cached


def use_late():
    """Alpha 7.02 (the user, 2026-11-17: «Make pattern related data, like lanex, follows the current pattern at play, even with pattern chain and
    pattern mutate» -> «Apply late»): when the pattern that plays changes (a chain, a pattern-mutate list, the stock's chain), its block is read
    from the DSP by the LED task (tens of ms) and the step values it holds were skipped until the next half step (micro step 0 / 3).  Now the end
    of a fill (c_xlfill) marks the track (LATE_RAM + m, 2 B below 0x2004FC00, free in every release build) and c_xlpl plays the current half step
    on the next micro step (micro 1 / 2: the first half, 4 / 5: the second): about one micro step late, not half a step.  A micro step 0 / 3
    clears the mark (garbage at power-up: one replay at most)."""
    global LATE
    LATE = True                                # (needs use_fillfix: fi_ok)


ATOMIC = False
MAXCODE = 34                                   # the highest stored code of the own synth (modmx.ranges: codes 0..34)


def use_atomic():
    """SC57.8 / Beta 5.63 (a fix, XL-6): the save wrote the header (the bitmap, the checksum) first and then the blocks, so a failed DSP copy or card
    write left a valid header over stale blocks (a file already long enough) and the next load played garbage codes (c_vvaddr has no bound for a
    code > 26: RAM past the V2 area written).  Now the header with bitmap 0 first, the blocks, the real header last (a failure in between = no
    lanes on the next load); and c_xlpl skips a code above MAXCODE.  (c_xlback needs nothing: it writes only over a file of exactly 160 780 B,
    so a failure leaves it too short for the load's size check.)"""
    global ATOMIC
    ATOMIC = True


def valid_new():
    """ldr r2, [r0, #4]; cmp r1, r2; bcc fail (0x080404DC); ldr r1, [pc, #0x20] (0x2740C); cmp r2, r1 -> the bne at 0x080404C0 stays."""
    out = h(0x6842) + h(0x4291)                                   # ldr r2, [r0, #4]; cmp r1, r2
    pc = VALID_AT + 4 + 4
    out += h(0xD300 | ((0x080404DC - pc) >> 1) & 0xFF)             # bcc
    out += h(0x4908) + h(0x428A)                                   # ldr r1, [pc, #0x20]; cmp r2, r1
    return out


def bl_to(img, at, base):
    """the target of a bl at at, or None"""
    h1, h2 = struct.unpack_from("<HH", img, at - base)
    if h1 & 0xF800 != 0xF000 or h2 & 0xD000 != 0xD000: return None
    return FD.bl_target(img, at, base)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_x{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
    def pushw10(): E(raw, h(0xE92D) + h(0x50FF))                                       # push.w {r0-r7, r12, lr}
    def popw10(): E(raw, h(0xE8BD) + h(0x50FF))                                        # pop.w {r0-r7, r12, lr}
    def meta(rd, rs):                                                                  # rd = XLR + O_CM (rs = XLR)
        E(movs_imm, rd, O_CM); E(adds_reg, rd, rd, rs)

    # ---- c_xlst() -> r0 = XLR, made the first time (no lanes, nothing pending); clobbers r1-r3
    a.label("c_xlst")
    imm32(0, XLR); E(ldr_imm, 1, 0, 0); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "st_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0)
    for o in range(4, ST_LEN, 4): E(str_imm, 1, 0, o)
    a.label("st_x"); E(raw, h(0x4770))

    # ---- c_xlbit(r0 = block, r1 = 1 set / 0 clear): the bitmap of the blocks holding data; keeps r0, r1; clobbers r2, r3
    a.label("c_xlbit")
    E(push_list, [0, 1, 4], lr=True); E(bl, "c_xlst"); E(mov_reg, 4, 0); E(raw, h(0x9800)); E(raw, h(0x9901))   # ldr r0, [sp]; ldr r1, [sp, #4]
    E(movs_imm, 2, 1); E(raw, h(0x4082)); E(ldrh_imm, 3, 4, O_MAP)                      # lsls r2, r0
    E(cmp_imm, 1, 0); E(b_cond, "bt_c", "eq"); E(orrs_reg, 3, 2); E(b, "bt_w")
    a.label("bt_c"); E(bics_reg, 3, 2)
    a.label("bt_w"); E(strh_imm, 3, 4, O_MAP); E(pop_list, [0, 1, 4], pc=True)

    # ---- c_xlmb(r0 = a note track's pattern object) -> r0 = 0 MIDI 1, 1 MIDI 2, 0xFF another track; clobbers r1
    a.label("c_xlmb")
    imm32(1, PAT_OBJ + 2 * PAT_SZ); E(cmp_reg, 0, 1); E(b_cond, "mb_0", "eq")
    imm32(1, PAT_OBJ + 3 * PAT_SZ); E(cmp_reg, 0, 1); E(b_cond, "mb_1", "eq")
    E(movs_imm, 0, 0xFF); E(raw, h(0x4770))
    a.label("mb_0"); E(movs_imm, 0, 0); E(raw, h(0x4770))
    a.label("mb_1"); E(movs_imm, 0, 1); E(raw, h(0x4770))

    # ---- c_xlcp (in place of the dispatcher's bl 0x0803D2B0: obj, the source pattern's pointer, the destination pattern): the stock's paste, then
    #      the lanes: MIDI 1 / 2 <- MIDI 1 / 2 = the block's bit, its words queued for the LED task; <- another track or an empty block = none
    a.label("c_xlcp")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(bl, COPY_FN)
    E(mov_reg, 0, 4); E(bl, "c_xlmb"); E(cmp_imm, 0, 0xFF); bc("cp_x", "eq")
    E(lsls_imm, 7, 0, 3); E(movs_imm, 1, 7); E(ands_reg, 6, 1); E(adds_reg, 7, 7, 6)   # r7 = the destination block
    E(movs_imm, 6, 0)                                                                 # r6 = the source track (0 / 1)
    a.label("cp_m")
    imm32(0, PAT_OBJ + 2 * PAT_SZ); E(movs_imm, 1, 0); E(cmp_imm, 6, 0); E(b_cond, "cp_mo", "eq"); imm32(1, PAT_SZ)
    a.label("cp_mo"); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 4); E(subs_reg, 1, 5, 0); E(b_cond, "cp_nx", "lo")    # r1 = the offset
    imm32(2, 8 * PAT_N); E(cmp_reg, 1, 2); E(b_cond, "cp_nx", "hs")
    E(movs_imm, 0, 0); imm32(2, PAT_N)
    a.label("cp_dv"); E(cmp_reg, 1, 2); E(b_cond, "cp_dd", "lo"); E(subs_reg, 1, 1, 2); E(adds_imm8, 0, 1); E(b, "cp_dv")
    a.label("cp_dd"); E(lsls_imm, 6, 6, 3); E(adds_reg, 6, 6, 0); E(b, "cp_src")       # r6 = the source block
    a.label("cp_nx"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 2); E(b_cond, "cp_m", "lo")
    a.label("cp_clr"); E(mov_reg, 0, 7); E(movs_imm, 1, 0); E(bl, "c_xlbit"); E(b, "cp_x")   # not from MIDI 1 / 2: no lanes
    a.label("cp_src")
    E(bl, "c_xlst"); E(mov_reg, 4, 0); E(ldrh_imm, 0, 4, O_MAP); E(raw, h(0x40F0))                     # lsrs r0, r6
    E(lsls_imm, 0, 0, 31); E(b_cond, "cp_clr", "pl")                                   # the source holds nothing
    E(ldrb_imm, 0, 4, O_QN); E(cmp_imm, 0, QMAX); E(b_cond, "cp_clr", "hs")            # the queue full: none (never stale lanes)
    E(lsls_imm, 1, 0, 1); E(adds_reg, 1, 1, 4); E(strb_imm, 6, 1, O_Q); E(strb_imm, 7, 1, O_Q + 1)
    E(adds_imm8, 0, 1); E(strb_imm, 0, 4, O_QN)
    E(mov_reg, 0, 7); E(movs_imm, 1, 1); E(bl, "c_xlbit")
    a.label("cp_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_xlclr (in place of the dispatcher's bl 0x0803D310: obj, pattern): the stock's clear, then no lanes in that block
    a.label("c_xlclr")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, CLEAR_FN)
    E(mov_reg, 0, 4); E(bl, "c_xlmb"); E(cmp_imm, 0, 0xFF); E(b_cond, "cl_x", "eq")
    E(mov_reg, 6, 0); E(lsls_imm, 0, 0, 3); E(movs_imm, 1, 7); E(ands_reg, 1, 5); E(adds_reg, 0, 0, 1); E(movs_imm, 1, 0); E(bl, "c_xlbit")
    E(mov_reg, 5, 0); E(bl, "c_xlst"); meta(1, 0); E(adds_reg, 1, 1, 6); E(ldrb_imm, 0, 1, 0); E(subs_imm8, 0, 1); E(cmp_reg, 0, 5)
    E(b_cond, "cl_x", "ne"); E(movs_imm, 0, 0); E(strb_imm, 0, 1, 0); E(strb_imm, 0, 1, 2)
    a.label("cl_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_xlsum() -> r0 = the sum of MIDI 1 / 2's patterns in the session record, as words; clobbers r1-r3
    a.label("c_xlsum")
    imm32(1, SESSION_OBJ + 0x14); E(ldr_imm, 1, 1, 0); imm32(2, PAT0); E(adds_reg, 1, 1, 2)
    imm32(2, PATLEN // 4); E(movs_imm, 0, 0)
    a.label("su_l"); E(ldr_imm, 3, 1, 0); E(adds_reg, 0, 0, 3); E(adds_imm8, 1, 4); E(subs_imm8, 2, 1); E(b_cond, "su_l", "ne")
    E(raw, h(0x4770))

    # ---- c_xlsv (in place of the bl at 0x0802FE5E: r0 = the session manager, r5 = the project slot, [manager + 0x60] p0 = the pack, as the
    #      stock's own item {2, r5, p0}): the chain, then the slot, the pack, the checksum noted (before use_svfix: the two swapped)
    a.label("c_xlsv")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 6, 5)
    E(bl, prev["save"])
    E(bl, "c_xlst"); E(mov_reg, 5, 0)
    E(ldr_imm, 0, 4, 0x60); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    if SVFIX:
        a.label("xs_fix"); E(strb_imm, 0, 5, O_SPK); E(strb_imm, 6, 5, O_SIDX)
    else:
        E(strb_imm, 0, 5, O_SIDX); E(strb_imm, 6, 5, O_SPK)
    E(bl, "c_xlsum"); E(str_imm, 0, 5, O_SSUM)
    E(ldrb_imm, 0, 5, O_FL); E(movs_imm, 1, F_SAVE); E(orrs_reg, 0, 1); E(strb_imm, 0, 5, O_FL)
    E(pop_list, [4, 5, 6], pc=True)

    # ---- c_xlld (the end of "apply session", 0x0802F5B8, the outermost head): the patterns' checksum, a load to do
    a.label("c_xlld")
    E(push_list, [0, 1, 2, 3, 4], lr=True)
    E(bl, "c_xlst"); E(mov_reg, 4, 0); E(bl, "c_xlsum"); E(str_imm, 0, 4, O_LSUM)
    E(ldrb_imm, 0, 4, O_FL); E(movs_imm, 1, F_LOAD); E(orrs_reg, 0, 1); E(strb_imm, 0, 4, O_FL); E(movs_imm, 0, 0); E(strb_imm, 0, 4, O_TRY)
    E(raw, popw([0, 1, 2, 3, 4], lr=True)); E(b_w, prev["load"])

    # ---- c_xlnew (the tail of "new project", 0x0802F5FA): no lanes
    a.label("c_xlnew")
    E(push_list, [0, 1, 2, 3, 4], lr=True)
    E(bl, "c_xlst"); E(ldrb_imm, 1, 0, O_FL); E(movs_imm, 2, F_NEW); E(orrs_reg, 1, 2); E(strb_imm, 1, 0, O_FL)
    E(raw, popw([0, 1, 2, 3, 4], lr=True)); E(b_w, prev["new"])

    # ---- c_xlled (the LED task's calls, the head): the work, then the chain with nothing on the stack
    a.label("c_xlled")
    E(push_list, [0, 1, 2, 3, 4, 5, 6], lr=True)
    E(bl, "c_xlwork")
    E(raw, popw([0, 1, 2, 3, 4, 5, 6], lr=True)); E(b_w, prev["ledtask"])

    # ---- c_xlwork(): what the hooks noted.  Frame r7 (40 B): [0] cb 0 [4] ctx 0 [8] &done [12] done [16..27] the item [28] off [32] k [36] status
    F = 40
    a.label("c_xlwork")
    E(push_list, [4, 5, 6, 7], lr=True); E(sub_sp_imm, F); E(mov_reg, 7, 13)
    E(bl, "c_xlst"); E(mov_reg, 4, 0)
    if EDITCACHE:                                                                       # stopped: the wanted blocks = the edited patterns
        imm32(0, REC_ON); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "ec_x", "ne")
        E(movs_imm, 5, 1)
        a.label("ec_l")
        imm32(0, PAT_OBJ + 2 * PAT_SZ + 0x24); E(movs_imm, 1, PAT_SZ >> 4); E(lsls_imm, 1, 1, 4); E(raw, h(0x4369)); E(adds_reg, 0, 0, 1)   # muls r1, r5
        E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(movs_imm, 1, 7); E(ands_reg, 0, 1)
        E(lsls_imm, 1, 5, 3); E(adds_reg, 0, 0, 1); E(adds_imm8, 0, 1); meta(1, 4); E(adds_reg, 1, 1, 5); E(strb_imm, 0, 1, 4)   # wanted = block + 1
        E(subs_imm8, 5, 1); E(b_cond, "ec_l", "pl")
        a.label("ec_x")
    E(ldrb_imm, 0, 4, O_FL); E(ldrb_imm, 1, 4, O_QN); E(orrs_reg, 1, 0)
    if RELOAD: E(ldrb_imm, 2, 4, O_RQ); E(orrs_reg, 1, 2)
    E(ldrh_imm, 2, 4, O_CM); E(ldrh_imm, 3, 4, O_CM + 4); E(raw, h(0x405A)); E(orrs_reg, 1, 2); bc("wk_x", "eq")   # eors r2, r3: wanted = cached?
    if ZLOOP: PK.zloop(a, 1, 7, F // 4, 2, 3, "_zwk")
    else:
        E(movs_imm, 1, 0)
        for o in range(0, F, 4): E(str_imm, 1, 7, o)
    E(mov_reg, 1, 7); E(adds_imm8, 1, 12); E(str_imm, 1, 7, 8)                       # &done
    E(movs_imm, 0, 0); E(bl, "c_xlflush"); E(movs_imm, 0, 1); E(bl, "c_xlflush")        # changed playing blocks back to the DSP first
    # the queued block copies (pattern pastes): BLKW words, NW at a time, DSP to DSP; a failed one leaves its destination empty
    E(movs_imm, 6, 0)
    a.label("wk_q")
    E(ldrb_imm, 0, 4, O_QN); E(cmp_reg, 6, 0); bc("wk_qe", "hs")
    E(lsls_imm, 0, 6, 1); E(adds_reg, 0, 0, 4); E(ldrb_imm, 1, 0, O_Q); E(ldrb_imm, 2, 0, O_Q + 1); E(str_imm, 2, 7, 36)
    imm32(3, BLKW); E(raw, h(0x4359)); imm32(0, XB); E(adds_reg, 1, 1, 0); E(str_imm, 1, 7, 28)      # muls r1, r3
    E(raw, h(0x435A)); E(adds_reg, 2, 2, 0); E(str_imm, 2, 7, 32)                                    # muls r2, r3
    E(movs_imm, 5, 0)
    a.label("wk_qc")
    imm32(0, BLKW); E(cmp_reg, 5, 0); E(b_cond, "wk_qn", "hs")
    E(subs_reg, 2, 0, 5); E(cmp_imm, 2, PK.NW); E(b_cond, "wk_qm", "ls"); E(movs_imm, 2, PK.NW)
    a.label("wk_qm"); E(str_imm, 2, 7, 12)
    E(ldr_imm, 0, 7, 28); E(adds_reg, 0, 0, 5); E(ldr_imm, 1, 7, 32); E(adds_reg, 1, 1, 5); E(bl, L["c_copy2"])
    E(cmp_imm, 0, 0); E(b_cond, "wk_qf", "ne")
    E(ldr_imm, 0, 7, 12); E(adds_reg, 5, 5, 0); E(b, "wk_qc")
    a.label("wk_qf"); E(ldr_imm, 0, 7, 36); E(movs_imm, 1, 0); E(bl, "c_xlbit")
    a.label("wk_qn")
    E(ldr_imm, 0, 7, 36); E(lsrs_imm, 1, 0, 3); meta(2, 4); E(adds_reg, 2, 2, 1); E(ldrb_imm, 3, 2, 0); E(subs_imm8, 3, 1)
    E(cmp_reg, 3, 0); E(b_cond, "wk_qi", "ne"); E(movs_imm, 3, 0); E(strb_imm, 3, 2, 0)                # the destination cached: read again
    a.label("wk_qi"); E(adds_imm8, 6, 1); E(b, "wk_q")
    a.label("wk_qe"); E(movs_imm, 0, 0); E(strb_imm, 0, 4, O_QN); E(str_imm, 0, 7, 12)
    E(ldrb_imm, 0, 4, O_FL)
    E(movs_imm, 1, F_NEW); E(ands_reg, 1, 0); E(b_cond, "wk_s", "eq")
    E(movs_imm, 1, 0); E(strh_imm, 1, 4, O_MAP); E(strh_imm, 1, 4, O_CM); E(strh_imm, 1, 4, O_CM + 2)   # a new project: no lanes, nothing cached
    if RELOAD: E(movs_imm, 1, 1); E(strb_w, 1, 4, O_NB)
    E(movs_imm, 1, F_NEW | F_LOAD); E(bics_reg, 0, 1); E(strb_imm, 0, 4, O_FL)
    a.label("wk_s")
    E(movs_imm, 1, F_SAVE); E(ands_reg, 1, 0); E(b_cond, "wk_l", "eq")
    E(b, "c_xlsave"); a.label("wk_svd")                                               # (inline: the stack top must stay the frame)
    E(ldrb_imm, 0, 4, O_FL); E(movs_imm, 1, F_SAVE); E(bics_reg, 0, 1); E(strb_imm, 0, 4, O_FL)
    if RELOAD: E(movs_imm, 0, 0); E(strb_w, 0, 4, O_NB)
    a.label("wk_l")
    E(ldrb_imm, 0, 4, O_FL); E(movs_imm, 1, F_LOAD); E(ands_reg, 1, 0); bc("wk_c", "eq")
    E(b, "c_xlload"); a.label("wk_ldr"); E(cmp_imm, 0, 0); E(b_cond, "wk_ld", "eq")
    E(ldrb_imm, 0, 4, O_TRY); E(adds_imm8, 0, 1); E(strb_imm, 0, 4, O_TRY); E(cmp_imm, 0, TRIES); bc("wk_x", "lo")
    E(movs_imm, 0, 0); E(strh_imm, 0, 4, O_MAP)                                      # given up: no lanes
    a.label("wk_ld")
    E(ldrb_imm, 0, 4, O_FL); E(movs_imm, 1, F_LOAD); E(bics_reg, 0, 1); E(strb_imm, 0, 4, O_FL)
    E(movs_imm, 0, 0); E(strh_imm, 0, 4, O_CM); E(strh_imm, 0, 4, O_CM + 2)          # loaded: nothing cached
    if RELOAD:
        E(strb_w, 0, 4, O_NB)
        a.label("wk_c")                                                                 # a block to read again (patrev)
        E(ldrb_imm, 0, 4, O_RQ); E(cmp_imm, 0, 0); E(b_cond, "wk_cc", "eq"); E(b_w, "c_xlrel")
        a.label("wk_cc")
    else:
        a.label("wk_c")                                                                 # the wanted blocks cached
    for m in (0, 1):
        meta(1, 4); E(ldrb_imm, 0, 1, m); E(ldrb_imm, 2, 1, 4 + m); E(cmp_reg, 0, 2); E(b_cond, f"wk_c{m}", "eq")
        E(movs_imm, 0, m); E(bl, "c_xlfill"); a.label(f"wk_c{m}")
    a.label("wk_x"); E(add_sp_imm, F); E(pop_list, [4, 5, 6, 7], pc=True)

    def item(idx_from, pack_from):
        """frame + 16 = {KIND_SES, idx, pack}: idx / pack from a register or a constant"""
        E(movs_imm, 0, KIND_SES); E(str_imm, 0, 7, 16); E(movs_imm, 0, 0); E(str_imm, 0, 7, 20); E(str_imm, 0, 7, 24)
        idx_from(); E(strb_imm, 0, 7, 20); pack_from(); E(strb_imm, 0, 7, 24)
    def iptr(rd): E(mov_reg, rd, 7); E(adds_imm8, rd, 16)
    def take(): E(mov_reg, 0, 4); E(adds_imm8, 0, O_HOLD); E(bl, L["c_take"])
    def give(): E(mov_reg, 0, 4); E(adds_imm8, 0, O_HOLD); E(bl, L["c_give"])

    # ---- c_xlsave (inline in c_xlwork; r4 = XLR, r7 = sp = the frame): the header, then the blocks when any holds data; no lanes and no tail: nothing
    a.label("c_xlsave")
    if SVFIX: E(ldrb_imm, 0, 4, O_SPK); E(cmp_imm, 0, 0); bc("sv_x", "eq")           # the internal pack: read-only for the mod, no tail
    item(lambda: E(ldrb_imm, 0, 4, O_SIDX), lambda: E(ldrb_imm, 0, 4, O_SPK))
    iptr(0); E(bl, PK.SIZE); E(mov_reg, 5, 0)
    E(ldrh_imm, 0, 4, O_MAP); E(cmp_imm, 0, 0); E(b_cond, "sv_go", "ne")
    imm32(1, SZ0); E(cmp_reg, 5, 1); bc("sv_x", "ls")                                 # no lanes, no tail: the stock's file only
    a.label("sv_go")
    E(movs_imm, 0, 5); E(bl, PK.BUF_LOCK)
    if ATOMIC:                                                                         # the header with bitmap 0 first, the real one last
        E(movs_imm, 1, 0); E(bl, "sv_hw"); E(cmp_imm, 0, 0); bc("sv_u", "ne")
    else:
        imm32(6, PK.BUF)
        imm32(0, MAGIC); E(str_imm, 0, 6, 0); E(movs_imm, 0, 1); E(strh_imm, 0, 6, 4); E(ldrh_imm, 0, 4, O_MAP); E(strh_imm, 0, 6, 6)
        E(ldr_imm, 0, 4, O_SSUM); E(str_imm, 0, 6, 8); imm32(0, DATA); E(str_imm, 0, 6, 12)
        iptr(0); imm32(1, SZ0); E(mov_reg, 2, 6); E(movs_imm, 3, HDR); E(bl, PK.WRITE); E(cmp_imm, 0, 0); bc("sv_u", "ne")
    E(ldrh_imm, 0, 4, O_MAP); E(cmp_imm, 0, 0); bc("sv_u", "eq")
    E(movs_imm, 0, 0); E(str_imm, 0, 7, 28)                                          # off
    a.label("sv_p")
    E(ldr_imm, 0, 7, 28); imm32(1, DATA); E(cmp_reg, 0, 1); bc("sv_h" if ATOMIC else "sv_u", "hs")
    E(subs_reg, 5, 1, 0); imm32(1, PK.BUFSZ); E(cmp_reg, 5, 1); E(b_cond, "sv_n", "ls"); E(mov_reg, 5, 1)
    a.label("sv_n")                                                                   # r5 = the piece's bytes
    E(movs_imm, 0, 0); E(str_imm, 0, 7, 32)                                          # k (words)
    a.label("sv_c")
    E(ldr_imm, 0, 7, 32); E(lsls_imm, 0, 0, 1); E(cmp_reg, 0, 5); bc("sv_w", "hs")
    E(subs_reg, 1, 5, 0); E(lsrs_imm, 1, 1, 1); E(cmp_imm, 1, PK.NW); E(b_cond, "sv_m", "ls"); E(movs_imm, 1, PK.NW)
    a.label("sv_m"); E(mov_reg, 6, 1)                                                 # r6 = m words
    E(ldr_imm, 0, 7, 28); E(lsrs_imm, 0, 0, 1); E(ldr_imm, 2, 7, 32); E(adds_reg, 0, 0, 2); imm32(2, XB); E(adds_reg, 0, 0, 2)
    E(mov_reg, 1, 6); E(bl, L["c_copy"]); E(cmp_imm, 0, 0); bc("sv_u", "ne")
    take()
    E(movs_imm, 0, 0); E(str_imm, 0, 7, 36)
    a.label("sv_r")
    E(ldr_imm, 2, 7, 36); E(cmp_reg, 2, 6); E(b_cond, "sv_rd", "hs")
    imm32(1, 0x8000 | PK.WIN); E(adds_reg, 1, 1, 2); E(movs_imm, 0, 0); E(bl, PK.DSP_READ); E(lsrs_imm, 0, 0, 16)
    E(ldr_imm, 1, 7, 32); E(ldr_imm, 2, 7, 36); E(adds_reg, 1, 1, 2); E(lsls_imm, 1, 1, 1); imm32(2, PK.BUF); E(strh_reg, 0, 2, 1)
    E(ldr_imm, 2, 7, 36); E(adds_imm8, 2, 1); E(str_imm, 2, 7, 36); E(b, "sv_r")
    a.label("sv_rd")
    give()
    E(ldr_imm, 0, 7, 32); E(adds_reg, 0, 0, 6); E(str_imm, 0, 7, 32); E(b, "sv_c")
    a.label("sv_w")
    iptr(0); E(ldr_imm, 1, 7, 28); imm32(2, SZ0 + HDR); E(adds_reg, 1, 1, 2); imm32(2, PK.BUF); E(mov_reg, 3, 5); E(bl, PK.WRITE)
    E(cmp_imm, 0, 0); bc("sv_u", "ne")
    E(ldr_imm, 0, 7, 28); E(adds_reg, 0, 0, 5); E(str_imm, 0, 7, 28); E(b, "sv_p")
    if ATOMIC:
        a.label("sv_h"); E(ldrh_imm, 1, 4, O_MAP); E(bl, "sv_hw")                      # every block written: the real header
    a.label("sv_u"); E(bl, PK.BUF_UNLOCK)
    a.label("sv_x"); E(b, "wk_svd")
    if ATOMIC:
        # ---- sv_hw(r1 = the bitmap) -> r0 = the write's status: the 16-byte header written at SZ0 (r4 = XLR, r7 = sp = the frame, the buffer
        #      locked; no push: the write reads its callback / context at [sp]); clobbers r0-r3, r5, r6
        a.label("sv_hw")
        E(mov_reg, 5, 14); imm32(6, PK.BUF); E(strh_imm, 1, 6, 6)
        imm32(0, MAGIC); E(str_imm, 0, 6, 0); E(movs_imm, 0, 1); E(strh_imm, 0, 6, 4)
        E(ldr_imm, 0, 4, O_SSUM); E(str_imm, 0, 6, 8); imm32(0, DATA); E(str_imm, 0, 6, 12)
        iptr(0); imm32(1, SZ0); E(mov_reg, 2, 6); E(movs_imm, 3, HDR); E(bl, PK.WRITE); E(raw, h(0x4728))   # bx r5

    # ---- c_xlload (inline in c_xlwork; r4 = XLR, r7 = sp = the frame) -> r0 = 0 done (the lanes or none), else a transfer failed (try again)
    a.label("c_xlload")
    def proj():
        imm32(0, PROJ_OBJ + 0x20); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 8); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    item(proj, lambda: E(movs_imm, 0, 0xFF))
    E(movs_imm, 0, 0); E(strh_imm, 0, 4, O_MAP)                                       # none until read
    iptr(0); E(bl, PK.SIZE); imm32(1, SZ0 + HDR + DATA); E(cmp_reg, 0, 1); bc("ld_0", "lo")
    E(movs_imm, 0, 5); E(bl, PK.BUF_LOCK)
    iptr(0); imm32(1, SZ0); imm32(2, PK.BUF); E(movs_imm, 3, HDR); E(bl, PK.READ); E(cmp_imm, 0, 0); bc("ld_f", "ne")
    imm32(6, PK.BUF)
    E(ldr_imm, 0, 6, 0); imm32(1, MAGIC); E(cmp_reg, 0, 1); bc("ld_u0", "ne")
    E(ldrh_imm, 0, 6, 4); E(cmp_imm, 0, 1); bc("ld_u0", "ne")
    E(ldr_imm, 0, 6, 12); imm32(1, DATA); E(cmp_reg, 0, 1); bc("ld_u0", "ne")
    E(ldr_imm, 0, 6, 8); E(ldr_imm, 1, 4, O_LSUM); E(cmp_reg, 0, 1); bc("ld_u0", "ne")
    E(ldrh_imm, 0, 6, 6); E(str_imm, 0, 7, 36)                                         # the bitmap, once the blocks are in
    E(cmp_imm, 0, 0); bc("ld_u0", "eq")
    E(movs_imm, 0, 0); E(str_imm, 0, 7, 28)
    a.label("ld_p")
    E(ldr_imm, 0, 7, 28); imm32(1, DATA); E(cmp_reg, 0, 1); bc("ld_ok", "hs")
    E(subs_reg, 5, 1, 0); imm32(1, PK.BUFSZ); E(cmp_reg, 5, 1); E(b_cond, "ld_n", "ls"); E(mov_reg, 5, 1)
    a.label("ld_n")
    iptr(0); E(ldr_imm, 1, 7, 28); imm32(2, SZ0 + HDR); E(adds_reg, 1, 1, 2); imm32(2, PK.BUF); E(mov_reg, 3, 5); E(bl, PK.READ)
    E(cmp_imm, 0, 0); bc("ld_f", "ne")
    E(movs_imm, 0, 0); E(str_imm, 0, 7, 32)
    a.label("ld_c")
    E(ldr_imm, 0, 7, 32); E(lsls_imm, 0, 0, 1); E(cmp_reg, 0, 5); bc("ld_nx", "hs")
    E(subs_reg, 1, 5, 0); E(lsrs_imm, 1, 1, 1); E(cmp_imm, 1, PK.NW); E(b_cond, "ld_m", "ls"); E(movs_imm, 1, PK.NW)
    a.label("ld_m"); E(mov_reg, 6, 1)
    take()
    E(ldr_imm, 0, 7, 32); E(lsls_imm, 0, 0, 1); imm32(1, PK.BUF); E(adds_reg, 0, 0, 1); E(mov_reg, 1, 6); E(bl, L["c_ywin"])
    give()
    imm32(0, PK.WIN); E(ldr_imm, 1, 7, 28); E(lsrs_imm, 1, 1, 1); E(ldr_imm, 2, 7, 32); E(adds_reg, 1, 1, 2); imm32(2, XB); E(adds_reg, 1, 1, 2)
    E(mov_reg, 2, 6); E(bl, L["c_copy2"]); E(cmp_imm, 0, 0); bc("ld_f", "ne")
    E(ldr_imm, 0, 7, 32); E(adds_reg, 0, 0, 6); E(str_imm, 0, 7, 32); E(b, "ld_c")
    a.label("ld_nx")
    E(ldr_imm, 0, 7, 28); E(adds_reg, 0, 0, 5); E(str_imm, 0, 7, 28); E(b, "ld_p")
    a.label("ld_ok"); E(ldr_imm, 0, 7, 36); E(strh_imm, 0, 4, O_MAP)
    a.label("ld_u0"); E(bl, PK.BUF_UNLOCK)
    a.label("ld_0"); E(movs_imm, 0, 0); E(b, "wk_ldr")
    a.label("ld_f"); E(bl, PK.BUF_UNLOCK); E(movs_imm, 0, 1); E(b, "wk_ldr")

    if RELOAD:
        # ---- c_xlrel (inline in c_xlwork; r4 = XLR, r7 = sp = the frame): block O_RQ - 1 read again from the loaded project's file
        a.label("c_xlrel")
        E(ldrb_imm, 6, 4, O_RQ); E(subs_imm8, 6, 1)                                     # r6 = the block
        item(proj, lambda: E(movs_imm, 0, 0xFF))
        iptr(0); E(bl, PK.SIZE); imm32(1, SZ0 + HDR + DATA); E(cmp_reg, 0, 1); bc("rl_e", "lo")
        E(movs_imm, 0, 5); E(bl, PK.BUF_LOCK)
        iptr(0); imm32(1, SZ0); imm32(2, PK.BUF); E(movs_imm, 3, HDR); E(bl, PK.READ); E(cmp_imm, 0, 0); bc("rl_f", "ne")
        imm32(5, PK.BUF)
        E(ldr_imm, 0, 5, 0); imm32(1, MAGIC); E(cmp_reg, 0, 1); bc("rl_u", "ne")
        E(ldrh_imm, 0, 5, 4); E(cmp_imm, 0, 1); bc("rl_u", "ne")
        E(ldr_imm, 0, 5, 12); imm32(1, DATA); E(cmp_reg, 0, 1); bc("rl_u", "ne")
        E(ldr_imm, 0, 5, 8); E(ldr_imm, 1, 4, O_LSUM); E(cmp_reg, 0, 1); E(b_cond, "rl_s", "eq")      # this project's file: as loaded
        E(ldr_imm, 1, 4, O_SSUM); E(cmp_reg, 0, 1); bc("rl_u", "ne")                                  # ... or as saved since
        a.label("rl_s")
        E(ldrh_imm, 0, 5, 6); E(movs_imm, 1, 1); E(raw, h(0x40B1)); E(raw, h(0x4208)); bc("rl_u", "eq")   # lsls r1, r6; tst r0, r1: no data
        iptr(0); imm32(1, BLK); E(raw, h(0x4371)); imm32(2, SZ0 + HDR); E(adds_reg, 1, 1, 2)          # muls r1, r6
        E(mov_reg, 2, 5); imm32(3, BLK); E(bl, PK.READ); E(cmp_imm, 0, 0); bc("rl_f", "ne")
        E(movs_imm, 5, 0)                                                                  # r5 = k (words)
        a.label("rl_c")
        imm32(0, BLKW); E(cmp_reg, 5, 0); bc("rl_ok", "hs")
        E(subs_reg, 1, 0, 5); E(cmp_imm, 1, PK.NW); E(b_cond, "rl_m", "ls"); E(movs_imm, 1, PK.NW)
        a.label("rl_m"); E(str_imm, 1, 7, 28)                                             # n
        take()
        E(lsls_imm, 0, 5, 1); imm32(1, PK.BUF); E(adds_reg, 0, 0, 1); E(ldr_imm, 1, 7, 28); E(bl, L["c_ywin"])
        give()
        imm32(1, BLKW); E(raw, h(0x4371)); E(adds_reg, 1, 1, 5); imm32(0, XB); E(adds_reg, 1, 1, 0)   # muls r1, r6
        imm32(0, PK.WIN); E(ldr_imm, 2, 7, 28); E(bl, L["c_copy2"]); E(cmp_imm, 0, 0); bc("rl_f", "ne")
        E(ldr_imm, 0, 7, 28); E(adds_reg, 5, 5, 0); E(b, "rl_c")
        a.label("rl_ok"); E(bl, PK.BUF_UNLOCK); E(movs_imm, 1, 1); E(b, "rl_b")
        a.label("rl_u"); E(bl, PK.BUF_UNLOCK)
        a.label("rl_e"); E(movs_imm, 1, 0)
        a.label("rl_b"); E(mov_reg, 0, 6); E(bl, "c_xlbit")
        E(lsrs_imm, 1, 6, 3); meta(2, 4); E(adds_reg, 2, 2, 1); E(ldrb_imm, 3, 2, 0); E(subs_imm8, 3, 1); E(cmp_reg, 3, 6); E(b_cond, "rl_d", "ne")
        E(movs_imm, 3, 0); E(strb_imm, 3, 2, 0); E(strb_imm, 3, 2, 2)                    # its cached copy dropped (cached, changed)
        a.label("rl_d"); E(movs_imm, 0, 0); E(strb_imm, 0, 4, O_RQ); E(strb_imm, 0, 4, O_TRY); E(b_w, "wk_cc")
        a.label("rl_f"); E(bl, PK.BUF_UNLOCK)
        E(ldrb_imm, 0, 4, O_TRY); E(adds_imm8, 0, 1); E(strb_imm, 0, 4, O_TRY); E(cmp_imm, 0, TRIES); bc("rl_e", "hs"); E(b_w, "wk_x")
    # ================================================================ the playing blocks: playback and recording from the ITCM

    # ---- c_xlcb(r0 = m) -> r0 = MIDI m's playing block in the ITCM; clobbers nothing else
    a.label("c_xlcb")
    E(cmp_imm, 0, 0); E(b_cond, "cb_1", "ne"); E(movs_imm, 0, IC0 >> 4); E(lsls_imm, 0, 0, 4); E(raw, h(0x4770))
    a.label("cb_1"); E(movs_imm, 0, (IC0 + ICS) >> 4); E(lsls_imm, 0, 0, 4); E(raw, h(0x4770))

    # ---- c_xlap(r0 = m, r1 = code, r2 = a lane value 0..127): the value set and sent out (vcf21's c_vapply without the lane)
    a.label("c_xlap")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(mov_reg, 0, 1); E(mov_reg, 1, 2); E(bl, L["c_vfromu"]); E(mov_reg, 6, 0)
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(mov_reg, 2, 6); E(bl, L["c_vstore"]); E(cmp_imm, 0, 0); E(b_cond, "xa_x", "eq")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(mov_reg, 2, 6); E(bl, L["c_vcc_emit"])
    a.label("xa_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_xlpl (the note players' slot 2, the head: this, pattern, step, micro step): MIDI 1 / 2 = the block wanted; at micro steps 0 and 3 its
    #      lanes played (codes without a stock lane only), then the chain
    a.label("c_xlpl")
    pushw10()
    imm32(1, PLAYER0 + 2 * PLAYER_SZ); E(movs_imm, 4, 0); E(cmp_reg, 0, 1); E(b_cond, "pl_m", "eq")
    imm32(1, PLAYER0 + 3 * PLAYER_SZ); E(movs_imm, 4, 1); E(cmp_reg, 0, 1); bc("pl_x", "ne")
    a.label("pl_m")                                                                     # r4 = m
    E(bl, "c_xlst"); E(mov_reg, 7, 0)
    E(raw, h(0x9801)); E(movs_imm, 1, 7); E(ands_reg, 0, 1); E(lsls_imm, 5, 4, 3); E(adds_reg, 5, 5, 0)   # ldr r0, [sp, #4]: r5 = the block
    meta(1, 7); E(adds_reg, 1, 1, 4); E(adds_imm8, 5, 1); E(strb_imm, 5, 1, 4); E(subs_imm8, 5, 1)          # wanted = block + 1
    if LATE:                                                                            # (Alpha 7.02) micro 0 / 3, or another one when a fill has just ended
        E(raw, h(0x9803)); E(movs_imm, 6, 1); E(cmp_imm, 0, 3); E(b_cond, "pl_c", "eq")       # ldr r0, [sp, #12]
        E(movs_imm, 6, 0); E(cmp_imm, 0, 0); E(b_cond, "pl_c", "eq")
        imm32(1, LATE_RAM); E(ldrb_reg, 2, 1, 4); E(cmp_imm, 2, 0); bc("pl_x", "eq")       # micro 1, 2: the first half; 4, 5: the second
        E(cmp_imm, 0, 3); E(b_cond, "pl_c", "ls"); E(movs_imm, 6, 1)
        a.label("pl_c"); imm32(1, LATE_RAM); E(movs_imm, 2, 0); E(strb_reg, 2, 1, 4)
    else:
        E(raw, h(0x9803)); E(movs_imm, 6, 0); E(cmp_imm, 0, 0); E(b_cond, "pl_h", "eq")                       # ldr r0, [sp, #12]: micro 0 / 3
        E(movs_imm, 6, 1); E(cmp_imm, 0, 3); bc("pl_x", "ne")
    a.label("pl_h")
    E(ldrh_imm, 0, 7, O_MAP); E(raw, h(0x40E8)); E(lsls_imm, 0, 0, 31); bc("pl_x", "pl")                  # lsrs r0, r5: no data in the block
    meta(1, 7); E(adds_reg, 1, 1, 4); E(ldrb_imm, 0, 1, 0); E(subs_imm8, 0, 1); E(cmp_reg, 0, 5); bc("pl_x", "ne")   # not cached yet
    E(mov_reg, 0, 4); E(bl, L["c_von"]); E(cmp_imm, 0, 0); bc("pl_x", "eq")
    E(raw, h(0x9802)); E(movs_imm, 1, 31); E(ands_reg, 0, 1); E(mov_reg, 7, 0)                                    # ldr r0, [sp, #8]: r7 = the step
    imm32(1, PAT_OBJ + 2 * PAT_SZ + 4); E(lsls_imm, 2, 4, 2); E(adds_reg, 1, 1, 2); E(ldr_imm, 1, 1, 0)          # the pattern's bytes (+ PAT_SZ m: muls)
    E(cmp_imm, 4, 0); E(b_cond, "pl_b0", "eq"); imm32(1, PAT_OBJ + 3 * PAT_SZ + 4); E(ldr_imm, 1, 1, 0)
    a.label("pl_b0"); E(movs_imm, 2, 7); E(ands_reg, 2, 5); imm32(3, PAT_N); E(raw, h(0x435A)); E(adds_reg, 1, 1, 2)   # muls r2, r3
    E(movs_imm, 2, 28); E(raw, h(0x437A)); E(adds_reg, 1, 1, 2); E(ldrb_imm, 1, 1, 3); E(lsls_imm, 1, 1, 24); bc("pl_x", "mi")   # muls r2, r7: released
    E(lsls_imm, 0, 7, 1); E(adds_reg, 6, 6, 0); E(adds_imm8, 6, VOFF)
    E(mov_reg, 0, 4); E(bl, "c_xlcb"); E(mov_reg, 5, 0); E(movs_imm, 7, 0)            # r5 = the block, r6 = the values' offset, r7 = the slot
    a.label("pl_l")
    E(ldrb_reg, 1, 5, 7); E(cmp_imm, 1, 0); E(b_cond, "pl_n", "eq")
    if ATOMIC: E(cmp_imm, 1, MAXCODE); E(b_cond, "pl_n", "hi")                         # (a damaged block: no code past the last)
    E(mov_reg, 0, 4); E(bl, L["c_vlane"]); E(cmp_imm, 0, 0xFF); E(b_cond, "pl_n", "ne")   # on a stock lane: that one plays
    E(lsls_imm, 2, 7, 6); E(adds_reg, 2, 2, 6); E(ldrb_reg, 2, 5, 2); E(cmp_imm, 2, 0xFF); E(b_cond, "pl_n", "eq")
    E(ldrb_reg, 1, 5, 7); E(mov_reg, 0, 4); E(bl, "c_xlap")
    a.label("pl_n"); E(adds_imm8, 7, 1); E(cmp_imm, 7, NSLOT); E(b_cond, "pl_l", "lo")
    a.label("pl_x"); popw10(); E(b_w, prev["play"])

    # ---- c_xlrec (vcf21's c_vcc_rec, the head: m, code, value): recording, a destination without a stock lane = its slot in the playing block
    #      (made when the block was empty); never the stock's / autolane's then
    a.label("c_xlrec")
    pushw10()
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(cmp_imm, 4, 1); bc("rc_p", "hi")
    for prm in (1, 0):
        imm32(0, REC_ON); E(movs_imm, 1, prm); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); bc("rc_p", "eq")
    imm32(0, L["t_dcode"]); E(movs_imm, 1, 0)
    a.label("rc_d"); E(ldrb_reg, 2, 0, 1); E(cmp_reg, 2, 5); E(b_cond, "rc_dk", "eq"); E(adds_imm8, 1, 1); E(cmp_imm, 1, L["nd"]); E(b_cond, "rc_d", "lo")
    E(b, "rc_p")
    a.label("rc_dk")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, L["c_vlane"]); E(cmp_imm, 0, 0xFF); bc("rc_p", "ne")
    E(sub_sp_imm, 16)                                                                  # ours from here: [0] half [4] step [8] block
    imm32(0, PLAYER0 + 2 * PLAYER_SZ + 0x10); E(cmp_imm, 4, 0); E(b_cond, "rc_pl", "eq"); imm32(0, PLAYER0 + 3 * PLAYER_SZ + 0x10)
    a.label("rc_pl"); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 1); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(cmp_imm, 0, 7); E(b_cond, "rc_r", "ls"); E(movs_imm, 0, 3)
    a.label("rc_r"); E(lsls_imm, 0, 0, 2); imm32(1, TICKS_TAB); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0); E(str_sp, 0, 0)   # [0] = ticks a step
    imm32(6, ENG + 0x38); E(lsls_imm, 0, 4, 2); E(adds_reg, 6, 6, 0); E(ldr_imm, 6, 6, 0)             # r6 = the store that plays
    E(mov_reg, 0, 6); E(movs_imm, 1, 2); E(bl, PK.PARAM_GET); E(ldr_imm, 0, 0, 0); E(lsls_imm, 0, 0, 1)
    E(ldr_sp, 1, 0); E(movs_imm, 2, 0); E(cmp_reg, 0, 1); E(b_cond, "rc_h", "lo"); E(movs_imm, 2, 1)
    a.label("rc_h"); E(str_sp, 2, 0)                                                              # [0] = the half
    E(mov_reg, 0, 6); E(movs_imm, 1, 1); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(movs_imm, 1, 31); E(ands_reg, 0, 1); E(str_sp, 0, 4)
    E(mov_reg, 0, 6); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(movs_imm, 1, 7); E(ands_reg, 0, 1)
    E(lsls_imm, 1, 4, 3); E(adds_reg, 0, 0, 1); E(str_sp, 0, 8)                                   # [8] = the block
    E(mov_reg, 0, 5); E(ldr_sp, 1, 16 + 8); E(bl, L["c_vtou"]); E(mov_reg, 2, 0)                  # the value (r2 at the entry) in lane units
    E(ldr_sp, 3, 4); E(lsls_imm, 3, 3, 1); E(ldr_sp, 0, 0); E(adds_reg, 3, 3, 0); E(lsls_imm, 3, 3, 8); E(ldr_sp, 0, 8); E(orrs_reg, 3, 0)
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_xlput")
    a.label("rc_x"); E(add_sp_imm, 16); popw10(); E(raw, h(0x4770))
    a.label("rc_p"); popw10(); E(b_w, prev["rec"])

    # ---- c_xlput(r0 = m, r1 = code, r2 = a lane value, r3 = block | (2 step + half) << 8): into the code's slot of the cached block (the block
    #      made when it held nothing; the first free slot for a new code; none free or the block not cached: nothing), the block changed
    a.label("c_xlput")
    E(push_list, [2, 3, 4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_xlst"); E(mov_reg, 7, 0); meta(1, 7); E(adds_reg, 1, 1, 4); E(ldrb_imm, 0, 1, 0); E(subs_imm8, 0, 1)
    E(ldr_sp, 1, 4); E(lsls_imm, 1, 1, 24); E(lsrs_imm, 1, 1, 24); E(cmp_reg, 0, 1); bc("pu_x", "ne")        # not cached: nothing
    E(mov_reg, 0, 4); E(bl, "c_xlcb"); E(mov_reg, 6, 0)                                                # r6 = the block
    E(ldrh_imm, 0, 7, O_MAP); E(ldr_sp, 1, 4); E(lsls_imm, 1, 1, 24); E(lsrs_imm, 1, 1, 24); E(raw, h(0x40C8)); E(lsls_imm, 0, 0, 31)   # lsrs r0, r1
    E(b_cond, "pu_s", "mi")
    if MEMFIX:                                                                          # (word-aligned destinations: the stock's memset uses stm)
        E(mov_reg, 0, 6); E(adds_imm8, 0, VOFF - 1); imm32(1, NSLOT * VSTEP + 1); E(movs_imm, 2, 0xFF); E(bl, PK.MEMSET)
        E(mov_reg, 0, 6); E(movs_imm, 1, NSLOT); E(movs_imm, 2, 0); E(bl, PK.MEMSET)                  # an empty block: made
    else:
        E(mov_reg, 0, 6); E(movs_imm, 1, NSLOT); E(movs_imm, 2, 0); E(bl, PK.MEMSET)                  # an empty block: made
        E(mov_reg, 0, 6); E(adds_imm8, 0, VOFF); imm32(1, NSLOT * VSTEP); E(movs_imm, 2, 0xFF); E(bl, PK.MEMSET)
    E(ldr_sp, 0, 4); E(lsls_imm, 0, 0, 24); E(lsrs_imm, 0, 0, 24); E(movs_imm, 1, 1); E(bl, "c_xlbit")
    a.label("pu_s")                                                                     # the slot: the code's, else the first free
    E(movs_imm, 7, 0); E(movs_imm, 3, 0xFF)
    a.label("pu_sl"); E(ldrb_reg, 0, 6, 7); E(cmp_reg, 0, 5); E(b_cond, "pu_sf", "eq")
    E(cmp_imm, 0, 0); E(b_cond, "pu_sn", "ne"); E(cmp_imm, 3, 0xFF); E(b_cond, "pu_sn", "ne"); E(mov_reg, 3, 7)
    a.label("pu_sn"); E(adds_imm8, 7, 1); E(cmp_imm, 7, NSLOT); E(b_cond, "pu_sl", "lo")
    E(cmp_imm, 3, 0xFF); bc("pu_x", "eq"); E(mov_reg, 7, 3); E(strb_reg, 5, 6, 7)                     # a free slot taken
    a.label("pu_sf")
    E(lsls_imm, 1, 7, 6); E(ldr_sp, 2, 4); E(lsrs_imm, 2, 2, 8); E(adds_reg, 1, 1, 2); E(adds_imm8, 1, VOFF)
    E(ldr_sp, 0, 0); E(strb_reg, 0, 6, 1)
    E(bl, "c_xlst"); meta(1, 0); E(adds_reg, 1, 1, 4); E(movs_imm, 0, 1); E(strb_imm, 0, 1, 2)      # changed
    a.label("pu_x"); E(pop_list, [2, 3, 4, 5, 6, 7], pc=True)

    # ---- c_xlsn (in place of recinst's "the first free lane" for a differing code without one: r4 = m, r1 = code, [sp] = the step): the value
    #      into the code's slot of the edited (cached) pattern, both halves of the step; then recinst's next code
    a.label("c_xlsn")
    E(push_list, [1, 5]); E(mov_reg, 5, 1)
    E(mov_reg, 0, 4); E(bl, L["c_vvaddr"]); E(movs_imm, 1, 0); E(raw, h(0x5641))                 # ldrsb r1, [r0, r1]: the value
    E(mov_reg, 0, 5); E(bl, L["c_vtou"]); E(mov_reg, 2, 0)
    imm32(0, PAT_OBJ + 2 * PAT_SZ + 0x24); E(cmp_imm, 4, 0); E(b_cond, "sn_o", "eq"); imm32(0, PAT_OBJ + 3 * PAT_SZ + 0x24)
    a.label("sn_o"); E(push_list, [2, 3]); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 3, 0, 0)
    E(movs_imm, 0, 7); E(ands_reg, 3, 0); E(lsls_imm, 0, 4, 3); E(adds_reg, 3, 3, 0)    # r3 = the block edited
    E(ldr_sp, 0, 16); E(lsls_imm, 0, 0, 9); E(orrs_reg, 3, 0); E(str_sp, 3, 4)          # + (2 step) << 8 ([sp + 16] = recinst's step)
    for half in (0, 1):
        E(ldr_sp, 2, 0); E(ldr_sp, 3, 4)
        if half: E(movs_imm, 0, 1); E(lsls_imm, 0, 0, 8); E(adds_reg, 3, 3, 0)
        E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_xlput")
    E(pop_list, [2, 3]); E(pop_list, [1, 5]); E(b_w, prev["ri_next"])

    # ---- c_xlnu (in place of playmode's bl c_pmnudge2: view, track, pattern, 0 back / 1 forward): the stock nudge, then the cached block's slots
    #      rotated the same way (first .. last by one)
    a.label("c_xlnu")
    E(push_list, [1, 2, 3, 4, 5, 6, 7], lr=True); E(bl, prev["nudge"])
    E(ldr_sp, 4, 0); E(subs_imm8, 4, 2); E(cmp_imm, 4, 1); bc("nu_x", "hi")            # r4 = m
    E(ldr_sp, 0, 0); E(ldr_sp, 1, 4); E(bl, L["c_pcrule"]); E(cmp_imm, 0, 0); bc("nu_x", "eq")
    E(subs_imm8, 0, 4); E(ldrb_imm, 5, 0, 1); E(ldrb_imm, 6, 0, 0); E(cmp_reg, 5, 6); bc("nu_x", "hs")  # r5 = first, r6 = last
    E(ldr_sp, 0, 4); E(movs_imm, 1, 7); E(ands_reg, 0, 1); E(lsls_imm, 1, 4, 3); E(adds_reg, 7, 0, 1)    # r7 = the block
    E(bl, "c_xlst"); meta(1, 0); E(adds_reg, 1, 1, 4); E(ldrb_imm, 0, 1, 0); E(subs_imm8, 0, 1); E(cmp_reg, 0, 7); bc("nu_x", "ne")
    E(movs_imm, 0, 1); E(strb_imm, 0, 1, 2)                                             # changed
    E(subs_reg, 6, 6, 5); E(adds_imm8, 6, 1)                                            # r6 = the count
    E(mov_reg, 0, 4); E(bl, "c_xlcb"); E(lsls_imm, 5, 5, 1); E(adds_reg, 5, 5, 0); E(adds_imm8, 5, VOFF)   # r5 = slot 0's first pair
    E(movs_imm, 7, 0)
    a.label("nu_l")
    E(mov_reg, 0, 5); E(movs_imm, 1, VPS); E(mov_reg, 2, 6); E(movs_imm, 3, 1); E(ldr_sp, 4, 8); E(cmp_imm, 4, 0)
    E(b_cond, "nu_k", "eq"); E(subs_imm8, 3, 1); E(adds_reg, 3, 3, 6); E(subs_imm8, 3, 1)  # forward: count - 1 to the left
    a.label("nu_k"); E(bl, L["c_pmrot"])
    E(adds_imm8, 5, VSTEP); E(adds_imm8, 7, 1); E(cmp_imm, 7, NSLOT); E(b_cond, "nu_l", "lo")
    a.label("nu_x"); E(pop_list, [1, 2, 3, 4, 5, 6, 7], pc=True)

    if MEMFIX:
        # ---- c_xlff(r0 = destination, r1 = n): n bytes of 0xFF, any alignment; clobbers r0-r2
        a.label("c_xlff")
        E(movs_imm, 2, 0xFF)
        a.label("ff_l"); E(cmp_imm, 1, 0); E(b_cond, "ff_x", "eq"); E(strb_imm, 2, 0, 0); E(adds_imm8, 0, 1); E(subs_imm8, 1, 1); E(b, "ff_l")
        a.label("ff_x"); E(raw, h(0x4770))

    # ---- c_xlca (vcf21's c_vclrauto, the head: macro handler, knob, m): the slots of the knob's two codes (plain, Shift) in the edited pattern,
    #      when it is cached, erased (code 0, the values 0xFF), the block changed; then the stock lanes as before
    a.label("c_xlca")
    pushw10()
    E(cmp_imm, 2, 1); bc("ca_p", "hi"); E(mov_reg, 4, 2); E(mov_reg, 6, 1)
    imm32(0, PAT_OBJ + 2 * PAT_SZ + 0x24); E(cmp_imm, 4, 0); E(b_cond, "ca_o", "eq"); imm32(0, PAT_OBJ + 3 * PAT_SZ + 0x24)
    a.label("ca_o"); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(movs_imm, 1, 7); E(ands_reg, 0, 1)
    E(lsls_imm, 5, 4, 3); E(adds_reg, 5, 5, 0)                                          # r5 = the block edited
    E(bl, "c_xlst")
    if MEMFIX: E(ldrh_imm, 1, 0, O_MAP); E(raw, h(0x40E9)); E(lsls_imm, 1, 1, 31); bc("ca_p", "pl")   # lsrs r1, r5: the block holds nothing
    meta(1, 0); E(adds_reg, 1, 1, 4); E(ldrb_imm, 0, 1, 0); E(subs_imm8, 0, 1); E(cmp_reg, 0, 5); bc("ca_p", "ne")
    E(mov_reg, 0, 4); E(bl, L["c_vpage"]); E(lsls_imm, 0, 0, 4); E(adds_reg, 6, 6, 0)   # r6 = page x 16 + knob
    E(mov_reg, 0, 4); E(bl, "c_xlcb"); E(mov_reg, 5, 0)                                 # r5 = the block
    for layer in (0, 8):
        E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(adds_imm8, 1, layer); E(bl, L["c_vkc"]); E(cmp_imm, 0, 0); E(b_cond, f"ca_n{layer}", "eq")
        E(movs_imm, 7, 0)
        a.label(f"ca_l{layer}"); E(ldrb_reg, 1, 5, 7); E(cmp_reg, 1, 0); E(b_cond, f"ca_f{layer}", "eq")
        E(adds_imm8, 7, 1); E(cmp_imm, 7, NSLOT); E(b_cond, f"ca_l{layer}", "lo"); E(b, f"ca_n{layer}")
        a.label(f"ca_f{layer}"); E(movs_imm, 1, 0); E(strb_reg, 1, 5, 7)
        E(lsls_imm, 0, 7, 6); E(adds_reg, 0, 0, 5); E(adds_imm8, 0, VOFF); E(movs_imm, 1, VSTEP); E(movs_imm, 2, 0xFF)
        E(bl, "c_xlff" if MEMFIX else PK.MEMSET)                                          # (odd: VOFF = 25)
        E(bl, "c_xlst"); meta(1, 0); E(adds_reg, 1, 1, 4); E(movs_imm, 0, 1); E(strb_imm, 0, 1, 2)
        a.label(f"ca_n{layer}")
    a.label("ca_p"); popw10()
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(b_w, L["c_vclrauto"] + 4)      # the displaced first instructions, then the rest

    # ---- c_xlflush(r0 = m) (in c_xlwork: r4 = XLR): a changed cached block back to the DSP; clobbers r0-r3
    a.label("c_xlflush")
    E(push_list, [5, 6, 7], lr=True); E(mov_reg, 5, 0)
    meta(6, 4); E(adds_reg, 6, 6, 5); E(ldrb_imm, 0, 6, 2); E(cmp_imm, 0, 0); E(b_cond, "fl_x", "eq")
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, 2)                                            # no longer changed
    E(ldrb_imm, 0, 6, 0); E(cmp_imm, 0, 0); E(b_cond, "fl_x", "eq")
    if FILLFIX: E(push_list, [6])                                                      # (meta + m: a failed copy marks it changed again)
    E(subs_imm8, 0, 1); imm32(1, BLKW); E(raw, h(0x4348)); imm32(1, XB); E(adds_reg, 7, 0, 1)         # muls r0, r1: r7 = the DSP's block
    E(mov_reg, 0, 5); E(bl, "c_xlcb"); E(mov_reg, 5, 0); E(movs_imm, 6, 0)                             # r5 = the cache, r6 = k
    a.label("fl_l")
    imm32(0, BLKW); E(cmp_reg, 6, 0); E(b_cond, "fl_e" if FILLFIX else "fl_x", "hs"); E(subs_reg, 1, 0, 6); E(cmp_imm, 1, PK.NW); E(b_cond, "fl_m", "ls"); E(movs_imm, 1, PK.NW)
    a.label("fl_m"); E(push_list, [1, 2])
    take(); E(lsls_imm, 0, 6, 1); E(adds_reg, 0, 0, 5); E(raw, h(0x9900)); E(bl, L["c_ywin"]); give()   # ldr r1, [sp]
    imm32(0, PK.WIN); E(adds_reg, 1, 7, 6); E(raw, h(0x9A00)); E(bl, L["c_copy2"])                       # ldr r2, [sp]
    if FILLFIX: E(cmp_imm, 0, 0); E(b_cond, "fl_f", "ne")
    E(pop_list, [1, 2]); E(adds_reg, 6, 6, 1); E(b, "fl_l")
    if FILLFIX:
        a.label("fl_f"); E(add_sp_imm, 8); E(pop_list, [6]); E(movs_imm, 0, 1); E(strb_imm, 0, 6, 2); E(b, "fl_x")   # changed again: the next frame
        a.label("fl_e"); E(add_sp_imm, 4)
    a.label("fl_x"); E(pop_list, [5, 6, 7], pc=True)

    # ---- c_xlfill(r0 = m) (in c_xlwork: r4 = XLR): the wanted block cached (read from the DSP when it holds data); clobbers r0-r3
    a.label("c_xlfill")
    E(push_list, [5, 6, 7], lr=True); E(mov_reg, 5, 0)
    if FILLFIX:                                                                          # cached = 0 while it fills: = the block once complete
        fx = "fi_ok"
        meta(6, 4); E(adds_reg, 6, 6, 5); E(ldrb_imm, 1, 6, 2); E(cmp_imm, 1, 0); E(b_cond, "fi_x", "ne")   # a block not written back yet: kept
        E(ldrb_imm, 0, 6, 4); E(strb_imm, 1, 6, 0); E(push_list, [0, 6])
    else:
        fx = "fi_x"
        meta(6, 4); E(adds_reg, 6, 6, 5); E(ldrb_imm, 0, 6, 4); E(strb_imm, 0, 6, 0); E(movs_imm, 1, 0); E(strb_imm, 1, 6, 2)
    E(cmp_imm, 0, 0); E(b_cond, fx, "eq")
    E(subs_imm8, 0, 1); E(ldrh_imm, 1, 4, O_MAP); E(raw, h(0x40C1)); E(lsls_imm, 1, 1, 31); E(b_cond, fx, "pl")   # lsrs r1, r0: no data
    imm32(1, BLKW); E(raw, h(0x4348)); imm32(1, XB); E(adds_reg, 7, 0, 1)
    E(mov_reg, 0, 5); E(bl, "c_xlcb"); E(mov_reg, 5, 0); E(movs_imm, 6, 0)
    a.label("fi_l")
    imm32(0, BLKW); E(cmp_reg, 6, 0); E(b_cond, fx, "hs"); E(subs_reg, 1, 0, 6); E(cmp_imm, 1, PK.NW); E(b_cond, "fi_m", "ls"); E(movs_imm, 1, PK.NW)
    a.label("fi_m"); E(push_list, [1, 2])
    E(adds_reg, 0, 7, 6); E(bl, L["c_copy"])
    if FILLFIX: E(cmp_imm, 0, 0); E(b_cond, "fi_f", "ne")
    take(); E(movs_imm, 0, 0); E(raw, h(0x9001))                                       # str r0, [sp, #4]: j
    a.label("fi_r")
    E(raw, h(0x9A01)); E(raw, h(0x9900)); E(cmp_reg, 2, 1); E(b_cond, "fi_rd", "hs")  # ldr r2, [sp, #4]; ldr r1, [sp]
    imm32(1, 0x8000 | PK.WIN); E(adds_reg, 1, 1, 2); E(movs_imm, 0, 0); E(bl, PK.DSP_READ); E(lsrs_imm, 0, 0, 16)
    E(raw, h(0x9A01)); E(adds_reg, 1, 6, 2); E(lsls_imm, 1, 1, 1); E(strh_reg, 0, 5, 1); E(adds_imm8, 2, 1); E(raw, h(0x9201))   # str r2, [sp, #4]
    E(b, "fi_r")
    a.label("fi_rd"); give(); E(pop_list, [1, 2]); E(adds_reg, 6, 6, 1); E(b, "fi_l")
    if FILLFIX:
        a.label("fi_f"); E(add_sp_imm, 16); E(b, "fi_x")                                # a failed copy: still not cached, the next frame
        a.label("fi_ok"); E(pop_list, [0, 6]); E(strb_imm, 0, 6, 0)                     # cached = the block filled
        assert not LATE or FILLFIX
        if LATE: E(movw, 1, (LATE_RAM - XLR - O_CM) & 0xFFFF); E(adds_reg, 1, 1, 6); E(strb_imm, 0, 1, 0)   # (Alpha 7.02) LATE_RAM + m = played late
    a.label("fi_x"); E(pop_list, [5, 6, 7], pc=True)

    # ================================================================ Components (its file protocol, a session of a pack 1..31)
    # frame r7 (40 B, at sp: the READ's cb / ctx / &done): [0] 0 [4] 0 [8] &done [12] done [16..27] the item [28] off [32] k [36] sum
    def frame_in():
        E(push_list, [4, 5, 6, 7], lr=True); E(sub_sp_imm, F); E(mov_reg, 7, 13)
        if ZLOOP: PK.zloop(a, 1, 7, F // 4, 2, 3, f"_zfi{frame_in.n}"); frame_in.n += 1
        else:
            E(movs_imm, 1, 0)
            for o in range(0, F, 4): E(str_imm, 1, 7, o)
        E(mov_reg, 1, 7); E(adds_imm8, 1, 12); E(str_imm, 1, 7, 8)
    frame_in.n = 0
    def frame_out(): E(add_sp_imm, F); E(pop_list, [4, 5, 6, 7], pc=True)
    def rd(off_fn, n_reg, fail):                                                       # READ(the item, off, TB, n) -> fail on an error
        iptr(0); off_fn(); imm32(2, TB); E(mov_reg, 3, n_reg); E(bl, PK.READ); E(cmp_imm, 0, 0); bc(fail, "ne")
    def piece(fail_to, done_to, total):                                                # r5 = min(TBN, total - [28]) -> done_to when nothing is left
        E(ldr_imm, 0, 7, 28); imm32(1, total); E(cmp_reg, 0, 1); bc(done_to, "hs")
        E(subs_reg, 5, 1, 0); imm32(1, TBN); E(cmp_reg, 5, 1); zc[0] += 1; n_ = f"_pz{zc[0]}"; E(b_cond, n_, "ls"); E(mov_reg, 5, 1); a.label(n_)

    # ---- c_xlhold(r0 = an item of the API): a session of a pack 1..31 with a tail: its header kept in XLR and its blocks in the DSP (XH)
    a.label("c_xlhold")
    frame_in(); E(mov_reg, 6, 0)
    E(bl, "c_xlst"); E(mov_reg, 4, 0); E(movs_imm, 0, 0); E(strb_imm, 0, 4, O_HV)
    E(ldr_imm, 0, 6, 0); E(cmp_imm, 0, KIND_SES); bc("ho_x", "ne")
    E(ldr_imm, 1, 6, 4); E(cmp_imm, 1, 64); bc("ho_x", "hs")
    E(ldrb_imm, 2, 6, 8); E(cmp_imm, 2, 0); bc("ho_x", "eq"); E(cmp_imm, 2, 32); bc("ho_x", "hs")
    E(str_imm, 0, 7, 16); E(str_imm, 1, 7, 20); E(movs_imm, 3, 0); E(str_imm, 3, 7, 24); E(strb_imm, 2, 7, 24)
    E(lsls_imm, 3, 1, 8); E(orrs_reg, 3, 2); E(strh_imm, 3, 4, O_HPS)
    iptr(0); E(bl, PK.SIZE); imm32(1, SZ0 + HDR + DATA); E(cmp_reg, 0, 1); bc("ho_r", "lo")
    E(movs_imm, 5, HDR); rd(lambda: imm32(1, SZ0), 5, "ho_r")
    imm32(0, TB); E(ldr_imm, 1, 0, 0); imm32(2, MAGIC); E(cmp_reg, 1, 2); bc("ho_r", "ne")
    E(ldr_imm, 1, 0, 12); imm32(2, DATA); E(cmp_reg, 1, 2); bc("ho_r", "ne")
    for o in range(0, HDR, 4): E(ldr_imm, 1, 0, o); E(str_imm, 1, 4, O_HHDR + o)
    E(movs_imm, 0, 0); E(str_imm, 0, 7, 28)
    a.label("ho_p")
    piece("ho_r", "ho_ok", DATA)
    rd(lambda: (E(ldr_imm, 1, 7, 28), imm32(2, SZ0 + HDR), E(adds_reg, 1, 1, 2)), 5, "ho_r")
    E(movs_imm, 0, 0); E(str_imm, 0, 7, 32)
    a.label("ho_c")
    E(ldr_imm, 0, 7, 32); E(lsls_imm, 0, 0, 1); E(cmp_reg, 0, 5); bc("ho_n", "hs")
    E(subs_reg, 1, 5, 0); E(lsrs_imm, 1, 1, 1); E(cmp_imm, 1, PK.NW); E(b_cond, "ho_m", "ls"); E(movs_imm, 1, PK.NW)
    a.label("ho_m"); E(mov_reg, 6, 1)
    take(); E(ldr_imm, 0, 7, 32); E(lsls_imm, 0, 0, 1); imm32(1, TB); E(adds_reg, 0, 0, 1); E(mov_reg, 1, 6); E(bl, L["c_ywin"]); give()
    imm32(0, PK.WIN); E(ldr_imm, 1, 7, 28); E(lsrs_imm, 1, 1, 1); E(ldr_imm, 2, 7, 32); E(adds_reg, 1, 1, 2); imm32(2, XH); E(adds_reg, 1, 1, 2)
    E(mov_reg, 2, 6); E(bl, L["c_copy2"]); E(cmp_imm, 0, 0); bc("ho_r", "ne")
    E(ldr_imm, 0, 7, 32); E(adds_reg, 0, 0, 6); E(str_imm, 0, 7, 32); E(b, "ho_c")
    a.label("ho_n"); E(ldr_imm, 0, 7, 28); E(adds_reg, 0, 0, 5); E(str_imm, 0, 7, 28); E(b, "ho_p")
    a.label("ho_ok"); E(movs_imm, 0, 1); E(strb_imm, 0, 4, O_HV)
    a.label("ho_r"); E(bl, L["c_curpack"]); E(bl, L["c_resel"])
    a.label("ho_x"); frame_out()

    # ---- c_xlback(): the held tail written back to the session Components just wrote, when the new file has none and its patterns are the same
    a.label("c_xlback")
    frame_in()
    E(bl, "c_xlst"); E(mov_reg, 4, 0)
    E(movs_imm, 0, KIND_SES); E(str_imm, 0, 7, 16); E(ldrh_imm, 0, 4, O_HPS); E(lsrs_imm, 1, 0, 8); E(str_imm, 1, 7, 20)
    E(movs_imm, 1, 0); E(str_imm, 1, 7, 24); E(strb_imm, 0, 7, 24)
    iptr(0); E(bl, PK.SIZE); imm32(1, SZ0); E(cmp_reg, 0, 1); bc("bk_r", "ne")          # the host wrote a tail of its own (or another size): it wins
    imm32(0, PAT0); E(str_imm, 0, 7, 28); E(movs_imm, 0, 0); E(str_imm, 0, 7, 36)
    a.label("bk_s")                                                                    # the patterns' checksum, from the file
    piece("bk_r", "bk_sd", PAT0 + PATLEN)
    rd(lambda: E(ldr_imm, 1, 7, 28), 5, "bk_r")
    imm32(1, TB); E(movs_imm, 2, 0); E(ldr_imm, 0, 7, 36)
    a.label("bk_sl"); E(ldr_imm, 3, 1, 0); E(adds_reg, 0, 0, 3); E(adds_imm8, 1, 4); E(adds_imm8, 2, 4); E(cmp_reg, 2, 5); E(b_cond, "bk_sl", "lo")
    E(str_imm, 0, 7, 36); E(ldr_imm, 0, 7, 28); E(adds_reg, 0, 0, 5); E(str_imm, 0, 7, 28); E(b, "bk_s")
    a.label("bk_sd")
    E(ldr_imm, 0, 7, 36); E(ldr_imm, 1, 4, O_HHDR + 8); E(cmp_reg, 0, 1); bc("bk_r", "ne")     # another project: the held lanes dropped
    imm32(2, TB)
    for o in range(0, HDR, 4): E(ldr_imm, 0, 4, O_HHDR + o); E(str_imm, 0, 2, o)
    iptr(0); imm32(1, SZ0); E(movs_imm, 3, HDR); E(bl, PK.WRITE); E(cmp_imm, 0, 0); bc("bk_r", "ne")
    E(movs_imm, 0, 0); E(str_imm, 0, 7, 28)
    a.label("bk_p")
    piece("bk_r", "bk_r", DATA)
    E(movs_imm, 0, 0); E(str_imm, 0, 7, 32)
    a.label("bk_c")
    E(ldr_imm, 0, 7, 32); E(lsls_imm, 0, 0, 1); E(cmp_reg, 0, 5); bc("bk_w", "hs")
    E(subs_reg, 1, 5, 0); E(lsrs_imm, 1, 1, 1); E(cmp_imm, 1, PK.NW); E(b_cond, "bk_m", "ls"); E(movs_imm, 1, PK.NW)
    a.label("bk_m"); E(mov_reg, 6, 1)
    E(ldr_imm, 0, 7, 28); E(lsrs_imm, 0, 0, 1); E(ldr_imm, 2, 7, 32); E(adds_reg, 0, 0, 2); imm32(2, XH); E(adds_reg, 0, 0, 2)
    E(mov_reg, 1, 6); E(bl, L["c_copy"]); E(cmp_imm, 0, 0); bc("bk_r", "ne")
    take(); E(movs_imm, 0, 0); E(str_imm, 0, 7, 36)
    a.label("bk_rl")
    E(ldr_imm, 2, 7, 36); E(cmp_reg, 2, 6); E(b_cond, "bk_rd", "hs")
    imm32(1, 0x8000 | PK.WIN); E(adds_reg, 1, 1, 2); E(movs_imm, 0, 0); E(bl, PK.DSP_READ); E(lsrs_imm, 0, 0, 16)
    E(ldr_imm, 1, 7, 32); E(ldr_imm, 2, 7, 36); E(adds_reg, 1, 1, 2); E(lsls_imm, 1, 1, 1); imm32(2, TB); E(strh_reg, 0, 2, 1)
    E(ldr_imm, 2, 7, 36); E(adds_imm8, 2, 1); E(str_imm, 2, 7, 36); E(b, "bk_rl")
    a.label("bk_rd"); give()
    E(ldr_imm, 0, 7, 32); E(adds_reg, 0, 0, 6); E(str_imm, 0, 7, 32); E(b, "bk_c")
    a.label("bk_w")
    iptr(0); E(ldr_imm, 1, 7, 28); imm32(2, SZ0 + HDR); E(adds_reg, 1, 1, 2); imm32(2, TB); E(mov_reg, 3, 5); E(bl, PK.WRITE)
    E(cmp_imm, 0, 0); bc("bk_r", "ne")
    E(ldr_imm, 0, 7, 28); E(adds_reg, 0, 0, 5); E(str_imm, 0, 7, 28); E(b, "bk_p")
    a.label("bk_r"); E(bl, L["c_curpack"]); E(bl, L["c_resel"]); frame_out()

    # ---- c_xlds (the delete at the start of a Components write, the head: r0 = the item, r1 = r2 = 0): a session's tail held, then the chain
    a.label("c_xlds")
    E(raw, h(0xE92D) + h(0x407F)); E(bl, "c_xlhold"); E(raw, popw([0, 1, 2, 3, 4, 5, 6], lr=True)); E(b_w, prev["cdel"])   # push.w {r0-r6, lr}
    # ---- c_xlce (the bl to the end of a Components write: r0 = the protocol object): the chain, then a held tail of that session written back
    a.label("c_xlce")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, prev["cend"])
    E(push_list, [0, 1]); E(bl, "c_xlst"); E(ldrb_imm, 1, 0, O_HV); E(cmp_imm, 1, 0); E(b_cond, "ce_x", "eq")
    E(ldrb_imm, 1, 4, 0x1C); E(cmp_imm, 1, T_SES); E(b_cond, "ce_x", "ne")
    E(ldrh_imm, 3, 0, O_HPS); E(ldrb_imm, 1, 4, 0x1D); E(movs_imm, 2, 0xFF); E(ands_reg, 2, 3); E(cmp_reg, 1, 2); E(b_cond, "ce_x", "ne")
    E(ldrb_imm, 1, 4, 0x1E); E(lsrs_imm, 2, 3, 8); E(cmp_reg, 1, 2); E(b_cond, "ce_x", "ne")
    E(movs_imm, 1, 0); E(strb_imm, 1, 0, O_HV); E(bl, "c_xlback")
    a.label("ce_x"); E(pop_list, [0, 1]); E(pop_list, [4], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Appended at the end (dspz.add moves it into the gap); heads: the save call, the load end, the new-project tail, the LED task's calls;
    the Projects view's session check."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("packio", k) for k in ("c_take", "c_give", "c_copy", "c_copy2", "c_ywin", "c_curpack", "c_resel")}
    L.update({k: lab("vcf20", k) for k in ("c_vfromu", "c_vstore", "c_vcc_emit", "c_vlane", "c_von", "c_vtou", "c_vcc_rec", "c_vclrauto", "c_vkc", "c_vpage")})
    L["c_vvaddr"] = lab("vcf20", "c_vvaddr"); L["c_pcrule"] = lab("patchain", "c_pcrule"); L["c_pmrot"] = lab("playmode", "c_pmrot")
    L["t_dcode"] = lab("modmx", "t_dcode"); L["nd"] = int(report["modmx"]["prev"]["pmax"], 16) // __import__("modmx").ZONE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    prev = dict(save=FD.bl_target(img, P19.SAVE_CALL, BASE), load=MP.bw_target(img, P19.LOAD_END, BASE), new=MP.bw_target(img, P19.NEW_TAIL, BASE),
                ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE), cdel=FD.bl_target(img, START_DEL, BASE), cend=FD.bl_target(img, END_CALL, BASE),
                play=u(PLAYER_VT + 8) & ~1, rec=MP.bw_target(img, L["c_vcc_rec"], BASE),
                nudge=lab("playmode", "c_pmnudge2"), ri_next=lab("recinst", "in_n"))
    code, labels = arm_code(base_addr, L, prev)
    img += code
    while len(img) % 4:
        img += bytes([0xFF])
    img[P19.SAVE_CALL - BASE:P19.SAVE_CALL - BASE + 4] = bl(P19.SAVE_CALL, labels["c_xlsv"])
    img[P19.LOAD_END - BASE:P19.LOAD_END - BASE + 4] = b_w(P19.LOAD_END, labels["c_xlld"])
    img[P19.NEW_TAIL - BASE:P19.NEW_TAIL - BASE + 4] = b_w(P19.NEW_TAIL, labels["c_xlnew"])
    for c in PK.LED_CALLS:
        assert FD.bl_target(img, c, BASE) == prev["ledtask"], hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_xlled"])
    for at, fn, ours in ((COPY_AT, COPY_FN, "c_xlcp"), (CLEAR_AT, CLEAR_FN, "c_xlclr")):
        assert FD.bl_target(img, at, BASE) == fn, hex(at)
        img[at - BASE:at - BASE + 4] = bl(at, labels[ours])
    img[START_DEL - BASE:START_DEL - BASE + 4] = bl(START_DEL, labels["c_xlds"])
    struct.pack_into("<I", img, PLAYER_VT + 8 - BASE, labels["c_xlpl"] | 1)
    img[L["c_vcc_rec"] - BASE:L["c_vcc_rec"] - BASE + 4] = b_w(L["c_vcc_rec"], labels["c_xlrec"])
    inf = lab("recinst", "in_f")
    assert bytes(img[inf - BASE:inf - BASE + 4]) == movs_imm(3, 1) + h(0x4093), img[inf - BASE:inf - BASE + 4].hex()   # movs r3, #1; lsls r3, r2
    img[inf - BASE:inf - BASE + 4] = b_w(inf, labels["c_xlsn"])
    sites = [o + BASE for o in range(0, len(img) - 4, 2) if o + BASE != prev["nudge"] and bl_to(img, o + BASE, BASE) == prev["nudge"]]
    assert 1 <= len(sites) <= 2, [hex(x) for x in sites]
    for at in sites: img[at - BASE:at - BASE + 4] = bl(at, labels["c_xlnu"])
    ca = L["c_vclrauto"]
    assert bytes(img[ca - BASE:ca - BASE + 4]) == push_list([4, 5, 6, 7], lr=True) + mov_reg(4, 0), img[ca - BASE:ca - BASE + 4].hex()
    img[ca - BASE:ca - BASE + 4] = b_w(ca, labels["c_xlca"])
    img[END_CALL - BASE:END_CALL - BASE + 4] = bl(END_CALL, labels["c_xlce"])
    assert bytes(img[VALID_AT - BASE:VALID_AT - BASE + 10]) == VALID_OLD, img[VALID_AT - BASE:VALID_AT - BASE + 10].hex()
    img[VALID_AT - BASE:VALID_AT - BASE + 10] = valid_new()
    return labels, code, prev
