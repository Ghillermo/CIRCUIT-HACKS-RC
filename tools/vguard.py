"""SC48.5 / Beta 3.42 (the user, 2026-10-28: «Some FM patches still produce crackling when you hold more than 5 notes … a watchdog to limit voices
when the DSP is about to break?»; S484D on the device: «save goes white when crackling», «up until red the sound was OK», «red is pretty much ok,
so push towards the red-white limit»; «maybe increase polyphony and let the limiter choose»; «also extend your findings and voice limiting to
unison»): a voice limiter on the DSP's time.

S484D's meter told it: the crackle is core 0 running out of time (the output ring ran dry), not the voices' sum clipping; a block taking longer
than a period (red) is still heard clean, the ring runs dry (white) only when the DSP has fallen the whole of its four blocks behind.  ARM only:
  * a head of the DSP service chain reads, every SAMPLE_MS ms and only while the own synth's poly / unison voices sounding or about to start
    (poly.py's records, both tracks: poly.c_pytot) are MIN_V or more, the margin m = (Y:$FFD - Y:$FFE) & $3FF (dspload's reads with
    0x08029344: the ring's play place, then the next block's; m > DRY = the ring ran dry, taken as 0);
  * m < SHED_AT (less than one block of the four left: deep red, before white) = one voice freed (poly.c_pyshed: the quietest one still ringing
    after its note-off, FM before the other engines; with none, the oldest held one: its note is cut, as a steal), at most one every GAP ms, or
    every GAP_E ms with m < EMERG_AT (half a block left);
  * then the cap (+ O_CAP) = the voices left (at least CAP_MIN): a new poly note at the cap frees the quietest first, and the unison plays the cap's
    voices at most (poly.use_v9); RELAX_MS with nothing freed = the cap one higher, past CAP_TOP none.  So the limiter finds the voices the DSP
    can run with the sounds and the project playing, and tries one more every RELAX_MS (red at worst, which is heard clean).
RAM: modmx.MXR + 0x1E80 (32 B, signed "VGD1": + 4 the last reading, + 8 the last voice freed, + 12 how many freed, + 16 the last margin, + 20 the
cap (byte, 0 = none), + 24 the last relax, + 28 the last hold (use_hold)).  In the hole (no card, no settings).  No DSP code.

use_hold (SC48.6 / Beta 3.43; the user: «stock synths sometimes cease to sound when 5 notes are held», «synth1/2 sometimes stop playing, they
come back when i let go of the chord», «Save was amber/yellow/orange», only with poly and 4+ notes): the stock has its own limiter on the DSP's
time, for Synth 1 / 2 only (read in core 0's program; the emulator's timer reads 0, so it never fires there):
  * at each block's start ($1EF -> $1C01) X:$30 = the timer 1 count ($FFFF88) since the main loop began to wait for the ring = the idle time;
    the voices' times by synth (X:$1E / $1F, from $1D at each voice's start) and their counts (X:$20 / $21) give X:$36 / $37 = how many more
    voices of that synth fit, 8.8 (count x (idle + t_other - t_s) / t_s);
  * below $80 (half a voice) the DSP kills one voice of that synth ($1BAD: the least by $1BB3's score, Y:voice = 1) each time its countdown
    X:$3239 / $323A reaches 0, then 12 blocks again: all of its voices within ~50 ms, and every new one 8 ms after its note;
  * the ARM's note-on (0x080217EA) reads X:$36 + s: below $140 the new note takes an old voice of that synth ($1BB3 by Y:$1B -> X:$35) instead
    of a free one.
Our voices run inside the block, so the stock counts their time as its own synths' lack of room.  Now, while MIN_V or more own voices sound,
the countdowns are written HOLD_BLK every HOLD_MS (2 SPI writes): the DSP never kills a Synth 1 / 2 voice for our sake; the note-on rule stays
(a new stock note reuses a voice of its synth while the DSP is short, as the stock under load); a real overload is vguard's (our voices freed).
With fewer than MIN_V own voices the countdowns run out within HOLD_BLK blocks and the stock's limiter is back.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, lsls_imm, lsrs_imm, mov_reg, movs_imm,  # noqa: E402
                   movt, movw, raw, str_imm, strb_imm, subs_reg)
import modmx as MX  # noqa: E402
import mpatch as MP  # noqa: E402
import build_sc14 as S14  # noqa: E402
import vcf21 as V  # noqa: E402
import fmeng as FE  # noqa: E402

RAM = MX.MXR + 0x1E80
SIG = 0x31444756                                              # "VGD1"
O_LAST, O_SHED, O_N, O_M, O_CAP, O_RLX, O_HOLD, RSZ = 4, 8, 12, 16, 20, 24, 28, 32
DSP_READ, HAL_TICK = 0x08029344, 0x2000081C
Y_ISR, Y_BLK = 0x8000 | 0xFFE, 0x8000 | 0xFFD                 # 0x08029344's Y addresses (the ring's play place, the next block's)
SAMPLE_MS = 2
MIN_V = 2                                                     # the voices sounding / starting before the margin is read
DRY = 640                                                     # m above: the ring ran dry (taken as 0)
SHED_AT, EMERG_AT = 64, 32                                    # m below: a voice freed (one block left / half a block)
GAP, GAP_E = 12, 4                                            # ms between two voices freed (with m < EMERG_AT)
CAP_MIN, CAP_TOP, RELAX_MS = 2, 12, 2000                      # the cap's floor; past the top none; one higher every RELAX_MS with nothing freed
S_REL_OTHER, S_HELD = 0x20000, 0x40000                        # poly.c_pyshed's scores: FM ringing = its envelopes' sum (< 0x20000); the least freed
HOLD = False                                                  # use_hold: the stock's Synth 1 / 2 steal held while our voices sound
STEAL_CNT = 0x3239                                            # X: the stock's steal countdowns (Synth 1, Synth 2), in blocks (32 samples)
HOLD_BLK, HOLD_MS = 48, 16                                    # written every HOLD_MS: 48 blocks = 32 ms
DSP_WRITE = 0x080292F8


def use_hold():
    """SC48.6 / Beta 3.43: the stock's DSP-time voice steal of Synth 1 / 2 held while our voices sound (see the docstring)."""
    global HOLD
    HOLD = True


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    import poly as P
    a = Asm(base)
    E = a.emit
    RET = h(0x4770)
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_g{zc[0]}"
        E(b_cond, n, V.INV[cond]); E(b, target); a.label(n)
    def rd_dsp(addr): E(movs_imm, 0, 0); imm32(1, addr); E(bl, DSP_READ)              # r0 = the word << 8

    # ---- c_vgst() -> r0 = our RAM (signed, zeroed the first time: no cap); clobbers r1-r3
    a.label("c_vgst")
    imm32(0, RAM); E(ldr_imm, 1, 0, 0); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "st_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0)
    for o in range(4, RSZ, 4): E(str_imm, 1, 0, o)
    a.label("st_x"); E(raw, RET)

    # ---- c_vgtick (the head of the DSP service chain): r4 = RAM, r5 = now
    a.label("c_vgtick")
    E(raw, pushw(list(range(12)), lr=True))
    E(bl, "c_vgst"); E(mov_reg, 4, 0)
    imm32(0, HAL_TICK); E(ldr_imm, 5, 0, 0)
    E(ldr_imm, 0, 4, O_LAST); E(subs_reg, 0, 5, 0); E(cmp_imm, 0, SAMPLE_MS); bc("vg_x", "lo"); E(str_imm, 5, 4, O_LAST)
    E(ldrb_imm, 6, 4, O_CAP); E(cmp_imm, 6, 0); E(b_cond, "vr_x", "eq")                # the cap: one higher after RELAX_MS with nothing freed
    E(ldr_imm, 0, 4, O_SHED); E(subs_reg, 0, 5, 0); E(movw, 1, RELAX_MS); E(cmp_reg, 0, 1); E(b_cond, "vr_x", "lo")
    E(ldr_imm, 0, 4, O_RLX); E(subs_reg, 0, 5, 0); E(cmp_reg, 0, 1); E(b_cond, "vr_x", "lo")
    E(str_imm, 5, 4, O_RLX); E(adds_imm8, 6, 1); E(cmp_imm, 6, CAP_TOP); E(b_cond, "vr_w", "ls"); E(movs_imm, 6, 0)
    a.label("vr_w"); E(strb_imm, 6, 4, O_CAP)
    a.label("vr_x")
    imm32(0, P.PY); E(ldr_imm, 1, 0, 0); imm32(2, P.SIG); E(cmp_reg, 1, 2); bc("vg_x", "ne")          # poly's RAM not set up yet
    E(bl, L["c_pytot"]); E(cmp_imm, 0, MIN_V); bc("vg_x", "lo")
    if HOLD:                                                                            # the stock's steal countdowns topped up
        E(ldr_imm, 0, 4, O_HOLD); E(subs_reg, 0, 5, 0); E(cmp_imm, 0, HOLD_MS); E(b_cond, "vh_x", "lo"); E(str_imm, 5, 4, O_HOLD)
        for k in range(2):
            E(movs_imm, 0, 0); E(movw, 1, HOLD_BLK << 8); E(movw, 2, STEAL_CNT + k); E(bl, DSP_WRITE)
        a.label("vh_x")
    rd_dsp(Y_ISR); E(lsrs_imm, 6, 0, 8)
    rd_dsp(Y_BLK); E(lsrs_imm, 7, 0, 8)
    E(subs_reg, 0, 7, 6); E(lsls_imm, 0, 0, 22); E(lsrs_imm, 0, 0, 22); E(str_imm, 0, 4, O_M)      # r0 = the margin (10 bits)
    E(movw, 1, DRY); E(cmp_reg, 0, 1); E(b_cond, "vm_d", "ls"); E(movs_imm, 0, 0)                   # the ring ran dry: 0
    a.label("vm_d"); E(cmp_imm, 0, SHED_AT); bc("vg_x", "hs")
    E(ldr_imm, 1, 4, O_SHED); E(subs_reg, 1, 5, 1)                                     # r1 = since the last voice freed
    E(cmp_imm, 0, EMERG_AT); E(b_cond, "vm_g", "hs")
    E(cmp_imm, 1, GAP_E); bc("vg_x", "lo"); E(b, "vm_go")
    a.label("vm_g"); E(cmp_imm, 1, GAP); bc("vg_x", "lo")
    a.label("vm_go")
    E(bl, L["c_pyshed"]); E(cmp_imm, 0, 0); bc("vg_x", "eq")
    E(str_imm, 5, 4, O_SHED); E(ldr_imm, 0, 4, O_N); E(adds_imm8, 0, 1); E(str_imm, 0, 4, O_N)
    E(bl, L["c_pytot"]); E(cmp_imm, 0, CAP_MIN); E(b_cond, "vc_w", "hs"); E(movs_imm, 0, CAP_MIN)   # the cap = the voices left
    a.label("vc_w"); E(strb_imm, 0, 4, O_CAP)
    a.label("vg_x"); E(raw, popw(list(range(12)), lr=True)); E(b_w, prev["svc"])
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add, after poly with use_v9); the head of the DSP service chain."""
    import ct_fw
    import poly as P
    from thumb import b_w as bw_enc
    BASE = ct_fw.APP_BASE
    assert P.V9
    L = {k: int(report["poly"]["labels"][k], 16) for k in ("c_pytot", "c_pyshed")}
    prev = dict(svc=MP.bw_target(img, S14.SVC_HOOK, BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    img[S14.SVC_HOOK - BASE:S14.SVC_HOOK - BASE + 4] = bw_enc(S14.SVC_HOOK, labels["c_vgtick"])
    assert RAM + RSZ <= MX.MXR + 0x1F00
    return labels, code, prev
