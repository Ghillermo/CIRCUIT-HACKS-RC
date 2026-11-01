"""SC49.9 / Beta 5.2 (janko.use_v3): one Jankó layout on Shift + pad 8, the upper pair of rows repeating the lower one, and Octave with a key held moving
only the other pair; through the controller and the real LED task (emu_sc46_3's harness).

    python tools/emu_janko3.py BUILD.bin manifest.json

  * the editor: Shift + pad 8 = on (B_ON 3, pad 8 cyan); Shift + pad 24 changes nothing and pad 24 stays dark; Shift + pad 8 again = off (the stock's
    tables back); a project saved with B_ON 2 (the first layout) plays the same layout;
  * the layout: bottom row = 60 + 2 c, the row above = 59 + 2 c, rows 1-2 = rows 3-4; each pad of the lower pair linked to the same note above;
    the root's colour on 60 / 72 in both pairs;
  * Octave with no key held: both pairs + 1; in the 2-row Note view with a key held too; held 450 ms: both + 12 from the press;
  * the expanded view with a key of the lower pair held: only the upper pair moves, the held note sounds on and its note-off is its own; with a key of
    the upper pair held: only the lower one; keys of both: nothing, and the stock's octave stays; the long press: the other pair an octave from the
    press, the release of a short one nothing more;
  * after a move the links follow (every link joins two pads with the same note, with an odd offset across the rows too);
  * the chord screen: a root held + Octave = both pairs (its rows 1-2 are not keys).
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc46_3 as T  # noqa: E402
import emu_janko2 as J2  # noqa: E402
import cscale as CS  # noqa: E402
import janko as J  # noqa: E402

MGR, V0 = T.MGR, T.V0
BTN_PRESS, BTN_REL = 0x08033320, 0x0803381A


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = T.E(Path(img).read_bytes(), man)
    lab = {k: int(v, 16) for k, v in man["report"]["janko"]["labels"].items()}
    e.btn(0); t0 = e.tables()
    oct0 = e.r0(lab["c_jkoct"], 0)
    J2.editor_pad(e, J.PAD_JK); e.frame(); led = e.scales_leds()
    check(e.on() == J.JK3 and led[J.PAD_JK] == J.COL_ON and led[J.PAD_JK2] == 0, f"Shift + pad 8 = on (B_ON {e.on()}, pad 8 {led[J.PAD_JK]:#x}, pad 24 {led[J.PAD_JK2]:#x})")
    e.btn(0); e.frame(); J2.editor_pad(e, J.PAD_JK2); e.frame(); led = e.scales_leds()
    check(e.on() == J.JK3 and led[J.PAD_JK2] == 0, f"Shift + pad 24: nothing (B_ON {e.on()}, pad 24 {led[J.PAD_JK2]:#x})")
    e.btn(0); e.goto(6); e.frame()
    rows = lambda: [[e.val(8 * k + c) for c in range(8)] for k in range(4)]
    r = rows()
    check(r[3] == [60 + 2 * c for c in range(8)] and r[2] == [59 + 2 * c for c in range(8)] and r[1] == r[3] and r[0] == r[2],
          f"the layout: rows 3-4 from 59 / 60, rows 1-2 the same ({[x[0] for x in r]})")
    def links():
        bad = []
        for p in range(32):
            i = e.idx(p); ln = e.r8(CS.KB + 0x180 + i)
            if ln != 0xFF and e.r8(CS.KB + 0x14 + ln) != e.r8(CS.KB + 0x14 + i): bad.append(p)
        return bad, sum(1 for p in range(32) if e.r8(CS.KB + 0x180 + e.idx(p)) != 0xFF)
    bad, n = links()
    check(not bad and n == 32, f"each pad linked to the same note in the other pair ({n} links, wrong {bad})")
    st = {p: J2.state(e, p) for p in (24, 30, 8, 14, 25, 16)}
    check(all(st[p] in (5, 6) for p in (24, 30, 8, 14)) and st[25] in (0, 3) and st[16] in (0, 3), f"the root's colour on 60 / 72 in both pairs ({st})")
    # no key held: both
    e.at(200000); e.btn(J.ID_UP); e.frame(); r = rows()
    check(r[3][0] == 61 and r[1][0] == 61 and r[2][0] == 60 and r[0][0] == 60, f"Octave up, no key held: both pairs + 1 ({[x[0] for x in r]})")
    e.at(201000); e.btn(J.ID_DOWN); e.frame()
    # a key of the lower pair held: the upper pair moves
    e.ons.clear(); e.press(24); n24 = e.ons[-1][0] if e.ons else None
    e.at(202000); e.btn(J.ID_UP); e.frame(); r = rows()
    check(n24 == 60 and r[3][0] == 60 and r[2][0] == 59 and r[1][0] == 61 and r[0][0] == 60, f"a key of the lower pair held, Octave up: only the upper pair + 1 ({[x[0] for x in r]})")
    bad, n = links()
    check(not bad and n > 0, f"the links follow with an odd offset ({n} links, wrong {bad})")
    e.release(24); e.frame()
    # a key of the upper pair held: the lower pair moves
    e.press(8); e.at(203000); e.btn(J.ID_UP); e.frame(); r = rows()
    check(r[3][0] == 61 and r[2][0] == 60 and r[1][0] == 61 and r[0][0] == 60, f"a key of the upper pair held, Octave up: only the lower pair + 1 ({[x[0] for x in r]})")
    # keys of both: nothing
    e.press(24); e.at(204000); e.btn(J.ID_UP); e.frame(); r2 = rows()
    check(r2 == r and e.r0(lab["c_jkoct"], 0) == oct0, f"keys of both pairs held: nothing moves ({[x[0] for x in r2]}), the stock's octave kept")
    e.release(8); e.release(24); e.frame()
    # the long press with a key held
    e.press(24); e.at(205000); e.call(BTN_PRESS, MGR, J.ID_DOWN, maxins=8_000_000); e.frame(); a = rows()
    e.at(205450); e.frame(); b = rows(); e.call(BTN_REL, MGR, J.ID_DOWN, maxins=8_000_000); e.at(206000); e.frame(); c_ = rows(); e.release(24); e.frame()
    check(a[1][0] == 60 and b[1][0] == 49 and c_[1][0] == 49 and b[3][0] == 61,
          f"held 450 ms with a key of the lower pair: the upper pair - 12 from the press, the lower stays ({a[1][0]}, {b[1][0]}, {c_[1][0]}, {b[3][0]})")
    # the 2-row Note view: both, with a key held
    e.goto(1); e.frame(); e.press(24); e.at(207000); e.btn(J.ID_UP); e.frame(); e.release(24); e.goto(6); e.frame(); r = rows()
    check(r[3][0] == 62 and r[1][0] == 50, f"the 2-row Note view with a key held: both pairs ({r[3][0]}, {r[1][0]})")
    # the chord screen: both
    e.press(7, shift=True); e.release(7); e.frame(); e.press(24); e.at(208000); e.btn(J.ID_UP); e.frame(); e.release(24)
    e.press(7, shift=True); e.release(7); e.frame(); r = rows()
    check(r[3][0] == 63 and r[1][0] == 51, f"the chord screen, a root held: both pairs ({r[3][0]}, {r[1][0]})")
    # a project saved with the first layout
    blk = e.r0(int(man["report"]["cscale"]["labels"]["c_csblk"], 16))
    b0 = list(e.uc.mem_read(blk, 12))
    e.uc.mem_write(blk + CS.B_ON, bytes([J.JK])); e.uc.mem_write(blk + CS.B_SUM, bytes([e.r8(blk + CS.B_SUM) ^ J.JK ^ J.JK3])); e.frame(); r = rows()
    check(e.on() == J.JK and r[2][0] + 1 == r[3][0], f"B_ON 2 (the first layout): this layout ({[x[0] for x in r]})")
    e.uc.mem_write(blk, bytes(b0)); e.frame()
    J2.editor_pad(e, J.PAD_JK); e.btn(0); e.goto(1); e.frame()
    check(e.on() in (0, 1) and e.tables() == t0, f"Shift + pad 8 again: off (B_ON {e.on()}), the stock's tables back")
    del e; gc.collect()
    print(f"{Path(img).stem} JANKO3 RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text())) else 0)
