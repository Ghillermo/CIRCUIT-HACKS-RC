"""SC36: the granular synth of the MIDI tracks and the Glitch of Master FX, on DSP core 1 (docs/NOTAS.md «sinte granular», «Glitch»).

Core 1 (its stock loop P:$10E..$12A keeps r5 / m5 = the gather pointer; P:$12A = `jmp c1loop`, as SC35D / SC35DB): once per core-0 block
(the counter CNT, bumped by core 0 at the end of its Master FX chain), with the block number c:
  1. the master block MIN (64 words, L R interleaved, written by core 0 just before CNT) goes into a stereo ring in the external memory
     (L at RL + w, R at RL + RN + w, RN frames; RL is aligned to RN so a1 & (RN - 1) | RL wraps an address);
  2. the two voices (MIDI 1 / 2) whose ACT = 2 with DFLAGS bit 4 (granular): grains read from the sample of the pack chosen by the source
     knob (core 0 publishes start / length of it), up to MAXG per voice, linear interpolation, a trapezoid window; written into OUT[c & 1]
     (32 words per voice);
  3. the Glitch (GIN = on, K1..K4): one tape head reading the ring (nearest sample, stereo): delay K3, speed K1 (top = 1, middle = stopped,
     bottom = backwards), segments of K2 (127 = no repeat: continuous) that repeat, with chaos K4 (random jumps back, mutes, reversals) and
     64-sample fades; into GOUT[c & 1].
The work is cut into short tasks, one per pass of the stock loop (core 0's reads through core 1 must not wait long; SC35DB).
Core 0 reads OUT / GOUT[k & 1] in its block k (CNT = k - 1 then): what core 1 made for c = k - 2, a whole block earlier (latency 2 blocks).

Core-0 pieces: publish (vcf21_dsp, per voice after its mailbox), the pickup (vcf21_dsp channel: the voice's samples = OUT), the tail of the
Master FX chain (sampler_dsp.TAIL: MIN, the Glitch replacing the master, CNT).  The ARM writes the Glitch to X:GARM (core 0): magic, K1..K4.

Values of a voice (the knob codes of the OSC pages, shared with the oscillator; VIN = the copy of core 0's blocks):
  VIN +0 P17 pitch (-64..63 -> +-24 st)   +1 P18 size (+64: 5..500 ms)   +2 P19 position (0..126)   +3 P20 density (0..100 -> 1..16)
      +4 P21 scan (-64..63: speed v|v|/64 samples per block, 0 = freeze)   +5 P22 envelope -> position   +6 P23 zone length (+64)
      +7 P24 LFO -> position   +8 P25 source (0..63 = sample, < 0 = the capture)   +9 P26 note mode (> 0 = slicer)   (+0..+21 = OSB0 + 0..21)
      +20 NOTE2   +21 DFLAGS   +22 P27 LFO -> size   +23 P28 fine (-64..63 = +-1 st)   +24 P29 pitch spray (0..126 = +-12 st)
      +25 P30 window (0..100: rectangle -> triangle -> percussive)   +28 P33 position spray (0..127)   +29 P34 reverse probability (0..127)
      +30 ENV   +31 LV   +32 NOTE   +33 ACT   +34 the count of new notes   +35 S (start, external Y)   +36 L (length)
"""
from __future__ import annotations
import math
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp56 as D  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import probe35_dsp as P5  # noqa: E402

T, J = G.T, G.J
GB = 0x37000                                     # shared X (core 0 clears $30000-$37FFF at boot; the gather list of core 1 ends at $30882)
CNT, MAGW, RNG, WR, LASTC = GB, GB + 1, GB + 2, GB + 3, GB + 4
TASK, OBP, GOBP = GB + 6, GB + 8, GB + 9         # core 1's task (0 idle), the output buffers of the block being made
GIN = GB + 0x10                                  # +0 on, +1..+4 K1..K4 (copied by core 0 from GARM)
VS0, VSS = GB + 0x20, 0x30                       # per voice state (core 1; VSS = the stride of core 0's voice blocks: core 0 adds GNEW into VS + V_GC)
GS = GB + 0x80                                   # Glitch state
RDOFS = GB + 5                                   # 64 x ((CNT + 1) & 1): the buffer core 0 reads in its next block (core 0 writes it)
MIN = GB + 0x100                                 # 64 words
OUT = GB + 0x140                                 # 2 x 64 (voice t at + 32 t)
GOUT = GB + 0x1C0                                # 2 x 64
GR0, GW, MAXG = GB + 0x240, 12, 16               # grains: voice t at GR0 + t * MAXG * GW
SHA = GB + 0x400                                 # core 0 copies (every block, at the end of its Master FX chain): X:$3900..$39BF (the oscillator blocks,
SHB = SHA + 0xC0                                 #   OSB0 + 48 t and OS2B0 = OSB0 + $60 + 48 t), X:$3B80..$3BDF (the voice blocks VB0 + 48 t),
SHT = SHA + 0x120                                #   X:$1D8D.. (the sample table, 64 x 4), the capture length
SHLEN = SHA + 0x220
VBX, OSBX = 0x3B80, 0x3900
C1MAGIC = 0x6A7A01
RL, RN = 0x340000, 0x20000                       # the ring: L at RL.., R at RL + RN.. (frames); $340000-$37FFFF lies in the free $337000-$57F000 (SC35D3)
GARM = 0x3D20                                    # core 0 X (free, dsp_free_scan): +0 = GMAGIC while the Glitch pad is held, +1..+4 K1..K4 (the ARM writes them)
GMAGIC = 0xC0FFEE
CAP_BASE, CAP_LEN = 0xE80000, 0x3D09             # the capture (sampler_dsp HIGH: BASE, X:LEN)
SAMPLE_TAB = 0x1D8D
FADE = 64

# voice state words
V_ON, V_PH, V_PL, V_CD, V_LG, V_ALT, V_Z, V_ZS, V_LGB, V_D, V_I, V_GAIN, V_NL, V_SL, V_L, V_S, V_SPN, V_RC, V_Q, V_LGG, V_SPAN, V_SPR, V_REV = range(23)
V_GC = 30                                        # core 0 adds GNEW (a new note) here
# grain words
G_TOT, G_SEG, G_SID, G_E, G_DE, G_PH, G_PL, G_IH, G_IL, G_LH, G_LR, G_DR = range(12)
# glitch state words
S_ON, S_HH, S_HL, S_SH, S_SL, S_REM, S_PHS, S_E, S_DE, S_STH, S_MUTE, S_DIR, S_BODY, S_RC, S_OV = range(15)

OVERLOAD = False                                 # SC37.5 (see use_overload)
STEREO = False                                   # SC44.7 (see use_stereo)
SOUT = GB + 0x700                                # (STEREO) the sides: 2 x 64 as OUT (voice t at + 32 t); free shared X after SHLEN
SHPAN = GB + 0x780                               # (STEREO) core 0's copy of X:$56..$59: MIDI 1 level, pan, MIDI 2 level, pan
MIXLP = 0x56                                     #   (the stock mixer group writes them: level << 15, pan w = p / 128 by 0x080287C4)
G_SD = 12                                        # (STEREO) grain word: its side gain (-1..1: -w left, +w right)
V_PAN = 23                                       # (STEREO) voice state word: the track's pan w (the chance of a grain on the right)
S_COEF = -0.445                                  # (STEREO) core 0: the sides into the mix arrays = S x GCUR x level x S_COEF: the mid's own gain at low
                                                 #   frequencies (measured on core 0 with the engine's defaults, emu_gstereo_dsp: -0.445 at DC, +0.289 at Nyquist)
GCUR_OFF, VCAON_OFF = 27, 34                     # vcf21_dsp: the ramped VCA gain (unity $100000, x 8) and its on flag in the voice block VB0 + 48 t


def use_stereo():
    """SC44.7 (the user, 2026-10-19: «haz que la dispersion granular sea stereo» · «el valor de paneo de pista controla la proporción / probabilidad de
    izquierda / derecha» · «mantén sk2 dispersión de la posición (centro) y sk4 dispersión stereo» · «junta en sk3 bipolar dispersión tono (+-24) y
    probabilidad reverse» · left reverse, right pitch; mid / side: the sides only follow the VCA gain and the track level):
      * core 1: each grain gets a side gain at its spawn: |w| = Shift + K4 (code 29, 0..126 -> 0..~1; it was the pitch spray), on the right with the
        chance of the track's pan (w = p / 128, the stock mixer's value, copied by core 0), else on the left; the grain adds its samples to OUT as
        before (the mid) and its samples x the side gain to SOUT (the sides);
      * Shift + K3 (code 34) bipolar: left of the centre = the chance of a reversed grain (up to 100 %), right = the pitch spray (up to +-24 st);
      * core 0 (before the master filter, smp_post's hook): L -= S x g, R += S x g per voice, g = the voice's VCA gain (GCUR x 8, 1 with the VCA
        off) x the track level: the sides pass the master filter and Master FX, not the engine's filter / effect, the track's pan or its sends;
      * core 1's program: the moves x:(Rn+d) in their one-word form (dsp56.force_sx), else it does not fit (2047 of 2048 words)."""
    global STEREO, GW, CPT_LIST
    STEREO = True
    GW = 13
    CPT_LIST = CPT_LIST + ((MIXLP, SHPAN, 4),)
OV_CHAOS, OV_BRAKE = 64, 88                      # K4 >= OV_CHAOS: the load (no chaos); K4 >= OV_BRAKE: the head also brakes by K4 - OV_BRAKE steps of K1


def use_overload():
    """SC37.5 (the user, 2026-10-10, after the SC35DB load test: «las pruebas más intensas producían stuttering y reproducción más grave y lenta … sería
    posible reproducir ese efecto de forma segura a través del master fx glitch»): K4 of the Glitch above the middle is a simulated DSP overload instead of
    chaos (the real one: late blocks from ~4 000 external reads per block = clicks at the normal pitch, then the whole audio slower and lower).  Nothing
    is loaded for real: the cost is a few instructions per block.
      * K4 1..63: the chaos as before (same instructions, same random numbers); K4 >= 64: no chaos;
      * late blocks: K4 >= 64, per block p = (K4 - 64) / 128: the head goes 32 frames back (the block is played again: a stutter) and at the next late
        block 32 frames ahead (it catches up), so the head is never ahead of its path and never more than 32 frames behind it (S_OV = 0 / 64);
      * the brake: K4 >= OV_BRAKE with a forward head (K1 >= 64): K1 - (K4 - OV_BRAKE), not below the stop; with K1 at the top it starts at K4 = 96
        and reaches 0.43 x at K4 127 (lower and slower, like the DSP clock in the test)."""
    global OVERLOAD
    OVERLOAD = True


FMLOAD = False                                   # S513D (see use_fmload)
LW = GB + 0x7C0                                  # (FMLOAD) shared X: + 0 LN voices, + 1 LCH chunks a voice, + 2 LS samples a chunk, + 3 LOPS operators (4 / 6),
LN, LCH, LS, LOPS, LREM, LATE, IDLAST, IDMIN, NZ, IDLE, LNP = (LW + i for i in range(11))   # + 4 chunks left, + 5 late blocks, + 6 / + 7 idle
LX = 0x3FE8                                      #   passes the last block / the fewest, + 8 the probe of FLB, + 9 idle passes now, + 10 LN seen; core 0 X:$3FE8..$3FEF = + 0..3 / + 5..8
FLB = 0x2B00                                     # (FMLOAD) core 1's internal X (free on the Rhythm, per Arrhythmia): 4-op blocks at + 0 (4 x 12), 6-op at + $40 (6 x 14), out + $C0


def use_fmload():
    """S513D (diagnostic; the user, 2026-11-04: «¿Podemos mejorar el FM a seis operadores? ¿O mejorar la polifonía?» -> the study «las voces FM en
    el núcleo 1» -> «Si» to its diagnostic): does core 1 have the time for the FM voices?  Core 1 runs LN dummy FM voices a block (the operator loop
    of core 0's FM, vcf21_dsp FMCOMPACT + FMORDER + FMSINE + FMSMOOTH + FBAVG + FMWIDE, instruction for instruction, on garbage data in its
    internal X: no branch depends on it), each cut into LCH tasks of LS samples (one task a pass of the stock loop, after the granular's), with LOPS
    unused (a 6-operator voice ~ 1.5 x a 4-operator one: run 1.5 x the voices).  A new block with chunks left = late (LATE + 1, the rest dropped); IDLE counts the passes with nothing to do (IDLAST the last
    block's, IDMIN the fewest since LN changed: the headroom).  Once at the first pass core 1 ORs X:FLB..FLB + 255 into NZ (0 = nobody used it before).
    Core 0 copies X:LX..LX + 3 (the PC writes them with ctremote.py dspw) into LN..LOPS and LATE..NZ back to X:LX + 4..7 (ctremote.py dspr) each block."""
    global FMLOAD, CPT_LIST
    assert STEREO
    FMLOAD = True
    CPT_LIST = CPT_LIST + ((LX, LW, 4), (LATE, LX + 4, 4))


FMC1 = False                                     # SC51.4 (see use_fmc1)
FNS, FBS = 14, 48                                # (FMC1) the FM slots (12 poly voices + the two tracks' own) and a slot's stride (4 operators of 12 on core 0)
SHF = GB + 0x800                                 # (FMC1) shared X: a slot each FBS words, as core 0 writes it each block: + 0 the increment, + 1 the stamp
                                                 #   (CNT), + 2 the reset count, + 3.. the four operators' R, AMP, K, M1-M4, the feedback's half (8 words each)
