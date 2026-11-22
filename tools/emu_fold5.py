"""Alpha 7.24 test (build_sc17.use_fold2, drumstore.use_fold): from the same booted state, the build before and the folded one make the same
RAM changes (address -> new byte, so code addresses kept in RAM do not count) and return the same value:
  * c_fsqfx (r4 = the Master FX block) for 64 slot masks from c_fxsq (stubbed), with random slot / Glitch-knob bytes in the block;
  * c_rlsync (rollers) and c_dasync (drumarp) for the four drums and all 32 steps, with random words in the pattern's raw arrays;
  * c_gleds and c_s_leds (c_gact stubbed to the block) for 32 random held / latched / selected states, then the LED buffers compared;
  * c_thon (throw) for 8 levels, the mark cleared each time; c_mxst (modmx) from a clobbered signature.

    python tools/emu_fold5.py firmware/a7.23 firmware/a7.24
"""
import gc, json, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR, UC_ARM_REG_R0, UC_ARM_REG_R4
import emu_sc48_8 as S
import drumstore as D

LO, HI = 0x20000000, 0x20050000


def lab(man, mod, name): return int(man["report"][mod]["labels"][name], 16)


def delta(before, after):
    return {i: after[i] for i in range(len(after)) if after[i] != before[i]}


def runs(d):
    d = Path(d); img, man = next(d.glob("*.bin")).read_bytes(), json.loads((d / "manifest.json").read_text())
    e = S.ET(img, man); uc = e.uc
    out = []
    # ---- c_fsqfx
    fxsq, fsqfx, gfst = lab(man, "sc17", "c_fxsq"), lab(man, "sc17", "c_fsqfx"), lab(man, "sc17", "c_gfst")
    mask = [0]
    def stub(u, ad, sz, ud): u.reg_write(UC_ARM_REG_R0, mask[0]); u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR) | 1)
    uc.hook_add(UC_HOOK_CODE, stub, begin=fxsq, end=fxsq)
    e.call(gfst, maxins=400_000); blk = uc.reg_read(UC_ARM_REG_R0)
    assert blk, "no Master FX block"
    rnd = random.Random(724)
    for m in range(64):
        uc.mem_write(blk + 0x90, bytes(rnd.randrange(256) for _ in range(0x30)))
        mask[0] = m | (rnd.randrange(256) << 8 if m & 0x40 else 0)
        b0 = bytes(uc.mem_read(LO, HI - LO))
        uc.reg_write(UC_ARM_REG_R4, blk); e.call(fsqfx, maxins=800_000)
        r0 = uc.reg_read(UC_ARM_REG_R0)
        out.append(("fsqfx", m, r0, delta(b0, bytes(uc.mem_read(LO, HI - LO)))))
    # ---- c_rlsync / c_dasync
    for mod, name in (("rollers", "c_rlsync"), ("drumarp", "c_dasync")):
        fn = lab(man, mod, name)
        for dr in range(4):
            st = int.from_bytes(uc.mem_read(int.from_bytes(uc.mem_read(D.PROB_VIEW0 + D.PROB_SZ * dr + 0xC, 4), "little"), 4), "little")
            base = int.from_bytes(uc.mem_read(st + 0x18, 4), "little") - 0xA8
            for step in range(32):
                uc.mem_write(base, bytes(rnd.randrange(256) for _ in range(0x80)))
                b0 = bytes(uc.mem_read(LO, HI - LO))
                e.call(fn, D.DP0 + D.DP_SZ * dr, step, base, maxins=800_000)
                out.append((name, dr, step, delta(b0, bytes(uc.mem_read(LO, HI - LO)))))
    # ---- c_gleds / c_s_leds (the Mixer's Master FX page: c_gact stubbed to return the block)
    gact = lab(man, "sc17", "c_gact")
    def gstub(u, ad, sz, ud): u.reg_write(UC_ARM_REG_R0, blk); u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR) | 1)
    uc.hook_add(UC_HOOK_CODE, gstub, begin=gact, end=gact)
    for name in ("c_gleds", "c_s_leds"):
        fn = lab(man, "sc17", name)
        for k in range(32):
            uc.mem_write(blk + 5, bytes([rnd.randrange(256), rnd.randrange(256), rnd.randrange(9)]))
            b0 = bytes(uc.mem_read(LO, HI - LO))
            e.call(fn, 0x200447D4, maxins=2_000_000)
            out.append((name, k, 0, delta(b0, bytes(uc.mem_read(LO, HI - LO)))))
    # ---- c_thon (the throw: the sends kept, then all eight at the level)
    thon = lab(man, "throw", "c_thon")
    for lv in range(0, 128, 16):
        b0 = bytes(uc.mem_read(LO, HI - LO))
        e.call(thon, lv, maxins=4_000_000)
        out.append(("thon", lv, 0, delta(b0, bytes(uc.mem_read(LO, HI - LO)))))
        uc.mem_write(LO, b0)                                                       # back to the state before (the mark too)
    # ---- c_mxst from a clobbered signature
    import modmx as M
    uc.mem_write(M.MXR, bytes(rnd.randrange(256) for _ in range(0x100)))
    b0 = bytes(uc.mem_read(LO, HI - LO)); e.call(lab(man, "modmx", "c_mxst"), maxins=400_000)
    out.append(("mxst", 0, uc.reg_read(UC_ARM_REG_R0), delta(b0, bytes(uc.mem_read(LO, HI - LO)))))
    del e; gc.collect()
    return out


def main(a):
    A, B = runs(a[0]), runs(a[1])
    bad = [x[:3] for x, y in zip(A, B) if x != y]
    n_ch = sum(1 for x in A if x[-1])
    for kind in ("fsqfx", "c_rlsync", "c_dasync", "c_gleds", "c_s_leds", "thon", "mxst"):
        print(f"      {kind:9s}: {sum(1 for x in A if x[0] == kind and x[-1])} / {sum(1 for x in A if x[0] == kind)} changed RAM")
    print(("ok  : " if not bad else "FAIL: ") + f"{len(A)} calls (c_fsqfx, c_rlsync / c_dasync, c_gleds / c_s_leds, c_thon, c_mxst), {n_ch} changed RAM: "
          "the same changes and results in both" + (f"; differ {bad[:8]}" if bad else ""))
    ok = not bad and len(A) == len(B) and n_ch > 0
    print("FOLD5 RESULT:", "ALL PASS" if ok else "FAILURES")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
