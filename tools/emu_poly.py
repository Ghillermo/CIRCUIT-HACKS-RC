"""SC47 ARM test (poly.py): the voices of MIDI 1 / 2's own engine.

    python tools/emu_poly.py NEW.bin NEW_manifest.json

The real controller, the template view, the note vtable (vcf21's c_vnon / c_vnoff through poly's entries; SC06's c_non / c_noff, the stock's MIDI
out and the recorder skipped), the whole DSP service chain (poly's tick is its head; the DSP's writes into a dict, its reads 0):
  * Shift + pad 29 (MIDI 1's Preset view, the engine on): retrigger -> legato -> poly -> retrigger (retrig's byte 0xA0 / A1 / A4 / A0); with Shift
    and poly pad 29 magenta;
  * poly on in the plain oscillator: the first tick writes the four records from scratch (G, target, TRIG, TSEEN 0; K) and then OSC2 + 38 = the
    records' base;
  * notes 60 / 64 / 67 / 71: one voice each (NOTE, TV 1, the target = velocity << 16, TRIG 1) at the next tick, the engine's VEL 127;
  * a fifth note (74): the oldest voice (60) fades (target 0), its start 2 ticks later (NOTE 74, TRIG 2);
  * a note-off with others held: that voice's target 0; all let go: the last one keeps its target (the release); a new note then: the ringing
    one off, the new one on a free voice;
  * the sample mode with a pending flip (0xC0 | 7): TV $107, the flip left for the engine's TRIG;
  * velocity 0: nothing; FM on / two oscillators / poly off: OSC2 + 38 = 0.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
import poly as P  # noqa: E402
import modmx as MX  # noqa: E402
import vcf21_dsp as VD  # noqa: E402

V = T4.V
MGR = T.MGR
STOCK_TX_ON, STOCK_TX_OFF, REC_GATE = 0x08029EFE, 0x08029F2A, 0x0802E56A
TXOBJ = 0x20011334


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]
    e = T.EL(img)
    vl = {k: int(v, 16) for k, v in R["vcf20"]["labels"].items()}
    sl = {k: int(v, 16) for k, v in R["sc06"]["labels"].items()}
    pl = {k: int(v, 16) for k, v in R["poly"]["labels"].items()}
    rl = {k: int(v, 16) for k, v in R["retrig"]["labels"].items()}
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    for ad in (sl["c_non"], sl["c_noff"], STOCK_TX_ON, STOCK_TX_OFF, REC_GATE):
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: skip(uc), begin=ad, end=ad)
    dsp, log = {}, []
    def w(uc, a, s, d):
        v, ad = uc.reg_read(UC_ARM_REG_R1) >> 8, uc.reg_read(UC_ARM_REG_R2); dsp[ad] = v; log.append((ad, v)); skip(uc)
    e.uc.hook_add(UC_HOOK_CODE, w, begin=P.DSP_WRITE, end=P.DSP_WRITE)
    def rd(uc, a, s, d): uc.reg_write(UC_ARM_REG_R0, 0); skip(uc)
    e.uc.hook_add(UC_HOOK_CODE, rd, begin=0x08029344, end=0x08029344)
    e.at(100000); e.transport(0)
    for _ in range(30): e.at(e.t + 40); e.call(vl["c_vtick"], maxins=3_000_000)     # past the engine's first ticks (they restore its saved state)
    rec = lambda v, f: VD.PV_REC0 + VD.PV_RS * v + f
    PVW = VD.OS2B0 + VD.PV_OFF
    def tick(n=1):
        for _ in range(n): e.at(e.t + 1); e.call(pl["c_pytick"], maxins=8_000_000)
    non, noff = e.r32(MX.NOTE_VT) & ~1, e.r32(MX.NOTE_VT + 4) & ~1
    def on(n, v=100): e.call(non, TXOBJ, 2, n, v, maxins=8_000_000)
    def off(n): e.call(noff, TXOBJ, 2, n, 0, maxins=8_000_000)
    def rbyte():
        e.call(rl["c_rtb"], maxins=100000); return e.r8(e.uc.reg_read(UC_ARM_REG_R0))
    vel7 = lambda: e.r8(P.RT0 + V.RT_VEL) & 0x7F

    # ---- the engine on in the plain oscillator; the gesture
    import modesel as MS
    import os
    def mode(k):                                                                    # the mode row (pad 27 opens it): k = 2 oscillator, 5 sample
        e.uc.mem_write(MS.RAM, bytes(8)); e.pad(26)                                  # (the RAM dump's bytes there: closed first)
        e.pad(MS.ROW + k); e.pad(26)
    e.btn(2); e.btn(8); mode(2)
    seq = []
    for _ in range(3):
        e.set_p0(e.r32(MGR + 0xC), 1); e.pad(P.PAD29); e.set_p0(e.r32(MGR + 0xC), 0); seq.append(rbyte())
    check(seq == [0xA1, 0xA4, 0xA0], f"Shift + pad 29: retrigger -> legato -> poly -> retrigger ({[hex(x) for x in seq]})")
    e.set_p0(e.r32(MGR + 0xC), 1); e.pad(P.PAD29); e.pad(P.PAD29); f = X.frame(e); e.set_p0(e.r32(MGR + 0xC), 0)
    check(rbyte() == 0xA4 and f[P.PAD29] & 0xFF == P.COL_POLY, f"poly: pad 29 magenta with Shift ({f[P.PAD29]:#x})")

    # ---- the edge
    log.clear(); tick(1)
    fields = all(dsp.get(rec(v, fld), -1) == 0 for v in range(4) for fld in (VD.PV_G, VD.PV_TGT, VD.PV_TRIG, VD.PV_SEEN))
    order = [ad for ad, _ in log]
    check(fields and dsp.get(PVW) == VD.PV_REC0 and order.index(PVW) > max(order.index(rec(v, VD.PV_SEEN)) for v in range(4))
          and all(dsp.get(rec(v, P.KW)) == 1 for v in range(4)), "poly on: the four records from scratch (K 1), then OSC2 + 38 = the base")

    # ---- four notes
    for i, n in enumerate((60, 64, 67, 71)): on(n, 90 + i)
    tick(1)
    got = [(dsp.get(rec(v, VD.PV_NOTE)), dsp.get(rec(v, VD.PV_TGT)), dsp.get(rec(v, VD.PV_TRIG)), dsp.get(rec(v, VD.PV_TV))) for v in range(4)]
    want = [(n, (90 + i) << 16, 1, 1) for i, n in enumerate((60, 64, 67, 71))]
    check(sorted(got) == sorted(want) and vel7() == 127, f"four notes: a voice each at the next tick, the engine's VEL 127 ({got})")
    v60 = [v for v in range(4) if dsp.get(rec(v, VD.PV_NOTE)) == 60][0]
    # ---- the fifth: the oldest fades, then starts
    on(74, 110); tick(1)
    t1 = dsp.get(rec(v60, VD.PV_TGT)); tick(1); t2n = dsp.get(rec(v60, VD.PV_NOTE)); tick(1)
    check(t1 == 0 and t2n == 60 and dsp.get(rec(v60, VD.PV_NOTE)) == 74 and dsp.get(rec(v60, VD.PV_TRIG)) == 2 and dsp.get(rec(v60, VD.PV_TGT)) == 110 << 16,
          f"a fifth note: the oldest (60, voice {v60}) faded first (target {t1}), started 2 ticks later (NOTE {dsp.get(rec(v60, VD.PV_NOTE))}, TRIG {dsp.get(rec(v60, VD.PV_TRIG))})")
    # ---- note-off with others held; all let go
    v64 = [v for v in range(4) if dsp.get(rec(v, VD.PV_NOTE)) == 64][0]
    off(64); tick(1)
    check(dsp.get(rec(v64, VD.PV_TGT)) == 0, f"a note-off with others held: its voice off (voice {v64})")
    for n in (67, 71): off(n)
    tick(1)
    v74 = v60
    keep = dsp.get(rec(v74, VD.PV_TGT))
    off(74); tick(3)
    check(dsp.get(rec(v74, VD.PV_TGT)) == keep == 110 << 16, "the last note let go: its voice rings on (the target kept: the shared release)")
    on(62, 100); tick(3)
    nv = [v for v in range(4) if dsp.get(rec(v, VD.PV_NOTE)) == 62]
    check(dsp.get(rec(v74, VD.PV_TGT)) == 0 and nv and nv[0] != v74 and dsp.get(rec(nv[0], VD.PV_TGT)) == 100 << 16,
          f"a new note with none held: the ringing voice off, the note on another ({nv})")
    off(62); tick(2)
    # ---- velocity 0
    trig = {v: dsp.get(rec(v, VD.PV_TRIG)) for v in range(4)}
    on(65, 0); tick(3)
    check({v: dsp.get(rec(v, VD.PV_TRIG)) for v in range(4)} == trig, "velocity 0: no voice")
    # ---- the sample mode, a pending flip
    mode(5)
    log.clear(); tick(2)
    e.call(vl["c_vsmpb"], 0, maxins=100000); pb = e.uc.reg_read(UC_ARM_REG_R0)
    if pb: e.uc.mem_write(pb, bytes([0xC7]))
    on(69, 100); tick(3)
    sv = [v for v in range(4) if dsp.get(rec(v, VD.PV_NOTE)) == 69]
    check(pb and sv and dsp.get(rec(sv[0], VD.PV_TV)) == 0x107 and e.r8(pb) == 0xC7, f"the sample mode: a pending flip = TV $107, left for the engine ({sv}, {pb:#x})")
    off(69); tick(2)
    # ---- poly off / not allowed
    mode(2)
    e.call(vl["c_vflip7"], 0, V.RT_VEL, maxins=1_000_000); tick(2)                    # two oscillators
    check(dsp.get(PVW) == 0, f"two oscillators: OSC2 + 38 = 0 ({dsp.get(PVW)})")
    e.call(vl["c_vflip7"], 0, V.RT_VEL, maxins=1_000_000); tick(2)
    check(dsp.get(PVW) == VD.PV_REC0, "one oscillator again: the base back")
    e.set_p0(e.r32(MGR + 0xC), 1); e.pad(P.PAD29); e.set_p0(e.r32(MGR + 0xC), 0); tick(2)
    check(rbyte() == 0xA0 and dsp.get(PVW) == 0, "Shift + pad 29 again: retrigger, OSC2 + 38 = 0")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} POLY ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
