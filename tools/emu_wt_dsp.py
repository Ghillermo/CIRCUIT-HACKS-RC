"""SC52.1 DSP test (vcf21_dsp.use_wavetable + gentab.use_xtab): the wavetable source of the MIDI 1 / 2 own synth on core 0.

    python tools/emu_wt_dsp.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json      (PREV = SC52)

On the dsp56kEmu interpreter with each build's real core-0 program (study_alias_dsp's set-up: MIDI 1, the chain neutral), a synthetic table in
Y (no device data in tests): frame 0 = a sine, frame 1 = a square band-limited at each level (harmonics <= WT_H[L]), at Y:$40000:
  * without a table (OSC2 + WT_N = 0) every oscillator plays as PREV, bit for bit (TINC / TLFO now in X; the waves' subroutine's new head);
  * position 0 = the sine: one harmonic, at the note's pitch, half scale; position 126 = the square: odd harmonics; position 63 = half of each;
  * the level: frame A's address = base + L x $400 with L the first from 2 whose harmonics stay under Nyquist (notes 36 / 72 / 96 / 120);
  * the warp: SHAPE 50 = no bend (the sine clean), SHAPE 100 = a bent sine (harmonics 2+ up);
  * two oscillators with the table: OSC 2 reads it too (its own position).
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import study_alias_dsp as AD  # noqa: E402
import granular_dsp as GD  # noqa: E402
import poly as PL  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
from emu_masterfx_dsp import s24  # noqa: E402

V, N, RING, OSB = AD.V, AD.N, AD.RING, AD.OSB
BASE = 0x40000
O2 = VD.OS2B0 - VD.OSB0


def table(nf=2):
    t = np.zeros(nf * VD.WT_FRAME, dtype=np.int64)
    i = np.arange(1024)
    for L, H in enumerate(VD.WT_H):
        sine = np.sin(2 * np.pi * i / 1024)
        sq = sum(np.sin(2 * np.pi * k * i / 1024) / k for k in range(1, H + 1, 2)) * 4 / np.pi
        sq = sq / max(1.0, np.abs(sq).max() / 0.99)
        for f, w in ((0, sine), (1, sq)):
            v = np.round(w * 32767).astype(np.int64)
            t[f * VD.WT_FRAME + L * VD.WT_LEVEL:f * VD.WT_FRAME + L * VD.WT_LEVEL + 1024] = (v & 0xFFFF) << 8   # 16 bits, low byte 0 (as the SDRAM)
    return [int(x) & 0xFFFFFF for x in t]


OLD_AT = dict(TATK=0x3E0D, TDEC=0x3E4E, TF=0x3E8E, TINC=0x3ECE, TEXP=0x3F4F, TLFO=0x3F80)     # gentab's layout before use_xtab


def gentabs(xtab):
    """the tables init2 makes at DSP start (the harness starts at vpre): gentab's model, where the build keeps them"""
    import gentab as G
    t = G.tables()
    if not xtab: return [('p', OLD_AT[k], t[k][1]) for k in OLD_AT]
    at = dict(TATK=G.GEN_TATK, TDEC=G.GEN_TDEC, TF=G.GEN_TF, TEXP=G.GEN_TEXP)
    return [('p', at[k], t[k][1]) for k in at] + [('x', G.XT_TINC, t["TINC"][1]), ('x', G.XT_TLFO, t["TLFO"][1])]


def renderer(img, man, nb=20, tab=None, xtab=True):
    PL.adopt(man["report"])
    gt = gentabs(xtab)
    sp = dsp_program(img)
    P = [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]
    vpre = int(man["report"]["sc16"]["dsp_labels"]["vpre"], 16)

    def render(note, wave_, pw, extra=None):
        blk = [0] * (2 * V.VBS)
        for k_, v_ in ((V.P_GAIN, 64), (V.P_DEC, 40), (V.P_SUS, 100), (V.P_REL, 40), (V.P_FXMOD, 64), (V.ACT, 2), (V.VEL, 127), (V.NOTE, note)):
            blk[k_] = v_
        osb = [0] * 144; osb[2], osb[3] = wave_, pw
        for k_, v_ in (extra or {}).items(): osb[k_] = v_
        out = []
        for b in range(nb):
            mem = [('x', 0x3A, [N]), ('x', V.VB0, blk), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, [0] * (2 * N)),
                   ('x', OSB, osb), ('x', GD.RDOFS, [0x40]), ('x', GD.SOUT, [0] * 128), ('x', V.SIDE0, [0, 0])]
            mem += gt
            if tab: mem.append(('y', BASE, tab))
            res, ran = run(P, vpre, mem=mem, dumps=[('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', OSB, 144)], regs_code=[], maxins=20_000_000)
            assert 'pc=00' in ran, ran
            blk, osb = res[('x', V.VB0)], list(res[('x', OSB)])
            out += [s24(v) / (1 << 23) for v in res[('y', RING)][0::2]]
        gc.collect()
        return np.array(out[N * 8:]), osb, out
    return render


