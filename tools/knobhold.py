"""SC56.7 / Beta 5.52 (the user, 2026-11-12: «Al mover un knob mientras se cambia de vista, el knob retiene su asignación anterior hasta que se deja
de tocar durante un segundo», «Retén [páginas] internas. Shift no afecta al knob hasta que termine el segundo», «El comportamiento completo "retener
knob" se activa o desactiva en Setup», «Botón Preset en setup (off por defecto)»): knob hold.

Every knob turn goes through the controller's entry 0x08033848 (ctrl, knob, delta), which hands it to the view on the screen ([ctrl + 0x6C], or the
Setup view [ctrl + 0x68]); what a knob does then depends on a few bytes of state: the view, the mode, Shift, the container's track and sub-view, and
each view's page.  With the hold on, the first turn of a knob after a second untouched takes a snapshot of those bytes (the CELLS below, masked);
while the knob keeps turning (less than HOLD_MS since its last event) and the state differs from its snapshot, each event runs with the snapshot
written back for the length of the call (the old view / track / page / Shift: what the handlers see is the old screen) and the current state put
back after.  The knob events and the LED task run in the same task, so nothing draws the swapped state; the view pointer is swapped as a whole word.

  * cells: the view on the screen (word), the mode (p0 of [ctrl + 0x14]), [ctrl + 0x152] (the track / sub-view the buttons see), Shift (p0 of
    [ctrl + 0xC]), the container's track (p0 of [cont + 0x188]) and sub-view ([cont + 0x18C]: 7 = Sidechain), the Mixer's page ([mixer + 0xAD]),
    the FX view's page (p0 of [fx + 0x20]), Advanced Setup ([setup + 0x24]), the own synth's knob page of MIDI 1 / 2 (vcf21: RT_TAG bits 1-2, the
    synth nibble's bit 0), the step-drummer's view / page / half (vcf21's flags bits 4-6), the Master FX block's mode / selected set, SC16's
    Sidechain page / drum, sckn's track, splitknob's track held;
  * Clear is not held (Clear + knob acts at once); the knob LEDs show the new screen (use_freeze: a held knob's LED stays as it was);
  * the switch: the normal Setup page, Preset (id 8, nothing there in the stock), no Shift = bit 4 of gmdrum's flags (saved with the unit's
    settings, off at the factory); Preset's LED 40 = 0x74 on / 0x55 off (the stock's toggle colours, as Note's next to it).
RAM KH = 0x2004F900 (free: S514D, between packio's PCR, which ends at 0x2004F8B4, and 0x2004FC00): + 0 "KHL1", + 4 the view word put aside during a
held call, + 8 the cells' bytes put aside, + 32 the cells' addresses, + 128 + 32 k knob k: + 0 its last event (ms), + 4 a snapshot taken, + 8 the view
word, + 12 the cells' bytes (masked); + 384 the knob entry's r0-r2, r4-r7, LR, + 416 / + 420 the LED wrapper's LR / frame, + 424 the knobs'
kept LEDs (use_freeze; nothing of
ours on the stack while the stock's knob path or the LED chain below runs: the panel task's stack is tight, issue #22).  In the dspz gap.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, bics_reg, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, lsls_imm, mov_reg,  # noqa: E402
                   movs_imm, movt, movw, orrs_reg, pop_list, push_list, raw, str_imm, strb_imm, strh_imm, ands_reg, subs_reg, ldrh_imm)
import mpatch as MP  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import pgmch as PG  # noqa: E402
import gmdrum as G  # noqa: E402
import vcf21 as V  # noqa: E402
import build_sc14 as S14  # noqa: E402
import build_sc17 as S17  # noqa: E402
import splitknob as SKN  # noqa: E402

KNOB = 0x08033848
MGR, CONT, MIXER, FXV = 0x20040B10, 0x20040DB8, 0x200447D4, 0x200443B4
HAL_TICK, PARAM_GET = 0x2000081C, 0x0803542C
HOLD_MS = 1000
N_KNOBS = 8
F_KH = 0x10                                                   # bit 4 of gmdrum's flags byte
PRESET_BTN, LED_PRESET = 8, 40
COL_ON, COL_OFF = 0x74, 0x55
KH, SIG = 0x2004F900, 0x314C484B                              # "KHL1"
O_VIEW, O_CUR, O_ADDR, O_KN, KN_SIZE = 4, 8, 32, 128, 32
K_TIME, K_OK, K_VIEW, K_CELLS = 0, 4, 8, 12
O_STASH = O_KN + N_KNOBS * KN_SIZE                            # the knob entry's r0-r2, r4-r7, LR; the LED wrapper's LR and frame
O_LLR, O_LFR = O_STASH + 32, O_STASH + 36
O_LED = O_STASH + 40                                          # (FREEZE) each knob's LED halfword as last drawn while not held
SIZE = O_LED + 2 * N_KNOBS
assert KH >= 0x2004F8B4 and KH + SIZE <= 0x2004FAC0          # (patmut / fmmap keep their LR at 0x2004FAC0 / 0x2004FAC8)
KNOB_LED = 60                                                 # the frame's knob LEDs 60..67
FREEZE = False


def use_freeze():
    """(the user, 2026-11-12: «el knob capture funciona, pero sería mejor si mantuviera el color mientras dure» → «sí» to the frozen LED): while a
    knob is held with the state changed, its LED is the one drawn just before (colour and brightness as they were); every other frame each
    knob's LED is kept in RAM.  The old view is not drawn again (modules count on one pass per frame)."""
    global FREEZE
    FREEZE = True
