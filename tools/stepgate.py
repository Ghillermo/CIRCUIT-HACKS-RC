"""SC42.3 (the user, 2026-10-16): «when manually inputting a sequence, the time you keep the pad held becomes the gate length».

The stock (emulated): on a note track's view, a step held + a note pad (or a note held + a step pad) calls 0x0804B094(view, note, velocity), which
adds the note to the held step's edit store [view + 0x24] (p0 byte 0 = the units' mask, p1..p6 = the units: note, gate | tie << 7, micro step,
velocity) with the step's longest gate, or 6 micro steps (a step) when it is the first; the commit (0x080353C0) carries it to the pattern.  Letting
go of a pad only runs the view's slot 1 (0x0804ACC4); [view + 0x2C] p0 = a step held.

Ours: the first 4 bytes of 0x0804B094 (push.w {r3-fp, lr}) -> c_sgadd: the track's note and the time (the record's tail + 904 + 8 t: 0xA5, the
note, the time); the view's slot 1 -> c_sgrel: with a note pending and a step still held, the gate of that note in the step = the time since it was
entered, in micro steps at the project's tempo and the track's sync rate (6 a step; 1..96, the tie kept), then the stock's release.  The first pad
let go after entering a note ends it (the note pad, or the step pad).

On / off per track (the user: «toggle on pad 25, Micro Step view»; pad 25 shows the step's first note there, so «anyway use pad 32»): the Micro
Step view (Gate twice; class 0x0805AB84, one object per track at 0x20042570 + 0x68 t; pads 17-22 the micro steps, 25-30 the step's notes) pad 32 =
the toggle (green on, dim off); the record's tail + 936: "GT" and a bit per track, saved with the project (off when missing).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, lsls_imm, lsrs_imm, mov_reg,  # noqa: E402
                   movs_imm, movt, movw, muls, pop_list, push_list, raw, str_imm, strb_imm, subs_imm8, subs_reg)
from build_sc14 import udiv  # noqa: E402

ADDNOTE, ADD_OLD, ADD_BACK = 0x0804B094, bytes.fromhex("2de9f84f"), 0x0804B098       # push.w {r3-fp, lr}
TV_VT, REL_STOCK = 0x0805A064, 0x0804ACC4                                              # the note tracks' views: slot 1 = a pad let go
PLAYER0, PLAYER_SZ = 0x20040200, 0x184
TICKS_TAB = 0x0805B8B8
TEMPO, HAL_TICK = 0x20011404, 0x2000081C
PARAM_GET, PARAM_WPTR, COMMIT = 0x0803542C, 0x080354FA, 0x080353C0
SESSION_OBJ, TAIL, O_PEND = 0x2003D71C, 0x27024, 904
PEND = 0xA5
GMAX = 96
MS_VT, MS_OBJ0, MS_SZ = 0x0805AB84, 0x20042570, 0x68                                     # the Micro Step view
MS_PAD, MS_LED = 0x0804C806, 0x08047592                                                 # its slots 0 / 7
PAD_TOG = 15                                                                            # pad 32 (the view gets pads 17-32 as 0..15; 16 LEDs)
O_ON = 936                                                                              # "GT", the bits
COL_ON, COL_OFF = 0x17, 0x02
# fixed length (the user: «pad 31 is fixed length: when pressed it toggles on and lets us select a gate length (a view like Gate); that length is the
# default for any manually entered step (not live recorded); off when held again or when pad 32 is on (pad 32 goes off in this mode)»)
PAD_FIX = 14                                                                            # pad 31
MS_REL = 0x0804CAAE                                                                     # the Micro Step view's slot 1
O_FL = 940                                                                              # "FL", + 2 + t: bit 7 on, bits 0-4 the length (1..16 steps, kept when off),
                                                                                        # + 6 the selector open (t + 1), + 8 the press time, + 12 the pressed track + 1
LONG_MS = 1000
COL_FIX = 0x09
CONT = 0x20040DB8                                                                       # the tracks' container ([ctrl + 0x6C] when a track view shows)
MGR = 0x20040B10
V2 = False                                                                              # SC42.5 (use_v2)
O_SELT = 960                                                                            # (V2) the time the Micro Step view's LEDs were last asked for
SEL_MS = 200


def use_v2():
    """SC42.5 (the user, 2026-10-16: «pads 31 and 32 are lit during Gate view, instead of just microstep view»; «fixed gate won't let you select
    length»): the Gate view (Gate once) and the Micro Step view (Gate twice) are the same object, in one mode or the other by [obj + 0x1C] p0
    (<> 0 = Micro Step): pads 31 / 32, the selector and their LEDs only in the Micro Step mode; the selector closes when the view's LEDs have not
    been asked for in 200 ms (instead of comparing the container's subview), so it no longer depends on how the view was reached."""
    global V2
    V2 = True


V3 = False                                                                              # SC42.7 (use_v3)


def use_v3():
    """SC42.7 (the user, 2026-10-16): «con toggles apagados: pad 31: activa vista de longitud personalizada, elegir una longitud activa la longitud
    personalizada; pad 32: activa longitud por tiempo mantenido.  Con un toggle activado: tocar el mismo toggle lo desactiva (sin abrir nuevas
    vistas); tocar el otro toggle desactiva el anterior y activa el nuevo».  Pad 31: fixed length on = off (no selector); else the selector (the
    gate by holding off); a length chosen = the fixed length on.  Pad 32: as before (on = the fixed length off).  No long press any more."""
    global V3
    V3 = True


def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    zc = [0]
    INV = {"eq": "ne", "ne": "eq", "hi": "ls", "ls": "hi", "lo": "hs", "hs": "lo", "pl": "mi", "mi": "pl"}
    def bcl(target, cond):                                                             # a conditional branch of any length
        zc[0] += 1; n = f"_l{zc[0]}"; E(b_cond, n, INV[cond]); E(b, target); a.label(n)

    # ---- c_sgslot(r0 = view) -> r0 = the pending slot of its track (0..3), or 0; r1 = the track; clobbers r2
    a.label("c_sgslot")
    E(ldr_imm, 1, 0, 0x18); E(ldrb_imm, 1, 1, 0xC); E(cmp_imm, 1, 3); E(b_cond, "ss_0", "hi")
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "ss_x", "eq")
    imm32(2, TAIL + O_PEND); E(adds_reg, 0, 0, 2); E(lsls_imm, 2, 1, 3); E(adds_reg, 0, 0, 2)
    a.label("ss_x"); E(raw, h(0x4770))
    a.label("ss_0"); E(movs_imm, 0, 0); E(raw, h(0x4770))

    # ---- c_sgon(r0 = track) -> r0 = 1 when the gate by holding is on for it; clobbers r1, r2
    a.label("c_sgon")
    E(mov_reg, 2, 0)
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "so_x", "eq")
    imm32(1, TAIL + O_ON); E(adds_reg, 0, 0, 1)
    E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, 0x47); E(b_cond, "so_0", "ne"); E(ldrb_imm, 1, 0, 1); E(cmp_imm, 1, 0x54); E(b_cond, "so_0", "ne")
    E(ldrb_imm, 0, 0, 2); E(raw, h(0x40D0)); E(movs_imm, 1, 1); E(raw, h(0x4008)); E(raw, h(0x4770))   # lsrs r0, r2; ands r0, r1
    a.label("so_0"); E(movs_imm, 0, 0)
    a.label("so_x"); E(raw, h(0x4770))

    # ---- c_sgtog(r0 = track): on <-> off; clobbers r1-r3
    a.label("c_sgtog")
    E(mov_reg, 3, 0)
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "st_x", "eq")
    imm32(1, TAIL + O_ON); E(adds_reg, 0, 0, 1)
    E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, 0x47); E(b_cond, "st_n", "ne"); E(ldrb_imm, 1, 0, 1); E(cmp_imm, 1, 0x54); E(b_cond, "st_n", "eq")
    a.label("st_n"); E(b_cond, "st_t", "eq")
    E(movs_imm, 1, 0x47); E(strb_imm, 1, 0, 0); E(movs_imm, 1, 0x54); E(strb_imm, 1, 0, 1); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 2)
    a.label("st_t")
    E(movs_imm, 1, 1); E(raw, h(0x4099)); E(ldrb_imm, 2, 0, 2); E(raw, h(0x404A)); E(strb_imm, 2, 0, 2)    # lsls r1, r3; eors r2, r1
    a.label("st_x"); E(raw, h(0x4770))

    # ---- c_sgt() -> r0 = the record's tail, or 0; clobbers r1
    a.label("c_sgt")
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "gt_x", "eq"); imm32(1, TAIL); E(adds_reg, 0, 0, 1)
    a.label("gt_x"); E(raw, h(0x4770))

    # ---- c_sgfget(r0 = track) -> r0 = its fixed-length byte (0 without the block); clobbers r1, r2
    a.label("c_sgfget")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(bl, "c_sgt"); E(cmp_imm, 0, 0); E(b_cond, "fg_x", "eq"); imm32(1, O_FL); E(adds_reg, 0, 0, 1)
    E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, 0x46); E(b_cond, "fg_0", "ne"); E(ldrb_imm, 1, 0, 1); E(cmp_imm, 1, 0x4C); E(b_cond, "fg_0", "ne")
    E(adds_reg, 0, 0, 4); E(ldrb_imm, 0, 0, 2); E(pop_list, [4], pc=True)
    a.label("fg_0"); E(movs_imm, 0, 0)
    a.label("fg_x"); E(pop_list, [4], pc=True)

    # ---- c_sgfb() -> r0 = the fixed-length block (made when missing), or 0; clobbers r1, r2
    a.label("c_sgfb")
    E(raw, h(0xB500))                                                                                   # push {lr}
    E(bl, "c_sgt"); E(cmp_imm, 0, 0); E(b_cond, "fb_x", "eq"); imm32(1, O_FL); E(adds_reg, 0, 0, 1)
    E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, 0x46); E(b_cond, "fb_m", "ne"); E(ldrb_imm, 1, 0, 1); E(cmp_imm, 1, 0x4C); E(b_cond, "fb_x", "eq")
    a.label("fb_m")
    E(movs_imm, 1, 0x46); E(strb_imm, 1, 0, 0); E(movs_imm, 1, 0x4C); E(strb_imm, 1, 0, 1); E(movs_imm, 1, 0); E(movs_imm, 2, 2)
    a.label("fb_z"); E(raw, h(0x5481)); E(adds_imm8, 2, 1); E(cmp_imm, 2, 16); E(b_cond, "fb_z", "lo")      # strb r1, [r0, r2]
    a.label("fb_x"); E(raw, h(0xBD00))                                                                  # pop {pc}

    # ---- c_sgmtrk(r0 = a Micro Step view) -> r0 = its track; clobbers r1
    a.label("c_sgmtrk")
    imm32(1, MS_OBJ0); E(subs_reg, 0, 0, 1); E(movs_imm, 1, MS_SZ); E(raw, udiv(0, 0, 1)); E(raw, h(0x4770))

    if V2:
        # ---- c_sgmode(r0 = the Gate / Micro Step view) -> r0 = 0 in the Gate mode; clobbers r1-r3
        a.label("c_sgmode")
        E(raw, h(0xB500)); E(ldr_imm, 0, 0, 0x1C); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(raw, h(0xBD00))

    # ---- c_sgmpad (the Micro Step view's slot 0: view, pad 0..15 = pads 17-32, velocity): the selector; pad 31 fixed length; pad 32 the gate
    #      by holding
    a.label("c_sgmpad")
    E(push_list, [0, 1, 2, 4, 5, 6], lr=True)
    E(mov_reg, 5, 1); E(bl, "c_sgmtrk"); E(mov_reg, 4, 0); E(cmp_imm, 0, 3); E(b_cond, "mp_s", "hi")
    if V2: E(ldr_sp, 0, 0); E(bl, "c_sgmode"); E(cmp_imm, 0, 0); E(b_cond, "mp_s", "eq")
    E(bl, "c_sgfb"); E(cmp_imm, 0, 0); E(b_cond, "mp_s", "eq"); E(mov_reg, 6, 0)
    E(ldrb_imm, 0, 6, 6); E(subs_imm8, 0, 1); E(cmp_reg, 0, 4); E(b_cond, "mp_n", "ne")
    E(cmp_imm, 5, 16); E(b_cond, "mp_c", "hs")                                                          # the selector: pad k = k + 1 steps
    E(adds_imm8, 5, 1); E(movs_imm, 0, 0x80); E(raw, h(0x4328)); E(adds_reg, 1, 6, 4); E(strb_imm, 0, 1, 2)   # orrs r0, r5
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, 6)
    if V3: E(mov_reg, 0, 4); E(bl, "c_sgon"); E(cmp_imm, 0, 0); E(b_cond, "mp_c", "eq"); E(mov_reg, 0, 4); E(bl, "c_sgtog")   # the gate by holding off
    E(b, "mp_c")
    a.label("mp_n"); E(cmp_imm, 5, PAD_FIX); E(b_cond, "mp_t", "ne")
    if V3:                                                                                              # on: off; else the selector (the gate by holding off)
        E(adds_reg, 1, 6, 4); E(ldrb_imm, 0, 1, 2); E(lsls_imm, 2, 0, 24); E(b_cond, "mp_v", "pl")
        E(movs_imm, 2, 0x7F); E(raw, h(0x4010)); E(strb_imm, 0, 1, 2); E(b, "mp_c")                        # ands r0, r2
        a.label("mp_v")
        E(mov_reg, 0, 4); E(adds_imm8, 0, 1); E(strb_imm, 0, 6, 6)
        E(mov_reg, 0, 4); E(bl, "c_sgon"); E(cmp_imm, 0, 0); E(b_cond, "mp_c", "eq"); E(mov_reg, 0, 4); E(bl, "c_sgtog")
        E(b, "mp_c")
    E(adds_reg, 1, 6, 4); E(ldrb_imm, 0, 1, 2); E(lsls_imm, 2, 0, 24); E(b_cond, "mp_on", "mi")
    E(movs_imm, 2, 0x1F); E(raw, h(0x4010)); E(cmp_imm, 0, 0); E(b_cond, "mp_l", "ne"); E(movs_imm, 0, 1)   # ands r0, r2: off -> on, the last length
    a.label("mp_l"); E(movs_imm, 2, 0x80); E(raw, h(0x4310)); E(strb_imm, 0, 1, 2)                       # orrs r0, r2
    E(mov_reg, 0, 4); E(adds_imm8, 0, 1); E(strb_imm, 0, 6, 6)                                           # the selector open
    E(mov_reg, 0, 4); E(bl, "c_sgon"); E(cmp_imm, 0, 0); E(b_cond, "mp_c", "eq"); E(mov_reg, 0, 4); E(bl, "c_sgtog")   # pad 32 off
    E(b, "mp_c")
    a.label("mp_on")                                                                                    # on: decided when let go (short = selector, long = off)
    imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(str_imm, 0, 6, 8); E(mov_reg, 0, 4); E(adds_imm8, 0, 1); E(strb_imm, 0, 6, 12); E(b, "mp_c")
    a.label("mp_t"); E(cmp_imm, 5, PAD_TOG); E(b_cond, "mp_s", "ne")
    E(mov_reg, 0, 4); E(bl, "c_sgtog"); E(mov_reg, 0, 4); E(bl, "c_sgon"); E(cmp_imm, 0, 0); E(b_cond, "mp_c", "eq")
    E(adds_reg, 1, 6, 4); E(ldrb_imm, 0, 1, 2); E(movs_imm, 2, 0x7F); E(raw, h(0x4010)); E(strb_imm, 0, 1, 2)   # the fixed length off
    a.label("mp_c"); E(pop_list, [0, 1, 2, 4, 5, 6], pc=True)
    a.label("mp_s"); E(raw, popw([0, 1, 2, 4, 5, 6], lr=True)); E(b_w, MS_PAD)

    # ---- c_sgmrel (the Micro Step view's slot 1: view, pad): pad 31 let go after a press while on: short = the selector, long = off
    a.label("c_sgmrel")
    if V3: E(b_w, MS_REL)                                                                              # (no long press)
    E(push_list, [0, 1, 4, 5, 6], lr=True)
    E(cmp_imm, 1, PAD_FIX); E(b_cond, "mr_s", "ne")
    E(bl, "c_sgmtrk"); E(mov_reg, 4, 0); E(cmp_imm, 0, 3); E(b_cond, "mr_s", "hi")
    if V2: E(ldr_sp, 0, 0); E(bl, "c_sgmode"); E(cmp_imm, 0, 0); E(b_cond, "mr_s", "eq")
    E(bl, "c_sgfb"); E(cmp_imm, 0, 0); E(b_cond, "mr_s", "eq"); E(mov_reg, 6, 0)
    E(ldrb_imm, 0, 6, 12); E(subs_imm8, 0, 1); E(cmp_reg, 0, 4); E(b_cond, "mr_s", "ne")
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, 12)
    imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(ldr_imm, 1, 6, 8); E(subs_reg, 0, 0, 1); imm32(1, LONG_MS); E(cmp_reg, 0, 1); E(b_cond, "mr_l", "hs")
    E(mov_reg, 0, 4); E(adds_imm8, 0, 1); E(strb_imm, 0, 6, 6); E(b, "mr_s")
    a.label("mr_l"); E(adds_reg, 1, 6, 4); E(ldrb_imm, 0, 1, 2); E(movs_imm, 2, 0x7F); E(raw, h(0x4010)); E(strb_imm, 0, 1, 2)
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, 6)
    a.label("mr_s"); E(pop_list, [0, 1, 4, 5, 6]); E(raw, h(0xF85D) + h(0xEB04)); E(b_w, MS_REL)

    # ---- c_sgmled (the Micro Step view's slot 7: view) -> r0 = its LED buffer (16: pads 17-32): the selector, or pads 31 / 32
    a.label("c_sgmled")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(bl, MS_LED); E(mov_reg, 5, 0)
    if V2:
        E(mov_reg, 0, 4); E(bl, "c_sgmode"); E(cmp_imm, 0, 0); E(b_cond, "ml_x", "eq")                    # the Gate mode: the stock's LEDs
        E(bl, "c_sgt"); E(cmp_imm, 0, 0); E(b_cond, "ml_x", "eq"); imm32(1, O_SELT); E(adds_reg, 0, 0, 1)
        imm32(1, HAL_TICK); E(ldr_imm, 1, 1, 0); E(str_imm, 1, 0, 0)                                     # the stamp
    E(mov_reg, 0, 4); E(bl, "c_sgmtrk"); E(mov_reg, 4, 0); E(cmp_imm, 0, 3); E(b_cond, "ml_x", "hi")
    E(bl, "c_sgfb"); E(cmp_imm, 0, 0); E(b_cond, "ml_x", "eq"); E(mov_reg, 6, 0)
    E(adds_reg, 1, 6, 4); E(ldrb_imm, 7, 1, 2)                                                          # r7 = the fixed-length byte
    E(ldrb_imm, 0, 6, 6); E(subs_imm8, 0, 1); E(cmp_reg, 0, 4); E(b_cond, "ml_p", "ne")
    E(movs_imm, 0, 0x1F); E(raw, h(0x4007)); E(movs_imm, 2, 0)                                           # ands r7, r0: the length
    a.label("ml_l"); E(movs_imm, 1, COL_OFF); E(cmp_reg, 2, 7); E(b_cond, "ml_w", "hs"); E(movs_imm, 1, COL_ON)
    a.label("ml_w"); E(lsls_imm, 0, 2, 1); E(raw, h(0x5229)); E(adds_imm8, 2, 1); E(cmp_imm, 2, 16); E(b_cond, "ml_l", "lo")   # strh r1, [r5, r0]
    E(b, "ml_x")
    a.label("ml_p")
    E(movs_imm, 1, COL_OFF); E(lsls_imm, 0, 7, 24); E(b_cond, "ml_f", "pl"); E(movs_imm, 1, COL_FIX)
    a.label("ml_f"); E(movs_imm, 0, 2 * PAD_FIX); E(raw, h(0x5229))
    E(mov_reg, 0, 4); E(bl, "c_sgon"); E(movs_imm, 1, COL_OFF); E(cmp_imm, 0, 0); E(b_cond, "ml_h", "eq"); E(movs_imm, 1, COL_ON)
    a.label("ml_h"); E(movs_imm, 0, 2 * PAD_TOG); E(raw, h(0x5229))
    a.label("ml_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_sgledtask (the LED task calls: ctrl, frame): the chain; the selector closes when its Micro Step view is not on the screen
    a.label("c_sgledtask")
    E(push_list, [3, 4], lr=True)
    E(bl, prev["ledtask"])
    E(bl, "c_sgt"); E(cmp_imm, 0, 0); E(b_cond, "lt_x", "eq"); imm32(1, O_FL); E(adds_reg, 4, 0, 1)
    E(ldrb_imm, 1, 4, 0); E(cmp_imm, 1, 0x46); E(b_cond, "lt_x", "ne"); E(ldrb_imm, 1, 4, 6); E(cmp_imm, 1, 0); E(b_cond, "lt_x", "eq")
    if V2:                                                                                              # its view drawn in the last 200 ms: kept
        E(bl, "c_sgt"); imm32(1, O_SELT); E(adds_reg, 0, 0, 1); E(ldr_imm, 1, 0, 0)
        imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(subs_reg, 0, 0, 1); imm32(1, SEL_MS); E(cmp_reg, 0, 1); E(b_cond, "lt_x", "ls")
    else:
        E(subs_imm8, 1, 1); E(lsls_imm, 2, 1, 3); E(adds_reg, 1, 1, 2); E(adds_imm8, 1, 8)                # 9 t + 8
        imm32(0, MGR)
        E(raw, h(0xF890) + h(2 << 12 | 0x152))                                                          # ldrb.w r2, [r0, #0x152]
        E(cmp_reg, 1, 2); E(b_cond, "lt_z", "ne")
        E(ldr_imm, 2, 0, 0x6C); imm32(1, CONT); E(cmp_reg, 1, 2); E(b_cond, "lt_x", "eq")
    a.label("lt_z"); E(movs_imm, 0, 0); E(strb_imm, 0, 4, 6)
    a.label("lt_x"); E(pop_list, [3, 4], pc=True)

    # ---- c_sgadd (0x0804B094's first 4 bytes: view, note, velocity): the note and the time
    a.label("c_sgadd")
    E(raw, pushw([0, 1, 2, 3], lr=True))
    E(ldr_imm, 1, 0, 0x18); E(ldrb_imm, 0, 1, 0xC); E(cmp_imm, 0, 3); E(b_cond, "sa_x", "hi")
    E(bl, "c_sgon"); E(cmp_imm, 0, 0); E(b_cond, "sa_p", "ne")
    E(ldr_sp, 1, 0); E(ldr_imm, 1, 1, 0x18); E(ldrb_imm, 0, 1, 0xC); E(bl, "c_sgfget"); E(lsls_imm, 0, 0, 24); E(b_cond, "sa_x", "pl")
    a.label("sa_p")
    E(ldr_sp, 0, 0); E(bl, "c_sgslot"); E(cmp_imm, 0, 0); E(b_cond, "sa_x", "eq")
    E(movs_imm, 1, PEND); E(strb_imm, 1, 0, 0); E(ldr_sp, 1, 4); E(strb_imm, 1, 0, 1)
    imm32(1, HAL_TICK); E(ldr_imm, 1, 1, 0); E(str_imm, 1, 0, 4)
    a.label("sa_x"); E(raw, popw([0, 1, 2, 3], lr=True))
    E(raw, ADD_OLD); E(b_w, ADD_BACK)

    # ---- c_sgrel (the views' slot 1: view, pad): a pending note with a step still held: its gate = the time held
    a.label("c_sgrel")
    E(push_list, [0, 1, 4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0)
    E(bl, "c_sgslot"); E(cmp_imm, 0, 0); bcl("sr_s", "eq"); E(mov_reg, 5, 0); E(mov_reg, 7, 1)   # r5 = the slot, r7 = the track
    E(ldrb_imm, 0, 5, 0); E(cmp_imm, 0, PEND); bcl("sr_s", "ne")
    E(movs_imm, 0, 0); E(strb_imm, 0, 5, 0)
    E(ldr_imm, 0, 4, 0x2C); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); bcl("sr_s", "eq")   # no step held
    E(mov_reg, 0, 7); E(bl, "c_sgfget"); E(lsls_imm, 1, 0, 24); E(b_cond, "sr_h", "pl")                # the fixed length: 6 x its steps
    E(movs_imm, 1, 0x1F); E(raw, h(0x4008)); E(movs_imm, 1, 6); E(muls, 0, 1); E(mov_reg, 6, 0); E(b, "sr_g1")   # ands r0, r1
    a.label("sr_h")
    # the gate in micro steps = (ms x 144 x BPM + tps x 30000) / (tps x 60000), 1..96
    imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(ldr_imm, 1, 5, 4); E(subs_reg, 6, 0, 1)                  # r6 = the ms held
    imm32(0, 60000); E(cmp_reg, 6, 0); E(b_cond, "sr_m", "ls"); E(mov_reg, 6, 0)
    a.label("sr_m")
    imm32(0, PLAYER_SZ); E(muls, 0, 7); imm32(1, PLAYER0); E(adds_reg, 0, 0, 1)                        # the track's player
    E(ldr_imm, 0, 0, 0x10); E(movs_imm, 1, 1); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 7); E(b_cond, "sr_t", "ls"); E(movs_imm, 0, 7)
    a.label("sr_t"); E(lsls_imm, 0, 0, 2); imm32(1, TICKS_TAB); E(adds_reg, 0, 0, 1); E(ldr_imm, 7, 0, 0)    # r7 = the ticks a step
    imm32(0, TEMPO); E(movs_imm, 1, 1); E(bl, PARAM_GET); E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, 30); E(b_cond, "sr_b", "hs"); E(movs_imm, 1, 120)
    a.label("sr_b")
    E(movs_imm, 0, 144); E(muls, 0, 1); E(muls, 0, 6)                                                  # ms x 144 x BPM
    imm32(1, 30000); E(muls, 1, 7); E(adds_reg, 0, 0, 1)
    imm32(1, 60000); E(muls, 1, 7); E(raw, udiv(6, 0, 1))                                              # r6 = the gate
    E(cmp_imm, 6, 0); E(b_cond, "sr_g1", "ne"); E(movs_imm, 6, 1)
    a.label("sr_g1"); E(cmp_imm, 6, GMAX); E(b_cond, "sr_g2", "ls"); E(movs_imm, 6, GMAX)
    a.label("sr_g2")
    # the unit of that note in the held step's store
    E(ldr_imm, 0, 4, 0x24); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 7, 0, 0)               # r7 = the units' mask
    E(movs_imm, 5, 0)                                                                                  # (the slot is free: r5 = the unit)
    a.label("sr_u")
    E(movs_imm, 0, 1); E(raw, h(0x40A8)); E(raw, h(0x4238)); E(b_cond, "sr_n", "eq")                   # lsls r0, r5; tst r0, r7
    E(ldr_imm, 0, 4, 0x24)
    E(mov_reg, 1, 5); E(adds_imm8, 1, 1); E(bl, PARAM_WPTR)
    E(ldrb_imm, 1, 0, 0); E(ldr_sp, 2, 0); E(bl, "c_sgnote"); E(cmp_reg, 1, 2); E(b_cond, "sr_n", "ne")
    E(ldrb_imm, 1, 0, 1); E(movs_imm, 2, 0x80); E(raw, h(0x4011)); E(raw, h(0x4331)); E(strb_imm, 1, 0, 1)   # ands r1, r2; orrs r1, r6
    a.label("sr_n"); E(adds_imm8, 5, 1); E(cmp_imm, 5, 6); E(b_cond, "sr_u", "lo")
    E(ldr_imm, 0, 4, 0x24); E(bl, COMMIT)
    a.label("sr_s")
    E(pop_list, [0, 1, 4, 5, 6, 7]); E(raw, h(0xF85D) + h(0xEB04))                                    # pop {lr}
    E(b_w, REL_STOCK)

    # ---- c_sgnote(r2 = the view) -> r2 = the pending note of its track (read before the slot was freed: the byte stays); clobbers r3
    a.label("c_sgnote")
    E(push_list, [0, 1], lr=True)
    E(mov_reg, 0, 2); E(bl, "c_sgslot"); E(cmp_imm, 0, 0); E(b_cond, "sn_0", "eq"); E(ldrb_imm, 2, 0, 1); E(pop_list, [0, 1], pc=True)
    a.label("sn_0"); E(movs_imm, 2, 0xFF); E(pop_list, [0, 1], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; 0x0804B094's first 4 bytes, slot 1 of the note tracks' views."""
    import ct_fw
    from thumb import b_w as bw_enc
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    assert bytes(img[ADDNOTE - BASE:ADDNOTE - BASE + 4]) == ADD_OLD
    assert u(TV_VT + 4) == REL_STOCK | 1, hex(u(TV_VT + 4))
    assert u(MS_VT) == MS_PAD | 1 and u(MS_VT + 4) == MS_REL | 1 and u(MS_VT + 28) == MS_LED | 1, (hex(u(MS_VT)), hex(u(MS_VT + 28)))
    import packio as PK, fxdiag as FD
    from thumb import bl as bl_enc
    prev = dict(rel=REL_STOCK, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[ADDNOTE - BASE:ADDNOTE - BASE + 4] = bw_enc(ADDNOTE, labels["c_sgadd"])
    struct.pack_into("<I", img, TV_VT + 4 - BASE, labels["c_sgrel"] | 1)
    struct.pack_into("<I", img, MS_VT - BASE, labels["c_sgmpad"] | 1)
    struct.pack_into("<I", img, MS_VT + 4 - BASE, labels["c_sgmrel"] | 1)
    struct.pack_into("<I", img, MS_VT + 28 - BASE, labels["c_sgmled"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_sgledtask"])
    return labels, code, prev
