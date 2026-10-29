"""SC49.6 (slock.use_cue): Record held + a step = its pad yellow while held.

    python tools/emu_reccue.py BUILD.bin manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]

Through the controller and the LED task (emu_lazysave's harness), Record held, the step pad pressed (not let go), the frame read; then the pad
let go, then Record:
  * Synth 1's track view (snapall), Drum 1's Note view (snapall / lanex), MIDI 1's track view with the own engine on (recinst): the pad yellow
    (0x2D) while held, not after it is let go;
  * the pad held without Record: not yellow;
  * the previous build (if given): never yellow.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import packio as PK  # noqa: E402
import vcf21 as V  # noqa: E402

MGR = T.MGR
YELLOW = 0x2D


def run(img, man):
    R = man["report"]
    e = T.EL(Path(img).read_bytes()); e.at(300000); e.transport(0)
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    def fake_mpr(uc, a, s, d):                                           # snapall's read of the patch: macro positions 64
        uc.mem_write(uc.reg_read(UC_ARM_REG_R2), bytes([0x40]) * uc.reg_read(UC_ARM_REG_R3)); uc.reg_write(UC_ARM_REG_R0, 0); skip(uc)
    mpr = int(R["mpatch"]["labels"]["c_mpr"], 16)
    e.uc.hook_add(UC_HOOK_CODE, fake_mpr, begin=mpr, end=mpr)
    for f in (PK.BUF_LOCK, PK.BUF_UNLOCK): e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: (uc.reg_write(UC_ARM_REG_R0, 0), skip(uc)), begin=f, end=f)
    rec = lambda down: e.call(0x08033320 if down else 0x0803381A, MGR, 16, maxins=8_000_000)
    def held(pad, record=True):
        if record: rec(True)
        e.call(PRESS, MGR, pad, 100, maxins=8_000_000); during = X.frame(e)[pad]
        e.call(RELEASE, MGR, pad, maxins=8_000_000); after = X.frame(e)[pad]
        if record: rec(False)
        X.frame(e)
        return during, after, e.r8(MGR + 0x152)
    o = {}
    e.btn(0); X.frame(e)
    if e.r8(MGR + 0x152) != 1: e.btn(0); X.frame(e)
    o["synth"] = held(2)
    o["synth_plain"] = held(5, record=False)
    e.btn(4); X.frame(e)
    o["drum"] = held(4)
    o["drum_plain"] = held(6, record=False)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))   # MIDI 1's own engine on
    e.btn(2); X.frame(e)
    o["midi"] = held(3)
    del e; gc.collect()
    return o


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    o = run(img, man)
    for k, name in (("synth", "Synth 1's track view, step 3"), ("drum", "Drum 1's Note view, step 5"), ("midi", "MIDI 1's track view (engine on), step 4")):
        d, a, v = o[k]
        check(d == YELLOW and a != YELLOW, f"{name} (view {v}), Record held: yellow while held ({d:#x}), not after it is let go ({a:#x})")
    for k, name in (("synth_plain", "Synth 1, step 6"), ("drum_plain", "Drum 1, step 7")):
        check(o[k][0] != YELLOW, f"{name} held without Record: not yellow ({o[k][0]:#x})")
    if prev:
        p = run(prev, pman)
        check(all(p[k][0] != YELLOW for k in ("synth", "drum", "midi")), f"the previous build: no cue ({[hex(p[k][0]) for k in ('synth', 'drum', 'midi')]})")
    print(f"{man.get('marker', Path(img).stem)} RECCUE RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text()), a[2] if len(a) > 2 else None,
                       json.loads(Path(a[3]).read_text()) if len(a) > 3 else None) else 0)
