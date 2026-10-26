"""SC47.3 ARM test (poly.use_v2): poly with two oscillators and in the VA-drum (emu_poly's harness: the real controller and note vtable, the whole
DSP service chain with poly's tick at its head, the DSP's writes into a dict).

    python tools/emu_poly2.py NEW.bin NEW_manifest.json

  * the plain oscillator, poly on: the base written; two oscillators: the base stays (poly allowed now; emu_poly expects 0 there);
  * the VA-drum (the mode row's pad 20): the base written; notes 60 / 64: a voice each; 60 let go with 64 held: its target kept (it rings through
    its own envelope); 64 let go: kept too; a new note (67) with none held: 60 and 64 keep their targets, 67 on a third voice; five hits: the
    oldest taken (faded first, then started);
  * the sample mode: still poly.
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
import modmx as MX  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
import modesel as MS  # noqa: E402
V = EP.V
MGR = T.MGR


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]
    P.adopt(R)                                                                        # (SC47.6: the six-record layout)
    e = T.EL(img)
    vl = {k: int(v, 16) for k, v in R["vcf20"]["labels"].items()}
    sl = {k: int(v, 16) for k, v in R["sc06"]["labels"].items()}
    pl = {k: int(v, 16) for k, v in R["poly"]["labels"].items()}
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
    rec = lambda v, f: VD.PV_REC0 + VD.PV_RS * v + f
    PVW = VD.OS2B0 + VD.PV_OFF
    def tick(n=1):
        for _ in range(n): e.at(e.t + 1); e.call(pl["c_pytick"], maxins=8_000_000)
    non, noff = e.r32(MX.NOTE_VT) & ~1, e.r32(MX.NOTE_VT + 4) & ~1
    def on(n, v=100): e.call(non, EP.TXOBJ, 2, n, v, maxins=8_000_000)
    def off(n): e.call(noff, EP.TXOBJ, 2, n, 0, maxins=8_000_000)
    def mode(k):
        e.uc.mem_write(MS.RAM, bytes(8)); e.pad(26); e.pad(MS.ROW + k); e.pad(26)
    def tgt(n): return [dsp.get(rec(v, VD.PV_TGT)) for v in range(4) if dsp.get(rec(v, VD.PV_NOTE)) == n]
    e.btn(2); e.btn(8); mode(2)
    if "c_vmset" in pl: e.call(pl["c_vmset"], 0, 3, maxins=1_000_000)               # (SC47.5: the voice mode; Shift + pad 29 steps through five)
    else:
        for _ in range(2): e.set_p0(e.r32(MGR + 0xC), 1); e.pad(P.PAD29); e.set_p0(e.r32(MGR + 0xC), 0)     # retrigger -> legato -> poly
    tick(2)
    check(dsp.get(PVW) == VD.PV_REC0, "the plain oscillator, poly: the base written")
    e.call(vl["c_vflip7"], 0, V.RT_VEL, maxins=1_000_000); tick(2)                     # two oscillators
    check(dsp.get(PVW) == VD.PV_REC0, f"two oscillators: poly (the base stays, {dsp.get(PVW)})")
    e.call(vl["c_vflip7"], 0, V.RT_VEL, maxins=1_000_000); tick(2)
    # ---- the VA-drum
    mode(3); tick(2)
    check(dsp.get(PVW) == VD.PV_REC0, f"the VA-drum: poly (the base written, {dsp.get(PVW)})")
    on(60, 100); on(64, 90); tick(1)
    check(tgt(60) == [100 << 16] and tgt(64) == [90 << 16], f"the VA-drum: notes 60 / 64, a voice each ({tgt(60)}, {tgt(64)})")
    off(60); tick(2)
    check(tgt(60) == [100 << 16], f"60 let go with 64 held: its target kept (it rings through its envelope) ({tgt(60)})")
    off(64); tick(2)
    check(tgt(64) == [90 << 16], "64 let go: kept too")
    on(67, 80); tick(3)
    check(tgt(60) == [100 << 16] and tgt(64) == [90 << 16] and tgt(67) == [80 << 16], f"a new hit with none held: the others ring on, 67 on a third voice ({tgt(60)}, {tgt(64)}, {tgt(67)})")
    off(67)
    on(69, 70); tick(3); off(69)
    old = [v for v in range(4) if dsp.get(rec(v, VD.PV_NOTE)) == 60]
    on(71, 75); tick(1)
    t1 = dsp.get(rec(old[0], VD.PV_TGT)) if old else None; tick(2)
    check(old and t1 == 0 and dsp.get(rec(old[0], VD.PV_NOTE)) == 71 and dsp.get(rec(old[0], VD.PV_TGT)) == 75 << 16,
          f"a fifth hit: the oldest (60) faded first ({t1}), then 71 on its voice")
    off(71); tick(2)
    # ---- the sample mode
    mode(5); tick(2)
    check(dsp.get(PVW) == VD.PV_REC0, "the sample mode: poly")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} POLY2 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
