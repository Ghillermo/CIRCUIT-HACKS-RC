"""SC33: the captured sample of Master FX, DSP side (core 0).

Hook: the end of the Master FX chain.  masterfx_dsp's `fx_out` (`move #>$2e10,r1` + `rts`, reached by every path of fx_hook, which P:$274 calls) becomes
`jmp smp_post` + `nop`; smp_post ends with the same `move #>$2e10,r1` + `rts`, so the stack depth is the Master FX chain's own.  Per block (x:$3a stereo frames
at X:$2E10, after the master filter and every Master FX effect):
  1. record: while STATE bit 0 (the ARM: pad 32 held), (L + R) / 2 of each frame goes to Y:BASE + WP (the external memory: 16 bits per word, SC32D.1);
     a new recording starts at 0 and stops the playback; it ends at MAXLEN (3.46 s) or when the pad is released; LEN = the recorded length.
     The capture is the output WITH the effects (the user, 2026-10-08) and BEFORE the sample is mixed in (it never records itself).
  2. command CMD (the ARM writes it, the DSP clears it): 1 = start, 2 = start in loop (Shift + pad 7, whatever the mode), 3 = stop.
  3. gate: in mode 1 (gate) a normal start stops when STATE bit 1 (pad 7 held) drops.
  4. play: position a1:a0 = absolute address : fraction (48 bit), increment INC (INCI : INCF, the pitch), from S to E with S / E = BASE + LEN * SF / EF
     (fractions from the knobs, re-read every block); E < S = reverse; at E: loop (mode 2 or forced) -> S, else the position parks on ZERO (a Y word = 0)
     and the playback ends.  The sample is added to both channels at unity.  No jump inside a `do` loop (conditional transfers only).
State X:SMB..SMB+15 (free in the dsp_free_scan, nothing of ours there), cleared once (magic at X:SMB + 15).  M4 is set linear for the capture pointer and
restored (the hook of P:$23C had M0 = $FFFF on the device: the M registers are not linear everywhere).
"""
from __future__ import annotations
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp56 as D  # noqa: E402
import masterfx_dsp as G  # noqa: E402

T, J = G.T, G.J
JCLR, JSET = G.JCLR, G.JSET
BASE, MAXLEN = 0x600000, 0x28800                     # Y: outside the stock zone map (it ends at $5BF000; SC32D2: writable, nothing changes there)
SMB = 0x3D00
STATE, CMD, INCI, INCF, SF, EF, MODE = (SMB + i for i in range(7))      # written by the ARM
PREV, WP, LEN, PLAY, PI, PF, SS, EE, LF, SAVM4, SAVR6 = (SMB + 7 + i for i in range(11))   # internal (PLAY: 0 stopped, 1 playing, 2 forced loop)
REPN, REPK, CPSRC, CPDST, CPLEN, SAVM5 = (SMB + 18 + i for i in range(6))           # SC34 (V34): drum replacement
SAVR2, SAVM2 = SMB + 0x1C, SMB + 0x1D                # V34: r2 = the base of the state, M2 linear; saved before the first-call clearing, which stops at SMB + 0x18
MAGIC_AT, MAGIC = SMB + 0x1F, 0x5A3301
V34 = False                                          # SC34: CMD 4 = the sample of index REPN (X:$1D8D + 4 N: start, length) := a copy of the capture in slot REPK
SLOT0, SLOTN, CHUNK = 0x640000, 8, 1024              #   (8 slots of MAXLEN from $640000, round robin; the copy runs CHUNK words per block)
HIGH = False                                         # SC34.1: SC35D2 found the pack samples loaded from Y:$580000 (limit $E80000), so BASE / SLOT0 sit in the
HIGH_BASE = 0xE80000                                 #   sample memory; SC35D3: $E80000-$FFFFFF is real memory (no mirror) that nothing writes.  HIGH puts the capture
HIGH_SLOT0 = HIGH_BASE + MAXLEN                      #   at $E80000 and the 8 slots right after it (they end at $FEC800)
CLIP = False                                         # SC37 (packio.use_cross): the first call also clears X:CLIPW (the sample "copied" for a swap between packs)
CLIPW, IMPW = SMB + 0x25, SMB + 0x26                 #   and X:IMPW (where the next sample imported from another pack goes); both free (dsp_free_scan)
CLIP2 = False                                        # SC37.1 (packio.use_cross2): also X:PCLIPW (the synth patch "copied" for a swap between packs)
PCLIPW = SMB + 0x27
HOLD = False                                         # SC34.1 (the user, 2026-10-08): a loop (mode 2 or forced) plays only while the pad is held: the gate stops every
                                                     #   playback but a plain one-shot; S = E (start on end, nothing to play) no longer stops a held / looping
                                                     #   playback: it parks at S (silent) and goes on when S != E again (a one-shot still stops)
