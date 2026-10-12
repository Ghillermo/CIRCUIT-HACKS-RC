"""SC13 ARM tests: drum side-chain pages in the Side Chain view, DSP parameter / trigger writes."""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc08 import E8, MGR, CONT  # noqa: E402
import build_sc13 as B  # noqa: E402

V = 0x20042BB8                       # Side Chain view
ST = B.ST


class E13(E8):
    def __init__(self, image):
        super().__init__(image)
        self.dw = []
        def h(uc, a, s, d):
            if a == 0x080292F8:      # DSP write: log and return (waits on hardware otherwise)
                self.dw.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2)))
                uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        self.uc.hook_add(UC_HOOK_CODE, h)

    def btn(self, b, shift=False):
        if shift: self.set_p0(self.r32(MGR + 0xC), 1)
        self.call(0x08033320, MGR, b, maxins=600000)
        if shift: self.set_p0(self.r32(MGR + 0xC), 0)

    def pad(self, p):
        marks = []
        hk = self.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: marks.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1))) if a == 0x0803BDCC else None)
        self.call(0x08033282, MGR, p, 100, maxins=600000); self.call(0x080332CE, MGR, p, maxins=600000)
        self.uc.hook_del(hk)
        return marks

    def page(self):
        return self.store_p0(self.r32(V + 0x20))

    def st(self):
        b = bytes(self.uc.mem_read(ST, 16))
        return dict(magic=struct.unpack_from("<I", b)[0], preset=list(b[4:8]), src=list(b[8:12]), dpage=b[12], chosen=b[13])

    def leds(self):
        fn = self.r32(self.r32(V) + 0x1C)
        self.call(fn, V); p = self.uc.reg_read(UC_ARM_REG_R0)
        return list(struct.unpack("<32H", bytes(self.uc.mem_read(p, 64))))

    def pager_leds(self):
        pg = self.r32(CONT + 0x144)
        buf = self.r32(self.r32(pg + 4))
        return list(struct.unpack("<2H", bytes(self.uc.mem_read(buf, 4))))


