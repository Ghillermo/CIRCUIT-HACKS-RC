"""SC48 ARM tests (tools/notecyc.py): with the step-drummer enabled, Note cycles Note -> expanded Note -> the step-drummer -> Note.  Through the
controller (0x08033320 / 0x0803381A); the controller's subview [ctrl + 0x152]; vcf21's c_sdscr = the step-drummer on the screen:
  * MIDI 1 without the step-drummer: Note <-> expanded (the stock);
  * MIDI 1 with it: Note (19) -> expanded (24) -> the step-drummer (Preset 18, c_sdscr = 0) -> Note (19), its open flag cleared;
  * MIDI 1 with it but the engine off: the stock (the step-drummer needs the engine);
  * Synth 1: the stock (its step-drummer has no on / off of its own).

    python tools/emu_notecyc.py SC48.bin SC48_manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402
import vcf21 as V  # noqa: E402

MGR, CUR = X.MGR, 0x152


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = X.EP(Path(img).read_bytes(), man)
    vl = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
    cur = lambda: e.r8(MGR + CUR)
    scr = lambda: e.r0(vl["c_sdscr"])
    def to(btn, want):
        e.btn(btn)
        for _ in range(4):
            if cur() == want: break
            e.btn(9)
        return cur()
    t = 1000
    def note():
        nonlocal t
        t += 600; e.at(t); e.btn(9); return cur()
    to(2, 19)
    seq = [cur(), note(), note()]
    check(seq == [19, 24, 19], f"MIDI 1 without the step-drummer: Note <-> expanded ({seq})")
    e.r0(vl["c_sdsetnib"], 0, e.r0(vl["c_sdnib"], 0) | 1)
    seq = [cur(), note(), note()]
    check(seq == [19, 24, 19], f"MIDI 1 with the step-drummer but the engine off: the stock ({seq})")
    e.btn(8); e.pad(26); e.pad(16 + 2); e.pad(26)                                         # the engine on (the oscillator, modesel's row)
    to(2, 19)
    check(e.r0(vl["c_sden"], 0) == 1, "MIDI 1: the step-drummer on (enabled, the engine on)")
    seq = [cur(), note()]; s2 = note(); sc = scr(); s3 = note()
    check(seq == [19, 24] and s2 == 18 and sc == 0 and s3 == 19 and not e.r0(vl["c_sdflag"], V.F_SDOPEN),
          f"MIDI 1 with the step-drummer: {seq + [s2, s3]}, on the screen {sc}, the open flag cleared")
    to(0, 1)
    seq = [cur(), note(), note()]
    check(seq == [1, 6, 1], f"Synth 1: the stock ({seq})")
    del e; gc.collect()
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text())) else 0)
