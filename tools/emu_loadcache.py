"""SC55.6 / Beta 5.41 / RC4.11 / RC4.11S tests (tools/loadcache.py): an own-synth patch saved into a slot and loaded again, the new build against the
previous one; the card behind mpatch's mp_io answered from a Python bank image (the body after the heads: mp_io + 4).
  * the load reads the card twice (the slot's padding and its FM area; once in the RCs, without the 8-operator FM), the previous build many times;
  * the sound after the load the same in both (codes 1..34, our RAM MXR..+0x2300, the FM block when the build has one);
  * a read outside the two areas during the load still goes to the card; after the load nothing is served from the copy (ON cleared).

    python tools/emu_loadcache.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6,
                               UC_ARM_REG_R7, UC_ARM_REG_PC, UC_ARM_REG_SP, UC_ARM_REG_LR)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402,F401
import packio as PK  # noqa: E402
import modmx as MX  # noqa: E402
import loadcache as LC  # noqa: E402


def run(img, man):
    R = man["report"]
    ml = {k: int(v, 16) for k, v in R["mpatch"]["labels"].items()}
    vl = {k: int(v, 16) for k, v in R["vcf20"]["labels"].items()}
    e = T.EL(img)
    banks = {}
    io = {"r": 0, "w": 0, "log": []}
    def body(uc, a, s, d):                                         # mp_io + 4: sp already - 32; r4 = read / write, r5.. not yet set
        r0, r1, r2, r3, r4 = (uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4))
        b = banks.setdefault(r0, bytearray(b"\xFF" * 8192))
        if (r4 & ~1) == PK.READ:
            io["r"] += 1; io["log"].append((r0, r1, r3)); uc.mem_write(r2, bytes(b[r1:r1 + r3]))
        else:
            io["w"] += 1; b[r1:r1 + r3] = uc.mem_read(r2, r3)
        sp = uc.reg_read(UC_ARM_REG_SP) + 32
        regs = struct.unpack("<5I", uc.mem_read(sp, 20))
        for rg, v in zip((UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7), regs[:4]): uc.reg_write(rg, v)
        uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_R1, r3); uc.reg_write(UC_ARM_REG_SP, sp + 20); uc.reg_write(UC_ARM_REG_PC, regs[4])
    e.uc.hook_add(UC_HOOK_CODE, body, begin=ml["mp_io"] + 4, end=ml["mp_io"] + 4)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: (uc.reg_write(UC_ARM_REG_R0, 8192), uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)),
                  begin=0x0803CB6A, end=0x0803CB6A)                 # the bank's size
    e.at(100000); e.btn(2); e.btn(8)
    fm = None
    if "fm8" in R and "fmeng" in R:
        import fmeng as FE, fm8arm as A, fm8inst as FI
        e.pad(26); e.pad(FE.ROWPAD); e.pad(26)
        fm = A.FM8R + A.TB0
        e.uc.mem_write(fm, FI.inst_full(3)); e.uc.mem_write(fm + A.B_DIRTY, b"\x01")
    for k in range(8): e.call(0x08033848, T.MGR, k, 5 + 3 * k, maxins=8_000_000)
    snap = lambda: (bytes(e.uc.mem_read(MX.MXR, 0x2300)), [e.r8(e.r0(vl["c_vvaddr"], 0, c)) if hasattr(e, "r0") else 0 for c in range(1, 35)],
                    bytes(e.uc.mem_read(fm, 216)) if fm else b"")
    e.call(ml["c_mpsave"], 0, 1, maxins=40_000_000)
    want = snap()
    if fm:
        e.uc.mem_write(fm, FI.inst_full(0)); e.uc.mem_write(fm + A.B_DIRTY, b"\x01")
    for k in range(8): e.call(0x08033848, T.MGR, k, -9, maxins=8_000_000)
    io["r"] = 0; io["log"].clear()
    e.call(ml["c_mpload"], 0, 1, maxins=40_000_000)
    got = snap(); reads = io["r"]; log = list(io["log"])
    on = int.from_bytes(e.uc.mem_read(LC.RAM, 4), "little") if "loadcache" in R else 0
    io["r"] = 0; e.call(ml["c_mpr"], 0, LC.EXT0 + 512, 0x20048000, 16, maxins=2_000_000); after = io["r"]
    del e; gc.collect()
    return dict(reads=reads, log=log, got=got, want=want, on=on, after=after)


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    T.EL.r0 = lambda self, fn, *a: (self.call(fn, *a, maxins=4_000_000), self.uc.reg_read(UC_ARM_REG_R0))[1]
    a, b = run(img, man), run(prev, pman)
    print(f"      reads in the load: new {a['reads']} {a['log']}\n      previous {b['reads']} {b['log']}")
    n = 2 if "fm8" in man["report"] else 1
    check(a["reads"] == n and b["reads"] > 2, f"the load reads the card {n} time(s) (previous build: {b['reads']})")
    same = a["got"] == b["got"]
    check(same, "the sound after the load is the same as the previous build's (our RAM, codes 1..34, the FM block)")
    if not same:
        for i, (x, y) in enumerate(zip(a["got"][0], b["got"][0])):
            if x != y: print(f"        MXR + {i:#x}: new {x:#x} previous {y:#x}"); break
        print("        codes", a["got"][1] == b["got"][1], "fm", a["got"][2] == b["got"][2])
    check(a["got"][2] == a["want"][2] and a["got"][1] == a["want"][1], "the load brings back what was saved (codes, FM)")
    check(a["on"] == 0 and a["after"] == 1, f"after the load: the copy off ({a['on']:#x}), a read of the slot's FM area goes to the card ({a['after']})")
    print(f"{man.get('marker', '?')} LOADCACHE RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    A_ = [Path(x) for x in sys.argv[1:5]]
    sys.exit(1 if main(A_[0].read_bytes(), json.loads(A_[1].read_text()), A_[2].read_bytes(), json.loads(A_[3].read_text())) else 0)
