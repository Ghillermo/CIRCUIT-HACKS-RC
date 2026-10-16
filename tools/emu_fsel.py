"""R0901 / SC41.4 ARM tests: the drums' default filter is the stock tilt EQ (persist19.use_fselstock).

    python tools/emu_fsel.py NEW.bin NEW_manifest.json PREVIOUS.bin PREVIOUS_manifest.json
  For each stored filter mode 0..4 of drum 1 (the byte 8 of its block in the project zone), marked to send, the DSP service hook (c_dtick19) sends
  the mailbox message of code 9: new build 4, 1, 2, 3, 0 (stored 0 = the stock tilt EQ, 4 = the DJ filter); the previous build 0, 1, 2, 3, 4.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc08 import E8  # noqa: E402
import persist19 as P19  # noqa: E402

DSP_WRITE = 0x080292F8


def sent(img, man):
    L = {k: int(v, 16) for k, v in man["report"]["persist19"]["labels"].items()}
    mh = int(man["report"]["sc18"]["labels"]["c_mh"], 16)
    e = E8(img)
    dw = []
    def h(uc, a, s_, d):
        dw.append((uc.reg_read(UC_ARM_REG_R2) & 0xFFFFFF, uc.reg_read(UC_ARM_REG_R1) >> 8)); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, h, begin=DSP_WRITE, end=DSP_WRITE)
    def r0(fn, *a): e.call(fn, *a, maxins=4_000_000); return e.uc.reg_read(UC_ARM_REG_R0)
    for _ in range(3): dw.clear(); r0(L["c_dtick19"])
    out = []
    for v in range(5):
        a = r0(L["c_xp"], P19.XM_DRUMS + 8)                                       # drum 0, byte 8: bits 0-2 = the filter mode
        e.uc.mem_write(a, bytes([e.r8(a) & ~7 | v]))
        h_ = r0(mh, 0); e.uc.mem_write(h_ + P19.O_FLAGS, bytes([e.r8(h_ + P19.O_FLAGS) & 0x80])); e.uc.mem_write(h_ + P19.O_DELTA, bytes([e.r8(h_ + P19.O_DELTA) & ~7 | 2]))
        got = None
        for _ in range(4):
            dw.clear(); r0(L["c_dtick19"])
            for addr, w in dw:
                if (w >> 16) & 0x7F == 9: got = w & 0xFFFF
            if got is not None: break
        out.append(got)
    del e; gc.collect()
    return out


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    a = sent(img, man); gc.collect(); p = sent(prev, prev_man)
    check(a == [4, 1, 2, 3, 0] and p == [0, 1, 2, 3, 4], f"stored filter modes 0..4 -> the DSP's modes {a} (0 = the stock tilt EQ by default); the previous build {p}")
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
