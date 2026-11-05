"""Probe (2026-11-03, the user: «setting it manually or pressing the pads don't work. Only some patches move a filter, but the amp remains the same»):
Synth 1's pad 1 in its Note view pressed at two velocities on an image; what the ARM sends to the DSP for that note (the note-on 0x080217EA's
arguments and every DSP write 0x080292F8 during the press), so the stock image and a mod image can be compared.

    python tools/probe_synthvel.py IMAGE.bin MANIFEST.json [STOCK]
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_cscale as ECS  # noqa: E402
import emu_lazysave as T  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402

LIVE = 0x0804B07A
OUT = 'build/uptest/vel_%s.json' % ('direct' if '--router' in sys.argv else 'pad')
DIRECT = '--router' in sys.argv
NOTE_ON, DSP_W, SERVICE, ROUTER = 0x080217B4, 0x080292F8, 0x080219E8, 0x0803222C


def run(img, man, vel):
    if man:
        e = ECS.EC(bytearray(img), {k: int(v, 16) for k, v in man["report"]["cscale"]["labels"].items()})
    else:
        e = ECS.EC(bytearray(img), {})
    e.stubs.pop(0x08031DA4, None)                                    # the note path itself, not stubbed
    e.at(300000); e.transport(0)
    log = []
    def on(uc, a, s, d):
        regs = [uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)]
        if a == NOTE_ON:
            q = struct.unpack_from("<I", uc.mem_read(0x080217B6 + 4 + 0x21C & ~3, 4))[0]
            log.append(("note_on", bytes(uc.mem_read(q, 0x20)).hex()))
        elif a == ROUTER:
            log.append(("router", tuple(regs)))
        else:
            log.append(("dsp_w", tuple(regs)))
    e.uc.hook_add(UC_HOOK_CODE, on, begin=NOTE_ON, end=NOTE_ON)
    e.uc.hook_add(UC_HOOK_CODE, on, begin=DSP_W, end=DSP_W)
    e.uc.hook_add(UC_HOOK_CODE, on, begin=ROUTER, end=ROUTER)
    st = e.r32(ECS.MGR + 0x78)                                        # fixed velocity (parameter 2, bit 1) off
    fx0 = e.r8(e.r0(0x0803542C, st, 2))
    e.call(0x080354FA, st, 2); w = e.uc.reg_read(UC_ARM_REG_R0); e.uc.mem_write(w, bytes([e.r8(w) & ~2])); e.call(0x080353C0, st)
    log.append(("fixed was", fx0, "now", e.r8(e.r0(0x0803542C, st, 2))))
    e.btn(0)                                                          # Synth 1: its Note view (subview 1)
    for _ in range(4):
        if e.r8(ECS.MGR + 0x152) == 1: break
        e.btn(9)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: log.append(("live", [uc.reg_read(r) & 0xFF for r in (UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)])), begin=LIVE, end=LIVE)
    if DIRECT: e.call(ROUTER, 537128156, 60, vel, 15, maxins=8_000_000)
    else: e.call(PRESS, ECS.MGR, 16, vel, maxins=8_000_000)
    log.append(("--- service",))
    for _ in range(3): e.call(SERVICE, maxins=8_000_000)
    got = list(log)
    e.call(RELEASE, ECS.MGR, 16, maxins=8_000_000)
    del e; gc.collect()
    return got


def main(img, man):
    a, b = run(img, man, 20), run(img, man, 120)
    print("vel 20 :", [x for x in a if x[0] != "dsp_w"])
    print("vel 120:", [x for x in b if x[0] != "dsp_w"])
    diff = [(x, y) for x, y in zip(a, b) if x != y]
    json.dump(dict(a=a, b=b), open(OUT, "w"))
    print("sub", "| differences:", diff if diff else "none", "| events", len(a), len(b))


if __name__ == "__main__":
    img = Path(sys.argv[1]).read_bytes()
    man = json.loads(Path(sys.argv[2]).read_text()) if len(sys.argv) > 2 and sys.argv[2] not in ("-", "--router") else None
    main(img, man)
