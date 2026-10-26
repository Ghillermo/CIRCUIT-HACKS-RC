"""SC46.9 DSP test (vcf21_dsp.use_poly): 4 voices per track in the oscillator and the sample mode of MIDI 1 / 2.

    python tools/emu_poly_dsp.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json      (PREV = SC46.8 / Beta 3.25)

vpre once a block on the dsp56kEmu interpreter with each build's real core-0 program (emu_smstereo_dsp's harness), MIDI 1's chain neutral (GAIN
64, no envelope amount, no tremolo, no effect, no filter: the ring = the source):
  * one voice (OSC2 + 38 = 0): the oscillator (sine, saw, supersaw) and the sample (mono, stereo) as PREV's, the ring and the OSC1 block bit for bit;
  * the oscillator with the records at X:$3E60: two voices (notes 48 / 55) from block 0 = the sum of two one-voice runs at those notes x the gain
    that goes from 0 to the target over the first block, then the target; voice 1 off at block 3 = its fade over the block, then silent (its
    record frozen, skipped); a new TRIG on voice 1 at block 5 (note 60) = its run from its frozen phases; a TRIG while sounding is not pending
    here (the ARM fades first); voices 2 / 3 at gain 0 untouched; the OSC1 block back as it was after each block, X(NOTE) untouched;
  * the sample: two voices (TV 1 = the track's sample, TV $107 = sample 7), mono: the sum of the one-voice runs with the gain; stereo (WAVE 100):
    the ring = the mid and the granular's side buffer = the side of (sum of g x L, sum of g x R), against the bit-exact model;
  * the poly word in the two-oscillator mode: the one-voice path (the same ring as without it);
  * the program ends at or below P:$3FFF.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import emu_smstereo_dsp as S  # noqa: E402
from emu_masterfx_dsp import s24, u24  # noqa: E402
import granular_dsp as GD  # noqa: E402
V = S.V
N, RING, OSB = S.N, S.RING, S.OSB
s56, lim, mpy = S.s56, S.lim, S.mpy
PVW = V.OS2B0 + V.PV_OFF - OSB                       # the poly word, as an index of the dumped OSC blocks (144 words from OSB0)
REC, RS = V.PV_REC0, V.PV_RS
T = 0x400000
SMP = {3: (0x40000, 300), 4: (0x48000, 260), 7: (0x50000, 280), 8: (0x58000, 240)}


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    progs = {}
    for name, im, mf in (("new", img, man), ("old", prev, pman)):
        sp = dsp_program(im)
        progs[name] = ([int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)], int(mf["report"]["sc16"]["dsp_labels"]["vpre"], 16))
    pw = progs["new"][0]
    seq = [0x0C1D20, 0x21C400, 0x47F400, 0x020800, 0x2000C2, 0x21C400]
    swap = any(pw[i:i + 6] == seq for i in range(len(pw) - 6))             # (use_smswap) the side negated, the width WAVE x $10410
    def side(l, r, wave):
        d = lim(s56(((s24(l) << 24) - (s24(r) << 24)) >> 1))
        if not swap: return lim(mpy(d, wave << 16))
        w = lim(s56(((wave << 16) << 24) + mpy(wave << 16, 0x20800)))
        return lim(s56(-mpy(w, d)))
    check(len(progs["new"][0]) <= 0x4000, f"core 0's program ends at P:${len(progs['new'][0]):x} (the previous build: ${len(progs['old'][0]):x})")
    ydat = {}
    for k, (st, ln) in SMP.items():
        for i in range(ln + 200): ydat[st + i] = u24(int((0x300000 + 0x40000 * k) * ((i * (11 + 6 * k) % 180) - 90) / 90)) & 0xFFFF00
    Y = lambda a_: ydat.get(a_, 0)
    tab = {}
    for slot in range(64): tab[V.SM_TAB + 4 * slot], tab[V.SM_TAB + 4 * slot + 1] = 0x60000, 100
    for k, (st, ln) in SMP.items(): tab[V.SM_TAB + 4 * k], tab[V.SM_TAB + 4 * k + 1] = st, ln
    mem_tab = [('x', a_, [v_]) for a_, v_ in tab.items()]
    mem_y = [('y', a_, [v_]) for a_, v_ in ydat.items()]

    def go(which, act, note, osc, blocks, recs=None, events=None, pw=50, wave=0, dual=False):
        """blocks of vpre; osc = {word: value} of the OSC1 block; recs = the 4 records (lists of 28) or None (one voice); events[b] = a function
        (osb, recs) -> None run before block b.  Returns per block: the ring's left samples, the side buffer, the OSC1 block, the records"""
        P, vpre = progs[which]
        blk = [0] * (2 * V.VBS)
        for kk, v in dict(GAIN=64, DEC=40, SUS=100, REL=40, LRATE=0, FXMOD=64, NOTE=note, ACT=act).items():
            blk[dict(GAIN=V.P_GAIN, DEC=V.P_DEC, SUS=V.P_SUS, REL=V.P_REL, LRATE=V.P_LRATE, FXMOD=V.P_FXMOD, NOTE=V.NOTE, ACT=V.ACT)[kk]] = v
        osb = [0] * 144
        osb[2] = wave; osb[3] = pw
        for w_, v_ in osc.items(): osb[w_] = v_
        if dual: osb[V.DFLAGS_OFF] = 2
        rec = [0] * (RS * V.PV_N) if recs is None else [x for r in recs for x in r]
        if recs is not None: osb[PVW] = REC
        sf = [0, 0]
        rd = 0x40
        outs, sides, osbs, recs_ = [], [], [], []
        for b in range(blocks):
            if events and b in events: events[b](osb, rec)
            res, ran = run(P, vpre, mem=[('x', 0x3A, [N]), ('x', V.VB0, blk), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, [0] * (2 * N)),
                                         ('x', OSB, osb), ('x', GD.RDOFS, [rd]), ('x', GD.SOUT, [0] * 128), ('x', V.SIDE0, sf), ('x', REC, rec)] + mem_tab + mem_y,
                           dumps=[('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', OSB, 144), ('x', GD.SOUT, 128), ('x', V.SIDE0, 2), ('x', REC, RS * V.PV_N)],
                           regs_code=[], maxins=8_000_000)
            assert 'pc=00' in ran, ran
            blk, osb, sf, rec = res[('x', V.VB0)], list(res[('x', OSB)]), res[('x', V.SIDE0)], list(res[('x', REC)])
            outs.append(res[('y', RING)][0::2]); sides.append(res[('x', GD.SOUT)][rd:rd + 32]); osbs.append(list(osb)); recs_.append(list(rec))
        gc.collect()
        return outs, sides, osbs, recs_, blk

    def record(note, tgt, trig, tv=1, seen=0, g=0, state=None):
        r = [0] * RS
        if state: r[:21] = state
        r[V.PV_NOTE], r[V.PV_TGT], r[V.PV_TRIG], r[V.PV_SEEN], r[V.PV_G], r[V.PV_TV] = note, tgt, trig, seen, g, tv
        return r
    def mix(ring, gs, xs):                                                    # ring += g x s, the DSP's mac and limit
        return [lim(s56((s24(r) << 24) + mpy(g, x))) for r, g, x in zip(ring, gs, xs)]
    def ramp(g0, g1):                                                         # the gains of one block from g0 to g1
        inc = (g1 - g0) >> 5
        return [u24(g0 + inc * (i + 1)) for i in range(N)]
    def state_of(r):                                                          # a record's state as OSC1 words (28..47, 10)
        d = {28 + i: r[i] for i in range(20)}; d[10] = r[20]; return d

    # ---- one voice: as PREV
    for act, osc, pw, wave, nm in ((2, {}, 50, 0, "the sine"), (2, {}, 50, 84, "the saw"), (2, {}, 100, 84, "the supersaw"),
                                   (3, {8: 3, V.SM_N: 1}, 50, 0, "the sample, mono"), (3, {8: 3, V.SM_N: 1, V.SM_K: 1}, 50, 100, "the sample, stereo")):
        on_, sn_, qn, _, _ = go("new", act, 57, osc, 3, pw=pw, wave=wave); oo, so, qo, _, _ = go("old", act, 57, osc, 3, pw=pw, wave=wave)
        sides_too = not (swap and wave)                                           # (use_smswap: the stereo's side changed on purpose; emu_smswap_dsp)
        check(on_ == oo and (sn_ == so or not sides_too) and [q[:96] for q in qn] == [q[:96] for q in qo] and any(any(x) for x in on_),
              f"one voice, {nm}: the ring{', the side buffer' if sides_too else ''} and the OSC1 blocks as the previous build's")

    # ---- the oscillator, two voices
    for pw, wave, nm in ((50, 84, "saw"), (100, 84, "supersaw"), (50, 0, "sine")):
        BL = 8
        recs = [record(48, T, 1), record(55, T, 1), record(0, 0, 0), record(0, 0, 0)]
        def ev3(osb, rec): rec[RS + V.PV_TGT] = 0                            # voice 1 off
        def ev5(osb, rec): rec[RS + V.PV_NOTE] = 60; rec[RS + V.PV_TGT] = T; rec[RS + V.PV_TRIG] = 2
        po, ps, pq, pr, pblk = go("new", 2, 64, {}, BL, recs=recs, events={3: ev3, 5: ev5}, pw=pw, wave=wave)
        m0, _, _, _, _ = go("new", 2, 48, {}, BL, pw=pw, wave=wave)
        m1, _, _, _, _ = go("new", 2, 55, {}, 4, pw=pw, wave=wave)
        st1 = state_of(pr[3][RS:2 * RS])                                      # voice 1 frozen after its fade (block 3)
        m1b, _, _, _, _ = go("new", 2, 60, st1, 3, pw=pw, wave=wave)
        exp = []
        for b in range(BL):
            r = mix([0] * N, ramp(0, T) if b == 0 else [T] * N, m0[b])
            if b < 4: r = mix(r, ramp(0, T) if b == 0 else ramp(T, 0) if b == 3 else [T] * N, m1[b])     # voice 1: on, then its fade at block 3
            if b >= 5: r = mix(r, ramp(0, T) if b == 5 else [T] * N, m1b[b - 5])                          # silent at 4; note 60 from its frozen state
            exp.append(r)
        bad = [b for b in range(BL) if po[b] != exp[b]]
        check(not bad and any(any(x) for x in po), f"the {nm}, two voices (48 / 55): the sum x the gains block by block, voice 1 fading at block 3, back on "
              f"note 60 at block 5 from its frozen phases (bad blocks {bad[:4]}{'' if not bad else ': ' + str([hex(x) for x in po[bad[0]][:3]]) + ' / ' + str([hex(x) for x in exp[bad[0]][:3]])})")
        check(pr[4][RS:2 * RS] == pr[3][RS:2 * RS] and pr[4][RS + V.PV_G] == 0, f"the {nm}: voice 1 silent at block 4, its record untouched")
        check(all(r[2 * RS:] == recs[2] + recs[3] for r in pr), f"the {nm}: voices 2 / 3 (gain 0) untouched")
        own = [10] + list(range(28, 34)) + [40, 41] + list(range(44, 48))
        check(pblk[V.NOTE] == 64 and all(not any(q[w_] for w_ in own) for q in pq), f"the {nm}: X(NOTE) untouched, the OSC1 block's own words back after each block")
        check(pr[0][V.PV_SEEN] == 1 and pr[5][RS + V.PV_SEEN] == 2 and pr[0][V.PV_G] == T, f"the {nm}: TSEEN follows TRIG, G = the target")

    # ---- the sample, two voices
    for wave, nm in ((0, "mono"), (100, "stereo")):
        BL = 4
        osc = {8: 3, V.SM_K: 1}
        recs = [record(60, T, 1, tv=1), record(60, T, 1, tv=0x107), record(0, 0, 0), record(0, 0, 0)]
        for r in recs: r[V.SM_K - 28] = 1                                     # the ARM writes K into the records too (the exchange then leaves OSC1 + 43 alone)
        po, ps, pq, pr, _ = go("new", 3, 70, osc, BL, recs=recs, wave=wave)
        if wave == 0:
            m0, _, _, _, _ = go("new", 3, 60, {**osc, V.SM_N: 1}, BL, wave=0)
            m1, _, _, _, _ = go("new", 3, 60, {**osc, V.SM_N: 0x107}, BL, wave=0)
            exp = [mix(mix([0] * N, ramp(0, T) if b == 0 else [T] * N, m0[b]), ramp(0, T) if b == 0 else [T] * N, m1[b]) for b in range(BL)]
            bad = [b for b in range(BL) if po[b] != exp[b]]
            check(not bad and any(any(x) for x in po), f"the sample, {nm}: two voices (samples 3 / 7) = the sum x the gains (bad blocks {bad[:4]})")
        else:
            good = True; bad = None
            pos = 0
            for b in range(BL):
                L0, _, _ = S.interp(Y, SMP[3][0], pos, 0, 1, 0, N); R0, _, _ = S.interp(Y, SMP[4][0], pos, 0, 1, 0, N)
                L1, _, _ = S.interp(Y, SMP[7][0], pos, 0, 1, 0, N); R1, _, _ = S.interp(Y, SMP[8][0], pos, 0, 1, 0, N)
                g = ramp(0, T) if b == 0 else [T] * N
                sl = mix(mix([0] * N, g, L0), g, L1); sr = mix(mix([0] * N, g, R0), g, R1)
                M_ = [lim(s56(((s24(l) << 24) + (s24(r) << 24)) >> 1)) for l, r in zip(sl, sr)]
                S_ = [side(l, r, 100) for l, r in zip(sl, sr)]
                if po[b] != M_ or ps[b] != S_: good = False; bad = bad or (b, [hex(x) for x in po[b][:3]], [hex(x) for x in M_[:3]], [hex(x) for x in ps[b][:3]], [hex(x) for x in S_[:3]])
                pos += N
            check(good, f"the sample, {nm}: two voices (3 + 4, 7 + 8): the ring = the mid, the side buffer = the side of the sums x the gains, bit-exact ({bad or ''})")
        check(pr[0][V.SM_S - 28] == SMP[3][0] and pr[0][RS + V.SM_S - 28] == SMP[7][0], f"the sample, {nm}: each voice's own sample in its record (TV 1 = the track's 3, TV $107 = 7)")

    # ---- two oscillators: the poly word changes nothing
    recs = [record(48, T, 1), record(55, T, 1), record(0, 0, 0), record(0, 0, 0)]
    po, _, _, _, _ = go("new", 2, 57, {}, 3, recs=recs, wave=84, dual=True); oo, _, _, _, _ = go("new", 2, 57, {}, 3, wave=84, dual=True)
    check(po == oo and any(any(x) for x in po), "two oscillators: with the poly word set, the one-voice path (the same ring)")
    print(f"{man.get('marker', '?')} POLY DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
