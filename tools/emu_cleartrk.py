"""Alpha 7.22 test (projinit.use_clear): through the controller's entries (0x08033320 / 0x0803381A):
  * Synth 1's view, Clear held + Synth 1 = the stock's 0x0802FC82(session, 0, 0) (the project's patch), the pack's patch (mpatch.c_mpr) not read;
  * MIDI 1's view with the own engine on (c_von forced to 1), Clear held + MIDI 1 = projsyn's restore (c_ysget(0)), not vcf21.c_vreset;
  * Synth 1 without Clear: no reload (the press is the stock's);
  * Shift + Preset (the swap): Synth 1 = the patch's macros from the pack (clrtrk.c_crsyn reads it with mpatch.c_mpr), no project reload;
    MIDI 1 = the engine's defaults (vcf21.c_vreset).

    python tools/emu_cleartrk.py firmware/a7.22
"""
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_PC, UC_ARM_REG_LR
import emu_sc48_8 as S
import jumpseq as J
import projinit as PI


def main(a):
    d = Path(a[0]); img, man = next(d.glob("*.bin")).read_bytes(), json.loads((d / "manifest.json").read_text())
    R = man["report"]; lab = lambda m, k: int(R[m]["labels"][k], 16)
    e = S.ET(img, man); uc = e.uc; MGR = S.MGR
    seen = []
    def mark(name, stop=False):
        def f(u, ad, sz, ud):
            seen.append((name, u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)))
            if stop: u.reg_write(UC_ARM_REG_R0, 0); u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR) | 1)
        return f
    for nm, ad, stop in (("reload", PI.SYN_RELOAD, True), ("vreset", lab("vcf20", "c_vreset"), True), ("mpr", lab("mpatch", "c_mpr"), True),
                         ("ysrun", lab("projsyn", "c_ysrun"), True)):
        uc.hook_add(UC_HOOK_CODE, mark(nm, stop), begin=ad, end=ad)
    ysg = lab("projsyn", "c_ysget")
    def f_ysg(u, ad, sz, ud):                                                 # a project with the own synth's blocks: 1
        seen.append(("ysget", u.reg_read(UC_ARM_REG_R0), 0)); u.reg_write(UC_ARM_REG_R0, 1); u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR) | 1)
    uc.hook_add(UC_HOOK_CODE, f_ysg, begin=ysg, end=ysg)
    von = lab("vcf20", "c_von"); force = {"on": False}
    def f_von(u, ad, sz, ud):
        if force["on"]: u.reg_write(UC_ARM_REG_R0, 1); u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR) | 1)
    uc.hook_add(UC_HOOK_CODE, f_von, begin=von, end=von)
    t = [500000]
    def at(ms): t[0] += ms; e.w32(J.HAL_TICK, t[0])
    def drain():
        r = e.r32(0x200069F4)
        for k in range(e.r8(r + 0x18)): uc.mem_write(e.r32(e.r32(e.r32(r + 0x14) + 4 * k) + 0x10), bytes(4))
    def press(b): drain(); e.call(0x08033320, MGR, b, maxins=20_000_000); at(20)
    def release(b): drain(); e.call(0x0803381A, MGR, b, maxins=20_000_000); at(20)
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    at(0); press(0); release(0); press(9); release(9)                     # Synth 1, its Note view
    seen.clear(); press(23); press(0); release(0); release(23)
    check(("reload", e.r32(0x2003D71C) and 0x2003D71C, 0) in [(n, r0, r1) for n, r0, r1 in seen] or any(n == "reload" and r1 == 0 for n, _, r1 in seen)
          and not any(n == "mpr" for n, _, _ in seen), f"Clear + Synth 1: the project's patch reloaded, the pack's not read ({[s[0] for s in seen]})")
    seen.clear(); press(0); release(0)
    check(not any(n == "reload" for n, _, _ in seen), "Synth 1 without Clear: no reload")
    def shift(on): e.w32(e.r32(MGR + 0xC) + 0, e.r32(e.r32(MGR + 0xC))) if False else None
    sh = e.r32(MGR + 0xC)
    def shift_preset():
        from unicorn.arm_const import UC_ARM_REG_R0 as R0
        e.call(0x0803542C, sh, 0, maxins=100000); p_ = uc.reg_read(R0); old = e.r8(p_); uc.mem_write(p_, bytes([1]))
        press(8); release(8); uc.mem_write(p_, bytes([old]))
    if "c_crsyn" in R["clrtrk"]["labels"]:
        seen.clear(); shift_preset()
        check(any(n == "mpr" for n, _, _ in seen) and not any(n == "reload" for n, _, _ in seen),
              f"Shift + Preset on Synth 1: the patch's macros from the pack, no project reload ({[s[0] for s in seen]})")
    force["on"] = True
    press(2); release(2); press(9); release(9)                            # MIDI 1, its Note view
    seen.clear(); press(23); press(2); release(2); release(23)
    check(any(n == "ysget" and r0 == 0 for n, r0, _ in seen) and any(n == "ysrun" for n, _, _ in seen) and not any(n == "vreset" for n, _, _ in seen),
          f"Clear + MIDI 1 (own engine on): the project's sound (c_ysget(0) / c_ysrun), not the defaults ({[s[0] for s in seen]})")
    if "c_crsyn" in R["clrtrk"]["labels"]:
        seen.clear(); shift_preset()
        check(any(n == "vreset" and r0 == 0 for n, r0, _ in seen) and not any(n == "ysget" for n, _, _ in seen),
              f"Shift + Preset on MIDI 1: the engine's defaults (c_vreset(0)) ({[s[0] for s in seen]})")
    del e; gc.collect()
    print("CLEARTRK RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:]) else 0)