PRE = False                                          # SC39.2 (the user, 2026-10-12: «sample antes de efectos (efectos aplican a captura, no se graban)»): the whole
                                                     #   routine runs at the start of the Master FX chain instead of its end: fx_hook's first instruction
                                                     #   (`move x:>FX_ON,x0`, 2 words) becomes `jmp smp_post`, and smp_post ends with that instruction and
                                                     #   `jmp fx_hook + 2` (fx_out keeps its own `move #>$2e10,r1` + `rts`).  The sample that plays goes through
                                                     #   the effects; the capture records the master before them (and still never itself); the tail (the
                                                     #   granular copies, the Glitch) also runs before the effects, so the effects process the Glitch's output
FILT = False                                         # RC2.01 (see use_prefilter)
PF_L, PF_R, PF_AT = 0x2C02, 0x2C24, 0xD53             # (FILT) the master mix before the master filter (P:$D3E: L / R, x:$3a words each, >> 1); the
                                                     #   two nops before the filter's jsr (P:$D55 jsr func_0013ad)
SAVF4, SAVF5, SAVF6 = SMB + 0x18, SMB + 0x19, SMB + 0x1A   # (FILT) the caller's r4 / r5 / r6 (free words, after the first call's clearing of 0x18 words);
                                                     #   r0 / r1 come back as the mix loop leaves them: X:$2C02 / $2C24 + x:$3a


def use_prefilter():
    """RC2.01 (the user, 2026-10-17: «pon el master sampler detras del filtro» · «Todo antes del filtro»): the capture and the playback of the
    sample run before the master filter, so the filter acts on the sample that plays (it went in after it: Master FX hooks P:$274, after the
    filter and the << 2), and the capture records the mix before the filter (still never itself).  smp_post is called by a jsr in place of the
    two nops of P:$D53 (after the mix loop of P:$D3E, before jsr func_0013ad: the same depth as the filter's own call); it works on the two
    mono arrays X:$2C02 (L) / X:$2C24 (R) of the final mix: the filter's last stage (P:$1451) mixes them with its low / high pass, multiplies
    by the master gain y:$7FF and shifts << 2 into X:$2E10, and P:$269 shifts << 2 again, so Master FX gets 16 x the mix: the capture =
    (L + R) / 2 x 16 and the playback adds the sample / 16 to L and R, the levels of before with the filter in the middle and the gain at the
    top (the capture no longer holds the gain y:$7FF; the sample that plays goes through it); r4, r5, r6 come back (saved) and
    r0 / r1 as the mix loop leaves them.  The
    tail (the granular copies, the Glitch) stays at the start of Master FX: fx_hook's first instruction -> jmp smp_tail (m4 linear, r2 = the
    state as before), which ends with that instruction and jmp fx_hook + 2."""
    global FILT
    assert PRE and V34                                                  # (V34: the first call clears only 0x18 words, so SAVF4..6 survive it)
    FILT = True


SAMPLE_TAB = 0x1D8D
TAIL = None                                          # SC36: a callable (a, e) emitting code at the end of smp_post, before M4 / M5 / R2 come back
TAIL_TABLE = None                                    #   and (a) emitting its data after the code (granular_dsp.core0_tail / core0_table)
ZERO = 0x3BFE                                        # Y: a word kept at 0
NSTATE = 0x20
FRAMES = 0x3A                                        # X:$3A = frames per block (masterfx_dsp uses `do x:$3a`)


