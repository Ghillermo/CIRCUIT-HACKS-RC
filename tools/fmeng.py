"""SC45.6 (the user, 2026-10-21: «can we have FM as another variant for osc? up to how many operators with dedicated envs?», «4op, A/R with fixed
sustain. Release could be velocity-dependant if it needs to save more space», «make sure to include some kick/noise percussive algos, some bell and
some strings along with the typical algorithms»): a 4-operator FM variant of the own engine's oscillator of MIDI 1 / 2 (DSP: vcf21_dsp.use_fm).

Choosing it: the mode row of the MIDI Preset view (modesel: a tap on pad 27) gets pad 24 = FM (violet): the oscillator mode (modesel's pad 19,
so every mode is set as the stock cycle sets it) + our flag; any other mode of the row (or the pad-27 cycle leaving the oscillator) = FM off.  With FM
on, pad 27 is violet and pad 7 = the FM knob page (vcf21's page 6; violet bright on it, dim off it):
  * K1-K4 = the ratio of operators 1-4 (24 values 0.5 .. 16, the inharmonic ones teal, the half ones light blue, the whole ones green), K5-K8 = their
    level (orange; a carrier's loudness, a modulator's index: up to 4 pi);
  * Shift + K1-K4 = their attack (light blue, 0 .. ~3 s); Shift + K5 = the algorithm (16, the colour of its family: classic white, percussive red,
    bells teal, strings green), Shift + K6 = feedback (magenta), Shift + K7 = noise (white: noise shaped by the algorithm's noise operator's
    envelope, added after the FM), Shift + K8 = release (blue, ~3 ms .. ~8 s; longer the harder the note: velocity-dependent);
  * Clear + knob = its default; Clear + pad 7 = every FM parameter back to the defaults.
The envelopes (A/R with a fixed sustain: the sustained operators hold at full while the note is held, the percussive ones (the algorithm says
which) decay at the release rate even while it is held) run here every millisecond (the head of the DSP service chain; RAM and DSP writes only:
0x080292F8, never MARK_DIRTY): AMP = envelope x level^2, R = ratio x the algorithm's detune x the pitch drop (the "kick" algorithms: operator 4 is
a pitch envelope, its level = the drop's depth, up to 3 octaves, its release = the drop's time), the noise level; the routing (the matrix M, the
carriers' weights K) when it changes and every 64 ms.  A note-on (the head of the note vtable) restarts the attacks (the percussive operators from 0)
and keeps the velocity; the gate = the engine's held notes (vcf21's RT_CNT).
Saved with the own-synth patches (mpatch): 21 bytes at padding + 100: "FM", version 1, on, the 16 parameters, a check byte (0x5A + the 20 bytes);
p4dest's c_p4gath / c_p4appl wrapped; a patch without them loads FM off (the parameters stay).  psave.XLEN = xpatch.XLEN = 124.
RAM: modmx.MXR + 0x200 (signature, then 2 blocks of 64 B)."""
from __future__ import annotations
import math
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, ldrb_reg, ldrb_w,  # noqa: E402
                   ldrh_imm, ldrh_reg, lsls_imm, lsls_reg, lsrs_imm, lsrs_reg, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list,
                   raw, str_imm, strb_imm, strb_reg, strb_w, strh_imm, strh_reg, subs_imm8, subs_reg, sub_sp_imm, add_sp_imm, str_sp)
import vcf21 as V  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
import mpatch as MP  # noqa: E402
import packio as PK  # noqa: E402
import modmx as MX  # noqa: E402
import modesel as MS  # noqa: E402
import build_sc14 as S14  # noqa: E402

FMR = MX.MXR + 0x200                  # 0x20045200
SIG = 0x31454D46                      # "FME1"
G_ACC = 4
B0, BS = 16, 64                       # track blocks: FMR + B0 + BS t
P_RAT, P_LEV, P_ATK, P_ALG, P_FB, P_NZ, P_REL = 0, 4, 8, 12, 13, 14, 15
B_ON, B_VEL, B_NEW, B_ATK, B_DIRTY, B_CNT, B_SENT, B_ENV, B_LAST = 16, 17, 18, 19, 20, 21, 22, 24, 32
PAGE = 6                              # vcf21's knob page index (pad 7)
PADNO = 6                             # pad 7
ROWPAD = 23                           # pad 24 of the mode row
DSP_WRITE, DSP_READ = 0x080292F8, 0x08029344
POFS, PLEN = 100, 21                  # in the padding: after p4dest's (88..99)
COL_FM = (0x49, 0x4A)                 # violet bright / dim (steady codes)
INV = V.INV

RATIOS = (0.5, 0.71, 1, 1.41, 1.5, 2, 2.5, 3, 3.5, 4, 4.24, 5, 5.5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)
def rcol(r): return 0x4D if r in (0.71, 1.41, 4.24) else 0x13 if r != int(r) and r != 0.5 else 0x17
ATK_MS = [0] + [round(2 * 1500 ** (i / 30)) for i in range(31)]                       # 32 attack times (pos >> 2)
ATK_STEP = [32767 if m == 0 else max(1, round(32767 / m)) for m in ATK_MS]
REL_TAU = [3 * (8000 / 3) ** (i / 63) for i in range(64)]                             # 64 release time constants (ms)
REL_C = [min(65535, round(65536 * math.exp(-1 / t))) for t in REL_TAU]
# defaults: ratios 1, carrier loud, modulators lower, no attack, the stack, no feedback / noise, a medium release
POS_R1 = (2 * 128 + 23) // 24
DEFAULTS = (POS_R1, POS_R1, POS_R1, POS_R1, 127, 64, 48, 32, 0, 0, 0, 0, 0, 0, 0, 64)
COL_LEV, COL_ATK, COL_FB, COL_NZ, COL_REL = 0x09, 0x13, 0x32, 0x01, 0x2B
FAM_COL = (0x01, 0x53, 0x4D, 0x17)    # classic white, percussive red, bells teal, strings green


def alg(name, fam, mods=(), car=(1,), sus=(1, 1, 1, 1), pitch=False, noise=1, det=(1, 1, 1, 1), relofs=(0, 0, 0, 0), fb=4):
    """mods: (source, destination) pairs of operators 1..4; car: the carriers; sus: 1 = held while the note is, 0 = percussive; pitch: operator 4
    is the pitch envelope (not heard); noise: the operator whose envelope shapes the noise; det: frequency multipliers; relofs: release steps; fb: the
    operator with the feedback (its M_kk)"""
    mask = 0
    for s_, d_ in mods: mask |= 1 << (4 * (d_ - 1) + (s_ - 1))
    if fb: mask |= 1 << (5 * (fb - 1))
    cm = sum(1 << (c - 1) for c in car)
    sm = sum(1 << k for k in range(4) if sus[k])
    kw = 0x3FFFFF // len(car)
    flags = (1 if pitch else 0) | (noise - 1) << 4
    return dict(name=name, fam=fam, b=struct.pack("<HBBBBxxI4H4b", mask, cm, sm, flags, (fb - 1) if fb else 0xFF, kw,
                                                    *[round(4096 * x) for x in det], *relofs))


