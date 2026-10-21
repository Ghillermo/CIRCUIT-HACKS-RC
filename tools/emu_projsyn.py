"""SC46 (tools/projsyn.py): the own synth of MIDI 1 / 2 saved with the project and restored by its load.

The emulated firmware, MIDI 1's own engine on, its knobs through the controller, the real LED task:
  * K1 of page 4 (TUNE) moved to A; the LED task gathers; the save hook (c_yssave, the stock's save skipped) writes 5 blocks into bytes 8..39 of
    MIDI 1's patterns 0..4 and 5 into MIDI 2's (0xC6, track << 4 | block), bytes 0..7 of those patterns untouched;
  * K1 moved to B (and MIDI 2's engine off); the load hook (c_ysload, the stock's rest skipped) + the LED task: TUNE = A again, MIDI 2's engine
    back on as saved; the slot cache's bytes 6 / 7 as before;
  * a project without the blocks (zeroed): the load leaves the sound (TUNE stays);
  * a damaged block (one byte changed): nothing restored;
  * before 3 s after power-up: nothing gathered.

    python tools/emu_projsyn.py SC46.bin SC46_manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
import projsyn as PS  # noqa: E402

V = T4.V
TUNE = 17


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = X.EP(Path(img).read_bytes(), man)
    e.uc.mem_write(PS.STR, bytes([0xA7] * 16))                                          # the RAM's power-up garbage
    R = man["report"]
    yl = {k: int(v, 16) for k, v in R["projsyn"]["labels"].items()}
    pv = {k: int(v, 16) for k, v in R["projsyn"]["prev"].items()}
    def skip(uc, a, s, d): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, skip, begin=pv["save"], end=pv["save"])
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: uc.emu_stop(), begin=pv["load"], end=pv["load"])
    rec = e.r32(PS.SESSION_OBJ + 0x14)
    blk = lambda t, k: rec + PS.AREA + PS.SET + (8 * t + k) * PS.PSIZE
    head0 = [bytes(e.uc.mem_read(blk(t, k), 8)) for t in range(2) for k in range(5)]
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x07]))           # MIDI 1 / 2 engines on
    on = lambda t: e.r8(V.TAIL + V.O_FLAGS) >> t & 1
    e.w32(V.HAL_TICK, 1000)
    e.btn(2); e.btn(8); e.pad(3)
    for _ in range(3): e.knob(0, 5)
    X.frame(e)
    check(e.r32(PS.STR + PS.O_SIG) == PS.STSIG and e.r8(PS.STR + PS.O_VALID) == 0, "before 3 s after power-up: the state set up, nothing gathered")
    e.w32(V.HAL_TICK, 10000); X.frame(e)
    a = e.val(0, TUNE)
    check(e.r8(PS.STR + PS.O_VALID) == 1, f"the LED task gathers (TUNE = A = {a})")
    e.call(yl["c_yssave"], maxins=2_000_000)
    hdr = [(e.r8(blk(t, k) + 8), e.r8(blk(t, k) + 9)) for t in range(2) for k in range(5)]
    check(hdr == [(PS.SIG, t << 4 | k) for t in range(2) for k in range(5)], f"the save: 10 blocks ({hdr})")
    check([bytes(e.uc.mem_read(blk(t, k), 8)) for t in range(2) for k in range(5)] == head0, "bytes 0..7 of those patterns untouched")
    saved = [bytes(e.uc.mem_read(blk(t, k), 40)) for t in range(2) for k in range(5)]
    for _ in range(4): e.knob(0, -9)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) & ~0x02 & 0xFF]))  # MIDI 2's engine off
    b = e.val(0, TUNE)
    cache = e.r0(int(R["mpatch"]["labels"]["c_mpc"], 16)); c67 = bytes(e.uc.mem_read(cache + 6, 2))
    e.call(yl["c_ysload"], maxins=2_000_000)
    e.w32(V.HAL_TICK, 20000); X.frame(e)
    check(b != a and e.val(0, TUNE) == a, f"the load: TUNE back to A ({b} -> {e.val(0, TUNE)}, A = {a})")
    check(on(1) == 1, "MIDI 2's engine back on, as saved")
    check(bytes(e.uc.mem_read(cache + 6, 2)) == c67, f"the slot cache's bytes 6 / 7 kept ({c67.hex()})")
    # a project without the blocks
    e.pad(3)
    for _ in range(4): e.knob(0, -9)
    c = e.val(0, TUNE)
    e.w32(V.HAL_TICK, 21000); X.frame(e)
    for t in range(2):
        for k in range(5): e.uc.mem_write(blk(t, k) + 8, bytes(32))
    e.call(yl["c_ysload"], maxins=2_000_000); e.w32(V.HAL_TICK, 30000); X.frame(e)
    check(c != a and e.val(0, TUNE) == c, f"a project without the blocks: the sound stays ({c} -> {e.val(0, TUNE)})")
    # a damaged block
    for i, s in enumerate(saved): e.uc.mem_write(blk(i // 5, i % 5), s)
    e.uc.mem_write(blk(0, 2) + 20, bytes([e.r8(blk(0, 2) + 20) ^ 0x10]))
    e.call(yl["c_ysload"], maxins=2_000_000); e.w32(V.HAL_TICK, 40000); X.frame(e)
    check(e.val(0, TUNE) == c, f"a damaged block: MIDI 1 not restored ({e.val(0, TUNE)})")
    del e; gc.collect()
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text())) else 0)
