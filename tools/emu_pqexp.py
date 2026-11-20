"""Alpha 7.12 / 7.13 / RC4.19 test (packio.use_pqexp; the user, 2026-11-20: «When I press clear and don't delete anything, pads flash for a while. Then
after a minute or so, they flash again»), by presses and the real LED task:
  * Clear, pad 31 (pack 30 asked), nothing more; LED frames at 1 s and 6 s; 65.5 s after the question (its 8-bit age wraps) the pads do not blink
    and Clear deletes nothing (before: the question was fresh again and Clear deleted pack 30);
  * a fresh question still works (Clear, pad, Clear within 5 s = deleted).

    python tools/emu_pqexp.py BUILD.bin manifest.json
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import E35, set_loaded, MGR, TICK, PVIEW_OBJ, PK  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_R4  # noqa: E402


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = E35(img, man)
    set_loaded(e, man, 31)
    e.btn(26, shift=True)
    def frame():
        from emu_sc05 import STOP
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR)
        e.call(0x08033B3E, maxins=5_000_000)
        return struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138)))
    clear = lambda: (e.call(0x08033320, MGR, 23, maxins=900000), e.call(0x0803381A, MGR, 23, maxins=900000))
    pad = lambda p_: (e.call(PRESS, MGR, p_, 100, maxins=2_000_000), e.call(RELEASE, MGR, p_, maxins=900000))
    T0 = 100000
    e.w32(TICK, T0); e.api.clear()
    clear(); pad(30)
    q = bytes(e.uc.mem_read(PVIEW_OBJ + PK.PQ_OFF, 2))
    check(q == bytes([PK.PQ_MAGIC, 30]), f"Clear, pad 31: pack 30 asked ({q.hex()})")
    blinks = lambda: {frame()[30] for _ in range(1)}
    seen = set()
    for t in range(T0, T0 + 4 * 128, 64):
        e.w32(TICK, t); seen.add(frame()[30])
    check(PK.RED in seen or 0 in seen, f"fresh: pad 31 blinks ({sorted(hex(x) for x in seen)})")
    e.w32(TICK, T0 + 1000); frame(); e.w32(TICK, T0 + 6000); frame()     # the LED task keeps running while nothing is pressed
    seen = set()
    for t in range(T0 + 65536, T0 + 65536 + 4 * 128, 64):
        e.w32(TICK, t); seen.add(frame()[30])
    check(len(seen) == 1, f"65.5 s later: pad 31 does not blink ({sorted(hex(x) for x in seen)})")
    e.api.clear(); clear()
    check(not any(c[0] == "del" for c in e.api), f"65.5 s later, Clear: nothing deleted ({e.api[:2]})")
    e.w32(TICK, 400000); e.uc.mem_write(PVIEW_OBJ + PK.PQ_OFF, bytes(3)); e.api.clear()
    clear(); pad(29); clear()
    check(any(c[0] == "del" and c[1][2] == 29 for c in e.api), f"a fresh question: Clear, pad 30, Clear = pack 29 deleted ({e.api[:2]})")
    if "packsave" in man["report"]:                  # Alpha 7.12 / 7.13: the black box's heartbeat 0 before a pack copy or delete
        import blackbox as BX
        now = BX.BB + BX.O.NOW
        e.w32(now, 12345); clear(); check(e.r32(now) == 0, "Clear: the black box's heartbeat 0 (a delete may follow)")
        e.uc.mem_write(PVIEW_OBJ + PK.PQ_OFF, bytes(3)); e.w32(now, 12345); e.seen.clear(); pad(28)   # (no question pending: the pad is the stock's)
        from emu_sc17_7 import VIEW7_PRESS
        check(e.r32(now) == 0 and any(x[0] == VIEW7_PRESS and x[2] == 28 for x in e.seen), "a packs view pad: the heartbeat 0, then the stock's pad (same pad)")
    print(f"{man.get('marker', '?')} PQEXP RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())) else 0)
