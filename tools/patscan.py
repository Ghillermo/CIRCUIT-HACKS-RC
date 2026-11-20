"""S714D (diagnostic, 2026-11-20; the user: «Pending bugs … how can we force them / investigate in the unit?» -> «Yes»): who leaves an impossible value in a
pattern (a note step's probability > 7, a unit mask with bits 6-7, a unit velocity > 127, a drum velocity > 127: the values behind the 5.63 / 5.64
crashes that paintguard skips)?  The A7PROT crash turned out to be incoming MIDI (CC 27, cc27fix), so the record also keeps the last MIDI in.

  * c_psmi, in front of the MIDI-in dispatcher's helper (0x08051720 + 2: bl 0x0805CE46, the injection helper of SC05): each message (r1 -> its
    bytes) into a ring of 12 (+ 0 the HAL tick, + 4 status, d1, d2, the port flags [ctx + 0x14]); RAM MRING (sig "MRG1", + 4 the index, + 16 the
    entries, 8 B each);
  * c_psc, a head of the LED task (LR / frame in RAM, nothing on the stack while the chain below runs): one pattern per frame (the 4 note tracks x 8
    and the 4 drums x 8 = 64: about a second for all), every step checked as tools/bytewatch.py does; the first find freezes the black box (state
    0x85, as paintguard; not when a record is already frozen): STK1 = tag 3, the value, its address, then the MIDI ring (16 + 96 B).
The pattern addresses are the session record's (fixed: the heap is laid out the same at every boot; bytewatch's NOTE / DRUM).  RAM 0x2004FB84 (12 B:
+ 0 LR, + 4 frame, + 8 the cursor) and 0x2004FB90..0x2004FBFF (the ring).  In dspz's first gap."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, lsls_imm, mov_reg, movs_imm, movt, movw,  # noqa: E402
                   pop_list, push_list, raw, str_imm, strb_imm, subs_imm8)
import bytewatch as BW  # noqa: E402
import fxdiag as FD  # noqa: E402
import packio as PK  # noqa: E402

ST = 0x2004FB84                       # + 0 LR, + 4 frame, + 8 cursor (0..63)
MRING, NRING = 0x2004FB90, 12         # + 0 "MRG1", + 4 index, + 16 entries
SIG = struct.unpack("<I", b"MRG1")[0]
HAL_TICK = 0x2000081C
HELPER_SITE, HELPER = 0x08051722, 0x0805CE46
NOTE = [b for _, b in BW.NOTE]
DRUM = [b for _, b in BW.DRUM]
NPAT, DPAT = BW.NPAT, BW.DPAT
assert MRING + 16 + 8 * NRING <= 0x2004FC00 and ST + 12 <= MRING


def arm_code(base, prev, freeze, bb):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_psmi(r0 = ctx, r1 = the message): the ring, then the helper (r0 / r1 kept, LR kept: a tail call)
    a.label("c_psmi")
    E(push_list, [0, 1, 2, 3])
    imm32(2, MRING); E(ldr_imm, 3, 2, 0); imm32(0, SIG); E(cmp_reg, 3, 0); E(b_cond, "mi_ok", "eq")
    E(str_imm, 0, 2, 0); E(movs_imm, 0, 0); E(str_imm, 0, 2, 4)
    a.label("mi_ok")
    E(ldr_imm, 3, 2, 4); E(cmp_imm, 3, NRING); E(b_cond, "mi_i", "lo"); E(movs_imm, 3, 0)
    a.label("mi_i")
    E(lsls_imm, 0, 3, 3); E(adds_reg, 0, 0, 2); E(adds_imm8, 0, 16)                 # r0 = the entry
    E(adds_imm8, 3, 1); E(str_imm, 3, 2, 4)                                       # the next index
    imm32(3, HAL_TICK); E(ldr_imm, 3, 3, 0); E(str_imm, 3, 0, 0)
    E(raw, h(0x9901))                                                             # ldr r1, [sp, #4]: the message pointer (pushed r1)
    E(ldrb_imm, 3, 1, 0); E(strb_imm, 3, 0, 4); E(ldrb_imm, 3, 1, 1); E(strb_imm, 3, 0, 5); E(ldrb_imm, 3, 1, 2); E(strb_imm, 3, 0, 6)
    E(raw, h(0x9900)); E(ldrb_imm, 3, 1, 0x14); E(strb_imm, 3, 0, 7)              # ldr r1, [sp]: the context's port flags
    E(pop_list, [0, 1, 2, 3]); E(b_w, HELPER)

    # ---- c_psc (the LED task's calls: ctrl, frame)
    a.label("c_psc")
    imm32(2, ST); E(raw, h(0xF8C2) + h(0xE000)); E(str_imm, 1, 2, 4)              # str.w lr, [r2]; str r1, [r2, #4]
    E(bl, prev["led"])
    E(push_list, [4, 5, 6, 7])
    imm32(0, bb.BB); E(ldrb_imm, 1, 0, bb.O.ST); E(lsls_imm, 1, 1, 31); E(b_cond, "sc_x", "mi")   # a record frozen: nothing
    imm32(6, ST); E(ldrb_imm, 7, 6, 8); E(adds_imm8, 7, 1); E(cmp_imm, 7, 64); E(b_cond, "sc_c", "lo"); E(movs_imm, 7, 0)
    a.label("sc_c"); E(strb_imm, 7, 6, 8)
    E(cmp_imm, 7, 32); E(b_cond, "sc_d", "hs")
    # a note pattern: track r7 >> 3, pattern r7 & 7; 32 steps of 28 B
    E(raw, h(0x08F8))                                                             # lsrs r0, r7, #3
    a.label("sc_nb"); imm32(4, NOTE[0])
    for k in range(1, 4):
        E(cmp_imm, 0, k); E(b_cond, f"sc_n{k}", "ne"); imm32(4, NOTE[k]); a.label(f"sc_n{k}")
    E(movs_imm, 0, 7); E(raw, h(0x4038)); E(movw, 1, NPAT); E(raw, h(0x4348)); E(adds_reg, 4, 4, 0)   # ands r0, r7; muls r0, r1, r0
    E(movs_imm, 5, 32)
    a.label("sc_ns")
    E(ldrb_imm, 0, 4, 1); E(cmp_imm, 0, 7); E(b_cond, "sc_hit1", "hi")
    E(ldrb_imm, 0, 4, 0); E(movs_imm, 1, 0xC0); E(raw, h(0x4208)); E(b_cond, "sc_hit0", "ne")       # tst r0, r1
    for u in range(6):
        E(ldrb_imm, 0, 4, 4 + 4 * u + 3); E(cmp_imm, 0, 127); E(b_cond, f"sc_hv{u}", "hi")
    E(adds_imm8, 4, 28); E(subs_imm8, 5, 1); E(b_cond, "sc_ns", "ne"); E(b, "sc_x")
    a.label("sc_hit1"); E(adds_imm8, 4, 1); E(b, "sc_hit")
    a.label("sc_hit0"); E(b, "sc_hit")
    for u in range(6):
        a.label(f"sc_hv{u}"); E(adds_imm8, 4, 4 + 4 * u + 3); E(b, "sc_hit")
    # a drum pattern: drum (r7 - 32) >> 3, pattern r7 & 7; velocities = the first 32 bytes
    a.label("sc_d")
    E(subs_imm8, 7, 32); E(raw, h(0x08F8)); imm32(4, DRUM[0])
    for k in range(1, 4):
        E(cmp_imm, 0, k); E(b_cond, f"sc_e{k}", "ne"); imm32(4, DRUM[k]); a.label(f"sc_e{k}")
    E(movs_imm, 0, 7); E(raw, h(0x4038)); E(movw, 1, DPAT); E(raw, h(0x4348)); E(adds_reg, 4, 4, 0)
    E(movs_imm, 5, 32)
    a.label("sc_ds"); E(ldrb_imm, 0, 4, 0); E(cmp_imm, 0, 127); E(b_cond, "sc_hit", "hi"); E(adds_imm8, 4, 1); E(subs_imm8, 5, 1); E(b_cond, "sc_ds", "ne")
    E(b, "sc_x")
    # a find (r4 = its address): the record frozen, STK1 = 3, the value, the address, the MIDI ring
    a.label("sc_hit")
    E(movs_imm, 0, 0x85); E(bl, freeze)
    imm32(0, bb.BB + bb.O.STK1); E(movs_imm, 1, 3); E(str_imm, 1, 0, 0); E(ldrb_imm, 1, 4, 0); E(str_imm, 1, 0, 4); E(str_imm, 4, 0, 8)
    E(adds_imm8, 0, 12); imm32(1, MRING); E(movs_imm, 2, (16 + 8 * NRING) // 4)
    a.label("sc_cp"); E(ldr_imm, 3, 1, 0); E(str_imm, 3, 0, 0); E(adds_imm8, 0, 4); E(adds_imm8, 1, 4); E(subs_imm8, 2, 1); E(b_cond, "sc_cp", "ne")
    a.label("sc_x")
    E(pop_list, [4, 5, 6, 7])
    imm32(2, ST); E(ldr_imm, 2, 2, 0); E(raw, h(0x4710))                           # bx r2
    return a.assemble()


def install(img, report, base_addr):
    import ct_fw
    import blackbox as bb
    BASE = ct_fw.APP_BASE
    prev = dict(led=FD.bl_target(img, PK.LED_CALLS[0], BASE), helper=FD.bl_target(img, HELPER_SITE, BASE))
    assert FD.bl_target(img, PK.LED_CALLS[1], BASE) == prev["led"] and prev["helper"] == HELPER, hex(prev["helper"])
    freeze = int(report["blackbox"]["labels"]["c_bbfrz"], 16)
    code, labels = arm_code(base_addr, prev, freeze, bb)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    for c in PK.LED_CALLS:
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_psc"])
    img[HELPER_SITE - BASE:HELPER_SITE - BASE + 4] = bl(HELPER_SITE, labels["c_psmi"])
    return labels, code, prev
