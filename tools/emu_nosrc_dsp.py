"""Alpha 7.03 DSP test (build_sc15 / linein3 use_nosrc: no line input as the Nova synths' noise), the whole core 0 with the engine's traffic of
emu_sc43_9_dsp (oscillators, VA-drum, granular, knob turns, notes, drum hits, Synth notes), against Alpha 7.02:
  * modes 0 (as at power-up): X and Y 0..$3FFF the same as Alpha 7.02's at every check;
  * the Setup's FX returns wired to strips 3 / 4 (X:$3A00 = 3, the MIDI tracks' feedback capture): the same as Alpha 7.02's;
  * X:$3A01 / $3A02 = 1 (input 1, as an old project could leave them): the new build = its own run with modes 0 (the modes are read by
    nobody); Alpha 7.02 differs (its input copy in Y:$3A00..: the path is reached).

    python tools/emu_nosrc_dsp.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc43_9_dsp as M  # noqa: E402

SKIP = {0x3A01, 0x3A02}                                    # X: the mode words themselves (forced)


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    def diff(R1, R2, skip_x=()):
        out = []
        for (s1, a1, v1), (s2, a2, v2) in zip(R1, R2):
            out.append([i for i, (x, y) in enumerate(zip(v1, v2)) if x != y and not (s1 == 'x' and i in skip_x)])
        return out
    sched = M.schedule(prev, pman)
    runs = {}
    for name, force in (("modes 0", ()), ("FX returns on strips 3 / 4", ((0x3A00, 3),)), ("modes = input 1", ((0x3A01, 1), (0x3A02, 1)))):
        Rn, _ = M.dsp_run(img, sched, force=force); gc.collect()
        Rp, _ = M.dsp_run(prev, sched, force=force); gc.collect()
        runs[name] = (Rn, Rp)
    for name in ("modes 0", "FX returns on strips 3 / 4"):
        Rn, Rp = runs[name]
        d = diff(Rn, Rp)
        check(len(Rn) == len(Rp) > 0 and not any(d), f"{name}: X / Y 0..$3FFF the same as Alpha 7.02's at {len(Rn)} dumps "
                                                     f"(first differences {[[hex(i) for i in x[:6]] for x in d if x][:2]})")
    Rn, Rp = runs["modes = input 1"]
    d0n = diff(Rn, runs["modes 0"][0], SKIP); d0p = diff(Rp, runs["modes 0"][1], SKIP)
    check(not any(d0n), f"modes = input 1: the new build as with modes 0 ({[[hex(i) for i in x[:6]] for x in d0n if x][:2]})")
    check(any(d0p), f"(Alpha 7.02 with input 1: differs, {sum(len(x) for x in d0p)} words: the input path was reached)")
    print("NOSRC DSP RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
