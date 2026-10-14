"""SC40D ARM test (live RAM dump; the LED task from its caller, the stock content API on emu_sc35's model of the SD card): the write after a project
save (tools/fxdiag.py).

    python tools/emu_sc40d.py SC40D.bin SC40D_manifest.json
  * the bl to the stock save (0x0802FE5E) goes to c_fdsave, which goes on to the hook that was there (the save still runs, with its r0);
  * nothing is written at once, nor in the frames of the first second; then one frame writes: the record 64 + project of the loaded pack is created
    (0xFF up to its padding), its padding = the mark (count 1, the project, the pack) + 0xFF, read back; the Save LED green for ~3 s, then as before;
  * a second save: the count is 2, nothing else of the bank changes; the bank of the own-synth patches (records 0..63) is never touched;
  * a bank that already holds synth patches at that record: its 340 bytes untouched; a read that fails: the Save LED red;
  * the buffer's lock balanced.
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc39_6 as T6  # noqa: E402
from emu_sc35 import MGR, PK  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R4
from emu_sc05 import STOP  # noqa: E402
from emu_sc35 import TICK  # noqa: E402
import fxdiag as FD  # noqa: E402

B = 0x08010000


def mark(count, proj, pack):
    a = FD.MARK + bytes([count, proj, pack, 0xA5]); return a + bytes(x ^ 0xFF for x in a)


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["fxdiag"]["labels"].items()}
    from thumb import bl
    check(bytes(img[FD.SAVE_CALL - B:FD.SAVE_CALL - B + 4]) == bl(FD.SAVE_CALL, L["c_fdsave"]) and all(bytes(img[c - B:c - B + 4]) == bl(c, L["c_fdledtask"]) for c in PK.LED_CALLS),
          f"the hooks: the bl to the save (in front of {man['report']['fxdiag']['prev']['save']}), the two LED task calls")
    e = T6.E6(img, man); e.setup(man)
    def led(dt=0):
        e.ms += dt; e.w32(TICK, e.ms)
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR)
        e.call(0x08033B3E, maxins=20_000_000)
        return struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138)))[FD.LED_SAVE]
    e.call(0x0803542C, e.r32(FD.PROJ_OBJ + 0x20), 8); proj = e.r8(e.uc.reg_read(UC_ARM_REG_R0)) & 63
    rec = 64 + proj; bank, slot = rec >> 3, rec & 7
    own = bytes((i * 7) & 0xFF for i in range(4096)); e.sd = {(3, 0, 0xFF): own}
    idle = led()
    wr = lambda: [(c[1][1], c[2], c[3]) for c in e.api if c[0] == "write"]
    e.api.clear(); e.saves.clear(); e.call(L["c_fdsave"], 0x1234, maxins=3_000_000)
    check(e.saves == [0x1234] and wr() == [], f"a project save: the stock's save runs with its r0 ({[hex(x) for x in e.saves]}), nothing written by us yet")
    a = [led(100) for _ in range(8)]
    check(wr() == [] and all(x == idle for x in a), "the frames of the first 0.8 s: nothing written, the Save LED as it was")
    b_ = led(400)
    f = e.sd.get((3, bank, 0xFF), b"")
    want = bytes([0xFF]) * (512 * slot + 340) + mark(1, proj, 31) + bytes([0xFF]) * 156
    check(f == want and e.lock == 0 and e.sd[(3, 0, 0xFF)] == own, f"a second later: record {rec} (bank {bank}) created with 0xFF, its padding = the mark (count 1, project {proj}, pack 31); the lock balanced; bank 0 untouched ({wr()})")
    c = [led(256) for _ in range(3)]; d = [led(300) for _ in range(12)]
    check(led() == FD.COL_OK or all(x == FD.COL_OK for x in c) and d[-1] == idle, f"the Save LED green for a while ({[hex(x) for x in c]}), then as before ({hex(d[-1])})")
    e.api.clear(); e.call(L["c_fdsave"], 0x55, maxins=3_000_000); led(1200); f2 = e.sd[(3, bank, 0xFF)]
    check(f2 == want[:512 * slot + 340] + mark(2, proj, 31) + bytes([0xFF]) * 156 and len(wr()) == 1, f"the second save of the project: the count is 2, one write of the padding only ({wr()})")
    for _ in range(14): led(300)
    full = bytes((i * 3 + 1) & 0x7F for i in range(4096)); e.sd[(3, bank, 0xFF)] = full
    e.api.clear(); e.call(L["c_fdsave"], 0x66, maxins=3_000_000); led(1200); f3 = e.sd[(3, bank, 0xFF)]; o = 512 * slot + 340
    check(f3[:o] == full[:o] and f3[o:o + 16] == mark(1, proj, 31) and f3[o + 172:] == full[o + 172:], "a bank that holds synth patches there: only the padding of that record changes")
    for _ in range(14): led(300)
    e.api.clear(); e.call(L["c_fdsave"], 0x77, maxins=3_000_000)
    for _ in range(4): led(100)
    e.fail_read = ((3, bank, 31), o)                                              # the read of the mark that is there fails: a new count; the read-back is the next one
    led(1200); x1 = led(100)
    e.api.clear(); e.call(L["c_fdsave"], 0x78, maxins=3_000_000); led(0)
    orig_sd = dict(e.sd)
    class Drop(dict):
        def __setitem__(s, k, v): pass
    e.sd = Drop(orig_sd)                                                          # the card keeps nothing: the read-back differs
    led(1200); x2 = led(100)
    check(x2 == FD.COL_BAD, f"a write the card does not keep: the Save LED red ({hex(x2)}; after a failed first read {hex(x1)})")
    print("SC40D ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
