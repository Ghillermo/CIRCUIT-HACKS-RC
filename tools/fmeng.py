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
                   raw, str_imm, strb_imm, strb_reg, strb_w, strh_imm, strh_reg, subs_imm8, subs_reg)
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
DSP_WRITE = 0x080292F8
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
    (code, labels), T = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
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
