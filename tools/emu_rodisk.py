"""SC41.3 / RC0.9 ARM tests: the pack of the internal memory is read-only for the mod (tools/rodisk.py).

    python tools/emu_rodisk.py NEW.bin NEW_manifest.json PREVIOUS.bin PREVIOUS_manifest.json
  * the stock's write (0x0803CC16) and delete (0x0803CC34) begin with a branch to the guards, their first 4 bytes kept in them;
  * called from the mod's area (a stub placed there): an item of pack 0, or of 0xFF while pack 0 is loaded, fails (0xFFFFFFFD) and the stock code
    is not reached; an item of a card pack (3, 31), or of 0xFF while a card pack is loaded, reaches the stock code; reads are never stopped;
  * after a refusal the Save LED is red, 1.5 s later it is not;
  * the previous build: every call reaches the stock code;
  * RC2S (rodisk.use_allpacks, the label ro_all): every item of every pack refused.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R4
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import MGR  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
from emu_sc08 import E8  # noqa: E402
import rodisk as RD  # noqa: E402
from thumb import bl as tbl, b_w  # noqa: E402

B = 0x08010000
STUB = 0x0807E000                                             # (in the mod's area; inside the largest images, but never called there by the test)


def run(img, man):
    e = E8(img)
    reached = []
    def hit(uc, a, s_, d):
        reached.append(a); uc.emu_stop()
    for fn in (RD.WRITE + 4, RD.DELETE + 4):
        e.uc.hook_add(UC_HOOK_CODE, hit, begin=fn, end=fn)
    cur = e.r32(RD.CUR_PACK)
    out = {}
    for name, fn in (("write", RD.WRITE), ("delete", RD.DELETE)):
        stub = b"\x00\xb5" + tbl(STUB + 2, fn) + b"\x00\xbd"
        e.uc.mem_write(STUB, stub)
        for loaded, pk in ((0, 0), (5, 0), (0, 0xFF), (5, 0xFF), (5, 3), (0, 31)):
            e.uc.mem_write(cur, bytes([loaded])); e.uc.mem_write(0x2006E100, struct.pack("<IIB", 2, 1, pk))
            reached.clear(); e.uc.reg_write(UC_ARM_REG_R0, 0)
            try: e.call(STUB, 0x2006E100, 0, 0x2006E200, 16, maxins=200_000)
            except Exception: pass
            out[(name, loaded, pk)] = ("stock" if reached else "refused", e.uc.reg_read(UC_ARM_REG_R0) & 0xFFFFFFFF)
    def led():
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR); e.call(0x08033B3E, maxins=40_000_000)
        return struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138)))[RD.LED_SAVE]
    rec = e.r32(RD.SESSION_OBJ + 0x14); t = e.r32(rec + RD.TAIL + RD.T_OFF) if rec else 0
    e.w32(RD.HAL_TICK, t + 100); l1 = led(); e.w32(RD.HAL_TICK, t + 2000); l2 = led()
    del e; gc.collect()
    return out, (t, l1, l2)


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["rodisk"]["labels"].items()}
    at = lambda a, n: bytes(img[a - B:a - B + n])
    check(at(RD.WRITE, 4) == b_w(RD.WRITE, L["c_rowr"]) and at(RD.DELETE, 4) == b_w(RD.DELETE, L["c_rodel"]),
          "the stock's write and delete begin with a branch to the guards")
    o, (t, l1, l2) = run(img, man)
    allp = "ro_all" in L                                                                       # RC2S (rodisk.use_allpacks): every pack refused
    want = {(0, 0): "refused", (5, 0): "refused", (0, 0xFF): "refused", (5, 0xFF): "stock", (5, 3): "stock", (0, 31): "stock"}
    if allp: want = {k: "refused" for k in want}
    for name in ("write", "delete"):
        got = {k[1:]: v[0] for k, v in o.items() if k[0] == name}
        fail_code = all(v[1] == RD.FAIL for k, v in o.items() if k[0] == name and v[0] == "refused")
        check(got == want and fail_code, (f"the mod's {name}: every pack refused with 0xFFFFFFFD (RC2S) ({got})" if allp else
                                          f"the mod's {name}: pack 0, or 0xFF with pack 0 loaded, refused with 0xFFFFFFFD; a card pack reaches the stock ({got})"))
    check(t != 0 and l1 == RD.COL_NO and l2 != RD.COL_NO, f"a refusal: the Save LED red ({l1:#x}), 1.5 s later not ({l2:#x})")
    gc.collect(); p, _ = run(prev, prev_man)
    check(all(v[0] == "stock" for v in p.values()), "the previous build: every call reaches the stock code")
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
