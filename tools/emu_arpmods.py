"""SC48.3 / Beta 3.40 (arp.use_ramst + use_mods): the arpeggiator's modifiers, through Synth 1's player tick by tick and the controller
(emu_arp's harness).

    python tools/emu_arpmods.py SC48.3.bin SC48.3_manifest.json

  * a step's chord C E G (16 steps long), the track's resolution, the order up unless said; the modifiers byte (spread | position << 2 |
    groove << 4 | reset << 6) by c_armset; the notes and their ticks:
      none: C E G C E G; spread +1 after an iteration: C E G C' E' G' C; spread +1 / -1 (low to high): C, E, G an octave down, then as they are,
      then up; the down order: high to low; spread +1 every note: C E' G C' E G'; every 4 notes: C E G C, E' G' C' E', G C E G; twice:
      C C E E G G; reset 1: C E G C, C E G C; reset 3 + spread +1 after an iteration: C E G C E G, then an octave up;
      note / dotted note: onsets every 6, 9, 6, 9 ticks; swing: 8, 4, 8, 4;
  * the input, stopped (1/8, the project's tempo), dotted: the second gap 1.5 x the first;
  * Pattern Settings: Shift + pad 4 with the arpeggiator off = the stock's first step (the modifiers untouched); on: Shift + pad 2 / 8 / 11 /
    16 = spread 1, position 3, groove 2, reset 3; the LEDs with Shift: sky / sky / amber / pink, the chosen one bright;
  * the running states in RAM (c_arst), the tail's block "ARM1" at + 320.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_arp import EA, chord_steps, PLAYER  # noqa: E402
from emu_sc08 import CONT  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_R0  # noqa: E402
import arp as A  # noqa: E402

C, E_, G = 60, 64, 67
CHORD = [(C, 96, 0, 100), (E_, 96, 0, 90), (G, 96, 0, 80)]


def M(spread=0, pos=0, groove=0, reset=0): return spread | pos << 2 | groove << 4 | reset << 6


def seq(img, man, mods, order=A.M_UP, steps=12):
    e = EA(img, man)
    p = e.playing(0); base = e.settings(0, p) - 0x380
    e.uc.mem_write(base, chord_steps(CHORD, 16)); e.setpat(0, p, 0, 15)
    e.setp(e.r32(PLAYER + 0x10), 1, bytes([3]))
    e.call(e.A["c_arset"], 0, p, 0x80 | order)
    e.call(e.A["c_armset"], 0, p, mods)
    e.transport(1); e.ons.clear(); e.run(p, steps)
    out = [(t, n) for t, n, _v, _d in e.ons]
    del e; gc.collect()
    return out


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    img = Path(img).read_bytes()
    notes = lambda o, k=None: [n for _t, n in o][:k]
    o = seq(img, man, 0)
    check(notes(o, 6) == [C, E_, G, C, E_, G] and [t for t, _ in o][:4] == [0, 6, 12, 18], f"none: {o[:6]}")
    o = seq(img, man, M(spread=1))
    check(notes(o, 7) == [C, E_, G, C + 12, E_ + 12, G + 12, C], f"spread +1, after an iteration: {notes(o, 7)}")
    o = seq(img, man, M(spread=2))
    check(notes(o, 9) == [C - 12, E_ - 12, G - 12, C, E_, G, C + 12, E_ + 12, G + 12], f"spread +1 / -1, low to high: {notes(o, 9)}")
    o = seq(img, man, M(spread=2), order=A.M_DOWN)
    check(notes(o, 9) == [G + 12, E_ + 12, C + 12, G, E_, C, G - 12, E_ - 12, C - 12], f"the down order: high to low: {notes(o, 9)}")
    o = seq(img, man, M(spread=1, pos=1))
    check(notes(o, 6) == [C, E_ + 12, G, C + 12, E_, G + 12], f"spread +1, every note: {notes(o, 6)}")
    o = seq(img, man, M(spread=1, pos=3))
    check(notes(o, 12) == [C, E_, G, C, E_ + 12, G + 12, C + 12, E_ + 12, G, C, E_, G], f"spread +1, every 4 notes: {notes(o, 12)}")
    o = seq(img, man, M(groove=3))
    check(notes(o, 6) == [C, C, E_, E_, G, G], f"twice: {notes(o, 6)}")
    o = seq(img, man, M(reset=1))
    check(notes(o, 8) == [C, E_, G, C, C, E_, G, C], f"reset after 1: {notes(o, 8)}")
    o = seq(img, man, M(spread=1, reset=2))
    check(notes(o, 12) == [C, E_, G, C, E_, G] + [C + 12, E_ + 12, G + 12, C + 12, E_ + 12, G + 12], f"reset after 3, spread +1 after an iteration: {notes(o, 12)}")
    o = seq(img, man, M(groove=1))
    ts = [t for t, _ in o][:5]
    check(ts == [0, 6, 15, 21, 30], f"note / dotted note: onsets {ts}")
    o = seq(img, man, M(groove=2))
    ts = [t for t, _ in o][:5]
    check(ts == [0, 8, 12, 20, 24], f"swing: onsets {ts}")

    # ---- the input, stopped: the dotted groove on the clock
    e = EA(img, man)
    p = e.playing(0); e.call(e.A["c_arset"], 0, p, 0x80 | 6 << 3 | A.M_UP); e.call(e.A["c_armset"], 0, p, M(groove=1))
    e.set_p0(e.r32(CONT + 0x188), 0); e.press(0); e.release(0); e.press(9); e.release(9)
    e.transport(0); e.w32(A.HAL_TICK, 100000)
    e.pad(20, up=False); e.pad(17, up=False)
    st = A.RAMST + (A.O_LIVE - A.O_SEQ)                                               # Synth 1's input state
    nxt = lambda: e.r32(st + A.S_NEXT)
    e.ifc.clear(); e.ledtask(); d1 = nxt() - 100000                                   # the first step (now): the time to the next
    e.w32(A.HAL_TICK, 100000 + d1); e.ifc.clear(); e.ledtask(); d2 = nxt() - (100000 + d1)
    ons = len([x for x in e.ifc if x[0] == "on"])
    check(ons == 1 and d1 > 0 and abs(2 * d2 - 3 * d1) <= 2, f"the input, stopped, dotted: the next note {d1} ms later, then {d2} ms (1.5 x)")
    e.unpad(17); e.unpad(20)
    del e; gc.collect()

    # ---- Pattern Settings
    e = EA(img, man)
    e.set_p0(e.r32(CONT + 0x188), 0); e.press(0); e.release(0); e.press(12); e.release(12)
    p = e.playing(0)
    stock = e.pads(shift=True)
    e.pad(3, shift=True)
    e.call(e.A["c_armcfg"], 0, p); m0 = e.uc.reg_read(UC_ARM_REG_R0)
    l0 = e.pads()
    check(m0 == 0 and l0[1:3] == [0, 0], f"arpeggiator off: Shift + pad 4 = the stock's first step (pads 1-3 off: {[hex(x) for x in l0[:4]]}), no modifiers ({m0})")
    e.pad(A.PS_PAD_ARP, shift=True)
    for q in (1, 7, 10, 15): e.pad(q, shift=True)
    e.call(e.A["c_armcfg"], 0, p); m1 = e.uc.reg_read(UC_ARM_REG_R0)
    check(m1 == M(1, 3, 2, 3), f"arpeggiator on: Shift + pads 2 / 8 / 11 / 16 = {m1:#x} (want {M(1, 3, 2, 3):#x})")
    l1 = e.pads(shift=True)
    t = int(man["report"]["arp"]["arm_start"], 16) + 12 - 0x08010000                 # the build's colour table (SC48.4: the spread sand)
    mcol = tuple(img[t:t + 8])
    check(mcol in (A.MCOL, (0x6D, 0x69) + A.MCOL[2:]), f"the colour table: sky / sky or sand / sky, amber, pink ({mcol})")
    want = [mcol[2 * (q // 4) + (0 if q % 4 == (1, 3, 2, 3)[q // 4] else 1)] for q in range(16)]
    check(l1[:16] == want, f"the LEDs with Shift: {[hex(x) for x in l1[:16]]} (want {[hex(x) for x in want]})")
    e.call(e.A["c_arst"], 0, 1); s1 = e.uc.reg_read(UC_ARM_REG_R0)
    check(s1 == A.RAMST + (A.O_LIVE - A.O_SEQ), f"the running states in RAM ({s1:#x})")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} ARPMODS RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    A.RAMST = 0x20045000 + 0x1C00                                                       # (build_sc48_3's use_ramst)
    sys.exit(1 if main(sys.argv[1], json.loads(Path(sys.argv[2]).read_text())) else 0)
