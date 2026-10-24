"""SC46.2 / Beta 3.19 (tools/gmdrum.py): the GM mode of the drums' MIDI out, through the controller (knobs, pads), the real LED task and the
transmitter's vtable entries (the drums = track 16, notes 60 / 62 / 64 / 65):
  * without our signature: mode off, a drum's note-on / note-off goes out as before; the Setup view's K4 dim, K5..K8 dim in the drums' colours;
  * Setup K4 to the right = on: signature, flags and the defaults 36 / 38 / 42 / 46 in both copies of the settings store, the save asked of lazysave;
    Drum 1..4 go out as their GM notes, the note-off the note its note-on had; other notes / tracks untouched;
  * K5 (Drum 1) one note up: it sounds once (on 100 / off) on track 16, its number drawn on the 32 pads in Drum 1's colour (vcf21's c_ednum), no
    save asked yet; a Setup pad meanwhile goes nowhere; Shift = confirmed (the pads back, the save asked); K8 then leaving the Setup view = the same;
  * clamped to 35..81; a note-off after a change = the note that sounded; K1..K3 nothing; the Advanced page: nothing; K4 to the left = off again;
  * the previous build (if given): K5 in the Setup view changes nothing, Drum 1 goes out as 60.

    python tools/emu_gmdrum.py BUILD.bin manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import lazysave as LZ  # noqa: E402
import pgmch as PG  # noqa: E402
import gmdrum as G  # noqa: E402
import leds18  # noqa: E402

MGR = T.MGR
SCRATCH = 0x2004F000


class EG(T.EL):
    def __init__(self, img, man):
        super().__init__(img)
        self.img = img
        R = man["report"]
        self.gl = {k: int(v, 16) for k, v in R["gmdrum"]["labels"].items()} if "gmdrum" in R else {}
        self.ednum = int(R["vcf20"]["labels"]["c_ednum"], 16)
        self.tx_on = struct.unpack_from("<I", img, G.TX_VT - 0x08010000)[0] & ~1
        self.tx_off = struct.unpack_from("<I", img, G.TX_VT + 4 - 0x08010000)[0] & ~1
        pv = R["gmdrum"]["prev"] if "gmdrum" in R else None
        self.p_on = int(pv["on"], 16) if pv else self.tx_on
        self.p_off = int(pv["off"], 16) if pv else self.tx_off
        self.p_pad = int(pv["pad"], 16) if pv else None
        self.sent, self.pads = [], 0
        def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        def cap(kind):
            def f(uc, a, s, d):
                self.sent.append((kind, uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3))); skip(uc)
            return f
        self.uc.hook_add(UC_HOOK_CODE, cap("on"), begin=self.p_on, end=self.p_on)
        self.uc.hook_add(UC_HOOK_CODE, cap("off"), begin=self.p_off, end=self.p_off)
        if self.p_pad:
            def padhit(uc, a, s, d): self.pads += 1
            self.uc.hook_add(UC_HOOK_CODE, padhit, begin=self.p_pad, end=self.p_pad)
        self.setup(True)
    def knob(self, k, d): self.call(0x08033848, MGR, k, d & 0xFFFFFFFF, maxins=8_000_000)
    def shift(self, on): self.set_p0(self.r32(MGR + 0xC), 1 if on else 0)
    def setup(self, on, adv=0):
        self.set_p0(self.r32(MGR + PG.MODE_STORE), PG.MODE_SETUP if on else 0); self.w32(MGR + 0x6C, 0)
        self.uc.mem_write(PG.SETUP_OBJ + PG.ADV_OFF, bytes([adv]))
    def store(self): return self.r32(self.r32(self.r32(PG.CTX)) + 0x54)
    def param(self, i, copy):
        self.call(PG.PARAM_WPTR if copy else PG.PARAM_GET, self.store(), i, maxins=1_000_000)
        return bytes(self.uc.mem_read(self.uc.reg_read(UC_ARM_REG_R0), 4))
    def tail(self): return self.r32(LZ.SESSION_OBJ + 0x14) + LZ.TAIL
    def pending(self): return self.r8(self.tail() + LZ.O_PEND) == LZ.PEND
    def unpend(self): self.uc.mem_write(self.tail() + LZ.O_PEND, b"\0")
    def note(self, kind, track, n, vel=100):
        self.sent.clear(); self.call(self.tx_on if kind == "on" else self.tx_off, G.TX, track, n, vel if kind == "on" else 0, maxins=2_000_000)
        return [s[2] for s in self.sent if s[0] == kind and s[1] == track]
    def edit(self): return self.r8(G.RAM + G.O_EDIT) if self.gl else 0
    def number(self, n, col):
        self.uc.mem_write(SCRATCH, bytes(64)); self.call(self.ednum, SCRATCH, n, col, maxins=1_000_000)
        return list(struct.unpack("<32H", bytes(self.uc.mem_read(SCRATCH, 64))))


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    raw = Path(img).read_bytes()
    dc = leds18.drum_codes(raw)
    e = EG(raw, man)
    f0 = X.frame(e)
    check([e.note("on", 0x10, n) for n in (60, 62, 64, 65)] == [[60], [62], [64], [65]] and e.note("off", 0x10, 60) == [60],
          "no signature: the drums go out with the stock's notes")
    check(f0[60 + 3] == 0x2000 | G.COL_OFF and all(f0[64 + d] == (6 << 8 | dc[d]) for d in range(4)),
          f"Setup: K4 dim, K5..K8 dim in the drums' colours ({[hex(x) for x in f0[63:68]]})")
    e.unpend(); e.knob(3, 1)
    p4 = [e.param(4, c) for c in (0, 1)]
    check(all(p[1] == G.SIG and p[2] & 1 and p[3] == 36 for p in p4) and all(e.param(4 + d, c)[1] == G.DEFAULTS[d] for d in (1, 2, 3) for c in (0, 1)),
          f"K4 right: on, the signature and the defaults in both copies ({[p.hex() for p in p4]})")
    check(e.pending(), "K4: the save asked of lazysave")
    got = [e.note("on", 0x10, n) for n in (60, 62, 64, 65)]
    check(got == [[36], [38], [42], [46]], f"on: Drum 1..4 go out as 36 / 38 / 42 / 46 ({got})")
    check(e.note("off", 0x10, 60) == [36] and e.note("on", 0x10, 61) == [61] and e.note("on", 2, 60) == [60],
          "the note-off the GM note; another note of track 16 / another track untouched")
    f1 = X.frame(e)
    check(f1[60 + 3] == 0x7F00 | G.COL_ON and f1[64] == ((36 - 34) * 2 << 8 | dc[0]), f"K4 green, K5 after the note ({hex(f1[63])}, {hex(f1[64])})")
    e.unpend(); e.sent.clear(); e.knob(4, 1)
    check(not [s for s in e.sent if s[0] == "on"] and e.edit() == 1, "K5 one click: no note yet (2 clicks a note), the number shown")
    e.sent.clear(); e.knob(4, 1)
    check(e.sent == [("on", 0x10, 37, 100), ("off", 0x10, 37, 0)], f"K5 a note up: 37 sounds once on track 16 ({e.sent})")
    f2 = X.frame(e)
    check(f2[:32] == e.number(37, dc[0]), f"its number on the pads in Drum 1's colour ({[hex(x) for x in f2[:32]]})")
    check(not e.pending() and e.param(4, 0)[3] == 37 and e.param(4, 1)[3] == 37, "the note in both copies, no save asked yet")
    n0 = e.pads; e.pad(0)
    check(e.pads == n0 and e.edit() == 1, "a Setup pad meanwhile goes nowhere")
    e.shift(True); X.frame(e); e.shift(False)
    f3 = X.frame(e)
    check(e.edit() == 0 and e.pending() and f3[:32] == f0[:32], "Shift: confirmed, the save asked, the Setup's pads back")
    e.unpend(); e.knob(7, -2)
    check(e.param(7, 0)[1] == 45 and e.edit() == 4 and not e.pending(), "K8 a note down: Drum 4 = 45, its number shown")
    check(X.frame(e)[:32] == e.number(45, dc[3]), "Drum 4's number in its colour")
    e.setup(False); X.frame(e)
    check(e.edit() == 0 and e.pending(), "leaving the Setup view: confirmed, the save asked")
    e.setup(True)
    check(e.note("on", 0x10, 65) == [45], "Drum 4 goes out as 45")
    e.note("on", 0x10, 60); e.knob(4, -400)
    check(e.param(4, 0)[3] == G.NMIN and e.note("off", 0x10, 60) == [37], "K5 far left: 35; the note-off = the note that sounded (37)")
    e.knob(4, 400)
    check(e.param(4, 0)[3] == G.NMAX, "K5 far right: 81")
    e.shift(True); X.frame(e); e.shift(False)
    before = [e.param(i, 0) for i in range(3, 8)]
    for k in (0, 1, 2): e.knob(k, 6)
    e.setup(True, adv=1); e.knob(4, -6); e.knob(3, -1); e.setup(True)
    check([e.param(i, 0) for i in range(3, 8)] == before and e.edit() == 0, "K1..K3 and the Advanced page: nothing")
    e.knob(3, -1)
    check(e.note("on", 0x10, 60) == [60] and e.param(4, 0)[2] & 1 == 0, "K4 left: off, Drum 1 = 60 again")
    del e; gc.collect()
    if prev:
        p = EG(Path(prev).read_bytes(), pman)
        p.knob(3, 1); p.knob(4, 4)
        check(p.param(4, 0)[1:] == b"\0\0\0" and p.note("on", 0x10, 60) == [60], "the previous build: the Setup's knobs change nothing, Drum 1 = 60")
        del p; gc.collect()
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text()), a[2] if len(a) > 2 else None,
                       json.loads(Path(a[3]).read_text()) if len(a) > 3 else None) else 0)
