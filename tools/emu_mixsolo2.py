"""SC50.9 / Beta 5.12: solo and solo flip in the Mixer (mixsolo v2), through the controller and the real LED task:
  * solo: pad 16 held + pads 1 / 3 = only those sound, pad 16 white while it is on; pad 16 again + pad 6 = only that one; pad 16 tapped alone = the mutes
    from before the solo (a manual mute included);
  * flip: pad 16 tapped alone = flip, orange; pads held = only those sound, one let go = the others still, the last let go = the mixer as it was;
    pad 16 + a pad in flip = solo; pad 16 tapped in flip = off, dim;
  * with Shift the row is the repeats'; on Master FX it is not ours; the end of «apply session» goes through c_soload, which turns either mode off.

    python tools/emu_mixsolo2.py NEW.bin NEW_manifest.json
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_mixsolo as EM  # noqa: E402
import mixsolo as M  # noqa: E402
import persist19 as P19  # noqa: E402
from thumb import b_w  # noqa: E402


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    lab = {k: int(v, 16) for k, v in man["report"]["mixsolo2"]["labels"].items()}
    e = EM.P(img, man); e.btn(14)
    led = lambda: e.frame()[M.PAD_SOLO] & 0xFF
    def tap16(): e.press(M.PAD_SOLO); e.release(M.PAD_SOLO); e.frame()
    e.tap(3); base = e.muted()
    check(base == [0, 0, 0, 1, 0, 0, 0, 0], f"a manual mute on MIDI 2 ({base})")
    check(led() == M.COL_DIM, "pad 16 dim")
    # ---- solo
    e.press(M.PAD_SOLO); e.tap(0); e.tap(2); e.release(M.PAD_SOLO); l1 = led(); a = e.muted()
    check(a == [0, 1, 0, 1, 1, 1, 1, 1], f"pad 16 + pads 1 / 3: only Synth 1 and MIDI 1 ({a})")
    check(l1 == M.COL_ON, f"solo on: pad 16 white ({l1:#x})")
    e.press(M.PAD_SOLO); e.tap(5); e.release(M.PAD_SOLO); b = e.muted(); l2 = led()
    check(b == [1, 1, 1, 1, 1, 0, 1, 1] and l2 == M.COL_ON, f"pad 16 again + pad 6: only Drum 2, still solo ({b}, {l2:#x})")
    tap16(); c = e.muted(); l3 = led()
    check(c == base and l3 == M.COL_DIM, f"pad 16 tapped: the mutes from before the solo ({c}, {l3:#x})")
    # ---- flip
    tap16(); l4 = led(); d = e.muted()
    check(l4 == M.COL_FLIP and d == base, f"pad 16 tapped alone: flip, orange, nothing changes yet ({l4:#x}, {d})")
    e.press(1); e.frame(); f1 = e.muted()
    check(f1 == [1, 0, 1, 1, 1, 1, 1, 1], f"flip, pad 2 held: only Synth 2 ({f1})")
    e.press(6); e.frame(); f2 = e.muted()
    check(f2 == [1, 0, 1, 1, 1, 1, 0, 1], f"+ pad 7 held: Synth 2 and Drum 3 ({f2})")
    e.release(1); e.frame(); f3 = e.muted()
    check(f3 == [1, 1, 1, 1, 1, 1, 0, 1], f"pad 2 let go: Drum 3 alone ({f3})")
    e.release(6); e.frame(); f4 = e.muted()
    check(f4 == base, f"the last let go: the mixer as it was ({f4})")
    e.press(3); e.frame(); f5 = e.muted(); e.release(3); e.frame(); f6 = e.muted()
    check(f5 == [1, 1, 1, 0, 1, 1, 1, 1] and f6 == base, f"a muted track held in flip sounds alone, then back ({f5}, {f6})")
    check(led() == M.COL_FLIP, "still flip")
    # ---- flip -> solo, then off
    e.press(M.PAD_SOLO); e.tap(2); e.release(M.PAD_SOLO); g = e.muted(); l5 = led()
    check(g == [1, 1, 0, 1, 1, 1, 1, 1] and l5 == M.COL_ON, f"flip + pad 16 + pad 3: solo of MIDI 1, white ({g}, {l5:#x})")
    tap16(); h_ = e.muted()
    check(h_ == base and led() == M.COL_DIM, f"pad 16 tapped: back from the solo ({h_})")
    tap16(); tap16(); i_ = e.muted()
    check(i_ == base and led() == M.COL_DIM, f"flip on and off again: nothing changes ({i_})")
    # ---- Shift, Master FX
    fs = e.frame(shift=True)[M.PAD_SOLO] & 0xFF
    check(fs not in (M.COL_DIM, M.COL_ON, M.COL_FLIP) or fs == 0x2D, f"with Shift: the repeats' row ({fs:#x})")
    tap16(); e.btn(14); m0 = e.muted(); e.press(0); m1 = e.muted(); e.release(0); e.frame()
    check(m0 == m1, f"Master FX page: its pads, not the flip ({m0}, {m1})")
    e.btn(14); check(led() == M.COL_FLIP, "back to the Mixer: still flip")
    # ---- a project load turns it off
    w = bytes(e.uc.mem_read(P19.LOAD_END, 4))
    check(w == b_w(P19.LOAD_END, lab["c_soload"]), "the end of «apply session» goes through c_soload")
    e.press(1); e.frame()
    st = M.RAM2
    e.r0(lab["c_soload"]) if False else None
    sp = 0x2004FF00
    e.uc.mem_write(st + 4, bytes([2]))                           # flip, a pad held
    e.uc.mem_write(st + 7, bytes([2]))
    pre = e.muted()
    e.uc.reg_write(e.uc_const.UC_ARM_REG_SP, sp) if hasattr(e, "uc_const") else None
    # run c_soload's body up to its b.w (its own code only)
    import unicorn.arm_const as A
    e.uc.reg_write(A.UC_ARM_REG_SP, sp); e.uc.reg_write(A.UC_ARM_REG_LR, 0x0807FFFD)
    e.uc.emu_start(lab["c_soload"] | 1, lab["c_soload"] + 22, count=200)
    s = bytes(e.uc.mem_read(st + 4, 4))
    check(s[0] == 0 and s[3] == 0 and e.muted() == pre, f"c_soload: mode off, nothing restored ({list(s)}, {e.muted()})")
    e.release(1); e.frame()
    check(e.muted() == pre and led() == M.COL_DIM, f"after the load the pad let go changes nothing ({e.muted()})")
    print(f"{man.get('marker', '?')} MIXSOLO2 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
