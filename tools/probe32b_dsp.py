"""SC32D.1 (DIAGNOSTIC): raw words of external Y memory accesses, core 0.  SC32D said: zone 0 (Y:$100000) writes and reads back (static content, not a live
delay line), every other zone and the addresses past the stock map do not read back.  This probe records what actually happens, once, NWAIT calls after power-up
(the stock memory set-up is done by then), from the same hook P:$23C (`jsr pprobe` ... `jmp premix`):
  R+0  SR at the hook                 R+1  OMR                        R+2  M0
  R+3  r0 after `move #>$128800,r0` (zone 1: does the address register keep 24 bits?)
  R+4  zone 1 word found (y:(r0))      R+5  read back right after writing PAT1 through r0      R+6  the same word read with an absolute address (y:>$128800)
  R+7  read back through r0 after ~1000 cycles (a posted / buffered write?)
  R+8  read back (absolute) after writing PAT2 with an absolute address
  R+9  zone 0 ($100000) read back after writing PAT0        R+10 Y:$000000 (internal) right then: PAT0 = zone 0 is the internal RAM
  R+11 zone 14 ($337000, samples) word found                R+12 its read back after writing PAT14
Every written word is restored at once; the interrupts are masked from the first write to the last restore.  Y:R-1 = MAGIC when done.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp56 as D  # noqa: E402
import masterfx_dsp as G  # noqa: E402

T, J = G.T, G.J
PREMIX = 0x87
YM = 0x3B10                                      # Y: MAGIC, then the 13 result words
R = YM + 1
NW = 13
MAGIC = 0xC0FFEE
SAV, CNT, FLAG = 0x3BE0, 0x3BF1, 0x3BF0          # X
NWAIT = 4000
Z0, Z1, Z14 = 0x100000, 0x128800, 0x100000 + 14 * 0x28800
PAT0, PAT1, PAT2, PAT14 = 0x5A5A00, 0x5A5A01, 0x5A5A11, 0x5A5A0E
NAMES = ["SR", "OMR", "M0", "r0 = $128800?", "zona 1: encontrada", "zona 1: releída (r0)", "zona 1: releída (absoluta)", "zona 1: releída tras ~1000 ciclos",
         "zona 1: escrita y releída con dirección absoluta", "zona 0: releída", "Y:$000000 interna", "zona 14: encontrada", "zona 14: releída"]


def code(base, premix, z0=Z0, z1=Z1, z14=Z14, internal=0, nwait=NWAIT):
    """z0 / z1 / z14 / internal / nwait are parameters for the emulation test (the interpreter has 512 K words)."""
    a = D.Asm(base)
    L = a.label
    def e(*lines):
        for l in lines: a.emit(T(l))
    def res(i, src="a"): e("move %s,y:>$%x" % (src, R + i))
    L("pprobe")
    e("move x0,x:>$%x" % SAV, "move x1,x:>$%x" % (SAV + 1), "move r0,x:>$%x" % (SAV + 2), "move sr,x0", "move x0,x:>$%x" % (SAV + 3))
    e("move x:>$%x,a" % FLAG, "tst a"); a.emit(J("ne"), "pb_out")
    e("move x:>$%x,a" % CNT, "move #>1,x0", "add x0,a", "move a1,x:>$%x" % CNT, "move #>%d,x0" % nwait, "cmp x0,a"); a.emit(J("lt"), "pb_out")
    e("move #>1,x0", "move x0,x:>$%x" % FLAG)                                      # once (also if it crashed half way)
    e("move x:>$%x,x0" % (SAV + 3)); res(0, "x0")
    e("move omr,x0"); res(1, "x0")
    e("move m0,x0"); res(2, "x0")
    e("ori #3,mr")
    e("move #>$%x,r0" % z1); a.emit(D.NOP)
    e("move r0,x0"); res(3, "x0")
    e("move y:(r0),x1"); res(4, "x1")                                              # x1 = zone 1 word found
    e("move #>$%x,x0" % PAT1, "move x0,y:(r0)"); a.emit(D.NOP); a.emit(D.NOP)
    e("move y:(r0),a"); res(5)
    e("move y:>$%x,a" % z1); res(6)
    e("rep #1000"); a.emit(D.NOP)
    e("move y:(r0),a"); res(7)
    e("move x1,y:(r0)"); a.emit(D.NOP); a.emit(D.NOP)                             # restored
    e("move #>$%x,x0" % PAT2, "move x0,y:>$%x" % z1); a.emit(D.NOP); a.emit(D.NOP)
    e("move y:>$%x,a" % z1); res(8)
    e("move x1,y:>$%x" % z1); a.emit(D.NOP); a.emit(D.NOP)                        # restored
    e("move #>$%x,r0" % z0); a.emit(D.NOP)
    e("move y:(r0),x1", "move #>$%x,x0" % PAT0, "move x0,y:(r0)"); a.emit(D.NOP); a.emit(D.NOP)
    e("move y:(r0),a"); res(9)
    e("move y:>$%x,a" % internal); res(10)
    e("move x1,y:(r0)"); a.emit(D.NOP); a.emit(D.NOP)                             # restored
    e("move #>$%x,r0" % z14); a.emit(D.NOP)
    e("move y:(r0),x1"); res(11, "x1")
    e("move #>$%x,x0" % PAT14, "move x0,y:(r0)"); a.emit(D.NOP); a.emit(D.NOP)
    e("move y:(r0),a"); res(12)
    e("move x1,y:(r0)"); a.emit(D.NOP); a.emit(D.NOP)                             # restored
    e("move x:>$%x,x0" % (SAV + 3), "move x0,sr")                                  # the interrupt mask as found
    e("move #>$%x,x0" % MAGIC, "move x0,y:>$%x" % YM)
    L("pb_out")
    e("move x:>$%x,x0" % SAV, "move x:>$%x,x1" % (SAV + 1), "move x:>$%x,r0" % (SAV + 2))
    a.emit(D.jmp(premix))
    return a.assemble()


def install_dsp(s16):
    prev = s16.dsp_code
    def wrapped(base):
        w, l = prev(base)
        w2, l2 = code(base + len(w), PREMIX)
        return w + w2, {**l, **l2}
    s16.dsp_code = wrapped


def patch_dsp(img, report):
    import linein2 as L2
    dl = {k: int(v, 16) for k, v in report["sc16"]["dsp_labels"].items()}
    assert int(report["sc10"]["dsp_labels"]["premix"], 16) == PREMIX
    L2.patch_p(img, 0x23C, [0x0BF080, PREMIX], [0x0BF080, dl["pprobe"]])
    assert dl["pb_out"] < 0x3800
