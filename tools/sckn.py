"""SC40.1 (the user, 2026-10-12: «alterar parámetros del sidechain a través de knobs en la vista sidechain» … «sidechain (de la última pista
seleccionada en la vista sidechain) usaría ataque, hold, decay y depth (fuente ya es asignable en stock mediante pads, no necesita knob)»): in the
Sidechain view K1..K4 = attack, hold, decay, depth of the side-chain of the track chosen last there.

The stock side-chain of a note track (Synth 1, Synth 2, MIDI 1, MIDI 2) is five project parameters of type 0x20: 26 + 5 t = the source (0..4),
+ 1 attack, + 2 hold, + 3 decay, + 4 depth (0..127; their CCs on the project channel: 55-59, 65-69, 70-74, 75-79).  The view only offers eight
presets per track (a row of pads writes the four values) and the source (pads 5-8); the knobs did nothing there (their LEDs: dim white).
Now: the track of the last preset pad touched (page x 2 + row; Synth 1 until one is touched) is "the chosen one"; K1..K4 move its four values
through the listener of the MIDI input (0x08034D92: the store, the DSP, MIDI out), so they travel with the project as any change of them; their
LEDs show the values in the colour of the track, K5..K8 go dark.  A preset pad still writes its four values over them.
Hooks: slot 0 of the Sidechain object (0x0805AC2C, in front of SC16's), slot 4 of the track views' container (0x0805A62C; knobs reach it in that
mode, [container + 0x18C] = 7), the LED task calls.  State: 2 bytes of the Master FX block's idle LED buffer (c_gst() + 144): tag, track.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, ldrb_w, lsls_imm, lsrs_imm, mov_reg,  # noqa: E402
                   movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, h, strb_imm, strh_reg, subs_imm8)
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402

SC_VT, CT_VT = 0x0805AC2C, 0x0805A62C
MGR, CTX = 0x20040B10, 0x200069E4
GETTER, PARAM_SET = 0x08036192, 0x08034D92
MODE_OFF, MODE_SC = 0x18C, 7
TYPE, BASE0, PER = 0x20, 26, 5
ST_OFF, MAGIC = FD.ST_OFF + 4, 0x5C
COL = (0x32, 0x17, 0x09, 0x3B)        # the knob LEDs by track: Synth 1 magenta, Synth 2 green, MIDI 1 orange, MIDI 2 purple (steady codes)


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    t_col = base; E(raw, bytes(COL))

    # ---- c_skst() -> r0 = the state (tag written when the bytes were someone else's: Synth 1), 0 without the block; clobbers r1-r3
    a.label("c_skst")
    E(push_list, [4], lr=True)
    E(bl, L["c_gst"]); E(cmp_imm, 0, 0); E(b_cond, "ks_x", "eq")
    E(adds_imm8, 0, ST_OFF)
    E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, MAGIC); E(b_cond, "ks_x", "eq")
    E(movs_imm, 1, MAGIC); E(strb_imm, 1, 0, 0); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 1)
    a.label("ks_x"); E(pop_list, [4], pc=True)

    # ---- c_skon() -> r0 = the container when the Sidechain view is on the screen, else 0; clobbers r1, r2
    a.label("c_skon")
    imm32(0, MGR); E(ldr_imm, 1, 0, 0x6C); E(ldr_imm, 0, 0, 0x2C); E(cmp_reg, 0, 1); E(b_cond, "ko_n", "ne")
    E(ldrb_w, 1, 0, MODE_OFF); E(cmp_imm, 1, MODE_SC); E(b_cond, "ko_n", "ne"); E(raw, h(0x4770))
    a.label("ko_n"); E(movs_imm, 0, 0); E(raw, h(0x4770))

    # ---- c_skpad (the Sidechain object's slot 0: object, pad, velocity): a preset pad of a note track = that track is the chosen one
    a.label("c_skpad")
    E(push_list, [0, 1, 2, 4, 5], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(cmp_imm, 5, 16); E(b_cond, "kp_f", "lo"); E(cmp_imm, 5, 32); E(b_cond, "kp_f", "hs")
    E(ldr_imm, 0, 4, 0x20); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 2); E(b_cond, "kp_f", "hs")     # (pages 0 / 1: the note tracks)
    E(lsls_imm, 0, 0, 1); E(subs_imm8, 5, 16); E(lsrs_imm, 5, 5, 3); E(adds_reg, 5, 5, 0)                    # r5 = the track
    E(bl, "c_skst"); E(cmp_imm, 0, 0); E(b_cond, "kp_f", "eq"); E(strb_imm, 5, 0, 1)
    a.label("kp_f"); E(raw, popw([0, 1, 2, 4, 5], lr=True)); E(b_w, prev["pad"])

    # ---- c_skknob (the container's slot 4: container, knob, delta): the Sidechain view = K1..K4 move the chosen track's attack / hold / decay / depth
    a.label("c_skknob")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(ldrb_w, 0, 0, MODE_OFF); E(cmp_imm, 0, MODE_SC); E(b_cond, "kk_f", "ne")
    E(cmp_imm, 5, 4); E(b_cond, "kk_e", "hs")                                         # K5..K8: nothing
    E(bl, "c_skst"); E(cmp_imm, 0, 0); E(b_cond, "kk_e", "eq")
    E(ldrb_imm, 4, 0, 1); E(cmp_imm, 4, 4); E(b_cond, "kk_e", "hs")
    E(movs_imm, 0, PER); E(muls, 4, 0); E(adds_imm8, 4, BASE0 + 1); E(adds_reg, 4, 4, 5)                     # r4 = the parameter
    E(movs_imm, 0, TYPE); E(mov_reg, 1, 4); E(bl, GETTER); E(movs_imm, 1, 0xFF); E(ands_reg, 0, 1); E(mov_reg, 7, 0)
    E(adds_reg, 0, 0, 6); E(cmp_imm, 0, 0); E(b_cond, "kk_l", "ge"); E(movs_imm, 0, 0)
    a.label("kk_l"); E(cmp_imm, 0, 127); E(b_cond, "kk_h", "le"); E(movs_imm, 0, 127)
    a.label("kk_h"); E(cmp_reg, 0, 7); E(b_cond, "kk_e", "eq")
    E(mov_reg, 3, 0)
    imm32(0, CTX); E(ldr_imm, 0, 0, 0); E(ldr_imm, 0, 0, 0x10); E(ldr_imm, 0, 0, 0)
    E(adds_imm8, 0, 4); E(movs_imm, 1, TYPE); E(mov_reg, 2, 4); E(bl, PARAM_SET)
    a.label("kk_e"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("kk_f"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["knob"])

    # ---- c_skledtask (the LED task calls: ctrl, frame): the chain; the Sidechain view: K1..K4 = the four values in the track's colour, K5..K8 dark
    a.label("c_skledtask")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    E(bl, "c_skon"); E(cmp_imm, 0, 0); E(b_cond, "kl_x", "eq")
    E(bl, "c_skst"); E(cmp_imm, 0, 0); E(b_cond, "kl_x", "eq")
    E(ldrb_imm, 4, 0, 1); E(cmp_imm, 4, 4); E(b_cond, "kl_x", "hs")
    imm32(0, t_col); E(adds_reg, 0, 0, 4); E(ldrb_imm, 7, 0, 0)                       # r7 = the colour
    E(movs_imm, 0, PER); E(muls, 4, 0); E(adds_imm8, 4, BASE0 + 1)                    # r4 = the first of the four parameters
    E(movs_imm, 6, 0)
    a.label("kl_l")
    E(movs_imm, 2, 0); E(cmp_imm, 6, 4); E(b_cond, "kl_w", "hs")
    E(movs_imm, 0, TYPE); E(mov_reg, 1, 4); E(adds_reg, 1, 1, 6); E(bl, GETTER); E(movs_imm, 1, 0x7F); E(ands_reg, 0, 1)
    E(adds_imm8, 0, 2); E(lsls_imm, 2, 0, 8); E(orrs_reg, 2, 7)
    a.label("kl_w"); E(mov_reg, 0, 6); E(adds_imm8, 0, 60); E(lsls_imm, 0, 0, 1); E(strh_reg, 2, 5, 0)
    E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "kl_l", "lo")
    a.label("kl_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; slot 0 of the Sidechain object, slot 4 of the container, the two LED task calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a: struct.unpack_from("<I", img, a - BASE)[0]
    lab = lambda sec, n: int(report[sec]["labels"][n], 16)
    L = dict(c_gst=lab("sc14", "c_gst"))
    head = "fxdiag" if "fxdiag" in report else "sesscopy"
    prev = dict(pad=u(SC_VT) & ~1, knob=u(CT_VT + 16) & ~1, ledtask=lab(head, "c_fdledtask" if head == "fxdiag" else "c_scledtask"))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, SC_VT - BASE, labels["c_skpad"] | 1)
    struct.pack_into("<I", img, CT_VT + 16 - BASE, labels["c_skknob"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_skledtask"])
    return labels, code, prev
