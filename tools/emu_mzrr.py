"""SC56.9 / Beta 5.54 test (morphz.use_rrfix): Beta 5.53's black box on the device: Synth 1's Preset, three patches held (pads 12, 10, 11) = the
morph entering, then «Main» looping in c_mznova until the watchdog restarted the unit.  O_RR (its round-robin place) was never set and the RAM is not
cleared on the device; with O_RR >= NROWS and every row already the patch's (nothing to write), the round never ends.

The emulated firmware (emu_sc48_8's harness): Synth 1, Preset, O_RR = 0xFFFF as a leftover, the card answering with the live patch (nothing to
write), the three pads held, 60 frames with the DSP service's head (c_mzsvc) after each:
  * the build: every service call returns, the morph on, O_RR < NROWS after;
  * the previous build (if given): a service call never returns (the loop of the device's record).

    python tools/emu_mzrr.py BUILD.bin manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc48_8 as S  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import emu_sc17_6 as T6  # noqa: E402
import emu_sc05 as E5  # noqa: E402
import morphz as M  # noqa: E402
import jumpseq as J  # noqa: E402

MGR, PRESS = S.MGR, T6.PRESS
PADS = (11, 9, 10)                                            # pads 12, 10, 11 (the record's order)


def run(img_path, man):
    img = Path(img_path).read_bytes()
    e = S.ET(img, man); R = man["report"]
    def drain():
        r = e.r32(0x200069F4)
        for k in range(e.r8(r + 0x18)): e.uc.mem_write(e.r32(e.r32(e.r32(r + 0x14) + 4 * k) + 0x10), bytes(4))
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: uc.mem_write(e.r32(uc.reg_read(UC_ARM_REG_R0) + 0x10), bytes(4)), begin=0x08035A50, end=0x08035A50)
    svc = int(R["morphz"]["labels"]["c_mzsvc"], 16)
    nxt = int(R["morphz"]["prev"]["svc"], 16)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1), begin=nxt, end=nxt)
    def mpr(uc, a, s_, d):                                    # the card: the live patch (nothing to write)
        buf, n = uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3)
        uc.mem_write(buf, bytes(uc.mem_read(M.LIVE, n))); uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    c_mpr = int(R["mpatch"]["labels"]["c_mpr"], 16)
    e.uc.hook_add(UC_HOOK_CODE, mpr, begin=c_mpr, end=c_mpr)
    t = [500000]
    def at(ms): t[0] += ms; e.w32(J.HAL_TICK, t[0])
    stuck = []
    def frames(k):
        for _ in range(k):
            at(10); X.frame(e)
            e.call(svc, maxins=3_000_000)
            pc = e.uc.reg_read(UC_ARM_REG_PC) & ~1
            if pc != E5.STOP & ~1: stuck.append(hex(pc)); return
    at(0)
    for b in (0, 8):
        drain(); e.call(0x08033320, MGR, b, maxins=20_000_000); drain(); e.call(0x0803381A, MGR, b, maxins=20_000_000)
    frames(3)
    e.uc.mem_write(M.MZ + M.O_RR, struct.pack("<H", 0xFFFF))
    for q in PADS: e.call(PRESS, MGR, q, 100, maxins=8_000_000); at(20)
    frames(60)
    out = dict(stuck=stuck, act=e.r8(M.MZ + M.O_ACT), rr=struct.unpack("<H", bytes(e.uc.mem_read(M.MZ + M.O_RR, 2)))[0])
    del e; gc.collect()
    return out


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    r = run(img, man)
    check(not r["stuck"] and r["act"] == 0 and r["rr"] < M.NROWS,
          f"O_RR left at 0xFFFF, three patches held, nothing to write: every service call returns, the morph on, O_RR {r['rr']} (stuck {r['stuck'][:2]})")
    if prev:
        p = run(prev, pman)
        check(bool(p["stuck"]), f"the previous build: the service loops ({p['stuck'][:1]})")
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text()), a[2] if len(a) > 2 else None,
                       json.loads(Path(a[3]).read_text()) if len(a) > 3 else None) else 0)
