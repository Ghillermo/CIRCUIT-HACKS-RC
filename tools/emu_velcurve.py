"""SC48 ARM tests (tools/velcurve.py): Advanced Setup K1 = the pads' velocity curve, through the controller (knobs 0x08033848, the pad entry
read from the controller's vtable as the pad scan calls it) and the real LED task:
  * the default (no tag in parameter 5 byte 2): a pad hit reaches 0x08033282 with its velocity unchanged;
  * Advanced Setup, K1 three steps right (6 clicks): parameter 5 byte 2 = 0xA0 + 11 in both copies, the save asked; the frame: Velocity's LED
    (42) green and the number 3 on the pads in green; the pads' velocities = velcurve.curve(v, 3) (1 .. 127 kept);
  * K1 far left: -8 (clamped), the number in red, velocities = curve(v, -8); back to the centre: unchanged;
  * 1.5 s after the last move: Velocity's LED and the pads back (as before the move);
  * the normal Setup view (not Advanced): K1 changes nothing of ours.

    python tools/emu_velcurve.py SC48.bin SC48_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R2
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_gmdrum as EGM  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import velcurve as VC  # noqa: E402

MGR = EGM.MGR


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    raw = Path(img).read_bytes()
    e = EGM.EG(raw, man)
    got = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: got.append(uc.reg_read(UC_ARM_REG_R2)), begin=VC.PAD_ENTRY, end=VC.PAD_ENTRY)
    entry = struct.unpack_from("<I", raw, VC.CTRL_VT - 0x08010000)[0] & ~1
    def hit(v):
        got.clear(); e.call(entry, MGR, 3, v, maxins=8_000_000); return got[0] if got else None
    byte = lambda c: e.param(VC.PARAM, c)[VC.BYTE]
    vs = (1, 20, 64, 100, 127)
    check([hit(v) for v in vs] == list(vs), f"the default: velocities unchanged ({[hit(v) for v in vs]})")
    e.setup(True, adv=1); e.call(0x08047494, e.r32(MGR + 0x68), 1, maxins=4_000_000); e.unpend(); fA = X.frame(e)
    for _ in range(6): e.knob(0, 1)
    f = X.frame(e)
    check(byte(0) == byte(1) == VC.TAG + 11 and e.pending(), f"K1 three steps right: 0xA0 + 11 in both copies ({byte(0):#x}, {byte(1):#x}), the save asked")
    check(f[VC.LED_VEL] & 0xFF == VC.COL_VEL and any(x & 0xFF == VC.COL_POS for x in f[:32]), f"Velocity's LED green, the number in green ({f[VC.LED_VEL]:#x})")
    check([hit(v) for v in vs] == [VC.curve(v, 3) for v in vs], f"the pads: curve(v, 3) ({[hit(v) for v in vs]} = {[VC.curve(v, 3) for v in vs]})")
    for _ in range(40): e.knob(0, -1)
    f = X.frame(e)
    check(byte(0) == VC.TAG and any(x & 0xFF == VC.COL_NEG for x in f[:32]), f"K1 far left: -8, the number in red ({byte(0):#x})")
    check([hit(v) for v in vs] == [VC.curve(v, -8) for v in vs], f"the pads: curve(v, -8) ({[hit(v) for v in vs]} = {[VC.curve(v, -8) for v in vs]})")
    for _ in range(16): e.knob(0, 1)
    check(byte(0) == VC.TAG + 8 and [hit(v) for v in vs] == list(vs), f"back to the centre: unchanged ({byte(0):#x})")
    f0 = X.frame(e)
    e.w32(VC.HAL_TICK, e.r32(VC.HAL_TICK) + 1600); f1 = X.frame(e)
    check(f0[VC.LED_VEL] & 0xFF == VC.COL_VEL and f1[VC.LED_VEL] == fA[VC.LED_VEL] and f1[:32] == fA[:32],
          f"1.5 s later: Velocity's LED and the pads back ({f0[VC.LED_VEL]:#x} -> {f1[VC.LED_VEL]:#x})")
    e.setup(True, adv=0); b0 = byte(0)
    for _ in range(6): e.knob(0, 1)
    check(byte(0) == b0, f"the normal Setup view: K1 changes nothing of ours ({byte(0):#x})")
    del e; gc.collect()
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text())) else 0)
