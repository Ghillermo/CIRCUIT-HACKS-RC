"""SC29 DSP tests (the real core-0 program on the DSP emulator): the VA-drum engine.

    python tools/emu_sc29_dsp.py SC29.bin SC29_manifest.json SC28.bin SC28_manifest.json
  * mailbox: the ACT value bits 10 / 11 land in DFLAGS bits 2 / 3 (with route and dual);
  * the other engines (DFLAGS bit 2 clear) give the samples of SC28 bit for bit (line input chain, one oscillator, two oscillators, with envelope and LFO amounts); the two extra envelope words
    are copies of the envelope and the noise level is 0;
  * VA-drum: the VCA envelope is a one-shot (the end of the gate does not release it, it decays to 0 whatever SUS is); the pitch envelope decays with the SUS value and the filter envelope with the REL
    value, independently of the VCA envelope; ENVP moves the pitch with the pitch envelope, ENVF the cutoff with the filter envelope; with DFLAGS bit 3 they start from the velocity;
  * the noise: LV is a random value per block; LRATE adds white noise to the oscillator at its level (twice the level = twice the rms; no correlation between neighbours);
  * the cost and the stack.
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
from emu_masterfx_dsp import s24, u24  # noqa: E402
import vcf21_dsp as V  # noqa: E402
import vcf21 as A  # noqa: E402
V.TILT, V.FB, V.SLOPES, V.FXMORE, V.BISEND, V.PLIMIT, V.OSC, V.VFF = False, True, True, True, True, 0x4000, True, True
V.use_osc3(); V.use_gaterel(); V.use_sinefix(); V.use_gatefix(); V.use_typezones(); V.use_dual(); V.use_vadrum()
A.FTYPE_N = A.FXTYPE_N = 7
A.use_osc3(); A.use_neutral()

N, RING = 32, 0x1000
OSB, OS2 = V.OSB0, V.OS2B0
NAMES = ("FILT", "RES", "ENVF", "LFOF", "ATK", "DEC", "SUS", "REL", "FXAMT", "GAIN", "LRATE", "LFOV", "FXTYPE", "FXMOD", "ENVA", "FTYPE")
VD, VELF, DUALF = 1 << 10, 1 << 11, 1 << 9


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    dl = {k: int(v, 16) for k, v in man["report"]["sc16"]["dsp_labels"].items()}
    dlp = {k: int(v, 16) for k, v in prev_man["report"]["sc16"]["dsp_labels"].items()}
    prog = lambda im: (lambda b: [int.from_bytes(b[i:i + 3], 'big') for i in range(0, len(b), 3)])(dsp_program(im))
    P0, PP = prog(img), prog(prev)
    off = dict(zip(NAMES, range(2, 18)))
    neutral = {n: A.DEFAULTS[i] for i, n in enumerate(NAMES)}
    check(len(P0) <= 0x4000, f"the DSP program fits in the P RAM ({len(P0):#x} words, {0x4000 - len(P0)} free; SC28 {len(PP):#x})")

    class St:
        def __init__(self, act, note=60, **kw):
            b = [0] * (2 * V.VBS)
            for n, v in {**neutral, **kw}.items(): b[off[n]] = v & 0xFFFFFF
            b[V.ACT], b[V.NOTE] = act, note
            self.blk, self.osb, self.os2 = b, [0] * 96, [0] * 96

    def step(st, msg=None, ring=None, prog_=None, labels=None):
        if msg:
            v, code, val = msg
            tag = ((st.blk[V.VBS * v + 1] >> 23) & 1) ^ 1
            st.blk[V.VBS * v] = (tag << 23) | (code << 16) | (val & 0xFFFF)
        mem = [('x', 0x3A, [N]), ('x', V.VB0, st.blk), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, ring or [0] * (2 * N)), ('x', OSB, st.osb), ('x', OS2, st.os2)]
        dumps = [('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', OSB, 96), ('x', OS2, 96)]
        res, ran = run(prog_ or P0, (labels or dl)["vpre"], mem=mem, dumps=dumps, regs_code=[])
        assert 'pc=00' in ran, ran
        st.blk, st.osb, st.os2 = res[('x', V.VB0)], res[('x', OSB)], res[('x', OS2)]
        return [s24(x) for x in res[('y', RING)][0::2]]

    # ---------------------------------------------------------------- mailbox
    st = St(1)
    step(st, (0, 19, 2 | VD))
    check(st.blk[V.ACT] == 2 and st.osb[V.DFLAGS_OFF] == 4, f"ACT = 2 | VA-drum: ACT slot {st.blk[V.ACT]}, DFLAGS {st.osb[V.DFLAGS_OFF]}")
    step(st, (0, 19, 2 | VD | VELF | DUALF | (1 << 8)))
    check(st.osb[V.DFLAGS_OFF] == 15, f"with velocity -> envelopes, dual and route: DFLAGS {st.osb[V.DFLAGS_OFF]}")
    step(st, (0, 19, 2))
    check(st.osb[V.DFLAGS_OFF] == 0, "ACT = 2 alone clears them")

    # ---------------------------------------------------------------- the other engines: the samples of SC28
    tone = lambda i, f=1000, a=0x300000: [u24(int(a * math.sin(2 * math.pi * f * (i * N + k) / 48000))) for k in range(N) for _ in (0, 1)]
    def play(prog_, labels, act, msgs, n, kw, gate_off=None, line=False, vel=100, note=60):
        st = St(1, note, **kw)
        q = list(msgs) + [(0, 19, act)]
        outs = []
        for i in range(n):
            if i == len(q): st.blk[V.GATE], st.blk[V.GNEW], st.blk[V.VEL] = 1, 1, vel
            if gate_off is not None and i == len(q) + gate_off: st.blk[V.GATE] = 0
            outs.append(step(st, q[i] if i < len(q) else None, tone(i) if line else None, prog_, labels))
        return outs, st, len(q)
    kwm = dict(ENVF=30, FILT=-20, LFOF=20, LRATE=90, ATK=20, DEC=50, SUS=70, REL=40, ENVA=63, LFOV=20)
    oscm = [(0, 27, 24), (0, 26, 12), (0, 28, 20), (0, 29, 15), (0, 30, 20), (0, 31, 10)]       # ENVP, LFOP, ENVW, LFOW, ENVM, LFOM
    for name, act, msgs, line in (("line input", 1, [], True), ("one oscillator", 2, oscm, False), ("two oscillators", 2 | DUALF, oscm + [(0, 14, 67), (0, 36, 64), (0, 38, 30), (0, 39, 30)], False)):
        a0, sa, _ = play(P0, dl, act, msgs, 40, kwm, gate_off=20, line=line)
        b0, sb, _ = play(PP, dlp, act, msgs, 40, kwm, gate_off=20, line=line)
        check(a0 == b0 and any(any(b) for b in a0), f"{name}, envelope and LFO amounts everywhere: the samples of SC28 bit for bit (peak {max(abs(x) for b in a0 for x in b):#x})")
    check(sa.osb[V.VD_EF] == sa.blk[V.ENV] == sa.osb[V.VD_EP] and sa.osb[V.VD_NL] == 0, f"there the two extra envelope words are the envelope ({sa.osb[V.VD_EF]:#x}) and the noise level is 0")

    # ---------------------------------------------------------------- VA-drum: the three envelopes
    def trace(act, kw, n=60, gate_off=4, msgs=(), vel=127, note=60):
        st = St(1, note, **kw)
        q = list(msgs) + [(0, 19, act)]
        rows, outs = [], []
        for i in range(n):
            if i == len(q): st.blk[V.GATE], st.blk[V.GNEW], st.blk[V.VEL] = 1, 1, vel
            if i == len(q) + gate_off: st.blk[V.GATE] = 0
            outs.append(step(st, q[i] if i < len(q) else None))
            rows.append(dict(env=st.blk[V.ENV], stg=st.blk[V.STG], ef=st.osb[V.VD_EF], ep=st.osb[V.VD_EP], inc=st.osb[11], ff=st.blk[V.FF], lv=s24(st.blk[V.LV]), nl=st.osb[V.VD_NL]))
        return rows[len(q):], outs[len(q):], st
    kw = dict(ATK=0, DEC=60, SUS=100, REL=20, ENVA=63)
    r, _, _ = trace(2 | VD, kw)
    rn, _, _ = trace(2, kw)
    check(all(x["stg"] in (2, 3) for x in r) and rn[6]["stg"] == 4, f"the end of the gate: VA-drum stays in its decay (stages {sorted({x['stg'] for x in r})}), the oscillator engine releases (stage {rn[6]['stg']})")
    check(all(r[i + 1]["env"] <= r[i]["env"] for i in range(len(r) - 1)) and r[3]["env"] > r[8]["env"] > 0, f"the VCA envelope decays through the end of the gate ({r[3]['env']:#x} -> {r[8]['env']:#x})")
    rl, _, _ = trace(2 | VD, dict(ATK=0, DEC=0, SUS=100, REL=20, ENVA=63), n=800)
    check(rl[-1]["env"] == 0 and rl[-1]["stg"] == 3, f"down to 0 whatever SUS is (envelope {rl[-1]['env']:#x}, stage {rl[-1]['stg']}); the oscillator engine would hold {100 << 16:#x}")
    ratio = lambda rows, key, i=3: rows[i + 1][key] / rows[i][key]
    r1, _, _ = trace(2 | VD, dict(ATK=0, DEC=127, SUS=100, REL=20, ENVA=63), n=170)
    r2, _, _ = trace(2 | VD, dict(ATK=0, DEC=127, SUS=20, REL=100, ENVA=63))
    check(abs(ratio(r1, "ep") - ratio(r2, "ef")) < 1e-5 and abs(ratio(r1, "ef") - ratio(r2, "ep")) < 1e-5 and ratio(r1, "ep") > ratio(r1, "ef") + 0.001,
          f"the pitch envelope decays with SUS, the filter envelope with REL (per block x {ratio(r1, 'ep'):.5f} / x {ratio(r1, 'ef'):.5f}; swapped values: x {ratio(r2, 'ep'):.5f} / x {ratio(r2, 'ef'):.5f})")
    check(r1[0]["ep"] > 0x7F0000 and r1[0]["ef"] > 0x700000 and all(abs(ratio(r1, "ep", i) - ratio(r1, "ep")) < 1e-4 for i in range(1, 30)), f"they start from the top at the note ({r1[0]['ep']:#x}, {r1[0]['ef']:#x}) and are exponential")
    check(r1[150]["env"] > 0x600000 and r1[150]["ef"] < r1[150]["env"] // 3 and r1[150]["ep"] > 2 * r1[150]["ef"], f"independently of the VCA envelope (after 150 blocks = 0.1 s: VCA {r1[150]['env']:#x}, pitch {r1[150]['ep']:#x}, filter {r1[150]['ef']:#x})")
    # ENVP: the pitch follows the pitch envelope; ENVF: the cutoff follows the filter envelope
    base, _, _ = trace(2 | VD, dict(ATK=0, DEC=127, SUS=40, REL=40, ENVA=63))
    rp, _, _ = trace(2 | VD, dict(ATK=0, DEC=127, SUS=40, REL=40, ENVA=63), msgs=[(0, 27, 40)])
    inc0 = base[5]["inc"]
    semis = lambda x: 12 * math.log2(x["inc"] / inc0)
    want = lambda x: 40 / 64 * 24 * x["ep"] / 0x800000
    check(all(x["inc"] == inc0 for x in base[2:]) and all(abs(semis(x) - want(x)) < 0.05 for x in rp[1:40]),
          f"ENVP +40: the pitch is the pitch envelope x 15 semitones ({semis(rp[1]):.2f} at the start, {semis(rp[20]):.2f} after 20 blocks; expected {want(rp[1]):.2f}, {want(rp[20]):.2f})")
    rf, _, _ = trace(2 | VD, dict(ATK=0, DEC=127, SUS=40, REL=40, ENVA=63, ENVF=40, FILT=-50))
    rf2, _, _ = trace(2, dict(ATK=0, DEC=127, SUS=127, REL=40, ENVA=63, ENVF=40, FILT=-50), gate_off=1000)
    check(rf[1]["ff"] > rf[30]["ff"] and rf2[1]["ff"] == rf2[30]["ff"], f"ENVF +40: the cutoff comes down with the filter envelope ({rf[1]['ff']:#x} -> {rf[30]['ff']:#x}); the oscillator engine with a held envelope keeps it ({rf2[30]['ff']:#x})")
    rv, _, _ = trace(2 | VD | VELF, dict(ATK=0, DEC=127, SUS=100, REL=20, ENVA=63), vel=64)
    rv0, _, _ = trace(2 | VD, dict(ATK=0, DEC=127, SUS=100, REL=20, ENVA=63), vel=64)
    check(abs(rv[0]["ep"] / rv0[0]["ep"] - 64 / 128) < 0.01 and abs(rv[0]["ef"] / rv0[0]["ef"] - 0.5) < 0.01, f"velocity -> envelopes, velocity 64: they start at half ({rv[0]['ep']:#x} against {rv0[0]['ep']:#x})")
    # a second note restarts all three
    st = St(1, 60, ATK=0, DEC=0, SUS=0, REL=0, ENVA=63)
    step(st, (0, 19, 2 | VD)); st.blk[V.GATE], st.blk[V.GNEW], st.blk[V.VEL] = 1, 1, 127
    for _ in range(120): step(st)
    low = (st.blk[V.ENV], st.osb[V.VD_EP], st.osb[V.VD_EF])
    st.blk[V.GNEW] = 1; step(st)
    check(min(st.blk[V.ENV], st.osb[V.VD_EP], st.osb[V.VD_EF]) > 0x700000 and max(low) < 0x400000, f"the next note restarts the three envelopes ({[hex(x) for x in low]} -> {st.blk[V.ENV]:#x}, {st.osb[V.VD_EP]:#x}, {st.osb[V.VD_EF]:#x})")

    # ---------------------------------------------------------------- the noise
    r, _, _ = trace(2 | VD, dict(ATK=0, DEC=127, SUS=40, REL=40, ENVA=63), n=260)
    lv = [x["lv"] / 0x800000 for x in r[2:]]
    mean = sum(lv) / len(lv); var = sum((x - mean) ** 2 for x in lv) / len(lv)
    c1 = sum((lv[i] - mean) * (lv[i + 1] - mean) for i in range(len(lv) - 1)) / (len(lv) - 1) / var
    check(len(set(lv)) == len(lv) and abs(mean) < 0.12 and 0.25 < var < 0.42 and abs(c1) < 0.2, f"LV is a random value per block (mean {mean:+.3f}, variance {var:.3f} (uniform: 0.333), lag-1 correlation {c1:+.3f})")
    rn, _, _ = trace(2, dict(ATK=0, DEC=127, SUS=127, REL=40, ENVA=63), n=40)
    check(all(rn[i + 1]["lv"] < rn[i]["lv"] or rn[i + 1]["lv"] > 0x700000 for i in range(5, 30)), "the oscillator engine keeps its sawtooth LFO")
    def audio(lrate, n=80):
        _, o, st = trace(2 | VD, dict(ATK=0, DEC=127, SUS=40, REL=40, ENVA=63, LRATE=lrate), n=n, gate_off=1000)
        return [x for b in o[4:] for x in b], st
    a0, s0 = audio(0); a1, s1 = audio(127); a2, s2 = audio(64)
    d1 = [x - y for x, y in zip(a1, a0)]; d2 = [x - y for x, y in zip(a2, a0)]
    rms = lambda v: math.sqrt(sum(x * x for x in v) / len(v))
    ac = lambda v: sum(v[i] * v[i + 1] for i in range(len(v) - 1)) / sum(x * x for x in v)
    check(s0.osb[V.VD_NL] == 0 and s1.osb[V.VD_NL] == 127 << 15 and rms(a0) > 0, f"LRATE = the noise level word ({s1.osb[V.VD_NL]:#x}); without it the oscillator alone (rms {rms(a0):.0f})")
    check(rms(d1) > 0.5 * rms(a0) and abs(rms(d1) / rms(d2) - 127 / 64) < 0.15 and abs(ac(d1)) < 0.05,
          f"LRATE 127 adds white noise (rms {rms(d1):.0f}, the oscillator {rms(a0):.0f}; lag-1 correlation {ac(d1):+.3f}); LRATE 64: half of it (ratio {rms(d1) / rms(d2):.2f})")
    spec = lambda v, f: math.hypot(sum(x * math.sin(2 * math.pi * f * i / 48000) for i, x in enumerate(v)), sum(x * math.cos(2 * math.pi * f * i / 48000) for i, x in enumerate(v))) / len(v)
    bands = [spec(d1, f) for f in (300, 1500, 5000, 11000, 19000)]
    check(max(bands) < 6 * min(bands), f"flat over the band (300 Hz .. 19 kHz: {[int(b) for b in bands]})")

    # ---------------------------------------------------------------- the cost
    from dsp_session import Session
    def sess(image, vals, xextra=()):
        ss = Session(image)
        extra = [('y', 0x1000 + i, u24(int(0x300000 * math.sin(i * 0.31)))) for i in range(0x400)] + [('x', V.VB0 + o_, v) for o_, v in vals.items()] + list(xextra)
        res, rans = ss.run(blocks=24, per_block=True, extra=extra, spmax=True, dumps=[('x', V.VB0, 2 * V.VBS)])
        return rans
    ins = lambda rans: [int(x.split('ins=')[1].split()[0]) for x in rans if x.startswith('RAN')][2:]
    spm = lambda rans: int([x for x in rans if x.startswith('SPMAX')][0].split()[1])
    avg = lambda v: sum(v) / len(v)
    both = {}
    for t in (0, 1):
        for n_, v in {**neutral, "NOTE": 60, "GATE": 1, "ACT": 2, "VEL": 100, "GNEW": 1, "LRATE": 100}.items():
            o_ = {**off, "GATE": V.GATE, "NOTE": V.NOTE, "ACT": V.ACT, "VEL": V.VEL, "GNEW": V.GNEW}[n_]
            both[V.VBS * t + o_] = v & 0xFFFFFF
    vdx = [('x', OSB + 48 * t + V.DFLAGS_OFF, 4) for t in (0, 1)]
    rp_, ro, rd = sess(prev, both), sess(img, both), sess(img, both, vdx)
    print(f"     DSP instructions/block, both voices on one oscillator: SC28 {avg(ins(rp_)):.0f}, SC29 {avg(ins(ro)):.0f}, SC29 VA-drum with noise {avg(ins(rd)):.0f}")
    check(0 <= avg(ins(ro)) - avg(ins(rp_)) < 80 and spm(ro) <= spm(rp_), f"the other engines: +{avg(ins(ro)) - avg(ins(rp_)):.0f} instructions per block, stack {spm(ro)} (SC28: {spm(rp_)})")
    check(avg(ins(rd)) - avg(ins(rp_)) < 1000 and spm(rd) <= spm(rp_), f"VA-drum with noise on both tracks: +{avg(ins(rd)) - avg(ins(rp_)):.0f} instructions per block (~{100 * (avg(ins(rd)) - avg(ins(rp_))) / 166000:.2f}% of the ~166000 budget), stack {spm(rd)}")
    print("SC29 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
