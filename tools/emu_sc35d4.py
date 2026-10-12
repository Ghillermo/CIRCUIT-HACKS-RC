"""SC35D4 / SC35D5 tests (SC35D5 = kind 4: python tools/emu_sc35d4.py SC35D5.bin SC35D5_manifest.json --kind 4): the read-only SD probe (tools/probe35s.py) on the RAM dump, through the real routes (the DSP service chain head, the controller's pad path
0x08033282 into the synth Preset view).  The stock content API (exists 0x0803CB50, size 0x0803CB6A, read 0x0803CBF0) and the MIDI send are stubbed.

    python tools/emu_sc35d4.py SC35D4.bin SC35D4_manifest.json
  * closed source view: the tick leaves the LEDs alone, pad 9 goes on to srcview, no API call;
  * open: pads 9-16 green, 17-24 dark (both synth views);
  * pad 9 + k: exists, size, read on the item (kind 2 = PCM, index k, pack 0xFF), read at offset 0 of NHEAD bytes, synchronous (cb = 0, ctx = 0, &done);
    the write API is never called; the dump = MAGIC, exists, size (2 words), status, bytes read, the 21 bytes, kind << 8 | index; 2 ms between words;
  * pad 17: no dump.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc19_1 as T  # noqa: E402
import emu_sc32d_1 as E1  # noqa: E402
import probe35s as PS  # noqa: E402
import build_sc14 as s14  # noqa: E402
import drums18  # noqa: E402

WRITE = 0x0803CC16
HEAD = b"RIFF" + struct.pack("<I", 187180) + b"WAVEfmt " + struct.pack("<IB", 16, 1)


class E35s(T.E191):
    def __init__(self, image, man):
        super().__init__(image, man)
        self.pl = {k: int(v, 16) for k, v in man["report"]["probe35s"]["labels"].items()}
        self.sent, self.sleeps, self.api = [], [], []
        def ret(uc, v):
            uc.reg_write(UC_ARM_REG_R0, v & 0xFFFFFFFF); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        def item(uc):
            b = bytes(uc.mem_read(uc.reg_read(UC_ARM_REG_R0), 12)); return struct.unpack("<II", b[:8]) + (b[8],)
        def exists(uc, a, s, d): self.api.append(("exists", item(uc))); ret(uc, 1)
        def size(uc, a, s, d): self.api.append(("size", item(uc))); ret(uc, 0x12345678)
        def read(uc, a, s, d):
            sp = uc.reg_read(UC_ARM_REG_SP)
            cb, ctx, done = struct.unpack("<III", bytes(uc.mem_read(sp, 12)))
            off, buf, n = uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3)
            self.api.append(("read", item(uc), off, n, cb, ctx))
            uc.mem_write(buf, HEAD[:n]); uc.mem_write(done, struct.pack("<I", n)); ret(uc, 0)
        def write(uc, a, s, d):
            sp = uc.reg_read(UC_ARM_REG_SP)
            cb, ctx = struct.unpack("<II", bytes(uc.mem_read(sp, 8)))
            off, buf, n = uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3)
            self.api.append(("WRITE", item(uc), off, bytes(uc.mem_read(buf, n)), cb, ctx)); ret(uc, 0)
        for f, ad in ((exists, PS.EXISTS), (size, PS.SIZE), (read, PS.READ), (write, WRITE)):
            self.uc.hook_add(UC_HOOK_CODE, f, begin=ad, end=ad)
        def snd(uc, a, s, d):
            self.sent.append((uc.reg_read(UC_ARM_REG_R0), tuple(uc.mem_read(uc.reg_read(UC_ARM_REG_R1), 3))))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        self.uc.hook_add(UC_HOOK_CODE, snd, begin=PS.SEND, end=PS.SEND)
        def slp(uc, a, s, d):
            self.sleeps.append(uc.reg_read(UC_ARM_REG_R0)); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        self.uc.hook_add(UC_HOOK_CODE, slp, begin=PS.SLEEP, end=PS.SLEEP)

    def tick(self):
        self.chain.clear(); self.dw.clear()
        self.call(self.pl["c_dtick35"], maxins=3_000_000)

    def buf(self, v): return self.r32(self.r32(v + 4))
    def row(self, v, first, n): return list(struct.unpack(f"<{n}H", bytes(self.uc.mem_read(self.buf(v) + 2 * first, 2 * n))))


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["probe35s"]["labels"].items()}
    check(drums18.decode_bw(bytearray(img), s14.SVC_HOOK) == L["c_dtick35"], "DSP service chain head -> c_dtick35")
    check(struct.unpack_from("<I", img, PS.SP_VT - 0x08010000)[0] == L["c_spad"] | 1, "slot 0 of the synth Preset view -> c_spad")
    gc.collect(); e = E35s(img, man)
    snap = [e.row(v, 0, 32) for v in PS.VIEWS]
    e.tick()
    check([e.row(v, 0, 32) for v in PS.VIEWS] == snap and len(e.chain) == 1, "source view closed: LEDs untouched, the chain goes on")
    e.sent.clear(); e.padr(8)
    ours = lambda: [m for k, m in e.sent if k == 7 and m[0] == PS.STATUS]
    check(not e.flag() and ours() == [] and e.api == [], "closed view: pad 9 sends nothing, no API call")
    e.btn(0)
    check(e.flag(), "source view open")
    e.tick()
    red = PS.WB_RED if PS.WB_PADS else 0
    check(all(e.row(v, 8, 16) == [PS.GREEN] * 8 + [red] * 8 for v in PS.VIEWS), f"pads 9-16 green, 17-24 {'red' if PS.WB_PADS else 'dark'} {[hex(x) for x in e.row(PS.VIEWS[0], 8, 9)]}")
    for k in (0, 5):
        e.sent.clear(); e.sleeps.clear(); e.api.clear()
        e.padr(8 + k)
        it = (PS.KIND, k, PS.PACK_CUR)
        check(e.api == [("exists", it), ("size", it), ("read", it, 0, PS.NHEAD, 0, 0)], f"pad {9 + k}: exists, size, read (offset 0, {PS.NHEAD} B, sync) on {it}; never write")
        msgs = [m for _, m in e.sent]
        w = E1.decode(msgs)
        hb = HEAD[:PS.NHEAD]
        want = [PS.MAGIC, 1, 0x345678, 0x12, 0, PS.NHEAD] + [hb[3 * j] << 16 | hb[3 * j + 1] << 8 | hb[3 * j + 2] for j in range(7)] + [PS.KIND << 8 | k]
        check(w == want, f"pad {9 + k}: the dump {[hex(x) for x in (w or [])]}")
        check(all(t == 7 for t, _ in e.sent) and e.sleeps == [2] * PS.NWORDS, f"{len(msgs)} messages through the stock send, 2 ms between words")
    if PS.WRITEBACK:                                                            # SC35D6: Shift + pad = write the same bytes back, then size and read again
        for k in (0, 7):
            e.sent.clear(); e.sleeps.clear(); e.api.clear()
            e.padr(16 + k) if PS.WB_PADS else e.padr(8 + k, shift=True)
            it = (PS.KIND, k, PS.PACK_CUR)
            hb = HEAD[:PS.NHEAD]
            check(e.api == [("exists", it), ("size", it), ("read", it, 0, PS.NHEAD, 0, 0), ("WRITE", it, 0, hb, 0, 0), ("size", it), ("read", it, 0, PS.NHEAD, 0, 0)],
                  f"{'pad ' + str(17 + k) if PS.WB_PADS else 'Shift + pad ' + str(9 + k)}: exists, size, read, WRITE of the same {PS.NHEAD} bytes at offset 0 (sync), size, read again")
            w = E1.decode([m for _, m in e.sent])
            want = [PS.MAGIC_WB, 1, 0x345678, 0, 0x345678, PS.NHEAD] + [hb[3 * j] << 16 | hb[3 * j + 1] << 8 | hb[3 * j + 2] for j in range(7)] + [PS.KIND << 8 | 0x80 | k]
            check(w == want, f"write-back {k}: the dump {[hex(x) for x in (w or [])]}")
        e.api.clear(); e.padr(8)
        check([c[0] for c in e.api] == ["exists", "size", "read"], "pad 9 without Shift: read only")
        if PS.WB_PADS:
            e.api.clear(); e.padr(8, shift=True)
            check([c[0] for c in e.api] == ["exists", "size", "read"], "WB_PADS: Shift + pad 9 reads only")
    else:
        e.api.clear(); e.padr(8, shift=True)
        check("WRITE" not in [c[0] for c in e.api], "no write even with Shift")
    last = 24 if PS.WB_PADS else 16
    e.sent.clear(); e.api.clear(); e.padr(last)
    check(ours() == [] and e.api == [], f"pad {last + 1}: no dump, no API call")
    print(f"SC35D4 (kind {PS.KIND}{', writeback' if PS.WRITEBACK else ''}) RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    if "--kind" in a:
        PS.KIND = int(a[a.index("--kind") + 1])
    if "--writeback" in a:
        PS.WRITEBACK = True
    if "--wbpads" in a:
        PS.WRITEBACK = PS.WB_PADS = True
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
