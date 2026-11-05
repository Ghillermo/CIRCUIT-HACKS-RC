"""S514D / S514D2 tests.

    python tools/emu_s514d.py firmware/s514d/circuittracks-4486-S514D.bin firmware/s514d/manifest.json
ARM (emu_s494d's harness: the real SysEx route, tools/ctremote.py's own protocol functions):
  * ping: the version carries 0x800 (RAMCK);
  * rfill / rchk on a free range: every word = address XOR key, 0 bad; two words changed: 2, the first (address, value) and the last;
  * refused (status 3, nothing written): unaligned, below 0x20000000, an empty range, a range reaching the stack pointer - 256.
Core 1 (granular_dsp.use_memdiag, the build's own core 1 program on the dsp56kEmu interpreter, a driver bumping CNT every PER passes):
  * the report at MREP: the magic, the OMR, the 48 tests (the interpreter's memory: every address reads back), scans done > 0;
  * a block of X that a driver changes every block counts passes; a block never written: its first sum kept, 0 changes; all-zero flags.
With S514D2 (tools/c1ms.py): the call for core 1's program goes through c_c1ms, which sends the stub (0x080296E0) to core 1 first.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_SP
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_s494d as S4  # noqa: E402
import rdiag as RD  # noqa: E402
import ctremote as CR  # noqa: E402
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import granular_dsp as GD  # noqa: E402

KEY = 0x3C5AA5C3
DRV, STOP, PASS = 0x3800, 0x3FF0, 0x3F80


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]
    # ---------------------------------------------------------------- ARM: the RAM canary
    RD.RAMCK = True
    gc.collect(); e = S4.E(img, man)
    def ask(make, cmd, seq=9):
        e.sysex(list(make(seq))); return CR.parse(e.out[0][2], cmd, seq) if len(e.out) == 1 else None
    ver = CR.dec_ping(ask(CR.req_ping, 1))["version"]
    check(ver & 0x800, f"ping: version {ver:#x} with RAMCK (0x800)")
    lo, n = 0x2004B000, 0x400
    e.uc.mem_write(lo, b"\x55" * n)
    d = CR.dec_rchk(ask(lambda s: CR.req_rfill(s, lo, n, KEY), 16))
    words = struct.unpack_from("<%dI" % (n // 4), bytes(e.uc.mem_read(lo, n)))
    check(d["status"] == 0 and all(w == (lo + 4 * i) ^ KEY for i, w in enumerate(words)), f"rfill: [{lo:#x}, +{n:#x}) = address XOR key ({d})")
    d = CR.dec_rchk(ask(lambda s: CR.req_rchk(s, lo, n, KEY), 17))
    check(d == dict(status=0, bad=0, first=0, value=0, last=0), f"rchk right after: {d}")
    e.uc.mem_write(lo + 0x40, struct.pack("<I", 0xDEADBEEF)); e.uc.mem_write(lo + 0x200, struct.pack("<I", 0x12345678))
    d = CR.dec_rchk(ask(lambda s: CR.req_rchk(s, lo, n, KEY), 17))
    check(d == dict(status=0, bad=2, first=lo + 0x40, value=0xDEADBEEF, last=lo + 0x200), f"rchk after two writes: {d}")
    sp = e.uc.reg_read(UC_ARM_REG_SP)
    for name, (a_, n_) in dict(unaligned=(lo + 2, 16), low=(0x1FFFF000, 16), empty=(lo, 0), stack=((sp - 0x100) & ~3, 0x200)).items():
        e.uc.mem_write(lo, b"\x55" * 16)
        d = CR.dec_rchk(ask(lambda s: CR.req_rfill(s, a_, n_, KEY), 16))
        check(d["status"] == 3 and bytes(e.uc.mem_read(lo, 16)) == b"\x55" * 16, f"rfill refused: {name} ({d['status']})")
    c1ms = "c1ms" in R
    if c1ms:
        site = 0x080292A6 - 0x08010000
        from thumb import bl as bl_enc
        check(bytes(img[site:site + 4]) == bl_enc(0x080292A6, int(R["c1ms"]["labels"]["c_c1ms"], 16)), "S514D2: core 1's program call through c_c1ms")
        sent = []
        def snd(uc, a, s, d_): sent.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1))); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        h1 = e.uc.hook_add(UC_HOOK_CODE, snd, begin=0x08029200, end=0x08029200)
        h2 = e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d_: uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1), begin=0x0801B394, end=0x0801B394)
        dz = int(R["dspz"]["labels"]["c_dspz"], 16)
        h3 = e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d_: (sent.append(("dspz", uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1))),
                                                                uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)), begin=dz, end=dz)
        e.call(int(R["c1ms"]["labels"]["c_c1ms"], 16), 0x08012345, 1, maxins=100_000)
        check(sent == [(0x080296E0, 1), ("dspz", 0x08012345, 1)], f"c_c1ms: the stub to core 1, then the program on to c_dspz ({sent})")
    del e; gc.collect()
    # ---------------------------------------------------------------- core 1: the report
    W = lambda bb: [int.from_bytes(bb[i:i + 3], "big") for i in range(0, len(bb), 3)]
    import dsp56, probe35_dsp as P5                                           # core 1 rebuilt with the build's options, the report at Y:$C000
    dsp56.use_shortx(); GD.use_stereo(); GD.use_overload(); GD.FMC1 = True; GD.MEMDIAG = True
    stock = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    MR = GD.MREP = 0xC000                                                     # (the interpreter's memory is 512 K words)
    w1, lab = GD.core1_code(P5.C1_STOCK_WORDS, rl=0x40000, rn=0x10000)
    check(P5.C1_STOCK_WORDS + len(w1) == R["granular"]["core1_words"], f"the rebuilt core 1 = the build's size ({P5.C1_STOCK_WORDS + len(w1)})")
    P = W(dsp_program(stock, 1)) + w1
    C1 = lab["c1loop"]
    P += [0] * (0x4000 - len(P))
    P[0x10E:0x110] = [0x0AF080, DRV]
    code = []
    def emit(*ls): code.extend(G.T(*ls))
    emit("move x:>$%x,a" % PASS, "move #>1,x0", "add x0,a", "move a1,x:>$%x" % PASS, "move #>2000,x0", "cmp x0,a")
    code += [0x0AF0A9, C1]
    emit("clr a", "move a,x:>$%x" % PASS, "move x:>$%x,a" % GD.CNT, "move #>1,x0", "add x0,a", "move a1,x:>$%x" % GD.CNT, "move a1,x:>$1040")   # X:$1040 changes
    emit("move #>8,x1", "cmp x1,a")
    code += [0x0AF0AA, STOP, 0x0AF080, C1]
    P[DRV:DRV + len(code)] = code; P[STOP] = 0
    res, ran = run(P, C1, mem=[('x', 0x2000, [0x123456] * 64)], regs_code=[], pc=C1, stop=STOP, maxins=80_000_000,
                   dumps=[('y', MR, 64), ('y', MR + 64, 3 * (GD.M_XN + GD.M_YN))])
    assert ran and 'pc=003ff0' in ran.lower(), ran
    head, blk = res[('y', MR)], res[('y', MR + 64)]
    check(head[0] == 0xC1DD00, f"the report: the magic ({head[0]:#x})")
    tests = head[8:56]
    check(all(t == 0x100 for t in tests), f"the 48 write tests read back on the interpreter ({sum(t == 0x100 for t in tests)})")
    check(head[6] >= 0x100, f"scans done: {head[6] >> 8}")
    k1040, k2000, k1800 = 0x1040 // 64, 0x2000 // 64, 0x1800 // 64
    ch = lambda k: blk[3 * k + 1] >> 8
    nz = lambda k: blk[3 * k + 2] >> 8
    check(ch(k1040) >= 1 and ch(k2000) == 0 and nz(k2000) == 1 and nz(k1800) == 0 and ch(k1800) == 0,
          f"X:$1040's block changed {ch(k1040)} scans; X:$2000 (constant) 0, not zero; X:$1800 zero, 0 changes")
    print(f"{man.get('marker', '?')} S514D RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
