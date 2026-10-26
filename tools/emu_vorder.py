"""SC47.7 ARM test (poly.use_v6, vmode.use_v3): the voice modes in the user's order and meaning (emu_vmode's harness).

    python tools/emu_vorder.py NEW.bin NEW_manifest.json

  * pads 17-24 = retrigger, legato, glide, uni retrig, uni legato, uni glide, uni always-glide, poly (the same colour for the same name, the
    current bright); Shift + pad 29 steps in that order (poly -> retrigger);
  * glide (pad 19): GK written, no new gate over a held note; one voice: a detached note sends the jump, a note over a held one does not, a
    detached one again sends the next;
  * uni legato (pad 21): GK 0; the records on; a note over a held one only moves the voices (the same TRIG), no jump;
  * uni glide (pad 22): GK written; a detached note sends the jump;
  * uni always-glide (pad 23): the DSP's GK the time's (the same as uni glide's: not written again); a detached note starts the voices with no jump (they slide from the last note); one over a held note
    only moves them; poly (pad 24): the records, GK 0.
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
MGR = T.MGR


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]
    assert P.adopt(R) and R["vmode"]["prev"].get("v3"), "a build with vmode.use_v3"
    VM.use_v2(); VM.use_v3()
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
    JMP, GKA = VD.OS2B0 + VD.JMP_OFF, VD.OS2B0 + VD.GK_OFF
    def tick(n=1):
        for _ in range(n): e.at(e.t + 1); e.call(ml["c_vmtick"], maxins=8_000_000)
    non, noff = e.r32(MX.NOTE_VT) & ~1, e.r32(MX.NOTE_VT + 4) & ~1
    def on(n, v=100, t=0): e.call(non, EP.TXOBJ, 2 + t, n, v, maxins=8_000_000)
    def off(n, t=0): e.call(noff, EP.TXOBJ, 2 + t, n, 0, maxins=8_000_000)
    def mode(k): e.uc.mem_write(MS.RAM, bytes(8)); e.pad(26); e.pad(MS.ROW + k); e.pad(26)
    def r0(fn, *a): e.call(fn, *a, maxins=4_000_000); return e.uc.reg_read(UC_ARM_REG_R0)
    vm = lambda t: r0(pl["c_vmget"], t)
    def frame(): e.at(e.t + 20); return X.frame(e)
    def pick(k): e.pad(31); frame(); e.pad(16 + k); frame(); e.pad(31)
    def shift(o): e.set_p0(e.r32(MGR + 0xC), 1 if o else 0)
    trigs = lambda: [dsp.get(rec(0, v, VD.PV_TRIG)) for v in range(4)]
    notes = lambda: [dsp.get(rec(0, v, VD.PV_NOTE)) for v in range(4)]
    jumps = lambda: [v for a, v in log if a == JMP]
    gks = lambda: [v for a, v in log if a == GKA]

    e.btn(2); e.btn(8); mode(2)
    e.call(pl["c_vmset"], 0, 0, maxins=1_000_000); e.call(pl["c_vmset"], 1, 0, maxins=1_000_000)
    tick(2)
    e.pad(31); f = frame(); e.pad(31)
    row = [f[16 + k] & 0xFF for k in range(8)]
    want = [VM.COLS[0][0]] + [VM.COLS[m][1] for m in VM.ORDER[1:]]
    same = VM.COLS[0] == VM.COLS[4] and VM.COLS[1] == VM.COLS[5] and VM.COLS[2] == VM.COLS[6]
    check(row == want and same, f"pads 17-24: retrigger, legato, glide, uni retrig, uni legato, uni glide, uni always-glide, poly; the same names the same colours ({[hex(x) for x in row]})")
    seq = []
    for _ in range(8): shift(True); e.pad(28); shift(False); seq.append(vm(0))
    check(seq == [1, 2, 4, 5, 6, 7, 3, 0], f"Shift + pad 29 in the pads' order ({seq})")
    # ---- glide: one voice
    pick(2); log.clear(); tick(3)
    check(vm(0) == 2 and r0(rl["c_rtoff"], 0) == 1 and r0(pl["c_pyflag"], 0) == 0 and gks() == [VM.gk(e.r8(VM.RAM + 8))],
          f"pad 19 = glide: no new gate over a held note, one voice, GK written ({gks()})")
    log.clear(); on(60); tick(2); j1 = jumps()
    log.clear(); on(64); tick(2); j2 = jumps()
    off(64); off(60); tick(2)
    log.clear(); on(67); tick(2); j3 = jumps(); off(67); tick(2)
    check(len(j1) == 1 and not j2 and j3 == [(j1[0] + 1) & 0xFF] if j1 else False, f"glide: a detached note jumps ({j1}), one over a held note glides ({j2}), detached again ({j3})")
    # ---- uni legato
    pick(4); log.clear(); tick(3)
    check(vm(0) == 5 and r0(pl["c_pyflag"], 0) == 1 and gks() == [0], f"pad 21 = uni legato: the records, GK 0 ({gks()})")
    on(60); tick(3); t1 = trigs(); log.clear(); on(64); tick(3)
    check(notes() == [64] * 4 and trigs() == t1 and not jumps(), f"uni legato: a note over a held one moves the voices, the same TRIG, no jump ({notes()})")
    off(64); off(60); tick(3)
    # ---- uni glide, poly
    pick(5); log.clear(); tick(3); g6 = gks()
    log.clear(); on(48); tick(3)
    check(vm(0) == 6 and g6 == [VM.gk(e.r8(VM.RAM + 8))] and len(jumps()) == 1 and notes() == [48] * 4, f"pad 22 = uni glide: GK written, a detached note jumps ({jumps()})")
    off(48); tick(3)
    # ---- uni always-glide
    pick(6); log.clear(); tick(3); g7 = gks()
    log.clear(); on(50); tick(3); t1 = trigs(); j1 = jumps()
    log.clear(); on(53); tick(3)
    check(vm(0) == 7 and r0(rl["c_rtoff"], 0) == 1 and dsp.get(GKA) == VM.gk(e.r8(VM.RAM + 8)) and not j1 and notes() == [53] * 4 and trigs() == t1 and not jumps(),
          f"pad 23 = uni always-glide: GK written, a detached note with no jump, one over it only moves the voices (the DSP's GK {dsp.get(GKA)}, jumps {j1})")
    off(53); off(50); tick(3)
    pick(7); log.clear(); tick(3)
    check(vm(0) == 3 and r0(pl["c_pyflag"], 0) == 1 and gks() == [0], "pad 24 = poly: the records, GK 0")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} VORDER ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
