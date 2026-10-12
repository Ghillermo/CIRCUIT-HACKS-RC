"""SC35D2 tests: probe35_dsp.V3 (read-only map of the external memory by core 0, core 1 at the top of the shared memory) and the image.

    python tools/emu_sc35d2.py SC35D2.bin SC35D2_manifest.json
Image: core 1 = the stock 364 words with P:$12A = jmp c1loop + core1_code3(); core 0: P:$23C = jsr pprobe + core0_code3(); the ARM dump of probe32b.
Core 1 (interpreter, a driver at P:$10E that counts passes, bumps core 0's block counter every 3 passes and grows the list pointer X:$30000): magic once, passes per
block last = min = 3, the longest list, passes / 256 every 256 passes; nothing written below SH3 (the list area untouched); r5 / m5 untouched.
Core 0 (24 test addresses in the interpreter's memory): the first round only records; a word changed later sets its bit in EVER and in the window; the window
closes every 1024 blocks (WIN, count); the external words are never written; the dump words; MAGIC3 only with core 1's magic; x0 / x1 / r0 restored.
"""
from __future__ import annotations
import json, sys, gc
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import probe35_dsp as PD  # noqa: E402
import drums18  # noqa: E402
import build_sc14 as s14  # noqa: E402

DRV = 0x3800
TS = [0x48000 + 0x100 * i for i in range(len(PD.SENT))]   # the 24 sentinels inside the interpreter's memory
T600 = 0x4A000                                            # stands for Y:$600000 in the dump


