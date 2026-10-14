"""SC40D (diagnostic; the user, 2026-10-12: «construye el diagnóstico»): can the mod write to the card about a second after the stock has saved a
project, from the chain of the LED task, without disturbing the stock's own save or the duplication of packs?  The answer decides how "Master FX per
session" is built (docs/NOTAS.md, «Estudio … Master FX por sesión»).

What it does, and nothing else: every time a project is saved (the bl to the stock save at 0x0802FE5E, in front of packio's and persist19's hooks)
a flag and the time are noted.  About a second later the LED task chain writes a mark into the padding of synth patch record 64 + n of the loaded
pack (n = the loaded project, parameter 8 of the Projects view's store; bank (64 + n) / 8, offset 512 x ((64 + n) % 8) + 340): the record (and the
bank file) that is missing is made of 0xFF, as the device does between patches; then it reads the mark back.  The Save button's LED shows the
result for ~3 s: green = written and read back the same, red = not.
The mark (16 bytes, the rest of the padding 0xFF): "FXD1", a counter (how many saves of this project it has seen), the project, the pack, 0xA5,
then the same eight bytes inverted.  tools/patchtool.py fxdiag PACK lists the marks from the PC.
Records 0..63 (the own-synth patches) and the 340 bytes of every synth patch are never written.  State: 4 bytes of the Master FX block's idle LED
buffer (c_gst() + 140): tag, phase (0 nothing, 1 a save seen, 2 written fine, 3 failed), the time.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, ldrh_imm, lsls_imm, lsrs_imm, mov_reg,  # noqa: E402
                   movs_imm, movt, movw, pop_list, push_list, raw, h, strb_imm, strh_imm, strh_reg, subs_reg)
import packio as PK  # noqa: E402
import persist19 as P19  # noqa: E402
import sesscopy as SCP  # noqa: E402

SAVE_CALL = P19.SAVE_CALL
PROJ_OBJ = 0x20044324                 # the Projects view: [+0x20] param 8 = the loaded project
ST_OFF, MAGIC = SCP.ST_OFF + 8, 0xD7
REC0 = 64                             # project n <-> synth patch record 64 + n
OFF, LEN = 340, 172
WAIT, SHOW = 4, 12                    # x 256 ms: after the save, the LED
LED_SAVE, COL_OK, COL_BAD = 57, 0x17, 0x53
MARK = b"FXD1"


def bl_target(img, addr, base):
    h1, h2 = struct.unpack_from("<HH", img, addr - base)
    assert h1 & 0xF800 == 0xF000 and h2 & 0xD000 == 0xD000, hex(addr)
    s = (h1 >> 10) & 1; j1 = (h2 >> 13) & 1; j2 = (h2 >> 11) & 1
    i1, i2 = 1 - (j1 ^ s), 1 - (j2 ^ s)
    off = s << 24 | i1 << 23 | i2 << 22 | (h1 & 0x3FF) << 12 | (h2 & 0x7FF) << 1
    if off & (1 << 24): off -= 1 << 25
    return addr + 4 + off


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def tick(rd): imm32(rd, PK.HAL_TICK); E(ldr_imm, rd, rd, 0); E(lsrs_imm, rd, rd, 8); E(lsls_imm, rd, rd, 16); E(lsrs_imm, rd, rd, 16)
    BUF = PK.BUF

    # ---- c_fdst() -> r0 = the state (tag written when the bytes were someone else's), 0 without the block; clobbers r1-r3
    a.label("c_fdst")
    E(push_list, [4], lr=True)
    E(bl, L["c_gst"]); E(cmp_imm, 0, 0); E(b_cond, "fs_x", "eq")
    E(adds_imm8, 0, ST_OFF)
    E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, MAGIC); E(b_cond, "fs_x", "eq")
    E(movs_imm, 1, MAGIC); E(strb_imm, 1, 0, 0); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 1)
    a.label("fs_x"); E(pop_list, [4], pc=True)

    # ---- c_fdsave (in the place of the bl to the stock save; r0 = the session manager): a save is noted, then the chain
    a.label("c_fdsave")
    E(push_list, [0, 1, 2, 3], lr=True)
    E(bl, "c_fdst"); E(cmp_imm, 0, 0); E(b_cond, "fv_x", "eq")
    E(mov_reg, 2, 0); E(movs_imm, 1, 1); E(strb_imm, 1, 2, 1); tick(0); E(strh_imm, 0, 2, 2)
    a.label("fv_x"); E(raw, popw([0, 1, 2, 3], lr=True)); E(b_w, prev["save"])

    # ---- c_fdwrite() -> r0 = 0 when the mark was written and read back the same
    a.label("c_fdwrite")
    E(push_list, [4, 5, 6, 7], lr=True)
    imm32(0, PROJ_OBJ); E(ldr_imm, 0, 0, 0x20); E(movs_imm, 1, 8); E(bl, PK.PARAM_GET); E(ldrb_imm, 5, 0, 0)       # r5 = the project
    E(movs_imm, 0, 63); E(ands_reg, 5, 0)
    E(mov_reg, 4, 5); E(adds_imm8, 4, REC0)                                           # r4 = the record
    E(lsls_imm, 6, 4, 29); E(lsrs_imm, 6, 6, 20)                                      # r6 = 512 x (record % 8)
    E(movs_imm, 0, 5); E(bl, PK.BUF_LOCK)
    E(lsrs_imm, 0, 4, 3); E(bl, L["c_mpsz"]); E(mov_reg, 7, 0)                        # r7 = the bank's size
    # the count so far (the mark that is there, if it is ours)
    E(push_list, [5])
    E(movs_imm, 5, 0)
    imm32(0, OFF + 16); E(adds_reg, 0, 0, 6); E(cmp_reg, 7, 0); E(b_cond, "fw_new", "lo")
    E(lsrs_imm, 0, 4, 3); imm32(1, OFF); E(adds_reg, 1, 1, 6); imm32(2, BUF); E(movs_imm, 3, 16); E(bl, L["c_mpr"]); E(cmp_imm, 0, 0); E(b_cond, "fw_new", "ne")
    imm32(0, BUF); E(ldr_imm, 1, 0, 0); imm32(2, struct.unpack("<I", MARK)[0]); E(cmp_reg, 1, 2); E(b_cond, "fw_new", "ne")
    E(ldrb_imm, 5, 0, 4)
    a.label("fw_new")
    E(adds_imm8, 5, 1); E(mov_reg, 1, 5); E(pop_list, [5]); E(push_list, [1])         # [sp] = the new count
    # what is missing up to the padding: 0xFF
    imm32(0, OFF); E(adds_reg, 0, 0, 6); E(cmp_reg, 7, 0); E(b_cond, "fw_pad", "hs")
    E(subs_reg, 1, 0, 7); E(push_list, [1]); imm32(0, BUF); E(movs_imm, 2, 0xFF); E(bl, PK.MEMSET)
    E(pop_list, [3]); E(lsrs_imm, 0, 4, 3); E(mov_reg, 1, 7); imm32(2, BUF); E(bl, L["c_mpw"]); E(cmp_imm, 0, 0); E(b_cond, "fw_f", "ne")
    a.label("fw_pad")
    # the padding: the mark, then 0xFF
    imm32(0, BUF); E(movs_imm, 1, LEN); E(movs_imm, 2, 0xFF); E(bl, PK.MEMSET)
    imm32(7, BUF); imm32(0, struct.unpack("<I", MARK)[0]); E(raw, h(0x6038))           # str r0, [r7]
    E(raw, h(0x9800)); E(strb_imm, 0, 7, 4); E(strb_imm, 5, 7, 5)                      # (ldr r0, [sp]) the count, the project
    E(bl, L["c_curpack"]); E(strb_imm, 0, 7, 6); E(movs_imm, 0, 0xA5); E(strb_imm, 0, 7, 7)
    for i in range(8): E(ldrb_imm, 0, 7, i); E(raw, h(0x43C0)); E(strb_imm, 0, 7, 8 + i)        # (mvns r0, r0) the same eight bytes inverted
    E(lsrs_imm, 0, 4, 3); imm32(1, OFF); E(adds_reg, 1, 1, 6); imm32(2, BUF); E(movs_imm, 3, LEN); E(bl, L["c_mpw"]); E(cmp_imm, 0, 0); E(b_cond, "fw_f", "ne")
    # read back into BUF + 256 and compare the 16 bytes
    E(lsrs_imm, 0, 4, 3); imm32(1, OFF); E(adds_reg, 1, 1, 6); imm32(2, BUF + 256); E(movs_imm, 3, 16); E(bl, L["c_mpr"]); E(cmp_imm, 0, 0); E(b_cond, "fw_f", "ne")
    E(cmp_imm, 1, 16); E(b_cond, "fw_f", "ne")
    imm32(2, BUF + 256)
    for o in (0, 4, 8, 12): E(ldr_imm, 0, 7, o); E(ldr_imm, 1, 2, o); E(cmp_reg, 0, 1); E(b_cond, "fw_f", "ne")
    E(movs_imm, 6, 0); E(b, "fw_u")
    a.label("fw_f"); E(movs_imm, 6, 1)
    a.label("fw_u"); E(pop_list, [1]); E(bl, PK.BUF_UNLOCK); E(mov_reg, 0, 6)
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_fdledtask (the LED task calls: ctrl, frame): the chain; a second after a save: the write; then the Save LED green / red for a while
    a.label("c_fdledtask")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    E(bl, "c_fdst"); E(mov_reg, 7, 0); E(cmp_imm, 7, 0); E(b_cond, "fl_x", "eq")
    E(ldrb_imm, 6, 7, 1); E(cmp_imm, 6, 0); E(b_cond, "fl_x", "eq")
    tick(0); E(ldrh_imm, 1, 7, 2); E(subs_reg, 0, 0, 1); E(lsls_imm, 0, 0, 16); E(lsrs_imm, 0, 0, 16); E(mov_reg, 4, 0)      # r4 = the time gone
    E(cmp_imm, 6, 1); E(b_cond, "fl_show", "ne")
    E(cmp_imm, 4, WAIT); E(b_cond, "fl_x", "lo")
    E(bl, "c_fdwrite"); E(adds_imm8, 0, 2); E(strb_imm, 0, 7, 1); tick(0); E(strh_imm, 0, 7, 2); E(b, "fl_x")
    a.label("fl_show")
    E(cmp_imm, 4, SHOW); E(b_cond, "fl_on", "lo")
    E(movs_imm, 0, 0); E(strb_imm, 0, 7, 1); E(b, "fl_x")
    a.label("fl_on")
    E(movs_imm, 2, COL_OK); E(cmp_imm, 6, 2); E(b_cond, "fl_c", "eq"); E(movs_imm, 2, COL_BAD)
    a.label("fl_c"); E(movs_imm, 0, 2 * LED_SAVE); E(strh_reg, 2, 5, 0)
    a.label("fl_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the bl to the save and the two LED task calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    lab = lambda sec, n: int(report[sec]["labels"][n], 16)
    L = dict(c_gst=lab("sc14", "c_gst"), c_curpack=lab("packio", "c_curpack"), **{n: lab("mpatch", n) for n in ("c_mpsz", "c_mpr", "c_mpw")})
    prev = dict(save=bl_target(img, SAVE_CALL, BASE), ledtask=lab("sesscopy", "c_scledtask"))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[SAVE_CALL - BASE:SAVE_CALL - BASE + 4] = bl(SAVE_CALL, labels["c_fdsave"])
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_fdledtask"])
    return labels, code, prev
