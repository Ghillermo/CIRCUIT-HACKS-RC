"""Clear + a scene pad clears the scene's chains too (scrules.use_sclear(), Beta 5.63; the 2026-11-14 bug hunt, SCR-3).

    python tools/emu_scnclear.py firmware/b5.62 [more build dirs]

Through the controller, the Mixer's own pad handler (not stubbed): a chain on Synth 1, Shift + scene 1 and Shift + scene 2 (the chains into
the scenes); Clear + scene 1 = the stock's scene clear (0x0802DFB8, its eight writes still made).  Expected: scene 1's bit in scrules' bitmap and
its mask gone, scene 2's kept; c_pcchained says no for scene 1; another chain in place, then scene 1 picked while stopped (the LED task's work)
or scene 1 starting while playing (the track advance): the chain in place stays.  Up to Beta 5.62 the old chains came back."""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR, UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc17_6
emu_sc17_6.MIX_PRESS = -1                                       # the Mixer's pad handler for real
from emu_sc40_5 import EC  # noqa: E402
from emu_sc35 import MGR  # noqa: E402
import scrules as SR  # noqa: E402

CLEAR, STORE_WRITE = 0x0802DFB8, 0x0802B2CC


def run(d):
    d = Path(d); img = next(d.glob("*.bin")).read_bytes(); man = json.loads((d / "manifest.json").read_text())
    R = man["report"]
    L = {k: int(v, 16) for k, v in R["patchain"]["labels"].items()}
    B = {k: int(v, 16) for k, v in R["scrules"]["io"]["labels"].items()}
    xpv = {k: int(v, 16) for k, v in R["xlanes"]["prev"].items()}
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = EC(img, man, L)
    for k in ("load", "new"):
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, dd: uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1), begin=xpv[k], end=xpv[k])
    RB = SR.RB
    st = lambda o, n: bytes(e.uc.mem_read(RB + o, n))
    hmap = lambda: struct.unpack_from("<H", st(SR.H_MAP, 2))[0]
    word = lambda t: struct.unpack_from("<I", st(SR.O_CURW + 4 * t, 4))[0]
    mask = lambda: st(SR.O_CURM, 1)[0]
    def setw(t, w):
        e.uc.mem_write(RB + SR.O_CURW + 4 * t, struct.pack("<I", w)); e.uc.mem_write(RB + SR.O_CURM, bytes([mask() | 1 << t]))
    e.uc.mem_write(RB, bytes(SR.O_SCW + 16 * 32)); e.uc.mem_write(RB, b"SCR3")
    e.st(); e.persistent(); e.clear_state(); e.live(0xFF)
    hits = {"clear": 0, "write": 0}
    def hk(name): return lambda uc, a, s, dd: hits.__setitem__(name, hits[name] + 1)
    e.uc.hook_add(UC_HOOK_CODE, hk("clear"), begin=CLEAR, end=CLEAR)
    e.uc.hook_add(UC_HOOK_CODE, hk("write"), begin=STORE_WRITE, end=STORE_WRITE)
    press = lambda i: e.call(0x08033320, MGR, i, maxins=8_000_000)
    release = lambda i: e.call(0x0803381A, MGR, i, maxins=8_000_000)
    pad = lambda q: (e.call(0x08033282, MGR, q, 100, maxins=8_000_000), e.call(0x080332FE, MGR, q, maxins=8_000_000))
    shift = lambda v: e.set_p0(e.r32(MGR + 0xC), v)
    held = lambda v: e.uc.mem_write(e.ptr(e.r32(e.r32(MGR + 0x20) + 0xC), 0), bytes([v]))
    chained = lambda s: (e.call(L["c_pcchained"], e.tail, s), e.uc.reg_read(UC_ARM_REG_R0))[1]
    W1, W2 = SR.pack([(0, 1, 2)]), SR.pack([(4, 6, 3)])

    press(14); release(14)
    setw(0, W1)
    shift(1); pad(16); pad(17); shift(0)
    check(hmap() & 3 == 3 and st(SR.O_SCM, 2) == b"\x01\x01" and chained(0), f"Shift + scenes 1 / 2: their chains saved (bitmap {hmap():#x})")
    hits.update(clear=0, write=0)
    held(1); pad(16); held(0)
    check(hits["clear"] == 1 and hits["write"] == 8, f"Clear + scene 1: the stock's clear, its eight writes ({hits})")
    check(not hmap() & 1 and st(SR.O_SCM, 1)[0] == 0, f"... scene 1's bit and mask gone (bitmap {hmap():#x}, mask {st(SR.O_SCM, 1)[0]})")
    check(hmap() & 2 and st(SR.O_SCM + 1, 1)[0] == 1, "... scene 2's kept")
    check(not chained(0) and chained(1), "... scene 1 no longer shown as chained, scene 2 still")
    setw(0, W2)
    pad(17); e.call(B["c_srwork"], maxins=200_000_000)
    setw(0, W2)
    pad(16); e.call(B["c_srwork"], maxins=200_000_000)
    check(word(0) == W2 and mask() & 1, f"scene 1 picked (stopped): the chain in place stays ({word(0):#010x})")
    setw(0, W2); e.clear_state(); e.set_playing(0, 0); e.advance(0, forced=1, scene_start=1, scene=0)
    check(word(0) == W2 and mask() & 1, f"scene 1 starting (playing): the chain in place stays ({word(0):#010x})")
    del e; gc.collect()
    return fails


if __name__ == "__main__":
    n = 0
    for d in sys.argv[1:]:
        print("==", d); n += run(d)
    print("ALL PASS" if not n else f"{n} FAILED")
    sys.exit(1 if n else 0)
