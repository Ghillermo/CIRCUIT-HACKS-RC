"""SC54 / Beta 5.34 tests: tools/morphz.py (the patch morph), through the controller, the real LED task (the frame) and the knobs' route; the card
reads of the patches answered from Python (mpatch's c_mpr hooked).

    python tools/emu_morph.py BUILD.bin manifest.json
  * Synth 1: patches 4 + 5 held 0.4 s = the morph view in Synth 1's alternative view (pads 1 / 8 dim in Synth 1's colour, pad 32 red, the rest
    dark); K1 at the end = the live patch becomes patch 5, K1 a quarter = halfway between the present sound and patch 4; pad 1 = the envelope;
    Octave up = the initial patch one place later; Duplicate nothing; Preset = the patches (4 / 5 white), Preset again = the morph view; Mixer, then
    Synth 1 = the morph view; Synth 1 there = the Note view, again = the morph view; one patch held 0.4 s = nothing, two = the chain anew; pad 32 =
    out, the patches as the stock draws them; one patch held = no morph; held + Duplicate = on; Preset twice with the morph off = the alternative view;
  * MIDI 1 (the own synth on): slots 1 + 2 held 0.4 s = the morph view; the LED task's stack no deeper than with the morph off; Preset toggles;
    Mixer, then MIDI 1 = the morph view; pad 32 = out.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc48_8 as S  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import emu_sc17_6 as T6  # noqa: E402
import morphz as M  # noqa: E402
import jumpseq as J  # noqa: E402
import mpatch as MP  # noqa: E402

MGR, PRESS, RELEASE = S.MGR, T6.PRESS, T6.RELEASE
SUS, NOCUR = "--sus" in sys.argv, "--nocur" in sys.argv     # SC55.1
BASE = 0x08010000


def rows(img):
    out = []
    for k in range(M.NROWS):
        r = img[M.TABLE - BASE + 8 * k:M.TABLE - BASE + 8 * k + 8]
        off = r[2] | r[3] << 8
        if r[0] >= 0xFD or not 30 <= off < 340: continue
        out.append((k, off, r[4] in (1, 2), r[6] - 256 if r[6] > 127 else r[6], r[7]))
    return out


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = S.ET(img, man)
    def drain():                                     # the MIDI-out queues: the stock's patch loads queue bytes the emulator never sends, and a view
        r = e.r32(0x200069F4)                        # change flushes them (an endless loop here)
        for k in range(e.r8(r + 0x18)): e.uc.mem_write(e.r32(e.r32(e.r32(r + 0x14) + 4 * k) + 0x10), bytes(4))
    def flush(uc, a_, s_, d_):                       # the MIDI-out flush (0x08035A50): its port's queue emptied first, as the hardware would
        uc.mem_write(e.r32(uc.reg_read(UC_ARM_REG_R0) + 0x10), bytes(4))
    e.uc.hook_add(UC_HOOK_CODE, flush, begin=0x08035A50, end=0x08035A50)
    e.btn = lambda b: (drain(), e.call(0x08033320, MGR, b, maxins=20_000_000), drain(), e.call(0x0803381A, MGR, b, maxins=20_000_000))   # (the morph's own taps need more than ET's budget)
    R = man["report"]
    SVCL = R["morphz"]["labels"].get("c_mzsvc")                                          # (SC55.4 use_svc) Synth 1 / 2's writes in the DSP service's head
    sem = [0, 0]                                                                         # the semaphore taken in the writes / 0x08021FDC calls
    if SVCL:
        nxt = int(R["morphz"]["prev"]["svc"], 16)
        def stub(uc, a_, s_, d_): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)   # the rest of the service chain: not run
        e.uc.hook_add(UC_HOOK_CODE, stub, begin=nxt, end=nxt)
        def cnt(k):
            def f_(uc, a_, s_, d_): sem[k] += 1
            return f_
        e.uc.hook_add(UC_HOOK_CODE, cnt(0), begin=0x08021064, end=0x08021064)
        e.uc.hook_add(UC_HOOK_CODE, cnt(1), begin=M.MARK_RAW, end=M.MARK_RAW)
    def svc():
        if SVCL: e.call(int(SVCL, 16), maxins=8_000_000)
    L = {k: int(v, 16) for k, v in R["morphz"]["labels"].items()}
    t = [500000]
    def at(ms): t[0] += ms; e.w32(J.HAL_TICK, t[0])
    at(0)
    recs = {}                                                                           # (bank, offset) -> bytes
    def mpr(uc, a, s_, d):
        bank, off, buf, n = (uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))
        data = recs.get((bank, off), b"\xFF" * n)
        uc.mem_write(buf, bytes(data[:n]).ljust(n, b"\xFF"))
        uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    cmpr = int(R["mpatch"]["labels"]["c_mpr"], 16)
    e.uc.hook_add(UC_HOOK_CODE, mpr, begin=cmpr, end=cmpr)
    pal = lambda i: struct.unpack_from("<H", img, J.PAL + 2 * i - BASE)[0]
    hold = lambda q: (e.call(PRESS, MGR, q, 100, maxins=8_000_000), at(5))
    let = lambda q: (e.call(RELEASE, MGR, q, maxins=8_000_000), at(5))
    pad = lambda q: (hold(q), let(q))
    st = lambda o: e.r8(M.MZ + o)
    def frames(n):
        f = None
        for _ in range(n): at(10); f = X.frame(e); svc()
        return f
    # ---- Synth 1
    live = lambda: bytes(e.uc.mem_read(M.LIVE + 30, 310))
    e.btn(0); e.btn(8); frames(2)
    p0 = live()
    RW = rows(img)
    def patch_like(seed):
        b = bytearray(p0)
        for k, off, cont, lo, hi in RW:
            if cont:
                span = (hi - lo) if lo < 0 else hi
                b[off - 30] = (64 + lo + (seed * 37 + k * 11) % (span + 1)) if lo < 0 else (seed * 29 + k * 7) % (hi + 1)
        return bytes(range(0)) + bytes(30) + bytes(b)
    P4, P5, P6 = patch_like(1), patch_like(2), patch_like(3)
    for n, p in ((4, P4), (5, P5), (6, P6)): recs[(n >> 3, 512 * (n & 7))] = p
    f_stock = frames(1)
    e.call(int(R["sc14"]["labels"]["c_gst"], 16)); GS = e.uc.reg_read(UC_ARM_REG_R0)
    src = lambda: bool(e.r8(GS + M.S_PAINT) & M.F_SRC)
    hold(4); hold(5); frames(1); at(450); f = frames(2); let(4); let(5)
    check(st(M.O_ACT) == 0 and st(M.O_N) == 3 and src() and bytes(e.uc.mem_read(M.MZ + M.O_SL, 2)) == b"\x04\x05",
          f"Synth 1: patches 4 + 5 held 0.4 s = the morph on, in Synth 1's alternative view (act {st(M.O_ACT)}, n {st(M.O_N)}, "
          f"slots {bytes(e.uc.mem_read(M.MZ + M.O_SL, 2)).hex()}, source view {src()})")
    check(f[0] == pal(9) and f[7] == pal(9) and f[31] == M.RED and all(f[q] == 0 for q in range(32) if q not in (0, 7, 31)),
          f"the morph view: pads 1 / 8 dim Synth 1, pad 32 red, the rest dark ({[hex(x) for x in f[:32]]})")
    frames(4)
    check(st(M.O_CV) & 7 == 7, f"the chain cached ({st(M.O_CV):#x})")
    for _ in range(130): e.knob(0, 1)
    frames(14)
    lv = live()
    bad = [(k, off) for k, off, cont, lo, hi in RW if lv[off - 30] != P5[off]]
    check(not bad, f"K1 at the end: the live patch = patch 5 ({len(bad)} rows differ: {bad[:6]})")
    if SVCL:
        check(sem[0] == 0 and sem[1] > 0, f"the writes in the DSP service's head: the semaphore never taken ({sem[0]}), marked directly ({sem[1]} times)")
        sem[:] = [0, 0]; nv = M.NV
        frames(3); x = X.frame(e)
        check(e.r8(nv + 5) == 0, "out of the service's writes the flag is down")
    for _ in range(127 - 32): e.knob(0, -1)
    check(st(M.O_K) == 32, f"K1 = 32 ({st(M.O_K)})")
    frames(14)
    lv = live()
    def mid(a, b): return a + (((b - a) * 64) >> 7)
    if NOCUR:                                                                  # (SC55.1 use_nocur) the chain = patches 4, 5: K1 32 = a quarter of the way
        q = lambda a, b: a + (((b - a) * 32) >> 7)
        bad = [(k, off, lv[off - 30], P4[off], P5[off]) for k, off, cont, lo, hi in RW if cont and lv[off - 30] != q(P4[off], P5[off])]
        check(not bad, f"no present sound in the chain: K1 32 = a quarter from patch 4 to patch 5 ({len(bad)} rows differ: {bad[:4]})")
    else:
        bad = [(k, off, lv[off - 30], p0[off - 30], P4[off]) for k, off, cont, lo, hi in RW if cont and lv[off - 30] != mid(p0[off - 30], P4[off])]
        check(not bad, f"K1 a quarter: halfway between the present sound and patch 4 ({len(bad)} rows differ: {bad[:4]})")
    for _ in range(10): e.knob(1, 1)
    k2 = struct.unpack("b", bytes([st(M.O_K + 1)]))[0]
    clr = e.r32(e.r32(MGR + 0x20) + 0xC); e.set_p0(clr, 1); e.knob(1, 1); e.set_p0(clr, 0)
    check(k2 == 10 and st(M.O_K + 1) == 0, f"K2 = 10, Clear + K2 = 0 ({k2}, {st(M.O_K + 1)})")
    for _ in range(40): e.knob(2, 1)                                            # K3 = LFO 1's rate
    frames(1); ph = lambda: e.r32(M.MZ + M.O_PH1) & 0xFFFF
    a0 = ph(); at(10); X.frame(e); svc(); a1 = ph(); at(20); X.frame(e); svc(); a2 = ph()
    d10, d20 = (a1 - a0) & 0xFFFF, (a2 - a1) & 0xFFFF
    check(d10 > 0 and abs(d20 - 2 * d10) <= 2, f"LFO 1 follows the elapsed time: 10 ms = {d10}, 20 ms = {d20}")
    pad(0); f = frames(1)
    check(f[0] == pal(1) and f[7] == pal(1) and e.r32(M.MZ + M.O_ENV) & 0xFFFF > 0, f"pad 1: the envelope runs, pads 1 / 8 bright ({f[0]:#x})")
    if SUS:                                                                    # (SC55.1 use_sus) pad 1 held = the envelope sustains
        hold(0); frames(20); e1 = e.r32(M.MZ + M.O_ENV) & 0xFFFF
        let(0); frames(5); e2 = e.r32(M.MZ + M.O_ENV) & 0xFFFF
        check(e1 == 0xFFFF and e2 < 0xFFFF, f"pad 1 held: the envelope stays at the top ({e1:#x}), let go: it falls ({e2:#x})")
    if NOCUR:
        e.btn(M.ID_UP); o = bytes(e.uc.mem_read(M.MZ + M.O_ORD, 3)); f = frames(1)
        check(o == bytes([1, 2, 3]) and src(), f"Octave up: nothing (no initial patch in the chain; {o.hex()})")
    else:
        e.btn(M.ID_UP); o = bytes(e.uc.mem_read(M.MZ + M.O_ORD, 3)); f = frames(1)
        check(o == bytes([1, 0, 2]) and f[52] == pal(1) and f[51] == pal(1), f"Octave up: the initial patch one place later ({o.hex()}; Octave {f[51]:#x} / {f[52]:#x})")
        e.btn(M.ID_UP); e.btn(M.ID_UP); o = bytes(e.uc.mem_read(M.MZ + M.O_ORD, 3)); f = frames(1)
        check(o == bytes([1, 2, 0]) and f[52] == 0, f"Octave up at the end: nothing more, Octave up dark ({o.hex()}, {f[52]:#x})")
    e.btn(M.DUP); check(st(M.O_ACT) == 0 and src(), "Duplicate: nothing, the morph view stays")
    e.btn(8); f = frames(1)
    check(not src() and f[4] == M.WHITE and f[5] == M.WHITE and f[31] != M.RED, f"Preset: the patches, 4 / 5 white ({f[4]:#x}, {f[5]:#x}, pad 32 {f[31]:#x})")
    e.btn(8); f = frames(1)
    check(src() and f[31] == M.RED, f"Preset again: the morph view ({src()}, pad 32 {f[31]:#x})")
    if "--clear" in sys.argv:                                                  # the user, 2026-11-08: Clear stays in the view; Clear + the track = the knobs to 0
        CLEAR, BDOWN, BUP = 23, 0x08033320, 0x0803381A
        e.call(BDOWN, MGR, CLEAR, maxins=8_000_000); e.call(BUP, MGR, CLEAR, maxins=8_000_000); f = frames(1)
        check(src() and f[31] == M.RED and st(M.O_ACT) == 0, f"Clear alone: the morph view stays ({src()}, pad 32 {f[31]:#x})")
        for _ in range(5): e.knob(1, 1)
        e.call(BDOWN, MGR, CLEAR, maxins=8_000_000); e.knob(1, 1); e.call(BUP, MGR, CLEAR, maxins=8_000_000); f = frames(1)
        check(src() and st(M.O_K + 1) == 0, f"pressed Clear + K2 = 0, the view stays ({st(M.O_K + 1)}, {src()})")
        for k in range(8): e.knob(k, 3)
        e.call(BDOWN, MGR, CLEAR, maxins=8_000_000); e.btn(0); e.call(BUP, MGR, CLEAR, maxins=8_000_000); f = frames(1)
        ks = bytes(e.uc.mem_read(M.MZ + M.O_K, 8))
        check(src() and ks == bytes(8) and st(M.O_ACT) == 0, f"Clear + Synth 1: every knob 0 / centre, the morph view stays ({ks.hex()}, {src()})")
    e.btn(14); frames(1)
    check(not src() and st(M.O_ACT) == 0, f"Mixer: the morph goes on ({st(M.O_ACT)})")
    e.btn(0); f = frames(1)
    check(src() and f[31] == M.RED and f[0] in (pal(9), pal(1)), f"Synth 1's button from the Mixer: the morph view ({src()}, pad 32 {f[31]:#x})")
    e.btn(0); frames(1)
    check(not src() and st(M.O_ACT) == 0 and e.r8(MGR + 0x152) == 1, f"Synth 1's button in the morph view: the stock (the Note view, {e.r8(MGR + 0x152)})")
    e.btn(0); f = frames(1)
    check(src() and f[31] == M.RED, f"Synth 1's button again: the morph view ({src()})")
    e.btn(0); frames(1)
    e.set_p0(clr, 1); e.btn(0); e.set_p0(clr, 0); frames(1)
    check(not src() and e.r8(MGR + 0x152) == 1, f"Clear + Synth 1 in the Note view: no morph view ({src()}, {e.r8(MGR + 0x152)})")
    e.btn(0); frames(1)
    e.btn(8); frames(1)
    hold(6); frames(1); at(450); frames(2)
    check(st(M.O_N) == 3 and st(M.O_HP) != 3, f"patch 6 alone held 0.4 s: the chain stays (n {st(M.O_N)}, hp {st(M.O_HP)})")
    hold(7); frames(2)
    check(st(M.O_HP) != 3, f"patch 7 pressed after a long hold of 6: the 0.4 s counted from 7 ({st(M.O_HP)})")
    at(450); frames(2)
    check(st(M.O_N) == 3 and bytes(e.uc.mem_read(M.MZ + M.O_SL, 2)) == b"\x06\x07" and st(M.O_HP) == 3,
          f"patches 6 + 7 held 0.4 s: the chain = the initial patch + 6, 7 (n {st(M.O_N)}, {bytes(e.uc.mem_read(M.MZ + M.O_SL, 2)).hex()})")
    let(6); let(7); frames(1)
    check(st(M.O_ACT) == 0, f"their release: still on ({st(M.O_ACT)})")
    e.set_p0(clr, 1); hold(4); let(4); e.set_p0(clr, 0); frames(1)
    check(st(M.O_ACT) == 0, f"Clear + a patch in the patches: the stock's gesture, the morph stays ({st(M.O_ACT)})")
    sl0 = bytes(e.uc.mem_read(M.MZ + M.O_SL, 3))
    hold(4); frames(1); e.set_p0(clr, 1); hold(5); at(450); frames(2); e.set_p0(clr, 0); let(5); let(4); frames(1)
    check(bytes(e.uc.mem_read(M.MZ + M.O_SL, 3)) == sl0 and st(M.O_ACT) == 0, f"patch 4 held, then Clear + 5: no new chain ({bytes(e.uc.mem_read(M.MZ + M.O_SL, 3)).hex()})")
    e.btn(8); f = frames(1)
    check(src() and f[31] == M.RED, "Preset: the morph view")
    pad(31); f = frames(2)
    diff = [q for q in range(32) if f[q] != f_stock[q]]
    check(st(M.O_ACT) == 0xFF and not src() and f[31] != M.RED and set(diff) <= {4, 5, 6, 7},
          f"pad 32: the morph out, back to the patches as the stock draws them (pad 32 {f[31]:#x}; differ at {diff})")
    hold(4); frames(1); at(450); frames(2)
    check(st(M.O_ACT) == 0xFF, f"one patch alone held 0.4 s: no morph ({st(M.O_ACT):#x})")
    let(4); frames(1)
    hold(4); hold(5); e.btn(24); let(4); let(5)
    check(st(M.O_ACT) == 0 and src(), "patches held + Duplicate: on again, the morph view")
    pad(31); frames(1)
    e.btn(14); e.btn(0); e.btn(8); e.btn(8); frames(1)
    check(src() and st(M.O_ACT) == 0xFF, f"the morph out: Preset twice = Synth 1's alternative view ({src()})")
    e.btn(8); frames(1)
    check(not src() and e.r8(MGR + 0x152) == 0, "Preset in the alternative view: the patches")
    hold(4); hold(5); frames(1); at(450); frames(2); let(4); let(5)
    check(st(M.O_ACT) == 0, "on again by holding")
    import split4 as S4
    on4 = lambda: e.r8(S4.SPR + S4.O_ON) if e.r32(S4.SPR) == S4.SIG else 0
    bp = lambda i: (drain(), e.call(0x08033320, MGR, i, maxins=20_000_000))
    br = lambda i: (drain(), e.call(0x0803381A, MGR, i, maxins=20_000_000))
    bp(1); br(1); bp(1); bp(0); s4 = (on4(), e.r8(MGR + 0x152)); br(0); br(1); frames(1)
    check(s4[0] == 1 and st(M.O_ACT) == 0, f"Synth 2 held + the morphed Synth 1: the split keyboard as always (split {s4[0]}, view {s4[1]}), the morph goes on")
    e.btn(0); frames(1); s1 = (on4(), e.r8(MGR + 0x152))
    e.btn(0); f = frames(1)
    check(s1 == (0, 1) and src() and f[31] == M.RED, f"Synth 1 alone: split4 ends the split (its Note view, {s1}); again: the morph view ({src()})")
    e.w32(M.MZ + M.O_T, t[0] + 100000); frames(1)
    check(st(M.O_ACT) == 0xFF, f"a reset (the clock behind the last frame): the morph off ({st(M.O_ACT):#x})")
    e.btn(14); frames(1)
    # ---- MIDI 1: the own synth on; the LED task's stack
    import emu_sc22_4 as T4
    from unicorn.arm_const import UC_ARM_REG_SP
    V = T4.V
    e.btn(2); e.btn(8)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 1])); frames(2)
    def depth():
        lo = [1 << 32]
        def hk(uc, a, s_, d):
            sp = uc.reg_read(UC_ARM_REG_SP)
            if sp < lo[0]: lo[0] = sp
        h_ = e.uc.hook_add(UC_HOOK_CODE, hk); frames(1); e.uc.hook_del(h_)
        return 0x2006F000 - lo[0]
    d_off = depth()
    hold(8); hold(9); frames(1); at(450); f = frames(2); let(8); let(9)
    check(st(M.O_ACT) == 2 and st(M.O_SHOW) == 1 and f[31] == M.RED, f"MIDI 1: slots 1 + 2 held 0.4 s = the morph view (act {st(M.O_ACT)}, pad 32 {f[31]:#x}, pad 1 {f[0]:#x})")
    d_on = depth()
    check(d_on <= d_off, f"the LED task's stack in the MIDI 1 morph view: {d_on} B (morph off {d_off} B)")
    e.btn(8); f = frames(1)
    check(st(M.O_SHOW) == 0 and f[31] != M.RED, f"Preset: the slots ({f[31]:#x})")
    fl0 = e.r8(V.TAIL + V.O_FLAGS)
    e.set_p0(clr, 1); pad(29); e.set_p0(clr, 0); f = frames(1)
    check(e.r8(V.TAIL + V.O_FLAGS) == fl0 and st(M.O_ACT) == 2, f"Clear + pad 30 in the slots during the morph: swallowed (flags {fl0:#x} -> {e.r8(V.TAIL + V.O_FLAGS):#x})")
    e.btn(8); f = frames(1)
    check(st(M.O_SHOW) == 1 and f[31] == M.RED, "Preset again: the morph view")
    sh = e.r32(MGR + 0xC); e.set_p0(sh, 1); e.btn(2); e.set_p0(sh, 0); f = frames(1)
    check(st(M.O_SHOW) == 1 and f[31] == M.RED and e.r8(MGR + 0x152) == 18, f"Shift + MIDI 1 in the morph view (dblpress: the track twice): the morph view ({e.r8(MGR + 0x152)}, {st(M.O_SHOW)})")
    e.btn(14)
    import os
    if os.environ.get("MZDBG"):
        print("dbg mixer", e.r8(MGR + 0x152), st(M.O_SHOW), st(M.O_ACT), hex(e.r32(MGR + 0x6C)))
        ev = []
        for nm in ("c_mzbtn", "c_mztap", "c_mzshow", "c_mzmv"):
            e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, dd, nm=nm: ev.append((nm, uc.reg_read(UC_ARM_REG_R0) & 0xFF, e.r8(MGR + 0x152))), begin=L[nm], end=L[nm])
        from unicorn import UC_HOOK_MEM_WRITE
        e.uc.hook_add(UC_HOOK_MEM_WRITE, lambda uc, acc, a_, sz, v, dd: ev.append(("W_SHOW", v, hex(uc.reg_read(UC_ARM_REG_PC)), hex(uc.reg_read(UC_ARM_REG_LR)), e.r8(MGR + 0x152))),
                      begin=M.MZ + M.O_SHOW, end=M.MZ + M.O_SHOW)
        for nm in ("c_mpon",):
            ad = int(R["mpatch"]["labels"][nm], 16)
            e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, dd: ev.append(("mpon", hex(uc.reg_read(UC_ARM_REG_LR)), e.r8(MGR + 0x152))), begin=ad, end=ad)
    e.btn(2)
    if os.environ.get("MZDBG"): print("dbg", ev, "pc", hex(e.uc.reg_read(UC_ARM_REG_PC)), e.r8(MGR + 0x152), st(M.O_SHOW), st(M.O_ACT))
    f = frames(1)
    check(st(M.O_SHOW) == 1 and f[31] == M.RED, f"MIDI 1's button from the Mixer: the morph view (pad 32 {f[31]:#x})")
    pad(31); f = frames(1)
    check(st(M.O_ACT) == 0xFF and f[31] != M.RED, f"pad 32: out, the slots as the stock draws them ({f[31]:#x})")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} MORPH RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    img = Path(sys.argv[1]).read_bytes()
    man = json.loads(Path(sys.argv[2]).read_text())
    sys.exit(1 if main(img, man) else 0)
