"""SC38.3 (the user, 2026-10-11: «comportamiento de MIDI thru: ahora mismo, midi thru sólo se puede configurar como segundo MIDI out o Thru.  Queremos añadir en
su toggle otros dos modos: Midi Merge: se clona todo lo de MIDI in a MIDI thru y también el MIDI generado por el aparato.  Midi Filter: se clona todo lo de
MIDI in menos los canales en los que Circuit está escuchando»).

The stock (found in the code and in emulation, docs/NOTAS.md «SC38.3»):
  * the toggle is Duplicate (button 24) in the Advanced Setup view (the Setup view 0x20044958 with byte +0x24 set; handler 0x08047016, 0x0804709A):
    settings parameter 2 bit 16: 1 = Thru (default: a hardware switch, GPIOB pin 4 set, copies the DIN In to the Thru jack), 0 = Out 2 (USART2 TX on
    the Thru jack); the listener 0x0802D28C writes the bit to the pin (0x0803C9D8 -> 0x0801B130); LED 56 = palette 0x34E (0x55 dim red) / 0x34C (0x74 green);
  * MIDI out: the router [0x200069F4] (0x08020C42) sends a message (a pointer to the MIDI bytes) to the ports of a mask: 0 USB, 1 USART1 TX (MIDI Out),
    2 USART2 TX (Thru jack in Out 2); every port is of the class 0x0805B60C, slot 2 = send 0x0803599A (queues the message);
  * MIDI in: the DIN In is USART1 RX, port 1; the poll 0x08020FB2 -> 0x08020FF2 parses the bytes and posts every short message (realtime included) with
    0x0801C894(queue, port, bytes) at 0x08021024;
  * the channels the unit listens on: the receive dispatcher D = [[[[0x200069E4]] + 0x18] + 8]: D + 4..8 = Synth 1, Synth 2, MIDI 1, MIDI 2, Drums,
    D + 9..13 = the CC / PC table (channel 16 for the project), D + 0x14 bit 4 = channel 16 blocked (SC03 / SC04).
Two more modes, software thru on the Out 2 wiring (bit 16 clear, so the stock listener keeps the pin on USART2):
  * Merge (bit 30): every DIN In message is also queued on port 2 (c_thin, in place of the post at 0x08021024), the unit's MIDI goes there as in Out 2;
  * Filter (bit 31): the DIN In messages, except channel messages on a listened channel, go to port 2; the unit's own messages to port 2 are dropped
    (c_thtx in slot 2 of the port class; c_thin calls the send directly).
SysEx from the DIN In is not copied (it goes through another path and the port's long-message send waits for its queue).
Duplicate in the Advanced Setup view cycles Thru -> Out 2 -> Merge -> Filter -> Thru (c_thbtn); its LED: dim red / green / yellow / blue (c_thled).
Bits 30 / 31 are saved: the save mask of SC07 / SC10 (c_m1 / c_m2) grows to 0xFF07FFFF.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, ldrh_imm, lsls_imm, mov_reg, movs_imm, movt, movw, pop_list, push_list,  # noqa: E402
                   raw, h, ands_reg, orrs_reg, bics_reg, adds_reg, adds_imm8, str_imm, ldrb_reg)

PARAM_GET, PARAM_WPTR = 0x0803542C, 0x080354FA
CTX_PTR = 0x200069E4                  # [[CTX_PTR]] = L: +0x18 the receive object, +0x54 the settings store
ROUTER_PTR = 0x200069F4               # [ROUTER_PTR] = the MIDI out router: +0x14 the ports, +0x18 their number
PORT_VT = 0x0805B60C                  # the class of the MIDI out ports: slot 2 = send
PORT_SEND = 0x0803599A
POST = 0x0801C894                     # post(queue, port, bytes) of an input message
POST_CALL = 0x08021024                # the bl of the short-message post in 0x08020FF2
BTN_TOGGLE = 0x080470A0               # Duplicate in the Advanced Setup view: after its first commit, the toggle of bit 16 (to 0x080470C8)
BTN_COMMIT = 0x080470EA               # the commit of the settings and the handler's return
LED_CODE = 0x080472F4                 # the LED of Duplicate: ubfx .. ldrh (20 bytes) -> r0 = colour, r1 = [view + 4]
LED_BACK = 0x08047308
PAL = 0x08056464
B16, B30, B31 = 1 << 16, 1 << 30, 1 << 31
DIN_IN = 1                            # the input port of the DIN In
PORT2 = 2                             # the out port of the Thru jack (Out 2)
COL_MERGE, COL_FILTER = 0x2D, 0x09    # yellow, blue (the RGB table: 255 / 255 / 25 and 26 / 71 / 255)
SAVE_MASK = 0xFF07FFFF


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def ldr_w(rt, rn, imm12): return h(0xF8D0 | rn) + h(rt << 12 | imm12)


def arm_code(base):
    a = Asm(base)
    E = a.emit

    def settings(rd):                                                             # rd = the settings store; clobbers rd only
        E(movw, rd, CTX_PTR & 0xFFFF); E(movt, rd, CTX_PTR >> 16); E(ldr_imm, rd, rd, 0); E(ldr_imm, rd, rd, 0); E(ldr_imm, rd, rd, 0x54)

    def port2(rd):                                                                # rd = the out port 2
        E(movw, rd, ROUTER_PTR & 0xFFFF); E(movt, rd, ROUTER_PTR >> 16); E(ldr_imm, rd, rd, 0); E(ldr_imm, rd, rd, 0x14); E(ldr_imm, rd, rd, 4 * PORT2)

    # ---- c_tmode -> r0 = 2 Merge, 3 Filter, 0 otherwise (Thru by the hardware switch, Out 2); clobbers r1-r3
    a.label("c_tmode")
    E(push_list, [], lr=True)
    settings(0); E(movs_imm, 1, 2); E(bl, PARAM_GET); E(ldr_imm, 0, 0, 0)
    E(lsls_imm, 1, 0, 15); E(b_cond, "tm_0", "mi")                               # bit 16: the hardware thru
    E(cmp_imm, 0, 0); E(b_cond, "tm_f", "lt")                                     # bit 31
    E(lsls_imm, 1, 0, 1); E(b_cond, "tm_0", "pl")                                 # bit 30
    E(movs_imm, 0, 2); E(pop_list, [], pc=True)
    a.label("tm_f"); E(movs_imm, 0, 3); E(pop_list, [], pc=True)
    a.label("tm_0"); E(movs_imm, 0, 0); E(pop_list, [], pc=True)

    # ---- c_thin (queue, port, bytes) in place of the post of a short input message: Merge / Filter copy the DIN In message to port 2, then the post
    a.label("c_thin")
    E(push_list, [0, 1, 2, 4, 5], lr=True)
    E(cmp_imm, 1, DIN_IN); E(b_cond, "ti_go", "ne")
    E(mov_reg, 4, 2)
    E(bl, "c_tmode"); E(cmp_imm, 0, 2); E(b_cond, "ti_go", "lo")
    E(cmp_imm, 0, 3); E(b_cond, "ti_fw", "ne")
    E(ldrb_imm, 0, 4, 0); E(cmp_imm, 0, 0x80); E(b_cond, "ti_fw", "lo"); E(cmp_imm, 0, 0xF0); E(b_cond, "ti_fw", "hs")   # not a channel message: copied
    E(movs_imm, 1, 0x0F); E(ands_reg, 0, 1)                                       # r0 = its channel
    E(movw, 5, CTX_PTR & 0xFFFF); E(movt, 5, CTX_PTR >> 16); E(ldr_imm, 5, 5, 0); E(ldr_imm, 5, 5, 0); E(ldr_imm, 5, 5, 0x18); E(ldr_imm, 5, 5, 8)   # r5 = D
    E(cmp_imm, 0, 15); E(b_cond, "ti_l", "ne")
    E(ldrb_imm, 1, 5, 0x14); E(lsls_imm, 1, 1, 27); E(b_cond, "ti_fw", "mi")      # channel 16 blocked: not listened
    a.label("ti_l")
    E(movs_imm, 2, 4)
    a.label("ti_lp")
    E(ldrb_reg, 1, 5, 2); E(cmp_reg, 1, 0); E(b_cond, "ti_go", "eq")              # a listened channel: not copied
    E(adds_imm8, 2, 1); E(cmp_imm, 2, 14); E(b_cond, "ti_lp", "lo")
    a.label("ti_fw")
    port2(0); E(mov_reg, 1, 4); E(bl, PORT_SEND)
    a.label("ti_go")
    E(raw, popw([0, 1, 2, 4, 5], lr=True)); E(b_w, POST)

    # ---- c_thtx (port, message): slot 2 of the out ports; Filter drops the unit's own messages to port 2
    a.label("c_thtx")
    E(push_list, [0, 1, 4], lr=True)
    port2(4); E(cmp_reg, 0, 4); E(b_cond, "tx_go", "ne")
    E(bl, "c_tmode"); E(cmp_imm, 0, 3); E(b_cond, "tx_go", "ne")
    E(raw, popw([0, 1, 4], lr=True)); E(movs_imm, 0, 1); E(raw, h(0x4770))
    a.label("tx_go")
    E(raw, popw([0, 1, 4], lr=True)); E(b_w, PORT_SEND)

    # ---- c_thbtn (r0 = the Setup view): Duplicate in the Advanced Setup view, Thru -> Out 2 -> Merge -> Filter -> Thru (the caller commits)
    a.label("c_thbtn")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 4, 0)
    E(ldr_imm, 0, 4, 0xC); E(movs_imm, 1, 2); E(bl, PARAM_GET); E(ldr_imm, 6, 0, 0)
    E(ldr_imm, 0, 4, 0xC); E(movs_imm, 1, 2); E(bl, PARAM_WPTR); E(mov_reg, 5, 0)
    E(ldr_imm, 1, 5, 0); E(movw, 2, B16 & 0xFFFF); E(movt, 2, (B16 | B30 | B31) >> 16); E(bics_reg, 1, 2)
    E(lsls_imm, 0, 6, 15); E(b_cond, "tb_w", "mi")                                # Thru -> Out 2 (no bit)
    E(movw, 2, 0); E(movt, 2, B16 >> 16)
    E(cmp_imm, 6, 0); E(b_cond, "tb_o", "lt")                                     # Filter -> Thru
    E(movt, 2, B31 >> 16); E(lsls_imm, 0, 6, 1); E(b_cond, "tb_o", "mi")         # Merge -> Filter
    E(movt, 2, B30 >> 16)                                                         # Out 2 -> Merge
    a.label("tb_o"); E(orrs_reg, 1, 2)
    a.label("tb_w"); E(str_imm, 1, 5, 0)
    E(pop_list, [4, 5, 6], pc=True)

    # ---- c_thled (r1 = parameter 2, r4 = the Setup view, r5 = the palette) -> r0 = the colour of Duplicate, r1 = [view + 4]
    a.label("c_thled")
    E(movs_imm, 0, COL_FILTER); E(cmp_imm, 1, 0); E(b_cond, "tl_x", "lt")
    E(movs_imm, 0, COL_MERGE); E(lsls_imm, 2, 1, 1); E(b_cond, "tl_x", "mi")
    E(movw, 0, 0x34C); E(lsls_imm, 2, 1, 15); E(b_cond, "tl_p", "pl"); E(movw, 0, 0x34E)
    a.label("tl_p"); E(adds_reg, 0, 0, 5); E(ldrh_imm, 0, 0, 0)
    a.label("tl_x"); E(ldr_imm, 1, 4, 4); E(raw, h(0x4770))
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the post hook, the port slot, the Duplicate toggle and LED, the save mask."""
    import ct_fw
    from thumb import bl as tbl
    BASE = ct_fw.APP_BASE
    code, labels = arm_code(base_addr)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    def put(addr, data, old):
        assert bytes(img[addr - BASE:addr - BASE + len(old)]) == old, hex(addr)
        img[addr - BASE:addr - BASE + len(data)] = data
    put(POST_CALL, tbl(POST_CALL, labels["c_thin"]), tbl(POST_CALL, POST))
    assert struct.unpack_from("<I", img, PORT_VT + 8 - BASE)[0] == PORT_SEND | 1
    struct.pack_into("<I", img, PORT_VT + 8 - BASE, labels["c_thtx"] | 1)
    old_btn = bytes.fromhex("e0 68 02 21".replace(" ", ""))                     # ldr r0,[r4,#0xc]; movs r1,#2
    put(BTN_TOGGLE, h(0x4620) + tbl(BTN_TOGGLE + 2, labels["c_thbtn"]) + b(BTN_TOGGLE + 6, BTN_COMMIT), old_btn)
    old_led = bytes.fromhex("c1f30040")                                           # ubfx r0, r1, #16, #1
    put(LED_CODE, tbl(LED_CODE, labels["c_thled"]) + h(0xBF00) * 8, old_led)
    from thumb import movt as tmovt
    for lab, reg in (("c_m1", 1), ("c_m2", 3)):                                   # the save mask: + bits 30 / 31
        addr = int(report["sc06"]["labels"][lab], 16) + 4
        put(addr, tmovt(reg, SAVE_MASK >> 16), tmovt(reg, 0x3F07))
    return labels, code
