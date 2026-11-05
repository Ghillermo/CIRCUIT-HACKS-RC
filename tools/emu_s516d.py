"""S516D: core 1's copy (granular_dsp.use_novadump) on the dsp56kEmu interpreter: a command (seq, source, words) = the words of X:source.. in Y:ND_Y..,
256 a pass, then the seq seen; a second command copies the next range; the same seq again does nothing.

    python tools/emu_s516d.py firmware/s516d/circuittracks-4486-S516D.bin firmware/s516d/manifest.json
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
    dsp56.use_shortx(); GD.use_stereo(); GD.use_overload(); GD.FMC1 = True; GD.use_c1ms(); GD.NOVADUMP = True
    GD.ND_Y = 0xC000                                                          # (the interpreter's memory: 512 K words)
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
        res, ran = run(P, C1, mem=[('x', 0x20000, pat), ('x', GD.ND_CMD, cmd), ('x', GD.ND_SEEN, [seen])], regs_code=[], pc=C1, stop=STOP,
                       maxins=60_000_000, dumps=[('y', GD.ND_Y, 1200), ('x', GD.ND_SEEN, 3)])
        assert ran and 'pc=003ff0' in ran.lower(), ran
        return res[('y', GD.ND_Y)], res[('x', GD.ND_SEEN)]
    y, s = go([5, 0x20000, 600])
    check(s[0] == 5 and y[:600] == pat[:600] and y[768:] == [0] * (1200 - 768), f"seq 5, X:$20000 + 600: copied (in 256-word steps: 768), then seen ({s[0]})")
    y, s = go([6, 0x20000 + 600, 512], seen=5)
    check(s[0] == 6 and y[:512] == pat[600:1112], f"seq 6: the next range ({s[0]})")
    y, s = go([5, 0x20000, 600], seen=5)
    check(not any(y), "the same seq again: nothing copied")
    print(f"{man.get('marker', '?')} S516D RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
