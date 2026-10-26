"""SC46.6 ARM tests (fmeng.use_v2, modmx.use_zero): the FM engine's ARM side, through the controller, the real LED task, the whole DSP service chain
(fmeng's tick is its head; the DSP's reads stubbed: the oscillator's shape OSC1 + 14 and increment OSC1 + 11) and the note vtable:
  * FM on (row pad 24): the off -> on edge writes 0 to every operator's smoothed AMP (+9) and y[n-2] (+10); the flag after the first AMP; R of
    ratio 1 = 2^16; the flag again every 64 ms;
  * K2 one click up = the fine detune (R x 4102 / 4096), its LED half bright; pads 9-32 show the ratios (the current one white when detuned, the
    others dim) for 1.5 s and a pad there is swallowed (no patch load); back one click: exact, the current one its class's colour;
  * pad 7 held: pads 9-24 = the algorithms (the families' colours, the current one bright); pad 7 + pad 17 = the kick, the tonic while held (the
    audition through the FM's note-on: a new note); Shift + pad = the snare without sound; pad 7 let go = the pads back;
  * Clear + pad 7 = the current algorithm's voicing; Clear + knob = its value there;
  * the kick: a note on and off before the tick still plays (the carrier's AMP > 0), the phases reset (PH = 0 right before each R), R of operator 1
    with the drop x the velocity's factor;
  * velocity 127 / 64: a modulator's AMP x the factor (256 - s (127 - v) / 128), the carrier not; the brightness (the shape 0.5): x 2; the feedback
    P^2 x 512 halved into M_kk and the y[n-2] coefficient;
  * aliasing: an operator above 0.45 fs = 0; a modulator capped to (NY - f) / (4 pi f); the percussive family not capped;
  * Shift + K1 left of the centre: operator 1 percussive, its own decay while held (REL_C[v + the velocity's offset] a ms), the shorter of it and
    the release after; its LED red, the distance from the centre;
  * the legato (retrigger off, a note held): no new note; keyboard scaling (the bell at note 96): the modulators x (256 - 3 x 36) / 256;
  * vcf21.c_sdio (the audition) = a new FM note; psave's audition with Shift: none (its state cleared);
  * Clear + MIDI 1: the FM back to the defaults, the matrix's amounts 0 (the destination kept);
  * the patch: version 2 gathered; a version 1 patch converted (Shift + K1-K4, the feedback's square root, the ratios to their exact click).

    python tools/emu_fmeng2.py SC46.6.bin SC46.6_manifest.json
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
import modesel as MS  # noqa: E402
import modmx as MX  # noqa: E402
import fmeng as F  # noqa: E402
import vcf21_dsp as VD  # noqa: E402

V = T4.V
MGR = X.MGR
CLEAR = 23
FB, OSB = VD.FMB0, VD.OSB0
lsq = lambda l: l * l * 4


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]
    fl = {k: int(v, 16) for k, v in R["fmeng"]["labels"].items()}
    ml = {k: int(v, 16) for k, v in R["modesel"]["labels"].items()}
    xl = {k: int(v, 16) for k, v in R["modmx"]["labels"].items()}
    pl = {k: int(v, 16) for k, v in R["mpatch"]["labels"].items()}
    sl = {k: int(v, 16) for k, v in R["psave"]["labels"].items()}
    e = X.EP(img, man)
    dw, rd, pads = [], {}, []
    cur = {}                                                                          # every word's last write (SC47.5: an unchanged word is not written again)
    def w(uc, a, s, d): dw.append((uc.reg_read(UC_ARM_REG_R1) >> 8, uc.reg_read(UC_ARM_REG_R2))); cur[dw[-1][1]] = dw[-1][0]
    e.uc.hook_add(UC_HOOK_CODE, w, begin=F.DSP_WRITE, end=F.DSP_WRITE)
    def dread(uc, a, s, d):
        uc.reg_write(UC_ARM_REG_R0, (rd.get(uc.reg_read(UC_ARM_REG_R1), 0) & 0xFFFFFF) << 8); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, dread, begin=F.DSP_READ, end=F.DSP_READ)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: pads.append(1), begin=pl["c_mppad"], end=pl["c_mppad"])
    def tick(n=1):
        for _ in range(n): e.at(e.t + 1); e.call(fl["c_fmtick"], maxins=8_000_000)
    blk = F.FMR + F.B0
    par = lambda i: e.r8(blk + i)
    setp = lambda i, v: e.uc.mem_write(blk + i, bytes([v]))
    env = lambda k: struct.unpack_from("<H", bytes(e.uc.mem_read(blk + F.B_ENV + 2 * k, 2)))[0]
    def last(addr):
        v = [x for x, a in dw if a == addr]; return v[-1] if v else cur.get(addr)
    def idx(addr):
        v = [i for i, (x, a) in enumerate(dw) if a == addr]; return v[-1] if v else None
    press = lambda q: e.call(PRESS, MGR, q, 100, maxins=8_000_000)
    release = lambda q: e.call(RELEASE, MGR, q, maxins=8_000_000)
    clear = lambda on: e.call(0x08033320 if on else 0x0803381A, MGR, CLEAR, maxins=8_000_000)
    gate = V.TAIL + V.O_RT + V.RT_CNT
    non = e.r32(MX.NOTE_VT) & ~1
    def note(n, v): e.call(non, 0x20011334, 2, n, v, maxins=4_000_000)
    def rr(pos, det=1.0, pf=4096, step=0):
        d = round(4096 * det) * (4096 + 6 * step) >> 12
        return min(0x7FFFFF, (round(256 * F.RATIOS[pos * 24 >> 7]) * d * pf) >> 16)
    gv = lambda s, v: 256 - (s * (127 - min(v, 127)) >> 7)
    def modamp(amp, G): return min(0x7FFFFF, ((amp >> 2) * G) >> 6)

    # ---- FM on: the edge, the flag, R
    e.btn(2); e.btn(8); e.pad(26); e.pad(F.ROWPAD)
    check(par(F.B_ON) == 1 and e.r0(ml["c_msmode"], 0) == 2, "row pad 24: FM on")
    dw.clear(); tick(1)
    zs = all((0, FB + 12 * k + VD.F_AS) in dw and (0, FB + 12 * k + VD.F_O2) in dw for k in range(4))
    check(zs and last(OSB + VD.FM_FLAG) == 1 and idx(OSB + VD.FM_FLAG) > idx(FB + VD.F_AMP), f"the edge: the DSP's states 0 ({zs}); the flag after the AMPs")
    check(last(FB + VD.F_R) == 1 << 16 and [par(i) for i in range(16)] == list(F.DEFAULTS2), f"R of ratio 1 = {last(FB + VD.F_R):#x}; the stack's defaults")
    dw.clear(); tick(64)
    check(sum(1 for x, a in dw if a == OSB + VD.FM_FLAG and x == 1) >= 1, "the flag written again within 64 ms")

    # ---- the fine detune, the ratio overlay
    e.pad(F.PADNO)
    e.knob(1, 1); dw.clear(); tick(1); f = X.frame(e)
    want = rr(par(F.P_RAT + 1), step=1)
    check(par(F.P_RAT + 1) == F.R1 + 1 and last(FB + 12 + VD.F_R) == want, f"K2 a click up: the fine detune (R {last(FB + 12 + VD.F_R)} = {want})")
    check(f[61] & 0xFF == 0x17 and f[61] >> 8 == ((2 * 4 + 30) >> 1) + 2, f"K2's LED the ratio's colour, half bright ({f[61]:#x})")
    ov = f[8:32]
    exp = [0x01 if j == 2 else F.RDIM[F.rcol(r)] for j, r in enumerate(F.RATIOS)]
    check(ov == exp, f"pads 9-32: the ratios, the current one white (detuned), the others dim ({[hex(x) for x in ov[:6]]})")
    pads.clear(); e.pad(9)
    check(not pads, "a pad under the overlay: swallowed (no patch load)")
    e.knob(1, -1); f = X.frame(e)
    check(f[10] == 0x17, f"back a click: exact, the current ratio green ({f[10]:#x})")
    e.at(e.t + 2000); f = X.frame(e); pads.clear(); e.pad(9)
    check(f[8:32] != ov and f[8:16] == [0x49] * 8 and pads, f"after 1.5 s the pads are the patches' again ({[hex(x) for x in f[8:16]]}), a pad loads ({len(pads)})")

    # ---- the algorithms under pad 7
    fB = X.frame(e)
    press(F.PADNO); f = X.frame(e)
    famw = [F.FAMC[F.ALGS[i]["fam"]][0 if i == 0 else 1] for i in range(16)]
    check(par(F.B_P7) == 1 and f[8:24] == famw, f"pad 7 held: pads 9-24 = the algorithms ({[hex(x) for x in f[8:24]]})")
    n0 = len(e.ons); pads.clear()
    setp(F.B_NEW, 0); press(16)
    check(par(F.P_ALG) == 8 << 3 and len(e.ons) == n0 + 1 and e.ons[-1][0] == "on" and par(F.B_NEW) == 1 and not pads,
          f"pad 7 + pad 17: the kick ({par(F.P_ALG) >> 3}), the tonic on ({e.ons[n0:]}), a new FM note")
    release(16)
    check(e.ons[-1][0] == "off", "pad 17 let go: the tonic off")
    n1 = len(e.ons)
    e.shift(True); press(17); e.shift(False); release(17)
    check(par(F.P_ALG) == 9 << 3 and len(e.ons) == n1, f"Shift + pad 18: the snare without sound ({e.ons[n1:]})")
    release(F.PADNO); f = X.frame(e)
    check(par(F.B_P7) == 0 and f[8:24] == fB[8:24], f"pad 7 let go: the pads back ({[(i + 8, hex(x), hex(y)) for i, (x, y) in enumerate(zip(f[8:24], fB[8:24])) if x != y]})")

    # ---- the voicings
    clear(True); e.pad(F.PADNO); clear(False)
    check([par(i) for i in range(16)] == list(F.VOICINGS[9]), f"Clear + pad 7: the snare's voicing ({[par(i) for i in range(16)]})")
    for _ in range(5): e.knob(4, 1)
    v5 = par(F.P_LEV); clear(True); e.knob(4, 1); clear(False)
    check(v5 == F.VOICINGS[9][4] + 5 and par(F.P_LEV) == F.VOICINGS[9][4], f"Clear + K5: the voicing's level ({v5} -> {par(F.P_LEV)})")

    # ---- the kick: a short note, the phase resets, the drop
    press(F.PADNO); press(16); release(16); release(F.PADNO)
    clear(True); e.pad(F.PADNO); clear(False)
    tick(2)
    e.uc.mem_write(gate, bytes([0])); note(60, 100)
    dw.clear(); tick(1)
    ph = all(idx(FB + 12 * k + VD.F_PH) is not None and idx(FB + 12 * k + VD.F_PH) + 1 == idx(FB + 12 * k + VD.F_R) and last(FB + 12 * k + VD.F_PH) == 0 for k in range(4))
    check(ph, "the kick's note: the phases 0, each right before its R")
    check((last(FB + VD.F_AMP) or 0) > 0x100000, f"a note on and off before the tick still plays (AMP {last(FB + VD.F_AMP)})")
    drop = (((32767 * lsq(115)) >> 15) * 7 >> 4) * gv(160, 100) >> 8
    check(last(FB + VD.F_R) == rr(F.R1, pf=4096 + drop), f"R of operator 1 with the drop x the velocity ({last(FB + VD.F_R)} = {rr(F.R1, pf=4096 + drop)})")

    # ---- the stack: velocity, brightness, feedback, aliasing
    press(F.PADNO); press(8); release(8); release(F.PADNO)
    clear(True); e.pad(F.PADNO); clear(False)
    e.uc.mem_write(gate, bytes([1]))
    def amps(v, n=60):
        note(n, v); dw.clear(); tick(1); return [last(FB + 12 * k + VD.F_AMP) for k in range(4)]
    a127, a64 = amps(127), amps(64)
    car = 32767 * lsq(127) >> 8; m2 = 32767 * lsq(64) >> 8
    check(a127[0] == car and a64[0] == car and a127[1] == modamp(m2, 256) and a64[1] == modamp(m2, gv(96, 64)),
          f"velocity: operator 2 {a127[1]} -> {a64[1]} (x {gv(96, 64)} / 256), the carrier the same ({a127[0]} / {a64[0]})")
    rd[OSB + 14] = 0x400000; setp(F.P_FB, 64)
    ab = amps(127)
    check(ab[1] == modamp(m2, 512) and last(FB + 36 + VD.F_M + 3) == min(0x7FFFFF, 64 * 64 * 512) and last(FB + 36 + VD.F_HC) == 64 * 64 * 512,
          f"the brightness (shape 0.5): operator 2 x 2 ({ab[1]}); the feedback halved into M_44 / y[n-2] ({last(FB + 36 + VD.F_M + 3):#x})")
    rd[OSB + 14] = 0; setp(F.P_FB, 0)
    inc = 731500; rd[OSB + 11] = inc; setp(F.P_RAT + 3, F.rpos(16)); setp(F.P_RAT + 1, F.rpos(4))
    aa = amps(127)
    f2 = inc * 4
    cap = (((F.NY - f2) >> 11) * F.AACAP) // (f2 >> 11)
    check(aa[3] == 0 and aa[1] == cap < modamp(m2, 256) and aa[0] == car,
          f"aliasing: operator 4 at 16 x C7 = 0 ({aa[3]}), operator 2 capped ({aa[1]} = min(.., {cap})), the carrier not ({aa[0]})")
    setp(F.P_ALG, 10 << 3); am = amps(127); setp(F.P_ALG, 0)
    check(am[1] > cap, f"the percussive family (metal): not capped ({am[1]})")
    rd[OSB + 11] = 0; setp(F.P_RAT + 3, F.R1); setp(F.P_RAT + 1, F.R1)

    # ---- Shift + K1 left: operator 1 percussive
    e.shift(True); e.knob(0, -40); f = X.frame(e); e.shift(False)
    v = par(F.P_ATK)
    check(v == 24 and f[60] == ((80 + 2) << 8 | F.COL_PERC), f"Shift + K1 left: {v}, its LED red at the distance ({f[60]:#x})")
    note(60, 100); tick(1); e0 = env(0); tick(10); e10 = env(0)
    c = F.REL_C[24 + ((100 - 64) >> 3)]
    m = e0
    for _ in range(10): m = m * c >> 16
    check(e0 == 32767 and e10 == m, f"held: operator 1 decays at its own rate ({e10} = {m})")
    e.uc.mem_write(gate, bytes([0])); tick(5); e15 = env(0)
    for _ in range(5): m = m * c >> 16
    check(e15 == m, f"let go: the shorter of its decay and the release ({e15} = {m})")
    e.shift(True); e.knob(0, 40); e.shift(False)

    # ---- the legato, the keyboard scaling
    rec = e.r32(0x2003D71C + 0x14)
    e.uc.mem_write(rec + 0x27024 + 159, bytes([0xA1])); e.uc.mem_write(gate, bytes([1])); tick(1); setp(F.B_NEW, 0); vel0 = par(F.B_VEL)
    note(64, 50)
    ok1 = par(F.B_NEW) == 0 and par(F.B_VEL) == vel0 and par(F.B_NOTE) == 64
    e.uc.mem_write(gate, bytes([0])); note(65, 50)
    check(ok1 and par(F.B_NEW) == 1, f"the retrigger off: a legato note is not a new one ({ok1}); with no note held it is")
    e.uc.mem_write(rec + 0x27024 + 159, bytes([0]))
    press(F.PADNO); press(8 + 12); release(8 + 12); release(F.PADNO)
    clear(True); e.pad(F.PADNO); clear(False)
    e.uc.mem_write(gate, bytes([1]))
    ak = amps(127, 96)
    mb = 32767 * lsq(F.VOICINGS[12][5]) >> 8
    check(ak[1] == modamp(mb, 256 - 3 * 36), f"keyboard scaling: the bell's operator 2 at note 96 x {256 - 3 * 36} / 256 ({ak[1]} = {modamp(mb, 256 - 3 * 36)})")

    # ---- the auditions
    vl = e.vl
    setp(F.B_NEW, 0); n2 = len(e.ons); e.call(vl["c_sdio"], 0, 1, 100, 60, maxins=4_000_000)
    check(par(F.B_NEW) == 1 and len(e.ons) == n2 + 1, "vcf21.c_sdio (the audition): a new FM note")
    e.call(vl["c_sdio"], 0, 0, 0, 60, maxins=4_000_000)
    st = e.r0(sl["c_psst"])
    e.uc.mem_write(st + 6, bytes([0x80 | 60, 0])); n3 = len(e.ons)
    e.shift(True); e.call(fl["c_fmqsd"], 0, 1, 100, 60, maxins=4_000_000); e.shift(False)
    check(len(e.ons) == n3 and e.r8(st + 6) == 0, "psave's audition with Shift: none, its state cleared")
    e.call(fl["c_fmqsd"], 0, 1, 100, 60, maxins=4_000_000)
    check(len(e.ons) == n3 + 1, "without Shift: the audition")
    e.call(vl["c_sdio"], 0, 0, 0, 60, maxins=4_000_000)

    # ---- Clear + MIDI 1
    e.call(xl["c_mxset"], 0, 0, 1 + 16 * 3 + 7, maxins=4_000_000)
    e.call(xl["c_mxset"], 0, 1, 1 + 16 * 5, maxins=4_000_000)
    clear(True); e.call(0x08033320, MGR, 2, maxins=8_000_000); e.call(0x0803381A, MGR, 2, maxins=8_000_000); clear(False)
    mb_ = e.r0(xl["c_mxblk"], 0)
    pos = struct.unpack("<8H", bytes(e.uc.mem_read(mb_ + MX.B_POS, 16)))
    check([par(i) for i in range(16)] == list(F.DEFAULTS2) and pos[0] == 1 + 16 * 3 and pos[1] == 1 + 16 * 5,
          f"Clear + MIDI 1: the FM's defaults, the matrix's amounts 0 with the destinations ({pos[:2]})")

    # ---- the patch
    setp(F.P_ATK, 90)
    e.call(pl["c_mpgather"], 0, maxins=4_000_000); e.call(fl["c_fmgath"], 0, maxins=8_000_000)
    buf = bytes(e.uc.mem_read(PK.BUF + F.POFS, F.PLEN))
    check(buf[:4] == b"FM\x02\x01" and buf[4 + F.P_ATK] == 90, f"gather: version 2 ({buf[:4]})")
    p1 = bytearray(b"FM\x01\x01") + bytes([F.rpos(2) + 2, F.R1, F.R1, F.R1, 127, 64, 48, 32, 40, 0, 127, 8, 0, 32, 0, 64])
    p1.append((0x5A + sum(p1)) & 0xFF)
    keep = bytes(p1)
    def mpr(uc, a, s, d):
        uc.mem_write(uc.reg_read(UC_ARM_REG_R2), keep); uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_R1, F.PLEN)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    hk = e.uc.hook_add(UC_HOOK_CODE, mpr, begin=pl["c_mpr"], end=pl["c_mpr"])
    e.uc.reg_write(UC_ARM_REG_R5, 3); e.call(fl["c_fmappl"], 0, maxins=12_000_000)
    got = [par(i) for i in range(16)]
    check(got[:4] == [F.rpos(2), F.R1, F.R1, F.R1] and got[8:12] == [84, 64, 127, 68] and got[F.P_FB] == 64 and par(F.B_ON) == 1,
          f"a version 1 patch: the ratios exact, Shift + K1-K4 to the right half, the feedback's square root ({got})")
    e.uc.hook_del(hk)
    print(f"{man['marker']} FM2 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
