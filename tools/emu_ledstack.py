"""SC56.7 / Beta 5.52 (fix, issue #22 of the public repository: «Beta 5.48 – Circuit Tracks crashes when opening MIDI 1/2 presets»): the LED task's
stack in MIDI 1's Preset view.  The emulated firmware (emu_sc48_8's harness), MIDI 1 then Preset through the controller, the lowest SP over the real
LED task's frames: the first frame after the view opens and a later one, the own synth off and on.  SC54 reset the unit there at 1 808 B (morph
heads); Beta 5.41 works at 1 792; Beta 5.48-5.51 read 1 840 (fmmap's c_mmled and patmut's c_pmled pushed 36 B each before the chain below).

    python tools/emu_ledstack.py BUILD.bin manifest.json [MAX_BYTES=1792]
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_SP, UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc48_8 as S  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
from emu_sc17_6 import MGR  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402

V = T4.V
TOP = 0x2006F000                                              # emu_sc05's stack top for a call


def depths(img, man):
    e = S.ET(img, man)
    def drain():
        r = e.r32(0x200069F4)
        for k in range(e.r8(r + 0x18)): e.uc.mem_write(e.r32(e.r32(e.r32(r + 0x14) + 4 * k) + 0x10), bytes(4))
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: uc.mem_write(e.r32(uc.reg_read(UC_ARM_REG_R0) + 0x10), bytes(4)), begin=0x08035A50, end=0x08035A50)
    lo = [1 << 32]
    def hk(uc, a, s_, d):
        sp = uc.reg_read(UC_ARM_REG_SP)
        if sp < lo[0]: lo[0] = sp
    def depth(fn):
        lo[0] = 1 << 32; h_ = e.uc.hook_add(UC_HOOK_CODE, hk); fn(); e.uc.hook_del(h_); return TOP - lo[0]
    t = [500000]
    def at(ms): t[0] += ms; e.w32(0x2000081C, t[0])
    def btn(b):
        drain(); e.call(0x08033320, MGR, b, maxins=20_000_000); drain(); e.call(0x0803381A, MGR, b, maxins=20_000_000)
    at(0); btn(2); at(20); btn(8)
    out = {}
    at(20); out["first frame"] = depth(lambda: X.frame(e))
    at(20); out["next frame"] = depth(lambda: X.frame(e))
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 1]))
    at(20); out["own synth on"] = depth(lambda: X.frame(e))
    del e; gc.collect()
    return out


def main(img, man, limit=1792):
    out = depths(Path(img).read_bytes(), man)
    worst = max(out.values())
    ok = worst <= limit
    print(("ok  : " if ok else "FAIL: ") + f"MIDI 1's Preset view, the LED task's stack: {out} (limit {limit} B)")
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if ok else '1 FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(main(a[0], json.loads(Path(a[1]).read_text()), int(a[2]) if len(a) > 2 else 1792))
