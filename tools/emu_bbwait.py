"""Alpha 7.15 test (tools/bbwait.py): the content API's two calls of its post (0x0803CAD6 / 0x0803CB02) go through c_bbwt; a request with no callback
(the caller waits) made by the main loop's task puts the black box's heartbeat to 0, then the post runs as always; a request with a callback, or one
from another task, leaves the heartbeat alone.

    python tools/emu_bbwait.py BUILD.bin manifest.json
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc05 as X  # noqa: E402
import bbwait as W  # noqa: E402
import blackbox as BB  # noqa: E402
from thumb import bl  # noqa: E402
import unicorn  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR, UC_ARM_REG_R0  # noqa: E402


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = int(man["report"]["bbwait"]["labels"]["c_bbwt"], 16)
    check(all(bytes(img[s - 0x08010000:s - 0x08010000 + 4]) == bl(s, L) for s in W.SITES), "both calls of the post -> c_bbwt")
    e = X.E(img)
    posted = []
    def h(uc, a, s, d):
        posted.append(uc.reg_read(UC_ARM_REG_R0)); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(unicorn.UC_HOOK_CODE, h, begin=W.POST, end=W.POST)
    req = 0x20060200
    now, mtcb = BB.BB + BB.O.NOW, BB.BB + BB.O2.MTCB
    main_tcb = 0x2000835C
    for cb, cur, want0, what in ((0, main_tcb, True, "the main task waits"), (0x08001234, main_tcb, False, "a request with a callback"),
                                 (0, 0x20008CDC, False, "the LED task waits")):
        e.uc.mem_write(req, bytes(0x3C) + struct.pack("<I", cb)); e.w32(W.CUR_TCB, cur); e.w32(mtcb, main_tcb); e.w32(now, 777)
        posted.clear(); e.call(L, req, maxins=10000)
        check(posted == [req] and (e.r32(now) == 0) == want0, f"{what}: the post called, heartbeat {'0' if want0 else 'kept'} ({e.r32(now)})")
    print(f"{man.get('marker', '?')} BBWAIT RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())) else 0)
