"""Beta 5.38 / SC55.3 (packio.use_pmode4 + use_pcat, 2026-11-08): the synth Preset view's patch pads by category, the card read only when needed.

    python tools/emu_pcat.py SC55.3.bin SC55.3_manifest.json
  * entering the view: the page's four banks read, one per LED pass (size, then the bank), the lock balanced; then nothing more is read;
  * colours: category 1..14 = CAT_PAL, category 0 / unknown = the track's colour (the stock's), the selected patch white (the stock's), an empty
    slot (0xFF record, past the bank's end, no bank file) dim white;
  * another patch chosen (the store's listener, as the stock's load does): the two pads redrawn at once, in their colours, nothing read;
  * a pad pressed, then another page at once: nothing read for 1 s, then its banks;
  * back to page 1: read again (a new page), the cached colours shown meanwhile;
  * Clear held, then released: read again; leaving the view and entering it again: read again; another pack: read again.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import E35, MGR, TICK, PK, set_loaded, SVIEW  # noqa: E402
from emu_sc08 import CONT  # noqa: E402
from emu_sc17_6 import RELEASE  # noqa: E402

fails = []


def check(c, m):
    print(("  ok   " if c else "  FAIL ") + m)
    if not c: fails.append(m)


def bank(cats, n=8, fill=()):
    out = bytearray()
    for k in range(n):
        rec = bytearray((k * 7 + i + 1) & 0x7F for i in range(PK.PATCH_SZ))
        rec[PK.PM_CAT] = cats[k % len(cats)]
        if k in fill: rec = bytearray([0xFF]) * PK.PATCH_SZ
        out += rec
        if k < n - 1: out += bytes([0xFF]) * (PK.PATCH_STRIDE - PK.PATCH_SZ)
    return bytes(out)


def save_test(e, frame, img):
    """psave.use_savecat: Clear + pad asks; K1 = the category (its LED and the slot's blink in its colour), K2-K8 off and ignored; Clear + the same
    pad again writes the patch with it."""
    P = PK.CAT_PAL
    e.uc.mem_write(0x20010044 + 16, bytes([2]))                                 # Synth 1's patch: Bass
    [frame(200) for _ in range(8)]
    knobs = lambda f: [struct.unpack_from("<H", bytes(e.uc.mem_read(0x2006E000 + 2 * (60 + k), 2)))[0] for k in range(8)]
    kb = knobs(None); e.held(1); e.call(0x08033282, MGR, 9, 100); e.call(RELEASE, MGR, 9, maxins=900000)
    frame(); k0 = knobs(None)
    check(k0[0] & 0xFF == P[2] and all(v & 0xFF == 0 for v in k0[1:]), f"asked: K1 in Bass's colour, the others off ({[hex(v) for v in k0]}, before {[hex(v) for v in kb]})")
    for _ in range(4): e.call(0x08033848, MGR, 0, 1, maxins=8_000_000)
    frame(); k1 = knobs(None)
    check(k1[0] & 0xFF == P[3], f"K1 4 clicks right: Bell ({hex(k1[0])})")
    for _ in range(8): e.call(0x08033848, MGR, 0, -1, maxins=8_000_000)
    for _ in range(9): e.call(0x08033848, MGR, 3, 1, maxins=8_000_000)
    frame(); k2 = knobs(None)
    check(k2[0] & 0xFF == PK.CAT_PAL[1] and e.r8(PK.PCR + 0x0E) == 1, f"8 clicks left: Arp; K4 does nothing ({hex(k2[0])}, category {e.r8(PK.PCR + 0x0E)})")
    e.api.clear(); e.call(0x08033282, MGR, 9, 100); e.call(RELEASE, MGR, 9, maxins=900000); e.held(0)
    w = [c for c in e.api if c[0] == "write"]
    sd = e.sd.get((3, 1, 0xFF), b"")
    check(len(w) >= 1 and len(sd) > 512 + 16 and sd[512 + 16] == 1, f"Clear + the same pad: written with Arp ({len(w)} writes, byte 16 = {sd[512 + 16] if len(sd) > 528 else None})")
    [frame(200) for _ in range(10)]
    check(frame()[9] in (P[1], struct.unpack_from("<H", img, PK.TRACK_COLS - 0x08010000 + 2 * struct.unpack("<H", bytes(e.uc.mem_read(SVIEW + 0x26, 2)))[0])[0]),
          "the slot's colour afterwards: Arp (or white if it became the selected patch)")


def main(img_p, man_p):
    img, man = Path(img_p).read_bytes(), json.loads(Path(man_p).read_text())
    e = E35(img, man)
    e.set_p0(e.r32(CONT + 0x188), 0); e.btn(0); e.btn(8)
    set_loaded(e, man, 31)
    c0 = [0, 2, 7, 9, 10, 14, 15, 1]                                             # None, Bass, Lead, Pad, Poly, Voc, (15: unknown), Arp
    e.sd = {(3, 0, 0xFF): bank(c0), (3, 1, 0xFF): bank([3], n=3), (3, 3, 0xFF): bank([11], fill={2, 3}),
            (3, 4, 0xFF): bank([5, 6]), (3, 5, 0xFF): bank([12]), (3, 6, 0xFF): bank([13]), (3, 7, 0xFF): bank([4])}
    ms = [200000]
    def frame(dt=20):
        ms[0] += dt; e.w32(TICK, ms[0]); e.call(0x08034196, MGR, 0x2006E000, maxins=8_000_000)
        return list(struct.unpack("<32H", bytes(e.uc.mem_read(0x2006E000, 64))))
    def vbuf(): return list(struct.unpack("<32H", bytes(e.uc.mem_read(e.r32(e.r32(SVIEW + 4)), 64))))
    reads = lambda: [(c[0], c[1][1]) for c in e.api if c[0] in ("size", "read")]
    def setp(st, n, v):
        e.call(0x080354FA, st, n); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes([v])); e.call(0x080353C0, st, maxins=8_000_000)
    idx = struct.unpack("<H", bytes(e.uc.mem_read(SVIEW + 0x26, 2)))[0]
    tab = lambda i: struct.unpack_from("<H", img, PK.TRACK_COLS - 0x08010000 + 2 * i)[0]
    B, D = tab(idx), tab(idx + 1)                                               # the stock: selected [idx] (white), the others [idx + 1] (the track's)
    P = PK.CAT_PAL
    def want(cats, sel):                                                        # None = empty
        return [B if i == sel else P[15] if c is None else P[c] if 1 <= c <= 14 else D for i, c in enumerate(cats)]
    page0 = c0 + [3] * 3 + [None] * 5 + [None] * 8 + [11, 11, None, None, 11, 11, 11, 11]
    page1 = [5, 6] * 4 + [12] * 8 + [13] * 8 + [4] * 8
    setp(e.r32(SVIEW + 0x14), 10, 0)
    e.api.clear(); fr = [frame() for _ in range(6)]; r = reads()
    check(r == [("size", 0), ("read", 0), ("size", 1), ("read", 1), ("size", 2), ("size", 3), ("read", 3)] and e.lock == 0,
          f"entering: the four banks, one per LED pass ({r}, lock {e.lock})")
    w = want(page0, 0)
    check(fr[-1] == w, f"the colours by category, empty dim white, None / unknown the stock's\n    got  {[hex(x) for x in fr[-1]]}\n    want {[hex(x) for x in w]}")
    e.api.clear(); [frame(200) for _ in range(23)]; check(reads() == [], "afterwards (also 4 s later): nothing read")
    setp(e.r32(SVIEW + 0x14), 10, 2)                                              # patch 3 (Lead) chosen
    v = vbuf(); w2 = want(page0, 2)
    check(v == w2, f"another patch chosen: the view's buffer redrawn at once in its colours\n    got  {[hex(x) for x in v]}\n    want {[hex(x) for x in w2]}")
    e.api.clear(); frame(); check(reads() == [] and frame() == w2, "and nothing read")
    e.call(0x08033282, MGR, 5, 100); e.call(RELEASE, MGR, 5, maxins=900000)               # a pad pressed (and let go)
    setp(e.r32(SVIEW + 0x20), 0, 1)                                               # the next page at once
    e.api.clear(); frame(); frame(200); q = reads()
    e.api.clear(); [frame(200) for _ in range(9)]; later = reads()
    check(q == [] and [c for c in later if c[0] == "size"] == [("size", b) for b in (4, 5, 6, 7)], f"a pad pressed: nothing for 1 s ({q}), then page 2's banks ({later})")
    check(frame() == want(page1, -1), "page 2's colours")
    [frame(200) for _ in range(6)]; setp(e.r32(SVIEW + 0x20), 0, 0); e.api.clear(); f = frame(200)
    r = reads()
    check(r[:2] == [("size", 0), ("read", 0)] and f[8:] == want(page0, 2)[8:], f"back to page 1: read again, one bank in the first pass ({r}), the others' colours from before")
    [frame() for _ in range(4)]
    e.held(1); e.api.clear(); frame(); n_held = len(reads()); e.held(0); [frame(200) for _ in range(10)]
    check(n_held == 0 and len(reads()) == 7, f"Clear held: nothing; released: read again ({len(reads())} requests)")
    e.btn(14); frame(200); frame(200); e.btn(0); e.btn(8); e.api.clear(); [frame(200) for _ in range(6)]
    check(len(reads()) == 7, f"left (Mixer) and entered again: read again ({len(reads())})")
    set_loaded(e, man, 12); e.sd = {(3, k, 0xFF): v for (t, k, p), v in e.sd.items()}; e.api.clear(); [frame(200) for _ in range(6)]
    check(len(reads()) == 7 and e.lock == 0, f"another pack: read again ({len(reads())}), lock {e.lock}")
    if "--nosave" not in sys.argv:
        save_test(e, frame, img)
    del e; gc.collect()
    print("PCAT RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
