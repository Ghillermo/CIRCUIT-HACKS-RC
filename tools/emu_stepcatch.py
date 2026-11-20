"""S715D3 tests (tools/stepcatch.py): the two sites call the traps; a play position < 32 goes straight on (the advance's bl 0x080354FA / the
listener's bl 0x0804E736, registers and LR intact, nothing recorded); >= 32 at the advance = a capture (state 0x85, tag 4, the value, r4..r11, the
caller's stack from its SP) then the stock call with r0 / r1 / LR intact and r5 & 31; a second one with the record frozen = only the clamp; >= 32
at the listener = a capture (tag 5) and back to the caller without the call.

    python tools/emu_stepcatch.py firmware/s715d3/circuittracks-4486-S715D3.bin firmware/s715d3/manifest.json
"""
import gc, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6,
                               UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_LR, UC_ARM_REG_SP, UC_ARM_REG_PC)
import emu_sc48_8 as S
import blackbox as BB
import stepcatch as SC
from emu_sc05 import STOP
from thumb import bl

REGS = (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)


def main(a):
    img, man = Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["stepcatch"]["labels"].items()}
    B = 0x08010000
    check(img[SC.ADV_SITE - B:SC.ADV_SITE - B + 4] == bl(SC.ADV_SITE, L["c_stc"]), "0x0802CE46 -> c_stc")
    check(img[SC.LST_SITE - B:SC.LST_SITE - B + 4] == bl(SC.LST_SITE, L["c_stl"]), "0x0804EB8E -> c_stl")
    e = S.ET(img, man)
    uc = e.uc
    hit = {}
    def stopper(u, addr, size, ud):
        hit["at"] = addr; hit["r"] = [u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)]
        hit["hi"] = [u.reg_read(r) for r in REGS]; hit["lr"] = u.reg_read(UC_ARM_REG_LR); hit["sp"] = u.reg_read(UC_ARM_REG_SP); u.emu_stop()
    for t in (SC.PARAM_WPTR, SC.FLAGS_SET):
        uc.hook_add(UC_HOOK_CODE, stopper, begin=t, end=t)
    SPV = 0x20047C00                                         # in RAM: c_bbcpy reads only checked RAM
    frame = bytes(range(1, 65)) + bytes(0x158 - 64)
    def run(entry, r0, r1, r5, frozen=False):
        hit.clear()
        uc.mem_write(BB.BB + BB.O.ST, bytes([BB.ST_FROZEN if frozen else 0])); uc.mem_write(BB.BB + BB.O.STK1, bytes(16))
        uc.mem_write(SPV, frame)
        for i, r in enumerate(REGS): uc.reg_write(r, 0x40 + i)
        uc.reg_write(UC_ARM_REG_R5, r5) if entry == "c_stc" else None
        uc.reg_write(UC_ARM_REG_R0, r0); uc.reg_write(UC_ARM_REG_R1, r1); uc.reg_write(UC_ARM_REG_R2, 9); uc.reg_write(UC_ARM_REG_R3, 1)
        uc.reg_write(UC_ARM_REG_SP, SPV); uc.reg_write(UC_ARM_REG_LR, STOP | 1)
        uc.emu_start(L[entry] | 1, STOP, count=2_000_000)
        if "at" not in hit:
            hit["at"] = uc.reg_read(UC_ARM_REG_PC); hit["sp"] = uc.reg_read(UC_ARM_REG_SP); hit["hi"] = [uc.reg_read(r) for r in REGS]
        return e.r8(BB.BB + BB.O.ST), bytes(uc.mem_read(BB.BB, BB.SIZE))

    base = [0x40 + i for i in range(8)]
    st, rec = run("c_stc", 0x2003BD90, 1, 7)
    check(hit.get("at") == SC.PARAM_WPTR and hit["r"][:2] == [0x2003BD90, 1] and hit["lr"] == STOP | 1 and hit["sp"] == SPV
          and hit["hi"][1] == 7 and st == 0, f"advance, step 7: straight to 0x080354FA, nothing recorded (state {st:#x})")
    st, rec = run("c_stc", 0x2003BD90, 1, 240)
    want = base[:]; want[1] = 240
    s1 = rec[BB.O.STK1:]
    tag, val = struct.unpack_from("<2I", s1)
    check(st == 0x85 and tag == 4 and val == 240 and list(struct.unpack_from("<8I", s1, 8)) == want and s1[40:40 + 64] == frame[:64],
          f"advance, step 240: captured (state {st:#x}, tag {tag}, value {val}, r4..r11, the caller's stack)")
    check(hit.get("at") == SC.PARAM_WPTR and hit["r"][:2] == [0x2003BD90, 1] and hit["lr"] == STOP | 1 and hit["sp"] == SPV and hit["hi"][1] == 16
          and [hit["hi"][i] for i in (0, 2, 3, 4, 5, 6, 7)] == [base[i] for i in (0, 2, 3, 4, 5, 6, 7)],
          f"  then 0x080354FA with r0 / r1 / LR / SP intact, r5 = {hit['hi'][1] if hit.get('hi') else None} (240 & 31)")
    d = SC.decode(rec, BB)
    check(d and d["track"] == 1 and d["new_pattern"] == 2 and d["settings_last"] == 5 and d["settings_first"] == 6, f"  decode: {d and {k: d[k] for k in ('where', 'value', 'track', 'new_pattern')}}")
    st, rec = run("c_stc", 0x2003BD90, 1, 0xF3, frozen=True)
    check(st == BB.ST_FROZEN and struct.unpack_from("<I", rec, BB.O.STK1)[0] == 0 and hit.get("at") == SC.PARAM_WPTR and hit["hi"][1] == 0x13,
          "advance with a record frozen: only the clamp (0xF3 -> 0x13)")
    st, rec = run("c_stl", 0x200433C4, 5, 0)
    check(hit.get("at") == SC.FLAGS_SET and hit["r"] == [0x200433C4, 5, 9, 1] and hit["lr"] == STOP | 1 and st == 0, "listener, step 5: straight to 0x0804E736")
    st, rec = run("c_stl", 0x200433C4, 240, 0)
    tag, val = struct.unpack_from("<2I", rec, BB.O.STK1)
    check(hit.get("at") == STOP and hit["sp"] == SPV and st == 0x85 and tag == 5 and val == 240, f"listener, step 240: captured (tag {tag}), back without the call")
    del e; gc.collect()
    print(f"{man.get('marker')} STEPCATCH RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:]) else 0)
