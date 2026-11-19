"""Alpha 7.06 (tools/xlwin.py, the bug hunt's XL-9): the extra lanes' LED-task transfers no longer share the DSP window with the main loop.
On emu_sc35's card / DSP model (emu_xlfix's harness), the main loop's traffic is simulated: whenever a transfer sleeps (packio's SLEEP, after the
model's block copy) and at every c_copy2 entry (a main-loop c_ywin just before), Y:WIN (packio's window, $3B40..$3B7F) is filled with junk.
  * the fill (c_xlfill): the ITCM block = the DSP's block;
  * the write back (c_xlflush): the DSP's block = the ITCM block;
  * the save (c_xlsave): the file's tail = the 16 blocks;
  * the load (c_xlload): the DSP's blocks = the file's;
  * the LED task's transfers never name Y:WIN (no copy from / to it, no read or write of it); Y:WIN2 ($3B80) is used.
The previous build (Alpha 7.05) fails the four data checks.

    python tools/emu_xlwin.py BUILD.bin manifest.json"""
from __future__ import annotations
import json, random, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R5
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import E35  # noqa: E402
import packio as PK  # noqa: E402
import sampler_dsp as SD  # noqa: E402
import xlanes as XL  # noqa: E402

IT = lambda slot: (XL.KIND_SES, slot, 0xFF)


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    import emu_arp as EAm
    e = E35(img, man); R = man["report"]
    xl = {k: int(v, 16) for k, v in R["xlanes"]["labels"].items()}
    pv = {k: int(v, 16) for k, v in R["xlanes"]["prev"].items()}
    pk = {k: int(v, 16) for k, v in R["packio"]["labels"].items()}
    back = lambda uc, a, s_, d: uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    for k in ("load", "new", "play"): e.uc.hook_add(UC_HOOK_CODE, back, begin=pv[k], end=pv[k])
    rnd = random.Random(7)
    noise = dict(on=False, n=0)
    def junk():
        if not noise["on"]: return
        noise["n"] += 1
        for i in range(PK.NW): e.y[PK.WIN + i] = rnd.randrange(1 << 24)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: junk(), begin=PK.SLEEP & ~1, end=PK.SLEEP & ~1)       # after the model's copy (added later)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: junk(), begin=pk["c_copy2"] & ~1, end=pk["c_copy2"] & ~1)
    named = []                                                         # the window named by the LED task: copies and reads / writes
    def h_cp(uc, a, s_, d):
        if noise["on"]: named.append(("copy", e.x.get(SD.CPSRC, 0), e.x.get(SD.CPDST, 0)))
    e.uc.hook_add(UC_HOOK_CODE, h_cp, begin=PK.SLEEP & ~1, end=PK.SLEEP & ~1)
    def h_rw(uc, w):
        if noise["on"]: named.append(("w" if w else "r", uc.reg_read(UC_ARM_REG_R2 if w else UC_ARM_REG_R1) & 0x7FFF))
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: h_rw(uc, False), begin=PK.DSP_READ & ~1, end=PK.DSP_READ & ~1)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: h_rw(uc, True), begin=PK.DSP_WRITE & ~1, end=PK.DSP_WRITE & ~1)
    meta = lambda: bytes(e.uc.mem_read(XL.XLR + XL.O_CM, 8))
    def setmeta(cached=None, changed=None, wanted=None, m=0):
        for off, v in ((0, cached), (2, changed), (4, wanted)):
            if v is not None: e.uc.mem_write(XL.XLR + XL.O_CM + off + m, bytes([v]))
    def setmap(v): e.call(xl["c_xlst"], maxins=10000); e.uc.mem_write(XL.XLR + XL.O_MAP, struct.pack("<H", v))
    def work():
        noise["on"] = True
        try: e.call(xl["c_xlwork"], maxins=200_000_000)
        finally: noise["on"] = False
    blockwords = lambda b: {XL.XB + b * XL.BLKW + i: rnd.randrange(0x10000) << 8 for i in range(XL.BLKW)}
    dspblock = lambda b: b"".join(struct.pack("<H", (e.ext.get(XL.XB + b * XL.BLKW + i, 0) >> 8) & 0xFFFF) for i in range(XL.BLKW))[:XL.BLK]
    itcm = lambda m=0: bytes(e.uc.mem_read(XL.IC0 + XL.ICS * m, XL.BLK))
    setp = lambda store, k, v: EAm.EA.setp(e, store, k, bytes([v]))
    from emu_xlfix import SES
    def in_win(a_, n=1): return any(PK.WIN <= x < PK.WIN + PK.NW for x in range(a_, a_ + n))

    # the fill
    setp(XL.REC_ON, 0, 1)
    e.ext.clear(); e.ext.update(blockwords(2)); setmap(1 << 2); setmeta(cached=0, wanted=3, changed=0)
    named.clear(); work()
    check(meta()[0] == 3 and itcm() == dspblock(2), f"the fill with the main loop's junk in Y:WIN ({noise['n']} times): the ITCM block = the DSP's")
    fill_named = list(named)
    # the write back
    blk = bytearray(rnd.randrange(256) for _ in range(XL.BLK)); e.uc.mem_write(XL.IC0, bytes(blk)); setmeta(cached=3, changed=1, wanted=5)
    named.clear(); work()
    check(dspblock(2) == bytes(blk), "the write back with junk in Y:WIN: the DSP's block = the ITCM block")
    fl_named = list(named)
    # the save
    e.cur = e.scur = 1
    plain = bytes(random.Random(5).randrange(256) for _ in range(XL.SZ0)); e.sd[IT(2)] = plain
    e.ext.clear(); w = {}; [w.update(blockwords(b)) for b in (0, 1)]; e.ext.update(w); setmap(3)
    named.clear(); setmeta(cached=0, wanted=0, changed=0); setmeta(cached=0, wanted=0, changed=0, m=1)
    e.set_p0(e.r32(SES + 0x60), 1); e.uc.reg_write(UC_ARM_REG_R5, 2); e.call(xl["c_xlsv"], SES, maxins=2_000_000); work()
    f = e.sd.get(IT(2), b"")
    tail = f[XL.SZ0 + XL.HDR:]
    want = dspblock(0) + dspblock(1)
    check(len(f) == XL.SZ0 + XL.HDR + XL.DATA and tail[:2 * XL.BLK] == want, f"the save with junk in Y:WIN: the file's blocks 0 / 1 = the DSP's ({len(f)} B)")
    sv_named = list(named)
    # the load
    e.ext.clear(); setmap(0)
    e.call(PK.PARAM_GET, e.r32(XL.PROJ_OBJ + 0x20), 8, maxins=100000); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes([2]))
    named.clear(); e.call(xl["c_xlld"], maxins=2_000_000); work()
    check(struct.unpack_from("<H", e.uc.mem_read(XL.XLR + XL.O_MAP, 2))[0] == 3 and dspblock(0) + dspblock(1) == want,
          "the load with junk in Y:WIN: the DSP's blocks 0 / 1 = the file's")
    ld_named = list(named)
    allnamed = fill_named + fl_named + sv_named + ld_named
    bad = [x for x in allnamed if (x[0] == "copy" and (in_win(x[1]) or in_win(x[2]))) or (x[0] in "rw" and in_win(x[1]))]
    w2 = [x for x in allnamed if (x[0] == "copy" and (x[1] == 0x3B80 or x[2] == 0x3B80)) or (x[0] in "rw" and 0x3B80 <= x[1] < 0x3BC0)]
    check(not bad and w2, f"the LED task never names Y:WIN ({bad[:3]}); Y:WIN2 used {len(w2)} times")
    print(f"{R['D']['marker']} XLWIN RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())) else 0)
