"""SC48.2 / Beta 3.39 (janko.use_v2): the two Jankó layouts, the root's colour and the long Octave press; through the controller and the real
LED task (emu_sc46_3's harness).

    python tools/emu_janko2.py BUILD.bin manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]

  * the editor (Shift + Scales): Shift + pad 8 = the new layout (B_ON 3; pad 8 cyan, pad 24 off); Shift + pad 24 = the old one (B_ON 2), from the
    new one at once; the same pad again = off (the stock's tables back);
  * the new layout, the Note view: the bottom row = 60 + 2 c, the row above = 59 + 2 c (a semitone lower); the expanded view: the third row =
    72 + 2 c, the top row = 71 + 2 c; the links (R, 6 / 7) <-> (R - 2, 0 / 1), both the same notes;
  * the old layout: the bottom row 60 + 2 c, the row above 61 + 2 c (as SC46.3);
  * the root's colour (0x0804AD78, the stock's colour of a pad): with either layout the pads whose note is the root (60, 72) in the root's state
    (5 / 6), the others (59, 62, a linked 63 of the old layout) not;
  * Octave: a short press = + / - 1 semitone; held 400 ms (the LED task) = an octave from where it started (+ 12 / - 12), nothing more at the
    release; released before = only the semitone (no jump later); the stock's octave kept;
  * the previous build: Shift + pad 24 in the editor does not switch the old layout on.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc46_3 as T  # noqa: E402
import cscale as CS  # noqa: E402
import janko as J  # noqa: E402

MGR, V0 = T.MGR, T.V0
BTN_PRESS, BTN_REL = 0x08033320, 0x0803381A
COLOUR = 0x0804AD78


def state(e, pad):
    """The stock's colour state of the pad of the Note view (the colour minus the track's base colour)."""
    base = e.r16(V0 + 0x10C) if hasattr(e, "r16") else int.from_bytes(e.uc.mem_read(V0 + 0x10C, 2), "little")
    return ((e.r0(COLOUR, V0, e.idx(pad)) & 0xFFFF) - base) & 0xFFFF


def editor_pad(e, pad):
    e.sbtn(CS.ID_SCALES); e.press(pad, shift=True); e.release(pad)


def run(img, man, check):
    e = T.E(Path(img).read_bytes(), man)
    e.btn(0); t0 = e.tables()
    if "c_jkrel" not in man["report"]["janko"]["labels"]:
        editor_pad(e, J.PAD_JK2)
        check(e.on() != J.JK, f"the previous build: Shift + pad 24 in the editor is not the old layout (B_ON {e.on()})")
        del e; gc.collect(); return
    lab = {k: int(v, 16) for k, v in man["report"]["janko"]["labels"].items()}
    oct0 = e.r0(lab["c_jkoct"], 0)
    editor_pad(e, J.PAD_JK)
    e.frame(); led = e.scales_leds()
    check(e.on() == J.JK3 and led[J.PAD_JK] == J.COL_ON and led[J.PAD_JK2] == 0,
          f"the editor: Shift + pad 8 = the new layout (B_ON {e.on()}, pad 8 {led[J.PAD_JK]:#x}, pad 24 {led[J.PAD_JK2]:#x})")
    e.btn(0); e.frame()
    bot = [e.val(24 + c) for c in range(8)]; up = [e.val(16 + c) for c in range(8)]
    check(bot == [60 + 2 * c for c in range(8)] and up == [59 + 2 * c for c in range(8)],
          f"the new layout, the Note view: bottom row {bot}, the row above {up}")
    st = {p: state(e, p) for p in (24, 25, 30, 16, 17)}
    check(st[24] in (5, 6) and st[30] in (5, 6) and st[25] in (0, 3) and st[16] in (0, 3) and st[17] in (0, 3),
          f"the new layout: the root's colour on 60 / 72 only ({st})")
    r = e.idx(24)
    ln = [e.r8(J.CS.KB + 0x180 + r + 6), e.r8(J.CS.KB + 0x180 + r + 7)]
    check(ln == [r - 16, r - 15] and e.r8(J.CS.KB + 0x14 + r - 16) == 72 and e.r8(J.CS.KB + 0x180 + r - 16) == r + 6,
          f"the links: (R, 6 / 7) <-> (R - 2, 0 / 1) ({ln} / {r - 16}, {r - 15})")
    # Octave: short, then held
    e.at(200000); e.btn(J.ID_UP); e.frame(); a1 = e.val(24)
    e.at(201000); e.call(BTN_PRESS, MGR, J.ID_UP, maxins=8_000_000); e.frame(); a2 = e.val(24)
    e.at(201300); e.frame(); a3 = e.val(24)
    e.at(201450); e.frame(); a4 = e.val(24)
    e.call(BTN_REL, MGR, J.ID_UP, maxins=8_000_000); e.at(203000); e.frame(); a5 = e.val(24)
    check((a1, a2, a3, a4, a5) == (61, 62, 62, 73, 73),
          f"Octave up: a press = + 1 ({a1}, {a2}); held 450 ms = an octave from where it started ({a3}, {a4}); the release: nothing more ({a5})")
    e.at(210000); e.call(BTN_PRESS, MGR, J.ID_DOWN, maxins=8_000_000); e.at(210300); e.call(BTN_REL, MGR, J.ID_DOWN, maxins=8_000_000)
    e.at(211000); e.frame(); b1 = e.val(24)
    e.at(212000); e.call(BTN_PRESS, MGR, J.ID_DOWN, maxins=8_000_000); e.at(212500); e.frame(); b2 = e.val(24); e.call(BTN_REL, MGR, J.ID_DOWN, maxins=8_000_000)
    oc = e.r0(lab["c_jkoct"], 0)
    check((b1, b2) == (72, 60) and oc == oct0, f"Octave down: released at 300 ms = - 1 only ({b1}); held = - 12 from the press ({b2}); "
                                               f"the stock's octave kept ({oc} / {oct0})")
    e.goto(6); e.frame()
    rows = [[e.val(8 * k + c) for c in range(8)] for k in range(4)]
    check(e.r8(MGR + 0x152) == 6 and rows[3] == bot and rows[2] == up and rows[1] == [72 + 2 * c for c in range(8)]
          and rows[0] == [71 + 2 * c for c in range(8)], f"the expanded view: the pair above = the pair below + 12 ({rows[1][:2]}, {rows[0][:2]})")
    # the old layout from the new one at once
    editor_pad(e, J.PAD_JK2)
    e.frame(); led = e.scales_leds()
    check(e.on() == J.JK and led[J.PAD_JK2] == J.COL_ON and led[J.PAD_JK] == 0,
          f"Shift + pad 24 = the old layout (B_ON {e.on()}, pad 24 {led[J.PAD_JK2]:#x}, pad 8 {led[J.PAD_JK]:#x})")
    e.btn(0); e.goto(5); e.frame()
    bot = [e.val(24 + c) for c in range(8)]; up = [e.val(16 + c) for c in range(8)]
    check(bot == [60 + 2 * c for c in range(8)] and up == [61 + 2 * c for c in range(8)], f"the old layout: bottom row {bot}, the row above {up}")
    st = {p: state(e, p) for p in (24, 25, 16, 17)}
    lk17 = e.r8(J.CS.KB + 0x180 + e.idx(17))
    check(st[24] in (5, 6) and st[25] in (0, 3) and st[16] in (0, 3) and st[17] in (0, 3) and lk17 != 0xFF,
          f"the old layout: the root's colour on 60, not on the linked 63 ({st}, link {lk17})")
    editor_pad(e, J.PAD_JK2); e.btn(0); e.frame()
    check(e.on() in (0, 1) and e.tables() == t0, f"Shift + pad 24 again: off (B_ON {e.on()}), the stock's tables back")
    del e; gc.collect()


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    run(img, man, check)
    if prev:
        run(prev, pman, check)
    print(f"{Path(img).stem} JANKO2 RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text()), a[2] if len(a) > 2 else None,
                       json.loads(Path(a[3]).read_text()) if len(a) > 3 else None) else 0)
