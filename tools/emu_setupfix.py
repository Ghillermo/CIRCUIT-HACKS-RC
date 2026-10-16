"""SC41.5 / RC0.9.2 ARM tests: Synth 1 / Synth 2 in the Setup view (tools/setupfix.py).

    python tools/emu_setupfix.py NEW.bin NEW_manifest.json PREVIOUS.bin PREVIOUS_manifest.json
  * srcview's «second press» test reads [ctrl + 0x152] through c_sxcur;
  * the Setup view (mode 8) entered from Synth 1's / Synth 2's track view ([ctrl + 0x152] = 1 / 10): pressing Synth 1 / Synth 2 reaches the Setup
    view's button slot as that track (0 / 1), and the Setup view's chosen track follows; the previous build: as Preset (8);
  * out of the Setup view the second press of a Synth button is still a tap on Preset (srcview's source view).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R1, UC_ARM_REG_R5
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import MGR  # noqa: E402
from emu_sc08 import E8  # noqa: E402
import setupfix as SF  # noqa: E402
import pgmch as PG  # noqa: E402
from thumb import bl as tbl  # noqa: E402

B = 0x08010000
SETUP_BTN = 0x08047016                                        # the stock's button method of the Setup view (r1 = the button)
BODY = 0x08033326                                             # the stock's button handler after its prologue (r5 = the button)
PRESET = 8


def run(img):
    out = {}
    for case in ("setup0", "setup1", "normal"):                   # (one instance each: a press turned into Preset leaves the source view open)
        e = E8(img)
        ms = e.r32(MGR + PG.MODE_STORE); mode0 = e.store_p0(ms)
        got = []
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: got.append(uc.reg_read(UC_ARM_REG_R1)), begin=SETUP_BTN, end=SETUP_BTN)
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: got.append(uc.reg_read(UC_ARM_REG_R5)), begin=BODY, end=BODY)
        t = 1 if case == "setup1" else 0
        if case != "normal":
            e.uc.mem_write(PG.SETUP_OBJ + PG.ADV_OFF, b"\0\0"); e.set_p0(ms, PG.MODE_SETUP); e.w32(MGR + 0x6C, 0)
        e.uc.mem_write(MGR + SF.S_CUR, bytes([9 * t + 1]))
        e.call(0x08033320, MGR, t, maxins=8_000_000); e.call(0x0803381A, MGR, t, maxins=8_000_000)
        out[case] = sorted(set(got)); out["mode0"] = mode0
        del e; gc.collect()
    return out


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["setupfix"]["labels"].items()}
    at = SF.site(man["report"])
    check(bytes(img[at - B:at - B + 4]) == tbl(at, L["c_sxcur"]), f"srcview's second-press test reads [ctrl + 0x152] through c_sxcur ({at:#x})")
    o = run(img)
    check(o["setup0"] == [0] and o["setup1"] == [1], f"the Setup view entered from Synth 1's / Synth 2's track view: Synth 1 / 2 reach it as tracks 0 / 1 ({o['setup0']}, {o['setup1']})")
    check(o["normal"] == [PRESET], f"out of the Setup view (mode {o['mode0']}): the second press of Synth 1 is still a tap on Preset ({o['normal']})")
    gc.collect(); p = run(prev)
    check(p["setup0"] == [PRESET] and p["setup1"] == [PRESET] and p["normal"] == [PRESET], f"the previous build: as Preset ({p['setup0']}, {p['setup1']})")
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
