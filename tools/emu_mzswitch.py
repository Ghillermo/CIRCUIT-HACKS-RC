"""SC57 / Beta 5.55 test (morphz.use_newstop; the user, 2026-11-12: «either several morphs co-exist or enabling a new morph stops the old one»):
with Synth 1's morph running, patches held 0.4 s on Synth 2's Preset view = Synth 2's morph, Synth 1's stopped.

The emulated firmware (emu_sc48_8's harness, as emu_mzrr): O_RR left as garbage too, the card answering with the live patch.
  1. Synth 1, Preset, pads 12 / 10 / 11 held, 60 frames: Synth 1's morph on (O_ACT 0); the pads let go.
  2. Synth 2, Preset, a single tap on pad 3: the stock loads it, Synth 1's morph goes on, nothing armed after the release.
  3. Pads 3 / 4 held 0.6 s: the build = Synth 2's morph (O_ACT 1, two links); the previous build (if given) = still Synth 1's.
Every DSP service call must return.

    python tools/emu_mzswitch.py BUILD.bin manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]
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

MGR, PRESS, RELEASE = S.MGR, T6.PRESS, T6.RELEASE


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
    def mpr(uc, a, s_, d):
        buf, n = uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3)
        uc.mem_write(buf, bytes(uc.mem_read(M.LIVE, n))); uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    c_mpr = int(R["mpatch"]["labels"]["c_mpr"], 16)
    e.uc.hook_add(UC_HOOK_CODE, mpr, begin=c_mpr, end=c_mpr)
    t = [500000]
    def at(ms): t[0] += ms; e.w32(J.HAL_TICK, t[0])
    stuck = []
    def frames(k):
        for _ in range(k):
            if stuck: return
            at(10); X.frame(e)
            e.call(svc, maxins=3_000_000)
            pc = e.uc.reg_read(UC_ARM_REG_PC) & ~1
            if pc != E5.STOP & ~1: stuck.append(hex(pc))
    def btn(b):
        drain(); e.call(0x08033320, MGR, b, maxins=20_000_000); drain(); e.call(0x0803381A, MGR, b, maxins=20_000_000)
    def st(): return dict(act=e.r8(M.MZ + M.O_ACT), n=e.r8(M.MZ + M.O_N), hp=e.r8(M.MZ + M.O_HP), snap=e.r8(M.MZ + 27))                                # O_SNAP with use_four
    out = {}
    at(0)
    btn(0); btn(8); frames(3)
    e.uc.mem_write(M.MZ + M.O_RR, struct.pack("<H", 0xFFFF))
    for q in (11, 9, 10): e.call(PRESS, MGR, q, 100, maxins=8_000_000); at(20)
    frames(60); out["s1"] = st()
    for q in (11, 9, 10): e.call(RELEASE, MGR, q, maxins=8_000_000)
    frames(5)
    btn(1); btn(8); frames(3)
    e.call(PRESS, MGR, 2, 100, maxins=8_000_000); frames(3); e.call(RELEASE, MGR, 2, maxins=8_000_000); frames(5)
    out["tap"] = st()
    for q in (2, 3): e.call(PRESS, MGR, q, 100, maxins=8_000_000); at(20)
    frames(60); out["s2"] = st()
    out["stuck"] = stuck
    del e; gc.collect()
    return out


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    r = run(img, man)
    check(r["s1"]["act"] == 0, f"Synth 1, three patches held: its morph on ({r['s1']})")
    check(r["tap"]["act"] == 0 and r["tap"]["hp"] != M.ARMED, f"a tap on Synth 2's pad 3: Synth 1's morph goes on, nothing armed ({r['tap']})")
    check(r["s2"]["act"] == 1 and r["s2"]["n"] >= 2, f"Synth 2, pads 3 / 4 held 0.6 s: Synth 2's morph, Synth 1's stopped ({r['s2']})")
    check(not r["stuck"], f"every DSP service call returns ({r['stuck'][:2]})")
    if prev:
        p = run(prev, pman)
        check(p["s2"]["act"] == 0, f"the previous build: Synth 1's morph still on, Synth 2's hold did nothing ({p['s2']})")
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text()), a[2] if len(a) > 2 else None,
                       json.loads(Path(a[3]).read_text()) if len(a) > 3 else None) else 0)
