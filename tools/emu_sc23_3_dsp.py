"""SC23.3 DSP tests: the neutral default state of the VCA / VCF mode and of the oscillator, end to end over many blocks (the hook routine vpre of the real DSP program).

    python tools/emu_sc23_3_dsp.py SC23.3.bin SC23.3_manifest.json
  * line in, neutral defaults (filter open, RES 0, ENVA +63, GAIN 0, SUS 127, A / D / R 0, LFOV 0): silent without the gate; a key press opens the sound, which is the input times a constant
    (the velocity) -- nothing else; a key release closes it within a few milliseconds (REL = 0 = ~2 ms), without ever going negative;
  * the oscillator (ACT = 2), WAVE 0 = sine, SHAPE 50, no sends: a clean sine at the pitch of the note (the equal-tempered scale, A4 = 440 Hz) for every note, steady amplitude, phase continuous
    across the blocks, nothing without the gate, the LFO and the envelope do not modulate it;
  * with the gate release option off (REL 0 = the 40 ms table value) the release is the old one: the new coefficient is only used when REL = 0.
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
V.use_osc3(); V.use_gaterel(); V.use_sinefix()
A.use_osc3(); A.use_neutral()

N, RING = 32, 0x1000
OSB = V.OSB0
NAMES = ("FILT", "RES", "ENVF", "LFOF", "ATK", "DEC", "SUS", "REL", "FXAMT", "GAIN", "LRATE", "LFOV", "FXTYPE", "FXMOD", "ENVA", "FTYPE")


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    dl = {k: int(v, 16) for k, v in man["report"]["sc16"]["dsp_labels"].items()}
    P0 = [int.from_bytes(dsp_program(img)[i:i + 3], 'big') for i in range(0, len(dsp_program(img)), 3)]
    off = dict(zip(NAMES, range(2, 18)))
    neutral = {n: A.DEFAULTS[i] for i, n in enumerate(NAMES)}
    check(neutral == dict(FILT=0, RES=0, ENVF=0, LFOF=0, ATK=0, DEC=0, SUS=127, REL=0, FXAMT=0, GAIN=0, LRATE=40, LFOV=0, FXTYPE=0, FXMOD=64, ENVA=63, FTYPE=0)
          and A.DEFAULTS[16:] == (0, 0, 0, 50, 0, 0, 0, 0, 0, 0), f"the neutral defaults: {neutral} + oscillator {A.DEFAULTS[16:]}")

    def fresh(act, note=60, **kw):
        b = [0] * (2 * V.VBS)
        for n, v in {**neutral, **kw}.items(): b[off[n]] = v & 0xFFFFFF
        b[V.ACT], b[V.NOTE] = act, note
        return b

    def blocks(n, blk, osb, ring_fn, script):
        """n blocks of vpre; script: {block: (gate, trig, velocity)}; returns the output of input 1 per block."""
        outs = []
        for i in range(n):
            if i in script:
                g, t, v = script[i]
                blk[V.GATE], blk[V.GNEW], blk[V.VEL] = g, t, v
            ring = ring_fn(i)
            res, ran = run(P0, dl["vpre"], mem=[('x', 0x3A, [N]), ('x', V.VB0, blk), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, ring), ('x', OSB, osb)],
                           dumps=[('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', OSB, 96)], regs_code=[])
            assert 'pc=00' in ran, ran
            blk, osb = res[('x', V.VB0)], res[('x', OSB)]
            outs.append([s24(x) for x in res[('y', RING)][0::2]])
        return outs, blk, osb

    tone = lambda i: [u24(int(0x300000 * math.sin(2 * math.pi * 1000 * (i * N + k) / 48000))) for k in range(N) for _ in (0, 1)]
    # ---- line in: the basic gate
    script = {3: (1, 1, 100), 12: (0, 0, 100)}
    outs, blk, _ = blocks(30, fresh(1), [0] * 96, tone, script)
    flat_in = [[s24(x) for x in tone(i)[0::2]] for i in range(30)]
    check(all(x == 0 for b in outs[:3] for x in b), "no gate: silence (the VCA is closed, GAIN 0)")
    check(blk[V.VCAON] == 1 and blk[V.FMODE] == 0 and blk[V.DRVF] == 0, f"the filter is off (FMODE {blk[V.FMODE]}) and the FX amount is 0 ({blk[V.DRVF]}); the VCA stage runs")
    ratios = []
    for i in range(5, 12):
        for k in range(N):
            if abs(flat_in[i][k]) > 0x40000: ratios.append(outs[i][k] / flat_in[i][k])
    g = sum(ratios) / len(ratios)
    check(max(ratios) - min(ratios) < 3e-3 and 0.76 < g < 0.99, f"gate open: the output is the input times a constant ({g:.4f}, spread {max(ratios) - min(ratios):.1e}): velocity 100 -> ENVA x velocity")
    ramp = [outs[3][k] / flat_in[3][k] for k in range(N) if abs(flat_in[3][k]) > 0x40000]
    check(ramp and max(ramp) < g + 0.01 and min(ramp) > -0.01 and ramp[0] < g, "the opening block ramps up smoothly (no click)")
    peak = lambda b: max(abs(x) for x in b)
    pk = [peak(b) for b in outs]
    check(pk[12] < pk[11] * 0.9 and pk[12] > 0, f"gate off: the release starts in the next block ({pk[11]:#x} -> {pk[12]:#x})")
    last = next((i for i in range(12, 30) if pk[i] < 0x2000), None)
    check(last is not None and last - 12 <= 24, f"gate off: closed (peak < 1/1000 of full scale) after {None if last is None else last - 12} blocks = {None if last is None else (last - 12) * N / 48:.1f} ms")
    check(all(blk_ == 0 for blk_ in outs[29]) or peak(outs[29]) < 0x100, "and silent afterwards")
    # the gain per block only falls after the key release
    gains = [pk[i] for i in range(13, 22)]
    check(all(gains[j + 1] <= gains[j] for j in range(len(gains) - 1)), "the release is monotone (no bumps)")
    # a second key with another velocity: another constant, same shape
    outs2, blk2, _ = blocks(14, fresh(1), [0] * 96, tone, {2: (1, 1, 50)})
    r2 = [outs2[i][k] / flat_in[i][k] for i in range(5, 12) for k in range(N) if abs(flat_in[i][k]) > 0x40000]
    check(abs(sum(r2) / len(r2) - g * 50 / 100) < 0.01, f"velocity 50: the level is {sum(r2) / len(r2):.4f} = {g:.4f} x 50 / 100")
    # the old release (REL > 0): 40 ms table value, untouched
    outs3, blk3, _ = blocks(30, fresh(1, REL=1), [0] * 96, tone, script)
    pk3 = [peak(b) for b in outs3]
    check(pk3[12] > pk3[11] * 0.9 and pk3[29] > 0x20000, f"REL = 1 keeps the long table release ({pk3[11]:#x} -> {pk3[12]:#x} -> {pk3[29]:#x} after 18 blocks)")

    # ---- the oscillator: a clean sine at the pitch of the note
    def osc_run(note, n=40, gate_at=2, off_at=None, **kw):
        osb = [0] * 96
        for k, v in enumerate(A.DEFAULTS[16:26]): osb[k] = v & 0xFFFFFF
        sc = {gate_at: (1, 1, 127)}
        if off_at is not None: sc[off_at] = (0, 0, 127)
        outs_, blk_, osb_ = blocks(n, fresh(2, note, **kw), osb, lambda i: [0] * (2 * N), sc)
        return outs_, blk_, osb_
    worst = 0.0
    for note in (48, 57, 60, 69, 72, 84, 96, 108):
        outs_, blk_, _ = osc_run(note)
        sig_ = [x for b in outs_[6:] for x in b]
        f = 440 * 2 ** ((note - 69) / 12)
        # least squares fit of A sin + B cos at f
        w = 2 * math.pi * f / 48000
        n0 = 6 * N
        sa = sum(x * math.sin(w * (n0 + j)) for j, x in enumerate(sig_)) * 2 / len(sig_)
        sb = sum(x * math.cos(w * (n0 + j)) for j, x in enumerate(sig_)) * 2 / len(sig_)
        amp = math.hypot(sa, sb)
        res = [x - (sa * math.sin(w * (n0 + j)) + sb * math.cos(w * (n0 + j))) for j, x in enumerate(sig_)]
        rms_res = math.sqrt(sum(r * r for r in res) / len(res)); rms_sig = amp / math.sqrt(2)
        thd = rms_res / rms_sig
        harm = []
        for hh in (2, 3, 4, 5, 7):
            wh = hh * w
            ha = math.hypot(sum(x * math.sin(wh * (n0 + j)) for j, x in enumerate(sig_)), sum(x * math.cos(wh * (n0 + j)) for j, x in enumerate(sig_))) * 2 / len(sig_)
            harm.append(f"H{hh} {20 * math.log10(max(ha, 1) / amp):.0f} dB")
        print("     ", note, ", ".join(harm))
        pks = [peak(b) for b in outs_[6:]]
        worst = max(worst, thd)
        check(thd < 0.02 and amp > 0x100000 and (max(pks) - min(pks) < 0.02 * max(pks) or note < 84), f"note {note}: {f:.1f} Hz, a sine (residual {thd * 100:.3f}% of the signal), amplitude {amp / 0x800000:.3f} of full scale, steady per block ({min(pks):#x}..{max(pks):#x})")
    outs_, blk_, _ = osc_run(60, n=12)
    check(all(x == 0 for b in outs_[:2] for x in b), "oscillator: silent before the key press")
    outs_, blk_, _ = osc_run(60, n=30, off_at=10)
    pk = [peak(b) for b in outs_]
    last = next((i for i in range(10, 30) if pk[i] < 0x2000), None)
    check(last is not None and last - 10 <= 24 and pk[9] > 0x200000, f"oscillator: key release closes the sound ({pk[9]:#x} -> silence after {None if last is None else last - 10} blocks)")
    # the LFO and the envelope do not modulate the neutral oscillator: two runs with different LFO phases give the same sine amplitude / frequency
    a1, _, _ = osc_run(69, n=30, LRATE=0)
    a2, _, _ = osc_run(69, n=30, LRATE=127)
    check(a1[10:] == a2[10:], "LRATE 0 and 127 give the identical sound (the LFO modulates nothing)")
    # the default is not a function of the other stored values: ATK / DEC / REL / SUS only shape the gate
    a3, _, _ = osc_run(69, n=30, DEC=100)
    d3 = max(abs(x - y) for b3, b1 in zip(a3[10:], a1[10:]) for x, y in zip(b3, b1))
    check(d3 < 0x30000, f"the decay time changes (almost) nothing at the maximum sustain (the envelope falls from 1 to 127/128 only: max difference {d3:#x})")
    print(f"     worst residual {worst * 100:.3f}%")
    # ---- cost and stack of the whole core with both oscillator voices on, against SC19.9 (the budget is ~166000 instructions per block)
    from dsp_session import Session
    def sess(image, vals):
        ss = Session(image)
        extra = [('y', 0x1000 + i, u24(int(0x300000 * math.sin(i * 0.31)))) for i in range(0x400)] + [('x', V.VB0 + o_, v) for o_, v in vals.items()]
        res, rans = ss.run(blocks=24, per_block=True, extra=extra, spmax=True, dumps=[('x', V.VB0, 2 * V.VBS)])
        return rans
    ins = lambda rans: [int(x.split('ins=')[1].split()[0]) for x in rans if x.startswith('RAN')][2:]
    spm = lambda rans: int([x for x in rans if x.startswith('SPMAX')][0].split()[1])
    avg = lambda v: sum(v) / len(v)
    prev = (Path(__file__).resolve().parents[1] / "firmware/sc19.9/circuittracks-4486-SC19.9.bin").read_bytes()
    both = {}
    for t in (0, 1):
        for n_, v in {**neutral, "NOTE": 60, "GATE": 1, "ACT": 2, "VEL": 100, "GNEW": 1}.items():
            o_ = {**off, "GATE": V.GATE, "NOTE": V.NOTE, "ACT": V.ACT, "VEL": V.VEL, "GNEW": V.GNEW}[n_]
            both[V.VBS * t + o_] = v & 0xFFFFFF
    rp, ro = sess(prev, {}), sess(img, both)
    print(f"     DSP instructions/block: SC19.9 {avg(ins(rp)):.0f}, SC23.3 both oscillators playing {avg(ins(ro)):.0f}")
    check(avg(ins(ro)) - avg(ins(rp)) < 16000 and spm(ro) <= max(spm(rp), 7), f"cost +{avg(ins(ro)) - avg(ins(rp)):.0f} instructions per block (~{100 * (avg(ins(ro)) - avg(ins(rp))) / 166000:.1f}% of ~166000), stack depth {spm(ro)} (SC19.9 {spm(rp)})")
    print("SC23.3 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
