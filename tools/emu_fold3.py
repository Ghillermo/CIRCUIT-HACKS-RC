"""Alpha 7.20 test (scpat.use_srcshare): c_spsrc0..3 give the stock DSP write (0x080292F8) the same arguments as before.  For each of two
images (A = before, B = with the option), after the same boot: 50 seeds of random bytes in scpat's RAM, then each c_spsrc<t>(0, value, address):
the arguments that reach 0x080292F8 and every RAM byte changed, compared.

    python tools/emu_fold3.py firmware/a7.19 firmware/a7.20
"""
import gc, json, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
import emu_sc48_8 as S
import scpat as SP

LO, HI = 0x20000000, 0x20050000


def runs(d):
    d = Path(d)
    img, man = next(d.glob("*.bin")).read_bytes(), json.loads((d / "manifest.json").read_text())
    L = {k: int(v, 16) for k, v in man["report"]["scpat"]["labels"].items()}
    e = S.ET(img, man); uc = e.uc
    got = []
    def at_w(u, ad, sz, ud): got.append((u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1), u.reg_read(UC_ARM_REG_R2))); u.emu_stop()
    uc.hook_add(UC_HOOK_CODE, at_w, begin=SP.DSP_W, end=SP.DSP_W)
    base = bytes(uc.mem_read(LO, HI - LO)); out = []
    lo_ram = min(v for k, v in vars(SP).items() if k.isupper() and isinstance(v, int) and 0x20040000 <= v < 0x20050000)
    for seed in range(50):
        rnd = random.Random(seed)
        uc.mem_write(LO, base)
        uc.mem_write(lo_ram, bytes(rnd.randrange(256) for _ in range(64)))
        for t in range(4):
            got.clear(); a = bytes(uc.mem_read(LO, HI - LO))
            e.call(L[f"c_spsrc{t}"], 0, rnd.randrange(1 << 16) << 8, 0x99 + rnd.randrange(64), maxins=200_000)
            b = bytes(uc.mem_read(LO, HI - LO))
            out.append((tuple(got), tuple((i, b[i]) for i in range(len(a)) if a[i] != b[i])))
    del e; gc.collect()
    return out


def main(a):
    A, B = runs(a[0]), runs(a[1])
    bad = [k for k in range(len(A)) if A[k] != B[k]]
    reach = sum(1 for x in A if x[0])
    print(("ok  : " if not bad and reach else "FAIL: ") + f"c_spsrc0..3: the same DSP writes and RAM in both over {len(A)} calls ({reach} reached the write)" + (f"; differ {bad[:8]}" if bad else ""))
    print("FOLD3 RESULT:", "ALL PASS" if not bad and reach else "FAILURES")
    return 1 if bad or not reach else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
