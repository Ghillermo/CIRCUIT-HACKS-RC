"""SC19.1 ARM tests: the synth source switch opened by pressing a Synth button a second time (tools/srcview.py), through the real controller
routes (button 0x08033320 + release 0x0803381A, pad 0x08033282) on the live RAM dump (unicorn).

    python tools/emu_sc19_1.py STOCK.bin SC19.bin SC19.1.bin SC19.1_manifest.json

Two stock waits hang here because the tasks that would end them do not run: the mailbox wait (0x080359E0, drained by the harness) and the
"busy" poll 0x08023172 (state byte 3 + ack byte, acknowledged after three polls).  The same harness is used on both sides of every comparison.
"""
from __future__ import annotations
import gc, json, random, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc19 as T19  # noqa: E402
from emu_sc08 import MGR  # noqa: E402
import build_sc15 as B15  # noqa: E402
import srcview as SV  # noqa: E402

BASE = 0x08010000
VIEWS = (0x20042980, 0x20042A34)                 # Synth 1 / Synth 2 Preset views
FLAGB = 20                                       # SC14 state byte of the flag (bit 2) and the "painted" bits (0 / 1)


class E191(T19.E19):
    def __init__(self, image, man):
        gc.collect()
        super().__init__(image, man)
        self.st = int(man["report"]["sc17"]["sc14_state"], 16)
        self.sp = []
        def h(uc, a, s, d):
            if a == B15.SP_PRESS: self.sp.append(("press", uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2)))
            elif a == B15.SP_REPAINT: self.sp.append(("repaint", uc.reg_read(UC_ARM_REG_R0)))
        self.uc.hook_add(UC_HOOK_CODE, h)
        def drain(uc, a, s, d): self.uc.mem_write(self.r32(uc.reg_read(UC_ARM_REG_R4) + 0x10), bytes(4))
        self.uc.hook_add(UC_HOOK_CODE, drain, begin=0x080359E0, end=0x080359E0)
        self.nbusy = 0
        def busy(uc, a, s, d):                                                    # 0x08023172: "busy" poll of a task that does not run here
            self.nbusy += 1
            if self.nbusy > 3: self.uc.mem_write(uc.reg_read(UC_ARM_REG_R0) + 0xC, b"\x01")       # the ack it waits for
        self.uc.hook_add(UC_HOOK_CODE, busy, begin=0x08023178, end=0x08023178)

    def btn(self, b, shift=False):
        self.nbusy = 0; super().btn(b, shift)
    def cur(self): return self.r8(MGR + 0x152)
    def trk(self): return self.store_p0(self.r32(self.r32(MGR + 0x2C) + 0x188))
    def mode(self): return self.store_p0(self.r32(MGR + 0x14))
    def flag(self): return (self.r8(self.st + FLAGB) >> 2) & 1
    def painted(self): return self.r8(self.st + FLAGB) & 3
    def modes(self): return [self.r8(self.st + B15.S_MODE), self.r8(self.st + B15.S_MODE + 1)]
    def shape(self): return (self.cur(), self.trk(), self.mode(), self.r32(MGR + 0x6C))
    def view_synth(self): return self.trk() if self.trk() in (0, 1) else 0
    def padr(self, p, vel=100, shift=False):
        self.sp.clear(); self.mark.clear()
        if shift: self.set_p0(self.r32(MGR + 0xC), 1)
        self.call(0x08033282, MGR, p, vel, maxins=900000)
        if shift: self.set_p0(self.r32(MGR + 0xC), 0)
        return list(self.sp)
    def pleds(self, v):
        self.sp.clear()
        self.call(self.r32(self.r32(v) + 0x1C), v, maxins=600000); p = self.uc.reg_read(UC_ARM_REG_R0)
        return list(struct.unpack("<32H", bytes(self.uc.mem_read(p, 64))))


def make_ref(img, man):
    """the image without the source view: the stock button handler entry and SC15's pad / LED handlers back (= SC19 behaviour, same layout as the image)"""
    r = bytearray(img)
    l15 = {k: int(v, 16) for k, v in man["report"]["sc15"]["labels"].items()}
    r[0x08033320 - BASE:0x08033324 - BASE] = bytes.fromhex("38b50446")
    struct.pack_into("<I", r, SV.SP_VT + 4 * SV.SLOT_PAD - BASE, l15["c_spad"] | 1)
    struct.pack_into("<I", r, SV.SP_VT + 4 * SV.SLOT_LEDS - BASE, l15["c_sleds"] | 1)
    return bytes(r)


