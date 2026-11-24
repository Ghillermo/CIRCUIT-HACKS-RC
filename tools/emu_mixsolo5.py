"""Alpha 7.45 (tools/mixsolo5.py; as 7.44, flip on top of a solo): the Mixer's pads 15 / 16, through the controller and the real LED task.
  * pad 16 tapped = solo armed (white, nothing yet); track taps = in / out of the group (alone); the group emptied = the saved mutes; pad 16 again = off;
  * pad 16 held + pads = the group anew (also while a solo is on);
  * pad 15 tapped = flip on (orange): a held track flips muted <-> sounding while held; pad 15 again = off;
  * the modes exclude each other; a project load (c_s5load) leaves them.

    python tools/emu_mixsolo5.py firmware/a7.44
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_mixsolo as EM  # noqa: E402
import mixsolo5 as M5  # noqa: E402


def main(d):
    img = next(Path(d).glob("*.bin")).read_bytes(); man = json.loads((Path(d) / "manifest.json").read_text())
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    lab = {k: int(v, 16) for k, v in man["report"]["mixsolo5"]["labels"].items()}
    e = EM.P(img, man); e.btn(14)
    S, F = M5.PAD_SOLO, M5.PAD_FLIP
    def led(p): return e.frame()[p] & 0xFF
    def tap(p): e.press(p); e.release(p); e.frame()
    e.tap(3); base = e.muted()
    check(base == [0, 0, 0, 1, 0, 0, 0, 0], f"a manual mute on MIDI 2 ({base})")
    check(led(S) == M5.COL_DIM and led(F) == M5.COL_DIM, "pads 15 / 16 dim")
    # ---- pad 16 tapped: armed, then track taps
    tap(S); a0 = e.muted()
    check(led(S) == M5.COL_ON and a0 == base, f"pad 16 tapped: armed, white, nothing yet ({a0})")
    e.tap(5); a1 = e.muted()
    check(a1 == [1, 1, 1, 1, 1, 0, 1, 1], f"pad 6: Drum 2 alone ({a1})")
    e.tap(0); a2 = e.muted()
    check(a2 == [0, 1, 1, 1, 1, 0, 1, 1], f"pad 1: Synth 1 added ({a2})")
    e.tap(5); e.tap(0); a3 = e.muted()
    check(a3 == base and led(S) == M5.COL_ON, f"both out: the saved mutes, still armed ({a3})")
    e.tap(2); a4 = e.muted()
    check(a4 == [1, 1, 0, 1, 1, 1, 1, 1], f"pad 3: MIDI 1 alone ({a4})")
    tap(S); a5 = e.muted()
    check(a5 == base and led(S) == M5.COL_DIM, f"pad 16 tapped again: the mutes before, dim ({a5})")
    # ---- pad 16 held + pads: the group anew
    e.press(S); e.tap(0); e.tap(2); e.release(S); e.frame(); h1 = e.muted()
    check(h1 == [0, 1, 0, 1, 1, 1, 1, 1] and led(S) == M5.COL_ON, f"pad 16 held + pads 1 / 3: those two, solo stays on ({h1})")
    e.press(S); e.tap(7); e.release(S); e.frame(); h2 = e.muted()
    check(h2 == [1, 1, 1, 1, 1, 1, 1, 0] and led(S) == M5.COL_ON, f"held again + pad 8: the group redone = Drum 4 ({h2})")
    e.tap(0); h3 = e.muted()
    check(h3 == [0, 1, 1, 1, 1, 1, 1, 0], f"a tap adds Synth 1 ({h3})")
    tap(S); check(e.muted() == base, f"pad 16: off, the mutes before ({e.muted()})")
    # ---- pad 15: flip
    tap(F); check(led(F) == M5.COL_FLIP and e.muted() == base, "pad 15 tapped: flip on, orange, nothing yet")
    e.press(1); e.frame(); f1 = e.muted()
    check(f1 == [0, 1, 0, 1, 0, 0, 0, 0], f"pad 2 held: Synth 2 muted ({f1})")
    e.press(3); e.frame(); f2 = e.muted()
    check(f2 == [0, 1, 0, 0, 0, 0, 0, 0], f"+ pad 4 held: MIDI 2 sounds ({f2})")
    e.release(1); e.frame(); e.release(3); e.frame(); f3 = e.muted()
    check(f3 == base, f"let go: the mixer as it was ({f3})")
    tap(F); check(led(F) == M5.COL_DIM and e.muted() == base, "pad 15 tapped: flip off")
    # ---- pad 16 held + pads, with LED frames in between (as on the device)
    e.press(S); e.frame(); e.frame(); e.press(6); e.frame(); e.release(6); e.frame(); e.press(1); e.frame(); e.release(1); e.frame()
    d1 = e.muted(); e.release(S); e.frame(); e.frame(); d2 = e.muted()
    check(d1 == [1, 0, 1, 1, 1, 1, 0, 1] and d2 == d1 and led(S) == M5.COL_ON, f"held with frames + pads 7 / 2: those alone, solo on after letting go ({d1}, {d2})")
    # ---- flip on top of the solo
    tap(F); o1 = e.muted()
    check(led(F) == M5.COL_FLIP and led(S) == M5.COL_ON and o1 == d1, f"pad 15 with the solo on: flip on, solo stays ({o1})")
    e.press(1); e.frame(); o2 = e.muted()
    check(o2 == [1, 1, 1, 1, 1, 1, 0, 1], f"pad 2 held: Synth 2 (in the solo) muted ({o2})")
    e.press(0); e.frame(); o3 = e.muted()
    check(o3 == [0, 1, 1, 1, 1, 1, 0, 1], f"+ pad 1 held: Synth 1 (muted by the solo) sounds ({o3})")
    e.release(1); e.frame(); e.release(0); e.frame(); o4 = e.muted()
    check(o4 == d1, f"let go: the solo as it was ({o4})")
    tap(F); check(led(F) == M5.COL_DIM and led(S) == M5.COL_ON and e.muted() == d1, "pad 15 again: flip off, solo stays")
    tap(F); tap(S); o5 = e.muted()
    check(o5 == base and led(F) == M5.COL_FLIP and led(S) == M5.COL_DIM, f"pad 16 with flip on: solo off, flip stays ({o5})")
    e.press(2); e.frame(); o6 = e.muted(); e.release(2); e.frame()
    check(o6 == [0, 0, 1, 1, 0, 0, 0, 0] and e.muted() == base, f"flip without solo: pad 3 held mutes MIDI 1 ({o6})")
    tap(F)
    # ---- Shift, Master FX
    fs = e.frame(shift=True)[F] & 0xFF
    check(fs not in (M5.COL_DIM, M5.COL_FLIP), f"with Shift: the repeats' row ({fs:#x})")
    tap(S); e.btn(14); m0 = e.muted(); e.press(0); m1 = e.muted(); e.release(0); e.frame()
    check(m0 == m1, f"Master FX page: its pads ({m0}, {m1})")
    e.btn(14); check(led(S) == M5.COL_ON, "back to the Mixer: still solo")
    # ---- a load leaves every mode
    import unicorn.arm_const as A
    e.tap(1); pre = e.muted()
    e.uc.reg_write(A.UC_ARM_REG_SP, 0x2004FF00); e.uc.reg_write(A.UC_ARM_REG_LR, 0x0807FFFD)
    end = lab["c_s5load"] + len(bytes(e.uc.mem_read(lab["c_s5load"], 64)).split(b"\xbd\xe8")[0]) + 4
    e.uc.emu_start(lab["c_s5load"] | 1, end, count=200)
    s = bytes(e.uc.mem_read(M5.RAM + 4, 9))
    check(s[0] == 0 and s[8] == 0 and e.muted() == pre and led(S) == M5.COL_DIM, f"c_s5load: modes off, nothing restored ({list(s)}, {e.muted()})")
    print(f"{man.get('marker', '?')} MIXSOLO5 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1]) else 0)
