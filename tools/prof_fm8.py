"""Profile (no pass / fail): the 8-operator FM engine's ARM cost per 1 ms tick and its SPI writes to the DSP, per instrument, through fmeng's
c_fmtick (emu_fm8's harness): silent, a 4-note chord held, the same chord with the block dirty every tick (what the morph does while it moves),
and the tick in which an instrument is loaded.

    python tools/prof_fm8.py BUILD.bin manifest.json [instrument ...]
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402,F401  (its import sets vcf21's options)
import fmeng as FE  # noqa: E402
import fm8 as F  # noqa: E402
import fm8arm as A  # noqa: E402
import fm8inst as FI  # noqa: E402
import vcf21_dsp as VD  # noqa: E402


def main(img, man, which):
    VD.FMC1 = True; VD.FV0 = 0x4000; VD.use_fm8()
    R = man["report"]
    if "c_fiun" in str(R.get("fm8ui", {}).get("labels", {})) or "inst2" in json.dumps(R.get("fm8ui", {})): FI.use_v2()
    fl = {k: int(v, 16) for k, v in R["fmeng"]["labels"].items()}
    e = X.EP(img, man)
    n = {"w": 0, "i": 0, "sem": 0, "sd": 0}
    def w(uc, a, s, d): n["w"] += 1
    e.uc.hook_add(UC_HOOK_CODE, w, begin=A.DSP_WRITE, end=A.DSP_WRITE)
    def dread(uc, a, s, d):
        uc.reg_write(UC_ARM_REG_R0, (A.INCS[60] if (uc.reg_read(UC_ARM_REG_R1) & 0xFFFF) == VD.OSB0 + 11 else 0) << 8)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, dread, begin=A.DSP_READ, end=A.DSP_READ)
    def ins(uc, a, s, d): n["i"] += 1
    def sem(uc, a, s, d): n["sem"] += 1
    e.uc.hook_add(UC_HOOK_CODE, sem, begin=0x08021064, end=0x08021064)
    def sd(uc, a, s, d): n["sd"] += 1
    for f in (0x0803CBF0, 0x0803CB6A): e.uc.hook_add(UC_HOOK_CODE, sd, begin=f, end=f)
    blk = A.FM8R + A.TB0
    non = e.r32(FE.MX.NOTE_VT) & ~1; noff = e.r32(FE.MX.NOTE_VT + 4) & ~1
    on = lambda nt: e.call(non, 0x20011334, 2, nt, 100, maxins=8_000_000)
    off = lambda nt: e.call(noff, 0x20011334, 2, nt, 0, maxins=8_000_000)
    def tick(k=1, dirty=False):
        h = e.uc.hook_add(UC_HOOK_CODE, ins)
        for _ in range(k):
            if dirty: e.uc.mem_write(blk + A.B_DIRTY, b"\x01")
            e.at(e.t + 1); e.call(fl["c_fmtick"], maxins=20_000_000)
        e.uc.hook_del(h)
    def meas(fn, k, dirty=False):
        for x in n: n[x] = 0
        fn(); tick(k, dirty)
        return n["i"] / k, n["w"] / k, n["sem"], n["sd"]
    e.btn(2); e.btn(8); e.pad(26); e.pad(FE.ROWPAD)
    tick(50)
    chord = (60, 64, 67, 71)
    print(f"{man.get('marker', '?')}: per 1 ms tick (ARM instructions, SPI writes); sem = DSP semaphore takes, sd = card reads")
    print(f"{'instrument':16s} {'load tick':>18s} {'silent':>16s} {'chord held':>16s} {'chord + dirty':>16s} {'release':>16s}")
    for k in which:
        def load():
            e.uc.mem_write(blk, FI.inst_full(k)); e.uc.mem_write(blk + A.B_DIRTY, b"\x01")
        ld = meas(load, 1)
        tick(30)
        sil = meas(lambda: None, 50)
        held = meas(lambda: [on(x) for x in chord], 100)
        dirt = meas(lambda: None, 50, dirty=True)
        rel = meas(lambda: [off(x) for x in chord], 100)
        tick(2000)
        f = lambda m: f"{m[0]:8.0f} {m[1]:6.1f}" + (f" s{m[2]}" if m[2] else "") + (f" d{m[3]}" if m[3] else "")
        print(f"{FI.INST[k]['name'][:16]:16s} {f(ld):>18s} {f(sil):>16s} {f(held):>16s} {f(dirt):>16s} {f(rel):>16s}")


if __name__ == "__main__":
    img = Path(sys.argv[1]).read_bytes(); man = json.loads(Path(sys.argv[2]).read_text())
    which = [int(x) for x in sys.argv[3:]] or [0, 1, 2, 3, 4, 5]
    main(img, man, which)
