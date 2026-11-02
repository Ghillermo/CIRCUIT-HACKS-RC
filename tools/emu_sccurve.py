"""SC50.6 / Beta 5.9 / RC4.07: the Sidechain view's knob LEDs, through the controller and the LED task: each preset of a note track and of a drum shows its four values
with the curve v x v / 128 (brightness + 2 in the high byte), and the old build shows them plain.

    python tools/emu_sccurve.py NEW.bin NEW_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc40_1 as T  # noqa: E402

BTN_DOWN = 19


def leds(e):
    e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, T.MGR, T.STOP | 1)); e.uc.reg_write(T.UC_ARM_REG_R4, T.MGR)
    e.call(0x08033B3E, maxins=8_000_000)
    return list(struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(T.MGR + 0x90)), 138))))[60:64]


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    curve = (lambda v: v * v >> 7) if "--plain" not in sys.argv else (lambda v: v)
    e = T.T8.E8(img, man); e.setup(man)
    e.set_p0(e.r32(T.MGR + 0xC), 1); e.btn(15); e.set_p0(e.r32(T.MGR + 0xC), 0)
    seen = []
    for p in range(8):
        e.pad(16 + p); e.rel(16 + p)
        v = [e.get(i) for i in range(27, 31)]; l = leds(e); seen.append(tuple(x >> 8 for x in l))
        check([x >> 8 for x in l] == [curve(x) + 2 for x in v], f"Synth 1, preset {p}: {v} -> {[hex(x) for x in l]}")
    check(len(set(seen)) == 8, f"eight different sets of LEDs ({len(set(seen))})")
    k4 = [s[3] for s in seen[1:]]; k2 = [s[1] for s in seen[1:]]
    if "--plain" not in sys.argv: check(max(k4) >= 2 * min(k4) and max(k2) >= 3 * min(k2), f"the presets stand apart: K2 {k2}, K4 {k4}")
    e.btn(20); e.btn(20)                                                                # the drums' pages
    e.pad(16 + 2); e.rel(16 + 2); a = leds(e); e.pad(16 + 6); e.rel(16 + 6); b = leds(e)
    check(a != b, f"a drum's page: its presets change the LEDs ({[hex(x) for x in a]}, {[hex(x) for x in b]})")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} SCCURVE RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(bytearray(Path(sys.argv[1]).read_bytes()), json.loads(Path(sys.argv[2]).read_text())) else 0)
