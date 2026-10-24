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
import math
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
P_FILT, P_RES, P_ENVF, P_LFOF, P_ATK, P_DEC, P_SUS, P_REL, P_FXAMT, P_GAIN, P_LRATE, P_LFOV, P_FXTYPE, P_FXMOD, P_ENVA, P_FTYPE = range(2, 18)
GATE, NOTE, ACT, VEL, GNEW = 18, 19, 20, 21, 22
ENV, STG, PH, LV, GCUR, GINC, GT, FF, FQ, FMODE, DRVF, VCAON, LOW0, BAND0, LOW1, BAND1 = range(23, 39)
ATKINC, DKC, RKC, SUSF, GINIT, ACTP, GRUN = 39, 40, 41, 42, 43, 44, 45
FXP, FXB = 46, 47                                # FX parameter (threshold / fold point), FX bias (wavefold)
TILT = True                                     # SC21.1: False = no tilt EQ (filter types DJ, band-pass, notch only: FMODE 1..4)
FB = False                                      # SC21.1: feedback of the FX returns (see pmfb): the premix puts the previous block's capture (Y:$3AC0 reverb, Y:$3A80 delay, as
                                                # captured by linein3.fx_cap AFTER our voices processed the returns) into the ring of the inputs 1 / 2 instead of zeros
FBBUF = (0x3AC0, 0x3A80)                        # ring input 1 <- the reverb capture, input 2 <- the delay capture
FBSAVE = 0x3BF1                                 # X: r1 saved around pmfb
SLOPES = False                                  # SC21.4 (needs TILT = False): filter types 0 DJ, 1 LP 12 dB, 2 HP 12 dB, 3 band-pass, 4 notch, 5 LP 24 dB, 6 HP 24 dB (FMODE = the type; 5 / 6 = the
                                                # low-pass / high-pass SVF run twice, the second stage with its own state at X:$3800 + 48 t + 2 c)
S2BASE = 0x3800
BISEND = False                                  # SC22: envelope -> VCA (ENVA) and LFO -> VCA (LFOV) bipolar (-64..63, 0 = no send, negative = inverted); negative envelope send closes the VCA (T clamped at 0)
FXMORE = False                                  # SC22: FX types 4 ring mod, 5 comb, 6 chorus (the program may now reach P:$3FFF: the RAM is 16 K words, probed by SC21D); the register save area moves
                                                # to SAVX (the old SAV + 10 collided with RBUF once r2 was saved), the per-voice FX state is at X:FXS + 48 t, the buffers in Y
PLIMIT = 0x3800
SAVX = 0x38C0                                   # 32 words: the registers, then RMODE / TCH / RBUF at +28..+30
FXS = 0x3840                                    # X: per voice (48 apart): +0 ring sin, +1 ring cos, +2 comb write index, +3 chorus write index, +4 chorus LFO phase, +5 chorus delay (running),
                                                #    +6 chorus delay step, +7 chorus buffer base
CB, HB = 0x3400, 0x3600                         # Y: comb buffers (256 words per voice), chorus buffers (512 words per voice, 512-aligned)
CHORUS_DC, CHORUS_DEP = 0x466666, 0x2CCCCC      # chorus delay = DC + DEP * triangle, as a fraction of 512 samples
SINEFIX = False                                  # SC23.3 (OSC3): the sine is the parabola refined with 0.225 (P |P| - P): a clean sine instead of 5 % of harmonics
STGLIDE = False                                 # SC37.4: the sustain stage glides ENV towards SUS with the decay coefficient instead of setting it: switching the engine
                                                #   (VA-drum sets SUS to 0, the oscillator brings it back) or turning SUS with a held note no longer steps the VCA (a click)
GATEFIX = False                                 # SC23.5: a gate that is high while the envelope is idle starts the envelope (a lost trigger message cannot silence a held note)
TYPEZONE = False                                # SC23.6: the values of the FX type (code 13) and the filter type (code 16) are zones of 7 over 0..127: the mailbox keeps the zone (the type) in the slot of the
                                                # code and the position inside the zone (0..127) in FXMOD (FX) / KEYF (the key follow of the filter cutoff, X:OSB0 + 48 t + KEYF_OFF); code 14 (FXMOD) is ignored
CODE7 = False                                   # SC24: the mailbox codes are 7 bits (bits 16..22 of the word); the codes 32..39 land in the OSC2 block at X:OS2B0 + 48 t + (code - 32)
DUAL = False                                    # SC24: a second oscillator + the interactions (mix, FM, ring, sync, bitwise); ACT message value bit 8 = route, bit 9 = two oscillators (the mailbox
                                                # splits them: the ACT slot keeps 0..2, DFLAGS keeps bit 0 route, bit 1 dual); code 14 = NOTE2 (the note of the second oscillator)
ROUTE = False                                   # SC24: the chain order is chosen per voice by DFLAGS bit 0: 0 = VCA -> FX -> filter, 1 = filter -> VCA -> FX
OS2B0 = 0x3960                                  # X: the second oscillator block, 48 words per voice: +0 TUNE2 +1 FINE2 +2 WAVE2 +3 PW2 +4 MIX +5 BITSYNC zone +6 FM +7 RING +8 BITSYNC position +10 phase +11 signed increment
                                                #    +12 fold drive +13 saw slope +14 pulse threshold +15..18 weights +19 increment +20 direction +21 sync period +22 sync counter +23 sample +24 FM +25 MIX +26 BITSYNC +27 RING (scaled)
NOTE2_OFF, DFLAGS_OFF = 20, 21                  # words of the OSC1 block: the note of the second oscillator, the flags (bit 0 route, bit 1 dual)
VADRUM = False                                  # SC29: the VA-drum engine (inspired by other step-based percussive synthesizers), a variant of the oscillator source chosen per voice by DFLAGS bit 2
                                                # (the ACT message value bit 10): the VCA envelope is a one-shot (attack, then DEC down to 0; the gate length does not matter), two more decay envelopes
                                                # restart with every note: the pitch one (its decay = the SUS value) feeds ENVP, the filter one (its decay = the REL value) feeds ENVF; the LFO is a random
                                                # value per block (LFOP / LFOF / LFOV / LFOW / LFOM = noise amounts) and LRATE is the level of white noise added to the oscillator.  DFLAGS bit 3 (ACT
                                                # value bit 11): the velocity sets the start level of the two extra envelopes.  Words of the OSC1 block: +22 the filter envelope, +23 the pitch envelope
                                                # (both = ENV in the other engines, so the code that reads them is the same), +24 the noise generator, +25 the noise level
VD_EF, VD_EP, VD_NS, VD_NL = 22, 23, 24, 25
LCG_K, LCG_C = 0x0343FD, 0x269EC3               # the noise: s = (s x K + C) mod 2^24 (full period)
KEYF_OFF = 19                                   # word of the oscillator block that holds the key follow (the block uses +0..+18)
LFOSHAPE = False                                # SC43.9 (see use_lfoshape)
SAMPLER = False                                 # SC44 (see use_sampler)
SM_P, SM_F, SM_S, SM_L, SM_ON, SM_N = 40, 41, 44, 45, 46, 47   # (SAMPLER) words of the OSC1 block: position, fraction (1.23), start, length, playing, the new note's TRIG
SM_TAB, SM_CAP, SM_CAPLEN = 0x1D8D, 0xE80000, 0x3D09           # the pack's sample table (X: start, length, ...), the capture and its length


def use_sampler():
    """SC44 (the user, 2026-10-17: «drum tracks on MIDI tracks, but the pitch is controlled by the noteON, inspired by Circuit Rhythm» · «A, … sample
    selection mode overtakes the note expand view, and the available samples are the whole library … sample flipping» · «since samples are one-hit,
    the vca will default to full open during sample mode and back to normal on the other modes»): a sample source of the own engine, ACT = 3.
      * a new note (control(): the TRIG value, GNEW) restarts it: TRIG & $100 = that sample (TRIG & 63), else code 25 (the track's sample; < 0 =
        the capture); its start / length from the pack's sample table X:$1D8D + 4 N (core 0's, the stock drums'), the position 0;
      * every block (vpre, like the oscillator): the rate = TINC[clamp(NOTE + TUNE)] x 2^38 / TINC[60] = the ratio to note 60 in 9.15 (note 60 = the
        sample as recorded), 32 frames read from the external Y memory with linear interpolation into the ring (r4 / n4 / m4 linear; n4 is saved
        with the registers); the block that could pass the end (up to 64 frames a block) stops it (silence after);
      * the VCA: the envelope term of its target is 1.0 (gain, the envelope amount, the velocity and the tremolo as before): the one-shot opens it;
        the other sources as before."""
    global SAMPLER
    assert OSC3 and VADRUM and GRAN
    SAMPLER = True
N_LSHAPES = 6                                   # (LFOSHAPE) 0 reverse saw (as before), 1 saw, 2 triangle, 3 square, 4 sine, 5 sample & hold
LS_SLEW = False                                 # SC44.3 (use_lfoshape2): shape 6 = slewed sample & hold
SL_PREV = 26                                    # (LS_SLEW) the word of the OSC1 block with the last random value (words 26..39 are free)


def use_lfoshape():
    """SC43.9 (the user, 2026-10-17: «add waveshapes to own synth's lfo»): the LFO of the own engine (one value LV a block per voice, from the phase
    PH += TLFO[LRATE]) had one shape, the reverse saw (LV = -PH).  The shape now comes with the ACT message (bits 13-15 of its value: the mailbox
    keeps bits 8-15 in DFLAGS, so DFLAGS bits 5-7; the other DFLAGS bits are only tested one by one): 0 the reverse saw (the same instructions as
    before), 1 saw (PH), 2 triangle (2 |PH| - 1), 3 square (+1 / -1 by the sign of PH), 4 sine (4 PH (1 - |PH|): the parabola, the limiter at the
    top), 5 sample & hold (a new value of the voice's noise generator, DFLAGS + 3, each time the phase wraps)."""
    global LFOSHAPE
    assert VADRUM and DUAL
    LFOSHAPE = True
LFOSYNC = False                                 # SC44.8 (see use_lfosync)
LFS_INC = 40                                    # (LFOSYNC) word of the OSC2 block (OS2B0 + 48 t + 40; the block uses +0..+23): the ARM's increment of the synced LFO


def use_lfosync():
    """SC44.8 (the user, 2026-10-19: «en los lfo rate, hazlo bipolar (manten 0 dim y lados bright) hacia la derecha, lfo libre, izquierda, lfo a tempo
    con sync en beat 1»): LRATE (code 11) bipolar -64..63: >= 0 = free, PH += TLFO[2 v]; < 0 = synced: PH += the increment the ARM keeps in
    OS2B0 + 48 t + LFS_INC (lfosync.py: from the tempo and the division, and the phase itself set from the sequencer's tick).  The VA-drum's noise
    level (the same knob) = v + 64."""
    global LFOSYNC
    LFOSYNC = True


SHSYNC = False                                  # SC46.1 (use_shsync)


def use_shsync():
    """SC46.1 (a fix of the beta; the user, 2026-10-24: «lfo s&h (random) no funciona»): the sample & hold shapes (5, and 6 slewed) take a new
    value when the phase wraps, seen as p < 0 and p - inc < -1; with the LFO synced (the left half of LRATE, lfosync.py) and the transport running
    the ARM sets the phase to exactly -1 ($800000) at every cycle's start, so p - inc = -1 and the value never changed.  Now p - inc <= -1."""
    global SHSYNC
    assert LFOSYNC
    SHSYNC = True


SUPERSAW = False                                # SC45.5 (use_supersaw)
SS_PH, SS_D, SS_W = 28, 35, 42                  # (SUPERSAW) words of each oscillator block: the six side phases (+28..+33), the detune steps D, 3 D, 6 D (+35..+37),
                                                # the side saws' weight (+42; OSC1: the sampler's words are +40, +41, +44..+47; OSC2: +40 is lfosync's)
SS_D1 = 0.0183                                  # the inner pair's detune at the knob's far right (x the increment); 3 D / 6 D = 0.055 / 0.11: the classic supersaw's spread


