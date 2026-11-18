"""Alpha 7.04 / RC4.16 (sclear2): Clear + a scene pad also resets the scene's chain mode / repeats in patchain's tail (sum kept valid) and, with
patmut, the scene's bytes 34..39; scene 2's are kept.  Through the controller and the Mixer's own pad handler (as emu_scnclear.py).

    python tools/emu_sclear2.py firmware/a7.04 firmware/r416 [firmware/a7.03 (before: kept)]"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR, UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc17_6
emu_sc17_6.MIX_PRESS = -1
from emu_sc40_5 import EC  # noqa: E402
from emu_sc35 import MGR  # noqa: E402
import patchain as PC  # noqa: E402

SESSION_OBJ = 0x2003D71C


def run(d):
    d = Path(d); img = next(d.glob("*.bin")).read_bytes(); man = json.loads((d / "manifest.json").read_text()); R = man["report"]
    L = {k: int(v, 16) for k, v in R["patchain"]["labels"].items()}
    e = EC(img, man, L)
    if "xlanes" in R:
        xpv = {k: int(v, 16) for k, v in R["xlanes"]["prev"].items()}
        for k in ("load", "new"):
            e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, dd: uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1), begin=xpv[k], end=xpv[k])
    if "scrules" in R:
        import scrules as SR
        e.uc.mem_write(SR.RB, bytes(SR.O_SCW + 16 * 32)); e.uc.mem_write(SR.RB, b"SCR3")
    e.st(); e.persistent(); e.clear_state(); e.live(0xFF)
    t = e.tail
    for s in (0, 1): e.uc.mem_write(t + PC.P_FLAGS + s, bytes([1])); e.uc.mem_write(t + PC.P_REPS + s, bytes([3]))
    e.call(L["c_pcsum"], t)
    rec = e.r32(SESSION_OBJ + 0x14)
    pm = "patmut" in R
    if pm:
        for s in (0, 1): e.uc.mem_write(rec + 0x40 + 40 * s + 34, bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66]))
    press = lambda i: e.call(0x08033320, MGR, i, maxins=8_000_000)
    release = lambda i: e.call(0x0803381A, MGR, i, maxins=8_000_000)
    pad = lambda q: (e.call(0x08033282, MGR, q, 100, maxins=8_000_000), e.call(0x080332FE, MGR, q, maxins=8_000_000))
    held = lambda v: e.uc.mem_write(e.ptr(e.r32(e.r32(MGR + 0x20) + 0xC), 0), bytes([v]))
    press(14); release(14)
    held(1); pad(16); held(0)                                                       # Clear + scene 1
    fl = [e.r8(t + PC.P_FLAGS + s) for s in (0, 1)]; rp = [e.r8(t + PC.P_REPS + s) for s in (0, 1)]
    e.call(L["c_pcvalid"], t); valid = e.uc.reg_read(UC_ARM_REG_R0)
    pmb = [bytes(e.uc.mem_read(rec + 0x40 + 40 * s + 34, 6)) for s in (0, 1)] if pm else None
    del e; gc.collect()
    return dict(fl=fl, rp=rp, valid=valid, pm=pmb, sc2="sclear2" in R)


def main(dirs):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    for d in dirs:
        r = run(d); print("==", d, r)
        if r["sc2"]:
            check(r["fl"][0] == (0 if PC.V3 or True else 0xFF) and r["rp"][0] == 1, f"scene 1: chain mode {r['fl'][0]}, repeats {r['rp'][0]} (reset)")
            check(r["fl"][1] == 1 and r["rp"][1] == 3, "scene 2: kept")
            check(r["valid"] == 1, "the tail's sum still valid")
            if r["pm"]: check(r["pm"][0] == bytes(6) and r["pm"][1] == bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66]), f"patmut: scene 1's bytes 0, scene 2's kept {r['pm']}")
        else:
            check(r["fl"][0] == 1 and r["rp"][0] == 3, f"(before: scene 1 kept its mode / repeats {r['fl'][0]} / {r['rp'][0]})")
    print("SCLEAR2 RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:]) else 0)
