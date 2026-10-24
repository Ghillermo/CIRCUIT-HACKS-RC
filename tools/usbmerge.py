"""SC46.4 / Beta 3.21 (issue #10 of the public repository, ledlaux, 2026-10-24: «Is there a way that midi merge works when device is connected to
usb? … i connect midi keyboard to CT using midi cable, i want then that device is outputting both midi combined to a computer»; the user: «si es
correcto y seguro, súbelo junto a la versión»): the DIN In merged into the USB MIDI out.

The stock never sends what comes in on the DIN In to the USB port (only to the Thru jack, by the hardware switch; midithru's Merge / Filter copy it
there by software).  The MIDI out router's ports (midithru): 0 USB, 1 MIDI Out, 2 the Thru jack; the DIN In = input port 1, every short message
posted at 0x08021024 (now the bl to midithru's c_thin).
  * c_usbin, in place of that bl (queue, port, bytes): with the USB merge on, a message of the DIN In is also queued on port 0 (the port's send
    0x0803599A, as c_thin does for port 2), then c_thin as before; with the unit's Clock Tx on (bit 3 of [0x20011334 + 0x18]) the DIN In's clock and
    transport (0xF8, 0xFA, 0xFB, 0xFC) are not copied (the computer would get two clocks); SysEx is not copied (another path, as Merge);
  * the toggle: Advanced Setup, pad 23 (the stock ignores the pads there; advleds keeps 22 / 23 dark): a tap = on / off; its LED green on, dim off;
  * saved with the unit's settings: bit 1 of gmdrum's flags byte (parameter 4 byte 2; its signature written first by gmdrum's c_gmput), the save
    asked of lazysave.
In the hole (no card, no settings save of its own).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b_cond, b_w, bl, cmp_imm, h, ldr_imm, ldrb_imm, ldrb_w, lsls_imm, mov_reg, movs_imm, movt, movw, pop_list, push_list,  # noqa: E402
                   raw, strh_imm)
import midithru as MT  # noqa: E402
import gmdrum as G  # noqa: E402
import pgmch as PG  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402

TX = 0x20011334
CLOCK_TX = 0x08                                          # [TX + 0x18] bit 3
F_USB = 0x02                                             # bit 1 of gmdrum's flags byte
PAD_USB = 22                                             # pad 23
USB_PORT = 0
COL_ON, COL_OFF = 0x17, 0x02


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_usbq() -> r0 = 1 with the USB merge on; clobbers r1-r3
    a.label("c_usbq")
    E(raw, h(0xB500))
    E(bl, L["c_gmsig"]); E(cmp_imm, 0, 0); E(b_cond, "uq_0", "eq")
    E(movs_imm, 0, G.P0); E(movs_imm, 1, 0); E(bl, L["c_gmp"]); E(ldrb_imm, 0, 0, G.B_FLAGS); E(movs_imm, 1, F_USB); E(raw, h(0x4208))   # tst r0, r1
    E(b_cond, "uq_0", "eq"); E(movs_imm, 0, 1); E(raw, h(0xBD00))
    a.label("uq_0"); E(movs_imm, 0, 0); E(raw, h(0xBD00))

    # ---- c_usbin (queue, port, bytes): the post of a short input message; the DIN In's also to the USB port, then midithru's c_thin
    a.label("c_usbin")
    E(push_list, [0, 1, 2, 4], lr=True)
    E(cmp_imm, 1, MT.DIN_IN); E(b_cond, "ui_go", "ne"); E(mov_reg, 4, 2)
    E(bl, "c_usbq"); E(cmp_imm, 0, 0); E(b_cond, "ui_go", "eq")
    E(ldrb_imm, 0, 4, 0); E(cmp_imm, 0, 0xF8); E(b_cond, "ui_s", "lo"); E(cmp_imm, 0, 0xFC); E(b_cond, "ui_s", "hi"); E(cmp_imm, 0, 0xF9); E(b_cond, "ui_s", "eq")
    imm32(1, TX); E(ldrb_imm, 1, 1, 0x18); E(movs_imm, 0, CLOCK_TX); E(raw, h(0x4201)); E(b_cond, "ui_go", "ne")   # tst r1, r0: the unit sends its own clock
    a.label("ui_s")
    imm32(0, MT.ROUTER_PTR); E(ldr_imm, 0, 0, 0); E(ldr_imm, 0, 0, 0x14); E(ldr_imm, 0, 0, 4 * USB_PORT); E(mov_reg, 1, 4); E(bl, MT.PORT_SEND)
    a.label("ui_go"); E(raw, popw([0, 1, 2, 4], lr=True)); E(b_w, prev["post"])

    # ---- c_usbpad (the Setup view's slot 0: view, pad, velocity): Advanced Setup, pad 23 = the USB merge on / off
    a.label("c_usbpad")
    E(push_list, [0, 1, 2, 4], lr=True)
    E(cmp_imm, 1, PAD_USB); E(b_cond, "up_f", "ne")
    E(ldrb_w, 0, 0, PG.ADV_OFF); E(cmp_imm, 0, 0); E(b_cond, "up_f", "eq")
    E(bl, "c_usbq"); E(mov_reg, 4, 0)
    E(bl, L["c_gmsig"]); E(movs_imm, 1, 0); E(cmp_imm, 0, 0); E(b_cond, "up_w", "eq")       # no signature yet: the flags are 0
    E(movs_imm, 0, G.P0); E(movs_imm, 1, 0); E(bl, L["c_gmp"]); E(ldrb_imm, 1, 0, G.B_FLAGS)
    a.label("up_w"); E(movs_imm, 0, F_USB); E(raw, h(0x4041))                          # eors r1, r0
    E(movs_imm, 0, G.B_FLAGS); E(bl, L["c_gmput"]); E(bl, L["c_gmsave"])
    E(pop_list, [0, 1, 2, 4], pc=True)
    a.label("up_f"); E(raw, popw([0, 1, 2, 4], lr=True)); E(b_w, prev["pad"])

    # ---- c_usbled (the LED task calls: ctrl, frame): the chain; Advanced Setup on the screen: pad 23 green on / dim off
    a.label("c_usbled")
    E(push_list, [3, 4, 5], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    imm32(0, PG.MGR); E(ldr_imm, 0, 0, PG.MODE_STORE); E(movs_imm, 1, 0); E(bl, PG.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(cmp_imm, 0, PG.MODE_SETUP); E(b_cond, "ul_x", "ne")
    imm32(0, PG.SETUP_OBJ); E(ldrb_w, 0, 0, PG.ADV_OFF); E(cmp_imm, 0, 0); E(b_cond, "ul_x", "eq")
    E(movs_imm, 4, COL_ON); E(bl, "c_usbq"); E(cmp_imm, 0, 0); E(b_cond, "ul_w", "ne"); E(movs_imm, 4, COL_OFF)
    a.label("ul_w"); E(strh_imm, 4, 5, 2 * PAD_USB)
    a.label("ul_x"); E(pop_list, [3, 4, 5], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the post's bl at 0x08021024, the Setup view's slot 0, the LED task calls."""
    import ct_fw
    from thumb import bl as bl_enc
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("gmdrum", k) for k in ("c_gmsig", "c_gmp", "c_gmput", "c_gmsave")}
    prev = dict(post=lab("midithru", "c_thin"), pad=u(PG.SETUP_VT) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    assert bytes(img[MT.POST_CALL - BASE:MT.POST_CALL - BASE + 4]) == bl_enc(MT.POST_CALL, prev["post"])
    assert G.V2 and G.V3, "gmdrum.use_v2 / use_v3 first (its flags byte: K4 keeps bit 1)"
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    img[MT.POST_CALL - BASE:MT.POST_CALL - BASE + 4] = bl_enc(MT.POST_CALL, labels["c_usbin"])
    struct.pack_into("<I", img, PG.SETUP_VT - BASE, labels["c_usbpad"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_usbled"])
    return labels, code, prev
