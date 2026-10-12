"""SC20D ARM tests: the capture meter on the SC19.1 source view (tools/meter20.py), on the live RAM dump (unicorn).

    python tools/emu_sc20d.py STOCK.bin SC19.1.bin SC20D.bin SC20D_manifest.json SC19.1_manifest.json

Real routes: the controller button (0x08033320) opens the source view (second Synth press), the DSP service tick (SVC hook 0x080213AA ->
c_dtick20 -> c_dtick19 -> SC17's chain) does the DSP reads (the stock read 0x08029344 is stubbed with scripted words) and paints the bars, and the LED slot
(view slot 7) repaints the pads.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc19_1 as T  # noqa: E402
from emu_sc08 import MGR  # noqa: E402
import build_sc15 as B15  # noqa: E402
import meter20 as M  # noqa: E402
import build_sc14 as s14  # noqa: E402
import drums18  # noqa: E402

BASE = 0x08010000
VIEWS = M.VIEWS


class E20(T.E191):
    def __init__(self, image, man):
        super().__init__(image, man)
        self.m20 = {k: int(v, 16) for k, v in man["report"]["meter20"]["labels"].items()}
        self.read_map, self.reads = {}, []
        def h(uc, a, s, d):
            ad = uc.reg_read(UC_ARM_REG_R1)
            self.reads.append((uc.reg_read(UC_ARM_REG_R0), ad))
            uc.reg_write(UC_ARM_REG_R0, (self.read_map.get(ad, 0) << 8) & 0xFFFFFFFF)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        self.uc.hook_add(UC_HOOK_CODE, h, begin=M.DSP_READ, end=M.DSP_READ)

    def tick20(self):
        self.reads.clear(); self.chain.clear(); self.dw.clear()
        self.call(self.m20["c_dtick20"], maxins=3_000_000)
        return list(self.reads)
    def buf(self, v): return self.r32(self.r32(v + 4))
    def row(self, v, first, n):
        return list(struct.unpack(f"<{n}H", bytes(self.uc.mem_read(self.buf(v) + 2 * first, 2 * n))))
    def allpads(self, v): return self.row(v, 0, 32)
    def set_words(self, delay, reverb, magic=0x5A3C69):
        self.read_map = {0x8000 | 0x3B00: delay, 0x8000 | 0x3B01: reverb, 0x8000 | 0x3B02: magic}


def thr(k): return 1 << (6 + 2 * k)            # value thresholds (24-bit)


def main(stock, ref, img, man, refman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]
    L = {k: int(v, 16) for k, v in rep["meter20"]["labels"].items()}
    p19 = {k: int(v, 16) for k, v in rep["persist19"]["labels"].items()}
    # ---- installation
    check(drums18.decode_bw(bytearray(img), s14.SVC_HOOK) == L["c_dtick20"], "DSP service chain head -> c_dtick20 (then SC19's c_dtick19)")
    NM = rep["linein3"]["modes"]
    check(NM == 7 and rep["linein3"]["meter"] == ["0x3b00", "0x3b01"], f"manifest: {NM} modes, meter words {rep['linein3']['meter']}")
    PAD0 = B15.PAD0
    e = E20(img, man)
    on0, dim0 = B15.COLORS[0]
    # ---- closed: nothing is read, nothing is written
    snap = [e.allpads(v) for v in VIEWS]
    r = e.tick20()
    check(r == [] and [e.allpads(v) for v in VIEWS] == snap and len(e.chain) == 1, f"source view closed: no DSP read, LED buffers untouched, the chain goes on ({len(e.chain)} svc_next)")
    # ---- open it (second press of Synth 1)
    e.btn(0)
    check(e.flag() and e.cur() == 0, "source view open")
    lp = e.pleds(VIEWS[0])
    check(lp[8:24] == [0] * 16 and lp[PAD0:PAD0 + NM] == [on0] + [dim0] * (NM - 1) and lp[:8] == [0] * 8 and lp[PAD0 + NM:] == [0] * (32 - PAD0 - NM),
          f"first paint: rows 2 / 3 dark, pads 25-31 = noise bright, 6 modes dim ({NM} pads)")
    # ---- levels
    def levels(nd, nr, magic=0x5A3C69):
        d = 0 if nd == 0 else thr(nd - 1)
        r_ = 0 if nr == 0 else thr(nr - 1)
        e.set_words(d, r_, magic)
        reads = e.tick20()
        return reads
    reads = levels(3, 5)
    check(reads == [(0, 0xBB00), (0, 0xBB01), (0, 0xBB02)] and len(e.chain) == 1, f"one tick = three DSP reads (delay, reverb, check) {[hex(a) for _, a in reads]}, then the chain")
    for v in VIEWS:
        check(e.row(v, 8, 8) == [M.COL_DELAY] * 3 + [0] * 5 and e.row(v, 16, 8) == [M.COL_REVERB] * 5 + [0] * 3,
              f"view {v:#x}: delay row 3 pads, reverb row 5 pads {e.row(v, 8, 8)} {e.row(v, 16, 8)}")
    bad = 0
    for nd in range(9):
        for nr in (0, nd, 8 - nd):
            levels(nd, nr)
            if e.row(VIEWS[0], 8, 8) != [M.COL_DELAY] * nd + [0] * (8 - nd) or e.row(VIEWS[1], 16, 8) != [M.COL_REVERB] * nr + [0] * (8 - nr): bad += 1
    check(bad == 0, "every pair of levels 0..8 paints the right number of pads on both views")
    # thresholds: just below / at each one
    bad = 0
    for k in range(8):
        for val, lit in ((thr(k) - 1, k), (thr(k), k + 1)):
            e.set_words(val, val); e.tick20()
            if e.row(VIEWS[0], 8, 8).count(M.COL_DELAY) != lit or e.row(VIEWS[0], 16, 8).count(M.COL_REVERB) != lit: bad += 1
    e.set_words(0x7FFFFF, 0x7FFFFF); e.tick20()
    check(bad == 0 and e.row(VIEWS[0], 8, 8) == [M.COL_DELAY] * 8, "thresholds 2^(6 + 2 k): one below = k pads, at it = k + 1 pads; full scale = 8")
    # ---- the LED slot keeps rows 2 / 3, repaints rows 1 / 4
    levels(2, 4)
    e.uc.mem_write(e.buf(VIEWS[0]), struct.pack("<8H", *([0x77] * 8)))          # stock scribbles over rows 1 and 4
    e.uc.mem_write(e.buf(VIEWS[0]) + 48, struct.pack("<16H", *([0x77] * 16)))
    lp = e.pleds(VIEWS[0])
    check(lp[8:16] == [M.COL_DELAY] * 2 + [0] * 6 and lp[16:24] == [M.COL_REVERB] * 4 + [0] * 4,
          f"LED slot keeps the meter rows {lp[8:24]}")
    check(lp[:8] == [0] * 8 and lp[PAD0 + NM:] == [0] * (32 - PAD0 - NM) and lp[PAD0] == on0, "... and repaints rows 1 and 4 (pads 25-31 = modes)")
    # ---- check constant failing: both rows red
    levels(3, 3, magic=0x123456)
    check(e.row(VIEWS[0], 8, 8) == [M.COL_BAD] * 8 and e.row(VIEWS[0], 16, 8) == [M.COL_BAD] * 8, "check constant does not read back: both rows red")
    levels(3, 3)
    check(e.row(VIEWS[0], 8, 8)[:4] == [M.COL_DELAY] * 3 + [0], "... and normal again when it does")
    # ---- guard on the view vtable
    e.uc.mem_write(VIEWS[1], struct.pack("<I", 0x1234))
    levels(1, 1)
    check(e.row(VIEWS[0], 8, 1) == [M.COL_DELAY], "a view whose vtable is not the synth Preset view is left alone (the other one is still painted)")
    e.uc.mem_write(VIEWS[1], struct.pack("<I", B15.SP_VT if hasattr(B15, 'SP_VT') else M.SP_VT))
    # ---- modes 5 / 6 on pads 30 / 31 of the source view
    for k, pad in ((5, PAD0 + 5), (6, PAD0 + 6)):
        c = e.padr(pad)
        check(c == [] and e.modes()[0] == k and (0x20, 48) in e.mark, f"pad {pad + 1}: Synth 1 mode {k}, Audio In group resent, no stock press")
    e.dw.clear(); e.call(0x08028EA4, maxins=600000)
    check(any(B15.MODE_S1 in r and 6 in r for r in e.dw), "H9 sends X:$3A01 = 6 to the DSP")
    e.padr(PAD0 + 7)
    check(e.modes()[0] == 6, "pad 32 (after the seven mode pads) is swallowed")
    # ---- close: stock repaint, no more reads
    e.btn(8)
    e.pleds(VIEWS[0])
    r = e.tick20()
    z = T.E191(ref, refman); z.btn(8); lref = z.pleds(VIEWS[0])
    check(not e.flag() and r == [] and e.pleds(VIEWS[0]) == lref, "closed again: no DSP read, stock LEDs back")
    # ---- synth 2
    x = E20(img, man)
    x.btn(1); x.btn(1)
    x.pleds(VIEWS[1])                                                          # first paint (clears the buffer), then the tick paints the bars
    x.set_words(thr(0), thr(7)); x.tick20()
    lp = x.pleds(VIEWS[1])
    check(lp[8] == M.COL_DELAY and lp[9] == 0 and lp[16:24] == [M.COL_REVERB] * 8 and lp[PAD0] == B15.COLORS[1][0],
          "Synth 2: same meter rows, Synth 2 colours on the mode pads")
    print("SC20D ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    stock = Path(sys.argv[1]).read_bytes(); ref = Path(sys.argv[2]).read_bytes(); img = Path(sys.argv[3]).read_bytes()
    man = json.loads(Path(sys.argv[4]).read_text()); refman = json.loads(Path(sys.argv[5]).read_text())
    sys.exit(1 if main(stock, ref, img, man, refman) else 0)
