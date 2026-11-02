"""SC50.4 / Beta 5.7 / RC4.06: the chord screen with the arpeggiator on, through the controller, the real router and the LED task:
  * two chords sharing notes, no arpeggiator: every note one note-on and one note-off; letting one go keeps the notes the other holds;
  * the same with the arpeggiator: the notes the other chord holds stay in the arpeggio;
  * (Beta) pad 16: no latch; the chord mirrored downwards from the root, the release stops it; with diatonic too;
  * the arpeggio with the track muted, playing (the players' tick dispatch): it steps on the grid, each note stopped by the next, and the sequence stays silent;
  * the count-in's tempo: the project's; as a slave the measured one;
  * rollers and the drums' arpeggio stopped: the tempo from p0;
  * (Beta) the click at level 0: Clear orange 100 ms; at another level, or with Shift, not.

    python tools/emu_chordfix.py NEW.bin NEW_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_cscale as ECS  # noqa: E402
import emu_sc46_3 as T  # noqa: E402
import chords as CH  # noqa: E402
import arp as A  # noqa: E402

MGR = ECS.MGR
IFC_ON, IFC_OFF = 0x0801D38E, 0x0801D942
PLAYER, DISPATCH = 0x20040200, 0x0804A5C6
LED_FRAME = 0x2006E000


class P(ECS.EC):
    """the sound path is real up to the note interface of the router"""
    def __init__(self, img, man):
        super().__init__(bytearray(img), {k: int(v, 16) for k, v in man["report"]["cscale"]["labels"].items()})
        self.man = man; self.at(100000); self.transport(0)
        self.ifc = []
        self.A = {k: int(v, 16) for k, v in man["report"]["arp"]["labels"].items()}
        def ifc(uc, a, s, d):
            if uc.reg_read(UC_ARM_REG_R0) in self.watch: self.ifc.append(("on" if a == IFC_ON else "off", uc.reg_read(UC_ARM_REG_R1) & 0xFF))
        self.watch = set()
        for f in (IFC_ON, IFC_OFF): self.uc.hook_add(UC_HOOK_CODE, ifc, begin=f, end=f)
        def skip(uc, a, s, d): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        self.uc.hook_add(UC_HOOK_CODE, skip, begin=A.REC_ON, end=A.REC_ON)
    press = T.E.press; release = T.E.release; tap = T.E.tap; goto = T.E.goto; val = T.E.val
    def setp(self, store, k, v, n=1):
        for fn in (0x080354FA, 0x0803542C): self.uc.mem_write(self.r0(fn, store, k), v.to_bytes(n, "little"))
    def get(self): out = sorted(set(self.ifc)); return out
    def sounding(self):
        s = {}
        for w, n in self.ifc: s[n] = s.get(n, 0) + (1 if w == "on" else -1)
        return s


def fresh(img, man, arp):
    gc.collect()
    e = P(img, man); e.btn(0); e.goto(6); e.tap(CH.PAD_TOG, shift=True); e.frame()
    e.watch = {0x200413F0, e.r32(PLAYER + 0x4C)}                                       # the track view's note interface and the player's
    if arp:
        pat = e.r0(e.A["c_arpat"], 0); e.call(e.A["c_arset"], 0, pat, 0x80 | A.M_UP); e.pat = pat
    return e


def lst(e):
    s = e.r0(e.A["c_arst"], 0, 1); n = e.r8(s + A.S_N)
    return sorted(e.r8(s + A.S_NOTES + i) for i in range(n))


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]; beta = "clickflash" in rep
    # ---- two chords, no arpeggiator
    e = fresh(img, man, False)
    a, b = 24, 26                                                                       # 48: 48 52 55; 51: 51 55 58
    ra, rb = e.val(a), e.val(b)
    e.ifc.clear(); e.press(a); e.press(b); ons = [n for w, n in e.ifc if w == "on"]
    check(ons.count(ra + 7) == 1 and len(ons) == 5, f"two chords sharing a note: one note-on of it ({ons})")
    e.ifc.clear(); e.release(b); off1 = sorted(n for w, n in e.ifc if w == "off")
    check(ra + 7 not in off1 and len(off1) == 2, f"one let go: the shared note stays ({off1})")
    e.ifc.clear(); e.release(a); off2 = sorted(n for w, n in e.ifc if w == "off")
    check(off2 == sorted([ra, ra + 4, ra + 7]), f"the other let go: its notes off, the shared one too ({off2})")
    del e
    # ---- with the arpeggiator
    e = fresh(img, man, True)
    e.press(a); e.press(b); l0 = lst(e)
    check(l0 == sorted({ra, ra + 4, ra + 7, rb, rb + 4, rb + 7}), f"arpeggiator: the held notes ({l0})")
    e.release(b); l1 = lst(e)
    check(l1 == [ra, ra + 4, ra + 7], f"one chord let go: the other's notes all stay in the arpeggio ({l1})")
    e.release(a); check(lst(e) == [], "the last let go: none")
    del e
    # ---- the arpeggio muted, playing
    e = fresh(img, man, True)
    mute, tick_store = e.r32(PLAYER + 0x28), e.r32(PLAYER + 0x18)
    st = e.r32(PLAYER + 8)
    e.press(a)
    e.setp(mute, 0, 1); e.setp(e.r32(PLAYER + 0x1C), 0, 1); e.transport(1)
    e.setp(st, 0, e.pat)
    e.ifc.clear(); hist = []
    for t in range(36):
        e.setp(st, 1, t // 6 % 16); e.setp(st, 2, t, 4)
        n0 = len(e.ifc); e.call(DISPATCH, PLAYER, tick_store, maxins=8_000_000)
        hist += [(t,) + x for x in e.ifc[n0:]]
    ons = [(t, n) for t, w, n in hist if w == "on"]
    gaps = {ons[i + 1][0] - ons[i][0] for i in range(len(ons) - 1)}
    check(len(ons) >= 5 and [n for t, n in ons[:3]] == [ra, ra + 4, ra + 7] and gaps == {6}, f"muted, playing: the arpeggio steps every 6 ticks, on the grid ({ons})")
    check(len([1 for t, w, n in hist if w == "off"]) >= len(ons) - 1, "each note stopped by the next")
    del e
    # ---- the count-in's tempo
    gc.collect(); e = P(img, man); site = int(rep["cibpm"]["labels"]["c_cibpm"], 16); import cibpm as CB
    e.setp(A.TEMPO, 0, 94)
    f0 = e.r8(CB.CLOCK + CB.O_FLAGS); e.uc.mem_write(CB.CLOCK + CB.O_FLAGS, bytes([f0 & ~2])); bp = e.r0(site, A.TEMPO, 0) & 0xFF
    e.uc.mem_write(CB.CLOCK + CB.O_FLAGS, bytes([f0 | 2])); e.w32(CB.CLOCK + CB.O_INC, ((133 << 32) + (1 << 31)) // CB.K_BPM); bs = e.r0(site, A.TEMPO, 0)
    check(bp == 94 and bs == 133, f"count-in: the project's tempo ({bp}), as a slave the measured one ({bs})")
    # ---- rollers and the drums' arpeggio
    def tempo_args(name):                                                               # ldr r0, =TEMPO; movs r1, #n, wherever the module has them
        base = int(rep[name]["arm_start"], 16) - 0x08010000; out = []
        for o in range(base, min(base + 16000, len(img) - 4), 2):
            x, y = struct.unpack_from("<HH", img, o)
            if x & 0xFF00 != 0x4800 or y & 0xFF00 != 0x2100: continue
            lit = (0x08010000 + o + 4 & ~3) + 4 * (x & 0xFF) - 0x08010000
            if struct.unpack_from("<I", img, lit)[0] == A.TEMPO: out.append(y & 0xFF)
        return out
    for name in ("rollers", "drumarp"):
        t = tempo_args(name)
        check(t and not any(t), f"{name}: stopped, the tempo from p0 ({t})")
    if beta:
        # ---- the chord screen's pad 16
        del e; e = fresh(img, man, False)
        e.tap(15); e.frame()
        check(e.r8(CH.CR + CH.O_FL) & 16, "pad 16 on")
        r = e.val(a); e.ifc.clear(); e.press(a); on = sorted(n for w, n in e.ifc if w == "on")
        check(on == sorted([r, r - 4, r - 7]), f"the inverse chord: {on}, root {r}")
        e.ifc.clear(); e.release(a); off = sorted(n for w, n in e.ifc if w == "off")
        check(off == on, f"no latch: the release stops it ({off})")
        e.tap(14); e.ifc.clear(); e.press(a); d = sorted(n for w, n in e.ifc if w == "on"); e.release(a)
        check(len(d) >= 3 and max(d) == r, f"with diatonic, mirrored too ({d})")
        e.tap(14); e.ifc.clear(); e.press(a); e.ifc.clear(); e.tap(15); ch = (sorted(n for w, n in e.ifc if w == "off"), sorted(n for w, n in e.ifc if w == "on")); e.release(a)
        check(ch == ([r - 7, r - 4], [r + 4, r + 7]), f"pad 16 off with the chord held: it changes at once {ch}")
        del e
        # ---- the flash
        gc.collect(); e = P(img, man); e.btn(0)
        beat = int(rep["clickflash"]["labels"]["c_vmbeat"], 16)
        skip = lambda uc, a_, s, d: uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        e.uc.hook_add(UC_HOOK_CODE, skip, begin=0x0803BD58, end=0x0803BD58)
        lv = []
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a_, s, d: (uc.reg_write(UC_ARM_REG_R0, lv[0]), skip(uc, a_, s, d)) if uc.reg_read(UC_ARM_REG_R0) == 0x21 and uc.reg_read(UC_ARM_REG_R1) == 9 else None, begin=0x08036192, end=0x08036192)
        def led(shift=False):
            e.frame(shift=shift)
            return struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138)))[55] & 0xFF
        lv.append(0); t = 200000; e.at(t); e.call(beat, 0xFF, 0, 0x60)
        l1 = led(); ls = led(True); e.at(t + 99); l2 = led(); e.at(t + 100); l3 = led()
        check(l1 == 0x45 and l2 == 0x45 and l3 != 0x45, f"level 0: Clear orange for 100 ms ({l1:#x}, {l2:#x}, {l3:#x})")
        check(ls != 0x45, f"with Shift: its own colours ({ls:#x})")
        lv[0] = 40; e.at(t + 200); e.call(beat, 0xFF, 0, 0x60); l4 = led()
        check(l4 != 0x45, f"a level above 0: no flash ({l4:#x})")
    print(f"{man.get('marker', '?')} CHORDFIX RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
