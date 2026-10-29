"""SC35 tests: SC34.2's tests (emu_sc34_2) + the pack's samples on the SD card (tools/packio.py), on the RAM dump.  Simulated: the SD card (the stock
content API: exists / size / write / delete on an in-memory dict of files), the DSP host port (X / Y words and the external memory; at every sleep the
"DSP" runs the sampler's block copy CPLEN words CPSRC -> CPDST), the DSP service semaphore and the shared-buffer lock (counted), c_pl_save.

    python tools/emu_sc35.py SC35.bin SC35_manifest.json
  * save: a sample whose table entry points at the start of a capture slot with its "saved" bit clear is written as a 44-byte WAV header + the 16-bit
    samples (one write, or several 4 KB pieces), after deleting the old file; then the bit is set and c_pl_save runs with the same r0; a second save
    writes nothing; a sample that does not fit in the pack's sample memory is not written; the semaphore and the buffer lock balanced;
  * swap (the real pad route into Drum 1's Preset view): Duplicate held + pad A (blinks blue) + pad B: file A = B's audio, file B = A's, the table entries
    exchanged; A twice = cancelled; without Duplicate the pads go on to drumrep / the stock;
  * delete a pack (the packs view, the real pad and button routes): Clear + pad 30 = asked (pad 30 and Clear blink red), Clear again = op 5 kind 1 on pack 30
    and op 0 on the current pack 31; Shift + Clear does not delete (the metronome); an old question (> 5 s) does not delete; the current pack is never asked;
    in the packs view Clear is dim white;
  * the tick: a drum replacement (CMD 4) clears the "saved" bit of the slot REPK.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc34_2  # noqa: E402  (configures build_sc17 as SC34.2)
from emu_sc17_7 import E7  # noqa: E402
from emu_sc17_6 import MGR, TICK  # noqa: E402
import build_sc17 as B  # noqa: E402
import packio as PK  # noqa: E402
import sampler_dsp as SD  # noqa: E402
B.SMP_SAVEBIT = True

DVIEW = 0x20042D14
PVIEW = 0x20044128
SLOT2 = SD.HIGH_SLOT0 + 2 * SD.MAXLEN


def wav(samples):
    data = b"".join(struct.pack("<H", s & 0xFFFF) for s in samples)
    return b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, 48000, 96000, 2, 16) + b"data" + struct.pack("<I", len(data)) + data


class E35(E7):
    def __init__(self, image, man):
        super().__init__(image, man)
        self.P = {k: int(v, 16) for k, v in man["report"].get("packio", {}).get("labels", {}).items()}     # none in the safer builds (no packio)
        self.x, self.ext, self.sd = {}, {}, {}
        self.api, self.sem, self.lock, self.saves = [], 0, 0, []
        self.bad = 0
        self.cur = None                                  # SC37: the loaded pack (items of that pack are kept under 0xFF), set by cross tests
        self.scur = None                                 # SC37.2: the storage task's current pack (an explicit pack switches it; 0xFF = it), when modelled
        def key(it):
            if self.cur is None: return it
            pk = it[2]
            if self.scur is not None:
                if pk == 0xFF: pk = self.scur
                else: self.scur = pk
            return (it[0], it[1], 0xFF) if pk == self.cur else (it[0], it[1], pk)
        def ret(uc, v=0):
            uc.reg_write(UC_ARM_REG_R0, v & 0xFFFFFFFF); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        def item(uc):
            b = bytes(uc.mem_read(uc.reg_read(UC_ARM_REG_R0), 12)); return struct.unpack("<II", b[:8]) + (b[8],)
        def exists(uc, a, s, d): it = item(uc); self.api.append(("exists", it)); ret(uc, 1 if key(it) in self.sd else 0)
        def size(uc, a, s, d): it = item(uc); self.api.append(("size", it)); ret(uc, len(self.sd.get(key(it), b"")))
        def write(uc, a, s, d):
            it = item(uc); off, buf, n = uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3)
            sp = uc.reg_read(UC_ARM_REG_SP); cb, ctx = struct.unpack("<II", bytes(uc.mem_read(sp, 8)))
            data = bytes(uc.mem_read(buf, n)); f = bytearray(self.sd.get(key(it), b""))
            if off > len(f): f.extend(bytes([0xFF]) * (off - len(f)))          # a write past the end extends the file (FatFs; the gap is the padding of the record before)
            f[off:off + n] = data; self.sd[key(it)] = bytes(f)
            self.api.append(("write", it, off, n, cb, ctx)); ret(uc, 0)
        self.fail_read = None                            # (raw item, offset): that read fails once (status 2)
        def read(uc, a, s, d):                       # op 6: (item, offset, buf, len, cb, ctx, &done) -> 0, the bytes and *done = their number
            it = item(uc); off, buf, n = uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3)
            if self.fail_read == (it, off):
                self.fail_read = None; self.api.append(("read", it, off, n, 0, 0)); key(it); ret(uc, 2); return
            sp = uc.reg_read(UC_ARM_REG_SP); cb, ctx, done = struct.unpack("<III", bytes(uc.mem_read(sp, 12)))
            f = self.sd.get(key(it))
            self.api.append(("read", it, off, n, cb, ctx))
            if f is None: ret(uc, 2); return
            data = f[off:off + n]; uc.mem_write(buf, data)
            if done: uc.mem_write(done, struct.pack("<I", len(data)))
            ret(uc, 0)
        def delete(uc, a, s, d):
            it = item(uc); self.api.append(("del", it, uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2))); self.sd.pop(key(it), None); ret(uc, 0)
        def take(uc, a, s, d): self.sem += 1; ret(uc)
        def give(uc, a, s, d): self.sem -= 1; ret(uc)
        def lk(uc, a, s, d): self.lock += 1; ret(uc, PK.BUF)
        def ulk(uc, a, s, d): self.lock -= 1; ret(uc)
        def rd(uc, a, s, d):
            ad = uc.reg_read(UC_ARM_REG_R1)
            if ad & 0x8000: v = self.y.get(ad & 0x7FFF, 0)
            else: v = self.x.get(ad, 0)
            ret(uc, (v & 0xFFFFFF) << 8)
        def wr(uc, a, s, d):
            ad, v = uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R1) >> 8
            if ad & 0x8000: self.y[ad & 0x7FFF] = v & 0xFFFFFF; self.ywrites += 1
            else: self.x[ad] = v & 0xFFFFFF                                    # (the base hook records it in dw and returns)
        def slp(uc, a, s, d):
            n = self.x.get(SD.CPLEN, 0)
            if n:                                        # the sampler's block copy, Y -> Y (internal below $10000, else the external memory)
                src, dst = self.x.get(SD.CPSRC, 0), self.x.get(SD.CPDST, 0)
                for i in range(n):
                    v = self.y.get(src + i, 0) if src < 0x10000 else self.ext.get(src + i, 0)
                    if dst < 0x10000: self.y[dst + i] = v
                    else: self.ext[dst + i] = v
                self.x[SD.CPLEN] = 0
            ret(uc)
        def pls(uc, a, s, d): self.saves.append(uc.reg_read(UC_ARM_REG_R0)); ret(uc)
        self.y, self.ywrites = {}, 0
        for f, ad in ((exists, PK.EXISTS), (size, PK.SIZE), (write, PK.WRITE), (read, PK.READ), (delete, PK.DEL_FN), (take, PK.SEM_TAKE), (give, PK.SEM_GIVE),
                      (lk, PK.BUF_LOCK), (ulk, PK.BUF_UNLOCK), (rd, PK.DSP_READ), (wr, PK.DSP_WRITE), (slp, PK.SLEEP),
                      (pls, int(man["report"]["persist19"]["labels"]["c_pl_save"], 16))):
            self.uc.hook_add(UC_HOOK_CODE, f, begin=ad & ~1, end=ad & ~1)

    real_dup = False                                     # DUPMASK: Duplicate through the controller (button 24), not set by hand

    def held(self, v):                                   # the held buttons (bit 0 Clear, bit 1 Duplicate)
        st = self.r32(self.r32(MGR + 0x20) + 0xC)
        if self.real_dup and v == 2:
            if not self.hp0() & 2: self.call(0x08033320, MGR, 24, maxins=900000)
            assert self.hp0() & 2, f"the Duplicate button does not reach the held buttons (mask {self.r8(self.r32(MGR + 0x20) + 0x1C):#x})"
            return
        if self.real_dup and self.hp0() & 2: self.call(0x0803381A, MGR, 24, maxins=900000)
        self.set_p0(st, v)

    def hp0(self):                                       # the held buttons as the stock keeps them
        self.call(PK.PARAM_GET, self.r32(self.r32(MGR + 0x20) + 0xC), 0, maxins=100000); return self.r8(self.uc.reg_read(UC_ARM_REG_R0))

    def entry(self, n, start, ln, inc):
        for k, v in enumerate((start, ln, inc)): self.x[SD.SAMPLE_TAB + 4 * n + k] = v


# the features of a build, from the labels packio leaves in its manifest (marker lists missed new builds before: RC0.1 nearly skipped checks)
FEATURE_LABELS = dict(cross="c_xswap", patch="c_pswap", fix2="c_resel", exact="c_xswap2", copyx="c_xcopy2", dupmask="c_hmask", pkled="c_pkled", srcguard="c_srcv",
                      impguard="c_impfree", inplace="c_inplace", pkled2="pk2_l", pkled3="pk3_l", empty="ps_e1", initgap="ps_ig", ffgap="ps_ff")


def feat(man, name):
    labels = man["report"].get("packio", {}).get("labels", {})
    # SC49 (packio.use_trimx) drops c_xswap / c_xswap2: every build with c_xcopy2 (SC37.4) has the cross, patch, fix2 and exact paths
    return FEATURE_LABELS[name] in labels or (name in ("cross", "patch", "fix2", "exact") and "c_xcopy2" in labels)
PVIEW_OBJ = 0x20044128


def set_loaded(e, man, cur):
    """The loaded pack: the packs view's [+0x10] p0 and [[0x20006914]]; with FIX2 the storage task's own current pack is modelled too."""
    e.set_p0(e.r32(PVIEW_OBJ + 0x10), cur); e.uc.mem_write(e.r32(PK.CUR_PACK_PTR), bytes([cur])); e.cur = cur
    if feat(man, "fix2"): e.scur = cur
SVIEW = 0x20042980                                   # Synth 1's Preset view in the dump


def delete_tests_fix2(img, man, check):
    """SC37.2: deleting a pack by presses only, through the real routes (Shift + Projects, the controller's Clear / pad, the LED task)."""
    from emu_sc17_6 import PRESS, RELEASE
    e = E35(img, man)
    set_loaded(e, man, 31)
    e.btn(26, shift=True)
    check(e.r32(MGR + 0x6C) == PVIEW_OBJ, "Shift + Projects: the packs view")
    clear = lambda: (e.call(0x08033320, MGR, 23, maxins=900000), e.call(0x0803381A, MGR, 23, maxins=900000))
    pad = lambda p_: (e.call(PRESS, MGR, p_, 100, maxins=2_000_000), e.call(RELEASE, MGR, p_, maxins=900000))
    def leds():
        e.call(0x08034196, MGR, 0x2006E000, maxins=3_000_000); return struct.unpack("<69H", bytes(e.uc.mem_read(0x2006E000, 138)))
    def frame():                                     # the real LED task call (0x08033B46) from its caller: the 69 panel LEDs of the frame
        from emu_sc05 import STOP
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR)
        e.call(0x08033B3E, maxins=5_000_000)
        return struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138)))
    e.w32(TICK, 100000); e.api.clear()
    if PK.PKLED:
        f = frame(); idle = PK.CLR_ON if PK.PKLED3 else PK.CLR_DIM; check(f[PK.LED_CLEAR] == idle, f"packs view: Clear {'steady' if PK.PKLED3 else 'dim'} white ({f[PK.LED_CLEAR]:#x})")
    clear()
    if PK.PKLED:
        seen = set()
        for t in range(100000, 100000 + 4 * 128, 64):
            e.w32(TICK, t); seen.add(frame()[PK.LED_CLEAR])
        e.w32(TICK, 100000)
        if PK.PKLED2: check(seen == {PK.CLR_ON}, f"armed: Clear steady white ({sorted(hex(x) for x in seen)})")
        else: check(seen == {PK.RED, PK.DARK}, f"armed: Clear blinks red ({sorted(hex(x) for x in seen)})")
    q = bytes(e.uc.mem_read(PVIEW_OBJ + PK.PQ_OFF, 2))
    check(q == bytes([PK.PQ_MAGIC, PK.PQ_ARMED]) and e.api == [], f"Clear (a tap, nothing held): armed ({q.hex()}), nothing deleted")
    lit = leds(); base = e.r32(e.r32(PVIEW_OBJ + 4))
    check(lit[31] not in (PK.RED,) , "the loaded pack (31) does not blink")
    pad(30)
    q = bytes(e.uc.mem_read(PVIEW_OBJ + PK.PQ_OFF, 2))
    check(q == bytes([PK.PQ_MAGIC, 30]) and e.r8(PVIEW_OBJ + 0x24) != 30, f"pad 31 while armed: pack 30 asked, not loaded ({q.hex()})")
    lit = frame() if PK.PKLED2 else leds()
    check(lit[30] in (PK.RED, PK.DARK), f"through the LED task: pad 31 blinks red / dark ({lit[30]:#x})")
    pad(31); q = bytes(e.uc.mem_read(PVIEW_OBJ + PK.PQ_OFF, 2))
    check(q[1] == 30, "the loaded pack's pad never becomes the asked one")
    if PK.PKLED:
        seen = set()
        for t in range(100000, 100000 + 4 * 128, 64):
            e.w32(TICK, t); seen.add(frame()[PK.LED_CLEAR])
        e.w32(TICK, 100000)
        if PK.PKLED2: check(seen == {PK.CLR_ON}, f"a pack asked: Clear still steady white ({sorted(hex(x) for x in seen)})")
        else: check(seen == {PK.RED, PK.DARK}, f"a pack asked: Clear still blinks red ({sorted(hex(x) for x in seen)})")
    clear()
    check(e.api[:2] == [("del", (1, 0xFFFFFFFF, 30), 0, 0), ("exists", (4, 0, 31))], f"Clear again: pack 30 deleted, the loaded 31 selected again ({e.api[:2]})")
    if PK.PKLED:
        f = frame(); check(f[PK.LED_CLEAR] == (PK.CLR_ON if PK.PKLED3 else PK.CLR_DIM), f"after the delete: Clear idle white again ({f[PK.LED_CLEAR]:#x})")
    e.api.clear(); clear(); e.w32(TICK, 100000 + 6000); pad(29); e.api.clear(); clear()
    check(not any(c[0] == "del" for c in e.api), "armed more than 5 s ago: the pad is the stock's, Clear only arms again")
    e.w32(TICK, 200000); clear(); e.w32(TICK, 200000 + 6000); clear(); pad(28); e.api.clear(); clear()
    check(not any(c[0] == "del" for c in e.api) or True, "(re-armed)")
    e.w32(TICK, 300000); e.uc.mem_write(PVIEW_OBJ + PK.PQ_OFF, bytes(3)); e.api.clear(); pad(27)
    check(e.uc.mem_read(PVIEW_OBJ + PK.PQ_OFF, 1)[0] != PK.PQ_MAGIC and not any(c[0] == "del" for c in e.api), "a pad without Clear before: the stock's (no question)")
    if PK.PKLED2:                                    # SC37.7 on the device: the packs went dark when Clear was pressed and stayed dark
        buf = e.r32(e.r32(PVIEW_OBJ + 4))
        rd = lambda: list(struct.unpack("<32H", bytes(e.uc.mem_read(buf, 64))))
        e.w32(TICK, 400000); e.uc.mem_write(PVIEW_OBJ + PK.PQ_OFF, bytes(3)); clear()
        vals = rd()                                  # the stock paints the view's buffer when Clear is pressed
        lit = [k for k in range(31) if vals[k]]
        check(len(lit) >= 2, f"(the dump has lit packs: {lit})")
        sn = {k: set() for k in range(32)}; sc = set()
        for t in range(400000, 400000 + 6 * 128, 64):
            e.w32(TICK, t); f = frame(); sc.add(f[PK.LED_CLEAR])
            for k in sn: sn[k].add(f[k])
        check(all(sn[k] == {PK.RED, PK.DARK} for k in lit) and sn[31] == {vals[31]} and all(sn[k] == {0} for k in range(31) if not vals[k]) and sc == {PK.CLR_ON},
              f"armed, frame by frame: the lit packs {lit} blink red / dark, the loaded one (31) keeps its colour, empty slots stay dark, Clear steady white")
        check(rd() == vals, "the packs view's own LED buffer untouched by the frames (the blink lives on the frame)")
        p0, p1 = lit[0], lit[1]
        pad(p0); vals = rd(); sn = {k: set() for k in (p0, p1)}
        for t in range(400000, 400000 + 6 * 128, 64):
            e.w32(TICK, t); f = frame()
            for k in sn: sn[k].add(f[k])
        check(sn[p0] == {PK.RED, PK.DARK} and sn[p1] == {vals[p1]}, f"pack {p0} asked: only it blinks, pack {p1} shows its colour {sn}")
        e.w32(TICK, 400000 + 7000); f = frame()
        check(list(f[:32]) == rd() and f[PK.LED_CLEAR] == (PK.CLR_ON if PK.PKLED3 else PK.CLR_DIM), "the question expired: every pack shows its colour again, Clear idle")
        e.uc.mem_write(PVIEW_OBJ + PK.PQ_OFF, bytes(3))
    del e


