"""On-device test of the global macro view's rows (Alpha 7.17) on a Circuit Tracks running S717D (tools/build_s717d.py: sxpanel's panel gestures
and the black box's memory reads over USB).  Nothing is saved: the levels and sends it moves are put back, the links taken off.

  1. Patterns held + Mixer = the view on (the Mixer's page set to the pans first, to check it is kept);
  2. K3 picked, pads 9 / 18 / 28 = Synth 1's level, Synth 2's reverb send, MIDI 2's delay send linked to it (the masks read back);
  3. K3 +5: the three values +5 (the stores read back), the Mixer still on its pans page; K3 -5: back;
  4. the links off, Mixer alone = the view off; the black box empty.

    python tools/gmview_dev.py
"""
from __future__ import annotations
import struct, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctremote as CR
import bbread as BR
import gmview as G
from panelstress_dev import Panel

G.use_rows()
MIX, PAT, OCT_DN, OCT_UP = 14, 13, 19, 20


def main():
    L = CR.Link("Circuit Tracks")
    log = (Path.home() / "Documents" / time.strftime("gmview_dev_%Y-%m-%d_%H%M%S.log")).open("w", encoding="utf-8")
    P = Panel(L, log)
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    mem = lambda a, n: BR.read(L, a, n)[:n]
    u32 = lambda a: struct.unpack("<I", mem(a, 4))[0]
    u8 = lambda a: mem(a, 1)[0]
    def sval(store, k):                                   # 0x0803542C(store, k) -> its byte
        m = u32(store + 4)
        return u8(u32(store + 0xC + 4 * ((m >> k) & 1)) + 4 * k)
    lvl = lambda t: sval(u32(G.MIXV + 0x6C), t)
    rev = lambda t: sval(u32(u32(G.FXV + 0x10) + 0x14), t)
    dly = lambda t: sval(u32(u32(G.FXV + 0xC) + 0x14), t)
    gm = lambda: mem(G.GM, 52)
    try:
        P.tap(MIX); time.sleep(0.2); P.tap(OCT_DN); time.sleep(0.2)                    # the Mixer on its pans page
        page0 = u8(G.MIXV + G.MIX_PAGE)
        check(page0 == 1, f"the Mixer on its pans page before the test ({page0})")
        P.g(1, PAT); P.g(1, MIX); P.g(2, MIX); P.g(2, PAT); time.sleep(0.2)
        b = gm()
        check(b[:4] == b"GMV2" and b[G.O_ON] == 1, f"Patterns held + Mixer: the view on (signature {b[:4]!r}, on {b[G.O_ON]})")
        P.knob(2, 1); time.sleep(0.1)
        b = gm()
        check(b[G.O_LAST] == 2, f"K3 picked ({b[G.O_LAST]})")
        for p in (8, 17, 27): P.pad(p); P.padup(p)
        time.sleep(0.2); b = gm()
        m = [b[G.O_M + 8 * r + 2] for r in range(4)]
        check(m[1] & 1 and m[2] & 2 and m[3] & 8, f"pads 9 / 18 / 28 linked to K3 (rows: {[hex(x) for x in m]})")
        v0 = (lvl(0), rev(1), dly(3))
        P.knob(2, 5); time.sleep(0.3)
        v1 = (lvl(0), rev(1), dly(3))
        check(v1 == tuple(min(127, v + 5) for v in v0), f"K3 +5: Synth 1's level, Synth 2's reverb send, MIDI 2's delay send {v0} -> {v1}")
        check(u8(G.MIXV + G.MIX_PAGE) == 1, "  the Mixer still on its pans page")
        P.knob(2, -5); time.sleep(0.3)
        v2 = (lvl(0), rev(1), dly(3))
        check(v2 == tuple(max(0, v - 5) for v in v1), f"K3 -5: {v1} -> {v2} (a value at 127 before stays 5 lower)")
        for p in (8, 17, 27): P.pad(p); P.padup(p)
        time.sleep(0.2); b = gm()
        check([b[G.O_M + 8 * r + 2] for r in (1, 2, 3)] == [m[1] ^ 1, m[2] ^ 2, m[3] ^ 8], "the three links off again")
        P.tap(MIX); time.sleep(0.2)
        b = gm()
        check(b[G.O_ON] == 0, f"Mixer alone: the view off ({b[G.O_ON]})")
        P.tap(OCT_UP); time.sleep(0.1)                                                 # the Mixer back on its levels page
        raw = BR.read(L)
        import blackbox as BB
        check(raw[BB.O.ST] == 0, f"the black box empty (state {raw[BB.O.ST]:#x})")
        check(P.lost == 0, "every gesture answered")
    finally:
        L.close(); log.close()
    print("S717D GMVIEW ON THE DEVICE:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
