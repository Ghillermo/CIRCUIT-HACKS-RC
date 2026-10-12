"""SC35D tests: the DSP core-1 probe (tools/probe35_dsp.py) on the dsp56kEmu interpreter, and the image.

    python tools/emu_sc35d.py SC35D.bin SC35D_manifest.json
Image: the core-1 pointer (0x08029700 + 8) -> the new block; its first 364 words = stock but P:$12A = jmp c1loop; core 0: P:$23C = jsr pprobe; the ARM dump of
probe32b at the head of the DSP service chain.
Core 1 (the code assembled with the external words in the interpreter's memory; the stock loop P:$10E replaced by a driver that counts passes and changes core 0's block
counter every 3 passes): the first pass writes the magic, all P / X / Y test bits (the interpreter has the memory), the word of core 0, its own pattern, the list
pointer; the P / X / Y words are restored; a, b, x0, x1, r0 restored; passes per block = 3 (last, min); the pass counter / 256 reaches the shared memory.
Core 0: first call writes the pattern for core 1 once; every call counts a block and copies the shared answers to Y:$3B11..; the magic only with core 1's magic.
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import probe35_dsp as PD  # noqa: E402
import drums18  # noqa: E402
import build_sc14 as s14  # noqa: E402

TE0, TE1 = 0x48000, 0x49000
DRV = 0x3800                                         # (the interpreter's P memory is 16 K words: $4000+ mirrors)


def T_(*l): return G.T(*l)


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    stock = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    rep = man["report"]; p35 = rep["probe35"]
    c1 = dsp_program(img, 1); c1s = dsp_program(stock, 1)
    W = lambda bb: [int.from_bytes(bb[i:i + 3], "big") for i in range(0, len(bb), 3)]
    P1, P1s = W(c1), W(c1s)
    check(len(P1s) == PD.C1_STOCK_WORDS and P1[:PD.C1_STOCK_WORDS] == [0x0C016C if i == PD.C1_HOOK else w for i, w in enumerate(P1s)],
          f"core 1: the stock 364 words, P:$12A = jmp $16C ({P1[PD.C1_HOOK]:#x}); {len(P1)} words in all")
    real, l1 = PD.core1_code(PD.C1_STOCK_WORDS)
    check(P1[PD.C1_STOCK_WORDS:] == real, "core 1: our words = core1_code()")
    dl = {k: int(v, 16) for k, v in rep["sc16"]["dsp_labels"].items()}
    P0 = W(dsp_program(img, 0))
    check(P0[0x23C:0x23E] == [0x0BF080, dl["pprobe"]] and P0[dl["pprobe"]:dl["pprobe"] + len(PD.core0_code(dl["pprobe"], PD.PREMIX)[0])] == PD.core0_code(dl["pprobe"], PD.PREMIX)[0], "core 0: P:$23C = jsr pprobe, the code")
    L = {k: int(v, 16) for k, v in p35["labels"].items()}
    check(drums18.decode_bw(bytearray(img), s14.SVC_HOOK) == L["c_dtick32b"], "ARM: the dump's tick heads the DSP service chain")

    # ---------------- core 1 in the interpreter
    w1, l1 = PD.core1_code(PD.C1_STOCK_WORDS, ext0=TE0, ext1=TE1)
    P = P1s + w1 + [0] * (0x8000 - len(P1s) - len(w1))
    # the driver: P:$10E (the stock loop, which polls hardware) -> count passes, every 3rd pass bump core 0's block counter, after N passes stop
    N = 12
    # the driver: pass counter p (X:$3F80), sub-counter s (X:$3F81): s == 3 -> s = 0, block++ ; p == N -> stop (jmp $3FF0)
    P[0x10E:0x110] = [0x0AF080, DRV]
    code = []
    def emit(*ls): code.extend(T_(*ls))
    emit("move x:>$3f80,a", "move #>1,x0", "add x0,a", "move a1,x:>$3f80")
    emit("move x:>$3f81,b", "add x0,b", "move #>3,x1", "cmp x1,b")
    jne_at = len(code); code += [0x0AF0A2, 0]
    emit("clr b", "move x:>$%x,a" % (PD.SH + 8), "add x0,a", "move a1,x:>$%x" % (PD.SH + 8))
    skip = len(code)
    code[jne_at + 1] = DRV + skip
    emit("move b1,x:>$3f81", "move x:>$3f80,a", "move #>%d,x1" % N, "cmp x1,a")
    code += [0x0AF0AA, 0x3FF0, 0x0AF080, 0x16C]                                  # jeq stop / jmp c1loop
    P[DRV:DRV + len(code)] = code
    P[0x3FF0] = 0
    mem = [('y', TE0, [PD.PAT0]), ('x', 0x30000, [0x30202]), ('x', 0x1000, [0x111111]), ('y', 0x3000, [0x222222])]
    pre = T_("move #>$a1a1a1,a", "move #>$b1b1b1,b", "move #>$123456,x0", "move #>$654321,x1", "move #>$77,r0")
    res, ran = run(P, 0x16C, mem=mem, regs_code=[], pc=0x16C, stop=0x3FF0, maxins=2_000_000,
                   dumps=[('x', PD.SH, 0x20), ('y', TE1, 1), ('x', PD.C1V, 16), ('x', 0x3F80, 2), ('x', 0x1000, 1), ('y', 0x3000, 1)] + [('p', a, 1) for a in PD.PTEST])
    sh = res[('x', PD.SH)]
    check(sh[0] == PD.C1MAGIC and sh[2] == (1 << len(PD.PTEST)) - 1 and sh[3] == 0xF, f"first pass: magic, P bits {sh[2]:#x}, X/Y bits {sh[3]:#x} ({ran})")
    check(sh[4] == PD.PAT0 and res[('y', TE1)] == [PD.PAT1] and sh[5] == 0x30202, f"external memory: core 1 read {sh[4]:#x}, wrote {res[('y', TE1)][0]:#x}; X:$30000 {sh[5]:#x}")
    check(all(res[('p', a)] == [P[a]] for a in PD.PTEST) and res[('x', 0x1000)] == [0x111111] and res[('y', 0x3000)] == [0x222222], "the tested P / X / Y words restored")
    check(res[('x', 0x3F80)][0] == N and sh[8] == N // 3, f"{N} passes, {sh[8]} core-0 blocks")
    check((sh[1], sh[0x18], sh[0x19]) == (0, 0, 0) and res[('x', PD.C1V)][4] == 3, f"fewer than 256 passes: nothing published yet; the internal minimum is 3 passes per block ({res[('x', PD.C1V)][4]})")
    # the registers: run one pass from a trampoline that loads them and stores them after
    TR = 0x3700
    tr = pre + [0x0AF080, 0x16C]
    P2 = list(P); P2[TR:TR + len(tr)] = tr
    P2[0x10E:0x110] = [0x0AF080, 0x3780]
    post = T_("move a1,x:>$3f90", "move b1,x:>$3f91", "move x0,x:>$3f92", "move x1,x:>$3f93", "move r0,x:>$3f94")
    P2[0x3780:0x3780 + len(post) + 1] = post + [0]
    res2, _ = run(P2, TR, mem=mem, regs_code=[], pc=TR, stop=0x3780 + len(post), dumps=[('x', 0x3F90, 5)])
    check(res2[('x', 0x3F90)] == [0xA1A1A1, 0xB1B1B1, 0x123456, 0x654321, 0x77], f"a1 b1 x0 x1 r0 restored {[hex(v) for v in res2[('x', 0x3F90)]]}")
    # 256 passes: the counters reach the shared memory
    P3 = list(P); N3 = 600
    P3[DRV:DRV + len(code)] = code
    P3[DRV + len(code) - 7:DRV + len(code) - 5] = T_("move #>%d,x1" % N3)
    res3, _ = run(P3, 0x16C, mem=mem, regs_code=[], pc=0x16C, stop=0x3FF0, maxins=20_000_000, dumps=[('x', PD.SH, 0x20)])
    s3 = res3[('x', PD.SH)]
    check(s3[1] == 2 and s3[0x18] == 3 and s3[0x19] == 3, f"after {N3} passes: passes / 256 = {s3[1]}, per block last {s3[0x18]} min {s3[0x19]}")

    # ---------------- core 0
    w0, l0 = PD.core0_code(0x3900, 0x3F00, ext0=TE0, ext1=TE1)
    Q = [0] * 0x8000; Q[0x3900:0x3900 + len(w0)] = w0; Q[0x3F00] = 0x00000C
    shm = [9, 1, 2, 3, 4, 5, 6, 7, 40] + [0] * 15 + [33, 22]
    drv0 = [0x0BF080, 0x3900] * 3 + [0x00000C]
    Q[0x3E00:0x3E00 + len(drv0)] = drv0
    for magic, want in ((PD.C1MAGIC, PD.MAGIC), (0x123, 0)):
        shm[0] = magic
        r0, _ = run(Q, 0x3E00, mem=[('x', PD.SH, shm), ('y', TE1, [PD.PAT1]), ('x', 0x30000, [0x30202])], regs_code=T_("move #>$999,x0", "move #>$88,r0"),
                    dumps=[('y', PD.YM, 14), ('y', TE0, 1), ('x', PD.SH + 8, 1), ('x', PD.C0F, 3)])
        y = r0[('y', PD.YM)]
        check(y[0] == want and y[1:6] == [magic, 1, 2, 3, 4] and y[6] == PD.PAT1 and y[7:10] == [33, 22, 43] and y[10:13] == [6, 7, 5] and y[13] == 0x30202,
              f"core 0 (core-1 magic {magic:#x}): dump {[hex(v) for v in y]}")
        check(r0[('y', TE0)] == [PD.PAT0] and r0[('x', PD.SH + 8)] == [43] and r0[('x', PD.C0F)][1:] == [0x999, 0x88], "the pattern for core 1, 3 blocks counted, x0 / r0 saved")
    print("SC35D RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
