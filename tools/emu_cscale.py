"""SC42.2 (tools/cscale.py): the custom scale of the note tracks.

Through the controller (buttons 0x08033320 / pads 0x08033282) and the real LED task, the emulated firmware:
  * Shift + Scales opens the Scales view with the editor; the Scales LED is yellow with Shift held;
  * the editor's pads: the piano keys toggle their interval (7 at most; the root does nothing); the block in the record's tail; the LEDs (root white,
    degrees green, the period orange, free keys dim, no key off);
  * the LED task rebuilds the keyboard: the major scale made by hand (2 4 5 7 9 11 + period 12) gives the stock's three tables of its major scale,
    byte for byte; a 5-note scale with period 10 (one iteration a row + the period note, links); 2 notes + period 7 (two iterations a row, no links);
  * the quantiser 0x080408C6 on the keyboard's scale object: the nearest note of the custom scale (ties down); another object: the stock's;
  * random-mutate (c_mutscale): another degree of the same iteration;
  * a track's note view plays the table: the index of pad 0 is unchanged and its note is the custom one;
  * a stock scale picked out of the editor switches the custom scale off (keys kept) and the keyboard goes back to the stock's;
  * a project load forces a rebuild; a new project clears the block;
  * the previous build (if given): Shift + Scales does nothing.

    python tools/emu_cscale.py firmware/sc42.2/circuittracks-4486-SC42.2.bin firmware/sc42.2/manifest.json [PREVIOUS.bin]
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R4
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
import cscale as CS  # noqa: E402

MGR = T.MGR
STOCK_MAJOR = 1                                   # the stock's scale 1 = 0x1AB5 (0 2 4 5 7 9 11 12)


class EC(T.EL):
    def __init__(self, img, labels):
        super().__init__(img); self.L = labels
    def r0(self, fn, *a, maxins=8_000_000):
        self.call(fn, *a, maxins=maxins); return self.uc.reg_read(UC_ARM_REG_R0)
    def shift(self, on): self.set_p0(self.r32(MGR + 0xC), 1 if on else 0)
    def sbtn(self, i):
        self.shift(1); self.btn(i); self.shift(0)
    def frame(self, shift=False):
        if shift: self.shift(1)
        self.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); self.uc.reg_write(UC_ARM_REG_R4, MGR)
        self.call(0x08033B3E, maxins=8_000_000)
        f = list(struct.unpack("<69H", bytes(self.uc.mem_read(self.r32(self.r32(MGR + 0x90)), 138))))
        if shift: self.shift(0)
        return f
    def blk(self): return self.r32(T.LZ.SESSION_OBJ + 0x14) + CS.TAIL + CS.O_BLK
    def keys(self):
        b = self.blk(); return (self.r8(b + 6) | self.r8(b + 7) << 8 | self.r8(b + 8) << 16) << 1
    def on(self): return self.r8(self.blk() + CS.B_ON)
    def tables(self):
        return (bytes(self.uc.mem_read(CS.KB + 0x14, 224)), bytes(self.uc.mem_read(CS.KB + 0xF4, 140)), bytes(self.uc.mem_read(CS.KB + 0x180, 224)))
    def set_scale(self, k):
        st = self.r32(CS.KB + 8)
        self.call(0x080354FA, st, 1); self.uc.mem_write(self.uc.reg_read(UC_ARM_REG_R0), bytes([k])); self.call(0x080353C0, st)
    def scales_leds(self):
        return list(struct.unpack("<32H", bytes(self.uc.mem_read(self.r32(self.r32(CS.SCALES_VIEW + 4)), 64))))
    def put_keys(self, ks, on=1):
        m = sum(1 << k for k in ks); self.call(self.L["c_csput"], on, m)


def pads_of(ivals):
    """the editor's pads for these intervals (the lower octave first)"""
    out = []
    for k in ivals:
        for p in (list(range(16, 32)) + list(range(0, 16))):
            if CS.PIANO[p] == k: out.append(p); break
    return out


