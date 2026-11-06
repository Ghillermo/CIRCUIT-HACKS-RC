"""SC52.6 / Beta 5.29 (janko.use_v4): in the expanded Note view, keys held in rows 2 and 4 = Octave moves rows 1 and 3; through the controller and the
real LED task (emu_sc46_3's harness).

    python tools/emu_janko4.py BUILD.bin manifest.json

  * keys held in rows 2 and 4, Octave up: rows 1 / 3 + 1, rows 2 / 4 stay; the links follow (each joins two pads with the same note);
  * held 450 ms (Octave down): rows 1 / 3 an octave below the press, rows 2 / 4 stay;
  * keys in row 1 and row 4: nothing moves (as before: keys of both pairs);
  * a key of one pair only: the other pair, rows 1 / 3 keep their own offset inside it.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc46_3 as T  # noqa: E402
import emu_janko2 as J2  # noqa: E402
import cscale as CS  # noqa: E402
import janko as J  # noqa: E402

MGR = T.MGR
BTN_PRESS, BTN_REL = 0x08033320, 0x0803381A


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = T.E(Path(img).read_bytes(), man)
    e.btn(0); J2.editor_pad(e, J.PAD_JK); e.btn(0); e.goto(6); e.frame()
    rows = lambda: [[e.val(8 * k + c) for c in range(8)] for k in range(4)]
    first = lambda: [x[0] for x in rows()]
    def links():
        bad = []
        for p in range(32):
            i = e.idx(p); ln = e.r8(CS.KB + 0x180 + i)
            if ln != 0xFF and e.r8(CS.KB + 0x14 + ln) != e.r8(CS.KB + 0x14 + i): bad.append(p)
        return bad, sum(1 for p in range(32) if e.r8(CS.KB + 0x180 + e.idx(p)) != 0xFF)
    r0 = first()
    check(r0 == [59, 60, 59, 60], f"start: rows 1-4 from {r0}")
    e.press(8); e.press(24); e.at(300000); e.btn(J.ID_UP); e.frame(); r = rows(); e.release(8); e.release(24); e.frame()
    check([x[0] for x in r] == [60, 60, 60, 60] and r[0] == r[2] and r[1] == r[3], f"keys in rows 2 / 4, Octave up: rows 1 / 3 + 1 ({[x[0] for x in r]})")
    bad, n = links()
    check(not bad and n > 0, f"the links follow ({n} links, wrong {bad})")
    e.press(8); e.press(24); e.at(301000); e.call(BTN_PRESS, MGR, J.ID_DOWN, maxins=8_000_000); e.frame(); a = first()
    e.at(301450); e.frame(); b = first(); e.call(BTN_REL, MGR, J.ID_DOWN, maxins=8_000_000); e.at(302000); e.frame(); c_ = first()
    e.release(8); e.release(24); e.frame()
    check(a == [59, 60, 59, 60] and b == [48, 60, 48, 60] and c_ == b, f"held 450 ms: rows 1 / 3 - 12 from the press ({a}, {b}, {c_})")
    e.press(0); e.press(24); e.at(303000); e.btn(J.ID_UP); e.frame(); r = first(); e.release(0); e.release(24); e.frame()
    check(r == b, f"keys in rows 1 and 4: nothing moves ({r})")
    e.press(24); e.at(304000); e.btn(J.ID_UP); e.frame(); r = first(); e.release(24); e.frame()
    check(r == [49, 61, 48, 60], f"a key of the lower pair: the upper pair + 1, row 1 keeps its offset ({r})")
    del e; gc.collect()
    print(f"{Path(img).stem} JANKO4 RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text())) else 0)
