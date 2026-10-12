"""SC14 DSP test: master gain ramp (P:$21D9 asr #$b -> #$6)."""
import sys, os, random
sys.path.insert(0, os.path.dirname(__file__))
from dspemu import run
import build_sc10 as b10
from dsp_session import dsp_program

N = 32
def prog(img):                     # via the loader table (SC16+ relocate the core-0 block)
    b = dsp_program(img)
    return [int.from_bytes(b[i:i + 3], 'big') for i in range(0, len(b), 3)]
def s24(v): return v - (1 << 24) if v & 0x800000 else v

def main(stock, img):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    PS, PP = prog(stock), prog(img)
    rnd = random.Random(3)
    sig = [rnd.randrange(0x100000, 0x180000) for _ in range(2 * N)]      # positive test signal
    for comp in (0, 1):
        base = [('x', 0x3A, [N]), ('x', 0x39, [5]), ('y', 0x10, [0x7FFFFF]), ('y', 0xFFD, [0x400]), ('x', 0x2E10, sig),
                ('x', 0x1EE5, [comp]), ('x', 0x1EE6, [0x7F0000])]
        dumps = [('x', 0x400, 2 * N), ('x', 0x1EE6, 1)]
        for de, name in ((0x7F0000, "constant gain"), (0, "gain -> 0")):
            rs, r1 = run(PS, 0, mem=base + [('x', 0xDE, [de])], dumps=dumps, pc=0x262, stop=0x278)
            rp, r2 = run(PP, 0, mem=base + [('x', 0xDE, [de])], dumps=dumps, pc=0x262, stop=0x278)
            gs, gp = rs[('x', 0x1EE6)][0], rp[('x', 0x1EE6)][0]
            if de:
                check(rs == rp, f"compressor={comp}, {name}: output identical to stock ({r1} / {r2})")
            else:
                check(gs > 0x7A0000 and gp < 0x420000 and ('pc=000278' in r2),
                      f"compressor={comp}, {name}: gain after 1 block stock {gs / 0x7F0000:.2f}, SC14 {gp / 0x7F0000:.2f}")
                # a few blocks later SC14 is (almost) closed
                g = 0x7F0000; outs = []
                for _ in range(6):
                    r, _ = run(PP, 0, mem=base[:-1] + [('x', 0x1EE6, [g]), ('x', 0xDE, [0])], dumps=dumps, pc=0x262, stop=0x278)
                    g = r[('x', 0x1EE6)][0]; outs.append(g)
                check(outs[-1] < 0x7F0000 // 50, f"compressor={comp}: closed to {outs[-1] / 0x7F0000:.3f} after 7 blocks (~4.7 ms)")
    print("SC14 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails

if __name__ == "__main__":
    sys.exit(1 if main(open(sys.argv[1], 'rb').read(), open(sys.argv[2], 'rb').read()) else 0)
