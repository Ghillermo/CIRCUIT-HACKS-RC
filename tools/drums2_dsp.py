"""SC18.1 drum controls, DSP side (core 0) — second version of drums_dsp.py (SC18 stays reproducible with that one).

Changes from SC18:
  * K1 = envelope shape (attack / decay, -64..63): left = slower attack (up to 250 ms, decay 40 ms), right = longer decay
    (40 ms .. ~1.5 s); Shift + K1 = envelope amount to the pitch (SC18's K1).  The same envelope drives K7 (-> filter).
  * K3 = ring modulator frequency (30 Hz .. 7 kHz), Shift + K3 = ring modulator amount (dry -> fully ring-modulated).
    Hold / gate removed.
  * Shift + K7 = filter mode, one step per turn: 0 DJ (LP left / HP right), 1 band-pass, 2 notch, 3 comb, 4 stock tilt EQ.
    K8 = frequency (comb: delay 6..255 samples = 190 Hz .. 8 kHz), Shift + K8 = resonance (comb: feedback).
    Modes 0-3 keep the stock tilt EQ flat by zeroing its smoothed value X:$A7+10d around the voice (saved, restored in dstage).
Per drum block DB(d) = X:$3A80 + 64*d (X:$3A80..$3B7F); comb buffers X:$3400 + 256*d (X:$3400..$37FF, modulo 256).
sc_init clears X:$3400..$3B7F (every default is 0).  Mailbox codes 1..9 -> offset 2 + code.
Hooks: P:$20A4 -> dctl, P:$20E0 -> dtrig, P:$218E -> dstage (as SC18); P:$2129 stays stock.
"""
from __future__ import annotations
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp56 as D  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import drums_dsp as D1  # noqa: E402

T, J, JCLR, JSET = G.T, G.J, G.JCLR, G.JSET
DB, STRIDE, SHIFT = 0x3A80, 64, 6
COMB, COMB_N = 0x3400, 256
CLR_FROM, CLR_END = COMB, DB + 4 * STRIDE
(MB, MBL, EXT, PE, RMF, LFO, LSPD, EC, RES, ENVS, RMA, FSEL,
 ENV, PH, BASE, EPH, LOW, BAND, CRH, CRC, TRI, FF, FQ, FMODE, TG, TGN, CRN, CRM, SR5, RS, RC, GSV, CWP, CD, ATK, DK, FSAV,
 SM4, SM5, TYPE, SLOPE, PASS, LOW2, BAND2, SAVL, SAVB) = range(46)
CODES = {1: PE, 2: RMF, 3: LFO, 4: LSPD, 5: EC, 6: RES, 7: ENVS, 8: RMA, 9: FSEL}
UNIPOLAR = (2, 6, 8)
N_MODES = 5                                   # 0 DJ, 1 band-pass, 2 notch, 3 comb, 4 tilt EQ (stock)
XTRA = False                                  # SC19.9: EXT bits 8-9 = distortion type (0 stock, 1 soft, 2 hard, 3 fold), bit 10 = filter slope (0 = 12 dB, 1 = 24 dB: the SVF twice)
SLOPE_PASS = False                            # with XTRA: EXT bit 10 = filter slope 24 dB (the SVF twice).  Dropped for SC19.9 (the user discarded it); the code stays as an option
COMPACT = False                               # SC36: TATK stored as its first 65 words (the rest is 0) and TDEC as its last 64 (the first 65 are equal): the
                                              # envelope index is clamped instead (ENVS <= 0 for TATK, ENVS >= 0 for TDEC); label TDEC = old TDEC + 64 (vcf21 compensates)
ABS = False                                   # SC19: mailbox messages carry the ABSOLUTE value (the ARM keeps the state in the project); default: deltas (SC18.1)
K3SPLIT = False                               # SC41.7 (use_k3split): the amp attack, the start point and the cut, written by the ARM into four new words
AINC, AENV, STARTF, ENDC = 46, 47, 48, 49     # (block words past the 46 above; sc_init clears them: 0 = none)


