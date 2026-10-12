"""SC32D (DIAGNOSTIC): the external Y memory probe, core 0.  Picks the zone for the captured sample (docs/NOTAS.md, «sample capturado»).

From the hook P:$23C (as SC21D: the `jsr premix` of SC10 becomes `jsr pprobe`, which ends with `jmp premix`: same stack depth), ONE AREA PER CALL, round robin over
the 38 areas of AREAS: the 30 stock zones of $28800 words from Y:$100000 (ARM 0x08035E28: 0-2 / 13 delay / reverb lines, 14-29 samples, 3-12 unknown) and 8 addresses
past the end of the stock map (Y:$5BF000), all below $900000 (an address with no memory behind it might stall the bus).  For an area:
  * 32 words read at a stride of $1440 (the whole zone): a checksum (eor + rotate) and the OR of the words;
  * flags (X:FL + k, sticky): bit 0 visited, bit 1 a non-zero word seen, bit 2 the checksum changed between two sweeps (a live buffer), bit 3 write / read back OK,
    bit 4 alias (the pattern also shows at the address - $400000 or - $800000, when that is still >= Y:$100000);
  * the write test runs on the first visit only: the first word of the area is saved, $5A5A00 + k written and read back, the alias addresses read, the word restored, all with
    the interrupts masked (core 1 is not stopped: if it used that word in those few cycles, one sample of a buffer would be wrong until it is written again);
  * the state code of the area (Y:STC + k): 0 not visited, 1 write failed, 2 alias, 3 changing, 4 static content, 5 free (every word read zero, unchanged, write OK);
    all codes packed into Y:PK..PK+4 (8 areas per word, area 8w + j in bits 3j..3j+2) for the ARM display (tools/probe32.py);
  * Y:SWEEP = the number of finished sweeps, Y:YR = MAGIC once the probe ran.
No DO loops (no system stack beyond the hook's own jsr; REP only to clear the arrays on the first call); x0, x1, y0, y1, r0, r1, r2, n0 and SR are restored;
a and b are free at P:$23C (SC21D).
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp56 as D  # noqa: E402
import masterfx_dsp as G  # noqa: E402

T, J = G.T, G.J
PREMIX = 0x87
ZONE, ZBASE, NZ = 0x28800, 0x100000, 30
BEYOND = (0x5BF000, 0x5C0000, 0x600000, 0x680000, 0x700000, 0x780000, 0x880000, 0x8FF000)   # all below $900000 (32 MB = 8 M words of 32 bits from $100000)
AREAS = tuple(ZBASE + z * ZONE for z in range(NZ)) + BEYOND
NA = len(AREAS)                                  # 38
NSAMP, STRIDE = 32, ZONE // 32                   # $1440
PAT = 0x5A5A00
YR = 0x3B10                                      # Y: MAGIC, PK0..PK4, SWEEP
PK, NPK, SWEEP = YR + 1, 5, YR + 6
STC = 0x3B20                                     # Y: state code per area
MAGIC = 0xC0FFEE
FL, CS = 0x3B80, 0x3BB0                          # X: flags, checksums
SAV, K, FLAG = 0x3BE0, 0x3BF1, 0x3BF0            # X: saved registers (9), area index, first-call flag
B_VIS, B_NZ, B_CHG, B_RW, B_AL = 1, 2, 4, 8, 16
S_NONE, S_FAIL, S_ALIAS, S_CHG, S_STATIC, S_FREE = range(6)
SAVED = ("x0", "x1", "y0", "y1", "r0", "r1", "r2", "n0")
# SC32D2 options (SC32D on the device, 2026-10-08: the external memory keeps 16 bits per word, the low byte reads back 0; M0 = $FFFF at the hook)
V2 = False                                       # pattern $5A5A00 + (k << 8) (low byte 0), M0 linear while the probe runs, flags also in Y:STF + k (for the MIDI dump)
STF = 0x3B50                                     # Y: flags per area (V2)
SAV_M0 = SAV + 9


ALIAS = (0x400000, 0x800000)


def alias_of(addr, zbase=ZBASE, offs=ALIAS):
    return [x if x >= zbase else 0 for x in (addr - o for o in offs)]


def table(areas, zbase=ZBASE, offs=ALIAS):
    """P table, 3 words per area: base address, alias - $400000, alias - $800000 (0 = none)."""
    return [w for ad in areas for w in [ad] + alias_of(ad, zbase, offs)]


def code(base, premix, areas=AREAS, stride=STRIDE, zbase=ZBASE, offs=ALIAS, v2=None):
    """areas / stride / zbase / offs are parameters so that the emulation test can map the areas into the interpreter's memory."""
    na = len(areas)
    v2 = V2 if v2 is None else v2
    assert na <= 8 * NPK and FL + na <= CS and CS + na <= SAV and STC + na <= 0x3B80
    a = D.Asm(base)
    L = a.label
    def e(*lines):
        for l in lines: a.emit(T(l))
    def orflag(bit):                                                               # y0 |= bit
        e("move #>%d,x0" % bit, "move y0,a", "or x0,a", "move a1,y0")
    def ptr(rn, arr, mul=1):                                                       # rn = arr + mul * k
        e("move x:>$%x,a" % K)
        if mul == 3: e("move a1,x0", "add x0,a", "add x0,a")
        a.emit(lambda t: T("move #>$%x,x0" % t), arr) if isinstance(arr, str) else e("move #>$%x,x0" % arr)
        e("add x0,a", "move a1,%s" % rn); a.emit(D.NOP)

    L("pprobe")
    for i, r in enumerate(SAVED): e("move %s,x:>$%x" % (r, SAV + i))
    e("move sr,x0", "move x0,x:>$%x" % (SAV + 8))
    if v2: e("move m0,x:>$%x" % SAV_M0, "move #>$ffffff,m0")                      # linear addressing for (r0)+n0 (M0 = $FFFF at the hook)
    e("move x:>$%x,a" % FLAG, "tst a"); a.emit(J("ne"), "pp_go")
    e("clr a", "move #>$%x,r0" % FL); a.emit(D.NOP)                               # first call: flags, checksums, codes, index, results cleared
    e("rep #%d" % (CS + na - FL), "move a,x:(r0)+")
    e("move #>$%x,r0" % STC); a.emit(D.NOP)
    e("rep #%d" % na, "move a,y:(r0)+")
    if v2:
        e("move #>$%x,r0" % STF); a.emit(D.NOP)
        e("rep #%d" % na, "move a,y:(r0)+")
    e("move a,x:>$%x" % K)
    for i in range(NPK + 1): e("move a,y:>$%x" % (PK + i))
    e("move #>1,x0", "move x0,x:>$%x" % FLAG)
    e("move #>$%x,x0" % MAGIC, "move x0,y:>$%x" % YR)
    L("pp_go")
    ptr("r1", "pp_tab", 3)                                                         # r1 = table entry
    ptr("r2", FL)                                                                  # r2 = flags
    e("move p:(r1),r0", "move #>$%x,n0" % stride); a.emit(D.NOP)
    e("clr a", "clr b")                                                            # 32 reads: a = checksum (eor, rotate), b = OR
    for _ in range(NSAMP):
        e("move y:(r0)+n0,x0", "eor x0,a", "or x0,b", "rol a")
    e("move a1,y1")                                                                # y1 = checksum
    e("move x:(r2),y0")                                                            # y0 = flags
    e("tst b"); a.emit(J("eq"), "pp_z")
    orflag(B_NZ)
    L("pp_z")
    ptr("r0", CS)
    e("move x:(r0),b", "move y1,x:(r0)")                                          # the old checksum; the new one stored
    e("move y1,x0", "cmp x0,b"); a.emit(J("eq"), "pp_same")
    e("move y0,a", "move #>%d,x0" % B_VIS, "and x0,a"); a.emit(J("eq"), "pp_same")   # the first visit has no old checksum
    orflag(B_CHG)
    L("pp_same")
    e("move y0,a", "move #>%d,x0" % B_VIS, "and x0,a"); a.emit(J("ne"), "pp_vis")
    # ---- first visit: the write test
    orflag(B_VIS)
    if v2: e("move x:>$%x,a" % K, "lsl #8,a", "move #>$%x,x0" % PAT, "add x0,a", "move a1,x1")   # x1 = the pattern, low byte 0 (16-bit memory)
    else: e("move x:>$%x,a" % K, "move #>$%x,x0" % PAT, "add x0,a", "move a1,x1")        # x1 = the pattern
    e("move p:(r1)+,r0"); a.emit(D.NOP)
    e("ori #3,mr")
    e("move y:(r0),y1")                                                            # y1 = the word found
    e("move x1,y:(r0)"); a.emit(D.NOP); a.emit(D.NOP)
    e("move y:(r0),a", "cmp x1,a"); a.emit(J("ne"), "pp_rwf")
    orflag(B_RW)
    L("pp_rwf")
    for i in range(2):                                                             # the pattern at an alias address?
        e("move p:(r1)+,a", "tst a"); a.emit(J("eq"), "pp_al%d" % i)
        e("move a1,r2"); a.emit(D.NOP)
        e("move y:(r2),a", "cmp x1,a"); a.emit(J("ne"), "pp_al%d" % i)
        orflag(B_AL)
        L("pp_al%d" % i)
    e("move y1,y:(r0)"); a.emit(D.NOP); a.emit(D.NOP)                             # the word restored
    e("move x:>$%x,x0" % (SAV + 8), "move x0,sr")                                  # the interrupt mask as found
    ptr("r2", FL)
    L("pp_vis")
    e("move y0,x:(r2)")
    if v2:
        ptr("r0", STF)
        e("move y0,y:(r0)")
    # ---- the state code of this area (y0 = flags) -> Y:STC + k
    for bit, code_, ne in ((B_VIS, S_NONE, False), (B_RW, S_FAIL, False), (B_AL, S_ALIAS, True), (B_CHG, S_CHG, True), (B_NZ, S_STATIC, True)):
        e("move y0,a", "move #>%d,x0" % bit, "and x0,a", "move #>%d,x1" % code_); a.emit(J("ne" if ne else "eq"), "pp_sc")
    e("move #>%d,x1" % S_FREE)
    L("pp_sc")
    ptr("r0", STC)                                                                 # (uses a / x0 only)
    e("move x1,y:(r0)")
    # ---- pack the codes: PK + w = sum(code(8w + j) << 3j)
    for w in range((na + 7) // 8):
        e("clr b")
        for j in reversed(range(8)):
            e("lsl b", "lsl b", "lsl b")
            if 8 * w + j < na: e("move y:>$%x,x0" % (STC + 8 * w + j), "or x0,b")
        e("move b1,y:>$%x" % (PK + w))
    # ---- next area
    e("move x:>$%x,a" % K, "move #>1,x0", "add x0,a", "move #>%d,x0" % na, "cmp x0,a"); a.emit(J("lt"), "pp_k")
    e("clr a", "move y:>$%x,b" % SWEEP, "move #>1,x0", "add x0,b", "move b1,y:>$%x" % SWEEP)
    L("pp_k")
    e("move a1,x:>$%x" % K)
    for i, r in enumerate(SAVED): e("move x:>$%x,%s" % (SAV + i, r))
    if v2: e("move x:>$%x,m0" % SAV_M0)
    a.emit(D.jmp(premix))
    L("pp_tab")
    a.emit(table(areas, zbase, offs))
    return a.assemble()


def install_dsp(s16):
    """Before building: the code is appended to the (wrapped) SC16 DSP code."""
    prev = s16.dsp_code
    def wrapped(base):
        w, l = prev(base)
        w2, l2 = code(base + len(w), PREMIX, v2=V2)
        return w + w2, {**l, **l2}
    s16.dsp_code = wrapped


def patch_dsp(img, report):
    """After building: P:$23C jsr premix -> jsr pprobe."""
    import linein2 as L2
    dl = {k: int(v, 16) for k, v in report["sc16"]["dsp_labels"].items()}
    assert int(report["sc10"]["dsp_labels"]["premix"], 16) == PREMIX
    L2.patch_p(img, 0x23C, [0x0BF080, PREMIX], [0x0BF080, dl["pprobe"]])
    assert dl["pp_tab"] + 3 * NA <= 0x3800, hex(dl["pp_tab"])