def use_supersaw():
    """SC45.5 (the user, 2026-10-20: «Cambia el control de sierra a normal-supersaw», all the knob's travel, 7 saws; «Implementa log/exp a la
    izquierda en triangular», exponential): SHAPE on the saw = s = (m + 1) / 2 (m = the shape, -1 .. 1: the knob's far left = a plain saw, its far
    right = the full supersaw; the envelope / LFO move it as before): six more saws at increment +- D, +- 3 D, +- 6 D (D = 0.0183 s x the
    increment; their phases kept in the block, the signed increment +11 so the soft sync's reversal follows), the centre saw at w (1 - s / 2) / 2,
    each side one at w s / 16 (w = the morph weight of the saw; the other waves are at +-0.5 too).  SHAPE on the triangle, left of the centre:
    t' = t - c / 2 x (1 - t^2), c = -m (exponential ramps: the peaks sharp, the valleys wide; c = 0 at the centre and right of it, where the
    wavefold works as before).  The saw's slope is gone (+13 = c / 2).  The four waves become a subroutine (OW = r4, called three times: the
    single oscillator, OSC2 and OSC1 of the dual one) to make room: one more level of the system stack inside the sample loop."""
    global SUPERSAW
    assert OSC3 and SINEFIX and DUAL
    SUPERSAW = True


FM = False                                      # SC45.6 (use_fm)
FMB0, FM_FLAG, FMS = 0x3E00, 27, 12             # (FM) the operator blocks at X:$3E00 + 48 t (the voices' stride; X:$3D00-$3FFF is free), the flag word of the OSC1 block, the operator stride
F_OUT, F_PH, F_R, F_AMP, F_K, F_M, F_NZ = 0, 1, 2, 3, 4, 5, 9                     # words of an operator block (F_NZ: operator 1's block only)


def use_fm():
    """SC45.6 (the user, 2026-10-21: «can we have FM as another variant for osc?», «4op, A/R with fixed sustain», «include some kick/noise
    percussive algos, some bell and some strings along with the typical algorithms»): a 4-operator FM variant of the oscillator, chosen by the ARM
    (fmeng.py): with the word FM_FLAG of the OSC1 block not 0 (the ARM writes it, only in the plain oscillator mode) the oscillator's samples are the
    FM voice's.  Each sample, for the operators 1..4 in their blocks (X:FMB0 + 48 t + 12 k): the phase += the oscillator's increment (OSC1 + 11:
    the note, TUNE / FINE, the pitch envelope and the vibrato as before) x R (the ratio / 16, from the ARM), the phase modulation 4 x sum(M_kj x
    OUT_j) (the routing matrix from the ARM: the algorithm; M_kk = feedback; the outputs of the previous sample for the operators not yet
    computed), OUT_k = AMP_k x sine (the parabola 4 u (1 - |u|)), the sample = sum(K_k x OUT_k) (the carriers' weights).  AMP_k (the operator's
    envelope x its level), R_k (with the algorithm's detune and the pitch drop) and the noise level (F_NZ, into VD_NL: the VA-drum's noise loop
    adds it) come from the ARM every millisecond: no envelope code here.  Two nested do loops (the system stack two levels deeper)."""
    global FM
    assert OSC3 and DUAL and VADRUM and SUPERSAW
    FM = True


def use_lfoshape2():
    """SC44.3 (the user, 2026-10-18: «add s&h (stepped random) and slewed s&h (glided random) as waveshapes»): shape 6 of the own engine's LFO =
    slewed sample & hold: when the phase wraps the old random value goes to OSC1 + SL_PREV and the voice's noise generator (DFLAGS + 3) gives a new
    one, as shape 5; every block LV = prev + (new - prev) x (p + 1) / 2: a straight glide from one random value to the next over the cycle."""
    global N_LSHAPES, LS_SLEW
    assert LFOSHAPE and SL_PREV - DFLAGS_OFF == 5
    N_LSHAPES, LS_SLEW = 7, True


GRAN = False                                    # SC36: the granular engine of DSP core 1 (granular_dsp): DFLAGS bit 4 (ACT bit 12) = this voice plays OUT instead of the oscillator; GNEW counted for core 1
GATEREL = False                                  # SC23.3: release 0 = a ~2 ms release (a basic gate); see use_gaterel
GATE_RKC = None                                  # set by use_gaterel: the release coefficient per block
VFF = False                                     # SC22: the chain is VCA -> FX -> filter (False: filter -> FX -> VCA as SC20..SC21.4)
OSC = False                                     # SC22.1: oscillator source (ACT = 2): the track's ring input is replaced by an oscillator (sine / triangle / saw / pulse) at the pitch of NOTE + TUNE
                                                # (+ fine + vibrato), then the usual chain.  Mailbox codes 22..26 (TUNE, FINE, WAVE, PW, LFOP) land in the second block at X:OSB0 + 48 t + (code - 22)
OSB0 = 0x3900                                   # +0 TUNE (-64..63 semitones), +1 FINE (-64..63, +-53 cents), +2 WAVE (0 sine, 1 triangle, 2 saw, 3 pulse), +3 PW (0..127, 64 = 50 %), +4 LFOP (vibrato depth,
                                                #    -64..63, +-1 semitone), +5 phase (24 bit, one cycle = 2^24), +6 increment of the block
OSC_AMP_NOTE = "oscillator level 0.5 (0x400000)"
OSC2 = False                                    # SC22.2: oscillator v2 (mathematical oscillators): the pitch in semitones (1 semitone = 65536) = NOTE + TUNE + FINE / 128 + ENVP x ENV x 24 + LFOP x LV x 6, interpolated
                                                # between the table steps; the shape m = (PW - 64) / 64 + ENVW x ENV + LFOW x LV (saturating at +-1) is, per waveform: sine / triangle: wavefold (m <= 0: none, m = 1: the
                                                # drive is x7.9 and the signal folds back); saw: the slope of the ramp (m = 0 straight, m = 1 parabolic r^2, m = -1 logarithmic 2 r - r^2); pulse: the pulse width (m = 0: 50 %).
                                                # Block words: +0 TUNE +1 FINE +2 WAVE +3 PW +4 LFOP +5 ENVP +6 ENVW +7 LFOW +8 phase +9 increment +10 shape parameter (fold drive / m / threshold, computed per block)
OSC3 = False                                    # SC22.3: oscillator v3: the WAVE value (0..126) is a continuous morph position over sine (0) - triangle (42) - saw (84) - square (126) that the envelope (ENVM) and the LFO
                                                # (LFOM) move; the four waves are computed and mixed with tent weights; the shape parameter (PW 0..100, 50 = centre) acts on every wave as in OSC2.  Block words: +0 TUNE
                                                # +1 FINE +2 WAVE +3 PW +4 LFOP +5 ENVP +6 ENVW +7 LFOW +8 ENVM +9 LFOM +10 phase +11 increment +12 fold drive +13 saw slope +14 pulse threshold +15..18 weights of the four waves
O_PH, O_INC = 5, 6                              # the phase and the increment words of the oscillator block (8 / 9 with OSC2, 10 / 11 with OSC3)


def use_sinefix():
    global SINEFIX
    SINEFIX = True


def use_typezones():
    global TYPEZONE
    assert OSC3
    TYPEZONE = True


def use_dual():
    """SC24: second oscillator, interactions, per-voice chain order, 7-bit mailbox codes (needs use_osc3 and use_typezones)."""
    global CODE7, DUAL, ROUTE
    assert OSC3 and TYPEZONE
    CODE7 = DUAL = ROUTE = True


def use_vadrum():
    """SC29: the VA-drum engine (needs use_dual)."""
    global VADRUM
    assert DUAL
    VADRUM = True


def use_stglide():
    global STGLIDE
    STGLIDE = True


def use_gatefix():
    global GATEFIX
    GATEFIX = True


def use_gaterel(tau=0.002):
    """SC23.3: with REL = 0 the VCA release is a ~2 ms exponential (a basic gate) instead of the 40 ms the table gives for the shortest setting."""
    global GATEREL, GATE_RKC
    GATEREL = True
    GATE_RKC = q24(math.exp(-D1.NFR / (D1.FS * tau)))


def use_osc2():
    global OSC, OSC2, O_PH, O_INC
    OSC, OSC2, O_PH, O_INC = True, True, 8, 9


def use_osc3():
    global OSC, OSC2, OSC3, O_PH, O_INC
    OSC, OSC2, OSC3, O_PH, O_INC = True, True, True, 10, 11
