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
    e("move x:>$%x,a" % CNT, "move x:>$%x,x0" % LASTC, "cmp x0,a"); jc("eq", "c1_out0")
    e("move x:>$%x,a" % MAGW, "move #>$%x,x0" % C1MAGIC, "cmp x0,a"); jc("eq", "c1_ok")
    for m in MREGS[1:]: e("move #>$ffffff,%s" % m)                                            # first time: the other M registers linear for good
    e("clr a", "move #>$%x,r0" % (GB + 0x18)); a.emit(D.NOP)                                     # first time: voice / glitch state, grains (not MIN)
    do_i(MIN - GB - 0x18, "c1_clr"); L("c1_clr"); e("move a,x:(r0)+")
    e("move #>$%x,r0" % GR0); a.emit(D.NOP)
    do_i(2 * maxg * GW, "c1_clg"); L("c1_clg"); e("move a,x:(r0)+")
    e("move a,x:>$%x" % WR, "move #>$%x,x0" % C1MAGIC, "move x0,x:>$%x" % MAGW, "move #>$1234,x0", "move x0,x:>$%x" % RNG)
    L("c1_ok")
    e("move x:>$%x,a" % CNT, "move a1,x:>$%x" % LASTC)
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

    # ================================================================ glitch (r1 = GOUT[c & 1]); r7 = GS, r6 = GIN
    L("glitch")
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
    w1, l1 = core1_code(n, **kw)
    assert n + len(w1) <= 0x800, hex(n + len(w1))
    prog[P5.C1_HOOK] = 0x0C0000 | l1["c1loop"]
    blk = (n + len(w1)).to_bytes(3, "big") + b"\0\0\0" + D.to_bytes(prog + w1)
    at = (len(img) + BASE + 3) & ~3
    img += b"\xFF" * (at - BASE - len(img)) + blk
    while len(img) % 4:
        img += b"\xFF"
    struct.pack_into("<I", img, tab - BASE, at)
    return dict(core1_block=hex(at), core1_words=n + len(w1), labels={k: hex(v) for k, v in l1.items()})


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


def core0_sides(a, e, pf_l, pf_r):
    """(STEREO) Before the master filter (sampler_dsp.PRE_HOOK, m4 linear): per voice t, g = GCUR x level (GCUR = unity with the VCA off), and for each
    frame L -= S x g x S_COEF, R += S x g x S_COEF, S = SOUT[RDOFS] + 32 t.  Two straight copies (no nested do: the stack).  Uses r0, r1, r4, a, b, x0,
    x1, y0, y1."""
    import vcf21_dsp as V
    for t in range(2):
        vb = V.VB0 + V.VBS * t
        e("move x:>$%x,b" % (vb + GCUR_OFF), "move x:>$%x,a" % (vb + VCAON_OFF), "tst a", "move #>$100000,x0", "teq x0,b", "move b1,x1")
        e("move x:>$%x,y1" % (MIXLP + 2 * t), "mpy y1,x1,a", "move a,x1", "move #>$%x,y1" % (round(S_COEF * (1 << 23)) & 0xFFFFFF), "mpy y1,x1,a", "move a,y1")
        e("move x:>$%x,a" % RDOFS, "add #>$%x,a" % (SOUT + 32 * t), "move a1,r4", "move #>$%x,r0" % pf_l, "move #>$%x,r1" % pf_r); a.emit(D.NOP)
        a.emit(lambda tt: T("do #32,$%x" % (tt + 1)), "gs_%d" % t)
        e("move x:(r4)+,x0", "mpy x0,y1,a")
        e("move x:(r0),b", "sub a,b", "move b,x:(r0)+", "move x:(r1),b", "add a,b")
        a.label("gs_%d" % t); e("move b,x:(r1)+")


def core0_table(a):
    a.label("gr_cpt")
    for src, dst, n in CPT_LIST: a.emit([src, dst, n])
