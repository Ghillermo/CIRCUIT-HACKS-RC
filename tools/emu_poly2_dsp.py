"""SC47.3 DSP test (vcf21_dsp.use_poly2): the polyphony of the own synth with two oscillators and in the VA-drum.

    python tools/emu_poly2_dsp.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json      (PREV = SC47.2 / Beta 3.29)

vpre once a block on the interpreter with each build's real core-0 program (emu_poly_dsp's harness, plus the records' extension in Y:PV_Y0), MIDI 1's
chain neutral (GAIN 64, no envelope amount, no filter: the ring = the source):
  * one voice (the poly word 0): two oscillators and the VA-drum as PREV's (the ring and the OSC blocks bit for bit);
  * two oscillators, two voices (notes 48 / 55): the sum of two one-voice runs (NOTE2 = the note) x the gain that goes from 0 to the target over
    the first block, then the target; each voice keeps its own second oscillator (its phase back in the extension after the block);
  * the VA-drum, voice A (note 48) from block 0 and voice B (note 55) from block 3: the ring = A alone + B alone, block by block (B's hit does not
    restart A: each voice its own pitch and amplitude envelopes), the noise off; A's amplitude envelope decays (the extension's + 1) and its pitch
    envelope too (OSC1 + 23 swapped: the extension's + 0); A's gain = its target x its envelope;
  * the VA-drum with the noise on: a second voice at target 0 changes nothing (no noise of its own);
  * the VA-drum in poly with GAIN 0 / ENVA +63 (the usual VA-drum set-up): the VCA's envelope term is 1.0 (the voice's envelope does the shape): the
    ring's late blocks as loud relative to the early ones as with GAIN 64 / ENVA 0.
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
PVW = V.OS2B0 + V.PV_OFF - OSB
REC, RS = V.PV_REC0, V.PV_RS
YX = V.PV_Y0
T = 0x400000


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    import poly as _PL
    _PL.adopt(man["report"])                                                          # (SC47.6: the six-record layout)
    progs = {}
    for name, im, mf in (("new", img, man), ("old", prev, pman)):
        sp = dsp_program(im)
        progs[name] = ([int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)], int(mf["report"]["sc16"]["dsp_labels"]["vpre"], 16))
    check(len(progs["new"][0]) <= 0x4000, f"core 0's program ends at P:${len(progs['new'][0]):x} (the previous build: ${len(progs['old'][0]):x})")

    def go(which, note, blocks, recs=None, events=None, wave=84, pw=50, dflags=0, note2=None, par=None):
        P, vpre = progs[which]
        blk = [0] * (2 * V.VBS)
        prm = dict(GAIN=64, DEC=40, SUS=100, REL=40, LRATE=0, FXMOD=64, ENVA=0, NOTE=note, ACT=2, VEL=127)
        prm.update(par or {})
        for kk, v in prm.items():
            blk[dict(GAIN=V.P_GAIN, DEC=V.P_DEC, SUS=V.P_SUS, REL=V.P_REL, LRATE=V.P_LRATE, FXMOD=V.P_FXMOD, ENVA=V.P_ENVA, NOTE=V.NOTE, ACT=V.ACT,
                     VEL=V.VEL)[kk]] = v & 0xFFFFFF
        osb = [0] * 144
        osb[2] = wave; osb[3] = pw; osb[V.DFLAGS_OFF] = dflags; osb[V.NOTE2_OFF] = note if note2 is None else note2
        rec = [0] * (RS * V.PV_N) if recs is None else [x for r in recs for x in r]
        if recs is not None: osb[PVW] = REC
        ext = [0] * (RS * V.PV_N)
        sf = [0, 0]
        outs, osbs, recs_, exts = [], [], [], []
        for b in range(blocks):
            if events and b in events: events[b](osb, rec)
            res, ran = run(P, vpre, mem=[('x', 0x3A, [N]), ('x', V.VB0, blk), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, [0] * (2 * N)),
                                         ('x', OSB, osb), ('x', GD.RDOFS, [0x40]), ('x', GD.SOUT, [0] * 128), ('x', V.SIDE0, sf), ('x', REC, rec), ('y', YX, ext)],
                           dumps=[('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', OSB, 144), ('x', V.SIDE0, 2), ('x', REC, RS * V.PV_N), ('y', YX, RS * V.PV_N)],
                           regs_code=[], maxins=12_000_000)
            assert 'pc=00' in ran, ran
            blk, osb, sf, rec, ext = res[('x', V.VB0)], list(res[('x', OSB)]), res[('x', V.SIDE0)], list(res[('x', REC)]), list(res[('y', YX)])
            outs.append(res[('y', RING)][0::2]); osbs.append(list(osb)); recs_.append(list(rec)); exts.append(list(ext))
        gc.collect()
        return outs, osbs, recs_, exts

    def record(note, tgt, trig, seen=0):
        r = [0] * RS
        r[V.PV_NOTE], r[V.PV_TGT], r[V.PV_TRIG], r[V.PV_SEEN] = note, tgt, trig, seen
        return r
    def mix(ring, gs, xs): return [lim(s56((s24(r) << 24) + mpy(g, x))) for r, g, x in zip(ring, gs, xs)]
    def ramp(g0, g1):
        inc = (g1 - g0) >> 5
        return [u24(g0 + inc * (i + 1)) for i in range(N)]
    def add(xs, ys): return [lim(s56((s24(x) << 24) + (s24(y) << 24))) for x, y in zip(xs, ys)]

    # ---- one voice: as PREV
    for nm, kw in (("two oscillators", dict(dflags=2)), ("two oscillators, supersaw", dict(dflags=2, pw=100)), ("the VA-drum", dict(dflags=4, wave=0))):
        on_, qn, _, _ = go("new", 57, 4, note2=64, **kw); oo, qo, _, _ = go("old", 57, 4, note2=64, **kw)
        if getattr(V, "GLIDE", False) or "GK_OFF" in dir(V):                     # (SC47.5: the glide's last note, OSC2 + LN_OFF, is written: not compared)
            qn = [[x for i, x in enumerate(q) if i % 48 not in (V.GK_OFF, V.LN_OFF) or i < 96] for q in qn]
            qo = [[x for i, x in enumerate(q) if i % 48 not in (V.GK_OFF, V.LN_OFF) or i < 96] for q in qo]
        check(on_ == oo and qn == qo and any(any(x) for x in on_), f"one voice, {nm}: the ring and the OSC blocks as the previous build's")

    # ---- two oscillators, two voices
    for pw, nm in ((50, "saw"), (100, "supersaw")):
        BL = 5
        recs = [record(48, T, 1), record(55, T, 1), record(0, 0, 0), record(0, 0, 0)]
        po, pq, pr, px = go("new", 64, BL, recs=recs, dflags=2, pw=pw)
        m0, q0, _, _ = go("new", 48, BL, dflags=2, pw=pw)
        m1, q1, _, _ = go("new", 55, BL, dflags=2, pw=pw)
        exp = [mix(mix([0] * N, ramp(0, T) if b == 0 else [T] * N, m0[b]), ramp(0, T) if b == 0 else [T] * N, m1[b]) for b in range(BL)]
        bad = [b for b in range(BL) if po[b] != exp[b]]
        check(not bad and any(any(x) for x in po), f"two oscillators ({nm}), two voices (48 / 55): the sum x the gains block by block (bad blocks {bad[:4]}"
              f"{'' if not bad else ': ' + str([hex(x) for x in po[bad[0]][:3]]) + ' / ' + str([hex(x) for x in exp[bad[0]][:3]])})")
        o2 = lambda q: [q[96 + 10], q[96 + 20], q[96 + 22]] + q[96 + 28:96 + 34]
        check(px[-1][V.YX_O2:V.YX_O2 + 9] == o2(q0[-1]) and px[-1][RS + V.YX_O2:RS + V.YX_O2 + 9] == o2(q1[-1]) and o2(q0[-1]) != o2(q1[-1]),
              f"two oscillators ({nm}): each voice's second oscillator in its extension (its phase, sync, supersaw), as the one-voice runs'")

    # ---- the VA-drum: A from block 0, B from block 3, the noise off (LRATE -64)
    BL = 8
    vd = dict(dflags=4, wave=0, par=dict(LRATE=-64, DEC=60, SUS=90))
    def evB(osb, rec): rec[RS + V.PV_NOTE] = 55; rec[RS + V.PV_TGT] = T; rec[RS + V.PV_TRIG] = 1
    pab, _, pr, px = go("new", 64, BL, recs=[record(48, T, 1), record(0, 0, 0), record(0, 0, 0), record(0, 0, 0)], events={3: evB}, **vd)
    pa, _, pra, pxa = go("new", 64, BL, recs=[record(48, T, 1), record(0, 0, 0), record(0, 0, 0), record(0, 0, 0)], **vd)
    pb, _, _, _ = go("new", 64, BL, recs=[record(0, 0, 0), record(0, 0, 0), record(0, 0, 0), record(0, 0, 0)], events={3: evB}, **vd)
    bad = [b for b in range(BL) if pab[b] != add(pa[b], pb[b])]
    check(not bad and any(pb[3]), f"the VA-drum: A (block 0) + B (block 3) = A alone + B alone, block by block: B's hit does not restart A (bad blocks {bad[:4]})")
    envs = [x[V.YX_ENV] for x in pxa]; eps = [x[V.YX_EP] for x in pxa]
    check(envs[0] > 0 and all(envs[i + 1] < envs[i] for i in range(1, BL - 1)) and all(eps[i + 1] < eps[i] for i in range(BL - 1)),
          f"the VA-drum: A's amplitude envelope and pitch envelope decay block by block ({[hex(x) for x in envs[:4]]}, {[hex(x) for x in eps[:4]]})")
    pk = lambda o: max(abs(s24(x)) for x in o)
    gs = [r[V.PV_G] for r in pra]
    check(all(gs[k] == lim(mpy(T, envs[k])) for k in range(BL)) and gs[-1] < gs[1], f"the VA-drum: A's gain = its target x its envelope each block ({[hex(x) for x in gs[:4]]})")
    # ---- the noise on: a voice at target 0 adds nothing
    vdn = dict(dflags=4, wave=0, par=dict(LRATE=60, DEC=60, SUS=90))
    n1, _, _, _ = go("new", 64, 4, recs=[record(48, T, 1), record(0, 0, 0), record(0, 0, 0), record(0, 0, 0)], **vdn)
    n2, _, _, _ = go("new", 64, 4, recs=[record(48, T, 1), record(55, 0, 1), record(0, 0, 0), record(0, 0, 0)], **vdn)
    n0, _, _, _ = go("new", 64, 4, recs=[record(48, T, 1), record(0, 0, 0), record(0, 0, 0), record(0, 0, 0)], par=dict(LRATE=-64, DEC=60, SUS=90), dflags=4, wave=0)
    check(n1 == n2 and n1 != n0, "the VA-drum with the noise: the voice's noise there (not the same as without it), a silent voice adds none")
    # ---- the VCA open: GAIN 0 / ENVA +63 shapes as GAIN 64 / ENVA 0
    vg, _, _, _ = go("new", 64, BL, recs=[record(48, T, 1), record(0, 0, 0), record(0, 0, 0), record(0, 0, 0)], dflags=4, wave=0, par=dict(LRATE=-64, DEC=60, SUS=90, GAIN=0, ENVA=63))
    ra, rg = pk(pa[BL - 1]) / max(1, pk(pa[2])), pk(vg[BL - 1]) / max(1, pk(vg[2]))
    check(pk(vg[2]) > 0 and abs(ra - rg) < 0.05 + 0.1 * ra, f"the VA-drum in poly, GAIN 0 / ENVA +63: the VCA open, the voice's envelope does the shape (late / early {rg:.3f} against {ra:.3f})")
    print(f"{man.get('marker', '?')} POLY2 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