STM_MASK = 0x40F7                                             # r0-r2, r4-r7, lr

ABS, PARAM = 0, 1
TAIL = V.TAIL
ST = S14.ST
MFX = ST + S17.GFX_OFF
CELLS = [                                                     # (kind, address, mask): ABS = the byte at the address; PARAM = p0 of the store at [address]
    (PARAM, MGR + PG.MODE_STORE, 0xFF),                       # the mode
    (ABS, MGR + 0x152, 0xFF),                                 # the track / sub-view the button entry sees (srcview)
    (PARAM, MGR + 0xC, 0xFF),                                 # Shift
    (PARAM, CONT + 0x188, 0xFF),                              # the container's track
    (ABS, CONT + 0x18C, 0xFF),                                # the container's sub-view (7 = Sidechain)
    (ABS, MIXER + 0xAD, 0xFF),                                # the Mixer's page (levels / pan)
    (PARAM, FXV + 0x20, 0xFF),                                # the FX view's page (reverb / delay)
    (ABS, PG.SETUP_OBJ + PG.ADV_OFF, 0xFF),                   # Advanced Setup
    (ABS, TAIL + V.O_RT + V.RT_TAG, 0x06),                    # MIDI 1's own-synth knob page (bits 1-2)
    (ABS, TAIL + V.O_RT + 8 + V.RT_TAG, 0x06),                # MIDI 2's
    (ABS, TAIL + V.O_SD + 1, 0x11),                           # the pages' third bit (bit 4 t)
    (ABS, TAIL + V.O_FLAGS, 0x70),                            # the step-drummer's view / page / half
    (ABS, MFX + S17.S_MODE, 0xFF),                            # Master FX on the Mixer
    (ABS, MFX + S17.S_SEL, 0xFF),                             # its knob set
    (ABS, ST + 24 + 12, 0xFF),                                # SC16's Sidechain page
    (ABS, ST + 24 + 13, 0xFF),                                # its drum
    (ABS, ST + 144, 0xFF),                                    # sckn's tag
    (ABS, ST + 145, 0xFF),                                    # sckn's track
    (ABS, SKN.SKR + SKN.O_TRK, 0xFF),                         # splitknob's track held
]
NC = len(CELLS)
assert O_CUR + NC <= O_ADDR and O_ADDR + 4 * NC <= O_KN and K_CELLS + NC <= KN_SIZE
INV = {"eq": "ne", "ne": "eq", "lo": "hs", "hs": "lo", "hi": "ls", "ls": "hi"}


def W(rt, rn, imm, op): return h(op | rn) + h(rt << 12 | imm)
def ldrb_w(rt, rn, imm): return W(rt, rn, imm, 0xF890)
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
RET = h(0x4770)


