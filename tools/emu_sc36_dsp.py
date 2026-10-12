"""SC36 DSP core 0 tests (the real program of the image on the dsp56kEmu interpreter) + the core-1 tests (emu_gran_core1) + the differential test of
the compact tables / the unchanged voices against SC35 (emu_compact).

    python tools/emu_sc36_dsp.py SC36.bin SC36_manifest.json SC35.bin SC35_manifest.json
  * the program: core 0 ends below $4000; core 1 = the stock words with P:$12A = jmp c1loop + granular_dsp.core1_code(), inside 2 K words;
  * the tail of the Master FX chain (smp_post): the copies for core 1 (the oscillator blocks, the voice blocks, the sample table, the capture length,
    the master block, the Glitch words of the ARM), CNT + 1, RDOFS = 64 ((CNT + 1) & 1); with the magic in GARM the master = GOUT[RDOFS], without it
    the master is untouched; r1 = $2E10 on return;
  * vpre: a voice with ACT 2 and DFLAGS bit 4 plays OUT[RDOFS + 32 t] through its chain (= the same samples as a line input through the same chain);
    GNEW is added into the voice state of core 1; ACT bit 12 -> DFLAGS bit 4 through the mailbox;
  * every voice without bit 4 and every drum control: the same as SC35 (emu_compact, without the length check).
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import granular_dsp as GD  # noqa: E402
import vcf21_dsp as V  # noqa: E402
import probe35_dsp as P5  # noqa: E402
import emu_gran_core1 as C1  # noqa: E402
import emu_compact as EC  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import sampler_dsp as S  # noqa: E402

N, RING = 32, 0x1000


def main(img, man, ref, rman):
    fails = C1.main()
    gc.collect()
    fails += EC.main(img, man, ref, rman, shrink=None)
    gc.collect()
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    W = lambda bb: [int.from_bytes(bb[i:i + 3], "big") for i in range(0, len(bb), 3)]
    P0, P1 = W(dsp_program(img, 0)), W(dsp_program(img, 1))
    stock = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    P1s = W(dsp_program(stock, 1))
    w1, l1 = GD.core1_code(P5.C1_STOCK_WORDS)
    check(len(P0) <= 0x4000, f"core 0 program ends at P:${len(P0):x} ({0x4000 - len(P0)} words free)")
    check(P1[:P5.C1_STOCK_WORDS] == [0x0C0000 | l1["c1loop"] if i == P5.C1_HOOK else x for i, x in enumerate(P1s)] and P1[P5.C1_STOCK_WORDS:] == w1 and len(P1) <= 0x800,
          f"core 1: stock + jmp c1loop + core1_code(), {len(P1):#x} words ({0x800 - len(P1)} free)")
    dl = {k: int(v, 16) for k, v in man["report"]["sc16"]["dsp_labels"].items()}

    # ---------------------------------------------------------------- the tail (smp_post)
    A = [(0x100000 + i) for i in range(0xC0)]; B = [(0x200000 + i) for i in range(0x60)]; Ct = [(0x300000 + i) for i in range(0x100)]
    M = [(0x050000 + 3 * i) for i in range(64)]; Go = [(0x070000 + 5 * i) for i in range(64)]
    def tail(magic):
        mem = [('x', 0x3A, [N]), ('x', S.MAGIC_AT, [S.MAGIC]), ('x', 0x3900, A), ('x', 0x3B80, B), ('x', 0x1D8D, Ct), ('x', 0x3D09, [12345]), ('x', 0x2E10, M),
               ('x', GD.GARM, [magic, 10, 20, 30, 40]), ('x', GD.CNT, [7]), ('x', GD.RDOFS, [64]), ('x', GD.GOUT + 64, Go)]
        res, ran = run(P0, dl["smp_post"], mem=mem, regs_code=G.T("move #>$1234,r1"),
                       dumps=[('x', GD.SHA, 0x221), ('x', GD.MIN, 64), ('x', GD.GIN, 5), ('x', GD.CNT, 6), ('x', 0x2E10, 64)])
        assert 'pc=00' in ran, ran
        return res
    r = tail(GD.GMAGIC)
    sh = r[('x', GD.SHA)]
    check(sh[:0xC0] == A and sh[0xC0:0x120] == B and sh[0x120 + 64 * 3:0x120 + 64 * 4] == Ct[64 * 3:64 * 4] and sh[0x220] == 12345 and r[('x', GD.MIN)] == M and r[('x', GD.GIN)] == [GD.GMAGIC, 10, 20, 30, 40],
          "tail: the oscillator / voice blocks, a quarter of the sample table (CNT 7 -> entries 48-63), the capture length, the master and the Glitch words copied for core 1")
    cnt = r[('x', GD.CNT)]
    check(cnt[0] == 8 and cnt[5] == 64 and r[('x', 0x2E10)] == Go, f"tail with the magic: master = GOUT[64], CNT 7 -> {cnt[0]}, RDOFS -> {cnt[5]}")
    r = tail(0)
    check(r[('x', 0x2E10)] == M and r[('x', GD.CNT)][0] == 8, "tail without the magic: the master untouched, CNT still counts")
    import re
    def cost(magic):
        mem = [('x', 0x3A, [N]), ('x', S.MAGIC_AT, [S.MAGIC]), ('x', GD.GARM, [magic])]
        res, ran = run(P0, dl["smp_post"], mem=mem, regs_code=[], dumps=[])
        return int(re.search(r"ins=(\d+)", ran).group(1))
    c_on, c_off = cost(GD.GMAGIC), cost(0)
    check(c_off < 1000 and c_on - c_off < 200, f"the cost of the tail on core 0: smp_post {c_off} instructions (the Glitch on: +{c_on - c_off}) of the ~166000 of a block")
    gc.collect()

    # ---------------------------------------------------------------- vpre: the granular voice
    neutral = {o: 0 for o in range(2, 18)}
    neutral.update({V.P_GAIN: 64, V.P_SUS: 127, V.P_FILT: 0, V.P_ENVA: 63})
    def vstate(act, df, gnew=0):
        blk = [0] * (2 * V.VBS)
        for o, x in neutral.items(): blk[o] = x & 0xFFFFFF
        blk[V.ACT], blk[V.NOTE], blk[V.VEL], blk[V.GATE], blk[V.GNEW] = act, 60, 100, 1, gnew
        osb = [0] * 96; osb[V.DFLAGS_OFF] = df
        return blk, osb
    O = [((0x020000 + 0x3000 * (i % 7)) * (1 if i % 2 else -1)) & 0xFFFFFF for i in range(32)]
    def vp(blk, osb, ring, extra=()):
        mem = [('x', 0x3A, [N]), ('x', V.VB0, blk), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, ring), ('x', V.OSB0, osb), ('x', V.OS2B0, [0] * 96),
               ('x', GD.RDOFS, [64]), ('x', GD.OUT + 64, O), ('x', GD.VS0, [0] * 0x60)] + list(extra)
        res, ran = run(P0, dl["vpre"], mem=mem, dumps=[('y', RING, 2 * N), ('x', GD.VS0, 0x60), ('x', V.OSB0, 96)], regs_code=[])
        assert 'pc=00' in ran, ran
        return res
    outs = []
    for k in range(3):                                                            # a few blocks so the envelope opens
        blk, osb = vstate(2, 16, gnew=1 if k == 0 else 0)
        ra = vp(blk, osb, [0] * (2 * N))
    blk, osb = vstate(2, 16, gnew=1)
    ra = vp(blk, osb, [0] * (2 * N))
    blk, osb = vstate(1, 0, gnew=1)
    ring = [0] * (2 * N); ring[0::2] = O
    rb = vp(blk, osb, ring)
    a_, b_ = ra[('y', RING)][0::2], rb[('y', RING)][0::2]
    check(a_ == b_ and any(a_), f"granular voice: OUT[RDOFS] through the chain = a line input with those samples ({[hex(x) for x in a_[:3]]})")
    check(ra[('x', GD.VS0)][GD.V_GC] == 1 and ra[('x', GD.VS0)][GD.VSS + GD.V_GC] == 0, "GNEW of voice 0 counted into its core-1 state")
    # the mailbox: ACT = 2 | granular << 12 -> DFLAGS 16
    blk, osb = vstate(2, 0)
    blk[V.MB] = (1 << 23) | (19 << 16) | (2 | (1 << 12))
    r = vp(blk, osb, [0] * (2 * N))
    check(r[('x', V.OSB0)][V.DFLAGS_OFF] == 16, f"mailbox: ACT 2 | 1 << 12 -> DFLAGS {r[('x', V.OSB0)][V.DFLAGS_OFF]}")
    print("SC36 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
