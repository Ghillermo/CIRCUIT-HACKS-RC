"""RC0.7 / RC0.7S ARM tests: RC0.6 / RC0.6S + the engine's address and the slower selector knob of the FX sequencer.

    python tools/emu_rc0_7.py RC0.7.bin RC0.7_manifest.json RC0.6.bin RC0.6_manifest.json
  * the step-drummer / FX sequencer of MIDI 1 reads the step of MIDI 1 (the previous one: of Drum 2);
  * the selector knob: one unit of its position every three events, the rest kept, both ways (the previous one: one an event);
  * the builder options are the only change: vcf21.ENGINE / build_sc17.SEQ_ENGINE and the knob code.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc40_9 as T9  # noqa: E402


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    fsq, step, seq = T9.seq_part(img, man)
    gc.collect(); pfsq, pstep, pseq = T9.seq_part(prev, prev_man)
    check(fsq == 1 and step == 7 and pstep == 3, f"the step-drummer / FX sequencer of MIDI 1 reads the step of MIDI 1 ({step}); the previous build read Drum 2's ({pstep})")
    check(seq == [0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 5, 0, 0] and pseq[:4] == [0, 1, 2, 3], f"the selector knob: one unit every three events, the rest kept ({seq}); the previous build: one an event ({pseq[:7]})")
    old, new = (0x20038ECC).to_bytes(4, "little"), (0x20038EC0).to_bytes(4, "little")
    check(len(img) - len(prev) in range(0, 96), f"the image grows {len(img) - len(prev)} bytes (the knob code)")
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
