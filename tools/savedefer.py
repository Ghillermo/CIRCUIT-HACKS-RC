"""SC49.7 / Beta 5.0 / RC4.02 (the user, 2026-10-29: «extend clock fix to project save»; chosen «Both»: our own work at save time cut —
packio.use_svskip — and the card write waiting while the sequencer plays, as the settings save does since SC42, lazysave).

The stock's project save (emulated): Save twice commits a store of the session manager (0x2003D71C); its listener, a dispatcher in the UI thread
(the vtable word 0x08059CF0 -> 0x08030500: this + 4 -> 0x08030502), calls the save routine 0x0802FDF8(manager, slot, flag): the manager's state
«saving» ([+ 0x64] p1 = 2: the dispatcher ignores every other request meanwhile), the blobs copied into the RAM record (0x0802F63C, our hooks at
0x0802FE5E), then the record (160 780 B) posted to the storage task (0x0803C946, with a callback that clears «saving»).  Writing it to the card
while the transport runs is what upsets the clock.

Ours:
  * the save routine's first 4 bytes -> c_sdsave: with the transport running (p0 of 0x20011034) the call is only kept (manager, slot, flag and the
    pack the manager has, [+ 0x60] p0): nothing is copied or written, the stock's state is untouched; stopped, it runs as always;
  * the LED task's head (c_sdled): a kept save is run (c_sdflush) once the transport stops; until then the Save LED (57) blinks yellow;
  * the dispatcher's vtable word -> c_sddisp: any project request while a save is kept runs the save first (a load / a new project then finds the
    stock «saving» and is ignored, as the stock does while it saves: press again), except a save of the same slot (Save twice again: kept again;
    the sequencer alone sends no request, a synth patch chosen does: the kept save is then written, as the stock would have written it at Save);
  * c_sdflush waits while the manager is busy ([+ 0x64] p1 = 2: a patch load or a save in flight) and drops a kept save when the manager's pack has
    changed since (another pack loaded meanwhile: the record is another project); a save that runs (stopped) replaces a kept one.
RAM: modmx.MXR + 0x2160: + 0 "SD01", + 4 a save kept, + 6 its slot, + 7 its flag, + 8 the manager, + 12 the pack.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, ands_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, lsrs_imm, mov_reg, movs_imm, movt, movw,  # noqa: E402
                   pop_list, push_list, raw, str_imm, strb_imm, strh_reg)
import modmx as MX  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402

RAM = MX.MXR + 0x2160
SIG = struct.unpack("<I", b"SD01")[0]
SAVE_FN, SAVE_OLD = 0x0802FDF8, bytes.fromhex("f0b585b0")       # push {r4-r7, lr}; sub sp, #0x14
DISP_VT, DISP = 0x08059CF0, 0x08030500                          # the session manager's store listener (this + 4 -> 0x08030502)
TRANSPORT, PARAM_GET, HAL_TICK = 0x20011034, 0x0803542C, 0x2000081C
LED_SAVE, YELLOW = 57, 0x2D
RET = h(0x4770)


def arm_code(base, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_sdram() -> r0 = RAM (nothing kept the first time); clobbers r1, r2
    a.label("c_sdram")
    imm32(0, RAM); E(ldr_imm, 1, 0, 0); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "sr_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 4)
    a.label("sr_x"); E(raw, RET)
    # ---- c_sdplay() -> r0 = the transport's p0 (playing); clobbers r1-r3
    a.label("c_sdplay")
    E(push_list, [], lr=True); imm32(0, TRANSPORT); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(pop_list, [], pc=True)
    # ---- c_sdpack(r0 = the manager) -> r0 = its pack ([+ 0x60] p0); clobbers r1-r3
    a.label("c_sdpack")
    E(push_list, [], lr=True); E(ldr_imm, 0, 0, 0x60); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(pop_list, [], pc=True)

    # ---- c_sdsave (the save routine's head: manager, slot, flag): playing = kept; else the stock's (and nothing kept any more)
    a.label("c_sdsave")
    E(push_list, [0, 1, 2, 4], lr=True)
    E(bl, "c_sdram"); E(mov_reg, 4, 0); E(bl, "c_sdplay"); E(cmp_imm, 0, 0); E(b_cond, "ss_run", "eq")
    E(ldr_sp, 0, 0); E(bl, "c_sdpack"); E(strb_imm, 0, 4, 12)
    E(ldr_sp, 1, 0); E(str_imm, 1, 4, 8); E(ldr_sp, 1, 4); E(strb_imm, 1, 4, 6); E(ldr_sp, 1, 8); E(strb_imm, 1, 4, 7)
    E(movs_imm, 1, 1); E(strb_imm, 1, 4, 4)
    E(pop_list, [0, 1, 2, 4], pc=True)
    a.label("ss_run"); E(movs_imm, 1, 0); E(strb_imm, 1, 4, 4); E(pop_list, [0, 1, 2, 4]); E(pop_list, [3]); E(mov_reg, 14, 3)
    a.label("c_sdorig"); E(push_list, [4, 5, 6, 7], lr=True); E(raw, h(0xB085)); E(b_w, SAVE_FN + 4)   # the 4 bytes replaced, then the rest

    # ---- c_sdflush(): a kept save run now (not while the manager is busy; dropped if its pack changed since); clobbers r0-r3
    a.label("c_sdflush")
    E(push_list, [4], lr=True); E(bl, "c_sdram"); E(mov_reg, 4, 0)
    E(ldrb_imm, 1, 4, 4); E(cmp_imm, 1, 0); E(b_cond, "sf_x", "eq")
    E(ldr_imm, 0, 4, 8); E(ldr_imm, 0, 0, 0x64); E(movs_imm, 1, 1); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 2); E(b_cond, "sf_x", "eq")
    E(movs_imm, 1, 0); E(strb_imm, 1, 4, 4)
    E(ldr_imm, 0, 4, 8); E(bl, "c_sdpack"); E(ldrb_imm, 1, 4, 12); E(cmp_reg, 0, 1); E(b_cond, "sf_x", "ne")
    E(ldr_imm, 0, 4, 8); E(ldrb_imm, 1, 4, 6); E(ldrb_imm, 2, 4, 7); E(bl, "c_sdorig")
    a.label("sf_x"); E(pop_list, [4], pc=True)

    # ---- c_sddisp (the session manager's store listener: this + 4, store, index, value, [sp] more): a kept save first (not for a save of its
    #      slot: [manager + 0x48] = the save requests, index = the slot), then the stock's
    a.label("c_sddisp")
    E(push_list, [0, 1, 2, 3], lr=True)
    E(ldr_imm, 3, 0, 0x44); E(cmp_reg, 1, 3); E(b_cond, "sd_f", "ne")
    E(bl, "c_sdram"); E(ldrb_imm, 1, 0, 6); E(ldr_sp, 2, 8); E(cmp_reg, 1, 2); E(b_cond, "sd_g", "eq")
    a.label("sd_f"); E(bl, "c_sdflush")
    a.label("sd_g"); E(pop_list, [0, 1, 2, 3]); E(raw, h(0xF85D) + h(0xEB04))   # ldr.w lr, [sp], #4
    E(b_w, DISP)

    # ---- c_sdled (the LED task's calls: ctrl, frame): the chain; a kept save: run once stopped, else Save blinking yellow
    a.label("c_sdled")
    E(push_list, [3, 4, 5], lr=True); E(mov_reg, 5, 1); E(bl, prev["led"])
    E(bl, "c_sdram"); E(ldrb_imm, 1, 0, 4); E(cmp_imm, 1, 0); E(b_cond, "sl_x", "eq")
    E(bl, "c_sdplay"); E(cmp_imm, 0, 0); E(b_cond, "sl_b", "ne")
    E(bl, "c_sdflush"); E(b, "sl_x")
    a.label("sl_b"); imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(lsrs_imm, 0, 0, 8); E(movs_imm, 1, 1); E(ands_reg, 0, 1)
    E(movs_imm, 1, 0); E(cmp_imm, 0, 0); E(b_cond, "sl_w", "eq"); E(movs_imm, 1, YELLOW)
    a.label("sl_w"); E(movs_imm, 2, 2 * LED_SAVE); E(strh_reg, 1, 5, 2)
    a.label("sl_x"); E(pop_list, [3, 4, 5], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """At the image's end: the save routine's head, the session manager's listener in its vtable, the LED task's calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    rd = lambda at, n: bytes(img[at - BASE:at - BASE + n])
    u = lambda at: struct.unpack_from("<I", img, at - BASE)[0]
    assert rd(SAVE_FN, 4) == SAVE_OLD, rd(SAVE_FN, 4).hex()
    assert u(DISP_VT) == DISP | 1, hex(u(DISP_VT))
    prev = dict(led=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    for c in PK.LED_CALLS[1:]: assert FD.bl_target(img, c, BASE) == prev["led"], hex(c)
    code, labels = arm_code(base_addr, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000, f"savedefer: the image is full ({len(img):#x})"
    def put(at, data): img[at - BASE:at - BASE + len(data)] = data
    put(SAVE_FN, b_w(SAVE_FN, labels["c_sdsave"]))
    struct.pack_into("<I", img, DISP_VT - BASE, labels["c_sddisp"] | 1)
    for c in PK.LED_CALLS: put(c, bl(c, labels["c_sdled"]))
    return labels, code, prev
