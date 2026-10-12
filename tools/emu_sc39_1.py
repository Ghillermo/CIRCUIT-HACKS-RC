"""SC39.1 ARM tests (live RAM dump, the real routes: the controller's buttons 0x08033320 / 0x0803381A and pads, the LED task, the stock content API on
emu_sc35's model of the SD card): the patches of the MIDI tracks' own synth (tools/mpatch.py).

    python tools/emu_sc39_1.py SC39.1.bin SC39.1_manifest.json SC39.bin SC39_manifest.json
  * MIDI 1, Preset: rows 2-3 dark (nothing saved), Octave down lit / up dark (page 1 of 4);
  * Duplicate (the real button: the container accepts it there now) + pad 9: the bank is created = the stock's Initial Patch + the 172 bytes of padding
    with the patch (the engine bits, the step-drummer nibble, 26 + 8 values, the sum); the pad bright; the shared buffer's lock balanced;
  * the engine changed, pad 9: every byte back, everything marked to be sent again; MIDI 2, pad 9: the same patch in the other track;
  * pad 14 with a bank of 3 patches: its padding completed with 0xFF, records 4 / 5 = the Initial Patch, record 6 = the Initial Patch + the patch; the
    three patches untouched; the LEDs: both slots lit, the last one bright;
  * an empty slot and a slot with a wrong sum: nothing loaded, nothing written; Clear + pad: the padding 0xFF again, the pad dark;
  * Octave down / up: the pages (0..3, no wrap), their LEDs, a save on page 2 goes to bank 2;
  * the card changed behind: nothing read before 4 s, then the new state;
  * the CC editor on: the pads and Octave are not ours; the previous build: nothing.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R4
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc36 as T36  # noqa: E402  (configures vcf21 as SC36: the layout of the engine's state)
from emu_sc35 import E35, MGR, TICK, PK, set_loaded  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
import emu_sc38_8 as T8  # noqa: E402
import mpatch as MP  # noqa: E402

V = T36.V
B = 0x08010000
INIT = None


def patch_bytes(flags, sd, vals, v2):
    body = bytes([flags, sd]) + bytes(v & 0xFF for v in vals) + bytes(v & 0xFF for v in v2)
    return struct.pack("<I", MP.MAGIC4) + body + bytes([sum(body) & 0xFF, 1])


class EM(E35):
    real_dup = True

    def gfst(self):
        self.call(self.lab["c_gfst"]); return self.uc.reg_read(UC_ARM_REG_R0)

    def set_engine(self, t, flags, sd, vals, v2):
        """the engine of track t as a patch describes it"""
        T = V.TAIL
        f = self.r8(T + V.O_FLAGS) & ~(5 << t) | 0x80 | ((flags & 1) << t) | ((flags >> 1 & 1) << (t + 2)); self.uc.mem_write(T + V.O_FLAGS, bytes([f]))
        s = self.r8(T + V.O_SIG) & ~(5 << t) | ((flags >> 2 & 1) << t) | ((flags >> 3 & 1) << (t + 2)); self.uc.mem_write(T + V.O_SIG, bytes([s]))
        for off, bit in ((V.RT_VEL, 4), (V.RT_NOTE, 5)):
            a = T + V.O_RT + 8 * t + off; self.uc.mem_write(a, bytes([self.r8(a) & 0x7F | (flags >> bit & 1) << 7]))
        a = T + V.O_SD; self.uc.mem_write(a, bytes([self.r8(a) & ~(15 << 4 * t) | sd << 4 * t]))
        self.uc.mem_write(T + V.STRIDE * t + V.O_PAR, bytes(v & 0xFF for v in vals))
        self.uc.mem_write(self.gfst() + V.V2_OFF + 8 * t, bytes(v & 0xFF for v in v2))

    def engine(self, t):
        T = V.TAIL
        f, s = self.r8(T + V.O_FLAGS), self.r8(T + V.O_SIG)
        flags = (f >> t & 1) | (f >> (t + 2) & 1) << 1 | (s >> t & 1) << 2 | (s >> (t + 2) & 1) << 3
        flags |= (self.r8(T + V.O_RT + 8 * t + V.RT_VEL) >> 7) << 4 | (self.r8(T + V.O_RT + 8 * t + V.RT_NOTE) >> 7) << 5
        sd = self.r8(T + V.O_SD) >> 4 * t & 15
        vals = [struct.unpack("b", bytes([x]))[0] for x in self.uc.mem_read(T + V.STRIDE * t + V.O_PAR, 26)]
        v2 = [struct.unpack("b", bytes([x]))[0] for x in self.uc.mem_read(self.gfst() + V.V2_OFF + 8 * t, 8)]
        return flags, sd, vals, v2

    def dirty(self, t):
        a = V.TAIL + V.O_RT + 8 * t
        return self.r8(a + V.RT_DLO), self.r8(a + V.RT_DHI), self.r8(a + V.RT_DX), self.r8(a + V.RT_AUX)


def run(img, man, new):
    e = EM(img, man)
    e.lab = {k: int(v, 16) for k, v in man["report"]["sc17"]["labels"].items()}
    set_loaded(e, man, 31)
    ms = [200000]
    def frame(dt=20):
        ms[0] += dt; e.w32(TICK, ms[0])
        e.call(0x08034196, MGR, 0x2006E000, maxins=8_000_000); return list(struct.unpack("<32H", bytes(e.uc.mem_read(0x2006E000, 64))))
    def panel():                                                                  # the LED task from its caller: the 69 LEDs of the frame
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR)
        e.call(0x08033B3E, maxins=8_000_000)
        f = struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138))); return f[MP.LED_DOWN], f[MP.LED_UP]
    pad = lambda p: (e.call(PRESS, MGR, p, 100, maxins=8_000_000), e.call(RELEASE, MGR, p, maxins=8_000_000))
    def dup(p): e.held(2); pad(p); e.held(0)
    def clr(p):
        e.call(0x08033320, MGR, 23, maxins=900000); pad(p); e.call(0x0803381A, MGR, 23, maxins=900000)
    ops = lambda: [(c[0], c[1][1]) + tuple(c[2:4]) for c in e.api if c[0] in ("read", "write") and c[1][0] == PK.KIND_PATCH]
    out = {}
    A = (0b101011, 0x5, [(7 * i + 3) % 120 - 50 for i in range(26)], [(5 * i + 1) % 100 for i in range(8)])
    Bv = (0b010100, 0xA, [(11 * i + 9) % 100 - 30 for i in range(26)], [(3 * i + 7) % 90 for i in range(8)])
    e.btn(2); e.btn(8)                                                            # MIDI 1, Preset
    out["sub"] = e.r8(MGR + 0x152)
    e.set_engine(0, *A); e.set_engine(1, *Bv)
    out["f0"] = frame(); out["p0"] = panel()
    e.api.clear(); dup(8)
    out["sd1"] = {k: v for k, v in e.sd.items() if k[0] == PK.KIND_PATCH}; out["keys1"] = sorted(e.sd); out["ops1"] = ops(); out["lock1"] = e.lock; out["f1"] = frame()
    e.set_engine(0, *Bv); e.uc.mem_write(V.TAIL + V.O_RT + V.RT_DLO, bytes(4))
    e.api.clear(); pad(8); out["eng2"] = e.engine(0); out["dirty2"] = e.dirty(0); out["ops2"] = ops(); out["lock2"] = e.lock
    e.btn(3); e.btn(8); out["sub3"] = e.r8(MGR + 0x152)                           # MIDI 2
    pad(8); out["eng3"] = (e.engine(1), e.engine(0))
    e.btn(2); e.btn(8)
    b1 = T8.bank([0, 1, 2], n=3); e.sd[(3, 1, 0xFF)] = b1
    e.set_engine(0, *Bv); e.api.clear(); dup(21)                                  # pad 22 = slot 13 = bank 1, record 5
    out["b1"] = (b1, e.sd[(3, 1, 0xFF)]); out["ops4"] = ops(); out["f4"] = frame()
    e.api.clear(); pad(10); out["empty"] = (e.engine(0), ops())                   # an empty slot
    f = bytearray(e.sd[(3, 0, 0xFF)]); f[340 + 10] ^= 1; e.sd[(3, 0, 0xFF)] = bytes(f)
    e.api.clear(); pad(8); out["bad"] = (e.engine(0), [o for o in ops() if o[0] == "write"])
    e.api.clear(); clr(8); out["clr"] = (e.sd[(3, 0, 0xFF)], ops(), frame(), e.lock)
    pg = lambda: e.r8(e.gst() + PK.PM_CACHE + 3)
    e.gst = lambda: (e.call(int(man["report"]["sc14"]["labels"]["c_gst"], 16)), e.uc.reg_read(UC_ARM_REG_R0))[1]
    pages = [pg()]
    for b_ in (20, 19, 19, 19, 19, 20, 20):                                       # up at page 1: stays; down x 4: stops at 4; up x 2
        e.btn(b_); pages.append(pg())
    out["pages"] = pages; out["p_mid"] = panel(); out["f_pg"] = frame()            # page 2 (index 1) now
    e.api.clear(); dup(8); out["pg_save"] = (sorted(k for k in e.sd), ops(), frame())
    e.btn(19); e.btn(19); out["p_last"] = panel()
    e.btn(20); e.btn(20); e.btn(20); out["p_first"] = panel(); frame()
    f = bytearray(e.sd[(3, 0, 0xFF)]); f += bytes([0xFF]) * (1024 - len(f)) if len(f) < 1024 else b""
    f[512:512 + 340] = bytes(340); f[512 + 340:512 + 340 + 44] = patch_bytes(*A); e.sd[(3, 0, 0xFF)] = bytes(f)       # a patch appears on the card (slot 1)
    e.api.clear(); out["stale"] = (frame(), ops()); e.api.clear(); out["fresh"] = (frame(4300), [o[:2] for o in ops()])
    e.set_engine(0, *Bv); pad(9); out["eng_card"] = e.engine(0)
    out["rst"] = []
    for pg_ in (0, 1, 4):                                                         # Clear + a page pad: that page's values to their defaults
        e.set_engine(0, *A); e.uc.mem_write(V.TAIL + V.O_RT + V.RT_DLO, bytes(2)); clr(pg_); out["rst"].append((pg_, e.engine(0), e.dirty(0)))
    e.set_engine(0, *A); clr(V.PAD_OSC); out["rst27"] = e.engine(0)                # Clear + pad 27: no reset any more
    e.set_engine(0, *A)
    pad(V.PAD_CC); out["ed"] = e.r8(V.TAIL + V.O_ED)                               # the CC editor
    e.api.clear(); p_ = pg(); pad(8); e.held(2); pad(8); e.held(0); out["ed_ops"] = (ops(), p_, pg())
    del e; gc.collect()
    return out


def prev_run(img, man):
    e = EM(img, man); set_loaded(e, man, 31)
    e.btn(2); e.btn(8)
    e.set_p0(e.r32(e.r32(MGR + 0x20) + 0xC), 2); e.call(PRESS, MGR, 8, 100, maxins=8_000_000); e.call(RELEASE, MGR, 8, maxins=8_000_000)
    e.call(0x08034196, MGR, 0x2006E000, maxins=8_000_000); f = list(struct.unpack("<32H", bytes(e.uc.mem_read(0x2006E000, 64))))
    r = ([c for c in e.api if c[0] == "write" and c[1][0] == PK.KIND_PATCH], f[8:24]); del e; gc.collect(); return r


def main(img, man, prev, prev_man):
    global INIT
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    INIT = bytes(img[PK.INIT_PATCH - B:PK.INIT_PATCH - B + 340])
    L = {k: int(v, 16) for k, v in man["report"]["mpatch"]["labels"].items()}
    P = {k: int(v, 16) for k, v in man["report"]["mpatch"]["prev"].items()}
    w = lambda a: struct.unpack_from("<I", img, a - B)[0]
    from thumb import b_w, bl
    HB, HL = L["c_mpbtn"], L["c_mpledtask"]
    mc = man["report"].get("macroed")                                             # SC39.3: the macro editor chains in front of both
    if mc is not None:
        assert int(mc["prev"]["btn"], 16) == HB and int(mc["prev"]["ledtask"], 16) == HL
        HB, HL = int(mc["labels"]["c_mcbtn"], 16), int(mc["labels"]["c_mcledtask"], 16)
    check(w(MP.TMPL_VT) == L["c_mppad"] | 1 and w(MP.TMPL_VT + 28) == L["c_mpleds"] | 1 and w(PK.CT_VT + 0x20) == L["c_mphmask"] | 1
          and bytes(img[MP.BTN_ENTRY - B:MP.BTN_ENTRY - B + 4]) == b_w(MP.BTN_ENTRY, HB) and all(bytes(img[c - B:c - B + 4]) == bl(c, HL) for c in PK.LED_CALLS),
          f"the hooks: the template view's slots 0 / 7, the button chain's head, the two LED task calls, the container's slot 8 (in front of {', '.join(f'{k} {v:#x}' for k, v in P.items())})")
    o = run(img, man, True)
    A = (0b101011, 0x5, [(7 * i + 3) % 120 - 50 for i in range(26)], [(5 * i + 1) % 100 for i in range(8)])
    Bv = (0b010100, 0xA, [(11 * i + 9) % 100 - 30 for i in range(26)], [(3 * i + 7) % 90 for i in range(8)])
    LIT, DIM = MP.COL_LIT, MP.COL_DIM
    row = lambda f: f[8:24]
    check(o["sub"] == 18 and row(o["f0"]) == [0] * 16 and o["p0"] == (MP.COL_BTN, 0), f"MIDI 1's Preset view: rows 2-3 dark, Octave down lit / up dark ({o['p0']})")
    f = o["sd1"].get((3, 0, 0xFF), b"")
    want = INIT + patch_bytes(*A) + bytes([0xFF]) * 130
    check(set(o["sd1"]) == {(3, 0, 0xFF)} and f == want and o["ops1"] == [("write", 0, 0, 340), ("write", 0, 340, 172)] and o["lock1"] == 0,
          f"Duplicate + pad 9: bank 0 created = the Initial Patch + the patch in its padding ({o['ops1']}, lock {o['lock1']})\n    {f[340:384].hex()}")
    check(row(o["f1"]) == [LIT] + [0] * 15, "the slot bright")
    check(o["eng2"] == A and o["dirty2"][0] == 0xFF and o["dirty2"][1] == 0xFF and o["dirty2"][2] == V.DX_MASK and o["dirty2"][3] & 0x61 == 0x61
          and o["ops2"] == [("read", 0, 340, 44)] and o["lock2"] == 0, f"pad 9: the engine back (flags {o['eng2'][0]:#x}, nibble {o['eng2'][1]:#x}), every value marked to be sent ({[hex(x) for x in o['dirty2']]})")
    check(o["sub3"] == 27 and o["eng3"][0] == A and o["eng3"][1] == A, "MIDI 2, pad 9: the same patch in the other track")
    b1, n1 = o["b1"]
    rec = lambda k: n1[512 * k:512 * k + 512]
    ff = bytes([0xFF]) * 172
    check(len(n1) == 6 * 512 and n1[:len(b1)] == b1 and n1[len(b1):1536] == ff and rec(3) == INIT + ff and rec(4) == INIT + ff
          and rec(5) == INIT + patch_bytes(*Bv) + bytes([0xFF]) * 130, f"pad 22 on a bank of 3: its padding completed, records 4 / 5 the Initial Patch, record 6 with the patch ({o['ops4']})")
    check(row(o["f4"]) == [DIM] + [0] * 12 + [LIT] + [0] * 2, f"both slots lit, the last one bright ({[hex(x) for x in row(o['f4'])]})")
    check(o["empty"] == (Bv, [("read", 0, 2 * 512 + 340, 44)]), f"an empty slot: nothing loaded ({o['empty'][1]})")
    check(o["bad"] == (Bv, []), "a slot with a wrong sum: nothing loaded")
    s, ops, fr, lk = o["clr"]
    check(s[340:512] == ff and s[:340] == INIT and ops == [("write", 0, 340, 172)] and row(fr)[0] == 0 and lk == 0, f"Clear + pad 9: the padding 0xFF again, the pad dark ({ops})")
    check(o["pages"] == [0, 0, 1, 2, 3, 3, 2, 1], f"Octave up at page 1 stays, down x 4 stops at page 4, up x 2: {o['pages']}")
    check(o["p_mid"] == (MP.COL_BTN, MP.COL_BTN) and o["p_last"] == (0, MP.COL_BTN) and o["p_first"] == (MP.COL_BTN, 0), f"Octave LEDs (down, up): a middle page {o['p_mid']}, the last {o['p_last']}, the first {o['p_first']}")
    keys, ops, fr = o["pg_save"]
    check(row(o["f_pg"]) == [0] * 16 and (3, 2, 0xFF) in keys and ops[0] == ("write", 2, 0, 340) and row(fr)[0] == LIT, f"page 2: its own slots; Duplicate + pad 9 there = slot 17 = bank 2 ({ops})")
    fr, ops = o["stale"]; fr2, ops2 = o["fresh"]
    check(ops == [] and row(fr)[1] == 0 and row(fr2)[1] == DIM and ("read", 0) in ops2, f"a patch written on the card behind: nothing read before 4 s, then the slot shows ({ops2})")
    check(o["eng_card"] == A, "that patch loads")
    rows = [V.KNOB_CODES, V.KNOB_CODES_B, V.KNOB_CODES_C, V.KNOB_CODES_D, V.KNOB_CODES_E]
    dflt = tuple(V.DEFAULTS[:26]) + tuple(V.DEFAULTS_V2)
    sgn = lambda v: v - 256 if v > 127 else v
    bad = []
    for pg_, eng, dirty in o["rst"]:
        vals, v2 = list(A[2]), list(A[3])
        for c in (tuple(g[0] for g in V.GR_TAB) if pg_ == 1 else rows[pg_]):          # (the test patch is the granular engine: its own page 2)
            if c == 0: continue
            if c <= 26: vals[c - 1] = sgn(dflt[c - 1] & 0xFF)
            else: v2[c - 27] = sgn(dflt[c - 1] & 0xFF)
        if eng != (A[0], A[1], vals, v2): bad.append((pg_, eng[2], vals, eng[3], v2))
    check(not bad, f"Clear + page pad 1 / 2 / 5: only that page's values go to their defaults {bad[:1]}")
    check(o["rst27"][2] == A[2] and o["rst27"][3] == A[3], "Clear + pad 27: the values stay (no reset of everything)")
    ops, p0, p1 = o["ed_ops"]
    check(o["ed"] & 0x80 and ops == [] and p0 == p1, f"the CC editor on: the pads are its own (no card access {ops})")
    gc.collect(); q = prev_run(prev, prev_man)
    check(q == ([], [0] * 16), f"the previous build: Duplicate + pad 9 does nothing ({q})")
    print("SC39.1 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
