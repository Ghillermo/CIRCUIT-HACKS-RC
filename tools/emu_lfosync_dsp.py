"""SC44.8 DSP test (vcf21_dsp.use_lfosync): the own engine's LFO rate bipolar, on the whole core 0 (dsp_session) with the engine's real traffic
(emu_sc43_9_dsp.schedule) and MIDI 1's voice forced to the oscillator (ACT 1).

    python tools/emu_lfosync_dsp.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json
  * LRATE = 20 (the right side): the phase moves as the previous build's with LRATE = 40 (TLFO[2 v]), block by block;
  * LRATE = -9 (synced): the phase moves by the increment in OS2B0 + 40 (the ARM's word), whatever it is (two values);
  * the drums: LSPD 10 as the previous build's -44, LSPD -9 by the increment in the block's word LINC;
  * the whole core 0 against the previous build's with the same traffic: printed only (the traffic turns LRATE, whose values now mean double the
    speed, and the VA-drum's noise level = v + 64).
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc44_dsp as T  # noqa: E402
import emu_sc43_9_dsp as M  # noqa: E402
import vcf21_dsp as VD  # noqa: E402

VB = VD.VB0
PH, LRATE, ACT = VB + VD.PH, VB + VD.P_LRATE, VB + 20
INC = VD.OS2B0 + VD.LFS_INC


def s24(v): return v - (1 << 24) if v & 0x800000 else v


def phases(img, sched, rate, inc=None):
    T0 = 60
    force = lambda b: ([(ACT, 1), (LRATE, rate & 0xFFFFFF)] + ([(INC, inc)] if inc is not None else [])) if b >= T0 else []
    sched = [[(w, ad) for w, ad in blk if not (ad in (VB, VB + VD.VBS) and (w >> 16) & 0x7F == VD.P_LRATE - 1)] for blk in sched]   # (no LRATE messages: ours stays)
    R = T.run(img, sched, 90, force, {}, [(PH, 1)])
    gc.collect()
    p = [r[0] for r in R[PH]]
    return [((p[k + 1] - p[k]) & 0xFFFFFF) for k in range(T0 + 2, len(p) - 1)]


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    sched = M.schedule(prev, pman)
    dn, dp = phases(img, sched, 20), phases(prev, sched, 40)
    check(dn == dp and len(set(dn)) == 1, f"LRATE 20 moves the phase as the previous build's 40 ({hex(dn[0])} a block vs {hex(dp[0])})")
    for inc in (0x1234, 0x23456):
        d = phases(img, sched, -9, inc)
        check(set(d) == {inc}, f"LRATE -9: the phase moves by the ARM's increment {inc:#x} ({sorted(set(hex(x) for x in d))[:3]})")
    # the drums: drum 2's LSPD; the previous build: v - 64 = the same TLFO index as 2 v here
    import drums2_dsp as D2
    DBd = D2.DB + 2 * D2.STRIDE
    def dph(im, v, inc=None):
        T0 = 60
        force = lambda b: ([(DBd + D2.LSPD, v & 0xFFFFFF)] + ([(DBd + D2.LINC, inc)] if inc is not None else [])) if b >= T0 else []
        R = T.run(im, sched, 80, force, {}, [(DBd + D2.PH, 1)]); gc.collect()
        p = [r[0] for r in R[DBd + D2.PH]]
        return [((p[k + 1] - p[k]) & 0xFFFFFF) for k in range(T0 + 2, len(p) - 1)]
    dn, dp = dph(img, 10), dph(prev, 20 - 64)
    check(dn == dp and dn and dn[0] != 0, f"drum 3, LSPD 10 moves its phase as the previous build's -44 (TLFO[20]: {hex(dn[0]) if dn else '-'})")
    d = dph(img, -9, 0x4567)
    check(set(d) == {0x4567}, f"drum 3, LSPD -9: its phase moves by the ARM's increment ({sorted(set(hex(x) for x in d))[:3]})")
    Rn, _ = M.dsp_run(img, sched); gc.collect()
    Rp, _ = M.dsp_run(prev, sched); gc.collect()
    check(len(Rn) == len(Rp) == 2 * len(M.CHECKS), f"{len(Rn)} / {len(Rp)} dumps")
    for k, ((sn, an, vn), (sp_, ap, vp)) in enumerate(zip(Rn, Rp)):
        diff = [i for i, (x, y) in enumerate(zip(vn, vp)) if x != y]
        print(f"     block {M.CHECKS[k // 2]}, {sn.upper()}: {len(diff)} words differ {[hex(i) for i in diff[:8]]}")
    print(f"{man.get('marker', '?')} DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
