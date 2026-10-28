"""SC48.1 ARM test (cueclk): the DSP service chain's new head writes the cue flag X:$3FF0 = the Mixer's cue mode.

    python tools/emu_cueclk.py SC48.1.bin SC48.1_manifest.json

  * the head of the chain (0x080213AA) -> c_cchead, which goes on to the previous head;
  * the cue mode off from the start: at most one write of 0 (the RAM byte is not cleared at power-on); on (cue's own c_cqmode): one write of 1 (r0 = core 0, r1 = 1 << 8, r2 = $3FF0), none on the next
    ticks; REFRESH ticks later the same write again; off: one write of 0.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import build_sc14 as S14  # noqa: E402
import mpatch as MP  # noqa: E402
import cueclk as CC  # noqa: E402


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    raw = Path(img).read_bytes()
    e = X.EP(raw, man)
    L = {k: int(v, 16) for k, v in man["report"]["cueclk"]["labels"].items()}
    P = {k: int(v, 16) for k, v in man["report"]["cueclk"]["prev"].items()}
    ql = {k: int(v, 16) for k, v in man["report"]["cue"]["labels"].items()}
    check(MP.bw_target(bytearray(raw), S14.SVC_HOOK, 0x08010000) == L["c_cchead"], f"the DSP service chain's head -> c_cchead at {L['c_cchead']:#x}")
    writes, nexts = [], []
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    def dw(uc, a, s, d):
        if uc.reg_read(UC_ARM_REG_R2) == CC.FLAG: writes.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)))
        skip(uc)
    e.uc.hook_add(UC_HOOK_CODE, dw, begin=CC.DSP_WRITE, end=CC.DSP_WRITE)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: (nexts.append(1), skip(uc)), begin=P["svc"], end=P["svc"])
    tick = lambda n=1: [e.call(L["c_cchead"], maxins=2_000_000) for _ in range(n)]
    e.call(ql["c_cqmode"], 0, maxins=4_000_000)
    tick(3)
    check(writes in ([], [(0, 0)]) and len(nexts) == 3, f"the cue mode off: at most one write of 0 ({writes}); the chain goes on ({len(nexts)})")
    writes.clear()
    e.call(ql["c_cqmode"], 1, maxins=4_000_000)
    tick()
    check(writes == [(0, 1 << 8)], f"the cue mode on: X:$3FF0 = 1 ({writes})")
    writes.clear(); tick(CC.REFRESH - 1)
    check(writes == [], f"the next {CC.REFRESH - 1} ticks: no write ({len(writes)})")
    tick()
    check(writes == [(0, 1 << 8)], f"tick {CC.REFRESH}: the refresh ({writes})")
    writes.clear(); e.call(ql["c_cqmode"], 0, maxins=4_000_000); tick()
    check(writes == [(0, 0)], f"the cue mode off: X:$3FF0 = 0 ({writes})")
    print(f"{man.get('marker', '?')} RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1], json.loads(Path(sys.argv[2]).read_text())) else 0)
