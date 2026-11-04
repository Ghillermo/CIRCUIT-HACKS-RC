"""SC51.1 ARM tests (loopcarry.py): the captured sample's latched loop through a project load, then Play at the end of its loop.

    python tools/emu_loopcarry.py SC51.1.bin SC51.1_manifest.json
On the live RAM dump, the loop latched through the real route (Master FX, Shift + pad 7, the Master FX tick); a DSP model answers the reads of
0x08029344 with what was written (X:PLAY = 2 = the DSP's forced loop).  The load = c_lcload (the head of the apply-session end) + the project's
knob bytes written as c_xm_load does + c_lcclr (c_rs's call, checked in the image); the DSP service tick = c_lctick; the LED task = the real call.
  * a latched loop at a load: no stop command, loop + gate kept, the old knob bytes kept (the new ones aside), DIRTY;
  * Play stopped: kept (the transport does not start), Play blinks; the tick writes MODE 0 / PLAY 1; while X:PLAY = 1 it waits; X:PLAY = 0: LEN 0
    (discarded), loop + gate off, the new knobs, DIRTY; the LED task presses Play: the transport runs;
  * Play twice: stop now (command 3), then Play;  pad 7 while carried: the carry ends, discarded, no Play;
  * no loop at the load, or the DSP not looping: c_clrall's stop as before; Play starts at once.
SC51.3 / Beta 5.16 (loopcarry.use_keep, label lt_fw): Play reads X:PI / SS / EE and writes nothing; it waits while the loop is far from its end, GO
when the end comes before the next tick's step (forward) or when the position wraps (reverse); the loop, its gate and its old knobs stay, LEN is
never written; Play twice = Play at once without the stop; pad 7 = the carry ends, nothing discarded.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R4
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc36 as T36  # noqa: E402  (configures build_sc17 as SC36)
import build_sc17 as B  # noqa: E402
import sampler_dsp as SD  # noqa: E402
import loopcarry as LC  # noqa: E402
from thumb import bl as bl_enc  # noqa: E402

MGR = LC.MGR
OLD, NEW = bytes([0x11, 0x22, 0x33, 0x44]), bytes([0x05, 0x40, 0x10, 0x20])


class EL(T36.T34.E7):
    def __init__(self, img, man):
        super().__init__(img, man)
        rep = man["report"]
        self.LC = {k: int(v, 16) for k, v in rep["loopcarry"]["labels"].items()}
        self.prev = {k: int(v, 16) for k, v in rep["loopcarry"]["prev"].items()}
        self.dsp = {}
        def rd(uc, a, s, d):
            uc.reg_write(UC_ARM_REG_R0, (self.dsp.get(uc.reg_read(UC_ARM_REG_R1), 0) << 8) & 0xFFFFFFFF)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        self.uc.hook_add(UC_HOOK_CODE, rd, begin=LC.DSP_READ, end=LC.DSP_READ)
        def skip(uc, a, s, d): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        for fa in (0x0801BE78, 0x08029A00): self.uc.hook_add(UC_HOOK_CODE, skip, begin=fa, end=fa)
        for k in ("load", "svc"):                                       # the rest of those chains: a bx lr here
            self.uc.mem_write(self.prev[k] & ~1, b"\x70\x47")
        self.ms = 30000

    def sync(self):
        for a, v in self.dw: self.dsp[a] = v
    def jf(self): return self.blkb(B.S_JF)[0]
    def knobs(self): return self.blkb(LC.KB, 4)
    def st(self): return self.r8(LC.RAM + LC.O_ST)
    def r8(self, a): return self.uc.mem_read(a, 1)[0]
    def press(self, b):
        self.call(0x08033320, MGR, b, maxins=8_000_000); self.call(0x0803381A, MGR, b, maxins=8_000_000)
    def playing(self):
        self.call(LC.PARAM_WPTR, LC.TRANSPORT, 0, maxins=200000); return self.r8(self.uc.reg_read(UC_ARM_REG_R0))
    def ftick(self):
        self.ms += 10; self.w32(LC.HAL_TICK, self.ms); self.dw.clear(); self.call(self.L["c_fxtick"], maxins=2_000_000); self.sync()
    def lctick(self):
        self.ms += 10; self.w32(LC.HAL_TICK, self.ms); self.dw.clear(); self.call(self.LC["c_lctick"], maxins=2_000_000); self.sync()
        return dict(self.dw)
    def frame(self):
        from emu_sc05 import STOP
        self.ms += 10; self.w32(LC.HAL_TICK, self.ms)
        self.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); self.uc.reg_write(UC_ARM_REG_R4, MGR)
        self.call(0x08033B3E, maxins=8_000_000)
        return struct.unpack("<69H", bytes(self.uc.mem_read(self.r32(self.r32(MGR + 0x90)), 138)))
    def gact(self):
        self.call(self.L["c_gact"], maxins=200000); return self.uc.reg_read(UC_ARM_REG_R0)
    def mfx(self):
        if not self.gact(): self.grid()
    def stop(self):
        if self.playing(): self.press(LC.ID_PLAY)
    def latch(self):
        self.stop(); self.mfx(); self.pad(B.SMP_PAD, shift=True); self.rel(B.SMP_PAD); self.ftick()
        self.dsp[SD.PLAY] = 2
    def load(self):
        self.uc.mem_write(self.blk + LC.KB, OLD)
        self.call(self.LC["c_lcload"], maxins=200000)
        self.uc.mem_write(self.blk + LC.KB, NEW)                     # c_xm_load: the new project's slots
        self.dw.clear(); self.call(self.LC["c_lcclr"], self.blk, maxins=2_000_000); self.sync()


def bits(v): return (bool(v & B.SMB_LOOP), bool(v & B.SMB_GATE), (v >> 4) & 3, bool(v & B.SMB_DIRTY))


def run(img, man):
    out = {}
    x = EL(img, man); x.uc.mem_write(x.blk + B.S_JF, b"\0\0"); x.w32(x.blk + B.S_SMT, 0); x.setsp()
    rs, rx = int(man["report"]["persist19"]["labels"]["c_rs"], 16), int(man["report"]["persist19"]["labels"]["rs_x"], 16)
    site = [a for a in range(rs, rx, 2) if bytes(x.uc.mem_read(a, 4)) == bl_enc(a, x.LC["c_lcclr"])]
    out["site"] = len(site)
    if "lt_fw" in x.LC:
        return run_keep(x, out)
    # 1. a latched loop through a load, Play at its end
    x.latch(); out["latched"] = bits(x.jf())
    x.load(); out["carry"] = (x.st(), bits(x.jf()), x.knobs() == OLD, bytes(x.uc.mem_read(LC.RAM + LC.O_NEW, 4)) == NEW)
    x.press(LC.ID_PLAY); out["held"] = (x.st(), x.playing())
    leds = [x.frame()[LC.LED_PLAY] for _ in range(60)]; out["blink"] = (min(leds), max(leds))
    w = x.lctick(); out["ask"] = (x.st(), w.get(SD.MODE), w.get(SD.PLAY))
    x.dsp[SD.PLAY] = 1; x.lctick(); x.lctick(); out["wait"] = x.st()
    x.dsp[SD.PLAY] = 0; w = x.lctick(); out["end"] = (x.st(), w.get(SD.LEN), bits(x.jf()), x.knobs() == NEW)
    x.frame(); out["play"] = (x.st(), x.playing())
    x.stop(); out['stopped'] = x.playing()
    # 2. Play twice = stop now
    x.uc.mem_write(x.blk + B.S_JF, b"\0"); x.latch(); x.load(); x.press(LC.ID_PLAY); x.lctick(); x.press(LC.ID_PLAY); out["now_st"] = x.st()
    w = x.lctick(); out["now"] = (x.st(), w.get(SD.LEN), bits(x.jf()))
    x.frame(); out["now_play"] = x.playing()
    x.stop()
    # 3. pad 7 while carried
    x.uc.mem_write(x.blk + B.S_JF, b"\0"); x.latch(); x.load(); x.mfx(); x.pad(B.SMP_PAD); x.rel(B.SMP_PAD)
    w = x.lctick(); out["pad7"] = (x.st(), w.get(SD.LEN), x.knobs() == NEW); x.frame(); out["pad7_play"] = x.playing()
    # 4. no loop at the load / the DSP not looping
    x.uc.mem_write(x.blk + B.S_JF, b"\0"); x.ftick(); x.load(); out["noloop"] = (x.st(), bits(x.jf()))
    x.press(LC.ID_PLAY); out["noloop_play"] = x.playing(); x.press(LC.ID_PLAY)
    x.uc.mem_write(x.blk + B.S_JF, b"\0"); x.latch(); x.dsp[SD.PLAY] = 0; x.load(); out["nodsp"] = (x.st(), bits(x.jf()))
    del x; gc.collect()
    print(out)
    return out


def run_keep(x, out):
    X0 = SD.HIGH_BASE
    def pos(pi, ss=None, ee=None):
        x.dsp[SD.PI] = X0 + pi
        if ss is not None: x.dsp[SD.SS], x.dsp[SD.EE] = X0 + ss, X0 + ee
    # 1. forward: far, then the end before the next step
    x.latch(); out["latched"] = bits(x.jf())
    x.load(); out["carry"] = (x.st(), bits(x.jf()), x.knobs() == OLD)
    x.press(LC.ID_PLAY); out["held"] = (x.st(), x.playing())
    leds = [x.frame()[LC.LED_PLAY] for _ in range(60)]; out["blink"] = (min(leds), max(leds))
    pos(1000, 0, 5000); w = x.lctick(); out["ask"] = (x.st(), sorted(w))
    pos(1480); w1 = x.lctick(); pos(1960); w2 = x.lctick(); out["far"] = (x.st(), sorted(w1) + sorted(w2))
    pos(4600); w = x.lctick(); out["near"] = (x.st(), sorted(w), bits(x.jf()), x.knobs() == OLD)
    x.frame(); out["play"] = (x.st(), x.playing(), bits(x.jf())[:2], x.knobs() == OLD)
    x.lctick(); out["after"] = (x.st(), bits(x.jf())[:2])
    x.stop()
    # 2. reverse: a wrap
    x.uc.mem_write(x.blk + B.S_JF, b"\0"); x.latch(); x.load(); x.press(LC.ID_PLAY)
    pos(4000, 5000, 0); x.lctick(); pos(3500); x.lctick(); out["rv_far"] = x.st()
    pos(4900); x.lctick(); out["rv_wrap"] = x.st(); x.frame(); out["rv_play"] = (x.playing(), bits(x.jf())[:2])
    x.stop()
    # 3. Play twice = at once, no stop
    x.uc.mem_write(x.blk + B.S_JF, b"\0"); x.latch(); x.load(); x.press(LC.ID_PLAY); pos(1000, 0, 5000); x.lctick(); x.press(LC.ID_PLAY)
    w = x.lctick(); out["now"] = (x.st(), sorted(w), bits(x.jf()))
    x.frame(); out["now_play"] = x.playing()
    x.stop()
    # 4. pad 7 while carried: the carry ends, nothing discarded
    x.uc.mem_write(x.blk + B.S_JF, b"\0"); x.latch(); x.load(); x.mfx(); x.pad(B.SMP_PAD); x.rel(B.SMP_PAD)
    w = x.lctick(); out["pad7"] = (x.st(), SD.LEN in w, x.knobs() == OLD); x.frame(); out["pad7_play"] = x.playing()
    # 5. no loop / the DSP not looping
    x.uc.mem_write(x.blk + B.S_JF, b"\0"); x.ftick(); x.load(); out["noloop"] = (x.st(), bits(x.jf()))
    x.press(LC.ID_PLAY); out["noloop_play"] = x.playing(); x.press(LC.ID_PLAY)
    x.uc.mem_write(x.blk + B.S_JF, b"\0"); x.latch(); x.dsp[SD.PLAY] = 0; x.load(); out["nodsp"] = (x.st(), bits(x.jf()))
    del x; gc.collect()
    print(out)
    return out


def main_keep(o, check):
    check(o["site"] == 1, f"c_rs calls c_lcclr ({o['site']} site)")
    check(o["latched"][:2] == (True, True), f"Shift + pad 7: latched loop {o['latched']}")
    check(o["carry"][0] == LC.ST_CARRY and o["carry"][1] == (True, True, 0, True) and o["carry"][2], f"a load: carried, loop + gate kept, old knobs {o['carry']}")
    check(o["held"] == (LC.ST_ASK, 0) and o["blink"] == (0, LC.COL_PLAY), f"Play: kept, transport stopped, Play blinks {o['held']} {o['blink']}")
    check(o["ask"] == (LC.ST_WAIT, []), f"the tick: reads only, nothing written {o['ask']}")
    check(o["far"] == (LC.ST_WAIT, []), f"far from the end: still waiting, nothing written {o['far']}")
    st, w, jb, ko = o["near"]
    check(st == LC.ST_GO and w == [] and jb[:3] == (True, True, 0) and ko, f"the end before the next step: GO, nothing written, loop + gate + old knobs kept {o['near']}")
    check(o["play"] == (LC.ST_NONE, 1, (True, True), True), f"the LED task presses Play: the transport runs, the loop goes on {o['play']}")
    check(o["after"] == (LC.ST_NONE, (True, True)), f"after: a plain latched loop {o['after']}")
    check(o["rv_far"] == LC.ST_WAIT and o["rv_wrap"] == LC.ST_GO and o["rv_play"] == (1, (True, True)), f"reverse: waits, the wrap = GO, Play, loop on {o['rv_far']} {o['rv_wrap']} {o['rv_play']}")
    check(o["now"][0] == LC.ST_GO and o["now"][1] == [] and o["now"][2][:3] == (True, True, 0) and o["now_play"] == 1, f"Play twice: at once, no stop {o['now']} {o['now_play']}")
    check(o["pad7"] == (LC.ST_NONE, False, True) and o["pad7_play"] == 0, f"pad 7 while carried: the carry ends, nothing discarded, no Play {o['pad7']} {o['pad7_play']}")
    check(o["noloop"][0] == LC.ST_NONE and o["noloop"][1][2] == 3 and o["noloop_play"] == 1, f"no loop: stop as before, Play at once {o['noloop']} {o['noloop_play']}")
    check(o["nodsp"][0] == LC.ST_NONE and o["nodsp"][1][:3] == (False, False, 3), f"the DSP not looping: stopped as before {o['nodsp']}")


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    o = run(img, man)
    if "rv_wrap" in o:
        main_keep(o, check)
        print("LOOPCARRY ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
        return fails
    check(o["site"] == 1, f"c_rs calls c_lcclr ({o['site']} site)")
    check(o["latched"][:2] == (True, True), f"Shift + pad 7: latched loop {o['latched']}")
    st, jb, kold, knew = o["carry"]
    check(st == LC.ST_CARRY and jb == (True, True, 0, True) and kold and knew,
          f"a load: carried (state {st}), loop + gate kept, no stop, DIRTY {jb}; old knobs kept {kold}, new ones aside {knew}")
    check(o["held"] == (LC.ST_ASK, 0), f"Play: kept, the transport stopped {o['held']}")
    check(o["blink"] == (0, LC.COL_PLAY), f"Play blinks green while it waits {o['blink']}")
    check(o["ask"] == (LC.ST_WAIT, 0, 1), f"the tick: MODE 0, PLAY 1 (to its end) {o['ask']}")
    check(o["wait"] == LC.ST_WAIT, f"X:PLAY 1: still waiting ({o['wait']})")
    st, ln, jb, kn = o["end"]
    check(st == LC.ST_GO and ln == 0 and jb[:2] == (False, False) and jb[3] and kn,
          f"X:PLAY 0: LEN 0 (discarded) {ln}, loop + gate off, DIRTY {jb}, the new knobs {kn} (state {st})")
    check(o["play"] == (LC.ST_NONE, 1), f"the LED task presses Play: the transport runs {o['play']}")
    check(o["now_st"] == LC.ST_NOW and o["now"][0] == LC.ST_GO and o["now"][1] == 0 and o["now"][2][2] == 3 and o["now_play"] == 1,
          f"Play twice: stop now (command {o['now'][2][2]}), discarded, then Play {o['now']} {o['now_play']}")
    check(o["pad7"] == (LC.ST_NONE, 0, True) and o["pad7_play"] == 0, f"pad 7 while carried: the carry ends, discarded, the new knobs, no Play {o['pad7']} {o['pad7_play']}")
    check(o["noloop"][0] == LC.ST_NONE and o["noloop"][1][2] == 3 and o["noloop_play"] == 1,
          f"no loop: c_clrall's stop as before {o['noloop']}, Play starts at once ({o['noloop_play']})")
    check(o["nodsp"][0] == LC.ST_NONE and o["nodsp"][1][:3] == (False, False, 3), f"the DSP not looping: stopped as before {o['nodsp']}")
    print("LOOPCARRY ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
