"""SC402D (diagnostic, 2026-10-13): are the last 1000 bytes of a project free?

The session record (what Sessions/NN_SESSION.ncs holds, 160 780 = 0x2740C bytes, kept whole in RAM at [0x2003D71C + 0x14]) ends with 1000 bytes
that are zero in the RAM dump and that no literal of the firmware addresses (0x27024 = the end of the last blob the stock writes, the project
parameters; the next literal is the size, 0x2740C).  The stock saves and loads the record whole, so if nothing else writes them they are 1000
bytes per project that travel with it without any card access of ours: the place for "Master FX per session" and more.
The probe: right before the stock saves a project (the bl at 0x0802FE5E, in front of the other hooks) it writes "TAIL" + a count at the start of
that tail and "END!" in its last four bytes, in the RAM record: the stock then saves them.  The Save LED shows what the loaded project carries:
green = both marks, red = only one of them, as the stock = none.  So: save (green), switch off, load: green = the bytes survive.
tools/patchtool.py sessdiag PACK reads the marks from the card on the PC.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, mov_reg, movs_imm, movt, movw, pop_list, push_list,  # noqa: E402
                   raw, h, str_imm, strb_imm, strh_reg)
import packio as PK  # noqa: E402
import persist19 as P19  # noqa: E402
import fxdiag as FD  # noqa: E402

SAVE_CALL = P19.SAVE_CALL
SESSION_OBJ = P19.SESSION_OBJ
TAIL, TAIL_LEN = 0x27024, 1000
M1, M2 = struct.unpack("<I", b"TAIL")[0], struct.unpack("<I", b"END!")[0]
LED_SAVE, COL_OK, COL_BAD = 57, 0x17, 0x53


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def tail(rd): imm32(rd, SESSION_OBJ); E(ldr_imm, rd, rd, 0x14); imm32(3, TAIL); E(adds_reg, rd, rd, 3)      # rd = the tail of the record (clobbers r3)

    # ---- c_tdsave (in the place of the bl to the stock save): the marks into the record, then the chain
    a.label("c_tdsave")
    E(push_list, [0, 1, 2, 3], lr=True)
    tail(0)
    E(ldr_imm, 1, 0, 0); imm32(2, M1); E(movs_imm, 3, 0); E(cmp_reg, 1, 2); E(b_cond, "ts_n", "ne"); E(ldrb_imm, 3, 0, 4)
    a.label("ts_n"); E(adds_imm8, 3, 1); E(str_imm, 2, 0, 0); E(strb_imm, 3, 0, 4)
    imm32(1, TAIL_LEN - 4); E(adds_reg, 0, 0, 1); imm32(2, M2); E(str_imm, 2, 0, 0)
    E(raw, popw([0, 1, 2, 3], lr=True)); E(b_w, prev["save"])

    # ---- c_tdledtask (the LED task calls: ctrl, frame): the chain; the Save LED = what the loaded project carries
    a.label("c_tdledtask")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    tail(0)
    E(movs_imm, 4, 0)
    E(ldr_imm, 1, 0, 0); imm32(2, M1); E(cmp_reg, 1, 2); E(b_cond, "tl_1", "ne"); E(adds_imm8, 4, 1)
    a.label("tl_1")
    imm32(1, TAIL_LEN - 4); E(adds_reg, 0, 0, 1); E(ldr_imm, 1, 0, 0); imm32(2, M2); E(cmp_reg, 1, 2); E(b_cond, "tl_2", "ne"); E(adds_imm8, 4, 1)
    a.label("tl_2")
    E(cmp_imm, 4, 0); E(b_cond, "tl_x", "eq")
    E(movs_imm, 2, COL_OK); E(cmp_imm, 4, 2); E(b_cond, "tl_c", "eq"); E(movs_imm, 2, COL_BAD)
    a.label("tl_c"); E(movs_imm, 0, 2 * LED_SAVE); E(strh_reg, 2, 5, 0)
    a.label("tl_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the bl to the save and the two LED task calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    prev = dict(save=FD.bl_target(img, SAVE_CALL, BASE), ledtask=int(report["compkn"]["labels"]["c_ckledtask"], 16))
    code, labels = arm_code(base_addr, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[SAVE_CALL - BASE:SAVE_CALL - BASE + 4] = bl(SAVE_CALL, labels["c_tdsave"])
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_tdledtask"])
    return labels, code, prev
