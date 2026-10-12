"""SC32D tests: the external Y memory probe (tools/probe32_dsp.py, on the dsp56kEmu interpreter) and its display (tools/probe32.py, on the RAM dump).

    python tools/emu_sc32d.py SC32D.bin SC32D_manifest.json
DSP (the interpreter has 512 K words: the same code is assembled with six areas mapped into Y:$40000..$45FFF, stride $80, alias offsets $1FFF / $10000;
the image's own probe is checked word for word against code() with the real areas):
  * first call: arrays cleared, magic; one area per call, the sweep counter after six calls;
  * states after three sweeps: zero -> free (5), non-zero -> static (4), the pattern at the alias address -> alias (2), a word changed between sweeps -> changing (3);
  * the packed words = the codes; every written word restored; x0 / x1 / y0 / y1 / r0 / r1 / r2 / n0 and the interrupt mask as found;
  * nothing else of X / Y written; P:$23C = jsr pprobe; the program ends below $3800.
ARM: the DSP service chain head = c_dtick32 (then c_dtick19); closed view = no read, LEDs untouched; open view = mark pad of each page (white, first 0.5 s, no read),
pages 0-2 = state colours of the packed words (pad 9 = the lowest area), page 3 = the sweep count in white; the magic missing = all red.
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
import probe32 as PR  # noqa: E402
import probe32_dsp as PD  # noqa: E402
import build_sc14 as s14  # noqa: E402
import drums18  # noqa: E402

VIEWS = PR.VIEWS
TB, TSTR, TOFF = 0x40000, 0x80, (0x1FFF, 0x10000)
TAREAS = tuple(TB + i * 0x1000 for i in range(6))
CODE_AT, RET_AT, DRV_AT = 0x3900, 0x3F00, 0x3E00


def T_(*l): return G.T(*l)


class E32(T.E191):
    def __init__(self, image, man):
        super().__init__(image, man)
        self.pl = {k: int(v, 16) for k, v in man["report"]["probe32"]["labels"].items()}
        self.read_map, self.reads = {}, []
        def h(uc, a, s, d):
            ad = uc.reg_read(UC_ARM_REG_R1)
            self.reads.append((uc.reg_read(UC_ARM_REG_R0), ad))
            uc.reg_write(UC_ARM_REG_R0, (self.read_map.get(ad, 0) << 8) & 0xFFFFFFFF)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        self.uc.hook_add(UC_HOOK_CODE, h, begin=PR.DSP_READ, end=PR.DSP_READ)
    def tick32(self, uptime=0):
        self.uc.mem_write(PR.HAL_TICK, struct.pack("<I", uptime))
        self.reads.clear(); self.chain.clear(); self.dw.clear()
        self.call(self.pl["c_dtick32"], maxins=3_000_000)
        return list(self.reads)
    def buf(self, v): return self.r32(self.r32(v + 4))
    def row(self, v, first, n): return list(struct.unpack(f"<{n}H", bytes(self.uc.mem_read(self.buf(v) + 2 * first, 2 * n))))
    def allpads(self, v): return self.row(v, 0, 32)


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]
    dl = {k: int(v, 16) for k, v in rep["sc16"]["dsp_labels"].items()}
    sp = dsp_program(img)
    P0 = [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]
    check(len(P0) <= 0x3800, f"program ends at P:${len(P0):x} (limit $3800)")
    check(P0[0x23C:0x23E] == [0x0BF080, dl["pprobe"]], "P:$23C = jsr pprobe")
    real, rl = PD.code(dl["pprobe"], PD.PREMIX)
    check(P0[dl["pprobe"]:dl["pprobe"] + len(real)] == real and rl["pp_tab"] == dl["pp_tab"], "the image's probe = code() with the real areas")
    tab = P0[dl["pp_tab"]:dl["pp_tab"] + 3 * PD.NA]
    check(tab[0::3] == list(PD.AREAS) and tab[3 * 30:3 * 30 + 3] == [0x5BF000, 0x1BF000, 0] and tab[-3:] == [0x8FF000, 0x4FF000, 0] and max(PD.AREAS) < 0x900000,
          f"table: the 38 bases, aliases only inside external memory ({[hex(x) for x in tab[90:93]]}, {[hex(x) for x in tab[-3:]]})")
    check(PD.AREAS[29] + PD.ZONE == 0x5BF000 and len(PD.AREAS) == 38, "zone 29 ends at Y:$5BF000; 38 areas")

    # ---------------------------------------------------------------- the probe logic, areas in the interpreter's memory
    tw, tl = PD.code(CODE_AT, RET_AT, TAREAS, TSTR, TB, TOFF)
    check(CODE_AT + len(tw) <= DRV_AT, f"test code fits ({len(tw)} words)")
    P = P0 + [0] * (0x4000 - len(P0))
    P[CODE_AT:CODE_AT + len(tw)] = tw
    P[RET_AT] = 0x00000C                                                         # rts (= premix)
    def pass_(n): return [0x0BF080, CODE_AT] * n
    bump = T_("move y:>$%x,a" % (TAREAS[3] + TSTR), "move #>$10101,x0", "add x0,a", "move a1,y:>$%x" % (TAREAS[3] + TSTR))
    drv = pass_(6) + bump + pass_(6) + bump + pass_(6) + [0x00000C]
    P[DRV_AT:DRV_AT + len(drv)] = drv
    stat = [0x123456, 0x000777]
    mem = [('y', TAREAS[1] + 5 * TSTR, [stat[0]]), ('y', TAREAS[5] + 31 * TSTR, [stat[1]]), ('y', TAREAS[2] - TOFF[0], [PD.PAT + 2]),
           ('y', TAREAS[3] + TSTR, [0x100]), ('y', TAREAS[1], [0x0ABCDE])]
    pre = T_("move #>$a5a5a5,x0", "move #>$5a5a5a,x1", "move #>$111111,y0", "move #>$222222,y1", "move #>$33,r0", "move #>$44,r1", "move #>$55,r2", "move #>$66,n0", "move sr,x:>$3a00")
    post_at = 0x3D00
    post = [0x0BF080, DRV_AT] + T_("move sr,x:>$3a01", "move x0,x:>$3a02", "move x1,x:>$3a03", "move y0,x:>$3a04", "move y1,x:>$3a05",
                                   "move r0,x:>$3a06", "move r1,x:>$3a07", "move r2,x:>$3a08", "move n0,x:>$3a09") + [0x00000C]
    P[post_at:post_at + len(post)] = post
    dumps = [('y', PD.YR, 7), ('y', PD.STC, 6), ('x', PD.FL, 6), ('x', 0x3A00, 10), ('x', PD.FLAG, 2)] + [('y', ad, 1) for ad in TAREAS] + [('y', TAREAS[1], 0x1000)]
    res, ran = run(P, post_at, mem=mem, dumps=dumps, regs_code=pre, maxins=5_000_000)
    check(ran is not None and 'pc=' in ran, f"ran {ran}")
    ys, codes, fl = res[('y', PD.YR)], res[('y', PD.STC)], res[('x', PD.FL)]
    check(ys[0] == PD.MAGIC and res[('x', PD.FLAG)] == [1, 0], f"magic, flag set, index back to 0 after 18 calls ({res[('x', PD.FLAG)]})")
    check(ys[6] == 3, f"three sweeps counted ({ys[6]})")
    want = [PD.S_FREE, PD.S_STATIC, PD.S_ALIAS, PD.S_CHG, PD.S_FREE, PD.S_STATIC]
    check(codes == want, f"states {codes} (want {want}); flags {[hex(f) for f in fl]}")
    check(all(f & (PD.B_VIS | PD.B_RW) == PD.B_VIS | PD.B_RW for f in fl), "every area visited, write test OK")
    pk = sum(c << 3 * j for j, c in enumerate(want))
    check(ys[1] == pk and ys[2:6] == [0, 0, 0, 0], f"packed word {ys[1]:#x} = {pk:#x}")
    check([res[('y', ad)][0] for ad in TAREAS] == [0, 0x0ABCDE, 0, 0, 0, 0], "the tested words restored")
    blk = res[('y', TAREAS[1])]
    check(blk[5 * TSTR] == stat[0] and sum(1 for v in blk if v) == 2, "nothing else written in area 1")
    r = res[('x', 0x3A00)]
    check(r[2:] == [0x010101, 0x5A5A5A, 0x111111, 0x222222, 0x33, 0x44, 0x55, 0x66] and (r[0] ^ r[1]) & 0xFFFF00 == 0,
          f"registers and the interrupt mask restored (x0 = the driver's last bump value) ({[hex(x) for x in r]})")
    # nothing else of X / Y written by the probe
    resz, _ = run(P, CODE_AT, mem=[], dumps=[('x', 0x3B00, 0x100), ('y', 0x3B00, 0x100), ('x', 0x3A00, 0x100), ('y', 0x3A00, 0x100)])
    xs, ys2 = resz[('x', 0x3B00)], resz[('y', 0x3B00)]
    okx = all(v == 0 for i, v in enumerate(xs) if not (PD.FL - 0x3B00 <= i < PD.FL - 0x3B00 + 6 or PD.CS - 0x3B00 <= i < PD.CS - 0x3B00 + 6 or PD.SAV - 0x3B00 <= i <= PD.K - 0x3B00))
    oky = all(v == 0 for i, v in enumerate(ys2) if not (PD.YR - 0x3B00 <= i < PD.YR - 0x3B00 + 7 or PD.STC - 0x3B00 <= i < PD.STC - 0x3B00 + 6))
    check(okx and oky and resz[('x', 0x3A00)] == [0] * 0x100 and resz[('y', 0x3A00)] == [0] * 0x100, "only the probe's own words of X / Y:$3A00..$3BFF written")

    # ---------------------------------------------------------------- ARM
    L = {k: int(v, 16) for k, v in rep["probe32"]["labels"].items()}
    check(drums18.decode_bw(bytearray(img), s14.SVC_HOOK) == L["c_dtick32"], "DSP service chain head -> c_dtick32")
    gc.collect(); e = E32(img, man)
    snap = [e.allpads(v) for v in VIEWS]
    r = e.tick32(uptime=1 << 9)
    check(r == [] and [e.allpads(v) for v in VIEWS] == snap and len(e.chain) == 1, "source view closed: no DSP read, LED buffers untouched, the chain goes on")
    e.btn(0)
    check(e.flag(), "source view open")
    col = lambda c: PR.STATE_COL[c]
    codes0 = [5, 4, 3, 2, 1, 0, 5, 5]; codes1 = [4, 4, 4, 0, 0, 0, 5, 3]
    word = lambda cs: sum(c << 3 * j for j, c in enumerate(cs))
    e.read_map = {0x8000 | PD.YR: PD.MAGIC, 0x8000 | PD.PK: word(codes0), 0x8000 | (PD.PK + 1): word(codes1), 0x8000 | (PD.PK + 2): word(codes1),
                  0x8000 | (PD.PK + 3): word(codes0), 0x8000 | (PD.PK + 4): word([2, 3, 4, 5, 1, 0]), 0x8000 | PD.SWEEP: 0x0123A5}
    for page in range(4):
        r = e.tick32(uptime=page << 12)
        mark = [PR.WHITE if i == page else 0 for i in range(16)]
        check(r == [] and e.row(VIEWS[0], 8, 16) == mark and e.row(VIEWS[1], 8, 16) == mark and len(e.chain) == 1, f"page {page}: first 0.5 s = the mark, pad {9 + page} white, no read")
    r = e.tick32(uptime=(0 << 12) | (1 << 9))
    check([x for _, x in r] == [0x8000 | PD.YR, 0x8000 | PD.PK, 0x8000 | (PD.PK + 1)] and all(c == 0 for c, _ in r), f"page 0: reads magic, PK0, PK1 ({[hex(x) for _, x in r]})")
    check(e.row(VIEWS[0], 8, 16) == [col(c) for c in codes0 + codes1] and e.row(VIEWS[1], 8, 16) == e.row(VIEWS[0], 8, 16), f"page 0: state colours {[hex(x) for x in e.row(VIEWS[0], 8, 16)]}")
    e.tick32(uptime=(1 << 12) | (7 << 9))
    check(e.row(VIEWS[0], 8, 16) == [col(c) for c in codes1 + codes0], "page 1: PK2 / PK3")
    r = e.tick32(uptime=(2 << 12) | (3 << 9))
    check(len(r) == 2 and e.row(VIEWS[0], 8, 16) == [col(c) for c in [2, 3, 4, 5, 1, 0, 0, 0]] + [0] * 8, "page 2: PK4, row 3 dark (two reads)")
    r = e.tick32(uptime=(3 << 12) | (2 << 9))
    bits = [PR.WHITE if (0x23A5 >> (15 - i)) & 1 else 0 for i in range(16)]
    check([x for _, x in r] == [0x8000 | PD.YR, 0x8000 | PD.SWEEP] and e.row(VIEWS[0], 8, 16) == bits, "page 3: the sweep count, 16 bits in white (pad 9 = bit 15)")
    e.read_map[0x8000 | PD.YR] = 0x123456
    for page in range(4):
        e.tick32(uptime=(page << 12) | (1 << 9))
        if e.row(VIEWS[0], 8, 16) != [PR.RED] * 16: check(False, f"magic missing: page {page} not all red"); break
    else: check(True, "magic missing: every page all red (after its mark)")
    e.pleds(VIEWS[0])                                                              # the first paint of the source view darkens all 32 pads (srcview.METER)
    e.tick32(uptime=(1 << 12) | (1 << 9))
    lp = e.pleds(VIEWS[0])
    check(lp[8:24] == [PR.RED] * 16 and lp[:8] == [0] * 8, f"later the LED slot keeps rows 2 / 3 and repaints row 1 {[hex(x) for x in lp]}")
    e.uc.mem_write(VIEWS[1], struct.pack("<I", 0x1234))
    e.read_map[0x8000 | PD.YR] = PD.MAGIC; e.tick32(uptime=1 << 9)
    check(e.row(VIEWS[0], 8, 1) == [col(codes0[0])], "a view whose vtable is not the synth Preset view is left alone (the other one painted)")
    print("SC32D RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
