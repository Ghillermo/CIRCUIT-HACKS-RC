"""SC39.1 ARM tests (live RAM dump, the real routes: the controller's buttons, pads and knobs, the LED task): the source of the granular engine as a
travel over the capture and the samples of the four drums (vcf21.use_grsrc).

    python tools/emu_sc39_1_gr.py SC39.1.bin SC39.1_manifest.json SC39.bin SC39_manifest.json
  * MIDI 1 with the granular engine, its page: Shift + K8, one click: the stored sample (0, no drum has it) -> the travel starts in the middle of
    Drum 1's zone: code 25 = Drum 1's sample; the LED = Drum 1's colour;
  * the whole travel up and down, one click at a time = the model: five zones (capture, Drum 1..4), -1 for the capture, the samples the drums have
    now for the others; the ends stop; the LED's colour = the zone's, brighter along the zone;
  * a stored sample no drum has: the LED dim white; another knob of the page as before; Clear + K8 = the capture;
  * the previous build: Shift + K8 = one sample per click.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc36 as T36  # noqa: E402  (configures vcf21 as SC36)
from emu_sc17_6 import MGR  # noqa: E402
import packio as PK  # noqa: E402

V, E20 = T36.V, T36.E20
GETTER = 0x08036192
COL = (0x53, 0x45, 0x2D, 0x49, 0x4D)


def run(img, man, new):
    e = E20(img, man)
    def stub(v):                                                                  # no card in this harness: the patch slots (the view's LED pass) find no bank
        def f(uc, a, s, d): uc.reg_write(UC_ARM_REG_R0, v); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        return f
    for ad, v in ((PK.SIZE, 0), (PK.BUF_LOCK, PK.BUF), (PK.BUF_UNLOCK, 0), (PK.READ, 2), (PK.WRITE, 2)):
        e.uc.hook_add(UC_HOOK_CODE, stub(v), begin=ad & ~1, end=ad & ~1)
    for _ in range(30): e.vtick()
    pad = lambda p: (e.padr(p), e.rel(p))
    def gval(code, t=0):
        e.call(e.vl["c_vvaddr"], t, code); return struct.unpack("b", bytes([e.r8(e.uc.reg_read(UC_ARM_REG_R0))]))[0]
    def sval(code, v, t=0):
        e.call(e.vl["c_vvaddr"], t, code); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes([v & 0xFF]))
    def led():                                                                    # the LED of K8 with Shift held
        e.set_p0(e.r32(MGR + 0xC), 1)
        v = e.frame()[60 + 7]                                                     # the LED task from its caller: panel LED 67 = K8
        e.set_p0(e.r32(MGR + 0xC), 0); return v
    drums = []
    for d in range(4):
        e.call(GETTER, 0x10, 7 * d); drums.append(e.uc.reg_read(UC_ARM_REG_R0) & 0xFF)
    e.btn(2); e.track(2); e.btn(8)
    for _ in range(6):                                                            # pad 27 until the granular engine: oscillator source, engine bits (0, 1)
        f, s = e.tailb(V.O_FLAGS), e.tailb(V.O_SIG)
        if f & 1 and f & 4 and not s & 1 and s & 4: break
        pad(V.PAD_OSC)
    out = dict(drums=drums, engine=(e.tailb(V.O_FLAGS), e.tailb(V.O_SIG)))
    pad(1)                                                                        # the page of OSC1 = the granular page
    sval(25, 0); out["v0"] = gval(25)
    e.knob_raw(7, 1, shift=True); out["first"] = (gval(25), led())
    up = []
    for _ in range(100): e.knob_raw(7, 1, shift=True); up.append((gval(25), led()))
    dn = []
    for _ in range(140): e.knob_raw(7, -1, shift=True); dn.append((gval(25), led()))
    out["up"], out["dn"] = up, dn
    e.knob_raw(7, 3, shift=True); out["multi"] = gval(25)                         # a turn of 3 = one click
    sval(25, 63 if 63 not in drums else 62); out["none"] = led()
    b20 = gval(20); e.knob_raw(4, 5); out["plain"] = gval(20) - b20                # another knob of the page
    sval(25, drums[1]); sval(22, 30)
    e.call(0x08033320, MGR, 23, maxins=900000); e.knob_raw(7, 1); e.call(0x0803381A, MGR, 23, maxins=900000)       # Clear + K8
    out["clear"] = (gval(25), gval(22))
    del e; gc.collect()
    return out


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    o = run(img, man, True)
    dr = o["drums"]
    zv = lambda p: -1 if p * 5 >> 7 == 0 else dr[(p * 5 >> 7) - 1]
    f, s = o["engine"]
    check(f & 5 == 5 and s & 5 == 4, f"MIDI 1: the granular engine (flags {f:#x}, nibble {s:#x}); the drums have the samples {dr}")
    v, l = o["first"]
    check(o["v0"] == 0 and v == dr[0] and l & 0xFF == COL[1], f"Shift + K8, one click from a sample no drum has: Drum 1's zone, its sample {v}, its colour ({l:#x})")
    p = 39; bad = []
    for i, (v, l) in enumerate(o["up"]):
        p = min(127, p + 1)
        if v != zv(p) or l & 0xFF != COL[p * 5 >> 7] or (l >> 8) - 2 != 48 + ((5 * p & 127) >> 1): bad.append(("up", i, p, v, hex(l)))
    for i, (v, l) in enumerate(o["dn"]):
        p = max(0, p - 1)
        if v != zv(p) or l & 0xFF != COL[p * 5 >> 7] or (l >> 8) - 2 != 48 + ((5 * p & 127) >> 1): bad.append(("dn", i, p, v, hex(l)))
    check(not bad, f"the travel, 100 clicks up and 140 down = the model (zones capture / Drum 1..4, the ends stop; the LED: the zone's colour, 48..111 along it) {bad[:3]}")
    check(o["dn"][-1][0] == -1 and o["up"][-1][0] == dr[3] and o["multi"] == -1, f"the top = Drum 4's sample ({o['up'][-1][0]}), the bottom = the capture (-1); a turn of 3 = one click ({o['multi']})")
    check(o["none"] == (0x01 | (16 + 2) << 8), f"a stored sample no drum has: dim white ({o['none']:#x})")
    check(o["plain"] != 0, f"another knob of the page moves as before ({o['plain']})")
    check(o["clear"] == (-1, V.DEFAULTS[21]), f"Clear + K8: the source = the capture, the plain layer at its default ({o['clear']})")
    gc.collect(); q = run(prev, prev_man, False)
    check(q["first"][0] == 1 and [v for v, l in q["up"][:3]] == [2, 3, 4], f"the previous build: one sample per click ({q['first'][0]}, {[v for v, l in q['up'][:3]]})")
    print("SC39.1 GRANULAR SOURCE RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