DDDD = {"x0": 4, "x1": 5, "y0": 6, "y1": 7, "a0": 8, "b0": 9, "a1": 0xC, "b1": 0xD, "a": 0xE, "b": 0xF}
_ABS = re.compile(r"^move (?:x:>\$([0-9a-f]+),(\w+)|(\w+),x:>\$([0-9a-f]+))$")


def short_x(line, rn=2):
    """`move x:>$SMB+d,D` / `move S,x:>$SMB+d` -> the one-word form `move x:(rn+d),D` (0000 0010 dddd ddrr r1dw DDDD with d bit 0 in bit 6, bits 1-6 in bits
    11-16; deduced from the stock words 0x020BDE = move x:(r3+3),a, 0x021B9E = (r3+6),a, 0x0213D8 = (r3+5),a0), or None."""
    m = _ABS.match(line)
    if not m: return None
    if m.group(1): addr, reg, w = int(m.group(1), 16), m.group(2), 1
    else: addr, reg, w = int(m.group(4), 16), m.group(3), 0
    d = addr - SMB
    if not (0 <= d < 0x20) or reg not in DDDD: return None
    return [0x020080 | rn << 8 | (d & 1) << 6 | (d >> 1) << 11 | w << 4 | DDDD[reg]]


def code(base, base_y=None, maxlen=MAXLEN, zero=ZERO, v34=None, slot0=None, stab=SAMPLE_TAB, hold=None, pre_ret=None):
    """base_y / maxlen / zero are parameters for the emulation test (the interpreter has 512 K words)."""
    if base_y is None: base_y = HIGH_BASE if HIGH else BASE
    if slot0 is None: slot0 = HIGH_SLOT0 if HIGH else SLOT0
    v34 = V34 if v34 is None else v34
    hold = HOLD if hold is None else hold
    a = D.Asm(base)
    L = a.label
    def e(*lines):
        for l in lines:
            w = short_x(l) if v34 else None
            a.emit(w if w else T(l))
    L("smp_post")
    if v34:                                                                                  # r2 = the base of the state (saved / restored)
        a.emit(T("move r2,x:>$%x" % SAVR2)); a.emit(T("move m2,x:>$%x" % SAVM2)); a.emit(T("move #>$%x,r2" % SMB)); a.emit(T("move #>$ffffff,m2"))
    if FILT: e("move r4,x:>$%x" % SAVF4, "move r5,x:>$%x" % SAVF5, "move r6,x:>$%x" % SAVF6)   # (before the first call's clearing, which keeps them)
    e("move x:>$%x,a" % MAGIC_AT, "move #>$%x,x0" % MAGIC, "cmp x0,a"); a.emit(J("eq"), "sm_ok")
    e("clr a", "move #>$%x,r0" % SMB); a.emit(D.NOP)
    e("rep #%d" % (0x18 if v34 else NSTATE), "move a,x:(r0)+")
    if CLIP: e("move a,x:>$%x" % CLIPW, "move a,x:>$%x" % IMPW)
    if CLIP2: e("move a,x:>$%x" % PCLIPW)
    e("move a,y:>$%x" % zero, "move x0,x:>$%x" % MAGIC_AT)
    L("sm_ok")
    e("move m4,x:>$%x" % SAVM4, "move #>$ffffff,m4")
    if v34: e("move m5,x:>$%x" % SAVM5, "move #>$ffffff,m5")
    # ---- 1. record
    e("move x:>$%x,x1" % STATE, "move x:>$%x,y1" % PREV, "move x1,x:>$%x" % PREV)
    a.emit(JCLR(0, "x1"), "sm_nr")
    a.emit(JSET(0, "y1"), "sm_rc")
    e("clr a", "move a,x:>$%x" % WP, "move a,x:>$%x" % LEN, "move a,x:>$%x" % PLAY)             # a new recording
    L("sm_rc")
    e("move x:>$%x,a" % WP, "move #>$%x,x0" % base_y, "add x0,a", "move a1,r4")
    e("move x:>$%x,a" % WP, "move x:>$%x,x0" % FRAMES, "add x0,a", "move #>$%x,x0" % maxlen, "cmp x0,a"); a.emit(J("gt"), "sm_nr")   # full
    e("move a1,x:>$%x" % WP, "move a1,x:>$%x" % LEN)
    if FILT:                                                                                 # before the filter: (L + R) / 2 x 16
        e("move #>$%x,r0" % PF_L, "move #>$%x,r1" % PF_R); a.emit(D.NOP)
        a.emit(D.do_x, FRAMES, "sm_re")
        e("move x:(r0)+,a", "move x:(r1)+,x0", "add x0,a", "asl #3,a,a")                    # (L + R) / 2 x 16
    else:
        e("move #>$%x,r0" % G.BUF); a.emit(D.NOP)
        a.emit(D.do_x, FRAMES, "sm_re")
        e("move x:(r0)+,a", "move x:(r0)+,x0", "add x0,a", "asr a")
    L("sm_re"); e("move a,y:(r4)+")
    L("sm_nr")
    # ---- 2. command
    e("move x:>$%x,a" % CMD, "tst a"); a.emit(J("eq"), "sm_nc")
    e("clr b", "move b,x:>$%x" % CMD)
    if v34: e("move #>4,x0", "cmp x0,a"); a.emit(J("eq"), "sm_rep")
    e("move #>3,x0", "cmp x0,a"); a.emit(J("ne"), "sm_go")
    e("move b,x:>$%x" % PLAY); a.emit(J("al"), "sm_nc")
    L("sm_go")
    e("move x:>$%x,b" % LEN, "move #>2,x0", "cmp x0,b"); a.emit(J("lt"), "sm_nc")                 # nothing recorded
    e("move a1,x:>$%x" % PLAY)
    a.emit(D.jsr, "sm_se")
    e("move a1,x:>$%x" % PI, "move #0,x0", "move x0,x:>$%x" % PF)
    L("sm_nc")
    # ---- 3. gate
    if hold:                                                                                 # every playback but a plain one-shot stops when the pad is released
        e("move x:>$%x,a" % PLAY, "tst a"); a.emit(J("eq"), "sm_ng")
        e("move x:>$%x,x1" % STATE); a.emit(JSET(1, "x1"), "sm_ng")
        e("move x:>$%x,x1" % PLAY); a.emit(JSET(1, "x1"), "sm_gs")                           # PLAY 2 = forced loop
        e("move x:>$%x,a" % MODE, "tst a"); a.emit(J("eq"), "sm_ng")                         # mode 0 = one-shot: goes on
        L("sm_gs")
    else:
        e("move x:>$%x,a" % PLAY, "move #>1,x0", "cmp x0,a"); a.emit(J("ne"), "sm_ng")
        e("move x:>$%x,a" % MODE, "cmp x0,a"); a.emit(J("ne"), "sm_ng")
        e("move x:>$%x,x1" % STATE); a.emit(JSET(1, "x1"), "sm_ng")
    e("clr a", "move a,x:>$%x" % PLAY)
    L("sm_ng")
    # ---- 4. play
    e("move x:>$%x,a" % PLAY, "tst a"); a.emit(J("eq"), "sm_x")
    e("move #0,x0", "move #>2,x1", "cmp x1,a"); a.emit(J("ne"), "sm_lf1")                         # loop flag: forced or mode 2
    e("move #>1,x0")
    L("sm_lf1")
    e("move x:>$%x,a" % MODE, "cmp x1,a"); a.emit(J("ne"), "sm_lf2")
    e("move #>1,x0")
    L("sm_lf2")
    e("move x0,x:>$%x" % LF)
    a.emit(D.jsr, "sm_se")                                                                   # a = S, b = E
    e("move a1,x:>$%x" % SS, "move b1,x:>$%x" % EE)
    e("cmp a,b"); a.emit(J("eq"), "sm_park" if hold else "sm_stop")
    e("move b1,y0")                                                                          # y0 = E
    e("move x:>$%x,b" % INCI, "move x:>$%x,b0" % INCF)
    e("move x:>$%x,a" % PI, "move x:>$%x,a0" % PF)                                            # a = position
    e("move r6,x:>$%x" % SAVR6, "move #>$%x,r6" % zero)                                     # r6 = the silent word
    if FILT: e("move #>$%x,r0" % PF_L, "move #>$%x,r1" % PF_R); a.emit(D.NOP)
    else: e("move #>$%x,r0" % G.BUF); a.emit(D.NOP)
    e("move x:>$%x,x1" % SS, "move y0,x0")
    e("move x1,a", "cmp x0,a"); a.emit(J("lt"), "sm_fw")                                      # S < E: forward (a is reloaded below)
    e("neg b")                                                                               # reverse: the increment negated
    loops(a, e, "rv", "le")
    L("sm_fw")
    loops(a, e, "fw", "ge")
    L("sm_pd")
    e("move x:>$%x,r6" % SAVR6)
    e("move a1,x:>$%x" % PI, "move a0,x:>$%x" % PF)
    e("move x:>$%x,b" % LF, "tst b"); a.emit(J("ne"), "sm_x")                                 # looping: goes on
    e("move x:>$%x,x0" % EE, "move x:>$%x,x1" % SS, "move x1,b", "cmp x0,b"); a.emit(J("lt"), "sm_pdf")
    e("cmp x0,a"); a.emit(J("le"), "sm_stop"); a.emit(J("al"), "sm_x")                       # reverse: at or below the end
    L("sm_pdf")
    e("cmp x0,a"); a.emit(J("lt"), "sm_x")                                                   # forward: at or past the end
    L("sm_stop")
    e("clr a", "move a,x:>$%x" % PLAY)
    L("sm_x")
    if v34:                                                                                  # the copy of a replacement goes on: CHUNK words per block
        e("move x:>$%x,a" % CPLEN, "tst a"); a.emit(J("eq"), "sm_ncp")
        e("move #>%d,x0" % CHUNK, "move a1,x1", "cmp x0,a"); a.emit(J("le"), "sm_c1")
        e("move x0,x1")
        L("sm_c1")
        e("sub x1,a", "move a1,x:>$%x" % CPLEN)
        e("move x:>$%x,r4" % CPSRC, "move x:>$%x,r5" % CPDST); a.emit(D.NOP)
        a.emit(lambda t: T("do x1,$%x" % (t + 1)), "sm_cl")
        e("move y:(r4)+,x0")
        L("sm_cl"); e("move x0,y:(r5)+")
        e("move r4,x:>$%x" % CPSRC, "move r5,x:>$%x" % CPDST)
        L("sm_ncp")
        e("move x:>$%x,m5" % SAVM5)
    if TAIL and not FILT: TAIL(a, e)
    e("move x:>$%x,m4" % SAVM4)
    if FILT:
        e("move x:>$%x,r4" % SAVF4, "move x:>$%x,r5" % SAVF5, "move x:>$%x,r6" % SAVF6)
        e("move x:>$%x,x0" % FRAMES, "move #>$%x,a" % PF_L, "add x0,a", "move a1,r0", "move #>$%x,a" % PF_R, "add x0,a", "move a1,r1")
    if v34: a.emit(T("move x:>$%x,m2" % SAVM2)); a.emit(T("move x:>$%x,r2" % SAVR2))
    if FILT:                                                                                 # back to the mix, before the filter
        a.emit(D.RTS)
        # ---- smp_tail (FILT: fx_hook's first instruction jumps here): the tail with m4 linear and r2 = the state, the replaced instruction, the chain
        L("smp_tail")
        if v34:
            a.emit(T("move r2,x:>$%x" % SAVR2)); a.emit(T("move m2,x:>$%x" % SAVM2)); a.emit(T("move #>$%x,r2" % SMB)); a.emit(T("move #>$ffffff,m2"))
        e("move m4,x:>$%x" % SAVM4, "move #>$ffffff,m4")
        if TAIL: TAIL(a, e)
        e("move x:>$%x,m4" % SAVM4)
        if v34: a.emit(T("move x:>$%x,m2" % SAVM2)); a.emit(T("move x:>$%x,r2" % SAVR2))
        a.emit(T("move x:>$%x,x0" % G.FX_ON)); a.emit(D.jmp(pre_ret))
    elif pre_ret is not None:                                                                # PRE: the instruction the hook replaced, then the chain
        a.emit(T("move x:>$%x,x0" % G.FX_ON)); a.emit(D.jmp(pre_ret))
    else:
        e("move #>$%x,r1" % G.BUF); a.emit(D.RTS)
    if hold:
        # ---- sm_park: S = E; a held / looping playback parks at S (silent) and goes on when S != E again; a one-shot stops
        L("sm_park")
        e("move x:>$%x,x1" % LF); a.emit(JSET(0, "x1"), "sm_pk")
        e("move x:>$%x,b" % MODE, "tst b"); a.emit(J("eq"), "sm_stop")
        L("sm_pk")
        e("move a1,x:>$%x" % PI, "clr a", "move a,x:>$%x" % PF); a.emit(J("al"), "sm_x")
    if v34:
        # ---- sm_rep (CMD 4): the sample REPN plays the capture: its table entry -> slot REPK (start, length - 2), the copy starts; next slot
        L("sm_rep")
        e("move x:>$%x,b" % LEN, "move #>2,x0", "cmp x0,b"); a.emit(J("lt"), "sm_nc")
        e("move x:>$%x,a" % REPK); a.emit(lambda t: T("move #>$%x,x0" % t), "sm_stab"); e("add x0,a", "move a1,r1"); a.emit(D.NOP)
        e("move p:(r1),x1")                                                                  # x1 = the slot
        e("move x:>$%x,a" % REPN, "asl #2,a,a", "move #>$%x,x0" % stab, "add x0,a", "move a1,r0"); a.emit(D.NOP)
        e("move x1,x:(r0)+", "move x:>$%x,a" % LEN, "move #>2,x0", "sub x0,a", "move a1,x:(r0)")
        e("move x1,x:>$%x" % CPDST, "move #>$%x,x0" % base_y, "move x0,x:>$%x" % CPSRC, "move x:>$%x,x0" % LEN, "move x0,x:>$%x" % CPLEN)
        e("move x:>$%x,a" % REPK, "move #>1,x0", "add x0,a", "move #>%d,x0" % (SLOTN - 1), "and x0,a", "move a1,x:>$%x" % REPK)
        a.emit(J("al"), "sm_nc")
        L("sm_stab")
        a.emit([(slot0 + k * maxlen) & 0xFFFFFF for k in range(SLOTN)])
    if TAIL_TABLE: TAIL_TABLE(a)
    # ---- sm_se: a = BASE + LEN * SF, b = BASE + LEN * EF (integer parts in a1 / b1); uses x0, y0
    L("sm_se")
    e("move x:>$%x,x0" % LEN, "move x:>$%x,y0" % SF, "mpy y0,x0,a", "move #>$%x,y0" % base_y, "add y0,a")
    e("move x:>$%x,y0" % EF, "mpy y0,x0,b", "move #>$%x,y0" % base_y, "add y0,b")
    a.emit(D.RTS)
    return a.assemble()


