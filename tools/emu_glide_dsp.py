"""SC47.5 DSP test (vcf21_dsp.use_glide): the oscillator's pitch offset (OSC1 + GO_OFF): the portamento's glide (one voice) and the unison's detune
(a voice's record word).

    python tools/emu_glide_dsp.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json      (PREV = SC47.4 / Beta 3.31)

vpre once a block on the interpreter (emu_poly3_dsp's harness), MIDI 1 in the oscillator (ACT 2, one oscillator), the chain neutral:
  * the glide off (GK 0): the ring as the previous build's, with the note held and with a note change (60 -> 72);
  * the glide on (GK = vmode.gk(48)): after the change the offset follows GO = (GO - 12 << 16) x GK, then x GK each block (the DSP's fixed point),
    the oscillator's increment rises block by block towards the note's and ends as the previous build's at note 72 (GO 0);
  * a poly voice with its record's offset word = 5 x 512 sounds bit for bit as a voice with FINE + 5 and no offset (the unison's detune).
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
import vmode as VM  # noqa: E402
import poly as PL  # noqa: E402
V = S.V
N, RING, OSB = S.N, S.RING, S.OSB
PVW = V.OS2B0 + V.PV_OFF - OSB
REC, RS = V.PV_REC0, V.PV_RS
GO = V.GO_OFF
GK = V.OS2B0 - OSB + V.GK_OFF
LN = V.OS2B0 - OSB + V.LN_OFF
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

    def go(which, notes, gk=0, recs=None, fine=0, osb0=None):
        P, vpre = progs[which]
        blk = [0] * (2 * V.VBS)
        for k_, v_ in ((V.P_GAIN, 64), (V.P_DEC, 40), (V.P_SUS, 100), (V.P_REL, 40), (V.P_FXMOD, 64), (V.ACT, 2), (V.VEL, 127)):
            blk[k_] = v_
        osb = list(osb0) if osb0 else [0] * 144
        osb[1] = fine; osb[GK] = gk; osb[LN] = notes[0]
        rec = [0] * (RS * V.PV_N)
        if recs is not None:
            osb[PVW] = REC
            for i, r in enumerate(recs): rec[RS * i:RS * i + RS] = r
        outs, gos, incs = [], [], []
        for nt in notes:
            blk[V.NOTE] = nt
            res, ran = run(P, vpre, mem=[('x', 0x3A, [N]), ('x', V.VB0, blk), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, [0] * (2 * N)),
                                         ('x', OSB, osb), ('x', GD.RDOFS, [0x40]), ('x', GD.SOUT, [0] * 128), ('x', V.SIDE0, [0, 0]), ('x', REC, rec),
                                         ('y', V.PV_Y0, [0] * (RS * V.PV_N))],
                           dumps=[('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', OSB, 144), ('x', REC, RS * V.PV_N)], regs_code=[], maxins=20_000_000)
            assert 'pc=00' in ran, ran
            blk, osb, rec = res[('x', V.VB0)], list(res[('x', OSB)]), list(res[('x', REC)])
            outs.append(res[('y', RING)][0::2]); gos.append(s24(osb[GO])); incs.append(osb[11])
        gc.collect()
        return outs, gos, incs, osb

    notes = [60] * 3 + [72] * 4
    on_, _, _, _ = go("new", notes); oo, _, _, _ = go("old", notes)
    check(on_ == oo and any(any(x) for x in on_), "the glide off: the ring as the previous build's (a note change too)")
    def model(notes, g):
        want, go_m, ln = [], 0, notes[0]
        for nt in notes:
            x = go_m - ((nt - ln) << 16); ln = nt
            x = max(-0x800000, min(0x7FFFFF, x))
            prod = x * g * 2
            go_m = (prod >> 24) + (1 if prod < 0 else 0)                           # the DSP's: towards 0
            want.append(go_m)
        return want
    g = VM.gk(48)
    notes = [60] * 3 + [72] * 8
    gn, gos, incs, osb = go("new", notes, gk=g)
    want = model(notes, g)
    check(gos == want and gos[3] < 0, f"the offset block by block = (GO - (note - last) << 16) x GK ({gos[3:7]} / {want[3:7]})")
    g = VM.gk(1)                                                                       # the shortest: settled within 45 blocks
    notes = [60] * 2 + [72] * 45
    gn, gos, incs, osb = go("new", notes, gk=g)
    ro, _, rinc, _ = go("old", [72] * 3)
    mono = all(incs[i] <= incs[i + 1] for i in range(2, len(incs) - 1))
    check(gos == model(notes, g) and mono and incs[2] < rinc[-1] and gos[-1] == 0 and incs[-1] == rinc[-1],
          f"the increment rises towards note 72's ({incs[2]:#x} .. {incs[-1]:#x} / {rinc[-1]:#x}), GO ends at {gos[-1]}")
    # ---- a voice's offset word = FINE
    def record(note, dt=0):
        r = [0] * RS
        r[V.PV_NOTE], r[V.PV_TGT], r[V.PV_TRIG] = note, T, 1
        r[V.GO_OFF - 28] = dt & 0xFFFFFF
        return r
    blank = [0] * RS
    a_, _, _, _ = go("new", [64] * 4, recs=[record(64, 5 * 512), blank, blank, blank])
    b_, _, _, _ = go("new", [64] * 4, recs=[record(64, 0), blank, blank, blank], fine=5)
    c_, _, _, _ = go("new", [64] * 4, recs=[record(64, 0), blank, blank, blank])
    check(a_ == b_ and a_ != c_ and any(any(x) for x in a_), "a poly voice's offset word 5 x 512 = FINE + 5, bit for bit (and differs from no offset)")
    print(f"{man.get('marker', '?')} GLIDE DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
