"""SC57.1 / Beta 5.56 test (morphz.use_fastatk; the user, 2026-11-12: «morph envelope attack should be shorter, almost instant»; Synth 1 / 2):
Synth 1's morph between three patches that differ (the card hook gives each slot its own bytes), the envelope depth K7 at the top, settled; pad 1 =
the trigger.  The DSP service's next pass must write every row that changed (more than the BUDGET of 40), the pass after it at most 40 again; the
previous build (if given) writes at most 40 in that pass.  Every service call returns.

    python tools/emu_fastatk.py BUILD.bin manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_LR, UC_ARM_REG_PC
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
    def mpr(uc, a, s_, d):                                    # each slot its own bytes (bank r0, offset r1)
        k = uc.reg_read(UC_ARM_REG_R0) * 8 + (uc.reg_read(UC_ARM_REG_R1) >> 9)
        buf, n = uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3)
        live = bytes(uc.mem_read(M.LIVE, n))                  # the morph's link reads (340 B): the live patch with bytes 60..339 per slot
        uc.mem_write(buf, live[:60] + bytes(((i * 7 + k * 37) & 0x7F) for i in range(60, n)) if n == 340 else live); uc.reg_write(UC_ARM_REG_R0, 0)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    c_mpr = int(R["mpatch"]["labels"]["c_mpr"], 16)
    e.uc.hook_add(UC_HOOK_CODE, mpr, begin=c_mpr, end=c_mpr)
    sets = [0]
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: sets.__setitem__(0, sets[0] + 1), begin=M.PARAM_SET, end=M.PARAM_SET)
    t = [500000]
    def at(ms): t[0] += ms; e.w32(J.HAL_TICK, t[0])
    stuck = []
    def frame():
        at(10); X.frame(e); sets[0] = 0
        e.call(svc, maxins=6_000_000)
        if e.uc.reg_read(UC_ARM_REG_PC) & ~1 != E5.STOP & ~1: stuck.append(hex(e.uc.reg_read(UC_ARM_REG_PC)))
        return sets[0]
    def btn(b):
        drain(); e.call(0x08033320, MGR, b, maxins=20_000_000); drain(); e.call(0x0803381A, MGR, b, maxins=20_000_000)
    at(0)
    btn(0); btn(8)
    for _ in range(3): frame()
    for q in (11, 9, 10): e.call(PRESS, MGR, q, 100, maxins=8_000_000); at(20)
    for _ in range(60): frame()
    held = e.r8(M.MZ + M.O_ACT)
    for q in (11, 9, 10): e.call(RELEASE, MGR, q, maxins=8_000_000)
    e.uc.mem_write(M.MZ + M.O_K + 6, bytes([63]))            # K7: the envelope's depth at the top
    settle = [frame() for _ in range(40)]
    act = e.r8(M.MZ + M.O_ACT)
    e.call(PRESS, MGR, 0, 100, maxins=8_000_000)              # pad 1: the trigger
    after = [frame() for _ in range(4)]
    out = dict(held=held, act=act, settle=settle[-3:], after=after, stuck=stuck)
    del e; gc.collect()
    return out


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    r = run(img, man)
    check(r["act"] == 0, f"Synth 1's morph on (held {r['held']}, after {r['act']})")
    w = r["after"]
    check(max(w[:2]) > M.BUDGET, f"the trigger: one pass writes every changed row, more than {M.BUDGET} (writes a pass after it: {w}; settled {r['settle']})")
    check(all(x <= M.BUDGET for x in w[2:]), f"the passes after: at most {M.BUDGET} again ({w[2:]})")
    check(not r["stuck"], f"every service call returns ({r['stuck'][:2]})")
    if prev:
        p = run(prev, pman)
        check(max(p["after"]) <= M.BUDGET, f"the previous build: at most {M.BUDGET} a pass ({p['after']})")
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text()), a[2] if len(a) > 2 else None,
                       json.loads(Path(a[3]).read_text()) if len(a) > 3 else None) else 0)
