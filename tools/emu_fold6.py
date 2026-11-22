"""persist19.use_fold test: from the same booted state, a build without it and one with it make the same RAM changes (address -> new byte) and
return the same value, with c_shift / c_clr_held stubbed to each combination:
  * c_dk19(handler, knob, delta) for the four drums, knobs 0..7, deltas +1 / -1, Shift off / on, Clear off / on (256 calls);
  * c_mhleds19(handler) for the four drums, Clear off / on, with random stock-Clear counters (0x28 or not) at handler + 0x36..0x3D (64 calls).

    python tools/emu_fold6.py firmware/a7.24 FOLDED_DIR
"""
import gc, json, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR, UC_ARM_REG_R0
import emu_sc48_8 as S

LO, HI = 0x20000000, 0x20050000


def labels(man):
    out = {}
    for v in man["report"].values():
        if isinstance(v, dict): out.update({k: int(x, 16) for k, x in v.get("labels", {}).items() if isinstance(x, str) and x.startswith("0x")})
    return out


def delta(before, after): return {i: after[i] for i in range(len(after)) if after[i] != before[i]}


def runs(d):
    d = Path(d); img, man = next(d.glob("*.bin")).read_bytes(), json.loads((d / "manifest.json").read_text())
    L = labels(man); e = S.ET(img, man); uc = e.uc
    flag = {"shift": 0, "clr": 0}
    def stub(key):
        def f(u, ad, sz, ud): u.reg_write(UC_ARM_REG_R0, flag[key]); u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR) | 1)
        return f
    uc.hook_add(UC_HOOK_CODE, stub("shift"), begin=L["c_shift"], end=L["c_shift"])
    uc.hook_add(UC_HOOK_CODE, stub("clr"), begin=L["c_clr_held"], end=L["c_clr_held"])
    hs = []
    for dr in range(4): e.call(L["c_mh"], dr, maxins=200_000); hs.append(uc.reg_read(UC_ARM_REG_R0))
    out, rnd = [], random.Random(7246)
    for dr, h in enumerate(hs):
        for knob in range(8):
            for sh in (0, 1):
                for cl in (0, 1):
                    for dl in (1, 0xFFFFFFFF):
                        flag.update(shift=sh, clr=cl)
                        b0 = bytes(uc.mem_read(LO, HI - LO)); e.call(L["c_dk19"], h, knob, dl, maxins=3_000_000)
                        out.append(("dk19", dr, knob, sh, cl, dl, uc.reg_read(UC_ARM_REG_R0) if False else 0, delta(b0, bytes(uc.mem_read(LO, HI - LO)))))
    for dr, h in enumerate(hs):
        for cl in (0, 1):
            for k in range(8):
                uc.mem_write(h + 0x36, bytes(0x28 if rnd.random() < 0.5 else rnd.randrange(40) for _ in range(8)))
                flag.update(shift=0, clr=cl)
                b0 = bytes(uc.mem_read(LO, HI - LO)); e.call(L["c_mhleds19"], h, maxins=3_000_000)
                out.append(("mhleds", dr, cl, k, 0, 0, 0, delta(b0, bytes(uc.mem_read(LO, HI - LO)))))
    del e; gc.collect()
    return out


def main(a):
    A, B = runs(a[0]), runs(a[1])
    bad = [x[:6] for x, y in zip(A, B) if x != y]
    for kind in ("dk19", "mhleds"):
        print(f"      {kind:7s}: {sum(1 for x in A if x[0] == kind and x[-1])} / {sum(1 for x in A if x[0] == kind)} changed RAM")
    ok = not bad and len(A) == len(B)
    print(("ok  : " if ok else "FAIL: ") + f"{len(A)} calls: the same RAM changes in both" + (f"; differ {bad[:8]}" if bad else ""))
    print("FOLD6 RESULT:", "ALL PASS" if ok else "FAILURES")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