def main(stock, img, labels):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    PAL = [struct.unpack_from("<H", stock, B.PAL - 0x08010000 + 2 * i)[0] for i in range(0x140)]
    ON, OFF = PAL[0x12D], PAL[0x12E]          # pager buffer = [down, up]

    e = E13(img)
    check(e.st()["magic"] != B.MAGIC, "RAM state starts as garbage in the dump")
    e.btn(15, shift=True)                                       # Shift + FX -> Side Chain view (synth track selected)
    s = e.st()
    check(e.r8(CONT + 0x18C) == 7 and s["magic"] == B.MAGIC and s["preset"] == [0] * 4 and s["src"] == [0] * 4 and s["dpage"] == 0,
          f"enter Side Chain view: state initialised {s}")
    es = E13(stock); es.btn(15, shift=True)
    check(e.leds() == es.leds() and e.page() == es.page() == 0, "page Synth: LEDs as stock")
    # stock pages behave as stock
    for p in (18, 25, 5, 16):
        e.pad(p); es.pad(p)
    check(e.leds() == es.leds(), "page Synth: pads 18/25/5/16 -> LEDs as stock")
    seq = []
    for b in (19, 19, 19, 19, 20, 20, 20, 20, 19):
        e.btn(b)
        if b == 19 and len(seq) == 0:
            es.btn(19); check(e.leds() == es.leds() and e.page() == 1, "down: page MIDI as stock")
        st = e.st(); seq.append((e.page(), st["dpage"], st["chosen"], e.pager_leds()))
    exp = [(1, 0, 0, [ON, ON]), (1, 2, 0, [ON, ON]), (1, 3, 2, [OFF, ON]), (1, 3, 2, [OFF, ON]),
           (1, 2, 0, [ON, ON]), (1, 0, 0, [ON, ON]), (0, 0, 0, [ON, OFF]), (0, 0, 0, [ON, OFF]), (1, 0, 0, [ON, ON])]
    check(seq == exp, f"down/up: Synth -> MIDI -> Drums 1-2 -> Drums 3-4 (stop) -> back; pager LEDs {seq}")
    check(all(x in (0, 1) for x, *_ in seq), "page store only ever 0 / 1")

    # drum pages: pads
    e.btn(19)                                                   # MIDI -> Drums 1-2
    check(e.st()["dpage"] == 2, "on Drums 1-2")
    m = e.pad(18)
    s = e.st(); check(s["preset"][0] == 2 and s["chosen"] == 0 and (0x20, 26) in m, f"pad 18: drum 1 preset 2, chosen, group marked {m}")
    m = e.pad(27)
    s = e.st(); check(s["preset"][1] == 3 and s["chosen"] == 1, f"pad 27: drum 2 preset 3, chosen")
    e.pad(6)
    s = e.st(); check(s["src"] == [0, 2, 0, 0], f"pad 6 (top row 7): drum 2 triggered by drum 3 {s['src']}")
    for p in (0, 3, 8, 15):
        m = e.pad(p); check(m == [] and e.st() == s, f"pad {p}: ignored on drum pages")
    L = e.leds()
    expL = [0] * 32
    for i in range(4): expL[4 + i] = PAL[5 + 1] if i == 2 else PAL[0x13]
    for r, k in ((0, 0), (1, 1)):
        p = s["preset"][k]
        expL[16 + 8 * r] = PAL[0x19] if p == 0 else PAL[0x46]
        for c in range(1, 8): expL[16 + 8 * r + c] = PAL[5 + k] if c == p else PAL[0xD + k]
    check(L == expL, "Drums 1-2 LEDs: OFF/presets in drum colours, trigger pad of drum 2")
    e.btn(19)                                                   # Drums 3-4
    e.pad(16); e.pad(31); e.pad(7)
    s = e.st(); check(s["preset"] == [2, 3, 0, 7] and s["src"] == [0, 2, 0, 3] and s["chosen"] == 3, f"Drums 3-4: drum 4 preset 7 trigger drum 4 {s}")
    L = e.leds(); check(L[16] == PAL[0x19] and L[24] == PAL[0x46] and L[31] == PAL[5 + 3] and L[7] == PAL[5 + 3], "Drums 3-4 LEDs")

    # DSP parameters (group 5 handler): stock writes first, then 4 x 5 drum words
    es = E13(stock); es.btn(15, shift=True); es.pad(18)        # stock Synth 1 preset 2 for reference conversions
    gs = es.r32(B.GROUP_TAB + 5 * 4); es.dw.clear(); es.call(gs, maxins=600000)
    ref = {r2: r1 for _, r1, r2 in es.dw}
    gp = e.r32(B.GROUP_TAB + 5 * 4); e.dw.clear(); e.call(gp, maxins=900000)
    stock_part = e.dw[:len(es.dw)]
    drum = e.dw[len(es.dw):]
    # same Synth 1 state in both? (only compare addresses/order of the stock part)
    check([x[2] for x in stock_part] == [x[2] for x in es.dw], "group 5: stock writes unchanged")
    check([x[2] for x in drum] == [0xEC + 9 * k + i for k in range(4) for i in (1, 2, 3, 4)] and all(x[0] == 0 for x in drum),
          f"group 5: then attack/hold/decay/depth of the 4 drum blocks (X:$ED..)")
    d0 = {x[2]: x[1] for x in drum}
    check([d0[0xED + i] for i in range(4)] == [ref[0x3F3], ref[0x3F4], ref[0x3F5], ref[0x3F6]],
          "drum 1 preset 2 values = stock Synth 1 preset 2 values")
    check(d0[0xEC + 9 * 2 + 4] == 0 and d0[0xEC + 9 * 3 + 4] == 127 << 24, "drum 3 OFF -> depth 0, drum 4 preset 7 -> depth 127")

    # triggers: drum d hit -> stock writes + block word 0 = 1 for each enabled target triggered by d
    for d, targets in ((0, [0]), (2, [1]), (3, [3]), (1, [])):
        e.dw.clear(); es.dw.clear()
        e.call(0x08051B54, d, 100, maxins=100000); es.call(0x08051B54, d, 100, maxins=100000)
        extra = e.dw[len(es.dw):]
        check(e.dw[:len(es.dw)] == es.dw and extra == [(0, 0x100, 0xEC + 9 * k) for k in targets],
              f"drum {d+1} hit: stock writes {[(hex(a), hex(b)) for _, a, b in es.dw]} + trigger blocks {targets}")

    # entering the view with a drum selected opens its page
    e = E13(img)
    e.btn(6); e.btn(15, shift=True)
    s = e.st(); check(s["dpage"] == 3 and s["chosen"] == 2, f"drum 3 selected + Shift+FX -> Drums 3-4, drum 3 chosen {s['dpage'], s['chosen']}")
    e.btn(0); e.btn(15, shift=True)
    s = e.st(); check(s["dpage"] == 0, "synth selected + Shift+FX -> stock pages")
    e.btn(5); e.btn(15, shift=True)
    s = e.st(); check(s["dpage"] == 2 and s["chosen"] == 1, "drum 2 selected -> Drums 1-2, drum 2 chosen")
    # other views unaffected: pad presses in other modes as stock
    for b in (12, 15):
        e1, e2 = E13(img), E13(stock)
        for x in (e1, e2): x.btn(b)
        for p in (0, 9, 18, 27):
            m1, m2 = e1.pad(p), e2.pad(p)
            check(m1 == m2 and e1.dw == e2.dw, f"button {b} view, pad {p}: as stock")
    print("SC13 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    man = json.loads(Path(sys.argv[3]).read_text())
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes(), man["report"]["sc13"]["labels"]) else 0)
