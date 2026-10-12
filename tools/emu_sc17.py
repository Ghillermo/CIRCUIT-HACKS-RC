"""SC17 ARM tests: Mixer double press -> Master FX view, pads / latch / knobs / LEDs, DSP parameter tick.

    python tools/emu_sc17.py STOCK.bin SC17.bin SC17_manifest.json
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc08 import E8, MGR  # noqa: E402
import build_sc17 as B  # noqa: E402
import masterfx_dsp as G  # noqa: E402

MIXV = 0x200441A8                         # view 1 (SC17-SC17.2; not the Mixer)
MIXV2 = 0x200447D4                        # view 2 = the real Mixer (SC17.3+)
TICK = 0x2000081C


class E17(E8):
    def __init__(self, image, labels):
        super().__init__(image)
        self.L = labels; self.dw = []; self.calls = []
        def h(uc, a, s, d):
            if a == B.DSP_WRITE:
                self.dw.append((uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R1) >> 8))
                uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
            elif a in (B.MIX_PRESS, B.MIX_REL, B.MIX_KNOB, B.BTN13_SHIFT, 0x08045D5A):
                self.calls.append(hex(a))
                if a in (B.MIX_PRESS, B.MIX_REL, B.MIX_KNOB):
                    uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
            elif a == labels["c_gtick"] if "c_gtick" in labels else False:
                pass
        self.uc.hook_add(UC_HOOK_CODE, h)
        def delay(uc, a, s, d):                      # 0x0801BE78 sleep(ms): the emulated clock never advances
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        self.uc.hook_add(UC_HOOK_CODE, delay, begin=0x0801BE78, end=0x0801BE78)

    def btn(self, b, shift=False):
        if shift: self.set_p0(self.r32(MGR + 0xC), 1)
        self.call(0x08033320, MGR, b, maxins=900000)
        self.call(0x0803381A, MGR, b, maxins=900000)                         # button release
        if shift: self.set_p0(self.r32(MGR + 0xC), 0)

    def view(self): return 1 if self.r32(self.r32(MGR + B.CTRL_VIEW)) == B.MIX_VT else 0
    def st(self):
        a = self.state
        b = bytes(self.uc.mem_read(a, B.GFX_SIZE))
        return dict(mode=b[B.S_MODE], held=b[B.S_HELD], latch=b[B.S_LATCH], sel=b[B.S_SEL],
                    knobs=[list(b[B.S_KNOB + 4 * s:B.S_KNOB + 4 * s + 4]) for s in range(5)], dirty=b[B.S_DIRTY])
    def vcall(self, slot, *args, shift=False):
        self.calls.clear()
        if shift: self.set_p0(self.r32(MGR + 0xC), 1)
        mv = MIXV2 if B.ENTRY == "mixer14" else MIXV
        self.call(self.r32(self.r32(mv) + 4 * slot), mv, *args, maxins=900000)
        if shift: self.set_p0(self.r32(MGR + 0xC), 0)
        return self.uc.reg_read(UC_ARM_REG_R0)
    def leds(self):
        p = self.vcall(7); return list(struct.unpack("<32H", bytes(self.uc.mem_read(p, 64))))
    def tick(self, ms):
        self.w32(TICK, ms); self.dw.clear()
        self.call(self.L["c_fxtick"], maxins=2000000)
        return {a: v for a, v in self.dw}


def main(stock, img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    if man["marker"] in ("SC17.3", "SC173D", "SC17.4", "SC174D", "SC17.5", "SC17.6", "SC17.7", "SC17.8", "SC18", "SC18.1", "SC18.2", "SC18.3", "SC19", "SC19.1", "SC19.2", "SC19.3", "SC19.4", "SC20D", "SC20D.1", "SC19.5", "SC19.6", "SC19.7", "SC19.8", "SC19.9", "SC20", "SC20.1", "SC20.2", "SC21", "SC21.1", "SC21.2", "SC21.3", "SC21.4", "SC22", "SC22.1", "SC22.2", "SC22.3", "SC22.4", "SC23", "SC23.1", "SC23.2", "SC23.3", "SC23.4", "SC23.5", "SC23.6", "SC24", "SC25", "SC26", "SC27", "SC28", "SC29", "SC30", "SC31", "SC32", "SC33", "SC34"): B.use_mixer14()
    if man["marker"] in ("SC17.4", "SC174D", "SC17.5", "SC17.6", "SC17.7", "SC17.8", "SC18", "SC18.1", "SC18.2", "SC18.3", "SC19", "SC19.1", "SC19.2", "SC19.3", "SC19.4", "SC20D", "SC20D.1", "SC19.5", "SC19.6", "SC19.7", "SC19.8", "SC19.9", "SC20", "SC20.1", "SC20.2", "SC21", "SC21.1", "SC21.2", "SC21.3", "SC21.4", "SC22", "SC22.1", "SC22.2", "SC22.3", "SC22.4", "SC23", "SC23.1", "SC23.2", "SC23.3", "SC23.4", "SC23.5", "SC23.6", "SC24", "SC25", "SC26", "SC27", "SC28", "SC29", "SC30", "SC31", "SC32", "SC33", "SC34"): B.use_full_leds()
    else: B.ENTRY = "shift" if man["marker"] in ("SC17.2", "SC17D") else "double"
    if man["marker"] in ("SC17.6", "SC17.7", "SC17.8", "SC18", "SC18.1", "SC18.2", "SC18.3", "SC19", "SC19.1", "SC19.2", "SC19.3", "SC19.4", "SC20D", "SC20D.1", "SC19.5", "SC19.6", "SC19.7", "SC19.8", "SC19.9", "SC20", "SC20.1", "SC20.2", "SC21", "SC21.1", "SC21.2", "SC21.3", "SC21.4", "SC22", "SC22.1", "SC22.2", "SC22.3", "SC22.4", "SC23", "SC23.1", "SC23.2", "SC23.3", "SC23.4", "SC23.5", "SC23.6", "SC24", "SC25", "SC26", "SC27", "SC28", "SC29", "SC30", "SC31", "SC32", "SC33", "SC34"): B.use_slots()
    if man["marker"] in ("SC17.7", "SC17.8", "SC18", "SC18.1", "SC18.2", "SC18.3", "SC19", "SC19.1", "SC19.2", "SC19.3", "SC19.4", "SC20D", "SC20D.1", "SC19.5", "SC19.6", "SC19.7", "SC19.8", "SC19.9", "SC20", "SC20.1", "SC20.2", "SC21", "SC21.1", "SC21.2", "SC21.3", "SC21.4", "SC22", "SC22.1", "SC22.2", "SC22.3", "SC22.4", "SC23", "SC23.1", "SC23.2", "SC23.3", "SC23.4", "SC23.5", "SC23.6", "SC24", "SC25", "SC26", "SC27", "SC28", "SC29", "SC30", "SC31", "SC32", "SC33", "SC34"): B.use_songptr()
    if man["marker"] in ("SC17.8", "SC18", "SC18.1", "SC18.2", "SC18.3", "SC19", "SC19.1", "SC19.2", "SC19.3", "SC19.4", "SC20D", "SC20D.1", "SC19.5", "SC19.6", "SC19.7", "SC19.8", "SC19.9", "SC20", "SC20.1", "SC20.2", "SC21", "SC21.1", "SC21.2", "SC21.3", "SC21.4", "SC22", "SC22.1", "SC22.2", "SC22.3", "SC22.4", "SC23", "SC23.1", "SC23.2", "SC23.3", "SC23.4", "SC23.5", "SC23.6", "SC24", "SC25", "SC26", "SC27", "SC28", "SC29", "SC30", "SC31", "SC32", "SC33", "SC34"): B.use_clearpad()
    if man["marker"] in ("SC18.1", "SC18.2", "SC18.3", "SC19", "SC19.1", "SC19.2", "SC19.3", "SC19.4", "SC20D", "SC20D.1", "SC19.5", "SC19.6", "SC19.7", "SC19.8", "SC19.9", "SC20", "SC20.1", "SC20.2", "SC21", "SC21.1", "SC21.2", "SC21.3", "SC21.4", "SC22", "SC22.1", "SC22.2", "SC22.3", "SC22.4", "SC23", "SC23.1", "SC23.2", "SC23.3", "SC23.4", "SC23.5", "SC23.6", "SC24", "SC25", "SC26", "SC27", "SC28", "SC29", "SC30", "SC31", "SC32", "SC33", "SC34"): B.use_jump(repeat=man["marker"] in ("SC19.7", "SC19.8"), white=man["marker"] in ("SC19.7", "SC19.8", "SC19.9", "SC20", "SC20.1", "SC20.2", "SC21", "SC21.1", "SC21.2", "SC21.3", "SC21.4"), hold=man["marker"] in ("SC19.9", "SC20", "SC20.1", "SC20.2", "SC21", "SC21.1", "SC21.2", "SC21.3", "SC21.4"))
    if man["marker"] in ("SC20.1", "SC20.2", "SC21", "SC21.1", "SC21.2", "SC21.3", "SC21.4", "SC22", "SC22.1", "SC22.2", "SC22.3", "SC22.4", "SC23", "SC23.1", "SC23.2", "SC23.3", "SC23.4", "SC23.5", "SC23.6", "SC24", "SC25", "SC26", "SC27", "SC28", "SC29", "SC30", "SC31", "SC32", "SC33", "SC34"): B.JMP_ON, B.JMP_OFF, B.SP_PLAY = 0x2D, 0x2E, True                                       # SC20.1: pad 7 in yellow (RGB table: 0x2D = 255, 255, 25; 0x2E = its dim twin)
    B.KNOB_BRIGHT = man["report"]["sc17"].get("knob_bright", False)
    MB = 14 if B.ENTRY == "mixer14" else 13
    L = {k: int(v, 16) for k, v in man["report"]["sc17"]["labels"].items()}
    L["c_gtick"] = int(man["report"]["sc14"]["labels"]["c_gtick"], 16)
    state = int(man["report"]["sc17"]["state"], 16)
    tabs = B.tables()
    pal = [(int(x, 16), int(y, 16)) for x, y in man["report"]["sc17"]["pal_codes"]]

    e = E17(img, L); e.state = state
    es = E17(stock, L); es.state = state
    # ---- Mixer button
    shift_entry = B.ENTRY == "shift"
    e.btn(MB); es.btn(MB)
    check(e.view() == 1 == es.view(), "Mixer from the track view: Mixer view (as stock)")
    check(e.st()["mode"] == 0, "Master FX mode off after entering the Mixer")
    if B.ENTRY == "mixer14":
        e.btn(14); check(e.view() == 1 and e.st()["mode"] == 1, "Mixer again: Master FX mode on, still the Mixer view object")
        e.calls.clear(); e.call(0x08033282, MGR, 0, 100, maxins=900000)            # pad 1 through the controller
        check(B.MIX_PRESS not in [int(x, 16) for x in e.calls] and e.st()["held"] == 1, f"Master FX: pad 1 via controller -> Gater held, no mute {e.calls}")
        e.call(0x080332FE, MGR, 0, maxins=900000); check(e.st()["held"] == 0, "pad 1 released via controller")
        e.btn(14); check(e.view() == 1 and e.st()["mode"] == 0, "Mixer again: back to the Mixer")
        e.calls.clear(); e.call(0x08033282, MGR, 0, 100, maxins=900000)
        check(e.calls == [hex(B.MIX_PRESS)], f"Mixer: pad 1 via controller -> stock mute handler {e.calls}")
        e.btn(14); e.btn(15); check(e.view() == 0, "Master FX -> FX: FX view active")
        e.btn(14); check(e.view() == 1 and e.st()["mode"] == 0, "FX -> Mixer: normal Mixer")
        e.btn(14, shift=True); check(e.view() == 1 and e.st()["mode"] == 0, "Shift + Mixer: filtered by the stock Shift mask, nothing changes")
        e.btn(13); check(e.view() == 0 and e.st()["mode"] == 0, "button 13 (view 1): stock, not the Mixer")
    elif shift_entry:
        e.btn(13); check(e.view() == 1 and e.st()["mode"] == 0, "Mixer again: still the normal Mixer (no toggle)")
        e.calls.clear(); e.btn(13, shift=True)
        check(e.view() == 1 and e.st()["mode"] == 1 and "0x8045d5a" not in e.calls, f"Shift + Mixer: Master FX on, Mixer view object {e.calls}")
        e.btn(13, shift=True); check(e.view() == 1 and e.st()["mode"] == 1, "Shift + Mixer again: stays in Master FX")
        e.btn(13); check(e.view() == 1 and e.st()["mode"] == 0, "Mixer: back to the Mixer")
        e.btn(15); e.btn(13, shift=True)
        check(e.view() == 1 and e.st()["mode"] == 1, "FX view -> Shift + Mixer: Master FX directly")
        e.btn(15); check(e.view() == 0, "Master FX -> FX: FX view active")
        e.btn(13); check(e.view() == 1 and e.st()["mode"] == 0, "FX -> Mixer: normal Mixer")
        e3, es3 = E17(img, L), E17(stock, L)
        e3.state = es3.state = state
        e3.btn(13, shift=True); es3.btn(13)
        check(bytes(e3.uc.mem_read(MGR, 0x180)) == bytes(es3.uc.mem_read(MGR, 0x180)),
              "Shift + Mixer leaves the controller exactly as a stock Mixer press")
    else:
        e.btn(13); check(e.view() == 1 and e.st()["mode"] == 1, "Mixer again: Master FX mode on, still the Mixer view object")
        e.btn(13); check(e.view() == 1 and e.st()["mode"] == 0, "Mixer again: back to the Mixer")
        e.btn(13); e.btn(15)
        check(e.view() == 0, "Master FX -> FX: FX view active")
        e.btn(13)
        check(e.view() == 1 and e.st()["mode"] == 0, "FX -> Mixer: normal Mixer")
        e.calls.clear(); e.btn(13, shift=True)
        check("0x8045d5a" in e.calls and e.st()["mode"] == 0, f"Shift + Mixer: stock function untouched {e.calls}")
    def enter():
        if B.ENTRY == "mixer14":
            if e.view() != 1: e.btn(14)
            e.btn(14)
        elif shift_entry: e.btn(13, shift=True)
        else:
            if e.view() != 1: e.btn(13)
            e.btn(13)
    # ---- view slots outside the mode: stock
    for slot, args, stockfn in ((0, (3, 100), B.MIX_PRESS), (1, (3,), B.MIX_REL), (4, (0, 5), B.MIX_KNOB)):
        e.vcall(slot, *args)
        check(e.calls == [hex(stockfn)], f"Mixer slot {slot} with Master FX off -> stock {e.calls}")
    e2, es2 = E17(img, L), E17(stock, L)
    e2.state = es2.state = state
    for x in (e2, es2): x.btn(MB)
    check(e2.leds() == es2.leds(), "Mixer LEDs with Master FX off: as stock")
    # ---- Master FX view
    enter(); assert e.st()["mode"] == 1
    s0 = e.st()
    check(s0["knobs"] == [list(d) for d in B.DEFAULTS] and s0["held"] == 0 and s0["latch"] == 0, f"defaults {s0['knobs']}")
    e.vcall(0, 0, 100); s = e.st(); check(s["held"] == 1 and s["sel"] == 0 and e.calls == [], "pad 1 held: Gater on, selected, no stock call")
    e.vcall(1, 0); check(e.st()["held"] == 0, "pad 1 released: Gater off")
    e.vcall(0, 4, 100, shift=True); s = e.st(); check(s["latch"] == 1 << 4 and s["sel"] == 4, "Shift + pad 5: Phaser latched, selected")
    e.vcall(1, 4); check(e.st()["latch"] == 1 << 4, "release: Phaser stays latched")
    e.vcall(0, 4, 100, shift=True); check(e.st()["latch"] == 0, "Shift + pad 5 again: unlatched")
    e.vcall(0, 10, 100); e.vcall(1, 10); check(e.st()["held"] == 0 and e.calls == [], "pad 11: ignored")
    # knobs edit the selected set
    e.vcall(0, 2, 100); e.vcall(1, 2)                                          # select AF HP -> set 1
    e.vcall(4, 0, 5); e.vcall(4, 3, -100); e.vcall(4, 1, 200); e.vcall(4, 6, 9)
    s = e.st(); k = s["knobs"][1]
    check(k == [B.DEFAULTS[1][0] + 5, 127, B.DEFAULTS[1][2], 0] and s["dirty"] == 1 and s["knobs"][0] == list(B.DEFAULTS[0]),
          f"knobs on AF (pad 3): +5, clamp 127, clamp 0, knob 7 ignored {k}")
    e.vcall(0, 1, 100); e.vcall(1, 1); e.vcall(4, 0, -5); check(e.st()["knobs"][1][0] == B.DEFAULTS[1][0], "pad 2 (AF LP) shares the AF set")
    # LEDs
    e.vcall(0, 3, 100, shift=True)                                             # latch Digitise, selected
    e.vcall(0, 0, 100)                                                         # hold Gater (selected)
    Ls = e.leds()
    exp = [0] * 32
    for i in range(6): exp[i] = pal[i][0] if i in (0, 3) else pal[i][1]
    exp[8 + 0] = pal[0][0]
    if B.SLOTS:                                    # SC17.6: the bottom row is the FX view's
        fxv = 0x200443B4
        e.call(e.r32(e.r32(fxv) + 0x1C), fxv); fp = e.uc.reg_read(UC_ARM_REG_R0)
        exp[24:32] = list(struct.unpack("<8H", bytes(e.uc.mem_read(fp + 48, 16))))
        check(Ls[24:32] == exp[24:32] and any(exp[24:32]), f"Master FX: bottom row (pads 25-32) = the FX view's {[hex(x) for x in exp[24:32]]}")
    if B.SONGPTR:                                  # SC17.7: rows 2 and 3 = the song pointer (idle pads while the transport is stopped)
        exp[8:24] = [B.SP_COLORS(pal)[0]] * 16
    if B.CLEARPAD:                                 # SC17.8: pad 8 = clear pad, lit while an effect is latched (Digitise is)
        exp[7] = B.CLR_ON
    if B.JUMP:                                     # SC18.1: pad 7 = jump mode (off: dim song pointer colour)
        exp[6] = B.JMP_OFF if B.JUMP_WHITE else B.SP_COLORS(pal)[0]                 # SC19.7: white
    check(Ls == exp, f"Master FX LEDs: on pads bright, others dim, selected marker in row 2 {[hex(x) for x in Ls[:16]]}")
    if B.LED_N > 32:
        def task(x):                                   # stock LED task: 0x45 LEDs of the whole panel
            buf = 0x2006E000; x.call(0x08034196, MGR, buf, maxins=900000)
            return list(struct.unpack("<69H", bytes(x.uc.mem_read(buf, 138))))
        mixleds = list(struct.unpack("<42H", bytes(e.uc.mem_read(e.r32(e.r32(MIXV2 + 4)), 84))))
        t = task(e)
        check(t[:32] == exp and t[51:53] == mixleds[32:34], f"LED task in Master FX: pads from Master FX, LEDs 51/52 = Mixer's {t[51:53]}")
        kv = lambda i, n: [pal[i][0] | (((B.DEFAULTS[B.SETMAP[i]][k] + 2) << 8) if getattr(B, "KNOB_BRIGHT", False) else 0) for k in range(n)]    # SC19.9: colour | (value + 2) << 8
        check(t[60:68] == kv(0, 4) + [0] * 4, f"knob LEDs: 1-4 in the Gater colour, 5-8 off {[hex(x) for x in t[60:68]]}")
        e.vcall(0, 3, 100, shift=True); e.vcall(0, 3, 100, shift=True)          # select Digitise (latch toggled twice)
        t = task(e); check(t[60:68] == kv(3, 2) + [0] * 6, f"Digitise selected: knobs 1-2 lit {[hex(x) for x in t[60:68]]}")
        e.vcall(0, 0, 100)
    # ---- tick: DSP parameters
    bpm_beat = None
    w = e.tick(1000)
    check(w.get(G.FX_ON) == (1 << G.B_GATE) | (1 << G.B_DIG), f"tick: FX_ON = Gater + Digitise {hex(w.get(G.FX_ON, -1))}")
    ks = e.st()["knobs"]
    check(w.get(G.DG_N) == tabs["DGN"][ks[2][0]] and w.get(G.DG_MASK) == tabs["DGM"][ks[2][1]] and w.get(G.G_K) == tabs["GK"][ks[0][3]]
          and w.get(G.VN_LPK) == tabs["VLPK"][ks[4][2]] and w.get(G.PH_MIX) == tabs["MIX"][ks[3][3]],
          "tick (dirty): static parameters from the tables")
    check(w.get(G.G_TGT) == 0x7FFFFF, "Gater starts open")
    w2 = e.tick(1001)
    check(G.DG_N not in w2 and G.G_TGT not in w2 and G.FX_ON not in w2, f"next tick: nothing rewritten {w2}")
    # gate timing: period = beat*4/div
    e.call(L["c_fxtick"] if False else int(man["report"]["sc14"]["labels"]["c_beat"], 16)); beat = e.uc.reg_read(UC_ARM_REG_R0)
    div = tabs["GDIV"][ks[0][0]]; period = beat * 4 // div; duty = 8 + ks[0][2] * 112 // 127
    seq = []
    for t in range(1000, 1000 + 2 * period, max(1, period // 16)):
        wt = e.tick(t)
        if G.G_TGT in wt: seq.append((t - 1000, wt[G.G_TGT]))
    closed = tabs["GOFF"][ks[0][1]]
    exp_close = (duty * period + 127) // 128
    check(len(seq) >= 2 and seq[0][1] == closed and abs(seq[0][0] - exp_close) <= period // 16 + 1 and seq[1][1] == 0x7FFFFF,
          f"Gater {beat} ms/beat, 1/{div}: closes after ~{exp_close} ms, reopens at the period ({period} ms) {seq[:4]}")
    # leaving the view drops held effects, latched ones stay
    e.btn(15); w = e.tick(5000)
    check(e.st()["held"] == 0 and w.get(G.FX_ON) == 1 << G.B_DIG, f"left the view: held Gater dropped, latched Digitise stays {hex(w.get(G.FX_ON, -1))}")
    # Auto-Filter and Phaser LFO writes
    enter(); assert e.st()["mode"] == 1
    e.vcall(0, 1, 100, shift=True); e.vcall(0, 4, 100, shift=True)
    fs, ps = set(), set()
    for t in range(6000, 6000 + 4000, 50):
        wt = e.tick(t)
        if G.AF_F in wt: fs.add(wt[G.AF_F])
        if G.PH_A in wt: ps.add(wt[G.PH_A])
    check(len(fs) > 5 and max(fs) <= tabs["AFTAB"][127] and len(ps) > 5, f"Auto-Filter and Phaser sweep: {len(fs)} / {len(ps)} distinct coefficients written")
    print("SC17 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    st, im = Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes()
    sys.exit(1 if main(st, im, json.loads(Path(sys.argv[3]).read_text())) else 0)
