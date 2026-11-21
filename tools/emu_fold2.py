"""Alpha 7.19 test (vcf21.use_fold): the same results as the unrolled code of the build before.  For each of two images (A = before,
B = with use_fold), after the same boot:
  * c_vrow(0 / 1) and c_vrow2(0 / 1) with their row signatures cleared (the first fill of both rows): every RAM byte written;
  * c_vclrled(0 / 1, buffer) with Clear held (c_vclr answers 1) over 100 seeds of random marks in the knob object's + 0x40..0x47 (0x28, 0x2A or
    other): the 8 LED halfwords written.
(c_vtick's state bytes: tools/emu_defloop.py, the first use.)

    python tools/emu_fold2.py firmware/a7.18 firmware/a7.19
"""
import gc, json, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_LR, UC_ARM_REG_PC
import emu_sc48_8 as S
import p4dest

LO, HI = 0x20000000, 0x20050000
NSRAM = 0x20046B60
BUF = 0x2006E800
SEEDS = 100


def runs(d):
    d = Path(d)
    img, man = next(d.glob("*.bin")).read_bytes(), json.loads((d / "manifest.json").read_text())
    L = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
    e = S.ET(img, man); uc = e.uc
    out = {}
    snap = lambda: bytes(uc.mem_read(LO, HI - LO))
    for nm, sig in (("c_vrow", p4dest.RAM + 16), ("c_vrow2", NSRAM + 16)):
        for t in (0, 1):
            uc.mem_write(sig, bytes(4)); a = snap()
            e.call(L[nm], t, maxins=200_000); r0 = uc.reg_read(UC_ARM_REG_R0); b = snap()
            out[f"{nm}({t})"] = (r0, tuple((LO + i, b[i]) for i in range(len(a)) if a[i] != b[i]))
    def force(u, ad, sz, ud):
        u.reg_write(UC_ARM_REG_R0, 1); u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR) | 1)
    uc.hook_add(UC_HOOK_CODE, force, begin=L["c_vclr"], end=L["c_vclr"])
    for t in (0, 1):
        e.call(L["c_vobj"], t, maxins=10_000); obj = uc.reg_read(UC_ARM_REG_R0)
        res = []
        for seed in range(SEEDS):
            rnd = random.Random(seed * 2 + t)
            if obj: uc.mem_write(obj + 0x40, bytes(rnd.choice((0x28, 0x2A, rnd.randrange(256))) for _ in range(8)))
            uc.mem_write(BUF, bytes(16))
            e.call(L["c_vclrled"], t, BUF, maxins=200_000)
            res.append(bytes(uc.mem_read(BUF, 16)))
        out[f"c_vclrled({t})"] = (obj != 0, tuple(res))
    del e; gc.collect()
    return out


def main(a):
    A, B = runs(a[0]), runs(a[1])
    fails = 0
    for k in A:
        same = A[k] == B[k]
        info = f"{len(A[k][1])} bytes written" if k.startswith("c_vrow") else f"{sum(1 for x in A[k][1] if any(x))} / {SEEDS} seeds lit"
        print(("ok  : " if same else "FAIL: ") + f"{k}: the same in both ({info})")
        fails += 0 if same else 1
    print("FOLD2 RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:]) else 0)
