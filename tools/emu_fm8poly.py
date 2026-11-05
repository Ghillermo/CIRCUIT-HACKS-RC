"""SC51.7 ARM test (poly.use_v11 + fm8): the 8-operator FM polyphonic (emu_poly3's harness: the real controller and note vtable, the whole DSP
service chain, the DSP's writes into a dict).

    python tools/emu_fm8poly.py SC51.7.bin SC51.7_manifest.json
  * MIDI 1 in FM, poly: six voices; the track's own slot (X:FMB0) left alone, its FM flag 1;
  * notes 60 / 64: a voice each; its record's PV_FMB = its slot (X:$4000 + 128 s); R / AMP of its operators in its slot (16 words each), N there;
    at its first use the slot's smoothed AMP / y[n - 2] 0; the noise at the record's + 10;
  * a DX7 algorithm (6 operators): N 6 in the voices' slots;
  * 60 let go with 64 held: rings, then (its envelopes below E_OFF) freed; 64 still sounding;
  * the shed's loudness (c_fmloud) of a ringing voice > 0, of a free one 0.
"""
from __future__ import annotations
import json, struct, sys
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
import fmeng as FE  # noqa: E402
import fm8 as F  # noqa: E402
import fm8arm as A  # noqa: E402


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]
    P.adopt(R)
    VD.use_fm8()
    e = T.EL(img)
    vl = {k: int(v, 16) for k, v in R["vcf20"]["labels"].items()}
    sl = {k: int(v, 16) for k, v in R["sc06"]["labels"].items()}
    pl = {k: int(v, 16) for k, v in R["poly"]["labels"].items()}
    fl = {k: int(v, 16) for k, v in R["fmeng"]["labels"].items()}
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
    FV = lambda s: VD.FV_ADDRS[s]
    def tick(n=1):
        for _ in range(n): e.at(e.t + 1); e.call(pl["c_pytick"], maxins=8_000_000)
    non, noff = e.r32(MX.NOTE_VT) & ~1, e.r32(MX.NOTE_VT + 4) & ~1
    def on(n, v=100, t=0): e.call(non, EP.TXOBJ, 2 + t, n, v, maxins=8_000_000)
    def off(n, t=0): e.call(noff, EP.TXOBJ, 2 + t, n, 0, maxins=8_000_000)
    def mode(k):
        e.uc.mem_write(MS.RAM, bytes(8)); e.pad(26); e.pad(MS.ROW + k); e.pad(26)
    def poly_on(t=0): e.call(pl["c_vmset"], t, 3, maxins=1_000_000)
    def voices(t, n): return [v for v in range(VD.PV_N) if dsp.get(rec(t, v, VD.PV_NOTE)) == n and dsp.get(rec(t, v, VD.PV_TGT))]
    blk = A.FM8R + A.TB0
    vmax = lambda t: e.r8(P.PY + 4 + P.TBS * t + P.O_VMAX)
    written = lambda lo, hi: [a for a, _ in log if lo <= a < hi]

    e.btn(2); e.btn(8); mode(FE.ROWPAD - MS.ROW); poly_on()
    for k in range(8): e.uc.mem_write(blk + F.OPB * k + F.O_R + 3, bytes([90]))      # a short release
    tick(3); log.clear(); tick(4)
    check(vmax(0) == 6, f"MIDI 1 in FM poly: {vmax(0)} voices")
    check(not written(VD.FMB0, VD.FMB0 + 128) and dsp.get(VD.OSB0 + VD.FM_FLAG) == 1, "the track's own slot left alone, its FM flag 1")

    log.clear(); on(60, 100); on(64, 90); tick(2)
    v60, v64 = voices(0, 60), voices(0, 64)
    ok = len(v60) == 1 and len(v64) == 1
    check(ok, f"notes 60 / 64: a voice each ({v60}, {v64})")
    if ok:
        a, b = v60[0], v64[0]
        order = [ad for ad, _ in log]
        check(dsp.get(rec(0, a, VD.PV_FMB)) == FV(a), f"PV_FMB = the slot ({dsp.get(rec(0, a, VD.PV_FMB))}, {FV(a)})")
        r_ok = all(dsp.get(FV(s) + 16 * k + VD.F_R) for s in (a, b) for k in range(4))
        amp = [dsp.get(FV(a) + 16 * k + VD.F_AMP) for k in range(4)]
        check(r_ok and any(amp) and dsp.get(FV(a) + VD.F8_N) == 4, f"R / AMP / N in each voice's slot (AMP of 60's {amp})")
        z = all((FV(s) + 16 * k + VD.F8_AS) in order and (FV(s) + 16 * k + VD.F8_O2) in order for s in (a, b) for k in range(8))
        check(z and not written(VD.OSB0 + VD.NZ_OFF, VD.OSB0 + VD.NZ_OFF + 1), "the first use: the slot's AMP_s / y[n - 2] 0; no noise at OSC1's")
        e.call(fl["c_fmloud"], a); loud = e.uc.reg_read(UC_ARM_REG_R0)
        off(60); tick(2)
        check(dsp.get(rec(0, a, VD.PV_TGT)) == 100 << 16 and loud > 0, f"60 let go with 64 held: its target kept (the release rings); loudness {loud}")
        n = 0
        while dsp.get(rec(0, a, VD.PV_TGT)) and n < 3000: tick(10); n += 10
        check(dsp.get(rec(0, a, VD.PV_TGT)) == 0 and 0 < n < 3000 and dsp.get(rec(0, b, VD.PV_TGT)) == 90 << 16,
              f"its envelopes down: freed after {n} ms; 64 still sounding")
        # a DX7 algorithm: N 6 in the sounding voice's slot
        e.uc.mem_write(blk + F.GLB + F.G_ALG, bytes([16 + 4])); e.uc.mem_write(blk + A.B_DIRTY, b"\x01")
        tick(4)
        check(dsp.get(FV(b) + VD.F8_N) == 6, f"DX7 algorithm 5: N 6 in 64's slot ({dsp.get(FV(b) + VD.F8_N)})")
        off(64); tick(200)
        # six voices of a 6-operator DX7 algorithm: the DSP writes a tick (SPI: each one waits for the DSP)
        for k in range(6): e.uc.mem_write(blk + F.OPB * k + F.O_R, bytes((80, 40, 30, 50))); e.uc.mem_write(blk + F.OPB * k + F.O_L, bytes((99, 80, 60, 0)))
        e.uc.mem_write(blk + A.B_DIRTY, b"")
        for n_ in (48, 52, 55, 60, 64, 67): on(n_, 100)
        log.clear(); tick(4); burst = len(log) / 4
        log.clear(); tick(100); move = len(log) / 100
        log.clear(); tick(400); hold = len(log) / 400
        for n_ in (48, 52, 55, 60, 64, 67): off(n_)
        log.clear(); tick(100); rel = len(log) / 100
        print(f"info: DSP writes a tick, six 6-operator voices: start {burst:.1f}, moving {move:.1f}, sustained {hold:.1f}, release {rel:.1f}")
        check(hold < 5 and move < 40, f"SPI: still decaying to L3 {hold:.1f} a tick (< 5: an AMP again only past THR), moving {move:.1f} (< 40)")
    print(f"{man['marker']} FM8 POLY RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
