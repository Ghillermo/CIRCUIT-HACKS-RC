"""SC48 ARM tests (build_sc17.use_fsqdef): the FX step sequencer's empty bottom-row slots play their default effect.  c_fsqfx called with the
Master FX block (r4), the sequencer's request (c_fxsq) stubbed:
  * slot 2 (pad 28) empty, asked: effect 2 (the top pad of its column, Digitise) on, no slot copy loaded; the previous build: nothing;
  * slot 0 assigned the Gater with its knobs: effect 0 (as before);
  * the random value (bit 6) with every slot empty: one of the five defaults (or pad 31's Glitch);
  * c_slotcol(2) = the colour of effect 2 (the previous build: dim white 0x03).

    python tools/emu_fsqdef.py SC48.bin SC48_manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R4, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import build_sc17 as B  # noqa: E402


def run(img, man):
    e = X.EP(Path(img).read_bytes(), man)
    L = {k: int(v, 16) for k, v in man["report"]["sc17"]["labels"].items()}
    want = [0]
    def stub(uc, a, s, d): uc.reg_write(UC_ARM_REG_R0, want[0]); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, stub, begin=L["c_fxsq"], end=L["c_fxsq"])
    loads = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: loads.append(1), begin=L["c_sload"], end=L["c_sload"])
    gf = e.r0(L["c_gfst"])
    e.uc.mem_write(gf + B.S_SLOT, bytes(4 * 7))                                        # every slot empty
    def ask(mask):
        want[0] = mask; loads.clear(); e.uc.reg_write(UC_ARM_REG_R4, gf)
        return e.r0(L["c_fsqfx"]) & 0x7F, len(loads)
    o = dict(empty=ask(1 << 2), col=e.r0(L["c_slotcol"], 2))
    rnd = [ask(0x40 | (sd << 8))[0] for sd in (0, 60, 120, 200, 250)]
    o["rand"] = rnd
    e.uc.mem_write(gf + B.S_SLOT, bytes([0x0A, 0x14, 0x1E, 0xA8]))                     # slot 0: the Gater (effect 0) with its knobs
    o["gater"] = ask(1)
    del e; gc.collect()
    return o


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    o = run(img, man)
    pal = [x for x in man["report"]["sc17"].get("pal_codes", [])] or None
    check(o["empty"] == (1 << 2, 0), f"slot 2 empty, asked: effect 2 (Digitise) on, no slot copy loaded ({o['empty']})")
    check(o["gater"][0] == 1, f"slot 0 assigned the Gater: effect 0 ({o['gater']})")
    check(all(r and (r & (r - 1)) == 0 and (r & 0x5F or r == 0x40) for r in o["rand"]), f"the random value, every slot empty: one default each time ({[hex(r) for r in o['rand']]})")
    check(o["col"] not in (0x03, 0), f"c_slotcol(2): the default effect's colour ({o['col']:#x})")
    if prev:
        p = run(prev, pman)
        check(p["empty"][0] == 0 and p["col"] == 0x03, f"the previous build: an empty slot plays nothing, dim white ({p['empty']}, {p['col']:#x})")
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text()), *([a[2], json.loads(Path(a[3]).read_text())] if len(a) > 3 else [])) else 0)