def main(stock, ref, img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]
    refimg = make_ref(img, man)
    L = {k: int(v, 16) for k, v in rep["srcview"]["labels"].items()}
    vt = lambda a, i: struct.unpack_from("<I", img, a + 4 * i - BASE)[0]
    # ---- installation: exactly four places differ from SC19 (marker, the stock button handler's first 4 bytes, two view slots)
    diff = [i for i in range(len(ref)) if ref[i] != img[i]]
    regs = sorted({(BASE + i) & ~0x3 for i in diff})
    p19 = {k: int(v, 16) for k, v in rep["persist19"]["labels"].items()}
    lo, hi = (p19["c_xm_load"], p19["c_xm_save"]) if rep["persist19"].get("fix_lock") else (0, 0)       # SC19.3: the one call in c_xm_load differs
    check(rep["persist19"].get("rec_restore") or all(0x080101E8 <= a < 0x080101F0 or a == 0x08033320 or a in (0x0805AC9C, 0x0805ACB8) or lo <= a < hi for a in regs),
          f"SC19 -> SC19.1 differs only at the marker, 0x08033320, vtable slots 0 / 7{' and the call in c_xm_load (lock fix)' if hi else ''} {[hex(a) for a in regs]}")
    check(img[0x08033320 - BASE:0x08033324 - BASE] == SV.b_w(0x08033320, L["c_bentry"]) and ref[0x08033320 - BASE:0x08033324 - BASE] == bytes.fromhex("38b50446"),
          "0x08033320: push {r3, r4, r5, lr}; mov r4, r0  ->  b.w c_bentry")
    check(vt(SV.SP_VT, 0) == L["c_xpad"] | 1 and vt(SV.SP_VT, 7) == L["c_xleds"] | 1, "synth Preset view slots 0 / 7 -> c_xpad / c_xleds")
    mem = int(rep["sc17"]["sc14_state"], 16)
    check(0x20044E58 - mem == 220, f"RAM reservation unchanged: {0x20044E58 - mem} bytes")
    on0, dim0 = B15.COLORS[0]; on1, dim1 = B15.COLORS[1]
    PAD0, NM = B15.PAD0, rep["linein3"]["modes"]
    check(NM in (5, 7), f"source modes {NM}")

    # ---- Synth 1: the dump starts in Synth 1's track view -> one press = "second press"
    e = E191(img, man)
    check(e.cur() == 1 and e.trk() == 0 and not e.flag(), f"start: Synth 1 track view (index {e.cur()}), no source view")
    e.btn(0)
    check(e.cur() == 0 and e.trk() == 0 and e.flag() and e.painted() == 0, f"Synth 1 pressed in its track view: Preset view of Synth 1 + source view {e.shape()[:3]} flag {e.flag()}")
    l = e.pleds(VIEWS[0])
    check(l[:PAD0] == [0] * PAD0 and l[PAD0 + NM:] == [0] * (32 - PAD0 - NM) and l[PAD0:PAD0 + NM] == [on0] + [dim0] * (NM - 1),
          f"LEDs: pads 25-{PAD0 + NM} = noise bright, the others dim, the rest dark {[hex(x) for x in l[PAD0 - 1:PAD0 + NM + 1]]}")
    c = e.padr(3); check(c == [] and e.modes() == [0, 0] and not e.mark, f"a pad outside the five (pad 4) is swallowed: no stock press, no mode change {c}")
    c = e.padr(24 + NM); check(c == [] and e.modes() == [0, 0], "the pad right after the five (pad 30) is swallowed")
    for m in range(NM):
        c = e.padr(PAD0 + m)
        l = e.pleds(VIEWS[0])
        check(c == [] and e.modes() == [m, 0] and (0x20, 48) in e.mark, f"pad {PAD0 + m + 1}: Synth 1 mode {m}, Audio In group resent, no stock press {e.modes()}")
        check(l[PAD0:PAD0 + NM] == [on0 if i == m else dim0 for i in range(NM)], f"   LEDs follow: mode {m} bright")
    check(e.flag() and e.cur() == 0, "the view stays open while pads are used")
    # knob / other controller routes stay stock (knob 1 in the Preset view)
    # ---- closing: every button but Shift
    def closes(first, later, name):
        x = E191(img, man)
        x.btn(first[0]) if first else None
        x.btn(0) if later is not None and not first else None
        return x
    for b, name in ((8, "Preset"), (0, "Synth 1"), (1, "Synth 2"), (2, "MIDI 1"), (4, "Drum 1"), (14, "Mixer"), (15, "FX"), (13, "13 (session / patterns)"), (24, "Duplicate")):
        x = E191(img, man); x.btn(0); assert x.flag()
        x.btn(b)
        y = E191(refimg, man); y.btn(8) if b != 8 else None                  # reference (SC19 = stock behaviour): Preset view of Synth 1 open, then the same button
        y.btn(b)
        check(not x.flag() and x.shape() == y.shape(),
              f"{name} closes the source view and does what stock does: {x.shape()[:3]} vs stock {y.shape()[:3]}, flag {x.flag()}")
    # Shift alone keeps it (press of id 27 = Shift)
    x = E191(img, man); x.btn(0)
    x.call(0x08033320, MGR, 27, maxins=900000)
    check(x.flag(), "Shift (id 27) pressed: the view stays open")
    # repaint once after closing, LEDs stock again
    x = E191(img, man); x.btn(0); x.pleds(VIEWS[0]); x.btn(8)
    l1 = x.pleds(VIEWS[0]); rp = [c for c in x.sp if c[0] == "repaint"]
    l2 = x.pleds(VIEWS[0]); rp2 = [c for c in x.sp if c[0] == "repaint"]
    z = E191(refimg, man); z.btn(8); lref = z.pleds(VIEWS[0])
    check(rp == [("repaint", VIEWS[0])] and l1 == lref and not rp2 and l2 == lref, "closed: one stock repaint, LEDs back to stock, no repaint on later refreshes")
    # reopening
    x = E191(img, man); x.btn(0); x.btn(0)
    check(x.cur() == 1 and not x.flag(), f"Synth 1 pressed again while open: closes, track view {x.cur()}")
    x.btn(0)
    check(x.cur() == 0 and x.flag(), "and a further press opens it again")

    # ---- Synth 2: first press selects it (stock), the second opens the view; its colours; Synth 1 untouched
    x = E191(img, man)
    x.btn(0)
    x.padr(PAD0 + 2); x.btn(8)                                              # Synth 1 -> In 2, closed
    x.btn(1)
    check(x.cur() == 10 and x.trk() == 1 and not x.flag(), f"Synth 2 pressed once (from Synth 1's Preset view): stock, its track view {x.shape()[:3]}")
    x.btn(1)
    check(x.cur() == 9 and x.trk() == 1 and x.flag(), f"Synth 2 pressed again: Preset view of Synth 2 + source view {x.shape()[:3]}")
    l = x.pleds(VIEWS[1])
    check(l[PAD0:PAD0 + NM] == [on1] + [dim1] * (NM - 1) and l[:PAD0] == [0] * PAD0 and l[PAD0 + NM:] == [0] * (32 - PAD0 - NM), f"Synth 2 colours {[hex(v) for v in l[PAD0:PAD0 + NM]]}")
    x.padr(PAD0 + 4)
    check(x.modes() == [2, 4], f"pad 29 sets Synth 2 only: Synth 1 keeps In 2 {x.modes()}")
    x.btn(1); x.btn(1)
    l = x.pleds(VIEWS[1])
    check(x.flag() and l[PAD0:PAD0 + NM] == [dim1] * (NM - 1) + [on1], "reopened later: shows Synth 2's current mode (inverted input 2)")

    # ---- not a second press: no view, stock behaviour
    for seq, name in (([4, 0], "Drum 1, then Synth 1"), ([2, 0], "MIDI 1, then Synth 1"), ([14, 0], "Mixer, then Synth 1"), ([15, 1], "FX, then Synth 2"), ([1, 0], "Synth 2, then Synth 1")):
        x = E191(img, man); y = E191(refimg, man)
        for b in seq: x.btn(b); y.btn(b)
        check(not x.flag() and x.shape() == y.shape(), f"{name}: one press only -> stock {x.shape()[:3]}")
    x = E191(img, man); y = E191(refimg, man)
    x.btn(8); y.btn(8)                                                       # Preset view of Synth 1, normal
    x.btn(0); y.btn(0)
    check(not x.flag() and x.shape() == y.shape() and x.cur() == 1, f"Preset view -> Synth 1: back to the track view (stock) {x.shape()[:3]}")
    x = E191(img, man)
    x.btn(0, shift=True); x.btn(1, shift=True)
    check(not x.flag() and x.cur() == 1 and x.trk() == 0, "Shift + Synth 1 / Synth 2: dropped by the stock Shift mask, nothing opens")
    x = E191(img, man); x.btn(8)
    check(not x.flag() and x.cur() == 0, "Preset button: the normal Preset view")
    # Preset view without the flag = stock: pads (also Shift + 25-29), LEDs
    z = E191(refimg, man); z.btn(8); lref = z.pleds(VIEWS[0])
    for p, sh in ((3, False), (24, False), (25, True), (26, True), (28, True), (29, True), (30, True)):
        c = x.padr(p, shift=sh)
        check(c == [("press", VIEWS[0], p, 100)] and x.modes() == [0, 0] and not x.mark, f"Preset view, pad {p + 1}{' + Shift' if sh else ''}: stock press, no mode change")
    check(x.pleds(VIEWS[0]) == lref, "Preset view LEDs = stock (Shift not held and not held)")
    x.set_p0(x.r32(MGR + 0xC), 1); l = x.pleds(VIEWS[0]); x.set_p0(x.r32(MGR + 0xC), 0)
    check(l == lref, "Preset view LEDs with Shift held = stock (the old Shift + pads display is gone)")

    # ---- the mode reaches the DSP (H9) and is saved with the project (SC19)
    x = E191(img, man); x.btn(0); x.padr(PAD0 + 1); x.btn(8)
    x.dw.clear(); x.call(0x08028EA4, maxins=600000)
    check(any(B15.MODE_S1 in r and 1 in r for r in x.dw), f"Audio In group: X:$3A01 = 1 sent to the DSP {[tuple(hex(v) for v in r) for r in x.dw][-4:]}")
    x.call(int(rep["persist19"]["labels"]["c_pl_save"], 16), T19.OBJ, maxins=8_000_000)         # the hooked bl of the stock save
    check(x.xm(T19.P.XM_MODES) & 7 == 1, f"stock save: the project's mode byte carries Synth 1 = 1 ({x.xm(T19.P.XM_MODES):#x})")

    # ---- model-based battery: random button sequences (biased to repeated Synth presses) against a reference SC19 run that gets the translated
    #      press (a second Synth press = a tap on Preset), with the model of the flag: set by the second press, cleared by any button but Shift
    rnd = random.Random(1910)
    ids = [0, 0, 1, 1, 2, 4, 8, 13, 14, 15, 24]
    bad = 0; steps = 0
    for k in range(5):
        x = E191(img, man); y = E191(refimg, man)
        flag = False; log = []
        for _ in range(9):
            b = rnd.choice(ids); log.append(b)
            if flag:
                x.btn(b); y.btn(b); flag = False
            elif b in (0, 1) and y.cur() == 9 * b + 1:
                x.btn(b); y.btn(8); flag = True
            else:
                x.btn(b); y.btn(b)
            steps += 1
            if x.shape() != y.shape() or bool(x.flag()) != flag:
                bad += 1; print("   differs after", log, x.shape(), y.shape(), x.flag(), flag); break
            if flag and rnd.random() < 0.6:                          # a pad press inside the open view: modes change only for the five pads, no stock press
                pad = rnd.choice([3, 24, 25, 26, 27, 28, 30, 31]); m0 = x.modes(); s = x.view_synth()
                c = x.padr(pad)
                exp = list(m0)
                if 24 <= pad <= 24 + NM - 1: exp[s] = pad - 24
                if c != [] or x.modes() != exp: bad += 1; print("   pad", pad, "in the open view:", c, m0, x.modes(), exp); break
    check(bad == 0, f"5 random sequences of 9 buttons (+ pads): the controller state follows SC19 with the second press translated, the flag follows the model ({steps} steps)")
    print("FAILS" if fails else "ALL PASS", fails)
    return fails


if __name__ == "__main__":
    stock = Path(sys.argv[1]).read_bytes(); ref = Path(sys.argv[2]).read_bytes(); img = Path(sys.argv[3]).read_bytes()
    man = json.loads(Path(sys.argv[4]).read_text())
    sys.exit(1 if main(stock, ref, img, man) else 0)