ALGS = [
    alg("stack 4-3-2-1", 0, mods=((4, 3), (3, 2), (2, 1))),
    alg("3+4 on 2, on 1", 0, mods=((4, 2), (3, 2), (2, 1))),
    alg("4 on 1, 3-2-1", 0, mods=((4, 1), (3, 2), (2, 1))),
    alg("4-3 on 1, 2 on 1", 0, mods=((4, 3), (3, 1), (2, 1))),
    alg("two stacks", 0, mods=((4, 3), (2, 1)), car=(1, 3)),
    alg("4 on three", 0, mods=((4, 1), (4, 2), (4, 3)), car=(1, 2, 3)),
    alg("4-3, 2, 1", 0, mods=((4, 3),), car=(1, 2, 3)),
    alg("organ", 0, car=(1, 2, 3, 4)),
    alg("kick", 1, mods=((2, 1),), sus=(0, 0, 0, 0), pitch=True, relofs=(0, -8, 0, 0), fb=2),
    alg("snare", 1, mods=((2, 1),), sus=(0, 0, 0, 0), pitch=True, noise=3, relofs=(0, -6, 0, -8), fb=2),
    alg("metal / hat", 1, mods=((2, 1), (3, 1), (4, 1)), sus=(0, 0, 0, 0), det=(1, 1.414, 2.71, 3.49), relofs=(0, -4, -4, -4)),
    alg("tom / zap", 1, mods=((3, 2), (2, 1)), sus=(0, 0, 0, 0), pitch=True, relofs=(0, -6, -6, 0), fb=3),
    alg("bell", 2, mods=((2, 1), (4, 3)), car=(1, 3), sus=(0, 0, 0, 0), det=(1, 3.5, 2.0, 2.76), relofs=(6, 0, 6, 0)),
    alg("tubular", 2, mods=((2, 1), (3, 1)), car=(1, 4), sus=(0, 0, 0, 0), det=(1, 2.76, 5.4, 2.0), relofs=(8, 0, -4, 8)),
    alg("strings", 3, mods=((2, 1), (4, 3)), car=(1, 3), det=(1.0, 1.0, 1.007, 1.007)),
    alg("ensemble", 3, mods=((4, 1), (4, 2), (4, 3)), car=(1, 2, 3), det=(0.994, 1.0, 1.006, 1.0)),
]
ALEN = 24
assert all(len(x["b"]) == ALEN for x in ALGS) and len(ALGS) == 16
A_MASK, A_CAR, A_SUS, A_FLG, A_FB, A_KW, A_DET, A_ROF = 0, 2, 3, 4, 5, 8, 12, 20


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def asrs_imm(rd, rm, imm): return h(0x1000 | imm << 6 | rm << 3 | rd)
def ldr_reg(rt, rn, rm): return h(0x5800 | rm << 6 | rn << 3 | rt)
def ldrsb_reg(rt, rn, rm): return h(0x5600 | rm << 6 | rn << 3 | rt)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_f{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    def now(rd): imm32(rd, V.HAL_TICK); E(ldr_imm, rd, rd, 0)

    # ---- data
    data = bytearray(); T = {}
    def put(name, bs):
        while len(data) % 4: data.append(0)
        T[name] = base + len(data); data.extend(bs)
    put("algs", b"".join(x["b"] for x in ALGS))
    put("rat", struct.pack("<24H", *[round(256 * r) for r in RATIOS]))
    put("rcol", bytes(rcol(r) for r in RATIOS))
    put("astep", struct.pack("<32H", *ATK_STEP))
    put("relc", struct.pack("<64H", *REL_C))
    put("defs", bytes(DEFAULTS))
    put("fam", bytes(x["fam"] for x in ALGS))
    put("pcol", bytes((0, 0, 0, 0, COL_LEV, COL_LEV, COL_LEV, COL_LEV, COL_ATK, COL_ATK, COL_ATK, COL_ATK, 0, COL_FB, COL_NZ, COL_REL)))
    while len(data) % 4: data.append(0)
    E(raw, bytes(data))

    # ---- c_fmst() -> r0 = FMR, set up at the first use (the RAM holds the power-up pattern); clobbers r1-r3
    a.label("c_fmst")
    imm32(0, FMR); E(ldr_imm, 1, 0, 0); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "st_i", "ne"); E(raw, h(0x4770))
    a.label("st_i")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0)
    E(movs_imm, 1, 0); E(movs_imm, 3, (B0 + 2 * BS) // 4)
    a.label("st_z"); E(str_imm, 1, 0, 0); E(adds_imm8, 0, 4); E(subs_imm8, 3, 1); E(b_cond, "st_z", "ne")
    for t in (0, 1):
        E(mov_reg, 2, 4); E(adds_imm8, 2, B0 + BS * t); E(movs_imm, 3, 0)
        a.label(f"st_d{t}")
        imm32(1, T["defs"]); E(ldrb_reg, 1, 1, 3); E(strb_reg, 1, 2, 3)
        E(adds_imm8, 3, 1); E(cmp_imm, 3, 16); E(b_cond, f"st_d{t}", "lo")
        E(movs_imm, 1, 0xFF); E(strb_w, 1, 4, B0 + BS * t + B_SENT); E(movs_imm, 1, 100); E(strb_w, 1, 4, B0 + BS * t + B_VEL)
    imm32(1, SIG); E(str_imm, 1, 4, 0); E(mov_reg, 0, 4)
    E(pop_list, [4, 5], pc=True)

    # ---- c_fmblk(r0 = track) -> r0 = its block; clobbers r1-r3
    a.label("c_fmblk")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, "c_fmst")
    E(lsls_imm, 1, 4, 6); E(adds_reg, 0, 0, 1); E(adds_imm8, 0, B0); E(pop_list, [4], pc=True)

    # ---- c_fmalg(r0 = block) -> r0 = its algorithm's entry; clobbers r1
    a.label("c_fmalg")
    E(ldrb_imm, 0, 0, P_ALG); E(lsrs_imm, 0, 0, 3); E(movs_imm, 1, ALEN); E(muls, 0, 1); imm32(1, T["algs"]); E(adds_reg, 0, 0, 1); E(raw, h(0x4770))

    # ---- c_fmact(r0 = track) -> r0 = 1 while FM sounds: on, the engine on, in the oscillator mode (on is cleared out of it); clobbers r1-r3
    a.label("c_fmact")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0)
    E(bl, "c_fmblk"); E(mov_reg, 5, 0); E(ldrb_w, 0, 5, B_ON); E(cmp_imm, 0, 0); E(b_cond, "ac_0", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_von"]); E(cmp_imm, 0, 0); E(b_cond, "ac_off", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_msmode"]); E(cmp_imm, 0, 2); E(b_cond, "ac_off", "ne")
    E(movs_imm, 0, 1); E(pop_list, [4, 5], pc=True)
    a.label("ac_off"); E(movs_imm, 0, 0); E(strb_w, 0, 5, B_ON)
    a.label("ac_0"); E(movs_imm, 0, 0); E(pop_list, [4, 5], pc=True)

    # ---- c_fmw(r0 = DSP X address, r1 = value 24 bit): the DSP write (core 0); clobbers r0-r3
    a.label("c_fmw")
    E(mov_reg, 2, 0); E(lsls_imm, 1, 1, 8); E(movs_imm, 0, 0); E(b_w, DSP_WRITE)

    # ---- c_fmenv(r4 = block, r5 = dt ms, r6 = the algorithm, r7 = gate): the four envelopes; clobbers r0-r3, r8
    a.label("c_fmenv")
    E(raw, pushw([4, 5, 6, 7, 8, 9, 10], lr=True))
    E(movs_imm, 0, 0); E(raw, h(0x4680))                                                # mov r8, r0: k = 0
    a.label("ev_l")
    E(raw, h(0x4641))                                                                   # mov r1, r8
    E(lsls_imm, 2, 1, 1); E(adds_reg, 2, 2, 4); E(ldrh_imm, 0, 2, B_ENV); E(raw, h(0x4691))   # r0 = env, mov r9, r2: the env's address - B_ENV
    E(cmp_imm, 7, 0); E(b_cond, "ev_rel", "eq")
    E(ldrb_imm, 2, 4, B_ATK); E(lsrs_reg, 2, 1); E(movs_imm, 3, 1); E(ands_reg, 2, 3); E(cmp_imm, 2, 0); E(b_cond, "ev_hold", "eq")
    # attack: env += step x dt
    E(adds_reg, 2, 4, 1); E(ldrb_imm, 2, 2, P_ATK); E(lsrs_imm, 2, 2, 2); E(lsls_imm, 2, 2, 1); imm32(3, T["astep"]); E(ldrh_reg, 2, 3, 2)
    E(muls, 2, 5); E(adds_reg, 0, 0, 2); imm32(2, 32767); E(cmp_reg, 0, 2); E(b_cond, "ev_st", "lt")
    E(mov_reg, 0, 2)
    E(ldrb_imm, 2, 4, B_ATK); E(movs_imm, 3, 1); E(lsls_reg, 3, 1); E(raw, h(0x439A)); E(strb_imm, 2, 4, B_ATK)    # bics r2, r3
    E(b, "ev_st")
    a.label("ev_hold")                                                                  # after the attack: a sustained operator holds, a percussive one decays
    E(ldrb_imm, 2, 6, A_SUS); E(lsrs_reg, 2, 1); E(movs_imm, 3, 1); E(ands_reg, 2, 3); E(cmp_imm, 2, 0); E(b_cond, "ev_st", "ne")
    E(b, "ev_dec")
    a.label("ev_rel")
    E(ldrb_imm, 2, 4, B_ATK); E(movs_imm, 3, 1); E(lsls_reg, 3, 1); E(raw, h(0x439A)); E(strb_imm, 2, 4, B_ATK)
    a.label("ev_dec")                                                                   # the release index: (rel >> 1) + (vel - 64) >> 3 + the algorithm's offset
    E(ldrb_imm, 2, 4, P_REL); E(lsrs_imm, 2, 2, 1); E(ldrb_imm, 3, 4, B_VEL); E(subs_imm8, 3, 64); E(raw, asrs_imm(3, 3, 3)); E(adds_reg, 2, 2, 3)
    E(movs_imm, 3, A_ROF); E(adds_reg, 3, 3, 1); E(raw, ldrsb_reg(3, 6, 3)); E(adds_reg, 2, 2, 3)
    E(cmp_imm, 2, 0); E(b_cond, "ev_i1", "ge"); E(movs_imm, 2, 0)
    a.label("ev_i1"); E(cmp_imm, 2, 63); E(b_cond, "ev_i2", "le"); E(movs_imm, 2, 63)
    a.label("ev_i2"); E(lsls_imm, 2, 2, 1); imm32(3, T["relc"]); E(ldrh_reg, 2, 3, 2)     # r2 = c (x 65536)
    E(mov_reg, 3, 5)
    a.label("ev_m"); E(muls, 0, 2); E(lsrs_imm, 0, 0, 16); E(subs_imm8, 3, 1); E(b_cond, "ev_m", "ne")
    a.label("ev_st"); E(raw, h(0x464A)); E(strh_imm, 0, 2, B_ENV)                        # mov r2, r9
    E(raw, h(0x4640)); E(adds_imm8, 0, 1); E(raw, h(0x4680)); E(cmp_imm, 0, 4); E(b_cond, "ev_l", "lo")   # k++
    E(raw, popw([4, 5, 6, 7, 8, 9, 10], lr=True)); E(raw, h(0x4770))

    # ---- c_fmlsq(r0 = level 0..127) -> r0 = level^2 x 4 (0..64516); clobbers nothing else
    a.label("c_fmlsq")
    E(muls, 0, 0); E(lsls_imm, 0, 0, 2); E(raw, h(0x4770))

    # ---- c_fmsend(r4 = block, r6 = the algorithm, r7 = track): R / AMP of the four operators, the noise; with B_DIRTY (or every 64) K / M and the flag
    a.label("c_fmsend")
    E(raw, pushw([4, 5, 6, 7, 8, 9, 10, 11], lr=True))
    E(movs_imm, 0, 48); E(muls, 0, 7); imm32(1, VD.FMB0); E(adds_reg, 0, 0, 1); E(raw, h(0x4683))   # r11 = the FM blocks of the voice
    # the pitch factor pf (x 4096): 4096 + (env4 x lsq(lev4) >> 15) x 7 >> 4 with the algorithm's pitch flag
    imm32(5, 4096)
    E(ldrb_imm, 0, 6, A_FLG); E(movs_imm, 1, 1); E(ands_reg, 0, 1); E(cmp_imm, 0, 0); E(b_cond, "sd_np", "eq")
    E(ldrb_imm, 0, 4, P_LEV + 3); E(bl, "c_fmlsq"); E(ldrh_imm, 1, 4, B_ENV + 6); E(muls, 0, 1); E(lsrs_imm, 0, 0, 15); E(movs_imm, 1, 7); E(muls, 0, 1); E(lsrs_imm, 0, 0, 4)
    E(adds_reg, 5, 5, 0)
    a.label("sd_np"); E(raw, h(0x46AA))                                                 # mov r10, r5 = pf
    E(movs_imm, 0, 0); E(raw, h(0x4680))                                                # r8 = k
    a.label("sd_l")
    # R = rat256 x det4096 >> 12 x pf >> 12 << 11, clamped
    E(raw, h(0x4640)); E(adds_reg, 1, 4, 0); E(ldrb_imm, 1, 1, P_RAT); E(movs_imm, 2, 24); E(muls, 1, 2); E(lsrs_imm, 1, 1, 7); E(lsls_imm, 1, 1, 1)
    imm32(2, T["rat"]); E(ldrh_reg, 1, 2, 1)                                          # r1 = ratio x 256
    E(lsls_imm, 2, 0, 1); E(adds_imm8, 2, A_DET); E(ldrh_reg, 2, 6, 2); E(muls, 1, 2); E(lsrs_imm, 1, 1, 12)
    E(raw, h(0x4652)); E(muls, 1, 2); E(lsrs_imm, 1, 1, 1)                              # mov r2, r10; x pf >> 12 << 11 = >> 1
    imm32(2, 0x7FFFFF); E(cmp_reg, 1, 2); E(b_cond, "sd_r1", "ls"); E(mov_reg, 1, 2)
    a.label("sd_r1")
    E(movs_imm, 2, VD.FMS); E(muls, 2, 0); E(raw, h(0x445A)); E(adds_imm8, 2, VD.F_R); E(mov_reg, 0, 2); E(bl, "c_fmw")   # add r2, r11
    # AMP = env x lsq(level) >> 8 (operator 4 of a pitch algorithm: 0)
    E(raw, h(0x4640)); E(cmp_imm, 0, 3); E(b_cond, "sd_a", "ne")
    E(ldrb_imm, 1, 6, A_FLG); E(movs_imm, 2, 1); E(ands_reg, 1, 2); E(cmp_imm, 1, 0); E(b_cond, "sd_a", "eq")
    E(movs_imm, 1, 0); E(b, "sd_aw")
    a.label("sd_a")
    E(adds_reg, 1, 4, 0); E(ldrb_imm, 0, 1, P_LEV); E(bl, "c_fmlsq")
    E(raw, h(0x4641)); E(lsls_imm, 1, 1, 1); E(adds_reg, 1, 1, 4); E(ldrh_imm, 1, 1, B_ENV); E(muls, 1, 0); E(lsrs_imm, 1, 1, 8)
    a.label("sd_aw")
    E(raw, h(0x4640)); E(movs_imm, 2, VD.FMS); E(muls, 2, 0); E(raw, h(0x445A)); E(adds_imm8, 2, VD.F_AMP); E(mov_reg, 0, 2); E(bl, "c_fmw")
    E(raw, h(0x4640)); E(adds_imm8, 0, 1); E(raw, h(0x4680)); E(cmp_imm, 0, 4); bc("sd_l", "lo")
    # the noise: (noise^2 x 4) x env(noise op) >> 9
    E(ldrb_imm, 0, 4, P_NZ); E(bl, "c_fmlsq"); E(ldrb_imm, 1, 6, A_FLG); E(lsrs_imm, 1, 1, 4); E(lsls_imm, 1, 1, 1); E(adds_reg, 1, 1, 4)
    E(ldrh_imm, 1, 1, B_ENV); E(muls, 1, 0); E(lsrs_imm, 1, 1, 9)
    E(raw, h(0x4658)); E(adds_imm8, 0, VD.F_NZ); E(bl, "c_fmw")                          # mov r0, r11
    # the routing: K, M1..M4 per operator (sequential addresses) when dirty or every 64
    E(ldrb_w, 0, 4, B_CNT); E(adds_imm8, 0, 1); E(strb_w, 0, 4, B_CNT); E(movs_imm, 1, 63); E(ands_reg, 0, 1); E(cmp_imm, 0, 0); E(b_cond, "sd_k", "eq")
    E(ldrb_w, 0, 4, B_DIRTY); E(cmp_imm, 0, 0); bc("sd_x", "eq")
    a.label("sd_k")
    E(movs_imm, 0, 0); E(strb_w, 0, 4, B_DIRTY)
    E(movs_imm, 0, 0); E(raw, h(0x4680))
    a.label("sd_kl")
    E(movs_imm, 1, 0); E(ldrb_imm, 2, 6, A_CAR); E(raw, h(0x4640)); E(lsrs_reg, 2, 0); E(movs_imm, 3, 1); E(ands_reg, 2, 3); E(cmp_imm, 2, 0); E(b_cond, "sd_kw", "eq")
    E(ldr_imm, 1, 6, A_KW)
    a.label("sd_kw")
    E(movs_imm, 2, VD.FMS); E(muls, 2, 0); E(raw, h(0x445A)); E(adds_imm8, 2, VD.F_K); E(mov_reg, 0, 2); E(bl, "c_fmw")
    E(movs_imm, 0, 0); E(raw, h(0x4681))                                               # r9 = j
    a.label("sd_ml")
    E(raw, h(0x4640)); E(lsls_imm, 0, 0, 2); E(raw, h(0x4649)); E(adds_reg, 0, 0, 1)        # bit 4 k + j of the mask
    E(ldrh_imm, 2, 6, A_MASK); E(lsrs_reg, 2, 0); E(movs_imm, 3, 1); E(ands_reg, 2, 3); E(movs_imm, 1, 0); E(cmp_imm, 2, 0); E(b_cond, "sd_mw", "eq")
    imm32(1, 0x7FFFFF)
    E(raw, h(0x4640)); E(raw, h(0x4649)); E(cmp_reg, 0, 1)                              # (r0 = k, r1 = j: the diagonal = the feedback)
    imm32(1, 0x7FFFFF); E(b_cond, "sd_mw", "ne")
    E(ldrb_imm, 1, 4, P_FB); E(lsls_imm, 1, 1, 16)
    a.label("sd_mw")
    E(raw, h(0x4640)); E(movs_imm, 2, VD.FMS); E(muls, 2, 0); E(raw, h(0x445A)); E(raw, h(0x4648)); E(adds_reg, 2, 2, 0); E(adds_imm8, 2, VD.F_M)
    E(mov_reg, 0, 2); E(bl, "c_fmw")
    E(raw, h(0x4648)); E(adds_imm8, 0, 1); E(raw, h(0x4681)); E(cmp_imm, 0, 4); E(b_cond, "sd_ml", "lo")
    E(raw, h(0x4640)); E(adds_imm8, 0, 1); E(raw, h(0x4680)); E(cmp_imm, 0, 4); bc("sd_kl", "lo")
    a.label("sd_x")
    E(raw, popw([4, 5, 6, 7, 8, 9, 10, 11], lr=True)); E(raw, h(0x4770))

    # ---- c_fmflag(r0 = track, r1 = 0 / 1): the OSC1 block's flag word, when it changes (B_SENT); clobbers r0-r3
    a.label("c_fmflag")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_fmblk"); E(mov_reg, 6, 0); E(ldrb_w, 0, 6, B_SENT); E(cmp_reg, 0, 5); E(b_cond, "fl_x", "eq")
    E(strb_w, 5, 6, B_SENT); E(movs_imm, 0, 1); E(strb_w, 0, 6, B_DIRTY)
    E(movs_imm, 0, 48); E(muls, 0, 4); imm32(1, VD.OSB0 + VD.FM_FLAG); E(adds_reg, 0, 0, 1); E(mov_reg, 1, 5); E(bl, "c_fmw")
    a.label("fl_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_fmtick: the head of the DSP service chain (the tick holds the DSP semaphore: RAM and DSP writes only, no MARK_DIRTY)
    a.label("c_fmtick")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7, 8], lr=True))
    E(movs_imm, 7, 0)
    a.label("tk_l")
    E(mov_reg, 0, 7); E(bl, "c_fmact"); E(cmp_imm, 0, 0); E(b_cond, "tk_on", "ne")
    E(mov_reg, 0, 7); E(movs_imm, 1, 0); E(bl, "c_fmflag")
    E(mov_reg, 0, 7); E(bl, L["c_vpage"]); E(cmp_imm, 0, PAGE); bc("tk_n", "ne")          # the FM page without FM: back to OSC 1
    E(mov_reg, 0, 7); E(movs_imm, 1, 1); E(bl, L["c_vsetpage"]); E(b, "tk_n")
    a.label("tk_on")
    E(mov_reg, 0, 7); E(movs_imm, 1, 1); E(bl, "c_fmflag")
    E(mov_reg, 0, 7); E(bl, "c_fmblk"); E(mov_reg, 4, 0)
    now(0); E(ldr_imm, 1, 4, B_LAST); E(subs_reg, 5, 0, 1); bc("tk_n", "eq"); E(str_imm, 0, 4, B_LAST)
    E(cmp_imm, 5, 50); E(b_cond, "tk_dt", "ls"); E(movs_imm, 5, 50)
    a.label("tk_dt")
    E(mov_reg, 0, 4); E(bl, "c_fmalg"); E(mov_reg, 6, 0)
    E(ldrb_w, 0, 4, B_NEW); E(cmp_imm, 0, 0); E(b_cond, "tk_g", "eq")                      # a new note: the attacks; the percussive operators from 0
    E(movs_imm, 0, 0); E(strb_w, 0, 4, B_NEW); E(movs_imm, 0, 15); E(strb_imm, 0, 4, B_ATK)
    E(movs_imm, 1, 0)
    a.label("tk_z")
    E(ldrb_imm, 0, 6, A_SUS); E(lsrs_reg, 0, 1); E(movs_imm, 2, 1); E(ands_reg, 0, 2); E(cmp_imm, 0, 0); E(b_cond, "tk_zn", "ne")
    E(lsls_imm, 0, 1, 1); E(adds_reg, 0, 0, 4); E(movs_imm, 2, 0); E(strh_imm, 2, 0, B_ENV)
    a.label("tk_zn"); E(adds_imm8, 1, 1); E(cmp_imm, 1, 4); E(b_cond, "tk_z", "lo")
    a.label("tk_g")                                                                    # the gate: the engine's held notes
    imm32(0, V.TAIL + V.O_RT + V.RT_CNT); E(lsls_imm, 1, 7, 3); E(ldrb_reg, 0, 0, 1); E(movs_imm, 1, 15); E(ands_reg, 0, 1)
    E(push_list, [7]); E(mov_reg, 7, 0); E(bl, "c_fmenv"); E(pop_list, [7])
    E(bl, "c_fmsend")
    a.label("tk_n"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 2); bc("tk_l", "lo")
    E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7, 8], lr=True)); E(b_w, prev["svc"])

    # ---- c_fmnon (the note vtable's slot: this, track id, note, velocity): MIDI 1 / 2, a note on: a new note, its velocity
    a.label("c_fmnon")
    E(raw, pushw([0, 1, 2, 3, 4, 5], lr=True))
    E(mov_reg, 4, 1); E(subs_imm8, 4, 2); E(cmp_imm, 4, 1); bc("nn_x", "hi")
    E(cmp_imm, 3, 0); bc("nn_x", "eq"); E(mov_reg, 5, 3)
    E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(strb_w, 5, 0, B_VEL); E(movs_imm, 1, 1); E(strb_w, 1, 0, B_NEW)
    a.label("nn_x")
    E(raw, popw([0, 1, 2, 3, 4, 5], lr=True)); E(b_w, prev["non"])

    # ---- c_fmpg(r0 = track) -> r0 = 1 when the FM page is the one the knobs move (FM on, the engine on, no CC editor, no step-drummer view)
    a.label("c_fmpg")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(bl, "c_fmact"); E(cmp_imm, 0, 0); E(b_cond, "pg_0", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_edact"]); E(cmp_imm, 0, 0); E(b_cond, "pg_0", "ne")
    E(mov_reg, 0, 4); E(bl, L["c_sdview"]); E(cmp_imm, 0, 0); E(b_cond, "pg_0", "ne")
    E(mov_reg, 0, 4); E(bl, L["c_vpage"]); E(cmp_imm, 0, PAGE); E(b_cond, "pg_0", "ne")
    E(movs_imm, 0, 1); E(pop_list, [4], pc=True)
    a.label("pg_0"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_fmpar(r0 = knob 0..7) -> r0 = the parameter index (with Shift: + 8); clobbers r1-r3
    a.label("c_fmpar")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(mov_reg, 0, 4); E(b_cond, "pa_x", "eq"); E(adds_imm8, 0, 8)
    a.label("pa_x"); E(pop_list, [4], pc=True)

    # ---- c_fmknob (slot 4 of the macro handlers: obj, knob, delta): the FM page of MIDI 1 / 2, else the previous slot
    a.label("c_fmknob")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(bl, L["c_vtrack"]); E(cmp_imm, 0, 1); bc("kn_prev", "hi"); E(mov_reg, 6, 0)
    E(bl, "c_fmpg"); E(cmp_imm, 0, 0); bc("kn_prev", "eq")
    E(ldr_sp, 0, 4); E(movs_imm, 1, 7); E(ands_reg, 0, 1); E(bl, "c_fmpar"); E(mov_reg, 5, 0)      # r5 = the parameter
    E(mov_reg, 0, 6); E(bl, "c_fmblk"); E(mov_reg, 4, 0)
    E(ldr_sp, 0, 0); E(bl, L["c_vclr"]); E(cmp_imm, 0, 0); E(b_cond, "kn_add", "eq")
    imm32(1, T["defs"]); E(ldrb_reg, 0, 1, 5); E(b, "kn_st")                                # Clear: the default
    a.label("kn_add")
    E(ldrb_reg, 0, 4, 5); E(ldr_sp, 2, 8); E(adds_reg, 0, 0, 2)
    E(cmp_imm, 0, 0); E(b_cond, "kn_c1", "ge"); E(movs_imm, 0, 0)
    a.label("kn_c1"); E(cmp_imm, 0, 127); E(b_cond, "kn_st", "le"); E(movs_imm, 0, 127)
    a.label("kn_st"); E(strb_reg, 0, 4, 5); E(movs_imm, 0, 1); E(strb_w, 0, 4, B_DIRTY)
    E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("kn_prev"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["knob"])

    # ---- c_fmkleds (slot 7 of the macro handlers: obj) -> r0 = the knob LED buffer: on the FM page the eight parameters (or, with Shift, the other eight)
    a.label("c_fmkleds")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(bl, prev["kleds"]); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(bl, L["c_vtrack"]); E(cmp_imm, 0, 1); bc("kl_x", "hi"); E(mov_reg, 6, 0)
    E(bl, "c_fmpg"); E(cmp_imm, 0, 0); bc("kl_x", "eq")
    E(mov_reg, 0, 6); E(bl, "c_fmblk"); E(mov_reg, 4, 0)
    E(movs_imm, 6, 0)
    a.label("kl_l")
    E(mov_reg, 0, 6); E(bl, "c_fmpar"); E(mov_reg, 7, 0); E(ldrb_reg, 0, 4, 7)            # r7 = the parameter, r0 = its value
    E(cmp_imm, 7, 4); E(b_cond, "kl_nr", "hs")                                            # a ratio: its class's colour, brighter the higher
    E(movs_imm, 1, 24); E(muls, 0, 1); E(lsrs_imm, 0, 0, 7); imm32(1, T["rcol"]); E(ldrb_reg, 1, 1, 0); E(lsls_imm, 0, 0, 2); E(adds_imm8, 0, 30); E(b, "kl_put")
    a.label("kl_nr")
    E(cmp_imm, 7, P_ALG); E(b_cond, "kl_na", "ne")                                        # the algorithm: its family's colour, brighter along the family
    E(lsrs_imm, 0, 0, 3); imm32(1, T["fam"]); E(ldrb_reg, 2, 1, 0); imm32(1, FAM_COL[0] | FAM_COL[1] << 8 | FAM_COL[2] << 16 | FAM_COL[3] << 24)
    E(lsls_imm, 3, 2, 3); E(lsrs_reg, 1, 3); E(movs_imm, 3, 0xFF); E(ands_reg, 1, 3)
    E(movs_imm, 3, 3); E(ands_reg, 0, 3); E(lsls_imm, 0, 0, 5); E(adds_imm8, 0, 30); E(b, "kl_put")
    a.label("kl_na")
    imm32(1, T["pcol"]); E(ldrb_reg, 1, 1, 7)
    a.label("kl_put")
    E(adds_imm8, 0, 2); E(lsls_imm, 0, 0, 8); E(orrs_reg, 0, 1); E(lsls_imm, 1, 6, 1); E(strh_reg, 0, 5, 1)
    E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "kl_l", "lo")
    a.label("kl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_fmdefs(r0 = track): every FM parameter back to its default; clobbers r0-r3
    a.label("c_fmdefs")
    E(push_list, [4], lr=True); E(bl, "c_fmblk"); E(mov_reg, 4, 0); E(movs_imm, 3, 0)
    a.label("df_l"); imm32(1, T["defs"]); E(ldrb_reg, 1, 1, 3); E(strb_reg, 1, 4, 3); E(adds_imm8, 3, 1); E(cmp_imm, 3, 16); E(b_cond, "df_l", "lo")
    E(movs_imm, 0, 1); E(strb_w, 0, 4, B_DIRTY); E(pop_list, [4], pc=True)

    # ---- c_fmrow(r0 = track) -> r0 = 1 while modesel's mode row is open for it; clobbers r1
    a.label("c_fmrow")
    imm32(1, MS.RAM); E(ldrb_imm, 1, 1, 0); E(adds_imm8, 0, 1); E(cmp_reg, 1, 0); E(b_cond, "rw_1", "eq")      # (movs sets the flags: after the branch)
    E(movs_imm, 0, 0); E(raw, h(0x4770))
    a.label("rw_1"); E(movs_imm, 0, 1); E(raw, h(0x4770))

    # ---- c_fmpad (slot 0 of the template view: view, pad, velocity): pad 24 of the mode row = FM; the row's other modes = FM off; pad 7 = the FM page
    a.label("c_fmpad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1)
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); bc("pd_prev", "hi"); E(mov_reg, 4, 0)            # r4 = the track
    E(cmp_imm, 5, PADNO); bc("pd_row", "ne")
    E(mov_reg, 0, 4); E(bl, "c_fmact"); E(cmp_imm, 0, 0); bc("pd_prev", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_edact"]); E(cmp_imm, 0, 0); bc("pd_prev", "ne")
    E(bl, L["c_mxclrh"]); E(cmp_imm, 0, 0); E(b_cond, "pd_pg", "eq")
    E(mov_reg, 0, 4); E(bl, "c_fmdefs"); E(b, "pd_x")                                        # Clear + pad 7: the defaults
    a.label("pd_pg"); E(mov_reg, 0, 4); E(movs_imm, 1, PAGE); E(bl, L["c_vsetpage"]); E(b, "pd_x")
    a.label("pd_row")
    E(mov_reg, 0, 4); E(bl, "c_fmrow"); E(cmp_imm, 0, 0); bc("pd_prev", "eq")
    E(bl, L["c_msheld"]); E(cmp_imm, 0, 0); bc("pd_prev", "ne")
    E(cmp_imm, 5, ROWPAD); E(b_cond, "pd_ofm", "ne")
    E(raw, h(0x9800)); E(movs_imm, 1, MS.ROW + 2); E(raw, h(0x9A02)); E(bl, prev["pad"])      # the oscillator (modesel), then FM on
    E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(movs_imm, 1, 1); E(strb_w, 1, 0, B_ON); E(strb_w, 1, 0, B_DIRTY); E(b, "pd_x")
    a.label("pd_ofm")
    E(cmp_imm, 5, MS.ROW); bc("pd_prev", "lo"); E(cmp_imm, 5, MS.ROW + 6); bc("pd_prev", "hi")
    E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(movs_imm, 1, 0); E(strb_w, 1, 0, B_ON)
    a.label("pd_prev"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["pad"])
    a.label("pd_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)

    # ---- c_fmleds (slot 7 of the template view: view) -> r0 = the LED buffer: pad 24 of the row, pad 27 and pad 7 with FM on
    a.label("c_fmleds")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); bc("le_x", "hi"); E(mov_reg, 6, 0)
    E(mov_reg, 0, 6); E(bl, "c_fmact"); E(mov_reg, 7, 0)
    E(mov_reg, 0, 6); E(bl, "c_fmrow"); E(cmp_imm, 0, 0); E(b_cond, "le_nr", "eq")
    E(movs_imm, 1, COL_FM[1]); E(cmp_imm, 7, 0); E(b_cond, "le_r1", "eq"); E(movs_imm, 1, COL_FM[0])
    E(movs_imm, 2, MS.COLS[2][1]); E(strh_imm, 2, 5, 2 * (MS.ROW + 2))                       # FM on: the oscillator's pad dim
    a.label("le_r1"); E(strh_imm, 1, 5, 2 * ROWPAD)
    a.label("le_nr")
    E(cmp_imm, 7, 0); E(b_cond, "le_x", "eq")
    E(movs_imm, 1, COL_FM[0]); E(strh_imm, 1, 5, 2 * 26)                                      # pad 27: the FM colour
    E(mov_reg, 0, 6); E(bl, L["c_vpage"]); E(movs_imm, 1, COL_FM[1]); E(cmp_imm, 0, PAGE); E(b_cond, "le_p", "ne"); E(movs_imm, 1, COL_FM[0])
    a.label("le_p"); E(strh_imm, 1, 5, 2 * PADNO)
    a.label("le_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_fmsum(r0 = 21 bytes) -> r0 = 0x5A + the first 20, & 0xFF; clobbers r1, r2
    a.label("c_fmsum")
    E(movs_imm, 1, 0); E(movs_imm, 2, 0x5A)
    a.label("su_l"); E(raw, h(0x5C43)); E(adds_reg, 2, 2, 3); E(adds_imm8, 1, 1); E(cmp_imm, 1, PLEN - 1); E(b_cond, "su_l", "lo")     # ldrb r3, [r0, r1]
    E(movs_imm, 0, 0xFF); E(ands_reg, 0, 2); E(raw, h(0x4770))

    # ---- c_fmgath(r0 = track) in c_mpsave: p4dest's gather, then FM at padding + 100
    a.label("c_fmgath")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0)
    E(bl, prev["gath"])
    E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(mov_reg, 5, 0); imm32(6, PK.BUF + POFS)
    E(movs_imm, 0, ord("F")); E(strb_imm, 0, 6, 0); E(movs_imm, 0, ord("M")); E(strb_imm, 0, 6, 1); E(movs_imm, 0, 1); E(strb_imm, 0, 6, 2)
    E(ldrb_w, 0, 5, B_ON); E(strb_imm, 0, 6, 3)
    E(movs_imm, 7, 0)
    a.label("ga_l"); E(ldrb_reg, 0, 5, 7); E(adds_imm8, 7, 4); E(strb_reg, 0, 6, 7); E(subs_imm8, 7, 3); E(cmp_imm, 7, 16); E(b_cond, "ga_l", "lo")
    E(mov_reg, 0, 6); E(bl, "c_fmsum"); E(strb_imm, 0, 6, PLEN - 1)
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_fmappl(r0 = track) in c_mpload (r5 = the slot there): p4dest's apply, then the patch's FM (none or not valid: FM off)
    a.label("c_fmappl")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 7, 5)
    E(bl, prev["appl"])
    E(lsrs_imm, 0, 7, 3); E(lsls_imm, 1, 7, 29); E(lsrs_imm, 1, 1, 20)                    # r0 = the bank, r1 = (slot & 7) x 512
    imm32(2, MP.OFF + POFS); E(adds_reg, 1, 1, 2)
    imm32(2, PK.BUF + POFS); E(movs_imm, 3, PLEN); E(bl, L["c_mpr"])
    imm32(6, PK.BUF + POFS); E(mov_reg, 5, 0); E(mov_reg, 7, 1)
    E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(mov_reg, 1, 0); E(movs_imm, 0, 0); E(strb_w, 0, 1, B_ON); E(movs_imm, 0, 1); E(strb_w, 0, 1, B_DIRTY)
    E(mov_reg, 4, 1)                                                                     # r4 = the block
    E(cmp_imm, 5, 0); E(b_cond, "ap_x", "ne"); E(cmp_imm, 7, PLEN); E(b_cond, "ap_x", "ne")
    E(ldrb_imm, 0, 6, 0); E(cmp_imm, 0, ord("F")); E(b_cond, "ap_x", "ne"); E(ldrb_imm, 0, 6, 1); E(cmp_imm, 0, ord("M")); E(b_cond, "ap_x", "ne")
    E(ldrb_imm, 0, 6, 2); E(cmp_imm, 0, 1); E(b_cond, "ap_x", "ne")
    E(mov_reg, 0, 6); E(bl, "c_fmsum"); E(ldrb_imm, 1, 6, PLEN - 1); E(cmp_reg, 0, 1); E(b_cond, "ap_x", "ne")
    E(movs_imm, 7, 0)
    a.label("ap_l"); E(adds_imm8, 7, 4); E(ldrb_reg, 0, 6, 7); E(subs_imm8, 7, 4)
    E(cmp_imm, 0, 127); E(b_cond, "ap_v", "ls"); E(movs_imm, 0, 127)
    a.label("ap_v"); E(strb_reg, 0, 4, 7); E(adds_imm8, 7, 1); E(cmp_imm, 7, 16); E(b_cond, "ap_l", "lo")
    E(ldrb_imm, 0, 6, 3); E(movs_imm, 1, 1); E(ands_reg, 0, 1); E(strb_w, 0, 4, B_ON)
    a.label("ap_x"); E(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble(), T


# ==================================================================================================================================== SC46.6 (use_v2)
V2 = False
SIGV2, SIG2 = False, 0x32454D46                                         # (use_sig2) "FME2"


POLY = False                                                            # SC47.4 (use_poly)
CTX = FMR + 0x90                                                        # (POLY) the send's context: + 0 the operator blocks, + 4 the increment, + 8 the noise's address,
CTXSIG = 0x58544346                                                     # + 12 "FCTX" while poly's (else the context is cleared: the RAM is not at boot)


def use_poly():
    """SC47.4 (the user, 2026-10-26: «add polyphony to the remaing voices», «FM: 4 voces en total»; vcf21_dsp.use_poly3, poly.use_v3): c_fmsend takes a
    context (CTX, 0 = the track's as before): the operator blocks (a voice's at X:FV0 + 48 s), the increment for the aliasing limits (the voice's,
    from its note; else the DSP's OSC1 + 11), the noise's address (the voice record's + 10; else OSC1 + NZ_OFF).  With the track in poly (poly's
    O_ACT) the tick leaves the track's envelopes and sends to poly's voices (it still writes the flag)."""
    global POLY
    assert V2
    POLY = True


WCACHE = False                                                          # SC47.5 (use_wcache)
WC = MX.MXR + 0xA00                                                     # (WCACHE) the last value written a word | bit 31: X:FV0..+191 (poly's FM voices), FMB0..+95, the
                                                                        # voice records PV_REC0..+223 (512 x 4 B)
SHC = MX.MXR + 0x9A0                                                    # (WCACHE) the shape read once a track a tick (poly clears it; 0 = read)
WCX, WCSIG = MX.MXR + 0x9A4, 0x31435757                                 # (WCACHE) + 0 the refresh's index, + 4 "WWC1" (the cache zeroed at the first use)
FV_MASK = sum(1 << w for w in (2, 3, 4, 5, 6, 7, 8, 11))                # (WCACHE) an operator block's ARM-owned words: R, AMP, K, M1-M4, the feedback's half
REC_MASK = sum(1 << w for w in (10, 15, 21, 22, 23, 26, 27))            # (WCACHE) a record's: the noise, K, NOTE, the target, TRIG, TV, the FM blocks (not the
                                                                        # offset word 6: SM_L2 in the sample mode)


def use_wcache():
    """SC47.5 (the user, 2026-10-26: «tengo la sensación de que el clock se vuelve inestable al usar FM poly»): every DSP write is an SPI transaction
    that waits for the DSP (0x080292F8: the address, then 3 bytes); an FM send wrote R / AMP of four operators, the noise and the feedback each time
    (and the whole routing at every poly note).  c_fmw now skips a write of an operator block's ARM-owned word (R, AMP, K, M1-M4, the feedback's
    half: not the phase, the output, the smoothed AMP, y[n - 2], which the DSP moves) when the word already holds that value: a cache of the last
    value a word (WC: poly's voice blocks X:FV0.., the tracks' X:FMB0.., and the ARM-owned words of poly's voice records, whose writes come here
    too: poly's c_pyw); fmeng's tick writes one cached word again a tick (c_fmref: all 512 every 0.5 s: a DSP reload is never stuck, and no
    burst).  With poly's context the shape (OSC1 + 14) is read once a track a tick (SHC)."""
    global WCACHE
    assert POLY
    WCACHE = True


WC6 = False                                                             # SC47.6 (use_wc6)


def wc_ranges():
    """(WC6) the cached ranges: (the first word, the words, the block size, the ARM-owned words' mask, the first index)."""
    r, i = [], 0
    for base, ln, mod, mask in ((VD.FV0, 240, VD.FMS, FV_MASK), (VD.FV_ADDRS[5], 48, VD.FMS, FV_MASK), (VD.FMB0, 96, VD.FMS, FV_MASK),
                                (VD.PV_REC0, 2 * VD.PV_N * VD.PV_RS, VD.PV_RS, REC_MASK)):
        r.append((base, ln, mod, mask, i)); i += ln
    return r, i


def use_wc6():
    """SC47.6 (poly.use_v5, vcf21_dsp.use_poly6: six FM voices, six records a track): the cache covers the five FM voices from X:FV0 (240 words),
    the sixth at its own place, the tracks' FMB0 and the twelve records (720 words); the refresh goes round them all (0.72 s); poly's track blocks
    are 128 B (TBS)."""
    global WC6
    assert WCACHE
    WC6 = True


def use_sig2():
    """SC46.9 (the user, 2026-10-26: «fm synth sounds clicky, with really short gates» · «they're ok after reboot»): installing a build resets the
    STM32 without clearing the RAM, so the FM's block of an older beta (version 1, the same "FME1", another layout from byte 33 on) was read
    as version 2's (the phase resets, pad 7 held, the overlay) until the power was cut.  Version 2's block has its own signature now."""
    global SIGV2
    SIGV2 = True
B_PHR, B_NOTE, B_P7, B_OVK, B_OVT, B_LEDT = 36, 37, 38, 39, 40, 44     # (V2) block bytes: phase resets, the note, pad 7 held, the overlay's kind / time, the LED task's time
A_VS, A_KS = 6, 7                                                       # (V2) the algorithm's bytes: velocity -> index sensitivity, keyboard scaling
NY = round(0.45 * (1 << 24))                                            # (V2) the highest operator frequency (2^24 = a cycle a sample)
AACAP = round((1 << 23) / (4 * math.pi))                                # (V2) AMP that gives a phase deviation of one radian
OVL_MS, STALE_MS = 1500, 200
FAMC = ((0x01, 0x02), (0x45, 0x46), (0x4D, 0x4E), (0x17, 0x18))       # (V2) the pad overlay: the families' bright / dim
RDIM = {0x4D: 0x4E, 0x13: 0x14, 0x17: 0x18}
COL_PERC = 0x53                                                         # (V2) Shift + K1-K4 left of the centre (the operator percussive): red
CENTRE = 64
VS = (96,) * 8 + (160, 160, 112, 160, 128, 128, 48, 48)                 # velocity -> index per algorithm (0 = none, 256 = all)
KS = (2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 3, 3, 2, 2)                    # index -1/256 a semitone above C4 (and the release one step every 8)


def rpos(r): return (RATIOS.index(r) * 128 + 23) // 24                  # the first knob position of a ratio
def atk(i): return CENTRE + 2 * i                                       # Shift + K1-K4 right: attack index i (0..31)


R1 = rpos(1)
DEFAULTS2 = (R1, R1, R1, R1, 127, 64, 48, 32, CENTRE, CENTRE, CENTRE, CENTRE, 0, 0, 0, 64)
# Clear + pad 7: a playable voicing of each algorithm (ratios, levels, Shift + K1-K4, the algorithm, feedback, noise, release); row 0 = the defaults
VOICINGS = [
    DEFAULTS2,
    (R1, R1, R1, rpos(2), 127, 72, 44, 40, atk(11), atk(14), CENTRE, CENTRE, 1 << 3, 24, 0, 50),             # brass
    (R1, R1, R1, rpos(14), 127, 56, 28, 36, CENTRE, 40, CENTRE, 22, 2 << 3, 0, 0, 70),                      # electric piano
    (R1, R1, R1, rpos(2), 127, 72, 30, 30, CENTRE, 34, CENTRE, CENTRE, 3 << 3, 30, 0, 40),                  # bass
    (R1, R1, R1, rpos(3), 110, 52, 110, 30, CENTRE, 44, CENTRE, 28, 4 << 3, 0, 0, 64),                      # electric piano 2
    (rpos(0.5), R1, rpos(2), R1, 100, 100, 90, 40, atk(8), atk(8), atk(8), CENTRE, 5 << 3, 10, 0, 50),     # pad
    (R1, rpos(2), rpos(3), R1, 110, 80, 70, 40, 40, 40, 36, 34, 6 << 3, 0, 0, 40),                          # harpsichord
    (rpos(0.5), R1, rpos(2), rpos(3), 110, 127, 90, 70, CENTRE, CENTRE, CENTRE, CENTRE, 7 << 3, 0, 0, 30),  # organ (drawbars)
    (R1, R1, R1, R1, 127, 40, 0, 115, CENTRE, CENTRE, CENTRE, CENTRE, 8 << 3, 20, 0, 40),                   # kick: about 3 octaves of drop
    (R1, rpos(1.41), R1, R1, 110, 50, 0, 60, CENTRE, CENTRE, CENTRE, CENTRE, 9 << 3, 30, 90, 36),           # snare
    (R1, R1, R1, R1, 100, 90, 80, 70, CENTRE, CENTRE, CENTRE, CENTRE, 10 << 3, 60, 40, 20),                 # hat
    (R1, R1, R1, R1, 127, 40, 30, 70, CENTRE, CENTRE, CENTRE, CENTRE, 11 << 3, 0, 0, 48),                   # tom
    (R1, R1, R1, R1, 127, 70, 110, 60, CENTRE, CENTRE, CENTRE, CENTRE, 12 << 3, 0, 0, 100),                 # bell
    (R1, R1, R1, R1, 127, 64, 50, 127, CENTRE, CENTRE, CENTRE, CENTRE, 13 << 3, 0, 0, 110),                 # tubular
    (R1, R1, R1, R1, 120, 50, 120, 50, atk(22), atk(20), atk(22), atk(20), 14 << 3, 0, 0, 90),             # strings
    (R1, R1, R1, R1, 110, 110, 110, 40, atk(21), atk(21), atk(21), atk(18), 15 << 3, 0, 0, 90),             # ensemble
]
assert len(VOICINGS) == 16 and all(len(v) == 16 and max(v) <= 127 and v[P_ALG] == i << 3 for i, v in enumerate(VOICINGS))
# SC48 (use_starters): pad 7 held + pads 9-24 = 16 instrument starters (every FM parameter), coloured by family; left of the centre of Shift + K1-K4
# = the operator's decay index (tau 3 ms .. 8 s: 40 = 0.45 s, 50 = 1.6 s), right = atk(i)
STARTERS = [
    ("piano", (R1, R1, R1 + 1, rpos(3), 127, 70, 110, 52, 52, 44, 50, 30, 4 << 3, 0, 0, 50)),
    ("e-piano", (R1, R1, R1, rpos(14), 127, 56, 28, 36, 54, 40, CENTRE, 22, 2 << 3, 0, 0, 70)),
    ("organ", VOICINGS[7]),
    ("pluck", (R1, R1, rpos(3), R1, 127, 96, 34, 0, 42, 28, 24, CENTRE, 0, 0, 0, 30)),
    ("harp", (R1, rpos(2), R1, R1, 127, 34, 24, 0, 52, 38, 44, CENTRE, 3 << 3, 0, 0, 56)),
    ("marimba", (R1, rpos(4), rpos(4), R1, 127, 60, 40, 0, 38, 18, 28, CENTRE, 4 << 3, 0, 0, 30)),
    ("bass", VOICINGS[3]),
    ("bell", VOICINGS[12]),
    ("strings", VOICINGS[14]),
    ("pad", (rpos(0.5), R1 + 1, rpos(2), R1, 100, 100, 80, 36, atk(24), atk(24), atk(26), atk(26), 5 << 3, 8, 0, 100)),
    ("flute", (R1, R1, R1, R1, 127, 26, 0, 0, atk(16), atk(18), CENTRE, CENTRE, 0, 0, 22, 44)),
    ("clarinet", (R1, rpos(2), R1, R1, 127, 60, 0, 0, atk(14), atk(15), CENTRE, CENTRE, 0, 0, 4, 40)),
    ("brass", VOICINGS[1]),
    ("kick", VOICINGS[8]),
    ("snare", VOICINGS[9]),
    ("hat", VOICINGS[10]),
]
ST_FAM = {"keys": (0x01, 0x02), "plucked": (0x49, 0x4A), "bass": (0x2B, 0x2C), "bell": (0x4D, 0x4E), "strings": (0x17, 0x18),
          "winds": (0x13, 0x14), "drums": (0x45, 0x46)}
ST_OF = ("keys", "keys", "keys", "plucked", "plucked", "plucked", "bass", "bell", "strings", "strings", "winds", "winds", "winds", "drums", "drums", "drums")
assert len(STARTERS) == 16 and all(len(v) == 16 and max(v) <= 127 and v[P_ALG] % 8 == 0 for _, v in STARTERS)
assert len({v for _, v in STARTERS}) == 16                              # (the LED shows the starter whose values the track has)
STARTER = False                                                         # SC48 (use_starters)


def use_starters():
    """SC48 (the user, 2026-10-27: «los parches de FM de la fila superior suenan todos muy parecidos, reduce el número de sintes demasiado iguales y
    añade sonidos más de tipo "instrumento" como starters (piano, pluck, cuerdas, vientos)»): pad 7 held on the FM page = pads 9-24 show 16
    instrument starters (an algorithm alone changes only the routing: with the same knobs most sounded alike); then (the user: «añade los
    parches nuevos en otra página (pad 8) y deja en 7 algos por defecto») on their own pad: with FM on, pad 8 (free there: vcf21's page row
    swallows it) = tap: the FM page, held: pads 9-24 show the starters (B_P7 = 2; pad 7 held = 1, the algorithms as before); a press loads every FM
    parameter of that starter (as Clear + pad 7 loads a voicing) and plays the tonic while held (Shift: no sound).  Colours by family (keys
    white, plucked violet, bass blue, bell teal, strings / pad green, winds light blue, drums red); the starter whose values the track has now is
    bright.  Pad 8 dim white with FM on, bright while held."""
    global STARTER
    STARTER = True
BEXP = [round(256 * 2 ** ((i - 32) / 16)) for i in range(64)]           # the brightness: x 2^(2 w), w = 0.94 m of the oscillator's shape (OSC1 + 14)


def algs2():
    """ALGS with the velocity sensitivity and the keyboard scaling (bytes 6 / 7) and the kick's operator 4 releasing faster (the drop)"""
    out = bytearray()
    for i, x in enumerate(ALGS):
        b_ = bytearray(x["b"]); b_[A_VS] = VS[i]; b_[A_KS] = KS[i]
        if x["name"] == "kick": b_[A_ROF + 3] = (-10) & 0xFF
        out += b_
    return bytes(out)


def use_v2():
    """SC46.6 (the user, 2026-10-24 / 25: «Mejora el motor FM»; the study's plan and the answers): with vcf21_dsp's use_fmvca / fmwide / fmcompact /
    fmorder / fmsine / fmsmooth / fbavg (one builder):
      * fixes: the off -> on edge clears the envelopes and the DSP's states (the VCA is open now: nothing frozen may sound), the flag after the first
        values; R at ratio x 2^16 (full detune, up to 128 x the note); a note on and off between two ticks still plays (the gate forced on the new
        note's tick); the audition (vcf21.c_sdio: the tonic after a patch load, the step-drummer) goes through the FM's note-on; Clear + MIDI 1 / 2 =
        the FM back to the defaults and the matrix's amounts to 0 (destinations kept: modmx.use_zero); the DSP's flag written again every 64 ms;
      * sound: velocity -> the modulators' index and the kick's drop (a sensitivity per algorithm); the phases reset on a new note of the percussive
        and bell algorithms; the feedback squared (the same top) and halved for the DSP's average of the last two outputs; keyboard scaling (a
        factor per algorithm, the release one step shorter every 8 semitones above C4); no aliasing (an operator above 0.45 fs muted, a modulator's
        index capped to (I + 1) f < 0.45 fs, not in the percussive family); the oscillator's shape (SHAPE, Env -> shape, LFO -> shape, the matrix,
        the lanes: OSC1 + 14) = the brightness, x 0.27 .. x 3.7 on the modulators and the feedback; the engine's legato (retrigger off) does not
        restart the attacks;
      * the knobs: Shift + K1-K4 centre-zero: right = the attack (32 times, as before), left = the operator percussive, its own decay (the further
        left the shorter, 3 ms .. 8 s); the unused clicks of each ratio = a fine detune (+2.5 cents a click, LED half bright); Clear + pad 7 = the
        current algorithm's voicing, Clear + knob = its value there;
      * the pads: pad 7 held (on the FM page) = pads 9-24 show the 16 algorithms (their family's colour, the current one bright): a press chooses it
        and plays the tonic while held (Shift: no sound); while a ratio turns pads 9-32 show the 24 ratios (white = the current one detuned),
        while Shift + K5 turns pads 9-24 the algorithms, 1.5 s, the pads under them swallowed; Shift + a patch pad (9-24) loads it without the
        audition (psave's call of c_sdio wrapped).
    Patches: version 2 (an older beta loads it with FM off); a version 1 patch is converted: Shift + K1-K4 a -> 64 + a / 2, the feedback
    p -> sqrt(128 p) (the same coefficient), the ratios to the first click of theirs (exact)."""
    global V2
    assert VD.FMVCA and VD.FMWIDE and VD.FMCOMPACT and VD.FMORDER and VD.FMSINE and VD.FMSMOOTH and VD.FBAVG
    V2 = True


def umull(lo, hi, rn, rm): return h(0xFBA0 | rn) + h(lo << 12 | hi << 8 | rm)
def udiv(rd, rn, rm): return h(0xFBB0 | rn) + h(0xF0F0 | rd << 8 | rm)
def addh(rdn, rm): return h(0x4400 | (rdn >> 3) << 7 | rm << 3 | (rdn & 7))
def bics(rdn, rm): return h(0x4380 | rm << 3 | rdn)


def arm_code2(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_f{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    def now(rd): imm32(rd, V.HAL_TICK); E(ldr_imm, rd, rd, 0)
    def clamp24(r, tmp):                                                # r = min(r, 0x7FFFFF) (unsigned)
        zc[0] += 1; n = f"_c{zc[0]}"
        imm32(tmp, 0x7FFFFF); E(cmp_reg, r, tmp); E(b_cond, n, "ls"); E(mov_reg, r, tmp); a.label(n)
    def bit(rd, src, k_reg, tmp):                                       # rd = (src >> k) & 1 (Z = clear)
        E(lsrs_reg, src, k_reg); E(movs_imm, tmp, 1); E(ands_reg, src, tmp)

    # ---- data
    data = bytearray(); T = {}
    def put(name, bs):
        while len(data) % 4: data.append(0)
        T[name] = base + len(data); data.extend(bs)
    put("algs", algs2())
    put("rat", struct.pack("<24H", *[round(256 * r) for r in RATIOS]))
    put("rcol", bytes(rcol(r) for r in RATIOS))
    put("rcd", bytes(RDIM[rcol(r)] for r in RATIOS))
    put("astep", struct.pack("<32H", *ATK_STEP))
    put("relc", struct.pack("<64H", *REL_C))
    put("voic", bytes(v for row in VOICINGS for v in row))
    put("fam", bytes(x["fam"] for x in ALGS))
    put("famc", bytes(c for pair in FAMC for c in pair))
    put("pcol", bytes((0, 0, 0, 0, COL_LEV, COL_LEV, COL_LEV, COL_LEV, COL_ATK, COL_ATK, COL_ATK, COL_ATK, 0, COL_FB, COL_NZ, COL_REL)))
    put("bexp", struct.pack("<64H", *BEXP))
    if STARTER:
        put("strt", bytes(v for _, row in STARTERS for v in row))
        put("stc", bytes(c for f in ST_OF for c in ST_FAM[f]))
    while len(data) % 4: data.append(0)
    E(raw, bytes(data))

    # ---- c_fmst() -> r0 = FMR, set up at the first use (the voicing of the stack); clobbers r1-r3
    a.label("c_fmst")
    imm32(0, FMR); E(ldr_imm, 1, 0, 0); imm32(2, SIG2 if SIGV2 else SIG); E(cmp_reg, 1, 2); E(b_cond, "st_i", "ne"); E(raw, h(0x4770))
    a.label("st_i")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0)
    E(movs_imm, 1, 0); E(movs_imm, 3, (B0 + 2 * BS) // 4)
    a.label("st_z"); E(str_imm, 1, 0, 0); E(adds_imm8, 0, 4); E(subs_imm8, 3, 1); E(b_cond, "st_z", "ne")
    for t in (0, 1):
        E(mov_reg, 2, 4); E(adds_imm8, 2, B0 + BS * t); E(movs_imm, 3, 0)
        a.label(f"st_d{t}")
        imm32(1, T["voic"]); E(ldrb_reg, 1, 1, 3); E(strb_reg, 1, 2, 3)
        E(adds_imm8, 3, 1); E(cmp_imm, 3, 16); E(b_cond, f"st_d{t}", "lo")
        E(movs_imm, 1, 0xFF); E(strb_w, 1, 4, B0 + BS * t + B_SENT); E(movs_imm, 1, 100); E(strb_w, 1, 4, B0 + BS * t + B_VEL)
    imm32(1, SIG2 if SIGV2 else SIG); E(str_imm, 1, 4, 0); E(mov_reg, 0, 4)
    E(pop_list, [4, 5], pc=True)

    # ---- c_fmblk(r0 = track) -> r0 = its block; clobbers r1-r3
    a.label("c_fmblk")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, "c_fmst")
    E(lsls_imm, 1, 4, 6); E(adds_reg, 0, 0, 1); E(adds_imm8, 0, B0); E(pop_list, [4], pc=True)

    # ---- c_fmalg(r0 = block) -> r0 = its algorithm's entry; clobbers r1
    a.label("c_fmalg")
    E(ldrb_imm, 0, 0, P_ALG); E(lsrs_imm, 0, 0, 3); E(movs_imm, 1, ALEN); E(muls, 0, 1); imm32(1, T["algs"]); E(adds_reg, 0, 0, 1); E(raw, h(0x4770))

    # ---- c_fmact(r0 = track) -> r0 = 1 while FM sounds; clobbers r1-r3
    a.label("c_fmact")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0)
    E(bl, "c_fmblk"); E(mov_reg, 5, 0); E(ldrb_w, 0, 5, B_ON); E(cmp_imm, 0, 0); E(b_cond, "ac_0", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_von"]); E(cmp_imm, 0, 0); E(b_cond, "ac_off", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_msmode"]); E(cmp_imm, 0, 2); E(b_cond, "ac_off", "ne")
    E(movs_imm, 0, 1); E(pop_list, [4, 5], pc=True)
    a.label("ac_off"); E(movs_imm, 0, 0); E(strb_w, 0, 5, B_ON)
    a.label("ac_0"); E(movs_imm, 0, 0); E(pop_list, [4, 5], pc=True)

    # ---- c_fmw(r0 = DSP X address, r1 = value 24 bit): the DSP write (core 0); clobbers r0-r3
    a.label("c_fmw")
    if WCACHE and WC6:                                                                   # (WC6) the six voices' ranges
        R, _ = wc_ranges()
        E(push_list, [4, 5], lr=True)
        for i, (base, ln, mod, mask, i0) in enumerate(R):
            imm32(2, base); E(subs_reg, 3, 0, 2)
            if ln <= 255: E(cmp_imm, 3, ln)
            else: imm32(4, ln); E(cmp_reg, 3, 4)
            E(b_cond, "fw_r%d" % i, "lo")
        E(b, "fw_wr")
        for i, (base, ln, mod, mask, i0) in enumerate(R):
            a.label("fw_r%d" % i)
            E(movs_imm, 4, mod); E(raw, udiv(5, 3, 4)); E(muls, 5, 4); E(subs_reg, 5, 3, 5)                   # r5 = the word in its block
            if i0: imm32(4, i0); E(adds_reg, 3, 3, 4)
            imm32(4, mask); E(b, "fw_t")
        a.label("fw_t"); E(lsrs_reg, 4, 5); E(lsrs_imm, 4, 4, 1); E(b_cond, "fw_wr", "lo")                   # not an ARM-owned word: written
        E(lsls_imm, 4, 1, 8); E(lsrs_imm, 4, 4, 8); E(movs_imm, 5, 1); E(lsls_imm, 5, 5, 31); E(orrs_reg, 4, 5)   # the value | bit 31
        imm32(5, WC); E(lsls_imm, 3, 3, 2); E(adds_reg, 5, 5, 3); E(ldr_imm, 3, 5, 0); E(cmp_reg, 3, 4); E(b_cond, "fw_s", "eq"); E(str_imm, 4, 5, 0)
        a.label("fw_wr")
        E(mov_reg, 2, 0); E(lsls_imm, 1, 1, 8); E(movs_imm, 0, 0); E(raw, popw([4, 5], lr=True)); E(b_w, DSP_WRITE)
        a.label("fw_s"); E(pop_list, [4, 5], pc=True)
    elif WCACHE:                                                                          # (WCACHE) an ARM-owned word with that value already: skipped
        E(push_list, [4, 5], lr=True)
        imm32(2, VD.FV0); E(subs_reg, 3, 0, 2); E(cmp_imm, 3, 192); E(b_cond, "fw_f", "lo")
        imm32(2, VD.FMB0); E(subs_reg, 3, 0, 2); E(cmp_imm, 3, 96); E(b_cond, "fw_m", "lo")
        imm32(2, VD.PV_REC0); E(subs_reg, 3, 0, 2); E(cmp_imm, 3, 224); E(b_cond, "fw_wr", "hs")
        E(movs_imm, 4, VD.PV_RS); E(raw, udiv(5, 3, 4)); E(muls, 5, 4); E(subs_reg, 5, 3, 5)                  # r5 = the record's word
        E(adds_imm8, 3, 255); E(adds_imm8, 3, 288 - 255); imm32(4, REC_MASK); E(b, "fw_t")
        a.label("fw_m"); E(adds_imm8, 3, 192)
        a.label("fw_f")
        E(movs_imm, 4, VD.FMS); E(raw, udiv(5, 3, 4)); E(muls, 5, 4); E(subs_reg, 5, 3, 5); imm32(4, FV_MASK)   # r5 = the word in its operator block
        a.label("fw_t"); E(lsrs_reg, 4, 5); E(lsrs_imm, 4, 4, 1); E(b_cond, "fw_wr", "lo")                   # not an ARM-owned word: written
        E(lsls_imm, 4, 1, 8); E(lsrs_imm, 4, 4, 8); E(movs_imm, 5, 1); E(lsls_imm, 5, 5, 31); E(orrs_reg, 4, 5)   # the value | bit 31
        imm32(5, WC); E(lsls_imm, 3, 3, 2); E(adds_reg, 5, 5, 3); E(ldr_imm, 3, 5, 0); E(cmp_reg, 3, 4); E(b_cond, "fw_s", "eq"); E(str_imm, 4, 5, 0)
        a.label("fw_wr")
        E(mov_reg, 2, 0); E(lsls_imm, 1, 1, 8); E(movs_imm, 0, 0); E(raw, popw([4, 5], lr=True)); E(b_w, DSP_WRITE)
        a.label("fw_s"); E(pop_list, [4, 5], pc=True)
    else:
        E(mov_reg, 2, 0); E(lsls_imm, 1, 1, 8); E(movs_imm, 0, 0); E(b_w, DSP_WRITE)

    # ---- c_fmosc(r0 = track, r1 = word of the OSC1 block) -> r0 = its address; clobbers r1, r2
    a.label("c_fmosc")
    E(movs_imm, 2, 48); E(muls, 0, 2); imm32(2, VD.OSB0); E(adds_reg, 0, 0, 2); E(adds_reg, 0, 0, 1); E(raw, h(0x4770))

    # ---- c_fmlsq(r0 = level 0..127) -> r0 = level^2 x 4
    a.label("c_fmlsq")
    E(muls, 0, 0); E(lsls_imm, 0, 0, 2); E(raw, h(0x4770))

    # ---- c_fmenv(r4 = block, r5 = dt ms, r6 = the algorithm, r7 = gate): the four envelopes; clobbers r0-r3
    #      Shift + K_k = v: v >= 64 = attack (v - 64) >> 1 then the algorithm's sustain; v < 64 = attack 0, then a decay of index v while held
    #      (the release index if that is shorter when let go).  Indexes: + (velocity - 64) >> 3, - (note - 60) >> 3 with the keyboard scaling.
    a.label("c_fmenv")
    E(raw, pushw([4, 5, 6, 7, 8, 9, 10, 11], lr=True))
    E(ldrb_imm, 0, 4, B_VEL); E(subs_imm8, 0, 64); E(raw, asrs_imm(0, 0, 3))
    E(ldrb_imm, 1, 6, A_KS); E(cmp_imm, 1, 0); E(b_cond, "ev_k0", "eq")
    E(ldrb_w, 1, 4, B_NOTE); E(cmp_imm, 1, 60); E(b_cond, "ev_k0", "ls"); E(subs_imm8, 1, 60); E(lsrs_imm, 1, 1, 3); E(subs_reg, 0, 0, 1)
    a.label("ev_k0"); E(mov_reg, 11, 0)                                                 # r11 = the indexes' offset
    E(movs_imm, 0, 0); E(mov_reg, 8, 0)
    a.label("ev_l")
    E(mov_reg, 1, 8); E(lsls_imm, 2, 1, 1); E(adds_reg, 2, 2, 4); E(ldrh_imm, 0, 2, B_ENV); E(mov_reg, 9, 2)     # r0 = env, r9 = its address - B_ENV
    E(adds_reg, 2, 4, 1); E(ldrb_imm, 2, 2, P_ATK); E(mov_reg, 10, 2)                  # r10 = v
    E(cmp_imm, 7, 0); E(b_cond, "ev_rel", "eq")
    E(ldrb_imm, 2, 4, B_ATK); bit(2, 2, 1, 3); E(b_cond, "ev_hold", "eq")
    E(mov_reg, 2, 10); E(subs_imm8, 2, CENTRE); E(b_cond, "ev_a1", "ge"); E(movs_imm, 2, 0)
    a.label("ev_a1"); E(lsrs_imm, 2, 2, 1); E(lsls_imm, 2, 2, 1); imm32(3, T["astep"]); E(ldrh_reg, 2, 3, 2)
    E(muls, 2, 5); E(adds_reg, 0, 0, 2); imm32(2, 32767); E(cmp_reg, 0, 2); E(b_cond, "ev_st", "lt")
    E(mov_reg, 0, 2)
    E(ldrb_imm, 2, 4, B_ATK); E(movs_imm, 3, 1); E(lsls_reg, 3, 1); E(raw, bics(2, 3)); E(strb_imm, 2, 4, B_ATK)
    E(b, "ev_st")
    a.label("ev_hold")
    E(mov_reg, 2, 10); E(cmp_imm, 2, CENTRE); E(b_cond, "ev_dk", "lo")                  # the knob: percussive
    E(ldrb_imm, 2, 6, A_SUS); bit(2, 2, 1, 3); E(b_cond, "ev_st", "ne")                 # sustained: holds
    E(b, "ev_ri")
    a.label("ev_rel")
    E(ldrb_imm, 2, 4, B_ATK); E(movs_imm, 3, 1); E(lsls_reg, 3, 1); E(raw, bics(2, 3)); E(strb_imm, 2, 4, B_ATK)
    def ri(dst):                                                                         # dst = (rel >> 1) + the algorithm's offset + r11 (k = r8)
        E(ldrb_imm, dst, 4, P_REL); E(lsrs_imm, dst, dst, 1); E(mov_reg, 3, 11); E(adds_reg, dst, dst, 3)
        E(mov_reg, 1, 8); E(movs_imm, 3, A_ROF); E(adds_reg, 3, 3, 1); E(raw, ldrsb_reg(3, 6, 3)); E(adds_reg, dst, dst, 3)
    ri(2)
    E(mov_reg, 1, 10); E(cmp_imm, 1, CENTRE); E(b_cond, "ev_c", "hs")
    E(mov_reg, 3, 11); E(adds_reg, 1, 1, 3); E(cmp_reg, 1, 2); E(b_cond, "ev_c", "ge"); E(mov_reg, 2, 1); E(b, "ev_c")    # the shorter of the two
    a.label("ev_dk"); E(mov_reg, 3, 11); E(adds_reg, 2, 2, 3); E(b, "ev_c")
    a.label("ev_ri"); ri(2)
    a.label("ev_c")
    E(cmp_imm, 2, 0); E(b_cond, "ev_i1", "ge"); E(movs_imm, 2, 0)
    a.label("ev_i1"); E(cmp_imm, 2, 63); E(b_cond, "ev_i2", "le"); E(movs_imm, 2, 63)
    a.label("ev_i2"); E(lsls_imm, 2, 2, 1); imm32(3, T["relc"]); E(ldrh_reg, 2, 3, 2)
    E(mov_reg, 3, 5)
    a.label("ev_m"); E(muls, 0, 2); E(lsrs_imm, 0, 0, 16); E(subs_imm8, 3, 1); E(b_cond, "ev_m", "ne")
    a.label("ev_st"); E(mov_reg, 2, 9); E(strh_imm, 0, 2, B_ENV)
    E(mov_reg, 0, 8); E(adds_imm8, 0, 1); E(mov_reg, 8, 0); E(cmp_imm, 0, 4); bc("ev_l", "lo")
    E(raw, popw([4, 5, 6, 7, 8, 9, 10, 11], lr=True)); E(raw, h(0x4770))

    # ---- c_fmsend(r4 = block, r6 = the algorithm, r7 = track): R / AMP of the four operators, the noise, the feedback; with B_DIRTY (or every 64)
    #      K / M, the flag.  Frame: [sp] G (the modulators' factor x 256), [sp + 4] the voice's increment, [sp + 8] the feedback's half
    #      coefficient, [sp + 12] the velocity's factor, [sp + 16] the family
    a.label("c_fmsend")
    E(raw, pushw([4, 5, 6, 7, 8, 9, 10, 11], lr=True)); E(sub_sp_imm, 24)
    if POLY:                                                                             # (POLY) no poly context: cleared
        imm32(0, CTX); E(ldr_imm, 1, 0, 12); imm32(2, CTXSIG); E(cmp_reg, 1, 2); E(b_cond, "sd_cs", "eq")
        E(movs_imm, 1, 0); E(str_imm, 1, 0, 0); E(str_imm, 1, 0, 4); E(str_imm, 1, 0, 8); E(str_imm, 1, 0, 12)
        a.label("sd_cs")
    if POLY: imm32(0, CTX); E(ldr_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "sd_cb", "ne")                # (POLY) a voice's operator blocks
    E(movs_imm, 0, 48); E(muls, 0, 7); imm32(1, VD.FMB0); E(adds_reg, 0, 0, 1)
    if POLY: a.label("sd_cb")
    E(mov_reg, 11, 0)                                                                    # r11 = the FM blocks of the voice
    if WCACHE:                                                                            # (WCACHE) in poly's context: the shape read once a track a tick
        imm32(0, CTX); E(ldr_imm, 1, 0, 12); imm32(2, CTXSIG); E(cmp_reg, 1, 2); E(b_cond, "sd_r0", "ne")
        imm32(0, SHC); E(ldr_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "sd_r1", "ne")
        a.label("sd_r0")
    E(mov_reg, 0, 7); E(movs_imm, 1, 14); E(bl, "c_fmosc"); E(mov_reg, 1, 0); E(movs_imm, 0, 0); E(bl, DSP_READ)   # the shape (0.94 m) << 8
    if WCACHE:
        imm32(1, CTX); E(ldr_imm, 2, 1, 12); imm32(3, CTXSIG); E(cmp_reg, 2, 3); E(b_cond, "sd_r1", "ne"); imm32(1, SHC); E(str_imm, 0, 1, 0)
        a.label("sd_r1")
    E(raw, asrs_imm(0, 0, 26)); E(adds_imm8, 0, 32); E(lsls_imm, 0, 0, 1); imm32(1, T["bexp"]); E(ldrh_reg, 5, 1, 0)   # r5 = the brightness x 256
    if POLY: imm32(0, CTX); E(ldr_imm, 0, 0, 4); E(cmp_imm, 0, 0); E(b_cond, "sd_ci", "ne")                # (POLY) a voice's increment
    E(mov_reg, 0, 7); E(movs_imm, 1, 11); E(bl, "c_fmosc"); E(mov_reg, 1, 0); E(movs_imm, 0, 0); E(bl, DSP_READ)
    E(lsrs_imm, 0, 0, 8)
    if POLY: a.label("sd_ci")
    E(str_sp, 0, 4)                                                                      # the increment (2^24 = a cycle a sample)
    E(ldrb_w, 0, 4, B_VEL); E(cmp_imm, 0, 127); E(b_cond, "sv1", "ls"); E(movs_imm, 0, 127)
    a.label("sv1"); E(movs_imm, 1, 127); E(subs_reg, 1, 1, 0); E(ldrb_imm, 0, 6, A_VS); E(muls, 1, 0); E(lsrs_imm, 1, 1, 7)
    E(movs_imm, 0, 1); E(lsls_imm, 0, 0, 8); E(subs_reg, 0, 0, 1); E(str_sp, 0, 12)     # gv = 256 - s (127 - v) / 128
    E(ldrb_imm, 1, 6, A_KS); E(ldrb_w, 2, 4, B_NOTE); E(cmp_imm, 2, 60); E(b_cond, "sk0", "ls"); E(subs_imm8, 2, 60); E(muls, 2, 1); E(b, "sk1")
    a.label("sk0"); E(movs_imm, 2, 0)
    a.label("sk1"); E(movs_imm, 3, 1); E(lsls_imm, 3, 3, 8); E(subs_reg, 2, 3, 2); E(cmp_imm, 2, 32); E(b_cond, "sk2", "ge"); E(movs_imm, 2, 32)
    a.label("sk2"); E(muls, 2, 0); E(lsrs_imm, 2, 2, 8); E(muls, 2, 5); E(lsrs_imm, 2, 2, 8); E(str_sp, 2, 0)   # G = gv x ks x brightness
    E(ldrb_imm, 0, 4, P_FB); E(muls, 0, 0); E(muls, 0, 5); clamp24(0, 1); E(str_sp, 0, 8)              # half of P^2 x 512, x the brightness
    E(ldrb_imm, 0, 4, P_ALG); E(lsrs_imm, 0, 0, 3); imm32(1, T["fam"]); E(ldrb_reg, 0, 1, 0); E(str_sp, 0, 16)
    # the pitch factor pf (x 4096): 4096 + (env4 x lsq(lev4) >> 15) x 7 >> 4 x gv >> 8 with the algorithm's pitch flag
    imm32(5, 4096)
    E(ldrb_imm, 0, 6, A_FLG); E(movs_imm, 1, 1); E(ands_reg, 0, 1); E(cmp_imm, 0, 0); E(b_cond, "sd_np", "eq")
    E(ldrb_imm, 0, 4, P_LEV + 3); E(bl, "c_fmlsq"); E(ldrh_imm, 1, 4, B_ENV + 6); E(muls, 0, 1); E(lsrs_imm, 0, 0, 15); E(movs_imm, 1, 7); E(muls, 0, 1); E(lsrs_imm, 0, 0, 4)
    E(ldr_sp, 1, 12); E(muls, 0, 1); E(lsrs_imm, 0, 0, 8); E(adds_reg, 5, 5, 0)
    a.label("sd_np"); E(mov_reg, 10, 5)                                                 # r10 = pf
    E(movs_imm, 0, 0); E(mov_reg, 8, 0)                                                  # r8 = k
    a.label("sd_l")
    # R = ratio x det x (1 + 6 / 4096 x the fine step) x pf x 2^16, clamped
    E(mov_reg, 0, 8); E(adds_reg, 1, 4, 0); E(ldrb_imm, 1, 1, P_RAT); E(movs_imm, 2, 24); E(muls, 1, 2)
    E(movs_imm, 3, 127); E(ands_reg, 3, 1); E(lsrs_imm, 1, 1, 7); E(lsls_imm, 1, 1, 1)
    imm32(2, T["rat"]); E(ldrh_reg, 1, 2, 1)                                             # r1 = ratio x 256
    E(movs_imm, 2, 171); E(muls, 3, 2); E(lsrs_imm, 3, 3, 12); E(movs_imm, 2, 6); E(muls, 3, 2)
    E(movs_imm, 2, 1); E(lsls_imm, 2, 2, 12); E(adds_reg, 3, 3, 2)                       # r3 = 4096 + 6 x step
    E(lsls_imm, 2, 0, 1); E(adds_imm8, 2, A_DET); E(ldrh_reg, 2, 6, 2); E(muls, 2, 3); E(lsrs_imm, 2, 2, 12); E(muls, 1, 2)
    E(mov_reg, 2, 10); E(raw, umull(1, 3, 1, 2)); E(lsrs_imm, 1, 1, 16); E(lsls_imm, 3, 3, 16); E(orrs_reg, 1, 3)
    clamp24(1, 2); E(mov_reg, 9, 1)                                                      # r9 = R
    E(ldrb_w, 2, 4, B_PHR); E(mov_reg, 0, 8); bit(2, 2, 0, 3); E(b_cond, "sd_nr", "eq")  # a phase reset: PH = 0 just before R / AMP
    E(ldrb_w, 2, 4, B_PHR); E(movs_imm, 3, 1); E(lsls_reg, 3, 0); E(raw, bics(2, 3)); E(strb_w, 2, 4, B_PHR)
    E(movs_imm, 0, VD.FMS); E(mov_reg, 1, 8); E(muls, 0, 1); E(raw, addh(0, 11)); E(adds_imm8, 0, VD.F_PH); E(movs_imm, 1, 0); E(bl, "c_fmw")
    a.label("sd_nr")
    E(movs_imm, 0, VD.FMS); E(mov_reg, 1, 8); E(muls, 0, 1); E(raw, addh(0, 11)); E(adds_imm8, 0, VD.F_R); E(mov_reg, 1, 9); E(bl, "c_fmw")
    # AMP = env x lsq(level) >> 8 (operator 4 of a pitch algorithm: 0); a modulator x G; the aliasing limits
    E(mov_reg, 0, 8); E(cmp_imm, 0, 3); E(b_cond, "sd_a", "ne")
    E(ldrb_imm, 1, 6, A_FLG); E(movs_imm, 2, 1); E(ands_reg, 1, 2); E(cmp_imm, 1, 0); E(b_cond, "sd_a", "eq")
    E(movs_imm, 1, 0); E(b, "sd_aw")
    a.label("sd_a")
    E(adds_reg, 1, 4, 0); E(ldrb_imm, 0, 1, P_LEV); E(bl, "c_fmlsq")
    E(mov_reg, 1, 8); E(lsls_imm, 1, 1, 1); E(adds_reg, 1, 1, 4); E(ldrh_imm, 1, 1, B_ENV); E(muls, 1, 0); E(lsrs_imm, 1, 1, 8)
    E(ldrb_imm, 2, 6, A_CAR); E(mov_reg, 0, 8); bit(2, 2, 0, 3); E(b_cond, "sd_c", "ne")
    E(lsrs_imm, 1, 1, 2); E(ldr_sp, 2, 0); E(muls, 1, 2); E(lsrs_imm, 1, 1, 6); clamp24(1, 2)
    a.label("sd_c"); E(mov_reg, 5, 1)                                                     # r5 = AMP
    E(ldr_sp, 0, 4); E(mov_reg, 1, 9); E(raw, umull(0, 3, 0, 1)); E(lsrs_imm, 0, 0, 16); E(lsls_imm, 3, 3, 16); E(orrs_reg, 0, 3)   # f = inc x R
    imm32(1, NY); E(cmp_reg, 0, 1); E(b_cond, "sd_ny", "lo"); E(movs_imm, 5, 0); E(b, "sd_a2")
    a.label("sd_ny")
    E(ldrb_imm, 2, 6, A_CAR); E(mov_reg, 3, 8); E(lsrs_reg, 2, 3); E(movs_imm, 3, 1); E(ands_reg, 2, 3); E(b_cond, "sd_a2", "ne")   # a carrier
    E(ldr_sp, 2, 16); E(cmp_imm, 2, 1); E(b_cond, "sd_a2", "eq")                       # the percussive family
    E(lsrs_imm, 2, 0, 11); E(b_cond, "sd_a2", "eq")
    E(subs_reg, 1, 1, 0); E(lsrs_imm, 1, 1, 11); imm32(3, AACAP); E(muls, 1, 3); E(raw, udiv(1, 1, 2))   # cap = (NY - f) / (4 pi f) x 2^23
    E(cmp_reg, 5, 1); E(b_cond, "sd_a2", "ls"); E(mov_reg, 5, 1)
    a.label("sd_a2"); E(mov_reg, 1, 5)
    a.label("sd_aw")
    E(movs_imm, 0, VD.FMS); E(mov_reg, 2, 8); E(muls, 0, 2); E(raw, addh(0, 11)); E(adds_imm8, 0, VD.F_AMP); E(bl, "c_fmw")
    E(mov_reg, 0, 8); E(adds_imm8, 0, 1); E(mov_reg, 8, 0); E(cmp_imm, 0, 4); bc("sd_l", "lo")
    # the noise: (noise^2 x 4) x env(noise op) >> 9, at OSC1 + NZ_OFF
    E(ldrb_imm, 0, 4, P_NZ); E(bl, "c_fmlsq"); E(ldrb_imm, 1, 6, A_FLG); E(lsrs_imm, 1, 1, 4); E(lsls_imm, 1, 1, 1); E(adds_reg, 1, 1, 4)
    E(ldrh_imm, 1, 1, B_ENV); E(muls, 1, 0); E(lsrs_imm, 5, 1, 9)
    if POLY: imm32(0, CTX); E(ldr_imm, 0, 0, 8); E(cmp_imm, 0, 0); E(b_cond, "sd_cn", "ne")                # (POLY) a voice's record + 10
    E(mov_reg, 0, 7); E(movs_imm, 1, VD.NZ_OFF); E(bl, "c_fmosc")
    if POLY: a.label("sd_cn")
    E(mov_reg, 1, 5); E(bl, "c_fmw")
    # the feedback (every ms: the brightness moves it): M_kk and the half coefficient of y[n - 2] of the feedback operator
    E(ldrb_imm, 5, 6, A_FB); E(cmp_imm, 5, 3); E(b_cond, "sd_nf", "hi")
    E(movs_imm, 0, VD.FMS + 1); E(muls, 0, 5); E(raw, addh(0, 11)); E(adds_imm8, 0, VD.F_M); E(ldr_sp, 1, 8); E(bl, "c_fmw")
    E(movs_imm, 0, VD.FMS); E(muls, 0, 5); E(raw, addh(0, 11)); E(adds_imm8, 0, VD.F_HC); E(ldr_sp, 1, 8); E(bl, "c_fmw")
    a.label("sd_nf")
    # the routing: K, M1..M4 per operator when dirty or every 64; the others' half coefficient 0; the flag again
    E(ldrb_w, 0, 4, B_CNT); E(adds_imm8, 0, 1); E(strb_w, 0, 4, B_CNT); E(movs_imm, 1, 63); E(ands_reg, 0, 1); E(cmp_imm, 0, 0); E(b_cond, "sd_k", "eq")
    E(ldrb_w, 0, 4, B_DIRTY); E(cmp_imm, 0, 0); bc("sd_x", "eq")
    a.label("sd_k")
    E(movs_imm, 0, 0); E(strb_w, 0, 4, B_DIRTY)
    E(movs_imm, 0, 0); E(mov_reg, 8, 0)
    a.label("sd_kl")
    E(movs_imm, 1, 0); E(ldrb_imm, 2, 6, A_CAR); E(mov_reg, 0, 8); bit(2, 2, 0, 3); E(cmp_imm, 2, 0); E(b_cond, "sd_kw", "eq")
    E(ldr_imm, 1, 6, A_KW)
    a.label("sd_kw")
    E(movs_imm, 0, VD.FMS); E(mov_reg, 2, 8); E(muls, 0, 2); E(raw, addh(0, 11)); E(adds_imm8, 0, VD.F_K); E(bl, "c_fmw")
    E(movs_imm, 0, 0); E(mov_reg, 9, 0)                                                  # r9 = j
    a.label("sd_ml")
    E(mov_reg, 0, 8); E(lsls_imm, 0, 0, 2); E(mov_reg, 1, 9); E(adds_reg, 0, 0, 1)
    E(ldrh_imm, 2, 6, A_MASK); E(lsrs_reg, 2, 0); E(movs_imm, 3, 1); E(ands_reg, 2, 3); E(movs_imm, 1, 0); E(cmp_imm, 2, 0); E(b_cond, "sd_mw", "eq")
    E(mov_reg, 0, 8); E(mov_reg, 1, 9); E(cmp_reg, 0, 1)
    imm32(1, 0x7FFFFF); E(b_cond, "sd_mw", "ne")
    E(ldr_sp, 1, 8)                                                                      # the diagonal = the feedback's half coefficient
    a.label("sd_mw")
    E(movs_imm, 0, VD.FMS); E(mov_reg, 2, 8); E(muls, 0, 2); E(raw, addh(0, 11)); E(mov_reg, 2, 9); E(adds_reg, 0, 0, 2); E(adds_imm8, 0, VD.F_M)
    E(bl, "c_fmw")
    E(mov_reg, 0, 9); E(adds_imm8, 0, 1); E(mov_reg, 9, 0); E(cmp_imm, 0, 4); E(b_cond, "sd_ml", "lo")
    E(ldrb_imm, 0, 6, A_FB); E(mov_reg, 1, 8); E(cmp_reg, 0, 1); E(b_cond, "sd_hn", "eq")    # not the feedback operator: no y[n - 2]
    E(movs_imm, 0, VD.FMS); E(muls, 0, 1); E(raw, addh(0, 11)); E(adds_imm8, 0, VD.F_HC); E(movs_imm, 1, 0); E(bl, "c_fmw")
    a.label("sd_hn")
    E(mov_reg, 0, 8); E(adds_imm8, 0, 1); E(mov_reg, 8, 0); E(cmp_imm, 0, 4); bc("sd_kl", "lo")
    E(mov_reg, 0, 7); E(movs_imm, 1, VD.FM_FLAG); E(bl, "c_fmosc"); E(movs_imm, 1, 1); E(bl, "c_fmw")   # the flag again (the DSP's boot clears it)
    a.label("sd_x")
    E(add_sp_imm, 24); E(raw, popw([4, 5, 6, 7, 8, 9, 10, 11], lr=True)); E(raw, h(0x4770))

    # ---- c_fmflag(r0 = track, r1 = 0 / 1): the OSC1 block's flag word, when it changes (B_SENT); clobbers r0-r3
    a.label("c_fmflag")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_fmblk"); E(mov_reg, 6, 0); E(ldrb_w, 0, 6, B_SENT); E(cmp_reg, 0, 5); E(b_cond, "fl_x", "eq")
    E(strb_w, 5, 6, B_SENT); E(movs_imm, 0, 1); E(strb_w, 0, 6, B_DIRTY)
    E(mov_reg, 0, 4); E(movs_imm, 1, VD.FM_FLAG); E(bl, "c_fmosc"); E(mov_reg, 1, 5); E(bl, "c_fmw")
    a.label("fl_x"); E(pop_list, [4, 5, 6], pc=True)

    if WCACHE:
        # ---- c_fmref(): one cached word written again (a tick; the 512 in 0.5 s): the DSP's copy never stays stale; clobbers r0-r3
        a.label("c_fmref")
        if WC6:                                                                           # (WC6) the 720 words
            R, WN = wc_ranges()
            E(push_list, [4], lr=True)
            imm32(4, WCX); E(ldr_imm, 0, 4, 4); imm32(1, WCSIG); E(cmp_reg, 0, 1); E(b_cond, "rf_ok", "eq")
            E(str_imm, 1, 4, 4); imm32(2, WC); E(movs_imm, 0, 0); imm32(3, WN)                                # the cache zeroed at the first use
            a.label("rf_z"); E(str_imm, 0, 2, 0); E(adds_imm8, 2, 4); E(subs_imm8, 3, 1); E(b_cond, "rf_z", "ne"); E(str_imm, 0, 4, 0)
            a.label("rf_ok")
            E(ldr_imm, 0, 4, 0); E(adds_imm8, 0, 1); imm32(1, WN); E(cmp_reg, 0, 1); E(b_cond, "rf_w", "lo"); E(movs_imm, 0, 0)
            a.label("rf_w"); E(str_imm, 0, 4, 0)
            imm32(2, WC); E(lsls_imm, 1, 0, 2); E(raw, ldr_reg(1, 2, 1)); E(cmp_imm, 1, 0); E(b_cond, "rf_x", "ge")   # bit 31: a value cached
            for i, (base, ln, mod, mask, i0) in enumerate(R):
                imm32(3, i0 + ln); E(cmp_reg, 0, 3); E(b_cond, "rf_%d" % i, "lo")
            E(b, "rf_x")
            for i, (base, ln, mod, mask, i0) in enumerate(R):
                a.label("rf_%d" % i); imm32(2, base - i0); E(b, "rf_a")
            a.label("rf_a"); E(adds_reg, 2, 2, 0); E(lsls_imm, 1, 1, 8); E(movs_imm, 0, 0); E(bl, DSP_WRITE)
            a.label("rf_x"); E(pop_list, [4], pc=True)
    if WCACHE and not WC6:                                                               # (the 512 words)
        E(push_list, [4], lr=True)
        imm32(4, WCX); E(ldr_imm, 0, 4, 4); imm32(1, WCSIG); E(cmp_reg, 0, 1); E(b_cond, "rf_ok", "eq")
        E(str_imm, 1, 4, 4); imm32(2, WC); E(movs_imm, 0, 0); E(movs_imm, 3, 1); E(lsls_imm, 3, 3, 9)          # the cache zeroed at the first use
        a.label("rf_z"); E(str_imm, 0, 2, 0); E(adds_imm8, 2, 4); E(subs_imm8, 3, 1); E(b_cond, "rf_z", "ne"); E(str_imm, 0, 4, 0)
        a.label("rf_ok")
        E(ldr_imm, 0, 4, 0); E(adds_imm8, 0, 1); imm32(1, 511); E(ands_reg, 0, 1); E(str_imm, 0, 4, 0)
        imm32(2, WC); E(lsls_imm, 1, 0, 2); E(raw, ldr_reg(1, 2, 1)); E(cmp_imm, 1, 0); E(b_cond, "rf_x", "ge")   # bit 31: a value cached
        imm32(2, VD.FV0); E(cmp_imm, 0, 192); E(b_cond, "rf_a", "lo")
        E(subs_imm8, 0, 192); imm32(2, VD.FMB0); E(cmp_imm, 0, 96); E(b_cond, "rf_a", "lo")
        E(subs_imm8, 0, 96); imm32(2, VD.PV_REC0)
        a.label("rf_a"); E(adds_reg, 2, 2, 0); E(lsls_imm, 1, 1, 8); E(movs_imm, 0, 0); E(bl, DSP_WRITE)
        a.label("rf_x"); E(pop_list, [4], pc=True)

    # ---- c_fmtick: the head of the DSP service chain (the tick holds the DSP semaphore: RAM and DSP writes / reads only, no MARK_DIRTY)
    a.label("c_fmtick")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7, 8], lr=True))
    if WCACHE: E(bl, "c_fmref")
    E(movs_imm, 7, 0)
    a.label("tk_l")
    E(mov_reg, 0, 7); E(bl, "c_fmact"); E(cmp_imm, 0, 0); E(b_cond, "tk_on", "ne")
    E(mov_reg, 0, 7); E(movs_imm, 1, 0); E(bl, "c_fmflag")
    E(mov_reg, 0, 7); E(bl, "c_fmblk"); E(movs_imm, 1, 0); E(strb_w, 1, 0, B_P7)
    E(mov_reg, 0, 7); E(bl, L["c_vpage"]); E(cmp_imm, 0, PAGE); bc("tk_n", "ne")          # the FM page without FM: back to OSC 1
    E(mov_reg, 0, 7); E(movs_imm, 1, 1); E(bl, L["c_vsetpage"]); E(b, "tk_n")
    a.label("tk_on")
    E(mov_reg, 0, 7); E(bl, "c_fmblk"); E(mov_reg, 4, 0)
    E(ldrb_w, 0, 4, B_SENT); E(cmp_imm, 0, 1); E(b_cond, "tk_e", "eq")
    # off -> on: the envelopes and attacks cleared, the routing sent again, the DSP's smoothed AMP and y[n - 2] of each operator 0
    E(movs_imm, 0, 0); E(str_imm, 0, 4, B_ENV); E(str_imm, 0, 4, B_ENV + 4); E(strb_imm, 0, 4, B_ATK); E(movs_imm, 0, 1); E(strb_w, 0, 4, B_DIRTY)
    E(movs_imm, 5, 0)
    a.label("tk_el")
    E(movs_imm, 0, 48); E(muls, 0, 7); E(movs_imm, 1, VD.FMS); E(muls, 1, 5); E(adds_reg, 0, 0, 1); imm32(1, VD.FMB0 + VD.F_AS); E(adds_reg, 0, 0, 1)
    E(mov_reg, 6, 0); E(movs_imm, 1, 0); E(bl, "c_fmw"); E(mov_reg, 0, 6); E(adds_imm8, 0, VD.F_O2 - VD.F_AS); E(movs_imm, 1, 0); E(bl, "c_fmw")
    E(adds_imm8, 5, 1); E(cmp_imm, 5, 4); E(b_cond, "tk_el", "lo")
    a.label("tk_e")
    now(0); E(ldr_imm, 1, 4, B_LAST); E(subs_reg, 5, 0, 1); bc("tk_n", "eq"); E(str_imm, 0, 4, B_LAST)
    E(cmp_imm, 5, 50); E(b_cond, "tk_dt", "ls"); E(movs_imm, 5, 50)
    a.label("tk_dt")
    if POLY:                                                                             # (POLY) the track in poly: its voices are poly's (the flag still)
        import poly as PL
        imm32(0, PL.PY); E(ldr_imm, 1, 0, 0); imm32(2, PL.SIG); E(cmp_reg, 1, 2); E(b_cond, "tk_np", "ne")             # (poly's RAM signed)
        E(adds_imm8, 0, 4 + PL.O_ACT); E(lsls_imm, 1, 7, PL.TBS.bit_length() - 1); E(ldrb_reg, 0, 0, 1); E(cmp_imm, 0, 0); E(b_cond, "tk_np", "eq")
        E(mov_reg, 0, 7); E(movs_imm, 1, 1); E(bl, "c_fmflag"); E(b, "tk_n")
        a.label("tk_np")
    E(mov_reg, 0, 4); E(bl, "c_fmalg"); E(mov_reg, 6, 0)
    E(movs_imm, 0, 0); E(mov_reg, 8, 0)                                                 # r8 = 1: a new note this tick (the gate forced on)
    E(ldrb_w, 0, 4, B_NEW); E(cmp_imm, 0, 0); E(b_cond, "tk_g", "eq")
    E(movs_imm, 0, 0); E(strb_w, 0, 4, B_NEW); E(movs_imm, 0, 15); E(strb_imm, 0, 4, B_ATK); E(movs_imm, 0, 1); E(mov_reg, 8, 0)
    E(ldrb_imm, 0, 6, A_SUS); E(cmp_imm, 0, 0); E(b_cond, "tk_pz", "ne"); E(movs_imm, 0, 15); E(strb_w, 0, 4, B_PHR)   # percussive and bells: the phases from 0
    a.label("tk_pz")
    E(movs_imm, 1, 0)
    a.label("tk_z")                                                                     # the percussive operators (the algorithm's or the knob's) from 0
    E(adds_reg, 0, 4, 1); E(ldrb_imm, 0, 0, P_ATK); E(cmp_imm, 0, CENTRE); E(b_cond, "tk_zz", "lo")
    E(ldrb_imm, 0, 6, A_SUS); E(lsrs_reg, 0, 1); E(movs_imm, 2, 1); E(ands_reg, 0, 2); E(cmp_imm, 0, 0); E(b_cond, "tk_zn", "ne")
    a.label("tk_zz"); E(lsls_imm, 0, 1, 1); E(adds_reg, 0, 0, 4); E(movs_imm, 2, 0); E(strh_imm, 2, 0, B_ENV)
    a.label("tk_zn"); E(adds_imm8, 1, 1); E(cmp_imm, 1, 4); E(b_cond, "tk_z", "lo")
    a.label("tk_g")                                                                     # the gate: the engine's held notes (or a new note)
    E(movs_imm, 0, 1); E(mov_reg, 1, 8); E(cmp_imm, 1, 0); E(b_cond, "tk_gs", "ne")
    imm32(0, V.TAIL + V.O_RT + V.RT_CNT); E(lsls_imm, 1, 7, 3); E(ldrb_reg, 0, 0, 1); E(movs_imm, 1, 15); E(ands_reg, 0, 1)
    a.label("tk_gs")
    E(push_list, [7]); E(mov_reg, 7, 0); E(bl, "c_fmenv"); E(pop_list, [7])
    E(bl, "c_fmsend")
    E(mov_reg, 0, 7); E(movs_imm, 1, 1); E(bl, "c_fmflag")                              # the flag after the first values
    a.label("tk_n"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 2); bc("tk_l", "lo")
    E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7, 8], lr=True)); E(b_w, prev["svc"])

    # ---- c_fmnon (the note vtable's slot: this, track id, note, velocity): a new note (legato with the retrigger off: none), its velocity, its note
    a.label("c_fmnon")
    E(raw, pushw([0, 1, 2, 3, 4, 5], lr=True))
    E(mov_reg, 4, 1); E(subs_imm8, 4, 2); E(cmp_imm, 4, 1); bc("nn_x", "hi")
    E(cmp_imm, 3, 0); bc("nn_x", "eq"); E(mov_reg, 5, 3)
    E(mov_reg, 0, 4); E(bl, L["c_rtoff"]); E(cmp_imm, 0, 0); E(b_cond, "nn_n", "eq")
    imm32(0, V.TAIL + V.O_RT); E(lsls_imm, 1, 4, 3); E(adds_reg, 0, 0, 1)
    E(ldrb_imm, 1, 0, V.RT_CNT); E(lsls_imm, 1, 1, 28); E(b_cond, "nn_n", "eq")          # no note held: a new note
    E(ldrb_imm, 1, 0, V.RT_VEL); E(lsls_imm, 1, 1, 24); E(b_cond, "nn_n", "mi")          # two oscillators: a new note
    E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(ldr_sp, 1, 8); E(strb_w, 1, 0, B_NOTE); E(b, "nn_x")
    a.label("nn_n")
    E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(strb_w, 5, 0, B_VEL); E(movs_imm, 1, 1); E(strb_w, 1, 0, B_NEW); E(ldr_sp, 1, 8); E(strb_w, 1, 0, B_NOTE)
    a.label("nn_x")
    E(raw, popw([0, 1, 2, 3, 4, 5], lr=True)); E(b_w, prev["non"])

    # ---- c_fmpg(r0 = track) -> r0 = 1 when the FM page is the one the knobs move
    a.label("c_fmpg")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(bl, "c_fmact"); E(cmp_imm, 0, 0); E(b_cond, "pg_0", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_edact"]); E(cmp_imm, 0, 0); E(b_cond, "pg_0", "ne")
    E(mov_reg, 0, 4); E(bl, L["c_sdview"]); E(cmp_imm, 0, 0); E(b_cond, "pg_0", "ne")
    E(mov_reg, 0, 4); E(bl, L["c_vpage"]); E(cmp_imm, 0, PAGE); E(b_cond, "pg_0", "ne")
    E(movs_imm, 0, 1); E(pop_list, [4], pc=True)
    a.label("pg_0"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_fmpar(r0 = knob 0..7) -> r0 = the parameter index (with Shift: + 8); clobbers r1-r3
    a.label("c_fmpar")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(mov_reg, 0, 4); E(b_cond, "pa_x", "eq"); E(adds_imm8, 0, 8)
    a.label("pa_x"); E(pop_list, [4], pc=True)

    # ---- c_fmvoc(r0 = block, r1 = parameter) -> r0 = its value in the voicing of the block's algorithm; clobbers r2
    a.label("c_fmvoc")
    E(ldrb_imm, 0, 0, P_ALG); E(lsrs_imm, 0, 0, 3); E(lsls_imm, 0, 0, 4); E(adds_reg, 0, 0, 1); imm32(2, T["voic"]); E(ldrb_reg, 0, 2, 0); E(raw, h(0x4770))

    # ---- c_fmovl(r0 = block, r1 = kind 1..5): the overlay (a ratio of operator kind, 5 the algorithm) from now; clobbers r1-r3
    a.label("c_fmovl")
    E(strb_w, 1, 0, B_OVK); now(1); E(str_imm, 1, 0, B_OVT); E(raw, h(0x4770))

    # ---- c_fmovk(r0 = block) -> r0 = the overlay's kind while it is shown, else 0; clobbers r1-r3
    a.label("c_fmovk")
    E(ldrb_w, 1, 0, B_OVK); E(cmp_imm, 1, 0); E(b_cond, "ok_0", "eq")
    E(ldr_imm, 2, 0, B_OVT); now(3); E(subs_reg, 3, 3, 2); imm32(2, OVL_MS); E(cmp_reg, 3, 2); E(b_cond, "ok_0", "hs")
    E(mov_reg, 0, 1); E(raw, h(0x4770))
    a.label("ok_0"); E(movs_imm, 0, 0); E(raw, h(0x4770))

    # ---- c_fmknob (slot 4 of the macro handlers: obj, knob, delta): the FM page of MIDI 1 / 2, else the previous slot
    a.label("c_fmknob")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(bl, L["c_vtrack"]); E(cmp_imm, 0, 1); bc("kn_prev", "hi"); E(mov_reg, 6, 0)
    E(bl, "c_fmpg"); E(cmp_imm, 0, 0); bc("kn_prev", "eq")
    E(ldr_sp, 0, 4); E(movs_imm, 1, 7); E(ands_reg, 0, 1); E(bl, "c_fmpar"); E(mov_reg, 5, 0)      # r5 = the parameter
    E(mov_reg, 0, 6); E(bl, "c_fmblk"); E(mov_reg, 4, 0)
    E(ldr_sp, 0, 0); E(bl, L["c_vclr"]); E(cmp_imm, 0, 0); E(b_cond, "kn_add", "eq")
    E(movs_imm, 0, 0); E(cmp_imm, 5, P_ALG); E(b_cond, "kn_st", "eq")                    # Clear: the algorithm = the stack, the rest = the voicing's
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_fmvoc"); E(b, "kn_st")
    a.label("kn_add")
    E(ldrb_reg, 0, 4, 5); E(ldr_sp, 2, 8); E(adds_reg, 0, 0, 2)
    E(cmp_imm, 0, 0); E(b_cond, "kn_c1", "ge"); E(movs_imm, 0, 0)
    a.label("kn_c1"); E(cmp_imm, 0, 127); E(b_cond, "kn_st", "le"); E(movs_imm, 0, 127)
    a.label("kn_st"); E(strb_reg, 0, 4, 5); E(movs_imm, 0, 1); E(strb_w, 0, 4, B_DIRTY)
    E(cmp_imm, 5, 4); E(b_cond, "kn_o1", "hs"); E(mov_reg, 0, 4); E(adds_imm8, 5, 1); E(mov_reg, 1, 5); E(bl, "c_fmovl"); E(b, "kn_x")   # a ratio: its overlay
    a.label("kn_o1"); E(cmp_imm, 5, P_ALG); E(b_cond, "kn_x", "ne"); E(mov_reg, 0, 4); E(movs_imm, 1, 5); E(bl, "c_fmovl")
    a.label("kn_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("kn_prev"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["knob"])

    # ---- c_fmrstep(r0 = ratio knob position) -> r0 = the ratio's index, r1 = the fine step (0 = exact); clobbers r2
    a.label("c_fmrstep")
    E(movs_imm, 2, 24); E(muls, 0, 2); E(movs_imm, 1, 127); E(ands_reg, 1, 0); E(lsrs_imm, 0, 0, 7)
    E(movs_imm, 2, 171); E(muls, 1, 2); E(lsrs_imm, 1, 1, 12); E(raw, h(0x4770))

    # ---- c_fmkleds (slot 7 of the macro handlers: obj) -> r0 = the knob LED buffer: on the FM page the eight parameters (or, with Shift, the other eight)
    a.label("c_fmkleds")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(bl, prev["kleds"]); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(bl, L["c_vtrack"]); E(cmp_imm, 0, 1); bc("kl_x", "hi"); E(mov_reg, 6, 0)
    E(bl, "c_fmpg"); E(cmp_imm, 0, 0); bc("kl_x", "eq")
    E(mov_reg, 0, 6); E(bl, "c_fmblk"); E(mov_reg, 4, 0)
    E(movs_imm, 6, 0)
    a.label("kl_l")
    E(mov_reg, 0, 6); E(bl, "c_fmpar"); E(mov_reg, 7, 0); E(ldrb_reg, 0, 4, 7)            # r7 = the parameter, r0 = its value
    E(cmp_imm, 7, 4); E(b_cond, "kl_nr", "hs")                                            # a ratio: its class's colour, brighter the higher, half when detuned
    E(bl, "c_fmrstep"); E(mov_reg, 3, 1); imm32(1, T["rcol"]); E(ldrb_reg, 1, 1, 0); E(lsls_imm, 0, 0, 2); E(adds_imm8, 0, 30)
    E(cmp_imm, 3, 0); E(b_cond, "kl_put", "eq"); E(lsrs_imm, 0, 0, 1); E(b, "kl_put")
    a.label("kl_nr")
    E(cmp_imm, 7, P_ATK); E(b_cond, "kl_na0", "lo"); E(cmp_imm, 7, P_ATK + 4); E(b_cond, "kl_na0", "hs")   # Shift + K1-K4: right light blue, left red, the distance from the centre
    E(movs_imm, 1, COL_ATK); E(subs_imm8, 0, CENTRE); E(b_cond, "kl_ab", "ge"); E(movs_imm, 1, COL_PERC); E(raw, h(0x4240))   # rsbs r0, r0, #0
    a.label("kl_ab"); E(lsls_imm, 0, 0, 1); E(cmp_imm, 0, 127); E(b_cond, "kl_put", "le"); E(movs_imm, 0, 127); E(b, "kl_put")
    a.label("kl_na0")
    E(cmp_imm, 7, P_ALG); E(b_cond, "kl_na", "ne")                                        # the algorithm: its family's colour, brighter along the family
    E(lsrs_imm, 0, 0, 3); imm32(1, T["fam"]); E(ldrb_reg, 2, 1, 0); imm32(1, FAM_COL[0] | FAM_COL[1] << 8 | FAM_COL[2] << 16 | FAM_COL[3] << 24)
    E(lsls_imm, 3, 2, 3); E(lsrs_reg, 1, 3); E(movs_imm, 3, 0xFF); E(ands_reg, 1, 3)
    E(movs_imm, 3, 3); E(ands_reg, 0, 3); E(lsls_imm, 0, 0, 5); E(adds_imm8, 0, 30); E(b, "kl_put")
    a.label("kl_na")
    imm32(1, T["pcol"]); E(ldrb_reg, 1, 1, 7)
    a.label("kl_put")
    E(adds_imm8, 0, 2); E(lsls_imm, 0, 0, 8); E(orrs_reg, 0, 1); E(lsls_imm, 1, 6, 1); E(strh_reg, 0, 5, 1)
    E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); bc("kl_l", "lo")
    a.label("kl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_fmdefs(r0 = track, r1 = 0: the voicing of its algorithm / 1: the stack's): every FM parameter; clobbers r0-r3
    a.label("c_fmdefs")
    E(push_list, [4, 5], lr=True); E(mov_reg, 5, 1); E(bl, "c_fmblk"); E(mov_reg, 4, 0)
    E(ldrb_imm, 0, 4, P_ALG); E(lsrs_imm, 0, 0, 3); E(lsls_imm, 0, 0, 4); E(cmp_imm, 5, 0); E(b_cond, "df_r", "eq"); E(movs_imm, 0, 0)
    a.label("df_r"); imm32(1, T["voic"]); E(adds_reg, 1, 1, 0); E(movs_imm, 3, 0)
    a.label("df_l"); E(ldrb_reg, 2, 1, 3); E(strb_reg, 2, 4, 3); E(adds_imm8, 3, 1); E(cmp_imm, 3, 16); E(b_cond, "df_l", "lo")
    E(movs_imm, 0, 1); E(strb_w, 0, 4, B_DIRTY); E(pop_list, [4, 5], pc=True)

    # ---- c_fmvrst(r0 = track): Clear + MIDI 1 / 2 (psave's c_psbtn): vcf21's initial values, the FM's (the stack), the matrix's amounts 0
    a.label("c_fmvrst")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(bl, L["c_vreset"]); E(mov_reg, 0, 4); E(movs_imm, 1, 1); E(bl, "c_fmdefs")
    if "c_mxzero" in L: E(mov_reg, 0, 4); E(bl, L["c_mxzero"])
    E(pop_list, [4], pc=True)

    # ---- c_fmrow(r0 = track) -> r0 = 1 while modesel's mode row is open for it; clobbers r1
    a.label("c_fmrow")
    imm32(1, MS.RAM); E(ldrb_imm, 1, 1, 0); E(adds_imm8, 0, 1); E(cmp_reg, 1, 0); E(b_cond, "rw_1", "eq")
    E(movs_imm, 0, 0); E(raw, h(0x4770))
    a.label("rw_1"); E(movs_imm, 0, 1); E(raw, h(0x4770))

    # ---- c_fmaud(r0 = track): the tonic while the pad is held (psave's audition: its state, ended by any release or button); not with Shift
    a.label("c_fmaud")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0)
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "au_x", "ne")
    E(bl, L["c_psaoff"]); E(bl, L["c_sdtonic"]); E(mov_reg, 5, 0)
    E(bl, L["c_psst"]); E(cmp_imm, 0, 0); E(b_cond, "au_x", "eq")
    E(movs_imm, 1, 0x80); E(orrs_reg, 1, 5); E(strb_imm, 1, 0, 6); E(strb_imm, 4, 0, 7)
    E(mov_reg, 0, 4); E(movs_imm, 1, 1); E(movs_imm, 2, 100); E(mov_reg, 3, 5); E(bl, L["c_sdio"])
    a.label("au_x"); E(pop_list, [4, 5], pc=True)

    # ---- c_fmpad (slot 0 of the template view: view, pad, velocity): pad 7 = the FM page (held: the algorithms on pads 9-24; Clear: the voicing);
    #      under pad 7 / an overlay the pads are ours; pad 24 of the mode row = FM; the row's other modes = FM off
    a.label("c_fmpad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1)
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); bc("pd_prev", "hi"); E(mov_reg, 4, 0)            # r4 = the track
    if STARTER:                                                                             # pad 8: the FM page, held = the starters
        E(cmp_imm, 5, PADNO + 1); E(b_cond, "pd_n8", "ne")
        E(mov_reg, 0, 4); E(bl, "c_fmact"); E(cmp_imm, 0, 0); bc("pd_prev", "eq")
        E(mov_reg, 0, 4); E(bl, L["c_edact"]); E(cmp_imm, 0, 0); bc("pd_prev", "ne")
        E(mov_reg, 0, 4); E(movs_imm, 1, PAGE); E(bl, L["c_vsetpage"])
        E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(movs_imm, 1, 2); E(strb_w, 1, 0, B_P7); E(b, "pd_x")
        a.label("pd_n8")
    E(cmp_imm, 5, PADNO); bc("pd_n7", "ne")
    E(mov_reg, 0, 4); E(bl, "c_fmact"); E(cmp_imm, 0, 0); bc("pd_prev", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_edact"]); E(cmp_imm, 0, 0); bc("pd_prev", "ne")
    E(bl, L["c_mxclrh"]); E(cmp_imm, 0, 0); E(b_cond, "pd_pg", "eq")
    E(mov_reg, 0, 4); E(movs_imm, 1, 0); E(bl, "c_fmdefs"); E(b, "pd_x")                    # Clear + pad 7: the algorithm's voicing
    a.label("pd_pg"); E(mov_reg, 0, 4); E(movs_imm, 1, PAGE); E(bl, L["c_vsetpage"])
    E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(movs_imm, 1, 1); E(strb_w, 1, 0, B_P7); E(b, "pd_x")
    a.label("pd_n7")
    E(cmp_imm, 5, 8); bc("pd_row", "lo"); E(cmp_imm, 5, 31); bc("pd_row", "hi")
    E(mov_reg, 0, 4); E(bl, "c_fmpg"); E(cmp_imm, 0, 0); bc("pd_row", "eq")
    E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(mov_reg, 6, 0)
    E(ldrb_w, 0, 6, B_P7); E(cmp_imm, 0, 0); E(b_cond, "pd_ov", "eq")
    E(cmp_imm, 5, 23); bc("pd_row", "hi")
    if STARTER:                                                                             # pad 8 + pad: the starter's every parameter
        E(cmp_imm, 0, 2); E(b_cond, "pd_alg", "ne")
        E(mov_reg, 0, 5); E(subs_imm8, 0, 8); E(lsls_imm, 0, 0, 4); imm32(1, T["strt"]); E(adds_reg, 1, 1, 0); E(movs_imm, 3, 0)
        a.label("pd_sl"); E(ldrb_reg, 2, 1, 3); E(strb_reg, 2, 6, 3); E(adds_imm8, 3, 1); E(cmp_imm, 3, 16); E(b_cond, "pd_sl", "lo")
        E(movs_imm, 0, 1); E(strb_w, 0, 6, B_DIRTY); E(b, "pd_au")
        a.label("pd_alg")
    E(mov_reg, 0, 5); E(subs_imm8, 0, 8); E(lsls_imm, 0, 0, 3); E(strb_imm, 0, 6, P_ALG); E(movs_imm, 0, 1); E(strb_w, 0, 6, B_DIRTY)   # pad 7 + pad: the algorithm
    if STARTER: a.label("pd_au")
    E(mov_reg, 0, 4); E(bl, "c_fmaud"); E(b, "pd_x")
    a.label("pd_ov")
    E(mov_reg, 0, 6); E(bl, "c_fmovk"); E(cmp_imm, 0, 0); bc("pd_row", "eq")
    E(cmp_imm, 0, 5); E(b_cond, "pd_x", "ne")                                               # a ratio: pads 9-32 swallowed
    E(cmp_imm, 5, 23); bc("pd_row", "hi"); E(b, "pd_x")                                    # the algorithm: 9-24
    a.label("pd_row")
    E(mov_reg, 0, 4); E(bl, "c_fmrow"); E(cmp_imm, 0, 0); bc("pd_prev", "eq")
    E(bl, L["c_msheld"]); E(cmp_imm, 0, 0); bc("pd_prev", "ne")
    E(cmp_imm, 5, ROWPAD); E(b_cond, "pd_ofm", "ne")
    E(raw, h(0x9800)); E(movs_imm, 1, MS.ROW + 2); E(raw, h(0x9A02)); E(bl, prev["pad"])      # the oscillator (modesel), then FM on
    E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(movs_imm, 1, 1); E(strb_w, 1, 0, B_ON); E(strb_w, 1, 0, B_DIRTY); E(b, "pd_x")
    a.label("pd_ofm")
    E(cmp_imm, 5, MS.ROW); bc("pd_prev", "lo"); E(cmp_imm, 5, MS.ROW + 6); bc("pd_prev", "hi")
    E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(movs_imm, 1, 0); E(strb_w, 1, 0, B_ON)
    a.label("pd_prev"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["pad"])
    a.label("pd_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)

    # ---- c_fmrel (slot 1 of the template view: view, pad): pad 7 let go = the algorithms off the pads
    a.label("c_fmrel")
    if STARTER: E(cmp_imm, 1, PADNO); E(b_cond, "rl_g", "eq"); E(cmp_imm, 1, PADNO + 1); E(b_cond, "rl_p", "ne"); a.label("rl_g")
    else: E(cmp_imm, 1, PADNO); E(b_cond, "rl_p", "ne")
    E(push_list, [0, 1, 2, 4], lr=True)
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); E(b_cond, "rl_x", "hi")
    E(bl, "c_fmblk"); E(movs_imm, 1, 0); E(strb_w, 1, 0, B_P7)
    a.label("rl_x"); E(raw, popw([0, 1, 2, 4], lr=True))
    a.label("rl_p"); E(b_w, prev["rel"])

    # ---- c_fmqsd (psave's audition, vcf21.c_sdio: track, on, velocity, note): with Shift a patch loads without it
    a.label("c_fmqsd")
    E(push_list, [0, 1, 2, 3], lr=True)
    E(cmp_imm, 1, 0); E(b_cond, "qs_go", "eq")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "qs_go", "eq")
    E(bl, L["c_psst"]); E(cmp_imm, 0, 0); E(b_cond, "qs_x", "eq"); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 6)
    a.label("qs_x"); E(pop_list, [0, 1, 2, 3], pc=True)
    a.label("qs_go"); E(raw, popw([0, 1, 2, 3], lr=True)); E(b_w, L["c_sdio"])

    # ---- c_fmleds (slot 7 of the template view: view) -> r0 = the LED buffer: pad 24 of the row, pad 27 and pad 7 with FM on; the overlays
    a.label("c_fmleds")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); bc("le_x", "hi"); E(mov_reg, 6, 0)
    E(mov_reg, 0, 6); E(bl, "c_fmact"); E(mov_reg, 7, 0)
    E(mov_reg, 0, 6); E(bl, "c_fmrow"); E(cmp_imm, 0, 0); E(b_cond, "le_nr", "eq")
    E(movs_imm, 1, COL_FM[1]); E(cmp_imm, 7, 0); E(b_cond, "le_r1", "eq"); E(movs_imm, 1, COL_FM[0])
    E(movs_imm, 2, MS.COLS[2][1]); E(strh_imm, 2, 5, 2 * (MS.ROW + 2))
    a.label("le_r1"); E(strh_imm, 1, 5, 2 * ROWPAD)
    a.label("le_nr")
    E(cmp_imm, 7, 0); bc("le_x", "eq")
    E(movs_imm, 1, COL_FM[0]); E(strh_imm, 1, 5, 2 * 26)
    E(mov_reg, 0, 6); E(bl, L["c_vpage"]); E(movs_imm, 1, COL_FM[1]); E(cmp_imm, 0, PAGE); E(b_cond, "le_p", "ne"); E(movs_imm, 1, COL_FM[0])
    a.label("le_p"); E(strh_imm, 1, 5, 2 * PADNO)
    E(mov_reg, 0, 6); E(bl, "c_fmblk"); E(mov_reg, 4, 0)                                    # a hold of pad 7 seen before a pause of the view: gone
    now(0); E(ldr_imm, 1, 4, B_LEDT); E(str_imm, 0, 4, B_LEDT); E(subs_reg, 0, 0, 1); E(cmp_imm, 0, STALE_MS); E(b_cond, "le_f", "ls")
    E(movs_imm, 0, 0); E(strb_w, 0, 4, B_P7)
    a.label("le_f")
    if STARTER:                                                                           # pad 8: dim white, bright while held
        E(ldrb_w, 0, 4, B_P7); E(movs_imm, 1, 0x02); E(cmp_imm, 0, 2); E(b_cond, "le_8", "ne"); E(movs_imm, 1, 0x01)
        a.label("le_8"); E(strh_imm, 1, 5, 2 * (PADNO + 1))
    E(mov_reg, 0, 6); E(bl, "c_fmpg"); E(cmp_imm, 0, 0); bc("le_x", "eq")
    if STARTER: E(movs_imm, 7, 5); E(ldrb_w, 0, 4, B_P7); E(cmp_imm, 0, 2); bc("le_st", "eq"); E(cmp_imm, 0, 0); E(b_cond, "le_al", "ne")
    else: E(movs_imm, 7, 5); E(ldrb_w, 0, 4, B_P7); E(cmp_imm, 0, 0); E(b_cond, "le_al", "ne")
    E(mov_reg, 0, 4); E(bl, "c_fmovk"); E(mov_reg, 7, 0); E(cmp_imm, 7, 0); bc("le_x", "eq")
    E(cmp_imm, 7, 5); E(b_cond, "le_al", "eq")
    # the ratios of operator kind - 1 on pads 9-32: the current one bright (white when detuned), the others dim
    E(subs_imm8, 7, 1); E(adds_reg, 0, 4, 7); E(ldrb_imm, 0, 0, P_RAT); E(bl, "c_fmrstep"); E(mov_reg, 7, 0); E(mov_reg, 4, 1)   # r7 = the index, r4 = step
    E(movs_imm, 6, 0)
    a.label("le_rl")
    imm32(1, T["rcd"]); E(ldrb_reg, 1, 1, 6); E(cmp_reg, 6, 7); E(b_cond, "le_rp", "ne")
    imm32(1, T["rcol"]); E(ldrb_reg, 1, 1, 6); E(cmp_imm, 4, 0); E(b_cond, "le_rp", "eq"); E(movs_imm, 1, 0x01)
    a.label("le_rp"); E(mov_reg, 0, 6); E(adds_imm8, 0, 8); E(lsls_imm, 0, 0, 1); E(strh_reg, 1, 5, 0)
    E(adds_imm8, 6, 1); E(cmp_imm, 6, 24); E(b_cond, "le_rl", "lo"); E(b, "le_x")
    a.label("le_al")                                                                      # the algorithms on pads 9-24: the family's colour, the current one bright
    E(ldrb_imm, 7, 4, P_ALG); E(lsrs_imm, 7, 7, 3); E(movs_imm, 6, 0)
    a.label("le_ap")
    imm32(1, T["fam"]); E(ldrb_reg, 1, 1, 6); E(lsls_imm, 1, 1, 1); E(cmp_reg, 6, 7); E(b_cond, "le_ab", "eq"); E(adds_imm8, 1, 1)
    a.label("le_ab"); imm32(2, T["famc"]); E(ldrb_reg, 1, 2, 1)
    E(mov_reg, 0, 6); E(adds_imm8, 0, 8); E(lsls_imm, 0, 0, 1); E(strh_reg, 1, 5, 0)
    E(adds_imm8, 6, 1); E(cmp_imm, 6, 16); E(b_cond, "le_ap", "lo")
    if STARTER:
        E(b, "le_x")
        a.label("le_st")                                                                  # the starters on pads 9-24: the family's colour, bright = the track's values
        E(movs_imm, 6, 0)
        a.label("le_sl")
        imm32(0, T["strt"]); E(lsls_imm, 1, 6, 4); E(adds_reg, 0, 0, 1); E(movs_imm, 2, 0)
        a.label("le_sc"); E(ldrb_reg, 1, 0, 2); E(ldrb_reg, 3, 4, 2); E(cmp_reg, 1, 3); E(b_cond, "le_sn", "ne")
        E(adds_imm8, 2, 1); E(cmp_imm, 2, 16); E(b_cond, "le_sc", "lo")
        E(movs_imm, 2, 0); E(b, "le_sk")                                                   # equal: the bright colour
        a.label("le_sn"); E(movs_imm, 2, 1)
        a.label("le_sk"); E(lsls_imm, 1, 6, 1); E(adds_reg, 1, 1, 2); imm32(2, T["stc"]); E(ldrb_reg, 1, 2, 1)
        E(mov_reg, 0, 6); E(adds_imm8, 0, 8); E(lsls_imm, 0, 0, 1); E(strh_reg, 1, 5, 0)
        E(adds_imm8, 6, 1); E(cmp_imm, 6, 16); E(b_cond, "le_sl", "lo")
    a.label("le_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_fmsum(r0 = 21 bytes) -> r0 = 0x5A + the first 20, & 0xFF; clobbers r1, r2
    a.label("c_fmsum")
    E(movs_imm, 1, 0); E(movs_imm, 2, 0x5A)
    a.label("su_l"); E(raw, h(0x5C43)); E(adds_reg, 2, 2, 3); E(adds_imm8, 1, 1); E(cmp_imm, 1, PLEN - 1); E(b_cond, "su_l", "lo")
    E(movs_imm, 0, 0xFF); E(ands_reg, 0, 2); E(raw, h(0x4770))

    # ---- c_fmgath(r0 = track) in c_mpsave: p4dest's gather, then FM at padding + 100 (version 2)
    a.label("c_fmgath")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0)
    E(bl, prev["gath"])
    E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(mov_reg, 5, 0); imm32(6, PK.BUF + POFS)
    E(movs_imm, 0, ord("F")); E(strb_imm, 0, 6, 0); E(movs_imm, 0, ord("M")); E(strb_imm, 0, 6, 1); E(movs_imm, 0, 2); E(strb_imm, 0, 6, 2)
    E(ldrb_w, 0, 5, B_ON); E(strb_imm, 0, 6, 3)
    E(movs_imm, 7, 0)
    a.label("ga_l"); E(ldrb_reg, 0, 5, 7); E(adds_imm8, 7, 4); E(strb_reg, 0, 6, 7); E(subs_imm8, 7, 3); E(cmp_imm, 7, 16); E(b_cond, "ga_l", "lo")
    E(mov_reg, 0, 6); E(bl, "c_fmsum"); E(strb_imm, 0, 6, PLEN - 1)
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_fmappl(r0 = track) in c_mpload (r5 = the slot there): p4dest's apply, then the patch's FM (version 1 converted; none: FM off)
    a.label("c_fmappl")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 7, 5)
    E(bl, prev["appl"])
    E(lsrs_imm, 0, 7, 3); E(lsls_imm, 1, 7, 29); E(lsrs_imm, 1, 1, 20)
    imm32(2, MP.OFF + POFS); E(adds_reg, 1, 1, 2)
    imm32(2, PK.BUF + POFS); E(movs_imm, 3, PLEN); E(bl, L["c_mpr"])
    imm32(6, PK.BUF + POFS); E(mov_reg, 5, 0); E(mov_reg, 7, 1)
    E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(mov_reg, 1, 0); E(movs_imm, 0, 0); E(strb_w, 0, 1, B_ON); E(movs_imm, 0, 1); E(strb_w, 0, 1, B_DIRTY)
    E(mov_reg, 4, 1)                                                                     # r4 = the block
    E(cmp_imm, 5, 0); bc("ap_x", "ne"); E(cmp_imm, 7, PLEN); bc("ap_x", "ne")
    E(ldrb_imm, 0, 6, 0); E(cmp_imm, 0, ord("F")); bc("ap_x", "ne"); E(ldrb_imm, 0, 6, 1); E(cmp_imm, 0, ord("M")); bc("ap_x", "ne")
    E(ldrb_imm, 0, 6, 2); E(subs_imm8, 0, 1); E(cmp_imm, 0, 1); bc("ap_x", "hi")          # version 1 or 2
    E(mov_reg, 0, 6); E(bl, "c_fmsum"); E(ldrb_imm, 1, 6, PLEN - 1); E(cmp_reg, 0, 1); bc("ap_x", "ne")
    E(movs_imm, 7, 0)
    a.label("ap_l"); E(adds_imm8, 7, 4); E(ldrb_reg, 0, 6, 7); E(subs_imm8, 7, 4)
    E(cmp_imm, 0, 127); E(b_cond, "ap_v", "ls"); E(movs_imm, 0, 127)
    a.label("ap_v"); E(strb_reg, 0, 4, 7); E(adds_imm8, 7, 1); E(cmp_imm, 7, 16); E(b_cond, "ap_l", "lo")
    E(ldrb_imm, 0, 6, 2); E(cmp_imm, 0, 2); bc("ap_on", "eq")
    # version 1: the attacks to the right half, the feedback's square root, the ratios to their exact click
    E(movs_imm, 7, 0)
    a.label("ap_c")
    E(adds_reg, 1, 4, 7); E(ldrb_imm, 0, 1, P_ATK); E(lsrs_imm, 0, 0, 1); E(adds_imm8, 0, CENTRE); E(strb_imm, 0, 1, P_ATK)
    E(ldrb_imm, 0, 1, P_RAT); E(movs_imm, 2, 24); E(muls, 0, 2); E(lsrs_imm, 0, 0, 7); E(lsls_imm, 0, 0, 7); E(adds_imm8, 0, 23); E(raw, udiv(0, 0, 2))
    E(strb_imm, 0, 1, P_RAT)
    E(adds_imm8, 7, 1); E(cmp_imm, 7, 4); E(b_cond, "ap_c", "lo")
    E(ldrb_imm, 1, 4, P_FB); E(lsls_imm, 1, 1, 7); E(movs_imm, 0, 0)                    # the largest r with r^2 <= 128 p
    a.label("ap_q"); E(adds_imm8, 0, 1); E(mov_reg, 2, 0); E(muls, 2, 0); E(cmp_reg, 2, 1); E(b_cond, "ap_q", "ls")
    E(subs_imm8, 0, 1); E(strb_imm, 0, 4, P_FB)
    a.label("ap_on")
    E(ldrb_imm, 0, 6, 3); E(movs_imm, 1, 1); E(ands_reg, 0, 1); E(strb_w, 0, 4, B_ON)
    a.label("ap_x"); E(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble(), T


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the heads: the DSP service chain, the note vtable, the macro handlers' slots 4 / 7, the template view's
    slots 0 / 7; p4dest's gather / apply calls in c_mpsave / c_mpload."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("vcf20", k) for k in ("c_vtrack", "c_von", "c_edact", "c_sdview", "c_vpage", "c_vsetpage", "c_vclr")}
    L["c_shift"] = lab("sc15", "c_shift")
    for k in ("c_mpon", "c_mpr", "c_mpload", "c_mpsave"): L[k] = lab("mpatch", k)
    for k in ("c_msmode", "c_msheld"): L[k] = lab("modesel", k)
    L["c_mxclrh"] = lab("modmx", "c_mxclrh")
    for k in ("c_p4gath", "c_p4appl"): L[k] = lab("p4dest", k)
    KN, TP = V.AC64_VT, MP.TMPL_VT
    prev = dict(svc=MP.bw_target(img, S14.SVC_HOOK, BASE), non=u(MX.NOTE_VT) & ~1, knob=u(KN + 16) & ~1, kleds=u(KN + 28) & ~1,
                pad=u(TP) & ~1, leds=u(TP + 28) & ~1, gath=L["c_p4gath"], appl=L["c_p4appl"])
    if V2:
        for k in ("c_sdio", "c_vnon", "c_vreset", "c_sdtonic"): L[k] = lab("vcf20", k)
        for k in ("c_psxpad", "c_psbtn", "c_psst", "c_psaoff"): L[k] = lab("psave", k)
        L["c_rtoff"] = lab("retrig", "c_rtoff")
        if "c_mxzero" in report["modmx"]["labels"]: L["c_mxzero"] = lab("modmx", "c_mxzero")
        prev["rel"] = u(TP + 4) & ~1
        (code, labels), T = arm_code2(base_addr, L, prev)
    else:
        (code, labels), T = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    if V2:
        # the audition of vcf21.c_sdio through the FM's note-on; psave's audition with Shift = none; Clear + MIDI 1 / 2 = the FM's defaults too
        for site_of, n, orig, ours in ((L["c_sdio"], 0x60, L["c_vnon"], "c_fmnon"), (L["c_psxpad"], 0x140, L["c_sdio"], "c_fmqsd"),
                                        (L["c_psbtn"], 0x120, L["c_vreset"], "c_fmvrst")):
            s = MX.bl_sites(img, site_of, site_of + n, orig, BASE)
            assert len(s) == 1, (ours, hex(site_of), [hex(x) for x in s])
            img[s[0] - BASE:s[0] - BASE + 4] = bl(s[0], labels[ours])
            prev[ours + "_site"] = s[0]
        struct.pack_into("<I", img, TP + 4 - BASE, labels["c_fmrel"] | 1)
    for site_of, orig, ours in ((L["c_mpsave"], L["c_p4gath"], "c_fmgath"), (L["c_mpload"], L["c_p4appl"], "c_fmappl")):
        s = MX.bl_sites(img, site_of, site_of + 0x120, orig, BASE)
        assert len(s) == 1, (hex(site_of), [hex(x) for x in s])
        img[s[0] - BASE:s[0] - BASE + 4] = bl(s[0], labels[ours])
    img[S14.SVC_HOOK - BASE:S14.SVC_HOOK - BASE + 4] = b_w(S14.SVC_HOOK, labels["c_fmtick"])
    struct.pack_into("<I", img, MX.NOTE_VT - BASE, labels["c_fmnon"] | 1)
    struct.pack_into("<I", img, KN + 16 - BASE, labels["c_fmknob"] | 1)
    struct.pack_into("<I", img, KN + 28 - BASE, labels["c_fmkleds"] | 1)
    struct.pack_into("<I", img, TP - BASE, labels["c_fmpad"] | 1)
    struct.pack_into("<I", img, TP + 28 - BASE, labels["c_fmleds"] | 1)
    labels.update({f"t_{k}": v for k, v in T.items()})
    return labels, code, prev
