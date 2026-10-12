"""SC183D (persistence probe v2) ARM tests, through the real controller routes and the real stock save / load code, on the live RAM dump.

    python tools/emu_sc183d.py STOCK.bin SC18.3.bin SC183D.bin SC183D_manifest.json
Checks: generation writes / clear / probe selection / display source (live stores or session record), the pad, knob and slot-row LEDs,
only the 15 reserved bytes ever written, the three event hooks around the stock save / new project / load, and the save -> load round
trip through the session record.
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc17_8 as T8  # noqa: E402  (applies the SC17.8 options to build_sc17)
from emu_sc17_7 import E7  # noqa: E402
from emu_sc17_6 import MIXER, MIX_PRESS  # noqa: E402
import build_sc17 as B  # noqa: E402
import probe20 as P  # noqa: E402
import thumb  # noqa: E402

OBJ = P.OBJ
BLOB = {P.P1.CTX_SYNTH1: 0x20010044, P.P1.CTX_SYNTH2: 0x2001019C, P.P1.CTX_DRUMS: 0x200102F4, P.P1.CTX_PROJECT: 0x20010324}
SIZE = {P.P1.CTX_SYNTH1: 340, P.P1.CTX_SYNTH2: 340, P.P1.CTX_DRUMS: 44, P.P1.CTX_PROJECT: 60}
NEW_PROJECT, LOAD, SAVE = 0x0802F5BC, 0x0802EEFE, 0x0802F63C
BASE = 0x08010000


class EP(E7):
    def byte(self, co, off): return self.r8(BLOB[co] + off)
    def setbyte(self, co, off, v): self.uc.mem_write(BLOB[co] + off, bytes([v]))
    def probes(self): return [self.byte(co, o) for co, o, m in P.PROBES]
    def record(self):
        buf = self.r32(OBJ + 0x14)
        return [self.r8(buf + P.REC[co] + o) for co, o, m in P.PROBES]
    def ex(self): return tuple(self.blkb(o)[0] for o in (P.B_GEN, P.B_SEL, P.B_MODE, P.B_CNT))


def expect(vals, gen, sel):
    out = []
    for i, v in enumerate(vals):
        out.append(P.SEL if i == sel else P.DIM if v == 0 else P.ON if v == gen else P.OTHER)
    return out


def main(stock, ref, img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]
    lab = {k: int(v, 16) for k, v in rep["probe20"]["labels"].items()}
    check(int(rep["sc17"]["state"], 16) + 184 == 0x20044E58, f"memory: Master FX block 184 bytes ends at the stock heap limit (reservation {0x20044E58 - int(rep['sc17']['sc14_state'], 16)} bytes)")
    check(img[P.LOAD_END - BASE:P.LOAD_END - BASE + 4] == thumb.b_w(P.LOAD_END, lab["c_pr_loadB"]), "load end 0x0802F5B8 -> c_pr_loadB")
    check(img[P.NEW_TAIL - BASE:P.NEW_TAIL - BASE + 4] == thumb.b_w(P.NEW_TAIL, lab["c_pr_loadA"]), "new-project tail 0x0802F5FA -> c_pr_loadA")
    check(img[P.SAVE_CALL - BASE:P.SAVE_CALL - BASE + 4] == thumb.bl(P.SAVE_CALL, lab["c_pr_save"]), "bl to the stock save 0x0802FE5E -> c_pr_save")
    vt = lambda i: struct.unpack_from("<I", img, P.MIX_VT + 4 * i - BASE)[0]
    check(vt(0) == lab["c_pr_press"] | 1 and vt(7) == lab["c_pr_leds"] | 1, "Mixer view slots 0 / 7 -> the probe wrappers")

    e = EP(img, man); e.grid()
    n = len(P.PROBES)
    check(e.probes() == [0] * n and e.ex() == (0, 0, 0, 0), f"fresh dump: all reserved bytes 0, probe state 0 {e.ex()}")
    g = e.gleds()
    check(g[8:23] == expect([0] * n, 0, 0) and g[23] == P.DIM and g[24:32] == [0] * 8 and g[34:42] == [0] * 8, "initial LEDs: dim pads (probe 0 selected), live source, no events")
    before = {co: bytes(e.uc.mem_read(BLOB[co], SIZE[co])) for co in BLOB}
    c = e.pad(7, shift=True); e.rel(7)
    check(c == [] and e.probes() == [1] * n and e.ex()[0] == 1, f"Shift + pad 8: generation 1 written {e.probes()}")
    after = {co: bytes(e.uc.mem_read(BLOB[co], SIZE[co])) for co in BLOB}
    touched = {(co, i) for co in BLOB for i in range(SIZE[co]) if before[co][i] != after[co][i]}
    check(touched == {(co, o) for co, o, _ in P.PROBES}, f"only the 15 reserved bytes changed ({len(touched)} bytes)")
    g = e.gleds()
    check(g[8:23] == expect([1] * n, 1, 0) and g[34:42] == [P.KNOB_ON] + [0] * 7, f"pads lit (selected probe 0 in SELECT colour), knob LEDs = value 1 {[hex(x) for x in g[34:42]]}")
    e.pad(7, shift=True); e.rel(7)
    check(e.probes() == [2] * n and e.ex()[0] == 2, "second Shift + pad 8: generation 2")
    e.pad(6, shift=True); e.rel(6)
    check(e.probes() == [0] * n and e.ex()[0] == 2, "Shift + pad 7: cleared, generation stays 2")
    e.pad(7, shift=True); e.rel(7)
    e.pad(13, shift=True); e.rel(13)
    check(e.ex()[1] == 5 and e.probes() == [3] * n, f"Shift + pad 14: probe 5 selected {e.ex()}")
    g = e.gleds()
    check(g[8:23] == expect([3] * n, 3, 5) and g[34:42] == [P.KNOB_ON, P.KNOB_ON] + [0] * 6, f"knob LEDs show probe 5 = 3 {[hex(x) for x in g[34:42]]}")
    e.setbyte(P.PROBES[2][0], P.PROBES[2][1], 0x80); e.setbyte(P.PROBES[4][0], P.PROBES[4][1], 0)
    g = e.gleds()
    check(g[10] == P.OTHER and g[12] == P.DIM and g[8] == P.ON, f"another generation = OTHER, zero = DIM {hex(g[10])} {hex(g[12])}")
    e.pad(12, shift=True); e.rel(12)                                            # select probe 4 (value 0)
    g = e.gleds(); check(g[34:42] == [0] * 8, "selected value 0: knob LEDs off")
    e.pad(10, shift=True); e.rel(10)                                            # probe 2 = 0x80
    g = e.gleds(); check(g[34:42] == [0] * 7 + [P.KNOB_ON], f"selected value 0x80: knob 8 lit {[hex(x) for x in g[34:42]]}")
    e.setbyte(P.PROBES[2][0], P.PROBES[2][1], 3); e.setbyte(P.PROBES[4][0], P.PROBES[4][1], 3)
    # the other pads keep their stock role
    e.pad(6); jf = e.blkb(177)[0]; e.rel(6)
    check(jf & 1 == 1, f"pad 7 without Shift: still the jump button (JF {jf:#x})")
    c = e.pad(0, shift=True); e.rel(0)
    check(e.blkb(B.S_LATCH)[0] == 1, "other pads with Shift (pad 1): Master FX latch as before")
    c = e.pad(7); e.rel(7)
    check(e.blkb(B.S_LATCH)[0] == 0 and e.probes() == [3] * n, "pad 8 without Shift: the clear pad, no write")
    # display source: the session record
    e.pad(23, shift=True); e.rel(23)
    check(e.ex()[2] == 1, "Shift + pad 24: record source")
    g = e.gleds()
    rec = e.record()
    check(g[23] == P.ON and g[8:23] == expect(rec, 3, 2), f"record display = the session record bytes {rec}")
    # stock save through the hooked bl wrapper, then clear the live bytes: the record keeps the generation
    cnt0 = e.ex()[3]
    e.call(lab["c_pr_save"], OBJ, maxins=8_000_000)
    check(e.record() == [3] * n and e.ex()[3] == cnt0 + 32, f"save wrapper: stock save copied the stores into the record, save count +1 {e.record()} {e.ex()[3]:#x}")
    e.pad(6, shift=True); e.rel(6)
    check(e.probes() == [0] * n and e.record() == [3] * n, "Shift + pad 7: live bytes cleared, the record still holds generation 3")
    g = e.gleds(); check(g[8:23] == expect([3] * n, 3, 2), "record source: pads still lit")
    e.pad(23, shift=True); e.rel(23)
    g = e.gleds(); check(g[8:23] == expect([0] * n, 3, 2) and g[23] == P.DIM, "live source: pads dim")
    e.call(LOAD, OBJ, 1, maxins=30_000_000)
    check(e.probes() == [3] * n and e.ex()[3] == cnt0 + 32 + 4, f"stock load: generation 3 back from the record, load count +1 {e.probes()} {e.ex()[3]:#x}")
    g = e.gleds()
    check(g[24:32] == [0, 0, P.KNOB_ON, 0, 0, P.KNOB_ON, 0, 0], f"slot row = counters (pad 27: 1 load, pad 30: 1 save) {[hex(x) for x in g[24:32]]}")
    e.call(NEW_PROJECT, OBJ, maxins=30_000_000)
    pr = e.probes()
    check(e.ex()[3] & 3 == 1 and pr[:8] == [0] * 8 and pr[12:] == [0] * 3 and pr[8:12] == [3] * 4, f"new project: counter, drums / project bytes back to 0, synth patches untouched {pr}")
    for _ in range(9): e.call(lab["c_pr_save"], OBJ, maxins=8_000_000)
    check(e.ex()[3] >> 5 == 7, f"save count saturates at 7 {e.ex()[3]:#x}")
    # a store that is not valid is never written
    e2 = EP(img, man); e2.grid(); e2.w32(0x200103B8, 0)
    e2.pad(7, shift=True); e2.rel(7)
    g = e2.gleds()
    check(e2.probes()[:8] == [0] * 8 and e2.probes()[8:] == [1] * 7 and g[9:16] == [0] * 7, "invalid drums store: nothing written, its pads off")
    # outside Master FX
    e.btn(14)
    c = e.pad(7, shift=True)
    check(c == [(MIX_PRESS, MIXER, 7)], f"normal Mixer: Shift + pad 8 = stock mute {[(hex(a), hex(b), n_) for a, b, n_ in c]}")
    a, b = EP(ref, man), EP(img, man)
    for x in (a, b): x.btn(14)
    check(a.gleds() == b.gleds(), "normal Mixer LEDs identical to SC18.3")
    print("SC183D ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    st, rf, im = (Path(sys.argv[i]).read_bytes() for i in (1, 2, 3))
    sys.exit(1 if main(st, rf, im, json.loads(Path(sys.argv[4]).read_text())) else 0)
