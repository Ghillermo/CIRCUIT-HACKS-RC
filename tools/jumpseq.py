"""SC50 / Beta 5.3 (the user, 2026-11-01: «Incluye un nuevo modo de secuenciador en midi 1/2. Este secuenciador, cuando se apunta a cualquier otra de las siete
pistas, en vez de reproducir una nota, hace saltar el patrón al paso indicado.»): MIDI 1 / 2 as a jump sequencer.

  * pointing: the engine row of the MIDI Preset view (pad 27, modesel) has pads 9-16 free: the eight tracks in the order of the track buttons, in the stock's
    track colours (0x08056464: [1 + t] bright, [9 + t] dim), the chosen one bright, the track itself dark.  A press = point at that track, the chosen one
    again = off.  While pointing, pad 27 has the target's colour (the mode's indicator);
  * while pointing, the track plays no note: the transmitter's note-on and note-off (the outermost heads of 0x08059FC4 / + 4: no engine, MIDI out, shared
    channel) are swallowed for tracks 2 / 3; a note-on, from the sequencer, the pads or the arpeggiator, makes the target jump.  The recorder is not on
    this path: pads recorded on the track are jumps when played back.  With the transport stopped a pad does nothing;
  * the indicated step (the user: «las dos filas inferiores (pads 17-32) reubican el paso actual del secuenciador destino a los pasos 1-16 respectivamente. Octave up
    para elegir pasos 17 a 32. La escala no cambia este comportamiento.»; «En vista expandida, se muestran por orden los pasos 1-32»; «algunas configuraciones de Janko
    contienen pads con todo notas distintas»): while a pointing track's Note view is on the screen the keyboard is Jankó's, whatever the project has: a row of 8 notes
    2 semitones apart, the row above them 1 lower: 16 different notes a pair of rows, and the pairs have their own offsets.  c_jslt, each frame in the LED task, before
    Jankó's: the Note view = lower pair + 16 with the octave above 64; the expanded view = upper pair + 0, lower pair + 16.  The note then says the step, from the
    router's value v - 59 (the upper row of a pair first, the bit 0 of v - 59): step = (v & 16) | (v & 1) << 3 | (v >> 1 & 7).  A MIDI track at the transmitter has
    12 less, plus the project's root.  janko.use_jump: c_jkon on, so Octave is the stock's and the quantiser leaves the notes (also during a pointing player's
    clock): the scale changes nothing.  The other tracks keep their keyboard: the tables go back the frame the view goes;
  * the jump lands on the note's own step: a clock is the clock store's commit: its first listener is the engine (the tick 0x0802C418: the tracks advance),
    then every player's TICK_BUILD, then, on a second store, every player's TICK_PLAY (their slot 0, 0x0804A5C6, with [player + 0x14] / [player + 0x18]).
    So c_jsadv, around the advance's call in the tick, gives the pointing players those two notifications itself (the mute and every per-step condition are in
    there), the players' slot 0 drops them when they arrive, and what is pending is written into the target's playing store before its own TICK_BUILD;
  * a jump waits for the target's first tick of a step (+ 0x30 + 4 t, p2 = 0), so a pad lands on its next step, and a slower target on its next step.  A
    step outside the pattern's first / last plays and then the pattern ends, as any step past the end;
  * saved with the project: the record's tail + 364: the target + 1 of MIDI 1, of MIDI 2, the signature 0xA7 (+ 363..375: zero in the 165 sessions of the card's
    copy without garbage; the 8 of 02_Shadow Child hold 0x55 / 0x5B at the signature); a new project keeps the tail, so it clears the signature.
RAM: modmx.MXR + 0x21F0: + 0 0xA7, + 4 + t the step + 1 track t jumps to, + 12 + 4 m the player of MIDI m + 1 served in this clock; Jankó's RAM (with its signature) + 30 a
pointing track's Note view on the screen, + 31 in a pointing player's clock.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm3, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, it, ldr_imm, ldrb_imm, ldrb_reg, ldrh_reg, lsls_imm,  # noqa: E402
                   lsrs_imm, mov_reg, orrs_reg, movs_imm, movt, movw, pop_list, push_list, raw, str_imm, strb_imm, strb_reg, strh_imm, strh_reg, subs_imm3, subs_imm8, subs_reg)
import modmx as MX  # noqa: E402
import packio as PK  # noqa: E402
import mpatch as MP  # noqa: E402
import modesel as MS  # noqa: E402
import mutate39 as MU  # noqa: E402
import persist19 as P19  # noqa: E402
import fxdiag as FD  # noqa: E402
import janko as JK  # noqa: E402

RAM = MX.MXR + 0x21F0
SIG = 0xA7
SESSION_OBJ, TAIL, O_JS = 0x2003D71C, 0x27024, 364
ENG, ADV_CALL, ADV = 0x20038EC0, 0x0802C444, 0x0802C6E2                             # the tick's call of the tracks' advance
PLAYER0, PLAYER_SZ, PLAYER_VT, PLAYER_TICK = 0x20040200, 0x184, 0x0805B750, 0x0804A5C6
PLAYER_M = PLAYER0 + 2 * PLAYER_SZ                                                  # MIDI 1's
PARAM_WPTR, COMMIT = 0x080354FA, 0x080353C0
TRANSPORT = 0x20011034                                                              # p0 = running
TX_VT = 0x08059FC4
PAL = 0x08056464
ROW = 8                                                                             # pads 9-16
NOTE0 = 59 - 12                                                                     # the first step's note at the transmitter (12 below the router's) with the root at C
CAVE = 0x0805CE36                                                                   # SC03's c_txf (16 B): nothing calls it since SC06's c_txf2
MGR, S_CUR = 0x20040B10, 0x152
PAD = MS.PAD
POP_LR = h(0xF85D) + h(0xEB04)                                                      # ldr lr, [sp], #4
RET = h(0x4770)


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_jsad() -> r1 = our bytes in the record, flags eq = they hold our signature; clobbers r2, r3
    a.label("c_jsad")
    imm32(1, SESSION_OBJ); E(ldr_imm, 1, 1, 0x14); imm32(2, TAIL + O_JS); E(adds_reg, 1, 1, 2); E(ldrb_imm, 2, 1, 2); E(cmp_imm, 2, SIG); E(raw, RET)

    # ---- c_jsnon (the transmitter's note-on: tx, track, note, velocity): a pointing track's note = the jump, no note
    a.label("c_jsnon")
    E(push_list, [0, 1, 2, 3, 4], lr=True)
    E(subs_imm3, 0, 1, 2); E(cmp_imm, 0, 1); E(b_cond, "on_q", "hi"); E(bl, CAVE); E(cmp_imm, 0, 0); E(b_cond, "on_q", "eq"); E(mov_reg, 4, 0)
    imm32(0, TRANSPORT); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "on_x", "eq")
    E(raw, h(0x9802))                                                                # ldr r0, [sp, #8]: the note
    imm32(3, MU.KB_CTX); E(ldr_imm, 1, 3, 0x10); E(ldrb_imm, 1, 1, 0); E(subs_imm8, 0, NOTE0); E(subs_reg, 0, 0, 1)
    E(movs_imm, 2, 1); E(ands_reg, 2, 0); E(lsls_imm, 2, 2, 3); E(lsrs_imm, 1, 0, 1); E(movs_imm, 3, 7); E(ands_reg, 1, 3); E(orrs_reg, 1, 2)
    E(movs_imm, 3, 16); E(ands_reg, 0, 3); E(orrs_reg, 0, 1); E(adds_imm8, 0, 1)    # the step + 1
    imm32(1, RAM); E(adds_reg, 1, 1, 4); E(strb_imm, 0, 1, 3)
    a.label("on_x"); E(pop_list, [0, 1, 2, 3, 4], pc=True)
    a.label("on_q"); E(raw, popw([0, 1, 2, 3, 4], lr=True)); E(b_w, prev["on"])

    # ---- c_jsnof (the transmitter's note-off): a pointing track's goes nowhere
    a.label("c_jsnof")
    E(push_list, [0, 1, 2, 3, 4], lr=True)
    E(subs_imm3, 0, 1, 2); E(cmp_imm, 0, 1); E(b_cond, "of_q", "hi"); E(bl, CAVE); E(cmp_imm, 0, 0); E(b_cond, "on_x", "ne")
    a.label("of_q"); E(raw, popw([0, 1, 2, 3, 4], lr=True)); E(b_w, prev["off"])

    # ---- c_jslst (slot 0 of the note players: player, store): the clock's two stores of a player c_jsadv has served go nowhere
    a.label("c_jslst")
    E(ldr_imm, 2, 0, 0x14); E(cmp_reg, 1, 2); E(b_cond, "ls_c", "eq")
    E(ldr_imm, 2, 0, 0x18); E(cmp_reg, 1, 2); E(b_cond, "ls_p", "ne")
    a.label("ls_c")
    imm32(2, RAM); E(ldr_imm, 3, 2, 12); E(cmp_reg, 0, 3); E(b_cond, "ls_x", "eq"); E(ldr_imm, 3, 2, 16); E(cmp_reg, 0, 3); E(b_cond, "ls_p", "ne")
    a.label("ls_x"); E(raw, RET)
    a.label("ls_p"); E(b_w, PLAYER_TICK)

    # ---- c_jsadv (the tick's call of the tracks' advance: engine): the advance, each pointing track's clock, then the jumps at the first tick of a step
    a.label("c_jsadv")
    E(push_list, [4, 5, 6], lr=True)
    E(bl, ADV)
    imm32(5, RAM); E(ldrb_imm, 1, 5, 0); E(cmp_imm, 1, SIG); E(b_cond, "ad_k", "eq")
    E(movs_imm, 0, 0); E(str_imm, 0, 5, 4); E(str_imm, 0, 5, 8); E(movs_imm, 1, SIG); E(strb_imm, 1, 5, 0)
    a.label("ad_k")
    imm32(4, PLAYER_M); E(movs_imm, 6, 0)
    a.label("ad_l")
    E(mov_reg, 0, 6); E(bl, CAVE); E(lsls_imm, 1, 6, 2); E(adds_reg, 1, 1, 5); E(cmp_imm, 0, 0); E(b_cond, "ad_z", "eq")
    E(str_imm, 4, 1, 12)
    E(bl, L["c_jkram"]); E(movs_imm, 1, 1); E(strb_imm, 1, 0, JK.O_JUMP + 1)
    E(mov_reg, 0, 4); E(ldr_imm, 1, 4, 0x14); E(bl, PLAYER_TICK)
    E(mov_reg, 0, 4); E(ldr_imm, 1, 4, 0x18); E(bl, PLAYER_TICK)
    E(bl, L["c_jkram"]); E(movs_imm, 1, 0); E(strb_imm, 1, 0, JK.O_JUMP + 1)
    E(b, "ad_n")
    a.label("ad_z"); E(str_imm, 0, 1, 12)
    a.label("ad_n")
    E(adds_imm8, 4, 0xFF); E(adds_imm8, 4, PLAYER_SZ - 0xFF); E(adds_imm8, 6, 1); E(cmp_imm, 6, 2); E(b_cond, "ad_l", "lo")
    E(adds_imm8, 5, 4); E(movs_imm, 6, 0)
    a.label("ap_l")
    E(ldrb_reg, 0, 5, 6); E(cmp_imm, 0, 0); E(b_cond, "ap_n", "eq")
    imm32(0, ENG + 0x30); E(lsls_imm, 1, 6, 2); E(adds_reg, 0, 0, 1); E(ldr_imm, 4, 0, 0)
    E(mov_reg, 0, 4); E(movs_imm, 1, 2); E(bl, PK.PARAM_GET); E(ldr_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "ap_n", "ne")
    E(mov_reg, 0, 4); E(movs_imm, 1, 1); E(bl, PARAM_WPTR); E(ldrb_reg, 1, 5, 6); E(subs_imm8, 1, 1); E(strb_imm, 1, 0, 0)
    E(mov_reg, 0, 4); E(bl, COMMIT); E(movs_imm, 0, 0); E(strb_reg, 0, 5, 6)
    a.label("ap_n"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "ap_l", "lo")
    E(pop_list, [4, 5, 6], pc=True)

    # ---- c_jslt (the LED task's calls: ctrl, frame): a pointing track's Note view: Jankó's offsets for it; then the chain, Jankó's rebuild in it
    a.label("c_jslt")
    E(push_list, [0, 1, 4, 5, 6], lr=True); E(movs_imm, 6, 0)
    E(bl, L["c_jktrk"]); E(mov_reg, 5, 0); E(subs_imm3, 0, 0, 2); E(cmp_imm, 0, 1); E(b_cond, "lt_w", "hi")
    E(bl, CAVE); E(cmp_imm, 0, 0); E(b_cond, "lt_w", "eq"); E(movs_imm, 6, 1)
    E(mov_reg, 0, 5); E(bl, L["c_jkoct"]); E(movs_imm, 4, 0); E(cmp_imm, 0, 64); E(b_cond, "lt_o", "ls"); E(movs_imm, 4, 16)
    a.label("lt_o")
    imm32(1, MGR + S_CUR); E(ldrb_imm, 1, 1, 0); E(cmp_imm, 1, 24); E(b_cond, "lt_x", "eq"); E(cmp_imm, 1, 33); E(b_cond, "lt_p", "ne")
    a.label("lt_x"); E(movs_imm, 4, 16)
    a.label("lt_p")
    E(bl, L["c_jkram"]); E(adds_reg, 0, 0, 5); E(strb_imm, 4, 0, 4); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 24)
    a.label("lt_w")
    E(bl, L["c_jkram"]); E(strb_imm, 6, 0, JK.O_JUMP)
    E(pop_list, [0, 1, 4, 5, 6]); E(raw, POP_LR); E(b_w, prev["ledtask"])

    # ---- c_jsnew (the end of a new project): the tail stays from the last project: none of ours
    a.label("c_jsnew")
    E(push_list, [0, 1, 2, 3], lr=True); E(bl, "c_jsad"); E(movs_imm, 2, 0); E(strb_imm, 2, 1, 2); E(pop_list, [0, 1, 2, 3]); E(raw, POP_LR); E(b_w, prev["new"])

    # ---- c_jspad (slot 0 of the template view: view, pad, velocity): pads 9-16 with the engine row open
    a.label("c_jspad")
    E(cmp_imm, 1, ROW); E(b_cond, "jp_f", "lo"); E(cmp_imm, 1, ROW + 7); E(b_cond, "jp_f", "hi")
    E(push_list, [0, 1, 2, 4, 5], lr=True); E(mov_reg, 5, 1)
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); E(b_cond, "jp_o", "hi"); E(mov_reg, 4, 0)  # r4 = 0 MIDI 1, 1 MIDI 2
    imm32(1, MS.RAM); E(ldrb_imm, 1, 1, 0); E(adds_imm8, 0, 1); E(cmp_reg, 0, 1); E(b_cond, "jp_o", "ne")
    E(subs_imm8, 5, ROW); E(adds_imm3, 0, 4, 2); E(cmp_reg, 0, 5); E(b_cond, "jp_x", "eq")   # its own track
    E(adds_imm8, 5, 1); E(mov_reg, 0, 4); E(bl, CAVE); E(cmp_reg, 0, 5); E(b_cond, "jp_w", "ne"); E(movs_imm, 5, 0)
    a.label("jp_w")
    E(bl, "c_jsad"); E(b_cond, "jp_k", "eq"); E(movs_imm, 0, 0); E(strh_imm, 0, 1, 0); E(movs_imm, 0, SIG); E(strb_imm, 0, 1, 2)
    a.label("jp_k"); E(strb_reg, 5, 1, 4)
    a.label("jp_x"); E(pop_list, [0, 1, 2, 4, 5], pc=True)
    a.label("jp_o"); E(raw, popw([0, 1, 2, 4, 5], lr=True))
    a.label("jp_f"); E(b_w, prev["pad"])

    # ---- c_jsled (slot 7 of the template view: view) -> r0 = the LED buffer: the eight tracks while the row is open, pad 27 in the target's colour
    a.label("c_jsled")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); E(b_cond, "ld_x", "hi"); E(mov_reg, 4, 0)
    E(bl, CAVE); E(mov_reg, 6, 0); imm32(7, PAL)                                # r6 = the target + 1
    imm32(1, MS.RAM); E(ldrb_imm, 1, 1, 0); E(adds_imm3, 0, 4, 1); E(cmp_reg, 0, 1); E(b_cond, "ld_c", "ne")
    E(movs_imm, 3, 0)
    a.label("ld_l")
    E(lsls_imm, 1, 3, 1); E(adds_imm8, 1, 2 * ROW); E(adds_imm3, 2, 1, 2)            # r1 = the pad's place, r2 = the dim colour's
    E(adds_imm3, 0, 3, 1); E(cmp_reg, 0, 6); E(b_cond, "ld_d", "ne"); E(subs_imm8, 2, 16)
    a.label("ld_d"); E(ldrh_reg, 2, 7, 2)
    E(adds_imm3, 0, 4, 2); E(cmp_reg, 0, 3); E(b_cond, "ld_o", "ne"); E(movs_imm, 2, 0)   # its own track: no light
    a.label("ld_o"); E(strh_reg, 2, 5, 1); E(adds_imm8, 3, 1); E(cmp_imm, 3, 8); E(b_cond, "ld_l", "lo")
    a.label("ld_c")
    E(cmp_imm, 6, 0); E(b_cond, "ld_x", "eq")
    E(lsls_imm, 2, 6, 1); E(ldrh_reg, 2, 7, 2); E(movs_imm, 1, 2 * PAD); E(strh_reg, 2, 5, 1)
    a.label("ld_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """At the image's end: the tick's call of the advance, slot 0 of the note players, the transmitter's note entries, slots 0 / 7 of the template view,
    the end of a new project."""
    import ct_fw
    from thumb import bl as bl_enc, b_w as bw_enc
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_mpon=lab("mpatch", "c_mpon"), c_jktrk=lab("janko", "c_jktrk"), c_jkoct=lab("janko", "c_jkoct"), c_jkram=lab("janko", "c_jkram"))
    prev = dict(on=u(TX_VT) & ~1, off=u(TX_VT + 4) & ~1, pad=u(MP.TMPL_VT) & ~1, leds=u(MP.TMPL_VT + 28) & ~1, new=MP.bw_target(img, P19.NEW_TAIL, BASE),
                ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    assert JK.JUMP and lab("cave", "c_txf") == CAVE
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000, f"jumpseq: the image is full ({len(img):#x})"
    assert bytes(img[ADV_CALL - BASE:ADV_CALL - BASE + 4]) == bl_enc(ADV_CALL, ADV) and u(PLAYER_VT) == PLAYER_TICK | 1
    img[ADV_CALL - BASE:ADV_CALL - BASE + 4] = bl_enc(ADV_CALL, labels["c_jsadv"])
    img[P19.NEW_TAIL - BASE:P19.NEW_TAIL - BASE + 4] = bw_enc(P19.NEW_TAIL, labels["c_jsnew"])
    # c_jsget(r0 = 0 MIDI 1, 1 MIDI 2) -> r0 = the track it points at + 1, 0 = none; clobbers r1-r3
    c = Asm(CAVE); c.emit(raw, h(0xB500)); c.emit(bl, labels["c_jsad"]); c.emit(it, "ne", "e"); c.emit(movs_imm, 0, 0); c.emit(ldrb_reg, 0, 1, 0); c.emit(raw, h(0xBD00))
    cave, _ = c.assemble()
    assert len(cave) <= 16
    img[CAVE - BASE:CAVE - BASE + len(cave)] = cave
    for at in PK.LED_CALLS:
        assert bytes(img[at - BASE:at - BASE + 4]) == bl_enc(at, prev["ledtask"]), hex(at)
        img[at - BASE:at - BASE + 4] = bl_enc(at, labels["c_jslt"])
    for at, k in ((PLAYER_VT, "c_jslst"), (TX_VT, "c_jsnon"), (TX_VT + 4, "c_jsnof"), (MP.TMPL_VT, "c_jspad"), (MP.TMPL_VT + 28, "c_jsled")):
        struct.pack_into("<I", img, at - BASE, labels[k] | 1)
    return labels, code, prev
