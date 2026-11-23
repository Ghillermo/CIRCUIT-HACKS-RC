"""Alpha 7.28 test (tools/novasec.py) through the controller and the LED task: Synth 1's alt page (Synth 1 twice):
  * pads 1-8 = the section row in the own synth's colours (Macros bright, the rest dim); pad 25 = the macro editor's LED, pad 32 = the knob
    sequencer's, pad 30 dark;
  * pad 2 = OSC 1: pad 2 bright; K1 turned = the patch's semitones (row 12) move, the macros do not; its knob LED in OSC 1's colour;
  * a list (OSC 1 wave, K3, 30 waves): 4 events a wave;  VCF (pad 5) K1 = the filter frequency (row 34);
  * Mod matrix (pad 8): K1 = the slot (4 events a slot), K4 = that slot's destination (row 94 + 4 slot + 3);
  * pad 1 = Macros: K1 = the stock macro again (row 175 moves);
  * pad 25 = the macro editor on (as pad 32 before), the row hidden; pad 25 again = off;  pad 32 = the knob sequencer's step view (as pad 30 before).
    python tools/emu_novasec.py firmware/a7.28
"""
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn.arm_const import UC_ARM_REG_R0
import emu_sc48_8 as S
import emu_sc42_6 as X
import arp as A
import novasec as N

MGR, GETTER = S.MGR, 0x08036192
PRESS, RELEASE, KNOB = 0x08033282, 0x080332FE, 0x08033848


def main(a):
    d = Path(a[0]); img = next(d.glob("*.bin")).read_bytes(); man = json.loads((d / "manifest.json").read_text())
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = S.ET(img, man)
    e.uc.mem_map(0x40024000 & ~0xFFF, 0x1000) if False else None
    t = [500000]
    def at(ms): t[0] += ms; e.w32(A.HAL_TICK, t[0])
    def frame(): at(20); X.frame(e); return X.frame(e)
    def pad(q): e.call(PRESS, MGR, q, 100, maxins=8_000_000); e.call(RELEASE, MGR, q, maxins=8_000_000); frame()
    def knob(k, dl, n=1):
        for _ in range(n): e.call(KNOB, MGR, k, dl & 0xFFFFFFFF, maxins=8_000_000)
        frame()
    def get(row): e.call(GETTER, 0, row, maxins=400_000); return e.uc.reg_read(UC_ARM_REG_R0) & 0xFF
    gst = int(man["report"]["sc14"]["labels"]["c_gst"], 16)
    def alt():
        e.call(gst, maxins=100_000); g = e.uc.reg_read(UC_ARM_REG_R0)
        return g and e.r8(g + N.S_PAINT) & N.F_SRC and e.r8(MGR + 0x152) == 0
    at(0)
    for _ in range(5):
        if alt(): break
        e.btn(0); frame()
    check(alt(), "Synth 1's alt page reached")
    f = frame()
    cols = N.page_colours()
    check([f[k] for k in range(8)] == [cols[0][0]] + [c[1] for c in cols[1:]], f"the row: Macros bright, the rest dim ({[hex(x) for x in f[:8]]})")
    check(f[29] == 0 and f[24] != 0 and f[31] != 0, f"pad 30 dark, pads 25 / 32 lit ({f[24]:#x}, {f[29]:#x}, {f[31]:#x})")
    pad(1); f = frame()
    check(f[1] == cols[1][0] and f[0] == cols[0][1], f"pad 2: OSC 1 bright ({f[1]:#x})")
    s0, m0 = get(12), get(174)
    knob(0, 5); s1, m1 = get(12), get(174)
    check(s1 == min(s0 + 5, 127) and m1 == m0, f"OSC 1, K1 +5: semitones {s0} -> {s1}, the macro stays ({m0} -> {m1})")
    f = frame(); kl = f[60] & 0xFF
    check(kl == cols[1][0], f"K1's LED in OSC 1's colour ({kl if kl is None else hex(kl)})")
    w0 = get(6); knob(2, 1, 3); w1 = get(6); knob(2, 1, 1); w2 = get(6)
    check(w1 == w0 and w2 == min(w0 + 1, 29), f"OSC 1 wave (30 waves): 3 events nothing, the 4th one wave ({w0}, {w1}, {w2})")
    pad(4); fr0 = get(34); knob(0, -7); fr1 = get(34)
    check(fr1 == max(fr0 - 7, 0), f"VCF K1 -7: the filter frequency {fr0} -> {fr1}")
    pad(7); knob(0, 1, 8)
    slot = e.r8(N.NS + 5)
    check(slot == 2, f"Mod matrix K1 +8 events: slot 3 (index {slot})")
    dd0 = get(N.MX0 + 4 * 2 + 3); knob(3, 1, 16); dd1 = get(N.MX0 + 4 * 2 + 3)
    check(dd1 == min(dd0 + 2, 17), f"K4 = slot 3's destination (18 values: 7 events each) {dd0} -> {dd1}")
    pad(0); m2 = get(174); knob(0, -3); m3 = get(174)
    check(m3 != m2, f"pad 1 = Macros: K1 moves the macro again ({m2} -> {m3})")
    pad(24); f = frame()
    import macroed as MC
    st = e.r32(0) if False else None
    check(f[0] != cols[0][0] or f[1] != cols[1][1], f"pad 25 = the macro editor on: the row hidden ({[hex(x) for x in f[:8]]})")
    pad(24); f = frame()
    check([f[k] for k in range(8)] == [cols[0][0]] + [c[1] for c in cols[1:]], "pad 25 again: the editor off, the row back")
    pad(31); f = frame()
    check([f[k] for k in range(8)] != [cols[0][0]] + [c[1] for c in cols[1:]], f"pad 32 = the knob sequencer's step view (the row hidden) ({[hex(x) for x in f[:8]]})")
    pad(31); f = frame()
    check([f[k] for k in range(8)] == [cols[0][0]] + [c[1] for c in cols[1:]], "pad 32 again: closed, the row back")
    print("NOVASEC RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
