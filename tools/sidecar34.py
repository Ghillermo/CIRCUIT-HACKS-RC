"""SC34D (DIAGNOSTIC): our own file next to each session on the SD card, written / read through the stock file class, in the stock storage task.

The stock file class (`FatFs_File`, vtable 0x0805B150: slot 0 open 0x08025CB8 (obj, path; f_open mode 0x13 = read | write | open always; the path is copied to
obj + 0xD), slot 1 close 0x08025D10, slot 4 read 0x08025D4C (obj, buf, len, offset, *done), slot 5 write 0x08025D98 (obj, buf, len, offset, *done)); two objects
exist ([0x20003738] / [0x2000373C]) with their 4 KB FatFs buffers.  Every session load / save goes through them.
  * c_sw (slot 5) / c_sr (slot 4): when the open file's path ends with "_SESSION.ncs", bit 6 (written) / bit 7 (read) of the Master FX block byte 179 is set;
    then the stock function runs with the registers and the stack as they came (the fifth argument is on the stack);
  * c_sc (slot 1): the stock close runs; then, if a bit is set (cleared first): the same object opens "<the session path without _SESSION.ncs>_SC34D.bin",
    reads its 16 bytes ("SC34DTST", saves u32, loads u32; a new / short / foreign file starts from 0), counts the save or the load, writes the 16 bytes back
    and closes.  Our calls go to the stock functions directly (not through the vtable): no recursion.  Nothing else is touched: the stock files stay as they are.
Check: the card in a PC: a "NN_SC34D.bin" next to every session saved, its counters going up with every save / load of that session.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw, adds_imm8, subs_imm8,  # noqa: E402
                   pop_list, push_list, raw, h, tst_reg, ands_reg, orrs_reg, bics_reg, adds_reg, subs_reg, str_imm, strb_imm, ldrb_reg, strb_reg,
                   add_sp_imm, sub_sp_imm, ldrb_w, strb_w, str_sp, ldr_sp)

FVT = 0x0805B150
F_OPEN, F_CLOSE, F_READ, F_WRITE = 0x08025CB8, 0x08025D10, 0x08025D4C, 0x08025D98
SLOT_CLOSE, SLOT_READ, SLOT_WRITE = 1, 4, 5
PATH_OFF = 0x0D
FLAGS = 179
B_WR, B_RD = 0x40, 0x80
SUFFIX = b"_SESSION.ncs"
NEWSUF = b"_SC34D.bin"
MAGIC = b"SC34DTST"
PATHMAX = 120


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


INV = {"eq": "ne", "ne": "eq", "lo": "hs", "hs": "lo"}


def arm_code(base, L):
    a = Asm(base)
    zc = [0]

    def bc(target, cond):                           # conditional branch, +-2 KB
        zc[0] += 1; n = f"_s{zc[0]}"
        a.emit(b_cond, n, INV[cond]); a.emit(b, target); a.label(n)

    # ---- c_ssuf (r0 = file object) -> r0 = the length of the path when it ends with "_SESSION.ncs", else 0; clobbers r1-r3
    a.label("c_ssuf")
    a.emit(push_list, [4, 5], lr=True)
    a.emit(adds_imm8, 0, PATH_OFF); a.emit(mov_reg, 4, 0); a.emit(movs_imm, 5, 0)
    a.label("su_l"); a.emit(ldrb_reg, 1, 4, 5); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "su_e", "eq")
    a.emit(adds_imm8, 5, 1); a.emit(cmp_imm, 5, PATHMAX); a.emit(b_cond, "su_l", "lo"); a.emit(b, "su_no")
    a.label("su_e"); a.emit(cmp_imm, 5, len(SUFFIX)); a.emit(b_cond, "su_no", "lo")
    for i, ch in enumerate(SUFFIX):
        a.emit(mov_reg, 2, 5); a.emit(subs_imm8, 2, len(SUFFIX) - i); a.emit(ldrb_reg, 1, 4, 2)
        a.emit(cmp_imm, 1, ch); a.emit(b_cond, "su_no", "ne")
    a.emit(mov_reg, 0, 5); a.emit(pop_list, [4, 5], pc=True)
    a.label("su_no"); a.emit(movs_imm, 0, 0); a.emit(pop_list, [4, 5], pc=True)

    # ---- c_sflag (r0 = file object, r1 = bit): the bit in byte 179 when the object's file is a session; clobbers r0-r3
    a.label("c_sflag")
    a.emit(push_list, [4], lr=True)
    a.emit(mov_reg, 4, 1); a.emit(bl, "c_ssuf"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sf_x", "eq")
    a.emit(bl, L["c_gfst"]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sf_x", "eq")
    a.emit(ldrb_w, 1, 0, FLAGS); a.emit(orrs_reg, 1, 4); a.emit(strb_w, 1, 0, FLAGS)
    a.label("sf_x"); a.emit(pop_list, [4], pc=True)

    for name, bit, orig in (("c_sw", B_WR, F_WRITE), ("c_sr", B_RD, F_READ)):
        # ---- c_sw / c_sr: vtable slot 5 / 4: mark, then the stock function with the registers and the stack untouched
        a.label(name)
        a.emit(push_list, [0, 1, 2, 3, 4], lr=True)
        a.emit(movs_imm, 1, bit); a.emit(bl, "c_sflag")
        a.emit(raw, popw([0, 1, 2, 3, 4], lr=True)); a.emit(b_w, orig)

    # ---- c_sc: vtable slot 1 (close): the stock close, then our file when a session was read / written
    a.label("c_sc")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(bl, F_CLOSE); a.emit(mov_reg, 7, 0)              # r7 = the stock result
    a.emit(bl, L["c_gfst"]); a.emit(cmp_imm, 0, 0); bc("sc_x", "eq")
    a.emit(ldrb_w, 1, 0, FLAGS); a.emit(movs_imm, 2, B_WR | B_RD); a.emit(mov_reg, 6, 1); a.emit(ands_reg, 6, 2)
    a.emit(cmp_imm, 6, 0); bc("sc_x", "eq")
    a.emit(bics_reg, 1, 2); a.emit(strb_w, 1, 0, FLAGS)                            # r6 = what happened; cleared
    a.emit(mov_reg, 0, 4); a.emit(bl, "c_ssuf"); a.emit(cmp_imm, 0, 0); bc("sc_x", "eq")
    a.emit(mov_reg, 5, 0)                                                          # r5 = path length
    a.emit(sub_sp_imm, 152)                                                        # sp + 0: 16 data, sp + 16: count, sp + 24: path
    a.emit(movs_imm, 2, 0)
    a.label("sc_cp")                                                               # the path without the suffix
    a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, PATH_OFF); a.emit(ldrb_reg, 1, 0, 2)
    a.emit(mov_reg, 0, 13); a.emit(adds_imm8, 0, 24); a.emit(strb_reg, 1, 0, 2)
    a.emit(adds_imm8, 2, 1); a.emit(mov_reg, 3, 5); a.emit(subs_imm8, 3, len(SUFFIX)); a.emit(cmp_reg, 2, 3); a.emit(b_cond, "sc_cp", "lo")
    for i, ch in enumerate(NEWSUF + b"\0"):
        a.emit(movs_imm, 1, ch); a.emit(strb_reg, 1, 0, 2); a.emit(adds_imm8, 2, 1)
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 13); a.emit(adds_imm8, 1, 24); a.emit(bl, F_OPEN)
    a.emit(cmp_imm, 0, 0); bc("sc_fr", "ne")                          # could not open: nothing more
    for i in range(4): a.emit(movs_imm, 0, 0); a.emit(str_sp, 0, 4 * i)       # the data starts at zero
    a.emit(mov_reg, 0, 13); a.emit(adds_imm8, 0, 16); a.emit(str_sp, 0, 20)  # (sp + 20 = &count, pushed as the fifth argument below)
    a.emit(raw, h(0xB082))                                                         # sub sp, #8: the fifth argument
    a.emit(ldr_sp, 0, 28); a.emit(str_sp, 0, 0)
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 13); a.emit(adds_imm8, 1, 8); a.emit(movs_imm, 2, 16); a.emit(movs_imm, 3, 0); a.emit(bl, F_READ)
    a.emit(raw, h(0xB002))                                                         # add sp, #8
    for i in range(0, 8, 4):                                                       # not ours (or short): start again
        a.emit(ldr_sp, 0, i); a.emit(movw, 1, int.from_bytes(MAGIC[i:i + 2], "little")); a.emit(movt, 1, int.from_bytes(MAGIC[i + 2:i + 4], "little"))
        a.emit(cmp_reg, 0, 1); a.emit(b_cond, "sc_new", "ne")
    a.emit(b, "sc_cnt")
    a.label("sc_new")
    for i in range(0, 8, 4):
        a.emit(movw, 1, int.from_bytes(MAGIC[i:i + 2], "little")); a.emit(movt, 1, int.from_bytes(MAGIC[i + 2:i + 4], "little")); a.emit(str_sp, 1, i)
    a.emit(movs_imm, 0, 0); a.emit(str_sp, 0, 8); a.emit(str_sp, 0, 12)
    a.label("sc_cnt")
    a.emit(movs_imm, 0, B_WR); a.emit(tst_reg, 6, 0); a.emit(b_cond, "sc_nw", "eq")
    a.emit(ldr_sp, 0, 8); a.emit(adds_imm8, 0, 1); a.emit(str_sp, 0, 8)
    a.label("sc_nw")
    a.emit(movs_imm, 0, B_RD); a.emit(tst_reg, 6, 0); a.emit(b_cond, "sc_nr", "eq")
    a.emit(ldr_sp, 0, 12); a.emit(adds_imm8, 0, 1); a.emit(str_sp, 0, 12)
    a.label("sc_nr")
    a.emit(raw, h(0xB082))
    a.emit(ldr_sp, 0, 28); a.emit(str_sp, 0, 0)
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 13); a.emit(adds_imm8, 1, 8); a.emit(movs_imm, 2, 16); a.emit(movs_imm, 3, 0); a.emit(bl, F_WRITE)
    a.emit(raw, h(0xB002))
    a.label("sc_fr")
    a.emit(mov_reg, 0, 4); a.emit(bl, F_CLOSE)
    a.emit(add_sp_imm, 152)
    a.label("sc_x"); a.emit(mov_reg, 0, 7); a.emit(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    import ct_fw
    BASE = ct_fw.APP_BASE
    vt = [struct.unpack_from("<I", img, FVT + 4 * i - BASE)[0] for i in range(6)]
    assert vt[SLOT_CLOSE] == F_CLOSE | 1 and vt[SLOT_READ] == F_READ | 1 and vt[SLOT_WRITE] == F_WRITE | 1 and vt[0] == F_OPEN | 1, [hex(x) for x in vt]
    L = dict(c_gfst=int(report["sc17"]["labels"]["c_gfst"], 16))
    code, labels = arm_code(base_addr, L)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    for slot, lab in ((SLOT_CLOSE, "c_sc"), (SLOT_READ, "c_sr"), (SLOT_WRITE, "c_sw")):
        struct.pack_into("<I", img, FVT + 4 * slot - BASE, labels[lab] | 1)
    return labels, code
