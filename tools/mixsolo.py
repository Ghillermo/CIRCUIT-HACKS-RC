"""SC50.5 / Beta 5.8 (the user, 2026-11-02: «pad 16 de mixer función sólo. Mantener este pad y cualquier combinación de pads mutea el resto», «Se queda así»): solo in the Mixer view.

The stock's pads 10-16 of the Mixer do nothing.  Pad 16 held ([MGR + 0x84], a bit per held pad) + pads 1-8: those tracks sound, every other track muted, through the stock's own
toggle (0x08046626, so the pads show it as always); the choice starts anew with each press of pad 16 and adds up while it is held; letting it go leaves the mutes as they are.
Not on the Master FX page of the view.  The pad: dim white, bright while held; with Shift the row is the scene's repeats.  RAM: modmx.MXR + 0x2210, the tracks chosen (read only
after pad 16 cleared it).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, add_sp_imm, adds_imm8, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, lsls_imm, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list,  # noqa: E402
                   push_list, raw, strb_imm, strh_imm)
from thumb import bl as bl_enc  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import modmx as MX  # noqa: E402
import qmute as Q  # noqa: E402

RAM = MX.MXR + 0x2210
PAD_SOLO = 15
HELD = 0x84                                                  # [MGR + 0x84]: the pads held, bit = pad
COL_DIM, COL_ON = 0x02, 0x01


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    # ---- c_sopad (the Mixer view's slot 0: view, pad, velocity)
    a.label("c_sopad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, L["c_gact"]); E(cmp_imm, 0, 0); E(b_cond, "so_f", "ne")                        # Master FX: its pads
    imm32(6, RAM)
    E(cmp_imm, 5, PAD_SOLO); E(b_cond, "so_t", "ne")
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, 0); E(b, "so_f")                                # pad 16: the choice anew
    a.label("so_t")
    E(cmp_imm, 5, 8); E(b_cond, "so_f", "hs")
    imm32(0, Q.MGR); E(raw, h(0xF8D0) + h(0 << 12 | HELD)); E(lsls_imm, 0, 0, 16); E(b_cond, "so_f", "pl")   # ldr.w r0, [r0, #0x84]: bit 15
    E(ldrb_imm, 7, 6, 0); E(movs_imm, 0, 1); E(raw, h(0x40A8)); E(orrs_reg, 7, 0); E(strb_imm, 7, 6, 0)      # lsls r0, r5
    E(movs_imm, 5, 0)
    a.label("so_l")                                                                      # r5 = a track, r7 = the chosen ones
    E(ldr_imm, 0, 4, 0x60); E(muls, 0, 5); E(ldr_imm, 1, 4, 0x68); E(raw, h(0x5808)); E(movs_imm, 1, 0); E(bl, Q.PARAM_GET); E(ldrb_imm, 0, 0, 0)   # ldr r0, [r1, r0]
    E(mov_reg, 1, 7); E(raw, h(0x40E9)); E(movs_imm, 2, 1); E(raw, h(0x4011))            # lsrs r1, r5; ands r1, r2: 1 = chosen
    E(cmp_reg, 0, 1); E(b_cond, "so_n", "ne")                                            # (muted 1, chosen 1) or (0, 0): the stock's toggle
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, Q.MIX_PAD)
    a.label("so_n"); E(adds_imm8, 5, 1); E(cmp_imm, 5, 8); E(b_cond, "so_l", "lo")
    E(add_sp_imm, 12); E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("so_f"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["pad"])

    # ---- c_soled (the LED task calls: ctrl, frame): pad 16 of the Mixer
    a.label("c_soled")
    E(push_list, [3, 4], lr=True); E(mov_reg, 4, 1); E(bl, prev["ledtask"])
    imm32(0, Q.MGR); E(ldr_imm, 0, 0, 0x6C); imm32(1, Q.MIX_VIEW); E(cmp_reg, 0, 1); E(b_cond, "sl_x", "ne")
    E(bl, L["c_gact"]); E(cmp_imm, 0, 0); E(b_cond, "sl_x", "ne")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "sl_x", "ne")
    E(movs_imm, 1, COL_DIM); imm32(0, Q.MGR); E(raw, h(0xF8D0) + h(0 << 12 | HELD)); E(lsls_imm, 0, 0, 16); E(b_cond, "sl_w", "pl"); E(movs_imm, 1, COL_ON)
    a.label("sl_w"); E(strh_imm, 1, 4, 2 * PAD_SOLO)
    a.label("sl_x"); E(pop_list, [3, 4], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    L = dict(c_shift=int(report["sc15"]["labels"]["c_shift"], 16), c_gact=int(report["sc17"]["labels"]["c_gact"], 16))
    prev = dict(pad=u(Q.MIX_VT) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, Q.MIX_VT - BASE, labels["c_sopad"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_soled"])
    return labels, code, prev
