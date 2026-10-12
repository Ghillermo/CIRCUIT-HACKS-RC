"""SC18 drum controls, DSP side (core 0).

Per drum d (0..3), state block DB(d) = X:$3A80 + 32*d (X:$3A80..$3AFF, cleared by sc_init: every default is 0):
   MB    mailbox from the ARM: bit 23 = tag (toggles on every message), bits 19..16 = code, bits 15..0 = signed delta
   MBL   last mailbox word applied (the DSP never writes MB: no race with the SHI writes)
   EXT   extended knob ranges from the ARM: bits 3..0 = start point (K4 left, 0..15), bits 7..4 = bitcrush (K6 left)
   PE    K1  pitch envelope        -64..63 (0 = off)            code 1
   HOLD  K3  hold / gate            0..127 (0 = off)             code 2
   LFO   K5  LFO amount            -64..63 (>0 tremolo, <0 vibrato)  code 3
   LSPD  Shift+K5 LFO speed        -64..63 (0 = ~1.4 Hz)          code 4
   EC    K7  envelope -> cutoff    -64..63                        code 5
   RES   Shift+K8 resonance         0..127                        code 6
   ENV, PH, BASE, HCNT, HGAIN, LOW, BAND, CRH, CRC, TRI, FF, FQ, FMODE, TG, TGN, CRN, CRM, SR5: runtime
Hooks (patched in both core-0 blocks):
   P:$20A4  jsr func_0020b3            -> jsr dctl   (mailbox, envelope, LFO, pitch modulation, filter / crush / tremolo setup;
                                                       ends with jmp $20B3)
   P:$20E0  move a,x:(r3+2) ; clr a   -> jsr dtrig  (trigger: base increment, envelope / LFO / hold restart, start point)
   P:$218F  jsr operand $2A67 (SC16)   -> dstage     (per sample on X:$2C02: hold gate, bitcrush, DJ filter, tremolo; jmp $2A67)
   P:$2129  move x:(r2+4),a           -> clr a      (the stock tilt EQ stays flat: K8 drives the DJ filter instead)
Tables live in P memory (read with movem): TEXP (pitch), TLFO (LFO rate), TF (filter), TCR (crush).
"""
from __future__ import annotations
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp56 as D  # noqa: E402
import masterfx_dsp as G  # noqa: E402

T, J, JCLR, JSET = G.T, G.J, G.JCLR, G.JSET
DB, STRIDE = 0x3A80, 32
(MB, MBL, EXT, PE, HOLD, LFO, LSPD, EC, RES, ENV, PH, BASE, HCNT, HGAIN, LOW, BAND, CRH, CRC, TRI, FF, FQ, FMODE, TG, TGN,
 CRN, CRM, SR5) = range(27)
CODE_OFF = {1: PE, 2: HOLD, 3: LFO, 4: LSPD, 5: EC, 6: RES}
UNIPOLAR = (2, 6)                     # codes with range 0..127 (others -64..63)
FS, NFR = 48000.0, 32
ENV_TAU = 0.1                         # s, shared by the pitch envelope and the envelope -> cutoff
PE_SEMIS = 24                         # K1 at +-64 -> +-24 semitones at the hit
VIB_SEMIS = 2                         # K5 fully left -> +-2 semitones vibrato
HOLD_K = 6                            # hold samples = (128 - K3)^2 * 6  (K3 = 1: ~2 s, K3 = 127: 6 samples)
HOLD_STEP = 0x020000                  # gate release: 1/64 per sample (~1.3 ms)
Q0, Q1 = 0.7071, 0.05                 # damping/2 at resonance 0 (Butterworth) and 127
FC0, FC1 = 30.0, 7000.0
HOOK_CTL, HOOK_TRIG, HOOK_MIX, HOOK_EQ = 0x20A4, 0x20E0, 0x218E, 0x2129
VOICE, SC16_MIX = 0x20B3, 0x2A67


def q24(x): return max(-0x800000, min(0x7FFFFF, int(round(x * 0x800000)))) & 0xFFFFFF


