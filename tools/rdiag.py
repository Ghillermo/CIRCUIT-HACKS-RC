"""SC35D8 (DIAGNOSTIC): remote diagnostics over USB SysEx, driven from the PC (tools/ctremote.py), no pad presses and no external MIDI monitor.

Hook: the incoming SysEx dispatcher 0x0801EB30(port, msg = {buf, len}, x) (called through a pointer; it offers each incoming SysEx to the Novation handlers and
the identity responder 0x0801EC54).  Its first 4 bytes (push.w {r4-r8, lr}) become `b.w c_rdin`: a message that starts with SIG (F0 7D 43 54: 7D = the
non-commercial manufacturer id, no stock handler answers it) is ours; anything else runs the original prologue and goes on at 0x0801EB34.

Request  F0 7D 43 54 cmd seq payload.. F7      Reply  F0 7D 43 54 cmd|0x40 seq payload.. F7 (sent to the same port through the stock SysEx output router
0x08020C90, as the identity responder does; a request shorter than PAD - 4 bytes is swallowed without a reply, so nothing is written past the buffer)
Numbers travel as 8 nibbles (u32, big-endian), bytes as 2 nibbles.  The reply is built IN the request buffer (owned by the caller during the call): the PC pads
every request to PAD bytes, so no RAM and little stack is needed.  Commands (status 0 = done):
  1 ping                                  -> VERSION, port
  2 mem   addr32 len(1 byte, <= NMAX)     -> status (1 = outside flash 0x08000000-0x0807FFFF / RAM 0x20000000-0x2004FFFF), the bytes
  4 info  kind idx pack                   -> exists (op 0), size (op 1)                       (the stock content API of the storage task, synchronous, the
  5 read  kind idx pack off32 len         -> status, done, the bytes (op 6)                    way Components' SysEx file transfer calls it from this task)
  6 write kind idx pack off32 len data    -> status (op 7; data = len bytes)                   -- writes to the SD card: used only with the user's go-ahead
  7 del   kind idx pack                   -> status (op 5, kinds 2-6 only; SC35D9, rdiag.DELETE) -- deletes a file of the pack: only with the user's go-ahead
  3 dspr  space(0 X / 1 Y) addr32 n       -> status, n words (6 nibbles; n <= NR; SC342D, rdiag.DSPX)
  8 dspx  src32 n                         -> status (3 = a copy busy, 4 = timeout), n samples (4 nibbles = bits 23..8; n <= NX; SC342D)
Kinds: 2 Sessions, 3 Patches, 4 PCM, 5 meta, 6 the effects folder; pack 0x7F = the current one (sent as 0xFF to the API).

WATCH (SEQWD, 2026-10-12: which code reads a step of a pattern while the sequencer plays?  The emulation never runs the note playback):
 10 watch addr32 func mask                -> status (2 = no state block), DWT_CTRL, DEMCR, DWT_FUNCTION0, the log's address.  The DWT data watchpoint 0
                                             (Cortex-M7: unlock LAR, COMP0 = addr, MASK0 = mask (address bits ignored), FUNCTION0 = func: 0 off,
                                             5 read, 6 write, 7 both) with DEMCR.TRCENA | MON_EN: a matching access raises the DebugMonitor exception
                                             (no debugger attached); the log is cleared
 11 poke  addr32 n data                   -> status (1 = outside RAM 0x20000000-0x2004FFFF): writes n (<= NMAX) bytes of RAM
 12 wlog                                  -> status, hits, 8 x (PC, LR): the distinct code addresses that touched the watched address
c_dmon (vector 12 of the app's table, DebugMonitor): the stacked PC / LR of the access (a data watchpoint stops a few instructions later: the PC is
in the function that read) into the log, the first 8 distinct PCs; DFSR.DWTTRAP cleared, FUNCTION0 read (clears MATCHED).  The log lives in the
Master FX block's idle LED buffer (c_gst() + LOG_OFF, after the 16 bytes of packio's PMODE cache): no new RAM; Master FX shown repaints it.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, ldrb_reg, lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw,  # noqa: E402
                   adds_imm8, subs_imm8, pop_list, push_list, raw, h, ands_reg, adds_reg, subs_reg, str_imm, strb_imm, strb_reg, add_sp_imm, sub_sp_imm,
                   orrs_reg, tst_reg)

HOOK = 0x0801EB30
HOOK_CONT = HOOK + 4
PROLOGUE = bytes.fromhex("2de9f041")             # push.w {r4, r5, r6, r7, r8, lr}
ROUTER = 0x08020C90                              # the stock SysEx output (router, port mask, &{buf, len}), as the identity responder 0x0801EC54 calls it
ROUTER_LIT = 0x0801EDD0                          # word that holds the address of the router pointer (0x0801EC66: ldr r0, [pc, #0x168]; ldr r0, [r0])
EXISTS, SIZE, READ, WRITE = 0x0803CB50, 0x0803CB6A, 0x0803CBF0, 0x0803CC16
DELETE = False                                   # SC35D9: command 7 = delete an item (op 5, 0x0803CC34(item, 0, 0) synchronous); kinds 2-6 only (kind 1 = a whole pack:
DEL_FN = 0x0803CC34                              #   refused with status 0xFFFFFFFE); the storage task closes the file, unlinks it and re-indexes the pack
DEL_PACK = False                                 # SC35DA: command 7 with kind 1 = delete a whole pack (op 5 kind 1), only an explicit pack != the current one
CUR_PACK_PTR = 0x20006914                        #   ([[CUR_PACK_PTR]] = the storage's current pack, numbered as the API: folder + 1); afterwards EXISTS on PCM 0
                                                 #   of the current pack re-selects it (op 5 kind 1 leaves the storage's current pack at 0xFF).  Reply: status, exists, cur
DSPW = False                                     # SC35DB: command 9 = write one DSP X word (addr32, value32) under the DSP service semaphore
DSPX = False                                     # SC342D: command 3 = DSP internal words (X / Y), command 8 = a chunk of the DSP's external Y memory through the
DSP_READ, DSP_WRITE = 0x08029344, 0x080292F8     #   sampler's own block copy (sampler_dsp V34: CPSRC / CPDST / CPLEN): CPSRC = source, CPDST = WIN, CPLEN = n; the next
SEM_PTR = 0x2000030C                             #   audio block copies it; the host port is used with the DSP service semaphore [[SEM_PTR] + 0xC] taken
SEM_TAKE, SEM_GIVE = 0x08021064, 0x08029028      #   (0x08021064(sem) / 0x08029028(&holder), as MARK_DIRTY does)
SLEEP = 0x0801BE78
WIN = 0x3B40                                     # Y window (SC34.2: no reference to Y:$3B40-$3B7F)
NX = 48                                          # samples per chunk (4 nibbles each: bits 23..8 of the word)
NR = 24                                          # internal words per command 3 (6 nibbles each)
SIG = (0xF0, 0x7D, 0x43, 0x54)
VERSION = 0x35D8
NMAX = 64
RAW = 160                                        # offset of the raw byte area in the request buffer (read / write)
PAD = 232                                        # every request is padded to this length (>= RAW + NMAX + some slack)
WATCH = False                                    # SEQWD: commands 10-12 + the DebugMonitor handler (see above)
LOG_OFF, LOG_N = 40 + 64 + 16, 8                 # c_gst() + LOG_OFF: hits, then LOG_N x (PC, LR) = 68 bytes, the end of Master FX's 84-byte LED buffer
VEC_DEBUGMON = 0x08010000 + 4 * 12               # the app's vector table (VTOR = 0x08010000): DebugMonitor
DEMCR, DFSR, DWT_CTRL, DWT_LAR, DWT_COMP0 = 0xE000EDFC, 0xE000ED30, 0xE0001000, 0xE0001FB0, 0xE0001020
GST = None                                       # c_gst (set by install from the report)
FLASH = (0x08000000, 0x08080000)
RAM = (0x20000000, 0x20050000)
INV = {"eq": "ne", "ne": "eq", "lo": "hs", "hs": "lo", "hi": "ls", "ls": "hi"}


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, router_ptr):
    a = Asm(base)
    zc = [0]

    def bc(target, cond):
        zc[0] += 1; n = f"_r{zc[0]}"
        a.emit(b_cond, n, INV[cond]); a.emit(b, target); a.label(n)

    def imm32(rd, v): a.emit(movw, rd, v & 0xFFFF); a.emit(movt, rd, v >> 16)

    # ---- c_rdin: the hooked entry (r0 = port, r1 = msg {buf, len}, r2)
    a.label("c_rdin")
    a.emit(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    a.emit(ldr_imm, 4, 1, 0); a.emit(ldr_imm, 5, 1, 4)                          # r4 = buf, r5 = len
    a.emit(cmp_imm, 5, 8); bc("ri_fwd", "lo")
    for i, v in enumerate(SIG):
        a.emit(ldrb_imm, 3, 4, i); a.emit(cmp_imm, 3, v); bc("ri_fwd", "ne")
    a.emit(mov_reg, 6, 0)                                                      # r6 = port
    a.emit(bl, "c_rdcmd")
    a.emit(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)                           # swallowed
    a.label("ri_fwd")
    a.emit(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True))
    a.emit(raw, PROLOGUE)
    a.emit(b_w, HOOK_CONT)

    # ---- c_g32 (r0 = ptr) -> r0 = u32 from 8 nibbles; clobbers r1-r3
    a.label("c_g32")
    a.emit(movs_imm, 1, 0); a.emit(movs_imm, 2, 8)
    a.label("g32_l")
    a.emit(ldrb_imm, 3, 0, 0); a.emit(adds_imm8, 0, 1); a.emit(lsls_imm, 1, 1, 4)
    a.emit(lsls_imm, 3, 3, 28); a.emit(lsrs_imm, 3, 3, 28); a.emit(orrs_reg, 1, 3)
    a.emit(subs_imm8, 2, 1); a.emit(b_cond, "g32_l", "ne")
    a.emit(mov_reg, 0, 1); a.emit(raw, h(0x4770))

    # ---- c_p32 (r0 = ptr, r1 = value) -> 8 nibbles, r0 = ptr + 8; clobbers r2, r3
    a.label("c_p32")
    a.emit(movs_imm, 2, 8)
    a.label("p32_l")
    a.emit(lsrs_imm, 3, 1, 28); a.emit(strb_imm, 3, 0, 0); a.emit(adds_imm8, 0, 1); a.emit(lsls_imm, 1, 1, 4)
    a.emit(subs_imm8, 2, 1); a.emit(b_cond, "p32_l", "ne")
    a.emit(raw, h(0x4770))

    # ---- c_pbytes (r0 = dst, r1 = src, r2 = n) -> 2 nibbles per byte, r0 = dst end; clobbers r1-r3
    a.label("c_pbytes")
    a.emit(cmp_imm, 2, 0); a.emit(b_cond, "pb_x", "eq")
    a.label("pb_l")
    a.emit(ldrb_imm, 3, 1, 0); a.emit(adds_imm8, 1, 1)
    a.emit(push_list, [3]); a.emit(lsrs_imm, 3, 3, 4); a.emit(strb_imm, 3, 0, 0); a.emit(pop_list, [3])
    a.emit(lsls_imm, 3, 3, 28); a.emit(lsrs_imm, 3, 3, 28); a.emit(strb_imm, 3, 0, 1); a.emit(adds_imm8, 0, 2)
    a.emit(subs_imm8, 2, 1); a.emit(b_cond, "pb_l", "ne")
    a.label("pb_x"); a.emit(raw, h(0x4770))

    # ---- c_gbytes (r0 = dst, r1 = src nibbles, r2 = n); clobbers r1-r3
    a.label("c_gbytes")
    a.emit(cmp_imm, 2, 0); a.emit(b_cond, "gb_x", "eq")
    a.emit(push_list, [4])
    a.label("gb_l")
    a.emit(ldrb_imm, 3, 1, 0); a.emit(lsls_imm, 3, 3, 28); a.emit(lsrs_imm, 3, 3, 24)
    a.emit(ldrb_imm, 4, 1, 1); a.emit(lsls_imm, 4, 4, 28); a.emit(lsrs_imm, 4, 4, 28); a.emit(orrs_reg, 3, 4)
    a.emit(strb_imm, 3, 0, 0); a.emit(adds_imm8, 0, 1); a.emit(adds_imm8, 1, 2)
    a.emit(subs_imm8, 2, 1); a.emit(b_cond, "gb_l", "ne")
    a.emit(pop_list, [4])
    a.label("gb_x"); a.emit(raw, h(0x4770))

    # ---- c_rdcmd (r4 = buf, r5 = len, r6 = port): the reply is written over buf; r7 = write pointer
    a.label("c_rdcmd")
    a.emit(cmp_imm, 5, PAD - 4); a.emit(b_cond, "rc_go", "hs"); a.emit(raw, h(0x4770))     # not padded: no reply
    a.label("rc_go")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(sub_sp_imm, 40); a.emit(mov_reg, 7, 13)                             # frame: [0] cb [4] ctx [8] &done [12] done [16..27] item [32] msg {buf, len}
    a.emit(movs_imm, 0, 0)
    for o in range(0, 40, 4): a.emit(str_imm, 0, 7, o)
    a.emit(ldrb_imm, 0, 4, 4); a.emit(movs_imm, 1, 0x40); a.emit(orrs_reg, 1, 0); a.emit(strb_imm, 1, 4, 4)   # cmd | 0x40 (r0 = cmd)
    a.emit(push_list, [0]); a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 6); a.emit(mov_reg, 1, 0); a.emit(pop_list, [0])  # r1 = payload pointer
    for cmd, lab in ((1, "rc_ping"), (2, "rc_mem"), (4, "rc_info"), (5, "rc_read"), (6, "rc_write")) + (((7, "rc_del"),) if DELETE else ()) + (((3, "rc_dspr"), (8, "rc_dspx")) if DSPX else ()) + (((10, "rc_watch"), (11, "rc_poke"), (12, "rc_wlog")) if WATCH else ()) + (((9, "rc_dspw"),) if DSPW else ()):
        a.emit(cmp_imm, 0, cmd); bc(lab, "eq")
    a.emit(mov_reg, 0, 1); imm32(1, 0xFFFFFFFF); a.emit(bl, "c_p32"); a.emit(b, "rc_send")   # unknown command: status -1

    a.label("rc_ping")
    a.emit(mov_reg, 0, 1); imm32(1, VERSION + (1 if DELETE else 0) + (0x10 if DSPX else 0) + (0x20 if DEL_PACK else 0) + (0x40 if DSPW else 0) + (0x80 if WATCH else 0)); a.emit(bl, "c_p32")
    a.emit(mov_reg, 1, 6); a.emit(bl, "c_p32"); a.emit(b, "rc_send")

    def item_from(off):                          # the item {kind, idx, pack} from buf[off..off+2] into the frame; pack 0x7F -> 0xFF
        a.emit(ldrb_imm, 0, 4, off); a.emit(str_imm, 0, 7, 16)
        a.emit(ldrb_imm, 0, 4, off + 1); a.emit(str_imm, 0, 7, 20)
        a.emit(ldrb_imm, 0, 4, off + 2); a.emit(cmp_imm, 0, 0x7F); zc[0] += 1; n = f"_pk{zc[0]}"
        a.emit(b_cond, n, "ne"); a.emit(movs_imm, 0, 0xFF); a.label(n); a.emit(strb_imm, 0, 7, 24)

    def item_ptr(rd): a.emit(mov_reg, rd, 7); a.emit(adds_imm8, rd, 16)

    def raw_ptr(rd): a.emit(mov_reg, rd, 4); a.emit(adds_imm8, rd, RAW)

    def clamp_n(off, rd):                        # rd = min(buf[off], NMAX)
        a.emit(ldrb_imm, rd, 4, off); a.emit(cmp_imm, rd, NMAX); zc[0] += 1; n = f"_cl{zc[0]}"
        a.emit(b_cond, n, "ls"); a.emit(movs_imm, rd, NMAX); a.label(n)

    # mem: addr = g32(buf + 6), n = buf[14]
    a.label("rc_mem")
    a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 6); a.emit(bl, "c_g32"); a.emit(push_list, [0])     # [sp] = addr
    clamp_n(14, 2); a.emit(pop_list, [1])                                     # r1 = addr, r2 = n
    a.emit(adds_reg, 3, 1, 2)                                                  # r3 = end
    for k, (lo, hi) in enumerate((FLASH, RAM)):
        imm32(0, lo); a.emit(cmp_reg, 1, 0); bc(f"mm_n{k}", "lo")
        imm32(0, hi); a.emit(cmp_reg, 3, 0); bc(f"mm_n{k}", "hi")
        a.emit(b, "mm_ok")
        a.label(f"mm_n{k}")
    a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 6); a.emit(movs_imm, 1, 1); a.emit(bl, "c_p32"); a.emit(b, "rc_send")
    a.label("mm_ok")
    a.emit(push_list, [1, 2])
    a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 6); a.emit(movs_imm, 1, 0); a.emit(bl, "c_p32")
    a.emit(pop_list, [1, 2]); a.emit(bl, "c_pbytes"); a.emit(b, "rc_send")

    # info: exists, size
    a.label("rc_info")
    item_from(6)
    item_ptr(0); a.emit(bl, EXISTS); a.emit(mov_reg, 1, 0); a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 6); a.emit(bl, "c_p32"); a.emit(push_list, [0])
    item_ptr(0); a.emit(bl, SIZE); a.emit(mov_reg, 1, 0); a.emit(pop_list, [0]); a.emit(bl, "c_p32"); a.emit(b, "rc_send")

    # read: item, off = g32(buf + 9), n = buf[17] -> status, done, bytes
    a.label("rc_read")
    item_from(6)
    a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 9); a.emit(bl, "c_g32"); a.emit(mov_reg, 1, 0)       # r1 = offset
    clamp_n(17, 3); a.emit(str_imm, 3, 7, 36)                                 # n kept at [36]
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 12); a.emit(str_imm, 0, 7, 8)    # &done
    item_ptr(0); raw_ptr(2)
    a.emit(bl, READ)
    a.emit(mov_reg, 1, 0); a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 6); a.emit(bl, "c_p32")
    a.emit(ldr_imm, 1, 7, 12); a.emit(bl, "c_p32")
    raw_ptr(1); a.emit(ldr_imm, 2, 7, 12); a.emit(ldr_imm, 3, 7, 36); a.emit(cmp_reg, 2, 3); zc[0] += 1
    a.emit(b_cond, f"_dn{zc[0]}", "ls"); a.emit(mov_reg, 2, 3); a.label(f"_dn{zc[0]}")
    a.emit(bl, "c_pbytes"); a.emit(b, "rc_send")

    # write: item, off = g32(buf + 9), n = buf[17], data nibbles from buf + 18 -> status
    a.label("rc_write")
    item_from(6)
    clamp_n(17, 2); a.emit(str_imm, 2, 7, 36)
    raw_ptr(0); a.emit(mov_reg, 1, 4); a.emit(adds_imm8, 1, 18); a.emit(bl, "c_gbytes")
    a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 9); a.emit(bl, "c_g32"); a.emit(mov_reg, 1, 0)
    item_ptr(0); raw_ptr(2); a.emit(ldr_imm, 3, 7, 36)
    a.emit(bl, WRITE)
    a.emit(mov_reg, 1, 0); a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 6); a.emit(bl, "c_p32"); a.emit(b, "rc_send")

    if DELETE:
        # delete: kinds 2-6 only
        a.label("rc_del")
        item_from(6)
        if DEL_PACK:                                                           # kind 1 = a whole pack: only an explicit pack that is not the current one
            a.emit(ldr_imm, 0, 7, 16); a.emit(cmp_imm, 0, 1); bc("rd_item", "ne")
            imm32(0, CUR_PACK_PTR); a.emit(ldr_imm, 0, 0, 0); a.emit(ldrb_imm, 0, 0, 0); a.emit(str_imm, 0, 7, 36)   # [36] = the current pack
            a.emit(ldrb_imm, 1, 7, 24); a.emit(cmp_imm, 1, 0xFF); bc("rd_bad", "eq"); a.emit(cmp_reg, 1, 0); bc("rd_bad", "eq")
            item_ptr(0); a.emit(movs_imm, 1, 0); a.emit(movs_imm, 2, 0); a.emit(bl, DEL_FN)
            a.emit(mov_reg, 1, 0); a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 6); a.emit(bl, "c_p32"); a.emit(str_imm, 0, 7, 32)
            # re-select the current pack in the storage task (its "current" is 0xFF after deleting a pack): exists(PCM 0 of the current pack)
            a.emit(movs_imm, 0, 4); a.emit(str_imm, 0, 7, 16); a.emit(movs_imm, 0, 0); a.emit(str_imm, 0, 7, 20)
            a.emit(ldr_imm, 0, 7, 36); a.emit(strb_imm, 0, 7, 24)
            item_ptr(0); a.emit(bl, EXISTS); a.emit(mov_reg, 1, 0); a.emit(ldr_imm, 0, 7, 32); a.emit(bl, "c_p32")
            a.emit(ldr_imm, 1, 7, 36); a.emit(bl, "c_p32"); a.emit(b, "rc_send")
            a.label("rd_item")
        a.emit(ldr_imm, 0, 7, 16); a.emit(subs_imm8, 0, 2); a.emit(cmp_imm, 0, 4); bc("rd_bad", "hi")
        item_ptr(0); a.emit(movs_imm, 1, 0); a.emit(movs_imm, 2, 0); a.emit(bl, DEL_FN)
        a.emit(mov_reg, 1, 0); a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 6); a.emit(bl, "c_p32"); a.emit(b, "rc_send")
        a.label("rd_bad")
        a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 6); imm32(1, 0xFFFFFFFE); a.emit(bl, "c_p32"); a.emit(b, "rc_send")

    if DSPX:
        import sampler_dsp as SD

        def take():                              # [r7 + 28] = the semaphore (the holder), taken
            imm32(0, SEM_PTR); a.emit(ldr_imm, 0, 0, 0); a.emit(adds_imm8, 0, 0xC); a.emit(str_imm, 0, 7, 28); a.emit(bl, SEM_TAKE)

        def give():
            a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 28); a.emit(bl, SEM_GIVE)

        def xread(addr):                         # r0 = the 24-bit word at X:addr
            imm32(1, addr); a.emit(movs_imm, 0, 0); a.emit(bl, DSP_READ); a.emit(lsrs_imm, 0, 0, 8)

        def xwrite(addr, vreg):                  # X:addr = vreg (r3)
            a.emit(lsls_imm, 1, vreg, 8); imm32(2, addr); a.emit(movs_imm, 0, 0); a.emit(bl, DSP_WRITE)

        # command 3: space = buf[6], addr = g32(buf + 7), n = buf[15] (<= NR) -> status 0, n words as 6 nibbles
        a.label("rc_dspr")
        a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 7); a.emit(bl, "c_g32"); a.emit(str_imm, 0, 7, 16)
        a.emit(ldrb_imm, 0, 4, 6); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "dr_sx", "eq")
        a.emit(ldr_imm, 0, 7, 16); imm32(1, 0x8000); a.emit(orrs_reg, 0, 1); a.emit(str_imm, 0, 7, 16)
        a.label("dr_sx")
        a.emit(ldrb_imm, 0, 4, 15); a.emit(cmp_imm, 0, NR); a.emit(b_cond, "dr_nr", "ls"); a.emit(movs_imm, 0, NR)
        a.label("dr_nr"); a.emit(str_imm, 0, 7, 20)
        a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 6); a.emit(movs_imm, 1, 0); a.emit(bl, "c_p32"); a.emit(str_imm, 0, 7, 24)   # [24] = write pointer
        take()
        a.label("dr_l")
        a.emit(ldr_imm, 0, 7, 20); a.emit(cmp_imm, 0, 0); bc("dr_x", "eq"); a.emit(subs_imm8, 0, 1); a.emit(str_imm, 0, 7, 20)
        a.emit(ldr_imm, 1, 7, 16); a.emit(movs_imm, 0, 0); a.emit(bl, DSP_READ); a.emit(lsrs_imm, 1, 0, 8)
        a.emit(ldr_imm, 0, 7, 16); a.emit(adds_imm8, 0, 1); a.emit(str_imm, 0, 7, 16)
        a.emit(ldr_imm, 0, 7, 24); a.emit(lsls_imm, 1, 1, 8); a.emit(bl, "c_p32"); a.emit(subs_imm8, 0, 2); a.emit(str_imm, 0, 7, 24)   # 6 nibbles
        a.emit(b, "dr_l")
        a.label("dr_x")
        give()
        a.emit(ldr_imm, 0, 7, 24); a.emit(b, "rc_send")

        # command 8: src = g32(buf + 6), n = buf[14] (<= NX) -> status, n samples (4 nibbles)
        a.label("rc_dspx")
        a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 6); a.emit(bl, "c_g32"); a.emit(str_imm, 0, 7, 16)
        a.emit(ldrb_imm, 0, 4, 14); a.emit(cmp_imm, 0, NX); a.emit(b_cond, "dx_nx", "ls"); a.emit(movs_imm, 0, NX)
        a.label("dx_nx"); a.emit(str_imm, 0, 7, 20)
        take()
        xread(SD.CPLEN); a.emit(cmp_imm, 0, 0); bc("dx_free", "eq")
        give(); a.emit(movs_imm, 1, 3); a.emit(b, "dx_status")
        a.label("dx_free")
        a.emit(ldr_imm, 3, 7, 16); xwrite(SD.CPSRC, 3)
        imm32(3, WIN); xwrite(SD.CPDST, 3)
        a.emit(ldr_imm, 3, 7, 20); xwrite(SD.CPLEN, 3)
        give()
        a.emit(movs_imm, 0, 100); a.emit(str_imm, 0, 7, 24)                    # up to 100 x 1 ms
        a.label("dx_w")
        a.emit(movs_imm, 0, 1); a.emit(bl, SLEEP)
        take(); xread(SD.CPLEN); a.emit(str_imm, 0, 7, 12); give()
        a.emit(ldr_imm, 0, 7, 12); a.emit(cmp_imm, 0, 0); bc("dx_done", "eq")
        a.emit(ldr_imm, 0, 7, 24); a.emit(subs_imm8, 0, 1); a.emit(str_imm, 0, 7, 24); bc("dx_w", "ne")
        a.emit(movs_imm, 1, 4); a.emit(b, "dx_status")
        a.label("dx_done")
        a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 6); a.emit(movs_imm, 1, 0); a.emit(bl, "c_p32"); a.emit(str_imm, 0, 7, 24)
        imm32(0, 0x8000 | WIN); a.emit(str_imm, 0, 7, 16)
        take()
        a.label("dx_l")
        a.emit(ldr_imm, 0, 7, 20); a.emit(cmp_imm, 0, 0); bc("dx_x", "eq"); a.emit(subs_imm8, 0, 1); a.emit(str_imm, 0, 7, 20)
        a.emit(ldr_imm, 1, 7, 16); a.emit(movs_imm, 0, 0); a.emit(bl, DSP_READ)
        a.emit(lsrs_imm, 1, 0, 16)                                             # the sample = bits 23..8 of the word
        a.emit(ldr_imm, 0, 7, 16); a.emit(adds_imm8, 0, 1); a.emit(str_imm, 0, 7, 16)
        a.emit(ldr_imm, 0, 7, 24); a.emit(lsls_imm, 1, 1, 16); a.emit(bl, "c_p32"); a.emit(subs_imm8, 0, 4); a.emit(str_imm, 0, 7, 24)   # 4 nibbles
        a.emit(b, "dx_l")
        a.label("dx_x")
        give()
        a.emit(ldr_imm, 0, 7, 24); a.emit(b, "rc_send")
        if DSPW:
            # command 9: X:addr (g32(buf + 6)) = value (g32(buf + 14)) -> status 0
            a.label("rc_dspw")
            a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 6); a.emit(bl, "c_g32"); a.emit(str_imm, 0, 7, 16)
            a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 14); a.emit(bl, "c_g32"); a.emit(str_imm, 0, 7, 20)
            take()
            a.emit(ldr_imm, 3, 7, 20); a.emit(lsls_imm, 1, 3, 8); a.emit(ldr_imm, 2, 7, 16); a.emit(movs_imm, 0, 0); a.emit(bl, DSP_WRITE)
            give()
            a.emit(movs_imm, 1, 0); a.emit(b, "dx_status")
        a.label("dx_status")
        a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 6); a.emit(bl, "c_p32"); a.emit(b, "rc_send")

    if WATCH:
        def outp(): a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 6)                # r0 = the reply's payload
        # ---- watch: addr = g32(buf + 6), func = buf[14], mask = buf[15]
        a.label("rc_watch")
        a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 6); a.emit(bl, "c_g32"); a.emit(str_imm, 0, 7, 16)
        a.emit(bl, GST); a.emit(cmp_imm, 0, 0); bc("rw_nost", "eq")
        a.emit(adds_imm8, 0, LOG_OFF); a.emit(str_imm, 0, 7, 20)                   # [20] = the log
        a.emit(movs_imm, 1, 0); a.emit(movs_imm, 2, 0)
        a.label("rw_clr"); a.emit(raw, h(0x5081)); a.emit(adds_imm8, 2, 4); a.emit(cmp_imm, 2, 4 + 8 * LOG_N); a.emit(b_cond, "rw_clr", "lo")   # str r1,[r0,r2]
        imm32(0, DEMCR); a.emit(ldr_imm, 1, 0, 0); imm32(2, 0x01010000); a.emit(orrs_reg, 1, 2); a.emit(str_imm, 1, 0, 0)   # TRCENA | MON_EN
        imm32(0, DWT_LAR); imm32(1, 0xC5ACCE55); a.emit(str_imm, 1, 0, 0)
        imm32(0, DWT_COMP0); a.emit(movs_imm, 1, 0); a.emit(str_imm, 1, 0, 8)      # FUNCTION0 = 0 while it changes
        a.emit(ldr_imm, 1, 7, 16); a.emit(str_imm, 1, 0, 0)                        # COMP0
        a.emit(ldrb_imm, 1, 4, 15); a.emit(str_imm, 1, 0, 4)                       # MASK0
        a.emit(ldrb_imm, 1, 4, 14); a.emit(str_imm, 1, 0, 8)                       # FUNCTION0
        outp(); a.emit(movs_imm, 1, 0); a.emit(bl, "c_p32")
        for reg in (DWT_CTRL, DEMCR, DWT_COMP0 + 8):
            a.emit(push_list, [0]); imm32(1, reg); a.emit(ldr_imm, 1, 1, 0); a.emit(pop_list, [0]); a.emit(bl, "c_p32")
        a.emit(ldr_imm, 1, 7, 20); a.emit(bl, "c_p32"); a.emit(b, "rc_send")
        a.label("rw_nost"); outp(); a.emit(movs_imm, 1, 2); a.emit(bl, "c_p32"); a.emit(b, "rc_send")
        # ---- poke: addr = g32(buf + 6), n = buf[14], data nibbles from buf + 15; RAM only
        a.label("rc_poke")
        a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 6); a.emit(bl, "c_g32"); a.emit(mov_reg, 1, 0)
        clamp_n(14, 2); a.emit(adds_reg, 3, 1, 2)
        imm32(0, RAM[0]); a.emit(cmp_reg, 1, 0); bc("rp_bad", "lo")
        imm32(0, RAM[1]); a.emit(cmp_reg, 3, 0); bc("rp_bad", "hi")
        a.emit(mov_reg, 0, 1); a.emit(mov_reg, 1, 4); a.emit(adds_imm8, 1, 15); a.emit(bl, "c_gbytes")
        outp(); a.emit(movs_imm, 1, 0); a.emit(bl, "c_p32"); a.emit(b, "rc_send")
        a.label("rp_bad"); outp(); a.emit(movs_imm, 1, 1); a.emit(bl, "c_p32"); a.emit(b, "rc_send")
        # ---- wlog: status, hits, LOG_N x (PC, LR)
        a.label("rc_wlog")
        a.emit(bl, GST); a.emit(cmp_imm, 0, 0); bc("rw_nost", "eq")
        a.emit(adds_imm8, 0, LOG_OFF); a.emit(str_imm, 0, 7, 20)
        outp(); a.emit(movs_imm, 1, 0); a.emit(bl, "c_p32")
        a.emit(movs_imm, 1, 0); a.emit(str_imm, 1, 7, 24)
        a.label("rl_l")
        a.emit(ldr_imm, 2, 7, 20); a.emit(ldr_imm, 3, 7, 24); a.emit(raw, h(0x58D1))                # ldr r1,[r2,r3]
        a.emit(bl, "c_p32")
        a.emit(ldr_imm, 3, 7, 24); a.emit(adds_imm8, 3, 4); a.emit(str_imm, 3, 7, 24); a.emit(cmp_imm, 3, 4 + 8 * LOG_N); a.emit(b_cond, "rl_l", "lo")
        a.emit(b, "rc_send")

    # r0 = end of the payload: F7, then send {buf, end + 1 - buf} to the port it came from
    a.label("rc_send")
    a.emit(movs_imm, 1, 0xF7); a.emit(strb_imm, 1, 0, 0); a.emit(adds_imm8, 0, 1); a.emit(subs_reg, 0, 0, 4)
    a.emit(str_imm, 4, 7, 32); a.emit(str_imm, 0, 7, 36)
    imm32(0, router_ptr); a.emit(ldr_imm, 0, 0, 0)                             # r0 = the router
    a.emit(movs_imm, 1, 1); a.emit(raw, h(0x40B1))                             # lsls r1, r6 -> mask = 1 << port
    a.emit(mov_reg, 2, 7); a.emit(adds_imm8, 2, 32)
    a.emit(bl, ROUTER)
    a.emit(add_sp_imm, 40); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    if WATCH:
        # ---- c_dmon: the DebugMonitor exception (a DWT match); hardware stacked r0-r3, r12, lr, pc, xpsr on MSP or PSP (EXC_RETURN bit 2)
        a.label("c_dmon")
        a.emit(push_list, [4, 5, 6], lr=True)
        a.emit(mov_reg, 0, 14); a.emit(movs_imm, 1, 4); a.emit(tst_reg, 0, 1); a.emit(b_cond, "dm_psp", "ne")
        a.emit(raw, h(0xF3EF) + h(0x8008)); a.emit(adds_imm8, 0, 16); a.emit(b, "dm_got")     # mrs r0, msp (+ our 16 bytes)
        a.label("dm_psp"); a.emit(raw, h(0xF3EF) + h(0x8009))                                 # mrs r0, psp
        a.label("dm_got")
        a.emit(ldr_imm, 4, 0, 24); a.emit(ldr_imm, 5, 0, 20)                     # r4 = PC, r5 = LR of the access
        a.emit(bl, GST); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "dm_x", "eq")
        a.emit(adds_imm8, 0, LOG_OFF); a.emit(mov_reg, 6, 0)
        a.emit(ldr_imm, 1, 6, 0); a.emit(adds_imm8, 1, 1); a.emit(str_imm, 1, 6, 0)        # hits + 1
        a.emit(movs_imm, 2, 0)
        a.label("dm_l")
        a.emit(cmp_imm, 2, LOG_N); a.emit(b_cond, "dm_x", "hs")
        a.emit(lsls_imm, 3, 2, 3); a.emit(adds_reg, 3, 3, 6)
        a.emit(ldr_imm, 1, 3, 4); a.emit(cmp_reg, 1, 4); a.emit(b_cond, "dm_x", "eq")
        a.emit(cmp_imm, 1, 0); a.emit(b_cond, "dm_new", "eq")
        a.emit(adds_imm8, 2, 1); a.emit(b, "dm_l")
        a.label("dm_new"); a.emit(str_imm, 4, 3, 4); a.emit(str_imm, 5, 3, 8)
        a.label("dm_x")
        imm32(0, DFSR); a.emit(movs_imm, 1, 4); a.emit(str_imm, 1, 0, 0)          # DFSR.DWTTRAP cleared (write 1)
        imm32(0, DWT_COMP0 + 8); a.emit(ldr_imm, 1, 0, 0)                          # reading FUNCTION0 clears MATCHED
        a.emit(pop_list, [4, 5, 6], pc=True)                                        # pc = EXC_RETURN: back from the exception
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the first 4 bytes of the incoming SysEx dispatcher -> b.w c_rdin."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    assert bytes(img[HOOK - BASE:HOOK - BASE + 4]) == PROLOGUE, img[HOOK - BASE:HOOK - BASE + 4].hex()
    import struct
    router_ptr = struct.unpack_from("<I", img, ROUTER_LIT - BASE)[0]
    global GST
    if WATCH: GST = int(report["sc14"]["labels"]["c_gst"], 16)
    code, labels = arm_code(base_addr, router_ptr)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[HOOK - BASE:HOOK - BASE + 4] = b_w(HOOK, labels["c_rdin"])
    if WATCH:                                    # the app's DebugMonitor vector (the stock's default handler) -> c_dmon
        assert struct.unpack_from("<I", img, VEC_DEBUGMON - BASE)[0] == 0x0805998B
        struct.pack_into("<I", img, VEC_DEBUGMON - BASE, labels["c_dmon"] | 1)
    return labels, code
