"""SC39.7 ARM tests (live RAM dump; the DSP service tick c_fxtick with the clock moved by hand, the DSP reads / writes on the harness's model): the
mechanical gesture on the Glitch engine in the place of Vinyl (build_sc17.use_mech).

    python tools/emu_sc39_7.py SC39.7.bin SC39.7_manifest.json SC39.6.bin SC39.6_manifest.json
  * the Vinyl effect switched on (its latch): the Vinyl bit never reaches the DSP's FX_ON (the previous build sets it); the Glitch's magic goes up;
  * the stop: tick by tick the speed (GARM + 1) and the repeat (GARM + 2) follow the model for 9 kinds (the five of K2 and the four half ways) and
    several K1: tape stop falls from 127 to 64 (stopped), the scratches swing around 64, the back spin starts in reverse, the rattle closes the repeat;
    at the end of the time everything stands still (speed 64) and stays so while held;
  * let go: the same curve backwards over the start time (K4), then the engine is let go (the magic 0) and the run flag drops;
  * the times: K3 / K4 = 20 ms + K x K / 4;
  * with nothing on: no DSP read at all in the tick (the state word is read only while a gesture runs).
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import E35, TICK, PK  # noqa: E402
import build_sc17 as S  # noqa: E402
import granular_dsp as GD  # noqa: E402
import masterfx_dsp as G  # noqa: E402

KG = S.S_SLOT + 4 * S.GL_SLOT
VK = S.S_KNOB + 16
BIT = 1 << (S.N_FX - 1)


def asr7(v): return v >> 7


def shape(n, y, p):
    if n == 0: return y
    if n == 1:
        t = 2 * p - 127
        if t < 0: t = -t
        return asr7((2 * t - 127) * y)
    if n == 2: return asr7(S.MECH_TEAR[p >> 5] * y)
    if n == 3: return -asr7(y * y)
    return 127 if y else 0


def model(k, el, phase):
    """-> (speed, repeat) or None when the start is over"""
    K = k[2] if phase == 1 else k[3]
    T = (K * K >> S.MECH_TK) + S.MECH_T0
    x = min(127, min(el, 0x7FFF) * 127 // T)
    if phase == 2:
        if x >= 127: return None
        x = 127 - x
    y = 127 - x; p = (x * ((k[0] >> 4) + 1)) & 127
    seg = k[1] * 4; i, w = seg >> 7, seg & 127
    v = asr7(shape(i, y, p) * (128 - w) + shape(i + 1, y, p) * w)
    sp = max(1, min(127, asr7(v * 63 + 64) + 64))
    r = 127
    if i >= 3: r = max(1, asr7((asr7(y * y) - 127) * w) + 127)
    return sp, r


class E7(E35):
    def setup(self, man):
        self.L7 = {k: int(v, 16) for k, v in man["report"]["sc17"]["labels"].items()}
        self.call(self.L7["c_gfst"]); self.blk7 = self.uc.reg_read(UC_ARM_REG_R0)
        self.reads = 0
        self.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: setattr(self, "reads", self.reads + (uc.reg_read(UC_ARM_REG_R1) == G.VN_T)), begin=PK.DSP_READ, end=PK.DSP_READ)
    def b(self, off): return self.r8(self.blk7 + off)
    def wb(self, off, v): self.uc.mem_write(self.blk7 + off, bytes([v]))
    def knobs(self, k):
        for i, v in enumerate(k): self.wb(VK + i, v)
    def on(self, v): self.wb(S.S_LATCH, (self.b(S.S_LATCH) & ~BIT) | (BIT if v else 0))
    def tick(self, ms):
        self.w32(TICK, ms); self.reads = 0; self.call(self.L7["c_fxtick"], maxins=3_000_000)
        return self.x.get(GD.GARM + 1), self.x.get(GD.GARM + 2), self.x.get(GD.GARM)


def run(img, man, new):
    e = E7(img, man); e.setup(man); o = {}
    t = 500000
    e.wb(S.S_LATCH, 0); e.wb(S.S_HELD, 0); e.wb(KG, e.b(KG) & 0x7F)
    e.tick(t); o["idle_reads"] = e.reads; o["fxon0"] = e.x.get(G.FX_ON, 0)
    e.knobs((40, 0, 60, 30)); e.on(1); e.tick(t + 1); o["fxon1"] = e.x.get(G.FX_ON, 0); o["magic1"] = e.x.get(GD.GARM)
    if not new:
        del e; gc.collect(); return o
    e.on(0)
    for _ in range(3): e.tick(t + 9000)                                              # (let it finish)
    o["curves"] = {}
    t = 600000
    for k1 in (0, 40, 127):
        for k2 in (0, 16, 32, 48, 64, 80, 96, 112, 127):
            k = (k1, k2, 60, 30); e.knobs(k); t += 20000
            T3 = (60 * 60 >> S.MECH_TK) + S.MECH_T0; T4 = (30 * 30 >> S.MECH_TK) + S.MECH_T0
            got, want = [], []
            e.on(1)
            for el in list(range(0, T3 + 40, 23)) + [T3 + 500, T3 + 3000]:
                r = e.tick(t + el); got.append(r); want.append(model(k, el, 1) + (GD.GMAGIC,))
            flag_on = e.b(KG + 3) >> 7
            t2 = t + T3 + 3001; e.on(0)
            for el in range(0, T4 + 60, 11):
                r = e.tick(t2 + el); m = model(k, el, 2)
                if m is None: got.append((r[2], e.b(KG + 3) >> 7)); want.append((0, 0)); break
                got.append(r); want.append(m + (GD.GMAGIC,))
            o["curves"][(k1, k2)] = (got == want, flag_on, got[0], got[len(range(0, T3 + 40, 23))], [g[0] for g in got[:12]], next(((g, w) for g, w in zip(got, want) if g != w), None))
    del e; gc.collect()
    return o


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    VN = 1 << G.B_VN
    o = run(img, man, True)
    check(o["idle_reads"] == 0, "nothing on: the tick does not read the state word from the DSP")
    check(not o["fxon1"] & VN and o["magic1"] == GD.GMAGIC, f"the Vinyl pad on: its bit never reaches FX_ON ({o['fxon1']:#x}); the Glitch engine is taken (the magic)")
    bad = {k: v[5] for k, v in o["curves"].items() if not v[0]}
    check(not bad and all(v[1] == 1 for v in o["curves"].values()), f"27 gestures (K1 0 / 40 / 127 x 9 kinds), every tick of the stop, the hold and the start = the model; first difference: {dict(list(bad.items())[:2])}")
    c = o["curves"]
    check(c[(40, 0)][2][:2] == (127, 127) and c[(40, 0)][3][:2] == (64, 127), f"tape stop: from the normal speed to stopped ({c[(40, 0)][4]})")
    check(min(c[(127, 32)][4]) < 64 < max(c[(127, 32)][4]), f"baby scratch: back and forth around the stop ({c[(127, 32)][4]})")
    check(c[(40, 96)][2][0] < 20 and c[(40, 96)][3][0] == 64, f"back spin: thrown backwards ({c[(40, 96)][4]})")
    check(c[(40, 127)][2][0] >= 120 and c[(40, 127)][3][1] < 10, f"rattle: the tape runs, the repeat closes ({c[(40, 127)][2]} -> {c[(40, 127)][3]})")
    gc.collect(); q = run(prev, prev_man, False)
    check(q["fxon1"] & VN and q["magic1"] != GD.GMAGIC, f"the previous build: the Vinyl bit in FX_ON ({q['fxon1']:#x}), the Glitch engine untouched")
    print("SC39.7 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
