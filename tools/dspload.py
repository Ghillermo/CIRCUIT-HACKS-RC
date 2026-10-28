"""S484D (diagnostic; the user, 2026-10-28: «Some FM patches still produce crackling when you hold more than 5 notes … a watchdog to limit voices
when the DSP is about to break?»; «the main issue comes when using notes with long releases, since it's easy to pile voices until the rattling
sounds appear quick»; «we can make a diag build if you need»): two live meters, to tell the DSP running out of time from the voices' sum clipping.

Core 0 (read in its program): the ESAI interrupt plays the output ring at Y:$FFE (2 words a frame, the ring 1024 words, M = $3FF); the main loop
calls the block function ($1D9), which computes a block when (Y:$FFE - Y:$FFD) & $3FF >= $300 (Y:$FFD at most 256 words = 4 blocks ahead) and
moves Y:$FFD on by 64 at its end ($27B).  So the margin m = (Y:$FFD - Y:$FFE) & $3FF falls from 256 while a block is computed and is
256 - 64 x (its time / the block period) just before it ends; m < 192 = a block took longer than a period (the DSP falls behind); m > 640 = the
ring ran dry (Y:$FFE passed Y:$FFD: the interrupt plays old audio, a buzz, until the DSP is 4 blocks ahead again).  The own synth of MIDI 1 / 2
writes its output into the input ring at the block (L = MIDI 1, R = MIDI 2: after the voices, the VCA, the effect and the filter): the last
block's words Y:[$FFD - 64, $FFD) stay there until the interrupt comes round.

ARM only (no DSP code): a head of the DSP service chain reads every SAMPLE_MS ms with 0x08029344 (allowed from the tick) Y:$FFE, then Y:$FFD (in
this order: a block that ends between the two reads only makes the margin look larger), then one word of the last block (the offset steps by 7
through its 64: both tracks); windows of WIN_MS.  The LED task calls draw over the frame:
  * Save (LED 57) = the DSP's time: green = every block within 1/2 a period (min margin >= 224), yellow 1/2 - 3/4, orange 3/4 - 1, red = a block
    took longer than a period; white for 2 s after the ring ran dry (the audio repeated);
  * Duplicate (LED 56) = the own synth's peak (MIDI 1 / 2): off < 1/8 of full scale, green < 1/2, yellow < 0.9, orange < 0.99, red >= 0.99
    (clipping).
RAM: modmx.MXR + 0x1F00 (signed "DLD1"): + 4 the last sample, + 8 the window's start, + 12 / 16 the window's min margin / peak, + 20 / 24 the
last window's, + 28 the last dry ring, + 32 the ring offset, + 36 how many dry rings, + 40 / 44 the worst margin / peak since power-on.
In the hole (no card, no settings).
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, lsls_imm, lsrs_imm, mov_reg, movs_imm,  # noqa: E402
                   movt, movw, pop_list, push_list, raw, str_imm, subs_reg, subs_imm8)
import modmx as MX  # noqa: E402
import mpatch as MP  # noqa: E402
import build_sc14 as S14  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402

RAM = MX.MXR + 0x1F00
SIG = 0x31444C44                                              # "DLD1"
DSP_READ, HAL_TICK = 0x08029344, 0x2000081C
Y_ISR, Y_BLK = 0x8000 | 0xFFE, 0x8000 | 0xFFD                 # 0x08029344's Y addresses
SAMPLE_MS, WIN_MS, DRY_MS = 4, 500, 2000
DRY = 640
LED_DUP, LED_SAVE = 56, 57
CPU_STEPS = ((224, 0x17), (208, 0x2D), (192, 0x2B))           # min margin >= : green, yellow, orange; below: red
COL_LATE, COL_DRY = 0x53, 0x01
PEAK_STEPS = ((0x100000, 0x00), (0x400000, 0x17), (0x733333, 0x2D), (0x7EB852, 0x2B))   # peak < : off, green, yellow, orange; above: red
COL_CLIP = 0x53
O_LAST, O_W0, O_MIN, O_PK, O_SMIN, O_SPK, O_DRY, O_OFS, O_NDRY, O_WMIN, O_WPK, RSZ = 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, prev):
    a = Asm(base)
    E = a.emit
    RET = h(0x4770)
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def rd_dsp(addr): E(movs_imm, 0, 0); imm32(1, addr); E(bl, DSP_READ)              # r0 = the word << 8

    # ---- c_dlst() -> r0 = our RAM (signed; the minima at 1023 the first time); clobbers r1-r3
    a.label("c_dlst")
    imm32(0, RAM); E(ldr_imm, 1, 0, 0); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "st_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0); E(movs_imm, 3, 4)
    a.label("st_z"); E(raw, h(0x50C1)); E(adds_imm8, 3, 4); E(cmp_imm, 3, RSZ); E(b_cond, "st_z", "lo")   # str r1, [r0, r3]
    imm32(1, 1023); E(str_imm, 1, 0, O_MIN); E(str_imm, 1, 0, O_SMIN); E(str_imm, 1, 0, O_WMIN)
    a.label("st_x"); E(raw, RET)

    # ---- c_dltick (the head of the DSP service chain): a sample every SAMPLE_MS ms, the windows
    #      r4 = RAM, r5 = now, r6 = Y:$FFE, r7 = Y:$FFD
    a.label("c_dltick")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    E(bl, "c_dlst"); E(mov_reg, 4, 0)
    imm32(0, HAL_TICK); E(ldr_imm, 5, 0, 0)
    E(ldr_imm, 0, 4, O_LAST); E(subs_reg, 0, 5, 0); E(cmp_imm, 0, SAMPLE_MS); E(b_cond, "tk_x", "lo"); E(str_imm, 5, 4, O_LAST)
    rd_dsp(Y_ISR); E(lsrs_imm, 6, 0, 8)
    rd_dsp(Y_BLK); E(lsrs_imm, 7, 0, 8)
    E(subs_reg, 0, 7, 6); E(lsls_imm, 0, 0, 22); E(lsrs_imm, 0, 0, 22)                # r0 = the margin (10 bits)
    E(movw, 1, DRY); E(cmp_reg, 0, 1); E(b_cond, "tk_m", "ls")
    E(str_imm, 5, 4, O_DRY); E(ldr_imm, 0, 4, O_NDRY); E(adds_imm8, 0, 1); E(str_imm, 0, 4, O_NDRY); E(b, "tk_r")   # the ring ran dry
    a.label("tk_m")
    E(ldr_imm, 1, 4, O_MIN); E(cmp_reg, 0, 1); E(b_cond, "tk_m2", "hs"); E(str_imm, 0, 4, O_MIN)
    a.label("tk_m2"); E(ldr_imm, 1, 4, O_WMIN); E(cmp_reg, 0, 1); E(b_cond, "tk_r", "hs"); E(str_imm, 0, 4, O_WMIN)
    a.label("tk_r")                                                                    # one word of the last block
    E(ldr_imm, 0, 4, O_OFS); E(adds_imm8, 0, 7); E(lsls_imm, 0, 0, 26); E(lsrs_imm, 0, 0, 26); E(str_imm, 0, 4, O_OFS)
    E(subs_imm8, 0, 64); E(adds_reg, 0, 0, 7); E(lsls_imm, 0, 0, 22); E(lsrs_imm, 0, 0, 22)                 # (Y:$FFD - 64 + offset) & $3FF
    E(lsrs_imm, 1, 7, 10); E(lsls_imm, 1, 1, 10); E(adds_reg, 1, 1, 0); imm32(0, 0x8000); E(adds_reg, 1, 1, 0); E(movs_imm, 0, 0)
    E(bl, DSP_READ); E(raw, h(0x1200))                                                 # asrs r0, r0, #8: the sample, signed
    E(cmp_imm, 0, 0); E(b_cond, "tk_p", "ge"); E(raw, h(0x4240))                       # negs r0, r0
    a.label("tk_p")
    E(ldr_imm, 1, 4, O_PK); E(cmp_reg, 0, 1); E(b_cond, "tk_p2", "ls"); E(str_imm, 0, 4, O_PK)
    a.label("tk_p2"); E(ldr_imm, 1, 4, O_WPK); E(cmp_reg, 0, 1); E(b_cond, "tk_w", "ls"); E(str_imm, 0, 4, O_WPK)
    a.label("tk_w")                                                                    # the window: shown, then from scratch
    E(ldr_imm, 0, 4, O_W0); E(subs_reg, 0, 5, 0); E(movw, 1, WIN_MS); E(cmp_reg, 0, 1); E(b_cond, "tk_x", "lo")
    E(str_imm, 5, 4, O_W0)
    E(ldr_imm, 0, 4, O_MIN); E(str_imm, 0, 4, O_SMIN); E(ldr_imm, 0, 4, O_PK); E(str_imm, 0, 4, O_SPK)
    imm32(0, 1023); E(str_imm, 0, 4, O_MIN); E(movs_imm, 0, 0); E(str_imm, 0, 4, O_PK)
    a.label("tk_x"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(b_w, prev["svc"])

    # ---- c_dlled (the LED task calls: ctrl, frame): the chain, then Save = the DSP's time, Duplicate = the synth's peak
    a.label("c_dlled")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    E(bl, "c_dlst"); E(mov_reg, 4, 0)
    E(ldr_imm, 0, 4, O_DRY); E(cmp_imm, 0, 0); E(b_cond, "ld_c", "eq")
    imm32(1, HAL_TICK); E(ldr_imm, 1, 1, 0); E(subs_reg, 1, 1, 0); imm32(0, DRY_MS); E(cmp_reg, 1, 0); E(b_cond, "ld_c", "hs")
    E(movs_imm, 1, COL_DRY); E(b, "ld_cw")
    a.label("ld_c")
    E(ldr_imm, 0, 4, O_SMIN); E(movs_imm, 1, COL_LATE)
    for i, (m, col) in enumerate(CPU_STEPS):
        E(cmp_imm, 0, m); E(b_cond, f"ld_c{i}", "lo"); E(movs_imm, 1, col); E(b, "ld_cw"); a.label(f"ld_c{i}")
    E(movs_imm, 1, COL_LATE)
    a.label("ld_cw"); E(movs_imm, 0, 2 * LED_SAVE); E(raw, h(0x5229))                 # strh r1, [r5, r0]
    E(ldr_imm, 0, 4, O_SPK)
    for i, (m, col) in enumerate(PEAK_STEPS):
        imm32(2, m); E(cmp_reg, 0, 2); E(b_cond, f"ld_p{i}", "hs"); E(movs_imm, 1, col); E(b, "ld_pw"); a.label(f"ld_p{i}")
    E(movs_imm, 1, COL_CLIP)
    a.label("ld_pw"); E(movs_imm, 0, 2 * LED_DUP); E(raw, h(0x5229))
    E(mov_reg, 0, 5); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the head of the DSP service chain and the LED task calls."""
    import ct_fw
    from thumb import b_w as bw_enc
    BASE = ct_fw.APP_BASE
    prev = dict(svc=MP.bw_target(img, S14.SVC_HOOK, BASE), ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    img[S14.SVC_HOOK - BASE:S14.SVC_HOOK - BASE + 4] = bw_enc(S14.SVC_HOOK, labels["c_dltick"])
    from thumb import bl as bl_enc_
    for c in PK.LED_CALLS:
        assert FD.bl_target(img, c, BASE) == prev["ledtask"], hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc_(c, labels["c_dlled"])
    assert RAM + RSZ <= MX.MXR + 0x2000
    return labels, code, prev