def loops(a, e, tag, cond):
    """b = the increment (b1 : b0, already negated for reverse), y0 = E, r6 = ZERO.  Two `do` loops without any jump inside: with the loop flag the
    position wraps to S when it reaches E (`tcc b,a`); without it the read address becomes ZERO from E on (`tcc y1,b r6,r5`), and sm_pd stops the playback."""
    L = a.label
    e("move b1,x1", "move b0,x0")                                                            # x = the increment
    e("move x:>$%x,a" % PI, "move x:>$%x,a0" % PF)                                            # a = the position
    e("move x:>$%x,b" % LF, "tst b"); a.emit(J("eq"), "sm_s" + tag)
    a.emit(D.do_x, FRAMES, "sm_l" + tag)                                                     # loop flag
    e("move x:>$%x,b" % SS, "cmp y0,a", "t%s b,a" % cond)
    e("move a1,r5"); a.emit(D.NOP)
    mix(e)
    L("sm_l" + tag); e("add x,a")
    a.emit(J("al"), "sm_pd")
    L("sm_s" + tag)
    a.emit(D.do_x, FRAMES, "sm_e" + tag)                                                     # one-shot / gate
    e("move a1,r5", "cmp y0,a", "t%s y1,b r6,r5" % cond); a.emit(D.NOP)
    mix(e)
    L("sm_e" + tag); e("add x,a")
    a.emit(J("al"), "sm_pd")