def table():
    return b"".join(struct.pack("<IBBH", addr, kind, mask, 0) for kind, addr, mask in CELLS)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def bc(target, cond):
        zc[0] += 1; n = f"_h{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    TAB = base
    a.label("kh_tab"); E(raw, table())

    # ---- c_khon() -> r0 = the switch (0 / F_KH); clobbers r1-r3
    a.label("c_khon")
    E(raw, h(0xB500)); E(bl, L["c_gmsig"]); E(cmp_imm, 0, 0); E(b_cond, "ho_x", "eq")
    E(movs_imm, 0, G.P0); E(movs_imm, 1, 0); E(bl, L["c_gmp"]); E(ldrb_imm, 0, 0, G.B_FLAGS); E(movs_imm, 1, F_KH); E(ands_reg, 0, 1)
    a.label("ho_x"); E(raw, h(0xBD00))

    # ---- c_khst() -> r0 = KH, signed (the knobs' snapshots cleared the first time); clobbers r1, r2
    a.label("c_khst")
    imm32(0, KH); E(ldr_imm, 1, 0, 0); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "hs_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0)
    for k in range(N_KNOBS): E(raw, W(1, 0, O_KN + KN_SIZE * k + K_OK, 0xF880))       # strb.w r1, [r0, #...]
    a.label("hs_x"); E(raw, RET)

    # ---- c_khadr (r4 = KH): the cells' addresses to KH + O_ADDR; clobbers r0-r3, r6, r7
    a.label("c_khadr")
    E(raw, h(0xB500)); imm32(6, TAB); E(movs_imm, 7, 0)
    a.label("ha_l")
    E(ldr_imm, 0, 6, 0); E(ldrb_imm, 1, 6, 4); E(cmp_imm, 1, ABS); E(b_cond, "ha_w", "eq")
    E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 0); E(bl, PARAM_GET)
    a.label("ha_w")
    E(lsls_imm, 1, 7, 2); E(adds_reg, 1, 1, 4); E(str_imm, 0, 1, O_ADDR)
    E(adds_imm8, 6, 8); E(adds_imm8, 7, 1); E(cmp_imm, 7, NC); E(b_cond, "ha_l", "lo")
    E(raw, h(0xBD00))

    # the cell loops (after push {r6, r7, lr}): r4 = KH, r5 = the knob's slot; r7 = i, r6 = the table entry; r0 = the cell's address, r1 = its
    # byte, r2 = the mask; the end: pop {r6, r7, pc}
    def cell_loop(name, body):
        E(push_list, [6, 7], lr=True); imm32(6, TAB); E(movs_imm, 7, 0)
        a.label(name)
        E(lsls_imm, 0, 7, 2); E(adds_reg, 0, 0, 4); E(ldr_imm, 0, 0, O_ADDR); E(ldrb_imm, 1, 0, 0); E(ldrb_imm, 2, 6, 5)
        body()
        E(adds_imm8, 6, 8); E(adds_imm8, 7, 1); E(cmp_imm, 7, NC); E(b_cond, name, "lo")
    def slot_byte(rd):                                        # rd = the snapshot byte of cell i (r5 + K_CELLS + i); clobbers r3
        E(adds_reg, 3, 5, 7); E(ldrb_imm, rd, 3, K_CELLS)

    # ---- c_khsnap: the view word and the cells (masked) to the knob's slot; clobbers r0-r3
    def snap_body():
        E(ands_reg, 1, 2); E(adds_reg, 3, 5, 7); E(strb_imm, 1, 3, K_CELLS)
    a.label("c_khsnap")
    imm32(0, MGR); E(ldr_imm, 0, 0, 0x6C); E(str_imm, 0, 5, K_VIEW)
    cell_loop("hn_l", snap_body)
    E(pop_list, [6, 7], pc=True)

    # ---- c_khcmp -> r0 = 0 the same state, 1 changed; clobbers r1-r3
    def cmp_body():
        E(ands_reg, 1, 2); slot_byte(3); E(cmp_reg, 1, 3); E(b_cond, "hc_d", "ne")
    a.label("c_khcmp")
    imm32(0, MGR); E(ldr_imm, 0, 0, 0x6C); E(ldr_imm, 1, 5, K_VIEW); E(cmp_reg, 0, 1); E(b_cond, "hc_dv", "ne")
    cell_loop("hc_l", cmp_body)
    E(movs_imm, 0, 0); E(pop_list, [6, 7], pc=True)
    a.label("hc_d"); E(movs_imm, 0, 1); E(pop_list, [6, 7], pc=True)
    a.label("hc_dv"); E(movs_imm, 0, 1); E(raw, RET)

    # ---- c_khswap: the current state put aside (KH + O_VIEW / O_CUR), the snapshot written; clobbers r0-r3
    def swap_body():
        E(mov_reg, 3, 1); E(ands_reg, 3, 2); E(push_list, [0]); E(adds_reg, 0, 4, 7); E(strb_imm, 3, 0, O_CUR); E(pop_list, [0])
        E(bics_reg, 1, 2); slot_byte(3); E(orrs_reg, 1, 3); E(strb_imm, 1, 0, 0)
    a.label("c_khswap")
    imm32(0, MGR); E(ldr_imm, 1, 0, 0x6C); E(str_imm, 1, 4, O_VIEW); E(ldr_imm, 1, 5, K_VIEW); E(str_imm, 1, 0, 0x6C)
    cell_loop("hw_l", swap_body)
    E(pop_list, [6, 7], pc=True)

    # ---- c_khrest: the current state back (the masked bits only: what the call changed elsewhere in those bytes stays); clobbers r0-r3
    def rest_body():
        E(bics_reg, 1, 2); E(adds_reg, 3, 4, 7); E(ldrb_imm, 3, 3, O_CUR); E(orrs_reg, 1, 3); E(strb_imm, 1, 0, 0)
    a.label("c_khrest")
    imm32(0, MGR); E(ldr_imm, 1, 4, O_VIEW); E(str_imm, 1, 0, 0x6C)
    cell_loop("hr_l", rest_body)
    E(pop_list, [6, 7], pc=True)

    # ---- c_khknob (the controller's knob entry: ctrl, knob, delta).  Nothing of ours stays on the stack while the stock's knob path runs: the
    # registers and LR go to KH + O_STASH (the knob events come one at a time, from the panel task)
    STM = h(0xE883) + h(STM_MASK)                             # stm.w r3, {r0-r2, r4-r7, lr}
    LDM = h(0xE893) + h(STM_MASK)                             # ldm.w r3, {r0-r2, r4-r7, lr}
    a.label("c_khknob")
    imm32(3, KH + O_STASH); E(raw, STM)
    E(cmp_imm, 1, N_KNOBS); bc("hk_pass", "hs")
    E(bl, "c_khon"); E(cmp_imm, 0, 0); bc("hk_pass", "eq")
    E(bl, "c_khst"); E(mov_reg, 4, 0)
    E(bl, "c_khadr")
    E(ldr_imm, 1, 4, O_STASH + 4) if O_STASH + 4 <= 124 else (imm32(1, KH + O_STASH), E(ldr_imm, 1, 1, 4))
    E(lsls_imm, 5, 1, 5); E(adds_reg, 5, 5, 4); E(movs_imm, 0, O_KN); E(adds_reg, 5, 5, 0)
    imm32(6, HAL_TICK); E(ldr_imm, 6, 6, 0)
    E(ldrb_imm, 0, 5, K_OK); E(cmp_imm, 0, 0); E(b_cond, "hk_snap", "eq")
    E(ldr_imm, 0, 5, K_TIME); E(subs_reg, 0, 6, 0); imm32(1, HOLD_MS); E(cmp_reg, 0, 1); E(b_cond, "hk_snap", "hs")
    E(str_imm, 6, 5, K_TIME)
    E(bl, "c_khcmp"); E(cmp_imm, 0, 0); E(b_cond, "hk_pass", "eq")
    E(bl, "c_khswap")
    imm32(3, KH + O_STASH); E(ldr_imm, 0, 3, 0); E(ldr_imm, 1, 3, 4); E(ldr_imm, 2, 3, 8)
    E(bl, prev["knob"])                                       # r4 / r5 kept by the callee
    E(bl, "c_khrest")
    imm32(3, KH + O_STASH); E(raw, LDM); E(raw, h(0x4770))
    a.label("hk_snap")
    E(str_imm, 6, 5, K_TIME); E(movs_imm, 0, 1); E(strb_imm, 0, 5, K_OK); E(bl, "c_khsnap")
    a.label("hk_pass")
    imm32(3, KH + O_STASH); E(raw, LDM); E(b_w, prev["knob"])

    # ---- c_khbtn (the Setup view's slot 2: view, button): the normal page's Preset = the switch flipped
    a.label("c_khbtn")
    E(push_list, [0, 1, 2, 4], lr=True)
    E(cmp_imm, 1, PRESET_BTN); E(b_cond, "hb_f", "ne")
    E(raw, ldrb_w(0, 0, PG.ADV_OFF)); E(cmp_imm, 0, 0); E(b_cond, "hb_f", "ne")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "hb_f", "ne")
    E(bl, L["c_gmsig"]); E(movs_imm, 1, 0); E(cmp_imm, 0, 0); E(b_cond, "hb_w", "eq")
    E(movs_imm, 0, G.P0); E(movs_imm, 1, 0); E(bl, L["c_gmp"]); E(ldrb_imm, 1, 0, G.B_FLAGS)
    a.label("hb_w"); E(movs_imm, 0, F_KH); E(raw, h(0x4041))                                 # eors r1, r0
    E(movs_imm, 0, G.B_FLAGS); E(bl, L["c_gmput"]); E(bl, L["c_gmsave"])
    E(pop_list, [0, 1, 2, 4], pc=True)
    a.label("hb_f"); E(raw, popw([0, 1, 2, 4], lr=True)); E(b_w, prev["btn"])

    # ---- c_khled (the LED task calls: ctrl, frame): the chain first, with nothing of ours on the stack (LR and the frame in RAM: the LED task's
    # stack is tight, SC54); then the normal Setup page: Preset's LED
    a.label("c_khled")
    imm32(2, KH + O_LLR); E(raw, h(0xF8C2) + h(0xE000)); E(str_imm, 1, 2, 4)                  # str.w lr, [r2]; str r1, [r2, #4]
    E(bl, prev["ledtask"])
    E(push_list, [4, 5, 6, 7] if FREEZE else [4, 5])
    if FREEZE:
        # each knob: held with the state changed = its kept LED; else its LED kept
        E(bl, "c_khon"); E(cmp_imm, 0, 0); bc("hf_x", "eq")
        E(bl, "c_khst"); E(mov_reg, 4, 0); E(bl, "c_khadr")
        imm32(6, HAL_TICK); E(ldr_imm, 6, 6, 0); E(movs_imm, 7, 0)
        a.label("hf_l")
        E(lsls_imm, 5, 7, 5); E(adds_reg, 5, 5, 4); E(movs_imm, 0, O_KN); E(adds_reg, 5, 5, 0)
        E(ldrb_imm, 0, 5, K_OK); E(cmp_imm, 0, 0); E(b_cond, "hf_k", "eq")
        E(ldr_imm, 0, 5, K_TIME); E(subs_reg, 0, 6, 0); imm32(1, HOLD_MS); E(cmp_reg, 0, 1); E(b_cond, "hf_k", "hs")
        E(bl, "c_khcmp"); E(cmp_imm, 0, 0); E(b_cond, "hf_k", "eq")
        E(bl, "hf_ad"); E(ldrh_imm, 3, 2, 0); E(strh_imm, 3, 0, 0); E(b, "hf_n")             # held: the kept LED to the frame
        a.label("hf_k")
        E(bl, "hf_ad"); E(ldrh_imm, 3, 0, 0); E(strh_imm, 3, 2, 0)                          # else: the frame's LED kept
        a.label("hf_n")
        E(adds_imm8, 7, 1); E(cmp_imm, 7, N_KNOBS); E(b_cond, "hf_l", "lo")
        E(b, "hf_x")
        a.label("hf_ad")                                                                   # r0 = the frame's LED of knob r7, r2 = its kept one
        imm32(0, KH + O_LFR); E(ldr_imm, 0, 0, 0); E(lsls_imm, 1, 7, 1); E(adds_reg, 0, 0, 1); E(adds_imm8, 0, 2 * KNOB_LED)
        imm32(2, KH + O_LED); E(adds_reg, 2, 2, 1); E(raw, RET)
        a.label("hf_x")
    imm32(0, KH + O_LFR); E(ldr_imm, 5, 0, 0)
    imm32(0, MGR); E(ldr_imm, 0, 0, PG.MODE_STORE); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(cmp_imm, 0, PG.MODE_SETUP); E(b_cond, "hl_x", "ne")
    imm32(0, PG.SETUP_OBJ); E(raw, ldrb_w(0, 0, PG.ADV_OFF)); E(cmp_imm, 0, 0); E(b_cond, "hl_x", "ne")
    E(bl, "c_khon"); E(movs_imm, 4, COL_ON); E(cmp_imm, 0, 0); E(b_cond, "hl_w", "ne"); E(movs_imm, 4, COL_OFF)
    a.label("hl_w"); E(movs_imm, 0, 2 * LED_PRESET); E(raw, h(0x522C))                        # strh r4, [r5, r0]
    a.label("hl_x"); E(pop_list, [4, 5, 6, 7] if FREEZE else [4, 5])
    imm32(2, KH + O_LLR); E(raw, h(0xF8D2) + h(0xF000))                                        # ldr.w pc, [r2]
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (dspz.add); hooks: the controller's knob entry (in front of what is there), the Setup view's slot 2, the LED task."""
    import ct_fw
    from thumb import bl as bl_enc
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("gmdrum", k) for k in ("c_gmsig", "c_gmp", "c_gmput", "c_gmsave")}
    L["c_shift"] = lab("sc15", "c_shift")
    assert base_addr % 4 == 0
    prev = dict(knob=MP.bw_target(img, KNOB, BASE), btn=u(PG.SETUP_VT + 8) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    img[KNOB - BASE:KNOB - BASE + 4] = b_w(KNOB, labels["c_khknob"])
    struct.pack_into("<I", img, PG.SETUP_VT + 8 - BASE, labels["c_khbtn"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_khled"])
    return labels, code, prev
