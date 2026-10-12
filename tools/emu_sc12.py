"""SC12 tests: drum fine tuning in cents (byte +0x53 of the drum Preset view)."""
from __future__ import annotations
import json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc08 import E8, MGR, VIEWS  # noqa: E402
from emu_sc11 import setup as _setup, shift_preset, bias  # noqa: E402
from build_sc09 import table as semi_table  # noqa: E402

HANDLERS = (0x080287DE, 0x0802887A, 0x0802890E, 0x080289A2)
PADDR = (0xA4, 0xAE, 0xB8, 0xC2)
SEMI = semi_table()


def expect(v, c):
    w = SEMI[v & 0x7F]
    if c:
        w = min(0x7FFFFF, (w * round(65536 * 2 ** (c / 1200))) >> 16)
    return w


def setup(image, drum=0, pitch=None):
    e = _setup(image, drum, pitch)
    for v in VIEWS: e.uc.mem_write(v + 0x53, b"\x00")       # constructor zeroes it on the device
    return e


def s8(b): return b - 256 if b > 127 else b


def dsp_pitch(e, d, pitch):
    """run drum d's DSP-update handler with Pitch forced to `pitch`; return the word written to the pitch address"""
    out = []
    def h(uc, a, s, _):
        if a == 0x08036192 and uc.reg_read(UC_ARM_REG_R0) == 0x10 and uc.reg_read(UC_ARM_REG_R1) == 2 + 7 * d:
            uc.reg_write(UC_ARM_REG_R0, pitch); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        elif a == 0x080292F8:                    # stub the SPI write (it waits on hardware)
            if uc.reg_read(UC_ARM_REG_R2) == PADDR[d]: out.append(uc.reg_read(UC_ARM_REG_R1))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    hk = e.uc.hook_add(UC_HOOK_CODE, h)
    e.call(HANDLERS[d], maxins=300000); e.uc.hook_del(hk)
    return out


def knob(e, k, delta):
    writes, marks = [], []
    def h(uc, a, s, _):
        if a == 0x08031A98: writes.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2)))
        elif a == 0x0803BDCC: marks.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)))
    hk = e.uc.hook_add(UC_HOOK_CODE, h)
    e.call(0x08033848, MGR, k, delta & 0xFFFFFFFF, maxins=600000); e.uc.hook_del(hk)
    return writes, marks


def main(stock, img, s11img):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1

    # 1. DSP pitch word = semitone table * 2^(cents/1200), every drum, any mode
    for d in range(4):
        e = setup(img, d); e11 = setup(s11img, d)
        for v in (64, 0, 30, 100, 127):
            check(dsp_pitch(e, d, v) == dsp_pitch(e11, d, v) == [expect(v, 0)], f"drum {d+1} Pitch {v}, 0 cents: same as SC11")
        for c in (1, -1, 37, -50, 100, -100):
            e.uc.mem_write(VIEWS[d] + 0x53, bytes([c & 0xFF]))
            for v in (64, 10, 127):
                got = dsp_pitch(e, d, v)
                check(got == [expect(v, c)], f"drum {d+1} Pitch {v}, {c:+} cents -> {got} (exp {expect(v, c):#x})")
        e.uc.mem_write(VIEWS[d] + 0x53, b"\x00")
    e = setup(img, 0); e.uc.mem_write(VIEWS[0] + 0x53, bytes([200]))          # out of range (-56 ok), 0x9C=-100..: test garbage 0x80
    e.uc.mem_write(VIEWS[0] + 0x53, b"\x80")
    check(dsp_pitch(e, 0, 64) == [expect(64, 0)], "garbage cents (-128) ignored")
    # precision: 1 cent = 2^(1/1200)
    r = expect(64, 1) / expect(64, 0)
    check(abs(r - 2 ** (1 / 1200)) < 2e-5, f"1 cent ratio {r:.6f}")
    # cents only affect their own drum
    e = setup(img, 0); e.uc.mem_write(VIEWS[1] + 0x53, bytes([50]))
    check(dsp_pitch(e, 0, 64) == [expect(64, 0)] and dsp_pitch(e, 1, 64) == [expect(64, 50)], "per-drum: drum 2 cents leave drum 1 alone")

    # 2. knob in chromatic mode: cents, no Pitch write, resend this drum's group
    for d in range(4):
        e = setup(img, d); shift_preset(e); v = VIEWS[d]; b0 = bias(e, v)
        seq = [(7, 7), (-20, -13), (300, 100), (-500, -100), (100, 0)]
        ok = True
        for delta, expc in seq:
            w, m = knob(e, 1, delta)
            ok &= w == [] and s8(e.r8(v + 0x53)) == expc and (0x10, 2 + 7 * d) in m and bias(e, v) == b0
            if not ok:
                print("   ", delta, w, m, s8(e.r8(v + 0x53)), bias(e, v)); break
        check(ok, f"drum {d+1} chromatic knob: cents 7,-13,+100 clamp,-100 clamp,0; no Pitch write; group resent; bias unchanged")
    # 3. Shift + knob in chromatic mode = SC11 behaviour
    e = setup(img, 0); e11 = setup(s11img, 0); shift_preset(e); shift_preset(e11)
    for x in (e, e11): x.set_p0(x.r32(MGR + 0xC), 1)
    for delta in (3, -5):
        w, _ = knob(e, 1, delta); w11, _ = knob(e11, 1, delta)
        check(w == w11 and w and bias(e, VIEWS[0]) == bias(e11, VIEWS[0]) and e.r8(VIEWS[0] + 0x53) == 0,
              f"Shift+knob {delta:+}: semitone bias as SC11 {w} bias {bias(e, VIEWS[0])}")
    # 4. outside chromatic mode: knob as stock, cents untouched
    es = E8(stock); es.call(0x08033320, MGR, 4, maxins=600000)
    e = setup(img, 0); e.uc.mem_write(VIEWS[0] + 0x53, bytes([12]))
    for delta in (2, -4):
        check(knob(e, 1, delta)[0] == knob(es, 1, delta)[0] and e.r8(VIEWS[0] + 0x53) == 12, f"normal mode knob {delta:+}: as stock, cents kept")
    for k in (3, 5, 7):
        es = setup(stock, 0); e = setup(img, 0); shift_preset(e)
        check(knob(es, k, 1)[0] == knob(e, k, 1)[0], f"knob {k} in chromatic mode: as stock")
    print("SC12 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(*(Path(p).read_bytes() for p in sys.argv[1:4])) else 0)
