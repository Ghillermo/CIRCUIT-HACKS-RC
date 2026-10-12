"""SC20: VCF / VCA for the audio inputs of the MIDI tracks (DSP side, core 0).

One "voice" per MIDI track (MIDI 1 = audio input 1 or, with the Setup's reverb -> strip 3 flag, the reverb return; MIDI 2 = input 2 / the delay return):
  input -> VCF (bipolar: low-pass left, high-pass right, centre = off) -> drive + soft saturation -> VCA (ADSR envelope by the gate of the track, LFO tremolo, level)
Processed IN PLACE, before the mixer strips (level, pan, sends, side-chain, main volume all act after it), so the mixer, the delay and the reverb get the processed signal:
  P:$23C  jsr premix  -> jsr vpre : control for every active voice, then the line inputs (the Y ring, frames [in1, in2]) in place; ends with jmp premix (tail call, same stack depth)
  P:$D21  jsr fx_cap (SC17.5+; its last jmp $9F is patched to jmp vret) -> vret: the FX returns (Y:$880 reverb, Y:$9C0 delay, frames [L, R]) of the voices whose strip
          takes the return (X:$3A00 bit 0 / 1), in place; ends with jmp $9F (SC10 returns).  The synth sources (P:$9C3) and the fx_cap capture happen before: they hear the clean signal.
Voice block (48 words at X:$3B80 + 48 t, t = 0 / 1; absolute values from the ARM through the mailbox, as the drums):
  +0 mailbox (tag << 23 | code << 16 | value16), +1 last tag, +1 + code = the value of code 1..22:
  1 FILT (-64..63, +-2 = off)  2 RES (0..127)  3 ENVF (-64..63, envelope -> cutoff)  4 LFOF (LFO -> cutoff)  5 ATK  6 DEC  7 SUS  8 REL  9 DRIVE  10 LEVEL (127 = unity)
  11 LRATE  12 LFOV (tremolo depth)  13 LSHAPE (0 triangle, 1 square, 2 saw, 3 reverse saw)  14 KEY (note -> cutoff, -64..63)  15 VELE (velocity -> level)
  16 VMODE (0 open: the VCA does not use the envelope, 1 gate, 2 LFO only)  17 GATE (0 / 1)  18 NOTE  19 ACT (voice on)  20 VEL  21 TRIG (any value: restart the envelope)
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp56 as D  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import drums_dsp as D1  # noqa: E402

T, J, JCLR = G.T, G.J, G.JCLR
VB0, VBS = 0x3B80, 48
SAV = 0x3BE0                                   # register save area (16 words): X:$3BE0..$3BEF; $3BF0 = track counter
TCNT = 0x3BF0
FLAGS = 0x3A00                                 # X:$3A00 bit 0 reverb -> strip 3, bit 1 delay -> strip 4 (SC14.2+)
RING_PTR = 0xFFD                               # y:$FFD = first frame of the block
RET_BUF = (0x880, 0x9C0)                       # Y: reverb (MIDI 1), delay (MIDI 2); frames [L, R]
(MB, MBL) = (0, 1)
P_FILT, P_RES, P_ENVF, P_LFOF, P_ATK, P_DEC, P_SUS, P_REL, P_DRIVE, P_LEVEL, P_LRATE, P_LFOV, P_LSHAPE, P_KEY, P_VELE, P_VMODE = range(2, 18)
GATE, NOTE, ACT, VEL, GNEW = 18, 19, 20, 21, 22
ENV, STG, PH, LV, GCUR, GINC, GT, FF, FQ, FMODE, DRVF, VCAON, LOW0, BAND0, LOW1, BAND1 = range(23, 39)
ATKINC, DKC, RKC, SUSF, GINIT, ACTP, GRUN = 39, 40, 41, 42, 43, 44, 45
N_CODES = 21
QK, Q0 = D1.QK, D1.Q0
q24 = D1.q24


def code(base, tabs, premix, ret_old):
    """tabs: P addresses of TATK, TDEC, TLFO, TF (drums2_dsp); premix / ret_old: where vpre / vret continue (SC10's premix, the old operand of the P:$D21 chain)."""
    a = D.Asm(base)
    L = a.label
    def e(*lines):
        for l in lines: a.emit(T(l))
    def X(off): return "x:(r6+$%x)" % off
    def ld_tab(name, idx_reg, dst):           # dst = TABLE[idx_reg] (idx_reg is a or b, clobbered; uses r0)
        e("add #>$%x,%s" % (tabs[name], idx_reg), "move %s,r0" % idx_reg); a.emit(D.NOP); e("move p:(r0),%s" % dst)
    def ld(addr, reg): e("move x:>$%x,%s" % (addr, reg))
    def st(reg, addr): e("move %s,x:>$%x" % (reg, addr))

    # ================================================================ control of one voice (r6 = block); falls through; clobbers a, b, x0, x1, y0, y1, r0, r7
    def mailbox(p):
        # ---- mailbox
        e("move %s,x0" % X(MB), "move %s,a" % X(MBL), "eor x0,a", "move a1,x1")
        a.emit(JCLR(23, "x1"), p + "mbd")
        e("move x0,%s" % X(MBL), "move x0,a", "lsr #16,a", "and #>$1f,a", "move a1,y1", "move y1,a", "tst a"); a.emit(J("eq"), p + "mbd")
        e("cmp #>%d,a" % N_CODES); a.emit(J("gt"), p + "mbd")
        e("move r6,b", "add a,b", "add #>1,b", "move b,r7"); a.emit(D.NOP)
        e("move x0,a", "and #>$ffff,a", "move a1,y0", "move y0,a", "cmp #>$8000,a"); a.emit(J("lt"), p + "pos")
        e("sub #>$10000,a")
        L(p + "pos"); e("move a,x:(r7)")
        L(p + "mbd")

    def control(p):
        # ---- voice switched on: restart
        e("move %s,a" % X(ACTP), "tst a"); a.emit(J("ne"), p + "ao")
        e("move #>1,x0", "move x0,%s" % X(ACTP), "move x0,%s" % X(GINIT), "move #>0,x0", "move x0,%s" % X(ENV), "move x0,%s" % X(STG))
        L(p + "ao")
        # ---- envelope
        e("move %s,a" % X(GNEW), "tst a"); a.emit(J("eq"), p + "ng")
        e("move #>0,x0", "move x0,%s" % X(GNEW), "move %s,a" % X(P_ATK), "tst a"); a.emit(J("ne"), p + "ga")
        e("move #>$7fffff,x0", "move x0,%s" % X(ENV), "move #>2,x0", "move x0,%s" % X(STG)); a.emit(J("al"), p + "ng")
        L(p + "ga"); e("move #>0,x0", "move x0,%s" % X(ENV), "move #>1,x0", "move x0,%s" % X(STG))
        L(p + "ng")
        e("move %s,a" % X(GATE), "tst a"); a.emit(J("ne"), p + "go")            # gate off: stages 1..3 -> release
        e("move %s,a" % X(STG), "tst a"); a.emit(J("eq"), p + "go"); e("cmp #>4,a"); a.emit(J("ge"), p + "go")
        e("move #>4,x0", "move x0,%s" % X(STG))
        L(p + "go")
        e("move %s,b" % X(P_ATK), "asr b", "move #>63,a", "sub b,a"); ld_tab("TATK", "a", "x0"); e("move x0,%s" % X(ATKINC))
        e("move %s,b" % X(P_DEC), "asr b", "add #>64,b"); ld_tab("TDEC", "b", "x0"); e("move x0,%s" % X(DKC))
        e("move %s,b" % X(P_REL), "asr b", "add #>64,b"); ld_tab("TDEC", "b", "x0"); e("move x0,%s" % X(RKC))
        e("move %s,a" % X(P_SUS), "asl #16,a,a", "move a,%s" % X(SUSF))
        e("move %s,a" % X(STG), "tst a"); a.emit(J("eq"), p + "e0")
        e("cmp #>1,a"); a.emit(J("eq"), p + "e1"); e("cmp #>2,a"); a.emit(J("eq"), p + "e2"); e("cmp #>3,a"); a.emit(J("eq"), p + "e3")
        # 4 release: ENV *= RKC; below 1/256: idle
        e("move %s,x0" % X(ENV), "move %s,y0" % X(RKC), "mpy y0,x0,a", "move a,%s" % X(ENV), "cmp #>$8000,a"); a.emit(J("ge"), p + "ee")
        L(p + "e0"); e("move #>0,x0", "move x0,%s" % X(ENV), "move x0,%s" % X(STG)); a.emit(J("al"), p + "ee")
        L(p + "e1")                                                              # attack: ENV += ATKINC
        e("move %s,a" % X(ENV), "move %s,x0" % X(ATKINC), "add x0,a", "cmp #>$7fffff,a"); a.emit(J("lt"), p + "e1s")
        e("move #>$7fffff,a", "move #>2,x0", "move x0,%s" % X(STG))
        L(p + "e1s"); e("move a,%s" % X(ENV)); a.emit(J("al"), p + "ee")
        L(p + "e2")                                                              # decay: ENV = SUS + (ENV - SUS) * DKC
        e("move %s,x0" % X(SUSF), "move %s,a" % X(ENV), "sub x0,a", "move a,y1", "move %s,y0" % X(DKC), "mpy y1,y0,a", "add x0,a", "move a,%s" % X(ENV))
        e("move %s,a" % X(ENV), "sub x0,a", "cmp #>$2000,a"); a.emit(J("gt"), p + "ee")
        e("move x0,%s" % X(ENV), "move #>3,x0", "move x0,%s" % X(STG)); a.emit(J("al"), p + "ee")
        L(p + "e3"); e("move %s,x0" % X(SUSF), "move x0,%s" % X(ENV))
        L(p + "ee")
        # ---- LFO: PH += TLFO[LRATE]; LV by shape
        e("move %s,a" % X(P_LRATE)); ld_tab("TLFO", "a", "x0")
        e("move %s,a" % X(PH), "add x0,a", "move a1,%s" % X(PH))
        e("move %s,a" % X(P_LSHAPE), "tst a"); a.emit(J("ne"), p + "l1")
        e("move %s,a" % X(PH), "abs a", "asl a", "add #>$800000,a", "move a,%s" % X(LV)); a.emit(J("al"), p + "lx")      # triangle
        L(p + "l1"); e("cmp #>1,a"); a.emit(J("ne"), p + "l2")
        e("move #>$7fffff,x0", "move %s,a" % X(PH), "tst a"); a.emit(J("ge"), p + "l1s"); e("move #>$800000,x0")        # square
        L(p + "l1s"); e("move x0,%s" % X(LV)); a.emit(J("al"), p + "lx")
        L(p + "l2"); e("cmp #>2,a"); a.emit(J("ne"), p + "l3")
        e("move %s,a" % X(PH), "move a,%s" % X(LV)); a.emit(J("al"), p + "lx")                                          # saw
        L(p + "l3"); e("move %s,a" % X(PH), "neg a", "move a,%s" % X(LV))                                                # reverse saw
        L(p + "lx")
        # ---- filter: FILT (bipolar), + ENVF * ENV + LFOF * LV + KEY * (NOTE - 60) / 128 (in table steps), table TF[0..63]
        e("move %s,x0" % X(P_ENVF), "move %s,y0" % X(ENV), "mpy y0,x0,b")
        e("move %s,x0" % X(P_LFOF), "move %s,y0" % X(LV), "mac y0,x0,b")
        e("move %s,a" % X(NOTE), "sub #>60,a", "asl #16,a,a", "move a,y0", "move %s,x0" % X(P_KEY), "mac y0,x0,b")
        e("move %s,a" % X(P_FILT), "cmp #>2,a"); a.emit(J("gt"), p + "hp")
        e("cmp #>$fffffe,a"); a.emit(J("lt"), p + "lp")
        # centre: no filter unless a modulation depth is set
        e("move %s,a" % X(P_ENVF), "tst a"); a.emit(J("ne"), p + "cm")
        e("move %s,a" % X(P_LFOF), "tst a"); a.emit(J("ne"), p + "cm")
        e("move %s,a" % X(P_KEY), "tst a"); a.emit(J("ne"), p + "cm")
        e("move #>0,x0", "move x0,%s" % X(FMODE)); a.emit(J("al"), p + "fq")
        L(p + "cm"); e("move #>1,x0", "move x0,%s" % X(FMODE), "move #>$3f,a"); a.emit(J("al"), p + "fi")
        L(p + "lp"); e("move #>1,x0", "move x0,%s" % X(FMODE), "move %s,a" % X(P_FILT), "add #>$40,a"); a.emit(J("al"), p + "fi")
        L(p + "hp"); e("move #>2,x0", "move x0,%s" % X(FMODE), "move %s,a" % X(P_FILT))
        L(p + "fi")
        e("add b,a", "tst a"); a.emit(J("ge"), p + "i2"); e("move #>0,a")
        L(p + "i2"); e("cmp #>$3f,a"); a.emit(J("le"), p + "i3"); e("move #>$3f,a")
        L(p + "i3"); ld_tab("TF", "a", "x0"); e("move x0,%s" % X(FF))
        e("move %s,a" % X(P_RES), "asl #16,a,a", "move a,x0", "move #>$%x,y0" % QK, "mpy y0,x0,b")
        e("move #>$%x,a" % q24(Q0), "sub b,a", "move a,%s" % X(FQ))
        L(p + "fq")
        # ---- drive factor (0 = no saturation) and the VCA gain target
        e("move %s,a" % X(P_DRIVE), "asl #16,a,a", "move a,%s" % X(DRVF))
        e("move %s,a" % X(P_LEVEL), "cmp #>127,a"); a.emit(J("lt"), p + "lv")
        e("move #>$7fffff,a"); a.emit(J("al"), p + "lw")
        L(p + "lv"); e("asl #16,a,a")
        L(p + "lw"); e("move a,x1")                                                                                      # x1 = level
        e("move %s,a" % X(P_VELE), "tst a"); a.emit(J("eq"), p + "nv")                                                  # velocity: level *= 1 - k (1 - vel)
        e("asl #16,a,a", "move a,x0", "move #>$7fffff,a", "sub x0,a", "move %s,y0" % X(VEL), "move y0,b", "asl #16,b,b", "move b,y0", "mac x0,y0,a")
        e("move a,y0", "mpy x1,y0,a", "move a,x1")
        L(p + "nv")
        e("move %s,a" % X(P_VMODE), "cmp #>1,a"); a.emit(J("ne"), p + "ng2")
        e("move %s,y0" % X(ENV), "mpy x1,y0,a", "move a,x1")                                                             # gate mode: level * ENV
        L(p + "ng2")
        e("move %s,a" % X(P_LFOV), "tst a"); a.emit(J("eq"), p + "nt")                                                  # tremolo: * (1 - depth * (1 - LV) / 2)
        e("asl #16,a,a", "move a,y0", "move #>$7fffff,a", "move %s,b" % X(LV), "sub b,a", "asr a", "move a,x0", "mpy y0,x0,a")
        e("move #>$7fffff,b", "sub a,b", "move b,y0", "mpy x1,y0,a", "move a,x1")
        L(p + "nt")
        e("move x1,%s" % X(GT))
        # VCAON: gate mode, tremolo, level < 127 (or velocity) -> the VCA stage runs
        e("move %s,a" % X(P_VMODE), "cmp #>1,a"); a.emit(J("eq"), p + "von")
        e("move %s,a" % X(P_LFOV), "tst a"); a.emit(J("ne"), p + "von")
        e("move %s,a" % X(P_VELE), "tst a"); a.emit(J("ne"), p + "von")
        e("move %s,a" % X(P_LEVEL), "cmp #>127,a"); a.emit(J("lt"), p + "von")
        e("move #>0,x0", "move x0,%s" % X(VCAON), "move #>$7fffff,x0", "move x0,%s" % X(GT), "move x0,%s" % X(GCUR)); a.emit(J("al"), p + "vx")
        L(p + "von"); e("move #>1,x0", "move x0,%s" % X(VCAON))
        L(p + "vx")
        e("move %s,a" % X(GINIT), "tst a"); a.emit(J("eq"), p + "gi")
        e("move %s,x0" % X(GT), "move x0,%s" % X(GCUR), "move #>0,x0", "move x0,%s" % X(GINIT))
        L(p + "gi")
        e("move %s,a" % X(GT), "move %s,x0" % X(GCUR), "sub x0,a", "asr #5,a,a", "move a,%s" % X(GINC))

    # ================================================================ one channel in place: r0 = first sample, n0 = 2, r6 = block, r7 = filter state (LOW, BAND)
    def channel(p, sp):
        e("move %s,a" % X(FMODE), "tst a"); a.emit(J("eq"), p + "p2")
        e("move r0,r1", "move x:(r7),a", "move x:(r7+1),x0", "move %s,y0" % X(FF), "move %s,y1" % X(FQ), "move %s,b" % X(FMODE), "cmp #>2,b")
        a.emit(J("eq"), p + "hp")
        for name in ("lp", "hp"):
            if name == "hp": L(p + "hp")
            a.emit(D.do_x, 0x3A, p + "e_" + name)
            e("mac y0,x0,a")
            e("move %s:(r0),b" % sp, "asr b", "sub a,b", "mac -x0,y1,b", "mac -x0,y1,b", "move b,x1")
            e("tfr x0,b", "mac x1,y0,b", "move b,x0")
            if name == "lp": e("tfr a,b", "asl b")
            else: e("move x1,b", "asl b")
            L(p + "e_" + name); e("move b,%s:(r0)+n0" % sp)
            if name == "lp": a.emit(J("al"), p + "pe")
        L(p + "pe")
        e("move a,x:(r7)", "move x0,x:(r7+1)", "move r1,r0")
        L(p + "p2")
        e("move %s,a" % X(DRVF), "tst a"); a.emit(J("ne"), p + "sat")
        e("move %s,a" % X(VCAON), "tst a"); a.emit(J("eq"), p + "done")
        e("move %s,x0" % X(GCUR), "move x0,%s" % X(GRUN))                       # VCA only
        a.emit(D.do_x, 0x3A, p + "ce")
        e("move %s,a" % X(GRUN), "move %s,x1" % X(GINC), "add x1,a", "move a,%s" % X(GRUN), "move a,y1", "move %s:(r0),x0" % sp, "mpy x0,y1,b")
        L(p + "ce"); e("move b,%s:(r0)+n0" % sp)
        a.emit(J("al"), p + "done")
        L(p + "sat")
        e("move %s,a" % X(VCAON), "tst a"); a.emit(J("ne"), p + "sv")
        a.emit(D.do_x, 0x3A, p + "se")                                           # saturation only
        e("move %s:(r0),x0" % sp, "move %s,y0" % X(DRVF), "mpy x0,y0,b", "asl #4,b,b", "add x0,b", "move b,x0")             # u = x * (1 + 16 d), limited
        e("mpy x0,x0,b", "move b,y0", "mpy x0,y0,b", "move x0,a", "sub b,a", "asr a", "add x0,a", "move a,x0")              # y = u + (u - u^3) / 2
        L(p + "se"); e("move x0,%s:(r0)+n0" % sp)
        a.emit(J("al"), p + "done")
        L(p + "sv")                                                              # saturation + VCA
        e("move %s,x0" % X(GCUR), "move x0,%s" % X(GRUN))
        a.emit(D.do_x, 0x3A, p + "ve")
        e("move %s:(r0),x0" % sp, "move %s,y0" % X(DRVF), "mpy x0,y0,b", "asl #4,b,b", "add x0,b", "move b,x0")
        e("mpy x0,x0,b", "move b,y0", "mpy x0,y0,b", "move x0,a", "sub b,a", "asr a", "add x0,a", "move a,x0")
        e("move %s,a" % X(GRUN), "move %s,x1" % X(GINC), "add x1,a", "move a,%s" % X(GRUN), "move a,y1", "mpy x0,y1,b")
        L(p + "ve"); e("move b,%s:(r0)+n0" % sp)
        L(p + "done")

    REGS = ["x0", "x1", "y0", "y1", "r0", "r1", "r6", "r7", "n0", "m0"]
    def save_regs():
        for i, r in enumerate(REGS): e("move %s,x:>$%x" % (r, SAV + i))
    def restore_regs():
        for i, r in enumerate(REGS): e("move x:>$%x,%s" % (SAV + i, r))

    RMODE, TCH, RBUF = SAV + 12, SAV + 11, SAV + 10                              # 0 ring (vpre) / 1 return (vret), channel of the return, its first sample
    # ================================================================ vpre (from P:$23C): control of the active voices + the line inputs in place
    L("vpre")
    save_regs()
    e("move #>$ffff,m0", "move #>2,n0", "move #>0,x0", "move x0,x:>$%x" % TCNT, "move #>$%x,r6" % VB0); a.emit(D.NOP)
    L("vp_loop")
    mailbox("vm_")
    e("move %s,a" % X(ACT), "tst a"); a.emit(J("ne"), "vp_on")
    e("move #>0,x0", "move x0,%s" % X(ACTP)); a.emit(J("al"), "vp_next")
    L("vp_on")
    control("vc_")
    e("move x:>$%x,a" % FLAGS, "move a1,x1")
    ld(TCNT, "b"); e("tst b"); a.emit(J("ne"), "vp_t1")
    a.emit(JCLR(0, "x1"), "vp_ring"); a.emit(J("al"), "vp_next")                 # the reverb return takes strip 3: vret does this voice
    L("vp_t1")
    a.emit(JCLR(1, "x1"), "vp_ring"); a.emit(J("al"), "vp_next")
    L("vp_ring")
    e("move y:>$%x,r0" % RING_PTR); a.emit(D.NOP)
    ld(TCNT, "a"); e("tst a"); a.emit(J("eq"), "vp_r0"); e("move (r0)+")
    L("vp_r0")
    e("move r6,a", "add #>%d,a" % LOW0, "move a,r7", "move #>0,x0", "move x0,x:>$%x" % RMODE); a.emit(D.NOP)
    a.emit(J("al"), "vchan")
    L("vp_cont")
    e("move %s,x0" % X(GT), "move x0,%s" % X(GCUR))
    L("vp_next")
    ld(TCNT, "a"); e("add #>1,a"); st("a", TCNT)
    e("move r6,a", "add #>%d,a" % VBS, "move a,r6", "cmp #>%d,a" % (VB0 + 2 * VBS)); a.emit(D.NOP); a.emit(J("lt"), "vp_loop")
    restore_regs()
    a.emit(D.jmp(premix))

    # ================================================================ vret (from the end of fx_cap, P:$D21 chain): the FX returns of the voices whose strip takes them
    L("vret")
    save_regs()
    e("move #>$ffff,m0", "move #>2,n0", "move #>0,x0", "move x0,x:>$%x" % TCNT, "move #>$%x,r6" % VB0); a.emit(D.NOP)
    L("vq_loop")
    e("move %s,a" % X(ACT), "tst a"); a.emit(J("eq"), "vq_next")
    e("move x:>$%x,a" % FLAGS, "move a1,x1")
    ld(TCNT, "b"); e("tst b"); a.emit(J("ne"), "vq_t1")
    a.emit(JCLR(0, "x1"), "vq_next"); e("move #>$%x,r0" % RET_BUF[0]); a.emit(J("al"), "vq_go")
    L("vq_t1")
    a.emit(JCLR(1, "x1"), "vq_next"); e("move #>$%x,r0" % RET_BUF[1])
    L("vq_go")
    a.emit(D.NOP)
    e("move r0,x:>$%x" % RBUF, "move #>0,x0", "move x0,x:>$%x" % TCH, "move #>1,x0", "move x0,x:>$%x" % RMODE)
    e("move r6,a", "add #>%d,a" % LOW0, "move a,r7"); a.emit(D.NOP)
    a.emit(J("al"), "vchan")
    L("vq_cont")
    ld(TCH, "a"); e("tst a"); a.emit(J("ne"), "vq_done")
    e("move #>1,x0", "move x0,x:>$%x" % TCH, "move x:>$%x,r0" % RBUF); a.emit(D.NOP); e("move (r0)+")
    e("move r6,a", "add #>%d,a" % LOW1, "move a,r7"); a.emit(D.NOP)
    a.emit(J("al"), "vchan")
    L("vq_done")
    e("move %s,x0" % X(GT), "move x0,%s" % X(GCUR))
    L("vq_next")
    ld(TCNT, "a"); e("add #>1,a"); st("a", TCNT)
    e("move r6,a", "add #>%d,a" % VBS, "move a,r6", "cmp #>%d,a" % (VB0 + 2 * VBS)); a.emit(D.NOP); a.emit(J("lt"), "vq_loop")
    restore_regs()
    a.emit(D.jmp(ret_old))

    # ================================================================ the channel (shared): r0 = first sample, n0 = 2, r6 = block, r7 = filter state; back to vpre / vret by RMODE
    L("vchan")
    channel("vc2_", "y")
    ld(RMODE, "a"); e("tst a"); a.emit(J("eq"), "vp_cont"); a.emit(J("al"), "vq_cont")
    return a.assemble()


def install_dsp(s16):
    """Before building: the code is appended to the (wrapped) SC16 DSP code, after the drums; sc_init clears the new memory (X:$3B80..$3BFF)."""
    import drums2_dsp as DD
    prev = s16.dsp_code
    def wrapped(base):
        w, l = prev(base)
        tabs = {k: l[k] for k in ("TATK", "TDEC", "TLFO", "TF")}
        w2, l2 = code(base + len(w), tabs, PREMIX, RET_OLD)
        return w + w2, {**l, **l2}
    s16.dsp_code = wrapped
    s16.CLR_N = max(s16.CLR_N, 0x3C00 - s16.CLR_FROM)


PREMIX, RET_OLD = 0x87, 0x9F                   # SC10's premix (its dsp label) and the operand the P:$D21 chain ends with


def patch_dsp(img, report):
    """After building: P:$23C jsr premix -> jsr vpre; the final jmp $9F of fx_cap -> jmp vret."""
    import linein2 as L2
    dl = {k: int(v, 16) for k, v in report["sc16"]["dsp_labels"].items()}
    assert int(report["sc10"]["dsp_labels"]["premix"], 16) == PREMIX
    L2.patch_p(img, 0x23C, [0x0BF080, PREMIX], [0x0BF080, dl["vpre"]])
    import struct
    tab = struct.unpack_from("<I", img, 0x08029700 - 0x08010000)[0]               # fx_cap lives above the original program: only the relocated block has it
    o = tab - 0x08010000 + 6 + 3 * (dl["fc_jmp"] + 1)
    assert int.from_bytes(img[o:o + 3], "big") == RET_OLD, hex(int.from_bytes(img[o:o + 3], "big"))
    img[o:o + 3] = dl["vret"].to_bytes(3, "big")
    assert dl["vret"] + 0 < 0x3800 and dl["vchan"] < 0x3800
