"""SC52.5 / RC4.08 DSP test (vcf21_dsp.use_blep2: the pulse's rising edge where it is), on the emulated core 0 (emu_wt_dsp's harness, MIDI 1, one
oscillator), against the build before it:
  * the pulse at widths 20 and 80 (PW, the shape knob) at notes 72 and 96: aliasing below 8 kHz under -55 dB (PREV: about -22 at note 96);
  * the pulse at 50 %: within 1 dB of PREV (the edges were already in place there);
  * the sine, the saw and the supersaw: bit for bit as PREV.

    python tools/emu_blep2_dsp.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json      (SC52.5 / SC52.4, RC4.08 / RC4.07)
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import study_alias_dsp as SD  # noqa: E402


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    xtab = "wtui" in man["report"]                                                  # (gentab.use_xtab: SC52.1 and after)
    if xtab:
        import gentab
        gentab.use_xtab()
    import emu_wt_dsp as W
    new, old = W.renderer(img, man, nb=40, xtab=xtab), W.renderer(prev, pman, nb=40, xtab=xtab)
    same = []
    for what, wave, pw in (("sine", 0, 50), ("saw", 84, 0), ("supersaw", 84, 100)):
        a, _, ra = new(72, wave, pw); b, _, rb = old(72, wave, pw)
        same.append((what, ra == rb))
    check(all(ok for _w, ok in same), f"bit for bit as PREV: {same}")
    for note in (72, 96):
        for pw in (20, 80, 50):
            x, _, _ = new(note, 126, pw); xo, _, _ = old(note, 126, pw)
            r, ro = SD.asr(x, note), SD.asr(xo, note)
            if pw == 50: check(abs(r[1] - ro[1]) < 1.0, f"pulse 50 %, note {note}: below 8 kHz {r[1]:.1f} dB (PREV {ro[1]:.1f})")
            else: check(r[1] < -55, f"pulse width {pw}, note {note}: below 8 kHz {r[1]:.1f} dB (PREV {ro[1]:.1f}); the whole band {r[0]:.1f} (PREV {ro[0]:.1f})")
    print(f"{man.get('marker', '?')} BLEP2 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
