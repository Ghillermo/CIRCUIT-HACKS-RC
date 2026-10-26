"""SC47.6 ARM test (poly.use_v5, vmode.use_v2): the unison's three modes and six FM voices in unison (emu_vmode's harness).

    python tools/emu_unimode.py NEW.bin NEW_manifest.json

  * the row has seven modes (pads 17-23); pad 22 = uni portamento: the records on, no new gate over a held note, GK written;
  * uni portamento: a note starts every voice (TRIG + 1); another over it only moves them (NOTE, the same TRIG); no jump;
  * uni glide (pad 23): a detached note sends the jump (OSC2 + 47 = the counter + 1) before the voices' NOTEs; one over it only moves them, no
    jump; a detached one again: the next jump;
  * uni retrig (pad 21): a note over a held one starts them again (TRIG + 1);
  * FM in unison alone: six voices on the note, their offsets spread over +-detune x 258 in five steps.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_poly as EP  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import poly as P  # noqa: E402
import vmode as VM  # noqa: E402
import modmx as MX  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
import modesel as MS  # noqa: E402
import fmeng as F  # noqa: E402
MGR = T.MGR


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
    rl = {k: int(v, 16) for k, v in R["retrig"]["labels"].items()}
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    for ad in (sl["c_non"], sl["c_noff"], EP.STOCK_TX_ON, EP.STOCK_TX_OFF, EP.REC_GATE):
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: skip(uc), begin=ad, end=ad)
    dsp, log = {}, []
    def w(uc, a, s, d):
        v, ad = uc.reg_read(UC_ARM_REG_R1) >> 8, uc.reg_read(UC_ARM_REG_R2); dsp[ad] = v; log.append((ad, v)); skip(uc)
    e.uc.hook_add(UC_HOOK_CODE, w, begin=P.DSP_WRITE, end=P.DSP_WRITE)
    def rd(uc, a, s, d): uc.reg_write(UC_ARM_REG_R0, 0); skip(uc)
    e.uc.hook_add(UC_HOOK_CODE, rd, begin=0x08029344, end=0x08029344)
    e.at(100000); e.transport(0)
    for _ in range(30): e.at(e.t + 40); e.call(vl["c_vtick"], maxins=3_000_000)
    rec = lambda t, v, f: VD.PV_REC0 + VD.PV_RS * (VD.PV_N * t + v) + f
    JMP = VD.OS2B0 + VD.JMP_OFF
    def tick(n=1):
        for _ in range(n): e.at(e.t + 1); e.call(ml["c_vmtick"], maxins=8_000_000)
    non, noff = e.r32(MX.NOTE_VT) & ~1, e.r32(MX.NOTE_VT + 4) & ~1
    def on(n, v=100, t=0): e.call(non, EP.TXOBJ, 2 + t, n, v, maxins=8_000_000)
    def off(n, t=0): e.call(noff, EP.TXOBJ, 2 + t, n, 0, maxins=8_000_000)
    def mode(k): e.uc.mem_write(MS.RAM, bytes(8)); e.pad(26); e.pad(MS.ROW + k); e.pad(26)
    def r0(fn, *a): e.call(fn, *a, maxins=4_000_000); return e.uc.reg_read(UC_ARM_REG_R0)
    vm = lambda t: r0(pl["c_vmget"], t)
    def frame(): e.at(e.t + 20); return X.frame(e)
    s16 = lambda v: v - (1 << 24) if v & 0x800000 else v
    def pick(m): e.pad(31); frame(); e.pad(16 + m); frame(); e.pad(31)
    trigs = lambda: [dsp.get(rec(0, v, VD.PV_TRIG)) for v in range(4)]
    notes = lambda n=4: [dsp.get(rec(0, v, VD.PV_NOTE)) for v in range(n)]

    e.btn(2); e.btn(8); mode(2)
    e.call(pl["c_vmset"], 0, 0, maxins=1_000_000); e.call(pl["c_vmset"], 1, 0, maxins=1_000_000)
    tick(2)
    e.pad(31); f = frame(); e.pad(31)
    row = [f[16 + k] & 0xFF for k in range(7)]
    check(row == [VM.COLS[0][0]] + [VM.COLS[k][1] for k in range(1, 7)], f"the row: seven modes on pads 17-23 ({[hex(x) for x in row]})")
    # ---- uni portamento
    pick(5); log.clear(); tick(3)
    gw = [v for a, v in log if a == VD.OS2B0 + VD.GK_OFF]
    check(vm(0) == 5 and r0(rl["c_rtoff"], 0) == 1 and r0(pl["c_pyflag"], 0) == 1 and r0(pl["c_pyuni"], 0) == 1 and gw == [VM.gk(e.r8(VM.RAM + 8))],
          f"pad 22 = uni portamento: the records, no new gate over a held note, GK written ({[hex(x) for x in gw]})")
    log.clear(); on(60); tick(3); t1 = trigs()
    on(64); log.clear(); tick(3); t2 = trigs()
    jm = [a for a, v in log if a == JMP]
    check(notes() == [64] * 4 and t2 == t1 and None not in t1 and not jm, f"a note over a held one: the voices move ({notes()}), the same TRIG ({t1} / {t2}), no jump")
    off(64); off(60); tick(3)
    # ---- uni glide
    pick(6); tick(3)
    j0 = dsp.get(JMP)
    log.clear(); on(48); tick(3)
    order = [a for a, v in log]
    jmps = [v for a, v in log if a == JMP]
    first_note = min([i for i, a in enumerate(order) if a in [rec(0, v, VD.PV_NOTE) for v in range(4)]], default=-1)
    check(vm(0) == 6 and len(jmps) == 1 and order.index(JMP) < first_note and notes() == [48] * 4,
          f"uni glide, a detached note: the jump ({j0} -> {jmps}) before the voices' NOTEs, every voice on it")
    t1 = trigs(); log.clear(); on(55); tick(3)
    check(notes() == [55] * 4 and trigs() == t1 and not [a for a, v in log if a == JMP], "a note over it: the voices move, the same TRIG, no jump")
    off(55); off(48); tick(3)
    log.clear(); on(50); tick(3)
    jmps2 = [v for a, v in log if a == JMP]
    check(jmps2 == [(jmps[0] + 1) & 0xFF] if jmps else False, f"a detached note again: the next jump ({jmps2})")
    off(50); tick(3)
    # ---- uni retrig
    pick(4); tick(2)
    on(60); tick(3); t1 = trigs(); on(62); tick(3); t2 = trigs()
    check(vm(0) == 4 and all(b == (a + 1) & 0xFFFF for a, b in zip(t1, t2)) and notes() == [62] * 4, f"uni retrig: a note over a held one starts them again ({t1} -> {t2})")
    off(62); off(60); tick(3)
    # ---- FM in unison: six voices
    mode(F.ROWPAD - MS.ROW); e.call(pl["c_vmset"], 0, 4, maxins=1_000_000); e.uc.mem_write(VM.RAM + 10, bytes([40])); tick(4)
    on(60); tick(3)
    h = 40 * P.DT_K
    dts = [s16(dsp.get(rec(0, v, P.O_DTW), 0)) for v in range(6)]
    want = [h * (2 * v - 5) // 5 if 2 * v - 5 >= 0 else -((h * (5 - 2 * v)) // 5) for v in range(6)]
    fmb = [dsp.get(rec(0, v, VD.PV_FMB)) for v in range(6)]
    check(notes(6) == [60] * 6 and dts == want and fmb == VD.FV_ADDRS, f"FM in unison: six voices on the note, the offsets {dts} ({want}), their blocks {[hex(x) for x in fmb]}")
    off(60); tick(2)
    del e; gc.collect()
    print(f"{man.get('marker', '?')} UNIMODE ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
