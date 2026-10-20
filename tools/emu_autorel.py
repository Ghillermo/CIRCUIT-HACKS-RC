"""SC45 ARM tests: tools/modesel.py (pad 27 of the MIDI Preset view = the mode row) and tools/autorel.py (Velocity view, Shift + a step pad = the
step lets go of the automation), through the controller, the real LED task and the stock's playback of the automation (0x08031AFC: a listener of
the object 0x2003EBDC, driven here as the sequencer drives it: the track's step store + 0xC p1 = the step, its trigger store + 0x28 p0 = 1,
the transport running).

    python tools/emu_autorel.py SC45.bin SC45_manifest.json
  * modesel: pad 27 opens the row (pads 17-23 in the modes' colours, the current one bright, pads 9-16 / 24 dark); a mode pad = that mode (the
    stock cycle, c_msmode), the row stays; a press on pads 9-16 is swallowed; pad 27 closes it (the patches' LEDs back); Shift + pad 27 = the stock;
  * autorel: Shift + pad 4 in MIDI 1's Velocity view = bit 7 of byte [3] of step 4, again = off; on the 17-32 page step 20; with Shift the step pads
    yellow / red; without Shift the stock's step pad (no mark);
  * Synth 1's playback: lane 0 = 100 at step 2: the macro store moves to 100; at step 4 (marked, with a value 50 in the lane) nothing plays and
    the store goes back to the macro's position before (127); then step 2 plays again; a turn of the macro knob by hand clears the flag (MIDI 1: K5 of page 4, through c_vsync);
  * MIDI 1 with the engine on: lane 4 at step 2, the mark at step 5: the macro store back to the engine's value before (as a lane value).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import autorel as AR  # noqa: E402
import modesel as MS  # noqa: E402

V = T4.V
MGR = X.MGR
O = 0x2003EBDC


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]
    ml = {k: int(v, 16) for k, v in R["modesel"]["labels"].items()}
    # ---- modesel
    e = X.EP(img, man)
    mode = lambda: e.r0(ml["c_msmode"], 0)
    e.btn(2); e.btn(8)
    f0 = X.frame(e)
    m0 = mode()
    e.pad(26); f = X.frame(e)
    want = [MS.COLS[k][0 if k == m0 else 1] for k in range(7)]
    check(e.r8(MS.RAM) == 1 and mode() == m0 and f[16:23] == want and f[8:16] == [0] * 8 and f[23] == 0,
          f"pad 27: the row open, the mode unchanged ({m0}); pads 17-23 {[hex(x) for x in f[16:23]]}, 9-16 / 24 dark")
    got = []
    for m in (5, 2, 6, 0, 3):
        e.pad(16 + m); got.append(mode())
    check(got == [5, 2, 6, 0, 3] and e.r8(MS.RAM) == 1, f"a mode pad = that mode, the row stays open ({got})")
    f = X.frame(e); check(f[16 + 3] == MS.COLS[3][0] and f[16 + 1] == MS.COLS[1][1], f"the current one bright ({f[19]:#x}), the others dim ({f[17]:#x})")
    m1 = mode(); e.pad(9); check(mode() == m1 and e.r8(MS.RAM) == 1, "a press on pad 10 swallowed")
    e.pad(26); f = X.frame(e)
    check(e.r8(MS.RAM) == 0 and f[8:24] == f0[8:24], f"pad 27 again: closed, the patches' LEDs back ({e.r8(MS.RAM)})")
    e.shift(True); e.pad(26); e.shift(False)
    check(e.r8(MS.RAM) == 0 and mode() != m1, f"Shift + pad 27: the stock / vcf21 (the mode moves on: {m1} -> {mode()}), the row closed")
    del e; gc.collect()
    # ---- autorel: the mark
    e = X.EP(img, man)
    pat = lambda t: e.r0(int(R["vcf20"]["labels"]["c_sdpat"], 16), (t + 2) % 4)
    b3 = lambda t, s: e.r8(pat(t) + 28 * s + 3)
    e.btn(2); e.btn(10)
    check(e.r8(MGR + 0x152) == 9 * 2 + 2, f"MIDI 1's Velocity view (subview {e.r8(MGR + 0x152)})")
    e.shift(True); e.pad(3); a1 = b3(2, 3); f = X.frame(e); e.shift(False)
    check(a1 & 0x80 and f[3] == AR.COL_MARK and f[0] == AR.COL_AV and f[15] == AR.COL_AV, f"Shift + pad 4: step 4 marked ({a1:#x}); Shift: the step pads yellow, the marked red ({f[0]:#x} {f[3]:#x})")
    e.shift(True); e.pad(3); e.shift(False)
    check(not b3(2, 3) & 0x80, f"again: unmarked ({b3(2, 3):#x})")
    e.btn(21); e.shift(True); e.pad(3); e.shift(False); e.btn(21)
    check(b3(2, 19) & 0x80 and not b3(2, 3) & 0x80, f"the 17-32 page: step 20 ({b3(2, 19):#x})")
    e.pad(5); check(not b3(2, 5) & 0x80 and e.r8(AR.RAM + 36) == 0, "without Shift: the stock's step pad, no mark")
    del e; gc.collect()
    # ---- autorel: the playback
    e = X.EP(img, man)
    def pget(st, i): e.call(0x0803542C, st, i, maxins=100000); return e.uc.reg_read(UC_ARM_REG_R0)
    def pset(st, i, v):
        e.call(0x080354FA, st, i, maxins=100000); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes([v])); e.call(0x080353C0, st, maxins=4_000_000)
    def step(t, s):
        sub = e.r32(e.r32(O + 0x38) + 4 * t)
        pset(e.r32(sub + 0xC), 1, s); pset(e.r32(sub + 0x28), 0, 1)
        e.call(0x08031AFC, O + 4, e.r32(sub + 0x28), 0, maxins=8_000_000)
    store = lambda t, k: e.r8(pget(e.r32(e.r32(O + 0x2C) + 4 * t), k))
    def lane(t, k, s, v): e.uc.mem_write(pat(t) + 0x3A8 + 192 * k + 6 * s, bytes([v]) * 6)
    def mark(t, s): a = pat(t) + 28 * s + 3; e.uc.mem_write(a, bytes([e.r8(a) | 0x80]))
    for t in (0, 2):
        for k in range(8):
            for s in range(16): lane(t, k, s, 0xFF)
    e.transport(1)
    lane(0, 0, 2, 100); lane(0, 0, 4, 50); mark(0, 4)
    e.call(V.GETTER, 0, 174, maxins=200000); kp = e.uc.reg_read(UC_ARM_REG_R0)
    seq = []
    for s in (1, 2, 3, 4, 5, 2):
        step(0, s); seq.append(store(0, 0))
    check(seq == [kp, 100, 100, kp, kp, 100], f"Synth 1, lane 0: steps 1-5 then 2 = {seq} (the knob {kp}; step 4 marked, its 50 does not play)")
    flags = e.r32(AR.RAM)
    check(flags & 1, f"after step 2 again the flag of lane 0 is set ({flags:#x})")
    e.btn(0); e.knob(0, 1); e.knob(0, -1)
    check(not e.r32(AR.RAM) & 1, f"Synth 1's macro 1 turned by hand: the flag cleared ({e.r32(AR.RAM):#x})")
    # MIDI 1, engine on: lane 4 = FILT
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    row = bytes(e.uc.mem_read(e.r0(e.vl["c_vrow"], 0), 8)); code = row[4]
    v0 = e.val(0, code)
    lane(2, 4, 2, 120); mark(2, 5)
    u0 = e.r0(e.vl["c_vtou"], code, v0 & 0xFFFFFFFF)
    vals = []
    for s in (2, 3, 5):
        step(2, s); vals.append(store(2, 4))
    step(2, 2); fl = e.r32(AR.RAM) & (1 << 20)
    e.btn(2); e.btn(8); e.pad(3); e.knob(4, 1)                                             # page 4, K5 = lane 4
    check(fl and not e.r32(AR.RAM) & (1 << 20), f"MIDI 1, K5 of page 4 turned by hand: lane 4's flag cleared ({fl:#x} -> {e.r32(AR.RAM) & (1 << 20):#x})")
    check(vals == [120, 120, u0], f"MIDI 1, lane 4 (code {code}, value {v0} = lane value {u0}): the macro store at steps 2 / 3 / 5 = {vals} (back at the mark; "
          "the store reaches the engine through vcf21's c_vplay, which the emulation does not run from a commit)")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