def use_k3split():
    """SC41.7 (the user, 2026-10-15: K3 «izquierda: decay, derecha: ataque, centro neutro»; Shift + K3 «izquierda: inicio, derecha: corte»).  The ARM computes
    and writes (the DSP service tick) per drum: AINC = the amp attack's increment per block (0 = no attack), STARTF = the start as a fraction of the sample's
    length (S / 128), ENDC = the cut as a fraction (E / 128).  The DSP:
      * dtrig: length = L - L x ENDC, position = L x STARTF (both 0: L and 0, exactly the stock's); with AINC != 0: AENV, TG, TGN = 0 (the hit starts silent);
      * dctl: with AINC != 0, AENV += AINC (limited to 1) and the block's target gain TGN = the tremolo's x AENV;
      * dstage: the gain ramp TG -> TGN runs whenever TGN != 1 (before: whenever the LFO amount > 0; the tremolo's TGN is 1 without LFO).
    The start point of EXT (bits 0-3) is not read any more (the ARM moves it into STARTF)."""
    global K3SPLIT
    K3SPLIT = True
FS, NFR = D1.FS, D1.NFR
ATK_MAX, DEC_BASE, DEC_OCT = 0.25, 0.040, 12  # s; decay doubles every 12 steps right of centre
RING_C0 = 0.9                                 # carrier amplitude after a hit (magic-circle oscillator)
COMB_FB = 0.95                                # feedback at resonance 127
HOOK_CTL, HOOK_TRIG, HOOK_MIX = D1.HOOK_CTL, D1.HOOK_TRIG, D1.HOOK_MIX
VOICE, SC16_MIX = D1.VOICE, D1.SC16_MIX
q24 = D1.q24


def tables():
    t = D1.tables()
    del t["TCR"]
    t["TCR"] = D1.tables()["TCR"]
    atk, dec = [], []
    for i in range(128):
        v = i - 64
        ta = -v / 64 * ATK_MAX if v < 0 else 0.0
        tau = DEC_BASE * (2 ** (v / DEC_OCT) if v > 0 else 1)
        atk.append(q24(min(0.9999999, NFR / (FS * ta))) if ta else 0)
        dec.append(q24(math.exp(-NFR / (FS * tau))))
    t["TATK"], t["TDEC"] = atk, dec
    t["TCOMB"] = [max(6, min(COMB_N - 1, int(round((COMB_N - 1) * (6 / (COMB_N - 1)) ** (k / 127))))) for k in range(128)]
    return t


QK, Q0 = D1.QK, D1.Q0
FBK = q24(COMB_FB * 128 / 127)               # FB = RES / 128 * FBK


def X(off): return "x:(r6+$%x)" % off


def sx(reg, off, write=False, rn=6):
    """the one-word `move x:(rn+off),reg` / `move reg,x:(rn+off)` (0 <= off < 64; the stock's form, see sampler_dsp.short_x)"""
    import sampler_dsp as SD
    assert 0 <= off < 64 and reg in SD.DDDD
    return [0x020080 | (off >> 6) << 16 | (off >> 1 & 0x1F) << 11 | rn << 8 | (off & 1) << 6 | (0 if write else 1) << 4 | SD.DDDD[reg]]


