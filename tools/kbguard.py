"""SC45.7 / RC2.05 (a fix; the user, 2026-10-21: «durante la reproducción, con al menos una secuencia tocando en cualquier pista, cambiar de escala
custom puede llegar a hacer que el aparato se cuelgue y necesita reiniciar»): the note tracks' pad LEDs never written out of their buffer.

The stock lights the pads of the notes a track view shows (its held step [view + 0x24], its sounding notes [view + 0x30]: the listener 0x0804B272 and
the redraw 0x0804AE96) as: q = the quantiser 0x080408C6 (the note), index = the keyboard's reverse table [0x20041044 + 0xF4 + q], then
0x0804AE66(view, index): the colour of that index with 0x0804AA40 ([[view + 4]] + 2 x index, no bound) and the same for its link
[0x20041044 + 0x180 + index].  The indices are 0..223 (0x0804AD38 walks them); a note not on the keyboard has 0xFF, and the halfword goes to the
buffer + 0x1FE = 0x20041602 for Synth 1's view: inside Synth 2's track view (0x200415D4 + 0x2E, the top half of its store pointer [+ 0x2C]).
The stock's scales always quantise to a note of its table (from 24 up), so it never comes up; with cscale's custom scale:
  * after every change of the custom scale the quantiser follows at once and the keyboard only at the next LED frame: a note sounding meanwhile
    gets 0xFF (the hang the user saw, with the transport running);
  * a short period does not cover the whole range (28 rows x P or 2P around 60: with P = 1, notes above 79 are not on the keyboard).
  * 0x0804AE66 (push {r4-r6, lr}; mov r4, r0) -> b.w c_kbg: an index >= 224 returns at once (no pad lit), else the stock's.
In the hole (RAM untouched, no card).
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, b_cond, b_w, cmp_imm, h, push_list, mov_reg, raw  # noqa: E402

AT, OLD, BACK = 0x0804AE66, bytes.fromhex("70b50446"), 0x0804AE6A
NIDX = 224                                                   # 28 rows x 8


def arm_code(base):
    a = Asm(base)
    E = a.emit
    # ---- c_kbg (0x0804AE66: r0 = the track view, r1 = a keyboard index): out of the keyboard = nothing
    a.label("c_kbg")
    E(cmp_imm, 1, NIDX); E(b_cond, "kg_x", "hs")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(b_w, BACK)
    a.label("kg_x"); E(raw, h(0x4770))                                                # bx lr
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the head of 0x0804AE66."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    code, labels = arm_code(base_addr)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert bytes(img[AT - BASE:AT - BASE + 4]) == OLD, hex(AT)
    img[AT - BASE:AT - BASE + 4] = b_w(AT, labels["c_kbg"])
    return labels, code, {}
