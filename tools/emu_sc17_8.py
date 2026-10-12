"""SC17.8 ARM tests: the clear pad (pad 8) of the Master FX view, tap-to-unlatch on every effect pad, and the synth source modes
back in the Shift + Preset view, through the real controller routes (button 0x08033320, pad 0x08033282, release 0x080332FE)
on the live RAM dump (unicorn).

    python tools/emu_sc17_8.py STOCK.bin SC17.7.bin SC17.8.bin SC17.8_manifest.json
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc17_7 as T7  # noqa: E402  (applies use_mixer14 / use_full_leds / use_slots / use_songptr to build_sc17)
from emu_sc17_7 import E7  # noqa: E402
from emu_sc17_6 import ES, MIXER, FX, MIX_PRESS, FX_PRESS  # noqa: E402
import build_sc17 as B  # noqa: E402
import masterfx_dsp as G  # noqa: E402

B.use_clearpad()
BASE = 0x08010000


def dtick(e, ms): return ES.tick(e, ms)                # E7.tick is the sequencer tick: the DSP service tick is ES.tick


def main(stock, ref, img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]
    pal = [(int(x, 16), int(y, 16)) for x, y in rep["sc17"]["pal_codes"]]
    check(int(rep["sc17"]["state"], 16) + B.GFX_SIZE == 0x20044E58 and B.GFX_SIZE == 180,
          f"memory: no new RAM, Master FX block {B.GFX_SIZE} bytes, total reservation {0x20044E58 - int(rep['sc17']['sc14_state'], 16)} bytes")
    def latch_top(e, i): e.pad(i, shift=True); e.rel(i)
    def assign_gater(e, slot_pad):                                  # hold Gater (pad 1), press a bottom pad: that slot = Gater
        e.pad(0); e.pad(slot_pad); e.rel(slot_pad); e.rel(0)

    # ---- the synth source modes are in the Preset view again (SC15), the Shift + Scales view is stock
    vt = lambda a, i: struct.unpack_from("<I", img, a + 4 * i - BASE)[0]
    L15 = {k: int(v, 16) for k, v in rep["sc15"]["labels"].items()}
    if "srcview" in rep:                                                                                    # SC19.1+: the source view's own handlers (tested by emu_sc19_1.py)
        L1 = {k: int(v, 16) for k, v in rep["srcview"]["labels"].items()}
        check(vt(0x0805AC9C, 0) == L1["c_xpad"] | 1 and vt(0x0805AC9C, 7) == L1["c_xleds"] | 1, "synth Preset view: the source view's pad / LED handlers (second Synth press)")
    else:
        check(vt(0x0805AC9C, 0) == L15["c_spad"] | 1 and vt(0x0805AC9C, 7) == L15["c_sleds"] | 1,
              "synth Preset view: SC15's pad / LED handlers (modes with Shift + pads 25-31)")
    check(vt(0x0805A6A4, 0) == 0x08044006 | 1 and vt(0x0805A6A4, 7) == 0x08047592 | 1 and "modeview" not in rep,
          "Shift + Scales view (stock view 7): untouched")

    # ---- the clear pad
    e = E7(img, man); e.grid()
    latch_top(e, 0); latch_top(e, 4)
    check(e.blkb(B.S_LATCH)[0] == 0b010001, f"Shift + pads 1 and 5: Gater and Phaser latched {e.blkb(B.S_LATCH)[0]:#x}")
    g = e.gleds(); check(g[7] == B.CLR_ON, f"pad 8 lit while something is latched {hex(g[7])}")
    w = dtick(e, 1000); check(w.get(G.FX_ON) == (1 << G.B_GATE) | (1 << G.B_PH), f"tick: Gater + Phaser on {hex(w.get(G.FX_ON, -1))}")
    c = e.pad(7); e.rel(7)
    check(c == [] and e.blkb(B.S_LATCH)[0] == 0, f"pad 8: both latched effects off, no stock call {c}")
    w = dtick(e, 1001); check(w.get(G.FX_ON) == 0, f"tick: FX_ON = 0 {hex(w.get(G.FX_ON, -1))}")
    g = e.gleds(); check(g[7] == B.CLR_DIM and g[0] == pal[0][1], f"pad 8 dim again, effect pads dim {hex(g[7])}")
    c = e.pad(7, shift=True); e.rel(7)
    check(c == [] and e.blkb(B.S_LATCH)[0] == 0, "pad 8 with Shift and nothing latched: harmless")

    # SC14 effects of the bottom row, latched
    e = E7(img, man); e.grid()
    e.pad(29, shift=True); e.rel(29); e.pad(26, shift=True); e.rel(26)       # Auto-Filter LP (bit 4), Gater 1/8 (bit 1)
    check(e.s14b(5) == (1 << 4) | (1 << 1) and e.s14b(6) == 2 and e.s14b(7) == 1, f"two SC14 effects latched (latch, Gater, AF) {e.s14b(5)} {e.s14b(6)} {e.s14b(7)}")
    g = e.gleds(); check(g[7] == B.CLR_ON, "pad 8 lit: an SC14 effect is latched")
    dtick(e, 1000)
    c = e.pad(7); e.rel(7)
    check(c == [] and e.s14b(5) == 0 and e.s14b(6) == 0 and e.s14b(7) == 0, f"pad 8: SC14 latches off and the active Gater / Auto-Filter re-picked {e.s14b(5)} {e.s14b(6)} {e.s14b(7)}")
    w = dtick(e, 1001); check(0xDE in w and 0xCF in w, f"tick: stock master gain / filter restored {sorted(hex(a) for a in w)}")
    g = e.gleds(); check(g[7] == B.CLR_DIM, "pad 8 dim")

    # assigned slots, held effects and the song pointer
    e = E7(img, man); e.grid()
    assign_gater(e, 27)
    e.pad(27, shift=True); e.rel(27)
    check(e.blkb(B.S_LATCH)[0] == 1 and e.slot(2) is not None, "Gater assigned to slot 3 and latched through it")
    P = e.step_pad
    e.pad(P(5), shift=True); e.rel(P(5)); sp0 = e.sp()
    latch_top(e, 4); e.pad(1)                                                  # Phaser latched, AF LP (pad 2) held
    check(e.blkb(B.S_LATCH)[0] == 0b010001 and e.blkb(B.S_HELD)[0] == 2 and sp0[0] == 5, "setup: 2 latched, 1 held, song pointer start 5")
    e.pad(7); e.rel(7)
    clr_sp = man["marker"] in ("SC18.1", "SC18.2", "SC18.3", "SC19", "SC19.1", "SC19.2", "SC19.3", "SC19.4", "SC20D", "SC20D.1", "SC19.5", "SC19.6", "SC19.7", "SC19.8", "SC19.9", "SC20", "SC20.1", "SC20.2", "SC21", "SC21.1", "SC21.2", "SC21.3", "SC21.4", "SC22", "SC22.1", "SC22.2", "SC22.3", "SC22.4", "SC23", "SC23.1", "SC23.2", "SC23.3", "SC23.4", "SC23.5", "SC23.6", "SC24", "SC25", "SC26", "SC27", "SC28", "SC29", "SC30", "SC31", "SC32", "SC33", "SC34")                                   # SC18.1: pad 8 also switches the song pointer off
    check(e.blkb(B.S_LATCH)[0] == 0 and e.blkb(B.S_HELD)[0] == 2 and e.sp() == ((0, 0, 0, 0) if clr_sp else sp0) and e.slot(2) is not None,
          f"pad 8: latches off; the held pad and the slot assignment stay; song pointer {'off' if clr_sp else 'kept'} {e.blkb(B.S_HELD)[0]} {e.sp()}")
    e.rel(1)

    # outside the Master FX mode pad 8 is the stock Mixer mute
    e.btn(14)
    e.uc.mem_write(e.blk + B.S_LATCH, bytes([0x11]))
    c = e.pad(7); e.rel(7)
    check(c == [(MIX_PRESS, MIXER, 7)] and e.blkb(B.S_LATCH)[0] == 0x11, f"normal Mixer: pad 8 = stock mute, latches untouched {[(hex(a), hex(b), n) for a, b, n in c]}")

    # ---- tap on a latched pad = off
    e = E7(img, man); e.grid()
    latch_top(e, 4)
    c = e.pad(4)
    check(c == [] and e.blkb(B.S_LATCH)[0] == 0 and e.blkb(B.S_HELD)[0] == 0 and e.blkb(B.S_SEL)[0] == 4,
          f"top row: a tap on the latched Phaser switches it off (not held) {e.blkb(B.S_LATCH)[0]} {e.blkb(B.S_HELD)[0]}")
    e.rel(4); check(e.blkb(B.S_HELD)[0] == 0, "release: still nothing held")
    e.pad(4); check(e.blkb(B.S_HELD)[0] == 1 << 4 and e.blkb(B.S_LATCH)[0] == 0, "next tap: normal hold")
    e.rel(4)
    latch_top(e, 0); e.pad(3)
    check(e.blkb(B.S_LATCH)[0] == 1 and e.blkb(B.S_HELD)[0] == 8, "a tap on another pad does not unlatch the Gater")
    e.rel(3); e.pad(0, shift=True); e.rel(0)
    check(e.blkb(B.S_LATCH)[0] == 0, "Shift + latched pad: off, as before")
    w = dtick(e, 1000); check(w.get(G.FX_ON, 0) == 0, "tick: off")

    # SC14 effects of the bottom row: Auto-Filter (idx 4 -> AF 1) and Gater (idx 1 -> Gater 2)
    e = E7(img, man); e.grid()
    e.pad(29, shift=True); e.rel(29)
    check(e.s14b(5) == 1 << 4 and e.s14b(7) == 1, "Shift + pad 30: Auto-Filter LP latched")
    c = e.pad(29)
    check(c == [] and e.s14b(5) == 0 and e.s14b(4) == 0 and e.s14b(7) == 0, f"tap on the latched SC14 pad: off, not held, Auto-Filter re-picked {e.s14b(5)} {e.s14b(4)} {e.s14b(7)}")
    e.rel(29)
    e.pad(29); check(e.s14b(4) == 1 << 4 and e.s14b(7) == 1 and e.s14b(5) == 0, "next tap: normal SC14 hold"); e.rel(29)
    check(e.s14b(4) == 0 and e.s14b(7) == 0, "released: off")
    e.pad(26, shift=True); e.rel(26); e.pad(25, shift=True); e.rel(25)
    check(e.s14b(5) == 0b11 and e.s14b(6) == 2, f"two Gaters latched: the highest runs (SC14 re-picks on release) {e.s14b(5)} {e.s14b(6)}")
    e.pad(26); e.rel(26)
    check(e.s14b(5) == 0b01 and e.s14b(6) == 1, f"tap on the active one: it goes off, the other takes over {e.s14b(5)} {e.s14b(6)}")
    e.pad(25); e.rel(25)
    check(e.s14b(5) == 0 and e.s14b(6) == 0, "tap on the last: all off")
    c = e.pad(24); e.rel(24)
    check(c == [(FX_PRESS, FX, 24)], "pad 25 (FX off): still the stock handler")

    # assigned slots
    e = E7(img, man); e.grid()
    assign_gater(e, 27)
    e.pad(27, shift=True); e.rel(27)
    check(e.blkb(B.S_LATCH)[0] == 1, "Shift + slot 3: Gater latched")
    c = e.pad(27)
    check(c == [] and e.blkb(B.S_LATCH)[0] == 0 and e.blkb(B.S_SLOTH)[0] == 0, f"tap on the latched slot: off, not held {e.blkb(B.S_LATCH)[0]} {e.blkb(B.S_SLOTH)[0]}")
    e.rel(27)
    e.pad(27); check(e.blkb(B.S_SLOTH)[0] == 1 << 2 and e.blkb(B.S_LATCH)[0] == 0, "next tap: normal slot hold"); e.rel(27)
    check(e.blkb(B.S_SLOTH)[0] == 0, "released")

    # the same in the FX view (bottom row)
    e = E7(img, man); e.grid(); e.btn(15)
    check(e.view() == FX, "FX view")
    e.pad(29, shift=True); e.rel(29)
    check(e.s14b(5) == 1 << 4, "FX view: Shift + pad 30 latches")
    c = e.pad(29); e.rel(29)
    check(c == [] and e.s14b(5) == 0 and e.s14b(7) == 0, "FX view: a tap on the latched pad switches it off")

    print("SC17.8 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    st, rf, im = (Path(sys.argv[i]).read_bytes() for i in (1, 2, 3))
    sys.exit(1 if main(st, rf, im, json.loads(Path(sys.argv[4]).read_text())) else 0)
