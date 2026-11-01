"""SC48.8 / Beta 3.44 (the user, 2026-10-28: «When you hold shift, you can see on each channel's top pad light (white) whenever they trigger and
back off when gate is no longer held»; «top pad labeled synth, midi, drum... lights on all views while shift is held»): with Shift held, in every
view, the eight track buttons light white while their track has a note sounding and go dark again when its gate ends (with Shift the stock leaves
them dark).

Where the gates are (read in the firmware, emulated):
  * the note tracks: the stock's own sounding-notes store of each track, the one its Note view lights the sounding keys from (the track view's
    [0x200412E0 + 0x2F4 t + 0x30], 160 bits read through 0x08035418): the note dispatcher 0x0803222C sets a note's bit when it sends the note out
    (Synth 1 / 2 after their synth, MIDI 1 / 2 at once) and clears it at the note-off, for the sequencer's notes and the pads alike; any bit = the gate;
  * the drums have no such store: the transmitter's note entries (vtable 0x08059FC4 / + 4: (tx, track, note, velocity); every drum hit and its
    note-off arrive as track 16 with the notes 60 / 62 / 64 / 65 = Drum 1..4, whatever the Setup's Note Tx says): their heads (in front of
    gmdrum's, so they see the stock's notes) keep a bit per drum, set by a note-on, cleared by its note-off or a velocity 0;
  * the LED task (after the chain): Shift held = the panel LED 32 + t (the track buttons: Synth 1, Synth 2, MIDI 1, MIDI 2, Drum 1..4) white 0x01
    for each track whose gate is on.
RAM: modmx.MXR + 0x1EC8 (8 B: + 0 "TRG1", + 4 the drums' bits).  In the hole (no card).

SC49.8 / Beta 5.1 (use_flash(); the user, 2026-10-30: «Trigger flash: with Shift held, each track button flashes white for 100 ms on every note that
track plays, from the sequence, pads, arpeggio or MIDI»): a note-on instead of a gate.  Every sounding note of every source goes through one call,
the note router's slot 0 (vtable word 0x0805B840 -> 0x0803222C: this, note, velocity, key): keys 15..18 = Synth 1, Synth 2, MIDI 1, MIDI 2 sounding, key
19 = a drum (the note = its number 1..4), the same keys that set the sounding-notes bits above.  Its new head keeps the HAL tick by track; the LED
task lights a track button while Shift is held and its last note is less than 100 ms old.  The transmitter's heads and the gate bits go.
RAM: modmx.MXR + 0x21C0 (36 B: + 0 "TFL1", + 4 + 4 t the track's last note, HAL tick)."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bics_reg, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, lsls_imm, lsls_reg,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, str_imm, strb_imm, subs_imm8, subs_reg, tst_reg)
import modmx as MX  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402

RAM = MX.MXR + 0x1EC8
SIG = struct.unpack("<I", b"TRG1")[0]
VIEW0, VIEW_SZ, NOTES_OFF = 0x200412E0, 0x2F4, 0x30   # the note tracks' views; + 0x30 = the track's sounding-notes store
STORE_READ = 0x08035418                                 # (store) -> the data a reader sees (the notes: 5 words)
TX_VT = 0x08059FC4                                      # the transmitter's vtable: + 0 note-on, + 4 note-off (tx, track, note, velocity)
DRUM_TRACK, DRUM_NOTES = 0x10, (60, 62, 64, 65)
LED_BTN, WHITE = 32, 0x01                               # the track buttons' panel LEDs 32..39; white
FLASH = False                                           # SC49.8 / Beta 5.1: 100 ms from each note-on instead of the gate
RAM2 = MX.MXR + 0x21C0
SIG2 = struct.unpack("<I", b"TFL1")[0]
ROUTER_VT, KEY_SOUND, KEY_DRUM = 0x0805B840, 15, 19     # the note router's slot 0; its keys for a note that sounds
HAL_TICK, FLASH_MS = 0x2000081C, 100


def use_flash():
    global FLASH
    FLASH = True


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_tgst() -> r0 = RAM, the drums' bits cleared the first time (the RAM holds the power-up pattern); clobbers r1, r2
    a.label("c_tgst")
    imm32(0, RAM); E(ldr_imm, 1, 0, 0); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "ts_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0); E(str_imm, 1, 0, 4)
    a.label("ts_x"); E(raw, h(0x4770))

    # ---- c_tgdrum(r1 = track, r2 = note) -> r0 = the drum 0..3, or 0xFF
    a.label("c_tgdrum")
    E(movs_imm, 0, 0xFF); E(cmp_imm, 1, DRUM_TRACK); E(b_cond, "td_x", "ne")
    for d, n in enumerate(DRUM_NOTES):
        E(cmp_imm, 2, n); E(b_cond, f"td_{d}", "eq")
    a.label("td_x"); E(raw, h(0x4770))
    for d in range(4):
        a.label(f"td_{d}"); E(movs_imm, 0, d); E(raw, h(0x4770))

    # ---- c_tgmark(r0 = the drum, r1 = 1 on / 0 off): its bit; clobbers r0-r3
    a.label("c_tgmark")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_tgst"); E(ldrb_imm, 1, 0, 4); E(movs_imm, 2, 1); E(lsls_reg, 2, 4)
    E(cmp_imm, 5, 0); E(b_cond, "tm_c", "eq"); E(orrs_reg, 1, 2); E(b, "tm_w")
    a.label("tm_c"); E(bics_reg, 1, 2)
    a.label("tm_w"); E(strb_imm, 1, 0, 4)
    E(pop_list, [4, 5], pc=True)

    # ---- c_tgon / c_tgoff (heads of the transmitter's note-on / note-off: tx, track, note, velocity): a drum's bit, then the chain
    for kind in ("on", "off"):
        a.label(f"c_tg{kind}")
        E(push_list, [0, 1, 2, 3, 4], lr=True)
        E(bl, "c_tgdrum"); E(cmp_imm, 0, 4); E(b_cond, f"t{kind}_p", "hs")
        if kind == "on": E(mov_reg, 1, 3)                                                     # the velocity: 0 = a note-off
        else: E(movs_imm, 1, 0)
        E(bl, "c_tgmark")
        a.label(f"t{kind}_p"); E(raw, popw([0, 1, 2, 3, 4], lr=True)); E(b_w, prev[kind])

    # ---- c_tgled (the LED task calls: ctrl, frame): the chain, then Shift held = the track buttons of the tracks with a gate white
    a.label("c_tgled")
    E(push_list, [3, 4, 5, 6, 7], lr=True); E(mov_reg, 5, 1)
    E(bl, prev["ledtask"])
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "tl_x", "eq")
    E(movs_imm, 4, 0)
    a.label("tl_t")                                                                           # the note tracks: their sounding notes
    imm32(0, VIEW_SZ); E(muls, 0, 4); imm32(1, VIEW0); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, NOTES_OFF)
    E(cmp_imm, 0, 0); E(b_cond, "tl_n", "eq")
    E(bl, STORE_READ); E(cmp_imm, 0, 0); E(b_cond, "tl_n", "eq")
    E(ldr_imm, 1, 0, 0)
    for k in range(1, 5): E(ldr_imm, 2, 0, 4 * k); E(orrs_reg, 1, 2)
    E(cmp_imm, 1, 0); E(b_cond, "tl_n", "eq")
    E(movs_imm, 0, LED_BTN); E(adds_reg, 0, 0, 4); E(bl, "c_tglit")
    a.label("tl_n"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 4); E(b_cond, "tl_t", "lo")
    E(bl, "c_tgst"); E(ldrb_imm, 6, 0, 4); E(movs_imm, 4, 0)                                 # the drums: their bits
    a.label("tl_d")
    E(movs_imm, 0, 1); E(lsls_reg, 0, 4); E(tst_reg, 6, 0); E(b_cond, "tl_e", "eq")
    E(movs_imm, 0, LED_BTN + 4); E(adds_reg, 0, 0, 4); E(bl, "c_tglit")
    a.label("tl_e"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 4); E(b_cond, "tl_d", "lo")
    a.label("tl_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)

    # ---- c_tglit(r0 = a panel LED, r5 = the frame): white; clobbers r0, r1
    a.label("c_tglit")
    E(lsls_imm, 0, 0, 1); E(movs_imm, 1, WHITE); E(raw, h(0x5229)); E(raw, h(0x4770))            # strh r1, [r5, r0]
    return a.assemble()


def arm_code2(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_tfst() -> r0 = RAM2, the ticks cleared the first time (the RAM holds the power-up pattern); clobbers r1, r2
    a.label("c_tfst")
    imm32(0, RAM2); E(ldr_imm, 1, 0, 0); imm32(2, SIG2); E(cmp_reg, 1, 2); E(b_cond, "fs_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0)
    for t in range(8): E(str_imm, 1, 0, 4 + 4 * t)
    a.label("fs_x"); E(raw, h(0x4770))

    # ---- c_tfrt (head of the note router's slot 0: this, note, velocity, key): a note that sounds = its track's tick, then the router
    a.label("c_tfrt")
    E(push_list, [0, 1, 2, 3, 4], lr=True)
    E(mov_reg, 4, 3); E(subs_imm8, 4, KEY_SOUND); E(cmp_imm, 4, KEY_DRUM - KEY_SOUND); E(b_cond, "fr_t", "lo"); E(b_cond, "fr_p", "ne")
    E(adds_imm8, 1, 3); E(mov_reg, 4, 1)                                                      # a drum: 1..4 = the tracks 4..7
    a.label("fr_t")
    E(cmp_imm, 4, 8); E(b_cond, "fr_p", "hs")
    E(bl, "c_tfst"); E(lsls_imm, 4, 4, 2); E(adds_reg, 0, 0, 4)
    imm32(1, HAL_TICK); E(ldr_imm, 1, 1, 0); E(str_imm, 1, 0, 4)
    a.label("fr_p"); E(raw, popw([0, 1, 2, 3, 4], lr=True)); E(b_w, prev["router"])

    # ---- c_tfled (the LED task calls: ctrl, frame): the chain, then Shift held = the track buttons with a note less than 100 ms old white
    a.label("c_tfled")
    E(push_list, [3, 4, 5, 6, 7], lr=True); E(mov_reg, 5, 1)
    E(bl, prev["ledtask"])
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "fl_x", "eq")
    E(bl, "c_tfst"); E(mov_reg, 6, 0)
    imm32(0, HAL_TICK); E(ldr_imm, 7, 0, 0)
    E(movs_imm, 4, 0)
    a.label("fl_t")
    E(lsls_imm, 0, 4, 2); E(adds_reg, 0, 0, 6); E(ldr_imm, 0, 0, 4); E(subs_reg, 0, 7, 0); E(cmp_imm, 0, FLASH_MS); E(b_cond, "fl_n", "hs")
    E(movs_imm, 0, LED_BTN); E(adds_reg, 0, 0, 4); E(lsls_imm, 0, 0, 1); E(movs_imm, 1, WHITE); E(raw, h(0x5229))   # strh r1, [r5, r0]
    a.label("fl_n"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 8); E(b_cond, "fl_t", "lo")
    a.label("fl_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the heads of the transmitter's note-on / note-off, the LED task calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    L = {"c_shift": int(report["sc15"]["labels"]["c_shift"], 16)}
    if FLASH:
        assert u(ROUTER_VT) == 0x0803222D, hex(u(ROUTER_VT))
        prev = dict(router=u(ROUTER_VT) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
        code, labels = arm_code2(base_addr, L, prev)
        img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
        while len(img) % 4:
            img += bytes([0xFF])
        struct.pack_into("<I", img, ROUTER_VT - BASE, labels["c_tfrt"] | 1)
        for c in PK.LED_CALLS:
            assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
            img[c - BASE:c - BASE + 4] = bl(c, labels["c_tfled"])
        return labels, code, prev
    prev = dict(on=u(TX_VT) & ~1, off=u(TX_VT + 4) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    struct.pack_into("<I", img, TX_VT - BASE, labels["c_tgon"] | 1)
    struct.pack_into("<I", img, TX_VT + 4 - BASE, labels["c_tgoff"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_tgled"])
    return labels, code, prev
