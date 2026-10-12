"""SC35DB tests: probe36_dsp (audio blocks DSP core 1 -> core 0 through the shared memory, with a load W on core 1) on the dsp56kEmu interpreter, the
image, and rdiag's DSPW (the PC writes one DSP X word) through the real incoming SysEx route; SC35D9's remote tests again (emu_sc35d8 --delete).

    python tools/emu_sc35db.py SC35DB.bin SC35DB_manifest.json
  * image: core 1 = the stock 364 words with P:$12A = jmp c1loop + core1_code(), inside 2 K words; core 0: P:$23C = jsr pprobe + core0_code();
  * core 1 (a driver bumps core 0's counter every 4 passes): magic once; for each new counter b: block b in buffer b & 1 (word i = (b & $FF) << 16 | i),
    READY = b; with W > 0 the load reads W x 64 words from the source (r4 ends at SRC + 64 W); W = 0 skips it; passes per block last / min = 4;
  * core 0: READY == b and the words right -> no late / corrupt, counter + 1; READY behind -> late; a wrong word -> corrupt; W requested -> core 1;
    the reset request clears late / corrupt / the minimum; before core 1 answers: only counting, no magic;
  * rdiag command 9: DSP_WRITE(0, v << 8, addr) under the semaphore, status 0.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import probe36_dsp as P6  # noqa: E402
import probe35_dsp as P5  # noqa: E402
import rdiag as RD  # noqa: E402
RD.DELETE = RD.DSPX = RD.DSPW = True
import emu_sc35d8 as T8  # noqa: E402
import emu_sc342d as TX  # noqa: E402
import ctremote as CR  # noqa: E402

DRV = 0x3800
TSRC = 0x48000


def T_(*l): return G.T(*l)


def main(img, man):
    fails = T8.main(img, man)
    gc.collect()
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    stock = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    W = lambda bb: [int.from_bytes(bb[i:i + 3], "big") for i in range(0, len(bb), 3)]
    P1, P1s = W(dsp_program(img, 1)), W(dsp_program(stock, 1))
    real, l1 = P6.core1_code(P5.C1_STOCK_WORDS)
    check(P1[:P5.C1_STOCK_WORDS] == [0x0C0000 | l1["c1loop"] if i == P5.C1_HOOK else w for i, w in enumerate(P1s)] and P1[P5.C1_STOCK_WORDS:] == real and len(P1) <= 0x800,
          f"core 1: stock + jmp c1loop + core1_code(), {len(P1)} words (<= 2 K)")
    dl = {k: int(v, 16) for k, v in man["report"]["sc16"]["dsp_labels"].items()}
    P0 = W(dsp_program(img, 0)); c0 = P6.core0_code(dl["pprobe"], P6.PREMIX)[0]
    check(P0[0x23C:0x23E] == [0x0BF080, dl["pprobe"]] and P0[dl["pprobe"]:dl["pprobe"] + len(c0)] == c0, "core 0: P:$23C = jsr pprobe, core0_code()")

    # ---------------- core 1
    w1, l1 = P6.core1_code(P5.C1_STOCK_WORDS, src=TSRC)
    C1 = l1["c1loop"]; SH = P6.SH5
    def program(N, every=4):
        P = P1s + w1 + [0] * (0x8000 - len(P1s) - len(w1))
        P[0x10E:0x110] = [0x0AF080, DRV]
        code = []
        def emit(*ls): code.extend(T_(*ls))
        emit("move x:>$3f80,a", "move #>1,x0", "add x0,a", "move a1,x:>$3f80")
        emit("move x:>$3f81,b", "add x0,b", "move #>%d,x1" % every, "cmp x1,b")
        jne = len(code); code += [0x0AF0A2, 0]
        emit("clr b", "move x:>$%x,a" % (SH + 8), "add x0,a", "move a1,x:>$%x" % (SH + 8))
        code[jne + 1] = DRV + len(code)
        emit("move b1,x:>$3f81", "move x:>$3f80,a", "move #>%d,x1" % N, "cmp x1,a")
        code += [0x0AF0AA, 0x3FF0, 0x0AF080, C1]
        P[DRV:DRV + len(code)] = code; P[0x3FF0] = 0
        return P
    for wl in (0, 3):
        res, ran = run(program(40), C1, mem=[('x', SH + 5, [wl]), ('y', TSRC, list(range(1, 300)))], regs_code=[], pc=C1, stop=0x3FF0, maxins=5_000_000,
                       dumps=[('x', SH, 0x18), ('x', P6.BUF0, 64), ('x', P6.BUF1, 64)])
        sh = res[('x', SH)]; b = sh[4]                                          # the last block generated (the driver bumped the counter after it)
        buf = res[('x', P6.BUF0 if b % 2 == 0 else P6.BUF1)]
        check(sh[0] == P6.C1MAGIC and b == sh[8] - 1 and buf == [((b & 0xFF) << 16) | i for i in range(64)],
              f"W {wl}: block {b} written into buffer {b & 1}, READY = {sh[4]}")
        check(sh[2] == 4 and sh[16 + 4] == 4, f"W {wl}: passes per block last {sh[2]} min {sh[16 + 4]} ({ran} instructions)")
    gc.collect()

    # ---------------- core 0
    w0, l0 = P6.core0_code(0x3900, 0x3F00)
    Q = [0] * 0x8000; Q[0x3900:0x3900 + len(w0)] = w0; Q[0x3F00] = 0x00000C
    Q[0x3E00:0x3E03] = [0x0BF080, 0x3900, 0x00000C]
    def c0(sh, bufs, v=(), regs="move #>$999,x0"):
        mem = [('x', SH, sh)] + [('x', a, d) for a, d in bufs] + [('x', P6.C0V + i, [x]) for i, x in v]
        r, _ = run(Q, 0x3E00, mem=mem, regs_code=T_(regs, "move #>$88,r0"), dumps=[('x', P6.C0V, 16), ('x', SH, 24)])
        return r[('x', P6.C0V)], r[('x', SH)]
    good = lambda b: ((b & 0xFF) << 16)
    shm = [P6.C1MAGIC, 7, 30, 25, 5, 3] + [0] * 2 + [5] + [0] * 7 + [0, 0, 0, 0, 21]
    v, sh = c0(shm, [(P6.BUF1, [good(5) | i for i in range(64)])], v=[(8, 6)])
    check(v[0] == P6.MAGIC and v[1] == 1 and v[2] == 0 and v[3] == 0 and sh[8] == 6 and sh[5] == 6 and v[4] == 21 and v[5] == 30 and v[6] == 7 and v[7] == 3,
          f"block 5 ready and right: no late / corrupt, counter 6, W 6 -> core 1, results copied {[hex(x) for x in v[:10]]}")
    check(v[12:15] == [0x999, 0, 0x88] or (v[12] == 0x999 and v[14] == 0x88), "x0 / r0 saved")
    shm2 = list(shm); shm2[4] = 4
    v, sh = c0(shm2, [(P6.BUF1, [good(5) | i for i in range(64)])])
    check(v[2] == 1 and v[3] == 0 and sh[8] == 6, "READY behind: late + 1")
    bad = [good(5) | i for i in range(64)]; bad[63] = 0x123
    v, sh = c0(shm, [(P6.BUF1, bad)])
    check(v[2] == 0 and v[3] == 1, "a wrong last word: corrupt + 1")
    v, sh = c0(shm, [(P6.BUF1, [good(5) | i for i in range(64)])], v=[(2, 9), (3, 9), (9, 1)])
    check(v[2] == 0 and v[3] == 0 and v[9] == 0 and sh[16 + 4] == 0x7FFFFF, "reset request: late / corrupt / minimum cleared")
    shm3 = list(shm); shm3[0] = 0
    v, sh = c0(shm3, [])
    check(v[0] != P6.MAGIC and v[2] == 0 and v[1] == 1 and sh[8] == 6, "core 1 not there: only counting")
    gc.collect()

    # ---------------- rdiag command 9 (DSPW)
    e = TX.EX(img, man)
    e.log.clear(); e.sysex(list(CR.req_dspw(9, 0x3BE8, 12)))
    p = CR.parse(e.out[0][2], 9, 9) if len(e.out) == 1 else None
    check(p is not None and CR.dec_write(p)["status"] == 0 and e.x.get(0x3BE8) == 12 and e.bad == 0 and e.held == 0, f"dspw X:$3BE8 = 12 under the semaphore ({e.log})")
    print("SC35DB RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
