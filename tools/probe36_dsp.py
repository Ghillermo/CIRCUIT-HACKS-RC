"""SC35DB (DIAGNOSTIC): audio blocks from DSP core 1 to core 0 through the shared memory, with a granular-like load on core 1 (the way to the granular
synth, docs/NOTAS.md «sinte granular»).

Core 1 (its stock loop P:$10E..$12A, P:$12A = jmp c1loop as in SC35D; all its words in the shared memory X:SH5.., core 0 clears X:$30000-$37FFF at boot):
  * every pass: pass counter; passes per core-0 block (last / min) = its idle capacity;
  * when core 0's block counter (SH5 + 8) becomes b: the load first (W "grains" x NS samples: `move y:(r4)+,x0` from the pack's sample memory at
    Y:$580000 + `mac`), then block b written into buffer b & 1 (X:BUF0 / BUF1, NS words: word i = (b & $FF) << 16 | i) and READY = b.  W = SH5 + 5 (0 = none);
Core 0 (the hook P:$23C, `jsr pprobe` ... `jmp premix`, as SC21D / SC35D): every block b (its own counter, published at SH5 + 8 after the check):
  READY == b (else a late block) and words 0 / NS-1 of buffer b & 1 = the expected values (else corrupt); W := X:C0V + 8 (written by the PC through
  rdiag.DSPW); results in its internal X:C0V.. for rdiag's dspr:
  C0V + 0 magic $C1D1B0 (core 1 answered)   + 1 blocks   + 2 late   + 3 corrupt   + 4 core-1 passes per block (min, since the last reset)   + 5 (last)
  C0V + 6 core-1 passes / 256   + 7 W in use   + 8 W requested (the PC writes it)   + 9 reset request (the PC writes 1: late / corrupt / min cleared)
Reversible: DSP RAM only.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp56 as D  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import probe35_dsp as P5  # noqa: E402

T, J = G.T, G.J
PREMIX = 0x87
MAGIC = 0xC1D1B0
C1MAGIC = 0xC1C1C3
SH5 = 0x37D00                                    # shared: core-1 words (the gather list ends at $30882 in SC35D2; SH3 = $37F00 was SC35D2's)
BUF0, BUF1 = 0x37C00, 0x37C40
NS = 64
SRC = 0x580000                                   # the pack's first sample (read-only load)
C0V = 0x3BE0                                     # core 0 internal X (free in this chain: SC35D4+ has no DSP probe)


def core1_code(base, sh=SH5, src=SRC):
    a = D.Asm(base)
    L = a.label
    def e(*lines):
        for l in lines: a.emit(T(l))
    CNT, FIRST, LAST, SINCE, MIN, LASTB = (sh + 16 + i for i in range(6))
    L("c1loop")
    e("move x:>$%x,a" % FIRST, "move #>$%x,x0" % P5.FIRSTM, "cmp x0,a"); a.emit(J("eq"), "c1_run")
    e("move x0,x:>$%x" % FIRST, "clr a", "move a,x:>$%x" % CNT, "move a,x:>$%x" % SINCE, "move a,x:>$%x" % (sh + 4))
    e("move #>$7fffff,x0", "move x0,x:>$%x" % MIN, "move x:>$%x,x0" % (sh + 8), "move x0,x:>$%x" % LAST, "move x0,x:>$%x" % LASTB)
    e("move #>$%x,x0" % C1MAGIC, "move x0,x:>$%x" % sh)
    L("c1_run")
    e("move x:>$%x,a" % CNT, "move #>1,x0", "add x0,a", "move a1,x:>$%x" % CNT)
    e("move x:>$%x,a" % SINCE, "add x0,a", "move a1,x:>$%x" % SINCE)
    e("move x:>$%x,b" % (sh + 8), "move x:>$%x,x1" % LAST, "cmp x1,b"); a.emit(J("eq"), "c1_same")
    e("move b1,x:>$%x" % LAST, "move a1,x:>$%x" % (sh + 2), "move x:>$%x,b" % MIN, "cmp a,b"); a.emit(J("le"), "c1_nmin")
    e("move a1,x:>$%x" % MIN, "move a1,x:>$%x" % (sh + 3))
    L("c1_nmin")
    e("clr a", "move a,x:>$%x" % SINCE)
    L("c1_same")
    # a new block b (core 0's counter) -> the load, then block b and READY
    e("move x:>$%x,b" % (sh + 8), "move x:>$%x,x1" % LASTB, "cmp x1,b"); a.emit(J("eq"), "c1_nob")
    e("move b1,x:>$%x" % LASTB)
    e("move x:>$%x,x1" % (sh + 5), "move x1,a", "tst a"); a.emit(J("eq"), "c1_noload")       # W = 0: no load (a `do` of 0 would run 65536 times)
    e("move #>$%x,r4" % src); a.emit(D.NOP)
    a.emit(lambda t: T("do #%d,$%x" % (NS, t + 1)), "c1_lo")
    a.emit(lambda t: T("do x1,$%x" % (t + 1)), "c1_li")
    e("move y:(r4)+,x0")
    L("c1_li"); e("mac y0,x0,a")
    L("c1_lo"); a.emit(D.NOP)
    L("c1_noload")
    e("move x:>$%x,b" % (sh + 8), "move #>$ff,x0", "and x0,b", "move b1,x0")                    # x0 = b & $FF
    e("move x:>$%x,a" % (sh + 8), "move #>1,x1", "and x1,a")
    e("move #>$%x,r0" % BUF0); a.emit(J("eq"), "c1_b0")
    e("move #>$%x,r0" % BUF1)
    L("c1_b0")
    e("move x0,a", "asl a", "asl a", "asl a", "asl a", "asl a", "asl a", "asl a", "asl a")        # a1 = (b & $FF) << 8 ... << 16 below
    e("asl a", "asl a", "asl a", "asl a", "asl a", "asl a", "asl a", "asl a", "move #>1,x1")
    a.emit(lambda t: T("do #%d,$%x" % (NS, t + 1)), "c1_wl")
    e("move a1,x:(r0)+")
    L("c1_wl"); e("add x1,a")
    e("move x:>$%x,x0" % (sh + 8), "move x0,x:>$%x" % (sh + 4))                                 # READY = b
    L("c1_nob")
    e("move x:>$%x,a" % CNT, "move #>$ff,x0", "and x0,a"); a.emit(J("ne"), "c1_out")
    e("move x:>$%x,a" % CNT, "lsr a", "lsr a", "lsr a", "lsr a", "lsr a", "lsr a", "lsr a", "lsr a", "move a1,x:>$%x" % (sh + 1))
    L("c1_out")
    a.emit(D.jmp(P5.C1_LOOP))
    return a.assemble()


def core0_code(base, premix, sh=SH5, v=C0V):
    a = D.Asm(base)
    L = a.label
    def e(*lines):
        for l in lines: a.emit(T(l))
    SX0, SX1, SR0 = v + 12, v + 13, v + 14
    L("pprobe")
    e("move x0,x:>$%x" % SX0, "move x1,x:>$%x" % SX1, "move r0,x:>$%x" % SR0)
    e("move x:>$%x,a" % (v + 9), "tst a"); a.emit(J("eq"), "c0_nrs")                           # reset request
    e("clr a", "move a,x:>$%x" % (v + 9), "move a,x:>$%x" % (v + 2), "move a,x:>$%x" % (v + 3), "move #>$7fffff,x0", "move x0,x:>$%x" % (sh + 16 + 4))
    L("c0_nrs")
    e("move x:>$%x,a" % sh, "move #>$%x,x0" % C1MAGIC, "cmp x0,a"); a.emit(J("ne"), "c0_count")   # core 1 not there yet: only count
    e("move #>$%x,x0" % MAGIC, "move x0,x:>$%x" % v)
    e("move x:>$%x,a" % (sh + 8), "move x:>$%x,x0" % (sh + 4), "cmp x0,a"); a.emit(J("eq"), "c0_rdy")
    e("move x:>$%x,a" % (v + 2), "move #>1,x0", "add x0,a", "move a1,x:>$%x" % (v + 2)); a.emit(J("al"), "c0_count")   # late
    L("c0_rdy")
    e("move x:>$%x,a" % (sh + 8), "move #>$ff,x0", "and x0,a", "move a1,x1")                   # x1 = b & $FF
    e("move x:>$%x,a" % (sh + 8), "move #>1,x0", "and x0,a")
    e("move #>$%x,r0" % BUF0); a.emit(J("eq"), "c0_b0")
    e("move #>$%x,r0" % BUF1)
    L("c0_b0"); a.emit(D.NOP)
    e("move x1,a", "asl a", "asl a", "asl a", "asl a", "asl a", "asl a", "asl a", "asl a", "asl a", "asl a", "asl a", "asl a", "asl a", "asl a", "asl a", "asl a")
    e("move x:(r0),x0", "cmp x0,a"); a.emit(J("ne"), "c0_bad")
    e("move #>%d,x0" % (NS - 1), "add x0,a", "move #>%d,n0" % (NS - 1)); a.emit(D.NOP)
    e("move x:(r0+n0),x0", "cmp x0,a"); a.emit(J("eq"), "c0_count")
    L("c0_bad")
    e("move x:>$%x,a" % (v + 3), "move #>1,x0", "add x0,a", "move a1,x:>$%x" % (v + 3))
    L("c0_count")
    e("move x:>$%x,a" % (v + 1), "move #>1,x0", "add x0,a", "move a1,x:>$%x" % (v + 1))
    e("move x:>$%x,a" % (sh + 8), "add x0,a", "move a1,x:>$%x" % (sh + 8))                      # the next block
    for i, src in ((4, sh + 16 + 4), (5, sh + 2), (6, sh + 1), (7, sh + 5)):
        e("move x:>$%x,x0" % src, "move x0,x:>$%x" % (v + i))
    e("move x:>$%x,x0" % (v + 8), "move x0,x:>$%x" % (sh + 5))                                  # W requested -> core 1
    e("move x:>$%x,x0" % SX0, "move x:>$%x,x1" % SX1, "move x:>$%x,r0" % SR0)
    a.emit(D.jmp(premix))
    return a.assemble()


def install_dsp(s16):
    prev = s16.dsp_code
    def wrapped(base):
        w, l = prev(base)
        w2, l2 = core0_code(base + len(w), PREMIX)
        return w + w2, {**l, **l2}
    s16.dsp_code = wrapped


def patch(img, report):
    """After building: P:$23C -> jsr pprobe (core 0); core 1's block copied to the end of the image with c1loop, P:$12A -> jmp c1loop."""
    import linein2 as L2
    BASE = 0x08010000
    dl = {k: int(v, 16) for k, v in report["sc16"]["dsp_labels"].items()}
    assert int(report["sc10"]["dsp_labels"]["premix"], 16) == PREMIX
    L2.patch_p(img, 0x23C, [0x0BF080, PREMIX], [0x0BF080, dl["pprobe"]])
    tab = 0x08029700 + 8
    old = struct.unpack_from("<I", img, tab - BASE)[0]
    o = old - BASE
    n = int.from_bytes(img[o:o + 3], "big")
    assert n == P5.C1_STOCK_WORDS and int.from_bytes(img[o + 3:o + 6], "big") == 0
    prog = [int.from_bytes(img[o + 6 + 3 * i:o + 9 + 3 * i], "big") for i in range(n)]
    assert prog[P5.C1_HOOK] == 0x0C0000 | P5.C1_LOOP, hex(prog[P5.C1_HOOK])
    w1, l1 = core1_code(n)
    assert n + len(w1) <= 0x800
    prog[P5.C1_HOOK] = 0x0C0000 | l1["c1loop"]
    blk = (n + len(w1)).to_bytes(3, "big") + b"\0\0\0" + D.to_bytes(prog + w1)
    at = (len(img) + BASE + 3) & ~3
    img += b"\xFF" * (at - BASE - len(img)) + blk
    while len(img) % 4:
        img += b"\xFF"
    struct.pack_into("<I", img, tab - BASE, at)
    return dict(core1_block=hex(at), core1_words=n + len(w1), c1loop=hex(l1["c1loop"]), old_block=hex(old))
