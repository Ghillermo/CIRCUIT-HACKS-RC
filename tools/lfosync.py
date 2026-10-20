"""SC44.8 (the user, 2026-10-19: «en los lfo rate, hazlo bipolar (manten 0 dim y lados bright) hacia la derecha, lfo libre, izquierda, lfo a tempo
con sync en beat 1»; with him: the divisions with their triplets, the values saved before may sound different): the synced side of the LFO
rates, on the ARM.

The own engine of MIDI 1 / 2 (vcf21 / vcf21_dsp.use_lfosync): LRATE (code 11) -64..63; the DSP takes PH += TLFO[2 v] for v >= 0 and, for v < 0,
the increment we keep in OS2B0 + 48 t + 40.  Here, a new head of the DSP service chain, for each track t with v < 0:
  * the division d = DIVS[(-v - 1) >> 2] (4 clicks a step, from the centre outwards: 1/16T, 1/16, 1/8T, 1/8, 1/4T, 1/4, 1/2T, 1/2, 1 bar T, 1 bar,
    2T, 2, 4T, 4, 8T, 8 bars; ticks of 24 a quarter note);
  * the increment a block (48 kHz / 32 frames = 1500 blocks a second) = BPM x KQ[d] >> 8 (BPM = p0 of the tempo store 0x20011404, the one
    the Tempo view's knob turns and SC14's c_beat reads; p1 is not the tempo: countin reads it by mistake), KQ = 2^24 x 24 x 256 / (60 x 1500 x d), written when
    it changes;
  * on each new sequencer tick (the global tick, [0x20038EC0 + 0x90] parameter 0): the phase PH = $800000 + (tick mod d) x 2^24 / d (the top of
    the reverse saw = the start of every shape) into VB0 + 48 t + PH: the cycles start on the bar's first beat (tick 0 of the transport) and
    keep in step; between ticks (and with the transport stopped) the DSP runs at the increment.
The drums (drums2_dsp.use_lfosync): Shift + K7 (LSPD, code 4, -64..63: the byte persist19 keeps in the project, c_dget) the same way, the
increment in the drum block's word LINC, the phase in its PH.
RAM (MX.MXR + 0x110): per LFO the last tick written, the last increment (u32 each); tracks 0 / 1, drums 0..3."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, lsls_imm, lsrs_imm, mov_reg, movs_imm,  # noqa: E402
                   movt, movw, muls, pop_list, push_list, raw, str_imm, subs_imm8, subs_reg)
from build_sc14 import udiv  # noqa: E402
import build_sc14 as S14  # noqa: E402
import mpatch as MP  # noqa: E402
import modmx as MX  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
import drums2_dsp as D2  # noqa: E402

DIVS = (4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512, 768)
BLOCKS = 48000 / 32
KQ = tuple(round((1 << 24) * 24 * 256 / (60 * BLOCKS * d)) for d in DIVS)
PHQ = tuple(round((1 << 24) / d) for d in DIVS)
ENG, TEMPO, PARAM_GET, DSP_WRITE = 0x20038EC0, 0x20011404, 0x0803542C, 0x080292F8
RAM = MX.MXR + 0x110                                 # 6 slots of 8 B (the last tick, the last increment): tracks 0 / 1, then drums 0..3
DRUMS = True                                         # the drums' LFO too (drums2_dsp.use_lfosync)
CODE_LRATE = 11


def ldrsb_w(rt, rn, imm12): return h(0xF990 | rn) + h(rt << 12 | imm12)
def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    assert base % 4 == 0
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    a.label("lf_tabs")                                   # DIVS (u32), KQ, PHQ
    for t in (DIVS, KQ, PHQ):
        E(raw, b"".join(struct.pack("<I", x) for x in t))
    T_DIV, T_KQ, T_PH = base, base + 64, base + 128

    # ---- c_lfhead (the head of the DSP service chain): the two tracks, the four drums, then the chain
    a.label("c_lfhead")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    for t in (0, 1):
        E(movs_imm, 0, t); E(bl, "c_lfv")
    if DRUMS:
        for d in range(4):
            E(movs_imm, 0, d); E(bl, "c_lfd")
    E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(b_w, prev["svc"])

    # ---- c_lfv(r0 = track): the own engine's LFO (LRATE, code 11)
    a.label("c_lfv")
    E(push_list, [4], lr=True)
    E(mov_reg, 4, 0); E(movs_imm, 1, CODE_LRATE); E(bl, L["c_vvaddr"]); E(raw, ldrsb_w(0, 0, 0))
    imm32(1, RAM); E(lsls_imm, 2, 4, 3); E(adds_reg, 1, 1, 2)                     # the slot RAM + 8 t
    E(movs_imm, 3, 48); E(muls, 3, 4)
    imm32(2, VD.OS2B0 + VD.LFS_INC); E(adds_reg, 2, 2, 3); E(push_list, [2])
    imm32(2, VD.VB0 + VD.PH); E(adds_reg, 3, 2, 3); E(pop_list, [2])
    E(bl, "c_lfs"); E(pop_list, [4], pc=True)

    if DRUMS:
        # ---- c_lfd(r0 = drum): Shift + K7 of a drum (LSPD, code 4; the byte in the project, 7 bits two's complement)
        a.label("c_lfd")
        E(push_list, [4], lr=True)
        E(mov_reg, 4, 0); E(movs_imm, 1, 4); E(bl, L["c_dget"]); E(adds_imm8, 0, 1); E(b_cond, "ld_x", "eq"); E(subs_imm8, 0, 1)
        E(lsls_imm, 0, 0, 25); E(raw, h(0x1000 | 25 << 6 | 0 << 3 | 0))          # asrs r0, r0, #25: the value -64..63
        imm32(1, RAM + 16); E(lsls_imm, 2, 4, 3); E(adds_reg, 1, 1, 2)           # the slot RAM + 16 + 8 d
        E(lsls_imm, 3, 4, 6)                                                       # 64 d
        imm32(2, D2.DB + D2.LINC); E(adds_reg, 2, 2, 3); E(push_list, [2])
        imm32(2, D2.DB + D2.PH); E(adds_reg, 3, 2, 3); E(pop_list, [2])
        E(bl, "c_lfs")
        a.label("ld_x"); E(pop_list, [4], pc=True)

    # ---- c_lfs(r0 = the rate -64..63, r1 = the RAM slot (+0 the last tick, +4 the last increment), r2 / r3 = the DSP words of the increment /
    #      the phase): synced (< 0): the increment when it changes, the phase on a new tick; clobbers r0-r3
    a.label("c_lfs")
    E(push_list, [1, 2, 3, 4, 5, 6, 7], lr=True)                                  # sp + 0 slot, + 4 the increment's word, + 8 the phase's
    E(cmp_imm, 0, 0); E(b_cond, "ls_x", "ge")
    E(raw, h(0x43C0))                                                             # mvns r0, r0 (-v - 1)
    E(lsrs_imm, 5, 0, 2); E(lsls_imm, 5, 5, 2)                                    # r5 = 4 x the step
    imm32(0, TEMPO); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 6, 0, 0)      # r6 = BPM
    imm32(1, T_KQ); E(adds_reg, 1, 1, 5); E(ldr_imm, 1, 1, 0); E(muls, 6, 1); E(lsrs_imm, 6, 6, 8)   # r6 = the increment
    E(ldr_sp, 7, 0)
    E(ldr_imm, 0, 7, 4); E(cmp_reg, 0, 6); E(b_cond, "ls_t", "eq"); E(str_imm, 6, 7, 4)
    E(ldr_sp, 2, 4); E(lsls_imm, 1, 6, 8); E(movs_imm, 0, 0); E(bl, DSP_WRITE)
    a.label("ls_t")
    imm32(0, ENG + 0x90); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldr_imm, 6, 0, 0)   # r6 = the tick
    E(ldr_imm, 0, 7, 0); E(cmp_reg, 0, 6); E(b_cond, "ls_x", "eq"); E(str_imm, 6, 7, 0)
    imm32(1, T_DIV); E(adds_reg, 1, 1, 5); E(ldr_imm, 1, 1, 0)                     # r1 = d
    E(raw, udiv(0, 6, 1)); E(muls, 0, 1); E(subs_reg, 0, 6, 0)                    # r0 = tick mod d
    imm32(1, T_PH); E(adds_reg, 1, 1, 5); E(ldr_imm, 1, 1, 0); E(muls, 0, 1)      # x 2^24 / d
    E(movs_imm, 1, 1); E(lsls_imm, 1, 1, 23); E(adds_reg, 0, 0, 1)                # + $800000
    E(lsls_imm, 1, 0, 8); E(ldr_sp, 2, 8); E(movs_imm, 0, 0); E(bl, DSP_WRITE)
    a.label("ls_x"); E(pop_list, [1, 2, 3, 4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the head of the DSP service chain."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    L = dict(c_vvaddr=int(report["vcf20"]["labels"]["c_vvaddr"], 16), c_dget=int(report["persist19"]["labels"]["c_dget"], 16))
    prev = dict(svc=MP.bw_target(img, S14.SVC_HOOK, BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    img[S14.SVC_HOOK - BASE:S14.SVC_HOOK - BASE + 4] = b_w(S14.SVC_HOOK, labels["c_lfhead"])
    return labels, code, prev
