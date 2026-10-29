"""SC45 (the user, 2026-10-19: «En velocity view, shift+pad hace que deje de aplicarse automatización (posición de knob + init en lugar de posición +
valor previo de automatización)»; with him: Synth 1 / 2 and MIDI 1 / 2; the 8 lanes): a step that lets go of the automation.

The stock's playback of the automation (found 2026-10-19: 0x08031AFC, a listener of the object 0x2003EBDC; with the transport running
([obj + 0x48] = 0x20011034 p0), on each step of a note track t (0..3 = Synth 1, Synth 2, MIDI 1, MIDI 2: the editor [[obj + 0x38] + 4 t], its
step store + 0xC p1) it takes, for each lane 0..7, the first byte <> 0xFF of the step's 6 micro steps (ldrb.w fp, [r0, #0x3a8] at 0x08031B8E;
r4 = t, r6 = the lane, sl = the micro step, r5 = the object) into p[lane] of the track's macro store [[obj + 0x2C] + 4 t] and commits it (the
macros of Synth 1 / 2 move; MIDI 1 / 2's own engine through vcf21's c_vplay); a lane with no byte at that step leaves the store as it is.  The
value it sets replaces the knob's, so there is no knob position to go back to.  (0x0804BA8C / 0x0804BB02, which smpick guards, only play the
step pressed on the step pads: the preview.)  Here:
  * the mark: bit 7 of byte [3] of the step (stepmod uses bits 0-2 / 4-6); **Velocity view (subview 2: [ctrl + 0x152] = 9 t + 2), Shift + a step
    pad** (pads 1-16, + 16 on the 17-32 page) toggles it; the press and its release are swallowed; with Shift the step pads are yellow, the marked
    ones red (the LED task chain);
  * the playback's read (0x08031B8E -> c_arread): the first value a lane plays (its flag clear) keeps the value it is about to replace (the base,
    as a lane value: Synth 1 / 2 the macro position GETTER(t, 174 + 17 k); MIDI 1 / 2 with the engine on c_vtou(code, value) of the row's code)
    and sets the flag; at a marked step no lane plays (0xFF) and a flagged lane gets its base back in the store (committed by the stock after
    the lanes), flag cleared;
  * a knob turned by hand clears its lane's flag (the knob's value is the base from then on): Synth 1 / 2 by the head of slot 4 of the macro
    handlers (the handler = [[[CTX] + 0x40] + 0x2C] + 0x148 + 4 t), MIDI 1 / 2 by vcf21's three calls of c_vsync (the lane of the code, c_vlane).
RAM: modmx.MXR + 0x1B0: + 0 the flags (bit 8 t + k), + 4 the bases (8 t + k), + 36 the swallowed pad + 1, + 40 "AR01" (the flags cleared
the first time: that RAM holds the power-up pattern).

use_v2() (SC48.8 / Beta 3.44; the user, 2026-10-28: «de-automation view (shift view in velocity view) keeps base cyan color and is no longer
yellow»; «yellow on steps with automation.  touching the step in this view (and only this view) allows to preview, on yellow, the automation value
on the knob.  yellow goes away and knob back to normal when shift is released»; a tap on a yellow step previews only, the others still toggle the
mark; the preview goes to the sound too):
  * the LEDs with Shift: the steps keep the stock's colours; a step with automation (a byte <> 0xFF in lanes 0..7 of any of its 6 micro steps)
    yellow, a marked one red (nothing plays there);
  * Shift + a yellow step = its values played, as the stock's preview of a held step does (0x0804BB02: the lane target [step object + 0x54], slot
    0 = 0x0805BFDC (target, the lane's id [[object + 0x58] + k], value); MIDI 1 / 2 with the own engine on through vcf21's c_vapply, which the
    stock's route only reaches with the transport running): for each lane with a value, the first of its micro steps (as the playback); before
    the first change of a lane its value now (c_arbase; MIDI 1 / 2 with the engine off: p[k] of the macro store) is kept;
  * Shift released (the LED task): the kept values played back the same way.
  RAM: modmx.MXR + 0x1EA0 (40 B): + 0 "ARP2", + 4 the lanes kept (bit 8 t + k), + 8 their values (8 t + k)."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bics_reg, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrb_reg,  # noqa: E402
                   lsls_imm, lsls_reg, lsrs_imm, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, str_imm, strb_imm, strb_reg,
                   strh_reg, subs_imm8, subs_reg, tst_reg, blx_reg)
import vcf21 as V  # noqa: E402
import mpatch as MP  # noqa: E402
import packio as PK  # noqa: E402
import modmx as MX  # noqa: E402
from build_sc14 import udiv  # noqa: E402
PARAM_WPTR = 0x080354FA

RAM = MX.MXR + 0x1B0
OBJ0, OSZ, PAGE_OFF = 0x20041EB0, 0x170, 0xC4
MGR, CONT = 0x20040B10, 0x20040DB8
SUB_VEL = 2
PB_READ, PB_OLD = 0x08031B8E, bytes.fromhex("90f8a8b3")      # ldrb.w fp, [r0, #0x3a8]
MARK = 0x80
COL_AV, COL_MARK = 0x2D, 0x53
SIG = 0x31305241                     # "AR01" at RAM + 40: the flags are cleared the first time (the RAM holds the power-up pattern)
INV = V.INV
V2 = False                           # SC48.8 (use_v2): yellow = the steps with automation; Shift + a yellow step = its values until Shift is let go
PVR = MX.MXR + 0x1EA0                # (V2) + 0 "ARP2", + 4 the lanes kept, + 8 their values
PV_SIG = struct.unpack("<I", b"ARP2")[0]
MACRO_OBJ = 0x2003EBDC               # the playback's object: [+ 0x2C] + 4 t = track t's macro store
LANE_SET = 0x0805BFDC                # the lane target's slot 0 (target, lane id, value): the stock's step preview
LANE0 = 0x3A8                        # lane k, step s, micro step m of a pattern: + 0x3A8 + 192 k + 6 s + m


INIT = False                         # SC49.1 / RC4.01 (use_init): a marked step brings the lanes back to the project's values
V3 = False                           # SC49.1 (use_v3): the knob LEDs yellow on a previewed step; Clear + step = its knob automation erased
SESSION_OBJ = 0x2003D71C             # (INIT) [+ 0x14] = the session record: the project as loaded / last saved (a patch chosen is copied there too)
REC_SYN, SYN_SZ = 0x26D14, 0x154     # Synth s's patch in the record (persist19.REC_BASE), in the bank's format: parameter i = byte 30 + i
MACRO_REC = 30 + 174                 # macro m's position = parameter 174 + 17 m
MPCODE = 5                           # (INIT) the own-synth patch (mpatch's format, projsyn's blocks in the record): code c = byte 5 + c, c = 1..34
PVM = MX.MXR + 0x1ED0                # (V3) + 0 the previewed track + 1 (0 = none), + 1 its step
KNOB_LED0 = 60                       # (V3) the panel's knob LEDs 60..67: colour | (value + 2) << 8
PJ_SIG, PJ_BLEN = 0xC6, 30            # (INIT) projsyn's block: SIG, track << 4 | block, BLEN data bytes
PJ_BLK0, PJ_PSIZE = 0x1A27C + 0x380 + 8, 0xCA8   # (INIT) block b of MIDI track t = record + PJ_BLK0 + PJ_PSIZE (8 t + b)


def use_v2():
    global V2
    V2 = True


def use_init():
    """SC49.1 / RC4.01 (the user, 2026-10-29, on RC4: «the shift step doesn't revert previous automation back to init»; «the cleared automation must go
    to Project init, not current pad»; MIDI 1 / 2 too: «Project init»): at a marked step a lane that played goes back to the project's value, not to
    the knob's position before the automation (after a Record + step snapshot the knobs stay at the snapshot's values, so nothing moved).
      * Synth 1 / 2: macro m in the synth's patch of the session record ([SESSION_OBJ + 0x14] + REC_SYN + SYN_SZ s + MACRO_REC + 17 m): the
        stock keeps it as loaded or last saved (turning a knob changes the patch in use, 0x20010044, not the record; choosing a patch copies it
        there, then 0x0802FC82 applies it);
      * MIDI 1 / 2 with the own engine on: the lane's code in the own-synth patch projsyn keeps in the record (its blocks 0 / 1: 0xC6, the index,
        "CTM1"), else the code's default (t_def, Clear + knob); as a lane value (c_vtou);
      * nothing usable (no record, a value over 127): the base as before."""
    global INIT
    INIT = True


def use_v3():
    """SC49.1 / Beta 3.46 (the user, 2026-10-29): «the updated leds should be yellow» (Shift + a yellow step: the knobs it moves light yellow, their
    brightness the value, until Shift is let go); «clear+pad in this view must keep the note and erase automation only» (Velocity view, Clear held,
    with or without Shift: the step's knob lanes 0..7 to 0xFF, its notes, its mark and the level / pan / send lanes 8..11 kept)."""
    global V3
    use_v2(); use_init()
    V3 = True


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def ldrb_w(rt, rn, imm12): return h(0xF890 | rn) + h(rt << 12 | imm12)
def ldrsb_reg(rt, rn, rm): return h(0x5600 | rm << 6 | rn << 3 | rt)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_a{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)

    # ---- c_arst() -> r0 = RAM, the flags cleared the first time; clobbers r1, r2
    a.label("c_arst")
    imm32(0, RAM); E(ldr_imm, 1, 0, 40); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "as_x", "eq")
    E(str_imm, 2, 0, 40); E(movs_imm, 1, 0); E(str_imm, 1, 0, 0)
    a.label("as_x"); E(raw, h(0x4770))

    # ---- c_artrk(r0 = a step / lane object) -> r0 = 0..3, or 0xFF; clobbers r1
    a.label("c_artrk")
    imm32(1, OBJ0)
    for t in range(4):
        E(cmp_reg, 0, 1); E(b_cond, f"tk_{t}", "eq")
        if t < 3: imm32(1, OBJ0 + OSZ * (t + 1))
    E(movs_imm, 0, 0xFF); E(raw, h(0x4770))
    for t in range(4):
        a.label(f"tk_{t}"); E(movs_imm, 0, t); E(raw, h(0x4770))

    # ---- c_arpat(r0 = track 0..3) -> r0 = the pattern of the track (c_sdpat numbers MIDI 1 / 2 = 0 / 1, the synths 2 / 3); clobbers r1-r3
    a.label("c_arpat")
    E(adds_imm8, 0, 2); E(cmp_imm, 0, 4); E(b_cond, "ap_g", "lo"); E(subs_imm8, 0, 4)
    a.label("ap_g"); E(b_w, L["c_sdpat"])

    # ---- c_arvel(r0 = track) -> r0 = 1 when that track's Velocity view shows; clobbers r1-r3
    a.label("c_arvel")
    imm32(1, MGR); E(ldr_imm, 2, 1, 0x6C); imm32(3, CONT); E(cmp_reg, 2, 3); E(b_cond, "av_0", "ne")
    E(raw, h(0xF891) + h(2 << 12 | 0x152))                                                 # ldrb.w r2, [r1, #0x152]
    E(movs_imm, 3, 9); E(muls, 3, 0); E(adds_imm8, 3, SUB_VEL); E(cmp_reg, 2, 3); E(b_cond, "av_0", "ne")
    E(movs_imm, 0, 1); E(raw, h(0x4770))
    a.label("av_0"); E(movs_imm, 0, 0); E(raw, h(0x4770))

    # ---- c_arpage(r0 = step object) -> r0 = 16 on the 17-32 page, else 0; clobbers r1-r3
    a.label("c_arpage")
    E(push_list, [], lr=True)
    E(raw, h(0xF8D0) + h(0 << 12 | PAGE_OFF)); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(cmp_imm, 0, 0); E(b_cond, "pg_x", "eq"); E(movs_imm, 0, 16)
    a.label("pg_x"); E(pop_list, [], pc=True)

    # ---- c_arpad (slot 0 of the step objects: obj, pad, velocity): Velocity view + Shift = the step's mark
    a.label("c_arpad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(cmp_imm, 1, 15); bc("pd_prev", "hi"); E(mov_reg, 5, 1); E(mov_reg, 6, 0)
    E(bl, "c_artrk"); E(cmp_imm, 0, 3); bc("pd_prev", "hi"); E(mov_reg, 4, 0)
    if V3:                                                                                    # Clear held: the step's knob automation erased
        E(bl, "c_arclr"); E(cmp_imm, 0, 0); E(b_cond, "pd_sh", "eq")
        E(mov_reg, 0, 4); E(bl, "c_arvel"); E(cmp_imm, 0, 0); bc("pd_prev", "eq")
        E(mov_reg, 0, 6); E(bl, "c_arpage"); E(adds_reg, 5, 5, 0)
        E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_arerase"); E(b, "pd_sw")
        a.label("pd_sh")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); bc("pd_prev", "eq")
    E(mov_reg, 0, 4); E(bl, "c_arvel"); E(cmp_imm, 0, 0); bc("pd_prev", "eq")
    E(mov_reg, 0, 6); E(bl, "c_arpage"); E(adds_reg, 5, 5, 0)                              # r5 = the step
    E(mov_reg, 0, 4); E(bl, "c_arpat")
    if V2: E(mov_reg, 7, 0)                                                                   # r7 = the pattern
    E(movs_imm, 1, 28); E(muls, 1, 5); E(adds_reg, 0, 0, 1)
    if V2:                                                                                    # not marked, with automation: preview only
        E(mov_reg, 6, 0); E(ldrb_imm, 1, 0, 3); E(movs_imm, 2, MARK); E(tst_reg, 1, 2); E(b_cond, "pd_tg", "ne")
        E(mov_reg, 0, 7); E(mov_reg, 1, 5); E(bl, "c_araut"); E(cmp_imm, 0, 0); E(b_cond, "pd_tg", "eq")
        E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_arprev"); E(b, "pd_sw")
        a.label("pd_tg"); E(mov_reg, 0, 6)
    E(ldrb_imm, 1, 0, 3); E(movs_imm, 2, MARK); E(raw, h(0x4051)); E(strb_imm, 1, 0, 3)     # eors r1, r2
    if V2: a.label("pd_sw")
    imm32(0, RAM + 36); E(raw, h(0x9901)); E(adds_imm8, 1, 1); E(strb_imm, 1, 0, 0)            # ldr r1, [sp, #4]: the pad
    E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("pd_prev"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["spad"])

    # ---- c_arrelp (slot 1 of the step objects: obj, pad): the release of a swallowed press swallowed too
    a.label("c_arrelp")
    imm32(3, RAM + 36); E(ldrb_imm, 2, 3, 0); E(cmp_imm, 2, 0); E(b_cond, "rl_prev", "eq")
    E(subs_imm8, 2, 1); E(cmp_reg, 2, 1); E(b_cond, "rl_prev", "ne")
    E(movs_imm, 2, 0); E(strb_imm, 2, 3, 0); E(raw, h(0x4770))
    a.label("rl_prev"); E(b_w, prev["srel"])

    # ---- c_arled (the LED task calls: ctrl, frame): the chain, then Shift in a Velocity view = the steps yellow, the marked ones red
    a.label("c_arled")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 5, 1)
    E(bl, prev["ledtask"])
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0)
    if V3: E(b_cond, "le_s", "ne"); imm32(0, PVM); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 0); E(bl, "c_arpvback"); E(b, "le_x"); a.label("le_s")
    elif V2: E(b_cond, "le_s", "ne"); E(bl, "c_arpvback"); E(b, "le_x"); a.label("le_s")
    else: E(b_cond, "le_x", "eq")
    E(movs_imm, 4, 0)
    a.label("le_t"); E(mov_reg, 0, 4); E(bl, "c_arvel"); E(cmp_imm, 0, 0); E(b_cond, "le_f", "ne")
    E(adds_imm8, 4, 1); E(cmp_imm, 4, 4); E(b_cond, "le_t", "lo"); E(b, "le_x")
    a.label("le_f")
    E(movs_imm, 0, OSZ >> 4); E(lsls_imm, 0, 0, 4); E(muls, 0, 4); imm32(1, OBJ0); E(adds_reg, 0, 0, 1); E(bl, "c_arpage"); E(mov_reg, 6, 0)
    if V2:                                                                                    # r6 = the page's first step (0 / 16)
        E(movs_imm, 7, 0)
        a.label("le_l")
        E(mov_reg, 0, 4); E(bl, "c_arpat"); E(adds_reg, 1, 6, 7); E(movs_imm, 2, 28); E(muls, 2, 1); E(adds_reg, 2, 2, 0)
        E(ldrb_imm, 2, 2, 3); E(movs_imm, 3, MARK); E(tst_reg, 2, 3); E(b_cond, "le_m", "ne")
        E(bl, "c_araut"); E(cmp_imm, 0, 0); E(b_cond, "le_n", "eq"); E(movs_imm, 1, COL_AV); E(b, "le_c")
        a.label("le_m"); E(movs_imm, 1, COL_MARK)
        a.label("le_c"); E(lsls_imm, 0, 7, 1); E(strh_reg, 1, 5, 0)
        a.label("le_n"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 16); E(b_cond, "le_l", "lo")
        if V3: E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_arkled")
    else:
        E(mov_reg, 0, 4); E(bl, "c_arpat"); E(movs_imm, 1, 28); E(muls, 1, 6); E(adds_reg, 6, 0, 1)   # r6 = the page's first step
        E(movs_imm, 7, 0)
        a.label("le_l")
        E(movs_imm, 1, COL_AV); E(ldrb_imm, 0, 6, 3); E(movs_imm, 2, MARK); E(tst_reg, 0, 2); E(b_cond, "le_c", "eq"); E(movs_imm, 1, COL_MARK)
        a.label("le_c"); E(lsls_imm, 0, 7, 1); E(strh_reg, 1, 5, 0)
        E(adds_imm8, 6, 28); E(adds_imm8, 7, 1); E(cmp_imm, 7, 16); E(b_cond, "le_l", "lo")
    a.label("le_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    if V2:
        # ---- c_araut(r0 = a pattern, r1 = a step) -> r0 = 1 when one of lanes 0..7 has a value at the step (any micro step); clobbers r1-r3
        a.label("c_araut")
        E(movs_imm, 2, 6); E(muls, 2, 1); E(adds_reg, 0, 0, 2); E(movw, 2, LANE0); E(adds_reg, 0, 0, 2)
        E(movs_imm, 3, 8)
        a.label("au_l")
        for m in range(6): E(ldrb_imm, 1, 0, m); E(cmp_imm, 1, 0xFF); E(b_cond, "au_y", "ne")
        E(adds_imm8, 0, 192); E(subs_imm8, 3, 1); E(b_cond, "au_l", "ne")
        E(movs_imm, 0, 0); E(raw, h(0x4770))
        a.label("au_y"); E(movs_imm, 0, 1); E(raw, h(0x4770))

        # ---- c_arpvst() -> r0 = PVR, nothing kept the first time (the RAM holds the power-up pattern); clobbers r1, r2
        a.label("c_arpvst")
        imm32(0, PVR); E(ldr_imm, 1, 0, 0); imm32(2, PV_SIG); E(cmp_reg, 1, 2); E(b_cond, "vs_x", "eq")
        E(str_imm, 2, 0, 0); E(movs_imm, 1, 0); E(str_imm, 1, 0, 4)
        a.label("vs_x"); E(raw, h(0x4770))

        # ---- c_arset(r0 = track 0..3, r1 = lane, r2 = value): played as the stock's step preview (MIDI 1 / 2 with the engine on: c_vapply); clobbers r0-r3
        a.label("c_arset")
        E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
        E(cmp_imm, 4, 2); E(b_cond, "se_s", "lo")
        E(subs_imm8, 0, 2); E(bl, L["c_von"]); E(cmp_imm, 0, 0); E(b_cond, "se_s", "eq")
        E(mov_reg, 0, 4); E(subs_imm8, 0, 2); E(mov_reg, 1, 5); E(mov_reg, 2, 6); E(bl, L["c_vapply"]); E(b, "se_x")
        a.label("se_s")
        E(movs_imm, 0, OSZ >> 4); E(lsls_imm, 0, 0, 4); E(muls, 0, 4); imm32(1, OBJ0); E(adds_reg, 7, 0, 1)   # r7 = the track's step object
        E(ldr_imm, 1, 7, 0x58); E(ldrb_reg, 1, 1, 5); E(ldr_imm, 0, 7, 0x54); E(mov_reg, 2, 6); E(bl, LANE_SET)
        a.label("se_x"); E(pop_list, [4, 5, 6, 7], pc=True)

        # ---- c_arprev(r0 = track 0..3, r1 = step): the step's lane values played, each lane's value before the first change kept
        a.label("c_arprev")
        E(push_list, [3, 4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(movs_imm, 6, 0)
        if V3: imm32(0, PVM); E(mov_reg, 1, 4); E(adds_imm8, 1, 1); E(strb_imm, 1, 0, 0); E(strb_imm, 5, 0, 1)   # the previewed step
        a.label("pv_k")
        E(mov_reg, 0, 4); E(bl, "c_arpat"); E(movs_imm, 1, 6); E(muls, 1, 5); E(adds_reg, 0, 0, 1); E(movw, 1, LANE0); E(adds_reg, 0, 0, 1)
        E(movs_imm, 1, 192); E(muls, 1, 6); E(adds_reg, 0, 0, 1)                                 # r0 = lane k at the step, micro step 0
        for m in range(6): E(ldrb_imm, 7, 0, m); E(cmp_imm, 7, 0xFF); E(b_cond, "pv_v", "ne")
        E(b, "pv_n")
        a.label("pv_v")                                                                       # r7 = the value
        E(bl, "c_arpvst"); E(ldr_imm, 2, 0, 4); E(lsls_imm, 3, 4, 3); E(adds_reg, 3, 3, 6); E(movs_imm, 1, 1); E(lsls_reg, 1, 3)
        E(tst_reg, 2, 1); E(b_cond, "pv_s", "ne")
        E(orrs_reg, 2, 1); E(str_imm, 2, 0, 4)
        E(push_list, [3]); E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(bl, "c_arcur"); E(pop_list, [3])
        imm32(1, PVR + 8); E(strb_reg, 0, 1, 3)
        a.label("pv_s"); E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(mov_reg, 2, 7); E(bl, "c_arset")
        a.label("pv_n"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "pv_k", "lo")
        E(pop_list, [3, 4, 5, 6, 7], pc=True)

        # ---- c_arcur(r0 = track, r1 = lane) -> r0 = the lane value now (c_arbase; MIDI with the engine off: p[k] of its macro store); clobbers r1-r3
        a.label("c_arcur")
        E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
        E(bl, "c_arbase"); E(cmp_imm, 0, 0xFF); E(b_cond, "cu_x", "ne")
        imm32(0, MACRO_OBJ); E(ldr_imm, 0, 0, 0x2C); E(lsls_imm, 1, 4, 2); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0)
        E(mov_reg, 1, 5); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
        a.label("cu_x"); E(pop_list, [4, 5], pc=True)

        # ---- c_arpvback() (the LED task, Shift not held): the kept values played back; clobbers r0-r3
        a.label("c_arpvback")
        E(push_list, [4, 5, 6, 7], lr=True)
        E(bl, "c_arpvst"); E(ldr_imm, 6, 0, 4); E(cmp_imm, 6, 0); E(b_cond, "pb_x", "eq")
        E(movs_imm, 1, 0); E(str_imm, 1, 0, 4); E(movs_imm, 7, 0)                                 # cleared first: once only, whatever happens
        a.label("pb_l")
        E(movs_imm, 0, 1); E(lsls_reg, 0, 7); E(tst_reg, 6, 0); E(b_cond, "pb_n", "eq")
        imm32(0, PVR + 8); E(ldrb_reg, 2, 0, 7); E(lsrs_imm, 0, 7, 3); E(movs_imm, 1, 7); E(ands_reg, 1, 7); E(bl, "c_arset")
        a.label("pb_n"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 32); E(b_cond, "pb_l", "lo")
        a.label("pb_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    if V3:
        # ---- c_arclr() -> r0 = 1 when Clear is held (Duplicate not); clobbers r1-r3
        a.label("c_arclr")
        E(push_list, [], lr=True)
        imm32(0, MGR); E(ldr_imm, 0, 0, 0x20); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
        E(movs_imm, 1, 3); E(ands_reg, 0, 1); E(cmp_imm, 0, 1); E(b_cond, "cl_0", "ne")
        E(movs_imm, 0, 1); E(pop_list, [], pc=True)
        a.label("cl_0"); E(movs_imm, 0, 0); E(pop_list, [], pc=True)

        # ---- c_arerase(r0 = track 0..3, r1 = step): lanes 0..7 of the step (its 6 micro steps) to 0xFF; clobbers r0-r3
        a.label("c_arerase")
        E(push_list, [4, 5], lr=True); E(mov_reg, 5, 1)
        E(bl, "c_arpat"); E(movs_imm, 1, 6); E(muls, 1, 5); E(adds_reg, 0, 0, 1); E(movw, 1, LANE0); E(adds_reg, 0, 0, 1)
        E(movs_imm, 2, 0xFF); E(movs_imm, 3, 8)
        a.label("er_l")
        for m in range(6): E(strb_imm, 2, 0, m)
        E(adds_imm8, 0, 192); E(subs_imm8, 3, 1); E(b_cond, "er_l", "ne")
        E(pop_list, [4, 5], pc=True)

        # ---- c_arkled(r0 = track, r1 = the frame): the previewed step's lanes on the knob LEDs, yellow, brightness = the value; clobbers r0-r3
        a.label("c_arkled")
        E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
        imm32(0, PVM); E(ldrb_imm, 1, 0, 0); E(subs_imm8, 1, 1); E(cmp_reg, 1, 4); E(b_cond, "kl_x", "ne"); E(ldrb_imm, 6, 0, 1)
        E(mov_reg, 0, 4); E(bl, "c_arpat"); E(movs_imm, 1, 6); E(muls, 1, 6); E(adds_reg, 0, 0, 1); E(movw, 1, LANE0); E(adds_reg, 0, 0, 1)
        E(movs_imm, 6, 0)
        a.label("kl_k")
        for m in range(6): E(ldrb_imm, 7, 0, m); E(cmp_imm, 7, 0xFF); E(b_cond, "kl_v", "ne")
        E(b, "kl_n")
        a.label("kl_v")
        E(adds_imm8, 7, 2); E(lsls_imm, 7, 7, 8); E(adds_imm8, 7, COL_AV)
        E(lsls_imm, 1, 6, 1); E(adds_imm8, 1, 2 * KNOB_LED0); E(strh_reg, 7, 5, 1)
        a.label("kl_n"); E(adds_imm8, 0, 192); E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "kl_k", "lo")
        a.label("kl_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    if INIT:
        # ---- c_arinit(r0 = track 0..3, r1 = lane) -> r0 = the lane's value in the project (a lane value), or 0xFF; clobbers r1-r3
        a.label("c_arinit")
        E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
        imm32(2, SESSION_OBJ); E(ldr_imm, 2, 2, 0x14); E(cmp_imm, 2, 0); E(b_cond, "ai_n", "eq")
        E(cmp_imm, 4, 2); E(b_cond, "ai_m", "hs")
        E(movw, 0, SYN_SZ); E(muls, 0, 4); E(adds_reg, 2, 2, 0)                                 # Synth 1 / 2: the patch of the record
        E(movs_imm, 0, 17); E(muls, 0, 5); E(adds_reg, 2, 2, 0)
        imm32(0, REC_SYN + MACRO_REC); E(adds_reg, 2, 2, 0)
        E(ldrb_imm, 0, 2, 0); E(cmp_imm, 0, 127); E(b_cond, "ai_n", "hi"); E(pop_list, [4, 5, 6], pc=True)
        a.label("ai_m")                                                                        # MIDI 1 / 2: the own engine on
        E(subs_imm8, 4, 2); E(mov_reg, 0, 4); E(bl, L["c_von"]); E(cmp_imm, 0, 0); E(b_cond, "ai_n", "eq")
        E(mov_reg, 0, 4); E(bl, L["c_vrow"]); E(ldrb_reg, 5, 0, 5)                              # r5 = the lane's code
        E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_arpjv"); E(cmp_imm, 1, 0); E(b_cond, "ai_v", "ne")
        imm32(2, L["t_def"]); E(raw, ldrsb_reg(0, 2, 5))                                       # no project data: the default
        a.label("ai_v"); E(mov_reg, 1, 0); E(mov_reg, 0, 5); E(bl, L["c_vtou"]); E(pop_list, [4, 5, 6], pc=True)
        a.label("ai_n"); E(movs_imm, 0, 0xFF); E(pop_list, [4, 5, 6], pc=True)

        # ---- c_arblk(r0 = MIDI track 0 / 1, r1 = block) -> r0 = projsyn's block b in the record (0: no record); clobbers r1-r3
        a.label("c_arblk")
        imm32(2, SESSION_OBJ); E(ldr_imm, 2, 2, 0x14); E(cmp_imm, 2, 0); E(b_cond, "bk_0", "eq")
        E(lsls_imm, 0, 0, 3); E(adds_reg, 0, 0, 1); imm32(1, PJ_PSIZE); E(muls, 0, 1)
        imm32(1, PJ_BLK0); E(adds_reg, 0, 0, 1); E(adds_reg, 0, 0, 2); E(raw, h(0x4770))
        a.label("bk_0"); E(movs_imm, 0, 0); E(raw, h(0x4770))

        # ---- c_arpjv(r0 = MIDI track 0 / 1, r1 = code) -> r0 = the code's value in the project's own-synth patch (projsyn's blocks), r1 = 1; r1 = 0 none
        a.label("c_arpjv")
        E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0)
        E(cmp_imm, 1, 1); E(b_cond, "pj_n", "lo"); E(cmp_imm, 1, 34); E(b_cond, "pj_n", "hi")
        E(adds_imm8, 1, MPCODE); E(mov_reg, 5, 1)                                              # r5 = its byte in the patch
        E(movs_imm, 1, 0); E(bl, "c_arblk"); E(cmp_imm, 0, 0); E(b_cond, "pj_n", "eq"); E(mov_reg, 6, 0)
        E(ldrb_imm, 1, 6, 0); E(cmp_imm, 1, PJ_SIG); E(b_cond, "pj_n", "ne")
        E(ldrb_imm, 1, 6, 1); E(lsls_imm, 2, 4, 4); E(cmp_reg, 1, 2); E(b_cond, "pj_n", "ne")
        for i, ch in enumerate(b"CTM1"): E(ldrb_imm, 1, 6, 2 + i); E(cmp_imm, 1, ch); E(b_cond, "pj_n", "ne")
        E(cmp_imm, 5, PJ_BLEN); E(b_cond, "pj_0", "lo")
        E(subs_imm8, 5, PJ_BLEN); E(mov_reg, 0, 4); E(movs_imm, 1, 1); E(bl, "c_arblk"); E(mov_reg, 6, 0)
        E(ldrb_imm, 1, 6, 0); E(cmp_imm, 1, PJ_SIG); E(b_cond, "pj_n", "ne")
        E(ldrb_imm, 1, 6, 1); E(lsls_imm, 2, 4, 4); E(adds_imm8, 2, 1); E(cmp_reg, 1, 2); E(b_cond, "pj_n", "ne")
        a.label("pj_0"); E(adds_reg, 6, 6, 5); E(movs_imm, 1, 2); E(raw, ldrsb_reg(0, 6, 1)); E(movs_imm, 1, 1); E(pop_list, [4, 5, 6], pc=True)
        a.label("pj_n"); E(movs_imm, 0, 0); E(movs_imm, 1, 0); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_arbase(r0 = track 0..3, r1 = lane) -> r0 = the lane value the track has now, or 0xFF (MIDI with the engine off); clobbers r1-r3
    a.label("c_arbase")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(cmp_imm, 0, 2); E(b_cond, "bs_m", "hs")
    E(movs_imm, 1, 17); E(muls, 1, 5); E(adds_imm8, 1, 174); E(bl, V.GETTER); E(pop_list, [4, 5], pc=True)
    a.label("bs_m")
    E(subs_imm8, 4, 2); E(mov_reg, 0, 4); E(bl, L["c_von"]); E(cmp_imm, 0, 0); E(b_cond, "bs_n", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_vrow"]); E(ldrb_reg, 5, 0, 5)                               # r5 = the lane's code
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, L["c_vvaddr"]); E(movs_imm, 1, 0); E(raw, ldrsb_reg(1, 0, 1))
    E(mov_reg, 0, 5); E(bl, L["c_vtou"]); E(pop_list, [4, 5], pc=True)
    a.label("bs_n"); E(movs_imm, 0, 0xFF); E(pop_list, [4, 5], pc=True)

    # ---- c_arread (in place of the playback's ldrb.w fp, [r0, #0x3a8]; r4 = the track, r6 = the lane, sl = the micro step, r5 = the object)
    a.label("c_arread")
    E(push_list, [1, 2, 3, 4, 5, 6, 7], lr=True)
    E(raw, ldrb_w(7, 0, 0x3A8))                                                              # r7 = the byte
    E(cmp_imm, 4, 3); E(b_cond, "rd_x", "hi"); E(cmp_imm, 6, 8); E(b_cond, "rd_x", "hs")
    E(raw, h(0x4651))                                                                        # mov r1, sl
    E(movs_imm, 2, 6); E(raw, udiv(1, 1, 2))                                                 # r1 = the step
    E(push_list, [1]); E(mov_reg, 0, 4); E(bl, "c_arpat"); E(pop_list, [1])
    E(movs_imm, 2, 28); E(muls, 1, 2); E(adds_reg, 0, 0, 1); E(ldrb_imm, 0, 0, 3)              # r0 = byte [3] of the step
    E(lsls_imm, 1, 4, 3); E(adds_reg, 1, 1, 6); E(movs_imm, 2, 1); E(lsls_reg, 2, 1)           # r1 = 8 t + k, r2 = its bit
    E(push_list, [0, 1, 2]); E(bl, "c_arst"); E(ldr_imm, 3, 0, 0); E(pop_list, [0, 1, 2])      # r3 = the flags
    E(movs_imm, 6, MARK); E(tst_reg, 0, 6); E(b_cond, "rd_nm", "eq")
    E(movs_imm, 7, 0xFF)                                                                      # a marked step: nothing plays
    E(tst_reg, 3, 2); E(b_cond, "rd_x", "eq")
    E(bics_reg, 3, 2); imm32(0, RAM); E(str_imm, 3, 0, 0)
    if INIT:                                                                                  # r6 = the project's value
        E(push_list, [1]); E(mov_reg, 0, 4); E(movs_imm, 2, 7); E(ands_reg, 1, 2); E(bl, "c_arinit"); E(pop_list, [1]); E(mov_reg, 6, 0)
        E(cmp_imm, 6, 0xFF); E(b_cond, "rd_hv", "ne")
    imm32(0, RAM + 4); E(ldrb_reg, 6, 0, 1); E(cmp_imm, 6, 0xFF); E(b_cond, "rd_x", "eq")      # r6 = the base
    if INIT: a.label("rd_hv")
    E(movs_imm, 0, 7); E(ands_reg, 1, 0)                                                     # r1 = k
    E(ldr_imm, 0, 5, 0x2C); E(lsls_imm, 2, 4, 2)
    E(adds_reg, 0, 0, 2); E(ldr_imm, 0, 0, 0); E(bl, PARAM_WPTR); E(strb_imm, 6, 0, 0)        # p[k] of the track's macro store = the base
    E(b, "rd_x")
    a.label("rd_nm")                                                                          # a value about to play: the base, the first time
    E(cmp_imm, 7, 0xFF); E(b_cond, "rd_x", "eq"); E(tst_reg, 3, 2); E(b_cond, "rd_x", "ne")
    E(orrs_reg, 3, 2); imm32(0, RAM); E(str_imm, 3, 0, 0)
    E(push_list, [1]); E(mov_reg, 0, 4); E(movs_imm, 2, 7); E(ands_reg, 1, 2); E(bl, "c_arbase"); E(pop_list, [1])
    imm32(2, RAM + 4); E(strb_reg, 0, 2, 1)
    a.label("rd_x"); E(raw, h(0x46BB))                                                       # mov fp, r7
    E(pop_list, [1, 2, 3, 4, 5, 6, 7], pc=True)

    # ---- c_arknob (slot 4 of the macro handlers: obj, knob, delta): a synth's macro turned by hand = its lane's flag cleared
    a.label("c_arknob")
    E(push_list, [0, 1, 2, 3, 4], lr=True)
    imm32(3, V.CTX_PTR); E(ldr_imm, 3, 3, 0); E(cmp_imm, 3, 0); E(b_cond, "kn_x", "eq")
    E(ldr_imm, 3, 3, 0x40); E(cmp_imm, 3, 0); E(b_cond, "kn_x", "eq")
    E(ldr_imm, 3, 3, 0x2C); E(cmp_imm, 3, 0); E(b_cond, "kn_x", "eq")
    E(movs_imm, 4, 0)
    E(raw, h(0xF8D3) + h(2 << 12 | 0x148)); E(cmp_reg, 2, 0); E(b_cond, "kn_f", "eq")        # ldr.w r2, [r3, #0x148]: Synth 1's
    E(movs_imm, 4, 8)
    E(raw, h(0xF8D3) + h(2 << 12 | 0x14C)); E(cmp_reg, 2, 0); E(b_cond, "kn_x", "ne")        # Synth 2's
    a.label("kn_f")
    E(movs_imm, 2, 7); E(ands_reg, 1, 2); E(adds_reg, 1, 1, 4); E(movs_imm, 2, 1); E(lsls_reg, 2, 1)
    E(push_list, [2]); E(bl, "c_arst"); E(pop_list, [2]); E(ldr_imm, 1, 0, 0); E(bics_reg, 1, 2); E(str_imm, 1, 0, 0)
    a.label("kn_x"); E(raw, popw([0, 1, 2, 3, 4], lr=True)); E(b_w, prev["knob"])

    # ---- c_arsync (in place of vcf21's bl c_vsync: track 0 / 1, code, value): the lane of the code, its flag cleared; then c_vsync
    a.label("c_arsync")
    E(push_list, [0, 1, 2, 4], lr=True); E(mov_reg, 4, 0)
    E(bl, L["c_vlane"]); E(cmp_imm, 0, 8); E(b_cond, "sy_x", "hs")
    E(lsls_imm, 1, 4, 3); E(adds_reg, 0, 0, 1); E(adds_imm8, 0, 16); E(movs_imm, 1, 1); E(lsls_reg, 1, 0)   # bit 8 (t + 2) + k
    E(mov_reg, 3, 1); E(bl, "c_arst"); E(ldr_imm, 1, 0, 0); E(bics_reg, 1, 3); E(str_imm, 1, 0, 0)
    a.label("sy_x"); E(raw, popw([0, 1, 2, 4], lr=True)); E(b_w, L["c_vsync"])
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the heads of slots 0 / 1 of the step objects, of slot 4 of the macro handlers and of the LED task chain;
    the playback's lane read; vcf21's calls of c_vsync."""
    import ct_fw
    import fxdiag as FD
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("vcf20", k) for k in ("c_sdpat", "c_von", "c_vrow", "c_vvaddr", "c_vtou", "c_vlane", "c_vsync")}
    if V2: L["c_vapply"] = lab("vcf20", "c_vapply")
    if INIT:
        import projsyn as PS                       # (installed after autorel: only its layout)
        assert (PS.SIG, PS.BLEN, PS.SESSION_OBJ, PS.AREA + PS.SET + PS.BYTE0, PS.PSIZE) == (PJ_SIG, PJ_BLEN, SESSION_OBJ, PJ_BLK0, PJ_PSIZE)
        L["t_def"] = lab("vcf20", "t_def")
    L["c_shift"] = lab("sc15", "c_shift")
    KN = V.AC64_VT
    import recinst as RI
    prev = dict(spad=u(RI.STEP_VT) & ~1, srel=u(RI.STEP_VT + 4) & ~1, knob=u(KN + 16) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, L, prev)
    end0 = BASE + len(img)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    struct.pack_into("<I", img, RI.STEP_VT - BASE, labels["c_arpad"] | 1)
    struct.pack_into("<I", img, RI.STEP_VT + 4 - BASE, labels["c_arrelp"] | 1)
    struct.pack_into("<I", img, KN + 16 - BASE, labels["c_arknob"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_arled"])
    assert bytes(img[PB_READ - BASE:PB_READ - BASE + 4]) == PB_OLD, bytes(img[PB_READ - BASE:PB_READ - BASE + 4]).hex()
    img[PB_READ - BASE:PB_READ - BASE + 4] = bl(PB_READ, labels["c_arread"])
    sites = MX.bl_sites(img, 0x0805CDDC, end0, L["c_vsync"], BASE)
    assert len(sites) == 3, [hex(s) for s in sites]
    for s in sites: img[s - BASE:s - BASE + 4] = bl(s, labels["c_arsync"])
    return labels, code, prev
