"""SC38.8 ARM tests (live RAM dump, the real routes: Synth 1's Preset view through the controller's buttons / pads 0x08033320 / PRESS, the LED task
0x08034196, the stock content API on emu_sc35's model of the SD card): the patch pads coloured by voice mode (packio.use_pmode) and pads 22 / 23 left to
the stock in the Advanced Setup view (build_sc10.use_advleds).

    python tools/emu_sc38_8.py SC38.8.bin SC38.8_manifest.json SC38.7.bin SC38.7_manifest.json
  * page 1 of the loaded pack: bank 0 with modes mono / glide / poly (byte 32), bank 1 with 3 patches, bank 2 missing, bank 3 with 0xFF records (the stock's
    empty slots): mono = PM_MONO[0], glide = PM_GLIDE[0], the selected patch PM_MONO[1] / PM_GLIDE[1], poly / missing / empty = the stock's colours; the
    four banks read once (size, then the bank), the shared-buffer lock balanced; the next frames read nothing;
  * another patch chosen (the real pad): read again, the old one back to its dim colour, the new one bright;
  * a mode changed on the card: nothing before 4 s, then the new colour (a pad that becomes poly gets the stock colour back);
  * page 2: its banks read, their colours; another pack loaded: read again;
  * Master FX shown in between (its LED buffer = the cache): read again when back;
  * Advanced Setup (+0x24 set): pads 22 / 23 as the stock draws them; the plain Setup view: the returns' colours as before;
  * the previous build: the stock colours, nothing read.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc35 as T  # noqa: E402
from emu_sc35 import E35, MGR, TICK, PK, set_loaded, SVIEW  # noqa: E402
from emu_sc08 import CONT  # noqa: E402

SETUP, SETUP_LISTEN = 0x20044958, 0x080470F4
MONO, GLIDE, POLY = 0, 1, 2


def bank(modes, n=8, fill=None):
    """n records of 512 bytes (the last one 340), byte 32 = the voice mode; fill = records of 0xFF (the stock's empty slots)"""
    out = bytearray()
    for k in range(n):
        rec = bytearray((k * 7 + i) & 0x7F for i in range(PK.PATCH_SZ))
        rec[PK.PM_VOICE] = modes[k % len(modes)]
        if fill and k in fill: rec = bytearray([0xFF]) * PK.PATCH_SZ
        out += rec
        if k < n - 1: out += bytes([0xFF]) * (PK.PATCH_STRIDE - PK.PATCH_SZ)
    return bytes(out)


def run(img, man, has):
    e = E35(img, man)
    e.set_p0(e.r32(CONT + 0x188), 0); e.btn(0); e.btn(8)                         # Synth 1's Preset view
    CUR = 31; set_loaded(e, man, CUR)
    page_of = lambda: (e.call(0x0803542C, e.r32(SVIEW + 0x20), 0), e.r8(e.uc.reg_read(UC_ARM_REG_R0)))[1]
    sel_of = lambda: (e.call(0x0803542C, e.r32(SVIEW + 0x14), 10), e.r8(e.uc.reg_read(UC_ARM_REG_R0)))[1]
    e.sd = {(3, 0, 0xFF): bank([POLY, MONO, GLIDE, POLY, MONO, GLIDE, POLY, POLY]), (3, 1, 0xFF): bank([MONO], n=3),
            (3, 3, 0xFF): bank([GLIDE], fill={2, 3}), (3, 4, 0xFF): bank([GLIDE, MONO]), (3, 5, 0xFF): bank([POLY])}
    ms = [200000]
    def frame(dt=20):
        ms[0] += dt; e.w32(TICK, ms[0])
        e.call(0x08034196, MGR, 0x2006E000, maxins=8_000_000); return list(struct.unpack("<32H", bytes(e.uc.mem_read(0x2006E000, 64))))
    reads = lambda: [(c[0], c[1][1]) for c in e.api if c[0] in ("size", "read")]
    def setp(st, n, v):                                                       # a store's value written and published (its listeners run)
        e.call(0x080354FA, st, n); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes([v])); e.call(0x080353C0, st, maxins=8_000_000)
    setsel = lambda v: setp(e.r32(SVIEW + 0x14), 10, v)                    # the patch chosen (the stock loads it asynchronously)
    idx = struct.unpack("<H", bytes(e.uc.mem_read(SVIEW + 0x26, 2)))[0]
    tab = lambda i: struct.unpack_from("<H", img, PK.TRACK_COLS - 0x08010000 + 2 * i)[0]
    out = dict(bright=tab(idx), dim=tab(idx + 1), page0=page_of())
    setsel(0); out["sel0"] = sel_of()                                            # patch 1 (poly) chosen
    e.api.clear(); out["f1"] = frame(); out["r1"] = reads(); out["lock1"] = e.lock
    e.api.clear(); out["f2"] = frame(); out["r2"] = reads()
    setsel(1); e.api.clear(); out["f3"] = frame(); out["r3"] = reads(); out["sel3"] = sel_of()  # patch 2 (mono) chosen
    s0 = bytearray(e.sd[(3, 0, 0xFF)]); s0[512 * 4 + PK.PM_VOICE] = POLY; s0[512 * 6 + PK.PM_VOICE] = MONO; e.sd[(3, 0, 0xFF)] = bytes(s0)
    e.api.clear(); out["f4"] = frame(); out["r4"] = reads()                       # within 4 s: the old modes
    e.api.clear(); out["f5"] = frame(4200); out["r5"] = reads()                   # 4 s later: read again
    setp(e.r32(SVIEW + 0x20), 0, 1); e.api.clear(); out["page5"] = page_of(); out["f6"] = frame(); out["r6"] = reads()   # the next page
    set_loaded(e, man, 12)
    e.api.clear(); out["f7"] = frame(); out["r7"] = reads()                       # another pack: read again
    e.btn(14); e.btn(14); frame(); e.btn(0); e.btn(8)                              # Master FX (Mixer twice) and back to Synth 1's Preset view
    e.api.clear(); out["f8"] = frame(); out["r8"] = reads(); out["lock8"] = e.lock
    # ---- the Setup view: plain and Advanced (+0x24)
    e.w32(MGR + 0x6C, SETUP)
    def setup_leds(adv):
        e.uc.mem_write(SETUP + 0x24, bytes([adv])); buf = e.r32(e.r32(SETUP + 4))
        e.uc.mem_write(buf + 2 * 21, struct.pack("<2H", 0x77, 0x77))            # what the stock left there (a mark)
        e.call(0x08034196, MGR, 0x2006E000, maxins=8_000_000); return struct.unpack("<2H", bytes(e.uc.mem_read(0x2006E000 + 2 * 21, 4)))
    out["adv"] = setup_leds(1); out["plain"] = setup_leds(0)
    del e; gc.collect()
    return out


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    o = run(img, man, True)
    B, D = o["bright"], o["dim"]
    M, G = PK.PM_MONO, PK.PM_GLIDE
    lo = {MONO: M[0], GLIDE: G[0]}
    page0 = [POLY, MONO, GLIDE, POLY, MONO, GLIDE, POLY, POLY] + [MONO] * 3 + [None] * 5 + [None] * 8 + [GLIDE, GLIDE, None, None, GLIDE, GLIDE, GLIDE, GLIDE]
    def want(modes, sel):
        return [(B if i == sel else D) if m not in lo else (M if m == MONO else G)[1 if i == sel else 0] for i, m in enumerate(modes)]
    check(o["page0"] == 0 and o["sel0"] == 0, f"Synth 1's Preset view, page 1, patch 1 chosen (page {o['page0']}, patch {o['sel0']}); stock colours dim {D:#x} / bright {B:#x}")
    w1 = want(page0, 0)
    check(o["f1"] == w1, f"the page by mode: mono {M[0]:#x}, glide {G[0]:#x}, poly / missing / empty the stock's\n    got  {[hex(x) for x in o['f1']]}\n    want {[hex(x) for x in w1]}")
    check(o["r1"] == [("size", 0), ("read", 0), ("size", 1), ("read", 1), ("size", 2), ("size", 3), ("read", 3)] and o["lock1"] == 0,
          f"the four banks: size, then the bank (none for the missing one); lock balanced ({o['r1']}, lock {o['lock1']})")
    check(o["f2"] == w1 and o["r2"] == [], f"the next frame: the same colours, nothing read ({o['r2']})")
    w3 = want(page0, 1)
    check(o["sel3"] == 1 and o["f3"] == w3 and len(o["r3"]) == 7, f"patch 2 (mono) chosen: bright blue {M[1]:#x}, patch 1 back to the stock's dim; read again ({len(o['r3'])} calls)\n    got  {[hex(x) for x in o['f3']]}")
    check(o["f4"] == w3 and o["r4"] == [], "a mode changed on the card: nothing read before 4 s")
    p5 = list(page0); p5[4] = POLY; p5[6] = MONO
    check(o["f5"] == want(p5, 1) and len(o["r5"]) == 7, f"4 s later: read again, pad 5 (now poly) back to the stock's colour, pad 7 (now mono) blue\n    got  {[hex(x) for x in o['f5']]}")
    page1 = [GLIDE, MONO] * 4 + [POLY] * 8 + [None] * 16
    check(o["page5"] == 1 and o["f6"] == want(page1, -1) and [c for c in o["r6"] if c[0] == "size"] == [("size", 4), ("size", 5), ("size", 6), ("size", 7)],
          f"page 2 (banks 4-7) read, its colours\n    got  {[hex(x) for x in o['f6']]}")
    check(len(o["r7"]) >= 4, f"another pack loaded: read again ({len(o['r7'])} calls)")
    check(len(o["r8"]) >= 4 and o["lock8"] == 0, f"Master FX shown in between (its LED buffer holds the cache): read again when back ({len(o['r8'])} calls)")
    check(o["adv"] == (0x77, 0x77), f"Advanced Setup: pads 22 / 23 as the stock left them ({[hex(x) for x in o['adv']]})")
    check(o["plain"] != (0x77, 0x77), f"the Setup view: pads 22 / 23 = the returns' colours as before ({[hex(x) for x in o['plain']]})")
    q = run(prev, prev_man, False)
    check(q["f1"] == want([None] * 32, 0) and q["r1"] == [], f"SC38.7: the stock's colours, nothing read ({q['r1']})")
    check(q["adv"] != (0x77, 0x77), f"SC38.7: Advanced Setup with pads 22 / 23 painted ({[hex(x) for x in q['adv']]}: what the user saw)")
    print("SC38.8 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
