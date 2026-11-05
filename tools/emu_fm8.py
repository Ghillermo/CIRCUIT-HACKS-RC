"""SC51.7 ARM tests (fmeng.use_fm8, fm8 / fm8arm / fm8ui, poly.use_v11): the 8-operator FM through the controller, the real LED task, fmeng's
trampolines and the whole DSP service chain (the DSP's reads stubbed: OSC1 + 14 the shape, OSC1 + 11 the increment).
  * FM on (row pad 24): the off -> on edge writes 0 to the 8 operators' smoothed AMP / y[n - 2]; N = 4 (the stack), R of ratio 1 = 2^16, the flag;
  * pad 7 = the FM page: pads 9-12 lit (op 1 a carrier green, 2-4 modulators light blue, op 1 picked bright), 13-16 dark, pad 17 amber dim;
    pad 10 picks op 2; K3 five clicks = op 2's output level + 5; K1 three clicks = coarse + 1 (R x 2); K5 (R1) its LED amber;
  * Shift + K1, 64 clicks: algorithm 16 (the DX7's 1): N = 6, the routing (6->5->4->3, 2->1; carriers 1 and 3), pads 1-32 the DX7's 32 with
    the first bright; pads 13-14 now lit (ops 5, 6);
  * pad 17 = the pitch envelope: K1 = transpose; Shift + K5 = PEG L1;
  * a note: the carriers' AMP > 0 after a few ticks, the stages; let go: the release;
  * Clear + knob = the default; Clear + pad 7 on a DX7 algorithm = six operators;
  * pad 8 held: the starters, a press = the starter converted (fm8.convert4), the tonic;
  * the patch: an old version 2 FM patch (c_fmappl) = fm8.convert4 of its 16 parameters, FM on.

    python tools/emu_fm8.py SC51.7.bin SC51.7_manifest.json
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R5, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import packio as PK  # noqa: E402
import fmeng as FE  # noqa: E402
import fm8 as F  # noqa: E402
import fm8arm as A  # noqa: E402
import vcf21_dsp as VD  # noqa: E402

V = T4.V
MGR = X.MGR
CLEAR = 23


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    VD.FMC1 = True; VD.FV0 = 0x4000; VD.use_fm8()
    FB, OSB = VD.FMB0, VD.OSB0
    R = man["report"]
    fl = {k: int(v, 16) for k, v in R["fmeng"]["labels"].items()}
    ml = {k: int(v, 16) for k, v in R["modesel"]["labels"].items()}
    pl = {k: int(v, 16) for k, v in R["mpatch"]["labels"].items()}
    e = X.EP(img, man)
    dw, rd = [], {}
    cur = {}
    def w(uc, a, s, d): dw.append((uc.reg_read(UC_ARM_REG_R1) >> 8, uc.reg_read(UC_ARM_REG_R2))); cur[dw[-1][1]] = dw[-1][0]
    e.uc.hook_add(UC_HOOK_CODE, w, begin=A.DSP_WRITE, end=A.DSP_WRITE)
    def dread(uc, a, s, d):
        uc.reg_write(UC_ARM_REG_R0, (rd.get(uc.reg_read(UC_ARM_REG_R1), 0) & 0xFFFFFF) << 8); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, dread, begin=A.DSP_READ, end=A.DSP_READ)
    rd[OSB + 11] = A.INCS[60]
    def tick(n=1):
        for _ in range(n): e.at(e.t + 1); e.call(fl["c_fmtick"], maxins=8_000_000)
    blk, vs = A.FM8R + A.TB0, A.FM8R + A.VT0
    par = lambda i: e.r8(blk + i)
    last = lambda addr: cur.get(addr)
    press = lambda q: e.call(PRESS, MGR, q, 100, maxins=8_000_000)
    release = lambda q: e.call(RELEASE, MGR, q, maxins=8_000_000)
    clear = lambda on: e.call(0x08033320 if on else 0x0803381A, MGR, CLEAR, maxins=8_000_000)
    non = e.r32(0x0805B840 if False else FE.MX.NOTE_VT) & ~1
    def note(n, v): e.call(non, 0x20011334, 2, n, v, maxins=4_000_000)
    gate = V.TAIL + V.O_RT + V.RT_CNT

    # ---- FM on: the edge, N, R, the flag
    e.btn(2); e.btn(8); e.pad(26); e.pad(FE.ROWPAD)
    check(par(A.B_ON) == 1 and e.r0(ml["c_msmode"], 0) == 2, "row pad 24: FM on")
    dw.clear(); tick(1)
    zs = all((0, FB + 16 * k + VD.F8_AS) in dw and (0, FB + 16 * k + VD.F8_O2) in dw for k in range(8))
    check(zs, "the edge: the 8 operators' smoothed AMP and y[n - 2] at 0")
    check(last(FB + VD.F8_N) == 4 and last(FB + VD.F_R) == 1 << 16 and last(OSB + VD.FM_FLAG) == 1 and bytes(e.uc.mem_read(blk, F.PLEN)) == F.DEFAULT,
          f"N 4, R of ratio 1 = {last(FB + VD.F_R)}, the flag; the defaults (the converted stack)")

    # ---- the FM page: the operator pads (the engine row closed: with it open its pads 9-16 are jumpflip's, dark)
    peg3 = "le_p3" in R["fm8"]["labels"]                                                 # SC51.9 (fm8ui.use_peg3): the pitch envelope on pad 3, violet
    PEGPAD = 2 if peg3 else 16
    e.pad(26); e.pad(FE.PADNO); f = X.frame(e)
    rowop = bool(R["fm8"]["labels"].get("t_rowc"))                                          # SC52: pad 17 = the engine row's «no voice», dim
    exp = [0x17, 0x14, 0x14, 0x14, 0, 0, 0, 0, (0x02 if rowop else 0) if peg3 else 0x2C]
    check(f[8:17] == exp and (not peg3 or f[2] & 0xFF == FE.COL_FM[1]),
          f"pads 9-17: op 1 carrier bright, 2-4 modulators dim, 5-8 dark, the pitch envelope dim ({[hex(x) for x in f[8:17]]}, pad 3 {f[2]:#x})")
    e.pad(9); f = X.frame(e)
    check(par(A.B_SEL) == 1 and f[9] == 0x13 and f[8] == 0x18, f"pad 10: op 2 picked ({par(A.B_SEL)}, {hex(f[9])}, {hex(f[8])})")
    ol0 = par(F.OPB + F.O_OL)
    for _ in range(5): e.knob(2, -1)
    check(par(F.OPB + F.O_OL) == ol0 - 5, f"K3 five clicks down: op 2's output level {ol0} -> {par(F.OPB + F.O_OL)}")
    e.uc.mem_write(FE.MX.MXR + 0x21EC, bytes([219]))                                  # the steps' accumulator: whatever the RAM held
    for _ in range(3): e.knob(0, 1)
    dw.clear(); tick(1)
    check(par(F.OPB + F.O_CRS) == 2 and last(FB + 16 + VD.F_R) == 2 << 16, f"K1 three clicks: op 2 coarse 2, R {last(FB + 16 + VD.F_R)}")
    f = X.frame(e)
    check(f[60 + 4] & 0xFF == 0x2B, f"K5 (R1) LED amber ({f[64]:#x})")

    # ---- Shift + K1: the algorithm, the DX7's
    e.shift(True)
    for _ in range(256): e.knob(0, 1)
    f = X.frame(e); e.shift(False)
    check(par(F.GLB + F.G_ALG) == 16, f"Shift + K1, 256 clicks: algorithm 16 ({par(F.GLB + F.G_ALG)})")
    bad = [(i, hex(x)) for i, x in enumerate(f[:32]) if x != (1 if i == 0 else 2) and i not in (28, 31)]
    check(not bad, f"pads 1-32 (not 29 / 32: poly's and the voice mode's with Shift): the DX7's 32, the first bright ({bad})")
    dw.clear(); tick(2)
    al = F.alg_of(F.algs(), 16)
    ok = last(FB + VD.F8_N) == 6
    for k in range(6):
        ok &= last(FB + 16 * k + VD.F_K) == (F.KW_CAR // 2 if al["car"] >> k & 1 else 0)
        for j in range(6):
            if (k, j) == (5, 5): continue
            ok &= last(FB + 16 * k + VD.F8_M + j) == (F.M_FULL if al["mask"] >> (8 * k + j) & 1 else 0)
    check(ok, "N 6, K on carriers 1 / 3, M from DX7 algorithm 1")
    e.at(e.t + 2000); f = X.frame(e)
    check(f[12] in (0x13, 0x14) and f[13] in (0x13, 0x14) and f[14] == 0, f"after the overlay: pads 13-14 lit (ops 5, 6), 15 dark ({[hex(x) for x in f[8:17]]})")

    # ---- the pitch envelope
    e.pad(PEGPAD); f = X.frame(e)
    check(par(A.B_SEL) == 8 and (not peg3 or f[2] & 0xFF == FE.COL_FM[0]), f"pad {PEGPAD + 1}: the pitch envelope")
    for _ in range(4): e.knob(0, 1)
    e.shift(True); e.knob(4, 5); e.shift(False)
    check(par(F.GLB + F.G_TRN) == 26 and par(F.PEG + 4) == 55, f"K1 4 clicks = transpose 26 ({par(F.GLB + F.G_TRN)}); Shift + K5 = PEG L1 55 ({par(F.PEG + 4)})")
    clear(True); e.knob(0, 1); e.shift(True); e.knob(4, 1); e.shift(False); clear(False)
    check(par(F.GLB + F.G_TRN) == 24 and par(F.PEG + 4) == 50, "Clear + knob: the defaults")

    # ---- a note
    e.pad(8)
    rd[OSB + 11] = A.INCS[60]
    note(60, 100); e.uc.mem_write(gate, bytes([1]))
    tick(30)
    amps = [last(FB + 16 * k + VD.F_AMP) or 0 for k in range(6)]
    st = list(e.uc.mem_read(vs + A.V_ST, 9))
    check(amps[0] > 0 and amps[2] > 0 and amps[1] > 0, f"a note: carriers 1 / 3 and modulator 2 sounding ({amps})")
    e.uc.mem_write(gate, bytes([0])); tick(5)
    st2 = list(e.uc.mem_read(vs + A.V_ST, 9))
    check(all(s in (3, 5) for s in st2[:6]), f"let go: the release stages ({st} -> {st2})")

    # ---- Clear + pad 7 on a DX7 algorithm: six operators
    clear(True); e.pad(FE.PADNO); clear(False)
    import fm8ui as U
    v2 = "c_fminst" in R["fm8"]["labels"]                                              # SC51.8 (fm8ui.use_v2): eight operators voiced, the instruments
    if v2 and not F.ALG8: F.use_alg8()
    got = bytes(e.uc.mem_read(blk, F.PLEN))
    check(got[:F.GLB] == U.DXDEF[:F.GLB] and got[F.GLB] == 16, "Clear + pad 7: the DX7 voicing, the algorithm kept")

    # ---- the starters
    n0 = len(e.ons)
    press(FE.PADNO + 1); press(8 + 3); release(8 + 3); release(FE.PADNO + 1)
    if v2:
        import fm8inst as FI
        check(bytes(e.uc.mem_read(blk, F.PLEN)) == FI.inst_full(3) and par(A.B_STR) == 3 and len(e.ons) >= n0 + 1,
              f"pad 8 + pad 12: the instrument {FI.INST[3]['name']} unpacked, the tonic ({e.ons[n0:]})")
    else:
        check(bytes(e.uc.mem_read(blk, F.PLEN)) == F.convert4(bytes(FE.STARTERS[3][1])) and par(A.B_STR) == 3 and len(e.ons) >= n0 + 1,
              f"pad 8 + pad 12: the pluck starter converted, the tonic ({e.ons[n0:]})")

    # ---- an old patch (version 2)
    p2 = bytearray(b"FM\x02\x01") + bytes(FE.VOICINGS[12])
    p2.append((0x5A + sum(p2)) & 0xFF)
    keep = bytes(p2)
    def mpr(uc, a, s, d):
        uc.mem_write(uc.reg_read(UC_ARM_REG_R2), keep); uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_R1, FE.PLEN)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    hk = e.uc.hook_add(UC_HOOK_CODE, mpr, begin=pl["c_mpr"], end=pl["c_mpr"])
    e.uc.reg_write(UC_ARM_REG_R5, 3); e.call(fl["c_fmappl"], 0, maxins=12_000_000)
    check(bytes(e.uc.mem_read(blk, F.PLEN)) == F.convert4(bytes(FE.VOICINGS[12])) and par(A.B_ON) == 1, "an old version 2 patch (the bell): converted, FM on")
    e.uc.hook_del(hk)
    print(f"{man['marker']} FM8 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
