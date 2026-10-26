"""SC47.3 DSP test (dsp56.use_shortbr): the core-0 program with the near jumps in their one-word relative form behaves exactly as the previous
build's, block by block.

    python tools/emu_shortbr_dsp.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json

NEW = a build whose only DSP change is use_shortbr (SC47.3), PREV = the build before it (SC47.2).
  * the program: shorter; the stock part only moves the targets of the hooks' jsr / jmp (emu_sc43_9_dsp.program_check's rule); the new program
    holds one-word branches (bcc / bra / bsr) and fewer long jumps;
  * the whole core 0 of both builds with the engine's traffic of emu_sc43_9_dsp (the oscillator, two oscillators, the VA-drum, the granular, knob
    turns on every page, notes, drum hits, Synth notes): X and Y memory 0..$3FFF the same at four points;
  * again with the FM voice forced on MIDI 1 (the flag and an operator block written before every block) and the sample mode on MIDI 2 (ACT = 3):
    the same memory.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp_session as DS  # noqa: E402
import emu_sc43_9_dsp as M  # noqa: E402
import vcf21_dsp as V  # noqa: E402


def fm_force():
    F = 0x7FFFFF
    one = 1 << 19
    R, AMP, K = [one, one * 3 // 2, one, 4 * one], [0x600000, 0x500000, 0x600000, 0x380000], [0x1FFFFF, 0, 0x1FFFFF, 0]
    MM = [[0, F, 0, 0], [0, 0, 0, 0], [0, 0, 0, F], [0, 0, 0, 0x500000]]
    out = [(V.OSB0 + V.FM_FLAG, 1)]
    for k in range(4):
        out += [(V.FMB0 + 12 * k + V.F_R, R[k]), (V.FMB0 + 12 * k + V.F_AMP, AMP[k]), (V.FMB0 + 12 * k + V.F_K, K[k])]
        out += [(V.FMB0 + 12 * k + V.F_M + j, MM[k][j]) for j in range(4)]
    out += [(V.FMB0 + V.F_NZ, 0x100000), (V.VB0 + V.VBS + V.ACT, 3)]
    return out


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    pn, pp = DS.dsp_program(img), DS.dsp_program(prev)
    wn = [int.from_bytes(pn[i:i + 3], 'big') for i in range(0, len(pn), 3)]
    wp = [int.from_bytes(pp[i:i + 3], 'big') for i in range(0, len(pp), 3)]
    base = 0x2A5E
    moved = [i for i in range(base) if wn[i] != wp[i]]
    jumps = all(i > 0 and wp[i - 1] in (0x0BF080, 0x0AF080) and wn[i - 1] == wp[i - 1] and wp[i] >= base and wn[i] >= base for i in moved)
    check(jumps, f"the stock part of the program: only the targets of the hooks' jsr / jmp moved ({len(moved)} words)")
    check(len(wn) < len(wp), f"the program ${len(wp):x} -> ${len(wn):x} ({len(wp) - len(wn)} words fewer)")
    nbr = sum(1 for w in wn[base:] if w & 0xFF0420 == 0x050400 or w & 0xFFFC20 in (0x050C00, 0x050800))
    nlong = lambda ws: sum(1 for i in range(base, len(ws) - 1) if ws[i] in (0x0AF080, 0x0BF080) or ws[i] & 0xFFFFF0 == 0x0AF0A0)
    check(nbr > 0 and nlong(wn) < nlong(wp), f"one-word branches: {nbr}; long jumps {nlong(wp)} -> {nlong(wn)}")
    sched = M.schedule(prev, pman)
    for name, force in (("the engine's traffic", ()), ("with FM on MIDI 1 and the sample mode on MIDI 2", fm_force())):
        Rn, _ = M.dsp_run(img, sched, force=force); gc.collect()
        Rp, _ = M.dsp_run(prev, sched, force=force); gc.collect()
        check(len(Rn) == len(Rp) == 2 * len(M.CHECKS), f"{name}: {len(Rn)} / {len(Rp)} dumps")
        for k, ((sn, an, vn), (sp_, ap, vp)) in enumerate(zip(Rn, Rp)):
            diff = [i for i, (x, y) in enumerate(zip(vn, vp)) if x != y]
            check(sn == sp_ and not diff, f"{name}, block {M.CHECKS[k // 2]}, {sn.upper()}: 0..$3FFF the same ({sum(1 for x in vn if x)} non-zero words; "
                                          f"differences at {[hex(i) for i in diff[:12]]})")
        if force:
            x = [v for s_, a, v in Rn if s_ == 'x'][-1]
            check(any(x[V.FMB0 + 12 * k + V.F_OUT] for k in range(4)) and any(x[V.FMB0 + 12 * k + V.F_PH] for k in range(4)),
                  f"{name}: the FM voice ran (outputs / phases in X:$3E00)")
    print(f"{man.get('marker', '?')} SHORTBR DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
