"""Alpha 7.23 test (vcf21.use_fold2): c_ednum (r0 = LED buffer, r1 = value, r2 = colour) and c_edclean (r0 = view) leave the same RAM as the
unrolled code of the build before, for 40 values and both, from the same booted state.

    python tools/emu_fold4.py firmware/a7.22 firmware/a7.23
"""
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR
import emu_sc48_8 as S
import vcf21 as V

LO, HI = 0x20000000, 0x20050000
BUF = 0x2006E800


def runs(d):
    d = Path(d); img, man = next(d.glob("*.bin")).read_bytes(), json.loads((d / "manifest.json").read_text())
    L = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
    e = S.ET(img, man); uc = e.uc
    def ret(u, ad, sz, ud): u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR) | 1)
    uc.hook_add(UC_HOOK_CODE, ret, begin=V.T_DRAW, end=V.T_DRAW)                   # the stock redraw: not part of the fold
    out = []
    for v in list(range(0, 200, 5)):
        uc.mem_write(BUF, bytes([0x5A]) * 128); e.call(L["c_ednum"], BUF, v, 0x32, maxins=400_000); out.append(bytes(uc.mem_read(BUF, 128)))
    obj = 0x2006EA00; uc.mem_write(obj, bytes(16)); uc.mem_write(obj + 4, (obj + 8).to_bytes(4, "little")); uc.mem_write(obj + 8, BUF.to_bytes(4, "little"))
    uc.mem_write(BUF, bytes([0x5A]) * 128); e.call(L["c_edclean"], obj, maxins=400_000); out.append(bytes(uc.mem_read(BUF, 128)))
    del e; gc.collect()
    return out


def main(a):
    A, B = runs(a[0]), runs(a[1])
    bad = [k for k in range(len(A)) if A[k] != B[k]]
    print(("ok  : " if not bad else "FAIL: ") + f"c_ednum (40 values) and c_edclean: the same LED buffer in both" + (f"; differ {bad}" if bad else ""))
    print("FOLD4 RESULT:", "ALL PASS" if not bad else "FAILURES")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
