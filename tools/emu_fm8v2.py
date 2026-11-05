"""SC51.8 ARM tests (fm8ui.use_v2 / use_heads / use_nodual, fm8.use_alg8, modesel.use_row2): through the controller and the real LED task.
  * the engine row (pad 27): no voice, VCA / VCF / FX only, oscillator, VA-drum, the wavetable's place (dark, a press does nothing), sample,
    granular, FM; the FX sequencer is not there: pad 31 with no voice = dim blue, a tap = the FX sequencer (bright; the row shows no voice), again = off;
  * with the row open: pad 8 held = the 24 instruments on pads 9-32 in their family's colour (the step-flip row no longer darkens 9-16); pad 10 =
    fm8inst.inst_full(1);
  * pad 7 held = the algorithms' pages: page 1 teal (the 16) + amber (49-56), Octave down lit; Octave down = page 2 (the DX7's 1-24, white, the
    current bright); pad 9 there = algorithm 16; Octave up, pad 25 = algorithm 48;
  * the operator page (the row closed): pads 18-24 dark and a press loads no patch; pad 28 and pad 3 dark with FM, pad 28 keeps the two
    oscillators' bit; pad 32 lit with FM, dark with VCA / VCF / FX only;
  * c_f8mpr / c_f8scol: the engines of a bank's records (FM, VA-drum, sample, not a patch) and their colours (bright = the last one); psave's empty
    colour is dim white.

    python tools/emu_fm8v2.py SC51.8.bin SC51.8_manifest.json
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R4, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import packio as PK  # noqa: E402
import fmeng as FE  # noqa: E402
import fm8 as F  # noqa: E402
import fm8arm as A  # noqa: E402
import fm8inst as FI  # noqa: E402
import modesel as MS  # noqa: E402
import mpatch as MP  # noqa: E402

V = T4.V
MGR = X.MGR


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    if not F.ALG8: F.use_alg8()
    R = man["report"]
    ml = {k: int(v, 16) for k, v in R["modesel"]["labels"].items()}
    fl = {k: int(v, 16) for k, v in R["fm8"]["labels"].items()}
    pl = {k: int(v, 16) for k, v in R["mpatch"]["labels"].items()}
    e = X.EP(img, man)
    def dread(uc, a, s, d): uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, dread, begin=A.DSP_READ, end=A.DSP_READ)
    loads = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: loads.append(1), begin=pl["c_mpr"], end=pl["c_mpr"])
    blk = A.FM8R + A.TB0
    par = lambda i: e.r8(blk + i)
    press = lambda q: e.call(PRESS, MGR, q, 100, maxins=8_000_000)
    release = lambda q: e.call(RELEASE, MGR, q, maxins=8_000_000)
    mode = lambda: e.r0(ml["c_msmode"], 0)
    lo = lambda f, a, b: [x & 0xFF for x in f[a:b]]
    COLS = MS.COLS

    # ---- the row
    e.btn(2); e.btn(8); e.pad(26); f = X.frame(e)
    wt = "wtui" in R                                                                     # SC52.1: the wavetable's pad is sand and plays
    want = [COLS[0][0], COLS[1][1], COLS[2][1], COLS[3][1], 0x69 if wt else 0, COLS[5][1], COLS[4][1], FE.COL_FM[1]]
    check(lo(f, 16, 24) == want, f"the row: no voice (bright), line, osc, VA-drum, wavetable {'sand' if wt else 'dark'}, sample, granular, FM ({[hex(x) for x in lo(f, 16, 24)]})")
    if not wt: e.pad(20); check(mode() == 0, "the wavetable's pad: nothing")
    e.pad(FE.ROWPAD); f = X.frame(e)
    check(par(A.B_ON) == 1 and f[23] & 0xFF == FE.COL_FM[0], f"pad 24: FM on, bright ({f[23]:#x})")

    # ---- pad 8 held with the row open: the 24 instruments
    press(FE.PADNO + 1); f = X.frame(e)
    ic = FI.colours()
    st = par(A.B_STR)
    exp = [ic[2 * j + (j != st)] for j in range(24)]
    check(lo(f, 8, 32) == exp, f"pad 8 held (the row open): the 24 instruments in their family's dim colour ({[hex(x) for x in lo(f, 8, 32)]})")
    press(9); release(9); f = X.frame(e)
    check(bytes(e.uc.mem_read(blk, F.PLEN)) == FI.inst_full(1) and f[9] & 0xFF == ic[2], f"pad 10: {FI.INST[1]['name']} unpacked, its pad bright ({f[9]:#x})")
    release(FE.PADNO + 1)

    # ---- pad 7 held: the pages
    press(FE.PADNO); f = X.frame(e)
    p0 = [0x4E] * 16 + [0x2C] * 8
    check(lo(f, 8, 32) == p0 and f[51] & 0xFF == 1 and f[52] & 0xFF == 0, f"pad 7 held, page 1: teal 16 + amber 8; Octave down lit, up dark ({[hex(x) for x in lo(f, 8, 32)]}, {f[51]:#x}, {f[52]:#x})")
    e.btn(19); f = X.frame(e)
    alg = par(F.GLB + F.G_ALG)
    exp = [0x01 if 16 + j == alg else 0x02 for j in range(24)]
    check(lo(f, 8, 32) == exp and f[52] & 0xFF == 1, f"Octave down: page 2, the DX7's 1-24, the current ({alg}) bright")
    press(8); release(8)
    check(par(F.GLB + F.G_ALG) == 16, f"pad 9 on page 2: algorithm 16 ({par(F.GLB + F.G_ALG)})")
    e.btn(19); f = X.frame(e)
    check(lo(f, 8, 16) == [0x02] * 8 and lo(f, 16, 32) == [0] * 16 and f[51] & 0xFF == 0, "page 3: the DX7's 25-32 on pads 9-16, the rest dark, Octave down dark")
    e.btn(20); e.btn(20); press(24); release(24)
    check(par(F.GLB + F.G_ALG) == 48, f"Octave up twice, pad 25: algorithm 48 (the first eight-operator one) ({par(F.GLB + F.G_ALG)})")
    release(FE.PADNO)
    e.at(e.t + 2000)

    # ---- the operator page
    e.pad(26); e.pad(FE.PADNO); f = X.frame(e)
    peg3 = "le_p3" in fl
    a0 = 16 if peg3 else 17
    rowop = "c_fminst" in fl and any(k == "le_r3" for k in fl) and bool(R["fm8"]["labels"].get("t_rowc"))
    if rowop:                                                                            # SC52 (use_rowop): the engine row on 17-24, pad 7 dim
        import fm8ui as U
        exp = [MS.COLS[m][1] if m != 0xFF else 0 for m in MS.ROWMODE] + [FE.COL_FM[0]]
        check(lo(f, 16, 24) == exp and f[6] & 0xFF == FE.COL_FM[1], f"the operator page: the engine row on pads 17-24, FM bright; pad 7 dim ({[hex(x) for x in lo(f, 16, 24)]}, {f[6]:#x})")
    else:
        check(lo(f, a0, 24) == [0] * (24 - a0), f"the operator page: pads {a0 + 1}-24 dark ({[hex(x) for x in lo(f, a0, 24)]})")
    check(all(lo(f, 8, 16)), f"algorithm 48: the 8 operators lit ({[hex(x) for x in lo(f, 8, 16)]})")
    if not rowop:
        n0 = len(loads); e.pad(19)
        check(len(loads) == n0, "pad 20 on the operator page: no patch read")
    rt = V.TAIL + V.O_RT + V.RT_VEL
    v0 = e.r8(rt); e.pad(27); f = X.frame(e)
    p3 = FE.COL_FM[1] if peg3 else 0
    check(e.r8(rt) == v0 and f[27] & 0xFF == 0 and f[2] & 0xFF == p3, f"pad 28 with FM: dark, the bit kept; pad 3 {'dim violet' if peg3 else 'dark'} ({f[27]:#x}, {f[2]:#x})")
    if peg3:
        if not rowop: e.pad(16)
        n1 = par(A.B_SEL)
        e.pad(2); f = X.frame(e)
        check(par(A.B_SEL) == 8 and n1 != 8 and f[2] & 0xFF == FE.COL_FM[0], f"pad 3: the pitch envelope, bright violet ({n1}, {par(A.B_SEL)}, {f[2]:#x})")
        e.pad(8)
    check(f[31] & 0xFF != 0, f"pad 32 with FM: lit ({f[31]:#x})")

    # ---- VCA / VCF / FX only, no voice, the FX sequencer
    if rowop:                                                                            # a row pad on the operator page = that engine
        n0 = len(loads); e.pad(19); f = X.frame(e)
        check(mode() == 3 and par(A.B_ON) == 0 and len(loads) == n0 and e.r8(MS.RAM) == 0, f"pad 20 on the operator page: the VA-drum, FM off, the row closed ({mode()}, {par(A.B_ON)})")
        e.pad(26); e.pad(FE.ROWPAD); e.pad(26)
    e.pad(26); e.pad(17); f = X.frame(e)
    check(mode() == 1 and f[31] & 0xFF == 0, f"VCA / VCF / FX only: pad 32 dark ({mode()}, {f[31]:#x})")
    e.pad(16); f = X.frame(e)
    check(mode() == 0 and f[30] & 0xFF == MS.COL_FXS[1], f"no voice: pad 31 dim blue ({mode()}, {f[30]:#x})")
    e.pad(30); f = X.frame(e)
    check(mode() == 6 and f[30] & 0xFF == MS.COL_FXS[0] and f[16] & 0xFF == COLS[0][0], f"pad 31: the FX sequencer, bright; the row shows no voice ({mode()}, {f[30]:#x}, {f[16]:#x})")
    e.pad(30); check(mode() == 0, f"pad 31 again: no voice ({mode()})")

    # ---- the slots' engines
    import fm8ui as U
    BUF = PK.BUF
    recs = bytearray(b"\xff" * 4096)
    def rec(r, flags, fm=False):
        o = 512 * r + MP.OFF
        recs[o:o + 4] = b"CTM1"; recs[o + 4] = flags
        if fm: recs[o + 100:o + 104] = b"FM\x03\x01"
    rec(0, 3, True); rec(1, 7); rec(2, 9); rec(4, 3)
    def mpr(uc, a, s, d):
        uc.mem_write(BUF, bytes(recs)); uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_R1, 4096); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    hk = e.uc.hook_add(UC_HOOK_CODE, mpr, begin=pl["c_mpr"], end=pl["c_mpr"])
    e.call(fl["c_f8mpr"], 3, 0, BUF, 4096, maxins=1_000_000)
    e.uc.hook_del(hk)
    got = list(e.uc.mem_read(U.ENGC + 8, 8))
    check(got == [7, 3, 5, 0xFF, 2, 0xFF, 0xFF, 0xFF], f"c_f8mpr, bank 3: FM, VA-drum, sample, empty, oscillator ({got})")
    def scol(i, last):
        e.uc.reg_write(UC_ARM_REG_R4, last + 1); e.call(fl["c_f8scol"], 0, 0, 0, i, maxins=100_000); return e.uc.reg_read(UC_ARM_REG_R2)
    check((scol(8, 8), scol(8, 3), scol(9, 3), scol(12, 3)) == (FE.COL_FM[0], FE.COL_FM[1], COLS[3][1], COLS[2][1]),
          "c_f8scol: FM bright when last, dim otherwise; VA-drum, oscillator dim")
    px = int(R["psave"]["labels"]["c_psxleds"], 16)
    ats = [px + i for i in range(0, 0x80, 2) if struct.unpack("<H", e.uc.mem_read(px + i, 2))[0] in (0x2249, 0x2202)]
    check(len(ats) == 1 and struct.unpack("<H", e.uc.mem_read(ats[0], 2))[0] == 0x2202, "psave's empty slots: dim white")
    print(f"{man['marker']} FM8 V2 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
