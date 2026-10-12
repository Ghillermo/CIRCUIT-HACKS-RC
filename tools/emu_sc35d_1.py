"""SC35D.1 tests: probe35_dsp.V2 (core 1 with its variables in the shared memory, finer map, passes per block, external memory both ways, sentinel) and the image.

    python tools/emu_sc35d_1.py SC35D.1.bin SC35D.1_manifest.json
Image: core 1 = the stock 364 words with P:$12A = jmp c1loop + core1_code2(); core 0: P:$23C = jsr pprobe + core0_code2(); the ARM dump of probe32b with MAGIC2.
Core 1 (interpreter, a driver at P:$10E that counts passes and bumps core 0's block counter every 3 passes): first pass = magic, all P / X / Y bits (the interpreter has
the memory), OMR / SR, first read of the external word; the tested words restored; r5 / m5 untouched; passes per block last = min = 3; every 256 passes: passes / 256, the
external word re-read, core 1's pattern written; the first part runs once (the variables live in the shared memory).
Core 0: the sentinel read before / written once, core 0's pattern every block, the dump words, MAGIC2 only with core 1's magic.
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

TE0, TE1, TES = 0x48000, 0x49000, 0x4A000
DRV = 0x3800                                          # (the interpreter's P memory is 16 K words)


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
    real, l1 = PD.core1_code2(PD.C1_STOCK_WORDS)
    check(len(P1s) == PD.C1_STOCK_WORDS and P1[:PD.C1_STOCK_WORDS] == [0x0C0000 | l1["c1loop"] if i == PD.C1_HOOK else w for i, w in enumerate(P1s)],
          f"core 1: the stock 364 words, P:$12A = jmp c1loop ({P1[PD.C1_HOOK]:#x})")
    check(P1[PD.C1_STOCK_WORDS:] == real and len(P1) < min(PD.PTEST2), f"core 1: our words = core1_code2(), {len(P1)} words in all (below the first P test ${min(PD.PTEST2):x})")
    dl = {k: int(v, 16) for k, v in rep["sc16"]["dsp_labels"].items()}
    P0 = W(dsp_program(img, 0))
    c0 = PD.core0_code2(dl["pprobe"], PD.PREMIX)[0]
    check(P0[0x23C:0x23E] == [0x0BF080, dl["pprobe"]] and P0[dl["pprobe"]:dl["pprobe"] + len(c0)] == c0, "core 0: P:$23C = jsr pprobe, core0_code2()")
    L = {k: int(v, 16) for k, v in p35["labels"].items()}
    check(drums18.decode_bw(bytearray(img), s14.SVC_HOOK) == L["c_dtick32b"], "ARM: the dump's tick heads the DSP service chain")

    # ---------------- core 1 in the interpreter
    w1, l1 = PD.core1_code2(PD.C1_STOCK_WORDS, ext0=TE0, ext1=TE1)
    C1 = l1["c1loop"]
    def program(N):
        P = P1s + w1 + [0] * (0x8000 - len(P1s) - len(w1))
        P[0x10E:0x110] = [0x0AF080, DRV]
        code = []
        def emit(*ls): code.extend(T_(*ls))
        emit("move x:>$3f80,a", "move #>1,x0", "add x0,a", "move a1,x:>$3f80")
        emit("move x:>$3f81,b", "add x0,b", "move #>3,x1", "cmp x1,b")
        jne_at = len(code); code += [0x0AF0A2, 0]
        emit("clr b", "move x:>$%x,a" % (PD.SH + 8), "add x0,a", "move a1,x:>$%x" % (PD.SH + 8))
        code[jne_at + 1] = DRV + len(code)
        emit("move b1,x:>$3f81", "move x:>$3f80,a", "move #>%d,x1" % N, "cmp x1,a")
        code += [0x0AF0AA, 0x3FF0, 0x0AF080, C1]                                  # jeq stop / jmp c1loop
        P[DRV:DRV + len(code)] = code
        P[0x3FF0] = 0
        return P
    mem = [('y', TE0, [PD.PAT0]), ('x', 0x30000, [0x30202])] + [(sp, ad, [0x100 + i]) for i, (sp, ad) in enumerate(PD.XYTEST2)]
    pre = T_("move #>$123,r5", "move #>$ffff,m5")
    N = 12
    P = program(N)
    TR = 0x3700
    P[TR:TR + len(pre) + 2] = pre + [0x0AF080, C1]
    post = T_("move r5,x:>$3f90", "move m5,x:>$3f91")
    P[0x3FF0:0x3FF0 + len(post) + 1] = post + [0]
    res, ran = run(P, TR, mem=mem, regs_code=[], pc=TR, stop=0x3FF0 + len(post), maxins=2_000_000,
                   dumps=[('x', PD.SH, 0x20), ('y', TE1, 1), ('x', 0x3F80, 2), ('x', 0x3F90, 2)] + [('p', a, 1) for a in PD.PTEST2]
                   + [(sp, ad, 1) for sp, ad in PD.XYTEST2])
    sh = res[('x', PD.SH)]
    check(sh[0] == PD.C1MAGIC and sh[2] == (1 << len(PD.PTEST2)) - 1 and sh[3] == (1 << len(PD.XYTEST2)) - 1,
          f"first pass: magic, P bits {sh[2]:#x}, X/Y bits {sh[3]:#x} ({ran} instructions)")
    check(sh[5] == PD.PAT0 and sh[17] == PD.FIRSTM and sh[16] == N, f"first read of Y:$640000 {sh[5]:#x}; the once-flag kept, {sh[16]} passes counted")
    check(all(res[('p', a)] == [P[a]] for a in PD.PTEST2) and all(res[(sp, ad)] == [0x100 + i] for i, (sp, ad) in enumerate(PD.XYTEST2)), "the tested P / X / Y words restored")
    check(res[('x', 0x3F90)] == [0x123, 0xFFFF], f"r5 / m5 untouched {[hex(v) for v in res[('x', 0x3F90)]]}")
    check(res[('x', 0x3F80)][0] == N and sh[8] == N // 3 and sh[9] == 3 and sh[10] == 3, f"{N} passes, {sh[8]} blocks, passes per block last {sh[9]} min {sh[10]}")
    check(sh[1] == 0 and sh[4] == 0 and res[('y', TE1)] == [0], "fewer than 256 passes: nothing published yet")
    del res; gc.collect()
    # 600 passes: published twice
    N3 = 600
    P3 = program(N3)
    res3, _ = run(P3, C1, mem=mem, regs_code=[], pc=C1, stop=0x3FF0, maxins=30_000_000, dumps=[('x', PD.SH, 0x20), ('y', TE1, 1)])
    s3 = res3[('x', PD.SH)]
    check(s3[1] == 2 and s3[4] == PD.PAT0 and res3[('y', TE1)] == [PD.PAT1] and s3[9] == 3 and s3[10] == 3,
          f"after {N3} passes: passes / 256 = {s3[1]}, Y:$640000 re-read {s3[4]:#x}, core 1's pattern {res3[('y', TE1)][0]:#x}, per block {s3[9]} / {s3[10]}")
    del res3; gc.collect()

    # ---------------- core 0
    w0, l0 = PD.core0_code2(0x3900, 0x3F00, ext0=TE0, ext1=TE1, exts=TES)
    Q = [0] * 0x8000; Q[0x3900:0x3900 + len(w0)] = w0; Q[0x3F00] = 0x00000C
    shm = [0] * 0x20
    shm[0:11] = [9, 1, 2, 3, 4, 5, 6, 7, 40, 33, 22]
    drv0 = [0x0BF080, 0x3900] * 3 + [0x00000C]
    Q[0x3E00:0x3E00 + len(drv0)] = drv0
    for magic, want in ((PD.C1MAGIC, PD.MAGIC2), (0x123, 0)):
        shm[0] = magic
        r0, _ = run(Q, 0x3E00, mem=[('x', PD.SH, shm), ('y', TE1, [PD.PAT1]), ('y', TES, [0x777])], regs_code=T_("move #>$999,x0", "move #>$88,r0"),
                    dumps=[('y', PD.YM, 14), ('y', TE0, 1), ('y', TES, 1), ('x', PD.SH + 8, 1), ('x', PD.C0F, 3)])
        y = r0[('y', PD.YM)]
        check(y == [want, 1, 2, 3, 4, PD.PAT1, 33, 22, 43, 0x777, PD.PATS, 6, 7, 5],
              f"core 0 (core-1 magic {magic:#x}): dump {[hex(v) for v in y]}")
        check(r0[('y', TE0)] == [PD.PAT0] and r0[('y', TES)] == [PD.PATS] and r0[('x', PD.SH + 8)] == [43] and r0[('x', PD.C0F)][1:] == [0x999, 0x88],
              "core 0's pattern, the sentinel written once (read before = $777), 3 blocks counted, x0 / r0 restored")
        del r0; gc.collect()
    print("SC35D.1 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
