"""SC19.2 tests: the staged deferred work (persist19.GUARD), on the live RAM dump (unicorn).

    python tools/emu_sc19_2.py SC19.1.bin SC19.2.bin SC19.2_manifest.json

The tick of SC19 does its power-up work (load the saved settings, Master FX and song pointer off, every drum parameter dirty -> messages to the DSP) as soon as
the four drum handlers exist.  SC19.2 holds it back by the uptime word X = [0x2000081C] (HAL uwTick, ms):
  X < 15 s : nothing;   15 s <= X < 30 s : settings -> RAM, validation, Master FX / song pointer off, NO drum message;   X >= 30 s : the drum messages.
The rest of SC19 is checked by tools/emu_sc19.py on the same image (the dump's uptime is 107 s, so both stages are open there).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc19 as T19  # noqa: E402
import persist19 as P  # noqa: E402
import emu_sc19_1 as T1  # noqa: E402

TICK = 0x2000081C


def main(ref, img, man, refman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]
    lab = {k: int(v, 16) for k, v in rep["persist19"]["labels"].items()}
    check("c_rs_dirty" in lab, "SC19.2: the staged work is in the image (c_rs_dirty)")
    check("c_rs_dirty" not in {k for k in refman["report"]["persist19"]["labels"]}, "SC19.1 has no stage code")
    e = T1.E191(img, man)
    def at(ms): e.w32(TICK, ms)
    def prepare():
        e.setrec(P.XM_SIG, (P.SIG << 3)); e.setrec(P.XM_MODES, 2 | (3 << 3))        # a saved project: signature + Synth 1 = In 2, Synth 2 = inverted In 1
    prepare(); at(1000)
    e.apply()
    check(e.flags() == P.F_RESYNC and e.modes() == [0, 0], f"after the apply at power-up: RESYNC pending, modes untouched {e.flags()} {e.modes()}")
    for ms in (1000, 5000, 14999):
        at(ms); m = e.tick19()
        check(e.flags() == P.F_RESYNC and e.modes() == [0, 0] and m == [], f"uptime {ms} ms: the tick does nothing (flags {e.flags()}, DSP messages {len(m)})")
    at(15000); m = e.tick19()
    check(e.flags() == P.F_MSG and e.modes() == [2, 3], f"15 s (stage A): settings loaded into RAM (modes {e.modes()}), flags = MSG ({e.flags()})")
    check(m == [] and all(not e.dirty(d) for d in range(4)), f"stage A sends no DSP message and marks no drum parameter ({len(m)} messages)")
    at(29999); m = e.tick19()
    check(e.flags() == P.F_MSG and m == [], "29.999 s: still waiting")
    at(30000); m1 = e.tick19()
    check(e.flags() == 0 and (m1 != [] or any(e.dirty(d) for d in range(4))), f"30 s (stage B): the drums are marked dirty and the messages start ({len(m1)} in the first tick, flags {e.flags()})")
    rest = e.drain()
    sent = sum(len(x) for x in [m1] + rest)
    check(sent >= 4 and all(not e.dirty(d) for d in range(4)), f"the messages go out one per drum per tick: {sent} in all, nothing left dirty")
    # a knob turn before the stages still works (the SC18 path)
    x = T1.E191(img, man); x.w32(TICK, 2000)
    x.sel(0); x.knob19(0, 3)
    mk = x.tick19()
    check(len(mk) >= 1, f"a drum knob turned at 2 s is sent in the next tick ({len(mk)} message)")
    # a second load later restarts the stages from the uptime then
    y = T1.E191(img, man); y.w32(TICK, 100000)
    y.setrec(P.XM_SIG, (P.SIG << 3)); y.setrec(P.XM_MODES, 2)
    y.apply()
    a = y.tick19(); b = y.tick19()
    check(y.flags() == 0 and (a or b), f"a project load at 100 s: stage A and B open at once (flags {y.flags()}, messages {len(a)} + {len(b)})")
    print("SC19.2 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    ref = Path(sys.argv[1]).read_bytes(); img = Path(sys.argv[2]).read_bytes()
    man = json.loads(Path(sys.argv[3]).read_text()); refman = json.loads(Path(sys.argv[4]).read_text())
    sys.exit(1 if main(ref, img, man, refman) else 0)
