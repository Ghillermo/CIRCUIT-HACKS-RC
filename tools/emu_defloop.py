"""Alpha 7.19 test (vcf21.use_defloop): the default values written by loops over t_def must leave exactly the same RAM as the unrolled code of
the build before.  For each of two images (A = before, B = with use_defloop), from the same booted state:
  * the own synth's first use: c_vtick with the boot bit off and the tail's flags / signature cleared, stopped at vt_run (both tracks' values,
    the second oscillator's volatile values, the notes);
  * c_vreset(0) and c_vreset(1) with every value dirtied first, stopped at c_vsave's entry;
every byte of the ARM RAM each run changes is compared between the two images.

    python tools/emu_defloop.py firmware/a7.18 firmware/a7.19
"""
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn import UC_HOOK_CODE
import emu_sc48_8 as S
import vcf21 as V

LO, HI = 0x20000000, 0x20050000


def runs(d):
    d = Path(d)
    img, man = next(d.glob("*.bin")).read_bytes(), json.loads((d / "manifest.json").read_text())
    R = man["report"]; L = {k: int(v, 16) for k, v in R["vcf20"]["labels"].items()}
    gfst = int(R["sc17"]["labels"]["c_gfst"], 16)
    e = S.ET(img, man); uc = e.uc
    from unicorn.arm_const import UC_ARM_REG_R0
    stop_at = {}
    def stopper(u, ad, sz, ud):
        if ad in stop_at: u.emu_stop()
    for lab in ("vt_run", "c_vsave"): uc.hook_add(UC_HOOK_CODE, stopper, begin=L[lab], end=L[lab])
    e.call(gfst, maxins=200_000); blk = uc.reg_read(UC_ARM_REG_R0)
    def snap(): return bytes(uc.mem_read(LO, HI - LO))
    def diff(a, b): return {LO + i: b[i] for i in range(len(a)) if a[i] != b[i]}
    out = {}
    # the first use
    fl = e.r8(blk + V.FLAGS_BYTE); uc.mem_write(blk + V.FLAGS_BYTE, bytes([fl & ~V.B_BOOT]))
    uc.mem_write(V.TAIL + V.O_FLAGS, bytes([0])); uc.mem_write(V.TAIL + V.O_SIG, bytes([0]))
    for i in range(1, 60): uc.mem_write(V.TAIL + i, bytes([0x5A]))                     # garbage in the values, so every write shows
    a = snap(); stop_at.clear(); stop_at[L["vt_run"]] = 1
    e.call(L["c_vtick"], maxins=2_000_000)
    out["first use"] = diff(a, snap())
    for t in (0, 1):
        for i in range(1, 60): uc.mem_write(V.TAIL + i, bytes([0x33]))
        uc.mem_write(blk + V.V2_OFF, bytes([0x44] * 16))
        a = snap(); stop_at.clear(); stop_at[L["c_vsave"]] = 1
        e.call(L["c_vreset"], t, maxins=2_000_000)
        out[f"c_vreset({t})"] = diff(a, snap())
    del e; gc.collect()
    return out


def main(a):
    A, B = runs(a[0]), runs(a[1])
    fails = 0
    for k in A:
        same = A[k] == B[k]
        print(("ok  : " if same else "FAIL: ") + f"{k}: {len(A[k])} bytes changed in each" + ("" if same else
              f" (A only {sorted(hex(x) for x in set(A[k]) - set(B[k]))[:8]}, B only {sorted(hex(x) for x in set(B[k]) - set(A[k]))[:8]}, differ "
              f"{[(hex(x), A[k][x], B[k][x]) for x in set(A[k]) & set(B[k]) if A[k][x] != B[k][x]][:8]})"))
        fails += 0 if same else 1
        if not A[k]: print("FAIL: nothing written"); fails += 1
    print("DEFLOOP RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:]) else 0)
