"""SC21D (DIAGNOSTIC): the DSP probe, core 0.

Runs ONCE (a flag in X:$3BF0), from the hook P:$23C (the `jsr premix` of SC10 becomes `jsr pprobe`, which ends with `jmp premix`: same stack depth), and leaves its
findings in Y:$3B10..$3B18 for the ARM to show (tools/probe21.py):
  Y:$3B10 magic $C0FFEE (the probe ran)           Y:$3B11 OMR     Y:$3B12 SR (as found)     Y:$3B13 = Y:$3B18 (the facts)
  Y:$3B14 the word found at P:$3800                Y:$3B15 the word found at X:$030000 (shared memory)        Y:$3B16 ICPR1 (y:$FFFFD1)       Y:$3B17 ICCR1 (y:$FFFFDA)
  Y:$3B18 FACTS (the 16 pads): bit 0 ran, bits 1..8 the P-RAM tests (P:$3800, $3C00, $3FFF, $4000, $5000, $6000, $7000, $7FFF write -> read back OK),
          bit 9 P:$3800 was 0, bit 10 P:$3800 was $FFFFFF, bit 11 the shared memory word is 0, bit 12 ICPR1 != 0, bit 13 ICCR1 != 0
P-RAM test: save the word, write $5A5A5A, read back, restore it, all with the interrupts masked (a mirrored address would otherwise be hit by the audio interrupt while
it holds a wrong word); only addresses above the end of the loaded program ($3800+) are written.  Read-only everything else: no ICDR (reading it clears an inter-core
interrupt flag), no EMC, no core 1.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp56 as D  # noqa: E402
import masterfx_dsp as G  # noqa: E402

T, J = G.T, G.J
YR = 0x3B10
SAV, FLAG = 0x3BE0, 0x3BF0
PREMIX = 0x87
PTEST = (0x3800, 0x3C00, 0x3FFF, 0x4000, 0x5000, 0x6000, 0x7000, 0x7FFF)
MAGIC = 0xC0FFEE


def code(base, premix):
    a = D.Asm(base)
    L = a.label
    def e(*lines):
        for l in lines: a.emit(T(l))
    L("pprobe")
    e("move x0,x:>$%x" % SAV, "move x1,x:>$%x" % (SAV + 1), "move r0,x:>$%x" % (SAV + 2))
    e("move x:>$%x,a" % FLAG, "tst a"); a.emit(J("ne"), "pp_done")
    e("move #>1,x0", "move x0,x:>$%x" % FLAG)                                     # set first: a probe that crashes the core runs once only
    e("move #>$%x,x0" % MAGIC, "move x0,y:>$%x" % YR)
    e("move omr,x0", "move x0,y:>$%x" % (YR + 1))
    e("move sr,x0", "move x0,y:>$%x" % (YR + 2), "move x0,x:>$%x" % (SAV + 3))
    e("move y:>$ffffd1,x0", "move x0,y:>$%x" % (YR + 6))
    e("move y:>$ffffda,x0", "move x0,y:>$%x" % (YR + 7))
    e("move x:>$030000,x0", "move x0,y:>$%x" % (YR + 5))
    # facts: b = the mask
    e("move #>1,b")                                                                # bit 0: ran
    e("move y:>$%x,a" % (YR + 5), "tst a"); a.emit(J("ne"), "pp_s1"); e("or #>$800,b")                                  # bit 11: shared word is 0
    L("pp_s1")
    e("move y:>$%x,a" % (YR + 6), "tst a"); a.emit(J("eq"), "pp_s2"); e("or #>$1000,b")                                 # bit 12: ICPR1 != 0
    L("pp_s2")
    e("move y:>$%x,a" % (YR + 7), "tst a"); a.emit(J("eq"), "pp_s3"); e("or #>$2000,b")                                 # bit 13: ICCR1 != 0
    L("pp_s3")
    e("ori #3,mr")                                                                 # interrupts masked while a P address holds the test word
    for k, addr in enumerate(PTEST):
        e("move #>$%x,r0" % addr); a.emit(D.NOP)
        e("move p:(r0),x1")
        if k == 0:
            e("move x1,y:>$%x" % (YR + 4), "move x1,a", "tst a"); a.emit(J("ne"), "pp_z0"); e("or #>$200,b")             # bit 9: P:$3800 was 0
            L("pp_z0")
            e("move x1,a", "move #>$ffffff,x0", "cmp x0,a"); a.emit(J("ne"), "pp_z1"); e("or #>$400,b")                               # bit 10: P:$3800 was $FFFFFF
            L("pp_z1")
        e("move #>$5a5a5a,x0", "move x0,p:(r0)"); a.emit(D.NOP); a.emit(D.NOP)
        e("move p:(r0),a", "cmp x0,a"); a.emit(J("ne"), "pp_n%d" % k)
        e("or #>%d,b" % (2 << k))                                                  # bits 1..8
        L("pp_n%d" % k)
        e("move x1,p:(r0)"); a.emit(D.NOP); a.emit(D.NOP)                          # restore the word
    e("move x:>$%x,x0" % (SAV + 3), "move x0,sr")                                  # the status register as found (the interrupt mask)
    e("move b,y:>$%x" % (YR + 8))
    mask_k = "move b,y:>$%x" % (YR + 3)
    e(mask_k)
    L("pp_done")
    e("move x:>$%x,x0" % SAV, "move x:>$%x,x1" % (SAV + 1), "move x:>$%x,r0" % (SAV + 2))
    a.emit(D.jmp(premix))
    return a.assemble()


def install_dsp(s16):
    """Before building: the code is appended to the (wrapped) SC16 DSP code."""
    prev = s16.dsp_code
    def wrapped(base):
        w, l = prev(base)
        w2, l2 = code(base + len(w), PREMIX)
        return w + w2, {**l, **l2}
    s16.dsp_code = wrapped


def patch_dsp(img, report):
    """After building: P:$23C jsr premix -> jsr pprobe."""
    import linein2 as L2
    dl = {k: int(v, 16) for k, v in report["sc16"]["dsp_labels"].items()}
    assert int(report["sc10"]["dsp_labels"]["premix"], 16) == PREMIX
    L2.patch_p(img, 0x23C, [0x0BF080, PREMIX], [0x0BF080, dl["pprobe"]])
    assert dl["pprobe"] < 0x3800
