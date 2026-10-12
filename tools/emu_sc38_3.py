"""SC38.3 ARM tests (live RAM dump, the real routes): the four MIDI Thru modes (tools/midithru.py).

    python tools/emu_sc38_3.py SC38.3.bin SC38.3_manifest.json
  * Advanced Setup view (the Setup view with byte +0x24 set, active in the controller): Duplicate (button 24, 0x08033320) cycles Thru -> Out 2 -> Merge ->
    Filter -> Thru (settings parameter 2 bits 16 / 30 / 31); its LED 56 (the LED task 0x08033B3E): dim red 0x55 / green 0x74 / yellow / blue; GPIOB pin 4
    (BSRR 0x40020418): set in Thru, reset (the Out 2 wiring) in the other three (the stock listener writes it on every change of parameter 2);
  * DIN In: MIDI bytes pushed into USART1's receive ring (0x0802214A), the stock poll 0x08020FB2 (parser, post 0x0801C894): what reaches the send of port 2:
    Thru / Out 2: nothing; Merge: everything (notes on listened channels, channel 16, clock, a program change); Filter: only what is not on a listened
    channel (Synth 1 ch 1, MIDI 2 ch 4, drums ch 10, project ch 16 skipped; ch 6, clock, PC ch 7 copied); every message is still posted to the unit;
  * the unit's MIDI (the central send 0x0803BEDA, mask 7): port 2 gets it in Out 2 / Merge, not in Filter; ports 0 / 1 always;
  * the save mask (c_m1) keeps bits 30 / 31.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R4
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc08 import E8  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
import midithru as T  # noqa: E402

MGR, SETUP = 0x20040B10, 0x20044958
UART1 = 0x20005848                     # the DIN In / MIDI Out UART object (USART1)
POLL, RING_PUSH, ROUTE = 0x08020FB2, 0x0802214A, 0x08020C42
SETUP_VT = 0x0805A984                  # the Setup view: slot 4 (vt + 0x10) = buttons 0x08047016, slot 9 (+0x24) the LEDs
SETUP_LISTEN = 0x080470F4              # the Setup view's settings listener (vtable 0x0805A9B8): redraws its LEDs when the settings change
MSGS = [("note ch 1 (Synth 1)", [0x90, 60, 100]), ("note ch 6", [0x95, 62, 90]), ("CC ch 16 (project)", [0xBF, 7, 64]), ("note ch 10 (drums)", [0x99, 60, 80]),
        ("clock", [0xF8]), ("PC ch 7", [0xC6, 5]), ("CC ch 4 (MIDI 2)", [0xB3, 74, 10])]
LISTENED = {0, 1, 2, 3, 9, 15}


def setup(img, man):
    e = E8(img)
    st = e.r32(e.r32(e.r32(T.CTX_PTR)) + 0x54)
    R = e.r32(T.ROUTER_PTR); ports = [e.r32(e.r32(R + 0x14) + 4 * i) for i in range(3)]
    e.uc.mem_write(SETUP + 0x24, b""); e.w32(MGR + 0x6C, SETUP)                 # the Advanced Setup view in the controller
    return e, st, R, ports


def p2(e, st):
    e.call(T.PARAM_GET, st, 2); return e.r32(e.uc.reg_read(UC_ARM_REG_R0))


def mode(e, st):
    v = p2(e, st); return "Filter" if v >> 31 & 1 else "Merge" if v >> 30 & 1 else "Thru" if v >> 16 & 1 else "Out 2"


def press(e, btn): e.call(e.r32(SETUP_VT + 0x10) & ~1, SETUP, btn, maxins=5_000_000)   # the Setup view's button method (the controller calls it)


def hook_sends(e, ports):
    sends = []
    def hs(uc, a, s_, d):
        p = uc.reg_read(UC_ARM_REG_R0); ptr = uc.reg_read(UC_ARM_REG_R1)
        sends.append((ports.index(p) if p in ports else p, bytes(uc.mem_read(ptr, 3))))
    e.uc.hook_add(UC_HOOK_CODE, hs, begin=T.PORT_SEND, end=T.PORT_SEND)
    return sends


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    ORDER = ["Thru", "Out 2", "Merge", "Filter"]
    # ---- one instance: the cycle, the LED, the pin, the unit's MIDI
    e, st, R, ports = setup(img, man)
    sends = hook_sends(e, ports); gpio = []
    e.uc.hook_add(UC_HOOK_MEM_WRITE, lambda uc, acc, a, size, v, d: gpio.append(v), begin=0x40020418, end=0x4002041B)
    def frame():                                                                  # the Setup view's LED buffer, drawn by its settings listener (0x080470F4; in the Advanced Setup view 0x080472E4)
        e.call(SETUP_LISTEN, SETUP + 8, st, maxins=5_000_000)
        return list(struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(SETUP + 4)), 138))))
    def unit():
        sends.clear()
        e.uc.mem_write(0x2006E000, bytes([0xB2, 20, 99])); e.call(ROUTE, R, 7, 0x2006E000, maxins=5_000_000)   # the central send past its gate (closed in the dump)
        return sorted({x[0] for x in sends})
    pal = lambda off: struct.unpack("<H", bytes(e.uc.mem_read(T.PAL + off, 2)))[0]
    want_led = {"Thru": pal(0x34E), "Out 2": pal(0x34C), "Merge": T.COL_MERGE, "Filter": T.COL_FILTER}
    check(mode(e, st) == "Thru", f"the dump is in Thru ({p2(e, st):#x})")
    seen = []
    for step in range(5):
        m = mode(e, st); seen.append(m); fr = frame(); u = unit()
        check(fr[56] == want_led[m], f"{m}: Duplicate LED {fr[56]:#x} (want {want_led[m]:#x})")
        check(u == ([0, 1] if m == "Filter" else [0, 1, 2]), f"{m}: the unit's MIDI goes to ports {u}")
        gpio.clear(); press(e, 24); nxt = mode(e, st)
        ok_g = gpio == [1 << 4] if nxt == "Thru" else (gpio and all(g == 1 << 20 for g in gpio)) if m == "Thru" else all(g == 1 << 20 for g in gpio)
        check(ok_g, f"Duplicate: {m} -> {nxt}, GPIOB BSRR writes {[hex(g) for g in gpio]} (pin 4 set only for Thru; the stock listener writes it on every change)")
    check(seen == ORDER + ["Thru"], f"the cycle {seen}")
    e.call(int(man["report"]["sc06"]["labels"]["c_m1"], 16), 0, 0, 0xFFFFFFFF); mk = e.uc.reg_read(UC_ARM_REG_R1)
    check(mk == T.SAVE_MASK, f"the save mask keeps bits 30 / 31 ({mk:#x})")
    del e; gc.collect()
    # ---- the DIN In per mode (a fresh instance each: the emulated poll leaves the next settings commit blocked)
    for k, m in enumerate(ORDER):
        e, st, R, ports = setup(img, man)
        sends = hook_sends(e, ports); posts = []
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: posts.append(1), begin=T.POST, end=T.POST)
        for _ in range(k): press(e, 24)
        assert mode(e, st) == m, mode(e, st)
        for _, bb in MSGS:
            for x in bb: e.call(RING_PUSH, UART1 + 0x18, x)
        for _ in range(sum(len(bb) for _, bb in MSGS) + 2): e.call(POLL, maxins=20_000_000)    # the stock poll takes one byte per call
        mlen = lambda st_: 1 if st_ >= 0xF8 else 2 if st_ & 0xE0 == 0xC0 else 3
        got = [x[1][:mlen(x[1][0])] for x in sends if x[0] == T.PORT2]
        if m in ("Thru", "Out 2"): want = []
        elif m == "Merge": want = [bytes(bb) for _, bb in MSGS]
        else: want = [bytes(bb) for _, bb in MSGS if not (0x80 <= bb[0] < 0xF0 and (bb[0] & 15) in LISTENED)]
        check(got == want and len(posts) == len(MSGS), f"{m}: DIN In -> port 2 {[g.hex() for g in got]} (want {[w.hex() for w in want]}), all {len(posts)} posted to the unit")
        del e; gc.collect()
    print("SC38.3 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
