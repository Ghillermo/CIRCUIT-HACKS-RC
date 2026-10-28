"""SC48.4 / Beta 3.41: the chord screen (chords.use_live / use_slatch, latchclr.use_chords), through the controller and the real LED task
(emu_sc46_3's harness: the track view's live note-on / off caught):
  * a root held, the type changed (major -> minor): at once only the third goes (off) and the new one comes (on); the inversion (1st): the root
    off, the root an octave up on; the root let go: the three notes off;
  * Shift + a root: its chord on, the release ignored; with Shift its root pad bright cyan (0x4D), without Shift not; the type changed: the
    latched chord follows; the same root again: its notes off, nothing on, the release nothing;
  * latched again, then Clear + Synth 1: its notes off.

    python tools/emu_chlive.py SC48.4.bin SC48.4_manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc46_3 as T  # noqa: E402
import chords as CH  # noqa: E402

BTN, BTN_REL, CLEAR = 0x08033320, 0x0803381A, 23
ROOT = 24


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = T.E(img, man)
    e.btn(0); e.goto(6); e.tap(CH.PAD_TOG, shift=True)
    r = e.val(ROOT)
    on = lambda: sorted(n for n, v, p in e.ons)
    off = lambda: sorted(n for n, p in e.offs)
    def clr(): e.ons.clear(); e.offs.clear()
    clr(); e.press(ROOT); held = on()
    check(held == [r, r + 4, r + 7], f"root {r} held: major ({held})")
    clr(); e.tap(1); a = (off(), on())
    check(a == ([r + 4], [r + 3]), f"minor while held: the third off, the minor third on at once {a}")
    clr(); e.tap(9); b = (off(), on())
    check(b == ([r], [r + 12]), f"1st inversion while held: the root off, an octave up on {b}")
    clr(); e.release(ROOT); c = off()
    check(c == [r + 3, r + 7, r + 12], f"the root let go: its notes off ({c})")
    e.tap(9)                                                                           # back to root position, nothing held
    clr(); e.press(ROOT, shift=True); e.release(ROOT); d = (on(), off())
    check(d == ([r, r + 3, r + 7], []), f"Shift + root: the minor chord on, the release ignored {d}")
    fs, f0 = e.frame(shift=True), e.frame()
    check(fs[ROOT] & 0xFF == CH.COL_SLAT and f0[ROOT] & 0xFF != CH.COL_SLAT, f"its root pad: cyan with Shift, not without ({fs[ROOT]:#x}, {f0[ROOT]:#x})")
    clr(); e.tap(0); g = (off(), on())
    check(g == ([r + 3], [r + 4]), f"major: the latched chord follows {g}")
    clr(); e.press(ROOT); p1 = (off(), on()); e.release(ROOT); p2 = (off(), on())
    check(p1 == ([r, r + 4, r + 7], []) and p2 == ([r, r + 4, r + 7], []), f"the root again: its notes off, nothing on; the release nothing ({p1}, {p2})")
    clr(); e.press(ROOT, shift=True); e.release(ROOT)
    e.call(BTN, T.MGR, CLEAR, maxins=8_000_000); clr(); e.call(BTN, T.MGR, 0, maxins=8_000_000); cl = off()
    e.call(BTN_REL, T.MGR, 0, maxins=8_000_000); e.call(BTN_REL, T.MGR, CLEAR, maxins=8_000_000)
    check(cl == [r, r + 4, r + 7], f"latched again, Clear + Synth 1: its notes off ({cl})")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} CHLIVE RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
