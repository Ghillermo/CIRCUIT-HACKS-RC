"""SC55.7 / Beta 5.42 tests (tools/fm8dest.py): an instrument of the 8-operator FM loaded from the pad 8 list sets the track's page 4 and its
non-sequenceable page (Shift + pad 4) to its family's destinations, through the controller (emu_inst2's path).

    python tools/emu_fm8dest.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json

  * before: the factory rows (LANE_TAB / NS_DEF); pad 8 held + pad 10 = instrument 2: its 216 parameters (as before) and its family's 8 + 8 codes
    on MIDI 1, MIDI 2's rows untouched; page 2 (Octave down) pad 9 and pad 32: theirs;
  * the previous build: the same presses leave the factory rows.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402,F401
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import fmeng as FE  # noqa: E402
import fm8 as F  # noqa: E402
import fm8arm as A  # noqa: E402
import fm8inst as FI  # noqa: E402
import make_examples as MK  # noqa: E402

MGR = X.MGR


def run(img, man):
    if not F.ALG8: F.use_alg8()
    FI.use_v2()
    vl = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
    e = X.EP(img, man)
    if not any(lo <= 0x100 < hi for lo, hi, _ in e.uc.mem_regions()): e.uc.mem_map(0, 0x4000)
    def dread(uc, a, s, d): uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, dread, begin=A.DSP_READ, end=A.DSP_READ)
    blk = A.FM8R + A.TB0
    press = lambda q: e.call(PRESS, MGR, q, 100, maxins=8_000_000)
    release = lambda q: e.call(RELEASE, MGR, q, maxins=8_000_000)
    def rows(t):
        out = []
        for fn in ("c_vrow", "c_vrow2"):
            e.call(vl[fn], t, maxins=1_000_000); out.append(tuple(e.uc.mem_read(e.uc.reg_read(UC_ARM_REG_R0), 8)))
        return tuple(out)
    e.btn(2); e.btn(8); e.pad(26); X.frame(e); e.pad(FE.ROWPAD); X.frame(e)
    r = dict(before=rows(0), other0=rows(1))
    press(FE.PADNO + 1); X.frame(e)
    press(9); release(9); X.frame(e)
    r["i1"] = (rows(0), bytes(e.uc.mem_read(blk, F.PLEN)) == FI.inst_full(1), rows(1))
    e.call(0x08033320, MGR, 19, maxins=8_000_000); e.call(0x0803381A, MGR, 19, maxins=8_000_000); X.frame(e)
    press(8); release(8); r["i24"] = (rows(0), bytes(e.uc.mem_read(blk, F.PLEN)) == FI.inst_full(24))
    press(31); release(31); r["i47"] = (rows(0), bytes(e.uc.mem_read(blk, F.PLEN)) == FI.inst_full(47))
    release(FE.PADNO + 1)
    del e; gc.collect()
    return r


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    fam = lambda i: MK.FAM_DEST[FI.INST[i]["fam"]]
    a = run(img, man)
    fac = (MK.LANE_TAB, MK.NS_DEF)
    check(a["before"] == fac, f"before: the factory rows {a['before']}")
    check(a["i1"][1] and a["i1"][0] == fam(1), f"pad 10: {FI.INST[1]['name']} ({FI.INST[1]['fam']}): its parameters, rows {a['i1'][0]}")
    check(a["i1"][2] == a["other0"], "MIDI 2's rows untouched")
    check(a["i24"][1] and a["i24"][0] == fam(24), f"page 2 pad 9: {FI.INST[24]['name']} ({FI.INST[24]['fam']}): rows {a['i24'][0]}")
    check(a["i47"][1] and a["i47"][0] == fam(47), f"page 2 pad 32: {FI.INST[47]['name']} ({FI.INST[47]['fam']}): rows {a['i47'][0]}")
    b = run(prev, pman)
    check(b["i1"][1] and b["i47"][0] == fac, f"the previous build: the instruments load, the rows stay the factory ones {b['i47'][0]}")
    print(f"{man.get('marker', '?')} FM8DEST RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    P = [Path(x) for x in sys.argv[1:5]]
    sys.exit(1 if main(P[0].read_bytes(), json.loads(P[1].read_text()), P[2].read_bytes(), json.loads(P[3].read_text())) else 0)
