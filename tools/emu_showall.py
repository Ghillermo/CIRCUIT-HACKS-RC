"""Alpha 7.01 test (blackbox.use_showall): Save (LED 57) blinks violet for as long as a record waits to be read, through the real LED task.
States written into the record (its signature kept): nothing frozen, a hand capture (FROZEN | MANUAL), a skipped value (0x85, paintguard), a crash
after its restart (FROZEN | FAULT | RESET); each at 0.2 s (blink on) / 0.3 s (off) and at 60 s after the boot (60.032 s: a blink-on phase) (past the 30 s of before).
    python tools/emu_showall.py A7.01.bin manifest.json B5.65.bin manifest.json"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import blackbox as BX  # noqa: E402

STATES = {"none": 0, "hand": BX.ST_FROZEN | BX.ST_MANUAL, "skip": 0x85, "crash": BX.ST_FROZEN | BX.ST_FAULT | BX.ST_RESET}


def run(img):
    e = T.EL(img); out = {}
    import struct
    e.uc.mem_write(BX.BB, bytes(BX.SIZE)); e.uc.mem_write(BX.BB, struct.pack("<I", BX.SIG)); sig = e.r32(BX.BB)   # (the tick signs it at boot; skipped here)
    for k, st in STATES.items():
        for ms in (200, 300, 60_032):
            e.uc.mem_write(BX.BB + BX.O.ST, bytes([st])); e.at(ms)
            out[(k, ms)] = X.frame(e)[BX.LED_SAVE] & 0xFF
    del e; gc.collect()
    return out, sig


a = sys.argv[1:]; fails = 0
def check(c, m):
    global fails
    print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
new, sig = run(Path(a[0]).read_bytes()); old, _ = run(Path(a[2]).read_bytes())
V = BX.COL_SHOW
for k in ("skip", "crash"):
    check(new[(k, 200)] == V and new[(k, 300)] != V and new[(k, 60_032)] == V, f"A7.01 {k}: violet on / off, still violet at 60 s {[hex(new[(k, m)]) for m in (200, 300, 60_032)]}")
check(all(new[("none", m)] != V for m in (200, 300, 60_032)), "A7.01 nothing frozen: no violet")
check(all(new[("hand", m)] != V for m in (200, 300, 60_032)), "A7.01 hand capture: no violet")
check(old[("skip", 200)] != V and old[("crash", 200)] == V and old[("crash", 60_032)] != V, "B5.65 as before: skip dark, crash violet only for 30 s")
check(all(new[(k, m)] == old[(k, m)] for k in ("none", "hand") for m in (200, 300, 60_032)), "A7.01 = B5.65 where nothing waits")
print("A7.01 SHOWALL RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES"); sys.exit(1 if fails else 0)
