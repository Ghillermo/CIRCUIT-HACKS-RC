"""SC50.2 / Beta 5.5 ARM tests, through the controller and the engine's tick:
  * vcf21.use_kslow: the LFO shape (Shift + K8, page 5) moves on the 16th click, both ways; the granular's note mode (Shift + K6) on the 16th click; the FM algorithm (Shift + K5) in 16;
  * vcf21.use_routedef: MIDI 1's ACT carries bit 8 = 1 (filter first) with pad 29 off, 0 with it on;
  * the ACT message with shapes 4-6 still carries the shape in bits 13-15;
  * modesel.use_bluedim: the FX sequencer's pad of the engine row, dim, is 0x0F.

    python tools/emu_sc50_2.py SC50.2.bin SC50.2_manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
import fmeng as FM  # noqa: E402

V = T4.V


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    fl = {k: int(v, 16) for k, v in man["report"]["fmeng"]["labels"].items()}
    e = X.EP(img, man)
    dw = []
    def w(uc, a, s, d): dw.append((uc.reg_read(UC_ARM_REG_R1) >> 8, uc.reg_read(UC_ARM_REG_R2)))
    e.uc.hook_add(UC_HOOK_CODE, w, begin=0x080292F8, end=0x080292F8)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    tick = lambda n=1: [(e.at(e.t + 40), e.call(e.vl["c_vtick"], maxins=3_000_000)) for _ in range(n)]
    tick(10)
    tail = e.r32(V.LS_SESSION + 0x14) + V.LS_TAIL
    sh = lambda: e.r8(tail + V.O_LS) & 7
    def act(): dw.clear(); tick(12); return [v for v, a in dw if a == V.VB0 and (v >> 16) & 0x7F == 19]
    e.btn(2); e.btn(8); e.call(e.vl["c_vsetpage"], 0, V.LS_PAGE); X.frame(e)
    e.uc.mem_write(tail + V.O_LS, bytes([0xB2, 0, 0]))
    e.shift(True)
    for _ in range(15): e.knob(7, 1)
    s15 = sh(); e.knob(7, 1); s16 = sh()
    for _ in range(15): e.knob(7, -1)
    b15 = sh(); e.knob(7, -1); b16 = sh()
    check((s15, s16, b15, b16) == (2, 3, 3, 2), f"the LFO shape: 15 clicks nothing, the 16th a step, both ways ({s15}, {s16}, {b15}, {b16})")
    for _ in range(16 * 4): e.knob(7, 1)
    e.shift(False)
    a6 = act()
    check(sh() == 6 and a6 and all((v >> 13) & 7 == 6 for v in a6), f"the ACT message with shape 6 ({sh()}, {[hex(v) for v in a6[:2]]})")
    a0 = a6
    check(a0 and all(v >> 8 & 1 for v in a0), f"pad 29 off: filter first, bit 8 of the ACT ({[hex(v) for v in a0[:2]]})")
    e.pad(28); X.frame(e); a1 = act()
    check(a1 and not any(v >> 8 & 1 for v in a1), f"pad 29 on: VCA, FX, filter ({[hex(v) for v in a1[:2]]})")
    e.pad(28); X.frame(e)
    del e; gc.collect()
    # the granular's note mode, on a fresh device
    e = X.EP(img, man)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05])); tick(10)
    e.uc.mem_write(0x20045000 + 0x21EC, bytes(1))
    e.btn(2); e.btn(8); X.frame(e); e.pad(26); f = X.frame(e)
    check(f[22] & 0xFF == 0x0F, f"pad 23 of the engine row, off: the dim blue 0x0F ({f[22]:#x})")
    e.pad(20); X.frame(e); e.pad(26); X.frame(e)
    e.call(e.vl["c_vsetpage"], 0, 1); X.frame(e)
    e.shift(True)
    for _ in range(15): e.knob(5, 1)
    n15 = e.val(0, 26); e.knob(5, 1); n16 = e.val(0, 26); e.shift(False)
    check((n15, n16) == (0, 1), f"the granular's note mode: the 16th click ({n15}, {n16})")
    # the FM algorithm
    e.pad(26); X.frame(e); e.pad(23); X.frame(e); e.pad(26); X.frame(e)
    e.call(fl["c_fmblk"], 0); blk = e.uc.reg_read(UC_ARM_REG_R0)
    e.call(e.vl["c_vsetpage"], 0, 6); X.frame(e)
    alg = lambda: e.r8(blk + FM.P_ALG) >> 3
    e.uc.mem_write(blk + FM.P_ALG, bytes([0])); e.uc.mem_write(0x20045000 + 0x21EC, bytes(1)); e.shift(True)
    for _ in range(15): e.knob(4, 1)
    a15 = alg(); e.knob(4, 1); a16 = alg()
    for _ in range(16): e.knob(4, 1)
    a32 = alg(); e.shift(False)
    check((a15, a16, a32) == (0, 1, 2), f"the FM algorithm: 16 clicks each ({a15}, {a16}, {a32})")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())) else 0)
