"""SC39.6 ARM tests (live RAM dump, the real routes: the controller's buttons and pads, the LED task from its caller, the stock content API on
emu_sc35's model of the SD card): a project copied to another slot, in the pack or in another pack (tools/sesscopy.py).

    python tools/emu_sc39_6.py SC39.6.bin SC39.6_manifest.json SC39.5.bin SC39.5_manifest.json
  * the Projects view (button 26); a plain pad: the stock's handler, nothing written;
  * Duplicate (the real button: the view accepts it now) + an empty slot: nothing; + a slot with a project: the source (it blinks yellow), the
    stock not reached, nothing written;
  * + an empty slot: the whole file (160 780 bytes in 40 pieces of 4 KB) copied byte by byte, the buffer's lock balanced, the slot steady yellow;
  * + the slot of the loaded project: nothing; + a slot with a project: a question (it blinks white, nothing written), again within ~5 s: written;
    later than that: asked again;
  * + the source again: forgotten;
  * another pack loaded: the source is still known (not shown: it is not of this pack); Duplicate + slot: the file of the other pack copied into
    this one, the storage task back on the loaded pack;
  * the previous build: Duplicate + pad = a plain pad.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R4
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc39_4 as T4  # noqa: E402
from emu_sc35 import MGR, TICK, PK, set_loaded  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
import sesscopy as SC  # noqa: E402

B = 0x08010000
SIZE = 160780
STOCK_CMD = 0x0803C68C
BTN_PROJECTS = 26


def sess(tag): return bytes((tag * 7 + i * 13 + (i >> 8)) & 0xFF for i in range(SIZE))


class E6(T4.E4):
    def setup(self, man):
        super().setup(man)
        self.cmd = []
        self.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: self.cmd.append(a), begin=STOCK_CMD, end=STOCK_CMD)
    def sst(self):
        self.call(self.gstf); return bytes(self.uc.mem_read(self.uc.reg_read(UC_ARM_REG_R0) + SC.ST_OFF, 8))
    def panel(self, phase=0):
        t = self.ms & ~0xFF | (0x80 if phase else 0); self.w32(TICK, t)
        self.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); self.uc.reg_write(UC_ARM_REG_R4, MGR)
        self.call(0x08033B3E, maxins=8_000_000); self.w32(TICK, self.ms)
        return list(struct.unpack("<69H", bytes(self.uc.mem_read(self.r32(self.r32(MGR + 0x90)), 138))))[:32]
    def swr(self): return [(c[1], c[2], c[3]) for c in self.api if c[0] == "write" and c[1][0] == SC.KIND_SESS]
    def dpad(self, p):
        self.held(2); self.api.clear(); self.cmd.clear(); self.call(T4.PRESS, MGR, p, 100, maxins=400_000_000); self.call(T4.RELEASE, MGR, p, maxins=8_000_000); self.held(0)


def run(img, man, new):
    e = E6(img, man); e.setup(man); o = {}
    CUR, X = 31, 7
    e.btn(BTN_PROJECTS); v = e.r32(MGR + 0x6C); o["view"] = e.r32(v)
    e.call(0x0803542C, e.r32(v + 0x20), 8); cur_s = e.r8(e.uc.reg_read(UC_ARM_REG_R0)); o["cur_s"] = cur_s
    S4, S7, SL = sess(4), sess(7), sess(1)
    e.sd = {(2, 4, 0xFF): S4, (2, 7, 0xFF): S7, (2, cur_s, 0xFF): SL}
    if not new:                                                                   # (the stock does not take Duplicate as a held button there)
        e.call(0x08033320, MGR, 24, maxins=900000); e.api.clear(); e.cmd.clear(); e.pad(4); e.call(0x0803381A, MGR, 24, maxins=900000)
        o["prev"] = (len(e.cmd) > 0, e.swr(), dict(e.sd) == {(2, 4, 0xFF): S4, (2, 7, 0xFF): S7, (2, cur_s, 0xFF): SL})
        del e; gc.collect(); return o
    e.dpad(9); o["empty_src"] = (e.sst()[1], len(e.cmd), e.swr())
    e.dpad(4); st = e.sst(); o["src"] = (st[1], st[2], len(e.cmd), e.swr(), e.panel(0)[4], e.panel(1)[4])
    e.dpad(6); w = e.swr(); st = e.sst()
    o["copy"] = (e.sd.get((2, 6, 0xFF)) == S4, len(w), w[0][1:] if w else None, w[-1][1:] if w else None, sum(x[2] for x in w), e.lock, st[6], st[7], st[1], e.panel(0)[6], e.panel(1)[6], len(e.cmd))
    e.dpad(cur_s); o["loaded"] = (e.swr(), e.sd[(2, cur_s, 0xFF)] == SL)
    e.dpad(7); st = e.sst(); o["ask"] = (e.swr(), st[3], e.panel(0)[7], e.panel(1)[7], e.sd[(2, 7, 0xFF)] == S7)
    e.dpad(7); o["ask2"] = (len(e.swr()), e.sd[(2, 7, 0xFF)] == S4, e.sst()[3])
    e.sd[(2, 7, 0xFF)] = S7
    e.dpad(7); e.wait(6000); e.dpad(7); a_ = e.sst()[3]; e.wait(6000); p = (e.panel(0)[7], e.panel(1)[7])
    o["late"] = (e.swr(), a_, e.sst()[3], p[0] == p[1], e.sd[(2, 7, 0xFF)] == S7)
    e.dpad(4); o["drop"] = (e.sst()[1], e.swr(), e.panel(0)[4] == e.panel(1)[4])
    e.dpad(4)                                                                     # the source again, then another pack is loaded
    e.sd = {((k[0], k[1], CUR) if k[2] == 0xFF else k): d for k, d in e.sd.items()}
    e.sd[(2, 2, 0xFF)] = sess(9)                                                  # pack X has one project
    set_loaded(e, man, X)
    st = e.sst(); f = e.panel(0); o["other"] = (st[1], st[2], f[4], f[6])
    e.dpad(12); w = e.swr()
    o["cross"] = (e.sd.get((2, 12, 0xFF)) == S4, len(w), {x[0][2] for x in w}, e.sd[(2, 4, CUR)] == S4, e.scur, e.lock, e.sst()[6:8], e.panel(0)[12])
    e.api.clear(); e.cmd.clear(); e.pad(5); o["plain"] = (len(e.cmd) > 0, e.swr())      # (last: a plain pad asks for that project, and the unit waits for it)
    del e; gc.collect()
    return o


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["sesscopy"]["labels"].items()}
    w = lambda a: struct.unpack_from("<I", img, a - B)[0]
    from thumb import bl
    check(w(SC.PROJ_VT) == L["c_scpad"] | 1 and w(SC.PROJ_VT + 32) == L["c_scmask"] | 1 and all(bytes(img[c - B:c - B + 4]) == bl(c, L["c_scledtask"]) for c in PK.LED_CALLS),
          "the hooks: slots 0 / 8 of the Projects view, the two LED task calls")
    o = run(img, man, True)
    Y, W = SC.COL_SRC, SC.COL_ASK
    check(o["view"] == SC.PROJ_VT and o["plain"] == (True, []), f"button 26 = the Projects view (the loaded project: {o['cur_s']}); a plain pad: the stock's handler, nothing written")
    check(o["empty_src"] == (0, 0, []), "Duplicate (held through the controller) + an empty slot: no source, the stock not reached")
    s1, s2, cmd, wr, on, off = o["src"]
    check(s1 == 0x84 and s2 == 31 and cmd == 0 and wr == [] and (on, off) == (Y, 0), f"Duplicate + slot 5: the source, blinking yellow ({on:#x} / {off:#x}); nothing written, the stock not reached")
    ok, n, first, last, total, lock, b6, b7, s1, on, off, cmd = o["copy"]
    check(ok and n == 40 and first == (0, 4096) and last == (39 * 4096, SIZE - 39 * 4096) and total == SIZE and lock == 0 and cmd == 0,
          f"Duplicate + an empty slot: the file copied byte by byte in {n} pieces ({total} bytes), the lock balanced")
    check(b6 == 0x86 and b7 == 31 and s1 == 0x84 and on == off == Y, "the copy steady yellow; the source stays for more copies")
    check(o["loaded"] == ([], True), "Duplicate + the slot of the loaded project: nothing")
    wr, a_, on, off, same = o["ask"]
    check(wr == [] and a_ == 0x87 and (on, off) == (W, 0) and same, "Duplicate + a slot with a project: it asks (blinks white), nothing written")
    check(o["ask2"] == (40, True, 0), "Duplicate + that slot again: written")
    wr, a1, a2, steady, same = o["late"]
    check(len(wr) == 0 and a1 == 0x87 and a2 == 0 and steady and same, "6 s later: asked again, nothing written; then the question is gone")
    check(o["drop"][0] == 0 and o["drop"][1] == [] and o["drop"][2], "Duplicate + the source again: forgotten")
    s1, s2, l4, l6 = o["other"]
    check(s1 == 0x84 and s2 == 31 and l4 != Y and l6 != Y, "another pack loaded: the source is kept; nothing of the other pack is drawn here")
    ok, n, packs, src, scur, lock, last, led = o["cross"]
    check(ok and n == 40 and packs == {7} and src and scur == 7 and lock == 0 and tuple(last) == (0x8C, 7) and led == Y,
          f"Duplicate + slot 13 there: the project of pack 31 copied into pack 7 ({n} pieces); the storage task back on the loaded pack ({scur})")
    gc.collect(); q = run(prev, prev_man, False)
    check(q["prev"] == (True, [], True), "the previous build: Duplicate + pad = a plain pad (the stock's handler), nothing written")
    print("SC39.6 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
