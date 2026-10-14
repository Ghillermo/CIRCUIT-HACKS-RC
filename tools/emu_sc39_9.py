"""SC39.9 ARM tests (live RAM dump; the real pads of the Master FX view, the DSP service tick with the clock moved by hand, the DSP on the harness's
model): the Glitch on pad 6 and the mechanical gesture on pad 31 (build_sc17.use_mechswap), Digitise's four knobs with the envelope on K4 and the
colours of the gesture's K2 (use_digi4).

    python tools/emu_sc39_9.py SC39.9.bin SC39.9_manifest.json SC39.8.bin SC39.8_manifest.json
  * pad 6 held: the Glitch plays with the knobs of pad 6's set (K1..K4, then the magic); a knob changed: sent again; let go: off; no Vinyl bit in FX_ON;
  * pad 31 held: the gesture, tick by tick = the model with the knobs of pad 31; let go: the start, then the engine is let go; pad 31 lit while it runs;
  * the previous build: pad 6 = the gesture, pad 31 = the Glitch;
  * Digitise held, K4 right of the middle: X:DG_N / DG_MASK follow a decay of the amount (the tables at K x e >> 7), left: an attack, the middle: the
    plain values, written once; the time = 20 + d x d ms;
  * the knob LEDs: Digitise selected = four LEDs (K3 its value, K4 dark in the middle and brighter either way); pad 31 selected = K2 in the colour of
    its stretch, brighter along it.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc39_7 as T7  # noqa: E402
from emu_sc35 import TICK  # noqa: E402
import build_sc17 as S  # noqa: E402
import granular_dsp as GD  # noqa: E402
import masterfx_dsp as G  # noqa: E402

KG = S.S_SLOT + 4 * S.GL_SLOT
PAD6, PAD31, PAD_DIG = S.N_FX - 1, S.GL_PAD, 3
TAB = S.tables()


class E9(T7.E7):
    def kset(self, s, v):
        for i, x in enumerate(v): self.wb(S.S_KNOB + 4 * s + i, x)
    def kg(self, v):
        for i, x in enumerate(v): self.wb(KG + i, (self.b(KG + i) & 0x80) | x)
    def ftick(self, ms):
        self.w32(TICK, ms); self.call(self.L7["c_fxtick"], maxins=3_000_000)
    def garm(self): return [self.x.get(GD.GARM + k) for k in range(5)]


def run(img, man, new):
    e = E9(img, man); e.setup(man); o = {}
    e.grid(); t = 700000
    o["kg0"] = [e.b(KG + i) & 0x7F for i in range(4)]; o["set4"] = [e.b(S.S_KNOB + 16 + i) for i in range(4)]
    e.ftick(t)
    # ---- pad 6
    e.kset(4, (100, 30, 40, 50)); e.kg((40, 0, 60, 30))
    e.pad(PAD6); e.ftick(t + 1); a = e.garm(); fx = e.x.get(G.FX_ON, 0)
    e.kset(4, (90, 30, 40, 50)); e.wb(S.S_DIRTY, 1); e.ftick(t + 2); b_ = e.garm()
    e.rel(PAD6); e.ftick(t + 3); c = e.garm(); e.ftick(t + 4000); d = e.garm()
    o["pad6"] = (a, fx, b_, c, d)
    # ---- pad 31
    t += 20000
    k = (40, 48, 60, 30); e.kg(k)
    T3 = (k[2] * k[2] >> S.MECH_TK) + S.MECH_T0
    e.pad(PAD31); got, want = [], []
    for el in list(range(0, T3 + 40, 37)) + [T3 + 900]:
        e.ftick(t + el); g = e.garm(); got.append((g[1], g[2], g[0])); want.append(T7.model(k, el, 1) + (GD.GMAGIC,))
    lit = e.gleds()[PAD31]
    e.rel(PAD31); t2 = t + T3 + 901
    for el in range(0, 400, 17):
        e.ftick(t2 + el); m = T7.model(k, el, 2); g = e.garm()
        if m is None: got.append((g[0], e.b(KG + 3) >> 7)); want.append((0, 0)); break
        got.append((g[1], g[2], g[0])); want.append(m + (GD.GMAGIC,))
    o["pad31"] = (got == want, next(((g, w) for g, w in zip(got, want) if g != w), None), lit, e.gleds()[PAD31], [g[0] for g in got[:10]])
    if not new:
        del e; gc.collect(); return o
    # ---- Digitise's envelope
    o["env"] = {}
    for k4 in (64 + 30, 64 - 30, 64):
        t += 30000
        e.kset(2, (100, 80, 0, k4)); d_ = k4 - 64; T = 20 + d_ * d_
        e.x[G.DG_N] = e.x[G.DG_MASK] = -1
        e.pad(PAD_DIG); got, want = [], []
        for el in (1, T // 4, T // 2, T - 1, T + 50, T + 5000):
            e.ftick(t + el); got.append((e.x.get(G.DG_N), e.x.get(G.DG_MASK)))
            x = min(127, min(el - 1, 0x7FFF) * 127 // T) if d_ else 0
            en = 127 if not d_ else (127 - x if d_ > 0 else x)
            want.append((TAB["DGN"][100 * en >> 7], TAB["DGM"][80 * en >> 7]) if d_ else (TAB["DGN"][100], TAB["DGM"][80]))
        e.rel(PAD_DIG); e.ftick(t + T + 5001)
        o["env"][k4] = (got == want, got, want)
    # ---- the knob LEDs
    e.kset(2, (10, 20, 100, 64)); e.pad(PAD_DIG); e.rel(PAD_DIG); f = e.gleds()[34:42]
    e.kset(2, (10, 20, 100, 104)); g1 = e.gleds()[37]; e.kset(2, (10, 20, 100, 24)); g2 = e.gleds()[37]
    o["dled"] = (f, g1, g2)
    e.pad(PAD31); e.rel(PAD31); cols = []
    for k2 in (0, 16, 31, 32, 60, 64, 90, 96, 127):
        e.kg((40, k2, 60, 30)); cols.append(e.gleds()[35])
    o["mled"] = cols
    del e; gc.collect()
    return o


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    VN = 1 << G.B_VN
    o = run(img, man, True)
    a, fx, b_, c, d = o["pad6"]
    check(a == [GD.GMAGIC, 100, 30, 40, 50] and not fx & VN, f"pad 6 held: the Glitch with the knobs of pad 6 ({a[1:]}), the magic; no Vinyl bit in FX_ON ({fx:#x})")
    check(b_[1] == 90 and b_[0] == GD.GMAGIC and c[0] == 0 and d[0] == 0, f"a knob changed: sent again ({b_[1]}); let go: off")
    ok, diff, lit, dark, sp = o["pad31"]
    check(ok and lit == S.GL_ON and dark == S.GL_DIM, f"pad 31 held: the gesture, every tick of the stop and the start = the model ({sp}; first difference {diff}); pad 31 lit while it runs")
    for k4, name in ((94, "right of the middle: a decay"), (34, "left: an attack"), (64, "the middle: the plain values")):
        ok, got, want = o["env"][k4]
        check(ok, f"Digitise, K4 {name} ({[g[0] for g in got]}{'' if ok else ' / ' + str([w[0] for w in want])})")
    f, g1, g2 = o["dled"]
    col = f[0] & 0xFF
    check(all(x & 0xFF == col and x >> 8 for x in f[:4]) and f[4:] == [0] * 4 and f[2] >> 8 == 102 and f[3] >> 8 == 2 and g1 >> 8 == 82 and g2 >> 8 == 82,
          f"Digitise selected: four knob LEDs ({[hex(x) for x in f[:4]]}); K4 dark in the middle, as bright at 40 either side ({g1 >> 8}, {g2 >> 8})")
    m = o["mled"]
    want = []
    for k2 in (0, 16, 31, 32, 60, 64, 90, 96, 127):
        seg = k2 * 4; want.append(S.MECH_COL[min(seg >> 7, 3)] | (((seg & 127) * (127 - S.MECH_MINB) >> 7) + S.MECH_MINB + 2) << 8)
    check(m == want and len({x & 0xFF for x in m}) == 4, f"pad 31 selected: K2 in the colour of its stretch, brighter along it ({[hex(x) for x in m]})")
    gc.collect(); q = run(prev, prev_man, False)
    check(q["pad6"][0][1] != 100 and q["pad31"][0] is False, f"the previous build: pad 6 is the gesture (GARM + 1 = {q['pad6'][0][1]}), pad 31 the Glitch")
    print(f"      the knobs of pad 31 as the dump has them: {o['kg0']}; of pad 6's set: {o['set4']}")
    print("SC39.9 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
