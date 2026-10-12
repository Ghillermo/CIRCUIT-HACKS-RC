"""SC35D4 (DIAGNOSTIC, READ-ONLY on the SD card): the stock content API of the storage task, the way to save the captured sample into the pack's PCM folder.

The SysEx file transfer of Novation Components (0x0803A0xx: "Data Packet", "Cache / Write Data Packet") does not touch any file object itself: it asks the
storage task through 0x0803CA52(op, item, args, cb, ...) (sync when cb = 0: 0x08022A46, async: 0x08022A5C).  Ops: 0 = exists (0x0803CB50, bool), 1 = size
(0x0803CB6A), 6 = read (0x0803CBF0(item, offset, buf, len, cb, ctx, &done)), 7 = write (0x0803CC16, same arguments).  An item is 12 bytes: u32 kind (the SysEx
byte b -> 0x08039570: 3..8 -> 2, 3, 4, 6, 5, 0), u32 index, u8 pack (0xFF = the current pack, 0x0803676C).  The pack folders (0x0805A4F8..): Sessions /
_SESSION.ncs, Patches / _PATCHBANK.cpb, PCM / _PCM.wav (64), meta / _META.ncm, the effects folder / its .ncg files.  This probe only READS, never writes.

  * c_dtick35 (head of the DSP service chain, then SC19's c_dtick19): with the synth source view open (Synth 1 / 2 pressed twice), pads 9-16 green (pad 9 + k
    = item index k), pads 17-24 dark; nothing is read in the tick.
  * c_spad (slot 0 of the synth Preset view, in front of srcview's c_xpad): with the source view open, pad 9 + k (k < 8): in the UI task, sync calls on the item
    (KIND, k, 0xFF): exists, size, read of the first NHEAD bytes at offset 0; the 14 words (SC14 state + 104, the idle Master FX LED buffer) go out as the
    SC32D.1 dump (CC 20 = 127; per word CC 21 = i, CC 22..25 = 3 + 7 + 7 + 7 bits; CC 20 = 0; channel 16).  Words: 0 MAGIC, 1 exists, 2 size bits 0-23,
    3 size bits 24-31, 4 read status, 5 bytes read, 6..12 the first 21 bytes (3 per word, big-endian), 13 = kind << 8 | index.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, ldr_imm, ldrb_imm, lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw, adds_imm8, subs_imm8,  # noqa: E402
                   pop_list, push_list, raw, h, tst_reg, ands_reg, strh_imm, adds_reg, str_imm, strb_imm, add_sp_imm, sub_sp_imm, orrs_reg)
import probe32b as PB  # noqa: E402

EXISTS, SIZE, READ, WRITE = 0x0803CB50, 0x0803CB6A, 0x0803CBF0, 0x0803CC16
WB_PADS = False                                  # SC35D7: the write-back on pads 17-24 (red) = items 0-7, not on Shift (SC35D6: Shift + pad never wrote on the device)
WB_RED = 0x53
O_WB = 56                                        # frame word: 1 = this press writes back
WRITEBACK = False                                # SC35D6: Shift + pad = the 21 bytes just read are written back unchanged (op 7, in place: the storage task opens the
MAGIC_WB = 0xC5D006                              #   existing NN_*.wav with the read / write / open-always mode, no truncation), then size and bytes read again.
                                                 #   Words: 0 MAGIC_WB, 1 exists, 2 size before, 3 write status, 4 size after, 5 read status << 8 | bytes,
                                                 #   6..12 the bytes read after the write, 13 = kind << 8 | 0x80 | index
KIND = 2                                         # SC35D4: 2 (it read session 0 on the device: kinds 2..6 = Sessions, Patches, PCM, meta, the effects folder); SC35D5: 4 = PCM
PACK_CUR = 0xFF
NHEAD = 21
MAGIC = 0xC5D004
NWORDS = 14
BUF = PB.BUF
GREEN = PB.GREEN
VIEWS, SP_VT, SEND, SLEEP, STATUS, CC0 = PB.VIEWS, PB.SP_VT, PB.SEND, PB.SLEEP, PB.STATUS, PB.CC0
FR = 64                                          # stack frame (8-byte aligned): [0] cb, [4] ctx, [8] &done, [12] done, [16..27] item, [28..51] read buffer
O_DONE, O_ITEM, O_RB = 12, 16, 28
INV = PB.INV


def arm_code(base, L, K, xpad):
    a = Asm(base)
    zc = [0]
    S_PAINT, F_SRC = K["S_PAINT"], K["F_SRC"]

    def bc(target, cond):
        zc[0] += 1; n = f"_q{zc[0]}"
        a.emit(b_cond, n, INV[cond]); a.emit(b, target); a.label(n)

    def src_open(fail):                          # r0 = SC14 state when the source view is open, else -> fail
        a.emit(bl, L["c_gst"]); a.emit(cmp_imm, 0, 0); bc(fail, "eq")
        a.emit(ldrb_imm, 1, 0, S_PAINT); a.emit(movs_imm, 2, F_SRC); a.emit(tst_reg, 1, 2); bc(fail, "eq")

    def word(i, rs):                             # BUF[i] = rs (r6 = SC14 state + BUF)
        a.emit(str_imm, rs, 6, 4 * i)

    # ---- c_dtick35: LEDs only
    a.label("c_dtick35")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    src_open("dt_out")
    for vi, view in enumerate(VIEWS):
        a.emit(movw, 0, view & 0xFFFF); a.emit(movt, 0, view >> 16)
        a.emit(ldr_imm, 1, 0, 0); a.emit(movw, 2, SP_VT & 0xFFFF); a.emit(movt, 2, SP_VT >> 16)
        a.emit(PB.cmp_reg, 1, 2); bc(f"dt_v{vi}", "ne")
        a.emit(bl, K["SP_LEDS"])
        a.emit(movs_imm, 1, GREEN)
        for i in range(8, 16): a.emit(strh_imm, 1, 0, 2 * i)
        a.emit(movs_imm, 1, WB_RED if WB_PADS else 0)
        for i in range(16, 24): a.emit(strh_imm, 1, 0, 2 * i)
        a.label(f"dt_v{vi}")
    a.label("dt_out")
    a.emit(raw, PB.popw([4, 5, 6, 7], lr=True))
    a.emit(b_w, L["c_dtick19"])

    # ---- c_snd (r0 = CC number, r1 = value)
    a.label("c_snd")
    a.emit(push_list, [4], lr=True)
    a.emit(sub_sp_imm, 8); a.emit(mov_reg, 4, 13)
    a.emit(movs_imm, 2, STATUS); a.emit(strb_imm, 2, 4, 0); a.emit(strb_imm, 0, 4, 1); a.emit(strb_imm, 1, 4, 2)
    a.emit(mov_reg, 1, 4); a.emit(movs_imm, 0, 7); a.emit(bl, SEND)
    a.emit(add_sp_imm, 8); a.emit(pop_list, [4], pc=True)

    # ---- c_spad (view, pad, vel)
    a.label("c_spad")
    a.emit(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    a.emit(cmp_imm, 1, 8); bc("sp_fwd", "lo"); a.emit(cmp_imm, 1, 24 if WB_PADS else 16); bc("sp_fwd", "hs")
    a.emit(mov_reg, 5, 1); a.emit(subs_imm8, 5, 8)                                   # r5 = item index (WB_PADS: 8-15 = write back 0-7)
    src_open("sp_fwd"); a.emit(mov_reg, 4, 0); a.emit(mov_reg, 6, 0); a.emit(adds_imm8, 6, BUF)
    a.emit(sub_sp_imm, FR); a.emit(mov_reg, 7, 13)
    a.emit(movs_imm, 0, 0)
    for o in range(0, FR, 4): a.emit(str_imm, 0, 7, o)
    if WB_PADS:
        a.emit(cmp_imm, 5, 8); bc("sp_rd", "lo")
        a.emit(subs_imm8, 5, 8); a.emit(movs_imm, 0, 1); a.emit(str_imm, 0, 7, O_WB)
        a.label("sp_rd")
    a.emit(movs_imm, 0, KIND); a.emit(str_imm, 0, 7, O_ITEM); a.emit(str_imm, 5, 7, O_ITEM + 4)
    a.emit(movs_imm, 0, PACK_CUR); a.emit(strb_imm, 0, 7, O_ITEM + 8)
    a.emit(movw, 0, MAGIC & 0xFFFF); a.emit(movt, 0, MAGIC >> 16); word(0, 0)
    a.emit(movs_imm, 0, KIND << 3); a.emit(lsls_imm, 0, 0, 5); a.emit(orrs_reg, 0, 5); word(13, 0)
    # exists
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, O_ITEM); a.emit(bl, EXISTS); word(1, 0)
    # size
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, O_ITEM); a.emit(bl, SIZE)
    a.emit(lsls_imm, 1, 0, 8); a.emit(lsrs_imm, 1, 1, 8); word(2, 1); a.emit(lsrs_imm, 1, 0, 24); word(3, 1)
    # read the first NHEAD bytes (sync: cb = 0, ctx = 0, &done)
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, O_DONE); a.emit(str_imm, 0, 7, 8)
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, O_ITEM); a.emit(movs_imm, 1, 0)
    a.emit(mov_reg, 2, 7); a.emit(adds_imm8, 2, O_RB); a.emit(movs_imm, 3, NHEAD)
    a.emit(bl, READ); word(4, 0)
    a.emit(ldr_imm, 0, 7, O_DONE); word(5, 0)
    def bytes_words():
        a.emit(mov_reg, 2, 7); a.emit(adds_imm8, 2, O_RB)
        for j in range(7):                                                           # words 6..12 = bytes 3j..3j+2
            a.emit(ldrb_imm, 0, 2, 3 * j); a.emit(lsls_imm, 0, 0, 16)
            a.emit(ldrb_imm, 1, 2, 3 * j + 1); a.emit(lsls_imm, 1, 1, 8); a.emit(orrs_reg, 0, 1)
            a.emit(ldrb_imm, 1, 2, 3 * j + 2); a.emit(orrs_reg, 0, 1); word(6 + j, 0)
    bytes_words()
    if WRITEBACK:                                                                    # Shift: write the same bytes back, then size and read again
        if WB_PADS: a.emit(ldr_imm, 0, 7, O_WB)
        else: a.emit(bl, L["c_shift"])
        a.emit(cmp_imm, 0, 0); bc("sp_nwb", "eq")
        a.emit(movw, 0, MAGIC_WB & 0xFFFF); a.emit(movt, 0, MAGIC_WB >> 16); word(0, 0)
        a.emit(movs_imm, 0, (KIND << 8 | 0x80) >> 3); a.emit(lsls_imm, 0, 0, 3); a.emit(orrs_reg, 0, 5); word(13, 0)
        a.emit(movs_imm, 0, 0); a.emit(str_imm, 0, 7, 0); a.emit(str_imm, 0, 7, 4)       # cb = 0, ctx = 0 (sync)
        a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, O_ITEM); a.emit(movs_imm, 1, 0)
        a.emit(mov_reg, 2, 7); a.emit(adds_imm8, 2, O_RB); a.emit(movs_imm, 3, NHEAD)
        a.emit(bl, WRITE); word(3, 0)
        a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, O_ITEM); a.emit(bl, SIZE)
        a.emit(lsls_imm, 0, 0, 8); a.emit(lsrs_imm, 0, 0, 8); word(4, 0)
        a.emit(movs_imm, 0, 0)
        for o in range(O_RB, O_RB + 24, 4): a.emit(str_imm, 0, 7, o)                 # the buffer cleared before reading again
        a.emit(str_imm, 0, 7, O_DONE)
        a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, O_ITEM); a.emit(movs_imm, 1, 0)
        a.emit(mov_reg, 2, 7); a.emit(adds_imm8, 2, O_RB); a.emit(movs_imm, 3, NHEAD)
        a.emit(bl, READ); a.emit(lsls_imm, 0, 0, 8); a.emit(ldr_imm, 1, 7, O_DONE); a.emit(orrs_reg, 0, 1); word(5, 0)
        bytes_words()
        a.label("sp_nwb")
    a.emit(add_sp_imm, FR)
    # the dump
    a.emit(movs_imm, 0, CC0); a.emit(movs_imm, 1, 127); a.emit(bl, "c_snd")
    a.emit(movs_imm, 5, 0)
    a.label("sp_l")
    a.emit(lsls_imm, 1, 5, 2); a.emit(adds_reg, 1, 1, 4); a.emit(ldr_imm, 6, 1, BUF)
    a.emit(movs_imm, 0, CC0 + 1); a.emit(mov_reg, 1, 5); a.emit(bl, "c_snd")
    a.emit(lsrs_imm, 1, 6, 21); a.emit(movs_imm, 0, 7); a.emit(ands_reg, 1, 0); a.emit(movs_imm, 0, CC0 + 2); a.emit(bl, "c_snd")
    for k, sh in ((3, 14), (4, 7), (5, 0)):
        if sh: a.emit(lsrs_imm, 1, 6, sh)
        else: a.emit(mov_reg, 1, 6)
        a.emit(movs_imm, 0, 0x7F); a.emit(ands_reg, 1, 0); a.emit(movs_imm, 0, CC0 + k); a.emit(bl, "c_snd")
    a.emit(movs_imm, 0, 2); a.emit(bl, SLEEP)
    a.emit(adds_imm8, 5, 1); a.emit(cmp_imm, 5, NWORDS); a.emit(b_cond, "sp_l", "lo")
    a.emit(movs_imm, 0, CC0); a.emit(movs_imm, 1, 0); a.emit(bl, "c_snd")
    a.emit(raw, PB.popw([0, 1, 2, 4, 5, 6, 7], lr=True)); a.emit(raw, h(0x4770))          # swallowed
    a.label("sp_fwd")
    a.emit(raw, PB.popw([0, 1, 2, 4, 5, 6, 7], lr=True))
    a.emit(b_w, xpad)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; c_dtick35 at the head of the DSP service chain; slot 0 of the synth Preset view -> c_spad (then srcview's c_xpad)."""
    import struct
    import ct_fw
    import build_sc14 as s14
    import build_sc15 as s15
    import srcview
    import drums18
    BASE = ct_fw.APP_BASE
    p19 = {k: int(v, 16) for k, v in report["persist19"]["labels"].items()}
    xpad = int(report["srcview"]["labels"]["c_xpad"], 16)
    assert struct.unpack_from("<I", img, SP_VT + 4 * srcview.SLOT_PAD - BASE)[0] == xpad | 1
    L = dict(c_gst=int(report["sc14"]["labels"]["c_gst"], 16), c_dtick19=p19["c_dtick19"], c_shift=int(report["sc15"]["labels"]["c_shift"], 16))
    K = dict(S_PAINT=s15.S_PAINT, F_SRC=srcview.F_SRC, SP_LEDS=s15.SP_LEDS)
    assert drums18.decode_bw(img, s14.SVC_HOOK) == p19["c_dtick19"]
    code, labels = arm_code(base_addr, L, K, xpad)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[s14.SVC_HOOK - BASE:s14.SVC_HOOK - BASE + 4] = b_w(s14.SVC_HOOK, labels["c_dtick35"])
    struct.pack_into("<I", img, SP_VT + 4 * srcview.SLOT_PAD - BASE, labels["c_spad"] | 1)
    return labels, code