def mix(e):
    if FILT:                                                                                 # before the filter: the sample / 16 on L (r0) and R (r1)
        e("move y:(r5),b", "asr #4,b,b", "move b,y1")
        e("move x:(r0),b", "add y1,b", "move b,x:(r0)+")
        e("move x:(r1),b", "add y1,b", "move b,x:(r1)+")
        return
    e("move y:(r5),y1")
    e("move x:(r0),b", "add y1,b", "move b,x:(r0)+")
    e("move x:(r0),b", "add y1,b", "move b,x:(r0)+")


def install_dsp(s16):
    """Before building: the code is appended to the (wrapped) SC16 DSP code."""
    prev = s16.dsp_code
    def wrapped(base):
        w, l = prev(base)
        w2, l2 = code(base + len(w), v34=V34, pre_ret=l["fx_hook"] + 2 if PRE else None)
        return w + w2, {**l, **l2}
    s16.dsp_code = wrapped


def patch_dsp(img, report):
    """After building: Master FX's fx_out (`move #>$2e10,r1` + `rts`) -> `jmp smp_post` + `nop` (PRE: fx_hook's first instruction -> `jmp smp_post`;
    FILT: -> `jmp smp_tail`, and P:$D53-$D54 (nop, nop) -> `jsr smp_post`)."""
    import struct
    dl = {k: int(v, 16) for k, v in report["sc16"]["dsp_labels"].items()}
    tab = struct.unpack_from("<I", img, 0x08029700 - 0x08010000)[0]          # the relocated core-0 block (our code exists only there)
    if PRE:                                                                  # the start of the chain: `move x:>FX_ON,x0` -> `jmp smp_post`
        o = tab - 0x08010000 + 6 + 3 * dl["fx_hook"]
        cur = [int.from_bytes(img[o + 3 * i:o + 3 * i + 3], 'big') for i in range(2)]
        assert cur == T("move x:>$%x,x0" % G.FX_ON), [hex(x) for x in cur]
        for i, w in enumerate(D.jmp(dl["smp_tail" if FILT else "smp_post"])):
            img[o + 3 * i:o + 3 * i + 3] = w.to_bytes(3, 'big')
        if FILT:                                                             # the two nops before the master filter -> jsr smp_post
            o = tab - 0x08010000 + 6 + 3 * PF_AT
            cur = [int.from_bytes(img[o + 3 * i:o + 3 * i + 3], 'big') for i in range(2)]
            assert cur == [0, 0], [hex(x) for x in cur]
            for i, w in enumerate(D.jsr(dl["smp_post"])):
                img[o + 3 * i:o + 3 * i + 3] = w.to_bytes(3, 'big')
        assert dl["sm_se"] + 16 <= 0x4000, hex(dl["sm_se"])
        return
    o = tab - 0x08010000 + 6 + 3 * dl["fx_out"]
    cur = [int.from_bytes(img[o + 3 * i:o + 3 * i + 3], 'big') for i in range(3)]
    assert cur == [0x61F400, G.BUF, 0x00000C], [hex(x) for x in cur]
    for i, w in enumerate(D.jmp(dl["smp_post"]) + [0x000000]):
        img[o + 3 * i:o + 3 * i + 3] = w.to_bytes(3, 'big')
    assert dl["sm_se"] + 16 <= 0x4000, hex(dl["sm_se"])
