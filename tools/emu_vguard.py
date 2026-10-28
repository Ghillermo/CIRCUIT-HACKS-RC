"""SC48.5 / Beta 3.42 ARM tests (emu_polygain's harness: the notes through the transmitter's entries, the DSP writes caught, the DSP's reads
answered by the test: Y:$FFE / Y:$FFD = the margin):
  * poly.use_polydef: a project that never set a voice mode = poly in both tracks;
  * poly.use_v8: the oscillator, poly: 1-4 notes = x 256 / 256 / 209 / 181 (/ 256) each; FM poly, six notes = x 148;
  * vguard (through the head of the DSP service chain, the whole chain after it):
      - fewer than two voices: the margin not read;
      - six FM notes held, margin 200 (red, the ring far from dry): nothing freed;
      - three let go (ringing; their envelopes set by the test to sums 120000 / 40000 / 80000), margin 50: the quietest freed, the others
        sounding; 2 ms later margin 50: nothing (12 ms apart); 4 ms after the first, margin 20 (half a block): the next quietest;
        12 ms later margin 50: the last released; 12 ms later margin 50, none released: the oldest held (the first note);
        4 ms later the ring dry (margin 900): the next oldest held;
      - margin 200 for 40 ms: nothing more freed; the freed voices' DSP targets 0, the one left at full level;
      - the cap (poly.use_v9) = the voices left (2 at least): a note with one voice = a second voice; another note = the oldest held freed first,
        two sounding; 2 s with nothing freed = the cap 3, 2 s more = 4;
      - the unison (uni retrig, FM, six voices allowed) with the cap at 3: three voices on the note, each x 209 (sqrt(2 / 3)); margin 50 = one of
        them freed, the cap 2; the next unison note: two voices;
      - (vguard.use_hold, SC48.6 / Beta 3.43) the stock's steal countdowns X:$3239 / $323A: never written with fewer than two voices; with six
        held, 48 written to both every 16 ms (not every 2 ms reading); one voice left: no longer written.

    python tools/emu_vguard.py SC48.5.bin SC48.5_manifest.json
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
import vguard as G  # noqa: E402


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
    gl = {k: int(v, 16) for k, v in R["vguard"]["labels"].items()}
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    for ad in (sl["c_non"], sl["c_noff"], EP.STOCK_TX_ON, EP.STOCK_TX_OFF, EP.REC_GATE):
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: skip(uc), begin=ad, end=ad)
    dsp = {}
    wlog = []
    def w(uc, a, s, d):
        ad_, v_ = uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R1) >> 8
        dsp[ad_] = v_; wlog.append((e.t, ad_, v_)); skip(uc)
    e.uc.hook_add(UC_HOOK_CODE, w, begin=P.DSP_WRITE, end=P.DSP_WRITE)
    st = dict(isr=0x1100, blk=0x1100 + 250); reads = []
    def rd(uc, a, s, d):
        ad = uc.reg_read(UC_ARM_REG_R1)
        v = st["isr"] if ad == G.Y_ISR else st["blk"] if ad == G.Y_BLK else 0
        if ad in (G.Y_ISR, G.Y_BLK): reads.append(ad)
        uc.reg_write(UC_ARM_REG_R0, (v & 0xFFFFFF) << 8); skip(uc)
    e.uc.hook_add(UC_HOOK_CODE, rd, begin=G.DSP_READ, end=G.DSP_READ)
    def margin(m): st["isr"] = (st["isr"] + 37) & 0x3FF | 0x1000; st["blk"] = (st["isr"] + m) & 0x3FF | 0x1000
    e.at(100000); e.transport(0)
    for _ in range(30): e.at(e.t + 40); e.call(vl["c_vtick"], maxins=3_000_000)
    md = [e.call(pl["c_vmget"], t, maxins=1_000_000) or e.uc.reg_read(UC_ARM_REG_R0) for t in (0, 1)]
    check(md == [3, 3], f"a project with no voice mode set: poly in both tracks ({md})")
    rec = lambda t, v, f: VD.PV_REC0 + VD.PV_RS * (VD.PV_N * t + v) + f
    def tick(n=1):
        for _ in range(n): e.at(e.t + 1); e.call(ml["c_vmtick"], maxins=8_000_000)
    def gtick(ms=1):                                                       # the whole chain from vguard's head
        e.at(e.t + ms); e.call(gl["c_vgtick"], maxins=20_000_000)
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
    want = [[lvl(g)] * (k + 1) for k, g in enumerate((256, 256, 209, 181))]
    check(got == want, f"the oscillator, poly: 1-4 notes ({[g[0] if g else None for g in got]} = {[w_[0] for w_ in want]})")
    for n in (60, 64, 67, 71): off(n)
    tick(10)
    blk = P.PY + 4
    vram = lambda v: blk + 4 + P.VS_ * v
    def voices():                                                          # note -> state, for the voices sounding / starting
        return {e.r8(vram(v) + P.VN): e.r8(vram(v) + P.VS) for v in range(VD.PV_N) if e.r8(vram(v) + P.VS) & (P.SND | P.PEND)}
    mode(F.ROWPAD - MS.ROW); e.call(pl["c_vmset"], 0, 3, maxins=1_000_000); tick(4)
    margin(30); n0 = len(reads); gtick(3); gtick(3)
    check(len(reads) == n0, f"no voices: the margin not read ({len(reads) - n0} reads)")
    hold = "vh_x" in R["vguard"]["labels"]
    held = lambda: [(t_, a_, v_) for t_, a_, v_ in wlog if a_ in (G.STEAL_CNT, G.STEAL_CNT + 1)]
    if hold:
        check(not held(), f"hold: fewer than two voices, the stock's countdowns not written ({held()})")
    NOTES = (48, 52, 55, 60, 64, 67)
    for n in NOTES: on(n); tick(3)
    tick(4)
    six = [t for t in tgts() if t]
    check(six == [lvl(148)] * 6, f"FM poly, six notes: x 148 / 256 each ({six})")
    margin(200)
    h0 = len(held()); t0 = e.t
    for _ in range(5): gtick(2)
    if hold:
        for _ in range(12): gtick(2)
        hw = held()[h0:]; tt = sorted({t_ for t_, _, _ in hw})
        ok = (hw and all(v_ == G.HOLD_BLK for _, _, v_ in hw) and {a_ for _, a_, _ in hw} == {G.STEAL_CNT, G.STEAL_CNT + 1}
              and len(hw) == 2 * len(tt) and all(b_ - a_ >= G.HOLD_MS for a_, b_ in zip(tt, tt[1:])) and len(tt) >= (e.t - t0) // G.HOLD_MS)
        check(ok, f"hold: six held, the countdowns = {G.HOLD_BLK} every {G.HOLD_MS} ms ({len(hw)} writes at {[t_ - t0 for t_ in tt]} ms)")
    v0 = voices()
    check(len(v0) == 6 and all(s & P.HELD for s in v0.values()) and reads, f"six held, margin 200: nothing freed ({sorted(v0)}, {len(reads)} reads)")
    ENV = {55: 30000, 60: 10000, 67: 20000}                               # the released ones: each envelope (sums 120000 / 40000 / 80000)
    for n in ENV: off(n)
    def setenv():
        for v in range(VD.PV_N):
            n = e.r8(vram(v) + P.VN)
            if n in ENV and e.r8(vram(v) + P.VS) & P.SND:
                for k in range(4): e.uc.mem_write(P.FVB + 64 * v + F.B_ENV + 2 * k, ENV[n].to_bytes(2, "little"))
    def step(m, ms):
        setenv(); margin(m); gtick(ms); return sorted(voices())
    seq = [("margin 50: the quietest released (60) freed", 50, 2, [48, 52, 55, 64, 67]),
           ("2 ms later, margin 50: nothing (12 ms apart)", 50, 2, [48, 52, 55, 64, 67]),
           ("4 ms after, margin 20: the next quietest (67)", 20, 2, [48, 52, 55, 64]),
           ("12 ms later, margin 50: the last released (55)", 50, 12, [48, 52, 64]),
           ("12 ms later, margin 50, none released: the oldest held (48)", 50, 12, [52, 64]),
           ("4 ms later, the ring dry (900): the next oldest held (52)", 900, 4, [64])]
    for name, m, ms, want_ in seq:
        got_ = step(m, ms); check(got_ == want_, f"{name}: {got_}")
    h1 = len(held())
    for _ in range(20): step(200, 2)
    check(sorted(voices()) == [64], f"margin 200 for 40 ms: nothing more freed ({sorted(voices())})")
    if hold:
        check(len(held()) == h1, f"hold: one voice left, the countdowns no longer written ({len(held()) - h1} writes)")
    tick(4); left = [t for t in tgts() if t]
    check(left == [lvl(256)], f"the freed voices' targets 0; the one left at full level ({left})")
    nfreed = e.r32(G.RAM + G.O_N)
    check(nfreed == 5, f"five voices freed in all ({nfreed})")
    cap = lambda: e.r8(G.RAM + G.O_CAP)
    check(cap() == 2, f"the cap = the voices left, 2 at least ({cap()})")
    on(70); tick(4); c1 = sorted(voices()); on(72); tick(4); c2 = sorted(voices())
    check(c1 == [64, 70] and c2 == [70, 72], f"at the cap: a second voice, then the oldest held freed for the next ({c1}, {c2})")
    for _ in range(42): margin(200); gtick(50)
    c3 = cap()
    for _ in range(40): margin(200); gtick(50)
    check((c3, cap()) == (3, 4), f"2 s with nothing freed: the cap 3, 2 s more: 4 ({c3}, {cap()})")
    for n in (70, 72): off(n)
    tick(10)
    e.call(pl["c_vmset"], 0, 4, maxins=1_000_000); tick(4)
    e.uc.mem_write(G.RAM + G.O_CAP, bytes([3])); e.uc.mem_write(G.RAM + G.O_SHED, (e.t).to_bytes(4, "little"))
    vl_ = lambda: [e.r8(vram(v) + P.VN) for v in range(VD.PV_N) if e.r8(vram(v) + P.VS) & (P.SND | P.PEND)]
    on(60); tick(6); u1 = vl_(); ut = [t for t in tgts() if t]
    check(len(u1) == 3 and set(u1) == {60} and ut == [lvl(209)] * 3, f"unison, the cap 3: three voices on 60, x 209 each ({u1}, {ut})")
    margin(50); e.at(e.t + G.GAP); e.call(gl["c_vgtick"], maxins=20_000_000); u2 = vl_()
    check(len(u2) == 2 and cap() == 2, f"margin 50: one unison voice freed, the cap 2 ({u2}, cap {cap()})")
    off(60); tick(4); margin(200); on(62); tick(6); u3 = vl_(); ut3 = [t for t in tgts() if t]
    check(len(u3) == 2 and set(u3) == {62} and ut3 == [lvl(256)] * 2, f"the next unison note: two voices at full level ({u3}, {ut3})")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} VGUARD RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())) else 0)
