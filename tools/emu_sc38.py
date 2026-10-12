"""SC38 ARM tests (live RAM dump, the real routes): Shift + a Mixer knob sets the level to 100 / 0 (tools/mixshift.py), and takes nothing from the stock or
the firmware.

    python tools/emu_sc38.py SC38.bin SC38_manifest.json SC37.9.bin SC37.9_manifest.json
  * the original firmware and SC37.9: Shift + a Mixer knob moves the level as the plain knob (no function of its own: what SC38 replaces);
  * SC38, Mixer view, levels page: Shift + K1 right = 100, Shift + K1 left = 0, again left = 0; the plain knob still moves by its turn;
  * the pan page (Octave down): Shift + K1 moves the pan as before, the level untouched; Octave up = the levels page again;
  * Clear held (no Shift): the stock Clear (its counter), the level untouched by the first steps;
  * Master FX (Mixer twice): Shift + K1 moves the selected effect's knob by its turn, as in SC37.9.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc08 import E8  # noqa: E402

MGR, MIX = 0x20040B10, 0x200447D4


def scenario(img, man):
    import emu_sc36 as T36
    x = T36.T34.E7(img, man) if man else E8(img)
    out = {}
    def p0(st, i): x.call(0x0803542C, st, i); return x.r8(x.uc.reg_read(UC_ARM_REG_R0))
    lvl = lambda i: p0(x.r32(MIX + 0x6C), i)
    pan = lambda i: p0(x.r32(MIX + 0x70), i)
    shift = lambda on: x.set_p0(x.r32(MGR + 0xC), 1 if on else 0)
    btn = lambda b: (x.call(0x08033320, MGR, b, maxins=900000), x.call(0x0803381A, MGR, b, maxins=900000))
    knob = lambda k, d: x.call(0x08033848, MGR, k, d & 0xFFFFFFFF, maxins=900000)
    btn(14)
    out["mixer"] = x.r32(MGR + 0x6C) == MIX and x.r8(MIX + 0xAD) == 0
    l0 = lvl(0)
    shift(True); knob(0, 1); out["s_right"] = (l0, lvl(0)); knob(0, -1); out["s_left"] = lvl(0); knob(0, -1); out["s_left2"] = lvl(0); shift(False)
    a = lvl(0); knob(0, 5); out["plain"] = (a, lvl(0))
    btn(19)                                                                     # Octave down: the pan page
    out["page"] = x.r8(MIX + 0xAD); p = pan(0); l = lvl(0)
    shift(True); knob(0, 1); shift(False); out["pan"] = (p, pan(0), l, lvl(0))
    btn(20); out["page2"] = x.r8(MIX + 0xAD)
    x.call(0x08033320, MGR, 23, maxins=900000)                                   # Clear held, no Shift
    l = lvl(0); knob(0, 1); out["clear"] = (l, lvl(0), x.r8(MIX + 0xAE)); x.call(0x0803381A, MGR, 23, maxins=900000)
    if man:
        import build_sc17 as B
        x.grid(); x.pad(0); x.rel(0); k0 = x.knobs(0)[0]
        shift(True); knob(0, 3); shift(False); out["grid"] = (k0, x.knobs(0)[0])
    del x; gc.collect()
    return out


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    stock = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    s = scenario(stock, None)
    check(s["s_right"][1] == s["s_right"][0] + 1 and s["plain"][1] == s["plain"][0] + 5, f"the original: Shift + K1 = the plain knob ({s['s_right']}), no function of its own")
    q = scenario(prev, prev_man)
    check(q["s_right"][1] == q["s_right"][0] + 1, f"SC37.9: Shift + K1 = the plain knob ({q['s_right']})")
    o = scenario(img, man)
    check(o["mixer"], "SC38: the Mixer view, levels page")
    check(o["s_right"][1] == 100 and o["s_left"] == 0 and o["s_left2"] == 0, f"Shift + K1 right = 100 (from {o['s_right'][0]}), left = 0, left again = {o['s_left2']}")
    check(o["plain"] == (o["plain"][0], o["plain"][0] + 5), f"the plain knob still turns ({o['plain']})")
    check(o["page"] == 1 and o["pan"][1] == o["pan"][0] + 1 and o["pan"][3] == o["pan"][2] and o["page2"] == 0,
          f"pan page (Octave down): Shift + K1 moves the pan {o['pan'][:2]} as before, level untouched; Octave up = levels again")
    check(o["clear"][1] == o["clear"][0] and q["clear"][1] == q["clear"][0] and o["clear"][2] == q["clear"][2] == 1,
          f"Clear held + K1 right: the stock Clear counts (counter {o['clear'][2]}, SC37.9 {q['clear'][2]}), the level untouched {o['clear'][:2]}")
    check(o["grid"][1] == q["grid"][1] and o["grid"][1] != 100, f"Master FX: Shift + K1 moves the effect's knob as in SC37.9 ({o['grid']})")
    print("SC38 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