def model(degs, P):
    """the keyboard's tables for a custom scale, as designed"""
    n = len(degs)
    pat = [0xFF] * 8
    if n <= 4:
        for i, d in enumerate(degs): pat[i] = d; pat[4 + i] = P + d
        span = 2 * P
    else:
        for i, d in enumerate(degs): pat[i] = d
        pat[n] = P; span = P
    tab, rev, lnk = bytearray(224), bytearray([0xFF] * 140), bytearray([0xFF] * 224)
    for r in range(28):
        base = CS.ANCHOR + (CS.ANCHOR_ROW - r) * span
        for c in range(8):
            if pat[c] == 0xFF: continue
            v = base + pat[c]
            if 1 <= v <= CS.VMAX:
                tab[8 * r + c] = v
                if rev[v] == 0xFF: rev[v] = 8 * r + c
    if n > 4:
        for r in range(27):
            i, j = 8 * r, 8 * r + 8 + n
            if tab[i] and tab[j]: lnk[i] = j; lnk[j] = i
    return bytes(tab), bytes(rev), bytes(lnk)


def near(v, degs, P, lo, hi):
    m = (v - CS.ANCHOR) % P
    best, bd = 0, m
    for c in list(degs[1:]) + [P]:
        if abs(m - c) < bd: best, bd = c, abs(m - c)
    return max(lo, min(hi, v - m + best))


