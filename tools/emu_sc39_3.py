"""SC39.3 ARM tests (live RAM dump, the real routes: the controller's buttons, pads and knobs, the LED task and the panel frame from its caller): the
editor of the synth macros' destinations (tools/macroed.py).

    python tools/emu_sc39_3.py SC39.3.bin SC39.3_manifest.json SC39.2.bin SC39.2_manifest.json
  * Synth 1's source view: pad 32 dim teal; pressed: bright, the editor on; the knobs' LEDs dim teal; nothing of the patch changes;
  * a knob turned: its macro picked (its LED white), no value changed, the pads show the slot (1, yellow); the knob again: slots 1..4, a step every
    STEP_SLOT events (a turn of the real knob sends many), no wrap;
  * Octave down / up: the fields slot -> start -> end -> destination -> depth, with their LEDs; each field writes its own parameter of the slot
    (175 + 17 macro + 4 slot: destination, + 1 start, + 2 end, + 3 depth), limited to 0..127, and nothing else of the patch;
  * the number on the pads = the stock glyphs (c_ednum) of the value in the field's colour; depth: the amount, teal / red / dim white by its sign;
  * destination: the whole walk up and down = the 31 destinations with a CC by ascending CC number, then the 39 NRPN ones in the order of the
    destinations; shown as that number in the colour of its bank; a destination out of range in the patch starts the walk at its first place;
  * any pad: back to the pads of the source view, the editor still on (pad 32 bright); another knob: its macro; pad 32: off (the knobs are the
    macros again: the stock moves the macro's position);
  * a view button: the editor off; Synth 2: its own patch (type 1);
  * the previous build: pad 32 and the knobs as before.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R4
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import E35, MGR  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
import macroed as MC  # noqa: E402
import mpatch as MP  # noqa: E402

B = 0x08010000
NPAR = 312


class EC(E35):
    def setup(self, man):
        self.gstf = int(man["report"]["sc14"]["labels"]["c_gst"], 16)
        self.ednum = int(man["report"]["vcf20"]["labels"]["c_ednum"], 16)
    def gst(self): self.call(self.gstf); return self.uc.reg_read(UC_ARM_REG_R0)
    def flag(self): return self.r8(self.gst() + 20)
    def state(self): return bytes(self.uc.mem_read(self.gst() + MC.ST_OFF, 3))
    def acc(self): return self.r8(self.gst() + MC.ST_OFF + 3)
    def pads(self):
        self.call(0x08034196, MGR, 0x2006E000, maxins=8_000_000); return list(struct.unpack("<32H", bytes(self.uc.mem_read(0x2006E000, 64))))
    def panel(self):
        self.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); self.uc.reg_write(UC_ARM_REG_R4, MGR)
        self.call(0x08033B3E, maxins=8_000_000)
        return struct.unpack("<69H", bytes(self.uc.mem_read(self.r32(self.r32(MGR + 0x90)), 138)))
    def pad(self, p): self.call(PRESS, MGR, p, 100, maxins=8_000_000); self.call(RELEASE, MGR, p, maxins=8_000_000)
    def knob(self, k, d): self.call(0x08033848, MGR, k, d & 0xFFFFFFFF, maxins=3_000_000)
    def get(self, t, i): self.call(MC.GETTER, t, i); return self.uc.reg_read(UC_ARM_REG_R0) & 0xFF
    def patch(self, t): return [self.get(t, i) for i in range(NPAR)]
    def put(self, t, i, v):
        this = self.r32(self.r32(self.r32(MC.CTX) + 0x10)); self.call(MC.PARAM_SET, this + 4, t, i, v, maxins=3_000_000)
    def glyphs(self, v, col):
        self.uc.mem_write(0x2006D000, bytes(64)); self.call(self.ednum, 0x2006D000, v, col, maxins=200000)
        return list(struct.unpack("<32H", bytes(self.uc.mem_read(0x2006D000, 64))))


def run(img, man, new):
    e = EC(img, man); e.setup(man)
    out = dict(cur0=e.r8(MGR + 0x152))
    e.btn(0)                                                                      # Synth 1 pressed in its track view: the source view
    out["src"] = (e.r8(MGR + 0x152), e.flag() & 4); out["f_src"] = e.pads(); out["k_src"] = e.panel()[60:68]
    p0 = e.patch(0)
    e.pad(MC.PAD_ED); out["on"] = (e.state(), e.pads(), e.panel()[60:68], e.patch(0) == p0)
    if not new:
        e.knob(3, 1); out["prev"] = (e.pads() == out["f_src"], [i for i, (a, b_) in enumerate(zip(p0, e.patch(0))) if a != b_])
        del e; gc.collect(); return out
    M, base = 3, 175 + 17 * 3
    e.knob(M, 1); out["pick"] = (e.state(), e.pads(), e.panel()[60:68], e.patch(0) == p0, e.panel()[MP.LED_DOWN], e.panel()[MP.LED_UP])
    out["one"] = e.glyphs(1, MC.COL_SLOT)
    slots = []
    U = MC.STEP_SLOT
    for d in (1, 1, 1, 1, -1, -1, -1, -1, 1):
        for _ in range(U - 1): e.knob(M, d)
        part = e.state()[2] >> 4
        e.knob(M, d); slots.append((part, e.state()[2] >> 4))
    out["slot_rev"] = []
    for d in [1] * (U - 1) + [-1] * (U - 1) + [1] * (U - 1): e.knob(M, d); out["slot_rev"].append(e.state()[2] >> 4)   # back and forth short of a step
    e.btn(MP.ID_DOWN); e.btn(MP.ID_UP)                                             # (a field change forgets the part of a step)
    for _ in range(U - 1): e.knob(M, 1)
    out["slot_rev"].append(e.state()[2] >> 4)
    out["slots"] = slots; out["slot_led"] = (e.pads(), e.glyphs(2, MC.COL_SLOT)); out["slot_patch"] = e.patch(0) == p0     # slot B now
    sb = base + 4
    fields = {}
    for f, ofs, col in ((1, 1, MC.COL_START), (2, 2, MC.COL_END)):
        e.btn(MP.ID_DOWN); st = e.state()[2] & 7
        e.put(0, sb + ofs, 60); q = e.patch(0)
        e.knob(M, 5); v1 = e.get(0, sb + ofs); led = (e.pads(), e.glyphs(v1, col))
        e.knob(M, 100); v2 = e.get(0, sb + ofs); e.knob(M, -127); e.knob(M, -127); v3 = e.get(0, sb + ofs)
        others = [i for i, (a, b_) in enumerate(zip(q, e.patch(0))) if a != b_ and i != sb + ofs]
        fields[f] = (st, v1, v2, v3, led, others, (e.panel()[MP.LED_DOWN], e.panel()[MP.LED_UP]))
    out["fields"] = fields
    e.btn(MP.ID_DOWN); out["f_dest"] = e.state()[2] & 7                            # the destination
    e.put(0, sb, MC.ORDER[0])
    walk = []
    e.knob(M, 1); out["half"] = e.get(0, sb); e.knob(M, -1)                         # one event: no step yet
    for d in [1] * 72 + [-1] * 72:
        for _ in range(MC.STEP_DEST): e.knob(M, d)
        v = e.get(0, sb); walk.append((v, e.pads() == e.glyphs(MC.DEST[v][2], MC.COL_BANK[MC.DEST[v][1]])))
    out["walk"] = walk
    e.put(0, sb, 70); e.knob(M, MC.STEP_DEST); out["oor"] = e.get(0, sb)                      # (0x08034D92 may clamp the 70 itself)
    e.btn(MP.ID_DOWN); out["f_depth"] = e.state()[2] & 7
    dep = []
    for v in (64, 64 + 20, 64 - 20):
        e.put(0, sb + 3, v); dep.append(e.pads())
    out["depth"] = (dep, [e.glyphs(0, MC.COL_ZERO), e.glyphs(20, MC.COL_POS), e.glyphs(20, MC.COL_NEG)])
    e.put(0, sb + 3, 120); e.knob(M, 50); d1 = e.get(0, sb + 3); e.btn(MP.ID_DOWN); out["depth_edge"] = (d1, e.state()[2] & 7, e.panel()[MP.LED_DOWN], e.panel()[MP.LED_UP])
    e.btn(MP.ID_UP); out["up"] = e.state()[2] & 7
    e.pad(5); out["drop"] = (e.state(), e.pads())                                  # any pad: back to the pads
    e.knob(6, -1); out["other"] = e.state()
    e.pad(9); q = e.patch(0); pos = e.get(0, 174 + 17 * 2)
    e.pad(MC.PAD_ED); out["off"] = (e.state(), e.pads()[MC.PAD_ED])
    e.knob(2, -9); out["stock"] = (pos, e.get(0, 174 + 17 * 2))                    # the editor off: the knob is the macro again
    e.pad(MC.PAD_ED); e.knob(1, 1); e.btn(9); out["viewbtn"] = (e.state(), e.r8(MGR + 0x152))    # Note: the source view and the editor close
    e.btn(1); e.btn(1)                                                             # Synth 2's track view, then its source view
    out["s2"] = (e.r8(MGR + 0x152), e.flag() & 4)
    p1, p0b = e.patch(1), e.patch(0)
    e.pad(MC.PAD_ED); e.knob(0, 1); e.btn(MP.ID_DOWN); e.put(1, 175 + 1, 10); p1 = e.patch(1); e.knob(0, 7)
    out["s2_edit"] = (e.state(), e.get(1, 175 + 1), [i for i, (a, b_) in enumerate(zip(p1, e.patch(1))) if a != b_], e.patch(0) == p0b)
    del e; gc.collect()
    return out


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["macroed"]["labels"].items()}
    P = {k: int(v, 16) for k, v in man["report"]["macroed"]["prev"].items()}
    w = lambda a: struct.unpack_from("<I", img, a - B)[0]
    from thumb import b_w, bl
    import packio as PK
    HP, HL, HB = L["c_mcpad"], L["c_mcleds"], L["c_mcbtn"]
    ps = man["report"].get("psave")                                               # SC39.4: the patch save chains in front of both
    if ps is not None:
        assert int(ps["prev"]["pad"], 16) == HP and int(ps["prev"]["leds"], 16) == HL
        HP, HL = int(ps["labels"]["c_pspad"], 16), int(ps["labels"]["c_psleds"], 16)
        if "btn" in ps["prev"]: assert int(ps["prev"]["btn"], 16) == HB; HB = int(ps["labels"]["c_psbtn"], 16)
    HT = L["c_mcledtask"]
    HK = L["c_mckleds"]
    tl_ = man["report"].get("typeleds")                                           # SC39.5: the type colours chain in front of the knob LEDs
    if tl_ is not None: assert int(tl_["prev"]["gleds"], 16) == HK; HK = int(tl_["labels"]["c_tgleds"], 16)
    sc_ = man["report"].get("sesscopy")                                           # SC39.6: the project copy chains in front of the LED task hook
    if sc_ is not None: assert int(sc_["prev"]["ledtask"], 16) == HT; HT = int(sc_["labels"]["c_scledtask"], 16)
    th_ = man["report"].get("throw")                                              # SC39.8: the delay throw is the head of the button chain
    if th_ is not None: HB = int(th_["labels"]["c_thbtn"], 16)
    check(w(MC.SP_VT) == HP | 1 and w(MC.SP_VT + 28) == HL | 1 and w(MC.AC64_VT + 16) == L["c_mcknob"] | 1 and w(MC.AC64_VT + 28) == HK | 1
          and bytes(img[MC.BTN_ENTRY - B:MC.BTN_ENTRY - B + 4]) == b_w(MC.BTN_ENTRY, HB) and all(bytes(img[c - B:c - B + 4]) == bl(c, HT) for c in PK.LED_CALLS),
          f"the hooks: the synth Preset view's slots 0 / 7, the macro handlers' slots 4 / 7, the button chain's head, the LED task calls (in front of {', '.join(f'{k} {v:#x}' for k, v in P.items())})")
    cc = [d for d in MC.ORDER if MC.DEST[d][1] == "CC"]
    check(len(MC.ORDER) == 70 and sorted(MC.ORDER) == list(range(70)) and len(cc) == 31 and MC.ORDER[:31] == cc and [MC.DEST[d][2] for d in cc] == sorted(MC.DEST[d][2] for d in cc)
          and MC.ORDER[31:] == sorted(MC.ORDER[31:]), f"the walk: 31 destinations with a CC by ascending CC number ({[MC.DEST[d][2] for d in cc][:6]}…), then the 39 NRPN ones by destination ({MC.ORDER[31:35]}…)")
    o = run(img, man, True)
    ON, SEL = MC.F_ON, MC.F_SEL
    check(o["cur0"] == 1 and o["src"] == (0, 4) and o["f_src"][MC.PAD_ED] == MC.COL_ED[1], f"Synth 1 pressed in its track view: the source view; pad 32 dim teal ({o['f_src'][MC.PAD_ED]:#x})")
    st, f, k, same = o["on"]
    check(st == bytes([MC.MAGIC, ON, 0]) and f[MC.PAD_ED] == MC.COL_ED[0] and f[:31] == o["f_src"][:31] and list(k) == [MC.KNOB_IDLE] * 8 and same,
          f"pad 32: the editor on, bright; the other pads as before; the knobs dim teal ({[hex(x) for x in k][:2]}); the patch untouched")
    st, f, k, same, dn, up = o["pick"]
    check(st == bytes([MC.MAGIC, ON | SEL | 3, 0]) and same and f == o["one"] and list(k) == [MC.KNOB_IDLE] * 3 + [MC.KNOB_SEL] + [MC.KNOB_IDLE] * 4 and (dn, up) == (MP.COL_BTN, 0),
          f"knob 4 turned: macro 4 picked (its LED white), nothing changed, the pads show 1 in yellow; Octave down lit / up dark")
    check([b_ for a_, b_ in o["slots"]] == [1, 2, 3, 3, 2, 1, 0, 0, 1] and [a_ for a_, b_ in o["slots"]] == [0, 1, 2, 3, 3, 2, 1, 0, 0] and set(o["slot_rev"]) == {1} and o["slot_led"][0] == o["slot_led"][1] and o["slot_patch"], f"the knob again: slots 1..4, a step every {MC.STEP_SLOT} events (not before; a field change forgets the part), no wrap; the pads show the slot; the patch untouched")
    for f_, name in ((1, "start"), (2, "end")):
        st, v1, v2, v3, led, others, oct_ = o["fields"][f_]
        check(st == f_ and (v1, v2, v3) == (65, 127, 0) and led[0] == led[1] and others == [] and oct_ == (MP.COL_BTN, MP.COL_BTN),
              f"Octave down: the {name} position of slot B: 60 + 5 = {v1}, limited to {v3}..{v2}, shown in its colour; nothing else of the patch; both Octave LEDs")
    w_ = o["walk"]
    want = MC.ORDER[1:] + [MC.ORDER[-1]] * 3 + MC.ORDER[-2::-1] + [MC.ORDER[0]] * 3
    check(o["f_dest"] == 3 and o["half"] == MC.ORDER[0] and [v for v, ok in w_] == want and all(ok for v, ok in w_),
          f"the destination: 72 steps up and 72 down ({MC.STEP_DEST} events each) = the walk, the ends stop; each shown as its CC / NRPN number in its bank's colour ({[v for v, ok in w_][:5]}…)")
    check(o["oor"] in (MC.ORDER[1], MC.ORDER[MC.INV[69] + 1] if MC.INV[69] < 69 else 69), f"a destination out of range in the patch: the next turn gives a valid one ({o['oor']})")
    dep, want = o["depth"]
    check(o["f_depth"] == 4 and dep == want, "the depth: 0 dim white, +20 teal, -20 red (the amount without the sign)")
    d1, f_, dn, up = o["depth_edge"]
    check(d1 == 127 and f_ == 4 and (dn, up) == (0, MP.COL_BTN) and o["up"] == 3, f"the depth stops at 127; Octave down at the last field stays (LEDs down dark / up lit); Octave up goes back ({o['up']})")
    st, f = o["drop"]
    check(st[1] == ON | 3 and f[:31] == o["f_src"][:31] and f[MC.PAD_ED] == MC.COL_ED[0], "any pad: the pads of the source view again, the editor still on")
    check(o["other"][1] == ON | SEL | 6 and o["other"][2] == 0, f"another knob: its macro, slot 1, the first field ({o['other'].hex()})")
    st, led = o["off"]
    check(st[1] == 0 and led == MC.COL_ED[1] and o["stock"][0] != o["stock"][1], f"pad 32 again: off; the knob moves the macro's position as the stock ({o['stock']})")
    check(o["viewbtn"][0][1] == 0 and o["viewbtn"][1] == 1, f"Note pressed with the editor on: the source view and the editor close ({o['viewbtn'][0].hex()})")
    st, v, ch, same0 = o["s2_edit"]
    check(o["s2"] == (9, 4) and st[1] == ON | SEL | 8 and v == 17 and ch == [176] and same0, f"Synth 2: its own patch (type 1): start of macro 1 slot A 10 + 7 = {v}; Synth 1's patch untouched")
    gc.collect(); q = run(prev, prev_man, False)
    check(q["on"][1] == q["f_src"] and q["prev"][0] and q["prev"][1] != [], f"the previous build: pad 32 does nothing, the knob moves its macro ({q['prev'][1]})")
    print("SC39.3 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
