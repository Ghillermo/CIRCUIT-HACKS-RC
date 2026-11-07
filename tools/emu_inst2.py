"""SC53 / Beta 5.33 tests (fm8ui.use_inst2, fm8inst.use_v2): the FM instruments' second page, through the controller and the real LED task.

    python tools/emu_inst2.py BUILD.bin manifest.json

  * the packed table: fm8inst.unlz(lz(table)) = the 48 records;
  * pad 8 held: page 1 = the 24 in their family's colour (Octave down lit, up dark); pad 10 = instrument 2 (its longer release) unpacked from the
    ITCM, the stamp written;
  * Octave down while pad 8 is held: page 2 (Octave up lit, down dark), the 24 new ones' colours (teal winds); pad 9 = Grand Piano (24), pad 32 =
    Long Bell (47), byte for byte; its pad bright;
  * Octave up: page 1 again.
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import fmeng as FE  # noqa: E402
import fm8 as F  # noqa: E402
import fm8arm as A  # noqa: E402
import fm8inst as FI  # noqa: E402
import fm8ui as U  # noqa: E402

MGR = X.MGR


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    if not F.ALG8: F.use_alg8()
    FI.use_v2()
    t = FI.table(); p = FI.lz(t)
    check(len(FI.INST) == 48 and FI.unlz(p, len(t)) == t, f"the packed table: {len(t)} B -> {len(p)} B, unpacked the same")
    e = X.EP(img, man)
    if not any(lo <= 0x100 < lo + sz for lo, _, sz in [(r[0], r[1], r[1] - r[0] + 1) for r in e.uc.mem_regions()]):
        e.uc.mem_map(0, 0x4000)                                                     # the ITCM
    def dread(uc, a, s, d): uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, dread, begin=A.DSP_READ, end=A.DSP_READ)
    blk = A.FM8R + A.TB0
    par = lambda i: e.r8(blk + i)
    press = lambda q: e.call(PRESS, MGR, q, 100, maxins=8_000_000)
    release = lambda q: e.call(RELEASE, MGR, q, maxins=8_000_000)
    lo = lambda f, a, b: [x & 0xFF for x in f[a:b]]
    ic = FI.colours()
    e.btn(2); e.btn(8); e.pad(26); X.frame(e); e.pad(FE.ROWPAD); X.frame(e)
    check(par(A.B_ON) == 1, "FM on")
    press(FE.PADNO + 1); f = X.frame(e)
    st = par(A.B_STR)
    check(lo(f, 8, 32) == [ic[2 * j + (j != st)] for j in range(24)] and f[51] & 0xFF == 1 and f[52] & 0xFF == 0,
          f"pad 8 held: page 1, Octave down lit ({[hex(x) for x in lo(f, 8, 32)]}, {f[51]:#x}, {f[52]:#x})")
    press(9); release(9); f = X.frame(e)
    stamp = struct.unpack("<I", bytes(e.uc.mem_read(U.IT_SIG, 4)))[0]
    import zlib
    check(bytes(e.uc.mem_read(blk, F.PLEN)) == FI.inst_full(1) and stamp == zlib.crc32(p) & 0xFFFFFFFF and bytes(e.uc.mem_read(U.IT_TAB, len(t))) == t,
          f"pad 10: {FI.INST[1]['name']} (R4 of op 1 = {FI.INST[1]['ops'][0]['r'][3]}) from the ITCM, the stamp written")
    e.call(0x08033320, MGR, 19, maxins=8_000_000); e.call(0x0803381A, MGR, 19, maxins=8_000_000); f = X.frame(e)
    check(lo(f, 8, 32) == [ic[2 * (24 + j) + 1] for j in range(24)] and f[51] & 0xFF == 0 and f[52] & 0xFF == 1,
          f"Octave down: page 2, Octave up lit ({[hex(x) for x in lo(f, 8, 32)]}, {f[51]:#x}, {f[52]:#x})")
    press(8); release(8); f = X.frame(e)
    check(bytes(e.uc.mem_read(blk, F.PLEN)) == FI.inst_full(24) and par(A.B_STR) == 24 and f[8] & 0xFF == ic[48],
          f"pad 9: {FI.INST[24]['name']} ({f[8]:#x})")
    press(31); release(31)
    check(bytes(e.uc.mem_read(blk, F.PLEN)) == FI.inst_full(47), f"pad 32: {FI.INST[47]['name']}")
    e.call(0x08033320, MGR, 20, maxins=8_000_000); e.call(0x0803381A, MGR, 20, maxins=8_000_000); f = X.frame(e)
    check(lo(f, 8, 32)[0] == ic[1] and f[51] & 0xFF == 1, "Octave up: page 1 again")
    release(FE.PADNO + 1)
    print(f"{man.get('marker', '?')} INST2 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
