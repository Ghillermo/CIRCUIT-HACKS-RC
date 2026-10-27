"""SC47.9 (tools/stpair.py): stereo drum pairs, on the emulated firmware through the real routes.

  * the gesture (the controller 0x08033320 / 0x0803381A): Drum 1 held + Drum 2 = pair 1+2 on, again = off; Drum 2 held + Drum 1 too; Drum 2 + Drum 3
    is no pair; with Shift nothing; a lone Drum 2 press still selects Drum 2;
  * a drum 1 hit (0x0803BD58(0x10, 60, vel), the stock's route): unpaired only X:$9F; paired also the slave: X:$A0 = the same velocity, its sample
    word X:$AD = the master's sample + 1, its pitch word X:$AE = the master's word (no detune); a drum 2 hit (its pads / notes) alone;
  * the slave's sequencer (word 0 of the drum players' vtable): returns for a paired slave, ticks otherwise;
  * a service flush after the toggle: the slave's words mirrored, the pans hard left / right (Y:$101 / $102), the width (Drum 2's K2 through the knob
    route) to 0 = both centred; K1 = the detune (the slave's pitch word moves, the master's not); the knob sends nothing else (no recorder gate);
  * the mod's codes (persist19's tick): a master's code also goes to the slave's mailbox (X:$3A80 / $3AC0) with the slave's deviation;
  * the LED task: the slave's SC16 bytes = the master's; a pick of drum 2's sample = k (its distance); Drum 2's LED pulses;
  * save / load: the block in MIDI 1's pattern 5 (0xC8, on, k, W), the pair back after the load's re-send hook; a project without it: off;
  * off: the slave's own words back; unpaired hits as in PREV (if given).

    python tools/emu_stpair.py BUILD.bin manifest.json [PREV.bin PREV_manifest.json]
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import E35, MGR  # noqa: E402
import stpair as SP  # noqa: E402

GETTER, PARAM_GET, SEND = 0x08036192, 0x0803542C, 0x0803BD58
SERVICE_FLUSH = 0x080214F4
HAL = 0x2000081C
FRAME = 0x2006E000


class EP:
    def __init__(self, img, man):
        gc.collect()
        self.e = e = E35(bytearray(Path(img).read_bytes()), man)
        self.L = {k: int(v, 16) for k, v in man["report"].get("stpair", {}).get("labels", {}).items()}
        self.P = {k: int(v, 16) for k, v in man["report"].get("persist19", {}).get("labels", {}).items()}
        self.ticks = 0
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: setattr(self, "ticks", self.ticks + 1), begin=SP.PLAYER_TICK, end=SP.PLAYER_TICK)
        self.gates = 0
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: setattr(self, "gates", self.gates + 1), begin=0x0802E62C, end=0x0802E62C)
        e.w32(HAL, 100000)
    def press(self, i): self.e.call(0x08033320, MGR, i, maxins=8_000_000)
    def release(self, i): self.e.call(0x0803381A, MGR, i, maxins=8_000_000)
    def knob(self, k, d): self.e.call(0x08033848, MGR, k, d & 0xFFFFFFFF, maxins=8_000_000)
    def hit(self, note, vel=100): self.e.call(SEND, 0x10, note, vel, maxins=8_000_000)
    def flush(self): self.e.call(SERVICE_FLUSH, maxins=20_000_000)
    def leds(self):                                       # the real LED task call (0x08033B46) from its caller: the panel's frame
        from emu_sc05 import STOP
        from unicorn.arm_const import UC_ARM_REG_R4
        self.e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); self.e.uc.reg_write(UC_ARM_REG_R4, MGR)
        self.e.call(0x08033B3E, maxins=20_000_000)
        return self.e.r32(self.e.r32(MGR + 0x90))
    def r0(self, fn, *a): self.e.call(fn, *a, maxins=8_000_000); return self.e.uc.reg_read(__import__("unicorn").arm_const.UC_ARM_REG_R0)
    def get(self, t, i): return self.r0(GETTER, t, i)
    def st(self): return bytes(self.e.uc.mem_read(SP.STR, SP.NSTR))
    def pairs(self): return self.st()[SP.O_PAIR] if self.e.r32(SP.STR) == SP.SIG else 0
    def pb(self, p): return self.st()[SP.PB + SP.PSZ * p:SP.PB + SP.PSZ * (p + 1)]
    def sel_ptr(self, player): return self.r0(PARAM_GET, self.e.r32(player + 0x5C), 0)
    def toggle(self, a=4, b=5):
        self.press(a); self.press(b); self.release(b); self.release(a)


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    t = EP(img, man); e = t.e; x = e.x
    # ---- unpaired
    x.clear(); t.hit(60)
    check(0x9F in x and 0xA0 not in x, f"unpaired: a drum 1 hit fires drum 1 only ({sorted(hex(k) for k in x if 0x99 <= k <= 0xB8)})")
    base = dict(x)
    # ---- the gesture
    t.toggle()
    check(t.pairs() == 1 and t.st()[SP.O_HELD] == 0, f"Drum 1 held + Drum 2: pair 1+2 on ({t.pairs()}, held {t.st()[SP.O_HELD]})")
    m_smp = t.get(0x10, 0)
    x.clear(); t.hit(60, 90)
    check(x.get(0xA0) == x.get(0x9F) == 90 << 15, f"paired: drum 1's hit fires drum 2 too, the same velocity ({x.get(0x9F)}, {x.get(0xA0)})")
    check(x.get(0xAD) == (m_smp + 1) & 63, f"drum 2's sample word = drum 1's sample + 1 ({x.get(0xAD)}, drum 1 {m_smp})")
    want = t.r0(t.L["c_stpw"], 0)
    check(x.get(0xAE) == want >> 8, f"drum 2's pitch word = drum 1's ({x.get(0xAE)}, {want >> 8})")
    x.clear(); t.hit(62, 70)
    check(x.get(0xA0) == 70 << 15 and 0x9F not in x, "a drum 2 hit (its pads, its notes) sounds alone")
    # ---- the slave's sequencer
    t.ticks = 0; e.call(t.L["c_pstick"], SP.PLAYERS[1], 0, maxins=2_000_000); s_t = t.ticks
    t.ticks = 0; e.call(t.L["c_pstick"], SP.PLAYERS[0], 0, maxins=8_000_000); m_t = t.ticks
    check(s_t == 0 and m_t == 1, f"the slave's sequencer is silent, the master's ticks ({s_t}, {m_t})")
    # ---- the flush: mirrored words, the pans; nothing takes the DSP service's semaphore in there (the tick holds it)
    e.ev.clear(); t.flush(); sem = sum(1 for v in e.ev if v[0] == "dsp")
    check(sem == 0, f"the paired flush takes no semaphore ({sem})")
    yl, yr = e.y.get(0x101), e.y.get(0x102)
    check(yl is not None and yr is not None and yl < 0x100000 and yr > 0x700000, f"the pans after the flush: drum 1 left, drum 2 right ({yl and hex(yl)}, {yr and hex(yr)})")
    # ---- drum 2's knobs: K2 = the width, K1 = the detune
    t.press(5); t.release(5)
    t.gates = 0
    for _ in range(127): t.knob(1, -1)
    w = t.pb(0)[SP.P_W]; t.flush(); yl, yr = e.y.get(0x101), e.y.get(0x102)
    check(w == 0 and yl == yr, f"drum 2's K2 to the left: width 0, both pans centred ({w}, {yl and hex(yl)}, {yr and hex(yr)})")
    w0 = t.r0(t.L["c_stpw"], 0)
    for _ in range(20): t.knob(0, 1)
    dv = struct.unpack("b", t.pb(0)[SP.P_DEV:SP.P_DEV + 1])[0]; w1 = t.r0(t.L["c_stpw"], 0)
    check(dv == 20 and w1 > w0, f"drum 2's K1: the detune up ({dv}, {hex(w0)} -> {hex(w1)})")
    check(t.gates == 0, f"drum 2's knobs record nothing ({t.gates} gate calls)")
    # ---- the mod's codes: a master's LFO amount (code 3) reaches the slave's mailbox too
    mh0 = t.r0(int(man["report"]["sc18"]["labels"]["c_mh"], 16), 0)
    mh1 = t.r0(int(man["report"]["sc18"]["labels"]["c_mh"], 16), 1)
    if mh0 and mh1:
        for mh in (mh0, mh1):                              # no other code pending: only the one below
            e.uc.mem_write(mh + 0x3E, bytes([e.r8(mh + 0x3E) & 0x80])); e.uc.mem_write(mh + 0x3F, bytes([e.r8(mh + 0x3F) & ~7 & 0xFF]))
        e.uc.mem_write(mh0 + 0x3E, bytes([e.r8(mh0 + 0x3E) | 0x04]))
        x.clear(); e.call(t.P["c_dtick19"], maxins=20_000_000)
        cm, cs = (x.get(0x3A80, 0) >> 16) & 0x7F, (x.get(0x3AC0, 0) >> 16) & 0x7F
        check(cm == 3 and cs == 3, f"a master's code (LFO amount) goes to both mailboxes (codes {cm}, {cs})")
    else:
        check(False, "no drum 1 macro handler in the RAM dump")
    # ---- the LED task: SC16 bytes, the pick detector, the LED
    fr = t.leds()
    sc = t.r0(int(man["report"]["sc16"]["labels"]["c_scst"], 16))
    b = bytes(e.uc.mem_read(sc, 12))
    check(b[5] == b[4] and b[9] == b[8], f"the slave's side-chain bytes = the master's ({b[4]}, {b[5]} / {b[8]}, {b[9]})")
    led = struct.unpack_from("<H", bytes(e.uc.mem_read(fr + 2 * SP.LED0, 2)))[0] & 0xFF
    check(led in (SP.LED_PULSE, SP.LED_BLINK), f"Drum 2's LED pulses / blinks in drum 1's colour ({hex(led)})")
    sp = t.sel_ptr(SP.PLAYERS[1]); mp = t.sel_ptr(SP.PLAYERS[0])
    msel = e.r8(mp); e.uc.mem_write(sp, bytes([(msel + 5) & 63])); t.leds()
    check(t.pb(0)[SP.P_K] == 5, f"a pick of drum 2's sample = the distance k ({t.pb(0)[SP.P_K]})")
    # ---- save / load
    e.call(t.L["c_stsave"], maxins=20_000_000)
    rec = e.r32(SP.SESSION_OBJ + 0x14)
    blk = bytes(e.uc.mem_read(rec + SP.AREA + SP.PSIZE * SP.PAT0 + SP.SET + SP.BYTE0, 32)) if rec else b""
    check(len(blk) == 32 and blk[0] == SP.BSIG and blk[2] == 1 and blk[3] == 5 and blk[4] == 0,
          f"saved: the block in MIDI 1's pattern 5 ({blk[:6].hex() if blk else None})")
    e.uc.mem_write(SP.STR + SP.O_PAIR, b"\0")
    e.call(t.L["c_stload"], maxins=60_000_000)
    check(t.pairs() == 1 and t.pb(0)[SP.P_K] == 5, f"loaded: the pair back with its distance ({t.pairs()}, {t.pb(0)[SP.P_K]})")
    if rec: e.uc.mem_write(rec + SP.AREA + SP.PSIZE * SP.PAT0 + SP.SET + SP.BYTE0, b"\0")
    e.call(t.L["c_stload"], maxins=60_000_000)
    check(t.pairs() == 0, f"a project without the block: the pair off ({t.pairs()})")
    # ---- the gesture again, other cases
    t.toggle(); t.toggle(5, 4)
    check(t.pairs() == 0, f"Drum 1 + Drum 2 then Drum 2 held + Drum 1: on, then off ({t.pairs()})")
    t.toggle(5, 6); check(t.pairs() == 0, "Drum 2 + Drum 3: no pair")
    t.toggle(6, 7); check(t.pairs() == 2, f"Drum 3 + Drum 4: pair 3+4 ({t.pairs()})"); t.toggle(6, 7)
    t.flush(); x.clear(); t.hit(60, 100)
    same = {k: v for k, v in x.items() if 0x99 <= k <= 0xB8} == {k: v for k, v in base.items() if 0x99 <= k <= 0xB8}
    check(same and t.pairs() == 0, "off: a drum 1 hit as before the pair")
    del t; gc.collect()
    if prev:
        q = EP(prev, pman); q.e.x.clear(); q.hit(60)
        pb_ = {k: v for k, v in q.e.x.items() if 0x99 <= k <= 0xB8}
        check(pb_ == {k: v for k, v in base.items() if 0x99 <= k <= 0xB8}, "unpaired hits as in PREV")
        del q; gc.collect()
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text()), a[2] if len(a) > 2 else None,
                       json.loads(Path(a[3]).read_text()) if len(a) > 3 else None) else 0)