def T_(*l): return G.T(*l)


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    stock = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    rep = man["report"]; p35 = rep["probe35"]
    W = lambda bb: [int.from_bytes(bb[i:i + 3], "big") for i in range(0, len(bb), 3)]
    P1, P1s = W(dsp_program(img, 1)), W(dsp_program(stock, 1))
    real, l1 = PD.core1_code3(PD.C1_STOCK_WORDS)
    check(P1[:PD.C1_STOCK_WORDS] == [0x0C0000 | l1["c1loop"] if i == PD.C1_HOOK else w for i, w in enumerate(P1s)] and P1[PD.C1_STOCK_WORDS:] == real,
          f"core 1: the stock 364 words, P:$12A = jmp c1loop, core1_code3(); {len(P1)} words (P RAM of core 1 ends at $7FF)")
    check(len(P1) <= 0x800, "core 1 program inside its 2 K words")
    dl = {k: int(v, 16) for k, v in rep["sc16"]["dsp_labels"].items()}
    P0 = W(dsp_program(img, 0))
    c0 = PD.core0_code3(dl["pprobe"], PD.PREMIX)[0]
    check(P0[0x23C:0x23E] == [0x0BF080, dl["pprobe"]] and P0[dl["pprobe"]:dl["pprobe"] + len(c0)] == c0, "core 0: P:$23C = jsr pprobe, core0_code3()")
    L = {k: int(v, 16) for k, v in p35["labels"].items()}
    check(drums18.decode_bw(bytearray(img), s14.SVC_HOOK) == L["c_dtick32b"], "ARM: the dump's tick heads the DSP service chain")

    # ---------------- core 1
    w1, l1 = PD.core1_code3(PD.C1_STOCK_WORDS)
    C1 = l1["c1loop"]
    def program(N):
        P = P1s + w1 + [0] * (0x8000 - len(P1s) - len(w1))
        P[0x10E:0x110] = [0x0AF080, DRV]
        code = []
        def emit(*ls): code.extend(T_(*ls))
        emit("move x:>$3f80,a", "move #>1,x0", "add x0,a", "move a1,x:>$3f80")
        emit("move x:>$30000,a", "add x0,a", "move a1,x:>$30000")                 # the list grows by one entry per pass
        emit("move x:>$3f81,b", "add x0,b", "move #>3,x1", "cmp x1,b")
        jne_at = len(code); code += [0x0AF0A2, 0]
        emit("clr b", "move x:>$%x,a" % (PD.SH3 + 8), "add x0,a", "move a1,x:>$%x" % (PD.SH3 + 8))
        code[jne_at + 1] = DRV + len(code)
        emit("move b1,x:>$3f81", "move x:>$3f80,a", "move #>%d,x1" % N, "cmp x1,a")
        code += [0x0AF0AA, 0x3FF0, 0x0AF080, C1]
        P[DRV:DRV + len(code)] = code
        return P
    TR = 0x3700
    for N, want256 in ((12, 0), (600, 2)):
        P = program(N)
        pre = T_("move #>$123,r5", "move #>$ffff,m5")
        P[TR:TR + len(pre) + 2] = pre + [0x0AF080, C1]
        post = T_("move r5,x:>$3f90", "move m5,x:>$3f91")
        P[0x3FF0:0x3FF0 + len(post) + 1] = post + [0]
        res, ran = run(P, TR, mem=[('x', 0x30000, [0x30202])], regs_code=[], pc=TR, stop=0x3FF0 + len(post), maxins=30_000_000,
                       dumps=[('x', PD.SH3, 0x18), ('x', 0x30000, 0x400), ('x', 0x3F90, 2)])
        sh = res[('x', PD.SH3)]; lst = res[('x', 0x30000)]
        check(sh[0] == PD.C1MAGIC and sh[17] == PD.FIRSTM and sh[16] == N and sh[1] == 0x30202 + N - 1 and sh[2] == want256,
              f"{N} passes: magic, once-flag, {sh[16]} passes, longest list {sh[1]:#x} (pointer now {lst[0]:#x}), passes / 256 = {sh[2]}")
        check(sh[8] == N // 3 and sh[9] == 3 and sh[10] == 3, f"core-0 blocks {sh[8]}, passes per block last {sh[9]} min {sh[10]}")
        check(lst[0] == 0x30202 + N and all(v == 0 for v in lst[1:]) and res[('x', 0x3F90)] == [0x123, 0xFFFF],
              "nothing written in the list area X:$30001..$303FF; r5 / m5 untouched")
        del res; gc.collect()

    # ---------------- core 0
    w0, l0 = PD.core0_code3(0x3900, 0x3F00, sent=TS)
    # EXTS (Y:$600000) is read for word 9: the interpreter's memory is 512 K words, so patch that one immediate to T600
    i600 = next(i for i in range(len(w0) - 1) if w0[i] == 0x60F400 and w0[i + 1] == PD.EXTS)
    w0[i600 + 1] = T600
    Q = [0] * 0x8000; Q[0x3900:0x3900 + len(w0)] = w0; Q[0x3F00] = 0x00000C
    sent0 = [0x100000 + i for i in range(len(TS))]
    def run0(calls, change=None, magic=PD.C1MAGIC):
        """`calls` blocks; `change` = (after this block, sentinel indices to change) applied by a driver write between calls."""
        drv = []
        for c in range(calls):
            drv += [0x0BF080, 0x3900]
            if change and c + 1 == change[0]:
                for k in change[1]:
                    drv += T_("move #>$%x,x0" % (0x200000 + k), "move x0,y:>$%x" % TS[k])
        drv += [0x00000C]
        R = list(Q); R[0x2000:0x2000 + len(drv)] = drv
        mem = [('y', t, [v]) for t, v in zip(TS, sent0)] + [('y', T600, [0x777]), ('x', PD.SH3, [magic]), ('x', 0x30000, [0x30234])]
        r, _ = run(R, 0x2000, mem=mem, regs_code=T_("move #>$999,x0", "move #>$555,x1", "move #>$88,r0"), maxins=50_000_000,
                   dumps=[('y', PD.YM, 14), ('x', PD.C0V, 0x30)] + [('y', t, 1) for t in TS])
        return r
    r = run0(24)
    y = r[('y', PD.YM)]
    check(y[0] == PD.MAGIC3 and y[1] == 0 and y[12] == (1 << 24) - 1 and y[7] == 24 and y[9] == 0x777 and y[10] == 0x30234 and y[11] == 0x30234,
          f"first round: all seen, nothing changed, 24 blocks, Y:$600000 word, list {[hex(v) for v in y]}")
    v = r[('x', PD.C0V)]
    check(v[:24] == sent0 and v[0x28:0x2B] == [0x999, 0x555, 0x88], "the previous words recorded; x0 / x1 / r0 saved")
    del r; gc.collect()
    r = run0(80, change=(30, [4, 9, 23]))
    y = r[('y', PD.YM)]
    bits = (1 << 4) | (1 << 9) | (1 << 23)
    check(y[1] == bits and y[13] == bits and y[2] == 0 and y[3] == 0, f"changed after the first round: EVER {y[1]:#x}, current window {y[13]:#x}, no full window yet")
    check(all(r[('y', t)] == [0x200000 + k if k in (4, 9, 23) else sent0[k]] for k, t in enumerate(TS)), "the external words are only read")
    del r; gc.collect()
    r = run0(1100, change=(30, [4]))
    y = r[('y', PD.YM)]
    check(y[1] == 1 << 4 and y[2] == 1 << 4 and y[3] == 1 and y[13] == 0 and y[7] == 1100, f"window closed at block 1024: WIN {y[2]:#x}, windows {y[3]}, current {y[13]:#x}")
    del r; gc.collect()
    r = run0(24, magic=0x123)
    check(r[('y', PD.YM)][0] == 0, "no MAGIC3 without core 1's magic")
    print("SC35D2 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
