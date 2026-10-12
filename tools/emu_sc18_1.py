"""SC18.1 ARM tests (besides emu_sc18.py, which covers the knobs with the SC18.1 map): Master FX pad 7 jump mode, pad 8 also
clearing the song pointer, and the dark rows 1-2 of the chromatic drum Preset view.

    python tools/emu_sc18_1.py SC17.8.bin SC18.1.bin SC18.1_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc17_7 import E7, ENGINE  # noqa: E402
import build_sc17 as B  # noqa: E402
from emu_sc08 import E8, VIEWS, MGR  # noqa: E402

JF, JT = B.GFX_OFF + B.S_JF, B.GFX_OFF + B.S_JT


def main(prev, img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]
    pal = [(int(x, 16), int(y, 16)) for x, y in rep["sc17"]["pal_codes"]]
    base_c, head_c, start_c, end_c = B.SP_COLORS(pal)
    jstate = lambda e: (e.s14b(JF), e.s14b(JT))

    # ---- pad 7: hold = jump mode, Shift + pad 7 = sticky toggle; LED
    e = E7(img, man); e.grid()
    check(jstate(e) == (0, 0) and e.gleds()[6] == base_c, "power-up: jump mode off, pad 7 dim")
    c = e.pad(6); check(jstate(e) == (1, 0) and c == [] and e.gleds()[6] == head_c, "hold pad 7: jump mode on (momentary), pad 7 bright, no stock press")
    e.rel(6); check(jstate(e) == (0, 0) and e.gleds()[6] == base_c, "release pad 7: off")
    e.pad(6, shift=True); e.rel(6); check(jstate(e) == (2, 0), "Shift + pad 7: sticky on (release keeps it)")
    e.pad(6); check(jstate(e) == (3, 0), "pad 7 held on top of sticky")
    e.rel(6); check(jstate(e) == (2, 0), "released: still sticky")
    e.pad(6, shift=True); e.rel(6); check(jstate(e) == (0, 0), "Shift + pad 7 again: sticky off")
    # ---- jump mode: a step pad = target of the next step, the ranges are left alone
    e.setsp(ls=5, le=12)
    e.pad(6); c = e.pad(e.step_pad(9)); e.rel(e.step_pad(9)); e.rel(6)
    check(jstate(e) == (0, 9) and e.sp() == (5, 12, 0, 0) and c == [], f"jump mode + step 9: target 9, start / end untouched {jstate(e)} {e.sp()}")
    e.uc.mem_write(e.s14 + JT, b"\x00"); e.setsp()
    e.pad(e.step_pad(3)); check(jstate(e)[1] == 0 and e.sp() == (0, 0, 3, 0), "without jump mode a step is the normal song pointer")
    e.rel(e.step_pad(3))

    # ---- the tick executes the jump at the next step start
    def run(start, target, count, ls=0, le=0):
        gc.collect()
        x = E7(img, man); x.set_ticks(start); x.setsp(ls=ls, le=le)
        x.uc.mem_write(x.s14 + JT, bytes([target]))
        return x, x.tick(count)
    x, seq = run(20, 9, 20)
    check(seq[:3] == [21, 22, 23] and seq[3] == 48 and seq[4] == 49 and x.s14b(JT) == 0 and x.sets == [47],
          f"tick 20 (step 4), target 9: 21, 22, 23, then step 9 = tick 48 at the next step start {seq[:6]} {x.sets}")
    x, seq = run(96 * 2 + 70, 3, 10)
    check(seq[1] == 96 * 2 + 12 and x.sets == [96 * 2 + 11], f"in a later cycle the jump stays in it (target 3 -> {96 * 2 + 12}) {seq[:4]}")
    x, seq = run(10, 1, 6)
    check(seq[1] == B.SP_BIG and x.sets == [B.SP_BIG - 1], f"target step 1 in cycle 0 (tick 0 would need -1): aligned tick {B.SP_BIG} {seq[:3]}")
    x = E7(img, man); x.set_ticks(23); x.setsp(); x.uc.mem_write(x.s14 + JT, bytes([16]))
    try: x.tick(2)
    except Exception: pass                    # the stock tick at steps 13-16 reads pattern data the RAM dump lacks (emulation only)
    check(x.sets == [89], f"tick 23 -> the jump is set on the very next tick (24 = step 5 start -> step 16 = tick 90) {x.sets}")
    x, seq = run(20, 6, 60, ls=4, le=8)
    jumps = [i for i in range(1, len(seq)) if seq[i] != seq[i - 1] + 1]
    check(seq[3] == 30 and x.s14b(JT) == 0 and len(x.sets) >= 2, f"a jump inside a loop range: done once, then the loop goes on ({[seq[j] for j in jumps][:4]})")
    # ---- pad 8 also clears the song pointer and the jump mode
    e = E7(img, man); e.grid()
    e.setsp(ls=5, le=12, h1=0, h2=0); e.uc.mem_write(e.s14 + JF, bytes([2, 7]))
    check(e.gleds()[7] == B.CLR_ON, "pad 8 lit while a song pointer range is set")
    e.pad(7); e.rel(7)
    check(e.sp() == (0, 0, 0, 0) and jstate(e) == (0, 0) and e.gleds()[7] == B.CLR_DIM, f"pad 8: song pointer and jump mode off {e.sp()} {jstate(e)}")
    e.setsp(h1=4, h2=9); e.pad(7); e.rel(7); check(e.sp() == (0, 0, 0, 0), "pad 8 also drops held steps")

    # ---- chromatic / scale drum Preset view: rows 1-2 dark, rows 3-4 as SC17.8
    for d in range(4):
        rows = {}
        for name, image in (("prev", prev), ("new", img)):
            gc.collect()
            x = E8(image)
            for v in VIEWS: x.uc.mem_write(v + 0x51, b"\x00\x00\x00")
            x.setflag(VIEWS[d], True)
            x.call(x.r32(x.r32(VIEWS[d]) + 0x1C), VIEWS[d], maxins=900000); p = x.uc.reg_read(UC_ARM_REG_R0)
            rows[name] = list(struct.unpack("<32H", bytes(x.uc.mem_read(p, 64))))
        check(rows["new"][:16] == [0] * 16 and rows["new"][16:] == rows["prev"][16:] and any(rows["prev"][:16]),
              f"drum {d+1} chromatic view: rows 1-2 off, rows 3-4 as before")
        gc.collect()
        x = E8(img)
        for v in VIEWS: x.uc.mem_write(v + 0x51, b"\x00\x00\x00")
        y = E8(prev)
        for v in VIEWS: y.uc.mem_write(v + 0x51, b"\x00\x00\x00")
        a = [z.call(z.r32(z.r32(VIEWS[d]) + 0x1C), VIEWS[d], maxins=900000) or list(struct.unpack("<32H", bytes(z.uc.mem_read(z.uc.reg_read(UC_ARM_REG_R0), 64)))) for z in (x, y)]
        check(a[0] == a[1], f"drum {d+1} normal Preset view: LEDs as SC17.8")
    print("SC18.1 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes(), json.loads(Path(sys.argv[3]).read_text())) else 0)
