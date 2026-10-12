"""SC23.6 DSP tests: the type knobs.  The FX type (code 13) and the filter type (code 16) arrive as p = 0..127; the mailbox keeps the zone t = 7 p >> 7 in the slot of the code and the position inside the
zone f = 7 p & 127 in FXMOD (FX) / in the key-follow word of the oscillator block (filter); code 14 (FXMOD) is ignored.  The filter cutoff then follows the note by f / 128 table steps per semitone.

    python tools/emu_sc23_6_dsp.py SC23.6.bin SC23.6_manifest.json SC23.5.bin
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
from emu_masterfx_dsp import s24, u24  # noqa: E402
import drums2_dsp as DD  # noqa: E402
import vcf21_dsp as V  # noqa: E402
import vcf21 as A  # noqa: E402
V.TILT, V.FB, V.SLOPES, V.FXMORE, V.BISEND, V.PLIMIT, V.OSC, V.VFF = False, True, True, True, True, 0x4000, True, True
V.use_osc3(); V.use_gaterel(); V.use_sinefix(); V.use_gatefix(); V.use_typezones()
A.use_osc3(); A.use_neutral()

N, RING = 32, 0x1000
OSB = V.OSB0
NAMES = ("FILT", "RES", "ENVF", "LFOF", "ATK", "DEC", "SUS", "REL", "FXAMT", "GAIN", "LRATE", "LFOV", "FXTYPE", "FXMOD", "ENVA", "FTYPE")


def main(img, man, prev):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    dl = {k: int(v, 16) for k, v in man["report"]["sc16"]["dsp_labels"].items()}
    P0 = [int.from_bytes(dsp_program(img)[i:i + 3], 'big') for i in range(0, len(dsp_program(img)), 3)]
    off = dict(zip(NAMES, range(2, 18)))
    neutral = {n: A.DEFAULTS[i] for i, n in enumerate(NAMES)}
    tf = lambda idx: P0[dl["TF"] + idx]
    check(len(P0) <= 0x4000, f"the DSP program fits in the P RAM ({len(P0):#x} words)")

    def fresh(act, note=60, **kw):
        b = [0] * (2 * V.VBS)
        for n, v in {**neutral, **kw}.items(): b[off[n]] = v & 0xFFFFFF
        b[V.ACT], b[V.NOTE] = act, note
        return b

    def step(blk, osb, msgs=(), gate=None):
        """one block of vpre with the mailbox messages [(voice, code, value)] (the tag of each voice alternates)"""
        for v, code, val in msgs:
            tag = ((blk[V.VBS * v + 1] >> 23) & 1) ^ 1
            blk[V.VBS * v] = (tag << 23) | (code << 16) | (val & 0xFFFF)
        res, ran = run(P0, dl["vpre"], mem=[('x', 0x3A, [N]), ('x', V.VB0, blk), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, [0] * (2 * N)), ('x', OSB, osb)],
                       dumps=[('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', OSB, 96)], regs_code=[])
        assert 'pc=00' in ran, ran
        return res[('x', V.VB0)], res[('x', OSB)]

    # ---- the mailbox: zone and position inside the zone
    for t in (0, 1):
        base = V.VBS * t
        blk, osb = fresh(1), [0] * 96
        for p in (0, 17, 18, 19, 36, 60, 100, 126, 127):
            blk, osb = step(blk, osb, [(t, 13, p)])
            want_t, want_f = (7 * p) >> 7, (7 * p) & 127
            check(blk[base + off["FXTYPE"]] == want_t and blk[base + off["FXMOD"]] == want_f, f"voice {t + 1}: FX type message {p}: zone {blk[base + off['FXTYPE']]} (expected {want_t}), FXMOD = {blk[base + off['FXMOD']]} (expected {want_f})")
        before = blk[base + off["FXMOD"]]
        blk, osb = step(blk, osb, [(t, 14, 99)])
        check(blk[base + off["FXMOD"]] == before, f"voice {t + 1}: a message for code 14 (FXMOD) is ignored ({blk[base + off['FXMOD']]})")
        for p in (0, 18, 19, 36, 100, 127):
            blk, osb = step(blk, osb, [(t, 16, p)])
            want_t, want_f = (7 * p) >> 7, (7 * p) & 127
            check(blk[base + off["FTYPE"]] == want_t and osb[48 * t + V.KEYF_OFF] == want_f, f"voice {t + 1}: filter type message {p}: zone {blk[base + off['FTYPE']]} (expected {want_t}), key follow = {osb[48 * t + V.KEYF_OFF]} (expected {want_f})")
        # the other codes are stored as before, the other voice is untouched
        blk, osb = step(blk, osb, [(t, 1, -5 & 0xFFFF)])
        check(s24(blk[base + off["FILT"]]) == -5, f"voice {t + 1}: FILT message still stored (-5)")
        blk, osb = step(blk, osb, [(t, 24, 33)])
        check(osb[48 * t + 2] == 33 and osb[48 * t + V.KEYF_OFF] == (7 * 127) & 127, f"voice {t + 1}: an oscillator message (code 24 -> WAVE {osb[48 * t + 2]}) leaves the key follow alone ({osb[48 * t + V.KEYF_OFF]})")
        o = 1 - t
        check(blk[V.VBS * o + off["FTYPE"]] == 0 and osb[48 * o + V.KEYF_OFF] == 0, "the other voice is untouched")

    # ---- the key follow of the filter cutoff: FF = TF[(FILT + 64) / 2 + (note - 60) f / 128]
    def ff(note, p, filt=0):
        blk, osb = fresh(1, note, FILT=filt), [0] * 96
        blk, osb = step(blk, osb, [(0, 16, p)])
        blk, osb = step(blk, osb)
        return blk[V.FF], blk[off["FTYPE"]], blk[V.FMODE]

    def idx_of(v): return next(i for i in range(64) if tf(i) == v)
    for p, f in ((36, 124), (19, 5)):
        i60, ty, fm = ff(60, p); i72, _, _ = ff(72, p); i48, _, _ = ff(48, p); i84, _, _ = ff(84, p)
        i60, i72, i48, i84 = idx_of(i60), idx_of(i72), idx_of(i48), idx_of(i84)
        check(ty == 1 and fm == 1, f"p = {p}: filter type zone {ty} (LP 12 dB), FMODE {fm}")
        check(i60 == 32, f"p = {p}: note 60 is the centre, table index {i60} (FILT 0 = 32)")
        e72, e48, e84 = 32 + 12 * f / 128, 32 - 12 * f / 128, min(63, 32 + 24 * f / 128)
        check(abs(i72 - e72) <= 1 and abs(i48 - e48) <= 1 and abs(i84 - e84) <= 1.01, f"p = {p} (follow {f}): the index follows the note: 48 -> {i48} (exp {e48:.1f}), 72 -> {i72} ({e72:.1f}), 84 -> {i84} ({e84:.1f})")
    # type 0 (DJ) with a modulation depth: key follow 0 (p = 0 .. 18 -> f = 7 p)
    a0, ty0, _ = ff(72, 0); b0, _, _ = ff(48, 0)
    check(ty0 == 0 and a0 == b0, f"p = 0 (DJ, follow 0): the note does not move the cutoff ({a0:#x}, {b0:#x})")
    # the FX parameters follow the zone's position: wavefold (zone 3) takes the bias from it, the others the threshold
    blk, osb = fresh(1, 60, FXAMT=100), [0] * 96
    blk, osb = step(blk, osb, [(0, 13, 70)])
    blk, osb = step(blk, osb)
    want_t, want_f = (7 * 70) >> 7, (7 * 70) & 127
    check(blk[off["FXTYPE"]] == want_t == 3 and blk[V.FXB] == (((want_f - 64) << 16) & 0xFFFFFF), f"p = 70: wavefold (zone {blk[off['FXTYPE']]}), FXMOD {want_f}: bias {blk[V.FXB]:#x}")
    # ---- cost against SC23.5
    from dsp_session import Session
    def sess(image, vals):
        ss = Session(image)
        extra = [('y', 0x1000 + i, u24(int(0x300000 * math.sin(i * 0.31)))) for i in range(0x400)] + [('x', V.VB0 + o_, v) for o_, v in vals.items()]
        res, rans = ss.run(blocks=24, per_block=True, extra=extra, spmax=True, dumps=[('x', V.VB0, 2 * V.VBS)])
        return rans
    ins = lambda rans: [int(x.split('ins=')[1].split()[0]) for x in rans if x.startswith('RAN')][2:]
    spm = lambda rans: int([x for x in rans if x.startswith('SPMAX')][0].split()[1])
    avg = lambda v: sum(v) / len(v)
    both = {}
    for t in (0, 1):
        for n_, v in {**neutral, "NOTE": 60, "GATE": 1, "ACT": 1, "VEL": 100, "GNEW": 1}.items():
            o_ = {**off, "GATE": V.GATE, "NOTE": V.NOTE, "ACT": V.ACT, "VEL": V.VEL, "GNEW": V.GNEW}[n_]
            both[V.VBS * t + o_] = v & 0xFFFFFF
    rp, ro = sess(prev, both), sess(img, both)
    print(f"     DSP instructions/block, both voices on the line input: SC23.5 {avg(ins(rp)):.0f}, SC23.6 {avg(ins(ro)):.0f}")
    check(abs(avg(ins(ro)) - avg(ins(rp))) < 200 and spm(ro) <= max(spm(rp), 7), f"cost {avg(ins(ro)) - avg(ins(rp)):+.0f} instructions per block, stack {spm(ro)} (SC23.5: {spm(rp)})")
    print("SC23.6 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes()) else 0)
