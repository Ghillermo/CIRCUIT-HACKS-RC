"""SC16 DSP tests (dsp56kEmu interpreter): drum side-chain hook vs the stock side-chain envelope.
(SC13 tests with the SC16 addresses: blocks at X:$3A10 + 9k, code after the stock program.)"""
import sys, os, random, json
sys.path.insert(0, os.path.dirname(__file__))
from dspemu import run
from dsp_session import dsp_program

N = 32                      # frames per block (x:$3a); x:$39 = log2 N
BLK, ENV = 0x3A10, 0x2028
CLR_FROM, CLR_N = 0x3A00, 0x34


def prog(img):
    b = dsp_program(img)
    return [int.from_bytes(b[i:i + 3], 'big') for i in range(0, len(b), 3)]


def s24(v): return v - (1 << 24) if v & 0x800000 else v


def mpy(x, y):              # mpy y0,x0,a ; move a,x:  (a1, limited)
    p = (s24(x) * s24(y)) << 1
    a1 = p >> 24
    return max(-0x800000, min(0x7FFFFF, a1)) & 0xFFFFFF


def main(stock, img, labels):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    PS, PP = prog(stock), prog(img)
    mix = int(labels["mixhook"], 16)
    rnd = random.Random(7)
    common = [('x', 0x3A, [N]), ('x', 0x39, [5]), ('y', 0x10, [0x7FFFFF])]

    # 1. init: X:$3A00..$3A33 cleared (SC10 flag, SC15 modes, drum blocks), neighbours untouched
    res, ran = run(PP, 0, mem=[('x', CLR_FROM - 1, [0x777777] + [0x5A5A5A] * CLR_N + [0x777777])],
                   dumps=[('x', CLR_FROM - 1, CLR_N + 2)], pc=0x10B, stop=0x10D)
    got = res[('x', CLR_FROM - 1)]
    check(got == [0x777777] + [0] * CLR_N + [0x777777], f"init: X:$3A00..$3A33 = 0, neighbours untouched ({ran})")

    # 2. depth 0: nothing changes (all 4 drums), r0 = $2e70, block trigger kept
    for d in range(4):
        sig = [rnd.randrange(0, 1 << 24) for _ in range(N)]
        blk = BLK + 9 * d
        mem = common + [('x', 0x1ED6, [0x9F + d]), ('x', 0x2C02, sig), ('x', blk, [1, 5, 9, 9, 0, 1, 2, 3, 4])]
        res, ran = run(PP, mix, mem=mem, dumps=[('x', 0x2C02, N), ('x', blk, 9)])
        check(res[('x', 0x2C02)] == sig and res[('x', blk)] == [1, 5, 9, 9, 0, 1, 2, 3, 4],
              f"drum {d+1} depth 0: signal and block untouched ({ran})")

    # 3. depth > 0: envelope = stock func_001277 (synth 1 side-chain) with the same params/state/trigger
    for d, (atk, hold, dec, depth) in ((0, (0x200000, 0x080000, 0x010000, 0x7F0000)), (1, (0x7FFFFF, 0x000100, 0x004000, 0x500000)),
                                       (2, (0x040000, 0x7FFFFF, 0x7FFFFF, 0x7B0000)), (3, (0x100000, 0x020000, 0x000800, 0x640000))):
        blk = BLK + 9 * d
        state = [0, 0, 0, 0]
        ok, maxd, mins = True, 0, []
        for blkno in range(12):
            trig = 1 if blkno in (0, 5) else 0
            sig = [rnd.randrange(0, 1 << 24) for _ in range(N)]
            # stock reference: synth 1 channel: X:$3F2 [src, atk, hold, decay, depth], state Y:$2008, trigger bit0 of X:$99+src
            ref, rr = run(PS, 0x1277, mem=common + [('x', 0x3F2, [2, atk, hold, dec, depth]), ('y', 0x2008, state),
                                                     ('x', 0x99, [0, 0, trig, 0])],
                          dumps=[('y', ENV, N), ('y', 0x2008, 4), ('x', 0x9B, 1)])
            env = ref[('y', ENV)]
            exp = [mpy(s, e) for s, e in zip(sig, env)]
            mem = common + [('x', 0x1ED6, [0x9F + d]), ('x', 0x2C02, sig), ('x', blk, [trig, atk, hold, dec, depth] + state),
                            ('y', 0x204C, [0]), ('x', 0x99, [0xF, 0xF, 0xF, 0xF])]
            res, ran = run(PP, mix, mem=mem, dumps=[('x', 0x2C02, N), ('x', blk, 9), ('x', 0x99, 4)])
            got = res[('x', 0x2C02)]
            nstate = res[('x', blk)][5:]
            ok &= got == exp and nstate == ref[('y', 0x2008)] and res[('x', blk)][0] == 2 and res[('x', 0x99)] == [0xF] * 4
            if not ok:
                print("   block", blkno, "state", [hex(x) for x in nstate], [hex(x) for x in ref[('y', 0x2008)]], ran)
                break
            state = nstate
            mins.append(min(env))
        check(ok, f"drum {d+1}: 12 blocks, 2 triggers: signal x stock side-chain envelope (exact), state and trigger as stock (block flag = advanced)")
        check(min(mins) < 0x7FFFFF * 0.8,
              f"drum {d+1}: envelope really ducks (min gain per block: {[round(m / 0x800000, 2) for m in mins]})")

    # 4. the hook inside the stock drum mix: P:$218E..$21AA  (depth 0 = bit-exact stock; depth > 0 = stock on ducked input)
    for d in (0, 3):
        sig = [rnd.randrange(0, 1 << 24) for _ in range(N)]
        gains = [rnd.randrange(0, 0x100000) for _ in range(6 * N)]
        acc = [rnd.randrange(0, 0x100000) for _ in range(2 * N)]
        base = common + [('x', 0x1ED6, [0x9F + d]), ('y', 0x1BB5, gains), ('x', 0x2E70, acc), ('x', 0x2EB0, acc), ('x', 0x2EF0, acc)]
        dumps = [('x', 0x2E70, 2 * N), ('x', 0x2EB0, 2 * N), ('x', 0x2EF0, 2 * N)]
        rs, r1 = run(PS, 0, mem=base + [('x', 0x2C02, sig)], dumps=dumps, pc=0x218E, stop=0x21AB)
        rp, r2 = run(PP, 0, mem=base + [('x', 0x2C02, sig), ('x', BLK + 9 * d, [0] * 9)], dumps=dumps, pc=0x218E, stop=0x21AB)
        check(rs == rp and ('pc=0021ab' in r2), f"drum {d+1} mix, side-chain off: identical to stock ({r1} / {r2})")
        atk, hold, dec, depth = 0x7FFFFF, 0x080000, 0x010000, 0x7F0000
        ref, _ = run(PS, 0x1277, mem=common + [('x', 0x3F2, [0, atk, hold, dec, depth]), ('y', 0x2008, [0] * 4), ('x', 0x99, [1])],
                     dumps=[('y', ENV, N)])
        duck = [mpy(s, e) for s, e in zip(sig, ref[('y', ENV)])]
        rs2, _ = run(PS, 0, mem=base + [('x', 0x2C02, duck)], dumps=dumps, pc=0x218E, stop=0x21AB)
        rp2, r3 = run(PP, 0, mem=base + [('x', 0x2C02, sig), ('x', BLK + 9 * d, [1, atk, hold, dec, depth, 0, 0, 0, 0])],
                      dumps=dumps, pc=0x218E, stop=0x21AB)
        check(rp2 == rs2 and rp2 != rs, f"drum {d+1} mix, side-chain on: = stock mix of the ducked signal ({r3})")

    # 5. silent voice: the idle exit (P:$21AB) keeps the envelope running; mixed voice: advanced once only
    idle = int(labels["idle"], 16)
    atk, hold, dec, depth = 0x200000, 0x080000, 0x010000, 0x7F0000
    for d in (1, 2):
        blk = BLK + 9 * d
        ref, _ = run(PS, 0x1277, mem=common + [('x', 0x3F2, [0, atk, hold, dec, depth]), ('y', 0x2008, [0] * 4), ('x', 0x99, [1])],
                     dumps=[('y', 0x2008, 4)])
        sig = [rnd.randrange(0, 1 << 24) for _ in range(N)]
        mem = common + [('x', 0x1ED6, [0x9F + d]), ('x', 0x2C02, sig), ('x', blk, [1, atk, hold, dec, depth, 0, 0, 0, 0])]
        res, ran = run(PP, idle, mem=mem, dumps=[('x', 0x2C02, N), ('x', blk, 9)])
        check(res[('x', 0x2C02)] == sig and res[('x', blk)][5:] == ref[('y', 0x2008)] and res[('x', blk)][0] == 0,
              f"drum {d+1} silent: idle exit advances the envelope like stock, signal untouched ({ran})")
        # mixed voice: P:$218E..$21AB then idle -> advanced exactly once, flag cleared
        res, ran = run(PP, 0, mem=mem + [('y', 0x1BB5, [0] * 6 * N)], dumps=[('x', blk, 9)], pc=0x218E, stop=0x21AB)
        check(res[('x', blk)][0] == 2 and res[('x', blk)][5:] == ref[('y', 0x2008)], f"drum {d+1} mixed: advanced, flag set ({ran})")
        mem2 = common + [('x', 0x1ED6, [0x9F + d]), ('x', blk, res[('x', blk)])]
        res2, ran = run(PP, idle, mem=mem2, dumps=[('x', blk, 9)])
        check(res2[('x', blk)] == [0] + res[('x', blk)][1:], f"drum {d+1} mixed then idle exit: no second advance, flag cleared")
        res3, _ = run(PP, idle, mem=common + [('x', 0x1ED6, [0x9F + d]), ('x', blk, [1, atk, hold, dec, 0, 5, 6, 7, 8])],
                      dumps=[('x', blk, 9)])
        check(res3[('x', blk)] == [1, atk, hold, dec, 0, 5, 6, 7, 8], f"drum {d+1} OFF: idle exit touches nothing")
    # 6. whole drum section (func_00208a, 4 silent voices): side-chain off = stock
    vs = [0] * (0x12 * 4)
    base = common + [('x', 0x1E8D, vs), ('x', 0x9F, [0, 0, 0, 0])]
    dumps = [('x', 0x2E70, 2 * N), ('x', 0x2EB0, 2 * N), ('x', 0x2EF0, 2 * N), ('x', 0x1E8D, 0x48), ('x', 0x9F, 4)]
    rs, r1 = run(PS, 0x208A, mem=base, dumps=dumps)
    rp, r2 = run(PP, 0x208A, mem=base + [('x', CLR_FROM, [0] * CLR_N)], dumps=dumps)
    check(rs == rp, f"func_00208a, 4 silent drums, side-chain off: identical to stock ({r1} / {r2})")
    blk = BLK + 9 * 1
    rp2, r3 = run(PP, 0x208A, mem=base + [('x', CLR_FROM, [0] * CLR_N), ('x', blk, [1, 0x200000, 0x080000, 0x010000, 0x7F0000, 0, 0, 0, 0])],
                  dumps=dumps + [('x', blk, 9)])
    ref, _ = run(PS, 0x1277, mem=common + [('x', 0x3F2, [0, 0x200000, 0x080000, 0x010000, 0x7F0000]), ('y', 0x2008, [0] * 4), ('x', 0x99, [1])],
                 dumps=[('y', 0x2008, 4)])
    check(rp2[('x', blk)][5:] == ref[('y', 0x2008)] and rp2[('x', blk)][0] == 0 and all(rp2[k] == rs[k] for k in rs),
          f"func_00208a, drum 2 silent with side-chain on + trigger: envelope advanced once inside the drum loop ({r3})")
    print("SC16 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    man = json.loads(open(sys.argv[3]).read())
    sys.exit(1 if main(open(sys.argv[1], 'rb').read(), open(sys.argv[2], 'rb').read(), man["report"]["sc16"]["dsp_labels"]) else 0)
