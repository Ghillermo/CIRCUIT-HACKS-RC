"""Alpha 7.11 / RC4.18 test (packio.use_delled; the user, 2026-11-20: «When I delete a pack, I want that pack's led to turn off. Right now, it won't
signal the deletion until reboot»), by presses only (Shift + Projects, Clear, pad, Clear) and the real LED task:
  * the card read ([view + 0xC] p0 bit 0: in emulation it is not, and every redraw pastes a fixed pattern); packs 29 / 30 present (their bytes of the packs view's store [view + 0x14] = a colour), the loaded pack 31;
  * Clear, pad 31 (pack 30), Clear: pack 30 deleted; its byte of [view + 0x14] = 0xFF, the view's buffer entry 30 = 0 and the frame's pad 30 dark;
  * pack 29 still lit.

    python tools/emu_delled.py BUILD.bin manifest.json
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc35 as T  # noqa: E402
from emu_sc35 import E35, set_loaded, MGR, TICK, PVIEW_OBJ, PK  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R4  # noqa: E402

PARAM_GET, PARAM_WPTR, PARAM_COMMIT = 0x0803542C, 0x080354FA, 0x080353C0


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    from emu_sc17_6 import PRESS, RELEASE
    e = E35(img, man)
    e.r0 = lambda fn, *a: (e.call(fn, *a, maxins=900000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    set_loaded(e, man, 31)
    e.btn(26, shift=True)
    check(e.r32(MGR + 0x6C) == PVIEW_OBJ, "Shift + Projects: the packs view")
    st = e.r32(PVIEW_OBJ + 0x14)
    e.set_p0(e.r32(PVIEW_OBJ + 0xC), e.r8(e.r0(PARAM_GET, e.r32(PVIEW_OBJ + 0xC), 0)) | 1)   # the card read (bit 0 of [view + 0xC] p0; else a fixed pattern, 0x080441DA)
    for k, c in ((29, 3), (30, 5)):                  # packs 29 / 30 present (a colour each), through the store (the view redraws them)
        p = e.r0(PARAM_WPTR, st, k); e.uc.mem_write(p, bytes([c])); e.call(PARAM_COMMIT, st, maxins=900000)
        e.uc.mem_write(e.r0(PARAM_GET, st, k), bytes([c]))   # (the read copy too: in emulation no task copies one store copy into the other)
    byte = lambda k: e.r8(e.r0(PARAM_GET, st, k))
    buf = e.r32(e.r32(PVIEW_OBJ + 4))
    view = lambda k: struct.unpack_from("<H", bytes(e.uc.mem_read(buf + 2 * k, 2)))[0]
    def frame():
        from emu_sc05 import STOP
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR)
        e.call(0x08033B3E, maxins=5_000_000)
        return struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138)))
    clear = lambda: (e.call(0x08033320, MGR, 23, maxins=900000), e.call(0x0803381A, MGR, 23, maxins=900000))
    pad = lambda p_: (e.call(PRESS, MGR, p_, 100, maxins=2_000_000), e.call(RELEASE, MGR, p_, maxins=900000))
    e.w32(TICK, 100000); e.api.clear()
    check(view(29) != 0 and view(30) != 0, f"packs 29 / 30 lit before ({view(29):#x}, {view(30):#x})")
    clear(); pad(30); clear()
    check(e.api[:1] == [("del", (1, 0xFFFFFFFF, 30), 0, 0)], f"Clear, pad 31, Clear: pack 30 deleted ({e.api[:2]})")
    check(byte(30) == 0xFF, f"pack 30's byte of [view + 0x14] = 0xFF (empty) ({byte(30):#x})")
    check(view(30) == 0, f"the view's buffer: pad 31 dark ({view(30):#x})")
    e.w32(TICK, 100000 + 8000)                       # (the question gone: the stock's colours on the frame)
    f = frame()
    check(f[30] == 0, f"the LED frame: pad 31 dark ({f[30]:#x})")
    check(byte(29) == 3 and view(29) != 0 and f[29] != 0, f"pack 29 still lit ({byte(29)}, {view(29):#x}, {f[29]:#x})")
    print(f"{man.get('marker', '?')} DELLED RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())) else 0)