def tables():
    t = {}
    t["TEXP"] = [q24(min(0.9999999, 2 ** ((i - 24) / 12) / 4)) for i in range(49)]
    t["TLFO"] = [int(round(0.1 * 2 ** (r / 127 * math.log2(200)) * NFR / FS * (1 << 24))) for r in range(128)]
    t["TF"] = [q24(2 * math.sin(math.pi * FC0 * (FC1 / FC0) ** (i / 63) / FS)) for i in range(64)]
    # crush c = 1..15: hold N = 1 + c // 3 samples, keep 16 - (12 * c) // 15 bits (c = 15: 4 bits, 6 samples)
    t["TCR"] = [0, 0] + sum(([1 + c // 3, (0xFFFFFF << (24 - (16 - (12 * c) // 15))) & 0xFFFFFF] for c in range(1, 16)), [])
    return t


KENV = q24(math.exp(-NFR / (FS * ENV_TAU)))
QK = q24((Q0 - Q1) * 128 / 127)       # FQ = Q0 - (RES / 128) * QK


def X(off): return "x:(r6+$%x)" % off


def code(base):
    a = D.Asm(base)
    L = a.label
    tabs = tables()
    def e(*lines):
        for l in lines: a.emit(T(l))
    def tab(reg, name):                # reg += address of a P table
        a.emit(lambda t: T("add #>$%x,%s" % (t, reg)), name)
    def blk_from(src):                 # r6 = DB + 32 * (src - $9F)   (src = "r1" or "x:>$1ed6"; uses b)
        e("move r1,b" if src == "r1" else "move x:>$1ed6,b")
        e("sub #>$9f,b", "asl #5,b,b", "add #>$%x,b" % DB, "move b,r6"); a.emit(D.NOP)

    def pmod(t):
        """inline: x:(r3+2) = BASE * 2^(semis / 12), semis = PE*24/64*ENV + (LFO < 0: -LFO*2/64*TRI)  (uses a, b, x, y, r0)"""
        e("move %s,x1" % X(BASE), "move x1,a", "tst a"); a.emit(J("eq"), "pm_x" + t)
        e("move %s,a" % X(PE), "move a,b", "asl #6,a,a", "asl #5,b,b", "add b,a")   # 256 * semis-per-unit: PE * 96
        e("move a,x0", "move %s,y0" % X(ENV), "mpy y0,x0,a")
        e("move %s,b" % X(LFO), "tst b"); a.emit(J("ge"), "pm_nv" + t)
        e("neg b", "asl #3,b,b", "move b,x0", "move %s,y0" % X(TRI), "mac y0,x0,a")
        L("pm_nv" + t)
        e("add #>$%x,a" % (24 * 256))
        e("tst a"); a.emit(J("ge"), "pm_c1" + t); e("move #>0,a")
        L("pm_c1" + t); e("cmp #>$%x,a" % (48 * 256 - 1)); a.emit(J("le"), "pm_c2" + t); e("move #>$%x,a" % (48 * 256 - 1))
        L("pm_c2" + t)
        e("move a,b", "lsr #8,b", "and #>$ff,a", "move #0,a0", "asl #15,a,a", "move a,y1")
        tab("b", "TEXP")
        e("move b,r0"); a.emit(D.NOP)
        e("move p:(r0)+,x0", "move p:(r0),a", "sub x0,a", "move a,y0", "tfr x0,a", "mac y1,y0,a")
        e("move a,y0", "mpy x1,y0,a", "asl #2,a,a", "move a,x:(r3+$2)")
        L("pm_x" + t)

    # ================================================================ dctl (jsr from P:$20A4 instead of func_0020b3)
    # No jsr / do inside: the stack depth stays the stock one; ends with jmp $20B3 (its rts returns to P:$20A6).
    L("dctl")
    blk_from("r1")
    # ---- mailbox
    e("move %s,x0" % X(MB), "move %s,a" % X(MBL), "eor x0,a", "move a1,x1")
    a.emit(JCLR(23, "x1"), "dc_mbd")
    e("move x0,%s" % X(MBL))
    e("move x0,a", "lsr #16,a", "and #>$f,a", "move a1,y1", "move y1,a")       # (y1 -> a: clean a2, the tag made a negative)
    e("tst a"); a.emit(J("eq"), "dc_mbd")
    e("cmp #>6,a"); a.emit(J("gt"), "dc_mbd")
    e("move r6,b", "add a,b", "add #>2,b", "move b,r5"); a.emit(D.NOP)
    e("move x0,a", "and #>$ffff,a", "move a1,y0", "move y0,a", "cmp #>$8000,a"); a.emit(J("lt"), "dc_pos")
    e("sub #>$10000,a")
    L("dc_pos")
    e("move x:(r5),b", "add a,b")
    e("move #>$ffffc0,x0", "move #>$3f,x1")
    e("move y1,a", "cmp #>2,a"); a.emit(J("eq"), "dc_u")
    e("cmp #>6,a"); a.emit(J("ne"), "dc_cl")
    L("dc_u"); e("move #>0,x0", "move #>$7f,x1")
    L("dc_cl"); e("cmp x0,b", "tfr x0,b iflt", "cmp x1,b", "tfr x1,b ifgt", "move b,x:(r5)")
    L("dc_mbd")
    # ---- envelope (per block decay)
    e("move %s,x0" % X(ENV), "move #>$%x,y0" % KENV, "mpy y0,x0,a", "move a,%s" % X(ENV))
    # ---- LFO: phase += TLFO[LSPD + 64] (wraps), TRI = 2 |phase| - 1
    e("move %s,a" % X(LSPD), "add #>$%x,a" % 64)
    tab("a", "TLFO")
    e("move a,r0"); a.emit(D.NOP)
    e("move p:(r0),x0", "move %s,a" % X(PH), "add x0,a", "move a1,%s" % X(PH))
    e("move %s,a" % X(PH), "abs a", "asl a", "add #>$800000,a", "move a,%s" % X(TRI))
    # ---- pitch modulation
    pmod("c")
    # ---- filter: g = EQ (X:$A7+10d = x:(r2+4) = (v - 64) / 64): mode, index (+ EC * ENV), coefficient, damping
    e("move %s,x0" % X(EC), "move %s,y0" % X(ENV), "mpy y0,x0,b")             # b1 = EC * env (index offset)
    e("move x:(r2+$4),a", "asr #17,a,a")                                       # a1 = v - 64
    e("tst a"); a.emit(J("ne"), "dc_fm")
    e("move %s,x0" % X(EC), "move x0,a", "tst a"); a.emit(J("ne"), "dc_lpo")
    e("move #>0,x0", "move x0,%s" % X(FMODE)); a.emit(J("al"), "dc_fd")
    L("dc_lpo"); e("move #>$3f,a", "move #>1,x0"); a.emit(J("al"), "dc_ix")   # no filter but EC set: LP fully open
    L("dc_fm")
    e("move #>1,x0", "tst a"); a.emit(J("lt"), "dc_lp")
    e("move #>2,x0"); a.emit(J("al"), "dc_ix")                                 # HP: index = v - 64
    L("dc_lp"); e("add #>$40,a")                                               # LP: index = v
    L("dc_ix")
    e("move x0,%s" % X(FMODE))
    e("add b,a")
    e("tst a"); a.emit(J("ge"), "dc_i2"); e("move #>0,a")
    L("dc_i2"); e("cmp #>$3f,a"); a.emit(J("le"), "dc_i3"); e("move #>$3f,a")
    L("dc_i3")
    tab("a", "TF")
    e("move a,r0"); a.emit(D.NOP)
    e("move p:(r0),x0", "move x0,%s" % X(FF))
    e("move %s,a" % X(RES), "asl #16,a,a", "move a,x0", "move #>$%x,y0" % QK, "mpy y0,x0,b")
    e("move #>$%x,a" % q24(Q0), "sub b,a", "move a,%s" % X(FQ))
    L("dc_fd")
    # ---- tremolo target gain: TGN = 1 - depth * (TRI + 1) / 2, depth = LFO / 64 (LFO > 0)
    e("move #>$7fffff,x0", "move %s,a" % X(LFO), "tst a"); a.emit(J("le"), "dc_tg")
    e("asl #17,a,a", "move a,x1")
    e("move %s,a" % X(TRI), "asr a", "add #>$400000,a", "move a,y0", "mpy x1,y0,b")
    e("move #>$7fffff,a", "sub b,a", "move a,x0")
    L("dc_tg"); e("move x0,%s" % X(TGN))
    # ---- crush: c = EXT bits 7..4 -> CRN, CRM from TCR
    e("move %s,a" % X(EXT), "lsr #4,a", "and #>$f,a", "asl a")
    tab("a", "TCR")
    e("move a,r0"); a.emit(D.NOP)
    e("move p:(r0)+,x0", "move x0,%s" % X(CRN), "move p:(r0),x0", "move x0,%s" % X(CRM))
    a.emit(D.jmp(VOICE))

    # ================================================================ dtrig (jsr from P:$20E0, a = new increment)
    L("dtrig")
    e("move a,x:(r3+$2)")
    blk_from("r1")
    e("move a,%s" % X(BASE))
    e("move #>$7fffff,x0", "move x0,%s" % X(ENV), "move x0,%s" % X(HGAIN))
    e("move #>$400000,x0", "move x0,%s" % X(PH), "move #>0,x0", "move x0,%s" % X(TRI), "move x0,%s" % X(CRC))
    e("move %s,b" % X(HOLD), "tst b"); a.emit(J("eq"), "dt_h")
    e("move b1,x0", "move #>$80,b", "sub x0,b", "asl #16,b,b", "move b,x0", "mpy x0,x0,b")   # ((128 - h) / 128)^2
    e("asr #8,b,b", "move b,x0", "asl b", "add x0,b")                          # (128 - h)^2 * 6
    L("dt_h"); e("move b,%s" % X(HCNT))
    pmod("t")
    e("move %s,b" % X(EXT), "and #>$f,b", "tst b"); a.emit(J("eq"), "dt_z")
    e("asl #17,b,b", "move b,y0", "move x:(r3+$1),x0", "mpy y0,x0,a")         # position = length * s / 64 (= index / 4)
    a.emit(D.RTS)
    L("dt_z"); e("clr a"); a.emit(D.RTS)

    # ================================================================ dstage (jsr from P:$218E instead of SC16's mixhook)
    # Same stack level as SC16's mixhook (it also runs do loops there); ends with jmp $2A67 (SC16), which returns.
    L("dstage")
    blk_from("x:>$1ed6")
    e("move r5,%s" % X(SR5))
    # ---- hold / gate
    e("move %s,a" % X(HOLD), "tst a"); a.emit(J("eq"), "hl_x")
    e("move %s,b" % X(HCNT), "move %s,y0" % X(HGAIN), "move #>$%x,y1" % HOLD_STEP, "move #>$2c02,r0")
    a.emit(D.do_x, 0x3A, "hl_e")
    e("sub #1,b"); a.emit(J("ge"), "hl_g")
    e("move #>$ffffff,b", "move y0,a", "sub y1,a"); a.emit(J("ge"), "hl_s"); e("clr a")
    L("hl_s"); e("move a,y0")
    L("hl_g"); e("move x:(r0),x0", "mpy y0,x0,a")
    L("hl_e"); e("move a,x:(r0)+")
    e("move b,%s" % X(HCNT), "move y0,%s" % X(HGAIN))
    e("move y0,a", "tst a"); a.emit(J("ne"), "hl_x")
    e("move x:>$1ed8,r4"); a.emit(D.NOP)                                       # gate closed: end the voice
    e("move #>0,x0", "move x0,x:(r4+$6)", "move x0,x:(r4+$7)")
    L("hl_x")
    # ---- bitcrush
    e("move %s,y1" % X(CRN), "move y1,a", "tst a"); a.emit(J("eq"), "cr_x")
    e("move %s,b" % X(CRC), "move %s,x0" % X(CRH), "move %s,x1" % X(CRM), "move #>$2c02,r0")
    a.emit(D.do_x, 0x3A, "cr_e")
    e("sub #1,b"); a.emit(J("gt"), "cr_k")
    e("move x:(r0),a", "and x1,a", "move a1,x0", "tfr y1,b")
    L("cr_k"); a.emit(D.NOP)
    L("cr_e"); e("move x0,x:(r0)+")
    e("move b,%s" % X(CRC), "move x0,%s" % X(CRH))
    L("cr_x")
    # ---- DJ filter (Chamberlin SVF on half-scale input, damping 2 * FQ)
    e("move %s,x0" % X(FMODE), "move x0,a", "tst a"); a.emit(J("eq"), "fl_x")
    e("move %s,y0" % X(FF), "move %s,y1" % X(FQ), "move #>$2c02,r0")
    e("cmp #>1,a"); a.emit(J("ne"), "fl_hp")
    for mode in ("lp", "hp"):
        if mode == "hp": L("fl_hp")
        e("move %s,a" % X(LOW), "move %s,x0" % X(BAND))
        a.emit(D.do_x, 0x3A, "fl_e_" + mode)
        e("mac y0,x0,a")                                                       # low += f * band
        e("move x:(r0),b", "asr b", "sub a,b", "mac -x0,y1,b", "mac -x0,y1,b", "move b,x1")   # high
        e("tfr x0,b", "mac x1,y0,b", "move b,x0")                              # band += f * high
        e("tfr a,b" if mode == "lp" else "move x1,b", "asl b")
        L("fl_e_" + mode); e("move b,x:(r0)+")
        e("move a,%s" % X(LOW), "move x0,%s" % X(BAND)); a.emit(J("al"), "fl_x")
    L("fl_x")
    # ---- tremolo (gain ramps from TG to TGN over the block)
    e("move %s,a" % X(LFO), "tst a"); a.emit(J("le"), "tr_x")
    e("move %s,b" % X(TG), "move %s,a" % X(TGN), "sub b,a", "asr #5,a,a", "move a,x1", "move #>$2c02,r0")
    a.emit(D.do_x, 0x3A, "tr_e")
    e("add x1,b", "move b,y0", "move x:(r0),x0", "mpy y0,x0,a")
    L("tr_e"); e("move a,x:(r0)+")
    L("tr_x")
    e("move %s,x0" % X(TGN), "move x0,%s" % X(TG))
    e("move %s,r5" % X(SR5))
    a.emit(D.jmp(SC16_MIX))

    # ================================================================ tables (P memory)
    for name in ("TEXP", "TLFO", "TF", "TCR"):
        L(name)
        for w in tabs[name]: a.emit([w & 0xFFFFFF])
    return a.assemble()