def harm(x, note, k):
    """the amplitude of harmonic k of the note in x (a DFT at that frequency)"""
    f = 440 * 2 ** ((note - 69) / 12) * k / 48000
    n = np.arange(len(x)); w = np.hanning(len(x))
    return 2 * abs(np.sum(x * w * np.exp(-2j * np.pi * f * n))) / np.sum(w)


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    dw = int(man["report"]["sc16"]["dsp_words"], 16)
    import gentab as G
    check(dw <= G.GEN_TATK if G.XTAB else True, f"core 0 ends at P:${dw:x}")
    new, old = renderer(img, man, nb=14), renderer(prev, pman, nb=14, xtab=False)
    same = []
    for what, note, wave_, pw, ex in (("sine", 60, 0, 50, None), ("saw", 72, 84, 0, None), ("supersaw", 60, 84, 100, None), ("morph", 72, 21, 70, None),
                                      ("two oscillators", 60, 84, 50, {V.DFLAGS_OFF if hasattr(V, "DFLAGS_OFF") else VD.DFLAGS_OFF: 2, VD.NOTE2_OFF: 67, O2 + 2: 42, O2 + 4: 64})):
        a, _, ra = new(note, wave_, pw, ex); b, _, rb = old(note, wave_, pw, ex)
        same.append((what, ra == rb and max(abs(v) for v in a) > 0.1))
    check(all(x[1] for x in same), f"no table: bit for bit as PREV: {[w for w, ok in same if ok]}; different: {[w for w, ok in same if not ok]}")
    tab = table()
    wt = renderer(img, man, nb=20, tab=tab)
    T = {O2 + VD.WT_N: 2, O2 + VD.WT_B: BASE}
    x, osb, _ = wt(60, 0, 50, T)
    h = [harm(x, 60, k) for k in (1, 2, 3, 5)]
    check(0.4 < h[0] < 0.55 and max(h[1:]) < 0.02 * h[0], f"position 0 = the sine at the note, half scale: harmonics 1/2/3/5 {[round(v, 4) for v in h]}")
    x, _, _ = wt(60, 126, 50, T)
    h = [harm(x, 60, k) for k in (1, 2, 3, 5)]
    check(h[2] > 0.25 * h[0] and h[4 - 1] > 0.12 * h[0] and h[1] < 0.02 * h[0], f"position 126 = the square: odd harmonics {[round(v, 4) for v in h]}")
    x, _, _ = wt(60, 63, 50, T)
    h = [harm(x, 60, k) for k in (1, 3)]
    check(0.4 < h[0] < 0.6 and 0.06 < h[1] < 0.12, f"position 63 = half of each: harmonics 1/3 {[round(v, 4) for v in h]}")
    for note in (36, 72, 96, 120):
        _, osb, _ = wt(note, 0, 50, T)
        inc = osb[11]
        want = next(L for L in range(2, 18) if inc <= min(0x7FFFFF, (1 << 23) // VD.WT_H[L]))
        got = (osb[VD.WT_A] - BASE) // VD.WT_LEVEL
        check(got == want and osb[VD.WT_B2] == osb[VD.WT_A] + VD.WT_FRAME, f"note {note}: the level {got} (want {want}: inc ${inc:x}), frame B = A + $4800")
    x, _, _ = wt(60, 0, 100, T)
    h = [harm(x, 60, k) for k in (1, 2, 3)]
    check(max(h[1:]) > 0.05 * h[0], f"SHAPE 100: the sine bent (harmonics 2 / 3 up): {[round(v, 4) for v in h]}")
    ex = dict(T); ex.update({VD.DFLAGS_OFF: 2, VD.NOTE2_OFF: 67, O2 + 2: 126, O2 + 3: 50, O2 + 4: 127})   # OSC 2 in the mix (MIX 127), a fifth up, the square, no warp
    x, osb, _ = wt(60, 0, 50, ex)
    h = [harm(x, 67, k) for k in (1, 3)]
    check(h[0] > 0.2 and h[1] > 0.25 * h[0] and osb[96 + VD.WT_A] >= BASE, f"OSC 2 with the table (MIX 127, its position 126): the square a fifth up {[round(v, 4) for v in h]}")
    print(f"{man.get('marker', '?')} WT DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    import gentab
    gentab.use_xtab()
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
