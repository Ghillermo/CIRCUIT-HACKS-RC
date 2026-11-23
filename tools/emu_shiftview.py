"""Alpha 7.31 test (tools/shiftview.py) through the controller and the LED task:
  * from Synth 1's Note view, Shift + Mixer = Master FX (c_gact); Shift + Mixer again = the Mixer; Shift + Mixer = Master FX again; the Shift byte
    still set after each (the user's Shift held);  Mixer without Shift from Synth 1 = the Mixer, as before;
  * Clear held + Shift + Mixer = nothing of ours.
    python tools/emu_shiftview.py firmware/a7.31
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn.arm_const import UC_ARM_REG_R0
import emu_sc48_8 as S
import emu_sc42_6 as X
import arp as A
import build_sc17 as S17

MGR = S.MGR
BTN, BTN_UP = 0x08033320, 0x0803381A


def main(a):
    d = Path(a[0]); img = next(d.glob("*.bin")).read_bytes(); man = json.loads((d / "manifest.json").read_text())
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = S.ET(img, man)
    from unicorn import UC_HOOK_CODE
    from unicorn.arm_const import UC_ARM_REG_R0 as R0
    def flush(uc, a_, s_, d_):                       # the MIDI-out flush (0x08035A50): emptied first, as the hardware would (emu_morph)
        uc.mem_write(e.r32(uc.reg_read(R0) + 0x10), bytes(4))
    e.uc.hook_add(UC_HOOK_CODE, flush, begin=0x08035A50, end=0x08035A50)
    t = [500000]
    def at(ms): t[0] += ms; e.w32(A.HAL_TICK, t[0])
    def frame(): at(20); X.frame(e); return X.frame(e)
    gact = int(man["report"]["sc17"]["labels"]["c_gact"], 16)
    def mfx(): e.call(gact, maxins=100_000); return e.uc.reg_read(UC_ARM_REG_R0) != 0
    def inmix(): v = e.r32(MGR + 0x6C); return v != 0 and e.r32(v) == S17.MIX2["MIX_VT"]
    def btn(i, shift=False, held=None):
        if held is not None: e.call(BTN, MGR, held, maxins=8_000_000)
        if shift: e.set_p0(e.r32(MGR + 0xC), 1)
        e.call(BTN, MGR, i, maxins=60_000_000); e.call(BTN_UP, MGR, i, maxins=8_000_000)
        sh = e.store_p0(e.r32(MGR + 0xC)) if shift else None
        if shift: e.set_p0(e.r32(MGR + 0xC), 0)
        if held is not None: e.call(BTN_UP, MGR, held, maxins=8_000_000)
        frame(); return sh
    at(0); frame()
    btn(0); btn(9)
    check(not inmix() and not mfx(), "Synth 1's Note view")
    sh = btn(14, shift=True)
    check(inmix() and mfx(), f"Shift + Mixer from Synth 1 = Master FX (shift byte after: {sh})")
    check(sh == 1, "the Shift byte put back")
    btn(14, shift=True)
    check(inmix() and not mfx(), "Shift + Mixer in Master FX = the Mixer")
    btn(14, shift=True)
    check(inmix() and mfx(), "Shift + Mixer in the Mixer = Master FX")
    btn(0); btn(9); btn(14)
    check(inmix() and not mfx(), "Mixer without Shift from Synth 1 = the Mixer (as before)")
    btn(0); btn(9); btn(14, shift=True, held=23)
    check(not mfx(), "Clear held + Shift + Mixer: not ours")
    print("SHIFTVIEW RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
