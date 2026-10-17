"""SC43.6 (the user, 2026-10-16 / 17: «On pan view, any shift+knob to the right toggles "Cue listening Mode" (octave down pink enabled, white
disabled) stored in setup. Shift+knob to the left to disable. On cue mode, performers can send mono signals through the left output and use the right
as a cue. … A knob to the right enables cue listening on the right channel, starting on 0 to max send. The pattern syncs to whatever step is in this
moment and starts reproducing only on the right channel. Only the cue listening patterns are heard. Left channel as usual. Knob to the left beyond
center does nothing. Channel selection pad remains in prior dim/bright state»; «Why DSP? can't this be solved with pan and arm/patterns?»): a cue
mode made with the stock's own levels and pans, on the ARM.

The stock (read in the firmware and the DSP program, emulated):
  * a track's level and pan are project parameters: Synth 1, Synth 2, MIDI 1, MIDI 2 = type 0x20 indices 46..49 / 50..53, Drum d = type 0x10
    indices 7 d + 1 / 7 d + 6; reverb / delay sends = type 0x20 indices 0..7 / 11..18; the DSP groups read them with the getter 0x08036192 (32
    calls, SITES) and write the level as v << 15 and the pan as w = p / 128 (p > 64: up to 1.0, 0x080287C4);
  * the DSP (P:$1B2B, the drums' P:$1B44): left = g x min(1, 2 (1 - w)), right = g x min(1, 2 w), g = level / 256 (x the side-chain): a balance
    law, the centre at full gain on both sides;
  * a mute is the sequencer's (the Mixer's 0x08046626(view, pad) toggles p0 of the store [[view + 0x68] + [view + 0x60] x pad] and commits; no
    DSP write); the Mixer's pads show a muted track in a dimmer code (MUTED); its pan page = [view + 0xAD] = 1 (Octave ▼).

Ours:
  * the mode = byte 3 of parameter 3 of the global settings (0xC5 = on; pgmch has bytes 1 / 2, the stock byte 0), written in both copies of the
    store without a commit (its listeners send MIDI) and saved by the stock's settings save (0x0802D2AC copies the read copy; deferred by
    lazysave);
  * the Mixer's pan page: Shift + a knob to the right = the mode on, to the left = off; in the mode a knob = that track's cue send c (0..127,
    from the centre to the right; to the left nothing), Clear + a knob = c back to 0; the stock's pans are not touched;
  * the getter calls of the 32 SITES -> c_cqg: in the mode, with L = the track's level (0 when it is muted but cued) and R = c, the DSP gets
    level = max(L, R) and the pan that gives L on the left and R on the right (L >= R: 64 R / L; else 127 - 63 L / R): a track without cue is hard
    left at its level; the sends of a cued muted track are 0;
  * a cued track is unmuted in the sequencer (its main mute kept in the record's tail + 158, bit t), so it plays only on the right; its pad keeps
    the muted look; the Mixer's pad toggles (also qmute's, at the next bar) act on that main mute; leaving the cue (c = 0, the mode off, a load)
    puts it back;
  * a project save writes the main mutes (the cued tracks' sequencer mutes put back around the stock's serialisation, 0x0802FE5E);
  * LEDs (the Mixer on the screen, not its Master FX page): Octave ▼ pink in the mode, white out of it; in the mode, on the pan page, the knobs in
    pink at the brightness of c;
  * RAM: c in the record's tail + 59..63 (Synth 1 .. Drum 1) and + 155..157 (Drum 2-4), the main mutes at + 158; reset by each load.
  * the delay / reverb returns and Master FX are shared: the cue (right) hears the effects of the whole mix.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, eors_reg, h, ldr_imm, ldr_sp, ldrb_imm, ldrb_w, ldrh_imm,  # noqa: E402
                   lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, strb_imm, subs_imm8, subs_reg,
                   ands_reg, bics_reg, add_sp_imm)
from build_sc14 import udiv  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import mpatch as MP  # noqa: E402
import persist19 as P19  # noqa: E402

GETTER = 0x08036192
SITES = (0x0802884E, 0x08028862, 0x080288EA, 0x080288FE, 0x0802897E, 0x08028992, 0x08028A12, 0x08028A26,      # the drums' level / pan
         *range(0x08028B86, 0x08028C05, 0x12), *range(0x08028C14, 0x08028C93, 0x12),                          # the reverb / delay sends
         0x08028D12, 0x08028D24, 0x08028DA8, 0x08028DBA, 0x08028EAA, 0x08028EBC, 0x08028ED2, 0x08028EE4)      # Synth 1/2, MIDI 1/2 level / pan
MGR, MIX_VIEW, MIX_VT, MIX_PAD, MIX_PAD_OLD = 0x20040B10, 0x200447D4, 0x0805A668, 0x08046626, bytes.fromhex("70b50c46")   # push {r4-r6, lr}; mov r4, r1
PAN_PAGE = 0xAD
CTX, P_SET, B_CUE, CUE_ON = 0x200069E4, 3, 3, 0xC5
SETOBJ, SAVE_SET = 0x2003974C, 0x0802D2AC
PARAM_GET, PARAM_WPTR, COMMIT, MARK_DIRTY = 0x0803542C, 0x080354FA, 0x080353C0, 0x0803BDCC
SESSION_OBJ, TAIL, O_C0, O_C1, O_MM = 0x2003D71C, 0x27024, 59, 150, 158      # c[t] = tail + 59 + t (t < 5) / + 150 + t (t >= 5); main mutes + 158
MUTED = (0x38, 0x26, 0x0F, 0x41, 0x46, 0x2E, 0x4A, 0x4E)                      # the Mixer's pad of a muted track (Synth 1 .. Drum 4)
PINK, WHITE = 0x5F, 0x01
LED_OCT, LED_KNOB0 = 51, 60


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def ctx(rd, off): imm32(rd, CTX); E(ldr_imm, rd, rd, 0); E(ldr_imm, rd, rd, 0); E(ldr_imm, rd, rd, off)
    RET = h(0x4770)
    E(raw, bytes(MUTED)); t_muted = base

    # ---- c_cqt() -> r0 = the record's tail, or 0; clobbers r1
    a.label("c_cqt")
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "qt_x", "eq")
    imm32(1, TAIL); E(adds_reg, 0, 0, 1)
    a.label("qt_x"); E(raw, RET)

    # ---- c_cqca(r0 = track 0..7) -> r0 = the address of its cue send, or 0; clobbers r1, r2
    a.label("c_cqca")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, "c_cqt"); E(cmp_imm, 0, 0); E(b_cond, "ca_x", "eq")
    E(adds_reg, 0, 0, 4); E(cmp_imm, 4, 5); E(b_cond, "ca_h", "hs"); E(adds_imm8, 0, O_C0); E(b, "ca_x")
    a.label("ca_h"); E(adds_imm8, 0, O_C1)
    a.label("ca_x"); E(pop_list, [4], pc=True)

    # ---- c_cqmm() -> r0 = the address of the main mutes, or 0; clobbers r1
    a.label("c_cqmm")
    E(push_list, [], lr=True); E(bl, "c_cqt"); E(cmp_imm, 0, 0); E(b_cond, "mm_x", "eq"); E(adds_imm8, 0, O_MM)
    a.label("mm_x"); E(pop_list, [], pc=True)

    # ---- c_cqbit(r0 = track) -> r0 = its main mute bit; clobbers r1-r3
    a.label("c_cqbit")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, "c_cqmm"); E(cmp_imm, 0, 0); E(b_cond, "cb_x", "eq")
    E(ldrb_imm, 0, 0, 0); E(raw, h(0x40E0)); E(movs_imm, 1, 1); E(ands_reg, 0, 1)            # lsrs r0, r4
    a.label("cb_x"); E(pop_list, [4], pc=True)

    # ---- c_cqcued(r0 = track) -> r0 = its cue send (0 = not cued); clobbers r1, r2
    a.label("c_cqcued")
    E(push_list, [], lr=True); E(bl, "c_cqca"); E(cmp_imm, 0, 0); E(b_cond, "cc_x", "eq"); E(ldrb_imm, 0, 0, 0)
    a.label("cc_x"); E(pop_list, [], pc=True)

    # ---- c_cqon() -> r0 = 1 in the cue mode (the settings' parameter 3, byte 3); clobbers r1-r3
    a.label("c_cqon")
    E(push_list, [], lr=True)
    imm32(0, CTX); E(ldr_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "on_n", "eq"); E(ldr_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "on_n", "eq")
    E(ldr_imm, 0, 0, 0x54); E(cmp_imm, 0, 0); E(b_cond, "on_n", "eq")
    E(movs_imm, 1, P_SET); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, B_CUE); E(cmp_imm, 0, CUE_ON); E(b_cond, "on_n", "ne")
    E(movs_imm, 0, 1); E(pop_list, [], pc=True)
    a.label("on_n"); E(movs_imm, 0, 0); E(pop_list, [], pc=True)

    # ---- c_cqms(r0 = track) -> r0 = the Mixer's mute store of it; clobbers r1, r2
    a.label("c_cqms")
    imm32(1, MIX_VIEW); E(ldr_imm, 2, 1, 0x60); E(muls, 0, 2); E(ldr_imm, 1, 1, 0x68); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0); E(raw, RET)

    # ---- c_cqgm(r0 = track) -> r0 = its sequencer mute 0 / 1; clobbers r1-r3
    a.label("c_cqgm")
    E(push_list, [], lr=True); E(bl, "c_cqms"); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(pop_list, [], pc=True)

    # ---- c_cqsm(r0 = track, r1 = 0 / 1): its sequencer mute through the store (committed); clobbers r0-r3
    a.label("c_cqsm")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_cqgm"); E(cmp_reg, 0, 5); E(b_cond, "sm_x", "eq")
    E(mov_reg, 0, 4); E(bl, "c_cqms"); E(mov_reg, 4, 0); E(movs_imm, 1, 0); E(bl, PARAM_WPTR); E(strb_imm, 5, 0, 0)
    E(mov_reg, 0, 4); E(bl, COMMIT)
    a.label("sm_x"); E(pop_list, [4, 5], pc=True)

    # ---- c_cqsb(r0 = track, r1 = 0 / 1): its main mute bit; clobbers r0-r3
    a.label("c_cqsb")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_cqmm"); E(cmp_imm, 0, 0); E(b_cond, "sb_x", "eq")
    E(movs_imm, 1, 1); E(raw, h(0x40A1)); E(ldrb_imm, 2, 0, 0); E(raw, h(0x438A))              # lsls r1, r4; bics r2, r1
    E(cmp_imm, 5, 0); E(b_cond, "sb_w", "eq"); E(orrs_reg, 2, 1)
    a.label("sb_w"); E(strb_imm, 2, 0, 0)
    a.label("sb_x"); E(pop_list, [4, 5], pc=True)

    # ---- c_cqdirty(r0 = track): its level / pan group and its two sends marked (the interface task only); clobbers r0-r3
    a.label("c_cqdirty")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(movs_imm, 0, 0x20); E(mov_reg, 1, 4); E(bl, MARK_DIRTY)
    E(movs_imm, 0, 0x20); E(mov_reg, 1, 4); E(adds_imm8, 1, 11); E(bl, MARK_DIRTY)
    E(cmp_imm, 4, 4); E(b_cond, "dy_d", "hs")
    E(movs_imm, 0, 0x20); E(mov_reg, 1, 4); E(adds_imm8, 1, 46); E(b, "dy_m")
    a.label("dy_d"); E(movs_imm, 0, 0x10); E(subs_imm8, 4, 4); E(lsls_imm, 1, 4, 3); E(subs_reg, 1, 1, 4); E(adds_imm8, 1, 1)
    a.label("dy_m"); E(bl, MARK_DIRTY)
    E(pop_list, [4], pc=True)

    # ---- c_cqlev(r0 = track) -> r0 = its stock level; clobbers r1-r3
    a.label("c_cqlev")
    E(cmp_imm, 0, 4); E(b_cond, "lv_d", "hs"); E(mov_reg, 1, 0); E(adds_imm8, 1, 46); E(movs_imm, 0, 0x20); E(b_w, GETTER)
    a.label("lv_d"); E(subs_imm8, 0, 4); E(lsls_imm, 1, 0, 3); E(subs_reg, 1, 1, 0); E(adds_imm8, 1, 1); E(movs_imm, 0, 0x10); E(b_w, GETTER)

    # ---- c_cqg (the DSP groups' getter calls: r0 = type, r1 = index) -> r0 = the value; in the cue mode the level / pan / sends of the cue
    a.label("c_cqg")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(bl, GETTER); E(mov_reg, 6, 0)
    E(bl, "c_cqon"); E(cmp_imm, 0, 0); E(b_cond, "g_r", "eq")
    E(cmp_imm, 4, 0x20); E(b_cond, "g_d", "ne")
    E(mov_reg, 7, 5); E(cmp_imm, 5, 8); E(b_cond, "g_s", "lo")
    E(subs_imm8, 7, 11); E(cmp_imm, 7, 7); E(b_cond, "g_s", "ls")
    E(mov_reg, 7, 5); E(subs_imm8, 7, 46); E(cmp_imm, 7, 7); E(b_cond, "g_r", "hi")
    E(movs_imm, 4, 1); E(cmp_imm, 7, 4); E(b_cond, "g_c", "lo"); E(movs_imm, 4, 2); E(subs_imm8, 7, 4); E(b, "g_c")   # r4 = 1 level / 2 pan, r7 = track
    a.label("g_d")
    E(cmp_imm, 5, 27); E(b_cond, "g_r", "hi"); E(movs_imm, 0, 7); E(raw, udiv(7, 5, 0)); E(muls, 0, 7); E(subs_reg, 0, 5, 0)   # r7 = drum, r0 = index % 7
    E(adds_imm8, 7, 4); E(movs_imm, 4, 1); E(cmp_imm, 0, 1); E(b_cond, "g_c", "eq"); E(movs_imm, 4, 2); E(cmp_imm, 0, 6); E(b_cond, "g_c", "eq"); E(b, "g_r")
    a.label("g_s")                                                                     # a send: 0 for a cued muted track
    E(mov_reg, 0, 7); E(bl, "c_cqcued"); E(cmp_imm, 0, 0); E(b_cond, "g_r", "eq")
    E(mov_reg, 0, 7); E(bl, "c_cqbit"); E(cmp_imm, 0, 0); E(b_cond, "g_r", "eq"); E(movs_imm, 6, 0); E(b, "g_r")
    a.label("g_c")                                                                     # L = the level (0 when muted and cued), R = c
    E(mov_reg, 5, 6); E(cmp_imm, 4, 1); E(b_cond, "g_l", "eq"); E(mov_reg, 0, 7); E(bl, "c_cqlev"); E(mov_reg, 5, 0)   # r5 = L
    a.label("g_l")
    E(mov_reg, 0, 7); E(bl, "c_cqcued"); E(mov_reg, 6, 0)                               # r6 = R
    E(cmp_imm, 6, 0); E(b_cond, "g_m", "eq"); E(mov_reg, 0, 7); E(bl, "c_cqbit"); E(cmp_imm, 0, 0); E(b_cond, "g_m", "eq"); E(movs_imm, 5, 0)
    a.label("g_m")
    E(cmp_reg, 5, 6); E(b_cond, "g_rr", "lo")
    E(cmp_imm, 4, 1); E(b_cond, "g_lp", "ne"); E(mov_reg, 6, 5); E(b, "g_r")            # L >= R: level L, pan 64 R / L
    a.label("g_lp"); E(cmp_imm, 5, 0); E(b_cond, "g_c64", "eq")
    E(lsls_imm, 0, 6, 6); E(lsrs_imm, 1, 5, 1); E(adds_reg, 0, 0, 1); E(raw, udiv(6, 0, 5)); E(b, "g_r")
    a.label("g_c64"); E(movs_imm, 6, 64); E(b, "g_r")
    a.label("g_rr")                                                                    # R > L: level R, pan 127 - 63 L / R
    E(cmp_imm, 4, 1); E(b_cond, "g_r", "eq")
    E(movs_imm, 0, 63); E(muls, 0, 5); E(lsrs_imm, 1, 6, 1); E(adds_reg, 0, 0, 1); E(raw, udiv(0, 0, 6)); E(movs_imm, 6, 127); E(subs_reg, 6, 6, 0)
    a.label("g_r"); E(mov_reg, 0, 6); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_cqput(r0 = track, r1 = c 0..127): its cue send; starting / leaving the cue moves its mute; marked; clobbers r0-r3
    a.label("c_cqput")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_cqca"); E(cmp_imm, 0, 0); E(b_cond, "pu_x", "eq"); E(ldrb_imm, 6, 0, 0); E(strb_imm, 5, 0, 0)   # r6 = the c before
    E(cmp_imm, 6, 0); E(b_cond, "pu_0", "eq")
    E(cmp_imm, 5, 0); E(b_cond, "pu_d", "ne")
    E(mov_reg, 0, 4); E(bl, "c_cqbit"); E(mov_reg, 1, 0); E(mov_reg, 0, 4); E(bl, "c_cqsm"); E(b, "pu_d")   # the cue left: its main mute back
    a.label("pu_0"); E(cmp_imm, 5, 0); E(b_cond, "pu_x", "eq")                           # the cue starts: the main mute kept, the track plays
    E(mov_reg, 0, 4); E(bl, "c_cqgm"); E(mov_reg, 1, 0); E(mov_reg, 0, 4); E(bl, "c_cqsb")
    E(mov_reg, 0, 4); E(movs_imm, 1, 0); E(bl, "c_cqsm")
    a.label("pu_d"); E(mov_reg, 0, 4); E(bl, "c_cqdirty")
    a.label("pu_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_cqmode(r0 = 1 on / 0 off): the setting written (its save deferred), the cues left, every track marked; clobbers r0-r3
    a.label("c_cqmode")
    E(push_list, [4, 5], lr=True); E(mov_reg, 5, 0)
    E(bl, "c_cqon"); E(cmp_reg, 0, 5); E(b_cond, "md_x", "eq")
    E(movs_imm, 4, 0)
    a.label("md_l"); E(mov_reg, 0, 4); E(movs_imm, 1, 0); E(bl, "c_cqput"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 8); E(b_cond, "md_l", "lo")
    E(movs_imm, 4, 0); E(cmp_imm, 5, 0); E(b_cond, "md_w", "eq"); E(movs_imm, 4, CUE_ON)
    a.label("md_w")
    for fn in (PARAM_WPTR, PARAM_GET):                                                  # both copies, no commit: no listener runs
        ctx(0, 0x54); E(movs_imm, 1, P_SET); E(bl, fn); E(strb_imm, 4, 0, B_CUE)
    imm32(0, SETOBJ); E(bl, SAVE_SET)
    E(movs_imm, 4, 0)
    a.label("md_k"); E(mov_reg, 0, 4); E(bl, "c_cqdirty"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 8); E(b_cond, "md_k", "lo")
    a.label("md_x"); E(pop_list, [4, 5], pc=True)

    # ---- c_cqmpad (the head of the Mixer's mute toggle 0x08046626: view, pad): a cued track's toggle = its main mute
    a.label("c_cqmpad")
    E(cmp_imm, 1, 8); E(b_cond, "mp_f", "hs")
    E(push_list, [0, 1, 2, 4], lr=True); E(mov_reg, 4, 1)
    E(bl, "c_cqon"); E(cmp_imm, 0, 0); E(b_cond, "mp_p", "eq")
    E(mov_reg, 0, 4); E(bl, "c_cqcued"); E(cmp_imm, 0, 0); E(b_cond, "mp_p", "eq")
    E(mov_reg, 0, 4); E(bl, "c_cqbit"); E(movs_imm, 1, 1); E(eors_reg, 1, 0); E(mov_reg, 0, 4); E(bl, "c_cqsb")
    E(mov_reg, 0, 4); E(bl, "c_cqdirty")
    E(pop_list, [0, 1, 2, 4], pc=True)
    a.label("mp_p"); E(raw, popw([0, 1, 2, 4], lr=True))
    a.label("mp_f"); E(raw, MIX_PAD_OLD); E(b_w, MIX_PAD + 4)

    # ---- c_cqknob (the Mixer view's slot 4: view, knob, delta): the pan page's Shift = the mode; in the mode a knob = its cue send
    a.label("c_cqknob")
    E(push_list, [0, 1, 2, 4, 5, 6], lr=True); E(mov_reg, 4, 1); E(mov_reg, 5, 2)
    E(cmp_imm, 4, 8); E(b_cond, "kn_p", "hs")
    E(bl, L["c_gact"]); E(cmp_imm, 0, 0); E(b_cond, "kn_p", "ne")                        # its Master FX page
    E(ldr_sp, 0, 0); E(ldrb_w, 0, 0, PAN_PAGE); E(cmp_imm, 0, 0); E(b_cond, "kn_p", "eq")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "kn_n", "eq")
    E(movs_imm, 0, 1); E(cmp_imm, 5, 0); E(b_cond, "kn_m", "gt"); E(movs_imm, 0, 0)
    a.label("kn_m"); E(bl, "c_cqmode"); E(b, "kn_e")
    a.label("kn_n")
    E(bl, "c_cqon"); E(cmp_imm, 0, 0); E(b_cond, "kn_p", "eq")
    imm32(0, MGR); E(ldr_imm, 0, 0, 0x20); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(movs_imm, 1, 3); E(ands_reg, 0, 1); E(movs_imm, 1, 0); E(cmp_imm, 0, 1); E(b_cond, "kn_w", "eq")   # Clear held: back to 0
    E(mov_reg, 0, 4); E(bl, "c_cqcued"); E(adds_reg, 1, 0, 5)
    E(cmp_imm, 1, 0); E(b_cond, "kn_l", "ge"); E(movs_imm, 1, 0)
    a.label("kn_l"); E(cmp_imm, 1, 127); E(b_cond, "kn_w", "le"); E(movs_imm, 1, 127)
    a.label("kn_w"); E(mov_reg, 0, 4); E(bl, "c_cqput")
    a.label("kn_e"); E(raw, add_sp_imm(12)); E(pop_list, [4, 5, 6], pc=True)
    a.label("kn_p"); E(raw, popw([0, 1, 2, 4, 5, 6], lr=True)); E(b_w, prev["knob"])

    # ---- c_cqsave (the project save's bl 0x0802F63C: the serialisation): around it the cued tracks' mutes = their main mutes (raw, no commit)
    a.label("c_cqsw")                                                                   # c_cqsw(r0 = 1 main / 0 back); clobbers r0-r3
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 7, 0); E(movs_imm, 4, 0)
    a.label("sw_l"); E(mov_reg, 0, 4); E(bl, "c_cqcued"); E(cmp_imm, 0, 0); E(b_cond, "sw_n", "eq")
    E(movs_imm, 5, 0); E(cmp_imm, 7, 0); E(b_cond, "sw_v", "eq"); E(mov_reg, 0, 4); E(bl, "c_cqbit"); E(mov_reg, 5, 0)
    a.label("sw_v")
    for fn in (PARAM_WPTR, PARAM_GET):
        E(mov_reg, 0, 4); E(bl, "c_cqms"); E(movs_imm, 1, 0); E(bl, fn); E(strb_imm, 5, 0, 0)
    a.label("sw_n"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 8); E(b_cond, "sw_l", "lo")
    E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("c_cqsave")
    E(push_list, [0, 4, 5], lr=True)
    E(bl, "c_cqon"); E(mov_reg, 5, 0); E(cmp_imm, 5, 0); E(b_cond, "sv_g", "eq"); E(movs_imm, 0, 1); E(bl, "c_cqsw")
    a.label("sv_g"); E(ldr_sp, 0, 0); E(bl, prev["save"])
    E(cmp_imm, 5, 0); E(b_cond, "sv_x", "eq"); E(movs_imm, 0, 0); E(bl, "c_cqsw")
    a.label("sv_x"); E(pop_list, [0, 4, 5], pc=True)

    # ---- c_cqload (the end of the stock's «apply session»): no cue from what a file holds
    a.label("c_cqload")
    E(raw, pushw([0, 1, 2, 3, 12], lr=True))
    E(movs_imm, 2, 0)
    a.label("lo_l"); E(mov_reg, 0, 2); E(push_list, [2]); E(bl, "c_cqca"); E(pop_list, [2]); E(cmp_imm, 0, 0); E(b_cond, "lo_x", "eq")
    E(movs_imm, 1, 0); E(strb_imm, 1, 0, 0); E(adds_imm8, 2, 1); E(cmp_imm, 2, 8); E(b_cond, "lo_l", "lo")
    E(bl, "c_cqmm"); E(cmp_imm, 0, 0); E(b_cond, "lo_x", "eq"); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 0)
    a.label("lo_x"); E(raw, popw([0, 1, 2, 3, 12], lr=True)); E(b_w, prev["load"])

    # ---- c_cqledtask (the LED task calls: ctrl, frame): the chain; the Mixer: Octave ▼ = the mode; the cued muted pads; the pan page's knobs
    a.label("c_cqledtask")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    imm32(0, MGR); E(ldr_imm, 0, 0, 0x6C); imm32(1, MIX_VIEW); E(cmp_reg, 0, 1); E(b_cond, "lt_x", "ne")
    E(bl, L["c_gact"]); E(cmp_imm, 0, 0); E(b_cond, "lt_x", "ne")
    E(bl, "c_cqon"); E(mov_reg, 6, 0)
    E(movs_imm, 1, WHITE); E(cmp_imm, 6, 0); E(b_cond, "lt_o", "eq"); E(movs_imm, 1, PINK)
    a.label("lt_o"); E(movs_imm, 0, 2 * LED_OCT); E(raw, h(0x5229))                       # strh r1, [r5, r0]
    E(cmp_imm, 6, 0); E(b_cond, "lt_x", "eq")
    E(movs_imm, 4, 0)
    a.label("lt_l")
    E(mov_reg, 0, 4); E(bl, "c_cqcued"); E(mov_reg, 7, 0)
    E(cmp_imm, 7, 0); E(b_cond, "lt_k", "eq"); E(mov_reg, 0, 4); E(bl, "c_cqbit"); E(cmp_imm, 0, 0); E(b_cond, "lt_k", "eq")
    E(lsls_imm, 1, 4, 1); E(raw, h(0x5A68)); E(cmp_imm, 0, 0); E(b_cond, "lt_k", "eq")     # ldrh r0, [r5, r1]: 0 = qmute's blink
    imm32(0, t_muted); E(adds_reg, 0, 0, 4); E(ldrb_imm, 0, 0, 0); E(raw, h(0x5268))      # strh r0, [r5, r1]
    a.label("lt_k")
    imm32(0, MIX_VIEW); E(ldrb_w, 0, 0, PAN_PAGE); E(cmp_imm, 0, 0); E(b_cond, "lt_n", "eq")
    E(mov_reg, 0, 7); E(cmp_imm, 0, 2); E(b_cond, "lt_b", "hs"); E(movs_imm, 0, 2)
    a.label("lt_b"); E(lsls_imm, 0, 0, 8); E(adds_imm8, 0, PINK)
    E(mov_reg, 1, 4); E(adds_imm8, 1, LED_KNOB0); E(lsls_imm, 1, 1, 1); E(raw, h(0x5268))   # strh r0, [r5, r1]
    a.label("lt_n"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 8); E(b_cond, "lt_l", "lo")
    a.label("lt_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the 32 getter calls, the head of the Mixer's mute toggle, the Mixer's slot 4, the save / load hooks, the LED task calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    L = dict(c_shift=int(report["sc15"]["labels"]["c_shift"], 16), c_gact=int(report["sc17"]["labels"]["c_gact"], 16))
    for s in SITES: assert bytes(img[s - BASE:s - BASE + 4]) == bl(s, GETTER), hex(s)
    assert bytes(img[MIX_PAD - BASE:MIX_PAD - BASE + 4]) == MIX_PAD_OLD
    prev = dict(knob=u(MIX_VT + 16) & ~1, save=FD.bl_target(img, P19.SAVE_CALL, BASE), load=MP.bw_target(img, P19.LOAD_END, BASE),
                ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    for s in SITES: img[s - BASE:s - BASE + 4] = bl(s, labels["c_cqg"])
    img[MIX_PAD - BASE:MIX_PAD - BASE + 4] = b_w(MIX_PAD, labels["c_cqmpad"])
    struct.pack_into("<I", img, MIX_VT + 16 - BASE, labels["c_cqknob"] | 1)
    img[P19.SAVE_CALL - BASE:P19.SAVE_CALL - BASE + 4] = bl(P19.SAVE_CALL, labels["c_cqsave"])
    img[P19.LOAD_END - BASE:P19.LOAD_END - BASE + 4] = b_w(P19.LOAD_END, labels["c_cqload"])
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_cqledtask"])
    return labels, code, prev
