"""SC52.1: core 1's copy of a wavetable (granular_dsp.use_wtcopy) on the dsp56kEmu interpreter, with the build's core-1 options (build_sc52_1): a
command (seq, source, destination, words) = the words of X:source.. in Y:destination.., 256 a pass, then the seq seen; a second command copies
another range to another place; the same seq again does nothing; a sample's single cycle (source = bit 23 | 5, a saw of period 200): the period
found, level 2 the saw (harmonics 1/2, 1/3), level 10 up to harmonic 16, level 17 a sine, levels 0 / 1 = level 2.  (As emu_s516d for S516D's novadump.)

    python tools/emu_wtcopy_core1.py build/sc52.1/circuittracks-4486-SC52.1.bin build/sc52.1/manifest.json
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import dsp56  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import granular_dsp as GD  # noqa: E402
import probe35_dsp as P5  # noqa: E402

DRV, STOP, PASS = 0x3800, 0x3FF0, 0x3F80


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    import build_sc52_1  # noqa: F401  (the build's options)
    DST = 0xC000                                                              # (the interpreter's memory: 512 K words)
    stock = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    W = lambda bb: [int.from_bytes(bb[i:i + 3], "big") for i in range(0, len(bb), 3)]
    w1, lab = GD.core1_code(P5.C1_STOCK_WORDS, rl=0x40000, rn=0x10000)
    check(P5.C1_STOCK_WORDS + len(w1) == man["report"]["granular"]["core1_words"], f"the rebuilt core 1 = the build's size ({P5.C1_STOCK_WORDS + len(w1)})")
    C1 = lab["c1loop"]
    P = W(dsp_program(stock, 1)) + w1; P += [0] * (0x4000 - len(P))
    P[0x10E:0x110] = [0x0AF080, DRV]
    code = []
    def emit(*ls): code.extend(G.T(*ls))
    emit("move x:>$%x,a" % PASS, "move #>1,x0", "add x0,a", "move a1,x:>$%x" % PASS, "move #>300,x0", "cmp x0,a")
    code += [0x0AF0A9, C1]
    emit("clr a", "move a,x:>$%x" % PASS, "move x:>$%x,a" % GD.CNT, "move #>1,x0", "add x0,a", "move a1,x:>$%x" % GD.CNT, "move #>6,x1", "cmp x1,a")
    code += [0x0AF0AA, STOP, 0x0AF080, C1]
    P[DRV:DRV + len(code)] = code; P[STOP] = 0
    pat = [(0x10000 + 7 * i) & 0xFFFF00 for i in range(1200)]
    def go(cmd, seen=0):
        res, ran = run(P, C1, mem=[('x', 0x20000, pat), ('x', GD.WC_CMD, cmd), ('x', GD.WC_SEEN, [seen])], regs_code=[], pc=C1, stop=STOP,
                       maxins=60_000_000, dumps=[('y', DST, 2000), ('x', GD.WC_SEEN, 3)])
        assert ran and 'pc=003ff0' in ran.lower(), ran
        return res[('y', DST)], res[('x', GD.WC_SEEN)]
    y, s = go([5, 0x20000, DST, 600])
    check(s[0] == 5 and y[:600] == pat[:600] and y[768:] == [0] * (2000 - 768), f"seq 5, X:$20000 + 600 -> Y:${DST:x}: copied (in 256-word steps: 768), then seen ({s[0]})")
    y, s = go([6, 0x20000 + 600, DST + 1024, 512], seen=5)
    check(s[0] == 6 and y[1024:1536] == pat[600:1112] and not any(y[:1024]), f"seq 6: another range to another place ({s[0]})")
    y, s = go([5, 0x20000, DST, 600], seen=5)
    check(not any(y), "the same seq again: nothing copied")
    # ---- a sample's single cycle: a saw of period 200 (8192 samples at Y:$10000, sample 5 of the table) -> 18 levels at Y:$14000
    import numpy as np
    GD.SCR = 0x70000                                                           # (the interpreter's memory)
    w2, lab2 = GD.core1_code(P5.C1_STOCK_WORDS, rl=0x40000, rn=0x10000)
    P2 = W(dsp_program(stock, 1)) + w2; P2 += [0] * (0x4000 - len(P2))
    P2[0x10E:0x110] = [0x0AF080, DRV]
    code = []
    emit("move x:>$%x,a" % PASS, "move #>1,x0", "add x0,a", "move a1,x:>$%x" % PASS, "move #>1000,x0", "cmp x0,a")
    code += [0x0AF0A9, lab2["c1loop"]]
    emit("clr a", "move a,x:>$%x" % PASS, "move x:>$%x,a" % GD.CNT, "move #>1,x0", "add x0,a", "move a1,x:>$%x" % GD.CNT, "move #>4,x1", "cmp x1,a")
    code += [0x0AF0AA, STOP, 0x0AF080, lab2["c1loop"]]
    P2[DRV:DRV + len(code)] = code; P2[STOP] = 0
    n = np.arange(8192); saw = ((n % 200) / 200.0 - 0.5) * 1.6
    smp = [(int(round(v * 32767)) & 0xFFFF) << 8 for v in saw]
    D2 = 0x14000                                                               # (the test ring is at Y:$40000)
    res, ran = run(P2, lab2["c1loop"], mem=[('y', 0x10000, smp), ('x', GD.SHT + 4 * 5, [0x10000, 8192]), ('x', GD.WC_CMD, [7, 0x800005, D2, 0]),
                                            ('x', GD.WC_SEEN, [6])], regs_code=[], pc=lab2["c1loop"], stop=STOP, maxins=900_000_000,
                   dumps=[('y', D2, 18 * 1024), ('x', GD.WC_SEEN, 1), ('x', GD.SJ, 10)])
    assert ran and 'pc=003ff0' in ran.lower(), ran
    sjv = res[('x', GD.SJ)]
    check(res[('x', GD.WC_SEEN)][0] == 7 and sjv[0] == 0, f"seq 7 (sample 5): done, seen ({res[('x', GD.WC_SEEN)][0]}, the phase {sjv[0]})")
    check(abs(sjv[5] - 200) <= 1, f"the period found: {sjv[5]} (the saw's 200)")
    y = res[('y', D2)]
    s16 = lambda v: (v - (1 << 24) if v & 0x800000 else v) / (1 << 23)
    lev = [np.array([s16(v) for v in y[1024 * L:1024 * L + 1024]]) for L in range(18)]
    def top(x):
        sp = np.abs(np.fft.rfft(x)); sp /= sp.max() + 1e-12; nz = np.where(sp > 0.01)[0]; return int(nz.max()) if len(nz) else 0, sp
    h2, sp2 = top(lev[2]); h10, _ = top(lev[10]); h17, sp17 = top(lev[17])
    check(0.55 < np.abs(lev[2]).max() < 1.0 and abs(sp2[2] - 0.5) < 0.1 and abs(sp2[3] - 0.333) < 0.08,
          f"level 2: the saw (peak {np.abs(lev[2]).max():.2f}; harmonics 2 / 3 at {sp2[2]:.2f} / {sp2[3]:.2f} of the first)")
    check(h10 <= 16 and h17 == 1, f"band-limited: level 10 up to harmonic {h10} (16), level 17 {h17} (a sine)")
    check(np.allclose(lev[0], lev[2]) and np.allclose(lev[1], lev[2]), f"levels 0 / 1 = level 2 (max diff {np.abs(lev[0] - lev[2]).max():.4f} / {np.abs(lev[1] - lev[2]).max():.4f}; level 0 peak {np.abs(lev[0]).max():.3f})")
    print(f"{man.get('marker', '?')} WT COPY CORE 1 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
