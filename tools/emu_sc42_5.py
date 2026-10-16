"""SC42.5 ARM tests (the fixes after the device, 2026-10-16), through the controller and the real LED task with the clock moving:
  * the arpeggiator: a chord recorded by holding (every note 36 micro steps long) at 1/16: each note one step (6 ticks), not to the chord's end;
    at 1/32: 3 ticks;
  * Gate once (the Gate view): pads 31 / 32 are the stock's (no toggle, the stock's LEDs); Gate twice (Micro Step): pad 31 = the selector, which
    survives the LED task while the view is drawn and closes 200 ms after another view; a length chosen there;
  * the rollers: held through several LED-task frames (the clock moving) they stay; on Drum 2 too; another view clears them after 200 ms; with Record
    armed a roller's hit is written into the pattern (velocity 100 on an empty step, the micro step's bit);
  * Preset again in Drum 1's Preset view: the chromatic view on (the flag), again off; Preset in a synth's Preset view: as before.

    python tools/emu_sc42_5.py SC42.5.bin SC42.5_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R4, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
from emu_arp import EA, chord_steps, PLAYER  # noqa: E402
import arp as A  # noqa: E402
import rollers as R  # noqa: E402
import stepgate as SG  # noqa: E402
import build_sc08 as S8  # noqa: E402
import drumnote as DN  # noqa: E402
DN.MIRROR = True                                  # as the builds since SC23.4 (the rollers' tables follow it)

MGR = T.MGR


def frame(e):
    e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR)
    e.call(0x08033B3E, maxins=40_000_000)
    return list(struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138))))


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1

    # ---- the arpeggiator: a note at most an arpeggio step
    def seq(setting, units, steps):
        e = EA(img, man)
        p = e.playing(0); base = e.settings(0, p) - 0x380
        e.uc.mem_write(base, chord_steps(units)); e.setpat(0, p, 0, 7)
        e.setp(e.r32(PLAYER + 0x10), 1, bytes([3]))
        e.call(e.A["c_arset"], 0, p, setting)
        e.transport(1); e.ons.clear(); e.run(p, steps)
        out = list(e.ons); del e; gc.collect(); return out
    held = [(64, 36, 0, 100), (60, 36, 0, 90), (67, 36, 0, 80)]
    s16 = seq(0x80 | A.M_UP, held, 7)
    check([t for t, *_ in s16] == list(range(0, 36, 6)) and all(d == 6 for *_, d in s16), f"a chord held 6 steps at 1/16: a note a step, each a step long ({s16[:4]}…)")
    s32 = seq(0x80 | 2 << 3 | A.M_UP, held, 7)
    check(all(d == 3 for *_, d in s32) and [t for t, *_ in s32][:4] == [0, 3, 6, 9], f"at 1/32: 3 ticks long ({s32[:4]}…)")
    short = [(64, 2, 0, 100), (60, 2, 0, 90), (67, 2, 0, 80), (72, 18, 0, 70)]
    ss = seq(0x80 | A.M_UP, short, 4)
    check([d for *_, d in ss][:3] == [2, 2, 2], f"notes entered short: their own (shorter) gate ({ss})")

    # ---- the Gate view vs the Micro Step view
    e = T.EL(img); t = [300000]; e.at(t[0]); e.transport(0)
    def tick(ms):
        t[0] += ms; e.at(t[0]); return frame(e)
    tail = e.r32(T.LZ.SESSION_OBJ + 0x14) + 0x27024
    e.btn(0); e.btn(11)
    f = tick(10)
    check(e.r8(MGR + 0x152) == 3 and f[30] not in (SG.COL_FIX, SG.COL_ON) or f[30] == f[29], f"Gate once: pads 31 / 32 the stock's ({f[30]:#x}, {f[31]:#x})")
    st = e.r8(tail + SG.O_FL + 6); e.call(T.PRESS, MGR, 30, 100, maxins=8_000_000); e.call(T.RELEASE, MGR, 30, maxins=8_000_000)
    check(e.r8(tail + SG.O_FL + 6) == st and e.r8(tail + SG.O_FL + 2) & 0x80 == 0, "Gate once, pad 31: no fixed length, no selector")
    e.btn(11)
    f = tick(10)
    check(e.r8(MGR + 0x152) == 8 and f[30] == SG.COL_OFF and f[31] == SG.COL_OFF, f"Gate twice (Micro Step): pads 31 / 32 dim ({f[30]:#x}, {f[31]:#x})")
    e.call(T.PRESS, MGR, 30, 100, maxins=8_000_000); e.call(T.RELEASE, MGR, 30, maxins=8_000_000)
    for _ in range(5): f = tick(60)
    check(e.r8(tail + SG.O_FL + 6) == 1 and f[16] == SG.COL_ON and f[17] == SG.COL_OFF, "pad 31: the selector, still open after 300 ms of LED task")
    e.call(T.PRESS, MGR, 21, 100, maxins=8_000_000); e.call(T.RELEASE, MGR, 21, maxins=8_000_000)
    f = tick(10)
    check(e.r8(tail + SG.O_FL + 2) == 0x86 and e.r8(tail + SG.O_FL + 6) == 0 and f[30] == SG.COL_FIX, f"pad 22: 6 steps, the selector closed ({e.r8(tail + SG.O_FL + 2):#x})")
    e.call(T.PRESS, MGR, 30, 100, maxins=8_000_000); e.call(T.RELEASE, MGR, 30, maxins=8_000_000)
    tick(10); e.btn(9); tick(100); o1 = e.r8(tail + SG.O_FL + 6); tick(150)
    check(o1 == 1 and e.r8(tail + SG.O_FL + 6) == 0, "the selector open, another view: closed after 200 ms")

    # ---- the rollers
    m_addr = tail + R.O_MASK
    def expanded(d):
        e.btn(4 + d)
        for _ in range(3):
            if e.r8(MGR + 0x152) == 42 + 8 * d: break
            e.btn(9)
    for d in (0, 1):
        expanded(d); tick(10)
        sub = e.r8(MGR + 0x152)
        pad = [p for p in range(24) if R.tables()[0][p] == d and R.tables()[1][p] == 0][0]
        e.call(T.PRESS, MGR, pad, 100, maxins=8_000_000)
        for _ in range(6): tick(50)
        kept = e.r8(m_addr + d)
        e.call(T.RELEASE, MGR, pad, maxins=8_000_000)
        check(kept == 1, f"Drum {d + 1} (subview {sub}): a roller held through 300 ms of LED task stays ({kept:#x})")
    e.call(T.PRESS, MGR, [p for p in range(24) if R.tables()[0][p] == 0 and R.tables()[1][p] == 2][0], 100, maxins=8_000_000)
    e.btn(0); tick(250)
    check(e.r32(m_addr) == 0, "another view: the rollers cleared (the stock lets go of the held pads; the 200 ms stamp as well)")
    # Record armed: written into the pattern
    expanded(0); tick(10)
    e.call(T.PRESS, MGR, [p for p in range(24) if R.tables()[0][p] == 0 and R.tables()[1][p] == 3][0], 100, maxins=8_000_000)
    DP = R.DP0; slot2 = e.r32(R.DP_VT + 8) & ~1
    iface = e.r32(DP + 0x4C); ivt = e.r32(iface)
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    for fn in (e.r32(ivt) & ~1, e.r32(ivt + 4) & ~1): e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: skip(uc), begin=fn, end=fn)
    base = e.r32(DP + 0x48); step = 9
    e.uc.mem_write(base + step, bytes([0])); e.uc.mem_write(base + 0x20 + step, bytes([7])); e.uc.mem_write(base + 0x60 + step, bytes([0]))
    for k in (0, 1):
        for fn in (0x080354FA, 0x0803542C):
            e.call(fn, R.TRANSPORT, k); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes([1]))
    for m in range(6): e.call(slot2, DP, 0, step, m, maxins=3_000_000)
    check(e.r8(base + step) == 100 and e.r8(base + 0x60 + step) == 1 << 3, f"Record armed: the hit written into the pattern (velocity {e.r8(base + step)}, micro steps {e.r8(base + 0x60 + step):#08b})")
    del e; gc.collect()

    # ---- Preset again in a drum's Preset view
    e = T.EL(img); e.at(100000); e.transport(0)
    e.btn(4); e.btn(8)
    view = e.r32(e.r32(MGR + 0x2C) + 0x8C)
    f0 = e.r8(view + S8.FLAG) & 1
    e.btn(8); f1 = e.r8(view + S8.FLAG) & 1; s1 = e.r8(MGR + 0x152)
    e.btn(8); f2 = e.r8(view + S8.FLAG) & 1
    check((f0, f1, f2) == (0, 1, 0) and s1 == 36, f"Drum 1's Preset view: Preset again = the chromatic view on, again off ({f0}, {f1}, {f2}), the view stays")
    e.btn(0); e.btn(8); e.btn(8)
    check(e.r8(view + S8.FLAG) & 1 == 0, "a synth's Preset view: Preset as before (the drum's flag untouched)")
    del e; gc.collect()
    # ---- the drums' sidechain (SC16's drum pages): K1-K4
    import scdrum as SD
    import build_sc16 as S16
    e = T.EL(img); e.at(100000); e.transport(0)
    dirty, dsp = [], []
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: (dirty.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1))), skip(uc)), begin=SD.MARK_DIRTY, end=SD.MARK_DIRTY)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: dsp.append((uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R1))), begin=S16.DSP_WRITE, end=S16.DSP_WRITE)
    e.btn(4); e.set_p0(e.r32(MGR + 0xC), 1); e.btn(15); e.set_p0(e.r32(MGR + 0xC), 0)
    st = e.r32(int(man["report"]["sc16"]["sc16_state"], 16)) and int(man["report"]["sc16"]["sc16_state"], 16)
    page = e.r8(st + 12)
    blk = e.r32(T.LZ.SESSION_OBJ + 0x14) + SD.TAIL + SD.O_BLK
    for _ in range(10): e.call(0x08033848, MGR, 0, 1, maxins=6_000_000)
    f = frame(e)
    check(page == 2 and e.r8(blk + 2) & 1 and e.r8(blk + 4) == S16.PRESETS[e.r8(st + 4) & 7][0] + 10 and (0x20, 26) in dirty,
          f"Drum 1, Sidechain (page {page}): K1 x 10 = drum 1's attack + 10 ({e.r8(blk + 4)}), its own values, the group marked")
    check(f[60] & 0xFF == SD.COL[0] and (f[60] >> 8) == e.r8(blk + 4) + 2, f"K1 in drum 1's colour, brightness = the value ({f[60]:#x})")
    grp = e.r32(S16.GROUP_TAB + 5 * 4) & ~1
    dsp.clear(); e.call(grp, maxins=8_000_000)
    adr = [a_ for a_, _ in dsp]
    check(S16.BLK + 1 in adr and S16.BLK + 4 in adr, f"the group handler: drum 1's own values to X:$3A11..$3A14 ({[hex(a_) for a_ in adr][-4:]})")
    e.call(T.PRESS, MGR, 16 + 2, 100, maxins=8_000_000); e.call(T.RELEASE, MGR, 16 + 2, maxins=8_000_000)
    check(e.r8(blk + 2) & 1 == 0 and e.r8(st + 4) & 7 == 2, f"a preset pad of drum 1: back to its presets (preset {e.r8(st + 4) & 7})")
    del e; gc.collect()

    # ---- the arpeggiator's colours with Shift
    ea = EA(img, man)
    from emu_sc08 import CONT
    ea.set_p0(ea.r32(CONT + 0x188), 0); ea.press(0); ea.release(0); ea.press(12); ea.release(12)
    p0 = ea.pads(); p1 = ea.pads(shift=True)
    pat = ea.playing(0); ea.call(ea.A["c_arset"], 0, pat, 0x80 | A.M_UP | 3 << 3); p2 = ea.pads(shift=True)
    up_pad = 26 + A.ORD_OF_PAD.index(A.M_UP)
    check(A.COL_AV not in p1[16:32], f"Shift, the arpeggiator off: no yellow, the Pattern Settings colours ({[hex(x) for x in p1[24:32]]})")
    check(p2[24] == A.COL_ON and p2[up_pad] == A.COL_ON and p2[16 + 2] == A.COL_ON and A.COL_AV not in p2[16:32],
          f"on, up, 1/16T: pad 25, its order and its resolution green, the others as Pattern Settings ({[hex(x) for x in p2[16:32]]})")
    del ea; gc.collect()
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(bytearray(Path(a[1]).read_bytes()), json.loads(Path(a[2]).read_text())) else 0)
