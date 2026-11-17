"""SC57.9 / Beta 5.64 DSP tests (masterfx_dsp.use_fsqmute): the FX sequencer's mute step = the master output faded to silence and back, at the
end of the Master FX chain (the module's code on the dsp56kEmu interpreter against a bit-exact model, as emu_masterfx_dsp):
  * FX_ON bit 7 with the gain at unity: every frame x (1 - (i + 1) x STEP), the gain stored after the block; a second block goes on down to 0;
  * silent (gain 0) with the bit set: the block zeroed, the gain stays 0 (the `tmi`);
  * bit clear with the gain at 0: a ramp up, the stored gain limited to $7FFFFF, then nothing more (unity + no bit: the block untouched);
  * all off at unity: the buffer untouched and the gater's gain reset as before (the chain's old behaviour).

    python tools/emu_fsqmute_dsp.py STOCK.bin
"""
from __future__ import annotations
import random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import masterfx_dsp as G  # noqa: E402
from emu_masterfx_dsp import Acc, u24, s24  # noqa: E402

N = 32
BASE = 0x2ACE
UNITY = 0x7FFFFF


def model(buf, g0, down):
    """the block through `mut`: g += +-STEP a frame, down stops at 0 (tmi), up is limited at the uses; -> (out, the stored gain)"""
    out = list(buf); a = g0                       # a = the accumulator's value (may pass $7FFFFF going up)
    for i in range(N):
        a = a - G.MUTE_STEP if down else a + G.MUTE_STEP
        if a < 0: a = 0
        y0 = min(a, UNITY)
        for c in (0, 1): out[2 * i + c] = Acc().mpy(y0, out[2 * i + c]).lim()
    return out, min(a, UNITY)


def main(stock):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    G.use_fsqmute()
    sp = dsp_program(stock)
    P = [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]
    words, lab = G.code(BASE)
    P = P[:BASE] + [0] * (BASE - len(P)) + words
    rnd = random.Random(5)
    sig = lambda amp=0x300000: [u24(rnd.randrange(-amp, amp)) for _ in range(2 * N)]
    common = [('x', 0x3A, [N])]
    def fx(mem, dumps):
        res, ran = run(P, lab["fx_hook"], mem=common + mem, dumps=dumps)
        assert 'pc=007002' in ran, ran
        return res
    DUMP = [('x', G.BUF, 2 * N), ('x', G.MG, 1), ('x', G.G_CUR, 1)]
    # all off at unity: untouched (the old behaviour: the gater's gain reset to 1)
    buf = sig()
    r = fx([('x', G.BUF, buf), ('x', G.FX_ON, [0]), ('x', G.MG, [UNITY]), ('x', G.G_CUR, [0x123456])], DUMP)
    check(r[('x', G.BUF)] == buf and r[('x', G.G_CUR)] == [UNITY] and r[('x', G.MG)] == [UNITY], "all off at unity: the block untouched, the gater's gain 1, the mute's gain kept")
    # the mute comes: a 2 ms fade down over this block and the next
    buf = sig(); exp, g1 = model(buf, UNITY, True)
    r = fx([('x', G.BUF, buf), ('x', G.FX_ON, [1 << G.B_MUTE]), ('x', G.MG, [UNITY]), ('x', G.G_CUR, [UNITY])], DUMP)
    check(r[('x', G.BUF)] == exp and r[('x', G.MG)] == [g1] and 0 < g1 < UNITY, f"bit 7 from unity: each frame x a falling gain (bit-exact), gain stored {g1:#x} after 32 frames")
    buf = sig(); exp, g2 = model(buf, g1, True)
    r = fx([('x', G.BUF, buf), ('x', G.FX_ON, [1 << G.B_MUTE]), ('x', G.MG, [g1]), ('x', G.G_CUR, [UNITY])], DUMP)
    check(r[('x', G.BUF)] == exp and r[('x', G.MG)] == [g2], f"the next block goes on down ({g2:#x})")
    for _ in range(4):
        exp, g2 = model(buf, g2, True)
    check(g2 == 0 and exp[-4:] == [0, 0, 0, 0], "by the fourth block the gain is 0 (2 ms) and the output silent")
    # silent and still muted: zeros, the gain stays 0
    buf = sig()
    r = fx([('x', G.BUF, buf), ('x', G.FX_ON, [1 << G.B_MUTE]), ('x', G.MG, [0]), ('x', G.G_CUR, [UNITY])], DUMP)
    check(r[('x', G.BUF)] == [0] * (2 * N) and r[('x', G.MG)] == [0], "silent and muted: the block zeroed, the gain stays 0")
    # the mute goes: a ramp up from 0, then unity and nothing more
    buf = sig(); exp, g3 = model(buf, 0, False)
    r = fx([('x', G.BUF, buf), ('x', G.FX_ON, [0]), ('x', G.MG, [0]), ('x', G.G_CUR, [UNITY])], DUMP)
    check(r[('x', G.BUF)] == exp and r[('x', G.MG)] == [g3] and 0 < g3 < UNITY, f"bit clear from 0: a rising gain (bit-exact), {g3:#x} after 32 frames")
    g = g3
    for _ in range(4): exp, g = model(buf, g, False)
    buf = sig(); exp, g4 = model(buf, g3, False); exp2, g5 = model(exp, g4, False); exp3, g6 = model(exp2, g5, False)
    r = fx([('x', G.BUF, buf), ('x', G.FX_ON, [0]), ('x', G.MG, [g5]), ('x', G.G_CUR, [UNITY])], DUMP)
    check(g == UNITY and r[('x', G.MG)] == [UNITY], f"the gain reaches unity within 2 ms and is stored limited to $7FFFFF ({r[('x', G.MG)][0]:#x})")
    buf = sig()
    r = fx([('x', G.BUF, buf), ('x', G.FX_ON, [0]), ('x', G.MG, [UNITY]), ('x', G.G_CUR, [UNITY])], DUMP)
    check(r[('x', G.BUF)] == buf, "at unity with the bit clear: the block untouched (no work)")
    # with another effect on, the mute still applies after it (the Digitise at N = 1 is a pass-through)
    buf = sig(); exp, g7 = model(buf, UNITY, True)
    r = fx([('x', G.BUF, buf), ('x', G.FX_ON, [(1 << G.B_MUTE) | (1 << G.B_DIG)]), ('x', G.DG_N, [1, 0xFFFFFF, 0, 0, 0]), ('x', G.MG, [UNITY]), ('x', G.G_CUR, [UNITY])], DUMP)
    check(r[('x', G.BUF)] == exp and r[('x', G.MG)] == [g7], "with the Digitise on (pass-through), the mute still fades the block")
    print("FSQMUTE DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes()) else 0)
