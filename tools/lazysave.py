"""The settings save of the mod, deferred (the user, 2026-10-15: «stutter audibles (de ritmo) sobre el delay al cambiar entre modos de sinte o mover sus
perillas»; with S419D2 the stutter came with Duplicate blue = an SD access of the stock code during a main-loop gap).

The cause: the own engine of MIDI 1 / 2 keeps its state in the global settings record, and the mod saved it with the stock's settings save 0x0802D2AC
(which writes the settings file to the card through the storage task and waits for it): vcf21's c_vsave at most every 700 ms while a knob turns, and
straight away on every toggle (pad 27 and the others), mpatch after loading / saving a patch.  The main loop waits for the write: no DSP service, no
UI for that time, and the delay's tempo-synced timing hiccups.

Now: the first 4 bytes of 0x0802D2AC go to c_lzsave.  Called from the mod's code (LR from 0x0805CDDC up to the end of the flash) it only marks the save
as pending with the time (the record's tail + 186 = 0xA5, + 188 = the time); called from the stock (its settings listener) it runs as always.  The LED
task (c_lzled, head of the chain) writes a pending save with the transport stopped and 2 s after the last request.  RAM only: a project load drops a
pending save (the next change asks again); turning the unit off while playing loses the last changes of the engine.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, mov_reg, movs_imm, movt, movw, pop_list, push_list, raw, h, str_imm, subs_reg, adds_reg  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402

SAVE_IN, SAVE_BACK, SAVE_OLD = 0x0802D2AC, 0x0802D2B0, bytes.fromhex("2de9f047")   # push.w {r4-sl, lr}
SETOBJ = 0x2003974C
MOD_START, FLASH_END = 0x0805CDDC, 0x08080000
SESSION_OBJ, TAIL, O_PEND, O_TIME = 0x2003D71C, 0x27024, 186, 188
PEND = 0xA5
HAL_TICK, TRANSPORT, PARAM_GET = 0x2000081C, 0x20011034, 0x0803542C
QUIET_MS = 2000


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def ldrb_w_(rt, rn, off): return h(0xF890 | rn) + h(rt << 12 | off)
def strb_w_(rt, rn, off): return h(0xF880 | rn) + h(rt << 12 | off)
def ldr_w_(rt, rn, off): return h(0xF8D0 | rn) + h(rt << 12 | off)
def str_w_(rt, rn, off): return h(0xF8C0 | rn) + h(rt << 12 | off)


def arm_code(base, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_lztail() -> r0 = the record's tail, or 0; clobbers r1
    a.label("c_lztail")
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "lt_x", "eq")
    imm32(1, TAIL); E(adds_reg, 0, 0, 1)
    a.label("lt_x"); E(raw, h(0x4770))

    # ---- c_lzrun(r0 = the settings object): the stock save itself (its first 4 bytes, then the rest)
    a.label("c_lzrun")
    E(raw, SAVE_OLD); E(b_w, SAVE_BACK)

    # ---- c_lzsave (the first 4 bytes of the stock save): from the mod's code only marked as pending
    a.label("c_lzsave")
    E(raw, pushw([0, 1, 2, 3, 12], lr=True))
    E(mov_reg, 0, 14); imm32(1, MOD_START); E(cmp_reg, 0, 1); E(b_cond, "ls_s", "lo")
    imm32(1, FLASH_END); E(cmp_reg, 0, 1); E(b_cond, "ls_s", "hs")
    E(bl, "c_lztail"); E(cmp_imm, 0, 0); E(b_cond, "ls_s", "eq")                         # (no record: saved as always)
    E(movs_imm, 1, PEND); E(raw, strb_w_(1, 0, O_PEND))
    imm32(1, HAL_TICK); E(ldr_imm, 1, 1, 0); E(raw, str_w_(1, 0, O_TIME))
    E(raw, popw([0, 1, 2, 3, 12], lr=True)); E(raw, h(0x4770))
    a.label("ls_s"); E(raw, popw([0, 1, 2, 3, 12], lr=True)); E(b_w, "c_lzrun")

    # ---- c_lzled (the LED task calls: ctrl, frame): the chain, then a pending save once stopped and quiet
    a.label("c_lzled")
    E(push_list, [4], lr=True)
    E(bl, prev["ledtask"])
    E(bl, "c_lztail"); E(cmp_imm, 0, 0); E(b_cond, "ll_x", "eq"); E(mov_reg, 4, 0)
    E(raw, ldrb_w_(0, 4, O_PEND)); E(cmp_imm, 0, PEND); E(b_cond, "ll_x", "ne")
    imm32(0, TRANSPORT); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(raw, h(0x7800)); E(cmp_imm, 0, 0); E(b_cond, "ll_x", "ne")   # ldrb r0, [r0]
    imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(raw, ldr_w_(1, 4, O_TIME)); E(subs_reg, 0, 0, 1)
    imm32(1, QUIET_MS); E(cmp_reg, 0, 1); E(b_cond, "ll_x", "lo")
    E(movs_imm, 0, 0); E(raw, strb_w_(0, 4, O_PEND))
    imm32(0, SETOBJ); E(bl, "c_lzrun")
    a.label("ll_x"); E(pop_list, [4], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the first 4 bytes of the stock settings save, the LED task calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    prev = dict(ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    assert bytes(img[SAVE_IN - BASE:SAVE_IN - BASE + 4]) == SAVE_OLD, bytes(img[SAVE_IN - BASE:SAVE_IN - BASE + 4]).hex()
    code, labels = arm_code(base_addr, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[SAVE_IN - BASE:SAVE_IN - BASE + 4] = b_w(SAVE_IN, labels["c_lzsave"])
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_lzled"])
    return labels, code, prev
