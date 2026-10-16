"""SC42.3 ARM tests: the arpeggiator's own resolution and the notes' own gates (arp.use_rate), the gate by holding in step entry (stepgate.py),
the metronome's colours (countin.use_cols2); through the controller, the players' per-tick calls and the real LED task.

    python tools/emu_arprate.py NEW.bin NEW_manifest.json
  * Pattern Settings of Synth 1, Shift + pads 17-24 = the resolution (bits 3-6 of the setting; the same pad again = the track's); with Shift those
    pads yellow and the chosen one green; the order pads keep the resolution; pad 25 keeps it;
  * the sequence (track at 1/16): at 1/32 one note every 3 ticks, at 1/8 every 12, at the track's every 6; each note lasts its own gate, at most
    what is left of the chord;
  * the input, stopped: at 1/8 and 120 BPM one note every 250 ms; playing: at 1/32 one note every 3 ticks, 3 ticks long;
  * step entry (Synth 1's track view; a step held + a note pad, or a note held + a step pad): with the toggle off, the stock's gate; pad 32 of the
    Micro Step view (Gate twice) turns it on (green; dim off); on: the time held = the gate (375 ms at 120 BPM = 18 micro steps; 2 s = 96 at most);
    the other track's toggle is its own;
  * Shift held: the Clear LED red / green / magenta / cyan for the metronome's four states.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_arp as EA_  # noqa: E402
from emu_arp import EA, chord_steps, PLAYER, TICK_BUILD, TICK_PLAY, VIEW_IFC  # noqa: E402
from emu_sc35 import MGR  # noqa: E402
from emu_sc08 import CONT  # noqa: E402
import arp as A  # noqa: E402
import stepgate as SG  # noqa: E402
import countin as CI  # noqa: E402

TV = 0x200412E0


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    Y, G = A.COL_AV, A.COL_ON

    # ---- Pattern Settings: the resolution
    e = EA(img, man)
    e.set_p0(e.r32(CONT + 0x188), 0); e.press(0); e.release(0); e.press(12); e.release(12)
    pat = e.playing(0)
    e.pad(16 + 5, shift=True); c1 = e.cfg(0, pat); l1 = e.pads(shift=True)
    check(c1 == 6 << 3 and l1[16:24] == [Y] * 5 + [G] + [Y] * 2, f"Shift + pad 22: the resolution 1/8 (setting {c1:#x}); with Shift pads 17-24 yellow, it green ({[hex(x) for x in l1[16:24]]})")
    e.pad(A.PS_PAD_ARP, shift=True); e.pad(26 + 3, shift=True); c2 = e.cfg(0, pat)
    check(c2 == 0x80 | 6 << 3 | A.M_DOWN, f"pad 25 and an order pad keep the resolution ({c2:#x})")
    e.pad(16 + 5, shift=True); c3 = e.cfg(0, pat)
    check(c3 == 0x80 | A.M_DOWN, f"the same pad again: back to the track's resolution ({c3:#x})")
    l0 = e.pads()
    check(l0[16:24] != [Y] * 8, "without Shift pads 17-24 are the stock's")
    del e; gc.collect()

    # ---- the sequence
    def seq(setting, units, steps):
        e = EA(img, man)
        p = e.playing(0); base = e.settings(0, p) - 0x380
        e.uc.mem_write(base, chord_steps(units)); e.setpat(0, p, 0, 7)
        e.setp(e.r32(PLAYER + 0x10), 1, bytes([3]))
        e.call(e.A["c_arset"], 0, p, setting)
        e.transport(1); e.ons.clear(); e.run(p, steps)
        out = list(e.ons); del e; gc.collect(); return out
    ch = [(64, 36, 0, 100), (60, 36, 0, 90), (67, 36, 0, 80)]
    s32 = seq(0x80 | 2 << 3 | A.M_UP, ch, 7)
    check([t for t, *_ in s32] == list(range(0, 36, 3)) and [n for _, n, _, _ in s32][:4] == [60, 64, 67, 60]
          and [d for *_, d in s32] == [36 - t for t in range(0, 36, 3)], f"1/32 on a 1/16 track: a note every 3 ticks, lasting what is left of the chord ({s32[:5]}…)")
    s8 = seq(0x80 | 6 << 3 | A.M_UP, ch, 7)
    check([t for t, *_ in s8] == [0, 12, 24], f"1/8: every 12 ticks ({s8})")
    gates = [(60, 6, 0, 90), (64, 24, 0, 100), (67, 12, 0, 80), (72, 30, 0, 70)]
    sg = seq(0x80 | A.M_UP, gates, 6)
    check(sg == [(0, 60, 90, 6), (6, 64, 100, 24), (12, 67, 80, 12), (18, 72, 70, 12), (24, 60, 90, 6)],
          f"the track's resolution: a note a step, each with its own gate (at most what is left of the chord) ({sg})")

    # ---- the input
    e = EA(img, man)
    p = e.playing(0); e.call(e.A["c_arset"], 0, p, 0x80 | 6 << 3 | A.M_UP)
    e.set_p0(e.r32(CONT + 0x188), 0); e.press(0); e.release(0); e.press(9); e.release(9)
    e.transport(0); e.w32(A.HAL_TICK, 100000); e.ifc.clear()
    e.pad(20, up=False); e.pad(17, up=False)
    e.ifc.clear(); e.ledtask()
    e.ifc.clear(); e.w32(A.HAL_TICK, 100249); e.ledtask(); s1 = list(e.ifc)
    e.w32(A.HAL_TICK, 100250); e.ledtask(); s2 = list(e.ifc)
    check(s1 == [] and len([x for x in s2 if x[0] == "on"]) == 1, f"the input, stopped, 1/8 at 120 BPM: the next note 250 ms later ({s1}, {s2})")
    e.unpad(17); e.unpad(20)
    e.call(e.A["c_arset"], 0, p, 0x80 | 2 << 3 | A.M_UP)
    e.ifc.clear(); e.pad(20, up=False); e.pad(17, up=False); e.transport(1); e.ons.clear()
    lo_n, hi_n = 62, 67
    e.ledtask()
    e.setp(e.r32(PLAYER + 0x10), 1, bytes([3])); e.run(p, 2)
    ons = [x for x in e.ons if x[1] in (lo_n, hi_n)]
    check([t for t, *_ in ons] == [0, 3, 6, 9] and all(d == 3 for *_, d in ons), f"the input, playing, 1/32: a note every 3 ticks, 3 ticks long ({ons})")
    e.unpad(17); e.unpad(20)
    del e; gc.collect()

    # ---- step entry: the gate by holding
    e = EA(img, man)
    lab = {k: int(v, 16) for k, v in man["report"]["stepgate"]["labels"].items()}
    e.set_p0(e.r32(CONT + 0x188), 0); e.press(0); e.release(0)
    e.transport(0)
    def store_units():
        st = e.r32(TV + 0x24); out = []
        e.call(0x0803542C, st, 0); mp = e.uc.reg_read(EA_.UC_ARM_REG_R0); mask = e.r8(mp)
        for k in range(6):
            if mask >> k & 1:
                e.call(0x080354FA, st, k + 1); q = e.uc.reg_read(EA_.UC_ARM_REG_R0); out.append((e.r8(q), e.r8(q + 1) & 0x7F))
        return out
    def enter(step_pad, note_pad, held_ms):
        e.w32(A.HAL_TICK, 200000)
        e.pad(step_pad, up=False); e.pad(note_pad, up=False)
        e.w32(A.HAL_TICK, 200000 + held_ms); e.unpad(note_pad); u = store_units(); e.unpad(step_pad); return u
    u_off = enter(4, 16, 375)
    check(u_off and all(g != 18 for _, g in u_off), f"toggle off: the stock's gate ({u_off})")
    e.press(11); e.release(11); e.press(11); e.release(11)
    sub = e.r8(MGR + 0x152)
    ms = e.pads()
    e.pad(31); ms2 = e.pads()
    check(sub == 8 and ms[31] == SG.COL_OFF and ms2[31] == SG.COL_ON, f"Gate twice = the Micro Step view; pad 32 dim, then green ({ms[31]:#x}, {ms2[31]:#x})")
    e.call(lab["c_sgon"], 0); on0 = e.uc.reg_read(EA_.UC_ARM_REG_R0); e.call(lab["c_sgon"], 1); on1 = e.uc.reg_read(EA_.UC_ARM_REG_R0)
    check(on0 == 1 and on1 == 0, "on for Synth 1 only")
    e.press(0); e.release(0)
    u_on = enter(5, 17, 375)
    n17 = [n for n, g in u_on if g == 18]
    check(len(n17) == 1, f"on: a step held + a note pad held 375 ms at 120 BPM = gate 18 micro steps ({u_on})")
    u_long = enter(6, 18, 2000)
    check(any(g == SG.GMAX for _, g in u_long), f"held 2 s: 96 at most ({u_long})")
    # ---- the fixed length: pad 31 of the Micro Step view
    e.press(11); e.release(11); e.press(11); e.release(11)
    e.w32(A.HAL_TICK, 300000); e.pad(30); sel = e.pads()
    e.call(lab["c_sgon"], 0); hold = e.uc.reg_read(EA_.UC_ARM_REG_R0)
    check(sel[16] == SG.COL_ON and sel[17:32] == [SG.COL_OFF] * 15 and hold == 0,
          f"pad 31 (off): on, the selector (pads 17-32 = 1..16 steps, 1 lit), pad 32 off ({[hex(x) for x in sel[16:]]}, {hold})")
    e.pad(19); after = e.pads()
    e.call(lab["c_sgfget"], 0); fb = e.uc.reg_read(EA_.UC_ARM_REG_R0)
    check(fb == 0x84 and after[30] == SG.COL_FIX and after[31] == SG.COL_OFF, f"pad 20 in the selector: 4 steps, the selector closed; pad 31 orange, pad 32 dim ({fb:#x}, {after[30]:#x}, {after[31]:#x})")
    e.press(0); e.release(0)
    u_fix = enter(7, 19, 100)
    check(any(g == 24 for _, g in u_fix), f"fixed length on: a note entered by hand = 4 steps (24 micro steps) whatever the hold ({u_fix})")
    e.press(11); e.release(11); e.press(11); e.release(11)
    e.w32(A.HAL_TICK, 400000); e.pad(30, up=False); e.w32(A.HAL_TICK, 400200); e.unpad(30); s2 = e.pads()
    check(s2[16:20] == [SG.COL_ON] * 4 and s2[20] == SG.COL_OFF, "pad 31 (on), short: the selector again, 4 lit")
    e.pad(16)
    e.w32(A.HAL_TICK, 500000); e.pad(30, up=False); e.w32(A.HAL_TICK, 501200); e.unpad(30)
    e.call(lab["c_sgfget"], 0); fo = e.uc.reg_read(EA_.UC_ARM_REG_R0)
    check(fo == 0x01, f"pad 31 (on), held 1.2 s: off, the length kept ({fo:#x})")
    e.pad(30); e.pad(19); e.pad(31)
    e.call(lab["c_sgfget"], 0); f3 = e.uc.reg_read(EA_.UC_ARM_REG_R0); e.call(lab["c_sgon"], 0); h3 = e.uc.reg_read(EA_.UC_ARM_REG_R0)
    check(f3 & 0x80 == 0 and h3 == 1, f"pad 32 on: the fixed length off ({f3:#x}, {h3})")
    del e; gc.collect()

    # ---- the metronome's colours with Shift
    e = EA(img, man)
    cols = []
    for k in range(4):
        e.set_p0(e.r32(MGR + 0xC), 1)
        e.ledtask(); f = list(struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138))))
        cols.append(f[CI.LED_CLEAR] & 0xFF)
        e.press(CI.ID_CLEAR); e.release(CI.ID_CLEAR); e.set_p0(e.r32(MGR + 0xC), 0)
    check(sorted(cols) == sorted([0x53, 0x17, 0x32, 0x4D]), f"Shift held: Clear red / green / magenta / cyan through the four states ({[hex(c) for c in cols]})")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