def main(img, man, prev=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    lab = {k: int(v, 16) for k, v in man["report"]["cscale"]["labels"].items()}
    e = EC(img, lab); e.at(100000); e.transport(0)
    stock_minor = e.tables()

    # Shift + Scales: the editor, in the Scales view; the LED with Shift
    f = e.frame(shift=True)
    check(f[CS.LED_SCALES] == CS.COL_SHIFT, f"Shift held: the Scales LED yellow ({f[CS.LED_SCALES]:#x})")
    e.sbtn(CS.ID_SCALES)
    check(e.r32(MGR + 0x6C) == CS.SCALES_VIEW and e.r8(e.blk() + CS.B_ED) == 1, "Shift + Scales: the Scales view with the editor")

    # the keys: a major scale by hand
    major = [2, 4, 5, 7, 9, 11, 12]
    for p in pads_of(major): e.pad(p)
    check(e.keys() == sum(1 << k for k in major) and e.on() == 1, f"the editor: 7 keys of a major scale pressed ({e.keys():#x})")
    e.pad(pads_of([1])[0])
    check(e.keys() == sum(1 << k for k in major), "an 8th key: refused")
    e.pad(24)
    check(e.keys() == sum(1 << k for k in major), "the root's pad: nothing")
    e.frame(); led = e.scales_leds()
    want = []
    for p in range(32):
        k = CS.PIANO[p]
        want.append(0 if k == 0xFF else CS.COL_ROOT if k == 0 else CS.COL_PER if k == 12 else CS.COL_DEG if k in major else CS.COL_FREE)
    check(led == want, f"the editor's LEDs ({[hex(x) for x in led]})")
    # the keyboard rebuilt by the LED task = the stock's major scale
    e.frame(); mine = e.tables()
    e.call(CS.KB_SLOT0, CS.KB)                                   # the stock's own builder (the vtable now points to ours)
    e.set_scale(STOCK_MAJOR); e.call(CS.KB_SLOT0, CS.KB); stock_major = e.tables()
    check(mine == stock_major, "major by hand (period 12) = the stock's major scale: the three tables byte for byte")
    check(mine != stock_minor, "(the stock's minor differs)")
    e.set_scale(0)
    e.uc.mem_write(e.blk() + CS.B_STAMP, struct.pack("<I", 0)); e.frame()
    check(e.tables() == stock_major, "a rebuild through the keyboard's slot 0 with the custom scale on = ours, whatever the stock's scale")

    # 5 notes, period 10
    degs, P = [0, 2, 3, 6, 8], 10
    e.put_keys([2, 3, 6, 8, 10]); e.frame()
    check(e.tables() == model(degs, P), "5 notes + period 10: one iteration a row with the period note; links")
    so = e.r32(CS.KB + 0xC); lo, hi = e.r8(so), e.r8(so + 1)
    bad = [(v, e.r0(CS.QUANT, so, v) & 0xFF, near(v, degs, P, lo, hi)) for v in range(0, 140) if (e.r0(CS.QUANT, so, v) & 0xFF) != near(v, degs, P, lo, hi)]
    check(not bad, f"the quantiser on the keyboard's object: the nearest custom note, ties down ({bad[:4]})")
    mutscale = int(man["report"]["mutate39"]["labels"]["c_mutscale"], 16)
    mut = [e.r0(mutscale, 63, r) for r in range(40)]
    okm = all(((m - CS.ANCHOR) % P) in degs and m != 63 and (m - 60) // P == (63 - 60) // P for m in mut)
    check(okm and len(set(mut)) == 4, f"random-mutate: another degree of the same iteration ({sorted(set(mut))})")

    # 2 notes, period 7: two iterations a row
    degs, P = [0, 3], 7
    e.put_keys([3, 7]); e.frame()
    check(e.tables() == model(degs, P), "2 notes + period 7: two iterations a row, no period note, no links")
    tv = 0x200412E0
    idx = e.r0(0x0804B174, tv, 0)
    check(idx == 56 and e.r8(CS.KB + 0x14 + 56 + 24) == model(degs, P)[0][80], f"the note view: pad 25 plays the custom table (index {idx + 24})")

    # out of the editor: a stock scale switches it off
    e.btn(CS.ID_SCALES)
    check(e.r8(e.blk() + CS.B_ED) == 0, "Scales alone: out of the editor")
    e.btn(CS.ID_SCALES); e.btn(CS.ID_SCALES) if e.r32(MGR + 0x6C) != CS.SCALES_VIEW else None
    try:
        e.pad(16 + 2)
    except Exception as ex:                                      # (the stock's scale change does not run in emulation past this point)
        print(f"      (the stock's scale pick stopped the emulation: {ex})")
    check(e.on() == 0 and e.keys() == (1 << 3 | 1 << 7), "a stock scale out of the editor: the custom scale off, the keys kept")
    gc.collect()

    # a fresh instance: load / new project
    e = EC(img, lab); e.at(100000); e.transport(0)
    e.put_keys([2, 4, 5, 7, 9, 11, 12]); e.frame(); t1 = e.tables()
    e.uc.mem_write(e.blk() + CS.B_STAMP, struct.pack("<I", 0x12345678))
    e.call(lab["c_cszero"], 0, 0, 0); stamp = e.r32(e.blk() + CS.B_STAMP)
    check(stamp == 0xFFFFFFFF and e.on() == 1, f"a load: the stamp unknown, the block kept ({stamp:#x})")
    e.frame(); check(e.tables() == t1 and e.r32(e.blk() + CS.B_STAMP) != 0xFFFFFFFF, "the LED task rebuilds after a load")
    e.call(lab["c_cszero"], 0, 0, 1); e.frame()
    check(e.r32(e.blk()) == 0 and e.tables() == stock_minor, "a new project: no block, the stock's keyboard")
    # with no custom scale, the quantiser is the stock's
    so = e.r32(CS.KB + 0xC)
    st = EC(bytearray(Path("stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()), lab) if Path("stock/circuittracks-firmware-4486-STOCK.bin").exists() else None
    if st is not None:
        st.at(100000)
        same = all((e.r0(CS.QUANT, so, v) & 0xFF) == (st.r0(CS.QUANT, so, v) & 0xFF) for v in range(0, 140, 3))
        check(same, "custom scale off: the quantiser gives the stock's notes")
    if prev is not None:
        gc.collect(); p = EC(prev, lab); p.at(100000); p.transport(0); v0 = p.r32(MGR + 0x6C)
        p.sbtn(CS.ID_SCALES)
        check(p.r32(MGR + 0x6C) == v0, "the previous build: Shift + Scales does nothing")
    return fails


if __name__ == "__main__":
    img = bytearray(Path(sys.argv[1]).read_bytes()); man = json.load(open(sys.argv[2]))
    prev = bytearray(Path(sys.argv[3]).read_bytes()) if len(sys.argv) > 3 else None
    f = main(img, man, prev)
    print(f"{man['marker']} ARM RESULT: " + ("ALL PASS" if f == 0 else f"{f} FAILURES"))
    sys.exit(1 if f else 0)