OUTF = SHF + FNS * FBS                           # (FMC1) shared X: the slots' samples, two buffers of FNS x 48 (a slot's 32 at its offset), to GB + $FE0
FS, FC, FL, FP, FQ = 0x18, 0x19, 0x1A, 0x1B, 0x1C    # (FMC1) shared X GB + : core 1's slot, task, late blocks, the slot's shared block, its own
FSB = 0x2B00                                     # (FMC1) core 1's internal X: the slots' blocks (FNS x 48 = $2B00-$2D9F; S513D wrote $2B00.. on the device),
FRS = FSB + FNS * FBS                            #   a slot's operator: + 0 OUT, + 1 PH, + 2 AS, + 3 O2, + 4 R, + 5 AMP, + 6 K, + 7..10 M1-M4, + 11 HC; the reset
                                                 #   counts seen at FRS + s
FLATE_X = 0x3FE8                                 # (FMC1) core 0 X: core 1's late blocks (copied each block: vguard reads it)
FCH = 4                                          # (FMC1) samples a task (8 tasks a voice, ~810 instructions each: S513D)


C1MS = False                                     # SC51.5 (see use_c1ms)


def use_c1ms():
    """SC51.5 (S514D2 on the device, 2026-11-04: core 1 started with OMR MS = 1 has P 8 K, X 8 K, Y 8 K, against 2 K / 12 K / 10 K; the stock's
    read service, the granular and the rest sounded right; the user: «all seems good»): with tools/c1ms.py (the stub to core 1 too) the FM slots'
    blocks move under X:$2000 (FSB = $1000, the reset counts after them): 6 K words more of program on core 1 for what comes next."""
    global C1MS, FSB, FRS
    assert FMC1
    C1MS = True
    FSB = 0x1000
    FRS = FSB + FNS * FBS


FM8 = False                                      # (see use_fm8)
F8_ST = 16                                       # (FM8) an operator's words on core 1: + 0 OUT, + 1 PH, + 2 AS, + 3 O2, + 4 R, + 5 AMP, + 6 K, + 7..14 M1-M8, + 15 HC


def use_fm8():
    """The 8-operator FM (the user, 2026-11-04: «FM up to 8 (some algos may not use them all)», «use only the new FM and port the old patches»):
    a slot = 8 operators of F8_ST words (128) on core 1, the same 128 on core 0 (vcf21_dsp.use_fm8) and in the shared copy (SHF = X:$34000:
    + 0 the increment, + 1 the stamp, + 2 the reset count, + 3 N = the operators the algorithm uses (4, 6 or 8), + 4 + 12 k operator k's R, AMP, K,
    M1-M8, HC; the outputs at OUTF = X:$35000, two buffers of FNS x 128: free shared X, the stock's read list ends at $30882).  Core 1 copies and
    renders only N operators with an N-wide modulation sum (paths for 4, 6, 8): a 4-operator patch costs what it costs today."""
    global FM8, FBS, SHF, OUTF, FRS
    assert FMC1 and C1MS
    FM8 = True
    FBS = 8 * F8_ST
    SHF, OUTF = 0x34000, 0x35000
    FRS = FSB + FNS * FBS
    assert SHF + FNS * FBS <= OUTF and OUTF + 2 * FNS * FBS <= 0x36000


def use_fmc1():
    """SC51.4 (the user, 2026-11-04: «amplía el número de voces ahora», after S513D on the device: core 1 runs ~10 FM voices, ~8 with the granular,
    and core 0 never waits): the FM voices of the own synth on core 1.  vcf21_dsp.use_fmc1 puts the FM slots' operator blocks together at
    X:$4000 (12 poly voices + the two tracks' own: FNS x 48) and turns core 0's FM loop into a copy: each block the slot's 48 words (+ 0 = the
    voice's increment, + 12 its stamp = CNT, + 24 its age, + 36 a reset count) go to SHF + (block - $4000), and its 32 samples come from OUTF[RDOFS
    parity] + the same offset (zeros for the first two blocks: core 1 is two blocks behind, as the granular).  Core 1, in the passes with no task
    (after the granular's), walks the FNS slots: a slot whose stamp is this block's (or the next's: core 0 may have copied it again already) is
    rendered, FCH samples a task, with core 0's FM loop instruction for instruction on its own copy in its internal X (FSB + 48 s: the phases, the
    outputs, the smoothed AMP, y[n - 2] stay there; R, AMP, K, M1-M4 and the feedback's half come from the shared copy at its first task); a reset
    count that moved (the ARM wrote a phase, the smoothed AMP or y[n - 2]: a note's start) zeroes those words first.  A new block with slots left =
    late (FST + 2; core 0 copies it to X:FLATE_X, vguard frees voices on it); what was not made stays as it was."""
    global FMC1, CPT_LIST
    assert STEREO and not FMLOAD
    FMC1 = True
    CPT_LIST = CPT_LIST + ((GB + FL, FLATE_X, 1),)


NOVADUMP = False                                 # S516D (see use_novadump)
ND_CMD, ND_SEEN, ND_OFS = GB + 0x7C0, GB + 0x7C4, GB + 0x7C6     # (NOVADUMP) shared: + 0 seq, + 1 source (core 1's X), + 2 words; the seq done; the words copied
ND_Y, ND_X = 0x57C000, 0x3FE8                    # (NOVADUMP) the copy in external Y (the PC reads it with dspx); core 0's X words the PC writes / reads


ND_X2 = 0x5FF0                                   # (S516D2) S516D's X:$3FE8 is also FLATE_X (core 1's late blocks, copied there each block first): the
                                                 # PC's seq was overwritten.  Core 0's X $4000-$5FFF is free (S494D2), past the FM slots of SC51.6


def use_novadump(nd_x=None):
    """S516D (diagnostic; the user, 2026-11-04: «can we take the existing Nova tables for this?» -> step 2): core 1 copies a range of its own external X
    (where the stock keeps the Nova oscillator waves, X:$100000-$41FFFF: tools/study_novawaves.py) to external Y at ND_Y, 256 words a pass with nothing
    else to do; the PC (tools/novadump.py) writes X:$3FE8.. = seq, source, words with dspw, waits for X:$3FEC = seq (core 0 copies both ways each
    block) and reads ND_Y with dspx.  The Glitch left out for room.  Nothing written outside ND_Y."""
    global NOVADUMP, CPT_LIST, ND_X
    assert FMC1 and not MEMDIAG
    NOVADUMP = True
    if nd_x is not None:
        ND_X = nd_x
    CPT_LIST = CPT_LIST + ((ND_X, ND_CMD, 3), (ND_SEEN, ND_X + 4, 1))


WTCOPY = False                                   # (use_wtcopy)
WC_CMD, WC_SEEN, WC_OFS = GB + 0x7E0, GB + 0x7E4, GB + 0x7E6     # (WTCOPY) shared: + 0 seq, + 1 source (core 1's X), + 2 destination (Y), + 3 words;
                                                 # the seq done; the words copied (free in the builds without FMLOAD / NOVADUMP: their GB + 0x7C0..)
WC_X = 0x5210                                    # (WTCOPY) core 0's X: + 0..3 the ARM's command, + 4 the seq done (copied both ways each block)
SJ = GB + 0x7E8                                  # (WTCOPY) shared X: a sample job's state: + 0 the phase, + 1 S, + 2 L, + 3 A, + 4 lag / k / offset, + 5 P,
                                                 # + 6 the destination, + 7 the step, + 8 the level, + 9 the position
SCR = 0x572000                                   # (WTCOPY) external Y (free, past the two tables): the sine (1024), the coefficients (+ $400 a_k, + $500 b_k),
                                                 # the AMDF (+ $800)
WT_H = (256, 256, 256, 192, 128, 96, 64, 48, 32, 24, 16, 12, 8, 6, 4, 3, 2, 1)   # (= vcf21_dsp.WT_H) the levels' harmonics


def use_wtcopy():
    """The wavetable engine (SC52.1): core 1 copies a Nova table from its own external X (where the stock keeps them) to the track's table in
    external Y, which core 0 reads: the ARM writes X:WC_X + 1..3 (source, destination, words), then + 0 = a new seq; core 0 copies them to the
    shared WC_CMD each block; core 1, in a pass with nothing else to do, copies 256 words and, at the end, writes the seq to WC_SEEN, which core 0
    copies back to X:WC_X + 4 (as the novadump of S516D, with a destination).
    A source with bit 23 = a sample's single cycle (method 2: at the sample's own pitch): sample s = source & 63 of the pack's table (core 0's
    X:$1D8D copy, SHT), into the 18 levels at the destination, one short step a pass: the sine table (a rotating phasor, 0.9); the period P by
    the AMDF of 512 samples a quarter into the sample, lags 16..1023 (the first lag within 1/8 of the smallest, then down its slope; a sample
    under 2048 words = itself, up to 1024, as one cycle); one period resampled to 1024 points (linear, 256 a pass), DC out, the peak at 0.225; its
    first 256 harmonics (a DFT, a harmonic a pass); level L = the first WT_H[L] harmonics again (a harmonic a pass), levels 0 / 1 = level 2's
    copy; then the seq seen."""
    global WTCOPY, CPT_LIST
    assert FMC1 and not (NOVADUMP or MEMDIAG or FMLOAD)
    WTCOPY = True
    CPT_LIST = CPT_LIST + ((WC_X, WC_CMD, 4), (WC_SEEN, WC_X + 4, 1))


MEMDIAG = False                                  # S514D (see use_memdiag)
MREP = 0x57C000                                  # (MEMDIAG) the report, external Y (16 bits a word: values << 8; in the free $380000-$57EFFF, past the imports)
M_XN, M_YN = 384, 256                            # (MEMDIAG) 64-word blocks scanned: X $0000-$5FFF, Y $0000-$3FFF
M_SCI = 0x1D                                     # (MEMDIAG) shared X GB + : the next block to scan
M_TESTS = dict(p=(0x0600, 0x07FF, 0x0800, 0x0A00, 0x0C00, 0x0E00, 0x0FFF, 0x1000, 0x1800, 0x2000, 0x2800, 0x3000, 0x3800, 0x3FFF, 0x4000, 0x6000),
               x=(0x2B00, 0x2FFF, 0x3000, 0x3800, 0x3FFF, 0x4000, 0x4800, 0x5000, 0x5800, 0x5FFF, 0x6000, 0x7000, 0x7FFF, 0x8000, 0xA000, 0xBFFF),
               y=(0x1FFF, 0x2000, 0x2400, 0x2800, 0x2C00, 0x2FFF, 0x3000, 0x3800, 0x3FFF, 0x4000, 0x5000, 0x5FFF, 0x6000, 0x7FFF, 0x8000, 0xBFFF))
M_PAT = 0xA5C3E1


def use_memdiag():
    """S514D / S514D2 (diagnostic; the user, 2026-11-04: «diagnostic the 4k», «diagnostic every remaining unknown area, to make sure we know our
    budget»): core 1 reports its own memory, which neither the ARM nor core 0 can read.  Once, at its first pass (the interrupts masked a word at a
    time): its OMR, and for 16 addresses of each of P, X and Y (M_TESTS) whether a pattern written there reads back (the word put back at once).
    Then, in the passes with nothing else to do (after the granular's tasks and the FM slots), one 64-word block a pass of X $0000-$5FFF and Y
    $0000-$3FFF: its sum (compared with the first scan's: a block whose sum changed counts one more pass) and whether it holds anything but zeros.
    All in external Y at MREP (the PC reads it with ctremote.py dspx): + 0 $C1DD, + 1 / + 2 the OMR's low 16 / high 8 bits, + 6 the scans done,
    + 8.. the P tests, + 24.. X, + 40.. Y (1 = read back), + 64 + 3 k: block k's first sum, the scans it differed, not all zero.  The Glitch (and
    the mechanical gesture) left out for room, as in S513D."""
    global MEMDIAG
    assert STEREO and FMC1
    MEMDIAG = True


def tables():
    t = {}
    t["SIZE_T"] = [int(round(240 * 100 ** (v / 127))) for v in range(128)]                       # 5 ms .. 500 ms
    t["PT"] = [int(round(2 ** (k / 12) * (1 << 19))) & 0xFFFFFF for k in range(-48, 38)]         # Q19, -48 .. +37 semitones
    win = []
    for w in range(101):
        if w <= 50: fa = fr = 5 + (123 * w) // 50
        else: fa, fr = 128 - (123 * (w - 50)) // 50, 128 + (123 * (w - 50)) // 50
        win.append(fa << 12 | fr)
    t["WIN_T"] = win
    t["GAIN_T"] = [int(round(0.6 / math.sqrt(d) * (1 << 23))) for d in range(1, 17)]
    return t


def model_window(w):
    """(fa, fr) of the window knob w (0..100), in 1/256 of the grain: 0 rectangle (2 %), 50 triangle, 100 percussive; k = w' x 2519 >> 10 (~ x 2.46)."""
    w = max(0, min(100, w))
    if w <= 50:
        k = (w * 2519) >> 10; return 5 + k, 5 + k
    k = ((w - 50) * 2519) >> 10; return 128 - k, 128 + k


