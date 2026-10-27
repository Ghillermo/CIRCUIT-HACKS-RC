"""SC48 ARM tests (cue.use_preview + tools/cueprev.py): in the cue mode the Preset views' previews go to the cue only.  Through the controller
(pads 0x08033282 / 0x0803381A) and the real LED task; the stock's preview scheduling (0x0803C432) and the drums' note-on body (0x0804E0CE)
caught:
  * the cue mode on, Synth 1's Preset view, a patch pad: the preview scheduled, Synth 1's bit set; c_cqg: its pan 127 (the cue only), its level
    as before, its reverb send 0; Shift + a patch pad: previewed too;
  * let go, 0.9 s later: the bit cleared, the pan back to the cue mode's (hard left = 0);
  * Drum 1's Preset view: a normal press = the note-on, no bit (the main); Shift + a pad = the note-on (silent on stock) and Drum 1's bit;
  * live playing: at the drums' funnel (c_cptrig, the hit itself skipped) the preview's own hit keeps the cue; the next hit of Drum 1 clears its
    bit first and flushes its group (0x080214D0) and marks its two sends;
  * Shift + a synth patch (a fresh unit): the cue mode = previewed in the cue; off = silent as on stock; Shift + a drum pad, the mode off: silent.

    python tools/emu_cueprev.py SC48.bin SC48_manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR, UC_ARM_REG_R0, UC_ARM_REG_R1
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import cue as CQ  # noqa: E402
import cueprev as CP  # noqa: E402

MGR = X.MGR


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = X.EP(Path(img).read_bytes(), man)
    ql = {k: int(v, 16) for k, v in man["report"]["cue"]["labels"].items()}
    sched, dons = [], []
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: (sched.append(1), skip(uc)), begin=CP.TIMER, end=CP.TIMER)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: dons.append(1), begin=0x0804E0CE, end=0x0804E0CE)
    mask = lambda: e.r8(CQ.PVR + 4) if e.r32(CQ.PVR) == CQ.PVSIG else 0
    g = lambda typ, idx: e.r0(ql["c_cqg"], typ, idx)
    def tap(pad, shift=False):
        if shift: e.shift(True)
        e.call(PRESS, MGR, pad, 100, maxins=8_000_000)
        if shift: e.shift(False)
        e.call(RELEASE, MGR, pad, maxins=8_000_000)
    t = 1000; e.at(t)
    e.call(ql["c_cqmode"], 1, maxins=4_000_000)
    check(e.r0(ql["c_cqon"]) == 1, "the cue mode on")
    e.btn(0); e.btn(8)
    sched.clear(); e.call(PRESS, MGR, 2, 100, maxins=8_000_000)
    m1, pan, lev, send = mask(), g(0x20, 50), g(0x20, 46), g(0x20, 0)
    check(sched and m1 & 1 and pan == 127 and send == 0, f"Synth 1, a patch: the preview scheduled, its bit ({m1:#x}), pan {pan} (the cue only), reverb send {send}")
    e.call(RELEASE, MGR, 2, maxins=8_000_000)
    t += 900; e.at(t); X.frame(e)
    check(mask() == 0 and g(0x20, 50) == 0, f"let go, 0.9 s later: the bit cleared ({mask():#x}), the pan back to the cue mode's ({g(0x20, 50)})")
    e.btn(4); e.btn(8)
    dons.clear(); tap(5)
    check(dons and not mask() & 0x10, f"Drum 1, a normal press: the note-on, no cue ({len(dons)}, {mask():#x})")
    dons.clear(); e.shift(True); e.call(PRESS, MGR, 6, 100, maxins=8_000_000); e.shift(False)
    check(dons and mask() & 0x10, f"Drum 1, Shift + a pad: the note-on (silent on stock) in the cue ({len(dons)}, {mask():#x})")
    cl = {k: int(v, 16) for k, v in man["report"]["cueprev"]["labels"].items()}
    fl, mk = [], []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: (fl.append(uc.reg_read(UC_ARM_REG_R0)), skip(uc)), begin=CP.FLUSH, end=CP.FLUSH)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: (mk.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1))), skip(uc)), begin=CP.MARK, end=CP.MARK)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: skip(uc), begin=0x08051B54, end=0x08051B54)
    e.call(cl["c_cptrig"], 0, 100, maxins=4_000_000); m_first = mask()
    e.call(cl["c_cptrig"], 0, 100, maxins=4_000_000)
    check(m_first & 0x10 and not mask() & 0x10 and fl == [0] and mk == [(0x20, 4), (0x20, 15)],
          f"live: the preview's own hit keeps the cue ({m_first:#x}); the next hit of Drum 1 = back to the main first ({mask():#x}, flush {fl}, marks {mk})")
    e.call(RELEASE, MGR, 6, maxins=8_000_000); t += 900; e.at(t); X.frame(e)
    e.call(ql["c_cqmode"], 0, maxins=4_000_000); X.frame(e)
    dons.clear(); tap(7, shift=True)
    check(not dons and mask() == 0, f"the cue mode off: Shift + a drum pad = silent, no bit ({len(dons)}, {mask():#x})")
    del e; gc.collect()
    # (a fresh unit for each synth selection: in emulation a patch's load never ends and the next selection is refused)
    for cue_on in (True, False):
        e = X.EP(Path(img).read_bytes(), man)
        sched = []
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: (sched.append(1), skip(uc)), begin=CP.TIMER, end=CP.TIMER)
        e.at(1000)
        if cue_on: e.call(ql["c_cqmode"], 1, maxins=4_000_000)
        e.btn(0); e.btn(8); sched.clear()
        e.shift(True); e.call(PRESS, MGR, 3, 100, maxins=8_000_000); e.shift(False)
        m = e.r8(CQ.PVR + 4) if e.r32(CQ.PVR) == CQ.PVSIG else 0
        if cue_on: check(sched and m & 1, f"the cue mode, Shift + a patch (silent on stock): previewed, in the cue ({len(sched)}, {m:#x})")
        else: check(not sched and m == 0, f"the cue mode off, Shift + a patch: silent as on stock ({len(sched)}, {m:#x})")
        del e; gc.collect()
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text())) else 0)