KEYK = 32                                       # key tracking to the cutoff, fixed (table steps per 128 note units)
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
        e("move x0,%s" % X(MBL), "move x0,a", "lsr #16,a", "and #>$%x,a" % (0x7f if CODE7 else 0x1f), "move a1,y1", "move y1,a", "tst a"); a.emit(J("eq"), p + "mbd")
        e("cmp #>%d,a" % (39 if CODE7 else 31 if OSC3 else 29 if OSC2 else 26 if OSC else N_CODES)); a.emit(J("gt"), p + "mbd")
        if DUAL:                                                                  # code 14 (the dead FXMOD slot of the ARM table) = the note of the second oscillator
            e("cmp #>14,a"); a.emit(J("ne"), p + "n14")
            e("move r6,b", "sub #>%d,b" % (VB0 - OSB0 - NOTE2_OFF)); a.emit(J("al"), p + "mj")
            L(p + "n14")
        elif TYPEZONE: e("cmp #>14,a"); a.emit(J("eq"), p + "mbd")                # FXMOD comes from the FX type now
        if OSC:
            e("cmp #>21,a"); a.emit(J("gt"), p + "mo")
            e("move r6,b", "add a,b", "add #>1,b"); a.emit(J("al"), p + "mj")
            L(p + "mo")
            if CODE7: e("cmp #>31,a"); a.emit(J("gt"), p + "m2")
            e("move r6,b", "add a,b", "sub #>%d,b" % (VB0 - OSB0 + 22))
            if CODE7: a.emit(J("al"), p + "mj"); L(p + "m2"); e("move r6,b", "add a,b", "sub #>%d,b" % (VB0 - OS2B0 + 32))
            L(p + "mj"); e("move b,r7"); a.emit(D.NOP)
        else:
            e("move r6,b", "add a,b", "add #>1,b", "move b,r7"); a.emit(D.NOP)
        e("move x0,a", "and #>$ffff,a", "move a1,y0", "move y0,a", "cmp #>$8000,a"); a.emit(J("lt"), p + "pos")
        e("sub #>$10000,a")
        L(p + "pos"); e("move a,x:(r7)")
        if TYPEZONE:
            e("move y1,b", "cmp #>13,b"); a.emit(J("eq"), p + "z13")
            e("cmp #>16,b"); a.emit(J("eq"), p + "z16")
            if DUAL:
                e("cmp #>19,b"); a.emit(J("eq"), p + "z19")
                e("cmp #>37,b"); a.emit(J("eq"), p + "z37")
            a.emit(J("al"), p + "mbd")
            for zc_ in (13, 16) + ((37,) if DUAL else ()):                        # a = the value p (0..127): zone t = 7 p >> 7 -> the slot of the code, position f = 7 p & 127
                L(p + "z%d" % zc_)
                e("move a1,b", "asl #3,a,a", "sub b,a", "move a1,y0", "lsr #7,a", "move a,x:(r7)", "move y0,a", "and #>$7f,a")
                if zc_ == 13: e("move a,x:(r7+1)")
                elif zc_ == 37: e("move a,x:(r7+3)")                              # BITSYNC: the zone in the slot (+5), the position at +8
                else:
                    e("move r6,b", "sub #>%d,b" % (VB0 - OSB0 - KEYF_OFF), "move b,r0"); a.emit(D.NOP)
                    e("move a,x:(r0)")
                a.emit(J("al"), p + "mbd")
            if DUAL:                                                              # ACT: the value = act | route << 8 | dual << 9 -> the ACT slot keeps act, DFLAGS keeps the two flags
                L(p + "z19")
                e("move a1,y0", "and #>3,a", "move a,x:(r7)", "move y0,a", "lsr #8,a", "and #>%d,a" % (255 if LFOSHAPE else 31 if GRAN else 15 if VADRUM else 3), "move a1,y0")
                e("move r6,b", "sub #>%d,b" % (VB0 - OSB0 - DFLAGS_OFF), "move b,r0"); a.emit(D.NOP)
                e("move y0,a", "move a,x:(r0)")
                a.emit(J("al"), p + "mbd")
        L(p + "mbd")

    def control(p):
        # ---- voice switched on: restart
        e("move %s,a" % X(ACTP), "tst a"); a.emit(J("ne"), p + "ao")
        e("move #>1,x0", "move x0,%s" % X(ACTP), "move x0,%s" % X(GINIT), "move #>0,x0", "move x0,%s" % X(ENV), "move x0,%s" % X(STG))
        L(p + "ao")
        # ---- envelope
        if VADRUM: e("move r6,a", "sub #>%d,a" % (VB0 - OSB0 - DFLAGS_OFF), "move a,r7"); a.emit(D.NOP)       # r7 = DFLAGS (+1 the filter envelope, +2 the pitch envelope, +3 the noise, +4 its level)
        if GATEFIX:
            e("move %s,a" % X(GATE), "tst a"); a.emit(J("eq"), p + "gf")
            e("move %s,a" % X(STG), "tst a"); a.emit(J("ne"), p + "gf")
            e("move #>1,x0", "move x0,%s" % X(GNEW))
            L(p + "gf")
        e("move %s,a" % X(GNEW), "tst a"); a.emit(J("eq"), p + "ng")
        if SAMPLER:                                                              # (SAMPLER) the TRIG value for the sample (r7 = DFLAGS), in the sample mode only
            e("move %s,b" % X(ACT), "cmp #>3,b"); a.emit(J("ne"), p + "nsn")
            e("move a,x:(r7+%d)" % (SM_N - DFLAGS_OFF))
            L(p + "nsn")
        if VADRUM:                                                               # a new note: the two extra envelopes start from the top (DFLAGS bit 3: from the velocity)
            e("move #>$7fffff,x0", "move x:(r7),a", "and #>8,a"); a.emit(J("eq"), p + "vt")
            e("move %s,a" % X(VEL), "asl #16,a,a", "move a,x0")
            L(p + "vt"); e("move x0,x:(r7+1)", "move x0,x:(r7+2)")
        e("move #>0,x0", "move x0,%s" % X(GNEW), "move %s,a" % X(P_ATK), "tst a"); a.emit(J("ne"), p + "ga")
        e("move #>$7fffff,x0", "move x0,%s" % X(ENV), "move #>2,x0", "move x0,%s" % X(STG)); a.emit(J("al"), p + "ng")
        L(p + "ga"); e("move #>0,x0", "move x0,%s" % X(ENV), "move #>1,x0", "move x0,%s" % X(STG))
        L(p + "ng")
        if VADRUM: e("move x:(r7),a", "and #>4,a"); a.emit(J("ne"), p + "go")    # VA-drum: a one-shot, the end of the gate does nothing
        e("move %s,a" % X(GATE), "tst a"); a.emit(J("ne"), p + "go")            # gate off: stages 1..3 -> release
        e("move %s,a" % X(STG), "tst a"); a.emit(J("eq"), p + "go"); e("cmp #>4,a"); a.emit(J("ge"), p + "go")
        e("move #>4,x0", "move x0,%s" % X(STG))
        L(p + "go")
        e("move %s,b" % X(P_ATK), "asr b", "move #>63,a", "sub b,a"); ld_tab("TATK", "a", "x0"); e("move x0,%s" % X(ATKINC))
        e("move %s,b" % X(P_DEC), "asr b", "add #>64,b"); ld_tab("TDEC", "b", "x0"); e("move x0,%s" % X(DKC))
        e("move %s,b" % X(P_REL), "asr b", "add #>64,b"); ld_tab("TDEC", "b", "x0"); e("move x0,%s" % X(RKC))
        if GATEREL:                                                              # REL = 0: a plain gate, the release lasts ~2 ms (instead of the 40 ms of the table)
            e("move %s,a" % X(P_REL), "tst a"); a.emit(J("ne"), p + "rk")
            e("move #>$%x,x0" % GATE_RKC, "move x0,%s" % X(RKC))
            L(p + "rk")
        e("move %s,a" % X(P_SUS), "asl #16,a,a", "move a,%s" % X(SUSF))
        if VADRUM:                                                               # VA-drum: the VCA envelope decays to 0 (the SUS value is the decay of the pitch envelope)
            e("move x:(r7),a", "and #>4,a"); a.emit(J("eq"), p + "vs")
            e("clr a", "move a,%s" % X(SUSF))
            L(p + "vs")
        e("move %s,a" % X(STG), "tst a"); a.emit(J("eq"), p + "e0")
        e("cmp #>1,a"); a.emit(J("eq"), p + "e1"); e("cmp #>2,a"); a.emit(J("eq"), p + "e2"); e("cmp #>3,a"); a.emit(J("eq"), p + ("e2" if STGLIDE else "e3"))
        # 4 release: ENV *= RKC; below 1/256: idle
        e("move %s,x0" % X(ENV), "move %s,y0" % X(RKC), "mpy y0,x0,a", "move a,%s" % X(ENV), "cmp #>$8000,a"); a.emit(J("ge"), p + "ee")
        L(p + "e0"); e("move #>0,x0", "move x0,%s" % X(ENV), "move x0,%s" % X(STG)); a.emit(J("al"), p + "ee")
        L(p + "e1")                                                              # attack: ENV += ATKINC
        e("move %s,a" % X(ENV), "move %s,x0" % X(ATKINC), "add x0,a", "cmp #>$7fffff,a"); a.emit(J("lt"), p + "e1s")
        e("move #>$7fffff,a", "move #>2,x0", "move x0,%s" % X(STG))
        L(p + "e1s"); e("move a,%s" % X(ENV)); a.emit(J("al"), p + "ee")
        L(p + "e2")                                                              # decay: ENV = SUS + (ENV - SUS) * DKC
        e("move %s,x0" % X(SUSF), "move %s,a" % X(ENV), "sub x0,a", "move a,y1", "move %s,y0" % X(DKC), "mpy y1,y0,a", "add x0,a", "move a,%s" % X(ENV))
        if STGLIDE:                                                              # sustain (3): the same glide, no stage change
            e("move %s,a" % X(STG), "cmp #>3,a"); a.emit(J("eq"), p + "ee")
            e("move %s,a" % X(ENV), "sub x0,a", "cmp #>$2000,a"); a.emit(J("gt"), p + "ee")
            e("move #>3,x0", "move x0,%s" % X(STG))
        else:
            e("move %s,a" % X(ENV), "sub x0,a", "cmp #>$2000,a"); a.emit(J("gt"), p + "ee")
            e("move x0,%s" % X(ENV), "move #>3,x0", "move x0,%s" % X(STG)); a.emit(J("al"), p + "ee")
            L(p + "e3"); e("move %s,x0" % X(SUSF), "move x0,%s" % X(ENV))
        L(p + "ee")
        # ---- LFO (reverse sawtooth only): PH += TLFO[LRATE]; LV = -PH
        if LFOSYNC:                                                               # < 0: the ARM's increment; >= 0: TLFO[2 v]
            e("move %s,a" % X(P_LRATE), "tst a"); a.emit(J("ge"), p + "lfr")
            e("move r6,b", "sub #>%d,b" % (VB0 - OS2B0 - LFS_INC), "move b,r0"); a.emit(D.NOP); e("move x:(r0),x0"); a.emit(J("al"), p + "lfi")
            L(p + "lfr"); e("asl a"); ld_tab("TLFO", "a", "x0")
            L(p + "lfi")
        else:
            e("move %s,a" % X(P_LRATE)); ld_tab("TLFO", "a", "x0")
        if LFOSHAPE:                                                              # the shape from DFLAGS bits 5-7 (r7 = DFLAGS)
            e("move %s,a" % X(PH), "add x0,a", "move a1,%s" % X(PH))
            e("move x:(r7),b", "lsr #5,b", "and #>7,b", "tst b"); a.emit(J("eq"), p + "l0")
            e("move %s,a" % X(PH))                                                # the wrapped phase p
            for k in range(1, N_LSHAPES):
                e("cmp #>%d,b" % k); a.emit(J("eq"), p + "l%d" % k)
            a.emit(J("al"), p + "l0")
            L(p + "l1"); a.emit(J("al"), p + "lw")                                # saw: p
            L(p + "l2"); e("abs a", "sub #>$400000,a", "asl a"); a.emit(J("al"), p + "lw")             # triangle: 2 |p| - 1
            L(p + "l3"); e("move #>$800000,b", "move #>$7fffff,x0", "tst a", "tge x0,a", "tlt b,a"); a.emit(J("al"), p + "lw")   # square (x0, y0, b: dead here)
            L(p + "l4"); e("move a1,x0", "abs a", "move #>$7fffff,b", "sub a,b", "move b1,y0", "mpy y0,x0,a", "asl #2,a,a"); a.emit(J("al"), p + "lw")   # sine
            L(p + "l5")                                                           # sample & hold: a new value when the phase wraps (p < 0 and p - inc < -1)
            e("tst a"); a.emit(J("ge"), p + "le")
            e("sub x0,a", "cmp #>$800000,a"); a.emit(J("gt" if SHSYNC else "ge"), p + "le")
            e("move x:(r7+3),x0", "move #>$%x,y0" % LCG_K, "mpy y0,x0,a", "asr a", "move a0,b", "add #>$%x,b" % LCG_C, "move b1,x:(r7+3)", "move b1,a")
            a.emit(J("al"), p + "lw")
            if LS_SLEW:
                L(p + "l6")                                                       # slewed sample & hold: y1 = p; at a wrap prev = the old value, a new one
                e("move a,y1", "tst a"); a.emit(J("ge"), p + "l6v")
                e("sub x0,a", "cmp #>$800000,a"); a.emit(J("gt" if SHSYNC else "ge"), p + "l6v")
                e("move x:(r7+3),x0", "move x0,x:(r7+%d)" % (SL_PREV - DFLAGS_OFF), "move #>$%x,y0" % LCG_K, "mpy y0,x0,a", "asr a", "move a0,b", "add #>$%x,b" % LCG_C, "move b1,x:(r7+3)")
                L(p + "l6v")                                                      # LV = prev + (new - prev) x (p + 1) / 2 (the halves keep it in range)
                e("move y1,a", "asr a", "add #>$400000,a", "move a1,x0")
                e("move x:(r7+3),b", "asr b", "move x:(r7+%d),a" % (SL_PREV - DFLAGS_OFF), "asr a", "sub a,b", "move b1,y0")
                e("mpy y0,x0,a", "asl a", "move x:(r7+%d),x1" % (SL_PREV - DFLAGS_OFF), "add x1,a")
                a.emit(J("al"), p + "lw")
            L(p + "l0"); e("neg a")                                               # the reverse saw: as before (from the unwrapped sum)
            L(p + "lw"); e("move a,%s" % X(LV))
            L(p + "le")
        else:
            e("move %s,a" % X(PH), "add x0,a", "move a1,%s" % X(PH), "neg a", "move a,%s" % X(LV))
        if VADRUM:
            e("move x:(r7),a", "and #>4,a"); a.emit(J("ne"), p + "vd")
            e("move %s,x0" % X(ENV), "move x0,x:(r7+1)", "move x0,x:(r7+2)", "move #>0,x0", "move x0,x:(r7+4)"); a.emit(J("al"), p + "vx2")    # the other engines: one envelope for everything, no noise
            L(p + "vd")
            for par, off in ((P_SUS, 2), (P_REL, 1)):                            # the decays of the pitch and the filter envelopes
                e("move %s,b" % X(par), "asr b", "add #>64,b"); ld_tab("TDEC", "b", "x0"); e("mpy x0,x0,a", "move a,x0", "move x:(r7+%d),y0" % off, "mpy y0,x0,a", "move a,x:(r7+%d)" % off)   # (the coefficient squared: twice as fast as the VCA table, 20 ms at 0)
            e("move %s,a" % X(P_LRATE), *(("add #>64,a",) if LFOSYNC else ()), "asl #15,a,a", "move a,x:(r7+4)")        # the noise level (LRATE 127 = 0.5, the level of the oscillator; LFOSYNC: v + 64)
            e("move x:(r7+3),x0", "move #>$%x,y0" % LCG_K, "mpy y0,x0,a", "asr a", "move a0,b", "add #>$%x,b" % LCG_C, "move b1,x:(r7+3)", "move b1,%s" % X(LV))   # LV = a random value per block
            L(p + "vx2")
        # ---- filter: type 0 (DJ) = FILT bipolar, low-pass left / high-pass right, centre off; types 1 band-pass, 2 notch, 3 tilt EQ: FILT = the cutoff (tilt: the direction),
        #      + ENVF * ENV + LFOF * LV + the key tracking (in table steps), table TF[0..63]
        e("move %s,x0" % X(P_ENVF), "move %s,y0" % ("x:(r7+1)" if VADRUM else X(ENV)), "mpy y0,x0,b")
        e("move %s,x0" % X(P_LFOF), "move %s,y0" % X(LV), "mac y0,x0,b")
        if DUAL:                                                                 # two oscillators: the key follow takes the mean of the two notes
            e("move r6,a", "sub #>%d,a" % (VB0 - OSB0 - KEYF_OFF), "move a,r0"); a.emit(D.NOP)
            e("move x:(r0+2),a", "and #>2,a"); a.emit(J("eq"), p + "kn1")
            e("move %s,a" % X(NOTE), "move x:(r0+1),x0", "add x0,a", "asr a"); a.emit(J("al"), p + "kn2")
            L(p + "kn1"); e("move %s,a" % X(NOTE))
            L(p + "kn2"); e("sub #>60,a", "asl #16,a,a", "move a,y0")
            e("move x:(r0),x0", "mac y0,x0,b")
        elif TYPEZONE:                                                           # the key follow (0..127) of the filter type's zone replaces the fixed KEYK
            e("move %s,a" % X(NOTE), "sub #>60,a", "asl #16,a,a", "move a,y0")
            e("move r6,a", "sub #>%d,a" % (VB0 - OSB0 - KEYF_OFF), "move a,r0"); a.emit(D.NOP)
            e("move x:(r0),x0", "mac y0,x0,b")
        else:
            e("move %s,a" % X(NOTE), "sub #>60,a", "asl #16,a,a", "move a,y0", "move #>%d,x0" % KEYK, "mac y0,x0,b")
        e("move %s,a" % X(P_FTYPE), "tst a"); a.emit(J("ne"), p + "ft")
        e("move %s,a" % X(P_FILT), "cmp #>2,a"); a.emit(J("gt"), p + "hp")
        e("cmp #>$fffffe,a"); a.emit(J("lt"), p + "lp")
        # centre: no filter unless a modulation depth is set
        e("move %s,a" % X(P_ENVF), "tst a"); a.emit(J("ne"), p + "cm")
        e("move %s,a" % X(P_LFOF), "tst a"); a.emit(J("ne"), p + "cm")
        e("move #>0,x0", "move x0,%s" % X(FMODE)); a.emit(J("al"), p + "fq")
        L(p + "cm"); e("move #>1,x0", "move x0,%s" % X(FMODE), "move #>$3f,a"); a.emit(J("al"), p + "fi")
        L(p + "lp"); e("move #>1,x0", "move x0,%s" % X(FMODE), "move %s,a" % X(P_FILT), "add #>$40,a"); a.emit(J("al"), p + "fi")
        L(p + "hp"); e("move #>2,x0", "move x0,%s" % X(FMODE), "move %s,a" % X(P_FILT)); a.emit(J("al"), p + "fi")
        L(p + "ft")                                                              # types 1..3: FMODE = type + 2 (3 band-pass, 4 notch, 5 tilt, 6 tilt the other way)
        if TILT:
            e("add #>2,a", "move a1,x0", "move x0,%s" % X(FMODE), "cmp #>5,a"); a.emit(J("ne"), p + "fb")
            e("move %s,a" % X(P_FILT), "tst a"); a.emit(J("lt"), p + "tb")
            e("move #>6,x0", "move x0,%s" % X(FMODE))
            L(p + "tb"); e("move #>32,a"); a.emit(J("al"), p + "fi")
        elif SLOPES:
            e("move a1,x0", "move x0,%s" % X(FMODE))                             # FMODE = the filter type (1 LP12, 2 HP12, 3 BP, 4 notch, 5 LP24, 6 HP24)
        else:
            e("add #>2,a", "move a1,x0", "move x0,%s" % X(FMODE))
        L(p + "fb"); e("move %s,a" % X(P_FILT), "add #>64,a", "asr a")
        L(p + "fi")
        e("add b,a", "tst a"); a.emit(J("ge"), p + "i2"); e("move #>0,a")
        L(p + "i2"); e("cmp #>$3f,a"); a.emit(J("le"), p + "i3"); e("move #>$3f,a")
        L(p + "i3"); ld_tab("TF", "a", "x0"); e("move x0,%s" % X(FF))
        e("move %s,a" % X(P_RES), "asl #16,a,a", "move a,x0", "move #>$%x,y0" % QK, "mpy y0,x0,b")
        e("move #>$%x,a" % q24(Q0), "sub b,a", "move a,%s" % X(FQ))
        L(p + "fq")
        # ---- FX amount (0 = off) and its parameter: threshold = 0.25 + 0.75 * mod (soft: ceiling, hard: clip level, fold: fold point); wavefold: fold point 0.5, bias (mod - 64) / 128
        e("move %s,a" % X(P_FXAMT), "asl #16,a,a", "move a,%s" % X(DRVF))
        e("move %s,a" % X(P_FXTYPE), "cmp #>3,a"); a.emit(J("ne"), p + "fp1")
        e("move %s,a" % X(P_FXMOD), "sub #>64,a", "asl #16,a,a", "move a,%s" % X(FXB), "move #>$400000,x0", "move x0,%s" % X(FXP)); a.emit(J("al"), p + "fp9")
        L(p + "fp1")
        e("move #>0,x0", "move x0,%s" % X(FXB), "move %s,a" % X(P_FXMOD), "asl #16,a,a", "move a,b", "asr b", "asr #2,a,a", "add b,a", "add #>$200000,a", "move a,%s" % X(FXP))
        L(p + "fp9")
        # ---- VCA target T (unity = $100000, full scale = x8): GAIN < 64: GAIN / 64, above: 1 .. 7.9 (+18 dB); + ENVA * ENV * velocity; * tremolo
        e("move %s,a" % X(P_GAIN), "cmp #>64,a"); a.emit(J("ge"), p + "gh")
        e("asl #14,a,a"); a.emit(J("al"), p + "gx")
        L(p + "gh"); e("sub #>64,a", "move a,b", "asl #3,a,a", "sub b,a", "asl #14,a,a", "add #>$100000,a")
        L(p + "gx")                                                              # a = T0 (kept in a: the next lines use b, x0, y0 only)
        if SAMPLER:                                                              # the sample: the envelope term at 1.0 (the VCA open for the one-shot)
            e("move %s,b" % X(P_ENVA), "asl #%d,b,b" % (17 if BISEND else 16), "move b,x0", "move %s,b" % X(ACT), "move #>$7fffff,y0", "cmp #>3,b"); a.emit(J("eq"), p + "vso")
            e("move %s,y0" % X(ENV))
            L(p + "vso"); e("mpy x0,y0,b")
        else:
            e("move %s,b" % X(P_ENVA), "asl #%d,b,b" % (17 if BISEND else 16), "move b,x0", "move %s,y0" % X(ENV), "mpy x0,y0,b")
        e("move b,x0", "move %s,b" % X(VEL), "asl #16,b,b", "move b,y0", "mpy x0,y0,b")
        if BISEND:
            e("asr #3,b,b", "add b,a", "tst a"); a.emit(J("ge"), p + "tp"); e("clr a")
            L(p + "tp"); e("move a,x1")
            e("move %s,a" % X(P_LFOV), "tst a"); a.emit(J("eq"), p + "nt")                                              # tremolo: * (1 - |depth| * (1 - LV') / 2), LV' = LV (depth > 0) or -LV (depth < 0)
            e("move %s,b" % X(LV)); a.emit(J("ge"), p + "ts"); e("neg a", "neg b")
            L(p + "ts"); e("asl #17,a,a", "move a,y0", "move #>$7fffff,a", "sub b,a", "asr a", "move a,x0", "mpy y0,x0,a")
        else:
            e("asr #3,b,b", "add b,a", "move a,x1")
            e("move %s,a" % X(P_LFOV), "tst a"); a.emit(J("eq"), p + "nt")                                              # tremolo: * (1 - depth * (1 - LV) / 2)
            e("asl #16,a,a", "move a,y0", "move #>$7fffff,a", "move %s,b" % X(LV), "sub b,a", "asr a", "move a,x0", "mpy y0,x0,a")
        e("move #>$7fffff,b", "sub a,b", "move b,y0", "mpy x1,y0,a", "move a,x1")
        L(p + "nt")
        e("move x1,%s" % X(GT))
        # VCAON: the VCA stage runs unless GAIN = 64 with no envelope amount and no tremolo
        e("move %s,a" % X(P_ENVA), "tst a"); a.emit(J("ne"), p + "von")
        e("move %s,a" % X(P_LFOV), "tst a"); a.emit(J("ne"), p + "von")
        e("move %s,a" % X(P_GAIN), "cmp #>64,a"); a.emit(J("ne"), p + "von")
        e("move #>0,x0", "move x0,%s" % X(VCAON), "move #>$100000,x0", "move x0,%s" % X(GT), "move x0,%s" % X(GCUR)); a.emit(J("al"), p + "vx")
        L(p + "von"); e("move #>1,x0", "move x0,%s" % X(VCAON))
        L(p + "vx")
        e("move %s,a" % X(GINIT), "tst a"); a.emit(J("eq"), p + "gi")
        e("move %s,x0" % X(GT), "move x0,%s" % X(GCUR), "move #>0,x0", "move x0,%s" % X(GINIT))
        L(p + "gi")
        e("move %s,a" % X(GT), "move %s,x0" % X(GCUR), "sub x0,a", "asr #5,a,a", "move a,%s" % X(GINC))
        if OSC3:
            # ---- oscillator v3: the pitch (as OSC2), the shape parameters of the three families, the morph weights of the four waves
            e("move %s,a" % X(ACT), "cmp #>2,a"); a.emit(J("ne"), p + "oi")
            e("move r6,a", "sub #>%d,a" % (VB0 - OSB0), "move a,r3"); a.emit(D.NOP)
            def modterm(off, src, scale):                                             # the modulation depths are the OSC1 block's (shared by both oscillators)
                e("move x:(r3+%d),b" % off, "asl #17,b,b", "move b,x0", "move %s,y0" % src, "mpy y0,x0,b")
                if scale != 0x7fffff: e("move b,x0", "move #>$%x,y0" % scale, "mpy y0,x0,b")
            def ox(OW, k): return "x:(%s)" % OW if k == 0 else "x:(%s+%d)" % (OW, k)
            def osc_ctrl(OW, note, lab, inc_off):                                       # OW = the block of the oscillator (r3 = OSC1, r4 = OSC2), note = the operand of its note
                e("move %s,a" % note, "move %s,x0" % ox(OW, 0), "add x0,a", "asl #16,a,a")
                e("move %s,b" % ox(OW, 1), "asl #9,b,b", "add b,a")
                modterm(5, "x:(r3+%d)" % VD_EP if VADRUM else X(ENV), 0x180000); e("add b,a")
                modterm(4, X(LV), 0x060000); e("add b,a")
                e("tst a"); a.emit(J("ge"), p + "s1" + lab); e("clr a")
                L(p + "s1" + lab); e("cmp #>$7effff,a"); a.emit(J("le"), p + "s2" + lab); e("move #>$7effff,a")
                L(p + "s2" + lab); e("move a1,x1", "move x1,b", "asr #16,b,b")
                e("move x1,a", "and #>$ffff,a", "asl #7,a,a", "move a,y1")
                a.emit(lambda x: T("add #>$%x,b" % x), "TINC"); e("move b,r0"); a.emit(D.NOP); e("move p:(r0)+,x0", "move p:(r0),y0")
                e("move y0,a", "sub x0,a", "move a,y0", "mpy y1,y0,a", "move x0,b", "add a,b", "move b1,%s" % ox(OW, inc_off))
                # the shape m = (PW - 50) / 50 + ENVW x ENV + LFOW x LV (saturating); fold drive / 8 = 0.125 + 0.86 max(m, 0); saw slope m; pulse threshold 0.94 m
                e("move %s,a" % ox(OW, 3), "sub #>50,a", "asl #17,a,a", "move a,x0", "move #>$51eb85,y0", "mpy y0,x0,a", "asl a")
                modterm(6, X(ENV), 0x7fffff); e("add b,a")
                modterm(7, X(LV), 0x7fffff); e("add b,a")
                e("move a,x0", "tst a"); a.emit(J("ge"), p + "w0" + lab); e("clr a")
                L(p + "w0" + lab); e("move a,y1", "move #>$6e147b,y0", "mpy y1,y0,b", "move #>$100000,a", "add b,a", "move a,%s" % ox(OW, 12))
                if not SUPERSAW: e("move x0,%s" % ox(OW, 13), "move #>$7851ec,y0", "mpy y0,x0,b", "move b,%s" % ox(OW, 14))
                else:
                    e("move #>$7851ec,y0", "mpy y0,x0,b", "move b,%s" % ox(OW, 14))                     # the pulse threshold 0.94 m
                    e("move x0,b", "neg b", "tst b"); a.emit(J("ge"), p + "tc" + lab); e("clr b")
                    L(p + "tc" + lab); e("asr b", "move b,%s" % ox(OW, 13))                             # the triangle's curve c / 2 = max(-m, 0) / 2
                    e("move x0,b", "asr b", "add #>$400000,b", "move b,%s" % ox(OW, SS_W))            # s = (m + 1) / 2 (kept in +42 until the weights)
                    e("move b,y0", "move %s,x0" % ox(OW, inc_off), "mpy y0,x0,b", "move b,x0", "move #>$%x,y0" % int(round(SS_D1 * (1 << 23))), "mpy y0,x0,b")
                    e("move b,%s" % ox(OW, SS_D), "move b,a", "asl a", "add b,a", "move a,%s" % ox(OW, SS_D + 1), "asl a", "move a,%s" % ox(OW, SS_D + 2))   # D, 3 D, 6 D
                # the morph position q = WAVE x 0x10410 (126 -> 0x7ffffc) + ENVM x ENV + LFOM x LV, clamped to 0..1; 3 q = i + f: the weights (1 - f) of wave i and f of wave i + 1
                e("move %s,a" % ox(OW, 2), "asl #16,a,a", "move %s,b" % ox(OW, 2), "asl #10,b,b", "add b,a", "move %s,b" % ox(OW, 2), "asl #4,b,b", "add b,a")
                modterm(8, X(ENV), 0x7fffff); e("add b,a")
                modterm(9, X(LV), 0x7fffff); e("add b,a")
                e("tst a"); a.emit(J("ge"), p + "m1" + lab); e("clr a")
                L(p + "m1" + lab); e("cmp #>$7fffff,a"); a.emit(J("le"), p + "m2" + lab); e("move #>$7fffff,a")
                L(p + "m2" + lab); e("asr #2,a,a", "tfr a,b", "asl a", "add b,a")              # a = 3 q / 4 (22 bits)
                e("move a1,b", "and #>$1fffff,b", "asl #2,b,b", "move b1,y1", "asr #21,a,b")        # y1 = f (23 bit), b1 = i
                e("clr a", "move a,%s" % ox(OW, 15), "move a,%s" % ox(OW, 16), "move a,%s" % ox(OW, 17), "move a,%s" % ox(OW, 18))
                e("move %s,a" % OW, "add #>15,a", "add b,a", "move a,r0"); a.emit(D.NOP)
                e("move #>$7fffff,a", "move y1,x0", "sub x0,a", "move a,x:(r0)+", "move y1,x:(r0)")
                if SUPERSAW:                                                              # the saw's weight w: the centre w (1 - s / 2) / 2, each side w s / 16
                    e("move %s,x0" % ox(OW, SS_W), "move %s,y0" % ox(OW, 17), "mpy y0,x0,b", "move y0,a", "asr b", "sub b,a", "asr a", "move a,%s" % ox(OW, 17),
                      "asr #3,b,b", "move b,%s" % ox(OW, SS_W))
            osc_ctrl("r3", X(NOTE), "", 11)
            if DUAL:                                                                  # the second oscillator: its pitch (own note, tune, fine; the shared vibrato / envelope), shape, morph, and the interaction amounts
                e("move x:(r3+%d),a" % DFLAGS_OFF, "and #>2,a"); a.emit(J("eq"), p + "oi")
                e("move r6,a", "sub #>%d,a" % (VB0 - OS2B0), "move a,r4"); a.emit(D.NOP)
                osc_ctrl("r4", "x:(r3+%d)" % NOTE2_OFF, "b", 19)
                e("move x:(r4+20),a", "tst a"); a.emit(J("eq"), p + "i2p")                  # the signed increment: the direction flag (soft sync) reverses it
                e("move x:(r4+19),a", "neg a", "move a,x:(r4+11)"); a.emit(J("al"), p + "i2d")
                L(p + "i2p"); e("move x:(r4+19),a", "move a,x:(r4+11)")
                L(p + "i2d")
                for srcoff, dstoff in ((4, 25), (6, 24), (7, 27), (8, 26)):                  # MIX, FM, RING, BITSYNC position: 0..127 -> 0..0x7ffff0
                    e("move x:(r4+%d),a" % srcoff, "asl #16,a,a", "move x:(r4+%d),b" % srcoff, "asl #10,b,b", "add b,a", "move x:(r4+%d),b" % srcoff, "asl #4,b,b", "add b,a", "move a,x:(r4+%d)" % dstoff)
                e("move x:(r4+8),a", "lsr #4,a", "add #>1,a", "move a,x:(r4+21)")              # the sync period: every 1 .. 8 master cycles
            L(p + "oi")
        elif OSC2:
            # ---- oscillator v2: the pitch in semitones (1 semitone = 65536), the wave shape c; both per block
            e("move %s,a" % X(ACT), "cmp #>2,a"); a.emit(J("ne"), p + "oi")
            e("move r6,a", "sub #>%d,a" % (VB0 - OSB0), "move a,r3"); a.emit(D.NOP)
            def modterm(off, src, scale):                                        # b = depth (-64..63) x source x scale (24 bit fractions)
                e("move x:(r3+%d),b" % off, "asl #17,b,b", "move b,x0", "move %s,y0" % src, "mpy y0,x0,b")                  # (y0, x0): the other order is a long form that treats y0 as unsigned
                if scale != 0x7fffff: e("move b,x0", "move #>$%x,y0" % scale, "mpy y0,x0,b")
            e("move %s,a" % X(NOTE), "move x:(r3),x0", "add x0,a", "asl #16,a,a")
            e("move x:(r3+1),b", "asl #9,b,b", "add b,a")
            modterm(5, X(ENV), 0x180000); e("add b,a")                           # envelope -> pitch: +-24 semitones
            modterm(4, X(LV), 0x060000); e("add b,a")                            # LFO -> pitch: +-6 semitones
            e("tst a"); a.emit(J("ge"), p + "s1"); e("clr a")
            L(p + "s1"); e("cmp #>$7effff,a"); a.emit(J("le"), p + "s2"); e("move #>$7effff,a")
            L(p + "s2"); e("move a1,x1", "move x1,b", "asr #16,b,b")              # b = the note index
            e("move x1,a", "and #>$ffff,a", "asl #7,a,a", "move a,y1")           # y1 = the fraction (23 bit)
            a.emit(lambda x: T("add #>$%x,b" % x), "TINC"); e("move b,r0"); a.emit(D.NOP); e("move p:(r0)+,x0", "move p:(r0),y0")
            e("move y0,a", "sub x0,a", "move a,y0", "mpy y1,y0,a", "move x0,b", "add a,b", "move b1,x:(r3+9)")
            # the shape m (24 bit fraction, saturating) and what each waveform needs from it: sine / triangle: the fold drive / 8 = 0.125 + 0.86 max(m, 0); saw: m; pulse: the threshold 0.94 m
            e("move x:(r3+3),a", "sub #>64,a", "asl #17,a,a")
            modterm(6, X(ENV), 0x7fffff); e("add b,a")
            modterm(7, X(LV), 0x7fffff); e("add b,a")
            e("move a,x0", "move x:(r3+2),b", "cmp #>2,b"); a.emit(J("eq"), p + "w2"); a.emit(J("gt"), p + "w3")
            e("move x0,a", "tst a"); a.emit(J("ge"), p + "w0"); e("clr a")
            L(p + "w0"); e("move a,x0", "move #>$6e147b,y0", "mpy x0,y0,b", "move #>$100000,a", "add b,a", "move a,x:(r3+10)"); a.emit(J("al"), p + "oi")
            L(p + "w3"); e("move #>$7851ec,y0", "mpy x0,y0,b", "move b,x:(r3+10)"); a.emit(J("al"), p + "oi")
            L(p + "w2"); e("move x0,x:(r3+10)")
            L(p + "oi")
        elif OSC:
            # ---- oscillator increment: TINC[clamp(NOTE + TUNE)] * (1 + fine / 32 + vibrato / 16): fine = FINE (-64..63) / 64 * 1/32, vibrato = LFOP / 64 * LV / 16
            e("move %s,a" % X(ACT), "cmp #>2,a"); a.emit(J("ne"), p + "oi")
            e("move r6,a", "sub #>%d,a" % (VB0 - OSB0), "move a,r3"); a.emit(D.NOP)
            e("move %s,a" % X(NOTE), "move x:(r3),x0", "add x0,a", "tst a"); a.emit(J("ge"), p + "o1"); e("clr a")
            L(p + "o1"); e("cmp #>127,a"); a.emit(J("le"), p + "o2"); e("move #>127,a")
            L(p + "o2"); a.emit(lambda x: T("add #>$%x,a" % x), "TINC"); e("move a,r0"); a.emit(D.NOP); e("move p:(r0),x1")
            e("move x:(r3+1),a", "asl #17,a,a", "move a,y0", "mpy x1,y0,b", "asr #5,b,b")
            e("move x:(r3+4),a", "asl #17,a,a", "move a,y0", "move %s,x0" % X(LV), "mpy x0,y0,a", "move a,y0", "mpy x1,y0,a", "asr #4,a,a", "add a,b")
            e("move x1,a", "add b,a", "move a1,x:(r3+6)")
            L(p + "oi")

    # ================================================================ one channel in place: r0 = first sample, n0 = 2, r6 = block, r7 = filter state (LOW, BAND)
    def channel(p, sp):
        if OSC3:
            # ---- oscillator v3 (vpre only, ACT = 2): the four waves of the shape family mixed with the morph weights; the phase lives in the block (X + 10)
            e("move x:>$%x,a" % RMODE, "tst a"); a.emit(J("ne"), p + "nosc")
            if SAMPLER:                                                           # ---- the sample (ACT = 3)
                y0k = int(round((1 << 38) / int(round(440 * 2 ** ((60 - 69) / 12) / 48000 * (1 << 24)))))
                e("move %s,a" % X(ACT), "cmp #>3,a"); a.emit(J("ne"), p + "nsm")
                e("move r6,a", "sub #>%d,a" % (VB0 - OSB0), "move a,r3"); a.emit(D.NOP)
                e("move r0,r1")
                e("move x:(r3+%d),a" % SM_N, "tst a"); a.emit(J("eq"), p + "smr")            # a new note: which sample, from its start
                e("move #>0,x0", "move x0,x:(r3+%d)" % SM_N, "move a1,b", "and #>$100,b"); a.emit(J("ne"), p + "smx")
                e("move x:(r3+8),a")                                                         # code 25: the track's sample
                L(p + "smx"); e("tst a"); a.emit(J("lt"), p + "smc")
                e("and #>63,a", "asl #2,a,a", "add #>$%x,a" % SM_TAB, "move a1,r4"); a.emit(D.NOP)
                e("move x:(r4)+,x0", "move x:(r4),a"); a.emit(J("al"), p + "sms")
                L(p + "smc"); e("move #>$%x,x0" % SM_CAP, "move x:>$%x,a" % SM_CAPLEN)
                L(p + "sms")
                e("move x0,x:(r3+%d)" % SM_S, "move a1,x:(r3+%d)" % SM_L, "move #>0,x0", "move x0,x:(r3+%d)" % SM_P, "move x0,x:(r3+%d)" % SM_F,
                  "move #>1,x0", "move x0,x:(r3+%d)" % SM_ON)
                L(p + "smr")
                e("move x:(r3+%d),a" % SM_ON, "tst a"); a.emit(J("eq"), p + "smz")
                e("move %s,a" % X(NOTE), "move x:(r3),x0", "add x0,a", "tst a"); a.emit(J("ge"), p + "sm1"); e("clr a")
                L(p + "sm1"); e("cmp #>127,a"); a.emit(J("le"), p + "sm2"); e("move #>127,a")
                L(p + "sm2"); a.emit(lambda x: T("add #>$%x,a" % x), "TINC"); e("move a,r4"); a.emit(D.NOP); e("move p:(r4),x0")
                e("move #>$%x,y0" % y0k, "mpy y0,x0,a")                                     # a1 = the ratio in 9.15
                e("move a1,b", "asr #15,b,b", "move b1,n4", "and #>$7fff,a", "asl #8,a,a", "move a1,y1")   # n4 = its integer part, y1 = the fraction (1.23)
                e("move n4,b", "add #>1,b", "asl #6,b,b", "move x:(r3+%d),x0" % SM_P, "add x0,b", "add #>1,b", "move x:(r3+%d),x0" % SM_L, "cmp x0,b"); a.emit(J("ge"), p + "sme")
                e("move x:(r3+%d),b" % SM_S, "move x:(r3+%d),x0" % SM_P, "add x0,b", "move b1,r4", "move #>$ffffff,m4", "move x:(r3+%d),x1" % SM_F)
                a.emit(D.do_x, 0x3A, p + "sml")
                e("move y:(r4)+,a", "move y:(r4)-,b", "sub a,b", "move b,y0", "move x1,x0", "mac y0,x0,a", "move a,%s:(r0)+n0" % sp, "move x1,b", "add y1,b")
                a.emit(lambda t: T("jclr #23,b1,$%x" % t), p + "smn")
                e("bclr #23,b1", "move (r4)+")
                L(p + "smn"); e("move b1,x1")
                L(p + "sml"); e("move (r4)+n4")
                e("move r4,b", "move x:(r3+%d),x0" % SM_S, "sub x0,b", "move b1,x:(r3+%d)" % SM_P, "move x1,x:(r3+%d)" % SM_F)
                e("move r1,r0"); a.emit(J("al"), p + "nosc")
                L(p + "sme"); e("move #>0,x0", "move x0,x:(r3+%d)" % SM_ON)
                L(p + "smz"); e("clr a")
                a.emit(D.do_x, 0x3A, p + "smzl")
                L(p + "smzl"); e("move a,%s:(r0)+n0" % sp)
                e("move r1,r0"); a.emit(J("al"), p + "nosc")
                L(p + "nsm")
            e("move %s,a" % X(ACT), "cmp #>2,a"); a.emit(J("ne"), p + "nosc")
            e("move r6,a", "sub #>%d,a" % (VB0 - OSB0), "move a,r3"); a.emit(D.NOP)
            e("move r0,r1")
            if GRAN:                                                              # granular: the samples core 1 made (a block of the 2-block delay)
                import granular_dsp as GD
                e("move x:(r3+%d),a" % DFLAGS_OFF, "and #>16,a"); a.emit(J("eq"), p + "ngr")
                e("move x:>$%x,a" % TCNT, "asl #5,a,a", "move x:>$%x,x0" % GD.RDOFS, "add x0,a", "add #>$%x,a" % GD.OUT, "move a1,r4", "move #>$ffffff,m4")
                a.emit(D.do_x, 0x3A, p + "gre")
                e("move x:(r4)+,a")
                L(p + "gre"); e("move a,%s:(r0)+n0" % sp)
                e("move r1,r0"); a.emit(J("al"), p + "nosc")
                L(p + "ngr")
            if FM: e("move x:(r3+%d),a" % FM_FLAG, "tst a"); a.emit(J("ne"), p + "fm")
            if DUAL: e("move x:(r3+%d),a" % DFLAGS_OFF, "and #>2,a"); a.emit(J("ne"), p + "dual")
            def fold():                                                           # b = p (4 g s) -> (1 - 2 |wrap(p - 0.5)|) / 2; x0 is the scratch (x1 keeps the phase)
                e("move b1,x0", "move x0,b", "sub #>$400000,b", "move b1,x0", "move x0,b", "abs b", "asl b", "neg b", "add #>$7fffff,b", "asr b")
            def waves(OW):                                                        # the phase is in x1: a += the four waves of the oscillator whose block is OW (a is clear)
                if SINEFIX:                                                       # P = 4 u (1 - |u|) refined to P (0.775 + 0.225 |P|) (THD 5 % -> 0.1 %), then the drive: p = 4 gh s
                    e("move x1,b", "abs b", "move b,y0", "move #>$7fffff,b", "sub y0,b", "move b,y0", "mpy x1,y0,b", "asl #2,b,b", "move b,y1", "move y1,b", "abs b", "move b,y0", "mpy y1,y0,b",
                      "move b1,y0", "move #>$1ccccd,x0", "mpy y0,x0,b", "move #>$633333,x0", "mac x0,y1,b", "move b,y1", "move x:(%s+12),x0" % OW, "mpy x0,y1,b", "asl #2,b,b"); fold()
                else:
                    e("move x1,b", "abs b", "move b,y0", "move #>$7fffff,b", "sub y0,b", "move b,y0", "mpy x1,y0,b", "move b,y1", "move x:(%s+12),x0" % OW, "mpy x0,y1,b", "asl #4,b,b"); fold()
                e("move b1,y1", "move x:(%s+15),y0" % OW, "mac y1,y0,a")                  # 0 sine (wavefold)
                e("move x1,b", "abs b", "asl b", "sub #>$7fffff,b")
                if SUPERSAW:                                                              # t' = t - c / 2 (1 - t^2): the exponential ramps left of the centre
                    e("move b,y1", "move b,y0", "mpy y0,y0,b", "move b,x0", "move #>$7fffff,b", "sub x0,b", "move b,x0", "move x:(%s+13),y0" % OW, "mpy y0,x0,b",
                      "move b,x0", "move y1,b", "sub x0,b")
                e("move b,y1", "move x:(%s+12),x0" % OW, "mpy x0,y1,b", "asl #2,b,b"); fold()
                e("move b1,y1", "move x:(%s+16),y0" % OW, "mac y1,y0,a")                  # 1 triangle (wavefold)
                if not SUPERSAW:
                    e("move x1,b", "asr b", "add #>$400000,b", "move b,y0", "mpy y0,y0,b", "sub y0,b", "move b,y1", "move x:(%s+13),x0" % OW, "mpy x0,y1,b", "add y0,b", "sub #>$400000,b")
                    e("move b1,y1", "move x:(%s+17),y0" % OW, "mac y1,y0,a")              # 2 saw (slope)
                else:                                                                     # 2 the supersaw: the centre (the phase) and six detuned ones
                    e("move x1,y1", "move x:(%s+17),y0" % OW, "mac y1,y0,a", "move x:(%s+%d),y1" % (OW, SS_W), "move x:(%s+11),x0" % OW)
                    for k in range(6):
                        e("move x:(%s+%d),b" % (OW, SS_PH + k), "add x0,b", "move x:(%s+%d),y0" % (OW, SS_D + k // 2), "add y0,b" if k % 2 == 0 else "sub y0,b",
                          "move b1,x:(%s+%d)" % (OW, SS_PH + k), "move b1,y0", "mac y1,y0,a")
                e("move x:(%s+14),y0" % OW, "move x1,b", "sub y0,b", "asr #23,b,b", "and #>$800000,b", "eor #>$c00000,b")
                e("move b1,y1", "move x:(%s+18),y0" % OW, "mac y1,y0,a")                  # 3 pulse (width)
            def wcall(OW):                                                        # (SUPERSAW) the four waves as a subroutine with OW = r4
                if not SUPERSAW: waves(OW); return
                if OW == "r3": e("move r4,n4", "move r3,r4")
                a.emit(lambda t: [0x0BF080, t], p + "wv")
                if OW == "r3": e("move n4,r4")
            if SUPERSAW: e("move r3,r4")
            a.emit(D.do_x, 0x3A, p + "o3e")
            e("move x:(r3+11),x0", "move x:(r3+10),a", "add x0,a", "move a1,x:(r3+10)", "move a1,x1", "clr a")
            if SUPERSAW: a.emit(lambda t: [0x0BF080, t], p + "wv")
            else: waves("r3")
            L(p + "o3e"); e("move a,%s:(r0)+n0" % sp)
            if DUAL:
                a.emit(J("al"), p + "o3f")
                if SUPERSAW:
                    L(p + "wv"); waves("r4"); a.emit(D.RTS)
                if FM:                                                                # ---- the FM voice (r2 = its operator blocks, y1 = the base increment, r4 / n4 = the outputs)
                    L(p + "fm")
                    e("move r6,a", "add #>$%x,a" % (FMB0 - VB0), "move a,r2", "move #%d,n4" % FMS, "move x:(r3+11),y1", "move #>$ffffff,m4")
                    a.emit(D.do_x, 0x3A, p + "fms")
                    e("move r2,r3", "clr b")
                    a.emit(lambda t: [0x060480, t], p + "fmo")                     # do #4 (the operators)
                    e("move x:(r3+%d),x0" % F_R, "mpy x0,y1,a", "asl #4,a,a", "move x:(r3+%d),x0" % F_PH, "add x0,a", "move a1,x:(r3+%d)" % F_PH, "move a1,x1", "move r2,r4", "clr a")
                    for j in range(4): e("move x:(r3+%d),x0" % (F_M + j), "move x:(r4)+n4,y0", "mac y0,x0,a")
                    e("asl #2,a,a", "add x1,a", "move a1,x1")                      # u = the phase + 4 x the modulation
                    e("move x1,a", "abs a", "move a,y0", "move #>$7fffff,a", "sub y0,a", "move a,y0", "mpy x1,y0,a", "asl #2,a,a")      # 4 u (1 - |u|)
                    e("move a,x0", "move x:(r3+%d),y0" % F_AMP, "mpy y0,x0,a", "move a,x:(r3)", "move a,x0", "move x:(r3+%d),y0" % F_K, "lua (r3+%d),r3" % FMS)
                    L(p + "fmo"); e("mac y0,x0,b")
                    L(p + "fms"); e("move b,%s:(r0)+n0" % sp)
                    e("move r6,a", "sub #>%d,a" % (VB0 - OSB0), "move a,r3", "move x:(r2+%d),x0" % F_NZ, "move x0,x:(r3+%d)" % VD_NL)
                    a.emit(J("al"), p + "o3f")
                # ---- two oscillators: OSC2 (the FM modulator and the slave of the soft sync) first, then OSC1 (phase modulated by OSC2), then the interactions
                L(p + "dual")
                e("move r6,a", "sub #>%d,a" % (VB0 - OS2B0), "move a,r4"); a.emit(D.NOP)
                a.emit(D.do_x, 0x3A, p + "d3e")
                e("move x:(r4+11),x0", "move x:(r4+10),a", "add x0,a", "move a1,x:(r4+10)", "move a1,x1", "clr a")
                wcall("r4")
                e("move a,x:(r4+23)")                                              # o2
                e("move x:(r3+10),y1", "move x:(r3+11),x0", "move y1,a", "add x0,a", "move a1,x:(r3+10)", "move a1,x1")
                e("move x1,a", "cmp y1,a"); a.emit(J("ge"), p + "ns")              # OSC1 wrapped (the new phase is below the old one): a master cycle
                e("move x:(r4+5),a", "cmp #>1,a"); a.emit(J("ne"), p + "ns")        # only in the sync zone
                e("move x:(r4+22),a", "add #>1,a", "move x:(r4+21),x0", "cmp x0,a"); a.emit(J("lt"), p + "sk")
                e("move x:(r4+11),a", "neg a", "move a,x:(r4+11)", "move x:(r4+20),a", "eor #>1,a", "move a,x:(r4+20)", "clr a")      # every N cycles: the slave runs the other way
                L(p + "sk"); e("move a,x:(r4+22)")
                L(p + "ns")
                e("move x:(r4+23),y0", "move x:(r4+24),x0", "mpy y0,x0,b", "asl #3,b,b", "move x1,a", "add b,a", "move a1,x1", "clr a")      # FM: the phase of OSC1 + 8 x FM x o2
                wcall("r3")
                e("move a,x1", "move x:(r4+23),y0")                                # x1 = o1, y0 = o2
                e("move y0,b", "sub x1,b", "move b,y1", "move x:(r4+25),x0", "mpy x0,y1,b", "move x1,a", "add b,a")                   # mix = o1 + MIX (o2 - o1)
                e("move x:(r4+7),b", "tst b"); a.emit(J("eq"), p + "nr")
                e("move x:(r4+23),x0", "mpy x1,x0,b", "asl #1,b,b", "sub a,b", "move b,y1", "move x:(r4+27),x0", "mpy x0,y1,b", "add b,a")   # ring: mix += RING (2 o1 o2 - mix)
                L(p + "nr")
                e("move x:(r4+5),b", "cmp #>2,b"); a.emit(J("lt"), p + "nb")        # the bitwise zones 2 xor, 3 or, 4 nor, 5 and, 6 nand
                e("move a,y1", "move x1,a", "move x:(r4+23),x0")
                e("cmp #>3,b"); a.emit(J("lt"), p + "bx"); a.emit(J("eq"), p + "bo")
                e("cmp #>4,b"); a.emit(J("eq"), p + "bn")
                e("cmp #>5,b"); a.emit(J("eq"), p + "ba")
                e("and x0,a", "not a"); a.emit(J("al"), p + "bd")
                L(p + "bx"); e("eor x0,a"); a.emit(J("al"), p + "bd")
                L(p + "bo"); e("or x0,a"); a.emit(J("al"), p + "bd")
                L(p + "bn"); e("or x0,a", "not a"); a.emit(J("al"), p + "bd")
                L(p + "ba"); e("and x0,a")
                L(p + "bd"); e("move a1,x0")
                e("move x0,a", "move y1,b", "sub b,a", "move a,x0", "move x:(r4+26),y0", "mpy y0,x0,a", "move y1,b", "add b,a")            # result = base + w (bitwise - base)
                L(p + "nb")
                L(p + "d3e"); e("move a,%s:(r0)+n0" % sp)
                L(p + "o3f")
            e("move r1,r0")
            if VADRUM:                                                            # the noise: one generator step per sample, added at its level
                e("move x:(r3+%d),a" % VD_NL, "tst a"); a.emit(J("eq"), p + "nosc")
                e("move a,y1", "move x:(r3+%d),x0" % VD_NS, "move #>$%x,y0" % LCG_K, "move #>$%x,x1" % LCG_C)
                a.emit(D.do_x, 0x3A, p + "nze")
                e("mpy y0,x0,a", "asr a", "move a0,b", "add x1,b", "move b1,x0", "move %s:(r0),a" % sp, "mac x0,y1,a")
                L(p + "nze"); e("move a,%s:(r0)+n0" % sp)
                e("move x0,x:(r3+%d)" % VD_NS, "move r1,r0")
            L(p + "nosc")
        elif OSC2:
            # ---- oscillator v2 (vpre only, ACT = 2): level 0.5; r2 = the shape parameter of the block
            e("move x:>$%x,a" % RMODE, "tst a"); a.emit(J("ne"), p + "nosc")
            e("move %s,a" % X(ACT), "cmp #>2,a"); a.emit(J("ne"), p + "nosc")
            e("move r6,a", "sub #>%d,a" % (VB0 - OSB0), "move a,r3"); a.emit(D.NOP)
            e("move r0,r1", "move x:(r3+9),x0", "move x:(r3+2),b", "move x:(r3+8),a", "move x:(r3+10),r2"); a.emit(D.NOP)
            def fold():                                                           # b = the signal s (+-1) is already scaled: p = 4 gh s wrapped to +-1 (the 24 bit wrap does the modulo 2), out = (1 - 2 |wrap(p - 0.5)|) / 2
                e("move b1,x1", "move x1,b", "sub #>$400000,b", "move b1,x1", "move x1,b", "abs b", "asl b", "neg b", "add #>$7fffff,b", "asr b")
            e("cmp #>2,b"); a.emit(J("lt"), p + "ow01"); a.emit(J("eq"), p + "ow2")
            e("move r2,y0", "move #>$c00000,y1")                                  # 3 pulse: +0.5 while the phase is below the threshold, else -0.5
            a.emit(D.do_x, 0x3A, p + "o3e")
            e("add x0,a", "move a1,x1", "move x1,b", "cmp y0,b", "move #>$400000,b", "tge y1,b")
            L(p + "o3e"); e("move b1,%s:(r0)+n0" % sp)
            a.emit(J("al"), p + "od")
            L(p + "ow2")                                                          # 2 saw with the slope m: r = (u + 1) / 2, out = r + m (r^2 - r) - 0.5
            e("move r2,x1")
            a.emit(D.do_x, 0x3A, p + "o2e")
            e("add x0,a", "move a1,y1", "move y1,b", "asr b", "add #>$400000,b", "move b,y0", "mpy y0,y0,b", "sub y0,b", "move b,y1", "mpy y1,x1,b", "add y0,b", "sub #>$400000,b")
            L(p + "o2e"); e("move b1,%s:(r0)+n0" % sp)
            a.emit(J("al"), p + "od")
            L(p + "ow01")
            e("tst b"); a.emit(J("ne"), p + "ow1")
            a.emit(D.do_x, 0x3A, p + "o0e")                                       # 0 sine, wavefolded: s = 4 u (1 - |u|), drive 8 gh = r2 x 8
            e("add x0,a", "move a1,x1", "move x1,b", "abs b", "move b,y0", "move #>$7fffff,b", "sub y0,b", "move b,y0", "mpy x1,y0,b")
            e("move b,y1", "move r2,x1", "mpy y1,x1,b", "asl #4,b,b"); fold()
            L(p + "o0e"); e("move b1,%s:(r0)+n0" % sp)
            a.emit(J("al"), p + "od")
            L(p + "ow1")                                                          # 1 triangle, wavefolded: s = 2 |u| - 1
            a.emit(D.do_x, 0x3A, p + "o1e")
            e("add x0,a", "move a1,x1", "move x1,b", "abs b", "asl b", "sub #>$7fffff,b", "move b,y1", "move r2,x1", "mpy y1,x1,b", "asl #2,b,b"); fold()
            L(p + "o1e"); e("move b1,%s:(r0)+n0" % sp)
            L(p + "od"); e("move a1,x:(r3+8)", "move r1,r0")
            L(p + "nosc")
        elif OSC:
            # ---- oscillator source (vpre only, ACT = 2): the ring samples of this input are replaced by the oscillator (level 0.5), the phase carried in the block
            e("move x:>$%x,a" % RMODE, "tst a"); a.emit(J("ne"), p + "nosc")
            e("move %s,a" % X(ACT), "cmp #>2,a"); a.emit(J("ne"), p + "nosc")
            e("move r6,a", "sub #>%d,a" % (VB0 - OSB0), "move a,r3"); a.emit(D.NOP)
            e("move r0,r1", "move x:(r3+6),x0", "move x:(r3+2),b", "move x:(r3+5),a")
            e("cmp #>2,b"); a.emit(J("lt"), p + "ow01"); a.emit(J("eq"), p + "ow2")
            # 3 pulse: +0.5 while the phase is below the threshold (PW - 64) << 16, else -0.5
            e("move x:(r3+3),b", "sub #>64,b", "asl #16,b,b", "move b,y0", "move #>$c00000,y1")
            a.emit(D.do_x, 0x3A, p + "o3e")
            e("add x0,a", "move a1,x1", "move x1,b", "cmp y0,b", "move #>$400000,b", "tge y1,b")
            L(p + "o3e"); e("move b1,%s:(r0)+n0" % sp)
            a.emit(J("al"), p + "od")
            L(p + "ow2")                                                          # 2 saw: phase / 2
            a.emit(D.do_x, 0x3A, p + "o2e")
            e("add x0,a", "move a1,x1", "move x1,b", "asr b")
            L(p + "o2e"); e("move b1,%s:(r0)+n0" % sp)
            a.emit(J("al"), p + "od")
            L(p + "ow01")
            e("tst b"); a.emit(J("ne"), p + "ow1")
            # 0 sine: 2 x (1 - |x|) (the parabola 4 x (1 - |x|) at level 0.5)
            a.emit(D.do_x, 0x3A, p + "o0e")
            e("add x0,a", "move a1,x1", "move x1,b", "abs b", "move b,y0", "move #>$7fffff,b", "sub y0,b", "move b,y0", "mpy x1,y0,b", "asl b")
            L(p + "o0e"); e("move b1,%s:(r0)+n0" % sp)
            a.emit(J("al"), p + "od")
            L(p + "ow1")                                                          # 1 triangle: |phase| - 0.5
            a.emit(D.do_x, 0x3A, p + "o1e")
            e("add x0,a", "move a1,x1", "move x1,b", "abs b", "sub #>$400000,b")
            L(p + "o1e"); e("move b1,%s:(r0)+n0" % sp)
            L(p + "od"); e("move a1,x:(r3+5)", "move r1,r0")
            L(p + "nosc")
        def blk_vca():
            # ---- VCA: ramped gain; the stored sample is x * T * 8 (limited)
            e("move %s,a" % X(VCAON), "tst a"); a.emit(J("eq"), p + "nv")
            e(*(("move r0,r1",) if VFF else ()), "move %s,x0" % X(GCUR), "move x0,%s" % X(GRUN))
            a.emit(D.do_x, 0x3A, p + "ce")
            e("move %s,a" % X(GRUN), "move %s,x1" % X(GINC), "add x1,a", "move a,%s" % X(GRUN), "move a,y1", "move %s:(r0),x0" % sp, "mpy x0,y1,b", "asl #3,b,b")
            L(p + "ce"); e("move b,%s:(r0)+n0" % sp)
            e("move r1,r0")
            L(p + "nv")
            # ---- GAIN above the middle: soft saturation of the output
            e("move %s,a" % X(P_GAIN), "cmp #>64,a"); a.emit(J("le"), p + "done")
            if VFF: e("move r0,r1")
            a.emit(D.do_x, 0x3A, p + "se")
            e("move %s:(r0),x0" % sp, "mpy x0,x0,b", "move b,y0", "mpy x0,y0,b", "move x0,a", "sub b,a", "asr a", "add x0,a")
            L(p + "se"); e("move a,%s:(r0)+n0" % sp)
            if VFF: e("move r1,r0")
            L(p + "done")
        def blk_fx():
            e("move r0,r1", "move %s,a" % X(DRVF), "tst a"); a.emit(J("eq"), p + "nf")
            if FXMORE:
                e("move %s,a" % X(P_FXTYPE), "cmp #>4,a"); a.emit(J("lt"), p + "fx0")
                e("move r6,a", "sub #>%d,a" % (VB0 - FXS), "move a,r3"); a.emit(D.NOP)             # r3 = this voice's FX state
                e("move %s,a" % X(P_FXTYPE), "cmp #>5,a"); a.emit(J("eq"), p + "cb"); a.emit(J("gt"), p + "ch")
                # ---- 4 ring mod: a magic-circle oscillator (s += k c; c -= k s, k = TF[FXMOD / 2]) times the input, mixed by the amount: out = x * (1 + m (s - 1))
                e("move x:(r3+1),a", "tst a"); a.emit(J("ne"), p + "rm1"); e("move #>$600000,x0", "move x0,x:(r3+1)")
                L(p + "rm1")
                e("move %s,a" % X(P_FXMOD), "asr a"); ld_tab("TF", "a", "x0"); e("move r1,r0", "move %s,y0" % X(DRVF))
                a.emit(D.do_x, 0x3A, p + "rme")
                e("move x:(r3+1),b", "move x:(r3),a", "move b,y1", "mac x0,y1,a", "move a,x:(r3)", "move a,y1", "mac -x0,y1,b", "move b,x:(r3+1)")
                e("move y1,a", "sub #>$7fffff,a", "asr a", "move a,y1", "mpy y1,y0,a", "asl a", "add #>$7fffff,a", "move a,y1", "move %s:(r0),x1" % sp, "mpy y1,x1,a")
                L(p + "rme"); e("move a,%s:(r0)+n0" % sp)
                a.emit(J("al"), p + "fxr")
                # ---- 5 comb: out = (1 - g) x + g y[n - D], g = 0.875 amount, D = 255 - 2 FXMOD samples (a 256-word circular buffer of the OUTPUT, base CB + 256 t)
                L(p + "cb")
                e("move %s,a" % X(P_FXMOD), "asl #1,a,a", "move #>255,b", "sub a,b")                 # b = D
                ld(TCNT, "a"); e("asl #8,a,a", "add #>%d,a" % CB, "move a,x1", "move a,x:(r3+7)")     # x1 = the base (kept at +7: the loop overwrites x1)
                e("move x:(r3+2),a", "add x1,a", "move a,r2")
                e("move x:(r3+2),a", "sub b,a", "add #>$100,a", "and #>$ff,a", "add x1,a", "move a,r4"); a.emit(D.NOP)
                e("move #>$ff,m2", "move #>$ff,m4")
                e("move %s,a" % X(DRVF), "asr #3,a,b", "sub b,a", "move a,y0", "move #>$7fffff,a", "sub y0,a", "move a,x0")
                a.emit(D.do_x, 0x3A, p + "cbe")
                e("move y:(r4)+,y1", "move %s:(r0),x1" % sp, "mpy x1,x0,a", "mac y1,y0,a", "move a,%s:(r0)+n0" % sp)
                L(p + "cbe"); e("move a,y:(r2)+")
                e("move x:(r3+7),x1", "move r2,a", "sub x1,a", "move a,x:(r3+2)")
                a.emit(J("al"), p + "fxr")
                # ---- 6 chorus: a 512-word circular buffer of the INPUT (base HB + 512 t); the delay = DC + DEP * triangle (a reverse-sawtooth-free triangle LFO, rate TLFO[FXMOD] per block), ramped
                #      linearly over the block, read with linear interpolation; out = x + m ((wet - x) / 2) * 2 / 2 (m = the amount)
                L(p + "ch")
                e("move %s,a" % X(P_FXMOD)); ld_tab("TLFO", "a", "x0"); e("move r1,r0")
                e("move x:(r3+4),a", "add x0,a", "move a1,x:(r3+4)", "move x:(r3+4),a", "abs a", "asl a", "add #>$800000,a", "move a,y1")
                e("move #>$%x,x0" % CHORUS_DEP, "mpy x0,y1,a", "add #>$%x,a" % CHORUS_DC, "move a,x1")                     # x1 = the delay at the end of the block
                e("move x:(r3+5),a", "tst a"); a.emit(J("ne"), p + "ch1"); e("move x1,x:(r3+5)")                          # first block: no ramp
                L(p + "ch1")
                e("move x1,a", "move x:(r3+5),x0", "sub x0,a", "asr #5,a,a", "move a,x:(r3+6)")
                ld(TCNT, "a"); e("asl #9,a,a", "add #>%d,a" % HB, "move a,x:(r3+7)")
                e("move x:(r3+3),a", "move x:(r3+7),x0", "add x0,a", "move a,r2"); a.emit(D.NOP)
                e("move #>$1ff,m2", "move #>$1ff,m4")
                a.emit(D.do_x, 0x3A, p + "che")
                e("move x:(r3+5),a", "move x:(r3+6),x0", "add x0,a", "move a1,x:(r3+5)")
                e("asr #14,a,b", "move b1,x0")                                              # x0 = the integer part of the delay (samples)
                e("move x:(r3+5),a", "and #>$3fff,a", "asl #9,a,a", "move a,y1")           # y1 = the fraction (24 bit)
                e("move r2,a", "sub x0,a", "and #>$1ff,a", "move x:(r3+7),x0", "add x0,a", "move a,r4"); a.emit(D.NOP)
                e("move y:(r4)-,x1", "move y:(r4),x0")                                      # x1 = y[w - Di], x0 = y[w - Di - 1]
                e("move x0,a", "sub x1,a", "asr a", "move a,y0", "mpy y1,y0,a", "asl a", "add x1,a", "move a,y0")     # y0 = the interpolated wet sample
                e("move %s:(r0),x0" % sp, "move x0,y:(r2)+")                               # the input into the buffer
                e("move y0,a", "sub x0,a", "asr a", "move a,y0", "move %s,y1" % X(DRVF), "mpy y1,y0,a", "add x0,a")
                L(p + "che"); e("move a,%s:(r0)+n0" % sp)
                e("move x:(r3+7),x0", "move r2,a", "sub x0,a", "move a,x:(r3+3)")
                a.emit(J("al"), p + "fxr")
                L(p + "fx0")
            # ---- FX: u = x * (1 + 16 amount) limited; types 0 soft (ceiling + cubic), 1 hard (ceiling), 2 fold, 3 wavefold (bias, fold at 0.5)
            a.emit(D.do_x, 0x3A, p + "fe")
            e("move %s:(r0),x0" % sp, "move %s,y0" % X(DRVF), "mpy x0,y0,b", "asl #4,b,b", "add x0,b", "move b,x0")
            e("move %s,a" % X(P_FXTYPE), "cmp #>2,a"); a.emit(J("ge"), p + "fold")
            e("move x0,a", "move %s,b" % X(FXP), "cmp b,a", "tgt b,a", "neg b", "cmp b,a", "tlt b,a", "move a,x0")
            e("move %s,a" % X(P_FXTYPE), "tst a"); a.emit(J("ne"), p + "fe")
            e("mpy x0,x0,b", "move b,y0", "mpy x0,y0,b", "move x0,a", "sub b,a", "asr a", "add x0,a", "move a,x0"); a.emit(J("al"), p + "fe")
            L(p + "fold")
            e("move x0,a", "move %s,b" % X(FXB), "add b,a", "move %s,b" % X(FXP), "sub b,a"); a.emit(J("le"), p + "fl")
            e("neg a", "add b,a"); a.emit(J("al"), p + "fd")
            L(p + "fl"); e("add b,a", "neg b", "cmp b,a"); a.emit(J("ge"), p + "fd")
            e("neg a", "add b,a", "add b,a")
            L(p + "fd"); e("move a,x0")
            L(p + "fe"); e("move x0,%s:(r0)+n0" % sp)
            L(p + "fxr"); e("move r1,r0")
            L(p + "nf")
        def blk_filter():
            # ---- filter (after the FX)
            e("move %s,a" % X(FMODE), "tst a"); a.emit(J("eq"), p + "p2")
            if SLOPES: e("move #0,r2")                                                # r2 = 0: first stage
            L(p + "ps")
            e("move r0,r1", "move x:(r7),a", "move x:(r7+1),x0", "move %s,y0" % X(FF), "move %s,y1" % X(FQ), "move %s,b" % X(FMODE), "cmp #>2,b")
            a.emit(J("eq"), p + "hp")
            if SLOPES: e("cmp #>6,b"); a.emit(J("eq"), p + "hp")
            for m, name in ((3, "bp"), (4, "nt"), (5, "tb"), (6, "tt"))[:4 if TILT else 2]:
                e("cmp #>%d,b" % m); a.emit(J("eq"), p + name)
            tails = (("lp", ("tfr a,b", "asl b")), ("hp", ("move x1,b", "asl b")), ("bp", ("move x0,b", "asl b")), ("nt", ("tfr a,b", "add x1,b", "asl b")),
                     ("tb", ("move x1,b", "asr b", "add a,b", "asl b")), ("tt", ("tfr a,b", "asr b", "add x1,b", "asl b")))
            if not TILT: tails = tails[:4]
            for k, (name, tail) in enumerate(tails):
                if name != "lp": L(p + name)
                a.emit(D.do_x, 0x3A, p + "e_" + name)
                e("mac y0,x0,a")
                e("move %s:(r0),b" % sp, "asr b", "sub a,b", "mac -x0,y1,b", "mac -x0,y1,b", "move b,x1")
                e("tfr x0,b", "mac x1,y0,b", "move b,x0")
                e(*tail)
                L(p + "e_" + name); e("move b,%s:(r0)+n0" % sp)
                if k < len(tails) - 1: a.emit(J("al"), p + "pe")
            L(p + "pe")
            e("move a,x:(r7)", "move x0,x:(r7+1)", "move r1,r0")
            if SLOPES:                                                               # 24 dB: the same SVF again over the block, its own state (r2 != 0 = second stage done)
                e("move %s,a" % X(FMODE), "cmp #>5,a"); a.emit(J("lt"), p + "p2")
                e("move r2,a", "tst a"); a.emit(J("ne"), p + "p2")
                e("move r7,a", "sub #>$%x,a" % (VB0 + LOW0 - S2BASE), "move a,r2"); a.emit(D.NOP); e("move r2,r7"); a.emit(D.NOP); a.emit(J("al"), p + "ps")
            L(p + "p2")
        if ROUTE:                                                                 # per voice (DFLAGS bit 0): 0 = VCA, FX, filter; 1 = filter, VCA, FX
            def rt_test(target):
                e("move r6,a", "sub #>%d,a" % (VB0 - OSB0 - DFLAGS_OFF), "move a,r4"); a.emit(D.NOP)
                e("move x:(r4),a", "and #>1,a"); a.emit(J("ne"), target)
            rt_test(p + "rtf")
            L(p + "rtv"); blk_vca(); blk_fx()
            rt_test(p + "rtx")
            L(p + "rtf"); blk_filter()
            rt_test(p + "rtv")
            L(p + "rtx")
        elif VFF: blk_vca(); blk_fx(); blk_filter()
        else: blk_filter(); blk_fx(); blk_vca()

    REGS = ["x0", "x1", "y0", "y1", "r0", "r1", "r6", "r7", "n0", "m0"] + (["r2"] if SLOPES else []) + (["r3", "r4", "m2", "m4"] if FXMORE else []) + (["n4"] if SAMPLER else [])
    SAVB = SAVX if FXMORE else SAV
    def save_regs():
        for i, r in enumerate(REGS): e("move %s,x:>$%x" % (r, SAVB + i))
    def restore_regs():
        for i, r in enumerate(REGS): e("move x:>$%x,%s" % (SAVB + i, r))

    RMODE, TCH, RBUF = (SAVX + 28, SAVX + 29, SAVX + 30) if FXMORE else (SAV + 12, SAV + 11, SAV + 10)      # 0 ring (vpre) / 1 return (vret), channel of the return, its first sample
    # ================================================================ vpre (from P:$23C): control of the active voices + the line inputs in place
    L("vpre")
    save_regs()
    e("move #>$ffff,m0", "move #>2,n0", "move #>0,x0", "move x0,x:>$%x" % TCNT, "move #>$%x,r6" % VB0); a.emit(D.NOP)
    L("vp_loop")
    mailbox("vm_")
    if GRAN:                                                                      # a new note for core 1: GNEW added into its voice state (same stride)
        import granular_dsp as GD
        e("move %s,x0" % X(GNEW), "move x:(r6+$%x),a" % (GD.VS0 + GD.V_GC - VB0), "add x0,a", "move a1,x:(r6+$%x)" % (GD.VS0 + GD.V_GC - VB0))
    e("move %s,a" % X(ACT), "tst a"); a.emit(J("ne"), "vp_on")
    e("move #>0,x0", "move x0,%s" % X(ACTP)); a.emit(J("al"), "vp_next")
    L("vp_on")
    control("vc_")
    if OSC: e("move %s,a" % X(ACT), "cmp #>2,a"); a.emit(J("eq"), "vp_ring")                  # the oscillator replaces the input: always the ring
    if SAMPLER: e("cmp #>3,a"); a.emit(J("eq"), "vp_ring")                                     # so does the sample
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
    if FB: a.emit(J("al"), "pmfb")
    else: a.emit(D.jmp(premix))

    # ================================================================ vret (from the end of fx_cap, P:$D21 chain): the FX returns of the voices whose strip takes them
    L("vret")
    save_regs()
    e("move #>$ffff,m0", "move #>2,n0", "move #>0,x0", "move x0,x:>$%x" % TCNT, "move #>$%x,r6" % VB0); a.emit(D.NOP)
    L("vq_loop")
    e("move %s,a" % X(ACT), "tst a"); a.emit(J("eq"), "vq_next")
    if OSC: e("cmp #>2,a"); a.emit(J("eq"), "vq_next")
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
    if FB:
        # ================================================================ pmfb: SC10's premix with feedback (vpre ends here; its rts returns to the caller of P:$23C)
        # SC10: with the Setup flag (X:$3A00 bit 0 reverb -> strip 3 = input 1, bit 1 delay -> strip 4 = input 2) the ring samples of that input are zeroed (the strip would hear the
        # ADC); here they get the capture of the previous block instead (mono, x $3a words, at the level of a line input): the strip's sends feed the FX again = feedback.  The
        # capture is taken after vret, so the filter / FX / VCA of the voice are in the loop.  r5 = the first ring frame on exit (as SC10), r1 is restored.
        L("pmfb")
        e("move x:>$3a00,a", "move r1,x:>$%x" % FBSAVE)
        a.emit(D.jclr_a1, 0, "pf_in2")
        e("move y:>$ffd,r5", "move #>$%x,r1" % FBBUF[0])
        a.emit(D.do_x, 0x3A, "pf_l1")
        e("move y:(r1)+,b", "move b,y:(r5)+")
        L("pf_l1"); e("move (r5)+")
        L("pf_in2")
        a.emit(D.jclr_a1, 1, "pf_done")
        e("move y:>$ffd,r5", "move #>$%x,r1" % FBBUF[1])
        e("move (r5)+")
        a.emit(D.do_x, 0x3A, "pf_l2")
        e("move y:(r1)+,b", "move b,y:(r5)+")
        L("pf_l2"); e("move (r5)+")
        L("pf_done")
        e("move x:>$%x,r1" % FBSAVE, "move y:>$ffd,r5")
        a.emit(D.RTS)
    if OSC:
        L("TINC")                                                                 # phase increment per sample (one cycle = 2^24) of MIDI note n at 48 kHz
        for n in range(129 if OSC2 else 128): a.emit([int(round(440 * 2 ** ((n - 69) / 12) / 48000 * (1 << 24))) & 0xFFFFFF])
    return a.assemble()


def install_dsp(s16):
    """Before building: the code is appended to the (wrapped) SC16 DSP code, after the drums; sc_init clears the new memory (X:$3B80..$3BFF)."""
    import drums2_dsp as DD
    prev = s16.dsp_code
    def wrapped(base):
        w, l = prev(base)
        tabs = {k: l[k] for k in ("TATK", "TDEC", "TLFO", "TF")}
        if DD.COMPACT:
            tabs["TDEC"] -= 64                                                   # the compact TDEC starts at the old index 64
        w2, l2 = code(base + len(w), tabs, PREMIX, l["fx_cap"] if FB else RET_OLD)
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
    if FB:                                                                        # P:$D21 jsr fx_cap -> jsr vret (vret ends with jmp fx_cap: the capture sees the processed returns)
        L2.patch_p(img, 0xD21, [0x0BF080, dl["fx_cap"]], [0x0BF080, dl["vret"]])
    else:
        tab = struct.unpack_from("<I", img, 0x08029700 - 0x08010000)[0]           # fx_cap lives above the original program: only the relocated block has it
        o = tab - 0x08010000 + 6 + 3 * (dl["fc_jmp"] + 1)
        assert int.from_bytes(img[o:o + 3], "big") == RET_OLD, hex(int.from_bytes(img[o:o + 3], "big"))
        img[o:o + 3] = dl["vret"].to_bytes(3, "big")
    assert dl["vret"] + 0 < PLIMIT and dl["vchan"] < PLIMIT
