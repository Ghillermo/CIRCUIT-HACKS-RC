"""Alpha 7.19 test (build_sc17.use_fold): c_slotbits (the slot tests as a loop) and c_f_leds (the palette chain as a table) give the same results
as the unrolled code of the build before.  For each of two images (A = before, B = with use_fold), after the same boot: 200 seeds of random
bytes in the Master FX block (c_gfst) and the view word, then c_slotbits (r4 = the block) and c_f_leds (r0 = the FX view): their r0 and the
LED buffer / every byte of the ARM RAM each call changes, compared between the two images.

    python tools/emu_fold.py firmware/a7.18 firmware/a7.19
"""
import gc, json, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R4
import emu_sc48_8 as S

LO, HI = 0x20000000, 0x20050000
BLK_N = 236                                            # the Master FX block's bytes
FXV = 0x200443B4
SEEDS = 200


def runs(d):
    d = Path(d)
    img, man = next(d.glob("*.bin")).read_bytes(), json.loads((d / "manifest.json").read_text())
    Ls = {k: int(v, 16) for k, v in man["report"]["sc17"]["labels"].items()}
    e = S.ET(img, man); uc = e.uc
    e.call(Ls["c_gfst"], maxins=200_000); blk = uc.reg_read(UC_ARM_REG_R0)
    base = bytes(uc.mem_read(LO, HI - LO))
    out = []
    for seed in range(SEEDS):
        rnd = random.Random(seed)
        uc.mem_write(LO, base)
        uc.mem_write(blk, bytes(rnd.randrange(256) for _ in range(BLK_N)))
        uc.mem_write(S.MGR + 0x6C, (FXV if rnd.random() < 0.5 else 0x200447D4).to_bytes(4, "little"))
        a = bytes(uc.mem_read(LO, HI - LO))
        uc.reg_write(UC_ARM_REG_R4, blk); e.call(Ls["c_slotbits"], maxins=2_000_000); r_sb = uc.reg_read(UC_ARM_REG_R0)
        b = bytes(uc.mem_read(LO, HI - LO))
        d1 = tuple((LO + i, b[i]) for i in range(len(a)) if a[i] != b[i])
        e.call(Ls["c_f_leds"], FXV, maxins=4_000_000); buf = uc.reg_read(UC_ARM_REG_R0)
        c = bytes(uc.mem_read(LO, HI - LO))
        d2 = tuple((LO + i, c[i]) for i in range(len(b)) if b[i] != c[i])
        leds = bytes(uc.mem_read(buf, 84)) if LO <= buf < HI else b""
        out.append((r_sb & 0xFF, d1, buf, leds, d2))
    del e; gc.collect()
    return out


def main(a):
    A, B = runs(a[0]), runs(a[1])
    bad = [s for s in range(SEEDS) if A[s] != B[s]]
    used = sum(1 for s in range(SEEDS) if A[s][0])
    lit = sum(1 for s in range(SEEDS) if A[s][3] and any(A[s][3]))
    print(("ok  : " if not bad else "FAIL: ") + f"c_slotbits and c_f_leds the same in both images over {SEEDS} seeds ({used} with slot bits, {lit} with LEDs)"
          + ("" if not bad else f"; differ at seeds {bad[:10]}"))
    if bad:
        s = bad[0]; print("  A", A[s][0], len(A[s][1]), hex(A[s][2]), A[s][3].hex()[:80]); print("  B", B[s][0], len(B[s][1]), hex(B[s][2]), B[s][3].hex()[:80])
    ok2 = used > 20 and lit > 20
    print(("ok  : " if ok2 else "FAIL: ") + "the seeds reach both paths")
    print("FOLD RESULT:", "ALL PASS" if not bad and ok2 else "FAILURES")
    return 1 if bad or not ok2 else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
