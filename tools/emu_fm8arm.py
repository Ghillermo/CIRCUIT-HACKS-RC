"""fm8arm's engine on its own (Unicorn, no firmware): c_fm8run against fm8's reference model.



    python tools/emu_fm8arm.py

A voice of the track's own slot, ticks of 1 ms: the envelopes (e, the stages) bit for bit with fm8.ref_tick for a sustained and a percussive

patch (the 4-operator defaults converted, a DX7 algorithm with every operator), a note on, held, let go; the R of every operator = the

reference's ratio x the pitch factor; the AMP written = the reference's from the attenuation sent; a note with the pitch envelope; the routing

words (K, M, HC, N) from the algorithm's table; the fixed mode; the write cache (a second identical tick writes nothing but the moving words)."""

from __future__ import annotations

import struct

import sys

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE  # noqa: E402

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_SP  # noqa: E402

import fm8 as F  # noqa: E402

import fm8arm as A  # noqa: E402

import fmeng as FE  # noqa: E402

import vcf21 as V  # noqa: E402

import vcf21_dsp as VD  # noqa: E402



BASE = 0x08070000

STUBS = {k: 0x08001000 + 0x10 * i for i, k in enumerate(["c_von", "c_msmode", "c_vpage", "c_vsetpage", "c_rtoff", "c_vreset", "c_mxzero", "c_edact",
                                                         "c_sdview", "c_shift", "c_vtrack", "c_vclr", "c_kslow", "c_psaoff", "c_sdtonic", "c_psst",
                                                         "c_sdio", "c_mpon", "c_mxclrh", "c_msheld", "c_mpr", "c_mpsz", "c_mpw",
                                                         "c_curpack", "c_resel"])}
PREV = dict(svc=0x08002000, non=0x08002100, knob=0x08002200, kleds=0x08002300, pad=0x08002400, rel=0x08002500, leds=0x08002600, gath=0x08002700,
            appl=0x08002800, mpio=0x08002900, save=0x08002A00, ledtask=0x08002B00, psxswap=0x08002C00, xqcopy=0x08002D00)   # fm8store's (not run here)

RETPAD = 0x08003000

INC60 = A.INCS[60]





def setup():

    VD.FMC1 = True; VD.FV0 = 0x4000; VD.use_fm8()
    import vcf21, modmx
    if vcf21.KSLOW is None: vcf21.use_kslow(modmx.MXR + 0x21EC)                     # as build_sc50_2 (the panel resets its accumulator)

    import fm8ui
    code, lab, T = A.build(BASE, STUBS, PREV, ui=fm8ui.ui)

    mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)

    mu.mem_map(0x08000000, 0x100000); mu.mem_map(0x20000000, 0x60000)

    mu.mem_write(BASE, code)

    mu.mem_write(RETPAD, b"\x00\xbf\x00\xbf")

    dsp = {}

    log = []

    def hook(uc, addr, size, _):

        if addr == A.DSP_WRITE:

            a_, v = uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R1) >> 8

            dsp[a_] = v; log.append((a_, v))

            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

        elif addr == A.DSP_READ:

            a_ = uc.reg_read(UC_ARM_REG_R1)

            uc.reg_write(UC_ARM_REG_R0, (dsp.get(a_, 0) << 8) & 0xFFFFFFFF)

            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    mu.hook_add(UC_HOOK_CODE, hook, begin=A.DSP_WRITE, end=A.DSP_WRITE + 1)

    mu.hook_add(UC_HOOK_CODE, hook, begin=A.DSP_READ, end=A.DSP_READ + 1)

    for a_ in (A.DSP_WRITE, A.DSP_READ): mu.mem_write(a_, b"\x70\x47")

    return mu, lab, T, dsp, log





def call(mu, addr, *regs):

    for i, r in enumerate(regs): mu.reg_write(UC_ARM_REG_R0 + i, r)

    mu.reg_write(UC_ARM_REG_SP, 0x2005F000); mu.reg_write(UC_ARM_REG_LR, RETPAD | 1)

    mu.emu_start(addr | 1, RETPAD, count=2_000_000)

    return mu.reg_read(UC_ARM_REG_R0)





