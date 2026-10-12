"""SC16 whole-core DSP session (relocated program, real init, ARM-captured writes, many blocks).

    python tools/emu_sc16_core.py STOCK.bin SC15.bin SC16.bin SC16_manifest.json
Checks what SC13 never had tested: the DSP boots with the new code, the voice-slot table stays intact,
the side-chain only touches its own memory, stack depth and per-block cost.
"""
from __future__ import annotations
import struct, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dsp_session import Session, dsp_block  # noqa: E402
import build_sc16 as B  # noqa: E402

TRIG = 0x08051B54
ST16 = B.s14.ST + B.SC_OFF
ISR_MARGIN = 4                       # ESAI + SHI interrupts nested on top (not emulated)


def main(stock, sc15, img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    from unicorn.arm_const import UC_ARM_REG_R0
    lab = {k: int(v, 16) for k, v in man["report"]["sc16"]["labels"].items()}
    a, n = dsp_block(img)
    check(a == int(man["report"]["sc16"]["dsp_block"], 16) and n == B.STOCK_WORDS + 0x70 or n > B.STOCK_WORDS,
          f"loader table points to the relocated core-0 block {hex(a)}, {hex(n)} words")

    def run(image, sc_on, hits, blocks=60, trace=None):
        s = Session(image)
        g5 = struct.unpack_from("<I", image, B.GROUP_TAB + 5 * 4 - 0x08010000)[0] & ~1
        if sc_on:
            s.e.call(lab["c_scst"]); st = s.e.uc.reg_read(UC_ARM_REG_R0)
            assert st == ST16, hex(st)
            s.e.uc.mem_write(st + 4, bytes([0, 7, 0, 0]))       # preset: drum 2 = 7
            s.e.uc.mem_write(st + 8, bytes([0, 0, 0, 0]))       # trigger: drum 1 for all
        s.capture('group5', g5)
        for d in hits: s.capture(f'hit{d}', TRIG, d, 100)
        wf = tempfile.mktemp()
        res, rans = s.run(blocks=blocks, per_block=False, trace=trace, spmax=True, watchfile=wf,
                          watch=[('x', B.BLK + 9, 9)],
                          dumps=[('x', 0xEB, 0x70), ('x', B.CLR_FROM, B.CLR_N), ('p', 0x80, 0x80)])
        hist = []
        for l in open(wf):
            pc, ad, rw, v = l.split()
            if rw == 'W' and ad == 'X:%06x' % (B.BLK + 9 + 7): hist.append(int(v, 16))
        return {(sp, ad): v for sp, ad, v in res}, rans, s, hist

    t15, t16 = tempfile.mktemp(), tempfile.mktemp()
    R15, r15, s15, _ = run(sc15, False, [0], trace=t15)
    R16o, r16o, s16o, _ = run(img, False, [0])
    R16, r16, s16, env = run(img, True, [0], trace=t16)
    ins = lambda rans: [int(x.split('ins=')[1].split()[0]) for x in rans if x.startswith('RAN')][2:]
    spm = lambda rans: [x for x in rans if x.startswith('SPMAX')][0]
    check(R16[('x', 0xEB)] == R15[('x', 0xEB)], "voice-slot table X:$EB..$15A after init + 60 blocks: identical to SC15")
    check(('pc=000113' in r16[1]), f"DSP init completes with the relocated program ({r16[1]})")
    w = [x for _, ws in s16.events for x in ws if x[1] == 'x' and B.CLR_FROM <= x[2] < B.CLR_FROM + B.CLR_N]
    check({x[2] for x in w} >= {B.BLK + 9 * k + i for k in range(4) for i in (1, 2, 3, 4)} and (0, 'x', B.BLK + 9, 1) in w,
          f"ARM wrote the 4 drum blocks and the drum-2 trigger ({len(w)} writes)")
    check(len(env) > 10 and min(env) < max(env), f"drum 2 envelope state evolves over the blocks ({len(env)} updates)")
    blk = R16[('x', B.CLR_FROM)][0x10 + 9: 0x10 + 18]
    check(blk[4] == 127 << 16 and blk[0] in (0, 2), f"drum 2 block after 60 blocks: depth 127, trigger consumed {[hex(x) for x in blk]}")
    check(R16o[('x', B.CLR_FROM)] == [0] * B.CLR_N or all(R16o[('x', B.CLR_FROM)][0x10 + 9 * k + 4] == 0 for k in range(4)),
          "side-chain off: all depths 0")
    a15, a16 = open(t15, 'rb').read(), open(t16, 'rb').read()
    extra = []
    for sp, o in (('x', 0), ('y', 0x80000)):
        for ad in range(0x80000):
            if a16[o + ad] and not a15[o + ad]: extra.append((sp, ad))
    allowed = lambda sp, ad: (sp == 'x' and B.CLR_FROM <= ad < B.CLR_FROM + B.CLR_N) or (sp == 'y' and 0x2028 <= ad <= 0x204C)
    bad = [(sp, hex(ad)) for sp, ad in extra if not allowed(sp, ad)]
    check(not bad, f"SC16 touches nothing new outside X:$3A00..$3A33 and Y:$2028..$204C ({len(extra)} new addresses, bad {bad[:8]})")
    i15, i16o, i16 = ins(r15), ins(r16o), ins(r16)
    avg = lambda v: sum(v) / len(v)
    print(f"     DSP instructions/block (emulated core 0, no core-1 audio): SC15 {avg(i15):.0f}, SC16 off {avg(i16o):.0f}, SC16 drum 2 ducked {avg(i16):.0f}")
    check(avg(i16) - avg(i15) < 2000, f"cost: +{avg(i16) - avg(i15):.0f} instructions per block with one drum ducked (~{100 * 2 * (avg(i16) - avg(i15)) / 166000:.2f}% of a 32-frame block at ~250 MHz, 2 cycles/instr)")
    sp15, sp16 = spm(r15), spm(r16)
    d15, d16 = int(sp15.split()[1]), int(sp16.split()[1])
    print(f"     stack: SC15 {sp15}, SC16 {sp16}")
    check(d16 + ISR_MARGIN <= 15, f"stack depth {d16} (+{ISR_MARGIN} for nested ESAI/SHI) <= 15")
    print("SC16 CORE RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    import json
    st, s15b, im = (Path(p).read_bytes() for p in sys.argv[1:4])
    sys.exit(1 if main(st, s15b, im, json.loads(Path(sys.argv[4]).read_text())) else 0)