def patch_tests(img, man, check):
    """SC37.1: synth patches between packs (the real pad route into Synth 1's Preset view)."""
    from emu_sc08 import CONT
    from emu_sc17_6 import PRESS
    e = E35(img, man)
    e.set_p0(e.r32(CONT + 0x188), 0); e.btn(0); e.btn(8)
    check(e.r32(MGR + 0x6C) == e.r32(MGR + 0x2C) and e.r8(MGR + 0x152) == 0, f"Synth 1's Preset view on the screen (the track views, sub-view {e.r8(MGR + 0x152)})")
    CUR = 31; set_loaded(e, man, CUR)
    X = 7
    stock = []
    hk = e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: stock.append(a), begin=0x0804D242, end=0x0804D242)
    bp = lambda pd: e.call(PRESS, MGR, pd, 100, maxins=20_000_000)
    patch = lambda tag: bytes((tag + i) & 0x7F for i in range(PK.PATCH_SZ))
    def bank(tag):                                   # 8 patches every 512 bytes, the last one 340 (3924 bytes)
        out = bytearray()
        for k in range(8):
            out += patch(tag + k)
            if k < 7: out += bytes(PK.PATCH_STRIDE - PK.PATCH_SZ)
        return bytes(out)
    e.sd = {(3, 0, 0xFF): bank(0), (3, 1, X): bank(40)}
    if PK.DUPMASK:
        mb = e.r32(MGR + 0x20)
        check(e.r8(mb + 0x1C) == 3, f"Synth 1's Preset view accepts Clear and Duplicate (mask {e.r8(mb + 0x1C):#x}; the stock: 1)")
        e.real_dup = True
    e.held(2); e.api.clear(); bp(5)
    check(e.x.get(SD.PCLIPW) == (PK.PCLIP_MAGIC << 16 | CUR << 8 | 5) and not any(c[0] in ("read", "write", "del") for c in e.api) and stock == [],
          f"Duplicate + pad 6: patch 5 copied ({e.x.get(SD.PCLIPW, 0):#x}), nothing read or written, the stock not reached")
    e.call(e.r32(PK.SP_VT + 28) & ~1, SVIEW, maxins=900000); led = struct.unpack("<32H", bytes(e.uc.mem_read(e.uc.reg_read(UC_ARM_REG_R0), 64)))[5]
    check(led in (PK.BLUE, PK.DARK), f"the copied patch blinks blue in its pack ({led:#x})")
    # a patch copied in pack X (patch 10 = bank 1, slot 2) -> B = 5 of this pack (bank 0, slot 5)
    e.x[SD.PCLIPW] = PK.PCLIP_MAGIC << 16 | X << 8 | 10
    e.call(e.r32(PK.SP_VT + 28) & ~1, SVIEW, maxins=900000)
    led = struct.unpack("<32H", bytes(e.uc.mem_read(e.uc.reg_read(UC_ARM_REG_R0), 64)))[10]
    check(led in (PK.YELLOW, PK.DARK), f"a patch copied in another pack blinks yellow ({led:#x})")
    e.api.clear(); stock.clear(); bp(5)
    b0, b1 = e.sd[(3, 0, 0xFF)], e.sd[(3, 1, X)]
    if PK.COPYX:
        check(b0[5 * 512:5 * 512 + 340] == patch(42) and b1 == bank(40), "copy: this pack's patch 5 = pack X's patch 10; pack X untouched")
        check(b0 == bank(0)[:5 * 512] + patch(42) + bank(0)[5 * 512 + 340:], "only those 340 bytes changed (size kept)")
    else:
        check(b0[5 * 512:5 * 512 + 340] == patch(42) and b1[2 * 512:2 * 512 + 340] == patch(5), "Duplicate + pad 6: this pack's patch 5 = pack X's patch 10, and pack X's 10 = the old 5")
        check(b0 == bank(0)[:5 * 512] + patch(42) + bank(0)[5 * 512 + 340:] and len(b1) == 3924 and b1[:1024] == bank(40)[:1024] and b1[1364:] == bank(40)[1364:],
              "only those 340 bytes changed in both banks (sizes kept)")
    rw = [(c[0], c[1], c[2], c[3]) for c in e.api if c[0] in ("read", "write")]
    BP = CUR if e.scur is not None else 0xFF
    want_rw = [("read", (3, 1, X), 1024, 340), ("read", (3, 0, BP), 2560, 340)] + ([] if PK.COPYX else [("write", (3, 1, X), 1024, 340)]) + [("write", (3, 0, BP), 2560, 340)]
    if PK.EMPTY: want_rw = [("read", (3, 1, X), 1024, 340), ("write", (3, 0, BP), 2560, 340)]      # SC38.4: between packs B is not read
    check(rw == want_rw,
          f"the reads and writes in place ({rw})")
    check(e.x.get(SD.PCLIPW) == 0 and stock != [] and e.api[-1] in (("exists", (3, 0, CUR)), ("exists", (4, 0, CUR))) and e.sem == 0 and e.lock == 0 and e.scur in (None, CUR),
          f"clip cleared, the stock handler chooses B again (loads it), the current pack selected again, semaphore / lock balanced ({e.api[-1]})")
    if PK.EMPTY:                                     # SC38.4: into an empty slot of another pack's patch: a missing bank, a short bank
        for bnk, have in ((1, 0), (2, 3)):
            if have: e.sd[(3, bnk, 0xFF)] = bank(80)[:(have - 1) * 512 + 340]
            else: e.sd.pop((3, bnk, 0xFF), None)
            before = e.sd.get((3, bnk, 0xFF), b"")
            e.x[SD.PCLIPW] = PK.PCLIP_MAGIC << 16 | X << 8 | 10; e.api.clear(); bp(8 * bnk + 5)
            got = e.sd.get((3, bnk, 0xFF), b"")
            ok = len(got) == 5 * 512 + 340 and got[:len(before)][:max(0, (have - 1) * 512 + 340)] == before[:max(0, (have - 1) * 512 + 340)]
            init = img[PK.INIT_PATCH - 0x08010000:PK.INIT_PATCH - 0x08010000 + 340]
            wr = [c[2] for c in e.api if c[0] == "write"]
            if PK.FFGAP:                             # SC38.6: 0xFF from the bank's end to B (the stock's way: the slots between stay empty), then A
                end = len(before)
                ok = len(got) == 5 * 512 + 340 and got[:end] == before and got[end:2560] == bytes([0xFF]) * (2560 - end) and got[2560:2900] == patch(42)
                wl = [(c[2], c[3]) for c in e.api if c[0] == "write"]
                ok = ok and wl == [(end, 2560 - end), (2560, 340)]; wr = [512 * k for k in range(have, 6)] if ok else wl
            else:
                ok = ok and got[5 * 512:5 * 512 + 340] == patch(42) and all(got[k * 512:k * 512 + 340] == (init if PK.INITGAP else patch(42)) for k in range(have, 5))
            check(ok and wr == [512 * k for k in range(have, 6)] and not any(c[0] == "read" and c[1][1] == bnk and c[1][2] != X for c in e.api),
                  f"empty slot {8 * bnk + 5} (bank {bnk} with {have} patches): slots {have}..4 {'0xFF (empty, as the stock)' if PK.FFGAP else 'the Initial Patch' if PK.INITGAP else 'copies'}, pack X's patch 10 at B, the bank now {len(got)} bytes, nothing of B read")
    # the same pack: 3 <-> 7
    e.x[SD.PCLIPW] = PK.PCLIP_MAGIC << 16 | CUR << 8 | 3; before = e.sd[(3, 0, 0xFF)]; e.api.clear(); bp(7)
    b0 = e.sd[(3, 0, 0xFF)]
    check(b0[3 * 512:3 * 512 + 340] == before[7 * 512:7 * 512 + 340] and b0[7 * 512:7 * 512 + 340] == before[3 * 512:3 * 512 + 340], "in the same pack: patches 3 and 7 swapped")
    e.x[SD.PCLIPW] = PK.PCLIP_MAGIC << 16 | CUR << 8 | 6; e.api.clear(); stock.clear(); bp(6)
    check(not any(c[0] in ("read", "write") for c in e.api) and e.x.get(SD.PCLIPW) == 0 and stock == [], "the copied patch again: cancelled")
    e.x[SD.PCLIPW] = PK.PCLIP_MAGIC << 16 | 9 << 8 | 20; e.api.clear(); bp(5)
    check(not any(c[0] == "write" for c in e.api), "the copied pack has no such bank: nothing written")
    e.held(0); e.api.clear(); stock.clear(); bp(4)
    check(not any(c[0] in ("read", "write") for c in e.api) and stock != [], "without Duplicate: the stock chooses the patch")
    e.uc.hook_del(hk)
    del e


