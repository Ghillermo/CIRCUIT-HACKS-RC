"""SC45.8 / RC2.06 (tools/dupnote.py): two pads of the same note held together no longer leave the note sounding.

The emulated firmware, Synth 1's Note view (its button, then Note), the pads through the controller and the track view's note interface logged:
  * pads 17 and 32 (indices 16 / 31) hold the same note (the end of a row and the start of the row above);
  * pad 17, then pad 32, let go in both orders: every note-on of that note has its note-off (the previous build: two note-ons, one note-off);
  * one pad alone: one note-on, one note-off, as always.

    python tools/emu_dupnote.py BUILD.bin manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_arp as EA  # noqa: E402
from emu_sc08 import CONT  # noqa: E402

A, B = 16, 31


def run(img, man, seq):
    """seq: ("p", pad) press / ("u", pad) let go -> the interface calls [(on|off, note)]"""
    e = EA.EA(bytearray(Path(img).read_bytes()), man)
    e.set_p0(e.r32(CONT + 0x188), 0); e.press(0); e.release(0); e.press(9); e.release(9)          # Synth 1, Note: its track view
    e.transport(0); e.ifc.clear()
    notes = {}
    for k, q in seq:
        n0 = len(e.ifc)
        if k == "p": e.pad(q, up=False)
        else: e.unpad(q)
        for x in e.ifc[n0:]:
            if x[0] == "on" and x[1] == EA.VIEW_IFC: notes[q] = x[2]
    out = [(x[0], x[2]) for x in e.ifc if x[1] == EA.VIEW_IFC]
    del e; gc.collect()
    return out, notes


def balanced(calls):
    held = {}
    for k, n in calls: held[n] = held.get(n, 0) + (1 if k == "on" else -1)
    return all(v == 0 for v in held.values())


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    one, _ = run(img, man, [("p", A), ("u", A)])
    check(len(one) == 2 and balanced(one), f"one pad: a note-on and its note-off ({one})")
    for name, seq in (("17 then 32, 17 let go first", [("p", A), ("p", B), ("u", A), ("u", B)]),
                      ("17 then 32, 32 let go first", [("p", A), ("p", B), ("u", B), ("u", A)])):
        calls, notes = run(img, man, seq)
        check(notes.get(A) is not None and notes.get(A) == notes.get(B), f"{name}: pads 17 and 32 play the same note ({notes})")
        check(balanced(calls), f"{name}: every note-on has its note-off ({calls})")
        if prev:
            pc, _ = run(prev, pman, seq)
            check(not balanced(pc), f"{name}: the previous build leaves the note on ({pc})")
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text()), a[2] if len(a) > 2 else None,
                       json.loads(Path(a[3]).read_text()) if len(a) > 3 else None) else 0)
