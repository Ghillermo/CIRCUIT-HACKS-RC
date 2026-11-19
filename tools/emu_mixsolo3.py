"""A7PROT (tools/mixsolo3.py): the Mixer's pads 15 / 16, through the controller and the real LED task.
  * pad 16 solo as before (held + pads = those alone, white; tapped = the mutes before);
  * pad 16 tapped alone = mute flip (orange): a held track flips its mute while held, the others stay; let go = back;
  * pad 15 tapped = the group (white): first pad = its solo, more pads in / out, the last out = all muted; tapped again = the mutes before, dim;
  * pad 15 held + pads = solo flip (only those, while held); pad 15 let go = the mixer as it was, the group not toggled;
  * the modes exclude each other; a project load (c_s3load) leaves them.

    python tools/emu_mixsolo3.py NEW.bin NEW_manifest.json
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_mixsolo as EM  # noqa: E402
import mixsolo3 as M3  # noqa: E402


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    lab = {k: int(v, 16) for k, v in man["report"]["mixsolo3"]["labels"].items()}
    e = EM.P(img, man); e.btn(14)
    S, G = M3.PAD_SOLO, M3.PAD_GRP
    def led(p): return e.frame()[p] & 0xFF
    def tap(p): e.press(p); e.release(p); e.frame()
    e.tap(3); base = e.muted()
    check(base == [0, 0, 0, 1, 0, 0, 0, 0], f"a manual mute on MIDI 2 ({base})")
    check(led(S) == M3.COL_DIM and led(G) == M3.COL_DIM, "pads 15 / 16 dim")
    # ---- pad 16 solo as before
    e.press(S); e.tap(0); e.tap(2); e.release(S); a = e.muted()
    check(a == [0, 1, 0, 1, 1, 1, 1, 1] and led(S) == M3.COL_ON, f"pad 16 + pads 1 / 3: solo, white ({a})")
    tap(S); check(e.muted() == base and led(S) == M3.COL_DIM, f"pad 16 tapped: the mutes before ({e.muted()})")
    # ---- pad 16 mute flip
    tap(S); check(led(S) == M3.COL_FLIP and e.muted() == base, "pad 16 tapped alone: mute flip, orange, nothing yet")
    e.press(1); e.frame(); f1 = e.muted()
    check(f1 == [0, 1, 0, 1, 0, 0, 0, 0], f"pad 2 held: Synth 2 muted, the rest as they were ({f1})")
    e.press(3); e.frame(); f2 = e.muted()
    check(f2 == [0, 1, 0, 0, 0, 0, 0, 0], f"+ pad 4 held: MIDI 2 (muted) sounds ({f2})")
    e.release(1); e.frame(); f3 = e.muted()
    check(f3 == [0, 0, 0, 0, 0, 0, 0, 0], f"pad 2 let go: Synth 2 back, MIDI 2 still flipped ({f3})")
    e.release(3); e.frame(); f4 = e.muted()
    check(f4 == base, f"pad 4 let go: the mixer as it was ({f4})")
    tap(S); check(led(S) == M3.COL_DIM and e.muted() == base, "pad 16 tapped: mute flip off")
    # ---- pad 15 group
    tap(G); g0 = e.muted()
    check(led(G) == M3.COL_ON and g0 == base, f"pad 15 tapped: group, white, nothing yet ({g0})")
    e.tap(5); g1 = e.muted()
    check(g1 == [1, 1, 1, 1, 1, 0, 1, 1], f"pad 6: Drum 2 solo ({g1})")
    e.tap(0); g2 = e.muted()
    check(g2 == [0, 1, 1, 1, 1, 0, 1, 1], f"pad 1: Synth 1 added ({g2})")
    e.tap(5); g3 = e.muted()
    check(g3 == [0, 1, 1, 1, 1, 1, 1, 1], f"pad 6 again: Drum 2 out ({g3})")
    e.tap(0); g4 = e.muted()
    check(g4 == [1] * 8, f"the last out: everything muted ({g4})")
    e.tap(2); g5 = e.muted()
    check(g5 == [1, 1, 0, 1, 1, 1, 1, 1] and led(G) == M3.COL_ON, f"pad 3: MIDI 1 alone, still group ({g5})")
    tap(G); g6 = e.muted()
    check(g6 == base and led(G) == M3.COL_DIM, f"pad 15 tapped: the mutes before, dim ({g6})")
    # ---- pad 15 held: solo flip
    e.press(G); e.frame(); lh = led(G)
    e.press(1); e.frame(); h1 = e.muted()
    check(lh == M3.COL_ON and h1 == [1, 0, 1, 1, 1, 1, 1, 1], f"pad 15 held + pad 2: Synth 2 alone ({h1})")
    e.press(6); e.frame(); h2 = e.muted()
    check(h2 == [1, 0, 1, 1, 1, 1, 0, 1], f"+ pad 7: Synth 2 and Drum 3 ({h2})")
    e.release(1); e.frame(); h3 = e.muted()
    check(h3 == [1, 1, 1, 1, 1, 1, 0, 1], f"pad 2 let go: Drum 3 alone ({h3})")
    e.release(G); e.frame(); h4 = e.muted()
    check(h4 == base and led(G) == M3.COL_DIM, f"pad 15 let go: the mixer as it was, no group ({h4})")
    e.release(6); e.frame(); h5 = e.muted()
    check(h5 == base, f"pad 7 let go afterwards: nothing changes ({h5})")
    e.press(G); e.press(4); e.frame(); e.release(4); e.frame(); h6 = e.muted(); e.release(G); e.frame()
    check(h6 == base and e.muted() == base and led(G) == M3.COL_DIM, f"pad 15 + a pad, let go in order: as it was, no group ({e.muted()})")
    # ---- the group's flip, then the group comes back
    tap(G); e.tap(0); gb = e.muted()
    e.press(G); e.press(7); e.frame(); gf = e.muted(); e.release(7); e.frame(); gr = e.muted(); e.release(G); e.frame()
    check(gf == [1, 1, 1, 1, 1, 1, 1, 0] and gr == gb and e.muted() == gb and led(G) == M3.COL_ON,
          f"in the group, pad 15 held + pad 8: Drum 4 alone, then the group again, still on ({gf}, {e.muted()})")
    # ---- modes exclude each other
    e.press(S); e.tap(4); e.release(S); x1 = e.muted()
    check(x1 == [1, 1, 1, 1, 0, 1, 1, 1] and led(S) == M3.COL_ON and led(G) == M3.COL_DIM, f"pad 16 solo from the group: Drum 1, group off ({x1})")
    tap(S); x2 = e.muted()
    check(x2 == base, f"pad 16 tapped: the mutes from before the group ({x2})")
    tap(S); tap(G); x3 = e.muted()
    check(led(S) == M3.COL_DIM and led(G) == M3.COL_ON and x3 == base, "pad 15 from the mute flip: group on, mute flip off")
    tap(G)
    # ---- Shift, Master FX
    fs = e.frame(shift=True)[G] & 0xFF
    check(fs not in (M3.COL_DIM, M3.COL_ON), f"with Shift: the repeats' row ({fs:#x})")
    tap(G); e.btn(14); m0 = e.muted(); e.press(0); m1 = e.muted(); e.release(0); e.frame()
    check(m0 == m1, f"Master FX page: its pads ({m0}, {m1})")
    e.btn(14); check(led(G) == M3.COL_ON, "back to the Mixer: still group")
    # ---- a load leaves every mode
    import unicorn.arm_const as A
    e.tap(1); pre = e.muted()
    e.uc.reg_write(A.UC_ARM_REG_SP, 0x2004FF00); e.uc.reg_write(A.UC_ARM_REG_LR, 0x0807FFFD)
    end = lab["c_s3load"] + len(bytes(e.uc.mem_read(lab["c_s3load"], 64)).split(b"\xbd\xe8")[0]) + 4      # up to its pop.w
    e.uc.emu_start(lab["c_s3load"] | 1, end, count=200)
    s = bytes(e.uc.mem_read(M3.RAM + 4, 9))
    check(s[0] == 0 and s[8] == 0 and e.muted() == pre and led(G) == M3.COL_DIM, f"c_s3load: modes off, nothing restored ({list(s)}, {e.muted()})")
    print(f"{man.get('marker', '?')} MIXSOLO3 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
