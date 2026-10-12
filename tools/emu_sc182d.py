"""SC182D (persistence probe) ARM tests, through the real controller routes and the real stock save / load code, on the live RAM dump.

    python tools/emu_sc182d.py STOCK.bin SC18.2.bin SC182D.bin SC182D_manifest.json
Checks: Shift + pad 8 writes / clears the 15 markers only in the reserved bytes, the pad / knob LEDs, the old pad 8 and the Mixer
untouched, and the two load hooks (counters) around the stock new-project (0x0802F5BC) and load (0x0802EEFE) functions; plus the
stock save (0x0802F63C) -> load round trip of the markers.
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
import masterfx_dsp as G  # noqa: E402
import probe19 as P  # noqa: E402

OBJ = 0x2003D71C                                   # session manager (stock save / load object)
BLOB = {P.CTX_SYNTH1: 0x20010044, P.CTX_SYNTH2: 0x2001019C, P.CTX_DRUMS: 0x200102F4, P.CTX_PROJECT: 0x20010324}
SIZE = {P.CTX_SYNTH1: 340, P.CTX_SYNTH2: 340, P.CTX_DRUMS: 44, P.CTX_PROJECT: 60}
SPARE = {P.CTX_SYNTH1: (18, 115), P.CTX_SYNTH2: (18, 115)}
NEW_PROJECT, LOAD, SAVE, REFRESH = 0x0802F5BC, 0x0802EEFE, 0x0802F63C, 0x08029A00


class EP(E7):
    def __init__(self, image, man):
        super().__init__(image, man)
        self.refresh = []
        self.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: self.refresh.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2))),
                         begin=REFRESH, end=REFRESH)
    def byte(self, co, off): return self.r8(BLOB[co] + off)
    def setbyte(self, co, off, v): self.uc.mem_write(BLOB[co] + off, bytes([v]))
    def probes(self): return [self.byte(co, o) for co, o, m in P.PROBES]
    def cnt(self): return self.blkb(P.CNT)[0]


def main(stock, ref, img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]
    lab = {k: int(v, 16) for k, v in rep["probe19"]["labels"].items()}
    BASE = 0x08010000
    check(img[P.LOAD_END - BASE:P.LOAD_END - BASE + 4] == __import__("thumb").b_w(P.LOAD_END, lab["c_pr_loadB"]), "load end 0x0802F5B8 -> c_pr_loadB")
    check(img[P.NEW_TAIL - BASE:P.NEW_TAIL - BASE + 4] == __import__("thumb").b_w(P.NEW_TAIL, lab["c_pr_loadA"]), "new-project tail 0x0802F5FA -> c_pr_loadA")
    vt = lambda i: struct.unpack_from("<I", img, P.MIX_VT + 4 * i - BASE)[0]
    check(vt(0) == lab["c_pr_press"] | 1 and vt(7) == lab["c_pr_leds"] | 1, "Mixer view slots 0 / 7 -> the probe wrappers")
    check(len(P.PROBES) == 15, "15 probes")

    e = EP(img, man)
    e.grid()
    zero = [0] * 15
    check(e.probes() == zero, f"fresh dump: all reserved bytes are 0 {e.probes()}")
    g = e.gleds()
    check(g[8:23] == [P.DIM] * 15 and g[23] == P.DIM and g[34:42] == [0] * 8, f"probe pads dim, counters off {[hex(x) for x in g[8:24]]}")
    before = {co: bytes(e.uc.mem_read(BLOB[co], SIZE[co])) for co in BLOB}
    c = e.pad(7, shift=True); e.rel(7)
    mk = [m for _, _, m in P.PROBES]
    check(c == [] and e.probes() == mk, f"Shift + pad 8: the 15 markers written {[hex(x) for x in e.probes()]}")
    after = {co: bytes(e.uc.mem_read(BLOB[co], SIZE[co])) for co in BLOB}
    touched = {(co, i) for co in BLOB for i in range(SIZE[co]) if before[co][i] != after[co][i]}
    check(touched == {(co, o) for co, o, _ in P.PROBES}, f"only the 15 reserved bytes changed ({len(touched)} bytes)")
    g = e.gleds()
    check(g[8:23] == [P.ON] * 15, f"probe pads lit {[hex(x) for x in g[8:23]]}")
    e.setbyte(P.PROBES[3][0], P.PROBES[3][1], 0x77); e.setbyte(P.PROBES[9][0], P.PROBES[9][1], 0)
    g = e.gleds()
    check(g[11] == P.OTHER and g[17] == P.DIM and g[8] == P.ON, f"another value = OTHER, zero = DIM {hex(g[11])} {hex(g[17])}")
    e.setbyte(P.PROBES[3][0], P.PROBES[3][1], P.PROBES[3][2]); e.setbyte(P.PROBES[9][0], P.PROBES[9][1], P.PROBES[9][2])
    c = e.pad(7, shift=True); e.rel(7)
    check(e.probes() == zero and bytes(e.uc.mem_read(BLOB[P.CTX_DRUMS], 44)) == before[P.CTX_DRUMS], "Shift + pad 8 again: markers cleared, blobs as before")
    # the stock clear pad is untouched
    e.pad(0, shift=True); e.rel(0)
    check(e.blkb(B.S_LATCH)[0] == 1, "Gater latched")
    c = e.pad(7); e.rel(7)
    check(e.blkb(B.S_LATCH)[0] == 0 and e.probes() == zero, "pad 8 without Shift: the clear pad, no markers")
    # a store that is not valid (vtable / size) is never written: break the drums store
    e2 = EP(img, man); e2.grid()
    e2.w32(0x200103B8, 0)
    c = e2.pad(7, shift=True); e2.rel(7)
    g = e2.gleds()
    check(e2.probes()[:8] == [0] * 8 and g[8:16] == [0] * 8 and e2.probes()[8:] == mk[8:], "invalid drums store: nothing written, its pads off")
    # outside the Master FX view
    e.btn(14)
    c = e.pad(7, shift=True)
    check(c == [(MIX_PRESS, MIXER, 7)] and e.probes() == zero, f"normal Mixer: Shift + pad 8 = stock mute {[(hex(a), hex(b), n) for a, b, n in c]}")
    # ---- the stock save / new project / load around the hooks
    e = EP(img, man); e.grid()
    c = e.pad(7, shift=True); e.rel(7)
    e.call(SAVE, OBJ, maxins=8_000_000)
    for co, o, m in P.PROBES: e.setbyte(co, o, 0)
    check(e.probes() == zero and e.cnt() == 0, "setup: markers in the saved buffer, live bytes cleared, counters 0")
    e.refresh.clear()
    e.call(LOAD, OBJ, 1, maxins=30_000_000)
    check(e.probes() == mk, f"stock load (0x0802EEFE): the markers come back from the buffer {[hex(x) for x in e.probes()]}")
    check(e.cnt() == 0x10, f"load hook counted: block byte {e.cnt():#x}")
    g = e.gleds()
    check(g[8:23] == [P.ON] * 15 and g[23] == P.ON and g[34:42] == [0, 0, 0, 0, P.KNOB_ON, 0, 0, 0], f"LEDs: probes lit, pad 24 lit, knob LED 5 = 1 load {[hex(x) for x in g[34:42]]}")
    e.refresh.clear()
    e.call(NEW_PROJECT, OBJ, maxins=30_000_000)
    check(e.cnt() == 0x11 and len(e.refresh) == 1 and e.refresh[0][1] == 0x10000 and e.refresh[0][2] == 1,
          f"new-project hook counted and the stock tail 0x08029A00(ctx, 0x10000, 1) still runs {e.cnt():#x} {[(hex(a), hex(b), c) for a, b, c in e.refresh]}")
    pr = e.probes()
    check(pr[:8] == [0] * 8 and pr[12:] == [0] * 3 and pr[8:12] == mk[8:12], "new project: drums and project reserved bytes back to 0 (defaults); the synth patches are not part of it")
    g = e.gleds()
    check(g[34:42] == [P.KNOB_ON, 0, 0, 0, P.KNOB_ON, 0, 0, 0], f"knob LEDs: 1 new project, 1 load {[hex(x) for x in g[34:42]]}")
    for _ in range(17): e.call(LOAD, OBJ, 1, maxins=30_000_000)
    check(e.cnt() >> 4 == 15 and e.cnt() & 15 == 1, f"counters saturate at 15 {e.cnt():#x}")
    # ---- patch loads behave like the project does for the other bytes: Mixer LEDs outside Master FX identical to SC18.2
    a, b = EP(ref, man), EP(img, man)
    for x in (a, b): x.btn(14)
    check(a.gleds() == b.gleds(), "normal Mixer LEDs identical to SC18.2")
    print("SC182D ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    st, rf, im = (Path(sys.argv[i]).read_bytes() for i in (1, 2, 3))
    sys.exit(1 if main(st, rf, im, json.loads(Path(sys.argv[4]).read_text())) else 0)
