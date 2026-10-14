"""SC41.2 ARM tests: patchain.use_rulecheck: the rule of a track or a pattern outside 0..7 is «none» (0) instead of an address past the RAM.

    python tools/emu_sc41_2.py SC41.2.bin SC41.2_manifest.json SC41.1.bin SC41.1_manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc40_8 as T8  # noqa: E402
import patchain as PC  # noqa: E402


def rules(img, man):
    LP = {k: int(v, 16) for k, v in man["report"]["patchain"]["labels"].items()}
    e = T8.E8(img, man, LP)
    out = {}
    for t, p in ((0, 0), (3, 7), (4, 0), (7, 7), (7, 0x84), (8, 0), (0, 8), (0xFF, 3)):
        e.call(LP["c_pcrule"], t, p); out[(t, p)] = e.uc.reg_read(UC_ARM_REG_R0)
    rec = e.rec
    del e; gc.collect()
    return out, rec


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    r, rec = rules(img, man); gc.collect(); p, _ = rules(prev, prev_man)
    good = all(r[k] == rec + PC.rule_offset(*k) for k in ((0, 0), (3, 7), (4, 0), (7, 7)))
    check(good and all(r[k] == 0 for k in ((7, 0x84), (8, 0), (0, 8), (0xFF, 3))),
          f"c_pcrule: the address of the rule for tracks / patterns 0..7, 0 outside ({hex(r[(7, 0x84)])}); the previous build: {hex(p[(7, 0x84)])}")
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
