"""SC37.4 DSP tests (the real core-0 program on the DSP emulator): the sustain stage glides (vcf21_dsp.use_stglide).

    python tools/emu_sc37_4_dsp.py SC37.4.bin SC37.4_manifest.json SC37.3.bin SC37.3_manifest.json
  * attack and decay: the envelope of SC37.3 block for block until the sustain stage;
  * the sustain holds SUS (within a few LSB) like SC37.3;
  * oscillator -> VA-drum with a held note: SC37.3 drops the envelope to 0 in one block (a click), SC37.4 glides down with the decay coefficient;
  * VA-drum -> oscillator with the gate still high: SC37.3 jumps back to SUS, SC37.4 glides up;
  * SUS turned with a held note: a glide instead of a step;
  * VA-drum alone still decays to 0; the end of the gate releases as before.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
from emu_masterfx_dsp import s24  # noqa: E402
import vcf21_dsp as V  # noqa: E402
import vcf21 as A  # noqa: E402
V.TILT, V.FB, V.SLOPES, V.FXMORE, V.BISEND, V.PLIMIT, V.OSC, V.VFF = False, True, True, True, True, 0x4000, True, True
V.use_osc3(); V.use_gaterel(); V.use_sinefix(); V.use_gatefix(); V.use_typezones(); V.use_dual(); V.use_vadrum()
A.FTYPE_N = A.FXTYPE_N = 7
A.use_osc3(); A.use_neutral()

N, RING = 32, 0x1000
OSB, OS2 = V.OSB0, V.OS2B0
NAMES = ("FILT", "RES", "ENVF", "LFOF", "ATK", "DEC", "SUS", "REL", "FXAMT", "GAIN", "LRATE", "LFOV", "FXTYPE", "FXMOD", "ENVA", "FTYPE")
VD = 1 << 10


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    prog = lambda im: (lambda b: [int.from_bytes(b[i:i + 3], 'big') for i in range(0, len(b), 3)])(dsp_program(im))
    lab = lambda m: {k: int(v, 16) for k, v in m["report"]["sc16"]["dsp_labels"].items()}
    NEW, OLD = (prog(img), lab(man)), (prog(prev), lab(prev_man))
    off = dict(zip(NAMES, range(2, 18)))
    neutral = {n: A.DEFAULTS[i] for i, n in enumerate(NAMES)}
    check(len(NEW[0]) <= 0x4000, f"the DSP program fits ({len(NEW[0]):#x} words, {0x4000 - len(NEW[0])} free)")

    class St:
        def __init__(self, **kw):
            b = [0] * (2 * V.VBS)
            for n, v in {**neutral, **kw}.items(): b[off[n]] = v & 0xFFFFFF
            b[V.ACT], b[V.NOTE] = 1, 60
            self.blk, self.osb, self.os2 = b, [0] * 96, [0] * 96

    def step(st, pg, msg=None):
        if msg:
            v, code, val = msg
            tag = ((st.blk[V.VBS * v + 1] >> 23) & 1) ^ 1
            st.blk[V.VBS * v] = (tag << 23) | (code << 16) | (val & 0xFFFF)
        mem = [('x', 0x3A, [N]), ('x', V.VB0, st.blk), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, [0] * (2 * N)), ('x', OSB, st.osb), ('x', OS2, st.os2)]
        dumps = [('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', OSB, 96), ('x', OS2, 96)]
        res, ran = run(pg[0], pg[1]["vpre"], mem=mem, dumps=dumps, regs_code=[])
        assert 'pc=00' in ran, ran
        st.blk, st.osb, st.os2 = res[('x', V.VB0)], res[('x', OSB)], res[('x', OS2)]

    def session(pg, events, n, **kw):
        """events: {block: msg or ('sus', v)}; the note starts after the ACT message (block 0) -> the envelope per block."""
        st = St(**kw)
        env = []
        step(st, pg, (0, 19, 2))
        st.blk[V.GATE], st.blk[V.GNEW], st.blk[V.VEL] = 1, 1, 127
        for i in range(n):
            ev = events.get(i)
            if isinstance(ev, tuple) and ev[0] == "sus": st.blk[off["SUS"]] = ev[1]; ev = None
            if ev == "gate_off": st.blk[V.GATE] = 0; ev = None
            step(st, pg, ev)
            env.append((st.blk[V.ENV], st.blk[V.STG]))
        return env

    kw = dict(ATK=0, DEC=0, SUS=100, REL=20, ENVA=63)
    a, b = session(NEW, {}, 600, **kw), session(OLD, {}, 600, **kw)
    k3 = next(i for i, (_, s) in enumerate(b) if s == 3)
    sw = k3 + 40
    check(a[:k3] == b[:k3], f"attack and decay: the envelope of SC37.3 block for block until the sustain stage (block {k3})")
    check(all(abs(e - (100 << 16)) <= 0x2000 for e, s in a[k3:]) and all(s == 3 for _, s in a[k3:]) and abs(a[-1][0] - (100 << 16)) < 0x100,
          f"the sustain holds SUS: the last 0.05 % of the decay glides in instead of a step ({a[k3][0]:#x} at the stage change, {a[-1][0]:#x}; SUS {100 << 16:#x})")
    # oscillator -> VA-drum with the note held
    a, b = session(NEW, {sw: (0, 19, 2 | VD)}, sw + 200, **kw), session(OLD, {sw: (0, 19, 2 | VD)}, sw + 200, **kw)
    dn = [a[i][0] for i in range(sw - 1, sw + 200)]
    jump = max(abs(dn[i + 1] - dn[i]) for i in range(len(dn) - 1))
    check(b[sw][0] == 0 and b[sw - 1][0] > 0x600000, f"SC37.3: oscillator -> VA-drum drops the envelope to 0 in one block ({b[sw - 1][0]:#x} -> {b[sw][0]:#x})")
    check(a[sw][0] > 0x500000 and all(dn[i + 1] <= dn[i] for i in range(len(dn) - 1)) and dn[-1] < dn[0] // 4 and jump < (b[sw - 1][0] - b[sw][0]) // 8,
          f"SC37.4: it glides down ({dn[0]:#x} -> {dn[1]:#x} -> {dn[30]:#x} -> {dn[-1]:#x}, largest step per block {jump:#x})")
    # VA-drum -> oscillator with the gate still high (the one-shot is over: the envelope is at 0)
    up = sw + 200
    a, b = session(NEW, {sw: (0, 19, 2 | VD), up: (0, 19, 2)}, up + 200, **kw), session(OLD, {sw: (0, 19, 2 | VD), up: (0, 19, 2)}, up + 200, **kw)
    check(b[up][0] - b[up - 1][0] > 0x500000, f"SC37.3: VA-drum -> oscillator jumps back to SUS ({b[up - 1][0]:#x} -> {b[up][0]:#x})")
    rise = [a[i][0] for i in range(up - 1, up + 200)]
    jump = max(abs(rise[i + 1] - rise[i]) for i in range(len(rise) - 1))
    check(rise[1] < 0x200000 and all(rise[i + 1] >= rise[i] for i in range(len(rise) - 1)) and abs(rise[-1] - (100 << 16)) < (100 << 16) // 16 and jump < (b[up][0] - b[up - 1][0]) // 8,
          f"SC37.4: it glides up to SUS ({rise[0]:#x} -> {rise[1]:#x} -> {rise[-1]:#x}, largest step {jump:#x})")
    # SUS turned with a held note
    t = sw
    a, b = session(NEW, {t: ("sus", 20)}, t + 200, **kw), session(OLD, {t: ("sus", 20)}, t + 200, **kw)
    check(b[t][0] == 20 << 16 and a[t][0] > 60 << 16 and abs(a[-1][0] - (20 << 16)) < (80 << 16) // 16, f"SUS 100 -> 20 with the note held: SC37.3 steps ({b[t - 1][0]:#x} -> {b[t][0]:#x}), SC37.4 glides ({a[t][0]:#x} -> {a[-1][0]:#x})")
    # VA-drum alone; the end of the gate
    st = St(ATK=0, DEC=0, SUS=100, REL=20, ENVA=63); step(st, NEW, (0, 19, 2 | VD)); st.blk[V.GATE], st.blk[V.GNEW], st.blk[V.VEL] = 1, 1, 127
    for _ in range(900): step(st, NEW)
    check(st.blk[V.ENV] < 0x100, f"VA-drum alone still decays to 0 ({st.blk[V.ENV]:#x})")
    a, b = session(NEW, {sw: "gate_off"}, sw + 300, **kw), session(OLD, {sw: "gate_off"}, sw + 300, **kw)
    d0 = abs(a[sw - 1][0] - b[sw - 1][0])
    check(all(abs(x[0] - y[0]) <= d0 + 0x40 and x[1] == y[1] for x, y in zip(a[sw:], b[sw:])), f"the end of the gate releases as in SC37.3 (stage {a[sw][1]}, {a[-1][0]:#x} at the end)")
    print("SC37.4 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
