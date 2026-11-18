"""Alpha 7.03 ARM test (srcview / build_sc15 use_nosrc): in the synth source view (Synth 1 pressed in its track view) pads 25-29 are dark and do
nothing (no mode stored, the Audio In group not resent); Alpha 7.02: the same pads light and set the mode.  The real controller routes.

    python tools/emu_nosrc.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc19_1 as T  # noqa: E402


def run(img, man):
    e = T.E191(img, man)
    e.btn(0)
    out = dict(open=bool(e.flag()), leds=e.pleds(T.VIEWS[0])[24:29], pads=[])
    for p in range(24, 29):
        c = e.padr(p)
        out["pads"].append((c, e.modes(), (0x20, 48) in e.mark))
    out["leds2"] = e.pleds(T.VIEWS[0])[24:29]
    out["still"] = bool(e.flag())
    return out


def main(a):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    n = run(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())); gc.collect()
    o = run(Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text())); gc.collect()
    check(n["open"] and n["still"], "Synth 1 pressed in its track view: the source view opens and stays open while pads 25-29 are pressed")
    check(n["leds"] == [0] * 5 and n["leds2"] == [0] * 5, f"pads 25-29 dark ({n['leds']}, after the presses {n['leds2']})")
    check(all(c == [] and m == [0, 0] and not mk for c, m, mk in n["pads"]), f"pads 25-29: nothing (no stock press, modes 0, no resend) {n['pads']}")
    check(any(o["leds"]) and any(m != [0, 0] for c, m, mk in o["pads"]), f"(Alpha 7.02: lit {o['leds']}, modes {[m for c, m, mk in o['pads']]})")
    print("NOSRC RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:]) else 0)
