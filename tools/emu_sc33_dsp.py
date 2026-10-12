"""SC33 DSP tests: the captured sample (tools/sampler_dsp.py) on the dsp56kEmu interpreter.

    python tools/emu_sc33_dsp.py [SC33.bin SC33_manifest.json]
Logic (the code assembled with the buffer in the interpreter's 512 K words: Y:$40000, 1024 words), driven block by block like the Master FX hook:
  * record while STATE bit 0: (L + R) / 2 of each frame, WP / LEN grow by a block, a new recording restarts at 0, it stops at MAXLEN;
  * CMD 1: plays S..E (fractions of LEN) at the pitch increment, added to L and R; at E it stops (silence after); CMD 3 stops; CMD is cleared;
  * reverse (EF < SF), pitch 2.0 (every other sample), loop (mode 2 and CMD 2 = forced loop), gate (mode 1: STATE bit 1 dropped -> stops);
  * M4 restored, r1 = $2E10 on return (fx_out's own instruction).
With the image: Master FX's fx_out = `jmp smp_post` + nop, the code = code() word for word, the program below $4000.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import sampler_dsp as S  # noqa: E402
import dsp56 as D  # noqa: E402

AT, DRV = 0x1000, 0x2000
TB, TMAX = 0x40000, 0x400
NF = 58


def T_(*l): return G.T(*l)


def main(img=None, man=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    if img is not None:
        from dsp_session import dsp_program
        rep = man["report"]; dl = {k: int(v, 16) for k, v in rep["sc16"]["dsp_labels"].items()}
        sp = dsp_program(img); P0 = [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]
        check(P0[dl["fx_out"]:dl["fx_out"] + 3] == D.jmp(dl["smp_post"]) + [0], "fx_out = jmp smp_post + nop")
        real, _ = S.code(dl["smp_post"])
        check(P0[dl["smp_post"]:dl["smp_post"] + len(real)] == real and len(P0) <= 0x4000, f"the image's code = code(); program ends at P:${len(P0):x}")
    w, lab = S.code(AT, TB, TMAX)
    P = [0] * 0x4000
    P[AT:AT + len(w)] = w

    def setx(addr, v): return T_("move #>$%x,x0" % (v & 0xFFFFFF), "move x0,x:>$%x" % addr)
    def frames(f): return [x & 0xFFFFFF for i in range(NF) for x in f(i)]
    def go(steps, mem=(), dumps=()):
        drv = T_("move #>$123456,m4")
        for s in steps:
            drv += [0x0BF080, AT] if s == "call" else s
        drv += T_("move m4,x:>$3c00", "move r1,x:>$3c01") + [0x00000C]
        P2 = list(P); P2[DRV:DRV + len(drv)] = drv
        return run(P2, DRV, mem=[('x', 0x3A, [NF])] + list(mem), maxins=3_000_000,
                   dumps=[('x', S.SMB, 0x20), ('x', G.BUF, 2 * NF), ('y', TB, TMAX), ('x', 0x3C00, 2)] + list(dumps))
    st = lambda r, k: r[('x', S.SMB)][k - S.SMB]
    src = lambda i: (0x1000 * (i + 1), 0x0800 * (i + 1))                   # L, R
    rec_buf = [('x', G.BUF, frames(src)), ('x', S.MAGIC_AT, [S.MAGIC])]       # (the first call clears the state: the magic says it ran)
    # ---- record
    r, ran = go([setx(S.STATE, 1), "call", "call", "call", setx(S.STATE, 0), "call"], mem=rec_buf)
    want = [((0x1000 + 0x800) * (i % NF + 1)) // 2 for i in range(3 * NF)]
    y = r[('y', TB)]
    check(st(r, S.LEN) == 3 * NF and st(r, S.WP) == 3 * NF and y[:3 * NF] == want and y[3 * NF] == 0, f"record 3 blocks: LEN {st(r, S.LEN)}, samples (L+R)/2 ({ran})")
    check(r[('x', 0x3C00)] == [0x123456, G.BUF], "M4 restored, r1 = $2E10")
    r, _ = go([setx(S.STATE, 1)] + ["call"] * 30, mem=rec_buf)
    check(st(r, S.LEN) == (TMAX // NF) * NF, f"stops at MAXLEN: LEN {st(r, S.LEN)} (max {TMAX})")
    r, _ = go([setx(S.STATE, 1), "call", "call", setx(S.STATE, 0), "call", setx(S.STATE, 1), "call", setx(S.STATE, 0)], mem=rec_buf)
    check(st(r, S.LEN) == NF, f"a new recording restarts at 0 (LEN {st(r, S.LEN)})")

    # ---- play: a ramp already in the buffer
    LENP = 300
    ramp = [(i + 1) * 0x100 for i in range(LENP)]
    base = [('y', TB, ramp), ('x', S.LEN, [LENP]), ('x', S.PREV, [0])]
    def magic(): return [('x', S.MAGIC_AT, [S.MAGIC])]
    def play(steps, sf=0, ef=0x7FFFFF, inci=1, incf=0, mode=0, cmd=1, extra=()):
        pre = setx(S.SF, sf) + setx(S.EF, ef) + setx(S.INCI, inci) + setx(S.INCF, incf) + setx(S.MODE, mode) + setx(S.CMD, cmd)
        return go([pre] + steps, mem=base + magic() + list(extra))
    zero_out = [('x', G.BUF, [0] * 2 * NF)]
    r, _ = play(["call"], extra=zero_out)
    out = r[('x', G.BUF)]
    check(out[0::2] == ramp[:NF] and out[1::2] == ramp[:NF] and st(r, S.CMD) == 0 and st(r, S.PLAY) == 1, "CMD 1: the first block = samples 0..57 on L and R; CMD cleared, playing")
    check(st(r, S.PI) == TB + NF, f"position {st(r, S.PI) - TB}")
    r, _ = play(["call"] * 6, extra=zero_out)                               # the buffer is not cleared between calls: sum of blocks
    check(st(r, S.PLAY) == 0, "at the end (E = LEN * 0.99..): stopped")
    E = (LENP * 0x7FFFFF) >> 23
    tot = [0] * NF
    for blk in range(6):
        for f in range(NF):
            p = blk * NF + f
            tot[f] += ramp[p] if p < E else 0
    out = r[('x', G.BUF)]
    check(out[0::2] == [v & 0xFFFFFF for v in tot], "six blocks: the samples up to E, then silence (the parked position reads the ZERO word)")
    r, _ = play(["call", setx(S.CMD, 3), "call"], extra=zero_out)
    check(st(r, S.PLAY) == 0 and st(r, S.CMD) == 0, "CMD 3: stops")
    r, _ = play(["call"], sf=0x7FFFFF, ef=0, extra=zero_out)
    s0 = (LENP * 0x7FFFFF) >> 23
    check(r[('x', G.BUF)][0::2] == [ramp[s0 - i] for i in range(NF)], "reverse (end < start): from the start downwards")
    r, _ = play(["call"], inci=2, extra=zero_out)
    check(r[('x', G.BUF)][0::2] == [ramp[2 * i] for i in range(NF)], "pitch x2: every other sample")
    r, _ = play(["call"], inci=0, incf=0x800000, extra=zero_out)
    check(r[('x', G.BUF)][0::2] == [ramp[i // 2] for i in range(NF)], "pitch x0.5: each sample twice")
    sfx, efx = int(0.1 * 0x800000), int(0.3 * 0x800000)
    S0, E0 = (LENP * sfx) >> 23, (LENP * efx) >> 23
    r, _ = play([setx(S.STATE, 2), "call"], sf=sfx, ef=efx, mode=2, extra=zero_out)          # (pad held: with sampler_dsp.HOLD a loop needs the gate)
    seq = [ramp[S0 + (i % (E0 - S0))] for i in range(NF)]
    check(r[('x', G.BUF)][0::2] == seq and st(r, S.PLAY) == 1, f"loop (mode 2) {S0}..{E0}: wraps to the start")
    r, _ = play([setx(S.STATE, 2), "call"], sf=sfx, ef=efx, mode=0, cmd=2, extra=zero_out)
    check(r[('x', G.BUF)][0::2] == seq, "CMD 2 = forced loop in one-shot mode")
    r, _ = play([setx(S.STATE, 2), "call", "call", setx(S.STATE, 0), "call"], mode=1, extra=zero_out)
    check(st(r, S.PLAY) == 0, "gate (mode 1): playing while held, stops on release")
    r, _ = play([setx(S.STATE, 0), "call"], mode=1, cmd=2, extra=zero_out)
    if S.HOLD:
        check(st(r, S.PLAY) == 0, "HOLD: the forced loop stops when the pad is released")
    else:
        check(st(r, S.PLAY) == 2, "forced loop ignores the gate")
    r, _ = go([setx(S.CMD, 1), "call"], mem=[('x', S.MAGIC_AT, [S.MAGIC]), ('x', S.LEN, [0])])
    check(st(r, S.PLAY) == 0, "nothing recorded: CMD 1 does nothing")
    r, _ = go(["call"], mem=[('x', S.CMD, [1]), ('x', S.STATE, [3]), ('x', S.MAGIC_AT, [0x111111])])
    check(st(r, S.MAGIC_AT) == S.MAGIC and st(r, S.CMD) == 0 and st(r, S.STATE) == 0 and st(r, S.PLAY) == 0, "first call: the state is cleared (garbage CMD / STATE ignored)")
    print("SC33 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    if len(a) > 2: sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
    sys.exit(1 if main() else 0)
