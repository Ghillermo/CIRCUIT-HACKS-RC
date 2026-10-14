"""SC402D ARM test (live RAM dump; the LED task from its caller): the marks in the tail of the project record (tools/taildiag.py).

    python tools/emu_sc402d.py SC402D.bin SC402D_manifest.json
  * the tail of the record in RAM (the last 1000 bytes) is zero in the dump; the Save LED as the stock's;
  * a project save: the stock's save still runs with its r0; "TAIL" + count 1 at the start of the tail, "END!" in its last four bytes, nothing
    else of the record changes; the Save LED green; a second save: count 2;
  * one mark gone: red; both gone: as the stock.
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc39_6 as T6  # noqa: E402
from emu_sc35 import MGR, PK  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_R4
from emu_sc05 import STOP  # noqa: E402
import taildiag as TD  # noqa: E402

B = 0x08010000
SIZE = 0x2740C


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["taildiag"]["labels"].items()}
    from thumb import bl
    check(bytes(img[TD.SAVE_CALL - B:TD.SAVE_CALL - B + 4]) == bl(TD.SAVE_CALL, L["c_tdsave"]) and all(bytes(img[c - B:c - B + 4]) == bl(c, L["c_tdledtask"]) for c in PK.LED_CALLS),
          "the hooks: the bl to the save, the two LED task calls")
    e = T6.E6(img, man); e.setup(man)
    def led():
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR)
        e.call(0x08033B3E, maxins=20_000_000)
        return struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138)))[TD.LED_SAVE]
    rec = e.r32(TD.SESSION_OBJ + 0x14); rd = lambda: bytes(e.uc.mem_read(rec, SIZE))
    r0 = rd(); idle = led()
    check(r0[:4] == b"USER" and set(r0[TD.TAIL:]) == {0} and len(r0) - TD.TAIL == TD.TAIL_LEN, f"the record in RAM ({rec:#x}): the last {TD.TAIL_LEN} bytes are zero; the Save LED as the stock's ({idle:#x})")
    e.saves.clear(); e.call(L["c_tdsave"], 0x1234, maxins=3_000_000); r1 = rd()
    check(e.saves == [0x1234] and r1[:TD.TAIL] == r0[:TD.TAIL] and r1[TD.TAIL:TD.TAIL + 5] == b"TAIL\x01" and r1[-4:] == b"END!" and set(r1[TD.TAIL + 5:-4]) == {0} and led() == TD.COL_OK,
          "a project save: the stock's save runs; the two marks in the tail (count 1), nothing else of the record changed; the Save LED green")
    e.call(L["c_tdsave"], 0x55, maxins=3_000_000); check(rd()[TD.TAIL + 4] == 2, "the second save: count 2")
    e.uc.mem_write(rec + SIZE - 4, bytes(4)); a = led(); e.uc.mem_write(rec + TD.TAIL, bytes(8)); b_ = led()
    check(a == TD.COL_BAD and b_ == idle, f"one mark gone: red; both gone: as the stock ({a:#x}, {b_:#x})")
    print("SC402D ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
