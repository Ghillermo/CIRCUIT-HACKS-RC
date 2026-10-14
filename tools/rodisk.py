"""SC41.3 / RC0.9 (the user, 2026-10-14: «implementa sólo lectura en pack interno»): nothing of the mod writes or deletes in the pack of the
Circuit's internal memory.

Found in the firmware: the storage task's pack switch (0x0803676C) takes pack 0 to the volume of [0x2000690C] (drive 0: the internal memory; the RAM
dump has "0:/Tracks/00_Synthwave" there while the card holds "10_Synthwave") and every other pack to [0x20006910] (drive 1: the microSD card, packs
1-31); 0xFF = the loaded pack ([[0x20006914]] byte 0), 0xFE = none.  Every write of the mod (the captured sample saved with the project, the
exchanges and copies of samples and patches between packs, the own-synth patches, the synth patch save, the copy of projects, the deletion of a
pack) goes through two stock entry points: 0x0803CC16 (op 7, write) and 0x0803CC34 (op 5, delete), item = u32 kind, u32 index, u8 pack.

Both entry points get a guard (their first 4 bytes -> b.w; the 4 bytes are moved into the guard): a call from the mod's code (return address in the
mod's area, from 0x0805CDDC) on an item of pack 0, or of 0xFF while pack 0 is loaded, returns «failed» (0xFFFFFFFD) without touching the memory,
and the Save LED shows red for 1.5 s.  The stock's own writes (its project saves, its patch writes) are never stopped.  Reading the internal pack
stays possible: copying from it to a pack of the card writes only on the card.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, mov_reg, movs_imm, movt, movw, pop_list, push_list, raw, h, str_imm,  # noqa: E402
                   strh_reg, subs_reg, b)
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402

WRITE, DELETE = 0x0803CC16, 0x0803CC34
OLD = {WRITE: bytes.fromhex("5cb585b0"), DELETE: bytes.fromhex("13460022")}      # push {r2, r3, r4, r6, lr}; sub sp, #0x14 / mov r3, r2; movs r2, #0
MOD_START = 0x0805CDDC                                        # the mod's code: the caves and what is appended after the stock image
CUR_PACK = 0x20006914                                         # [[it]] byte 0 = the loaded pack
INTERNAL = 0
SESSION_OBJ, TAIL, T_OFF = 0x2003D71C, 0x27024, 276           # the time of the last refusal: the record's tail + 276 (after the LED buffer, 192..275)
HAL_TICK = 0x2000081C
LED_SAVE, COL_NO, SHOW_MS = 57, 0x53, 1500
FAIL = 0xFFFFFFFD


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_rointernal (r0 = an item) -> r0 = 1 when it is in the internal pack; clobbers r1
    a.label("c_rointernal")
    E(ldrb_imm, 1, 0, 8); E(cmp_imm, 1, 0xFF); E(b_cond, "ri_c", "ne")
    imm32(1, CUR_PACK); E(ldr_imm, 1, 1, 0); E(ldrb_imm, 1, 1, 0)
    a.label("ri_c"); E(movs_imm, 0, 0); E(cmp_imm, 1, INTERNAL); E(b_cond, "ri_x", "ne"); E(movs_imm, 0, 1)
    a.label("ri_x"); E(raw, h(0x4770))

    # ---- c_rowr / c_rodel (in place of the first 4 bytes of the stock's write / delete): the mod's calls on the internal pack fail
    for name, fn in (("c_rowr", WRITE), ("c_rodel", DELETE)):
        a.label(name)
        E(raw, pushw([0, 1, 2, 3], lr=True))
        imm32(1, MOD_START)
        E(mov_reg, 2, 14); E(cmp_reg, 2, 1); E(b_cond, f"{name}_p", "lo")              # (lr below the mod's area: a stock caller)
        E(bl, "c_rointernal"); E(cmp_imm, 0, 0); E(b_cond, f"{name}_p", "eq")
        E(bl, "c_ronote")
        E(raw, popw([0, 1, 2, 3], lr=True)); imm32(0, FAIL); E(raw, h(0x4770))
        a.label(f"{name}_p")
        E(raw, popw([0, 1, 2, 3], lr=True)); E(raw, OLD[fn]); E(b_w, fn + 4)

    # ---- c_ronote(): the time of this refusal, for the LED; clobbers r0-r2
    a.label("c_ronote")
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "rn_x", "eq")
    imm32(1, TAIL + T_OFF); imm32(2, HAL_TICK); E(ldr_imm, 2, 2, 0)
    E(raw, h(0x1840))                                                             # adds r0, r0, r1
    E(str_imm, 2, 0, 0)
    a.label("rn_x"); E(raw, h(0x4770))

    # ---- c_roledtask (the LED task calls: ctrl, frame): the chain; a refusal within 1.5 s: the Save LED red
    a.label("c_roledtask")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "rl_x", "eq")
    imm32(1, TAIL + T_OFF); E(raw, h(0x1840)); E(ldr_imm, 1, 0, 0); E(cmp_imm, 1, 0); E(b_cond, "rl_x", "eq")
    imm32(2, HAL_TICK); E(ldr_imm, 2, 2, 0); E(subs_reg, 2, 2, 1); imm32(3, SHOW_MS); E(cmp_reg, 2, 3); E(b_cond, "rl_x", "hs")
    E(movs_imm, 2, COL_NO); E(movs_imm, 0, 2 * LED_SAVE); E(strh_reg, 2, 5, 0)
    a.label("rl_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the first 4 bytes of the stock's write and delete, the two LED task calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    for fn, old in OLD.items():
        assert bytes(img[fn - BASE:fn - BASE + 4]) == old, hex(fn)
    prev = dict(ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[WRITE - BASE:WRITE - BASE + 4] = b_w(WRITE, labels["c_rowr"])
    img[DELETE - BASE:DELETE - BASE + 4] = b_w(DELETE, labels["c_rodel"])
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_roledtask"])
    return labels, code, prev
