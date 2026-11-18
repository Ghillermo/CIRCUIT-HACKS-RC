"""RC4.16 / Alpha 7.04 DSP logic tests (dspemu, sampler_dsp.code with PRE / V34 / HOLD / FILT as the builds): the captured sample of Master FX.
  * use_noplayrec (RC4.16): while recording (STATE bit 0), CMD 1 does not start the playback (the mix untouched, PLAY 0); CMD 3 still stops;
    released, CMD 1 plays;
  * use_overdub (Alpha 7.04): a recording no longer stops a playing sample; the playback keeps the old take's length (it goes on with the next frames
    although LEN restarts at 0); the take = (L + R) / 2 x 16 of the mix before the sample + 0.7 x the sample (c + K (m - c), +-1); with nothing
    playing the take = the mix (as before); not recording, nothing is written; m4 / r4 / r5 / r6 back.
    python tools/emu_overdub_dsp.py"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import sampler_dsp as S  # noqa: E402
import dsp56 as D  # noqa: E402
import emu_sc44_1_dsp as B  # noqa: E402

T_ = G.T
AT, DRV, FXH, TB, TMAX, NF = B.AT, B.DRV, B.FXH, B.TB, B.TMAX, B.NF


def harness(od, npr):
    S.PRE, S.V34, S.HOLD = True, True, True
    S.FILT = False; S.use_prefilter()
    S.OVERDUB, S.NOPLAYREC = od, npr
    w, lab = S.code(AT, TB, TMAX, pre_ret=FXH + 2)
    cw, _ = B.chain()
    P = [0] * 0x4000
    P[FXH:FXH + len(cw)] = cw; P[FXH:FXH + 2] = D.jmp(lab["smp_tail"]); P[AT:AT + len(w)] = w
    def setx(addr, v): return T_("move #>$%x,x0" % (v & 0xFFFFFF), "move x0,x:>$%x" % addr)
    def go(steps, mem=()):
        drv = T_("move #>$123456,m4", "move #>$111,r4", "move #>$222,r5", "move #>$333,r6", "move #>$444,r0", "move #>$555,r1")
        for s_ in steps: drv += D.jsr(AT) if s_ == "call" else s_
        drv += T_("move m4,x:>$3c00", "move r4,x:>$3c01", "move r5,x:>$3c02", "move r6,x:>$3c03") + [0x00000C]
        P2 = list(P); P2[DRV:DRV + len(drv)] = drv
        r, _ = run(P2, DRV, mem=[('x', 0x3A, [NF]), ('x', G.FX_ON, [0x2A]), ('x', S.MAGIC_AT, [S.MAGIC])] + list(mem), maxins=3_000_000,
                   dumps=[('x', S.SMB, 0x20), ('x', S.PF_L, NF), ('x', S.PF_R, NF), ('y', TB, TMAX), ('x', 0x3C00, 4)])
        return r
    return go, setx


def s24(v): return v - (1 << 24) if v & 0x800000 else v


def main():
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    st = lambda r, k: r[('x', S.SMB)][k - S.SMB]
    LENP = 300
    ramp = [(i + 1) * 0x100 for i in range(LENP)]
    Ls, Rs = [0x1000 * (i + 1) for i in range(NF)], [0x0800 * (i + 1) for i in range(NF)]
    arrays = lambda l, r: [('x', S.PF_L, l), ('x', S.PF_R, r)]
    zero = arrays([0] * NF, [0] * NF)
    base = [('y', TB, ramp), ('x', S.LEN, [LENP]), ('x', S.PREV, [0])]
    # ---- RC4.16
    go, setx = harness(False, True)
    pre = setx(S.SF, 0) + setx(S.EF, 0x7FFFFF) + setx(S.INCI, 1) + setx(S.INCF, 0) + setx(S.MODE, 0)
    r = go([pre, setx(S.STATE, 1), "call", setx(S.CMD, 1), "call"], mem=base + zero)
    check(st(r, S.PLAY) == 0 and r[('x', S.PF_L)] == [0] * NF, f"noplayrec: CMD 1 while recording plays nothing (PLAY {st(r, S.PLAY)})")
    r = go([pre, setx(S.STATE, 1), "call", setx(S.STATE, 0), setx(S.CMD, 1), "call"], mem=base + arrays(Ls, Rs))
    check(st(r, S.PI) == TB + NF and r[('x', S.PF_L)] != Ls, "noplayrec: released, CMD 1 plays the new take (one shot, to its end)")
    r = go([pre, setx(S.CMD, 1), "call", setx(S.CMD, 3), "call"], mem=base + zero)
    check(st(r, S.PLAY) == 0, "noplayrec: CMD 3 stops")
    # ---- Alpha 7.04
    go, setx = harness(True, False)
    pre = setx(S.SF, 0) + setx(S.EF, 0x7FFFFF) + setx(S.INCI, 1) + setx(S.INCF, 0) + setx(S.MODE, 0)
    r = go([pre, setx(S.CMD, 1), "call", setx(S.STATE, 1), "call"], mem=base + arrays(Ls, Rs))
    y = r[('y', TB)]
    s = ramp[NF:2 * NF]                                                       # the second call plays the next frames of the old take
    L1 = [l + (v >> 4) for l, v in zip(Ls, ramp)]; R1 = [r_ + (v >> 4) for r_, v in zip(Rs, ramp)]   # (the first call's sample stays in the arrays)
    want = [(l + r_) * 8 + round(0.7 * (16 * (v >> 4))) for l, r_, v in zip(L1, R1, s)]
    got = [s24(v) for v in y[:NF]]
    check(st(r, S.PLAY) == 1, "overdub: a recording does not stop the playback")
    check(r[('x', S.PF_L)] == [l + (v >> 4) for l, v in zip(L1, s)], "overdub: the playback goes on with the old take's next frames (LEN restarted)")
    check(all(abs(g - w_) <= 1 for g, w_ in zip(got, want)), f"overdub: the take = the mix + 0.7 x the sample ({got[:3]} vs {want[:3]})")
    check(st(r, S.LEN) == NF, f"overdub: the new take's length {st(r, S.LEN)}")
    r = go([setx(S.STATE, 1), "call"], mem=base + arrays(Ls, Rs))
    check([s24(v) for v in r[('y', TB)][:NF]] == [(l + r_) * 8 for l, r_ in zip(Ls, Rs)], "overdub: nothing playing: the take = the mix (as before)")
    r = go([pre, setx(S.CMD, 1), "call", "call"], mem=base + arrays(Ls, Rs))
    check(r[('y', TB)][:LENP] == ramp, "overdub: playing without recording writes nothing")
    check(r[('x', 0x3C00)] == [0x123456, 0x111, 0x222, 0x333], f"m4 / r4 / r5 / r6 back ({[hex(v) for v in r[('x', 0x3C00)]]})")
    r = go([pre, setx(S.CMD, 1), "call", setx(S.STATE, 1), "call"], mem=base + arrays(Ls, Rs))
    check(r[('x', 0x3C00)] == [0x123456, 0x111, 0x222, 0x333], "m4 / r4 / r5 / r6 back after an overdub block")
    print("OVERDUB DSP RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
