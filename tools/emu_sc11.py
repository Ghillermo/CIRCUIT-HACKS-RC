"""SC11 tests: chromatic drum Preset view with Pitch-knob bias."""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE, Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc08 import E8, MGR, CONT, VIEWS, MASKS, model  # noqa: E402


def setup(image, drum=0, pitch=None):
    e = E8(image)
    for v in VIEWS: e.uc.mem_write(v + 0x51, b"\x00\x00")
    if pitch is not None:      # force the DSP-mirror value of this drum's Pitch
        def h(uc, a, s, d):
            if a == 0x08036192 and uc.reg_read(UC_ARM_REG_R0) == 0x10 and uc.reg_read(UC_ARM_REG_R1) == 2 + 7 * drum:
                uc.reg_write(UC_ARM_REG_R0, e.cur); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        e.cur = pitch; e.uc.hook_add(UC_HOOK_CODE, h)
    e.call(0x08033320, MGR, 4 + drum, maxins=600000)
    return e


def shift_preset(e):
    e.set_p0(e.r32(MGR + 0xC), 1); e.call(0x08033320, MGR, 8, maxins=600000); e.set_p0(e.r32(MGR + 0xC), 0)


def press(e, view, pad):
    log = []
    hk = e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: log.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2))) if a == 0x08031A98 else None)
    e.call(0x08033282, MGR, pad, 100, maxins=600000); e.call(0x080332CE, MGR, pad, maxins=600000)
    e.uc.hook_del(hk)
    return log


def bias(e, view):
    b = e.r8(view + 0x52); return b - 256 if b > 127 else b


def main(stock, img):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    # constructor now zeroes +0x51..+0x53
    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
    uc.mem_map(0x08000000, 0x80000); uc.mem_write(0x08010000, img); uc.mem_map(0x20000000, 0x10000)
    uc.mem_write(0x20000050, b"\x77\x55\x66\x44"); uc.reg_write(UC_ARM_REG_R5, 0x20000000); uc.reg_write(UC_ARM_REG_R0, 1)
    uc.emu_start(0x0804D89C | 1, 0x0804D8A0)
    check(bytes(uc.mem_read(0x20000050, 4)) == b"\x01\x00\x00\x00", "constructor clears flag and bias")
    for d, pitch in ((0, 64), (1, 67), (2, 52), (3, 64)):
        e = setup(img, d, pitch); shift_preset(e); v = VIEWS[d]
        check(e.r8(v + 0x51) & 1 == 1 and bias(e, v) == pitch - 64, f"drum {d+1}: Shift+Preset on, bias = Pitch-64 = {bias(e, v)}")
        log = press(e, v, 0x13)
        exp = max(0, min(127, model(MASKS[0], 0, 0x13)[0] + pitch - 64))
        check(log == [(40 + 5 * d, exp)], f"drum {d+1}: pad 0x13 -> Pitch {exp} (bias {pitch-64}) {log}")
    # knob turns: stock Pitch write + bias follows the applied change
    e = setup(img, 0, None); shift_preset(e); v = VIEWS[0]; b0 = bias(e, v)
    ks = E8(stock); ks.call(0x08033320, MGR, 4, maxins=600000); ks.call(0x08033320, MGR, 8, maxins=600000)
    for delta in (3, -5, 9):
        log_s = []; hk = ks.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: log_s.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2))) if a == 0x08031A98 else None)
        ks.call(0x08033848, MGR, 1, delta & 0xFFFFFFFF, maxins=600000); ks.uc.hook_del(hk)
        log = []; hk = e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: log.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2))) if a == 0x08031A98 else None)
        e.call(0x08033848, MGR, 1, delta & 0xFFFFFFFF, maxins=600000); e.uc.hook_del(hk)
        check(log == log_s and bias(e, v) == log[0][1] - 64, f"knob delta {delta}: Pitch write identical to stock {log}, bias {bias(e, v)}")
    b1 = bias(e, v)
    check(b1 == b0 + 3 - 5 + 9, f"bias followed the knob: {b0} -> {b1}")
    log = press(e, v, 0x13)
    check(log == [(40, max(0, min(127, model(MASKS[0], 0, 0x13)[0] + b1)))], f"pad after knob uses new bias {log}")
    # other knobs untouched, knob in normal mode does not change bias
    e = setup(img, 0, None); e.uc.mem_write(VIEWS[0] + 0x52, b"\x05")
    e.call(0x08033848, MGR, 1, 2, maxins=600000)
    check(bias(e, VIEWS[0]) == 5, "chromatic off: knob leaves bias alone")
    for knob in (3, 5, 7):
        es = setup(stock, 0); e9 = setup(img, 0); shift_preset(e9)
        ls, l9 = [], []
        es.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: ls.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2))) if a == 0x08031A98 else None)
        e9.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: l9.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2))) if a == 0x08031A98 else None)
        es.call(0x08033848, MGR, knob, 1, maxins=600000); e9.call(0x08033848, MGR, knob, 1, maxins=600000)
        check(ls == l9, f"knob {knob}: same as stock {l9}")
    # turning off restores stock colours
    e = setup(img, 0, None); shift_preset(e); shift_preset(e)
    check(e.r8(VIEWS[0] + 0x51) & 1 == 0 and e.leds(VIEWS[0]) == E8(stock).leds(VIEWS[0]), "second Shift+Preset: off, stock LEDs")
    es, e9 = setup(stock, 0), setup(img, 0)
    es.call(0x08033320, MGR, 0, maxins=600000); e9.call(0x08033320, MGR, 0, maxins=600000)
    es.set_p0(es.r32(MGR + 0xC), 1); e9.set_p0(e9.r32(MGR + 0xC), 1)
    es.call(0x08033320, MGR, 8, maxins=600000); e9.call(0x08033320, MGR, 8, maxins=600000)
    check(es.r8(CONT + 0x18C) == e9.r8(CONT + 0x18C), "Shift+Preset on a synth: as stock")
    print("SC11 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes()) else 0)
