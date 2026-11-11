"""SC55.8 tests (tools/tabpack.py): c_tboot, run as at power-up with the RAM / ITCM areas wiped, rebuilds every packed table byte for byte (the
same bytes the build packed and the previous build kept in its flash), then calls c_dspz with the same r0..r3 and returns its r0.

    python tools/emu_tabpack.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc05 as S  # noqa: E402
import tabpack as TP  # noqa: E402
import dspz  # noqa: E402

BASE = 0x08010000


def prev_tables(img, man):
    """the tables as the previous build keeps them in its flash: {name: bytes}"""
    out = {}
    fl = man["report"]["fm8"]["labels"]
    ts = sorted((int(v, 16), k[2:]) for k, v in fl.items() if k.startswith("t_"))
    for i, (a, k) in enumerate(ts[:-1]):
        out[k] = bytes(img[a - BASE:ts[i + 1][0] - BASE])
    return out


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    r = man["report"]
    tl = {k: int(v, 16) for k, v in r["tabpack"]["labels"].items()}
    info = r["tabpack_info"]
    e = S.E(img)
    uc = e.uc
    for lo, hi in (TP.RAM, TP.ITCM): uc.mem_write(lo, b"\xA5" * (hi - lo))
    seen = []
    def dsp(uc_, a, s, d):
        seen.append(tuple(uc_.reg_read(x) for x in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)))
        uc_.reg_write(UC_ARM_REG_R0, 0x1234); uc_.reg_write(UC_ARM_REG_PC, uc_.reg_read(UC_ARM_REG_LR) | 1)
    c_dspz = int(r["dspz"]["labels"]["c_dspz"], 16)
    uc.hook_add(UC_HOOK_CODE, dsp, begin=c_dspz, end=c_dspz)
    site = dspz.SITES[0]
    import fm8dest as FD
    check(FD.bl_target(img, site, BASE) == tl["c_tboot"], "the site calls c_tboot")
    e.call(tl["c_tboot"], 0x11, 0x22, 0x33, 0x44, maxins=5_000_000)
    check(seen == [(0x11, 0x22, 0x33, 0x44)], f"c_dspz called once with r0..r3 {seen}")
    check(uc.reg_read(UC_ARM_REG_R0) == 0x1234, "c_tboot returns c_dspz's r0")
    # the tables, from the decoded stream (Python) and from the previous build's flash
    got = {}
    i = bytes(img).find(TP.MAGIC)
    TP.decode(bytes(img[i + 8:]), lambda a, b_: got.__setitem__(a, bytes(b_)))
    ok = all(bytes(uc.mem_read(a, len(b_))) == b_ for a, b_ in got.items())
    check(ok, f"the device's decoder = the build's ({len(got)} records, {sum(len(x) for x in got.values())} B)")
    pt = prev_tables(prev, pman)
    fl = r["fm8"]["labels"]
    fm = [n for n in info["tables"] if n in pt]
    same = [n for n in fm if bytes(uc.mem_read(int(fl["t_" + n], 16), len(pt[n]))) == pt[n]]
    check(len(same) == len(fm), f"FM tables equal to the previous build's flash: {len(same)} / {len(fm)} {sorted(set(fm) - set(same))}")
    import build_sc17 as B17
    B17.SMP = True
    want = B17.tables()
    mfx = [n for n in info["tables"] if n in want]
    # the Master FX tables: found by content in RAM (their addresses are in build_sc17's code, not in the report)
    ram = bytes(uc.mem_read(TP.RAM[0], TP.RAM[1] - TP.RAM[0]))
    found = [n for n in mfx if ram.find(struct.pack("<128I", *[v & 0xFFFFFFFF for v in want[n]])) >= 0]
    check(len(found) == len(mfx), f"Master FX tables rebuilt: {found}")
    check(info["saved"] > 2000, f"saved {info['saved']} B")
    print(f"{man.get('marker', '?')} TABPACK RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    del e; gc.collect()
    return fails


if __name__ == "__main__":
    P = [Path(x) for x in sys.argv[1:5]]
    sys.exit(1 if main(P[0].read_bytes(), json.loads(P[1].read_text()), P[2].read_bytes(), json.loads(P[3].read_text())) else 0)
