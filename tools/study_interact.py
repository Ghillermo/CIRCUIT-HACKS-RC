"""Study (2026-11-06, «Al usar las interacciones de onda (fm, sync, bitwise...) se produce bastante ruido»): the own synth's two oscillators on the
emulated core 0 (study_alias_dsp's harness), OSC 2 at the same note: every partial of a clean result is a harmonic of the note, so the energy off
the harmonics = aliasing / noise (dB against the harmonics; whole band | below 8 kHz).

    python tools/study_interact.py BUILD.bin manifest.json [NB]
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import study_alias_dsp as SD  # noqa: E402
import emu_wt_dsp as W  # noqa: E402
import vcf21_dsp as VD  # noqa: E402

O2 = VD.OS2B0 - VD.OSB0
CASES = [  # name, WAVE1, PW1, WAVE2, PW2, {OSC2 word: value} (the FM word as the build reads it: OLD = 0..127, NEW = 64 + ...)
    ("plain saw + saw, mix 64", 84, 0, 84, 0, {4: 64}),
    ("FM 1/4, sine <- sine", 0, 50, 0, 50, {6: ("fm", 32)}),
    ("FM 1/4, saw <- sine", 84, 0, 0, 50, {6: ("fm", 32)}),
    ("FM full, saw <- sine", 84, 0, 0, 50, {6: ("fm", 127)}),
    ("FM 1/4, sine <- saw", 0, 50, 84, 0, {6: ("fm", 32)}),
    ("sync, saw <- saw, mix 127", 84, 0, 84, 0, {4: 127, 5: 1, 8: 40}),
    ("xor 100, saw ^ sine", 84, 0, 0, 50, {5: 2, 8: 100}),
    ("ring 100, saw x sine", 84, 0, 0, 50, {7: 100}),
]
NEW_FM = {32: 64 + 16, 127: 64 + 32}       # the same amount on the new knob (4 t^2 = v / 127)


def main(img, man, nb=48):
    r_ = W.renderer(img, man, nb=nb)
    new = "oscmod" in man["report"]
    for note in (84,):
        for name, w1, p1, w2, p2, o2 in CASES:
            extra = {VD.DFLAGS_OFF: 2, VD.NOTE2_OFF: note, O2 + 2: w2, O2 + 3: p2}
            for k, v in o2.items():
                if isinstance(v, tuple): v = NEW_FM[v[1]] if new else v[1]
                extra[O2 + k] = v
            if new and 6 not in o2: extra[O2 + 6] = 64
            x, ins, _ = r_(note, w1, p1, extra)
            a, b = SD.asr(x, note)
            print(f"note {note}  {name:36s} off-harmonic {a:6.1f} | {b:6.1f} dB   rms {float((x ** 2).mean()) ** .5:.3f}   {ins} ins")


if __name__ == "__main__":
    import gentab; gentab.use_xtab()
    main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text()), *(int(v) for v in sys.argv[3:]))
