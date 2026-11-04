"""SC51 / Beta 5.13 ARM tests (tools/velglob.py), through the controller (knobs, the pad entry from the controller's vtable), the real LED task and
direct calls of the replaced reads:
  * the pads: velocities unchanged whatever was saved for the old curve (the pad entry is the stock's again);
  * Advanced Setup K1 / K2: 0 by default; turned right 40 / 90 events: parameter 6 bytes 2 / 3 = 0x80 | value in both copies, the save asked; K2's move
    marks parameter 96 of both synths; their LEDs (60 / 61) white, brightness = value + 2; the normal Setup view: nothing of ours;
  * Synth 1's amp velocity (c_vgamp, as 0x0802712E calls it): a patch with 64 (none) = 64 + K1 / 2; with 100 = 100; K1 at 0 = 64;
  * the matrix (c_vgmx, as the sender calls it): a patch without velocity: its last unused slot = velocity -> filter frequency, depth 64 + K2 / 2; the
    other slots as they are; a patch with velocity in a slot: as it is; K2 at 0: as it is; Synth 2's patch read 344 bytes on;
  * the own synth (c_vgoff, as c_mxfx calls it): velocity source off, velocity 20: code 15 - (107 K1) / 256, code 1 - (107 K2) / 256, other codes
    and velocity 127 unchanged; the velocity source on: unchanged; the DSP service head marks codes 15 / 1 when the velocity changes.

  SC51.2 / Beta 5.15 (velglob.use_setup, label vk_s): the same in the normal Setup view; Advanced Setup's K1 does nothing; gmdrum's K4 still ours.

    python tools/emu_velglob.py SC51.bin SC51_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_gmdrum as EGM  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import velcurve as VC  # noqa: E402
import velglob as VG  # noqa: E402
import modmx as MX  # noqa: E402

MGR = EGM.MGR


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    raw = Path(img).read_bytes()
    L = {k: int(v, 16) for k, v in man["report"]["velglob"]["labels"].items()}
    e = EGM.EG(raw, man)
    got = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: got.append(uc.reg_read(UC_ARM_REG_R2)), begin=VC.PAD_ENTRY, end=VC.PAD_ENTRY)
    entry = struct.unpack_from("<I", raw, VC.CTRL_VT - 0x08010000)[0] & ~1
    for cp in (0, 1):                                                         # an old curve saved (+8)
        e.call(int(man["report"]["gmdrum"]["labels"]["c_gmp"], 16), VC.PARAM, cp); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0) + VC.BYTE, bytes([VC.TAG + 16]))
    def hit(v):
        got.clear(); e.call(entry, MGR, 3, v, maxins=8_000_000); return got[0] if got else None
    vs = (1, 20, 64, 100, 127)
    check(entry == VC.PAD_ENTRY and [hit(v) for v in vs] == list(vs), f"the pads: the stock's entry, velocities unchanged ({[hit(v) for v in vs]})")
    k = lambda i: (e.param(VG.PARAM, i)[VG.BYTE_AMP], e.param(VG.PARAM, i)[VG.BYTE_FLT])
    check(k(0) == (0, 0), f"K1 / K2 off by default ({k(0)})")
    marks = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: marks.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1))), begin=VG.MARK_DIRTY, end=VG.MARK_DIRTY)
    SET = "vk_s" in L                                                         # SC51.2: the normal Setup view
    ours, other = (0, 1) if SET else (1, 0)
    e.setup(True, adv=ours)
    if ours: e.call(0x08047494, e.r32(MGR + 0x68), 1, maxins=4_000_000)       # Advanced Setup entered as at the boot
    e.unpend()
    for _ in range(40): e.knob(0, 1)
    m0 = list(marks)
    for _ in range(90): e.knob(1, 1)
    f = X.frame(e)
    check(k(0) == k(1) == (0x80 | 40, 0x80 | 90) and e.pending(), f"K1 40, K2 90: 0x80 | value in both copies ({k(0)}, {k(1)}), the save asked")
    check(not m0 and (0, 96) in marks and (1, 96) in marks, f"K2's move marks parameter 96 of both synths, K1's none ({sorted(set(marks))[:4]})")
    check(f[VG.LED_K] == 0x01 | 42 << 8 and f[VG.LED_K + 1] == 0x01 | 92 << 8, f"LEDs 60 / 61 white, brightness = value + 2 ({f[VG.LED_K]:#x}, {f[VG.LED_K + 1]:#x})")
    e.setup(True, adv=other)
    if other: e.call(0x08047494, e.r32(MGR + 0x68), 1, maxins=4_000_000)
    b0 = k(0)
    for _ in range(5): e.knob(0, 1)
    for _ in range(5): e.knob(1, 1)
    f2 = X.frame(e)
    check(k(0) == b0, ("Advanced Setup" if SET else "the normal Setup view") + ": nothing of ours")
    if SET:
        check(f2[VG.LED_K] != 0x01 | 42 << 8, f"Advanced Setup: not our LEDs ({f2[VG.LED_K]:#x})")
        import gmdrum as GM
        e.setup(True, adv=0); e.knob(GM.K_TOG, 1)
        check(e.param(GM.P0, 0)[GM.B_FLAGS] & 1 == 1, f"Setup K4: the GM drum mode still turns on ({e.param(GM.P0, 0)[GM.B_FLAGS]:#x})")
    ram = VG.RAM
    def r0f(fn, *a):
        e.call(fn, *a, maxins=4_000_000); return e.uc.reg_read(UC_ARM_REG_R0)
    e.r0 = r0f
    def cache(k1, k2): e.uc.mem_write(ram + 4, bytes([k1, k2]))
    # the amp velocity
    P0 = VG.PATCH0
    def amp(byte69, k1):
        cache(k1, 0); e.uc.mem_write(P0 + 69, bytes([byte69])); return e.r0(L["c_vgamp"], 0, 39) & 0xFF
    a = [amp(64, 100), amp(100, 100), amp(64, 0), amp(64, 127)]
    check(a == [114, 100, 64, 127], f"Synth 1's amp velocity: 64 -> 64 + K1 / 2, a patch's own kept, K1 0 = 64 ({a})")
    # the matrix
    def mx(s, k2, slots):
        cache(0, k2); base = P0 + 344 * s + VG.P_MX
        e.uc.mem_write(base, bytes(sum(([s1, s2, d, ds] for s1, s2, d, ds in slots), [])))
        return [[e.r0(L["c_vgmx"], s, 94 + 4 * j + f_) & 0xFF for f_ in range(4)] for j in range(20)]
    novel = [[6, 0, 90, 12]] + [[0, 0, 64, 0]] * 18 + [[7, 0, 70, 1]]
    r = mx(0, 100, novel)
    check(r[18] == [4, 0, 114, 12] and r[0] == [6, 0, 90, 12] and r[19] == [7, 0, 70, 1] and r[5] == [0, 0, 64, 0],
          f"no velocity: the last unused slot (18) = velocity -> filter, depth 114; the others as they are ({r[18]}, {r[19]})")
    withv = [[4, 0, 80, 7]] + [[0, 0, 64, 0]] * 19
    r = mx(0, 100, withv)
    check(r[19] == [0, 0, 64, 0] and r[0] == [4, 0, 80, 7], f"a patch with velocity in its matrix: as it is ({r[0]}, {r[19]})")
    r = mx(0, 0, novel)
    check(r[18] == [0, 0, 64, 0], f"K2 at 0: as it is ({r[18]})")
    r = mx(1, 100, novel)
    name2 = bytes(e.uc.mem_read(P0 + 344, 16)).decode("latin1", "replace")
    check(r[18] == [4, 0, 114, 12], f"Synth 2: its patch 344 bytes on ({r[18]}, name {name2!r})")
    # the own synth
    blk = e.r0(int(man["report"]["modmx"]["labels"]["c_mxblk"], 16), 0)
    def off(code, vel, pos0, k1, k2):
        cache(k1, k2); e.uc.mem_write(blk + MX.B_POS, struct.pack("<H", pos0)); e.uc.mem_write(blk + MX.B_VEL, bytes([vel]))
        v = e.r0(L["c_vgoff"], 0, code); return v - (1 << 32) if v & 0x80000000 else v
    base15, base1 = off(15, 127, 0, 0, 0), off(1, 127, 0, 0, 0)
    o = [off(15, 20, 0, 127, 64) - base15, off(1, 20, 0, 127, 64) - base1, off(5, 20, 0, 127, 64) - off(5, 127, 0, 0, 0), off(15, 127, 0, 127, 64) - base15]
    check(o == [-(107 * 127 >> 8), -(107 * 64 >> 8), 0, 0], f"own synth, velocity 20: level - 53, filter - 26, other codes and velocity 127 unchanged ({o})")
    o2 = off(15, 20, 3, 127, 64) - off(15, 20, 3, 0, 0)
    check(o2 == 0, f"its velocity source on: unchanged ({o2})")
    vm = []
    hk = e.uc.hook_add(UC_HOOK_CODE, lambda uc, a_, s, d: vm.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1))),
                       begin=int(man["report"]["vcf20"]["labels"]["c_vmark"], 16), end=int(man["report"]["vcf20"]["labels"]["c_vmark"], 16))
    cache(127, 64); e.uc.mem_write(blk + MX.B_VEL, bytes([33])); e.call(L["c_vgtick"], maxins=4_000_000); m1 = list(vm); vm.clear()
    e.call(L["c_vgtick"], maxins=4_000_000); m2 = list(vm)
    check((0, 15) in m1 and (0, 1) in m1 and not [x for x in m2 if x[0] == 0], f"the service head marks codes 15 / 1 once when the velocity changes ({m1}, {m2})")
    del e; gc.collect()
    print(f"{Path(img).stem} VELGLOB RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text())) else 0)
