"""SC17.6 ARM tests: the FX view's bottom row in the Master FX view and the assignable FX slots, through the real
controller routes (button 0x08033320, pad press 0x08033282, release 0x080332FE), on the live RAM dump (unicorn).

    python tools/emu_sc17_6.py STOCK.bin SC17.5.bin SC17.6.bin SC17.6_manifest.json
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc08 import MGR  # noqa: E402
from emu_sc17_5 import EA  # noqa: E402
import build_sc17 as B  # noqa: E402
import masterfx_dsp as G  # noqa: E402

FX, MIXER = 0x200443B4, 0x200447D4
TICK = 0x2000081C
FX_PRESS, MIX_PRESS = 0x080456C0, 0x08046626
PRESS, RELEASE = 0x08033282, 0x080332FE
B.use_mixer14(); B.use_full_leds(); B.use_slots()


class ES(EA):
    def __init__(self, image, man):
        super().__init__(image)
        rep = man["report"]
        self.L = {k: int(v, 16) for k, v in rep["sc17"]["labels"].items()}
        self.blk = int(rep["sc17"]["state"], 16); self.s14 = int(rep["sc17"]["sc14_state"], 16)
        self.dw, self.pc = [], []
        def h(uc, a, s, d):
            if a == B.DSP_WRITE:
                self.dw.append((uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R1) >> 8))
                uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
            elif a in (FX_PRESS, MIX_PRESS):
                self.pc.append((a, uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)))
                uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        self.uc.hook_add(UC_HOOK_CODE, h)
        self.call(self.L["c_gfst"])                                              # create the block (c_gst + defaults)

    def pad(self, p, vel=100, shift=False):
        self.pc.clear()
        if shift: self.set_p0(self.r32(MGR + 0xC), 1)
        self.call(PRESS, MGR, p, vel, maxins=900000)
        if shift: self.set_p0(self.r32(MGR + 0xC), 0)
        return list(self.pc)
    def rel(self, p): self.call(RELEASE, MGR, p, maxins=900000)
    def blkb(self, off, n=1): return bytes(self.uc.mem_read(self.blk + off, n))
    def s14b(self, off): return self.uc.mem_read(self.s14 + off, 1)[0]
    def slot(self, j):
        b = self.blkb(B.S_SLOT + 4 * j, 4)
        if not b[3] >> 7: return None
        return (b[0] >> 7 | (b[1] >> 7) << 1 | (b[2] >> 7) << 2, [x & 0x7F for x in b])
    def knobs(self, s): return list(self.blkb(B.S_KNOB + 4 * s, 4))
    def setk(self, s, v): self.uc.mem_write(self.blk + B.S_KNOB + 4 * s, bytes(v))
    def tick(self, ms=1000):
        self.w32(TICK, ms); self.dw.clear()
        self.call(self.L["c_fxtick"], maxins=2000000)
        return {a: v for a, v in self.dw}
    def fxleds(self):
        self.call(self.r32(self.r32(FX) + 0x1C), FX, maxins=900000); p = self.uc.reg_read(UC_ARM_REG_R0)
        return list(struct.unpack("<32H", bytes(self.uc.mem_read(p, 64))))
    def gleds(self):
        self.call(self.r32(self.r32(MIXER) + 0x1C), MIXER, maxins=900000); p = self.uc.reg_read(UC_ARM_REG_R0)
        return list(struct.unpack("<42H", bytes(self.uc.mem_read(p, 84))))
    def grid(self):                                                               # Mixer -> Mixer = Master FX
        if self.view() != MIXER: self.btn(14)
        self.btn(14)


def main(stock, ref, img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]
    tabs = B.tables()
    pal = [(int(x, 16), int(y, 16)) for x, y in rep["sc17"]["pal_codes"]]
    check(int(rep["sc17"]["state"], 16) + B.GFX_SIZE == 0x20044E58 and B.GFX_SIZE == 180,
          f"memory: Master FX block {B.GFX_SIZE} bytes ends at the stock heap limit; total reservation {0x20044E58 - int(rep['sc17']['sc14_state'], 16)} bytes")
    e = ES(img, man)
    e.grid(); check(e.view() == MIXER and e.blkb(B.S_MODE)[0] == 1, "Mixer, Mixer: Master FX mode")
    # ---- bottom row in the Master FX view
    c = e.pad(25); check(c == [] and e.s14b(4) == 1 and e.s14b(6) == 1 and e.blkb(B.S_HELD)[0] == 0,
                         f"pad 26 (Gater 1/4) through the controller: SC14 effect held, no mute, no Master FX pad {c}")
    e.rel(25); check(e.s14b(4) == 0 and e.s14b(6) == 0, "pad 26 released")
    c = e.pad(24); check(c == [(FX_PRESS, FX, 24)], f"pad 25: the FX view's stock handler (FX off) {[(hex(a), hex(b), n) for a, b, n in c]}")
    e.rel(24)
    e.pad(29, shift=True); check(e.s14b(5) == 1 << 4, "Shift + pad 30 (Auto-Filter LP): latched (SC14)")
    e.pad(29, shift=True); check(e.s14b(5) == 0, "Shift + pad 30 again: unlatched")
    c = e.pad(30); e.rel(30)
    check(c == [] and e.s14b(4) == 0, f"pad 31: SC14 Auto-Filter HP pressed and released {c}")
    g, f = e.gleds(), e.fxleds()
    check(g[24:32] == f[24:32] and any(f[24:32]), "Master FX LEDs: pads 25-32 = the FX view's bottom row")
    task = lambda x: (x.call(0x08034196, MGR, 0x2006E000, maxins=900000), list(struct.unpack("<69H", bytes(x.uc.mem_read(0x2006E000, 138)))))[1]
    t = task(e); check(t[24:32] == f[24:32], "stock LED task: bottom row from Master FX")
    # pads 7-24 of the Master FX view stay unused, the Mixer's mute outside the mode
    c = e.pad(10); check(c == [], f"pad 11 in Master FX: ignored {c}")
    e.btn(14)
    check(e.blkb(B.S_MODE)[0] == 0, "Mixer again: normal Mixer")
    c = e.pad(27); check(c == [(MIX_PRESS, MIXER, 27)], f"Mixer: pad 28 = stock mute {[(hex(a), hex(b), n) for a, b, n in c]}")
    # ---- assignment: top held, then bottom
    e.grid()
    e.setk(0, [11, 22, 33, 44])
    e.pad(0); check(e.blkb(B.S_HELD)[0] == 1, "pad 1 (Gater) held")
    e.pad(27)                                                                    # bottom pad 28 = slot 2
    s = e.slot(2)
    check(s == (0, [11, 22, 33, 44]), f"top Gater held + bottom pad 28: slot 3 = Gater with a copy of its parameters {s}")
    check(e.s14b(4) == 0 and e.s14b(6) == 0, "the bottom press did not start the SC14 effect")
    e.rel(27); e.rel(0)
    check(e.blkb(B.S_HELD)[0] == 0 and e.s14b(4) == 0 and e.blkb(B.S_SLOTH)[0] == 0, "both released: nothing held")
    # ---- bottom first, then top (Digitise = effect 3 = parameter set 2)
    e.setk(2, [50, 60, 0, 0])
    e.pad(28); check(e.s14b(4) == 1 << 3, "bottom pad 29 held first: its SC14 effect runs")
    e.pad(3)
    check(e.slot(3) == (3, [50, 60, 0, 0]) and e.blkb(B.S_HELD)[0] == 0, f"then top Digitise: slot 4 = Digitise + parameters, top press swallowed {e.slot(3)}")
    e.rel(3); e.rel(28)
    check(e.s14b(4) == 0 and e.s14b(6) == 0, "released: the SC14 hold is cleared (no stuck effect)")
    check(e.slot(0) is None and e.slot(1) is None and e.slot(4) is None, "other slots untouched")
    # ---- Shift: no assignment
    e.pad(0); e.pad(26, shift=True)
    check(e.slot(1) is None and e.s14b(5) == 1 << 1, "Shift + bottom pad with a top held: SC14 latch, no assignment")
    e.pad(26, shift=True); e.rel(26); e.rel(0)
    # ---- activation of an assigned slot
    e.setk(0, [1, 2, 3, 99])
    e.pad(27)
    check(e.knobs(0) == [11, 22, 33, 44] and e.blkb(B.S_SLOTH)[0] == 1 << 2 and e.blkb(B.S_SEL)[0] == 0 and e.blkb(B.S_DIRTY)[0] == 1
          and e.s14b(4) == 0, f"slot 3 pressed: Gater parameters restored from its copy, effect selected, slot held {e.knobs(0)}")
    w = e.tick(1000)
    check(w.get(G.FX_ON) == 1 << G.B_GATE and w.get(G.G_K) == tabs["GK"][44], f"tick: FX_ON = Gater, softness from the copy {hex(w.get(G.FX_ON, -1))}")
    g = e.gleds(); check(g[27] == pal[0][0], f"slot LED bright in the Gater colour {hex(g[27])} (want {hex(pal[0][0])})")
    e.rel(27); check(e.blkb(B.S_SLOTH)[0] == 0, "released")
    w = e.tick(1001); check(w.get(G.FX_ON) == 0, f"tick: effect off again {hex(w.get(G.FX_ON, -1))}")
    g = e.gleds(); check(g[27] == pal[0][1], f"slot LED dim again {hex(g[27])}")
    e.pad(27, shift=True); e.rel(27)
    check(e.blkb(B.S_LATCH)[0] == 1 and e.blkb(B.S_SLOTH)[0] == 0, "Shift + slot: effect latched")
    w = e.tick(1002); check(w.get(G.FX_ON) == 1 << G.B_GATE, "tick: latched Gater on")
    e.pad(27, shift=True); e.rel(27); e.tick(1003)
    check(e.blkb(B.S_LATCH)[0] == 0, "Shift + slot again: unlatched")
    # slot 4 = Digitise: the parameter set 2 and its two parameters
    e.setk(2, [1, 1, 0, 0]); e.pad(28)
    check(e.knobs(2) == [50, 60, 0, 0] and e.blkb(B.S_SEL)[0] == 3, f"slot 4 pressed: Digitise parameters restored {e.knobs(2)}")
    w = e.tick(1004); check(w.get(G.FX_ON) == 1 << G.B_DIG and w.get(G.DG_N) == tabs["DGN"][50], f"tick: Digitise with the copy {hex(w.get(G.FX_ON, -1))}")
    e.rel(28)
    # ---- the slots in the FX view
    e.tick(1005)
    e.btn(15); check(e.view() == FX, "FX view")
    c = e.pad(27)
    check(c == [] and e.blkb(B.S_SLOTH)[0] == 1 << 2, "FX view: assigned slot pressed through the controller")
    w = e.tick(2000); check(w.get(G.FX_ON) == 1 << G.B_GATE, f"FX view tick: the held slot is not dropped {hex(w.get(G.FX_ON, -1))}")
    f = e.fxleds(); check(f[27] == pal[0][0], "FX view LED of the slot: bright")
    e.rel(27); w = e.tick(2001); check(w.get(G.FX_ON) == 0, "released: effect off")
    f = e.fxleds(); check(f[27] == pal[0][1], "FX view LED of the slot: dim again")
    c = e.pad(26); check(c == [] and e.s14b(4) == 1 << 1, "FX view: an unassigned pad is still the SC14 effect")
    e.rel(26)
    # leaving the views drops a held slot
    e.pad(27); e.btn(14)
    e.tick(3000); check(e.blkb(B.S_SLOTH)[0] == 0 and e.view() == MIXER, "held slot dropped when leaving to the normal Mixer")
    e.btn(13); e.uc.mem_write(e.blk + B.S_SLOTH, bytes([4]))
    e.tick(3001); check(e.blkb(B.S_SLOTH)[0] == 0, "held slot in another view: dropped by the tick")
    print("SC17.6 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    st, rf, im = (Path(sys.argv[i]).read_bytes() for i in (1, 2, 3))
    sys.exit(1 if main(st, rf, im, json.loads(Path(sys.argv[4]).read_text())) else 0)
