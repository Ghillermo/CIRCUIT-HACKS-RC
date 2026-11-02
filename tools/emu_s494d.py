"""S494D tests: rdiag's ITCM canary and the DSP core select (rdiag.ITCM / CORE1), through the real route (the incoming SysEx dispatcher 0x0801EB30) and
tools/ctremote.py's own protocol functions.  The DSP read / write (0x08029344 / 0x080292F8) and the semaphore are stubbed and logged.

    python tools/emu_s494d.py firmware/s494d/circuittracks-4486-S494D.bin firmware/s494d/manifest.json
  * ping: the version carries 0x100 (ITCM) and 0x200 (CORE1);
  * mem reads the ITCM (0x0-0x3FFF) and still refuses past it;
  * itfill / itchk refuse while ITCMCR has no EN or SZ < 5 (status 2, nothing written);
  * itfill: every word of 0x100-0x3FFF = address XOR key, 0x0-0xFF untouched; itchk: 0 bad, then two changed words = 2, the first one and its value;
  * dspr x / y on core 0 and on core 1 (r0 = the core, Y = 0x8000 | address); dspw with bit 31 = core 1, the address = bits 0..15, value << 8;
  * gatediag: the heads of the bulk enter / leave and of the two host writers; a write inside an interval counted as ours (LR past the image) or the
    stock's (LR elsewhere), outside an interval not at all; the writers' arguments reach the stock code unchanged.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc35d8 as D8  # noqa: E402
import rdiag as RD  # noqa: E402
import ctremote as CR  # noqa: E402
import gatediag as GD  # noqa: E402
import emu_sc05  # noqa: E402

RD.DSPX = RD.DSPW = RD.ITCM = RD.CORE1 = True
KEY = 0x5AC3A53C


class E(D8.E8):
    def __init__(self, image, man):
        super().__init__(image, man)
        self.dsp = []
        def ret(uc, v):
            uc.reg_write(UC_ARM_REG_R0, v & 0xFFFFFFFF); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        def rd(uc, a, s, d):
            c, ad = uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1); self.dsp.append(("r", c, ad)); ret(uc, ((c << 20) | ad) << 8)
        def wr(uc, a, s, d):
            self.dsp.append(("w", uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R1))); ret(uc, 0)
        def sem(uc, a, s, d): ret(uc, 0)
        self.dsph = [self.uc.hook_add(UC_HOOK_CODE, f, begin=ad, end=ad) for f, ad in ((rd, RD.DSP_READ), (wr, RD.DSP_WRITE), (sem, RD.SEM_TAKE), (sem, RD.SEM_GIVE))]


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    gc.collect(); e = E(img, man)
    def ask(make, cmd, seq=9):
        e.sysex(list(make(seq))); return CR.parse(e.out[0][2], cmd, seq) if len(e.out) == 1 else None
    ver = RD.VERSION + 0x10 + 0x40 + 0x100 + 0x200
    check(CR.dec_ping(ask(CR.req_ping, 1))["version"] == ver, f"ping: version {ver:#x} (DSPX, DSPW, ITCM, CORE1)")
    e.uc.mem_write(0x40, bytes(range(0x30, 0x40)))
    check(CR.dec_mem(ask(lambda s: CR.req_mem(s, 0x40, 16), 2)) == dict(status=0, data=bytes(range(0x30, 0x40))), "mem reads the ITCM (0x40, 16 B)")
    check(CR.dec_mem(ask(lambda s: CR.req_mem(s, 0x3FF8, 16), 2))["status"] == 1, "mem past the ITCM (0x3FF8 + 16): status 1")
    e.uc.mem_write(0, b"\x77" * 0x4000)
    for cr in (0, 0x28, 0x21):                                  # off; SZ 5 but not enabled; enabled, SZ 4
        e.uc.mem_write(RD.ITCMCR, struct.pack("<I", cr))
        d = CR.dec_itchk(ask(lambda s: CR.req_itfill(s, KEY), 13))
        check(d["status"] == 2 and d["itcmcr"] == cr and bytes(e.uc.mem_read(0, 0x4000)) == b"\x77" * 0x4000, f"itfill with ITCMCR {cr:#x}: refused, nothing written")
    e.uc.mem_write(RD.ITCMCR, struct.pack("<I", 0x29))          # EN, SZ = 5 (16 KB)
    d = CR.dec_itchk(ask(lambda s: CR.req_itfill(s, KEY), 13))
    words = struct.unpack("<4096I", bytes(e.uc.mem_read(0, 0x4000)))
    check(d["status"] == 0 and all(words[i] == (4 * i) ^ KEY for i in range(64, 4096)) and bytes(e.uc.mem_read(0, 0x100)) == b"\x77" * 0x100,
          "itfill: 0x100-0x3FFF = address XOR key, the first 256 B untouched")
    d = CR.dec_itchk(ask(lambda s: CR.req_itchk(s, KEY), 14))
    check(d["status"] == 0 and d["bad"] == 0, f"itchk right after: {d}")
    e.uc.mem_write(0x1234, struct.pack("<I", 0xDEADBEEF)); e.uc.mem_write(0x3FFC, struct.pack("<I", 0))
    d = CR.dec_itchk(ask(lambda s: CR.req_itchk(s, KEY), 14))
    check(d == dict(status=0, itcmcr=0x29, bad=2, first=0x1234, value=0xDEADBEEF), f"itchk after two writes: {d}")
    check(CR.dec_itchk(ask(lambda s: CR.req_itchk(s, KEY ^ 1), 14))["bad"] == 4096 - 64, "itchk with another key: every word bad")
    for sp, core, base in ((0, 0, 0), (1, 0, 0x8000), (2, 1, 0), (3, 1, 0x8000)):
        e.dsp.clear()
        d = CR.dec_dspr(ask(lambda s: CR.req_dspr(s, sp, 0x4000, 3), 3))
        want = [("r", core, base | (0x4000 + i)) for i in range(3)]
        check(e.dsp == want and d["words"] == [(core << 20 | base | (0x4000 + i)) & 0xFFFFFF for i in range(3)], f"dspr space {sp}: core {core}, {e.dsp}")
    for addr, core in ((0x3F41, 0), (0x80002B00, 1)):
        e.dsp.clear(); ask(lambda s: CR.req_dspw(s, addr, 0x123456), 9)
        check(e.dsp == [("w", core, addr & 0xFFFF, 0x12345600)], f"dspw {addr:#x}: core {core}, {e.dsp}")
    # ---- gatediag: the stock bodies are cut at their first instruction after our head (+ 4): logged, back to the caller
    for hd in e.dsph: e.uc.hook_del(hd)                       # the writers run our heads now
    GL = {k: int(v, 16) for k, v in man["report"]["gatediag"]["labels"].items()}
    import drums18
    check(all(drums18.decode_bw(bytearray(img), f) == GL[l] for f, l in ((GD.ENTER, "c_dgon"), (GD.LEAVE, "c_dgoff"), (GD.W16, "c_dgw16"), (GD.W24, "c_dgw24"))),
          "the four heads: b.w c_dgon / c_dgoff / c_dgw16 / c_dgw24")
    W16, W24 = GL["c_dgw16"], GL["c_dgw24"]                     # the emulation's base classes return from 0x080292F8 at entry: enter the head's target
    reach = []
    def cut(uc, a, sz, d):
        reach.append((a, uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2))); uc.reg_write(UC_ARM_REG_PC, emu_sc05.STOP | 1)
    for f in (GD.ENTER, GD.LEAVE, GD.W16, GD.W24):
        e.uc.hook_add(UC_HOOK_CODE, cut, begin=f + 4, end=f + 4)
    STUB = 0x20060400                                          # blx r4 from RAM: a caller with a stock-like LR
    e.uc.mem_write(STUB, bytes.fromhex("a047"))
    def stock_call(fn, *args):
        e.uc.reg_write(UC_ARM_REG_R4, fn | 1); e.call(STUB, *args)
    blk = lambda: struct.unpack("<6I", bytes(e.uc.mem_read(GD.BLOCK, 24)))
    e.uc.mem_write(GD.BLOCK, bytes(range(24)))                  # garbage until the first enter
    e.call(W16, 0, 0x111100, 0x3A00)
    check(blk() == struct.unpack("<6I", bytes(range(24))) and reach[-1] == (GD.W16 + 4, 0, 0x111100, 0x3A00), "a write before any interval: the block untouched, the stock body gets r0-r2")
    stock_call(GD.ENTER, 0)
    check(blk() == (GD.SIG, 1, 1, 0, 0, 0) and reach[-1][0] == GD.ENTER + 4, f"enter: the block set up, in an interval, 1 interval ({blk()})")
    e.call(W16, 0, 0x222200, 0x3A01); e.call(W24, 1, 0x333300, 0x8001)
    check(blk()[3] == 2 and blk()[5] == emu_sc05.STOP | 1 and reach[-1] == (GD.W24 + 4, 1, 0x333300, 0x8001), f"two writes of ours inside: counted, last LR kept, arguments intact ({blk()})")
    stock_call(W16, 0, 0x444400, 0x3A02)
    check(blk()[4] == 1 and blk()[3] == 2, f"a stock write inside: counted as the stock's ({blk()})")
    stock_call(GD.LEAVE, 0)
    e.call(W16, 0, 0x555500, 0x3A03)
    check(blk()[1] == 0 and blk()[3] == 2 and reach[-1][0] == GD.W16 + 4, f"leave: out of the interval, a later write not counted ({blk()})")
    stock_call(GD.ENTER, 0)
    check(blk()[:3] == (GD.SIG, 1, 2) and blk()[3] == 2, "a second enter: 2 intervals, the counts kept")
    print("S494D RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
