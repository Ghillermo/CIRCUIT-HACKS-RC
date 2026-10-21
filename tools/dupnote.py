"""SC45.8 / RC2.06 (a fix; the user, 2026-10-21: «on play note pads, when pad17/32 are held at the same time (both the same C note) the note won't
stop until the pad is touched again»): two pads of the same note held together no longer leave the note sounding.

The note tracks' keyboard repeats a note at the end of a row and the start of the row above (pads 17 and 32 of the scale layout).  The stock's live
note-on of a track view 0x0804AEF2(view, pad, velocity): note = the keyboard's note of the pad; a pad that already holds that note ([view + 0x40 + i]
= note, i = 0..31) gets its slot cleared ([+ 0x40 + i], [+ 0x60 + i] = 0) with no note-off, then [+ 0x40 + pad] = note and a second note-on
(0x0804B07A).  Letting the first pad go finds its slot empty and sends nothing; the second one sends one note-off: two note-ons, one note-off, and
the first voice keeps sounding.
  * 0x0804AF2C (movs r2, #0; add.w r3, r5, #0x40: the slot cleared) -> bl c_dnoff; b 0x0804AF3C: the stock's note-off of that pad
    0x0804AF5A(view, i) (it clears the slot too; r0 = the note kept), then the new note-on: the note plays again, one voice, and the last pad let
    go stops it.
In the hole (RAM untouched, no card).
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, b, bl, mov_reg, pop_list, push_list  # noqa: E402

AT, OLD, BACK = 0x0804AF2C, bytes.fromhex("00 22 05 f1 40 03".replace(" ", "")), 0x0804AF3C
NOTE_OFF = 0x0804AF5A


def arm_code(base):
    a = Asm(base)
    E = a.emit
    # ---- c_dnoff (0x0804AF2C: r0 = the note, r1 = the pad that holds it, r5 = the track view; r4 / r6 = the new pad / velocity): its note-off
    a.label("c_dnoff")
    E(push_list, [0], lr=True); E(mov_reg, 0, 5); E(bl, NOTE_OFF); E(pop_list, [0], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the slot clearing of 0x0804AEF2."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    code, labels = arm_code(base_addr)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert bytes(img[AT - BASE:AT - BASE + 6]) == OLD, hex(AT)
    img[AT - BASE:AT - BASE + 6] = bl(AT, labels["c_dnoff"]) + b(AT + 4, BACK)
    return labels, code, {}
