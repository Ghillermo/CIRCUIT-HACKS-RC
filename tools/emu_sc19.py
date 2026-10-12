"""SC19 ARM tests: drum controls, Master FX slot assignments and synth source modes saved in the project (tools/persist19.py).

    python tools/emu_sc19.py STOCK.bin SC18.3.bin SC19.bin SC19_manifest.json
Real routes: the controller's knob path (0x08033848 -> container -> drum macro handler slot 4), the DSP service tick (c_dtick19), the stock
save (0x0802F63C, through the hooked bl), the stock apply (0x0802EEFE, project load / new project / power-up) and the stock new-project
defaults (0x0802F5BC), on the live RAM dump with the real session manager object and record buffer.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc17_8 as T8  # noqa: E402  (applies the SC17.8 options to build_sc17)
from emu_sc17_7 import E7  # noqa: E402
from emu_sc08 import MGR  # noqa: E402
import build_sc17 as B  # noqa: E402
import build_sc14 as s14  # noqa: E402
import persist19 as P  # noqa: E402
import drums2_dsp as DD  # noqa: E402
import drums18 as K  # noqa: E402
import thumb  # noqa: E402

BASE = 0x08010000
OBJ = 0x2003D71C                               # session manager (stock save / load object)
BLOB = {P.CTX_SYNTH1: 0x20010044, P.CTX_SYNTH2: 0x2001019C, P.CTX_DRUMS: 0x200102F4, P.CTX_PROJECT: 0x20010324}
SIZE = {P.CTX_SYNTH1: 340, P.CTX_SYNTH2: 340, P.CTX_DRUMS: 44, P.CTX_PROJECT: 60}
REC = {P.CTX_SYNTH1: 0x26D14, P.CTX_SYNTH2: 0x26E68, P.CTX_DRUMS: 0x26FBC, P.CTX_PROJECT: 0x26FE8}
NEW_PROJECT, LOAD, SAVE = 0x0802F5BC, 0x0802EEFE, 0x0802F63C
DESC = {P.CTX_SYNTH1: 0x805454C, P.CTX_SYNTH2: 0x805454C, P.CTX_DRUMS: 0x8058FA0, P.CTX_PROJECT: 0x8057AD0}
BIPOLAR = (1, 3, 4, 5, 7)


def covered(stock, ctx):
    """byte offsets the stock parameter descriptors cover in a store"""
    d, size = DESC[ctx], SIZE[ctx]
    used, n = set(), 0
    while True:
        a = d - BASE + 8 * n
        off, kind = struct.unpack_from("<H", stock, a)[0], stock[a + 2]
        if off >= size + 8 or kind > 8 or n > 400: break
        used.add(off); n += 1
    return used


class E19(E7):
    def __init__(self, image, man):
        super().__init__(image, man)
        rep = man["report"]
        self.lab = {k: int(v, 16) for k, v in rep["persist19"]["labels"].items()}
        self.remap = bool(rep["persist19"].get("remap"))
        if self.remap:                                                               # the dump's drum views may be in chromatic mode (view + 0x51 bit 0): Shift + pitch is then the stock semitone bias
            from emu_sc08 import VIEWS
            for v in VIEWS: self.uc.mem_write(v + 0x51, b"\x00")
        self.s18 = {k: int(v, 16) for k, v in rep["sc18"]["labels"].items()}
        self.dw, self.chain, self.mark, self.sem = [], [], [], []
        def h(uc, a, s, d):
            if a == 0x080292F8:
                self.dw.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1) >> 8, uc.reg_read(UC_ARM_REG_R2)))
                uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
            elif a == self.s18["svc_next"]:
                self.chain.append(1); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
            elif a == 0x0803BDCC or a == 0x08021FDC:                    # MARK_DIRTY (takes the service semaphore) / its dirty-bit setter
                self.mark.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)))
            elif a == 0x08021064:                                        # the service semaphore take
                self.sem.append(1)
        self.uc.hook_add(UC_HOOK_CODE, h)
        for v in range(4):
            o = self.mh(v)
            if o: self.uc.mem_write(o + 0x31, b"\x00\x00\x00"); self.uc.mem_write(o + K.O_FLAGS, b"\x00\x00")     # as the constructor hook does

    def mh(self, d):
        self.call(self.s18["c_mh"], d); return self.uc.reg_read(UC_ARM_REG_R0)
    def sel(self, d): self.call(0x08033320, MGR, 4 + d, maxins=600000)
    # SC19.8+: the tests are written with the SC19.7 knob positions; (old knob, Shift) -> the knob of the same function in the panel-label layout
    OLD2NEW = {(0, False): (3, True), (0, True): (0, True), (1, False): (0, False), (1, True): (0, True), (2, False): (1, False), (2, True): (1, True),
               (3, False): (2, False), (3, True): (2, True), (4, False): (6, False), (4, True): (6, True), (5, False): (7, False), (5, True): (7, True),
               (6, False): (3, False), (6, True): (4, True), (7, False): (4, False), (7, True): (5, False)}
    def knob19(self, k, delta, shift=False):
        if self.remap: k, shift = self.OLD2NEW[(k, shift)]
        self._knob19(k, delta, shift)
    def _knob19(self, k, delta, shift=False):
        if shift: self.set_p0(self.r32(MGR + 0xC), 1)
        self.call(0x08033848, MGR, k, delta & 0xFFFFFFFF, maxins=900000)
        if shift: self.set_p0(self.r32(MGR + 0xC), 0)
    def macro(self, d, m):
        self.call(0x0803542C, self.r32(self.mh(d) + 0xC), m); return self.r8(self.uc.reg_read(UC_ARM_REG_R0))
    def xa(self, i): c, o = P.FLAT[i]; return BLOB[c] + o
    def xm(self, i): return self.r8(self.xa(i))
    def setxm(self, i, v): self.uc.mem_write(self.xa(i), bytes([v & 0xFF]))
    def ra(self, i): c, o = P.FLAT[i]; return self.r32(OBJ + 0x14) + REC[c] + o
    def setrec(self, i, v): self.uc.mem_write(self.ra(i), bytes([v & 0xFF]))          # the session RECORD (what a project load copies into the stores)
    def rec(self, i): return self.r8(self.ra(i))
    def xmall(self): return [self.xm(i) for i in range(P.N_XM)]
    def dflag(self, d):
        o = self.mh(d); return self.r8(o + K.O_FLAGS), self.r8(o + K.O_DELTA)
    def dirty(self, d):
        f, dl = self.dflag(d); return (f & 0x7F) | ((dl & 7) << 7)
    def dval(self, d, code):                           # signed / unsigned value of a code from XMEM
        b = self.xm(P.XM_DRUMS + 9 * d + code - 1)
        if code == 9: return b & 7
        v = b & 0x7F
        return v - 128 if (code in BIPOLAR and v >= 64) else v
    def dext(self, d): return sum(((self.xm(P.XM_DRUMS + 9 * d + k) >> 7) & 1) << k for k in range(8))
    def tick19(self):
        self.dw.clear(); self.chain.clear(); self.sem.clear()
        self.call(self.lab["c_dtick19"], maxins=3_000_000)
        self.sem_max = max(getattr(self, 'sem_max', 0), len(self.sem))
        return [x for x in self.dw if len(x) == 3]         # ES's own hook also records (addr, value) pairs
    def drain(self, n=14):
        out = []
        for _ in range(n):
            m = self.tick19()
            out.append(m)
            if not m and not self.flags(): break               # SC19.2: the staged work needs a second tick before the messages start
        return out
    def flags(self): return self.blkb(P.FLAGS)[0]
    def apply(self, flag=1): self.call(LOAD, OBJ, flag, maxins=30_000_000)
    def rslot(self, i): return self.blkb(P.S_SLOT + i)[0]


def msg(d, word_tag_code_val, DB=DD.DB, STRIDE=DD.STRIDE): return (0, word_tag_code_val, DB + STRIDE * d)


REF183_MAN = json.loads((Path(__file__).resolve().parent.parent / 'firmware/sc18.3/manifest.json').read_text())   # the reference image's own labels


def main(stock, ref, img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]
    lab = {k: int(v, 16) for k, v in rep["persist19"]["labels"].items()}
    s18 = {k: int(v, 16) for k, v in rep["sc18"]["labels"].items()}
    fx = int(rep["sc17"]["labels"]["c_fxtick"], 16)
    vt = lambda a: struct.unpack_from("<I", img, a - BASE)[0]
    # ---- installation
    check(vt(P.MH_SLOT4) == lab["c_dk19"] | 1, "drum macro handler slot 4 -> c_dk19")
    head = int(rep["vcf20"]["labels"]["c_vtick"], 16) if "vcf20" in rep else lab["c_dtick19"]                  # SC20: its tick is in front of c_dtick19 (and tail-calls it)
    check(img[s14.SVC_HOOK - BASE:s14.SVC_HOOK - BASE + 4] == thumb.b_w(s14.SVC_HOOK, head) and s18["svc_next"] == fx,
          f"DSP service chain head -> {'c_vtick -> ' if 'vcf20' in rep else ''}c_dtick19, then SC17's c_fxtick {hex(fx)}")
    check(img[P.LOAD_END - BASE:P.LOAD_END - BASE + 4] == thumb.b_w(P.LOAD_END, lab["c_pl_load"]), "end of the stock apply 0x0802F5B8 -> c_pl_load")
    check(img[P.NEW_TAIL - BASE:P.NEW_TAIL - BASE + 4] == thumb.b_w(P.NEW_TAIL, lab["c_pl_new"]), "tail of the stock new-project defaults 0x0802F5FA -> c_pl_new")
    check(img[P.SAVE_CALL - BASE:P.SAVE_CALL - BASE + 4] == thumb.bl(P.SAVE_CALL, lab["c_pl_save"]), "bl to the stock save 0x0802FE5E -> c_pl_save")
    # ---- the 65 bytes: unique, inside the stores, covered by no descriptor
    cov = {c: covered(stock, c) for c in DESC}
    check(len(set(P.FLAT)) == P.N_XM == 65 and all(o < SIZE[c] for c, o in P.FLAT), "65 distinct bytes inside their stores")
    bad = [(hex(c), o) for c, o in P.FLAT if o in cov[c]]
    check(not bad, f"no byte is covered by a stock parameter descriptor {bad}")
    check(all(not (c == P.CTX_SYNTH1 or c == P.CTX_SYNTH2) or (18 <= o <= 31 or o in (101, 103, 104) or 111 <= o <= 115) for c, o in P.FLAT), "synth bytes = the reserved ones")
    check(sum(1 for c, o in P.FLAT if c == P.CTX_DRUMS and o == 43) == 0, "drums offset 43 (last byte of the store) is not used")

    # ---- drum knobs write the XMEM bytes, mark them dirty, the stock handlers are left alone
    for d in range(4):
        gc.collect()
        e = E19(img, man); e.sel(d)
        base = P.XM_DRUMS + 9 * d
        e.setxm(P.XM_SIG, e.xm(P.XM_SIG))
        e.knob19(0, 3); e.knob19(0, 2)
        check(e.dval(d, 7) == 5 and e.dirty(d) == 1 << 6, f"drum {d+1} K1 +3 +2: envelope = 5 (code 7), dirty bit 7 {e.dval(d, 7)} {e.dirty(d):#x}")
        e.knob19(0, -70); check(e.dval(d, 7) == -64 and e.xm(base + 6) & 0x7F == 0x40, "K1 -70: clamps at -64 (two's complement in 7 bits)")
        e.knob19(0, 4, shift=True); check(e.dval(d, 1) == 4 and e.xm(base) & 0x7F == 4, "Shift + K1: code 1 (pitch env) = 4")
        e.knob19(2, -3); check(e.dval(d, 2) == 0 and not e.dirty(d) & 2, "K3 -3 at 0: unipolar, unchanged, not dirty")
        e.knob19(2, 90); e.knob19(2, 90); check(e.dval(d, 2) == 127, "K3 +180: clamps at 127")
        e.knob19(2, 6, shift=True); check(e.dval(d, 8) == 6, "Shift + K3: code 8 (ring mod amount) = 6")
        e.knob19(4, -9); check(e.dval(d, 3) == -9, "K5: code 3 (LFO) = -9")
        e.knob19(4, 7, shift=True); check(e.dval(d, 4) == 7, "Shift + K5: code 4 (LFO speed) = 7")
        e.knob19(6, 12); check(e.dval(d, 5) == 12, "K7: code 5 (env -> cutoff) = 12")
        e.knob19(7, 50, shift=True); check(e.dval(d, 6) == 50, "Shift + K8: code 6 (resonance) = 50")
        seq = []
        for _ in range(6): e.knob19(6, 1, shift=True); seq.append(e.dval(d, 9))
        check(seq == [1, 2, 3, 4, 0, 1], f"Shift + K7: filter mode steps and wraps 0..4 {seq}")
        e.knob19(6, -1, shift=True); e.knob19(6, -9, shift=True)
        check(e.dval(d, 9) == 4, f"Shift + K7 turned left: 0 -> 4 (wraps) {e.dval(d, 9)}")
        check(e.dirty(d) == 0x1FF, f"dirty bits of the nine codes {e.dirty(d):#x}")
        # other drums untouched
        for o in range(4):
            if o != d: check(all(e.dval(o, c) == 0 for c in range(1, 10)) and e.dirty(o) == 0, f"drum {o+1} untouched by the knobs of drum {d+1}")
    # extended values K4 / K6
    for d in (0, 3):
        for k, m, sh in ((3, 1, 0), (5, 2, 4)):
            gc.collect()
            e = E19(img, man); e.sel(d)
            steps = 0
            while e.macro(d, m) > 0 and steps < 200: e.knob19(k, -1); steps += 1
            check(e.dext(d) == 0 and e.dirty(d) == 0, f"drum {d+1} K{k+1}: stock value to 0 in {steps} clicks, the extended value stays 0")
            e.knob19(k, -1); e.knob19(k, -3)
            check((e.dext(d) >> sh) & 15 == 4 and e.macro(d, m) == 0 and e.dirty(d) == 1 << 9, f"K{k+1}: 4 more clicks left -> extended {(e.dext(d) >> sh) & 15}, dirty (ext)")
            e.knob19(k, -40); check((e.dext(d) >> sh) & 15 == 15, "clamps at 15")
            e.knob19(k, 10); e.knob19(k, 3); check((e.dext(d) >> sh) & 15 == 2 and e.macro(d, m) == 0, "right turn: the extended value comes back first (15 -> 2)")
            e.knob19(k, 5); check((e.dext(d) >> sh) & 15 == 0 and e.macro(d, m) == 0, "right turn past it: stops at 0")
            e.knob19(k, 2); check(e.macro(d, m) == 2, f"then the stock value moves ({e.macro(d, m)})")
    # ext bits live in bit 7 of the value bytes: turning a value knob keeps them
    gc.collect()
    e = E19(img, man); e.sel(1)
    for k in range(8): e.setxm(P.XM_DRUMS + 9 + k, 0x80)
    e.knob19(0, 5); e.knob19(4, -3); e.knob19(7, 9, shift=True)
    check(e.dext(1) == 0xFF and e.dval(1, 7) == 5 and e.dval(1, 3) == -3 and e.dval(1, 6) == 9, f"value turns keep the extended bits (ext {e.dext(1):#x})")
    # knobs the patches do not use: same writes as SC18.3
    remap = bool(rep["persist19"].get("remap"))
    def writes(image, k, sh):
        gc.collect(); x = E19(image, man) if image is img else E7(image, REF183_MAN)
        for dd in range(4):                                  # as the constructor hook does (the dump's padding bytes are not zero)
            o = x.r32(x.r32(x.r32(x.r32(0x200069E4) + 0x40) + 0x2C) + 0x158 + 4 * dd)
            if o: x.uc.mem_write(o + 0x31, bytes(1)); x.uc.mem_write(o + K.O_FLAGS, bytes(2))
        if remap:
            from emu_sc08 import VIEWS
            for v in VIEWS: x.uc.mem_write(v + 0x51, bytes([0]))              # both sides not chromatic
        log = []
        def h(uc, a, s_, d_):
            if a == 0x08031A98: log.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2)))
        x.uc.hook_add(UC_HOOK_CODE, h)
        x.call(0x08033320, MGR, 5, maxins=600000)
        if sh: x.set_p0(x.r32(MGR + 0xC), 1)
        x.call(0x08033848, MGR, k, (-3) & 0xFFFFFFFF, maxins=900000)
        if sh: x.set_p0(x.r32(MGR + 0xC), 0)
        return log
    for k, sh in ((1, False), (1, True), (7, False), (3, False), (5, False)):
        if remap and (k, sh) == (1, True): continue                                      # Shift + pitch is the pitch envelope there (emu_sc19_8.py covers the layout)
        a, b = writes(img, *(E19.OLD2NEW[(k, sh)] if remap else (k, sh))), writes(ref, k, sh)
        check(a == b, f"K{k+1}{' + Shift' if sh else ''}: the stock parameter writes are the same as SC18.3 {a}")

    # ---- the service tick: one absolute message per drum per tick, lowest code first, tag toggling
    gc.collect()
    e = E19(img, man); e.sel(2)
    e.knob19(0, -7); e.knob19(2, 20); e.knob19(4, 5, shift=True)
    e.setxm(P.XM_SIG, 0)
    out = e.drain()
    c7, c2, c4 = 7, 2, 4
    exp = [[msg(2, (1 << 23) | (2 << 16) | 20)], [msg(2, (0 << 23) | (4 << 16) | 5)], [msg(2, (1 << 23) | (7 << 16) | (-7 & 0xFFFF))], []]
    check(out == exp and all(True for _ in out), f"drum 3: messages in code order (2, 4, 7), tag toggling 1, 0, 1, absolute values {[[(hex(w)) for _, w, _ in m] for m in out]}")
    check(e.dirty(2) == 0 and e.chain == [1], "dirty bits cleared; the previous chain head still runs")
    # ---- extended message goes to X:DB + EXT with the 8-bit value
    gc.collect()
    e = E19(img, man); e.sel(0)
    for k in range(8): e.setxm(P.XM_DRUMS + k, 0x80 if k in (1, 4, 7) else 0)
    o = e.mh(0); e.uc.mem_write(o + K.O_DELTA, bytes([4]))
    out = e.tick19()
    check(out == [(0, 0x92, DD.DB + DD.EXT)], f"extended values -> X:DB+{DD.EXT} = 0x92 {[(hex(v), hex(ad)) for _, v, ad in out]}")

    # ---- project load: the deferred work in the tick
    def prep(e, sig=True):
        """XMEM with data: drum 0 values, slot 2 (Gater, params 11 22 33 44), modes 2 and 4, ext 0x35"""
        for i in range(P.N_XM): e.setrec(i, 0)
        vals = {1: 4, 2: 100, 3: -20, 4: 9, 5: -3, 6: 77, 7: 31, 8: 5}
        for c, v in vals.items(): e.setrec(P.XM_DRUMS + c - 1, v & 0x7F)
        e.setrec(P.XM_DRUMS + 8, 3 | ((P.SIG << 3) if sig else 0))
        for k in range(8): e.setrec(P.XM_DRUMS + k, e.rec(P.XM_DRUMS + k) | (((0x35 >> k) & 1) << 7))
        for i, v in enumerate((11, 22, 33, 44)): e.setrec(P.XM_SLOTS + 8 + i, v | (0x80 if i == 3 else 0))      # slot 2: effect 0 (Gater), assigned
        e.setrec(P.XM_MODES, 2 | (4 << 3))
        return vals
    gc.collect()
    e = E19(img, man); e.grid()
    vals = prep(e)
    e.pad(0, shift=True); e.rel(0); e.pad(29, shift=True); e.rel(29)                    # Gater latched, SC14 AF latched
    e.setsp(ls=5, le=12); e.uc.mem_write(e.blk + B.S_SLOTH, bytes([4])); e.uc.mem_write(e.s14 + 4, bytes([2]))
    check(e.flags() == 0, "before the apply: no pending work")
    e.apply(1)
    check(e.flags() == P.F_RESYNC, f"stock apply (project load): RESYNC set by the hook {e.flags()}")
    e.mark.clear()
    out = e.drain(14)
    d0 = [w for m in out for (_, w, ad) in m if ad == DD.DB]
    codes = [(w >> 16) & 15 for w in d0]
    got_v = [((w >> 16) & 15, w & 0xFFFF) for w in d0]
    want = [(c, (vals[c] & 0xFFFF) if c <= 8 else 3) for c in range(1, 10)]
    check(got_v == want, f"drum 1: nine absolute messages in code order {[(c, hex(v)) for c, v in got_v]}")
    tags = [(w >> 23) & 1 for w in d0]
    check(tags == [1, 0, 1, 0, 1, 0, 1, 0, 1], f"tags toggle {tags}")
    exts = [(v, ad) for m in out for (_, v, ad) in m if ad == DD.DB + DD.EXT]
    check(exts == [(0x35, DD.DB + DD.EXT)], f"extended values sent once: {[(hex(v), hex(ad)) for v, ad in exts]}")
    check(all(e.dirty(d) == 0 for d in range(4)), "every dirty bit sent")
    n_msgs = [len([1 for _, _, ad in [x for m in out for x in m] if DD.DB + DD.STRIDE * d <= ad < DD.DB + DD.STRIDE * (d + 1)]) for d in range(4)]
    check(n_msgs == [10, 10, 10, 10], f"messages per drum {n_msgs} (nine codes + the extended values, every dirty bit)")
    check([e.rslot(8 + i) for i in range(4)] == [11, 22, 33, 44 | 0x80] and all(e.rslot(i) == 0 for i in range(8)) and all(e.rslot(12 + i) == 0 for i in range(16)),
          "slots: XMEM -> RAM")
    check(e.s14b(18) == 2 and e.s14b(19) == 4 and (0x20, 48) in e.mark, f"synth modes 2 / 4 -> SC14 state, Audio In group resent {e.s14b(18)} {e.s14b(19)} {e.mark}")
    check(e.blkb(B.S_LATCH)[0] == 0 and e.s14b(5) == 0 and e.sp() == (0, 0, 0, 0) and e.blkb(B.S_SLOTH)[0] == 0 and e.s14b(4) == 0 and e.s14b(6) == 0 and e.s14b(7) == 0,
          "Master FX effects, SC14 effects, held pads and the song pointer are off")
    check(e.flags() == 0, "RESYNC cleared")
    e.tick19(); check(e.dw == [] , "nothing more to send afterwards")
    # no signature: the zone is cleared (project saved by stock or by the diagnostic builds)
    for junk in (0xA5, 0x15):
        gc.collect()
        e = E19(img, man); e.grid(); prep(e, sig=False)
        for i in range(P.N_XM): e.setrec(i, junk if i % 2 else e.rec(i))
        e.setrec(P.XM_SIG, (e.rec(P.XM_SIG) & 7) | (((P.SIG + 1) & 31) << 3))
        e.apply(1); e.drain(3)
        check(e.xmall() == [0] * P.N_XM, f"no signature (junk {junk:#x}): the 65 bytes are cleared")
        check(all(e.rslot(i) == 0 for i in range(28)) and e.s14b(18) == 0 and e.s14b(19) == 0, "slots and modes are the defaults")
    # invalid values are repaired
    gc.collect()
    e = E19(img, man); e.grid(); prep(e)
    for i, v in enumerate((1, 1, 1, 0x80)): e.setrec(P.XM_SLOTS + i, v | 0x80)          # slot 0: effect 7, assigned
    e.setrec(P.XM_SLOTS + 3, 0x80 | 3)
    e.setrec(P.XM_MODES, 7 | (7 << 3))                                                   # 7 is not a mode in any build (modes 0..4, or 0..6 with the return modes)
    e.apply(1); e.drain(3)
    check(e.rslot(3) & 0x80 == 0 and e.s14b(18) == 0 and e.s14b(19) == 0, f"an effect > 5 is unassigned, modes > 4 are 0 {e.rslot(3):#x} {e.s14b(18)} {e.s14b(19)}")
    # new project: even a valid signature is dropped (the record keeps the previous project's bytes)
    gc.collect()
    e = E19(img, man); e.grid(); prep(e)
    e.call(NEW_PROJECT, OBJ, maxins=30_000_000)
    check(e.flags() == P.F_NEW, f"stock new-project defaults: NEW set by the hook {e.flags()}")
    for i in range(P.N_XM): e.setrec(i, e.xm(i) or 0)
    e.apply(1)
    check(e.flags() == P.F_NEW | P.F_RESYNC, "then the stock apply: RESYNC too")
    prep(e)                                                                        # the previous project's bytes are still there after the apply
    e.drain(3)
    check(e.xmall() == [0] * P.N_XM and all(e.rslot(i) == 0 for i in range(28)) and e.s14b(18) == 0, "new project: everything starts clean")
    out = e.drain(1)
    # the work waits until the four drum handlers exist
    gc.collect()
    e = E19(img, man); e.grid(); prep(e)
    e.apply(1)
    cont = e.r32(e.r32(e.r32(0x200069E4) + 0x40) + 0x2C)
    e.uc.mem_write(e.r32(e.r32(0x200069E4) + 0x40) + 0x2C, b"\0\0\0\0")
    e.tick19()
    check(e.flags() == P.F_RESYNC and all(e.rslot(i) == 0 for i in range(28)), "no drum handlers yet: the work waits, nothing is changed")
    e.uc.mem_write(e.r32(e.r32(0x200069E4) + 0x40) + 0x2C, struct.pack("<I", cont))
    e.drain(3)
    check(e.flags() == 0 and e.rslot(8) == 11, "handlers exist: done on the next tick")

    # ---- save: XMEM <- RAM right before the stock save, record gets it
    gc.collect()
    e = E19(img, man); e.grid()
    for i in range(P.N_XM): e.setxm(i, 0)
    for i, v in enumerate((9, 8, 7, 0x80 | 6)): e.uc.mem_write(e.blk + B.S_SLOT + 4 * 5 + i, bytes([v]))
    e.uc.mem_write(e.s14 + 18, bytes([4, 6]))
    e.sel(1); e.knob19(0, 8)
    e.call(lab["c_pl_save"], OBJ, maxins=8_000_000)
    check([e.xm(P.XM_SLOTS + 20 + i) for i in range(4)] == [9, 8, 7, 0x86] and e.xm(P.XM_MODES) == (4 | 6 << 3), "save: slots and modes copied to XMEM")
    check(e.xm(P.XM_SIG) >> 3 == P.SIG, f"save: signature written {e.xm(P.XM_SIG) >> 3}")
    buf = e.r32(OBJ + 0x14)
    rec = {c: bytes(e.uc.mem_read(buf + REC[c], SIZE[c])) for c in REC}
    live = {c: bytes(e.uc.mem_read(BLOB[c], SIZE[c])) for c in BLOB}
    check(rec == live, "the stock save copied the four blobs, with the reserved bytes, into the session record")
    check(e.dval(1, 7) == 8, "the drum value was already in the stores (store-as-truth)")
    # no copy while a load is pending
    e2 = E19(img, man); e2.grid()
    for i in range(P.N_XM): e2.setxm(i, 0)
    e2.uc.mem_write(e2.blk + B.S_SLOT, bytes([5])); e2.uc.mem_write(e2.blk + P.FLAGS, bytes([P.F_RESYNC]))
    e2.call(lab["c_pl_save"], OBJ, maxins=8_000_000)
    check(e2.xm(P.XM_SLOTS) == 0 and e2.xm(P.XM_SIG) == 0, "RESYNC pending: the stale RAM is not copied (the project data is not overwritten)")

    # ---- the whole cycle: edit, save, change project (wipe), load -> restored
    gc.collect()
    e = E19(img, man); e.grid(); e.sel(3)
    for i in range(P.N_XM): e.setxm(i, 0)
    e.knob19(0, 11); e.knob19(2, 33); e.knob19(4, -17, shift=True); e.knob19(6, 3, shift=True)
    for i, v in enumerate((12, 34, 56, 0x80)): e.uc.mem_write(e.blk + B.S_SLOT + 4 * 1 + i, bytes([v]))
    e.uc.mem_write(e.s14 + 18, bytes([3, 1]))
    e.call(lab["c_pl_save"], OBJ, maxins=8_000_000)
    saved = e.xmall()
    for i in range(P.N_XM): e.setxm(i, 0)                                          # "another project" in the stores (record kept)
    e.uc.mem_write(e.blk + B.S_SLOT, bytes(28)); e.uc.mem_write(e.s14 + 18, bytes([0, 0]))
    e.drain(12)
    e.apply(0)                                                                     # project load: the record -> the stores
    out = e.drain(14) if rep["persist19"].get("rec_restore") else None             # SC19.4+: the synth bytes come from the record at the next tick (the stock copy keeps the live ones)
    check(e.xmall() == saved and any(saved), "load: the stores carry what was saved")
    if out is None: out = e.drain(14)
    d3 = [((w >> 16) & 15, w & 0xFFFF) for m in out for (_, w, ad) in m if ad == DD.DB + 3 * DD.STRIDE]
    got = dict(d3)
    check(got.get(7) == 11 and got.get(2) == 33 and got.get(4) == (-17 & 0xFFFF) and got.get(1) == 0 and e.dval(3, 5) == 0,
          f"drum 4 values resent after the load {sorted(got.items())}")
    check([e.rslot(4 + i) for i in range(4)] == [12, 34, 56, 0x80] and e.s14b(18) == 3 and e.s14b(19) == 1, "slots and modes restored in RAM")
    # ---- fixes from the hardware: LEDs of the FX view buttons, chromatic drum view, synth source modes
    from emu_sc18_2 import E182
    from emu_sc08 import E8, VIEWS
    fxl = {int(k): int(v, 16) for k, v in rep["leds18"]["fx_leds"].items()}
    def fx_frame(image):
        gc.collect(); x = E182(image); x.btn(15); return x.frame()
    f19, f18, fst = fx_frame(img), fx_frame(ref), fx_frame(stock)
    check(f19[53] == fxl[53] and 53 in fxl and 48 not in fxl, f"FX view: the LED of the real 1-16 / 17-32 button (53) is {hex(f19[53])} (green), Record's (48) is not in the list {fxl}")
    check(f19[48] == fst[48] and f19[49] == fst[49], f"Record / Play LEDs (48 / 49) as stock ({hex(f19[48])}, {hex(f19[49])})")
    check(all(f19[i] == f18[i] for i in range(69) if i not in (48, 53)), "every other LED of the FX view as SC18.3")
    check(f19[48] != f18[48] and f18[53] != f19[53], "LED 48 and LED 53 are the two that changed from SC18.3")
    if len(sys.argv) > 5:
        ref8 = Path(sys.argv[5]).read_bytes()
        for d in range(4):
            rows = {}
            for name, image in (("sc17.8", ref8), ("sc19", img)):
                gc.collect(); x = E8(image)
                for v in VIEWS: x.uc.mem_write(v + 0x51, bytes(3))
                x.setflag(VIEWS[d], True)
                x.call(x.r32(x.r32(VIEWS[d]) + 0x1C), VIEWS[d], maxins=900000); p_ = x.uc.reg_read(UC_ARM_REG_R0)
                rows[name] = list(struct.unpack("<32H", bytes(x.uc.mem_read(p_, 64))))
            if rep["D"].get("marker") in ("SC20.1", "SC20.2", "SC21", "SC21.1", "SC21.2", "SC21.3", "SC21.4", "SC22", "SC22.1", "SC22.2", "SC22.3", "SC22.4", "SC23", "SC23.1", "SC23.2", "SC23.3", "SC23.4", "SC23.5", "SC23.6", "SC24", "SC25", "SC26", "SC27", "SC28", "SC29", "SC30", "SC31", "SC32", "SC33", "SC34"):                      # SC20.1: the scale keyboard has three rows (the top row is dark), the rest as before
                check(not any(rows["sc19"][:8]) and rows["sc19"][8:] == rows["sc17.8"][8:] and any(rows["sc19"][8:16]) and any(rows["sc19"][16:]), f"drum {d+1} scale view: top row dark, the three lower rows as before")
            else:
                check(rows["sc19"] == rows["sc17.8"] and any(rows["sc19"][:16]) and any(rows["sc19"][16:]), f"drum {d+1} chromatic view: all four rows lit, as before SC18.1")
    pk = rep["persist19"]
    check(vt(0x0805ABBC + 0x1C) == int(rep["sc08"]["labels"]["c_dleds"], 16) | 1, "drum Preset view LED slot = SC08's c_dleds (no dark rows)")
    check(rep["linein3"]["modes"] == rep["persist19"].get("modes", 5), f"synth source modes: the UI ({rep['linein3']['modes']}) and the saved-settings validation ({rep['persist19'].get('modes', 5)}) agree")
    print("SC19 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    st, rf, im = (Path(sys.argv[i]).read_bytes() for i in (1, 2, 3))
    sys.exit(1 if main(st, rf, im, json.loads(Path(sys.argv[4]).read_text())) else 0)
