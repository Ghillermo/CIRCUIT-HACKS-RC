"""SC43.4 ARM tests, through the controller, the real LED task and the stock DSP group handlers:
  * the step-drummer (sdpv.use_v4): MIDI 1 with FM as the destination: an empty pair = 64 (dim), +5 = 69 at brightness 2 + 10;
  * the side-chain from patterns (scpat): Sidechain view, pad 1 = Synth 1 as the source of Synth 1's side-chain (the block in the tail); the group
    writes X:$3F2 = $3BF2 - $99 (the DSP then reads the trigger word X:$3BF2); a Synth 1 pattern note (the players' note-on) writes X:$3BF2 = $F, a
    MIDI 1 note nothing (nobody listens); LEDs: pad 1 in Synth 1's colour, pads 2-8 dim; pad 6 (Drum 2) = back to the stock (X:$3F2 = 1);
  * the next-bar mute (qmute): Mixer, Shift + pad 1, stopped = Synth 1 muted at once; playing at tick 90 Shift + pad 2 = pending (pad 2 blinks), at
    tick 94 still pending, at tick 95 (the next bar, one tick early) Synth 2 muted; Shift + pad 3 twice = cancelled; Shift + pad 11 still the scene repeats
    (patchain);
  * Clear + K8 (persist19.use_clrbc): the bitcrush (left of the knob's 0) back to 0;
  * Clear + Drum 1 (clrtrk) on Drum 1's view: its decay, pitch and ring frequency back to their defaults.

    python tools/emu_sc43_4.py SC43.4.bin SC43.4_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_SP, UC_ARM_REG_R4
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import scpat as SP  # noqa: E402
import qmute as QM  # noqa: E402

MGR = T.MGR
GROUPS, DSP_W = 0x0805B3B0, 0x080292F8
PLAYER0, PLAYER_SZ = 0x20040200, 0x184


def lab(man, m, k): return int(man["report"][m]["labels"][k], 16)


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    # ---- the step-drummer, every destination bipolar
    e = X.EP(img, man)
    e.btn(2); e.btn(8)
    for _ in range(2): e.pad(26)
    e.pad(29); e.pad(19)                                                              # its view, pad 20 = FM
    h0 = e.r0(e.vl["c_sdhalf"], 0); f = X.frame(e)
    base = e.r0(e.vl["c_sdbase"], 0); b0 = f[61] >> 8
    e.knob(1, 5); f = X.frame(e)
    check(base == 64 and b0 == 2 and e.lane(0, h0 + 2, 0) == 69 and f[61] >> 8 == 12, f"step-drummer, FM: empty = 64 dim ({base}, {b0}), +5 = 69 at 12 ({e.lane(0, h0 + 2, 0)}, {f[61] >> 8})")
    del e; gc.collect()

    # ---- the side-chain from patterns
    e = T.EL(img); e.at(300000); e.transport(0)
    dsp = []
    def w(uc, a, s, d): dsp.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1) >> 8, uc.reg_read(UC_ARM_REG_R2)))
    e.uc.hook_add(UC_HOOK_CODE, w, begin=DSP_W, end=DSP_W)
    def rest(uc, a, s, d):                                                            # the rest of the note-on: pop {r4-r8, pc} (the sound path waits for the DSP)
        sp = uc.reg_read(UC_ARM_REG_SP); ws = struct.unpack("<6I", bytes(uc.mem_read(sp, 24)))
        for i, r in enumerate((UC_ARM_REG_R4, 0, 0, 0, 0)):
            pass
        from unicorn.arm_const import UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8
        for r, v in zip((UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8), ws[:5]): uc.reg_write(r, v)
        uc.reg_write(UC_ARM_REG_SP, sp + 24); uc.reg_write(UC_ARM_REG_PC, ws[5])
    e.uc.hook_add(UC_HOOK_CODE, rest, begin=0x08040FA6, end=0x08040FA6)
    e.set_p0(e.r32(MGR + 0xC), 1); e.btn(15); e.set_p0(e.r32(MGR + 0xC), 0)
    e.pad(0); f = X.frame(e)
    src = e.r0(lab(man, "scpat", "c_spget"), 0) if hasattr(e, "r0") else None
    e.call(lab(man, "scpat", "c_spget"), 0); src = e.uc.reg_read(UC_ARM_REG_R0)
    tail = e.r32(SP.SESSION_OBJ + 0x14) + SP.TAIL
    blk = bytes(e.uc.mem_read(tail + SP.O_BLK, 4))
    g5 = struct.unpack("<I", img[GROUPS - 0x08010000 + 20:][:4])[0] & ~1
    dsp.clear(); e.call(g5, maxins=3_000_000); srcw = [x for x in dsp if x[2] == 0x3F2]
    check(src == 1 and blk[0] == SP.MAGIC and srcw == [(0, SP.TRIG - SP.FLAGS, 0x3F2)], f"pad 1: Synth 1 as Synth 1's source ({src}, block {blk.hex()}); the group writes X:$3F2 = {srcw}")
    check(f[0] == SP.COL[0] and all(x == SP.DIM for x in f[1:8]), f"LEDs: pad 1 in Synth 1's colour, pads 2-8 dim ({[hex(x) for x in f[:8]]})")
    dsp.clear(); e.call(0x08040FA2, PLAYER0, 60, 100, 6, maxins=3_000_000); n1 = list(dsp)
    dsp.clear(); e.call(0x08040FA2, PLAYER0 + 2 * PLAYER_SZ, 60, 100, 6, maxins=3_000_000); n2 = list(dsp)
    check(n1 == [(0, 0xF, SP.TRIG)] and n2 == [], f"a Synth 1 pattern note writes X:$3BF2 = $F ({n1}); a MIDI 1 note nothing ({n2})")
    e.pad(5); e.call(lab(man, "scpat", "c_spget"), 0); src2 = e.uc.reg_read(UC_ARM_REG_R0)
    dsp.clear(); e.call(g5, maxins=3_000_000); srcw2 = [x for x in dsp if x[2] == 0x3F2]
    check(src2 == 0 and srcw2 == [(0, 1, 0x3F2)], f"pad 6 (Drum 2): back to the stock ({src2}, X:$3F2 = {srcw2})")
    del e; gc.collect()

    # ---- the next-bar mute
    e = T.EL(img); e.at(300000); e.transport(0)
    view = QM.MIX_VIEW
    def muted(k):
        st = e.r32(e.r32(view + 0x68) + e.r32(view + 0x60) * k); e.call(0x0803542C, st, 0); return e.r8(e.uc.reg_read(UC_ARM_REG_R0))
    def shpad(q): e.set_p0(e.r32(MGR + 0xC), 1); e.pad(q); e.set_p0(e.r32(MGR + 0xC), 0)
    tail = e.r32(SP.SESSION_OBJ + 0x14) + SP.TAIL
    e.btn(14); X.frame(e)
    m0 = muted(0); shpad(0); X.frame(e)
    check(muted(0) != m0 and e.r8(tail + QM.O_PEND) == 0, f"stopped: Shift + pad 1 = Synth 1's mute toggled at once ({m0} -> {muted(0)})")
    st = e.r32(QM.ENG + 0x90)
    def tick(v):
        for fn in (0x080354FA, 0x0803542C):
            e.call(fn, st, 0); e.w32(e.uc.reg_read(UC_ARM_REG_R0), v)
    def setp(store, k, v):
        for fn in (0x080354FA, 0x0803542C):
            e.call(fn, store, k); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes([v]))
    setp(QM.TRANSPORT, 0, 1); tick(80); X.frame(e)
    m1 = muted(1); shpad(1); tick(90); e.w32(QM.HAL_TICK, 0x100); f = X.frame(e)
    pend, blink = e.r8(tail + QM.O_PEND), f[1]
    tick(94); X.frame(e); p94 = (muted(1), e.r8(tail + QM.O_PEND))
    tick(95); X.frame(e); p95 = (muted(1), e.r8(tail + QM.O_PEND))
    check(pend == 2 and blink == 0 and p94 == (m1, 2) and p95[0] != m1 and p95[1] == 0,
          f"playing: Shift + pad 2 at tick 90 = pending (pad 2 dark on the blink: {blink:#x}), tick 94 still ({p94}), tick 95 = muted ({p95})")
    m2 = muted(2); shpad(2); shpad(2); tick(200); X.frame(e)
    check(muted(2) == m2 and e.r8(tail + QM.O_PEND) == 0, "Shift + pad 3 twice = cancelled")
    rep0 = bytes(e.uc.mem_read(tail + 24, 16)); m9 = [muted(k) for k in range(8)]; shpad(10); rep1 = bytes(e.uc.mem_read(tail + 24, 16))
    check(rep1 != rep0 and [muted(k) for k in range(8)] == m9 and e.r8(tail + QM.O_PEND) == 0, f"Shift + pad 11: still patchain's scene repeats ({rep0.hex()} -> {rep1.hex()}), no mute")
    del e; gc.collect()

    # ---- Clear + K8, Clear + Drum 1
    e = T.EL(img); e.at(300000); e.transport(0)
    mh = lab(man, "sc18", "c_mh"); dget = lab(man, "persist19", "c_dget"); xget = lab(man, "persist19", "c_dext_get")
    r0 = lambda fn, *a: (e.call(fn, *a, maxins=3_000_000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    h = r0(mh, 0)
    def stockv(s): return e.r8(r0(0x0803542C, e.r32(h + 0xC), s >> 1))
    knob = lambda k, d: e.call(0x08033848, MGR, k, d & 0xFFFFFFFF, maxins=8_000_000)
    e.btn(4)
    knob(7, -20); bc0 = (r0(xget, 0) >> 4) & 15
    e.call(0x08033320, MGR, 23, maxins=8_000_000)                                     # Clear held
    knob(7, 1); bc1 = (r0(xget, 0) >> 4) & 15
    check(bc0 > 0 and bc1 == 0, f"Clear + K8 right: the bitcrush back to 0 ({bc0} -> {bc1})")
    e.call(0x0803381A, MGR, 23, maxins=8_000_000)
    knob(2, -30); knob(0, 20); knob(1, 15)
    before = (stockv(3), stockv(1), r0(dget, 0, 2))
    e.call(0x08033320, MGR, 23, maxins=8_000_000); e.call(0x08033320, MGR, 4, maxins=60_000_000); e.call(0x0803381A, MGR, 23, maxins=8_000_000)
    after = (stockv(3), stockv(1), r0(dget, 0, 2))
    check(before[0] != 127 and before[1] != 64 and after[:2] == (127, 64) and after[2] != before[2],
          f"Clear + Drum 1: decay, pitch and ring frequency back to their defaults ({before} -> {after})")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
