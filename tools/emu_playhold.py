"""SC42.1 (packio.use_playhold): the ~4 s card rereads of the Preset views wait for the transport stopped.

Through the controller and the real LED task (a frame every 10 ms for 10 s), the content API's ops counted (and answered by emu_lazysave's harness):
  * playing, Preset view of MIDI 1 (mpatch: 2 banks) / of Synth 1 (c_pmode: 4 banks): one read of the page on entering, then nothing;
  * stopped: the same views read again every ~4 s (3 rounds in 10 s);
  * the previous build (if given): playing, it read again every ~4 s.

    python tools/emu_playhold.py firmware/sc42.1/circuittracks-4486-SC42.1.bin firmware/sc42.1/manifest.json [PREVIOUS.bin]
"""
from __future__ import annotations
import gc, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402

VIEWS = (("MIDI 1 Preset", (2, 8), 2), ("Synth 1 Preset", (0, 8), 4))      # buttons, banks per round (size + read each)


def rounds(img, seq, playing, banks):
    e = T.EL(img); e.at(100000); e.transport(playing)
    for b in seq: e.btn(b)
    n = [0]
    def h(uc, a, s, d): n[0] += 1
    for f in T.SD_OPS: e.uc.hook_add(UC_HOOK_CODE, h, begin=f, end=f)
    for k in range(1000): e.at(100000 + 10 * (k + 1)); e.leds()
    r = n[0] / (2 * banks)
    del e; gc.collect()
    return r


def main(img, prev=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    for name, seq, banks in VIEWS:
        r = rounds(img, seq, 1, banks); check(r == 1, f"{name}, playing: one read of the page on entering, then nothing ({r} rounds in 10 s)")
        r = rounds(img, seq, 0, banks); check(r >= 3, f"{name}, stopped: read again every ~4 s ({r} rounds in 10 s)")
        if prev is not None:
            r = rounds(prev, seq, 1, banks); check(r >= 3, f"the previous build, {name}, playing: read again every ~4 s ({r} rounds)")
    return fails


if __name__ == "__main__":
    img = bytearray(Path(sys.argv[1]).read_bytes())
    prev = bytearray(Path(sys.argv[3]).read_bytes()) if len(sys.argv) > 3 else None
    f = main(img, prev)
    print(f"{Path(sys.argv[1]).stem.split('-')[-1]} ARM RESULT: " + ("ALL PASS" if f == 0 else f"{f} FAILURES"))
    sys.exit(1 if f else 0)
