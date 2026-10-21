"""SC45.6 ARM tests (tools/fmeng.py: the FM variant of the own engine's oscillator), through the controller, the real LED task, the whole DSP
service chain (fmeng's tick is its head) and the note vtable's head:
  * MIDI 1's Preset view, the mode row (a tap on pad 27): pad 24 = FM: the oscillator mode (modesel) and FM on; pad 24 violet, the oscillator's pad
    dim; pad 27 violet; the DSP gets the flag (X:OSB0 + 27 = 1) and the routing (K / M of the stack) at the next tick;
  * pad 7 = the FM page (vcf21's page 6), violet bright; K1 / K5 / Shift + K1 / Shift + K5 move the ratio / level / attack / algorithm of their
    operator; their LEDs (the ratio's class colour, the level's orange, the attack's light blue, the family's colour); Clear + knob = the default;
  * a note on (the note vtable) with the gate (vcf21's held notes): the attacks run (AMP of operator 1 rises to env x level^2 >> 8 as the model),
    an attack 0 = full at once; the gate off: the release (c^dt per ms, the velocity's offset); a percussive algorithm (kick) decays while held,
    operator 4 is silent and drops the pitch (R of operator 1 above the ratio's, back to it);
  * the R words = ratio x 2^19 (ratio 1 = 0x80000, 2 = 0x100000); the noise level (F_NZ) = noise^2 x 4 x env >> 9;
  * another mode of the row (or pad 27's cycle) = FM off: the flag 0 to the DSP, the page back to OSC 1;
  * the patch: gathering writes "FM", 1, on, the 16 parameters, the check at padding + 100; applying it restores them and FM on; a patch without it
    = FM off.

    python tools/emu_fmeng.py SC45.6.bin SC45.6_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R5, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
import packio as PK  # noqa: E402
import modesel as MS  # noqa: E402
import modmx as MX  # noqa: E402
import fmeng as F  # noqa: E402
import vcf21_dsp as VD  # noqa: E402

V = T4.V
MGR = X.MGR
CLEAR = 23


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]
    fl = {k: int(v, 16) for k, v in R["fmeng"]["labels"].items()}
    ml = {k: int(v, 16) for k, v in R["modesel"]["labels"].items()}
    e = X.EP(img, man)
    dw = []
    def w(uc, a, s, d): dw.append((uc.reg_read(UC_ARM_REG_R1) >> 8, uc.reg_read(UC_ARM_REG_R2)))
    e.uc.hook_add(UC_HOOK_CODE, w, begin=0x080292F8, end=0x080292F8)
    def tick(n=1, step=1):
        for _ in range(n): e.at(e.t + step); e.call(fl["c_fmtick"], maxins=8_000_000)
    blk = F.FMR + F.B0
    par = lambda i: e.r8(blk + i)
    env = lambda k: struct.unpack_from("<H", bytes(e.uc.mem_read(blk + F.B_ENV + 2 * k, 2)))[0]
    def last(addr):
        v = [x for x, a in dw if a == addr]; return v[-1] if v else None
    mode = lambda: e.r0(ml["c_msmode"], 0)
    FB = VD.FMB0
    e.btn(2); e.btn(8); f0 = X.frame(e)
    e.pad(26)                                                                         # the row
    e.pad(F.ROWPAD); f = X.frame(e)
    check(mode() == 2 and par(F.B_ON) == 1 and e.r0(fl["c_fmact"], 0) == 1, f"row pad 24: the oscillator mode ({mode()}), FM on")
    check(f[F.ROWPAD] == F.COL_FM[0] and f[MS.ROW + 2] == MS.COLS[2][1] and f[26] == F.COL_FM[0], f"pad 24 violet ({f[23]:#x}), the oscillator's pad dim ({f[18]:#x}), pad 27 violet ({f[26]:#x})")
    dw.clear(); tick(2)
    kw = 0x3FFFFF
    check(last(VD.OSB0 + VD.FM_FLAG) == 1 and last(FB + VD.F_K) == kw and last(FB + 12 + VD.F_K) == 0 and last(FB + VD.F_M + 1) == 0x7FFFFF
          and last(FB + 12 + VD.F_M + 2) == 0x7FFFFF and last(FB + VD.F_M + 0) == 0 and last(FB + 36 + VD.F_M + 3) == 0,
          f"the DSP: the flag 1, K1 = {last(FB + VD.F_K)}, the stack's M (2 on 1, 3 on 2), no feedback ({last(FB + 36 + VD.F_M + 3)})")
    check(last(FB + VD.F_R) == 1 << 19 and last(FB + 12 + VD.F_R) == 1 << 19, f"R of the ratio 1 = {last(FB + VD.F_R):#x}")
    e.pad(26); fc = X.frame(e)                                                        # the row closed
    check(e.r8(MS.RAM) == 0 and fc[16:24] == f0[16:24], f"the row closed: pads 17-24 the patch list's again ({[hex(x) for x in fc[16:24]]})")
    e.uc.mem_write(MS.RAM, bytes([2])); fo = X.frame(e); e.uc.mem_write(MS.RAM, bytes([0]))
    check(fo[16:24] == f0[16:24], f"the row open for MIDI 2 only: MIDI 1's pads 17-24 the patch list's ({fo[23]:#x})")
    e.pad(F.PADNO); f = X.frame(e)
    check(e.r0(e.vl["c_vpage"], 0) == F.PAGE and f[F.PADNO] == F.COL_FM[0], f"pad 7: the FM page ({e.r0(e.vl['c_vpage'], 0)}), pad 7 violet ({f[6]:#x})")
    # knobs
    r0_ = par(F.P_RAT + 1)
    for _ in range(11): e.knob(1, 1)                                                 # K2: operator 2's ratio up
    ri = par(F.P_RAT + 1) * 24 >> 7
    dw.clear(); tick(1)
    check(par(F.P_RAT + 1) == r0_ + 11 and last(FB + 12 + VD.F_R) == round(256 * F.RATIOS[ri]) << 11, f"K2: operator 2's ratio {F.RATIOS[ri]} (R {last(FB + 12 + VD.F_R):#x})")
    f = X.frame(e)
    check(f[61] & 0xFF == F.rcol(F.RATIOS[ri]) and f[64] & 0xFF == F.COL_LEV, f"K2's LED the ratio's colour ({f[61]:#x}), K5's the level's ({f[64]:#x})")
    e.shift(True)
    for _ in range(8 * 8): e.knob(4, 1)                                               # Shift + K5: algorithm 8 + ... = kick (index 8)
    f = X.frame(e); e.shift(False)
    check(par(F.P_ALG) >> 3 == 8 and f[64] & 0xFF == F.FAM_COL[1], f"Shift + K5: the algorithm {par(F.P_ALG) >> 3} (kick), its LED the percussive red ({f[64]:#x})")
    e.call(0x08033320, MGR, CLEAR, maxins=8_000_000); e.shift(True); e.knob(4, 1); e.shift(False); e.call(0x0803381A, MGR, CLEAR, maxins=8_000_000)
    check(par(F.P_ALG) == 0, f"Clear + Shift + K5: the algorithm back to the stack ({par(F.P_ALG)})")
    # envelopes: a note, the gate
    gate = V.TAIL + V.O_RT + V.RT_CNT
    e.shift(True)
    for _ in range(40): e.knob(0, 1)                                                  # Shift + K1: operator 1's attack 40 (pos >> 2 = 10)
    e.shift(False)
    non = e.r32(MX.NOTE_VT) & ~1
    e.uc.mem_write(gate, bytes([1]))
    e.call(non, 0x20011334, 2, 60, 100, maxins=4_000_000)
    dw.clear(); tick(1); e1 = env(0); e2 = env(1); tick(4); e1b = env(0)
    st = F.ATK_STEP[10]
    lsq = 127 * 127 * 4
    check(e1 == min(32767, st) and e2 == 32767 and e1b == min(32767, 5 * st), f"the attacks: operator 1 {e1} -> {e1b} (step {st} a ms), operator 2 (attack 0) full at once ({e2})")
    check(last(FB + VD.F_AMP) == e1b * lsq >> 8, f"AMP of operator 1 = env x level^2 >> 8 ({last(FB + VD.F_AMP)} = {e1b * lsq >> 8})")
    tick(400); top = env(0)
    e.uc.mem_write(gate, bytes([0])); tick(1); r1 = env(0); tick(9); r10 = env(0)
    idx = min(63, max(0, (par(F.P_REL) >> 1) + ((100 - 64) >> 3)))
    c = F.REL_C[idx]
    m = top
    for _ in range(10): m = m * c >> 16
    check(top == 32767 and r10 == m and r1 < top, f"held: full ({top}); the gate off: the release (10 ms: {r10} = {m}, idx {idx})")
    # the kick: percussive, operator 4 = the pitch drop
    e.shift(True)
    for _ in range(64): e.knob(4, 1)
    e.shift(False)
    e.uc.mem_write(gate, bytes([1])); e.call(non, 0x20011334, 2, 60, 100, maxins=4_000_000)
    dw.clear(); tick(1); rk = last(FB + VD.F_R); a4 = last(FB + 36 + VD.F_AMP); tick(300); rk2 = last(FB + VD.F_R); ek = env(0)
    check(par(F.P_ALG) >> 3 == 8 and rk > 1 << 19 and a4 == 0 and rk2 < rk and ek < 32767,
          f"kick: operator 1's R dropped from {rk:#x} to {rk2:#x} (ratio 1 = 0x80000), operator 4 silent ({a4}), the held note decays ({ek})")
    # the noise
    e.shift(True)
    for _ in range(100): e.knob(6, 1)
    e.shift(False)
    e.uc.mem_write(gate, bytes([1])); e.call(non, 0x20011334, 2, 60, 100, maxins=4_000_000); dw.clear(); tick(1)
    nz = par(F.P_NZ)
    check(last(FB + VD.F_NZ) == (nz * nz * 4 * env(0)) >> 9 and last(FB + VD.F_NZ) > 0, f"the noise: F_NZ {last(FB + VD.F_NZ)} = noise^2 x 4 x env >> 9")
    # the patch
    pl = {k: int(v, 16) for k, v in R["mpatch"]["labels"].items()}
    p0 = [par(i) for i in range(16)]
    e.call(pl["c_mpgather"], 0, maxins=4_000_000)
    e.call(fl["c_fmgath"], 0, maxins=8_000_000)
    buf = bytes(e.uc.mem_read(PK.BUF + F.POFS, F.PLEN))
    check(buf[:4] == b"FM\x01\x01" and list(buf[4:20]) == p0, f"gather: {buf[:4]} + the 16 parameters at padding + 100")
    keep = bytes(buf)
    def rd(uc, a, s, d):
        uc.mem_write(uc.reg_read(UC_ARM_REG_R2), keep[:F.PLEN]); uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_R1, F.PLEN)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    hk = e.uc.hook_add(UC_HOOK_CODE, rd, begin=pl["c_mpr"], end=pl["c_mpr"])
    e.call(fl["c_fmdefs"], 0, maxins=2_000_000); e.uc.mem_write(blk + F.B_ON, b"\0")
    e.uc.reg_write(UC_ARM_REG_R5, 3); e.call(fl["c_fmappl"], 0, maxins=12_000_000)
    ok1 = [par(i) for i in range(16)] == p0 and par(F.B_ON) == 1
    keep = bytes(F.PLEN)
    e.uc.reg_write(UC_ARM_REG_R5, 3); e.call(fl["c_fmappl"], 0, maxins=12_000_000)
    ok2 = par(F.B_ON) == 0
    e.uc.hook_del(hk)
    check(ok1 and ok2, f"apply: a patch with FM restores it and FM on ({ok1}); one without = FM off ({ok2})")
    # FM off by another mode
    e.uc.mem_write(blk + F.B_ON, b"\1"); tick(1)
    e.pad(F.PADNO); e.pad(26); e.pad(MS.ROW + 3)                                     # the VA-drum
    dw.clear(); tick(2)
    check(par(F.B_ON) == 0 and mode() == 3 and last(VD.OSB0 + VD.FM_FLAG) == 0 and e.r0(e.vl["c_vpage"], 0) == 1,
          f"another mode of the row: FM off, the flag 0 to the DSP ({last(VD.OSB0 + VD.FM_FLAG)}), the page back to OSC 1 ({e.r0(e.vl['c_vpage'], 0)})")
    f = X.frame(e)
    check(f[F.ROWPAD] == F.COL_FM[1] and f[26] != F.COL_FM[0], f"pad 24 dim violet ({f[23]:#x}), pad 27 not violet ({f[26]:#x})")
    print(f"{man['marker']} FM ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
