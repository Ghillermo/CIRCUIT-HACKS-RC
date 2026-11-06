"""SC52.7 / Beta 5.30 DSP test (vcf21_dsp.use_blep4: the 4-sample BLEP from RYTHM's RD43), on the emulated core 0 (emu_osc4_dsp's harness, MIDI 1),
against the build before it (SC52.6 / Beta 5.29):
  * core 0 still ends before gentab's tables;
  * the sine and the triangle (no BLEP): bit for bit as PREV;
  * the saw, the pulse at widths 20 / 50 / 80 and the supersaw at notes 72 and 96: aliasing below 8 kHz at least 10 dB under PREV's or under -85 dB
    (study_alias_dsp's metric; the supersaw's with its seven saws), the peak under 1;
  * two oscillators: FM at the centre (64) with two sines = PREV bit for bit; the hard sync and FM right with saws: no worse than PREV below 8 kHz;
  * the cost: the median instructions a block of one oscillator (saw, supersaw) and of two (saw + supersaw), against PREV.

    python tools/emu_blep4_dsp.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json      (B5.30 / B5.29)
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import emu_wt_dsp as W  # noqa: E402
import study_alias_dsp as SD  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
from emu_masterfx_dsp import s24  # noqa: E402

V, N, RING, OSB, GD, PL = W.V, W.N, W.RING, W.OSB, W.GD, W.PL
O2 = VD.OS2B0 - VD.OSB0


def renderer(img, man, nb):
    """render(note, wave, shape, extra) -> (the left samples past the first 8 blocks, the median instructions a block, the raw words)"""
    PL.adopt(man["report"])
    gt = W.gentabs(True)
    sp = dsp_program(img)
    P = [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]
    vpre = int(man["report"]["sc16"]["dsp_labels"]["vpre"], 16)

    def render(note, w1, p1, extra=None):
        blk = [0] * (2 * V.VBS)
        for k_, v_ in ((V.P_GAIN, 64), (V.P_DEC, 40), (V.P_SUS, 100), (V.P_REL, 40), (V.P_FXMOD, 64), (V.ACT, 2), (V.VEL, 127), (V.NOTE, note)):
            blk[k_] = v_
        osb = [0] * 144; osb[2], osb[3] = w1, p1
        for k_, v_ in (extra or {}).items(): osb[k_] = v_
        omw = [0] * (2 * V.VBS)
        out, raw, ins = [], [], []
        for _b in range(nb):
            mem = [('x', 0x3A, [N]), ('x', V.VB0, blk), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, [0] * (2 * N)),
                   ('x', OSB, osb), ('x', GD.RDOFS, [0x40]), ('x', GD.SOUT, [0] * 128), ('x', V.SIDE0, [0, 0]), ('x', VD.OM_T, omw)] + gt
            res, ran = run(P, vpre, mem=mem, dumps=[('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', OSB, 144)], regs_code=[], maxins=20_000_000)
            assert 'pc=00' in ran, ran
            ins.append(int(ran.split('ins=')[1].split()[0]))
            blk, osb = res[('x', V.VB0)], list(res[('x', OSB)])
            raw += res[('y', RING)][0::2]
            out += [s24(v) / (1 << 23) for v in res[('y', RING)][0::2]]
        gc.collect()
        return np.array(out[N * 8:]), int(np.median(ins[8:])), raw
    return render


def main(img, man, prev, pman, fast=False):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    import gentab as G
    G.use_xtab()
    dw, pw = int(man["report"]["sc16"]["dsp_words"], 16), int(pman["report"]["sc16"]["dsp_words"], 16)
    check(dw <= G.GEN_TATK, f"core 0 ends at P:${dw:x} (PREV ${pw:x}: {dw - pw:+d} words; the tables from ${G.GEN_TATK:x})")
    nb = 40 if fast else 72
    new, old = renderer(img, man, nb), renderer(prev, pman, nb)
    same = []
    for what, wave, pw_ in (("sine", 0, 50), ("triangle", 42, 50), ("folded sine", 0, 90)):
        a, _, ra = new(72, wave, pw_); b, _, rb = old(72, wave, pw_)
        same.append((what, ra == rb and float(np.abs(a).max()) > 0.1))
    check(all(ok for _w, ok in same), f"no BLEP, bit for bit as PREV: {same}")
    cost = {}
    for what, wave, pw_ in (("saw", 84, 0), ("pulse 20", 126, 20), ("pulse 50", 126, 50), ("pulse 80", 126, 80), ("supersaw", 84, 100)):
        row = []
        for note in (72, 96):
            x, i_new, _ = new(note, wave, pw_); xo, i_old, _ = old(note, wave, pw_)
            f = SD.asr_super if what == "supersaw" else SD.asr
            r, ro = f(x, note), f(xo, note)
            row.append((note, r[1], ro[1], r[0], ro[0], float(np.abs(x).max())))
            cost[(what, note)] = (i_new, i_old)
        check(all((r[1] < r[2] - 10 or r[1] < -85) and r[5] < 1.0 for r in row),
              f"{what}: below 8 kHz " + ", ".join(f"note {n} {a:.1f} dB (PREV {b:.1f}), whole band {c:.1f} (PREV {d:.1f})" for n, a, b, c, d, _ in row)
              + f"; peak {max(r[5] for r in row):.3f}")
    note = 84
    base = lambda w2, p2, **k: {VD.DFLAGS_OFF: 2, VD.NOTE2_OFF: note, O2 + 2: w2, O2 + 3: p2, **{O2 + int(a[1:]): v for a, v in k.items()}}
    _, _, ra = new(note, 0, 50, base(0, 50, o4=64, o6=64)); _, _, rb = old(note, 0, 50, base(0, 50, o4=64, o6=64))
    check(ra == rb, "two sines, MIX 64, FM at the centre: bit for bit as PREV")
    for what, ex in (("the hard sync (saws, sweep 40)", base(84, 0, o4=127, o5=1, o8=40, o6=64)), ("FM right 80 (saw <- sine)", base(0, 50, o6=80)),
                     ("FM left 40 (saws)", base(84, 0, o4=80, o6=40))):
        x, _, _ = new(note, 84, 0, ex); xo, _, _ = old(note, 84, 0, ex)
        r, ro = SD.asr(x, note), SD.asr(xo, note)
        check(r[1] < ro[1] + 0.5 and float(np.abs(x).max()) < 1.0, f"{what}: below 8 kHz {r[1]:.1f} dB (PREV {ro[1]:.1f}), peak {np.abs(x).max():.3f}")
    _, i2n, _ = new(72, 84, 0, {VD.DFLAGS_OFF: 2, VD.NOTE2_OFF: 79, O2 + 2: 84, O2 + 3: 100, O2 + 4: 64, O2 + 6: 64})
    _, i2o, _ = old(72, 84, 0, {VD.DFLAGS_OFF: 2, VD.NOTE2_OFF: 79, O2 + 2: 84, O2 + 3: 100, O2 + 4: 64, O2 + 6: 64})
    lines = [f"{w} note {n}: {a} ({a - b:+d}, {100 * (a - b) / b:+.0f} %)" for (w, n), (a, b) in cost.items() if w in ("saw", "supersaw", "pulse 50")]
    print("cost a block (instructions, against PREV): " + "; ".join(lines) + f"; saw + supersaw note 72: {i2n} ({i2n - i2o:+d}, {100 * (i2n - i2o) / i2o:+.0f} %)")
    print(f"{man.get('marker', '?')} BLEP4 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if x != "--fast"]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text()), Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text()),
                       fast="--fast" in sys.argv) else 0)
