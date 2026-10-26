"""SC47.4 ARM test (poly.use_v3, fmeng.use_poly): FM polyphonic, 4 FM voices in all between MIDI 1 and MIDI 2 (emu_poly's harness: the real
controller and note vtable, the whole DSP service chain with poly's tick at its head, the DSP's writes into a dict).

    python tools/emu_poly3.py NEW.bin NEW_manifest.json

  * MIDI 1 in FM (the mode row's pad 24), poly: the base written; the track's own operator blocks (X:FMB0) no longer written (fmeng leaves the
    track to poly), its FM flag still 1;
  * notes 60 / 64: a voice each, its record's PV_FMB = X:FV0 + 48 v (written before its target), R / AMP of its operators in its own blocks,
    its noise at the record's + 10, the DSP's smoothed AMP / y[n - 2] of its operators 0 at its start;
  * 60 let go with 64 held: its target kept while its release rings, then (its envelopes down) freed: its target 0;
  * MIDI 2 in FM poly too: 2 voices each (MIDI 1's voices 2 / 3 silent at once: G and target 0); MIDI 2's notes on X:FV0 + 48 (2 + v); a third
    note on MIDI 1 takes one of its two voices (the oldest, faded first);
  * MIDI 2 back to the oscillator: MIDI 1 has 4 voices again.
"""
from __future__ import annotations
import gc, json, struct, sys
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
import fmeng as F  # noqa: E402
MGR = T.MGR


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]
    v5 = P.adopt(R)                                                                   # (SC47.6: six records, six FM voices alone, 3 + 3)
    N1, N2 = (6, 3) if v5 else (4, 2)
    e = T.EL(img)
    vl = {k: int(v, 16) for k, v in R["vcf20"]["labels"].items()}
    sl = {k: int(v, 16) for k, v in R["sc06"]["labels"].items()}
    pl = {k: int(v, 16) for k, v in R["poly"]["labels"].items()}
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
    PVW = lambda t: VD.OS2B0 + 48 * t + VD.PV_OFF
    FV = lambda s: VD.FV_ADDRS[s]
    def tick(n=1):
        for _ in range(n): e.at(e.t + 1); e.call(pl["c_pytick"], maxins=8_000_000)
    non, noff = e.r32(MX.NOTE_VT) & ~1, e.r32(MX.NOTE_VT + 4) & ~1
    def on(n, v=100, t=0): e.call(non, EP.TXOBJ, 2 + t, n, v, maxins=8_000_000)
    def off(n, t=0): e.call(noff, EP.TXOBJ, 2 + t, n, 0, maxins=8_000_000)
    def mode(k):
        e.uc.mem_write(MS.RAM, bytes(8)); e.pad(26); e.pad(MS.ROW + k); e.pad(26)
    def poly_on(t=0):
        if "c_vmset" in pl: e.call(pl["c_vmset"], t, 3, maxins=1_000_000); return    # (SC47.5: the voice mode; Shift + pad 29 steps through five)
        for _ in range(2): e.set_p0(e.r32(MGR + 0xC), 1); e.pad(P.PAD29); e.set_p0(e.r32(MGR + 0xC), 0)     # retrigger -> legato -> poly
    def voices(t, n): return [v for v in range(4) if dsp.get(rec(t, v, VD.PV_NOTE)) == n and dsp.get(rec(t, v, VD.PV_TGT))]
    blk = lambda t: F.FMR + F.B0 + F.BS * t
    setp = lambda t, i, x: e.uc.mem_write(blk(t) + i, bytes([x]))
    vmax = lambda t: e.r8(P.PY + 4 + P.TBS * t + P.O_VMAX)
    written = lambda lo, hi: [a for a, _ in log if lo <= a < hi]

    # ---- MIDI 1 in FM, poly
    e.btn(2); e.btn(8); mode(F.ROWPAD - MS.ROW); poly_on()
    for t in (0, 1): setp(t, F.P_REL, 0)                                            # a short release
    tick(3); log.clear(); tick(4)
    check(dsp.get(PVW(0)) == VD.PV_REC0 and vmax(0) == N1, f"MIDI 1 in FM poly: the base written, {N1} voices ({dsp.get(PVW(0))}, {vmax(0)})")
    check(not written(VD.FMB0, VD.FMB0 + 96) and dsp.get(VD.OSB0 + VD.FM_FLAG) == 1, "the track's own operator blocks left alone, its FM flag 1")

    # ---- two notes
    log.clear(); on(60, 100); on(64, 90); tick(2)
    v60, v64 = voices(0, 60), voices(0, 64)
    ok = len(v60) == 1 and len(v64) == 1
    check(ok, f"notes 60 / 64: a voice each ({v60}, {v64})")
    if ok:
        a, b = v60[0], v64[0]
        order = [ad for ad, _ in log]
        check(dsp.get(rec(0, a, VD.PV_FMB)) == FV(a) and dsp.get(rec(0, b, VD.PV_FMB)) == FV(b)
              and order.index(rec(0, a, VD.PV_FMB)) < order.index(rec(0, a, VD.PV_TGT)), f"PV_FMB = X:FV0 + 48 v, before the target")
        r_ok = all(dsp.get(FV(s) + 12 * k + VD.F_R) for s in (a, b) for k in range(4))
        amp = [dsp.get(FV(a) + 12 * k + VD.F_AMP) for k in range(4)]
        check(r_ok and any(amp), f"R / AMP of each voice's operators in its own blocks (AMP of 60's {amp})")
        z = all((FV(s) + 12 * k + VD.F_AS) in order and (FV(s) + 12 * k + VD.F_O2) in order for s in (a, b) for k in range(4))
        check(z and rec(0, a, VD.NZ_OFF - 28) in order and not written(VD.OSB0 + VD.NZ_OFF, VD.OSB0 + VD.NZ_OFF + 1),
              "at the start: the DSP's AMP_s / y[n - 2] 0; the noise at the record's + 10 (not OSC1's)")
        # ---- 60 let go with 64 held: rings, then freed
        off(60); tick(2)
        check(dsp.get(rec(0, a, VD.PV_TGT)) == 100 << 16, "60 let go with 64 held: its target kept (the release rings)")
        n = 0
        while dsp.get(rec(0, a, VD.PV_TGT)) and n < 400: tick(5); n += 5
        envs = struct.unpack_from("<4H", bytes(e.uc.mem_read(P.FVB + 64 * a + F.B_ENV, 8)))
        check(dsp.get(rec(0, a, VD.PV_TGT)) == 0 and 0 < n < 400 and max(envs) < 64 and dsp.get(rec(0, b, VD.PV_TGT)) == 90 << 16,
              f"its envelopes down: freed after {n} ms (target 0, {envs}); 64 still sounding")
        off(64); tick(2)

    # ---- MIDI 2 in FM poly too: 2 voices each
    e.btn(3); e.btn(8); mode(F.ROWPAD - MS.ROW); poly_on(1)
    log.clear(); tick(4)
    check(vmax(0) == N2 and vmax(1) == N2 and dsp.get(PVW(1)) == VD.PV_REC0 + VD.PV_RS * VD.PV_N, f"both in FM poly: {N2} voices each ({vmax(0)}, {vmax(1)})")
    check(all(dsp.get(rec(0, v, VD.PV_G)) == 0 and dsp.get(rec(0, v, VD.PV_TGT)) == 0 for v in range(VD.PV_N)), "MIDI 1's voices silent at once (G / target 0)")
    log.clear(); on(48, 80, t=1); on(55, 70, t=1); tick(2)
    w48, w55 = voices(1, 48), voices(1, 55)
    check(len(w48) == 1 and len(w55) == 1 and {dsp.get(rec(1, w48[0], VD.PV_FMB)), dsp.get(rec(1, w55[0], VD.PV_FMB))} == {FV(N2), FV(N2 + 1)},
          f"MIDI 2's notes on X:FV0 + 96 / + 144 ({w48}, {w55})")
    held = [60, 62, 63][:N2]
    on(held[0], 100); tick(1)
    for n_ in held[1:]: on(n_, 100); tick(1)
    tick(1); old = voices(0, 60)
    on(64, 100); tick(1); t1 = dsp.get(rec(0, old[0], VD.PV_TGT)) if old else None; tick(3)
    used = {v for v in range(VD.PV_N) if dsp.get(rec(0, v, VD.PV_TGT))}
    check(old and t1 == 0 and voices(0, 64) == old and used <= set(range(N2)) and {dsp.get(rec(0, v, VD.PV_FMB)) for v in used} <= {FV(s_) for s_ in range(N2)},
          f"one more note on MIDI 1: the oldest of its {N2} voices faded, then taken ({old}, {t1}, {used})")
    for n_ in held + [64]: off(n_)
    off(48, t=1); off(55, t=1); tick(2)

    # ---- MIDI 2 back to the oscillator: MIDI 1 has 4 again
    mode(2); tick(4)
    check(vmax(0) == N1 and vmax(1) == 4, f"MIDI 2 out of FM: MIDI 1 back to {N1} voices ({vmax(0)}, {vmax(1)})")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} POLY3 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
