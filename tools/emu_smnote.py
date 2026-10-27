"""SC47.9 (tools/smnote.py): the own engine's sample picker and the notes of its steps, on the emulated firmware (MIDI 1 in the sample mode, its
picker on the screen; the pads through the controller, the frame through the real LED task call).

  * the last pressed note: MIDI 1's live note-on (0x0804B07A on its track view) with note 64 -> kept;
  * a step held + a sample: the flip and, the step being empty, a note there = 64, one step (6), velocity 100;
  * a sample held + a step: the same; a step that has a note already: its note stays;
  * the step pads: note + flip = peach, a note alone = cyan, a flip alone = violet, nothing = the dim cyan background;
  * the stock's erase of a step's notes (the Note view, a tap on a step with notes) leaves the flip in lane 8, and the picker shows it violet.

    python tools/emu_smnote.py BUILD.bin manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402
import smpick as SP  # noqa: E402
import smnote as SN  # noqa: E402
import arp as A  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402

VIEW1 = A.VIEW_IFC0 - 0x110 + 2 * A.VIEW_SZ           # MIDI 1's track view
EMPTY = bytes([0, 0, 0, 0]) + bytes([0, 0, 0, 0x60]) * 6


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]
    V = T4.V
    e = X.EP(Path(img).read_bytes(), man)
    sl = {k: int(v, 16) for k, v in R["smpick"]["labels"].items()}
    nl = {k: int(v, 16) for k, v in R["smnote"]["labels"].items()}
    def skip(uc, a, s, d): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    for f in (SP.REC_ON, SP.REC_OFF): e.uc.hook_add(UC_HOOK_CODE, skip, begin=f, end=f)
    lane = lambda step: bytes(e.uc.mem_read(e.r0(sl["c_splb"], 0, step), 6))
    rec = lambda step: e.r0(nl["c_snrec"], 0, step)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    for _ in range(10): e.at(e.t + 40); e.call(e.vl["c_vtick"], maxins=3_000_000)
    e.btn(2); e.btn(8)
    if "modesel" in R: e.pad(26); e.pad(16 + 5); e.pad(26)
    else:
        for _ in range(3): e.pad(26)
    for _ in range(3):
        if e.r8(X.MGR + SP.S_CUR) == SP.PICK[0]: break
        e.btn(9)
    check(e.r0(sl["c_spk"]) == 0, f"MIDI 1 in the sample mode, its picker on the screen (c_spk {e.r0(sl['c_spk'])})")
    for s in range(16):
        e.uc.mem_write(e.r0(sl["c_splb"], 0, s), b"\xff" * 6); e.uc.mem_write(rec(s), EMPTY)
    # ---- the last pressed note
    trk = e.r8(e.r32(VIEW1 + 0x18) + 0xC)
    e.call(SN.LIVE_ON, VIEW1, 64, 100, 0, maxins=8_000_000); e.call(0x0804AF5A, VIEW1, 0, maxins=8_000_000)
    check(trk == 2 and e.r8(SN.SNR + 4) == 64, f"MIDI 1's live note 64 kept as the last pressed (track {trk}, {e.r8(SN.SNR + 4)})")
    # ---- a step held + a sample
    e.call(PRESS, X.MGR, 3, 100, maxins=8_000_000); e.pad(16 + 2); e.call(RELEASE, X.MGR, 3, maxins=8_000_000)
    r3 = bytes(e.uc.mem_read(rec(3), 8))
    check(lane(3) == bytes([0x80 | 2]) * 6 and r3[0] == 1 and r3[4:8] == bytes([64, SN.GATE, 0, SN.VEL]),
          f"step 4 held + sample 3: the flip and a note 64 there ({lane(3).hex()}, {r3.hex()})")
    # ---- a sample held + a step; a step with a note already
    e.uc.mem_write(rec(6), bytes([1, 0, 0, 0, 70, 12, 2, 90]))
    e.call(PRESS, X.MGR, 16 + 7, 90, maxins=8_000_000)
    for p in (5, 6): e.call(PRESS, X.MGR, p, 100, maxins=8_000_000); e.call(RELEASE, X.MGR, p, maxins=8_000_000)
    e.call(RELEASE, X.MGR, 16 + 7, maxins=8_000_000)
    r5, r6 = bytes(e.uc.mem_read(rec(5), 8)), bytes(e.uc.mem_read(rec(6), 8))
    check(lane(5) == bytes([0x87]) * 6 and r5[0] == 1 and r5[4] == 64, f"sample 8 held + step 6: the flip and a note 64 ({lane(5).hex()}, {r5.hex()})")
    check(lane(6) == bytes([0x87]) * 6 and r6 == bytes([1, 0, 0, 0, 70, 12, 2, 90]), f"step 7 had a note: the flip, its note kept ({r6.hex()})")
    # ---- the step pads
    e.uc.mem_write(rec(9), bytes([1, 0, 0, 0, 60, 6, 0, 100]))                                      # a note alone
    e.uc.mem_write(e.r0(sl["c_splb"], 0, 10), bytes([0x85]) * 6)                                    # a flip alone
    f = X.frame(e)
    got = {s: f[s] & 0xFF for s in (3, 9, 10, 11)}
    check(got == {3: SP.COL_FLIP, 9: SN.COL_NOTE, 10: SN.COL_FONLY, 11: SP.COL_STEP},
          f"the step pads: note + flip peach, note cyan, flip violet, nothing dim cyan ({ {k: hex(v) for k, v in got.items()} })")
    # ---- the stock's erases in the Note view: Clear + step 4 (its notes and its lanes: the flip kept); step 7 held + its note's key (added, then erased)
    e.btn(9)
    if e.r8(X.MGR + SP.S_CUR) == SP.PICK[0]: e.btn(9)
    cur = e.r8(X.MGR + SP.S_CUR)
    clr = e.r32(e.r32(X.MGR + SP.HELD) + 0xC)
    lv = e.r0(sl["c_splb"], 0, 2); e.uc.mem_write(lv, bytes([90]) * 6)                                # level automation on step 3
    for st in (3, 2):
        e.set_p0(clr, 1); e.call(PRESS, X.MGR, st, 100, maxins=8_000_000); e.call(RELEASE, X.MGR, st, maxins=8_000_000); e.set_p0(clr, 0)
    r3b = bytes(e.uc.mem_read(rec(3), 8))
    check(r3b[0] == 0 and lane(3) == bytes([0x82]) * 6, f"the Note view, Clear + step 4: its note erased, the flip kept (view {cur}; {r3b.hex()}, {lane(3).hex()})")
    check(lane(2) == bytes([0xFF]) * 6, f"Clear + step 3: its level automation cleared as before ({lane(2).hex()})")
    e.uc.mem_write(rec(7), EMPTY); e.uc.mem_write(e.r0(sl["c_splb"], 0, 7), bytes([0x84]) * 6)
    e.call(PRESS, X.MGR, 7, 100, maxins=8_000_000)
    for _ in range(2): e.call(PRESS, X.MGR, 20, 100, maxins=8_000_000); e.call(RELEASE, X.MGR, 20, maxins=8_000_000)
    e.call(RELEASE, X.MGR, 7, maxins=8_000_000)
    r7 = bytes(e.uc.mem_read(rec(7), 8))
    check(r7[0] == 0 and lane(7) == bytes([0x84]) * 6, f"step 8 held + a key twice (a note added, then erased): the flip kept ({r7.hex()}, {lane(7).hex()})")
    for _ in range(3):
        if e.r8(X.MGR + SP.S_CUR) == SP.PICK[0]: break
        e.btn(9)
    f = X.frame(e)
    check(f[3] & 0xFF == SN.COL_FONLY, f"back in the picker: step 4 violet (a flip, no note) ({f[3] & 0xFF:#x})")
    del e; gc.collect()
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text())) else 0)
