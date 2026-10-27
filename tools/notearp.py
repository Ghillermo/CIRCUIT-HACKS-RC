"""SC48 / Beta 3.37 (the user, 2026-10-26: «optional midi input into arpeggiator (Note toggle in setup view)»; 2026-10-27: «note se ve en Advanced
setup, pero queremos note (midi al arpeggiator) en setup normal»): the external keyboard through the arpeggiator (arpx: bit 2 of gmdrum's flags
byte, saved with the unit's settings) moves from Advanced Setup's pad 22 to the Note button of the normal Setup view.

  * the Setup view's slot 2 (every button press while Setup is on the screen: view, button): the normal page (+ 0x24 = 0), Note (id 9), no Shift
    = the flag flipped (arpx's way: gmdrum's c_gmput, the signature written first, and the save asked of lazysave), the press swallowed;
  * the Setup view's slot 0 (view, pad, velocity): Advanced Setup's pad 22 swallowed (arpx's toggle there is gone);
  * the LED task (the chain first): the normal Setup page = Note's LED (41) bright green 0x74 on / dim red 0x55 off (the stock's own toggle
    colours: Easy Start, MIDI Thru, the compressor in Advanced Setup); Advanced Setup = pad 22 dark again.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, h, ldr_imm, ldrb_imm, ldrb_w, mov_reg, movs_imm, movt, movw, pop_list, push_list, raw,  # noqa: E402
                   strh_imm, tst_reg)
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import pgmch as PG  # noqa: E402
import gmdrum as G  # noqa: E402
import arpx as AX  # noqa: E402

NOTE_BTN, LED_NOTE = 9, 41
COL_ON, COL_OFF = 0x74, 0x55
PARAM_GET = 0x0803542C


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_naon() -> r0 = the flag (0 / F_ARX); clobbers r1-r3
    a.label("c_naon")
    E(raw, h(0xB500)); E(bl, L["c_gmsig"]); E(cmp_imm, 0, 0); E(b_cond, "no_x", "eq")
    E(movs_imm, 0, G.P0); E(movs_imm, 1, 0); E(bl, L["c_gmp"]); E(ldrb_imm, 0, 0, G.B_FLAGS); E(movs_imm, 1, AX.F_ARX); E(raw, h(0x4008))   # ands r0, r1
    a.label("no_x"); E(raw, h(0xBD00))

    # ---- c_nabtn (the Setup view's slot 2: view, button): the normal page's Note = the flag flipped
    a.label("c_nabtn")
    E(push_list, [0, 1, 2, 4], lr=True)
    E(cmp_imm, 1, NOTE_BTN); E(b_cond, "nb_f", "ne")
    E(ldrb_w, 0, 0, PG.ADV_OFF); E(cmp_imm, 0, 0); E(b_cond, "nb_f", "ne")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "nb_f", "ne")
    E(bl, L["c_gmsig"]); E(movs_imm, 1, 0); E(cmp_imm, 0, 0); E(b_cond, "nb_w", "eq")        # no signature yet: the flags are 0
    E(movs_imm, 0, G.P0); E(movs_imm, 1, 0); E(bl, L["c_gmp"]); E(ldrb_imm, 1, 0, G.B_FLAGS)
    a.label("nb_w"); E(movs_imm, 0, AX.F_ARX); E(raw, h(0x4041))                             # eors r1, r0
    E(movs_imm, 0, G.B_FLAGS); E(bl, L["c_gmput"]); E(bl, L["c_gmsave"])
    E(pop_list, [0, 1, 2, 4], pc=True)
    a.label("nb_f"); E(raw, popw([0, 1, 2, 4], lr=True)); E(b_w, prev["btn"])

    # ---- c_napad (the Setup view's slot 0: view, pad, velocity): Advanced Setup's pad 22 swallowed
    a.label("c_napad")
    E(cmp_imm, 1, AX.PAD_ARX); E(b_cond, "np_f", "ne")
    E(push_list, [0], lr=False); E(ldrb_w, 0, 0, PG.ADV_OFF); E(cmp_imm, 0, 0); E(pop_list, [0]); E(b_cond, "np_f", "eq")
    E(raw, h(0x4770))
    a.label("np_f"); E(b_w, prev["pad"])

    # ---- c_naled (the LED task calls: ctrl, frame): the chain; the normal Setup page: Note's LED; Advanced Setup: pad 22 dark
    a.label("c_naled")
    E(push_list, [3, 4, 5], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    imm32(0, PG.MGR); E(ldr_imm, 0, 0, PG.MODE_STORE); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(cmp_imm, 0, PG.MODE_SETUP); E(b_cond, "nl_x", "ne")
    imm32(0, PG.SETUP_OBJ); E(ldrb_w, 0, 0, PG.ADV_OFF); E(cmp_imm, 0, 0); E(b_cond, "nl_n", "eq")
    E(movs_imm, 0, 0); E(strh_imm, 0, 5, 2 * AX.PAD_ARX); E(b, "nl_x")
    a.label("nl_n")
    E(bl, "c_naon"); E(movs_imm, 4, COL_ON); E(cmp_imm, 0, 0); E(b_cond, "nl_w", "ne"); E(movs_imm, 4, COL_OFF)
    a.label("nl_w"); E(movs_imm, 0, 2 * LED_NOTE); E(raw, h(0x522C))                          # strh r4, [r5, r0]
    a.label("nl_x"); E(pop_list, [3, 4, 5], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the Setup view's slots 0 / 2, the LED task calls."""
    import ct_fw
    from thumb import bl as bl_enc
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("gmdrum", k) for k in ("c_gmsig", "c_gmp", "c_gmput", "c_gmsave")}
    L["c_shift"] = lab("sc15", "c_shift")
    prev = dict(btn=u(PG.SETUP_VT + 8) & ~1, pad=u(PG.SETUP_VT) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    struct.pack_into("<I", img, PG.SETUP_VT + 8 - BASE, labels["c_nabtn"] | 1)
    struct.pack_into("<I", img, PG.SETUP_VT - BASE, labels["c_napad"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_naled"])
    return labels, code, prev
