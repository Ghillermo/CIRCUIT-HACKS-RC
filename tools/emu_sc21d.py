"""SC21D tests: the DSP probe (tools/probe21_dsp.py, on the dsp56kEmu interpreter with the real core 0 program) and the display / NRPN monitor (tools/probe21.py, on the RAM dump).

    python tools/emu_sc21d.py SC20D.1.bin SC21D.bin SC20D.1_manifest.json SC21D_manifest.json
DSP probe:
  * runs once (the flag X:$3BF0): the second call changes nothing; the registers it uses are restored; the status register (interrupt mask) is as found;
  * the facts: magic, P-RAM write tests (the word is restored afterwards), P:$3800 was 0 / $FFFFFF, shared word 0, results in Y:$3B10..$3B18, and nothing else of X / Y written;
  * it ends with `jmp premix` (same stack depth) and is on the P:$23C hook.
ARM:
  * the DSP service chain head = c_dtick21 (then SC19's c_dtick19), the first bytes of the stock CC dispatcher = b.w c_nrpnlog;
  * the NRPN monitor keeps r0..r3, runs the displaced instructions and the stock body (the registers / stack the stock code gets are the ones it would get), stores [CC, value, MSB, LSB, data, count];
  * the display: closed = nothing read; open = four 4-second pages in rows 2 / 3 (facts LSB first in yellow, OMR in blue, MSB / LSB in green, CC / value in magenta); the magic missing = all red.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc19_1 as T  # noqa: E402
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import probe21 as PR  # noqa: E402
import probe21_dsp as PD  # noqa: E402
import build_sc14 as s14  # noqa: E402
import build_sc15 as B15  # noqa: E402
import drums18  # noqa: E402

BASE = 0x08010000
VIEWS = PR.VIEWS


def T_(*l): return G.T(*l)


class E21(T.E191):
    def __init__(self, image, man):
        super().__init__(image, man)
        self.pl = {k: int(v, 16) for k, v in man["report"]["probe21"]["labels"].items()}
        self.read_map, self.reads = {}, []
        def h(uc, a, s, d):
            ad = uc.reg_read(UC_ARM_REG_R1)
            self.reads.append((uc.reg_read(UC_ARM_REG_R0), ad))
            uc.reg_write(UC_ARM_REG_R0, (self.read_map.get(ad, 0) << 8) & 0xFFFFFFFF)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        self.uc.hook_add(UC_HOOK_CODE, h, begin=PR.DSP_READ, end=PR.DSP_READ)
    def tick21(self, uptime=0):
        self.uc.mem_write(PR.HAL_TICK, struct.pack("<I", uptime))
        self.reads.clear(); self.chain.clear(); self.dw.clear()
        self.call(self.pl["c_dtick21"], maxins=3_000_000)
        return list(self.reads)
    def buf(self, v): return self.r32(self.r32(v + 4))
    def row(self, v, first, n): return list(struct.unpack(f"<{n}H", bytes(self.uc.mem_read(self.buf(v) + 2 * first, 2 * n))))
    def allpads(self, v): return self.row(v, 0, 32)
    def words(self, facts=0, omr=0, magic=PR.MAGIC):
        self.read_map = {0x8000 | PR.YR: magic, 0x8000 | PR.FACTS: facts, 0x8000 | PR.OMR: omr}


def main(prev, img, prevman, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]
    L = {k: int(v, 16) for k, v in rep["probe21"]["labels"].items()}
    # ---------------------------------------------------------------- DSP probe
    dl = {k: int(v, 16) for k, v in rep["sc16"]["dsp_labels"].items()}
    sp = dsp_program(img)
    P0 = [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]
    check(len(P0) <= 0x3800, f"program ends at P:${len(P0):x} (limit $3800); the probe only writes above it")
    YR = PD.YR
    check(P0[0x23C:0x23E] == [0x0BF080, dl["pprobe"]], "P:$23C = jsr pprobe")
    PRG = 0x3800
    Pbig = P0 + [0] * (PRG - len(P0))
    def probe(P, mem=(), dumps=(), regs=()):
        return run(P, dl["pprobe"], mem=[('x', 0x3A, [32])] + list(mem), dumps=[('y', YR, 9), ('x', PD.FLAG, 1), ('x', PD.SAV, 4)] + list(dumps), regs_code=list(regs))
    initr = T_("move #>$a5a5a5,x0", "move #>$5a5a5a,x1", "move #>$33,r0", "move #>$123456,y0")
    res, ran = probe(Pbig, regs=initr, dumps=[('p', a, 1) for a in PD.PTEST])
    ys = res[('y', YR)]
    check('pc=00' in ran, f"the probe returns ({ran})")
    check(ys[0] == PD.MAGIC and res[('x', PD.FLAG)] == [1], "magic written, flag set")
    facts = ys[8]
    check(facts & 1 == 1 and facts == ys[3] and facts >> 14 == 0, f"facts word {facts:#06x}")
    p_ok = [(facts >> (1 + k)) & 1 for k in range(8)]
    check(all(p_ok), f"the interpreter has writable P memory at all 8 test addresses ({p_ok}): write -> read back OK")
    check(all(res[('p', a)] == [0] for a in PD.PTEST if a != 0x7000), "every tested P word was restored (they were 0; P:$7000 is the test stub of the interpreter, which the probe also writes and restores)")
    check((facts >> 9) & 1 == 1 and (facts >> 10) & 1 == 0 and ys[4] == 0, "P:$3800 found 0: bit 9 set, bit 10 clear, raw word 0")
    P_ff = Pbig + []; P_ff = list(P_ff); P_ff[0x3800 - 1] = 0
    res2, _ = run(P_ff + [0xFFFFFF], dl["pprobe"], mem=[('x', 0x3A, [32])], dumps=[('y', YR, 9), ('p', 0x3800, 1)], regs_code=[])
    y2 = res2[('y', YR)]
    check((y2[8] >> 9) & 1 == 0 and (y2[8] >> 10) & 1 == 1 and y2[4] == 0xFFFFFF and res2[('p', 0x3800)] == [0xFFFFFF], "P:$3800 found $FFFFFF: bit 10 set, the word restored")
    check(((facts >> 11) & 1) == (1 if ys[5] == 0 else 0), "bit 11 follows the shared-memory word")
    res3, _ = probe(Pbig, mem=[('x', 0x30000, [0x123456])])
    check(res3[('y', YR)][5] == 0x123456 and (res3[('y', YR)][8] >> 11) & 1 == 0, "X:$030000 read: a non-zero word clears bit 11")
    # registers, SR and the second call
    TR = 0x3900
    regs = ["x0", "x1", "r0"]
    tramp = [0x0BF080, dl["pprobe"]] + T_("move sr,x:>$3bd0", "move x0,x:>$3bd1", "move x1,x:>$3bd2", "move r0,x:>$3bd3") + [0x00000C]
    Pt = Pbig + [0] * (TR - len(Pbig)) + tramp
    pre = initr + T_("move sr,x:>$3bc0")
    resr, ranr = run(Pt, TR, mem=[('x', 0x3A, [32])], dumps=[('x', 0x3BC0, 1), ('x', 0x3BD0, 4)], regs_code=pre)
    sr0 = resr[('x', 0x3BC0)][0]; after = resr[('x', 0x3BD0)]
    check((after[0] ^ sr0) & 0xFFFF00 == 0 and after[1:] == [0xA5A5A5, 0x5A5A5A, 0x33], f"SR (the interrupt mask and mode bits) as found ({sr0:#x} -> {after[0]:#x}; the condition codes differ by the probe's own compares) and x0 / x1 / r0 restored {[hex(x) for x in after]}")
    mem2 = [('x', 0x3A, [32]), ('x', PD.FLAG, [1]), ('y', YR, [0x111111] * 9)]
    res4, _ = probe(Pbig, mem=mem2)
    check(res4[('y', YR)] == [0x111111] * 9, "second call (flag set): nothing is written")
    # nothing else of X / Y written
    zero = [0] * 0x100
    resz, _ = run(Pbig, dl["pprobe"], mem=[('x', 0x3A, [32])], dumps=[('x', 0x3B00, 0x100), ('y', 0x3B00, 0x100), ('x', 0x3A00, 0x100), ('y', 0x3A00, 0x100)], regs_code=[])
    check(resz[('x', 0x3B00)][:0xE0] == [0] * 0xE0 and resz[('y', 0x3B00)][0x20:] == [0] * 0xE0 and resz[('x', 0x3A00)] == zero and resz[('y', 0x3A00)] == zero,
          "only Y:$3B10..$3B18 and X:$3BE0..$3BF0 are written")

    # ---------------------------------------------------------------- ARM
    check(drums18.decode_bw(bytearray(img), s14.SVC_HOOK) == L["c_dtick21"], "DSP service chain head -> c_dtick21 (then SC19's c_dtick19)")
    check(drums18.decode_bw(bytearray(img), PR.CC_FN) == L["c_nrpnlog"], "the stock CC dispatcher starts with b.w c_nrpnlog")
    gc.collect(); e = E21(img, man)
    PAD0, NM = B15.PAD0, rep["linein3"]["modes"]
    snap = [e.allpads(v) for v in VIEWS]
    r = e.tick21()
    check(r == [] and [e.allpads(v) for v in VIEWS] == snap and len(e.chain) == 1, "source view closed: no DSP read, LED buffers untouched, the chain goes on")
    e.btn(0)
    check(e.flag(), "source view open")
    on0, dim0 = B15.COLORS[0]
    def pattern(bits, msb_first, col):
        return [col if (bits >> (15 - i if msb_first else i)) & 1 else 0 for i in range(16)]
    facts = 0b0011111110000011                                                     # a sample
    e.words(facts=facts, omr=0xA5C3)
    r = e.tick21(uptime=0 << 12)
    check(r == [(0, 0x8000 | YR), (0, 0x8000 | PR.FACTS)] and len(e.chain) == 1, f"page 0: two DSP reads (magic, facts) {[hex(a) for _, a in r]}")
    check(e.row(VIEWS[0], 8, 16) == pattern(facts, False, PR.COL[0]) and e.row(VIEWS[1], 8, 16) == pattern(facts, False, PR.COL[0]), f"page 0: facts, pad 9 = bit 0, yellow {e.row(VIEWS[0], 8, 16)}")
    r = e.tick21(uptime=1 << 12)
    check(r == [(0, 0x8000 | YR), (0, 0x8000 | PR.OMR)] and e.row(VIEWS[0], 8, 16) == pattern(0xA5C3, True, PR.COL[1]), f"page 1: OMR 0xA5C3, pad 9 = bit 15, blue")
    tail = lambda msb, lsb, cc, val, data, n: e.uc.mem_write(PR.TAIL, bytes([cc, val, msb, lsb, data, n]))
    tail(0x12, 0x34, 0x56, 0x78, 0x1F, 3)
    r = e.tick21(uptime=2 << 12)
    check(r == [] and e.row(VIEWS[0], 8, 16) == pattern(0x1234, True, PR.COL[2]), "page 2: the last NRPN MSB / LSB (0x12, 0x34), green, no DSP read")
    r = e.tick21(uptime=3 << 12)
    check(r == [] and e.row(VIEWS[0], 8, 16) == pattern(0x5678, True, PR.COL[3]), "page 3: the last CC / value (0x56, 0x78), magenta")
    e.words(facts=facts, omr=0xA5C3, magic=0x123456)
    e.tick21(uptime=0); a0 = e.row(VIEWS[0], 8, 16)
    e.tick21(uptime=1 << 12); a1 = e.row(VIEWS[0], 8, 16)
    check(a0 == [PR.COL_BAD] * 16 and a1 == [PR.COL_BAD] * 16, "magic missing: pages 0 and 1 all red")
    e.tick21(uptime=2 << 12); check(e.row(VIEWS[0], 8, 16) == pattern(0x1234, True, PR.COL[2]), "... the NRPN pages do not depend on the DSP")
    lp = e.pleds(VIEWS[0])
    check(lp[:8] == [0] * 8 and lp[PAD0 + NM:] == [0] * (32 - PAD0 - NM) and lp[PAD0] == on0, "the LED slot repaints rows 1 and 4 (the source pads) and keeps rows 2 / 3")
    e.uc.mem_write(VIEWS[1], struct.pack("<I", 0x1234))
    e.words(facts=1); e.tick21(uptime=0)
    check(e.row(VIEWS[0], 8, 1) == [PR.COL[0]], "a view whose vtable is not the synth Preset view is left alone")

    # ---------------------------------------------------------------- the NRPN monitor
    gc.collect(); e = E21(img, man)
    stopped = []
    def at_next(uc, a, s, d):
        stopped.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3), uc.reg_read(UC_ARM_REG_R4),
                        uc.reg_read(UC_ARM_REG_SP), bytes(uc.mem_read(uc.reg_read(UC_ARM_REG_SP), 16))))
        uc.reg_write(UC_ARM_REG_SP, uc.reg_read(UC_ARM_REG_SP) + 16); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, at_next, begin=PR.CC_NEXT, end=PR.CC_NEXT)
    e.uc.mem_write(PR.TAIL, bytes(6))
    def cc(this, port, num, val):
        stopped.clear()
        e.uc.reg_write(UC_ARM_REG_R4, 0x44444444); e.uc.reg_write(UC_ARM_REG_R5, 0x55555555); e.uc.reg_write(UC_ARM_REG_R6, 0x66666666)
        sp0 = 0x20060000 + 0x8000
        e.call(PR.CC_FN, this, port, num, val)
        return stopped[0] if stopped else None
    s = cc(0x20011000, 3, 99, 5)
    check(s is not None and s[:4] == (0x20011000, 3, 99, 5) and s[4] == 0x20011000, "the CC dispatcher body is reached with r0..r3 intact and the displaced `mov r4, r0` done")
    pushed = struct.unpack("<4I", s[6])
    check(pushed[:3] == (0x44444444, 0x55555555, 0x66666666), f"the displaced push {{r4, r5, r6, lr}} ran (stack {[hex(x) for x in pushed]})")
    for num, val in ((98, 7), (6, 100), (38, 9), (1, 64)):
        cc(0x20011000, 3, num, val)
    tl = bytes(e.uc.mem_read(PR.TAIL, 6))
    check(tl == bytes([1, 64, 5, 7, 100, 5]), f"monitor bytes [CC, value, MSB, LSB, data, count] = {list(tl)} (last CC 1 = 64, MSB 5, LSB 7, data 100, five messages)")
    print("SC21D RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text()), json.loads(Path(a[4]).read_text())) else 0)
