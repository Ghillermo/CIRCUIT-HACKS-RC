"""SC41.5 (the user, 2026-10-14: «implementa un canal de escucha y envío a PGM.  Cuando se toca el pad de PGM Rx, se ilumina el canal de escucha, y
cuando se toca el de Tx, se ilumina el de salida.  Por defecto, 16.  Además de escuchar / recibir en esos canales, se hace forward de los mensajes
entrantes al canal de salida»).

The stock (read in the firmware):
  * the project's program changes (they choose the project) are received on the channel of the receive table's entries 0x20 / 0x21 (D + 12 / 13,
    D = [[[[0x200069E4]] + 0x18] + 8]) and sent on the transmit table's entries 3 / 4 ([[X + 0xC] + 5 + 3 / 4], X = [[[0x200069E4]] + 0x1C]); both
    are 15 (channel 16), set once and never by the settings; the same entries also carry the project's CCs, which stay on channel 16;
  * receive (0x080518AA, with PGM Rx on): 0x08052B24(D + 4, channel) = «is it a channel of the table»; then Synth 1 / Synth 2 / drums by their
    channel, anything else of the table = the project; a project asked for by MIDI is not sent back (0x0802F77E's third argument);
  * send: 0x0802A018(X, port, id, program): the channel of the table's entry of id (0x20 -> 3, 0x21 -> 4), PGM Tx gate = bit 2 of [X + 0x18]; a
    project chosen on the panel sends its program change through it (id 0x20, port 7);
  * the Setup view (the controller's mode 8, [ctrl + 0x68], an object of 0x28 B, + 0x24 = its Advanced flag): pads 1-15 = the channel of the
    track chosen with the track buttons, pad 29 = PGM Rx (bit 9 of parameter 2), pad 30 = PGM Tx (bit 8);
  * the settings are saved when 0x0802D300 («changed?») finds a difference: it compares the low bytes of parameters 3-7, parameter 0's and part
    of parameter 2, then the same 4 B again with memcmp 0x08025180 (bl at 0x0802D35A, r4 = the record 0x2003974C, [r4 + 0x9C] = the store).

Ours:
  * two channels kept in bytes of the global settings nobody else uses: bytes 1 and 2 of parameter 3 (Synth 1's channel is its byte 0; every reader
    and writer of the channel parameters uses byte accesses, the load-time check looks at byte 0 only, the load 0x0802D178 and the save 0x0802D2AC
    copy the 8 first parameters as words); stored as channel index XOR 15, so 0 = channel 16; written through the store; c_pgcmp after the
    memcmp of 0x0802D35A also compares them, so the stock's own save writes them;
  * receive: the stock's test (bl at 0x080518C0) -> c_pgrx: a program change on the listen channel is accepted (the project's) and sent again by
    the stock's send (id 0x20, port 7: on the output channel, if PGM Tx is on); Synth 1 / Synth 2 / drums on their channels as before; channel 16
    is no longer the project's unless it is the listen channel;
  * send: in 0x0802A018 the `orr r5, #0xc0` (0x0802A04E) -> c_pgtx: the project's entries (3 / 4) take the output channel;
  * the Setup view (not Advanced): pad 29 (PGM Rx) the first time shows the listen channel on pads 1-16 (the chosen one white, the rest dim white),
    touched again = the stock's on / off; pad 30 the same for the output channel; a channel pad sets it; a track button or another pad goes back to
    the stock's channels.  The view's state = its byte + 0x25 (padding after the Advanced flag; Beta's Record toggle is + 0x26), cleared by the LED
    task out of the Setup view.

SC41.6 (PF, use_pf(); the user, 2026-10-15: «el patch flipper envía por el canal asignado a la pista MIDI, no el general»): the patch flip of
MIDI 1 / 2 (build_sc06: a note = a program change on the MIDI track's channel, out with PGM Tx and injected with c_injB when that channel is
Synth 1's / Synth 2's / the drums') stays on the track's channel.  Its injection reaches c_pgrx; with the listen channel = that channel, SC41.5
sent it again on the general output channel.  Now c_pgrx does not send again what comes from an internal injection (bit 5 of the receiver's
+ 0x14, set by c_inject during the injection); it still goes to its track.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, b, b_cond, b_w, bl, cmp_imm, cmp_reg, eors_reg, ands_reg, ldr_imm, ldrb_imm, ldrb_reg, ldrb_w, lsls_imm,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, orrs_reg, pop_list, push_list, raw, h, strb_reg, strb_w, strh_reg)
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402

CTX = 0x200069E4
PARAM_GET, PARAM_WPTR, PARAM_COMMIT = 0x0803542C, 0x080354FA, 0x080353C0
SETOBJ = 0x2003974C
PC_SEND, PC_PORT, PC_ID = 0x0802A018, 7, 0x20
RX_HOOK, RX_OLD = 0x080518C0, 0x08052B24
TX_HOOK, TX_OLD = 0x0802A04E, bytes.fromhex("45f0c005")              # orr r5, r5, #0xc0
CMP_HOOK, MEMCMP = 0x0802D35A, 0x08025180
SETUP_VT, SETUP_OBJ, ADV_OFF, ST_OFF = 0x0805A98C, 0x20044958, 0x24, 0x25
MGR, MODE_STORE, MODE_SETUP = 0x20040B10, 0x14, 8
P_CH, B_RX, B_TX = 3, 1, 2                                            # parameter 3, its bytes 1 / 2
ST_RX, ST_TX = 0xB1, 0xB2
PAD_RX, PAD_TX = 0x1C, 0x1D                                           # pads 29 / 30
COL_SEL, COL_DIM = 0x01, 0x02                                         # white, dim white
PF = False                                                            # SC41.6 (use_pf): an internal injection is not sent again
RX_INTERNAL = 0x20                                                    # the receiver's + 0x14: an internal injection (c_inject)


def use_pf():
    global PF
    PF = True


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def ctx(rd, off):                                 # rd = [[[CTX]] + off]
        imm32(rd, CTX); E(ldr_imm, rd, rd, 0); E(ldr_imm, rd, rd, 0); E(ldr_imm, rd, rd, off)

    # ---- c_pgch(r0 = 1 listen / 2 output) -> r0 = the channel index 0..15; clobbers r1-r3
    a.label("c_pgch")
    E(push_list, [4], lr=True)
    E(mov_reg, 4, 0); ctx(0, 0x54); E(movs_imm, 1, P_CH); E(bl, PARAM_GET)
    E(ldrb_reg, 0, 0, 4); E(movs_imm, 1, 15); E(eors_reg, 0, 1); E(ands_reg, 0, 1)
    E(pop_list, [4], pc=True)

    # ---- c_pgset(r0 = 1 / 2, r1 = index 0..15): written through the store; clobbers r0-r3
    a.label("c_pgset")
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0); E(movs_imm, 0, 15); E(eors_reg, 1, 0); E(mov_reg, 5, 1)
    ctx(0, 0x54); E(movs_imm, 1, P_CH); E(bl, PARAM_WPTR); E(strb_reg, 5, 0, 4)
    ctx(0, 0x54); E(bl, PARAM_COMMIT)
    E(pop_list, [4, 5], pc=True)

    # ---- c_pgrx (in place of the receive's bl 0x08052B24: r0 = the receive table + 4, r1 = channel; the caller's r5 = the message) -> r0 = 1 accepted
    a.label("c_pgrx")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 6, 1)
    E(movs_imm, 0, B_RX); E(bl, "c_pgch"); E(cmp_reg, 6, 0); E(b_cond, "rx_t", "ne")
    if PF:                                                                             # (an internal injection, the patch flip: not sent again)
        E(ldrb_imm, 0, 4, 0x10); E(lsls_imm, 0, 0, 26); E(b_cond, "rx_n", "mi")
    ctx(0, 0x1C); E(movs_imm, 1, PC_PORT); E(movs_imm, 2, PC_ID); E(ldrb_imm, 3, 5, 1)     # the listen channel: the project's, sent again
    E(bl, PC_SEND)
    if PF:
        a.label("rx_n")
    E(movs_imm, 0, 1); E(pop_list, [4, 5, 6], pc=True)
    a.label("rx_t")
    for off in (5, 6, 7):                                                              # Synth 1, Synth 2, drums: by their channel, as the stock
        E(ldrb_imm, 0, 4, off); E(cmp_reg, 6, 0); E(b_cond, "rx_y", "eq")
    E(movs_imm, 0, 0); E(pop_list, [4, 5, 6], pc=True)
    a.label("rx_y"); E(movs_imm, 0, 1); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_pgtx (in place of `orr r5, r5, #0xc0` in 0x0802A018: r2 = the table's entry, r5 = its channel): the project's entries take the output channel
    a.label("c_pgtx")
    E(push_list, [0, 1, 2, 3], lr=True)
    E(cmp_imm, 2, 3); E(b_cond, "tx_k", "lo"); E(cmp_imm, 2, 4); E(b_cond, "tx_k", "hi")
    E(movs_imm, 0, B_TX); E(bl, "c_pgch"); E(mov_reg, 5, 0)
    a.label("tx_k"); E(movs_imm, 0, 0xC0); E(orrs_reg, 5, 0)
    E(pop_list, [0, 1, 2, 3], pc=True)

    # ---- c_pgcmp (in place of the bl memcmp at 0x0802D35A: r0, r1, r2 its arguments, r4 = the settings record) -> r0 != 0 = changed
    a.label("c_pgcmp")
    E(push_list, [5], lr=True)
    E(bl, MEMCMP); E(cmp_imm, 0, 0); E(b_cond, "cp_x", "ne")
    E(mov_reg, 0, 4); E(adds_imm8, 0, 0x9C); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, P_CH); E(bl, PARAM_GET)
    for byte in (B_RX, B_TX):
        E(ldrb_imm, 1, 0, byte); E(ldrb_imm, 2, 4, 0x14 + byte); E(cmp_reg, 1, 2); E(b_cond, "cp_d", "ne")
    E(movs_imm, 0, 0); E(pop_list, [5], pc=True)
    a.label("cp_d"); E(movs_imm, 0, 1)
    a.label("cp_x"); E(pop_list, [5], pc=True)

    # ---- c_pgpad (the Setup view's pad press: view, pad, velocity): pads 29 / 30 and the channel pads while one of them is shown
    a.label("c_pgpad")
    E(push_list, [0, 1, 2, 4, 5], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(ldrb_w, 0, 4, ADV_OFF); E(cmp_imm, 0, 0); E(b_cond, "pp_f", "ne")
    E(ldrb_w, 2, 4, ST_OFF)
    for pad, st in ((PAD_RX, ST_RX), (PAD_TX, ST_TX)):
        E(cmp_imm, 5, pad); E(b_cond, f"pp_n{pad}", "ne")
        E(cmp_imm, 2, st); E(b_cond, "pp_f", "eq")                                    # shown already: the stock's on / off
        E(movs_imm, 0, st); E(strb_w, 0, 4, ST_OFF); E(b, "pp_x")
        a.label(f"pp_n{pad}")
    E(cmp_imm, 5, 16); E(b_cond, "pp_o", "hs")
    E(movs_imm, 0, B_RX); E(cmp_imm, 2, ST_RX); E(b_cond, "pp_s", "eq")
    E(movs_imm, 0, B_TX); E(cmp_imm, 2, ST_TX); E(b_cond, "pp_f", "ne")
    a.label("pp_s"); E(mov_reg, 1, 5); E(bl, "c_pgset")
    a.label("pp_x"); E(pop_list, [0, 1, 2, 4, 5], pc=True)
    a.label("pp_o"); E(movs_imm, 0, 0); E(strb_w, 0, 4, ST_OFF)                         # another pad: the stock's channels again
    a.label("pp_f"); E(raw, popw([0, 1, 2, 4, 5], lr=True)); E(b_w, prev["pad"])

    # ---- c_pgbtn (the Setup view's slot 2: view, button): a track button = the stock's channels again
    a.label("c_pgbtn")
    E(cmp_imm, 1, 8); E(b_cond, "pb_f", "hs")
    E(movs_imm, 2, 0); E(strb_w, 2, 0, ST_OFF)
    a.label("pb_f"); E(b_w, prev["btn"])

    # ---- c_pgledtask (the LED task calls: ctrl, frame): the chain; the Setup view with a PGM channel shown: pads 1-16; out of it the state cleared
    a.label("c_pgledtask")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    imm32(4, SETUP_OBJ)
    imm32(0, MGR); E(ldr_imm, 0, 0, MODE_STORE); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, MODE_SETUP); E(b_cond, "pl_c", "ne")
    E(ldrb_w, 0, 4, ADV_OFF); E(cmp_imm, 0, 0); E(b_cond, "pl_c", "ne")
    E(ldrb_w, 1, 4, ST_OFF); E(movs_imm, 0, B_RX); E(cmp_imm, 1, ST_RX); E(b_cond, "pl_s", "eq")
    E(movs_imm, 0, B_TX); E(cmp_imm, 1, ST_TX); E(b_cond, "pl_x", "ne")
    a.label("pl_s"); E(bl, "c_pgch"); E(mov_reg, 6, 0)
    E(movs_imm, 7, 0)
    a.label("pl_l")
    E(movs_imm, 2, COL_DIM); E(cmp_reg, 7, 6); E(b_cond, "pl_w", "ne"); E(movs_imm, 2, COL_SEL)
    a.label("pl_w"); E(lsls_imm, 0, 7, 1); E(strh_reg, 2, 5, 0)
    E(adds_imm8, 7, 1); E(cmp_imm, 7, 16); E(b_cond, "pl_l", "lo")
    E(b, "pl_x")
    a.label("pl_c"); E(movs_imm, 0, 0); E(strb_w, 0, 4, ST_OFF)
    a.label("pl_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the receive's test, the send's channel, the settings' «changed?», slots 0 / 2 of the Setup view, the two LED task calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a: struct.unpack_from("<I", img, a - BASE)[0]
    at = lambda a: bytes(img[a - BASE:a - BASE + 4])
    assert at(RX_HOOK) == bl(RX_HOOK, RX_OLD), "receive hook"
    assert at(TX_HOOK) == TX_OLD, "send hook"
    assert at(CMP_HOOK) == bl(CMP_HOOK, MEMCMP), "compare hook"
    prev = dict(pad=u(SETUP_VT) & ~1, btn=u(SETUP_VT + 8) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[RX_HOOK - BASE:RX_HOOK - BASE + 4] = bl(RX_HOOK, labels["c_pgrx"])
    img[TX_HOOK - BASE:TX_HOOK - BASE + 4] = bl(TX_HOOK, labels["c_pgtx"])
    img[CMP_HOOK - BASE:CMP_HOOK - BASE + 4] = bl(CMP_HOOK, labels["c_pgcmp"])
    struct.pack_into("<I", img, SETUP_VT - BASE, labels["c_pgpad"] | 1)
    struct.pack_into("<I", img, SETUP_VT + 8 - BASE, labels["c_pgbtn"] | 1)
    for c in PK.LED_CALLS:
        assert at(c) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_pgledtask"])
    return labels, code, prev