def main():

    fails = 0

    def check(c_, m):

        nonlocal fails

        print(("ok  : " if c_ else "FAIL: ") + m); fails += 0 if c_ else 1

    mu, lab, T, dsp, log = setup()

    call(mu, lab["c_fmst"])

    TB, VS = A.FM8R + A.TB0, A.FM8R + A.VT0

    slot = VD.FMB0

    dsp[VD.OSB0 + 11] = INC60

    rd = lambda a_, n: mu.mem_read(a_, n)

    def put_patch(P): mu.mem_write(TB, bytes(P))

    def voice():

        b_ = bytes(rd(VS, 80))

        return list(struct.unpack_from("<9I", b_, 0)), list(b_[A.V_ST:A.V_ST + 9]), list(struct.unpack_from("<8H", b_, A.V_LAST))

    def tick(gate, dt=1, new=False, note=60, vel=100):

        if new: mu.mem_write(VS + A.V_NEW, b"\x01"); mu.mem_write(VS + A.V_NOTE, bytes([note])); mu.mem_write(VS + A.V_VEL, bytes([vel]))

        call(mu, lab["c_fmctx"], slot, 0, 0, 0)

        mu.mem_write(A.CTX8 + A.C_GATE, struct.pack("<I", gate)); mu.mem_write(A.CTX8 + A.C_DT, struct.pack("<I", dt))

        mu.mem_write(A.CTX8 + A.C_POLY, struct.pack("<I", 0))

        call(mu, lab["c_fm8run"], VS, TB)



    def scenario(P, name, ticks, rel_at, note=60, vel=100):

        nonlocal fails

        put_patch(P)

        call(mu, lab["c_fmvz"], VS)

        rv = F.Voice()

        ok_env = ok_r = ok_amp = True

        for i in range(ticks):

            gate = 1 if i < rel_at else 0

            new = i == 0

            log.clear()

            tick(gate, 1, new, note, vel)

            atts, pf = F.ref_tick(P, rv, gate, note, vel, 1, new)

            e, st, last = voice()

            if e != rv.e or st != rv.st:

                if ok_env: print(f"  {name} tick {i}: e {e[:4]} / {rv.e[:4]}, st {st} / {rv.st}")

                ok_env = False

            al = F.alg_of(F.algs(), P[F.GLB + F.G_ALG])

            for k in range(al["n"]):

                r_exp = min(0x7FFFFF, (F.ratio_r(P, k, INC60) * pf) >> 12)

                if dsp.get(slot + 16 * k + VD.F_R) != r_exp:

                    if ok_r: print(f"  {name} tick {i} op {k + 1}: R {dsp.get(slot + 16 * k + VD.F_R)} / {r_exp}")

                    ok_r = False

                used = al["used"] >> k & 1

                exp_att = atts[k] if used else None

                la = last[k]

                if (0xFFFF if exp_att is None else exp_att) != la and abs((0xFFFF if exp_att is None else exp_att) - la) >= F.THR and st[k] >= 4:

                    if ok_amp: print(f"  {name} tick {i} op {k + 1}: att sent {la}, now {exp_att}")

                    ok_amp = False

                amp = dsp.get(slot + 16 * k + VD.F_AMP)

                if (al["car"] >> k & 1) and la != 0xFFFF:

                    if amp != F.amp_of(la):

                        if ok_amp: print(f"  {name} tick {i} op {k + 1}: carrier AMP {amp} / {F.amp_of(la)}")

                        ok_amp = False

        check(ok_env, f"{name}: the envelopes (e, stages) = the reference's, {ticks} ticks, let go at {rel_at}")

        check(ok_r, f"{name}: R of every operator = ratio x pitch factor")

        check(ok_amp, f"{name}: the carriers' AMP = the reference's from the attenuation sent; a settled one sent")

        return rv



    P0 = bytearray(F.DEFAULT)

    scenario(P0, "the 4-op defaults", 400, 200)

    P1 = bytearray(F.convert4(FE.VOICINGS[12]))                                           # bell: percussive

    scenario(P1, "bell (percussive, 4-op)", 300, 150, note=72, vel=60)

    P2 = bytearray(F.convert4(FE.VOICINGS[8]))                                            # kick: the pitch envelope

    rv = scenario(P2, "kick (pitch envelope)", 200, 100, note=36, vel=127)

    P3 = bytearray(F.DEFAULT)

    P3[F.GLB + F.G_ALG] = 16 + 4                                                          # DX7 algorithm 5: three stacks of two

    for k in range(6):

        b_ = F.OPB * k

        P3[b_:b_ + 8] = bytes((70 - 5 * k, 50, 40, 60, 99, 80, 70, 0))

        P3[b_ + F.O_OL], P3[b_ + F.O_CRS], P3[b_ + F.O_FINE], P3[b_ + F.O_KVS] = 99 - 3 * k, k + 1, 10 * k, k

        P3[b_ + F.O_BP], P3[b_ + F.O_RD], P3[b_ + F.O_LD], P3[b_ + F.O_RS] = 39, 20 * k, 10, k

    P3[F.OPB * 5 + F.O_MODE] = 1                                                          # op 6 fixed

    P3[F.GLB + F.G_FB] = 90

    scenario(P3, "DX7 algorithm 5, 6 operators", 600, 300, note=84, vel=40)

    # routing words of P3: K (carriers 1, 3, 5), M (6->5, 4->3, 2->1), the feedback on 6, N = 6

    al = F.alg_of(F.algs(), 20)

    G = struct.unpack_from("<I", rd(A.CTX8 + A.C_G, 4))[0]

    fbc = min(0x7FFFFF, 90 * 90 * G)

    ok = dsp.get(slot + VD.F8_N) == 6

    for k in range(6):

        ok &= dsp.get(slot + 16 * k + VD.F_K) == (F.KW_CAR // 3 if al["car"] >> k & 1 else 0)

        for j in range(6):

            want = fbc if (k, j) == (5, 5) else F.M_FULL if al["mask"] >> (8 * k + j) & 1 else 0

            if dsp.get(slot + 16 * k + VD.F8_M + j) != want:

                print(f"  M[{k + 1}][{j + 1}] {dsp.get(slot + 16 * k + VD.F8_M + j)} / {want}"); ok = False

        ok &= dsp.get(slot + 16 * k + VD.F8_HC) == (fbc if k == 5 else 0)

    check(ok, "routing: N 6, K = KW / 3 on the carriers, M from the mask, the feedback's M and HC on op 6")

    # the cache: a settled voice, a second tick writes nothing but the refreshed counter-driven words

    put_patch(P0); call(mu, lab["c_fmvz"], VS); tick(1, 1, True)

    for _ in range(300): tick(1, 1)

    mu.mem_write(TB + A.B_DIRTY, bytes(1))                                              # (the tick clears it)
    cnt = []

    for _ in range(64):

        log.clear(); tick(1, 1); cnt.append(len(log))

    check(sorted(cnt)[-2] == 0 and max(cnt) <= 2, f"a sustained voice: no DSP write in 63 of 64 ticks, the routing's N and flag in one ({cnt})")

    # c_fm8conv = fm8.convert4, byte for byte: the voicings, the starters, the defaults and random parameter sets
    import random
    rnd = random.Random(5)
    sets = [list(v) for v in FE.VOICINGS] + [list(v) for _, v in FE.STARTERS] + [list(FE.DEFAULTS2)]
    sets += [[rnd.randrange(128) for _ in range(12)] + [rnd.randrange(16) << 3] + [rnd.randrange(128) for _ in range(3)] for _ in range(60)]
    bad = 0
    for p16 in sets:
        mu.mem_write(0x20030000, bytes(p16)); call(mu, lab["c_fm8conv"], 0x20030000, 0x20031000)
        got, want = bytes(rd(0x20031000, F.PLEN)), F.convert4(bytes(p16))
        if got != want:
            if not bad: print("  ", p16, [(i, got[i], want[i]) for i in range(F.PLEN) if got[i] != want[i]][:8])
            bad += 1
    check(bad == 0, f"c_fm8conv = fm8.convert4 on {len(sets)} parameter sets ({bad} differ)")
    print("FM8 ARM ENGINE RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")

    return fails





if __name__ == "__main__":

    sys.exit(1 if main() else 0)

