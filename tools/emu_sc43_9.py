"""SC43.9 ARM tests (vcf21.use_lfoshape, mpatch.use_lshape), through the controller, the real LED task, the engine's tick and the patch routines:
  * MIDI 1's own engine on, its Preset view, knob page 5: Shift + K8 = the LFO shape, a step every 4 clicks (3 clicks: still 0; the fourth: 1), up to 5
    and down to 0 (no wrap); the project's tail + 561 = 0xB0 | shape (MIDI 2's + 562 untouched); K8 without Shift still LFOP (code 21);
  * its LED with Shift on page 5: the shape's colour at full brightness;
  * the engine's tick: MIDI 1's ACT message carries the shape in bits 13-15;
  * the own-synth patch: gathering writes version 2 and the shape ([41] = 2, [42]); applying a version 1 patch = the reverse saw, a version 2 one
    = its shape.

    python tools/emu_sc43_9.py SC43.9.bin SC43.9_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
import mpatch as MP  # noqa: E402
import packio as PK  # noqa: E402

V = T4.V
MGR = X.MGR


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = X.EP(img, man)
    dw = []
    def w(uc, a, s, d): dw.append((uc.reg_read(UC_ARM_REG_R1) >> 8, uc.reg_read(UC_ARM_REG_R2)))
    e.uc.hook_add(UC_HOOK_CODE, w, begin=0x080292F8, end=0x080292F8)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    tick = lambda n=1: [(e.at(e.t + 40), e.call(e.vl["c_vtick"], maxins=3_000_000)) for _ in range(n)]
    tick(10)
    tail = e.r32(V.LS_SESSION + 0x14) + V.LS_TAIL
    sh = lambda t=0: e.r8(tail + V.O_LS + t)
    e.btn(2); e.btn(8); e.call(e.vl["c_vsetpage"], 0, V.LS_PAGE); X.frame(e)
    lfop0 = e.val(0, 21)
    e.uc.mem_write(tail + V.O_LS, bytes([0, 0x5A, 0]))
    e.shift(True)
    for _ in range(3): e.knob(7, 1)
    s3 = sh()
    e.knob(7, 1); s4 = sh(); f1 = X.frame(e)
    check(s3 >> 4 != 0xB and s4 == 0xB1 and sh(1) == 0x5A, f"Shift + K8, page 5: 3 clicks nothing ({s3:#x}), the fourth = shape 1 ({s4:#x}); MIDI 2's byte untouched ({sh(1):#x})")
    check(f1[67] == (127 + 2) << 8 | V.LS_COLS[1], f"its LED with Shift: the saw's colour at full brightness ({f1[67]:#x})")
    for _ in range(40): e.knob(7, 1)
    s5 = sh(); f5 = X.frame(e)
    for _ in range(60): e.knob(7, -1)
    s0 = sh()
    check(s5 == 0xB5 and s0 == 0xB0 and f5[67] & 0xFF == V.LS_COLS[5], f"up to 5 ({s5:#x}, LED {f5[67]:#x}), down to 0 ({s0:#x}): no wrap")
    for _ in range(4 * 3): e.knob(7, 1)
    e.shift(False)
    e.knob(7, 2)
    check(sh() == 0xB3 and e.val(0, 21) == lfop0 + 2, f"shape 3 ({sh():#x}); K8 without Shift still LFOP (code 21: {lfop0} -> {e.val(0, 21)})")
    dw.clear(); tick(12)
    acts = [v for v, a in dw if a == V.VB0 and (v >> 16) & 0x7F == 19]
    check(acts and all((v >> 13) & 7 == 3 for v in acts), f"the engine's tick: MIDI 1's ACT with the shape in bits 13-15 ({[hex(v) for v in acts[:3]]})")
    # the patch
    ml = {k: int(v, 16) for k, v in man["report"]["mpatch"]["labels"].items()}
    e.call(ml["c_mpgather"], 0, maxins=4_000_000)
    buf = bytes(e.uc.mem_read(PK.BUF, MP.DATA))
    check(buf[:4] == b"CTM1" and buf[41] == 2 and buf[42] == 3, f"the patch: version {buf[41]}, shape {buf[42]}")
    e.uc.mem_write(PK.BUF + 41, bytes([1])); e.call(ml["c_mpapply"], 0, maxins=8_000_000); a1 = sh()
    e.uc.mem_write(PK.BUF + 41, bytes([2, 4])); e.call(ml["c_mpapply"], 0, maxins=8_000_000); a2 = sh()
    check(a1 == 0xB0 and a2 == 0xB4, f"applying a version 1 patch: the reverse saw ({a1:#x}); a version 2 one: its shape ({a2:#x})")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
