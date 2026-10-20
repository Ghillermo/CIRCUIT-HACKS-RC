"""SC44.8 ARM test (lfosync.py): the synced LFO of the own engine from the DSP service chain's new head.

    python tools/emu_lfosync.py NEW.bin NEW_manifest.json
  * the head of the DSP service chain -> c_lfhead (in the dead DSP block of the stock image: hole.py), which ends in the previous head;
  * LRATE (code 11) of MIDI 1 = -37 (division 9 = 1 bar), 120 BPM, tick 100: the DSP gets the increment 120 x KQ[9] >> 8 at OS2B0 + 40 and the
    phase $800000 + (100 mod 96) x 2^24 / 96 at VB0 + PH; the same tick again: nothing; tick 101: only the phase; 90 BPM: only the increment;
  * every division: -1 .. -4 = 1/16T (4 ticks), -61 .. -64 = 8 bars (768); MIDI 2 (track 1): its own words (+ 48);
  * LRATE >= 0: nothing written;
  * the drums: Shift + K7 (the project byte) -37 = the same increment / phase in the drum block's LINC / PH; +20 nothing;
  * Master FX's Auto-Filter / Phaser K1: free = PHPER[2 (v - 64)] with the effect's start time; synced = a beat x d / 24 and the start time
    now - (tick mod d) x period / d, set again on a new tick or a new division only;
  * the matrix's LFO 2: c_mxsync's advance (BPM x 2^16 x 24 / (60000 d) a ms) and the phase set on a new tick only.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc17_5 import EA  # noqa: E402
import lfosync as LF  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
import build_sc14 as S14  # noqa: E402
import mpatch as MP  # noqa: E402

BASE = 0x08010000


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["lfosync"]["labels"].items()}
    V = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
    check(MP.bw_target(img, S14.SVC_HOOK, BASE) == L["c_lfhead"], f"the DSP service chain's head -> c_lfhead at {L['c_lfhead']:#x}")
    check(0x080101F0 <= L["c_lfhead"] < 0x0801865A, "c_lfhead lives in the dead DSP block of the stock image")
    e = EA(img)
    def ptr(fn, st, i):
        e.call(fn, st, i, maxins=200000); return e.uc.reg_read(UC_ARM_REG_R0)
    def set_bpm(b): e.uc.mem_write(ptr(LF.PARAM_GET, LF.TEMPO, 0), bytes([b]))
    def set_tick(t): e.uc.mem_write(ptr(LF.PARAM_GET, e.r32(LF.ENG + 0x90), 0), struct.pack("<I", t))
    def set_rate(t, v):
        e.call(V["c_vvaddr"], t, 11, maxins=200000); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), struct.pack("b", v))
    def run(t):
        e.shi.writes.clear(); e.call(L["c_lfv"], t, maxins=2_000_000)
        return {a: v for c, sp, a, v in e.shi.writes if c == 0 and sp == 'x'}
    INC0, PH0 = VD.OS2B0 + VD.LFS_INC, VD.VB0 + VD.PH
    e.uc.mem_write(LF.RAM, bytes(48))
    set_bpm(120); set_tick(100); set_rate(0, -37)
    w = run(0)
    inc, ph = (120 * LF.KQ[9]) >> 8, (0x800000 + (100 % 96) * LF.PHQ[9]) & 0xFFFFFF
    check(w == {INC0: inc, PH0: ph}, f"-37, 120 BPM, tick 100: increment {inc:#x}, phase {ph:#x} ({ {hex(a): hex(v) for a, v in w.items()} })")
    check(run(0) == {}, "the same tick again: nothing written")
    set_tick(101); w = run(0)
    check(w == {PH0: (0x800000 + 5 * LF.PHQ[9]) & 0xFFFFFF}, f"tick 101: only the phase ({ {hex(a): hex(v) for a, v in w.items()} })")
    set_bpm(90); w = run(0)
    check(w == {INC0: (90 * LF.KQ[9]) >> 8}, f"90 BPM: only the increment ({ {hex(a): hex(v) for a, v in w.items()} })")
    bad = []
    for v, k in ((-1, 0), (-4, 0), (-5, 1), (-61, 15), (-64, 15)):
        set_rate(0, v); set_tick(1000 + 7 * k + abs(v)); w = run(0)
        t_ = 1000 + 7 * k + abs(v)
        if w.get(PH0) != (0x800000 + (t_ % LF.DIVS[k]) * LF.PHQ[k]) & 0xFFFFFF or w.get(INC0, (90 * LF.KQ[k]) >> 8) != (90 * LF.KQ[k]) >> 8: bad.append((v, k, w))
    check(not bad, f"divisions: -1 / -4 = 1/16T, -5 = 1/16, -61 / -64 = 8 bars {bad[:1]}")
    e.uc.mem_write(LF.RAM, bytes(48)); set_rate(1, -37); set_tick(200); w = run(1)
    check(set(w) == {INC0 + 48, PH0 + 48}, f"MIDI 2: its own words ({[hex(a) for a in w]})")
    set_rate(0, 0); set_tick(300); w0 = run(0); set_rate(0, 63); w1 = run(0)
    check(w0 == {} and w1 == {}, "LRATE 0 / 63 (free): nothing written")
    # ---- the drums (drums2_dsp.use_lfosync): Shift + K7 = the project byte XM[28 + 9 d + 3], c_lfd(d)
    import drums2_dsp as D2
    P = {k: int(v, 16) for k, v in man["report"]["persist19"]["labels"].items()}
    def set_drum(d, v):
        e.call(P["c_xp"], 28 + 9 * d + 3, maxins=200000); ad = e.uc.reg_read(UC_ARM_REG_R0)
        e.uc.mem_write(ad, bytes([e.r8(ad) & 0x80 | (v & 0x7F)])); return ad
    def runc(fn, d):
        e.shi.writes.clear(); e.call(L[fn], d, maxins=2_000_000)
        return {a_: v_ for c, sp, a_, v_ in e.shi.writes if c == 0 and sp == 'x'}
    e.uc.mem_write(LF.RAM, bytes(48)); set_bpm(120); set_tick(100)
    ad = set_drum(2, -37)
    w = runc("c_lfd", 2); DBd = D2.DB + 2 * D2.STRIDE
    check(ad != 0 and w == {DBd + D2.LINC: (120 * LF.KQ[9]) >> 8, DBd + D2.PH: (0x800000 + 4 * LF.PHQ[9]) & 0xFFFFFF},
          f"drum 3, Shift + K7 = -37: increment and phase in its block ({ {hex(a_): hex(v_) for a_, v_ in w.items()} })")
    set_drum(2, 20); w = runc("c_lfd", 2)
    check(w == {}, "drum 3, Shift + K7 = +20 (free): nothing written")

    # ---- the matrix's LFO 2 (modmx.use_sync): c_mxsync(track, division, dt, block)
    import modmx as MX
    M = {k: int(v, 16) for k, v in man["report"]["modmx"]["labels"].items()}
    blk = MX.MXR + MX.T0
    e.uc.mem_write(MX.SYNC_RAM, bytes(8)); set_bpm(120); set_tick(500)
    K2 = lambda i: round((1 << 16) * 24 * 4096 / (60000 * LF.DIVS[i]))
    e.call(M["c_mxsync"], 0, 9, 10, blk, maxins=2_000_000); adv = e.uc.reg_read(UC_ARM_REG_R0 + 1)
    ph = struct.unpack("<H", bytes(e.uc.mem_read(blk + MX.B_PH, 2)))[0]
    check(adv == (120 * K2(9) * 10) >> 12 and ph == ((500 % 96) << 16) // 96,
          f"matrix LFO 2, 1 bar at 120 BPM, 10 ms: advance {adv} (~{65536 * 10 // 2000}), tick 500: phase {ph:#x} = (500 mod 96) / 96")
    e.uc.mem_write(blk + MX.B_PH, struct.pack("<H", 0x1234))
    e.call(M["c_mxsync"], 0, 9, 10, blk, maxins=2_000_000)
    check(struct.unpack("<H", bytes(e.uc.mem_read(blk + MX.B_PH, 2)))[0] == 0x1234, "the same tick: the phase is left alone (it runs on by the advance)")
    # ---- Master FX (build_sc17.use_lfosync): c_lfper(K1, the start time, the slot) -> the period, the start time for c_tri
    import build_sc17 as S17
    G = {k: int(v, 16) for k, v in man["report"]["sc17"]["labels"].items()}
    slot = LF.RAM + 48
    def lfper(v, t0):
        e.call(G["c_lfper"], v, t0, slot, maxins=2_000_000)
        return e.uc.reg_read(UC_ARM_REG_R0), e.uc.reg_read(UC_ARM_REG_R0 + 1)
    phper = S17.tables()["PHPER"]
    check(lfper(100, 1234) == (phper[72], 1234), f"K1 100 (free): the period PHPER[72] = {phper[72]} ms, the effect's own start time")
    e.uc.mem_write(slot, bytes(12)); set_bpm(120); set_tick(150); e.w32(0x2000081C, 50000)
    per, t0 = lfper(26, 1234)
    check(per == 2000 and t0 == 50000 - 54 * 2000 // 96, f"K1 26 (1 bar) at 120 BPM, tick 150: period {per} ms, start {t0} (= now - (150 mod 96) x 2000 / 96)")
    e.w32(0x2000081C, 50300); per2, t02 = lfper(26, 1234)
    check((per2, t02) == (per, t0), "300 ms later, the same tick: the same start time (the phase runs on)")
    per3, t03 = lfper(22, 1234)
    check(per3 == 128 * 500 // 24 and t03 != t0, f"K1 22 (2 bars T = 128 ticks): period {per3} ms, the start time set again for the new division")

    del e; gc.collect()
    print("SC44.8 lfosync RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())) else 0)
