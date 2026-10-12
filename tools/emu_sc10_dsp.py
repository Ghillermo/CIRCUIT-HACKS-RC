"""SC10 DSP tests on the dsp56kEmu interpreter: stock vs patched core-0 fragments."""
import sys, random, subprocess, os
sys.path.insert(0, os.path.dirname(__file__))
from dspemu import run
import build_sc10 as b10
from dsp_session import dsp_program

N = 16          # frames per block (x:$3a)
FLAGS = 0xEC    # SC10 flag address in DSP X memory (SC14.2: 0x3A00)


def prog(img):                     # via the loader table (SC16+ relocate the core-0 block)
    b = dsp_program(img)
    return [int.from_bytes(b[i:i + 3], 'big') for i in range(0, len(b), 3)]


def s24(v): return v - (1 << 24) if v & 0x800000 else v
def sat(v): return max(-0x800000, min(0x7FFFFF, v))


def main(stock, img):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    PS, PP = prog(stock), prog(img)
    rnd = random.Random(1)
    rev = [rnd.randrange(-0x200000, 0x200000) & 0xFFFFFF for _ in range(2 * N)]
    dly = [rnd.randrange(-0x200000, 0x200000) & 0xFFFFFF for _ in range(2 * N)]
    g3 = [rnd.randrange(0, 0x080000) for _ in range(2 * N)]          # strip gains (<= ~0.0625)
    g4 = [rnd.randrange(0, 0x080000) for _ in range(2 * N)]
    base = [('x', 0x3A, [N]), ('y', 0x880, rev), ('y', 0x9C0, dly), ('x', 0x20C, g3), ('x', 0x24C, g4), ('x', 0x18B, [1])]
    dumps = [('y', 0x880, 2 * N), ('y', 0x9C0, 2 * N)]
    ref, r0 = run(PS, 0, mem=base, dumps=dumps, pc=0xD21, stop=0xD32)
    for flags in (0, 1, 2, 3):
        res, ran = run(PP, 0, mem=base + [('x', FLAGS, [flags])], dumps=dumps, pc=0xD21, stop=0xD32)
        exp = []
        for i in range(2 * N):
            r = s24(rev[i]); d = s24(dly[i])
            if flags & 1: r = sat((r * g3[i] >> 23) << 4) if False else sat(((r * g3[i]) >> 23) * 16)
            if flags & 2: d = sat(((d * g4[i]) >> 23) * 16)
            exp.append(((r + d) >> 1) & 0xFFFFFF)
        got = res.get(('y', 0x880))
        if flags == 0:
            check(got == ref[('y', 0x880)] and ran and ('pc=000d32' in ran), f"flags=0: returns identical to stock ({ran})")
        diff = max(abs(s24(a) - s24(b)) for a, b in zip(got, exp))
        check(diff <= 16 * 2 + 2, f"flags={flags}: returns = (reverb*g3*16 if bit0) + (delay*g4*16 if bit1) >> 1 (max diff {diff})")
    # premix: input ring at y:(y:$ffd)
    ring = [rnd.randrange(1, 0x7FFFFF) for _ in range(2 * N)]
    m = [('x', 0x3A, [N]), ('y', 0xFFD, [0x400]), ('y', 0x400, ring)]
    rs, _ = run(PS, 0, mem=m, dumps=[('y', 0x400, 2 * N + 2)], pc=0x23C, stop=0x23E)
    for flags in (0, 1, 2, 3):
        res, ran = run(PP, 0, mem=m + [('x', FLAGS, [flags])], dumps=[('y', 0x400, 2 * N + 2)], pc=0x23C, stop=0x23E)
        exp = [0 if ((i % 2 == 0 and flags & 1) or (i % 2 == 1 and flags & 2)) else ring[i] for i in range(2 * N)] + [0, 0]
        check(res[('y', 0x400)] == exp and ('pc=00023e' in ran), f"premix flags={flags}: inputs muted as flagged, rest untouched ({ran})")
        if flags == 0:
            check(res[('y', 0x400)] == rs[('y', 0x400)], "premix flags=0 identical to stock")
    # the main mix then uses r5 = y:$ffd: run patched P:$23C..$24F-ish? check r5 by a follow-up store
    res, ran = run(PP, 0, mem=[('x', FLAGS, [0x123456])], dumps=[('x', FLAGS, 1)], pc=0x10B, stop=0x10D)
    check(res[('x', FLAGS)] == [0], f"init hook clears X:${FLAGS:X} ({ran})")
    print("SC10 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(open(sys.argv[1], 'rb').read(), open(sys.argv[2], 'rb').read()) else 0)
