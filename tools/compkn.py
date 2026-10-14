"""SC40.2 (the user, 2026-10-12: «alterar parámetros del compresor master que se activa en Advanced Setup … para editar los parámetros en vivo
tendría que estar en la vista Setup normal (knobs no se usan en esta vista)» … «intenta identificarlos y si no hacemos pruebas»): in the Setup
view K1 / K2 = the attack and the release of the master compressor.

What the stock has (read in the firmware and in the DSP program, 2026-10-13): the "master" group of the session, type 0x21: 0 the master filter,
1 its resonance, 2 the compressor on / off, 3 and 4 two values 0..127, 5 a value nothing sends to the DSP, 6 a second switch, 7 the output gain.
The ARM (0x08028F62) writes 2 -> Y:$10D, 3 -> Y:$10E, 4 -> Y:$10F, 6 -> Y:$110, 7 -> X:$DE.  In the DSP (P:$21C4): Y:$10D / Y:$110 are bits 0 / 1
of X:$1EE5 (bit 0 clear = the compressor is skipped; bit 1 = which of two versions of its loop runs); Y:$10E -> X:$1EE0 and Y:$10F -> X:$1EE1 +
X:$1EDE through the same curve (P:$225E), and the loop uses X:$1EE0 to smooth the gain when it falls, X:$1EE1 when it rises, X:$1EDE as the decay
of its level detector: 3 = the attack time, 4 = the release time.  The threshold and the ratio are constants of the DSP: no parameter.
The descriptor gives 2..6 the CCs 22..26 of the project channel.  The stock keeps both at 0 and has no control for them.
The master group is not one of the four stores a project saves: what the knobs set lasts until the unit is switched off or the stock writes the
group again (to be seen on the device: loading a project).
Hooks: slot 4 of the Setup view (vtable 0x0805A98C: the stock has a do-nothing stub there; not in its Advanced page, [view + 0x24] set), the LED task calls (K1 / K2 white with their value,
only in the Setup view).  The values go through the listener of the MIDI input (0x08034D92, type 0x21).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_w, lsls_imm, mov_reg, movs_imm, movt, movw,  # noqa: E402
                   orrs_reg, pop_list, push_list, raw, h, strh_reg)
import packio as PK  # noqa: E402

SETUP_VT, SETUP_OBJ, ADV_OFF = 0x0805A98C, 0x20044958, 0x24      # (the vtable starts 8 bytes into the table at 0x0805A984; slot 4 = knobs, a stub in the stock)
MGR, CTX = 0x20040B10, 0x200069E4
GETTER, PARAM_SET = 0x08036192, 0x08034D92
TYPE, IDX = 0x21, (3, 4)              # K1 the attack, K2 the release
COL = 0x01


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_ckknob (the Setup view's slot 4: view, knob, delta): K1 / K2 = the attack / the release of the master compressor (not in the Advanced page)
    a.label("c_ckknob")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(ldrb_w, 0, 0, ADV_OFF); E(cmp_imm, 0, 0); E(b_cond, "ck_f", "ne")
    E(cmp_imm, 5, len(IDX)); E(b_cond, "ck_f", "hs")
    E(mov_reg, 4, 5); E(adds_imm8, 4, IDX[0])
    E(movs_imm, 0, TYPE); E(mov_reg, 1, 4); E(bl, GETTER); E(movs_imm, 1, 0xFF); E(ands_reg, 0, 1); E(mov_reg, 7, 0)
    E(adds_reg, 0, 0, 6); E(cmp_imm, 0, 0); E(b_cond, "ck_l", "ge"); E(movs_imm, 0, 0)
    a.label("ck_l"); E(cmp_imm, 0, 127); E(b_cond, "ck_h", "le"); E(movs_imm, 0, 127)
    a.label("ck_h"); E(cmp_reg, 0, 7); E(b_cond, "ck_e", "eq")
    E(mov_reg, 3, 0)
    imm32(0, CTX); E(ldr_imm, 0, 0, 0); E(ldr_imm, 0, 0, 0x10); E(ldr_imm, 0, 0, 0)
    E(adds_imm8, 0, 4); E(movs_imm, 1, TYPE); E(mov_reg, 2, 4); E(bl, PARAM_SET)
    a.label("ck_e"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("ck_f"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["knob"])

    # ---- c_ckledtask (the LED task calls: ctrl, frame): the chain; the Setup view (not Advanced): K1 / K2 white with their value
    a.label("c_ckledtask")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    imm32(0, MGR); E(ldr_imm, 0, 0, 0x6C); imm32(1, SETUP_OBJ); E(cmp_reg, 0, 1); E(b_cond, "cl_x", "ne")
    E(ldrb_w, 0, 0, ADV_OFF); E(cmp_imm, 0, 0); E(b_cond, "cl_x", "ne")
    for k, idx in enumerate(IDX):
        E(movs_imm, 0, TYPE); E(movs_imm, 1, idx); E(bl, GETTER); E(movs_imm, 1, 0x7F); E(ands_reg, 0, 1)
        E(adds_imm8, 0, 2); E(lsls_imm, 0, 0, 8); E(movs_imm, 1, COL); E(orrs_reg, 0, 1); E(movs_imm, 1, 2 * (60 + k)); E(strh_reg, 0, 5, 1)
    a.label("cl_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; slot 4 of the Setup view and the two LED task calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a: struct.unpack_from("<I", img, a - BASE)[0]
    prev = dict(knob=u(SETUP_VT + 16) & ~1, ledtask=int(report["sckn"]["labels"]["c_skledtask"], 16))
    code, labels = arm_code(base_addr, {}, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, SETUP_VT + 16 - BASE, labels["c_ckknob"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_ckledtask"])
    return labels, code, prev
