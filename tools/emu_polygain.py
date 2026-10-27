"""SC48 ARM test (poly.use_v7): in the poly mode each voice's level = velocity x 1 / sqrt(the voices sounding), so a chord does not clip
(emu_unimode's harness; the DSP writes caught):
  * the oscillator, poly: 1 note = velocity << 16 (as before); 2, 3, 4 notes held = every sounding voice's target x 181 / 148 / 128 (/ 256);
    one let go: the others back to the three-voice level;
  * FM poly alone (six voices): six notes = x 105 / 256 each;
  * uni retrig: unchanged (the unison's own scaling).

    python tools/emu_polygain.py SC48.bin SC48_manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_poly as EP  # noqa: E402
import poly as P  # noqa: E402
import vmode as VM  # noqa: E402
import modmx as MX  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
import modesel as MS  # noqa: E402
import fmeng as F  # noqa: E402


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]
    assert P.adopt(R), "a build with poly.use_v5"
    VM.use_v2()
    e = T.EL(img)
    vl = {k: int(v, 16) for k, v in R["vcf20"]["labels"].items()}
    sl = {k: int(v, 16) for k, v in R["sc06"]["labels"].items()}
    pl = {k: int(v, 16) for k, v in R["poly"]["labels"].items()}
    ml = {k: int(v, 16) for k, v in R["vmode"]["labels"].items()}
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    for ad in (sl["c_non"], sl["c_noff"], EP.STOCK_TX_ON, EP.STOCK_TX_OFF, EP.REC_GATE):
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: skip(uc), begin=ad, end=ad)
    dsp = {}
    def w(uc, a, s, d): dsp[uc.reg_read(UC_ARM_REG_R2)] = uc.reg_read(UC_ARM_REG_R1) >> 8; skip(uc)
    e.uc.hook_add(UC_HOOK_CODE, w, begin=P.DSP_WRITE, end=P.DSP_WRITE)
    def rd(uc, a, s, d): uc.reg_write(UC_ARM_REG_R0, 0); skip(uc)
    e.uc.hook_add(UC_HOOK_CODE, rd, begin=0x08029344, end=0x08029344)
    e.at(100000); e.transport(0)
    for _ in range(30): e.at(e.t + 40); e.call(vl["c_vtick"], maxins=3_000_000)
    rec = lambda t, v, f: VD.PV_REC0 + VD.PV_RS * (VD.PV_N * t + v) + f
    def tick(n=1):
        for _ in range(n): e.at(e.t + 1); e.call(ml["c_vmtick"], maxins=8_000_000)
    non, noff = e.r32(MX.NOTE_VT) & ~1, e.r32(MX.NOTE_VT + 4) & ~1
    def on(n, v=100): e.call(non, EP.TXOBJ, 2, n, v, maxins=8_000_000)
    def off(n): e.call(noff, EP.TXOBJ, 2, n, 0, maxins=8_000_000)
    def mode(k): e.uc.mem_write(MS.RAM, bytes(8)); e.pad(26); e.pad(MS.ROW + k); e.pad(26)
    tgts = lambda: sorted(dsp.get(rec(0, v, VD.PV_TGT), 0) for v in range(VD.PV_N))
    lvl = lambda g: (100 << 16 >> 8) * g if g != 256 else 100 << 16
    e.btn(2); e.btn(8); mode(2)
    e.call(pl["c_vmset"], 0, 3, maxins=1_000_000); tick(3)
    got = []
    for k, n in enumerate((60, 64, 67, 71)):
        on(n); tick(4); got.append([t for t in tgts() if t])
    want = [[lvl(g)] * (k + 1) for k, g in enumerate((256, 181, 148, 128))]
    check(got == want, f"the oscillator, poly: 1-4 notes ({[g[0] if g else None for g in got]} = {[w_[0] for w_ in want]})")
    off(71); tick(6)
    check([t for t in tgts() if t] == [lvl(148)] * 3, f"one let go: the others at the three-voice level ({[t for t in tgts() if t]})")
    for n in (60, 64, 67): off(n)
    tick(10)
    mode(F.ROWPAD - MS.ROW); e.call(pl["c_vmset"], 0, 3, maxins=1_000_000); tick(4)
    for n in (48, 52, 55, 60, 64, 67): on(n); tick(3)
    tick(4)
    six = [t for t in tgts() if t]
    check(six == [lvl(105)] * 6, f"FM poly, six notes: x 105 / 256 each ({six})")
    for n in (48, 52, 55, 60, 64, 67): off(n)
    tick(10)
    mode(2); e.call(pl["c_vmset"], 0, 4, maxins=1_000_000); tick(4)
    on(60); tick(4); uni = [t for t in tgts() if t]
    check(uni and len(set(uni)) == 1 and uni[0] == (100 << 16) // 2, f"uni retrig: the unison's own scaling, x 1/2 ({uni})")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())) else 0)