def core1_code(base, gb_src=None, rl=RL, rn=RN, maxg=MAXG, cap_base=CAP_BASE):
    """The core-1 block (appended after the stock words).  rl / rn: the ring (tests use a small one)."""
    a = D.Asm(base)
    if STEREO: a.force_sx = True
    L = a.label
    def e(*lines):
        for l in lines: a.emit(T(l))
    def jsr(lab): a.emit(lambda t: [0x0BF080, t], lab)
    def jmp(lab): a.emit(J("al"), lab)
    def jc(cc, lab): a.emit(J(cc), lab)
    def do_i(n, lab): a.emit(lambda t: T("do #%d,$%x" % (n, t + 1)), lab)
    def do_r(r, lab): a.emit(lambda t: T("do %s,$%x" % (r, t + 1)), lab)
    def tab(reg, name): a.emit(lambda t: T("add #>$%x,%s" % (t, reg)), name)
    def X(r, off): return "x:(%s+%d)" % (r, off)
    tabs = tables()
    MREGS = ("m0", "m1", "m2", "m3", "m4", "m6", "m7")

    # ================================================================ c1loop (from P:$12A): one short task per pass, so the stock loop keeps serving core 0's reads
    #   TASK 0: wait for a new block (CNT), then the ring, the output buffers -> 1;  1: voice 0;  2 .. MAXG + 1: its grains;  MAXG + 2: voice 1;  then its grains;  last: the Glitch -> 0
    L("c1loop")
    e("move #>$ffffff,m0")                                                                     # (the interrupt handler saves / restores m0; the stock loop uses only r5 / m5)
    e("move x:>$%x,a" % TASK, "tst a"); jc("ne", "c1_task")
    e("move x:>$%x,a" % CNT, "move x:>$%x,x0" % LASTC, "cmp x0,a"); jc("eq", "c1_idl" if (FMLOAD or FMC1) else "c1_out0")
    e("move x:>$%x,a" % MAGW, "move #>$%x,x0" % C1MAGIC, "cmp x0,a"); jc("eq", "c1_ok")
    for m in MREGS[1:]: e("move #>$ffffff,%s" % m)                                            # first time: the other M registers linear for good
    e("clr a", "move #>$%x,r0" % (GB + 0x18)); a.emit(D.NOP)                                     # first time: voice / glitch state, grains (not MIN)
    do_i(MIN - GB - 0x18, "c1_clr"); L("c1_clr"); e("move a,x:(r0)+")
    e("move #>$%x,r0" % GR0); a.emit(D.NOP)
    do_i(2 * maxg * GW, "c1_clg"); L("c1_clg"); e("move a,x:(r0)+")
    e("move a,x:>$%x" % WR, "move #>$%x,x0" % C1MAGIC, "move x0,x:>$%x" % MAGW, "move #>$1234,x0", "move x0,x:>$%x" % RNG)
    if MEMDIAG:                                                                                # (S514D) first time: the report cleared, the OMR, the tests
        e("clr a", "move #>$%x,r4" % MREP); a.emit(D.NOP)
        do_i(64 + 3 * (M_XN + M_YN), "md_c"); L("md_c"); e("move a,y:(r4)+")
        e("move #>$%x,r4" % MREP, "move #>$c1dd00,x0"); a.emit(D.NOP)
        e("move x0,y:(r4)+", "move omr,a", "move a1,x0", "asl #8,a,a", "move a1,y:(r4)+", "move x0,a", "asr #8,a,a", "and #>$ff00,a", "move a1,y:(r4)+")
        e("move #>$%x,r4" % (MREP + 8), "move #>$%x,x0" % M_PAT, "move #>$100,y1"); a.emit(D.NOP)
        for sp in ("p", "x", "y"):
            a.emit(lambda t, sp=sp: T("move #>$%x,r1" % t), "md_t" + sp); a.emit(D.NOP)
            do_i(16, "md_l" + sp)
            e("move p:(r1)+,r0"); a.emit(D.NOP)
            e("ori #$03,mr", "move %s:(r0),b" % sp, "move x0,%s:(r0)" % sp); a.emit(D.NOP); a.emit(D.NOP)
            e("move %s:(r0),a" % sp, "move b,%s:(r0)" % sp, "andi #$fc,mr", "clr b", "cmp x0,a", "teq y1,b")
            L("md_l" + sp); e("move b1,y:(r4)+")
    if FMLOAD:                                                                                 # (S513D) first time: does anything use X:FLB..FLB + 255?
        e("clr b", "move #>$%x,r0" % FLB); a.emit(D.NOP)
        do_i(256, "fl_ck"); e("move x:(r0)+,x0"); L("fl_ck"); e("or x0,b")
        e("move b1,x:>$%x" % NZ)
    L("c1_ok")
    e("move x:>$%x,a" % CNT, "move a1,x:>$%x" % LASTC)
    if FMC1:                                                                                   # (SC51.4) slots left from the last block = late; from the first slot
        def F(k): return "x:(r1+%d)" % k
        e("move #>$%x,r1" % GB); a.emit(D.NOP)
        e("move %s,a" % F(FS), "cmp #%d,a" % FNS); jc("ge", "fc_ok")
        e("move %s,a" % F(FL), "add #1,a", "move a1,%s" % F(FL))
        L("fc_ok")
        e("clr a", "move a,%s" % F(FS), "move a,%s" % F(FC), "move #>$%x,x0" % SHF, "move x0,%s" % F(FP), "move #>$%x,x0" % FSB, "move x0,%s" % F(FQ))
    if FMLOAD:                                                                                 # (S513D) the last block's load: late?  the idle passes; this block's chunks
        def W(k): return "x:(r1+%d)" % (k - LW)
        e("move #>$%x,r1" % LW); a.emit(D.NOP)
        e("move %s,a" % W(LREM), "tst a"); jc("eq", "fl_nl")
        e("move %s,a" % W(LATE), "add #>1,a", "move a1,%s" % W(LATE))
        L("fl_nl")
        e("move %s,a" % W(LN), "move %s,x0" % W(LNP), "cmp x0,a"); jc("eq", "fl_s")
        e("move a1,%s" % W(LNP), "clr a", "move a,%s" % W(LATE), "move #>$7fffff,x0", "move x0,%s" % W(IDMIN))
        L("fl_s")
        e("move %s,a" % W(IDLE), "move a1,%s" % W(IDLAST), "move %s,x0" % W(IDMIN), "cmp x0,a"); jc("ge", "fl_nm")
        e("move a1,%s" % W(IDMIN))
        L("fl_nm")
        e("clr a", "move a,%s" % W(IDLE))
        e("move %s,x0" % W(LN), "move %s,y0" % W(LCH), "mpy y0,x0,a", "asr a", "move a0,%s" % W(LREM))
    # ---- the ring
    e("move #>$%x,r0" % MIN, "move x:>$%x,a" % WR, "move #>$%x,x0" % rl, "add x0,a", "move a1,r4", "move #>$%x,n4" % rn)
    do_i(32, "c1_rw")
    e("move x:(r0)+,x0", "move x0,y:(r4)", "move x:(r0)+,x0", "move x0,y:(r4+n4)")
    L("c1_rw"); e("move (r4)+")
    e("move x:>$%x,a" % WR, "add #>32,a", "and #>$%x,a" % (rn - 1), "move a1,x:>$%x" % WR)
    # ---- the output buffers of this block
    e("move x:>$%x,a" % LASTC, "and #>1,a", "asl #6,a,a", "move a1,x0", "move #>$%x,a" % OUT, "add x0,a", "move a1,x:>$%x" % OBP)
    e("move #>$%x,a" % GOUT, "add x0,a", "move a1,x:>$%x" % GOBP, "move #>1,x0", "move x0,x:>$%x" % TASK)
    jmp("c1_out0")
    L("c1_task")
    e("cmp #>1,a"); jc("eq", "c1_v0")
    e("cmp #>%d,a" % (2 + maxg)); jc("lt", "c1_g0"); jc("eq", "c1_v1")
    e("cmp #>%d,a" % (3 + 2 * maxg)); jc("lt", "c1_g1")
    e("move x:>$%x,r1" % GOBP); a.emit(D.NOP); jsr("glitch")                                        # the last task: the Glitch, then idle
    e("clr a", "move a,x:>$%x" % TASK); jmp("c1_out0")
    for t in range(2):
        L("c1_v%d" % t)
        e("move #>$%x,r6" % (SHA + 48 * t), "move #>$%x,r7" % (VS0 + VSS * t), "move #>$%x,r3" % (GR0 + t * maxg * GW), "move x:>$%x,a" % OBP)
        if STEREO: e("move x:>$%x,x0" % (SHPAN + 2 * t + 1), "move x0,%s" % X("r7", V_PAN))
        if t: e("add #>32,a")
        e("move a1,r1"); a.emit(D.NOP); jsr("voice"); jmp("c1_next")
        L("c1_g%d" % t)
        e("sub #>%d,a" % (2 + t * (maxg + 1)), "move a1,x0", "move #>%d,x1" % GW, "mpy x1,x0,a", "asr a", "move a0,a", "add #>$%x,a" % (GR0 + t * maxg * GW), "move a1,r2")
        e("move #>$%x,r7" % (VS0 + VSS * t), "move x:>$%x,a" % OBP)
        if t: e("add #>32,a")
        e("move a1,r1", "move %s,a" % X("r7", V_ON), "tst a"); jc("eq", "c1_next")
        e("move x:(r2),a", "tst a"); jc("eq", "c1_next")
        jsr("grain")
        if t == 0: jmp("c1_next")
    L("c1_next")
    e("move x:>$%x,a" % TASK, "add #>1,a", "move a1,x:>$%x" % TASK)
    L("c1_out0")
    a.emit(D.jmp(P5.C1_LOOP))
    if FMC1 and FM8:                                                                           # (FM8) an idle pass: a task of the FM slots, N operators
        def F(k): return "x:(r1+%d)" % k
        st = F8_ST
        PH, AS, O2, R_, AMP, K_, M1, HC = 1, 2, 3, 4, 5, 6, 7, 15
        L("c1_idl")
        e("move #>$%x,r1" % GB); a.emit(D.NOP)
        e("move %s,a" % F(FS), "cmp #%d,a" % FNS); jc("ge", "c1_scan" if MEMDIAG else "c1_nd" if NOVADUMP else "c1_wc" if WTCOPY and FMC1 else "c1_out0")
        e("move %s,r2" % F(FP), "move %s,r4" % F(FQ), "move %s,b" % F(FC), "tst b"); jc("ne", "fc_run")
        e("move x:(r2+1),a", "move %s,x0" % F(LASTC - GB), "cmp x0,a"); jc("eq", "fc_ld")
        e("add #1,a", "cmp x0,a"); jc("ne", "fc_nx")
        L("fc_ld")                                                                             # its first task: a reset?  then N operators' parameters
        e("move %s,n6" % F(FS), "move #>$%x,r6" % FRS); a.emit(D.NOP)
        e("move x:(r2+2),a", "move x:(r6+n6),x0", "cmp x0,a"); jc("eq", "fc_nr")
        e("move a1,x:(r6+n6)", "clr a", "move r4,r0", "move #%d,n0" % (st - 4))
        do_i(8, "fc_z"); e("move a,x:(r0)+", "move a,x:(r0)+", "move a,x:(r0)+", "move a,x:(r0)+"); L("fc_z"); e("move (r0)+n0")
        L("fc_nr")
        e("lua (r2+4),r0", "lua (r4+%d),r3" % R_, "move #%d,n3" % (st - 12), "move x:(r2+3),x1")
        do_r("x1", "fc_po")
        do_i(12, "fc_pi"); e("move x:(r0)+,x0"); L("fc_pi"); e("move x0,x:(r3)+")
        L("fc_po"); e("move (r3)+n3")
        L("fc_run")                                                                            # one task: FCH samples into OUTF[LASTC & 1] + the slot's offset + FCH x task
        e("move r2,a", "add #>$%x,a" % (OUTF - SHF), "move %s,b" % F(LASTC - GB), "and #1,b"); jc("eq", "fc_p0")
        e("add #>$%x,a" % (FNS * FBS))
        L("fc_p0"); e("move %s,b" % F(FC), "asl #2,b,b", "add b,a", "move x:(r2),y1", "move a1,r0")
        e("move x:(r2+3),b", "cmp #4,b"); jc("le", "fc_w4")
        e("cmp #6,b"); jc("le", "fc_w6")
        for W in (8, 6, 4):                                                                    # r6 = operator 1's block, r7 = the top one's (the loop runs top down)
            L("fc_w%d" % W)
            e("move r4,r6", "move r4,a", "add #>%d,a" % ((W - 1) * st), "move #%d,n4" % st, "move a1,r2")
            e("move a1,r7")
            do_i(FCH, "fc_e%d" % W)
            e("clr b")
            do_i(W, "fc_o%d" % W)
            e("move x:(r2+%d),a" % AMP, "move x:(r2+%d),x0" % AS, "sub x0,a", "asr #5,a,a", "add x0,a", "move a,x:(r2+%d)" % AS)
            e("move x:(r2+%d),x0" % R_, "mpy x0,y1,a", "asl #7,a,a", "move x:(r2+%d),x0" % PH, "add x0,a", "move a1,x:(r2+%d)" % PH, "move a1,x1")
            e("move x:(r2+%d),x0" % M1, "move x:(r4)+n4,y0")
            a.emit([0x46CCD0])                                                                   # mpy y0,x0,a x:(r4)+n4,y0
            for j in range(1, W - 1):
                e("move x:(r2+%d),x0" % (M1 + j)); a.emit([0x46CCD2])                             # mac y0,x0,a x:(r4)+n4,y0
            e("move x:(r2+%d),x0" % (M1 + W - 1), "mac y0,x0,a", "move r6,r4")
            e("move x:(r2+%d),x0" % HC, "move x:(r2+%d),y0" % O2, "mac y0,x0,a")
            e("asl #2,a,a", "add x1,a", "move a1,x1")
            e("move x1,a", "abs a", "move a,y0", "mpy -x1,y0,a", "add x1,a", "asl #2,a,a")
            e("abs a a,x0", "move a,y0", "mpy y0,x0,a", "sub x0,a", "asr #2,a,a", "add x0,a", "move a,x0")
            e("move x:(r2+%d),y0" % AS)
            a.emit([0x45E2D0])                                                                   # mpy y0,x0,a x:(r2),x1
            a.emit([0x182200])                                                                   # move a,x:(r2) a,y0
            e("move x1,x:(r2+%d)" % O2)
            e("move x:(r2+%d),x0" % K_, "lua (r2-%d),r2" % st)
            L("fc_o%d" % W); e("mac y0,x0,b")
            e("move r7,r2")
            L("fc_e%d" % W); e("move b,x:(r0)+")
            if W != 4: jmp("fc_tk")
        L("fc_tk")
        e("move %s,a" % F(FC), "add #1,a", "move a1,%s" % F(FC), "cmp #%d,a" % (32 // FCH)); jc("lt", "c1_out0")
        L("fc_nx")
        e("clr a", "move a,%s" % F(FC), "move %s,a" % F(FS), "add #1,a", "move a1,%s" % F(FS))
        e("move %s,a" % F(FP), "add #>%d,a" % FBS, "move a1,%s" % F(FP), "move %s,a" % F(FQ), "add #>%d,a" % FBS, "move a1,%s" % F(FQ))
        jmp("c1_out0")
    elif FMC1:                                                                                 # (SC51.4) an idle pass: a task of the FM slots
        def F(k): return "x:(r1+%d)" % k
        K, st = 4, 12
        PH, AS, O2, R_, AMP, K_, M1, HC = 1, 2, 3, 4, 5, 6, 7, 11                                # core 1's own layout (the parameters together)
        L("c1_idl")
        e("move #>$%x,r1" % GB); a.emit(D.NOP)
        e("move %s,a" % F(FS), "cmp #%d,a" % FNS); jc("ge", "c1_scan" if MEMDIAG else "c1_nd" if NOVADUMP else "c1_wc" if WTCOPY and FMC1 else "c1_out0")  # every slot done
        e("move %s,r2" % F(FP), "move %s,r4" % F(FQ), "move %s,b" % F(FC), "tst b"); jc("ne", "fc_run")
        e("move x:(r2+1),a", "move %s,x0" % F(LASTC - GB), "cmp x0,a"); jc("eq", "fc_ld")         # its stamp: this block's (core 0 copied it again)
        e("add #1,a", "cmp x0,a"); jc("ne", "fc_nx")                                              #   or the last one's; else not sounding
        L("fc_ld")                                                                             # its first task: a reset?  then the parameters
        e("move %s,n6" % F(FS), "move #>$%x,r6" % FRS); a.emit(D.NOP)
        e("move x:(r2+2),a", "move x:(r6+n6),x0", "cmp x0,a"); jc("eq", "fc_nr")
        e("move a1,x:(r6+n6)", "clr a", "move r4,r0", "move #8,n0")
        do_i(K, "fc_z"); e("move a,x:(r0)+", "move a,x:(r0)+", "move a,x:(r0)+", "move a,x:(r0)+"); L("fc_z"); e("move (r0)+n0")
        L("fc_nr")
        e("lua (r2+3),r0", "lua (r4+%d),r3" % R_, "move #4,n3")
        do_i(K, "fc_po")
        do_i(8, "fc_pi"); e("move x:(r0)+,x0"); L("fc_pi"); e("move x0,x:(r3)+")
        L("fc_po"); e("move (r3)+n3")
        L("fc_run")                                                                            # one task: FCH samples into OUTF[LASTC & 1] + the slot's offset + FCH x task
        e("move r2,a", "add #>$%x,a" % (OUTF - SHF), "move %s,b" % F(LASTC - GB), "and #1,b"); jc("eq", "fc_p0")
        e("add #>$%x,a" % (FNS * FBS))
        L("fc_p0"); e("move %s,b" % F(FC), "asl #2,b,b", "add b,a", "move x:(r2),y1", "move a1,r0")
        e("move r4,a", "add #%d,a" % (3 * st), "move #%d,n4" % st, "move a1,r2")
        do_i(FCH, "fc_e")
        e("clr b")
        do_i(K, "fc_o")                                                                          # core 0's FM loop (vcf21_dsp FMCOMPACT ...), core 1's offsets
        e("move x:(r2+%d),a" % AMP, "move x:(r2+%d),x0" % AS, "sub x0,a", "asr #5,a,a", "add x0,a", "move a,x:(r2+%d)" % AS)
        e("move x:(r2+%d),x0" % R_, "mpy x0,y1,a", "asl #7,a,a", "move x:(r2+%d),x0" % PH, "add x0,a", "move a1,x:(r2+%d)" % PH, "move a1,x1")
        e("move x:(r2+%d),x0" % M1, "move x:(r4)+n4,y0")
        a.emit([0x46CCD0])                                                                       # mpy y0,x0,a x:(r4)+n4,y0
        for j in (1, 2):
            e("move x:(r2+%d),x0" % (M1 + j)); a.emit([0x46CCD2])                                 # mac y0,x0,a x:(r4)+n4,y0
        e("move x:(r2+%d),x0" % (M1 + 3), "mac y0,x0,a", "lua (r4-%d),r4" % (K * st))
        e("move x:(r2+%d),x0" % HC, "move x:(r2+%d),y0" % O2, "mac y0,x0,a")
        e("asl #2,a,a", "add x1,a", "move a1,x1")
        e("move x1,a", "abs a", "move a,y0", "mpy -x1,y0,a", "add x1,a", "asl #2,a,a")
        e("abs a a,x0", "move a,y0", "mpy y0,x0,a", "sub x0,a", "asr #2,a,a", "add x0,a", "move a,x0")
        e("move x:(r2+%d),y0" % AS)
        a.emit([0x45E2D0])                                                                       # mpy y0,x0,a x:(r2),x1
        a.emit([0x182200])                                                                       # move a,x:(r2) a,y0
        e("move x1,x:(r2+%d)" % O2)
        e("move x:(r2+%d),x0" % K_, "lua (r2-%d),r2" % st)
        L("fc_o"); e("mac y0,x0,b")
        e("lua (r2+%d),r2" % (K * st))
        L("fc_e"); e("move b,x:(r0)+")
        e("move %s,a" % F(FC), "add #1,a", "move a1,%s" % F(FC), "cmp #%d,a" % (32 // FCH)); jc("lt", "c1_out0")
        L("fc_nx")                                                                             # the next slot
        e("clr a", "move a,%s" % F(FC), "move %s,a" % F(FS), "add #1,a", "move a1,%s" % F(FS))
        e("move %s,a" % F(FP), "add #%d,a" % FBS, "move a1,%s" % F(FP), "move %s,a" % F(FQ), "add #%d,a" % FBS, "move a1,%s" % F(FQ))
        jmp("c1_out0")
    if FMLOAD:                                                                                 # (S513D) an idle pass: a chunk of the dummy FM voices, or count it
        def W(k): return "x:(r1+%d)" % (k - LW)
        K, st, base = 4, 12, FLB                                                                 # core 0's FM loop (vcf21_dsp, FMCOMPACT ...): 4 operators of 12 words
        top, AS, O2, HC = base + 3 * st, 9, 10, 11                                               #   (+ 0 OUT, + 1 PH, + 2 R, + 3 AMP, + 4 K, + 5..8 M, AS, O2, HC)
        L("c1_idl")
        e("move #>$%x,r1" % LW); a.emit(D.NOP)
        e("move %s,a" % W(LREM), "tst a"); jc("ne", "fl_go")
        e("move %s,a" % W(IDLE), "add #>1,a", "move a1,%s" % W(IDLE)); jmp("c1_out0")
        L("fl_go")
        e("sub #>1,a", "move a1,%s" % W(LREM), "move %s,a" % W(LS), "tst a", "move a1,n0"); jc("eq", "c1_out0")
        e("move #>$%x,r2" % top, "move #>$%x,r4" % base, "move #%d,n4" % st, "move #>$%x,r0" % (FLB + 0xC0), "move #>$123456,y1")
        do_r("n0", "fm_e")
        e("clr b")
        do_i(K, "fm_o")
        e("move x:(r2+3),a", "move x:(r2+%d),x0" % AS, "sub x0,a", "asr #5,a,a", "add x0,a", "move a,x:(r2+%d)" % AS)
        e("move x:(r2+2),x0", "mpy x0,y1,a", "asl #7,a,a", "move x:(r2+1),x0", "add x0,a", "move a1,x:(r2+1)", "move a1,x1")
        e("move x:(r2+5),x0", "move x:(r4)+n4,y0")
        a.emit([0x46CCD0])                                                                       # mpy y0,x0,a x:(r4)+n4,y0
        for j in (6, 7):
            e("move x:(r2+%d),x0" % j); a.emit([0x46CCD2])                                        # mac y0,x0,a x:(r4)+n4,y0
        e("move x:(r2+8),x0", "mac y0,x0,a", "lua (r4-%d),r4" % (K * st))
        e("move x:(r2+%d),x0" % HC, "move x:(r2+%d),y0" % O2, "mac y0,x0,a")
        e("asl #2,a,a", "add x1,a", "move a1,x1")
        e("move x1,a", "abs a", "move a,y0", "mpy -x1,y0,a", "add x1,a", "asl #2,a,a")
        e("abs a a,x0", "move a,y0", "mpy y0,x0,a", "sub x0,a", "asr #2,a,a", "add x0,a", "move a,x0")
        e("move x:(r2+%d),y0" % AS)
        a.emit([0x45E2D0])                                                                       # mpy y0,x0,a x:(r2),x1
        a.emit([0x182200])                                                                       # move a,x:(r2) a,y0
        e("move x1,x:(r2+%d)" % O2)
        e("move x:(r2+4),x0", "lua (r2-%d),r2" % st)
        L("fm_o"); e("mac y0,x0,b")
        e("lua (r2+%d),r2" % (K * st))
        L("fm_e"); e("move b,x:(r0)+")
        jmp("c1_out0")

    # ================================================================ rnd: x0 = the next value of the generator (s x $0343FD + $269EC3, 24 bit); uses a, y0
    L("rnd")
    e("move x:>$%x,x0" % RNG, "move #>$0343fd,y0", "mpy y0,x0,a", "asr a", "move a0,a", "add #>$269ec3,a", "move a1,x:>$%x" % RNG, "move a1,x0")
    a.emit(D.RTS)
    # ================================================================ udiv: a0 = a / x0 (a = 48-bit dividend, a2 = 0, x0 > 0, quotient < 2^23)
    L("udiv")
    e("asl a", "andi #$fe,ccr", "rep #24", "div x0,a")
    a.emit(D.RTS)

    # ================================================================ voice (r1 out, r6 VIN, r7 VS, r3 grains)
    L("voice")
    e("clr a", "move r1,r0"); a.emit(D.NOP)
    if STEREO:
        e("move #>$%x,n0" % (SOUT - OUT))
        do_i(32, "v_clr"); e("move a,x:(r0+n0)"); L("v_clr"); e("move a,x:(r0)+")
    else:
        do_i(32, "v_clr"); L("v_clr"); e("move a,x:(r0)+")
    e("move %s,a" % X("r6", 212), "cmp #>2,a"); jc("ne", "v_off")
    e("move %s,a" % X("r6", 21), "and #>16,a"); jc("eq", "v_off")
    e("move %s,a" % X("r6", 8), "tst a"); jc("ge", "v_tab")                                  # the source: < 0 = the capture, else the sample table entry
    e("move #>$%x,x0" % cap_base, "move x:>$%x,a" % SHLEN); jmp("v_src")
    L("v_tab")
    e("and #>63,a", "asl #2,a,a", "add #>$%x,a" % SHT, "move a1,r0"); a.emit(D.NOP); e("move x:(r0)+,x0", "move x:(r0),a")
    L("v_src")
    e("move x0,%s" % X("r7", V_S), "move #>256,x0", "cmp x0,a"); jc("lt", "v_off")
    e("move a1,%s" % X("r7", V_L))
    e("move %s,a" % X("r7", V_ON), "tst a"); jc("ne", "v_on")
    e("clr a", "move r3,r0", "move #>%d,n0" % GW); a.emit(D.NOP)                                  # switched on: no grain, playhead 0
    do_i(maxg, "v_gc"); L("v_gc"); e("move a,x:(r0)+n0")
    e("move a,%s" % X("r7", V_PH), "move a,%s" % X("r7", V_PL), "move a,%s" % X("r7", V_CD), "move a,%s" % X("r7", V_ALT))
    e("move %s,x0" % X("r7", V_GC), "move x0,%s" % X("r7", V_LG), "move #>1,x0", "move x0,%s" % X("r7", V_ON))
    L("v_on")
    # ---- the zone: pitch mode Z = L (P23 + 65) / 128, start (L - Z) P19 / 128; slicer: Z = L / 16, start = Z ((NOTE - 36) & 15)
    e("move %s,a" % X("r6", 9), "tst a"); jc("gt", "v_slice")
    e("move %s,a" % X("r6", 6), "add #>65,a", "move a1,x0", "move %s,x1" % X("r7", V_L), "mpy x1,x0,a", "asr a", "asr #7,a,a", "move a0,b")
    e("move #>64,x0", "cmp x0,b", "tlt x0,b", "move b1,%s" % X("r7", V_Z))
    e("move %s,a" % X("r7", V_L), "sub b,a", "move a1,x1", "move %s,x0" % X("r6", 2), "mpy x1,x0,a", "asr a", "asr #7,a,a", "move a0,%s" % X("r7", V_ZS))
    jmp("v_zd")
    L("v_slice")
    e("move %s,a" % X("r7", V_L), "asr #4,a,a", "move a1,%s" % X("r7", V_Z), "move a1,x1")
    e("move %s,a" % X("r6", 211), "sub #>36,a", "and #>15,a", "move a1,x0", "mpy x1,x0,a", "asr a", "move a0,%s" % X("r7", V_ZS))
    L("v_zd")
    # ---- a new note: spawn now; the slicer starts its slice again
    e("move %s,a" % X("r7", V_GC), "move %s,x0" % X("r7", V_LG), "cmp x0,a"); jc("eq", "v_ne")
    e("move a1,%s" % X("r7", V_LG), "clr b", "move b,%s" % X("r7", V_CD))
    e("move %s,a" % X("r6", 9), "tst a"); jc("le", "v_ne")
    e("move b,%s" % X("r7", V_PH), "move b,%s" % X("r7", V_PL))
    L("v_ne")
    # ---- the playhead: += P21 |P21| / 64 samples per block, inside [0, Z)
    e("move %s,x0" % X("r6", 4), "move x0,a", "abs a", "move a1,x1", "mpy x1,x0,a", "asr a", "move a0,a", "asl #18,a,a")
    e("move %s,b" % X("r7", V_PH), "move %s,b0" % X("r7", V_PL), "add a,b", "move %s,x0" % X("r7", V_Z))
    e("cmp x0,b"); jc("lt", "v_w1")
    e("sub x0,b", "cmp x0,b"); jc("lt", "v_w2"); e("clr b"); jmp("v_w2")
    L("v_w1"); e("tst b"); jc("ge", "v_w2")
    e("add x0,b", "tst b"); jc("ge", "v_w2"); e("clr b")
    L("v_w2"); e("move b1,%s" % X("r7", V_PH), "move b0,%s" % X("r7", V_PL))
    # ---- the grain size: SIZE_T[P18 + 64] x (1 + P27 / 64 x LV), >= 64
    e("move %s,a" % X("r6", 1), "add #>64,a", "and #>$7f,a"); tab("a", "SIZE_T"); e("move a1,r0"); a.emit(D.NOP); e("move p:(r0),x0")
    e("move %s,a" % X("r6", 96), "asl #17,a,a", "move a,y0", "move %s,y1" % X("r6", 218), "mpy y1,y0,b", "move b,y0", "mpy y0,x0,b", "add x0,b")
    e("move #>64,x1", "cmp x1,b", "tlt x1,b", "move b1,%s" % X("r7", V_LGB))
    # ---- density D = 1 + P20 x 154 / 1024 (1..16), the spawn interval Lg / D, the gain
    e("move %s,x0" % X("r6", 3), "move #>154,x1", "mpy x1,x0,a", "asr a", "asr #10,a,a", "move a0,a", "add #>1,a")
    e("move #>1,x0", "cmp x0,a", "tlt x0,a", "move #>16,x0", "cmp x0,a", "tgt x0,a", "move a1,%s" % X("r7", V_D))
    e("move a1,x0", "clr a", "move %s,a0" % X("r7", V_LGB)); jsr("udiv"); e("move a0,%s" % X("r7", V_I))
    e("move %s,a" % X("r7", V_D), "sub #>1,a"); tab("a", "GAIN_T"); e("move a1,r0"); a.emit(D.NOP); e("move p:(r0),x0", "move x0,%s" % X("r7", V_GAIN))
    # ---- spawn: the countdown -= 32; while <= 0 (at most 4): a grain, += the interval; a debt is forgotten
    e("move %s,a" % X("r7", V_CD), "sub #>32,a", "move a1,%s" % X("r7", V_CD), "move #>4,x0", "move x0,%s" % X("r7", V_SPN))
    L("v_sp")
    e("move %s,a" % X("r7", V_CD), "tst a"); jc("gt", "v_spd")
    jsr("spawn")
    e("move %s,a" % X("r7", V_CD), "move %s,x0" % X("r7", V_I), "add x0,a", "move a1,%s" % X("r7", V_CD))
    e("move %s,a" % X("r7", V_SPN), "sub #>1,a", "move a1,%s" % X("r7", V_SPN)); jc("ne", "v_sp")
    e("move %s,a" % X("r7", V_CD), "tst a"); jc("ge", "v_spd"); e("clr a", "move a,%s" % X("r7", V_CD))
    L("v_spd")
    a.emit(D.RTS)
    L("v_off")
    e("clr a", "move a,%s" % X("r7", V_ON))
    a.emit(D.RTS)

    # ================================================================ spawn: one grain into a free slot (r6 VIN, r7 VS, r3 grains); uses r0, r2, r4
    L("spawn")
    e("move r3,r2", "move #>%d,b" % maxg, "move #>%d,n2" % GW); a.emit(D.NOP)
    L("sp_f")
    e("move x:(r2),a", "tst a"); jc("eq", "sp_ok")
    e("move (r2)+n2", "sub #>1,b"); jc("ne", "sp_f")
    a.emit(D.RTS)
    L("sp_ok")
    e("move %s,x0" % X("r7", V_LGB), "move x0,%s" % X("r7", V_LGG))
    # ---- the pitch in 1/64 semitone: P17 (+-24) x 64 + P28 + (the note - 60) x 64 (pitch mode; two notes alternate) + the spray
    e("move %s,a" % X("r6", 0), "move #>24,x1", "cmp x1,a", "tgt x1,a", "move #>$ffffe8,x1", "cmp x1,a", "tlt x1,a", "asl #6,a,a")
    e("move %s,x0" % X("r6", 97), "add x0,a")
    e("move %s,b" % X("r6", 9), "tst b"); jc("gt", "sp_nn")
    e("move %s,b" % X("r7", V_ALT), "move #>1,x0", "eor x0,b", "move b1,%s" % X("r7", V_ALT), "move %s,x0" % X("r6", 211)); jc("eq", "sp_n1")
    e("move %s,x0" % X("r6", 20))
    L("sp_n1")
    e("move x0,b", "sub #>60,b", "asl #6,b,b", "move b1,x0", "add x0,a")
    L("sp_nn")
    e("move a1,%s" % X("r7", V_Q))
    jsr("rnd")
    if STEREO:                                                                                     # code 34 right of the centre: rnd x v / 64 x 24 st
        e("move %s,b" % X("r6", 103), "tst b"); jc("ge", "sp_ps"); e("clr b")
        L("sp_ps"); e("asl #17,b,b", "move b,y0", "mpy y0,x0,b", "move b,x1", "move #>1536,x0", "mpy x1,x0,b")
    else:
        e("move %s,b" % X("r6", 98), "asl #16,b,b", "move b,y0", "mpy y0,x0,b", "move b,x1", "move #>768,x0", "mpy x1,x0,b")
    e("move %s,a" % X("r7", V_Q), "move b1,x0", "add x0,a")
    e("move #>%d,x0" % (36 * 64 + 63), "cmp x0,a", "tgt x0,a", "move #>$%x,x0" % ((-48 * 64) & 0xFFFFFF), "cmp x0,a", "tlt x0,a")
    # ---- the increment q (Q19) = PT[st] + (PT[st + 1] - PT[st]) x frac / 64
    e("move a1,y1", "move a1,b", "asr #6,b,b", "add #>48,b"); tab("b", "PT"); e("move b1,r0"); a.emit(D.NOP)
    e("move p:(r0)+,x0", "move p:(r0),b", "sub x0,b", "move b1,x1", "move y1,b", "and #>63,b", "asl #17,b,b", "move b1,y0", "mpy x1,y0,b", "add x0,b")
    e("move b1,%s" % X("r7", V_Q))
    # ---- the span Lg x q >> 19; longer than L - 4: span = L - 4, Lg = (L - 4) << 19 / q
    e("move %s,x0" % X("r7", V_LGG), "move b1,x1", "mpy x1,x0,b", "asl #4,b,b")
    e("move %s,a" % X("r7", V_L), "sub #>4,a", "cmp b,a"); jc("ge", "sp_sp")
    e("move a1,b", "asr #5,a,a", "move %s,x0" % X("r7", V_Q)); jsr("udiv"); e("move a0,%s" % X("r7", V_LGG))
    L("sp_sp")
    e("move b1,%s" % X("r7", V_SPAN))
    # ---- the position spray: rnd x P33 / 128 x L / 2
    jsr("rnd")
    e("move %s,a" % X("r6", 102), "asl #16,a,a", "move a,y0", "mpy y0,x0,a", "move a,x0", "move %s,a" % X("r7", V_L), "asr a", "move a1,y0", "mpy y0,x0,a", "move a1,%s" % X("r7", V_SPR))
    # ---- g = zone start + playhead + Z x (P22 / 64 x ENV + P24 / 64 x LV) + the spray, clamped into [0, L - 4 - span]
    e("move %s,b" % X("r6", 5), "asl #17,b,b", "move b,x0", "move %s,y0" % X("r6", 215), "mpy y0,x0,b")
    e("move %s,a" % X("r6", 7), "asl #17,a,a", "move a,x0", "move %s,y0" % X("r6", 218), "mac y0,x0,b")
    e("move b,x0", "move %s,y0" % X("r7", V_Z), "mpy y0,x0,b")
    e("move %s,x0" % X("r7", V_PH), "add x0,b", "move %s,x0" % X("r7", V_ZS), "add x0,b", "move %s,x0" % X("r7", V_SPR), "add x0,b")
    e("tst b"); jc("ge", "sp_c1"); e("clr b")
    L("sp_c1")
    e("move %s,a" % X("r7", V_L), "sub #>4,a", "move %s,x0" % X("r7", V_SPAN), "sub x0,a", "move a1,x0", "cmp x0,b", "tgt x0,b")
    # ---- reversed with probability P34 / 128: start at g + span, the increment negated
    e("move b1,%s" % X("r7", V_SPR))
    jsr("rnd")
    if STEREO:                                                                                     # code 34 left of the centre: the chance (-v) x 2 / 128
        e("move %s,b" % X("r6", 103), "neg b"); jc("ge", "sp_rv"); e("clr b")
        L("sp_rv"); e("asl b", "move b1,y1")
        # the side from the low 16 bits of the same random word: +w on the right with the chance of the pan, else -w
        e("clr a", "move x0,a1", "and #>$ffff,a", "asl #7,a,a", "move %s,x1" % X("r7", V_PAN), "move %s,b" % X("r6", 98), "asl #16,b,b", "cmp x1,a"); jc("lt", "sp_sr")
        e("neg b")
        L("sp_sr"); e("move b1,%s" % X("r2", G_SD))
        e("clr a", "move x0,a1", "and #>$7f0000,a", "asr #16,a,a", "move y1,x0", "clr b", "move #>1,x1", "cmp x0,a", "tlt x1,b", "move b1,%s" % X("r7", V_REV))
    else:
        e("clr a", "move x0,a1", "and #>$7f0000,a", "asr #16,a,a", "move %s,x0" % X("r6", 103), "clr b", "move #>1,x1", "cmp x0,a", "tlt x1,b", "move b1,%s" % X("r7", V_REV))
    e("move %s,b" % X("r7", V_SPR), "move %s,x0" % X("r7", V_S), "add x0,b")
    e("move %s,a" % X("r7", V_Q), "asr #19,a,a", "move %s,y0" % X("r7", V_REV)); a.emit(G.JCLR(0, "y0"), "sp_fw")
    e("neg a", "move %s,x0" % X("r7", V_SPAN), "add x0,b")
    L("sp_fw")
    e("move b1,%s" % X("r2", G_PH), "clr b", "move b,%s" % X("r2", G_PL), "move a1,%s" % X("r2", G_IH), "move a0,%s" % X("r2", G_IL))
    # ---- the window: La = Lg fa / 256, Lr = Lg fr / 256 (>= 1), Lh = Lg - La - Lr (>= 0); de_a = gain / La, de_r = -(La de_a) / Lr
    e("move %s,a" % X("r6", 99), "tst a"); jc("ge", "sp_w0"); e("clr a")
    L("sp_w0"); e("move #>100,x0", "cmp x0,a", "tgt x0,a", "move #>50,x0", "cmp x0,a"); jc("gt", "sp_w2")      # y0 = fa, y1 = fr (model_window)
    e("move a1,x0", "move #>2519,x1", "mpy x1,x0,a", "asr a", "asr #10,a,a", "move a0,a", "add #>5,a", "move a1,y0", "move a1,y1"); jmp("sp_w3")
    L("sp_w2")
    e("sub x0,a", "move a1,x0", "move #>2519,x1", "mpy x1,x0,a", "asr a", "asr #10,a,a", "move a0,x0", "move #>128,a", "sub x0,a", "move a1,y0", "move #>128,a", "add x0,a", "move a1,y1")
    L("sp_w3")
    e("move %s,x0" % X("r7", V_LGG), "mpy y0,x0,a", "asr a", "asr #8,a,a", "move a0,a", "move #>1,x1", "cmp x1,a", "tlt x1,a")
    e("move a1,%s" % X("r2", G_SEG), "move a1,b")
    e("mpy x0,y1,a", "asr a", "asr #8,a,a", "move a0,a", "cmp x1,a", "tlt x1,a", "move a1,%s" % X("r2", G_LR))
    e("add a,b", "move x0,a", "sub b,a"); jc("ge", "sp_lh"); e("clr a")
    L("sp_lh"); e("move a1,%s" % X("r2", G_LH))
    e("move %s,x0" % X("r2", G_SEG), "clr a", "move %s,a0" % X("r7", V_GAIN)); jsr("udiv")
    e("move a0,x1", "move x1,%s" % X("r2", G_DE), "mpy x1,x0,a", "asr a", "move a0,a", "move a1,y0")
    e("clr a", "move y0,a0", "move %s,x0" % X("r2", G_LR)); jsr("udiv"); e("move a0,a", "neg a", "move a1,%s" % X("r2", G_DR))
    e("move %s,a" % X("r2", G_SEG), "move %s,x0" % X("r2", G_LH), "add x0,a", "move %s,x0" % X("r2", G_LR), "add x0,a", "move a1,%s" % X("r2", G_TOT))
    e("clr a", "move a,%s" % X("r2", G_SID), "move a,%s" % X("r2", G_E))
    a.emit(D.RTS)

    # ================================================================ grain: 32 samples (or until it ends) added to r1 (r2 = the grain); uses r0, r4
    L("grain")
    e("move r1,r0", "move #>32,x0", "move x0,%s" % X("r7", V_NL))
    if STEREO: e("move #>$%x,n0" % (SOUT - OUT))
    e("move %s,a" % X("r2", G_PH), "move %s,a0" % X("r2", G_PL))
    L("g_l")
    e("move %s,b" % X("r7", V_NL), "move %s,x0" % X("r2", G_SEG), "cmp x0,b", "tgt x0,b", "tst b"); jc("eq", "g_seg")
    e("move b1,x1")
    e("move %s,b" % X("r7", V_NL), "sub x1,b", "move b1,%s" % X("r7", V_NL))
    e("move %s,b" % X("r2", G_SEG), "sub x1,b", "move b1,%s" % X("r2", G_SEG))
    e("move %s,b" % X("r2", G_TOT), "sub x1,b", "move b1,%s" % X("r2", G_TOT))
    do_r("x1", "g_e")
    e("move %s,b" % X("r2", G_E), "move %s,x0" % X("r2", G_DE), "add x0,b", "move b1,%s" % X("r2", G_E), "move b1,y1")
    e("move a1,r4", "move a0,b", "lsr b", "move b1,x0", "move y:(r4)+,y0", "move y:(r4),b", "sub y0,b", "asr b", "move b1,x1", "mpy x1,x0,b", "asl b", "add y0,b")
    if STEREO:                                                                                     # the mid as before, the sides = the sample x the side gain
        e("move b1,x0", "mpy x0,y1,b", "move b,x0", "move x:(r0),b", "add x0,b", "move b,x:(r0)")
        e("move %s,y0" % X("r2", G_SD), "mpy y0,x0,b", "move x:(r0+n0),x1", "add x1,b", "move b,x:(r0+n0)", "move (r0)+")
        e("move %s,x1" % X("r2", G_IH), "move %s,x0" % X("r2", G_IL))
    else:
        e("move b1,x0", "mpy x0,y1,b", "move x:(r0),x1", "add x1,b", "move b,x:(r0)+", "move %s,x1" % X("r2", G_IH), "move %s,x0" % X("r2", G_IL))
    L("g_e"); e("add x,a")
    e("move %s,b" % X("r2", G_SEG), "tst b"); jc("ne", "g_chk")
    L("g_seg")
    e("move %s,b" % X("r2", G_SID), "add #>1,b", "move b1,%s" % X("r2", G_SID))
    e("cmp #>1,b"); jc("ne", "g_s2")
    e("move %s,x0" % X("r2", G_LH), "move x0,%s" % X("r2", G_SEG), "clr b", "move b,%s" % X("r2", G_DE)); jmp("g_chk")
    L("g_s2")
    e("cmp #>2,b"); jc("ne", "g_dead")
    e("move %s,x0" % X("r2", G_LR), "move x0,%s" % X("r2", G_SEG), "move %s,x0" % X("r2", G_DR), "move x0,%s" % X("r2", G_DE)); jmp("g_chk")
    L("g_dead")
    e("clr b", "move b,%s" % X("r2", G_TOT)); jmp("g_x")
    L("g_chk")
    e("move %s,b" % X("r2", G_TOT), "tst b"); jc("le", "g_dead")
    e("move %s,b" % X("r7", V_NL), "tst b"); jc("ne", "g_l")
    L("g_x")
    e("move a1,%s" % X("r2", G_PH), "move a0,%s" % X("r2", G_PL))
    a.emit(D.RTS)

    if MEMDIAG:                                                                                # (S514D) a pass with nothing to do: one 64-word block summed
        NCH = M_XN + M_YN
        L("c1_scan")
        e("move x:(r1+%d),a" % M_SCI, "cmp #>%d,a" % NCH); jc("lt", "sc_k")
        e("clr a", "move y:>$%x,b" % (MREP + 6), "add #>$100,b", "move b1,y:>$%x" % (MREP + 6))   # a whole scan done
        L("sc_k")
        e("move a1,x0", "add #1,a", "move a1,x:(r1+%d)" % M_SCI)
        e("move x0,a", "asl a", "add x0,a", "add #>$%x,a" % (MREP + 64), "move a1,r4")
        e("clr b", "move x0,a", "cmp #>%d,a" % M_XN); jc("ge", "sc_y")
        e("asl #6,a,a", "move a1,r0", "clr a")
        do_i(64, "sc_xl"); e("move x:(r0)+,x0", "add x0,b"); L("sc_xl"); e("or x0,a")
        jmp("sc_st")
        L("sc_y"); e("sub #>%d,a" % M_XN, "asl #6,a,a", "move a1,r0", "clr a")
        do_i(64, "sc_yl"); e("move y:(r0)+,x0", "add x0,b"); L("sc_yl"); e("or x0,a")
        L("sc_st")
        e("move b1,x1", "move #>$100,y1", "clr b", "tst a", "tne y1,b", "move b1,y:(r4+2)")
        e("move x1,a", "asl #8,a,a", "add x1,a", "and #>$ffff00,a", "move a1,a", "move y:>$%x,b" % (MREP + 6), "tst b"); jc("ne", "sc_cmp")   # the sum + sum << 8
        e("move a1,y:(r4)"); jmp("c1_out0")
        L("sc_cmp"); e("move y:(r4),x0", "cmp x0,a"); jc("eq", "c1_out0")
        e("move y:(r4+1),a", "add #>$100,a", "move a1,y:(r4+1)"); jmp("c1_out0")
        for sp in ("p", "x", "y"):
            L("md_t" + sp)
            for ad in M_TESTS[sp]: a.emit([ad])
    if NOVADUMP:                                                                               # (S516D) a pass with nothing to do: 256 words of a copy
        L("c1_nd")
        e("move #>$%x,r1" % ND_CMD); a.emit(D.NOP)
        e("move x:(r1),a", "move x:(r1+%d),x0" % (ND_SEEN - ND_CMD), "cmp x0,a"); jc("eq", "c1_out0")     # nothing new
        e("move x:(r1+%d),b" % (ND_OFS - ND_CMD), "move x:(r1+2),x0", "cmp x0,b"); jc("lt", "nd_go")
        e("move a1,x:(r1+%d)" % (ND_SEEN - ND_CMD), "clr b", "move b,x:(r1+%d)" % (ND_OFS - ND_CMD)); jmp("c1_out0")   # done: seen = seq
        L("nd_go")
        e("move x:(r1+1),a", "add b,a", "move a1,r0", "move #>$%x,a" % ND_Y, "add b,a", "move a1,r4", "add #>256,b", "move b1,x:(r1+%d)" % (ND_OFS - ND_CMD)); a.emit(D.NOP)
        do_i(256, "nd_l"); e("move x:(r0)+,x0"); L("nd_l"); e("move x0,y:(r4)+")
        jmp("c1_out0")
    if WTCOPY and FMC1:                                                                        # (WTCOPY) a pass with nothing to do: 256 words of the table's copy
        L("c1_wc")
        e("move #>$%x,r1" % WC_CMD); a.emit(D.NOP)
        e("move x:(r1),a", "move x:(r1+%d),x0" % (WC_SEEN - WC_CMD), "cmp x0,a"); jc("eq", "c1_out0")     # nothing new
        e("move x:(r1+1),b"); a.emit(lambda t: T("jset #23,b1,$%x" % t), "ws_go")                             # a sample's cycle
        e("move x:(r1+%d),b" % (WC_OFS - WC_CMD), "move x:(r1+3),x0", "cmp x0,b"); jc("lt", "wc_go")
        e("move a1,x:(r1+%d)" % (WC_SEEN - WC_CMD), "clr b", "move b,x:(r1+%d)" % (WC_OFS - WC_CMD)); jmp("c1_out0")   # done: seen = seq
        L("wc_go")
        e("move x:(r1+1),a", "add b,a", "move a1,r0", "move x:(r1+2),a", "add b,a", "move a1,r4", "add #>256,b", "move b1,x:(r1+%d)" % (WC_OFS - WC_CMD)); a.emit(D.NOP)
        do_i(256, "wc_l"); e("move x:(r0)+,x0"); L("wc_l"); e("move x0,y:(r4)+")
        jmp("c1_out0")
        # ---- a sample's cycle: one step a pass (SJ + 0 = the phase)
        def sj(k): return "x:>$%x" % (SJ + k)
        def lin(*rs): e(*["move #>$ffffff,%s" % r for r in rs])
        def dst_lv(): e("move %s,a" % sj(8), "asl #10,a,a", "move %s,x0" % sj(6), "add x0,a", "move a1,r0"); a.emit(D.NOP)   # r0 = level L
        L("ws_go")
        e("move %s,a" % sj(0), "tst a"); jc("ne", "ws_1")
        e("and #>63,b", "asl #2,b,b", "add #>$%x,b" % SHT, "move b1,r0"); a.emit(D.NOP)                           # 0: start
        e("move x:(r0)+,x0", "move x:(r0),a", "move x0,%s" % sj(1), "move a1,%s" % sj(2), "move x:(r1+2),x1", "move x1,%s" % sj(6))
        e("move #>$%x,r4" % SCR, "move #>$733333,x0", "clr b", "move b,y0"); a.emit(D.NOP)                          # the sine: c = 0.9, s = 0
        do_i(1024, "ws_sn")
        e("move y0,y:(r4)+", "move #>$7fff62,y1", "mpy x0,y1,a", "mpy y1,y0,b", "move #>$00c90f,y1", "mac -y1,y0,a", "mac x0,y1,b", "move a,x0")
        L("ws_sn"); e("move b,y0")
        e("move %s,a" % sj(2), "cmp #>2048,a"); jc("ge", "ws_lg")
        e("move #>1024,x0", "cmp x0,a", "tgt x0,a", "move a1,%s" % sj(5), "move %s,x0" % sj(1), "move x0,%s" % sj(3))   # short: itself, one cycle
        e("clr a", "move a1,%s" % sj(4), "move a1,%s" % sj(9), "move #>3,a"); jmp("ws_ph")
        L("ws_lg"); e("asr #2,a,a", "move %s,x0" % sj(1), "add x0,a", "move a1,%s" % sj(3), "move #>16,a", "move a1,%s" % sj(4), "move #>1,a")
        L("ws_ph"); e("move a1,%s" % sj(0)); jmp("c1_out0")
        L("ws_1"); e("cmp #>1,a"); jc("ne", "ws_2")                                                                  # 1: the AMDF of a lag
        e("move %s,r0" % sj(3), "move %s,a" % sj(4), "move %s,x0" % sj(3), "add x0,a", "move a1,r4", "clr b"); a.emit(D.NOP)
        do_i(512, "ws_am"); e("move y:(r0)+,a", "move y:(r4)+,x0", "sub x0,a", "abs a", "asr #3,a,a"); L("ws_am"); e("add a,b")
        e("asr #8,b,b", "move %s,a" % sj(4), "add #>$%x,a" % (SCR + 0x800), "move a1,r4"); a.emit(D.NOP); e("move b,y:(r4)")
        e("move %s,a" % sj(4), "add #>1,a", "move a1,%s" % sj(4), "cmp #>1024,a"); jc("lt", "c1_out0")
        e("move #>2,a", "move a1,%s" % sj(0)); jmp("c1_out0")
        L("ws_2"); e("cmp #>2,a"); jc("ne", "ws_3")                                                                  # 2: P
        e("move #>$%x,r0" % (SCR + 0x800 + 16), "move #>$7fffff,b"); a.emit(D.NOP)
        do_i(1008, "ws_mn"); e("move y:(r0)+,x0", "cmp x0,b"); L("ws_mn"); e("tgt x0,b")
        e("move b,x0", "asr #3,b,b", "add x0,b", "add #>$100,b", "move #>$%x,r0" % (SCR + 0x800 + 16), "move #>16,a"); a.emit(D.NOP)
        L("ws_fs"); e("move y:(r0)+,x0", "cmp x0,b"); jc("ge", "ws_fd"); e("add #>1,a", "cmp #>1023,a"); jc("lt", "ws_fs"); jmp("ws_pd")
        L("ws_fd"); e("move x0,b")
        L("ws_fl"); e("cmp #>1023,a"); jc("ge", "ws_pd"); e("move y:(r0)+,x0", "cmp x0,b"); jc("le", "ws_pd"); e("move x0,b", "add #>1,a"); jmp("ws_fl")
        L("ws_pd"); e("move a1,%s" % sj(5), "move #>3,a", "move a1,%s" % sj(0))
        e("clr a", "move a1,%s" % sj(4), "move a1,%s" % sj(9)); jmp("c1_out0")
        L("ws_3"); e("cmp #>3,a"); jc("ne", "ws_4")                                                                  # 3: 256 points of the resampling a pass
        e("move %s,a" % sj(5), "asl #3,a,a", "move a1,%s" % sj(7))                                                   # the step: P / 1024 in 1/8192
        e("move %s,a" % sj(6), "move %s,x0" % sj(4), "add x0,a", "move a1,r4", "move %s,b" % sj(9), "move %s,x1" % sj(3)); a.emit(D.NOP)
        do_i(256, "ws_rs")
        e("move b1,a", "lsr #13,a", "add x1,a", "move a1,r0", "move b1,a", "and #>$1fff,a", "asl #10,a,a", "move a1,y1"); a.emit(D.NOP)
        e("move y:(r0)+,x0", "move y:(r0),a", "sub x0,a", "move a,y0", "move x0,a", "mac y1,y0,a", "asr #3,a,a", "move a,y:(r4)+", "move %s,x0" % sj(7))
        L("ws_rs"); e("add x0,b")
        e("move b1,%s" % sj(9), "move %s,a" % sj(4), "add #>256,a", "move a1,%s" % sj(4), "cmp #>1024,a"); jc("lt", "c1_out0")
        e("move %s,r0" % sj(6), "clr a"); a.emit(D.NOP)                                                              # DC out, the peak at 0.225
        do_i(1024, "ws_dc"); e("move y:(r0)+,x0"); L("ws_dc"); e("add x0,a")
        e("asr #10,a,a", "move a,y1", "move %s,r0" % sj(6), "clr b"); a.emit(D.NOP)
        do_i(1024, "ws_pk"); e("move y:(r0),a", "sub y1,a", "move a,y:(r0)+", "abs a", "cmp a,b"); L("ws_pk"); e("tlt a,b")
        e("move b,x0", "move #>$1ccccd,a", "cmp x0,a"); jc("ge", "ws_n0")
        e("andi #$fe,ccr", "rep #24", "div x0,a", "move a0,y1", "move %s,r0" % sj(6)); a.emit(D.NOP)
        do_i(1024, "ws_nm"); e("move y:(r0),x0", "mpy x0,y1,a"); L("ws_nm"); e("move a,y:(r0)+")
        L("ws_n0"); e("move #>1,a", "move a1,%s" % sj(4), "move #>4,a", "move a1,%s" % sj(0)); jmp("c1_out0")
        L("ws_4"); e("cmp #>4,a"); jc("ne", "ws_5")                                                                  # 4: harmonic k's coefficients
        e("move #>$%x,r1" % SCR, "move #>$%x,r2" % (SCR + 256), "move #>$3ff,m1", "move #>$3ff,m2", "move %s,n1" % sj(4), "move %s,n2" % sj(4),
          "move %s,r0" % sj(6), "clr a", "clr b")
        do_i(1024, "ws_df"); e("move y:(r0)+,x0", "move y:(r2)+n2,y0", "mac y0,x0,a", "move y:(r1)+n1,y0"); L("ws_df"); e("mac y0,x0,b")
        lin("m1", "m2")
        e("asr #6,a,a", "asr #6,b,b", "move %s,n0" % sj(4), "move #>$%x,r0" % (SCR + 0x400)); a.emit(D.NOP)
        e("move a,y:(r0+n0)", "move #>$%x,r0" % (SCR + 0x500)); a.emit(D.NOP); e("move b,y:(r0+n0)")
        e("move %s,a" % sj(4), "add #>1,a", "move a1,%s" % sj(4), "cmp #>256,a"); jc("le", "c1_out0")
        e("move #>2,a", "move a1,%s" % sj(8), "move #>1,a", "move a1,%s" % sj(4), "move #>5,a", "move a1,%s" % sj(0)); jmp("c1_out0")
        L("ws_5"); e("cmp #>5,a"); jc("ne", "ws_6")                                                                  # 5: a harmonic into level L
        dst_lv()
        e("move %s,a" % sj(4), "cmp #>1,a"); jc("ne", "ws_nz")
        e("clr a"); do_i(1024, "ws_z"); L("ws_z"); e("move a,y:(r0)+")
        dst_lv()
        L("ws_nz")
        e("move %s,n1" % sj(4), "move #>$%x,r1" % (SCR + 0x400)); a.emit(D.NOP); e("move y:(r1+n1),x1", "move #>$%x,r1" % (SCR + 0x500)); a.emit(D.NOP)
        e("move y:(r1+n1),y1", "move #>$%x,r1" % SCR, "move #>$%x,r2" % (SCR + 256), "move #>$3ff,m1", "move #>$3ff,m2", "move %s,n2" % sj(4))
        do_i(1024, "ws_sy"); e("move y:(r0),a", "move y:(r2)+n2,x0", "mac x1,x0,a", "move y:(r1)+n1,x0", "mac x0,y1,a"); L("ws_sy"); e("move a,y:(r0)+")
        lin("m1", "m2")
        a.emit(lambda t: T("move #>$%x,r0" % t), "ws_ht"); e("move %s,n0" % sj(8)); a.emit(D.NOP); e("move p:(r0+n0),x0")
        e("move %s,a" % sj(4), "add #>1,a", "move a1,%s" % sj(4), "cmp x0,a"); jc("le", "c1_out0")
        e("move #>1,a", "move a1,%s" % sj(4), "move %s,a" % sj(8), "add #>1,a", "move a1,%s" % sj(8), "cmp #>17,a"); jc("le", "c1_out0")
        e("move #>6,a", "move a1,%s" % sj(0)); jmp("c1_out0")
        L("ws_6")                                                                                                    # 6: levels 0 / 1 = level 2; done
        for lv in (0, 1):
            e("move %s,a" % sj(6), "add #>2048,a", "move a1,r0", "move %s,a" % sj(6), "add #>%d,a" % (1024 * lv), "move a1,r4"); a.emit(D.NOP)
            do_i(1024, "ws_c%d" % lv); e("move y:(r0)+,x0"); L("ws_c%d" % lv); e("move x0,y:(r4)+")
        e("clr a", "move a1,%s" % sj(0), "move x:(r1),a", "move a1,x:(r1+%d)" % (WC_SEEN - WC_CMD)); jmp("c1_out0")
        L("ws_ht"); [a.emit([h_]) for h_ in WT_H]
    # ================================================================ glitch (r1 = GOUT[c & 1]); r7 = GS, r6 = GIN
    L("glitch")
    if FMLOAD or MEMDIAG or NOVADUMP:                                                                      # (S513D / S514D) no Glitch (nor the mechanical gesture): core 1's room
        e("clr a", "move #>$%x,r7" % GS); a.emit(D.NOP); e("move a,%s" % X("r7", S_ON)); a.emit(D.RTS)
    else:
        e("move #>$%x,r7" % GS, "move #>$%x,r6" % GIN); a.emit(D.NOP)
        e("move x:(r6),a", "move #>$%x,x0" % GMAGIC, "cmp x0,a"); jc("eq", "gl_on")
        e("clr a", "move a,%s" % X("r7", S_ON)); a.emit(D.RTS)
        L("gl_on")
        e("move %s,a" % X("r7", S_ON), "tst a"); jc("ne", "gl_run")
        # ---- the pad was just pressed: the head = now - the delay, a fade-in, forward
        e("move #>1,x0", "move x0,%s" % X("r7", S_ON), "move x0,%s" % X("r7", S_DIR))
        jsr("gl_delay")
        e("move a1,%s" % X("r7", S_STH), "move a1,%s" % X("r7", S_HH), "clr b", "move b,%s" % X("r7", S_HL), "move b,%s" % X("r7", S_MUTE)); jsr("gl_newseg")
        e("clr b", "move b,%s" % X("r7", S_E), "move #>$%x,x0" % (0x7FFFFF // FADE), "move x0,%s" % X("r7", S_DE))      # the start always fades in
        L("gl_run")
        # ---- the speed from K1: >= 120 = 1; 64..119 = (K1 - 64) / 56; < 64 = -(64 - K1) / 64; times the direction
        if OVERLOAD:                                                                              # the brake: K1 - (K4 - OV_BRAKE) for a forward head, not below 64
            e("move %s,a" % X("r6", 1), "move %s,b" % X("r6", 4), "sub #>%d,b" % OV_BRAKE); jc("lt", "gl_nb")
            e("cmp #>64,a"); jc("lt", "gl_nb")
            e("sub b,a", "move #>64,x0", "cmp x0,a", "tlt x0,a")
            L("gl_nb"); e("cmp #>120,a")
        else:
            e("move %s,a" % X("r6", 1), "cmp #>120,a")
        jc("lt", "gl_s1")
        e("move #>1,a"); jmp("gl_s3")
        L("gl_s1")
        e("cmp #>64,a"); jc("lt", "gl_s2")
        e("sub #>64,a", "move a1,x0", "move #>$024925,y0", "mpy y0,x0,a", "asr a", "move a0,x0", "clr a", "move x0,a0", "asl a"); jmp("gl_s3")
        L("gl_s2")
        e("move a1,x0", "move #>64,a", "sub x0,a", "asl #17,a,a", "move a1,x0", "clr a", "move x0,a0", "asl a", "neg a")
        L("gl_s3")
        e("move %s,b" % X("r7", S_DIR), "tst b"); jc("gt", "gl_s4"); e("neg a")
        L("gl_s4"); e("move a1,%s" % X("r7", S_SH), "move a0,%s" % X("r7", S_SL))
        # ---- 32 frames in runs of the fade / body phases
        e("move r1,r0", "move #>%d,n4" % rn, "move #>32,x0", "move x0,%s" % X("r7", S_RC))
        e("move %s,a" % X("r7", S_HH), "move %s,a0" % X("r7", S_HL))
        L("gl_l")
        e("move %s,b" % X("r7", S_RC), "move %s,x0" % X("r7", S_REM), "cmp x0,b", "tgt x0,b", "tst b"); jc("eq", "gl_ph")
        e("move b1,x1")
        e("move %s,b" % X("r7", S_RC), "sub x1,b", "move b1,%s" % X("r7", S_RC))
        e("move %s,b" % X("r7", S_REM), "sub x1,b", "move b1,%s" % X("r7", S_REM))
        do_r("x1", "gl_e")
        e("move %s,b" % X("r7", S_E), "move %s,x0" % X("r7", S_DE), "add x0,b", "move b1,%s" % X("r7", S_E), "move b1,y1")
        e("move a1,r4"); a.emit(D.NOP); a.emit(D.NOP)
        e("move y:(r4),x0", "mpy x0,y1,b", "move b,x:(r0)+", "move y:(r4+n4),x0", "mpy x0,y1,b")
        e("move %s,x1" % X("r7", S_SH), "move %s,x0" % X("r7", S_SL), "add x,a", "and #>$%x,a" % (rn - 1), "or #>$%x,a" % rl)
        L("gl_e"); e("move b,x:(r0)+")
        e("move %s,b" % X("r7", S_REM), "tst b"); jc("ne", "gl_c")
        L("gl_ph")                                                                                # the next phase: 0 fade-in -> 1 body -> 2 fade-out -> a new segment
        e("move %s,b" % X("r7", S_PHS), "add #>1,b", "move b1,%s" % X("r7", S_PHS))
        e("cmp #>1,b"); jc("ne", "gl_p2")
        e("move %s,x0" % X("r7", S_BODY), "move x0,%s" % X("r7", S_REM), "clr b", "move b,%s" % X("r7", S_DE)); jmp("gl_c")
        L("gl_p2")
        e("cmp #>2,b"); jc("ne", "gl_p3")
        e("move #>%d,x0" % FADE, "move x0,%s" % X("r7", S_REM), "clr b", "move %s,a" % X("r6", 2), "cmp #>127,a"); jc("eq", "gl_f0")      # K2 = 127 (continuous): no fade
        e("move %s,b" % X("r7", S_E), "asr #6,b,b", "neg b")
        L("gl_f0"); e("move b1,%s" % X("r7", S_DE)); jmp("gl_c")
        L("gl_p3")
        e("move a1,%s" % X("r7", S_HH), "move a0,%s" % X("r7", S_HL))
        jsr("gl_end")
        e("move %s,a" % X("r7", S_HH), "move %s,a0" % X("r7", S_HL))
        L("gl_c")
        e("move %s,b" % X("r7", S_RC), "tst b"); jc("ne", "gl_l")
        e("move a1,%s" % X("r7", S_HH), "move a0,%s" % X("r7", S_HL))
        if OVERLOAD:                                                                              # a late block (p = (K4 - 64) / 128): 32 frames back, the next one 32 ahead
            e("move %s,b" % X("r6", 4), "sub #>%d,b" % OV_CHAOS); jc("lt", "gl_ov")
            jsr("rnd")
            e("clr a", "move x0,a1", "and #>$ff0000,a", "asr #16,a,a", "asl b", "cmp b,a"); jc("ge", "gl_ov")
            e("move %s,a" % X("r7", S_OV), "eor #>64,a", "move a1,%s" % X("r7", S_OV), "sub #>32,a", "neg a")      # S_OV 0 -> 64: -32, 64 -> 0: +32
            e("move %s,x0" % X("r7", S_HH), "add x0,a", "and #>$%x,a" % (rn - 1), "or #>$%x,a" % rl, "move a1,%s" % X("r7", S_HH))
            L("gl_ov")
        a.emit(D.RTS)
        # ---- gl_delay: a1 = the ring address of now - (K3 x 1024 + 64) frames
        L("gl_delay")
        e("move %s,a" % X("r6", 3), "asl #10,a,a", "add #>64,a", "move a1,x0", "move x:>$%x,a" % WR, "sub x0,a", "and #>$%x,a" % (rn - 1), "or #>$%x,a" % rl)
        a.emit(D.RTS)
        # ---- gl_end: the end of a segment.  K2 < 127: back to the segment start (a repeat); else on from here.  Chaos K4: a jump back (p = K4 / 256),
        #      a mute (K4 / 384), a reversal (K4 / 384)
        L("gl_end")
        e("move %s,a" % X("r6", 2), "cmp #>127,a"); jc("lt", "ge_rp")
        e("move %s,x0" % X("r7", S_HH), "move x0,%s" % X("r7", S_STH)); jmp("ge_ch")
        L("ge_rp")
        e("move %s,x0" % X("r7", S_STH), "move x0,%s" % X("r7", S_HH), "clr b", "move b,%s" % X("r7", S_HL))
        L("ge_ch")
        e("move %s,a" % X("r6", 4), "tst a"); jc("eq", "ge_nc")
        if OVERLOAD: e("cmp #>%d,a" % OV_CHAOS); jc("ge", "ge_nc")                                   # K4 >= 64: the load, no chaos
        jsr("rnd"); e("clr a", "move x0,a1", "and #>$ff0000,a", "asr #16,a,a", "move %s,x0" % X("r6", 4), "cmp x0,a"); jc("ge", "ge_nj")
        jsr("gl_delay"); e("move a1,y1"); jsr("rnd")                                              # a jump: a random point between now - delay and now - 64
        e("clr a", "move x0,a1", "and #>$7fffff,a", "move a1,x0", "move %s,a" % X("r6", 3), "asl #10,a,a", "move a1,y0", "mpy y0,x0,a")   # rnd (0..1) x K3 x 1024
        e("move a1,x0", "move y1,a", "add x0,a", "and #>$%x,a" % (rn - 1), "or #>$%x,a" % rl)
        e("move a1,%s" % X("r7", S_STH), "move a1,%s" % X("r7", S_HH), "clr b", "move b,%s" % X("r7", S_HL))
        L("ge_nj")
        e("clr b", "move b,%s" % X("r7", S_MUTE))
        jsr("rnd"); e("clr a", "move x0,a1", "and #>$ff0000,a", "asr #16,a,a", "move a1,b", "asl a", "add b,a", "asr a", "move %s,x0" % X("r6", 4), "cmp x0,a"); jc("ge", "ge_nm")
        e("move #>1,x0", "move x0,%s" % X("r7", S_MUTE))
        L("ge_nm")
        jsr("rnd"); e("clr a", "move x0,a1", "and #>$ff0000,a", "asr #16,a,a", "move a1,b", "asl a", "add b,a", "asr a", "move %s,x0" % X("r6", 4), "cmp x0,a"); jc("ge", "ge_nc")
        e("move %s,a" % X("r7", S_DIR), "neg a", "move a1,%s" % X("r7", S_DIR))
        L("ge_nc")
        # fall into gl_newseg
        # ---- gl_newseg: phase 0 = a fade-in of FADE frames to 1 (to 0 when muted); the body = SIZE_T[K2] x 2 - 2 FADE (K2 = 127: 1 s)
        L("gl_newseg")
        e("clr b", "move b,%s" % X("r7", S_PHS), "move b,%s" % X("r7", S_E), "move #>%d,x0" % FADE, "move x0,%s" % X("r7", S_REM))
        e("move #>$%x,x0" % (0x7FFFFF // FADE), "move %s,b" % X("r7", S_MUTE), "tst b"); jc("eq", "gn_m"); e("move #>0,x0")
        L("gn_m"); e("move x0,%s" % X("r7", S_DE))
        e("move %s,a" % X("r6", 2), "cmp #>127,a"); jc("ne", "gn_f")                              # continuous and not muted: full level at once, no fade
        e("tst b"); jc("ne", "gn_f")
        e("move #>$7fffff,x0", "move x0,%s" % X("r7", S_E), "clr b", "move b,%s" % X("r7", S_DE))
        L("gn_f")
        e("move %s,a" % X("r6", 2), "and #>$7f,a"); tab("a", "SIZE_T"); e("move a1,r0"); a.emit(D.NOP)
        e("move p:(r0),a", "asl a", "sub #>%d,a" % (2 * FADE), "move a1,%s" % X("r7", S_BODY))
        a.emit(D.RTS)

    # ================================================================ tables (P)
    for name in ("SIZE_T", "PT", "GAIN_T"):
        L(name)
        for w in tabs[name]: a.emit([w & 0xFFFFFF])
    return a.assemble()


def patch_core1(img, **kw):
    """After building: core 1's block copied to the end of the image with core1_code, P:$12A -> jmp c1loop (as probe36_dsp.patch)."""
    BASE = 0x08010000
    tab = 0x08029700 + 8
    old = struct.unpack_from("<I", img, tab - BASE)[0]
    o = old - BASE
    n = int.from_bytes(img[o:o + 3], "big")
    assert n == P5.C1_STOCK_WORDS and int.from_bytes(img[o + 3:o + 6], "big") == 0
    prog = [int.from_bytes(img[o + 6 + 3 * i:o + 9 + 3 * i], "big") for i in range(n)]
    assert prog[P5.C1_HOOK] == 0x0C0000 | P5.C1_LOOP, hex(prog[P5.C1_HOOK])
    global FMC1
    fmc1, FMC1 = FMC1, False                                                    # (FMC1) the block without the FM slots here: the image keeps its layout
    w1, l1 = core1_code(n, **kw)
    FMC1 = fmc1
    assert n + len(w1) <= 0x800, hex(n + len(w1))
    prog[P5.C1_HOOK] = 0x0C0000 | l1["c1loop"]
    blk = (n + len(w1)).to_bytes(3, "big") + b"\0\0\0" + D.to_bytes(prog + w1)
    at = (len(img) + BASE + 3) & ~3
    img += b"\xFF" * (at - BASE - len(img)) + blk
    while len(img) % 4:
        img += b"\xFF"
    struct.pack_into("<I", img, tab - BASE, at)
    rep = dict(core1_block=hex(at), core1_words=n + len(w1), labels={k: hex(v) for k, v in l1.items()})
    if FMC1:                                                                    # (FMC1) dspz packs the block with the FM slots into the same place
        import dspz
        def override(raw, prog=list(prog)):
            w2, l2 = core1_code(n, **kw)
            assert n + len(w2) <= (0x1800 if FM8 else 0x800) and l2["c1loop"] == l1["c1loop"], hex(n + len(w2))     # (FM8: MS = 1, P 8 K)
            rep.update(core1_words=n + len(w2), labels={k: hex(v) for k, v in l2.items()}, fmc1_late=True)
            return (n + len(w2)).to_bytes(3, "big") + b"\0\0\0" + D.to_bytes(prog + w2)
        dspz.OVERRIDE[1] = override
    return rep


# ==================================================================== core 0
CPT_LIST = ((OSBX, SHA, 0xC0), (VBX, SHB, 0x60), (CAP_LEN, SHLEN, 1), (0x2E10, MIN, 64), (GARM, GIN, 5))   # + a quarter of the sample table per block


DIAGCNT, DIAG_Y = False, 0x3B0F                 # SC419D (stutdiag): core 0 also copies CNT to Y:$3B0F, inside the 16-bit range of the ARM's DSP read


def use_diagcnt():
    global DIAGCNT
    DIAGCNT = True


def core0_tail(a, e):
    """The end of the Master FX chain on core 0 (sampler_dsp.TAIL, before its registers come back; m4 is linear there): the copies of CPT_LIST,
    the Glitch replacing the master with GOUT[RDOFS] while the ARM holds the magic in GARM, CNT + 1, RDOFS for the next block.
    Uses r0, r1, r4, a, x0, x1 (r1 gets $2E10 back after)."""
    L = a.label
    a.emit(lambda t: T("move #>$%x,r1" % t), "gr_cpt"); a.emit(D.NOP)
    a.emit(lambda t: T("do #%d,$%x" % (len(CPT_LIST), t + 1)), "gr_co")
    e("move p:(r1)+,r0", "move p:(r1)+,r4", "move p:(r1)+,x1")
    a.emit(lambda t: T("do x1,$%x" % (t + 1)), "gr_ci")
    e("move x:(r0)+,x0")
    L("gr_ci"); e("move x0,x:(r4)+")
    L("gr_co"); a.emit(D.NOP)
    e("move x:>$%x,a" % CNT, "and #>3,a", "asl #6,a,a", "move a1,n0", "move a1,n4", "move #>$%x,r0" % SAMPLE_TAB, "move #>$%x,r4" % SHT); a.emit(D.NOP)   # 16 entries of the table
    e("move (r0)+n0", "move (r4)+n4")
    a.emit(lambda t: T("do #64,$%x" % (t + 1)), "gr_tc")
    e("move x:(r0)+,x0")
    L("gr_tc"); e("move x0,x:(r4)+")
    e("move x:>$%x,a" % GARM, "move #>$%x,x0" % GMAGIC, "cmp x0,a"); a.emit(J("ne"), "gr_ng")
    e("move x:>$%x,a" % RDOFS, "add #>$%x,a" % GOUT, "move a1,r0", "move #>$2e10,r4"); a.emit(D.NOP)
    a.emit(lambda t: T("do #64,$%x" % (t + 1)), "gr_gc")
    e("move x:(r0)+,x0")
    L("gr_gc"); e("move x0,x:(r4)+")
    L("gr_ng")
    e("move x:>$%x,a" % CNT, "add #>1,a", "move a1,x:>$%x" % CNT)
    if DIAGCNT: e("move a1,y:>$%x" % DIAG_Y)                                                   # (SC419D) the counter where the ARM can read it
    e("add #>1,a", "and #>1,a", "asl #6,a,a", "move a1,x:>$%x" % RDOFS)


STRIPG = False                                   # SC47.1 (see use_stripgain)
STRIP = (0x20C, 0x24C)                           # (STRIPG) the stock strips of MIDI 1 / 2: 32 pairs gL, gR (func_0013a3: Y:$2068 / $2088 x Y:$5B..$5E)
SG_SHIFT = 4                                     # (STRIPG) the sides = S x GCUR x gL (gR) x 2^SG_SHIFT (-S_COEF x level / gL at the old calibration = 15.98)


def use_stripgain():
    """SC47.1 (the user, 2026-10-26, on the device: the stereo sample «sigue mezclando los dos samples a los dos canales por igual», the granular's
    width «tampoco se aprecia gran diferencia»; S469D / S469D2 read on the device: the sides reach the mix, ~4.5 x weaker than the mid): S_COEF was
    measured 15 blocks after forcing the level, with the stock mixer's ramp at 0x16459 of its 0x63FBF (the ramp from 0 takes > 250 blocks in the
    emulation; on the device it is settled): 4.49 x too small.  core0_sides takes the strip's own gains instead of the level x S_COEF: the first pair
    of the block in X:$20C / $24C (what func_0013a3 multiplies the track's input by: level, pan law, mute, the sidechain's duck, ramped), x 16
    (asl), L += S x g x gL, R -= S x g x gR: the sides follow the mid in every mixer state, the pan included (+ 2 words)."""
    global STRIPG
    STRIPG = True


DIAG_RING = False                                # (S469D2) + 9 = MIDI 1's ring frame 0
DIAG_SIDES = None                                # (S469D) X address of 9 words: SOUT's address, g, SOUT[0], mix L / R before, CNT, mix L / R after, blocks


def core0_sides(a, e, pf_l, pf_r):
    """(STEREO) Before the master filter (sampler_dsp.PRE_HOOK, m4 linear): per voice t, g = GCUR x level (GCUR = unity with the VCA off), and for each
    frame L -= S x g x S_COEF, R += S x g x S_COEF, S = SOUT[RDOFS] + 32 t.  Two straight copies (no nested do: the stack).  Uses r0, r1, r4, a, b, x0,
    x1, y0, y1."""
    import vcf21_dsp as V
    for t in range(2):
        vb = V.VB0 + V.VBS * t
        e("move x:>$%x,b" % (vb + GCUR_OFF), "move x:>$%x,a" % (vb + VCAON_OFF), "tst a", "move #>$100000,x0", "teq x0,b", "move b1,x1")
        if STRIPG:                                                                # y1 / y0 = g x gL / gR x 16 (the sign of S_COEF in the loop)
            e("move x:>$%x,x0" % STRIP[t], "mpy x1,x0,a", "asl #%d,a,a" % SG_SHIFT, "move x:>$%x,x0" % (STRIP[t] + 1), "mpy x1,x0,b",
              "asl #%d,b,b" % SG_SHIFT, "move a,y1", "move b,y0")
        else:
            e("move x:>$%x,y1" % (MIXLP + 2 * t), "mpy y1,x1,a", "move a,x1", "move #>$%x,y1" % (round(S_COEF * (1 << 23)) & 0xFFFFFF), "mpy y1,x1,a", "move a,y1")
        e("move x:>$%x,a" % RDOFS, "add #>$%x,a" % (SOUT + 32 * t), "move a1,r4", "move #>$%x,r0" % pf_l, "move #>$%x,r1" % pf_r); a.emit(D.NOP)
        if DIAG_SIDES and t == 0:                                                 # (S469D) what the device sees: SOUT's address, g, SOUT[0], the mix before
            D0 = DIAG_SIDES
            e("move r4,x:>$%x" % D0, "move y1,x:>$%x" % (D0 + 1), "move x:(r4),x0", "move x0,x:>$%x" % (D0 + 2), "move x:>$%x,x0" % pf_l, "move x0,x:>$%x" % (D0 + 3),
              "move x:>$%x,x0" % pf_r, "move x0,x:>$%x" % (D0 + 4), "move x:>$%x,x0" % CNT, "move x0,x:>$%x" % (D0 + 5), "move x:>$%x,a" % (D0 + 8), "add #>1,a",
              "move a1,x:>$%x" % (D0 + 8))
            if DIAG_RING: e("move y:>$ffd,r4"); a.emit(D.NOP); e("move y:(r4),x0", "move x0,x:>$%x" % (D0 + 9))   # (S469D2) MIDI 1's ring frame 0 (the mid after the chain)
            e("move x:>$%x,a" % RDOFS)
            e("add #>$%x,a" % (SOUT + 32 * t), "move a1,r4"); a.emit(D.NOP)
        a.emit(lambda tt: T("do #32,$%x" % (tt + 1)), "gs_%d" % t)
        if STRIPG:
            e("move x:(r4)+,x0", "mpy x0,y1,a x:(r0),b", "add a,b", "move b,x:(r0)+", "mpy y0,x0,a x:(r1),b", "sub a,b")
        else:
            e("move x:(r4)+,x0", "mpy x0,y1,a")
            e("move x:(r0),b", "sub a,b", "move b,x:(r0)+", "move x:(r1),b", "add a,b")
        a.label("gs_%d" % t); e("move b,x:(r1)+")
        if DIAG_SIDES and t == 0: e("move x:>$%x,x0" % pf_l, "move x0,x:>$%x" % (DIAG_SIDES + 6), "move x:>$%x,x0" % pf_r, "move x0,x:>$%x" % (DIAG_SIDES + 7))


def core0_table(a):
    a.label("gr_cpt")
    for src, dst, n in CPT_LIST: a.emit([src, dst, n])