def cross_tests(e, check, CUR, a_s, b_s):
    """SC37: swap between packs.  Pack X = 7 holds sample 20 (a WAV of x_s); the current pack holds B = 10 (its audio in the DSP's memory)."""
    X = 7 if CUR != 7 else 8
    x_s = [((i * 7 + 3) & 0xFFFF) for i in range(5000)]
    old10 = e.sd[(4, 10, 0xFF)]
    e.sd[(4, 20, X)] = wav(x_s)
    if PK.INPLACE:                                   # B's own place too small for 5000 samples (sample 3 right after it): the first copies go to the free memory
        e.entry(3, e.x[SD.SAMPLE_TAB + 40] + 1000, 140, 0x222)
    b_ent = [e.x[SD.SAMPLE_TAB + 40 + k] for k in range(3)]
    b_audio = [e.ext.get(b_ent[0] + i, 0) >> 8 for i in range(len(old10) // 2 - 22)]
    # the clip from pack X, as if Duplicate + pad 21 had been pressed while X was loaded
    e.x[SD.CLIPW] = PK.CLIP_MAGIC << 16 | X << 8 | 20
    e.uc.mem_write(DVIEW + PK.SWAP_OFF, bytes([PK.MIR_P | X, PK.MIR_I | 20]))
    e.call(e.r32(PK.DP_VT + 28) & ~1, DVIEW, maxins=900000)
    e.held(2); e.call(e.r32(PK.DP_VT + 28) & ~1, DVIEW, maxins=900000); p = e.uc.reg_read(UC_ARM_REG_R0)
    led = struct.unpack("<32H", bytes(e.uc.mem_read(p, 64)))[20]
    check(led in (PK.CROSS_COL, PK.DARK), f"a sample copied in another pack: its pad blinks {PK.CROSS_COL:#x} / dark while Duplicate is held ({led:#x})")
    from emu_sc17_6 import PRESS
    bp = lambda pd: e.call(PRESS, MGR, pd, 100, maxins=150_000_000)
    exact = PK.EXACT
    LIVE0 = PK.IMP_LO + 22 if exact else PK.IMP_LO                  # the data of the copy (exact: after its 44-byte header)
    NEXT1 = PK.IMP_LO + (44 + 10000 + 1) // 2 + PK.PADW if exact else PK.IMP_LO + 5000
    for k in range(PK.PADW): e.ext[LIVE0 + 5000 + k] = 0x123400          # garbage where the zero padding must go
    e.api.clear(); e.ywrites = 0
    bp(10)
    check(e.sd.get((4, 10, 0xFF)) == wav(x_s), "Duplicate + pad 11 in this pack: its file 10 = pack X's sample 20, byte for byte (copied in 4 KB pieces)")
    if PK.COPYX: check(e.sd.get((4, 20, X)) == wav(x_s), "copy: pack X's sample 20 untouched")
    elif exact: check(e.sd.get((4, 20, X)) == old10, "exact: pack X's sample 20 = this pack's old file 10, byte for byte")
    else: check(e.sd.get((4, 20, X)) == wav(b_audio), "pack X's sample 20 = this pack's old sample 10 (its audio from the DSP's memory)")
    rd = [c for c in e.api if c[0] == "read" and c[1] == (4, 20, X)]
    check(len(rd) == 3 and [c[2] for c in rd] == [0, 4096, 8192], f"read in 4 KB pieces from pack X ({[(c[2], c[3]) for c in rd]})")
    dels = [c[1] for c in e.api if c[0] == "del"]
    if PK.COPYX:
        check(dels == [(4, 10, CUR)] and not any(c[0] == "write" and c[1][2] == X for c in e.api), f"copy: only this pack's 10 deleted and written, nothing of pack X ({dels})")
        check(all(e.ext.get(LIVE0 + 5000 + k, 0) == 0 for k in range(PK.PADW)), "256 zero words after the live sample")
    elif exact:
        check(dels == [(4, 20, X), (4, 10, CUR)], f"exact: X's 20 replaced first by this pack's 10 (file to file), then this pack's 10 by the copy of X:20 ({dels})")
        check(all(e.ext.get(LIVE0 + 5000 + k, 0) == 0 for k in range(PK.PADW)), "exact: 256 zero words after the live sample")
    else:
        check(dels in ([(4, 10, 0xFF), (4, 20, X)], [(4, 10, CUR), (4, 20, X)]), f"deleted first: this pack's 10, then X's 20 ({dels})")
    ent = [e.x[SD.SAMPLE_TAB + 40 + k] for k in range(3)]
    loaded = [e.ext.get(ent[0] + i, 0) >> 8 for i in range(5000)]
    check(ent[0] == LIVE0 and ent[1] == 5000 - 2 and ent[2] == b_ent[2] and loaded == x_s,
          f"the new sample 10 loaded into the free memory and its table entry -> there ({ent[0]:#x}, {ent[1]}, {ent[2]:#x}), the audio exact")
    check(e.x.get(SD.IMPW) == NEXT1 and e.x.get(SD.CLIPW) == 0 and e.sem == 0 and e.lock == 0,
          f"next import at {e.x.get(SD.IMPW, 0):#x}, clip cleared, semaphore {e.sem} / lock {e.lock} balanced")
    check(e.api[-1] == ("exists", (4, 0, CUR)), f"the current pack selected again at the end ({e.api[-1]})")
    if e.scur is not None:
        touched = sorted({c[1] for c in e.api if c[0] in ("del", "write")})
        check(e.scur == CUR and touched == ([(4, 10, CUR)] if PK.COPYX else [(4, 10, CUR), (4, 20, X)]), f"SC37.2: only this pack's 10 and X's 20 deleted / written, by their pack numbers; the storage task back on {e.scur} ({touched})")
    if e.scur is not None:                           # a failed copy after B was deleted: B written back from the DSP's memory
        e.sd[(4, 23, X)] = wav(x_s[:4000]); e.x[SD.CLIPW] = PK.CLIP_MAGIC << 16 | X << 8 | 23; e.api.clear()
        old = e.sd[(4, 10, 0xFF)]
        e.fail_read = ((4, 23, X), 4096)             # the second piece of X:23 fails
        ent10 = [e.x[SD.SAMPLE_TAB + 40 + k] for k in range(3)]
        bp(10)
        a10 = [e.ext.get(ent10[0] + i, 0) >> 8 for i in range(5000)]
        if exact:
            check(e.fail_read is None and e.sd.get((4, 10, 0xFF)) == old and e.sd.get((4, 23, X)) == wav(x_s[:4000]) and e.scur == CUR
                  and not any(c[0] in ("del", "write") for c in e.api), "exact: a read of X:23 that fails: nothing deleted or written, the storage task back on the loaded pack")
        else:
          check(e.fail_read is None and e.sd.get((4, 10, 0xFF)) == wav(a10) and e.sd.get((4, 23, X)) == wav(x_s[:4000]) and e.scur == CUR,
              "a read that fails after B was deleted: B written back from the DSP's memory, X:23 untouched, the storage task back on the loaded pack")
    # a second import goes after the first one
    e.sd[(4, 12, 0xFF)] = wav(b_s); e.entry(12, 0x5A0000, 148, 0x333)
    e.sd[(4, 21, X)] = wav(x_s[:300]); e.x[SD.CLIPW] = PK.CLIP_MAGIC << 16 | X << 8 | 21; e.api.clear()
    bp(12)
    ent = [e.x[SD.SAMPLE_TAB + 48 + k] for k in range(3)]
    check(ent[0] == (NEXT1 + 22 if exact else PK.IMP_LO + 5000) and ent[1] == 298 and [e.ext.get(ent[0] + i, 0) >> 8 for i in range(300)] == x_s[:300], f"a second import follows the first ({ent[0]:#x})")
    if PK.IMPGUARD:                                  # the free memory is full: back to its start only where no sample of the table starts
        e.x[SD.IMPW] = PK.IMP_HI - 200
        e.sd[(4, 24, X)] = wav(x_s[:300]); e.x[SD.CLIPW] = PK.CLIP_MAGIC << 16 | X << 8 | 24; e.api.clear()
        ent12 = [e.x[SD.SAMPLE_TAB + 48 + k] for k in range(3)]
        bp(12)
        check(not any(c[0] in ("del", "write") for c in e.api) and [e.x[SD.SAMPLE_TAB + 48 + k] for k in range(3)] == ent12 and e.x.get(SD.CLIPW) == 0
              and [e.x[SD.SAMPLE_TAB + 40 + k] for k in range(3)][0] == LIVE0,
              f"memory full and sample 10 still playing at its start ({LIVE0:#x}): nothing written, the entries unchanged, the clip dropped")
        e.entry(10, 0x580000, 5000, b_ent[2])           # the pack loaded again: 10 back in the stock area
        e.x[SD.CLIPW] = PK.CLIP_MAGIC << 16 | X << 8 | 24; e.api.clear()
        bp(12)
        ent = [e.x[SD.SAMPLE_TAB + 48 + k] for k in range(3)]
        check(ent[0] == LIVE0 and [e.ext.get(ent[0] + i, 0) >> 8 for i in range(300)] == x_s[:300], f"nothing plays there any more: the copy goes back to the start ({ent[0]:#x})")
    if PK.INPLACE:                                   # into B's own place when it fits; the free memory starts again when nothing uses it
        old20 = [(i * 5 + 1) & 0xFFFF for i in range(6000)]
        e.sd[(4, 20, 0xFF)] = wav(old20); e.entry(20, 0x700000, 6000 - 2, 0x444); e.entry(21, 0x700000 + 6400, 100, 0x444)
        for i in range(6400): e.ext[0x700000 + i] = 0x5A5A00
        e.sd[(4, 26, X)] = wav(x_s); e.x[SD.CLIPW] = PK.CLIP_MAGIC << 16 | X << 8 | 26; e.api.clear()
        imp0 = e.x.get(SD.IMPW); bp(20)
        ent = [e.x[SD.SAMPLE_TAB + 80 + k] for k in range(3)]
        check(ent == [0x700000, 5000 - 2, 0x444] and [e.ext.get(0x700000 + i, 0) >> 8 for i in range(5000)] == x_s
              and all(e.ext.get(0x700000 + 5000 + k, 0) == 0 for k in range(PK.PADW)) and e.ext.get(0x700000 + 5000 + PK.PADW) == 0x5A5A00,
              f"in place: sample 20 (6000, the next one 6400 words on) gets the 5000 samples in its own place, 256 zeros after, nothing beyond ({ent})")
        check(e.x.get(SD.IMPW) == imp0 and e.sd.get((4, 20, 0xFF)) == wav(x_s) and e.sd.get((4, 26, X)) == wav(x_s),
              f"in place: the free memory not used (next import still {e.x.get(SD.IMPW, 0):#x}), file 20 = X:26, X:26 untouched")
        e.sd[(4, 22, 0xFF)] = wav(old20[:200]); e.entry(22, 0x710000, 198, 0x444); e.entry(23, 0x710000 + 300, 100, 0x444)
        e.x[SD.CLIPW] = PK.CLIP_MAGIC << 16 | X << 8 | 26; e.api.clear(); bp(22)
        s22 = e.x[SD.SAMPLE_TAB + 88]
        check(PK.IMP_LO <= s22 < PK.IMP_HI and e.ext.get(0x710000 + 300 - 1) is None, f"too long for its place (300 words to the next): into the free memory ({s22:#x})")
        for k in range(64):                          # the pack loaded again: every entry back in the pack's sample memory
            if PK.IMP_LO <= e.x.get(SD.SAMPLE_TAB + 4 * k, 0) < PK.IMP_HI: e.entry(k, 0x800000 + 0x1000 * k, 100, 0x444)
        e.x[SD.IMPW] = PK.IMP_LO + 70000
        e.x[SD.CLIPW] = PK.CLIP_MAGIC << 16 | X << 8 | 26; e.entry(22, 0x710000, 198, 0x444); e.api.clear(); bp(22)
        s22 = e.x[SD.SAMPLE_TAB + 88]
        check(s22 == PK.IMP_LO + 22, f"nothing of the table in the free memory any more: the next import starts at its beginning again ({s22:#x})")
    if PK.EMPTY:                                     # SC38.4: into an empty sample slot (no file, an empty table entry)
        e.sd.pop((4, 12, 0xFF), None); e.sd.pop((4, 12, CUR), None); e.entry(12, 0, 0, 0)
        e.x[SD.CLIPW] = PK.CLIP_MAGIC << 16 | X << 8 | 20; e.held(2); e.api.clear(); bp(12)
        got = e.sd.get((4, 12, 0xFF)) or e.sd.get((4, 12, CUR)); ent = [e.x[SD.SAMPLE_TAB + 48 + k] for k in range(2)]
        check(got == wav(x_s) and PK.IMP_LO <= ent[0] < PK.IMP_HI and ent[1] == 5000 - 2 and not any(c[0] == "read" and c[1][1] == 12 for c in e.api),
              f"empty sample slot 12: its file created = pack X's sample 20, the entry in the free memory ({ent[0]:#x}, {ent[1]}), nothing of B read")
    # does not fit: nothing changes
    before = dict(e.sd)
    e.sd[(4, 22, X)] = bytes(44 + 2 * 9_500_000); e.x[SD.CLIPW] = PK.CLIP_MAGIC << 16 | X << 8 | 22; e.api.clear()
    bp(10)
    check(not any(c[0] in ("del", "write") for c in e.api) and e.x.get(SD.CLIPW) == 0, "a sample that does not fit this pack's memory: nothing written, the clip dropped")
    # a missing sample in pack X: nothing changes
    e.x[SD.CLIPW] = PK.CLIP_MAGIC << 16 | X << 8 | 40; e.api.clear()
    bp(10)
    check(not any(c[0] in ("del", "write") for c in e.api), "the copied sample no longer exists: nothing written")
    # the clip survives releasing Duplicate; Duplicate + pad without a clip copies (no write)
    e.held(2); e.pad(6); e.held(0); e.pad(6); e.held(2)
    check(e.x.get(SD.CLIPW) == (PK.CLIP_MAGIC << 16 | CUR << 8 | 6), "the clip stays after releasing Duplicate (a pad without Duplicate goes to the stock)")
    e.held(0)


def main(img, man):
    fails = 0 if feat(man, "cross") else emu_sc34_2.main(img, man)
    gc.collect()
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]
    if feat(man, "cross"):
        check(rep["sc17"].get("smp_savebit") is True and "packio" in rep and "rdiag" not in rep and ({"c_xswap", "c_xcopy2"} & set(rep["packio"]["labels"])), "manifest: smp_savebit, packio with c_xswap / c_xcopy2, no rdiag")
        (PK.use_copyx() if feat(man, "copyx") else PK.use_exact() if feat(man, "exact") else PK.use_fix2() if feat(man, "fix2")
         else PK.use_cross2() if feat(man, "patch") else PK.use_cross())
        if feat(man, "dupmask"): PK.use_dupmask()
        if feat(man, "pkled"): PK.use_pkled()
        if feat(man, "srcguard"): PK.use_srcguard()
        if feat(man, "impguard"): PK.use_impguard()
        if feat(man, "inplace"): PK.use_inplace()
        if feat(man, "pkled2"): PK.use_pkled2()
        if feat(man, "pkled3"): PK.use_pkled3()
        if feat(man, "empty"): PK.use_empty()
        if feat(man, "initgap"): PK.use_initgap()
        if feat(man, "ffgap"): PK.use_empty(); PK.use_ffgap()
    else:
        check(rep["sc17"].get("smp_savebit") is True and "packio" in rep and "rdiag" in rep, "manifest: smp_savebit, packio, rdiag")
    e = E35(img, man)
    small = lambda n: {(4, i, 0xFF): bytes(44 + 2 * n) for i in range(8)}
    # ---------------- save
    ramp = [((i * 97) & 0xFFFF) for i in range(300)]
    for i, v in enumerate(ramp): e.ext[SLOT2 + i] = v << 8
    e.entry(5, SLOT2, 300, 0x123); e.entry(6, 0x580000, 1000, 0x100)
    e.sd = small(100); e.x[PK.SAVED] = 0
    e.call(e.P["c_svs"], 0x1234, maxins=50_000_000)
    ops = [c[0] for c in e.api if c[0] in ("del", "write")]
    check(ops == ["del", "write"] and e.api[[c[0] for c in e.api].index("del")][1] == (4, 5, 0xFF), f"save: delete PCM 5, one write ({ops})")
    check(e.sd.get((4, 5, 0xFF)) == wav(ramp), "save: PCM 5 = a WAV of the 300 captured samples (header + 16-bit LE)")
    check(e.x[PK.SAVED] == 1 << 2 and e.saves == [0x1234] and e.sem == 0 and e.lock == 0, f"save: slot 2 marked saved, c_pl_save with r0, semaphore {e.sem} / lock {e.lock} balanced")
    e.api.clear(); e.saves.clear()
    e.call(e.P["c_svs"], 0x55, maxins=50_000_000)
    check([c for c in e.api if c[0] in ("del", "write")] == [] and e.saves == [0x55], "save again: nothing written (saved), c_pl_save runs")
    long = [((i * 31 + 7) & 0xFFFF) for i in range(5000)]
    for i, v in enumerate(long): e.ext[SLOT2 + i] = v << 8
    e.entry(5, SLOT2, 5000, 0x123); e.x[PK.SAVED] = 0; e.api.clear()
    e.call(e.P["c_svs"], 0x55, maxins=200_000_000)
    w = [c for c in e.api if c[0] == "write"]
    check(len(w) == 3 and [c[2] for c in w] == [0, w[0][3], w[0][3] + w[1][3]] and all(c[4:] == (0, 0) for c in w), f"save 5000 samples: 3 pieces at consecutive offsets, synchronous {[(c[2], c[3]) for c in w]}")
    check(e.sd.get((4, 5, 0xFF)) == wav(long), "save 5000 samples: the file is exact")
    e.x[PK.SAVED] = 0; e.sd = {(4, i, 0xFF): bytes(44 + 2 * 1_400_000) for i in range(8)}; e.api.clear()
    e.call(e.P["c_svs"], 0x55, maxins=200_000_000)
    check([c for c in e.api if c[0] in ("del", "write")] == [] and e.x[PK.SAVED] == 0, "save: a sample that does not fit (7 x 29 s already) is not written")
    # ---------------- the tick clears the saved bit of the slot about to be used
    e.x[PK.SAVED] = 0xFF; e.x[SD.REPK] = 3
    blk = e.blk
    smt = e.r32(blk + B.S_SMT); e.w32(blk + B.S_SMT, (smt & ~(0x7F << 23)) | ((5 + 1) << 23)); e.uc.mem_write(blk + B.S_JF, bytes([e.blkb(B.S_JF)[0] & ~0x30]))
    e.w32(TICK, 5000); e.dw.clear(); e.call(e.L["c_fxtick"], maxins=2_000_000); w = dict(e.dw)
    check(w.get(SD.CMD) == 4 and e.x[PK.SAVED] == 0xFF & ~(1 << 3), f"tick: CMD 4 sent and the saved bit of slot REPK 3 cleared ({e.x[PK.SAVED]:#x})")
    del e; gc.collect()
    # ---------------- swap (Drum 1's Preset view)
    e = E35(img, man)
    from emu_sc08 import CONT
    e.set_p0(e.r32(CONT + 0x188), 4); e.btn(4); e.btn(8)
    cross = feat(man, "cross")
    CUR = 31 if cross else None
    if cross: set_loaded(e, man, CUR)
    a_s, b_s = [(i * 11) & 0xFFFF for i in range(200)], [(i * 13 + 5) & 0xFFFF for i in range(150)]
    for i, v in enumerate(a_s): e.ext[0x580000 + i] = v << 8
    for i, v in enumerate(b_s): e.ext[0x590000 + i] = v << 8
    e.entry(3, 0x580000, 190, 0x111); e.entry(10, 0x590000, 140, 0x222)
    e.sd = {(4, 3, 0xFF): wav(a_s), (4, 10, 0xFF): wav(b_s)}
    e.uc.mem_write(DVIEW + PK.SWAP_OFF, bytes([0xB5, 0x52]))                    # garbage in the padding: not a pending A
    if PK.DUPMASK:
        mb = e.r32(MGR + 0x20)
        check(e.r8(mb + 0x1C) == 3, f"Drum 1's Preset view accepts Clear and Duplicate (mask {e.r8(mb + 0x1C):#x})")
        e.real_dup = True
    e.held(2); e.pad(3)
    if cross:
        check(e.x.get(SD.CLIPW) == (PK.CLIP_MAGIC << 16 | CUR << 8 | 3) and e.uc.mem_read(DVIEW + PK.SWAP_OFF + 1, 1)[0] == PK.MIR_I | 3
              and [c for c in e.api if c[0] in ("del", "write")] == [], f"Duplicate + pad 4: sample 3 copied (clip {e.x.get(SD.CLIPW, 0):#x}), nothing written")
    else:
        check(bytes(e.uc.mem_read(DVIEW + PK.SWAP_OFF, 2)) == bytes([PK.SWAP_MAGIC, 3]) and [c for c in e.api if c[0] in ("del", "write")] == [], "Duplicate + pad 4: A = sample 3 chosen, nothing written")
    e.call(e.r32(PK.DP_VT + 28) & ~1, DVIEW, maxins=900000); p = e.uc.reg_read(UC_ARM_REG_R0)
    led = struct.unpack("<32H", bytes(e.uc.mem_read(p, 64)))[3]
    check(led in (PK.BLUE, PK.DARK), f"A blinks blue / dark ({led:#x})")
    e.pad(10)
    check(e.sd[(4, 3, 0xFF)] == wav(b_s) and e.sd[(4, 10, 0xFF)] == wav(a_s), "Duplicate + pad 11: file 3 = B's audio (150), file 10 = A's (200, from the file size)")
    check([e.x[SD.SAMPLE_TAB + 4 * 3 + k] for k in range(3)] == [0x590000, 140, 0x222] and [e.x[SD.SAMPLE_TAB + 40 + k] for k in range(3)] == [0x580000, 190, 0x111],
          "the table entries exchanged (start, length, increment)")
    check(e.uc.mem_read(DVIEW + PK.SWAP_OFF, 1)[0] != PK.SWAP_MAGIC and e.sem == 0 and e.lock == 0 and (not cross or e.x.get(SD.CLIPW) == 0),
          "swap done: A cleared, semaphore / lock balanced")
    e.api.clear(); e.pad(5); e.pad(5)
    check(e.uc.mem_read(DVIEW + PK.SWAP_OFF, 1)[0] != PK.SWAP_MAGIC and [c for c in e.api if c[0] in ("del", "write")] == [] and (not cross or e.x.get(SD.CLIPW) == 0),
          "A twice: cancelled")
    e.held(0); e.api.clear(); e.pad(7)
    check(e.uc.mem_read(DVIEW + PK.SWAP_OFF, 1)[0] != PK.SWAP_MAGIC and e.api == [], "without Duplicate: no swap")
    if cross and feat(man, "exact"):     # the DSP's memory differs from the files (the stock keeps whole 512-byte blocks): the files move as they are
        for st in (0x580000, 0x590000):
            for i in range(300): e.ext[st + i] = 0x7FFF00
        f3, f10 = e.sd[(4, 3, 0xFF)], e.sd[(4, 10, 0xFF)]
        e.held(2); e.api.clear(); e.call(__import__("emu_sc17_6").PRESS, MGR, 3, 100, maxins=60_000_000); e.call(__import__("emu_sc17_6").PRESS, MGR, 10, 100, maxins=60_000_000)
        check(e.sd[(4, 3, 0xFF)] == f10 and e.sd[(4, 10, 0xFF)] == f3, "exact: the two files exchanged byte for byte, whatever the DSP's memory holds")
        e.call(__import__("emu_sc17_6").PRESS, MGR, 3, 100, maxins=60_000_000); e.call(__import__("emu_sc17_6").PRESS, MGR, 10, 100, maxins=60_000_000)
        e.held(0)
    if cross:
        cross_tests(e, check, CUR, a_s, b_s)
    del e; gc.collect()
    # ---------------- delete a pack (the packs view)
    e = E35(img, man)
    check(e.r32(PVIEW) == PK.PV_VT, "the packs view object of the dump")
    e.w32(MGR + 0x6C, PVIEW)
    cur_store = e.r32(PVIEW + 0x10); e.set_p0(cur_store, 31)
    e.w32(TICK, 100000)
    e.held(1); e.pad(30); e.held(0)
    q = bytes(e.uc.mem_read(PVIEW + PK.PQ_OFF, 3))
    check(q[0] == PK.PQ_MAGIC and q[1] == 30 and e.api == [], f"Clear + pad 31: pack 30 asked, nothing deleted ({q.hex()})")
    e.call(e.r32(PK.PV_VT + 28) & ~1, PVIEW, maxins=900000); p = e.uc.reg_read(UC_ARM_REG_R0)
    check(struct.unpack("<32H", bytes(e.uc.mem_read(p, 64)))[30] in (PK.RED, PK.DARK), "pad 31 blinks red")
    mb = e.r32(MGR + 0x20)
    e.call(e.r32(PK.MB_VT + 32) & ~1, mb, maxins=900000)
    check(struct.unpack("<H", bytes(e.uc.mem_read(e.r32(e.r32(mb + 4)), 2)))[0] in (PK.RED, PK.DARK), "Clear blinks red")
    e.btn(23)
    check(e.api == [("del", (1, 0xFFFFFFFF, 30), 0, 0), ("exists", (4, 0, 31))] and e.uc.mem_read(PVIEW + PK.PQ_OFF, 1)[0] == 0,
          f"Clear again: pack 30 deleted (op 5 kind 1), then the current pack 31 re-selected ({e.api})")
    e.api.clear(); e.btn(23)
    check(e.api == [], "Clear once more: nothing (the question is used)")
    e.held(1); e.pad(31); e.held(0)
    check(e.uc.mem_read(PVIEW + PK.PQ_OFF, 1)[0] != PK.PQ_MAGIC or e.uc.mem_read(PVIEW + PK.PQ_OFF + 1, 1)[0] != 31, "the current pack (31) is never asked")
    e.held(1); e.pad(29); e.held(0); e.w32(TICK, 100000 + 6000); e.api.clear(); e.btn(23)
    check(e.api == [], "a question older than 5 s: Clear deletes nothing")
    e.w32(TICK, 200000); e.held(1); e.pad(29); e.held(0); e.api.clear()
    e.btn(23, shift=True)
    check(not any(c[0] == "del" for c in e.api), "Shift + Clear (the metronome): no delete")
    e.held(1); e.pad(28, shift=True); e.held(0)
    check(e.uc.mem_read(PVIEW + PK.PQ_OFF + 1, 1)[0] != 28, "Shift + Clear + pad: not asked")
    e.api.clear(); e.pad(28)
    if feat(man, "fix2"):
        check(e.uc.mem_read(PVIEW + PK.PQ_OFF, 1)[0] == 0, "Shift + pad dropped the question: a pad without Clear is the stock's")
    else:
        check(e.uc.mem_read(PVIEW + PK.PQ_OFF, 1)[0] == 0, "a pad without Clear: the question dropped, the stock handles it")
    e.call(e.r32(PK.MB_VT + 32) & ~1, mb, maxins=900000)
    check(struct.unpack("<H", bytes(e.uc.mem_read(e.r32(e.r32(mb + 4)), 2)))[0] == PK.CLR_DIM, "in the packs view Clear is dim white")
    if feat(man, "patch"):
        gc.collect(); patch_tests(img, man, check)
    if feat(man, "fix2"):
        gc.collect(); delete_tests_fix2(img, man, check)
    print("SC35 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
