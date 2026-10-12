"""SC35D (DIAGNOSTIC): DSP core 1, the way to a granular engine (docs/NOTAS.md, «síntesis granular»).

Core 1's stock program (364 words at P:0, bootstrap block 0x08018110, pointer at 0x08029700 + 8) is a gather service: its loop P:$10E..$12A serves the list of the shared
memory (X:$30002.., end pointer X:$30000) and ends with `jmp $10E` (P:$12A, one word).  Here the block is copied to the end of the ARM image with our words after it,
the pointer is redirected, and P:$12A becomes `jmp c1loop`, which does its work and goes on with `jmp $10E`:
  * every pass: a pass counter (internal X:C1CNT); when core 0's block counter (shared X:SH + 8) changes, the passes since the last change are stored (last and minimum):
    the idle capacity of core 1 per audio block (one pass of the empty stock loop is ~10 instructions);
  * once, at the first pass (interrupts masked while a P word holds a pattern): write / read back / restore at P:$0400, $1000, $2000, $3000, $3FFF, $4000, $7FFF
    (bits 0..6), the same in its internal X:$1000 / $3000 and Y:$1000 / $3000 (bits 0..3), its OMR / SR, the word core 0 left at Y:$640000 (external memory), a pattern
    written to Y:$650000 for core 0, the list end pointer X:$30000;
  * results in shared X:SH..SH+7, refreshed every 256 passes.
Core 0 (the P:$23C hook, `jsr pprobe` ... `jmp premix`, as SC21D / SC32D): every block its counter (shared X:SH + 8); once, the pattern $5A6400 at Y:$640000 for core 1;
every block it reads Y:$650000 (core 1's pattern) and copies the shared results to Y:$3B11..$3B1D (MAGIC at Y:$3B10 once core 1 has answered), for the ARM dump of
tools/probe32b.py (pad 9 of the synth source view, 72 CC on channel 16).
  Y:$3B11 core-1 magic ($C1C1C1)   $3B12 core-1 passes / 256     $3B13 P-RAM bits     $3B14 X/Y bits       $3B15 core 1 read Y:$640000 (want $5A6400)
  $3B16 core 0 read Y:$650000 (want $5A6500)    $3B17 passes per block (last)    $3B18 passes per block (min)   $3B19 core-0 blocks   $3B1A core-1 OMR
  $3B1B core-1 SR    $3B1C core-1 X:$30000 (stock: $30202)    $3B1D core-0 X:$30000
Reversible: only DSP RAM (volatile); the external words are in the free area past $628800.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp56 as D  # noqa: E402
import masterfx_dsp as G  # noqa: E402

T, J = G.T, G.J
PREMIX = 0x87
YM, NW = 0x3B10, 13
MAGIC = 0xC1D1A6                                   # the dump's word 0 (tells the reader this is SC35D)
C1MAGIC = 0xC1C1C1
SH = 0x30300                                        # shared X: results of core 1 (8 words), +8 = core-0 block counter
EXT0, EXT1 = 0x640000, 0x650000                     # external Y: core 0 -> core 1, core 1 -> core 0
PAT0, PAT1 = 0x5A6400, 0x5A6500
PTEST = (0x0400, 0x1000, 0x2000, 0x3000, 0x3FFF, 0x4000, 0x7FFF)
XYTEST = (("x", 0x1000), ("x", 0x3000), ("y", 0x1000), ("y", 0x3000))
C1_HOOK, C1_LOOP = 0x12A, 0x10E
C1_STOCK_WORDS = 0x16C
C1V = 0x3F00                                         # core 1 internal X: our variables (CNT, FIRST, LASTBLK, SINCE, MIN, saved regs)
C0F = 0x3BF0                                         # core 0 X: first-call flag


def core1_code(base, sh=SH, ext0=EXT0, ext1=EXT1, ptest=PTEST, xytest=XYTEST):
    """Core 1 words from `base` (after the stock 364).  a, b, x0, x1, r0 are saved / restored (the stock loop keeps r5 / m5)."""
    a = D.Asm(base)
    L = a.label
    def e(*lines):
        for l in lines: a.emit(T(l))
    CNT, FIRST, LAST, SINCE, MIN, SAV = C1V, C1V + 1, C1V + 2, C1V + 3, C1V + 4, C1V + 8
    L("c1loop")
    for i, r in enumerate(("a", "b", "x0", "x1", "r0")):
        e("move %s,x:>$%x" % (r if r not in ("a", "b") else r + "1", SAV + i))
    e("move a0,x:>$%x" % (SAV + 5), "move a2,x:>$%x" % (SAV + 6), "move b0,x:>$%x" % (SAV + 7), "move b2,x:>$%x" % (SAV + 8))
    e("move x:>$%x,a" % FIRST, "tst a"); a.emit(J("ne"), "c1_run")
    e("move #>1,x0", "move x0,x:>$%x" % FIRST, "clr a", "move a,x:>$%x" % CNT, "move a,x:>$%x" % SINCE, "move #>$7fffff,x0", "move x0,x:>$%x" % MIN)
    e("move x:>$%x,x0" % (sh + 8), "move x0,x:>$%x" % LAST)
    # ---- once: P RAM
    e("move sr,x:>$%x" % (SAV + 9), "ori #3,mr", "clr b")
    for k, ad in enumerate(ptest):
        e("move #>$%x,r0" % ad); a.emit(D.NOP)
        e("move p:(r0),x1", "move #>$5a5a5a,x0", "move x0,p:(r0)"); a.emit(D.NOP); a.emit(D.NOP)
        e("move p:(r0),a", "cmp x0,a"); a.emit(J("ne"), "c1_p%d" % k)
        e("move #>%d,x0" % (1 << k), "or x0,b")
        L("c1_p%d" % k)
        e("move x1,p:(r0)"); a.emit(D.NOP); a.emit(D.NOP)
    e("move b1,x:>$%x" % (sh + 2))
    # ---- once: internal X / Y
    e("clr b")
    for k, (sp, ad) in enumerate(xytest):
        e("move %s:>$%x,x1" % (sp, ad), "move #>$a5a5a5,x0", "move x0,%s:>$%x" % (sp, ad), "move %s:>$%x,a" % (sp, ad), "cmp x0,a"); a.emit(J("ne"), "c1_x%d" % k)
        e("move #>%d,x0" % (1 << k), "or x0,b")
        L("c1_x%d" % k)
        e("move x1,%s:>$%x" % (sp, ad))
    e("move b1,x:>$%x" % (sh + 3))
    e("move x:>$%x,x0" % (SAV + 9), "move x0,sr")
    # ---- once: OMR, SR, external memory, the list pointer
    e("move omr,x0", "move x0,x:>$%x" % (sh + 6), "move x:>$%x,x0" % (SAV + 9), "move x0,x:>$%x" % (sh + 7))
    e("move #>$%x,r0" % ext0); a.emit(D.NOP); e("move y:(r0),x0", "move x0,x:>$%x" % (sh + 4))
    e("move #>$%x,r0" % ext1); a.emit(D.NOP); e("move #>$%x,x0" % PAT1, "move x0,y:(r0)")
    e("move x:>$30000,x0", "move x0,x:>$%x" % (sh + 5))
    e("move #>$%x,x0" % C1MAGIC, "move x0,x:>$%x" % sh)
    L("c1_run")
    # ---- every pass: count; passes per core-0 block
    e("move x:>$%x,a" % CNT, "move #>1,x0", "add x0,a", "move a1,x:>$%x" % CNT)
    e("move x:>$%x,a" % SINCE, "add x0,a", "move a1,x:>$%x" % SINCE)
    e("move x:>$%x,b" % (sh + 8), "move x:>$%x,x1" % LAST, "cmp x1,b"); a.emit(J("eq"), "c1_same")
    e("move b1,x:>$%x" % LAST, "move a1,x:>$%x" % (sh + 1 + 0x10), "move x:>$%x,b" % MIN, "cmp a,b"); a.emit(J("le"), "c1_nmin")
    e("move a1,x:>$%x" % MIN)
    L("c1_nmin")
    e("clr a", "move a,x:>$%x" % SINCE)
    L("c1_same")
    e("move x:>$%x,a" % CNT, "move #>$ff,x0", "and x0,a"); a.emit(J("ne"), "c1_out")       # every 256 passes: the counters to the shared memory
    e("move x:>$%x,a" % CNT, "lsr a", "lsr a", "lsr a", "lsr a", "lsr a", "lsr a", "lsr a", "lsr a", "move a1,x:>$%x" % (sh + 1))
    e("move x:>$%x,x0" % (sh + 1 + 0x10), "move x0,x:>$%x" % (sh + 0x18), "move x:>$%x,x0" % MIN, "move x0,x:>$%x" % (sh + 0x19))
    L("c1_out")
    e("move x:>$%x,a0" % (SAV + 5), "move x:>$%x,a2" % (SAV + 6), "move x:>$%x,b0" % (SAV + 7), "move x:>$%x,b2" % (SAV + 8))
    for i, r in enumerate(("a1", "b1", "x0", "x1", "r0")):
        e("move x:>$%x,%s" % (SAV + i, r))
    a.emit(D.jmp(C1_LOOP))
    return a.assemble()


def core0_code(base, premix, sh=SH, ext0=EXT0, ext1=EXT1):
    a = D.Asm(base)
    L = a.label
    def e(*lines):
        for l in lines: a.emit(T(l))
    SAV = C0F + 1
    L("pprobe")
    e("move x0,x:>$%x" % SAV, "move r0,x:>$%x" % (SAV + 1))
    e("move x:>$%x,a" % C0F, "tst a"); a.emit(J("ne"), "c0_go")
    e("move #>1,x0", "move x0,x:>$%x" % C0F)
    e("move #>$%x,r0" % ext0); a.emit(D.NOP); e("move #>$%x,x0" % PAT0, "move x0,y:(r0)")
    L("c0_go")
    e("move x:>$%x,a" % (sh + 8), "move #>1,x0", "add x0,a", "move a1,x:>$%x" % (sh + 8))       # the block counter for core 1
    # the dump: Y:YM + 1.. = shared results; core 0's own reads
    for i, src in enumerate((sh, sh + 1, sh + 2, sh + 3, sh + 4)):
        e("move x:>$%x,x0" % src, "move x0,y:>$%x" % (YM + 1 + i))
    e("move #>$%x,r0" % ext1); a.emit(D.NOP); e("move y:(r0),x0", "move x0,y:>$%x" % (YM + 6))
    for i, src in ((7, sh + 0x18), (8, sh + 0x19), (9, sh + 8), (10, sh + 6), (11, sh + 7), (12, sh + 5)):
        e("move x:>$%x,x0" % src, "move x0,y:>$%x" % (YM + i))
    e("move x:>$30000,x0", "move x0,y:>$%x" % (YM + 13))
    e("move x:>$%x,a" % sh, "move #>$%x,x0" % C1MAGIC, "cmp x0,a"); a.emit(J("ne"), "c0_x")
    e("move #>$%x,x0" % MAGIC, "move x0,y:>$%x" % YM)
    L("c0_x")
    e("move x:>$%x,x0" % SAV, "move x:>$%x,r0" % (SAV + 1))
    a.emit(D.jmp(premix))
    return a.assemble()


# ---------------------------------------------------------------- SC35D.1 (V2)
# SC35D on the device: core 1 runs our code and shares the external memory with core 0, but its OMR = 0 (the MS = 1 stub goes to core 0 only) and its internal
# memory is small (P writes at $0400, not at $1000; X / Y at $1000, not at $3000): our variables at X:$3F00 did not exist.  V2 keeps every core-1 variable in the
# shared memory (X:SH + 16..), maps P / X / Y more finely, measures the idle passes per audio block, re-reads the external memory both ways all the time and puts a
# sentinel at Y:$600000 (the SC33 capture buffer) that core 0 writes once: if it changes later, stock writes in that area.  The stock loop P:$10E..$12A keeps only
# r5 / m5 across passes (a, x0, r0 are reloaded), so nothing else is saved.  Dump words (Y:YM + i, the ARM sends 0..13, 0..11 survive the 64-message cut):
#   0 MAGIC2   1 core-1 passes / 256   2 P bits (PTEST2)   3 X / Y bits (XYTEST2)   4 core 1 reads Y:$640000 now (want PAT0)   5 core 0 reads Y:$650000 (want PAT1)
#   6 passes per block (last)   7 passes per block (min)   8 core-0 blocks   9 Y:$600000 before core 0 wrote the sentinel   10 Y:$600000 now (want PATS)
#   11 core-1 OMR   12 core-1 SR   13 core 1's first read of Y:$640000
V2 = False
MAGIC2 = 0xC1D1A7
EXTS, PATS = 0x600000, 0x5A6600
PTEST2 = (0x0400, 0x0600, 0x0800, 0x0A00, 0x0C00, 0x0E00, 0x0FFF, 0x1000)
XYTEST2 = tuple((sp, ad) for sp in ("x", "y") for ad in (0x0800, 0x1800, 0x2000, 0x2800, 0x2FFF))
FIRSTM = 0xF1F1F1


def core1_code2(base, sh=SH, ext0=EXT0, ext1=EXT1, ptest=PTEST2, xytest=XYTEST2):
    a = D.Asm(base)
    L = a.label
    def e(*lines):
        for l in lines: a.emit(T(l))
    CNT, FIRST, LAST, SINCE, MIN, SAVSR = (sh + 16 + i for i in range(6))
    L("c1loop")
    e("move x:>$%x,a" % FIRST, "move #>$%x,x0" % FIRSTM, "cmp x0,a"); a.emit(J("eq"), "c1_run")
    e("move x0,x:>$%x" % FIRST, "clr a", "move a,x:>$%x" % CNT, "move a,x:>$%x" % SINCE, "move #>$7fffff,x0", "move x0,x:>$%x" % MIN)
    e("move x:>$%x,x0" % (sh + 8), "move x0,x:>$%x" % LAST)
    e("move sr,x:>$%x" % SAVSR, "ori #3,mr", "clr b")
    for k, ad in enumerate(ptest):
        e("move #>$%x,r0" % ad); a.emit(D.NOP)
        e("move p:(r0),x1", "move #>$5a5a5a,x0", "move x0,p:(r0)"); a.emit(D.NOP); a.emit(D.NOP)
        e("move p:(r0),a", "cmp x0,a"); a.emit(J("ne"), "c1_p%d" % k)
        e("move #>%d,x0" % (1 << k), "or x0,b")
        L("c1_p%d" % k)
        e("move x1,p:(r0)"); a.emit(D.NOP); a.emit(D.NOP)
    e("move b1,x:>$%x" % (sh + 2), "clr b")
    for k, (sp, ad) in enumerate(xytest):
        e("move %s:>$%x,x1" % (sp, ad), "move #>$a5a5a5,x0", "move x0,%s:>$%x" % (sp, ad), "move %s:>$%x,a" % (sp, ad), "cmp x0,a"); a.emit(J("ne"), "c1_x%d" % k)
        e("move #>%d,x0" % (1 << k), "or x0,b")
        L("c1_x%d" % k)
        e("move x1,%s:>$%x" % (sp, ad))
    e("move b1,x:>$%x" % (sh + 3))
    e("move x:>$%x,x0" % SAVSR, "move x0,sr")
    e("move omr,x0", "move x0,x:>$%x" % (sh + 6), "move x:>$%x,x0" % SAVSR, "move x0,x:>$%x" % (sh + 7))
    e("move #>$%x,r0" % ext0); a.emit(D.NOP); e("move y:(r0),x0", "move x0,x:>$%x" % (sh + 5))
    e("move #>$%x,x0" % C1MAGIC, "move x0,x:>$%x" % sh)
    L("c1_run")
    e("move x:>$%x,a" % CNT, "move #>1,x0", "add x0,a", "move a1,x:>$%x" % CNT)
    e("move x:>$%x,a" % SINCE, "add x0,a", "move a1,x:>$%x" % SINCE)
    e("move x:>$%x,b" % (sh + 8), "move x:>$%x,x1" % LAST, "cmp x1,b"); a.emit(J("eq"), "c1_same")
    e("move b1,x:>$%x" % LAST, "move a1,x:>$%x" % (sh + 9), "move x:>$%x,b" % MIN, "cmp a,b"); a.emit(J("le"), "c1_nmin")
    e("move a1,x:>$%x" % MIN, "move a1,x:>$%x" % (sh + 10))
    L("c1_nmin")
    e("clr a", "move a,x:>$%x" % SINCE)
    L("c1_same")
    e("move x:>$%x,a" % CNT, "move #>$ff,x0", "and x0,a"); a.emit(J("ne"), "c1_out")          # every 256 passes
    e("move x:>$%x,a" % CNT, "lsr a", "lsr a", "lsr a", "lsr a", "lsr a", "lsr a", "lsr a", "lsr a", "move a1,x:>$%x" % (sh + 1))
    e("move #>$%x,r0" % ext0); a.emit(D.NOP); e("move y:(r0),x0", "move x0,x:>$%x" % (sh + 4))
    e("move #>$%x,r0" % ext1); a.emit(D.NOP); e("move #>$%x,x0" % PAT1, "move x0,y:(r0)")
    L("c1_out")
    a.emit(D.jmp(C1_LOOP))
    return a.assemble()


def core0_code2(base, premix, sh=SH, ext0=EXT0, ext1=EXT1, exts=EXTS):
    a = D.Asm(base)
    L = a.label
    def e(*lines):
        for l in lines: a.emit(T(l))
    SAV = C0F + 1
    L("pprobe")
    e("move x0,x:>$%x" % SAV, "move r0,x:>$%x" % (SAV + 1))
    e("move x:>$%x,a" % C0F, "tst a"); a.emit(J("ne"), "c0_go")
    e("move #>1,x0", "move x0,x:>$%x" % C0F)
    e("move #>$%x,r0" % exts); a.emit(D.NOP); e("move y:(r0),x0", "move x0,x:>$%x" % (SAV + 2), "move #>$%x,x0" % PATS, "move x0,y:(r0)")
    L("c0_go")
    e("move x:>$%x,a" % (sh + 8), "move #>1,x0", "add x0,a", "move a1,x:>$%x" % (sh + 8))
    e("move #>$%x,r0" % ext0); a.emit(D.NOP); e("move #>$%x,x0" % PAT0, "move x0,y:(r0)")             # every block
    for i, src in ((1, sh + 1), (2, sh + 2), (3, sh + 3), (4, sh + 4), (6, sh + 9), (7, sh + 10), (8, sh + 8), (11, sh + 6), (12, sh + 7), (13, sh + 5)):
        e("move x:>$%x,x0" % src, "move x0,y:>$%x" % (YM + i))
    e("move #>$%x,r0" % ext1); a.emit(D.NOP); e("move y:(r0),x0", "move x0,y:>$%x" % (YM + 5))
    e("move x:>$%x,x0" % (SAV + 2), "move x0,y:>$%x" % (YM + 9))
    e("move #>$%x,r0" % exts); a.emit(D.NOP); e("move y:(r0),x0", "move x0,y:>$%x" % (YM + 10))
    e("move x:>$%x,a" % sh, "move #>$%x,x0" % C1MAGIC, "cmp x0,a"); a.emit(J("ne"), "c0_x")
    e("move #>$%x,x0" % MAGIC2, "move x0,y:>$%x" % YM)
    L("c0_x")
    e("move x:>$%x,x0" % SAV, "move x:>$%x,r0" % (SAV + 1))
    a.emit(D.jmp(premix))
    return a.assemble()


# ---------------------------------------------------------------- SC35D2 (V3)
# SC35D.1 on the device: core 1 has P:$0000-$07FF, at least 976 idle passes per block; Y:$600000 changes after boot (stock writes there: the SC33 / SC34 capture
# buffer collides); and with a bigger pack the stock gather list (X:$30002.., end pointer X:$30000) grew past $30308 and overwrote our shared words.
# V3: the core-1 words go to the top of the shared memory (X:SH3.., core 0 clears X:$30000-$37FFF at boot; the list never gets near), core 1 also tracks the longest
# list (max of X:$30000).  Core 0 maps the external memory READ-ONLY: one of SENT (24 addresses, two controls in the sample zones) per block, round robin; a change
# of the word since the previous visit sets its bit in EVER and in the current window (1024 blocks); WIN = the bits of the last full window.  Nothing is written
# outside our own words.  Dump words (Y:YM + i; 0..11 survive the 64-message cut):
#   0 MAGIC3   1 EVER   2 WIN   3 windows   4 longest list (core 1)   5 / 6 passes per block last / min   7 core-0 blocks   8 core-1 passes / 256
#   9 Y:$600000 now   10 longest list seen by core 0   11 X:$30000 now   12 SEEN   13 CUR
V3 = False
MAGIC3 = 0xC1D1A8
SH3 = 0x37F00
SENT = (0x337000, 0x5BE000, 0x5C0000, 0x5E0000, 0x600000, 0x608000, 0x610000, 0x620000, 0x630000, 0x640000, 0x650000, 0x660000,
        0x680000, 0x6A0000, 0x6C0000, 0x6E0000, 0x700000, 0x740000, 0x780000, 0x7C0000, 0x800000, 0x840000, 0x880000, 0x8F0000)
C0V = 0x3B80                                        # core 0 X: PREV[24], then the variables
WIN_MASK = 0x3FF


def core1_code3(base, sh=SH3):
    a = D.Asm(base)
    L = a.label
    def e(*lines):
        for l in lines: a.emit(T(l))
    CNT, FIRST, LAST, SINCE, MIN = (sh + 16 + i for i in range(5))
    L("c1loop")
    e("move x:>$%x,a" % FIRST, "move #>$%x,x0" % FIRSTM, "cmp x0,a"); a.emit(J("eq"), "c1_run")
    e("move x0,x:>$%x" % FIRST, "clr a", "move a,x:>$%x" % CNT, "move a,x:>$%x" % SINCE, "move a,x:>$%x" % (sh + 1), "move #>$7fffff,x0", "move x0,x:>$%x" % MIN)
    e("move x:>$%x,x0" % (sh + 8), "move x0,x:>$%x" % LAST, "move #>$%x,x0" % C1MAGIC, "move x0,x:>$%x" % sh)
    L("c1_run")
    e("move x:>$%x,a" % CNT, "move #>1,x0", "add x0,a", "move a1,x:>$%x" % CNT)
    e("move x:>$%x,a" % SINCE, "add x0,a", "move a1,x:>$%x" % SINCE)
    e("move x:>$%x,b" % (sh + 8), "move x:>$%x,x1" % LAST, "cmp x1,b"); a.emit(J("eq"), "c1_same")
    e("move b1,x:>$%x" % LAST, "move a1,x:>$%x" % (sh + 9), "move x:>$%x,b" % MIN, "cmp a,b"); a.emit(J("le"), "c1_nmin")
    e("move a1,x:>$%x" % MIN, "move a1,x:>$%x" % (sh + 10))
    L("c1_nmin")
    e("clr a", "move a,x:>$%x" % SINCE)
    L("c1_same")
    e("move x:>$30000,a", "move x:>$%x,x0" % (sh + 1), "cmp x0,a"); a.emit(J("le"), "c1_nmax")         # the longest list
    e("move a1,x:>$%x" % (sh + 1))
    L("c1_nmax")
    e("move x:>$%x,a" % CNT, "move #>$ff,x0", "and x0,a"); a.emit(J("ne"), "c1_out")
    e("move x:>$%x,a" % CNT, "lsr a", "lsr a", "lsr a", "lsr a", "lsr a", "lsr a", "lsr a", "lsr a", "move a1,x:>$%x" % (sh + 2))
    L("c1_out")
    a.emit(D.jmp(C1_LOOP))
    return a.assemble()


def core0_code3(base, premix, sh=SH3, sent=SENT, v=C0V):
    a = D.Asm(base)
    L = a.label
    def e(*lines):
        for l in lines: a.emit(T(l))
    n = len(sent)
    PREV = v
    IDX, SEEN, EVER, CUR, WIN, NWIN, BLK, MAXL, SX0, SX1, SR0, TB, TV = (v + 0x20 + i for i in range(13))
    L("pprobe")
    e("move x0,x:>$%x" % SX0, "move x1,x:>$%x" % SX1, "move r0,x:>$%x" % SR0)
    e("move x:>$%x,a" % BLK, "move #>1,x0", "add x0,a", "move a1,x:>$%x" % BLK, "move a1,x:>$%x" % (sh + 8))
    e("move x:>$30000,a", "move x:>$%x,x0" % MAXL, "cmp x0,a"); a.emit(J("le"), "c0_nmax")
    e("move a1,x:>$%x" % MAXL)
    L("c0_nmax")
    # one sentinel per block: x1 = its address, TB = its bit, TV = the word now
    e("move x:>$%x,a" % IDX); a.emit(lambda t: [0x44F400, t], "c0_addr"); e("add x0,a", "move a1,r0"); a.emit(D.NOP); e("move p:(r0),x1")
    e("move x:>$%x,a" % IDX); a.emit(lambda t: [0x44F400, t], "c0_bits"); e("add x0,a", "move a1,r0"); a.emit(D.NOP); e("move p:(r0),x0", "move x0,x:>$%x" % TB)
    e("move x1,r0"); a.emit(D.NOP); e("move y:(r0),a", "move a1,x:>$%x" % TV)
    e("move x:>$%x,a" % IDX, "move #>$%x,x0" % PREV, "add x0,a", "move a1,r0"); a.emit(D.NOP)
    e("move x:>$%x,a" % SEEN, "move x:>$%x,x0" % TB, "and x0,a"); a.emit(J("ne"), "c0_seen")
    e("move x:>$%x,a" % SEEN, "or x0,a", "move a1,x:>$%x" % SEEN, "move x:>$%x,x0" % TV, "move x0,x:(r0)"); a.emit(J("al"), "c0_next")
    L("c0_seen")
    e("move x:(r0),x0", "move x:>$%x,a" % TV, "cmp x0,a"); a.emit(J("eq"), "c0_next")
    e("move a1,x:(r0)", "move x:>$%x,x0" % TB)
    e("move x:>$%x,a" % EVER, "or x0,a", "move a1,x:>$%x" % EVER, "move x:>$%x,a" % CUR, "or x0,a", "move a1,x:>$%x" % CUR)
    L("c0_next")
    e("move x:>$%x,a" % IDX, "move #>1,x0", "add x0,a", "move #>%d,x0" % n, "cmp x0,a"); a.emit(J("ne"), "c0_nw")
    e("clr a")
    L("c0_nw")
    e("move a1,x:>$%x" % IDX)
    # windows of WIN_MASK + 1 blocks
    e("move x:>$%x,a" % BLK, "move #>$%x,x0" % WIN_MASK, "and x0,a"); a.emit(J("ne"), "c0_nwin")
    e("move x:>$%x,x0" % CUR, "move x0,x:>$%x" % WIN, "clr a", "move a,x:>$%x" % CUR)
    e("move x:>$%x,a" % NWIN, "move #>1,x0", "add x0,a", "move a1,x:>$%x" % NWIN)
    L("c0_nwin")
    # the dump
    for i, src in ((1, EVER), (2, WIN), (3, NWIN), (4, sh + 1), (5, sh + 9), (6, sh + 10), (7, BLK), (8, sh + 2), (10, MAXL), (11, 0x30000), (12, SEEN), (13, CUR)):
        e("move x:>$%x,x0" % src, "move x0,y:>$%x" % (YM + i))
    e("move #>$%x,r0" % EXTS); a.emit(D.NOP); e("move y:(r0),x0", "move x0,y:>$%x" % (YM + 9))
    e("move x:>$%x,a" % sh, "move #>$%x,x0" % C1MAGIC, "cmp x0,a"); a.emit(J("ne"), "c0_x")
    e("move #>$%x,x0" % MAGIC3, "move x0,y:>$%x" % YM)
    L("c0_x")
    e("move x:>$%x,x0" % SX0, "move x:>$%x,x1" % SX1, "move x:>$%x,r0" % SR0)
    a.emit(D.jmp(premix))
    L("c0_addr"); a.emit(list(sent))
    L("c0_bits"); a.emit([1 << i for i in range(n)])
    return a.assemble()


# ---------------------------------------------------------------- SC35D3 (V4)
# SC35D2 on the device: the pack samples are loaded back to back from Y:$580000 (limit $E80000, ARM 0x08049A1C), so the SC33 / SC34 buffer at $600000 sits in
# the sample memory.  V4 maps the two candidate areas READ-ONLY: $337000..$57F000 (zones 14-28 of the ARM map, below the samples) and $E80000..$FFF000 (above
# the sample limit), with controls $580000 (the first sample: must change at a pack load) and $840000.  On every visit it also reads the address with bit 23
# flipped (± $800000): a word that never differs from that one is a mirror (the memory is not there).  Core 1 = core1_code3.  Dump words:
#   0 MAGIC4   1 EVER   2 WIN   3 NOTMIR (bits: the word differed from its ± $800000 word at least once = real memory)   4 windows   5 longest list (core 1)
#   6 passes per block (min)   7 core-0 blocks   8 core-1 passes / 256   9 Y:$E80000 now   10 Y:$680000 now   11 X:$30000 now   12 SEEN   13 CUR
V4 = False
MAGIC4 = 0xC1D1A9
SENT4 = (0x580000, 0x840000, 0x337000, 0x360000, 0x388000, 0x3B0000, 0x3D8000, 0x400000, 0x440000, 0x480000, 0x4C0000, 0x500000,
         0x540000, 0x57F000, 0xE80000, 0xEA0000, 0xEC0000, 0xEE0000, 0xF00000, 0xF40000, 0xF80000, 0xFC0000, 0xFF0000, 0xFFF000)
MIRROR = 0x800000
PEEK4 = (0xE80000, 0x680000)


def core0_code4(base, premix, sh=SH3, sent=SENT4, v=C0V, peek=PEEK4, mirror=MIRROR):
    a = D.Asm(base)
    L = a.label
    def e(*lines):
        for l in lines: a.emit(T(l))
    n = len(sent)
    PREV = v
    IDX, SEEN, EVER, CUR, WIN, NWIN, BLK, MAXL, SX0, SX1, SR0, TB, TV, NOTMIR = (v + 0x20 + i for i in range(14))
    L("pprobe")
    e("move x0,x:>$%x" % SX0, "move x1,x:>$%x" % SX1, "move r0,x:>$%x" % SR0)
    e("move x:>$%x,a" % BLK, "move #>1,x0", "add x0,a", "move a1,x:>$%x" % BLK, "move a1,x:>$%x" % (sh + 8))
    e("move x:>$30000,a", "move x:>$%x,x0" % MAXL, "cmp x0,a"); a.emit(J("le"), "c0_nmax")
    e("move a1,x:>$%x" % MAXL)
    L("c0_nmax")
    e("move x:>$%x,a" % IDX); a.emit(lambda t: [0x44F400, t], "c0_addr"); e("add x0,a", "move a1,r0"); a.emit(D.NOP); e("move p:(r0),x1")
    e("move x:>$%x,a" % IDX); a.emit(lambda t: [0x44F400, t], "c0_bits"); e("add x0,a", "move a1,r0"); a.emit(D.NOP); e("move p:(r0),x0", "move x0,x:>$%x" % TB)
    e("move x1,r0"); a.emit(D.NOP); e("move y:(r0),a", "move a1,x:>$%x" % TV)
    # the mirror: the word at the address with bit 23 flipped
    e("move x1,a", "move #>$%x,x0" % mirror, "eor x0,a", "move a1,r0"); a.emit(D.NOP); e("move y:(r0),x0", "move x:>$%x,a" % TV, "cmp x0,a"); a.emit(J("eq"), "c0_mir")
    e("move x:>$%x,a" % NOTMIR, "move x:>$%x,x0" % TB, "or x0,a", "move a1,x:>$%x" % NOTMIR)
    L("c0_mir")
    e("move x:>$%x,a" % IDX, "move #>$%x,x0" % PREV, "add x0,a", "move a1,r0"); a.emit(D.NOP)
    e("move x:>$%x,a" % SEEN, "move x:>$%x,x0" % TB, "and x0,a"); a.emit(J("ne"), "c0_seen")
    e("move x:>$%x,a" % SEEN, "or x0,a", "move a1,x:>$%x" % SEEN, "move x:>$%x,x0" % TV, "move x0,x:(r0)"); a.emit(J("al"), "c0_next")
    L("c0_seen")
    e("move x:(r0),x0", "move x:>$%x,a" % TV, "cmp x0,a"); a.emit(J("eq"), "c0_next")
    e("move a1,x:(r0)", "move x:>$%x,x0" % TB)
    e("move x:>$%x,a" % EVER, "or x0,a", "move a1,x:>$%x" % EVER, "move x:>$%x,a" % CUR, "or x0,a", "move a1,x:>$%x" % CUR)
    L("c0_next")
    e("move x:>$%x,a" % IDX, "move #>1,x0", "add x0,a", "move #>%d,x0" % n, "cmp x0,a"); a.emit(J("ne"), "c0_nw")
    e("clr a")
    L("c0_nw")
    e("move a1,x:>$%x" % IDX)
    e("move x:>$%x,a" % BLK, "move #>$%x,x0" % WIN_MASK, "and x0,a"); a.emit(J("ne"), "c0_nwin")
    e("move x:>$%x,x0" % CUR, "move x0,x:>$%x" % WIN, "clr a", "move a,x:>$%x" % CUR)
    e("move x:>$%x,a" % NWIN, "move #>1,x0", "add x0,a", "move a1,x:>$%x" % NWIN)
    L("c0_nwin")
    for i, src in ((1, EVER), (2, WIN), (3, NOTMIR), (4, NWIN), (5, sh + 1), (6, sh + 10), (7, BLK), (8, sh + 2), (11, 0x30000), (12, SEEN), (13, CUR)):
        e("move x:>$%x,x0" % src, "move x0,y:>$%x" % (YM + i))
    for i, ad in ((9, peek[0]), (10, peek[1])):
        e("move #>$%x,r0" % ad); a.emit(D.NOP); e("move y:(r0),x0", "move x0,y:>$%x" % (YM + i))
    e("move x:>$%x,a" % sh, "move #>$%x,x0" % C1MAGIC, "cmp x0,a"); a.emit(J("ne"), "c0_x")
    e("move #>$%x,x0" % MAGIC4, "move x0,y:>$%x" % YM)
    L("c0_x")
    e("move x:>$%x,x0" % SX0, "move x:>$%x,x1" % SX1, "move x:>$%x,r0" % SR0)
    a.emit(D.jmp(premix))
    L("c0_addr"); a.emit(list(sent))
    L("c0_bits"); a.emit([1 << i for i in range(n)])
    return a.assemble()


def install_dsp(s16):
    prev = s16.dsp_code
    def wrapped(base):
        w, l = prev(base)
        w2, l2 = (core0_code4 if V4 else core0_code3 if V3 else core0_code2 if V2 else core0_code)(base + len(w), PREMIX)
        return w + w2, {**l, **l2}
    s16.dsp_code = wrapped


def patch(img, report):
    """After building: P:$23C -> jsr pprobe (core 0); core 1's block copied to the end of the image with c1loop, P:$12A -> jmp c1loop."""
    import struct
    import linein2 as L2
    BASE = 0x08010000
    dl = {k: int(v, 16) for k, v in report["sc16"]["dsp_labels"].items()}
    assert int(report["sc10"]["dsp_labels"]["premix"], 16) == PREMIX
    L2.patch_p(img, 0x23C, [0x0BF080, PREMIX], [0x0BF080, dl["pprobe"]])
    tab = 0x08029700 + 8
    old = struct.unpack_from("<I", img, tab - BASE)[0]
    o = old - BASE
    n = int.from_bytes(img[o:o + 3], "big")
    assert n == C1_STOCK_WORDS and int.from_bytes(img[o + 3:o + 6], "big") == 0
    prog = [int.from_bytes(img[o + 6 + 3 * i:o + 9 + 3 * i], "big") for i in range(n)]
    assert prog[C1_HOOK] == 0x0C0000 | C1_LOOP, hex(prog[C1_HOOK])
    w1, l1 = (core1_code3 if (V3 or V4) else core1_code2 if V2 else core1_code)(n)
    assert n + len(w1) < 0x1000
    prog[C1_HOOK] = 0x0C0000 | l1["c1loop"]                                    # jmp c1loop (short form)
    blk = (n + len(w1)).to_bytes(3, "big") + b"\0\0\0" + D.to_bytes(prog + w1)
    at = (len(img) + BASE + 3) & ~3
    img += b"\xFF" * (at - BASE - len(img)) + blk
    while len(img) % 4:
        img += b"\xFF"
    struct.pack_into("<I", img, tab - BASE, at)
    return dict(core1_block=hex(at), core1_words=n + len(w1), c1loop=hex(l1["c1loop"]), old_block=hex(old))
