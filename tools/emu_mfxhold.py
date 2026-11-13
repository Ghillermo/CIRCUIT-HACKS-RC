"""SC57.1 / Beta 5.56 test (mfxhold; the user, 2026-11-12: «master fx view should be able to be held and drop back to previous view»): in the Mixer,
Mixer tapped = Master FX kept (as before); Mixer held >= 0.5 s = Master FX until the release, then the Mixer; in Master FX, Mixer held = the Mixer until
the release, then Master FX.  Through the controller (0x08033320 / 0x0803381A).  The previous build (if given): held = kept like a tap.

    python tools/emu_mfxhold.py BUILD.bin manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc48_8 as S  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import jumpseq as J  # noqa: E402
import build_sc17 as S17  # noqa: E402

MGR = S.MGR


def run(img_path, man):
    img = Path(img_path).read_bytes()
    e = S.ET(img, man); R = man["report"]
    gfst = int(R["sc17"]["labels"]["c_gfst"], 16)
    t = [500000]
    def at(ms): t[0] += ms; e.w32(J.HAL_TICK, t[0])
    def drain():
        r = e.r32(0x200069F4)
        for k in range(e.r8(r + 0x18)): e.uc.mem_write(e.r32(e.r32(e.r32(r + 0x14) + 4 * k) + 0x10), bytes(4))
    def press(b): drain(); e.call(0x08033320, MGR, b, maxins=20_000_000)
    def release(b): drain(); e.call(0x0803381A, MGR, b, maxins=20_000_000)
    def mode():
        e.call(gfst); g = e.uc.reg_read(UC_ARM_REG_R0)
        return e.r8(g + S17.S_MODE)
    def mixer(): return e.r32(MGR + 0x6C) != 0 and e.r32(e.r32(MGR + 0x6C)) == S17.MIX2["MIX_VT"]
    def hold(b, ms):
        press(b); X.frame(e); during = (mixer(), mode())
        for _ in range(ms // 10): at(10); X.frame(e)
        release(b); at(10); X.frame(e)
        return during, (mixer(), mode())
    out = {}
    at(0)
    press(0); release(0); X.frame(e)
    out["enter"] = hold(14, 50)                      # from Synth 1: the Mixer
    out["tap"] = hold(14, 100)                       # tap in the Mixer: Master FX kept
    out["tap2"] = hold(14, 100)                      # tap in Master FX: the Mixer kept
    out["held"] = hold(14, 700)                      # held in the Mixer: Master FX while held, then the Mixer
    out["tapon"] = hold(14, 100)                     # Master FX again (tap)
    out["held2"] = hold(14, 700)                     # held in Master FX: the Mixer while held, then Master FX
    del e; gc.collect()
    return out


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    r = run(img, man)
    check(r["enter"][1] == (True, 0), f"Mixer from Synth 1: the Mixer ({r['enter']})")
    check(r["tap"][1] == (True, 1) and r["tap2"][1] == (True, 0), f"taps: Master FX kept, then the Mixer kept ({r['tap']}, {r['tap2']})")
    check(r["held"] == ((True, 1), (True, 0)), f"held 0.7 s in the Mixer: Master FX while held, the Mixer after ({r['held']})")
    check(r["tapon"][1] == (True, 1), f"a tap: Master FX ({r['tapon']})")
    check(r["held2"] == ((True, 0), (True, 1)), f"held 0.7 s in Master FX: the Mixer while held, Master FX after ({r['held2']})")
    if prev:
        p = run(prev, pman)
        check(p["held"][1] == (True, 1), f"the previous build: held = kept like a tap ({p['held']})")
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text()), a[2] if len(a) > 2 else None,
                       json.loads(Path(a[3]).read_text()) if len(a) > 3 else None) else 0)