def code(base):
    a = D.Asm(base)
    L = a.label
    tabs = tables()
    def e(*lines):
        for l in lines: a.emit(T(l))
    def tab(reg, name): a.emit(lambda t: T("add #>$%x,%s" % (t, reg)), name)
    def blk_from(src):
        e("move r1,b" if src == "r1" else "move x:>$1ed6,b")
        e("sub #>$9f,b", "asl #%d,b,b" % SHIFT, "add #>$%x,b" % DB, "move b,r6"); a.emit(D.NOP)
    def ld_tab(name, idx_reg, dst):  # dst = TABLE[idx_reg] (idx_reg is a or b, clobbered; uses r0)
        tab(idx_reg, name); e("move %s,r0" % idx_reg); a.emit(D.NOP); e("move p:(r0),%s" % dst)

    def pmod(t):                     # as SC18 (drums_dsp), offsets of this layout
        e("move %s,x1" % X(BASE), "move x1,a", "tst a"); a.emit(J("eq"), "pm_x" + t)
        e("move %s,a" % X(PE), "move a,b", "asl #6,a,a", "asl #5,b,b", "add b,a")
        e("move a,x0", "move %s,y0" % X(ENV), "mpy y0,x0,a")
        e("move %s,b" % X(LFO), "tst b"); a.emit(J("ge"), "pm_nv" + t)
        e("neg b", "asl #3,b,b", "move b,x0", "move %s,y0" % X(TRI), "mac y0,x0,a")
        L("pm_nv" + t)
        e("add #>$%x,a" % (24 * 256))
        e("tst a"); a.emit(J("ge"), "pm_c1" + t); e("move #>0,a")
        L("pm_c1" + t); e("cmp #>$%x,a" % (48 * 256 - 1)); a.emit(J("le"), "pm_c2" + t); e("move #>$%x,a" % (48 * 256 - 1))
        L("pm_c2" + t)
        e("move a,b", "lsr #8,b", "and #>$ff,a", "move #0,a0", "asl #15,a,a", "move a,y1")
        tab("b", "TEXP"); e("move b,r0"); a.emit(D.NOP)
        e("move p:(r0)+,x0", "move p:(r0),a", "sub x0,a", "move a,y0", "tfr x0,a", "mac y1,y0,a")
        e("move a,y0", "mpy x1,y0,a", "asl #2,a,a", "move a,x:(r3+$2)")
        L("pm_x" + t)

    # ================================================================ dctl (jsr from P:$20A4; no jsr / do inside)
    L("dctl")
    blk_from("r1")
    # ---- mailbox
    e("move %s,x0" % X(MB), "move %s,a" % X(MBL), "eor x0,a", "move a1,x1")
    a.emit(JCLR(23, "x1"), "dc_mbd")
    e("move x0,%s" % X(MBL))
    e("move x0,a", "lsr #16,a", "and #>$f,a", "move a1,y1", "move y1,a")
    e("tst a"); a.emit(J("eq"), "dc_mbd")
    e("cmp #>9,a"); a.emit(J("gt"), "dc_mbd")
    e("move r6,b", "add a,b", "add #>2,b", "move b,r5"); a.emit(D.NOP)
    e("move x0,a", "and #>$ffff,a", "move a1,y0", "move y0,a", "cmp #>$8000,a"); a.emit(J("lt"), "dc_pos")
    e("sub #>$10000,a")
    L("dc_pos")
    e("move y1,b", "cmp #>9,b"); a.emit(J("ne"), "dc_val")
    if ABS:
        # code 9: filter mode = value (0..4, anything else 0)
        e("tfr a,b", "tst b"); a.emit(J("lt"), "dc_m0"); e("cmp #>%d,b" % (N_MODES - 1)); a.emit(J("le"), "dc_ms")
        L("dc_m0"); e("move #>0,b")
        L("dc_ms"); e("move b,x:(r5)"); a.emit(J("al"), "dc_mbd")
        L("dc_val")
        e("tfr a,b")
    else:
        # code 9: filter mode += sign(delta), wraps 0..4
        e("move x:(r5),b", "tst a"); a.emit(J("lt"), "dc_md")
        e("add #>1,b", "cmp #>%d,b" % (N_MODES - 1)); a.emit(J("le"), "dc_ms"); e("move #>0,b"); a.emit(J("al"), "dc_ms")
        L("dc_md"); e("sub #>1,b"); a.emit(J("ge"), "dc_ms"); e("move #>%d,b" % (N_MODES - 1))
        L("dc_ms"); e("move b,x:(r5)"); a.emit(J("al"), "dc_mbd")
        L("dc_val")
        e("move x:(r5),b", "add a,b")
    e("move #>$ffffc0,x0", "move #>$3f,x1")
    e("move y1,a")
    for c in UNIPOLAR:
        e("cmp #>%d,a" % c); a.emit(J("eq"), "dc_u")
    a.emit(J("al"), "dc_cl")
    L("dc_u"); e("move #>0,x0", "move #>$7f,x1")
    L("dc_cl"); e("cmp x0,b", "tfr x0,b iflt", "cmp x1,b", "tfr x1,b ifgt", "move b,x:(r5)")
    L("dc_mbd")
    # ---- envelope: ATK / DK from ENVS; attack phase (EPH = 1) ramps up, then decay
    if COMPACT:
        e("move %s,b" % X(ENVS), "clr a", "cmp a,b", "tfr a,b ifgt", "add #>$40,b"); ld_tab("TATK", "b", "x0"); e("move x0,%s" % X(ATK))
        e("move %s,b" % X(ENVS), "clr a", "cmp a,b", "tfr a,b iflt"); ld_tab("TDEC", "b", "x0"); e("move x0,%s" % X(DK))
    else:
        e("move %s,b" % X(ENVS), "add #>$40,b"); ld_tab("TATK", "b", "x0"); e("move x0,%s" % X(ATK))
        e("move %s,b" % X(ENVS), "add #>$40,b"); ld_tab("TDEC", "b", "x0"); e("move x0,%s" % X(DK))
    e("move %s,a" % X(EPH), "tst a"); a.emit(J("eq"), "dc_dec")
    e("move %s,a" % X(ENV), "move %s,x0" % X(ATK), "add x0,a", "cmp #>$7fffff,a"); a.emit(J("lt"), "dc_atk")
    e("move #>$7fffff,a", "move #>0,x0", "move x0,%s" % X(EPH))
    L("dc_atk"); e("move a,%s" % X(ENV)); a.emit(J("al"), "dc_env")
    L("dc_dec"); e("move %s,x0" % X(ENV), "move %s,y0" % X(DK), "mpy y0,x0,a", "move a,%s" % X(ENV))
    L("dc_env")
    # ---- LFO
    e("move %s,a" % X(LSPD), "add #>$40,a"); ld_tab("TLFO", "a", "x0")
    e("move %s,a" % X(PH), "add x0,a", "move a1,%s" % X(PH))
    e("move %s,a" % X(PH), "abs a", "asl a", "add #>$800000,a", "move a,%s" % X(TRI))
    # ---- pitch
    pmod("c")
    # ---- filter: FSEL 4 = stock tilt EQ; else zero the EQ's smoothed value while the voice plays (restored in dstage)
    e("move #>0,x0", "move x0,%s" % X(FMODE))
    e("move %s,a" % X(FSEL), "cmp #>4,a"); a.emit(J("eq"), "dc_fd")
    e("move x:(r2+$4),x0", "move x0,%s" % X(GSV))                            # GSV = EQ value (filter frequency)
    e("move x:(r1),a", "tst a"); a.emit(J("ne"), "dc_sv")                    # trigger pending or voice active: zero it
    e("move x:(r3+$6),a", "tst a"); a.emit(J("eq"), "dc_g")
    L("dc_sv")
    e("move #>0,x1", "move x1,x:(r2+$4)", "move #>1,x1", "move x1,%s" % X(FSAV))
    L("dc_g")
    e("move %s,a" % X(GSV), "asr #17,a,a")                                       # a1 = v - 64
    e("move %s,x0" % X(EC), "move %s,y0" % X(ENV), "mpy y0,x0,b")             # b1 = EC * env
    e("move %s,x1" % X(FSEL), "move x1,y1")                                     # y1 = mode
    e("move a,x1")                                                               # x1 = v - 64
    # comb (3): index = v + 2 * EC * env over 0..127 -> CD ; feedback in FQ
    e("move y1,a", "cmp #>3,a"); a.emit(J("ne"), "dc_svf")
    e("move x1,a", "add #>$40,a", "add b,a", "add b,a")
    e("tst a"); a.emit(J("ge"), "dc_c1"); e("move #>0,a")
    L("dc_c1"); e("cmp #>$7f,a"); a.emit(J("le"), "dc_c2"); e("move #>$7f,a")
    L("dc_c2"); ld_tab("TCOMB", "a", "x0"); e("move x0,%s" % X(CD))
    e("move %s,a" % X(RES), "asl #16,a,a", "move a,x0", "move #>$%x,y0" % FBK, "mpy y0,x0,a", "move a,%s" % X(FQ))
    e("move #>5,x0", "move x0,%s" % X(FMODE)); a.emit(J("al"), "dc_fd")
    L("dc_svf")
    e("move y1,a", "tst a"); a.emit(J("ne"), "dc_bp")
    # DJ (0): as SC18
    e("move x1,a", "tst a"); a.emit(J("ne"), "dc_fm")
    e("move %s,x0" % X(EC), "move x0,a", "tst a"); a.emit(J("eq"), "dc_fd")
    e("move #>$3f,a", "move #>1,x0"); a.emit(J("al"), "dc_ix")
    L("dc_fm"); e("move #>1,x0", "tst a"); a.emit(J("lt"), "dc_lp")
    e("move #>2,x0"); a.emit(J("al"), "dc_ix")
    L("dc_lp"); e("add #>$40,a"); a.emit(J("al"), "dc_ix")
    L("dc_bp")                                                                   # band-pass (1) / notch (2): index = v / 2
    e("move #>3,x0", "cmp #>1,a"); a.emit(J("eq"), "dc_bn"); e("move #>4,x0")
    L("dc_bn"); e("move x1,a", "add #>$40,a", "asr a")
    L("dc_ix")
    e("move x0,%s" % X(FMODE))
    e("add b,a")
    e("tst a"); a.emit(J("ge"), "dc_i2"); e("move #>0,a")
    L("dc_i2"); e("cmp #>$3f,a"); a.emit(J("le"), "dc_i3"); e("move #>$3f,a")
    L("dc_i3"); ld_tab("TF", "a", "x0"); e("move x0,%s" % X(FF))
    e("move %s,a" % X(RES), "asl #16,a,a", "move a,x0", "move #>$%x,y0" % QK, "mpy y0,x0,b")
    e("move #>$%x,a" % q24(Q0), "sub b,a", "move a,%s" % X(FQ))
    L("dc_fd")
    # ---- tremolo target gain
    e("move #>$7fffff,x0", "move %s,a" % X(LFO), "tst a"); a.emit(J("le"), "dc_tg")
    e("asl #17,a,a", "move a,x1")
    e("move %s,a" % X(TRI), "asr a", "add #>$400000,a", "move a,y0", "mpy x1,y0,b")
    e("move #>$7fffff,a", "sub b,a", "move a,x0")
    L("dc_tg")
    if K3SPLIT:                                                                  # amp attack: AENV += AINC (limited), TGN = gain x AENV
        a.emit(sx("a", AINC)); e("tst a"); a.emit(J("eq"), "dc_tgs")
        a.emit(sx("b", AENV)); e("add a,b"); a.emit(sx("b", AENV, True))
        a.emit(sx("y0", AENV)); e("mpy y0,x0,b", "move b,x0")
        L("dc_tgs")
    e("move x0,%s" % X(TGN))
    if XTRA:
        e("move %s,a" % X(EXT), "lsr #8,a", "and #>3,a", "move a1,%s" % X(TYPE))
        if SLOPE_PASS: e("move %s,a" % X(EXT), "lsr #10,a", "and #>1,a", "move a1,%s" % X(SLOPE))
    # ---- crush
    e("move %s,a" % X(EXT), "lsr #4,a", "and #>$f,a", "asl a")
    tab("a", "TCR"); e("move a,r0"); a.emit(D.NOP)
    e("move p:(r0)+,x0", "move x0,%s" % X(CRN), "move p:(r0),x0", "move x0,%s" % X(CRM))
    a.emit(D.jmp(VOICE))

    # ================================================================ dtrig (jsr from P:$20E0, a = new increment)
    L("dtrig")
    e("move a,x:(r3+$2)")
    blk_from("r1")
    e("move a,%s" % X(BASE))
    e("move %s,x0" % X(ATK), "move x0,b", "tst b"); a.emit(J("ne"), "dt_a")
    e("move #>$7fffff,x0", "move x0,%s" % X(ENV), "move #>0,x0", "move x0,%s" % X(EPH)); a.emit(J("al"), "dt_e")
    L("dt_a"); e("move #>0,x0", "move x0,%s" % X(ENV), "move #>1,x0", "move x0,%s" % X(EPH))
    L("dt_e")
    e("move #>$400000,x0", "move x0,%s" % X(PH), "move #>0,x0", "move x0,%s" % X(TRI), "move x0,%s" % X(CRC))
    if K3SPLIT:                                                                  # an amp attack: the hit starts silent (x0 = 0 here)
        a.emit(sx("b", AINC)); e("tst b"); a.emit(J("eq"), "dt_na")
        a.emit(sx("x0", AENV, True)); a.emit(sx("x0", TG, True)); a.emit(sx("x0", TGN, True))
        L("dt_na")
    e("move x0,%s" % X(RS), "move #>$%x,x0" % q24(RING_C0), "move x0,%s" % X(RC))
    pmod("t")
    if K3SPLIT:                                                                  # length L - L x ENDC, position L x STARTF
        a.emit(sx("x0", 1, rn=3)); a.emit(sx("y0", ENDC)); e("mpy y0,x0,a", "tfr x0,b", "sub a,b"); a.emit(sx("b", 1, True, rn=3))
        a.emit(sx("y0", STARTF)); e("mpy y0,x0,a")
        a.emit(D.RTS)
    else:
        e("move %s,b" % X(EXT), "and #>$f,b", "tst b"); a.emit(J("eq"), "dt_z")
        e("asl #17,b,b", "move b,y0", "move x:(r3+$1),x0", "mpy y0,x0,a")
        a.emit(D.RTS)
        L("dt_z"); e("clr a"); a.emit(D.RTS)

    # ================================================================ dstage (jsr from P:$218E; X:$2C02 = 32 mono samples)
    L("dstage")
    blk_from("x:>$1ed6")
    e("move r5,%s" % X(SR5))
    # ---- restore the stock EQ value zeroed by dctl
    e("move %s,a" % X(FSAV), "tst a"); a.emit(J("eq"), "st_nr")
    e("move x:>$1ed7,r4"); a.emit(D.NOP)
    e("move %s,x0" % X(GSV), "move x0,x:(r4+$4)", "move #>0,x0", "move x0,%s" % X(FSAV))
    L("st_nr")
    # ---- ring modulator: c rotates (magic circle, f = TF[RMF / 2]); out = x + amt * (x * c - x)
    e("move %s,a" % X(RMA), "tst a"); a.emit(J("eq"), "rm_x")
    e("asl #16,a,a", "move a,y1")                                               # y1 = amount (RMA / 128)
    e("move %s,b" % X(RMF), "asr b"); ld_tab("TF", "b", "x1")                    # x1 = f
    e("move %s,a" % X(RS), "move %s,b" % X(RC), "move #>$2c02,r0")
    a.emit(D.do_x, 0x3A, "rm_e")
    e("move b,y0", "mac x1,y0,a")                                               # s += f * c
    e("move a,y0", "mac -x1,y0,b")                                              # c -= f * s
    e("move a,%s" % X(SM4))                                                     # keep s (only 2 accumulators)
    e("move x:(r0),x0", "move b,y0", "mpy y0,x0,a", "move a,y0")              # y0 = x * c
    e("move x0,a", "neg a", "add y0,a", "move a,y0", "move x0,a", "mac y1,y0,a")   # x + amt * (x*c - x)
    e("move a,x:(r0)+", "move %s,a" % X(SM4))
    L("rm_e"); a.emit(D.NOP)
    e("move a,%s" % X(RS), "move b,%s" % X(RC))
    L("rm_x")
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
    if XTRA:
        # ---- distortion type on top of the stock one: drive u = x * (1 + 8 d), d = the stock distortion value (smoothed, X:$A6 + 10 voice = x:(r4 + 3), 0..1)
        #      1 soft: u limited to +-1, y = u + (u - u^3) / 2;  2 hard: u limited (the limiter of the accumulator read);  3 fold: u folded into +-1 (triangle)
        e("move %s,a" % X(TYPE), "tst a"); a.emit(J("eq"), "ds_x")
        e("move x:>$1ed7,r4"); a.emit(D.NOP)
        e("move x:(r4+$3),y1", "move #>$7fffff,x1", "move #>$800001,y0", "move #>$2c02,r0")
        e("cmp #>2,a"); a.emit(J("eq"), "ds_hard")
        e("cmp #>3,a"); a.emit(J("eq"), "ds_fold")
        a.emit(D.do_x, 0x3A, "ds_se")                                            # soft
        e("move x:(r0),x0", "mpy x0,y1,b", "asl #3,b,b", "add x0,b")
        e("move b,x0", "mpy x0,x0,a", "move a,y0")
        e("mpy y0,x0,a", "tfr x0,b", "sub a,b", "asr b")
        e("move x0,a", "add b,a")
        L("ds_se"); e("move a,x:(r0)+")
        e("move #>$800001,y0"); a.emit(J("al"), "ds_x")
        L("ds_hard")
        a.emit(D.do_x, 0x3A, "ds_he")
        e("move x:(r0),x0", "mpy x0,y1,b", "asl #3,b,b", "add x0,b")
        L("ds_he"); e("move b,x:(r0)+")
        a.emit(J("al"), "ds_x")
        L("ds_fold")
        a.emit(D.do_x, 0x3A, "ds_fe")
        e("move x:(r0),x0", "mpy x0,y1,b", "asl #3,b,b", "add x0,b")
        for n in range(3):
            e("cmp x1,b"); a.emit(J("le"), "ds_f%da" % n); e("neg b", "add x1,b", "add x1,b")
            L("ds_f%da" % n); e("cmp y0,b"); a.emit(J("ge"), "ds_f%db" % n); e("neg b", "sub x1,b", "sub x1,b")
            L("ds_f%db" % n); a.emit(D.NOP)
        L("ds_fe"); e("move b,x:(r0)+")
        L("ds_x")
    # ---- filters: FMODE 1 LP, 2 HP, 3 band-pass, 4 notch (SVF), 5 comb
    L("fl_again")
    e("move %s,x0" % X(FMODE), "move x0,a", "tst a"); a.emit(J("eq"), "fl_x")
    e("cmp #>5,a"); a.emit(J("eq"), "fl_comb")
    e("move %s,y0" % X(FF), "move %s,y1" % X(FQ), "move #>$2c02,r0")
    for m, name in ((1, "lp"), (2, "hp"), (3, "bp"), (4, "nt")):
        if m < 4:
            e("cmp #>%d,a" % m); a.emit(J("eq"), "fl_" + name)
    a.emit(J("al"), "fl_nt")
    for m, name in ((1, "lp"), (2, "hp"), (3, "bp"), (4, "nt")):
        L("fl_" + name)
        e("move %s,a" % X(LOW), "move %s,x0" % X(BAND))
        a.emit(D.do_x, 0x3A, "fl_e_" + name)
        e("mac y0,x0,a")
        e("move x:(r0),b", "asr b", "sub a,b", "mac -x0,y1,b", "mac -x0,y1,b", "move b,x1")
        e("tfr x0,b", "mac x1,y0,b", "move b,x0")
        if name == "lp": e("tfr a,b", "asl b")
        elif name == "hp": e("move x1,b", "asl b")
        elif name == "bp": e("tfr x0,b", "asl b")
        else: e("tfr a,b", "add x1,b", "asl b")                                 # notch = low + high
        L("fl_e_" + name); e("move b,x:(r0)+")
        e("move a,%s" % X(LOW), "move x0,%s" % X(BAND)); a.emit(J("al"), "fl_pass" if XTRA and SLOPE_PASS else "fl_x")
    if XTRA and SLOPE_PASS:
        # 24 dB: the same SVF a second time over the output, with its own state (LOW2 / BAND2 swapped into LOW / BAND for the pass and back after it)
        L("fl_pass")
        e("move %s,a" % X(SLOPE), "tst a"); a.emit(J("eq"), "fl_fin")
        e("move %s,a" % X(PASS), "tst a"); a.emit(J("ne"), "fl_fin")
        e("move #>1,x0", "move x0,%s" % X(PASS))
        e("move %s,x0" % X(LOW), "move x0,%s" % X(SAVL), "move %s,x0" % X(BAND), "move x0,%s" % X(SAVB))
        e("move %s,x0" % X(LOW2), "move x0,%s" % X(LOW), "move %s,x0" % X(BAND2), "move x0,%s" % X(BAND))
        a.emit(J("al"), "fl_again")
        L("fl_fin")
        e("move %s,a" % X(PASS), "tst a"); a.emit(J("eq"), "fl_x")
        e("move %s,x0" % X(LOW), "move x0,%s" % X(LOW2), "move %s,x0" % X(BAND), "move x0,%s" % X(BAND2))
        e("move %s,x0" % X(SAVL), "move x0,%s" % X(LOW), "move %s,x0" % X(SAVB), "move x0,%s" % X(BAND))
        e("move #>0,x0", "move x0,%s" % X(PASS)); a.emit(J("al"), "fl_x")
    # comb: y = (1 - fb) * x + fb * buf[n - D] ; buf[n] = y   (modulo-256 buffer per drum)
    L("fl_comb")
    e("move m4,%s" % X(SM4), "move m5,%s" % X(SM5))
    e("move #>$%x,m4" % (COMB_N - 1), "move #>$%x,m5" % (COMB_N - 1))
    e("move %s,r4" % X(CWP), "move %s,n5" % X(CD))
    e("move r4,b", "and #>$%x,b" % (COMB_N - 1))                               # keep the pointer inside this drum's buffer
    e("move x:>$1ed6,a", "sub #>$9f,a", "asl #8,a,a", "add #>$%x,a" % COMB, "add a,b", "move b,r4")
    e("move %s,y1" % X(FQ), "move #>$7fffff,a", "sub y1,a", "move a,y0")        # y0 = 1 - fb, y1 = fb
    e("move #>$2c02,r0"); a.emit(D.NOP)
    e("move r4,r5"); a.emit(D.NOP); e("move (r5)-n5")
    a.emit(D.do_x, 0x3A, "cb_e")
    e("move x:(r0),x0", "mpy y0,x0,a", "move x:(r5)+,x1", "mac y1,x1,a", "move a,x:(r4)+")
    L("cb_e"); e("move a,x:(r0)+")
    e("move r4,%s" % X(CWP))
    e("move %s,m4" % X(SM4), "move %s,m5" % X(SM5))
    L("fl_x")
    # ---- tremolo
    if K3SPLIT:
        a.emit(sx("a", TGN)); e("cmp #>$7fffff,a"); a.emit(J("eq"), "tr_x")
    else:
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
    for name in ("TEXP", "TLFO", "TF", "TCR", "TATK", "TDEC", "TCOMB"):
        L(name)
        ws = tabs[name]
        if COMPACT and name == "TATK":
            assert not any(ws[65:]); ws = ws[:65]
        if COMPACT and name == "TDEC":
            assert len(set(ws[:65])) == 1; ws = ws[64:]
        for w in ws: a.emit([w & 0xFFFFFF])
    return a.assemble()
