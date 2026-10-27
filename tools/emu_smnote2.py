"""SC48 ARM tests (smnote.use_v2): the sample picker's auto-added note seen by the stock at once, and the Note view's note + flip colour.  MIDI 1
in the sample mode, through the controller and the real LED task (the transport stopped all along):
  * the picker: step 4 held + a sample = the flip and the note (SC47.9's behaviour);
  * back to the Note view (no Play): step 4 = smpick's peach (a note with a flip), at once; a step with a note and no flip = the stock's 0x13;
    a flip without a note = the stock's empty colour (only the picker shows it).

    python tools/emu_smnote2.py SC48.bin SC48_manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402
import smpick as SP  # noqa: E402
import smnote as SN  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402

EMPTY = bytes([0, 0, 0, 0]) + bytes([0, 0, 0, 0x60]) * 6


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]; V = T4.V
    e = X.EP(Path(img).read_bytes(), man)
    sl = {k: int(v, 16) for k, v in R["smpick"]["labels"].items()}
    nl = {k: int(v, 16) for k, v in R["smnote"]["labels"].items()}
    def skip(uc, a, s, d): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    for f in (SP.REC_ON, SP.REC_OFF): e.uc.hook_add(UC_HOOK_CODE, skip, begin=f, end=f)
    lane = lambda step: e.r0(sl["c_splb"], 0, step)
    rec = lambda step: e.r0(nl["c_snrec"], 0, step)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    for _ in range(10): e.at(e.t + 40); e.call(e.vl["c_vtick"], maxins=3_000_000)
    e.btn(2); e.btn(8)
    if "modesel" in R: e.pad(26); e.pad(16 + 5); e.pad(26)
    for _ in range(3):
        if e.r8(X.MGR + SP.S_CUR) == SP.PICK[0]: break
        e.btn(9)
    for s in range(16):
        e.uc.mem_write(lane(s), b"\xff" * 6); e.uc.mem_write(rec(s), EMPTY)
    e.uc.mem_write(rec(9), bytes([1, 0, 0, 0, 60, 6, 0, 100]))                      # a note alone
    e.uc.mem_write(lane(10), bytes([0x85]) * 6)                                      # a flip alone
    e.call(PRESS, X.MGR, 3, 100, maxins=8_000_000); e.pad(16 + 2); e.call(RELEASE, X.MGR, 3, maxins=8_000_000)
    check(e.r8(rec(3)) == 1 and e.r8(lane(3)) == 0x82, f"the picker: step 4 held + sample 3 = the flip and a note ({e.r8(rec(3))}, {e.r8(lane(3)):#x})")
    for _ in range(3):
        if e.r8(X.MGR + SP.S_CUR) == SN.NV_CUR[0]: break
        e.btn(9)
    f = X.frame(e)
    check(e.r8(X.MGR + SP.S_CUR) == SN.NV_CUR[0] and f[3] & 0xFF == SP.COL_FLIP,
          f"the Note view, no Play: step 4 peach (a note with a flip) ({e.r8(X.MGR + SP.S_CUR)}, {f[3]:#x})")
    check(f[9] & 0xFF == SN.NV_NOTE and f[10] & 0xFF == f[11] & 0xFF and f[10] & 0xFF != SN.NV_NOTE,
          f"a note alone: the stock's {SN.NV_NOTE:#x} ({f[9]:#x}); a flip alone: empty like step 12 ({f[10]:#x}, {f[11]:#x})")
    del e; gc.collect()
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text())) else 0)
