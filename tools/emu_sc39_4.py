"""SC39.4 ARM tests (live RAM dump, the real routes: the controller's buttons and pads, the LED task, the stock content API on emu_sc35's model of the
SD card): the synth's patch saved into the pack's bank, and the same gesture for the own-synth patches of MIDI 1 / 2 (tools/psave.py).

    python tools/emu_sc39_4.py SC39.4.bin SC39.4_manifest.json SC39.3.bin SC39.3_manifest.json
Synth 1 / 2, the Preset view:
  * a plain pad: the stock's handler, nothing written;
  * Clear (the real button) + pad: nothing written, the stock not reached, the pad blinks white; Clear + another pad: the question moves;
  * Clear + the same pad again: one write = the 340 bytes of the synth's patch in RAM at 512 x (patch % 8) of bank patch / 8; the padding of the
    record and the other records untouched; the stock's handler then chooses the slot; an edit of the patch (0x08034D92) is in the next save;
  * after ~5 s the question is gone (asked again, nothing written; the pad no longer blinks);
  * a slot past the end of a bank / in a bank that does not exist: 0xFF up to the slot, then the patch; the records before untouched;
  * Clear + Duplicate: nothing; the pointer in front of the patch wrong: nothing written; Synth 2: its own patch; the source view closes with Clear;
MIDI 1 / 2, the Preset view (the own-synth patches):
  * Clear + slot: asks (blinks white), nothing written; again: the track's engine in the padding of the record (mpatch's save);
  * the question of MIDI 1 is not MIDI 2's; a plain pad loads as before; Clear + a page pad still resets that page;
  * a pad that loads a slot plays the root of the scale on that track while it is held (an empty slot does not);
  * the empty slots violet; Clear + MIDI 1 / 2 (the track's button) in a view of that track: its engine's values back to the initial ones (not
    with the CC editor open, not the other track's button);
  * Duplicate + slot: nothing written (before: saved), it blinks while Duplicate is held; + another slot: the two patches change places, the 340
    bytes of the synth patches untouched; onto an empty slot: moved; an empty slot A, or a slot B whose record is not in the bank: nothing;
the previous build: Clear + pad twice in the synth Preset view writes nothing.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc39_1 as T1  # noqa: E402
from emu_sc35 import MGR, TICK, PK, set_loaded  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import mpatch as MP  # noqa: E402
import macroed as MC  # noqa: E402
import psave as PS  # noqa: E402
from thumb import b_w  # noqa: E402

V = T1.V
B = 0x08010000
STOCK_PAD = 0x0804D242
CLEAR = 23


def bank(n, tag):
    """n records of 512 bytes: 340 of a patch, 172 of padding with its own marks"""
    return b"".join(bytes((tag + k + i) & 0x7F for i in range(340)) + bytes(0x80 | (k + i) & 0x7F for i in range(172)) for k in range(n))


class E4(T1.EM):
    def setup(self, man):
        self.lab = {k: int(v, 16) for k, v in man["report"]["sc17"]["labels"].items()}
        self.gstf = int(man["report"]["sc14"]["labels"]["c_gst"], 16)
        set_loaded(self, man, 31)
        self.ms = 200000; self.w32(TICK, self.ms)
        self.stock = []
        self.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: self.stock.append(a), begin=STOCK_PAD, end=STOCK_PAD)
        self.saves_fn = 0                                                         # the settings save (after a load): it does not end in the emulation
        def sv(uc, a, s_, d): self.saves_fn += 1; uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        self.uc.hook_add(UC_HOOK_CODE, sv, begin=V.SAVE_FN & ~1, end=V.SAVE_FN & ~1)
    def st(self):
        self.call(self.gstf); return bytes(self.uc.mem_read(self.uc.reg_read(UC_ARM_REG_R0) + PS.ST_OFF, 8))
    def frame(self, phase=0, dt=0):
        """the LED task; phase 0 = the lit half of the blink"""
        self.ms += dt; t = self.ms & ~0xFF | (0x80 if phase else 0); self.w32(TICK, t)
        self.call(0x08034196, MGR, 0x2006E000, maxins=8_000_000); self.w32(TICK, self.ms)
        return list(struct.unpack("<32H", bytes(self.uc.mem_read(0x2006E000, 64))))
    def pad(self, p): self.call(PRESS, MGR, p, 100, maxins=20_000_000); self.call(RELEASE, MGR, p, maxins=8_000_000)
    def clear(self, on): self.call(0x08033320 if on else 0x0803381A, MGR, CLEAR, maxins=900000)
    def wr(self): return [(c[1][1], c[2], c[3]) for c in self.api if c[0] == "write" and c[1][0] == PK.KIND_PATCH]
    def ram(self, s): return bytes(self.uc.mem_read(PS.PATCH_RAM + PS.PATCH_RAM_STRIDE * s, 340))
    def put(self, t, i, v):
        this = self.r32(self.r32(self.r32(MC.CTX) + 0x10)); self.call(MC.PARAM_SET, this + 4, t, i, v, maxins=3_000_000)
    def srcflag(self):
        self.call(self.gstf); return self.r8(self.uc.reg_read(UC_ARM_REG_R0) + 20) & 4
    def wait(self, ms): self.ms += ms; self.w32(TICK, self.ms)


def synth_run(img, man, new):
    e = E4(img, man); e.setup(man)
    o = {}
    e.btn(0); e.btn(8)
    o["view"] = (e.r32(MGR + 0x6C) == e.r32(MGR + 0x2C), e.r8(MGR + 0x152))
    b0, b2 = bank(8, 3), bank(3, 50)[:2 * 512 + 340]
    e.sd = {(3, 0, 0xFF): b0, (3, 2, 0xFF): b2}
    e.api.clear(); e.stock.clear(); e.pad(3); o["plain"] = (e.wr(), len(e.stock))
    e.clear(1); e.api.clear(); e.stock.clear(); e.pad(3)
    o["ask"] = (e.wr(), len(e.stock), e.st(), e.frame(0)[3], e.frame(1)[3])
    if not new:
        e.pad(3); e.clear(0); o["prev"] = (e.wr(), dict(e.sd) == {(3, 0, 0xFF): b0, (3, 2, 0xFF): b2})
        del e; gc.collect(); return o
    e.pad(5); f = e.frame(0); o["move"] = (e.wr(), e.st()[1], f[3], f[5])
    ram = e.ram(0); e.stock.clear(); e.pad(5); e.clear(0)
    o["save"] = (e.wr(), e.sd[(3, 0, 0xFF)], b0, ram, len(e.stock), e.st()[1], e.lock, e.frame(0)[5], e.frame(1)[5])
    v = e.ram(0)[176 + 30] ^ 0x15; e.put(0, 176, v); ram = e.ram(0)
    e.clear(1); e.api.clear(); e.pad(5); e.pad(5); e.clear(0)
    o["edit"] = (ram[176 + 30] == v, e.wr(), e.sd[(3, 0, 0xFF)][5 * 512:5 * 512 + 340] == ram)
    e.clear(1); e.api.clear(); e.pad(6); e.wait(6000); e.pad(6); a1 = e.st()[1]; e.wait(6000); f = (e.frame(0)[6], e.frame(1)[6]); e.clear(0)
    o["late"] = (e.wr(), a1, e.st()[1], f, e.frame(0)[6])
    ram = e.ram(0)
    e.clear(1); e.api.clear(); e.pad(12); e.pad(12); o["nobank"] = (e.wr(), e.sd.get((3, 1, 0xFF)), ram)
    e.api.clear(); e.pad(22); e.pad(22); e.clear(0); o["past"] = (e.wr(), e.sd[(3, 2, 0xFF)], b2, ram)
    keep = dict(e.sd)
    e.set_p0(e.r32(e.r32(MGR + 0x20) + 0xC), 3); e.api.clear(); e.pad(7); e.pad(7); e.set_p0(e.r32(e.r32(MGR + 0x20) + 0xC), 0)
    o["both"] = (e.wr(), dict(e.sd) == keep)
    ptr = e.r32(PS.PATCH_RAM - 4); e.w32(PS.PATCH_RAM - 4, 0)
    e.clear(1); e.api.clear(); e.pad(2); e.pad(2); e.clear(0); o["ptr"] = (ptr == PS.PATCH_RAM, e.wr(), e.lock); e.w32(PS.PATCH_RAM - 4, ptr)
    e.btn(1); e.btn(8); o["view2"] = e.r8(MGR + 0x152)
    ram2 = e.ram(1)
    e.sd[(3, 4, 0xFF)] = bank(8, 9)
    e.clear(1); e.api.clear(); e.pad(1); k2 = e.st()[1:3]; e.pad(1); e.clear(0)
    pt = k2[0] & 0x7F; f = e.sd[(3, pt >> 3, 0xFF)]; of = 512 * (pt & 7)
    o["s2"] = (k2[1], pt, e.wr() == [(pt >> 3, of, 340)], f[of:of + 340] == ram2, ram2 != e.ram(0), f[:of] + f[of + 340:] == bank(8, 9)[:of] + bank(8, 9)[of + 340:])
    e.btn(1); e.btn(1); o["src"] = (e.r8(MGR + 0x152), e.srcflag())               # the track view, then the source view
    e.clear(1); o["srcv"] = e.srcflag(); e.clear(0)
    del e; gc.collect()
    return o


def midi_run(img, man):
    e = E4(img, man); e.setup(man)
    o = {}
    A = (0b101011, 0x5, [(7 * i + 3) % 120 - 50 for i in range(26)], [(5 * i + 1) % 100 for i in range(8)])
    Bv = (0b010100, 0xA, [(11 * i + 9) % 100 - 30 for i in range(26)], [(3 * i + 7) % 90 for i in range(8)])
    pa, pb = T1.patch_bytes(*A), T1.patch_bytes(*Bv)
    e.btn(2); e.btn(8); o["sub"] = e.r8(MGR + 0x152)
    e.set_engine(0, *A); e.set_engine(1, *Bv)
    b0 = b"".join(bytes((3 + k + i) & 0x7F for i in range(340)) + bytes([0xFF]) * 172 for k in range(8))
    e.sd = {(3, 0, 0xFF): b0}
    slot = lambda n: e.sd[(3, 0, 0xFF)][512 * n + 340:512 * n + 340 + 42]
    synths = lambda: all(e.sd[(3, 0, 0xFF)][512 * k:512 * k + 340] == b0[512 * k:512 * k + 340] for k in range(8))
    e.frame(0)
    e.held(2); e.api.clear(); e.pad(8); f = (e.frame(0)[8], e.frame(1)[8]); st = e.st(); e.held(0); f2 = e.frame(0)[8]
    o["dup1"] = (e.wr(), f, st[1:3], e.st()[1], f2)
    e.clear(1); e.api.clear(); e.pad(8); o["ask"] = (e.wr(), e.st()[1:3], e.frame(0)[8], e.frame(1)[8])
    e.pad(8); e.clear(0); o["save"] = (slot(0) == pa, e.sd[(3, 0, 0xFF)][340 + 42:512] == bytes([0xFF]) * 130, synths(), e.st()[1], e.lock, e.frame(0)[8], e.frame(1)[8])
    e.clear(1); e.pad(9); k1 = e.st()[1:3]; e.clear(0)
    e.btn(3); e.btn(8); o["sub2"] = e.r8(MGR + 0x152)                              # MIDI 2
    e.clear(1); e.api.clear(); e.pad(9); o["other"] = (k1, e.wr(), e.st()[1:3])    # MIDI 1's question is not MIDI 2's: asked again
    e.pad(9); e.clear(0); o["save2"] = (slot(1) == pb, slot(0) == pa)
    e.btn(2); e.btn(8); e.frame(0, 5000)
    f = bytearray(e.sd[(3, 0, 0xFF)]); f[340 + 44:340 + 60] = b"Nombre de A     "; f[852 + 44:852 + 60] = b"Nombre de B     "; e.sd[(3, 0, 0xFF)] = bytes(f)   # names (tools/patchtool.py)
    e.held(2); e.api.clear(); e.pad(8); e.pad(9); e.held(0)
    nm = lambda n: e.sd[(3, 0, 0xFF)][512 * n + 340 + 44:512 * n + 340 + 60]
    o["swap"] = (slot(0) == pb and nm(0) == b"Nombre de B     ", slot(1) == pa and nm(1) == b"Nombre de A     ", synths(), [w[1:] for w in e.wr()], e.lock)
    f = e.frame(0, 5000); o["swap_led"] = (f[8], f[9], f[10])
    e.held(2); e.api.clear(); e.pad(8); e.pad(10); e.held(0)                      # onto an empty slot whose record exists
    o["move"] = (slot(2) == pb, slot(0) == bytes([0xFF]) * 42, slot(1) == pa)
    keep = dict(e.sd)
    e.held(2); e.api.clear(); e.pad(11); e.pad(9); e.held(0); w1 = e.wr()         # A empty
    e.held(2); e.api.clear(); e.pad(9); e.pad(21); e.held(0); w2 = e.wr()         # B = slot 13: bank 1 is not there
    e.held(2); e.api.clear(); e.pad(9); e.pad(9); e.held(0); w3 = e.wr()          # A twice
    o["noswap"] = (w1, w2, w3, dict(e.sd) == keep)
    e.set_engine(0, *Bv); e.api.clear(); e.pad(9); g = e.engine(0); g[2][13] = A[2][13]; o["load"] = (g == A, e.wr())   # (code 14 is the second note: the audition sets it, as any note does)
    rt = lambda t: (e.r8(V.TAIL + V.O_RT + 8 * t + V.RT_CNT) & 15, e.r8(V.TAIL + V.O_RT + 8 * t + V.RT_NOTE) & 0x7F)
    e.call(int(man["report"]["vcf20"]["labels"]["c_sdtonic"], 16)); tonic = e.uc.reg_read(UC_ARM_REG_R0)
    n0 = rt(0); e.call(PRESS, MGR, 9, 100, maxins=20_000_000); n1 = rt(0); a1 = e.st()[6:8]; e.call(RELEASE, MGR, 9, maxins=8_000_000); n2 = rt(0)
    e.call(PRESS, MGR, 11, 100, maxins=20_000_000); n3 = rt(0); e.call(RELEASE, MGR, 11, maxins=8_000_000)              # an empty slot: no note
    e.call(PRESS, MGR, 9, 100, maxins=20_000_000); e.btn(19); n4 = rt(0); e.btn(20); e.call(RELEASE, MGR, 9, maxins=8_000_000)   # a button while it sounds
    o["aud"] = (tonic, n0, n1, bytes(a1), n2, n3, n4, rt(0), rt(1))
    e.set_engine(0, *A); e.clear(1); e.pad(0); e.clear(0); o["rst"] = (e.engine(0) != A, e.st()[1])
    o["empty"] = e.frame(0, 6000)[8:24]
    e.set_engine(0, *A); e.set_engine(1, *Bv)
    e.clear(1); e.btn(3); e.clear(0); o["rb_other"] = (e.engine(0) == A, e.engine(1) == Bv, e.r8(MGR + 0x152))   # MIDI 2's button in MIDI 1's view: not ours
    e.btn(2); e.btn(8); e.set_engine(0, *A); e.set_engine(1, *Bv)
    e.btn(2); n0 = (e.engine(0) == A, e.r8(MGR + 0x152)); e.btn(8)                # the button alone: the stock
    e.clear(1); e.btn(2); e.clear(0); o["rb"] = (n0, e.engine(0), e.engine(1) == Bv, e.dirty(0), e.r8(MGR + 0x152))
    e.set_engine(0, *A); e.btn(2); s_ = e.r8(MGR + 0x152)                         # its track view
    e.clear(1); e.btn(2); e.clear(0); o["rb_track"] = (s_, e.engine(0)[2:], e.r8(MGR + 0x152))
    e.btn(8); e.set_engine(0, *A); e.pad(V.PAD_CC); ed = e.r8(V.TAIL + V.O_ED)     # the CC editor on
    e.clear(1); e.btn(2); e.clear(0); o["rb_ed"] = (ed, e.engine(0)[2] == A[2])
    del e; gc.collect()
    return o


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["psave"]["labels"].items()}
    P = {k: int(v, 16) for k, v in man["report"]["psave"]["prev"].items()}
    w = lambda a: struct.unpack_from("<I", img, a - B)[0]
    check(w(PS.SP_VT) == L["c_pspad"] | 1 and w(PS.SP_VT + 28) == L["c_psleds"] | 1 and w(PS.TMPL_VT) == L["c_psxpad"] | 1 and w(PS.TMPL_VT + 4) == L["c_psxrel"] | 1 and w(PS.TMPL_VT + 28) == L["c_psxleds"] | 1
          and bytes(img[PS.BTN_ENTRY - B:PS.BTN_ENTRY - B + 4]) == b_w(PS.BTN_ENTRY, int(man["report"]["throw"]["labels"]["c_thbtn"], 16) if "throw" in man["report"] else L["c_psbtn"]),
          f"the hooks: slots 0 / 7 of the synth Preset view, 0 / 1 / 7 of the template view, the head of the button chain (in front of {', '.join(f'{k} {v:#x}' for k, v in P.items())})")
    o = synth_run(img, man, True)
    W, OFF_ = PS.COL_ASK, 0
    check(o["view"] == (True, 0) and o["plain"] == ([], 1), f"Synth 1's Preset view; a plain pad: the stock's handler, nothing written ({o['plain']})")
    wr, hits, st, on, off = o["ask"]
    check(wr == [] and hits == 0 and st[1] == 0x80 | 3 and st[2] == 0 and (on, off) == (W, OFF_), f"Clear + pad 4: nothing written, the stock not reached, the pad blinks white ({on:#x} / {off:#x})")
    wr, a_, l3, l5 = o["move"]
    check(wr == [] and a_ == 0x80 | 5 and l3 != W and l5 == W, "Clear + pad 6: the question moves there, nothing written")
    wr, f, b0, ram, hits, a_, lock, l_on, l_off = o["save"]
    check(wr == [(0, 5 * 512, 340)] and f[5 * 512:5 * 512 + 340] == ram and f[:5 * 512] == b0[:5 * 512] and f[5 * 512 + 340:] == b0[5 * 512 + 340:] and ram != b0[5 * 512:5 * 512 + 340],
          "Clear + pad 6 again: one write of 340 bytes = the synth's patch in RAM at slot 5 of bank 0; its padding and the other records untouched")
    check(hits == 1 and a_ == 0 and lock == 0 and l_on == l_off, "then the stock's handler chooses the slot; nothing asked any more; the buffer's lock balanced")
    check(o["edit"] == (True, [(0, 5 * 512, 340)], True), "a parameter edited (the route of the MIDI input): it is in the patch the next save writes")
    wr, a1, a2, f, f3 = o["late"]
    check(wr == [] and a1 == 0x80 | 6 and a2 == 0 and f[0] == f[1] == f3, "6 s later: Clear + the same pad asks again (nothing written); another 6 s: the question is gone, the pad steady")
    wr, f, ram = o["nobank"]
    check(wr == [(1, 0, 4 * 512), (1, 4 * 512, 340)] and f == bytes([0xFF]) * 2048 + ram, "a slot of a bank that does not exist (pad 13): 0xFF up to the slot, then the patch")
    wr, f, b2, ram = o["past"]
    check(wr == [(2, len(b2), 6 * 512 - len(b2)), (2, 6 * 512, 340)] and f == b2 + bytes([0xFF]) * (6 * 512 - len(b2)) + ram,
          "a slot past the end of a bank of 3 patches (pad 23): 0xFF from the end of the file, then the patch; the three patches untouched")
    check(o["both"] == ([], True), "Clear + Duplicate + pad twice: nothing written")
    check(o["ptr"] == (True, [], 0), "the patch in RAM has a pointer to itself in front; without it nothing is written (the lock balanced)")
    k2, pt, wr, same, differ, rest = o["s2"]
    check(o["view2"] == 9 and k2 == 1 and pt & 31 == 1 and wr and same and differ and rest,
          f"Synth 2 (its view on page {(pt >> 5) + 1}): its own patch (344 bytes after Synth 1's) into patch {pt}; the rest of the bank untouched")
    check(o["src"] == (9, 4) and o["srcv"] == 0, "the source view: the Clear button closes it (any button does), so Clear + pad there is the Preset view's")
    gc.collect(); m = midi_run(img, man)
    A_FLAGS = 0b101011
    wr, f, st, a_, f2 = m["dup1"]
    check(m["sub"] == MP.SUBS[0] and wr == [] and f == (PS.COL_A, 0) and tuple(st) == (0x80, PS.K_DUP) and a_ == 0 and f2 != PS.COL_A,
          f"MIDI 1: Duplicate + slot 1: nothing written (before: saved); it blinks while Duplicate is held ({f}), forgotten when it is let go")
    wr, st, on, off = m["ask"]
    check(wr == [] and tuple(st) == (0x80, PS.K_MIDI) and (on, off) == (W, 0), "Clear + slot 1: asks (blinks white), nothing written")
    ok, fill, syn, a_, lock, l_on, l_off = m["save"]
    check(ok and fill and syn and a_ == 0 and lock == 0 and l_on == l_off == MP.COL_LIT, "Clear + slot 1 again: the track's engine in the padding of record 0; the synth patches untouched; the slot bright")
    k1, wr, st = m["other"]
    check(m["sub2"] == MP.SUBS[1] and tuple(k1) == (0x81, PS.K_MIDI) and wr == [] and tuple(st) == (0x81, PS.K_MIDI + 1), "a question asked in MIDI 1 is not MIDI 2's: asked again there")
    check(m["save2"] == (True, True), "MIDI 2: Clear + slot 2 twice: its engine in record 1; record 0 as it was")
    s0, s1, syn, wr, lock = m["swap"]
    check(s0 and s1 and syn and wr == [(512 + 340, 64), (340, 64)] and lock == 0, f"Duplicate + slot 1 + slot 2: the two patches change places (two writes of 64 bytes, the patch and its name: {wr}); the synth patches untouched")
    check(m["swap_led"][0] in (MP.COL_LIT, MP.COL_DIM) and m["swap_led"][1] in (MP.COL_LIT, MP.COL_DIM) and m["swap_led"][2] == PS.COL_EMPTY, f"both slots lit after the exchange ({[hex(x) for x in m['swap_led']]})")
    check(m["move"] == (True, True, True), "Duplicate + slot 1 + an empty slot: the patch moves there, slot 1 empty")
    w1, w2, w3, same = m["noswap"]
    check(w1 == [] and w2 == [] and w3 == [] and same, "an empty slot A, a slot B whose record is not in the bank, the same slot twice: nothing written")
    check(m["load"] == (True, []), "a plain pad loads the slot as before")
    tonic, n0, n1, a1, n2, n3, n4, n5, o1 = m["aud"]
    check(n0[0] == 0 and n1 == (1, tonic) and a1 == bytes([0x80 | tonic, 0]) and n2[0] == 0 and n3[0] == 0 and n4[0] == 0 and n5[0] == 0 and o1[0] == 0,
          f"the pad held: the root of the scale (note {tonic}) sounds on that track with the patch just loaded; it ends with the pad, or with any button; an empty slot plays nothing")
    check(m["rst"][0] and m["rst"][1] == 0, "Clear + page pad 1: that page back to its defaults, as before; nothing asked")
    lit = [x for x in m["empty"] if x not in (PS.COL_EMPTY,)]
    check(m["empty"].count(PS.COL_EMPTY) == 14 and all(x in (MP.COL_LIT, MP.COL_DIM) for x in lit), f"the empty slots are violet ({PS.COL_EMPTY:#x}), the two with a patch peach")
    DEF = ([v if v < 128 else v - 256 for v in (x & 0xFF for x in V.DEFAULTS[:26])], [v if v < 128 else v - 256 for v in (x & 0xFF for x in V.DEFAULTS_V2)])
    n0, eng, other, dirty, sub = m["rb"]
    check(n0[0] and eng[2] == DEF[0] and eng[3] == DEF[1] and eng[0] == A_FLAGS and other and dirty[0] == dirty[1] == 0xFF and sub == MP.SUBS[0],
          f"MIDI 1's Preset view: its button alone changes nothing of the engine; Clear + MIDI 1: every value back to the initial one, all marked to be sent, the engine kept, MIDI 2 untouched, the view stays")
    check(m["rb_other"][:2] == (True, True), "Clear + MIDI 2 with MIDI 1's view on the screen: nothing reset")
    s_, eng, sub = m["rb_track"]
    check(s_ == MP.SUBS[0] + 1 and eng[0] == DEF[0] and eng[1] == DEF[1] and sub == s_, "the same from the track view of MIDI 1")
    check(m["rb_ed"][0] != 0 and m["rb_ed"][1], "with the CC editor open the track button is the editor's: nothing reset")
    gc.collect(); q = synth_run(prev, prev_man, False)
    check(q["ask"][1] == 1 and q["prev"] == ([], True), "the previous build: Clear + pad = the stock's handler; twice: nothing written")
    print("SC39.4 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
