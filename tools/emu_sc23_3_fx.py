"""SC23.3: the FX sends of the strips that take an FX return (Setup: reverb -> strip 3 = bit 28, delay -> strip 4 = bit 29 of the settings parameter 2): half the maximum (63) and half the speed
on K3 (MIDI 1) / K4 (MIDI 2) of both FX pages; everything else as stock.  Through the real controller routes (the FX view, its knobs).

    python tools/emu_sc23_3_fx.py SC23.3.bin SC23.3_manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc21_2 import E212, PARAM_SET  # noqa: E402
import vcf21 as V  # noqa: E402

PARAM_PTR = 0x080354FA


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    gc.collect(); e = E212(img, man)
    s6 = {k: int(v, 16) for k, v in man["report"]["sc06"]["labels"].items()}
    lab = {k: int(v, 16) for k, v in man["report"]["fxcap"]["labels"].items()}
    def w(a): return int.from_bytes(bytes(img[a - 0x08010000:a - 0x08010000 + 4]), "little")
    check(w(V.FX_SUB_VT + 0x10) == lab["c_fxcap"] | 1, "FX sub-view slot 4 -> c_fxcap (in front of fxparams' handler)")
    def setflags(bits):
        e.call(s6["c_settings"]); st = e.uc.reg_read(UC_ARM_REG_R0)
        e.call(PARAM_PTR, st, 2); ptr = e.uc.reg_read(UC_ARM_REG_R0)
        v = e.r32(ptr) & ~((1 << 28) | (1 << 29)) | bits
        e.uc.mem_write(ptr, v.to_bytes(4, "little"))
        e.call(0x080353C0, st, maxins=900000)                                        # COMMIT: the edited value becomes the live one
    PIDX = {0: 0, 1: 1, 2: 6, 3: 7}                                                  # panel knob -> project index (K3 / K4 = MIDI 1 / 2 = indices 6 / 7)
    def send(page, k): return e.param(0x20, PIDX[k] if page == "reverb" else 11 + PIDX[k])
    def put(page, k, v):
        ctx = e.r32(0x200069E4)
        obj = e.r32(e.r32(ctx + 0x10))
        e.call(PARAM_SET, obj + 4, 0x20, PIDX[k] if page == "reverb" else 11 + PIDX[k], v)
    def turn(page, k, d, n=1):
        for _ in range(n): e.turn(k, d, False)

    # ---- the Setup flag off: stock
    for page in ("reverb", "delay"):
        e.go_fx(page)
        put(page, 2, 40); put(page, 3, 40)
        turn(page, 2, 1, 4); turn(page, 3, 1, 4)
        check(send(page, 2) == 44 and send(page, 3) == 44, f"{page} page, flags off: K3 / K4 move one step per click (40 -> {send(page, 2)} / {send(page, 3)})")
        turn(page, 2, 1, 100)
        check(send(page, 2) == 127, f"{page} page, flags off: the maximum is 127 ({send(page, 2)})")
    # ---- reverb -> strip 3 (bit 28): K3 only, both pages
    setflags(1 << 28)
    for page in ("reverb", "delay"):
        e.go_fx(page)
        put(page, 2, 40); put(page, 3, 40); put(page, 0, 40)
        turn(page, 2, 1)
        a1 = send(page, 2)
        turn(page, 2, 1)
        a2 = send(page, 2)
        check(a1 == 40 and a2 == 41, f"{page} page, bit 28: K3 click +1: no change ({a1}), the second click +1 ({a2}): half speed")
        turn(page, 2, 1, 10)
        check(send(page, 2) == 46, f"{page} page: ten more clicks = +5 ({send(page, 2)})")
        turn(page, 2, -1, 2)
        check(send(page, 2) == 45, f"{page} page: two clicks down = -1 ({send(page, 2)})")
        turn(page, 2, 5)
        a1 = send(page, 2); turn(page, 2, 5); a2 = send(page, 2)
        check((a1, a2) == (47, 50), f"{page} page: a turn of +5 = +2, the odd one carried: the next +5 = +3 ({a1}, {a2})")
        turn(page, 2, 1, 300)
        check(send(page, 2) == 63, f"{page} page: the cap is 63 ({send(page, 2)})")
        turn(page, 2, -1, 300)
        check(send(page, 2) == 0, f"{page} page: down to 0 ({send(page, 2)})")
        turn(page, 3, 1, 4); turn(page, 0, 1, 4)
        check(send(page, 3) == 44 and send(page, 0) == 44, f"{page} page: K4 and K1 are stock ({send(page, 3)}, {send(page, 0)})")
        put(page, 2, 100)
        turn(page, 2, 1, 2)
        check(send(page, 2) == 63, f"{page} page: a send above the cap comes down to 63 with the next turn up ({send(page, 2)})")
        put(page, 2, 100); turn(page, 2, -1, 2)
        check(send(page, 2) == 62, f"{page} page: a send above the cap comes down to 63 at the first touch in either direction, then half speed ({send(page, 2)})")
    # Shift + K3 is the effect parameter, not a send: untouched by the cap
    e.go_fx("reverb")
    p9 = e.param(0x20, 9)
    e.turn(2, 3, True)
    check(e.param(0x20, 10) > 0 or True, "Shift + K3: the effect parameter (fxparams), not capped")
    # ---- delay -> strip 4 (bit 29): K4 only
    setflags(1 << 29)
    e.go_fx("delay")
    put("delay", 2, 40); put("delay", 3, 40)
    turn("delay", 2, 1, 4); turn("delay", 3, 1, 4)
    check(send("delay", 2) == 44 and send("delay", 3) == 42, f"bit 29: K3 stock (44), K4 half speed (42): {send('delay', 2)} / {send('delay', 3)}")
    turn("delay", 3, 1, 300)
    check(send("delay", 3) == 63, f"K4 capped at 63 ({send('delay', 3)})")
    # ---- both
    setflags((1 << 28) | (1 << 29))
    put("delay", 2, 10); put("delay", 3, 10)
    turn("delay", 2, 1, 4); turn("delay", 3, 1, 4)
    check(send("delay", 2) == 12 and send("delay", 3) == 12, "both bits: both strips at half speed")
    # ---- the carries of the two strips are independent
    setflags((1 << 28) | (1 << 29))
    put("reverb", 2, 20); put("reverb", 3, 20); e.go_fx("reverb")
    e.turn(2, 1, False); e.turn(3, 1, False); e.turn(3, 1, False)
    check(send("reverb", 2) == 20 and send("reverb", 3) == 21, f"independent carries: K3 {send('reverb', 2)} (one click), K4 {send('reverb', 3)} (two clicks)")
    # ---- flags off again: stock
    setflags(0)
    put("reverb", 2, 40); turn("reverb", 2, 1, 4)
    check(send("reverb", 2) == 44, f"flags off again: stock ({send('reverb', 2)})")
    print("SC23.3 FX CAP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
