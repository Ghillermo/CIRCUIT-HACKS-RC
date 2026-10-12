"""SC39.5 ARM tests (live RAM dump; the LED task from its caller: the raw LED halfwords of the frame): the type knobs as colours (tools/typeleds.py)
and the steady dim white.

    python tools/emu_sc39_5.py SC39.5.bin SC39.5_manifest.json SC39.4.bin SC39.4_manifest.json
  * a drum track, Shift held: K5 = the colour of the filter mode (5 modes) at full brightness, K8 = the colour of the distortion type (4 types);
    the other knob LEDs as the previous build; without Shift: every LED as the previous build;
  * MIDI 1 with the granular engine on its page, Shift held: K6 = the colour of the note mode (pitch / slicer / stretch); the other LEDs as before;
    another engine or another page: as before;
  * the image: outside the new code only the dim white changes (0x03 -> 0x02, a steady code).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R4
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc39_4 as T4  # noqa: E402
from emu_sc35 import MGR  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
import emu_sc19_6 as T196  # noqa: E402
import persist19 as P  # noqa: E402
import typeleds as TL  # noqa: E402

V = T4.V
B = 0x08010000
FULL = TL.FULL


def drums(img, man):
    e = T196.E196(img, man); out = {}
    d = 1; e.track(4 + d)
    for sh in (0, 1):
        e.set_p0(e.r32(MGR + 0xC), sh)
        for m in range(5):
            e.setcode(d, 9, m); out[("f", sh, m)] = e.frame()[60:68]
        for t in range(4):
            for k in range(2):
                i, mask = P.XT_BITS[3 * d + k]; a = e.xa(i); v = e.r8(a); e.uc.mem_write(a, bytes([(v | mask) if t >> k & 1 else (v & ~mask)]))
            out[("d", sh, t)] = e.frame()[60:68]
    del e; gc.collect(); return out


def gran(img, man):
    e = T4.E4(img, man); e.setup(man); out = {}
    def knobs():
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR)
        e.call(0x08033B3E, maxins=8_000_000)
        return list(struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138))))[60:68]
    vals = [0] * 26
    e.btn(2); e.btn(8)
    for name, flags in (("gran", 0b1011), ("osc", 0b0011)):
        for page in (1, 0):
            e.set_engine(0, flags, 0, vals, [0] * 8); e.pad(page)                 # (the page pads are the engine's only with the mode on)
            for nm in range(3):
                vals[25] = nm; e.set_engine(0, flags, 0, vals, [0] * 8)
                for sh in (0, 1):
                    e.set_p0(e.r32(MGR + 0xC), sh); out[(name, page, nm, sh)] = knobs()
                e.set_p0(e.r32(MGR + 0xC), 0)
    del e; gc.collect(); return out


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["typeleds"]["labels"].items()}
    w = lambda a: struct.unpack_from("<I", img, a - B)[0]
    start = int(man["report"]["typeleds"]["arm_start"], 16) - B
    check(w(TL.MH_SLOT7) == L["c_tdleds"] | 1 and w(TL.AC64_SLOT7) == L["c_tgleds"] | 1, "the hooks: slot 7 of the drum macro handlers and of the note tracks' macro handlers")
    diff = [i for i in range(min(start, len(prev))) if img[i] != prev[i] and not (0x1C8 <= i < 0x1C8 + 0x26) and i not in range(TL.MH_SLOT7 - B, TL.MH_SLOT7 - B + 4) and i not in range(TL.AC64_SLOT7 - B, TL.AC64_SLOT7 - B + 4)]
    if "sesscopy" in man["report"]: print("      (a later build: it patches more of the stock image; the image comparison is SC39.5's own)")
    else: check(0 < len(diff) <= 8 and all((prev[i], img[i]) == (3, 2) for i in diff), f"outside the new code, the version block and the two slots: only the dim white 0x03 -> 0x02 ({len(diff)} bytes)")
    n, o = drums(img, man), drums(prev, prev_man)
    ok_f = all(n[("f", 1, m)][TL.POS_FMODE] == FULL | TL.COL_FMODE[m] and [x for k, x in enumerate(n[("f", 1, m)]) if k != TL.POS_FMODE and k != TL.POS_DTYPE] ==
               [x for k, x in enumerate(o[("f", 1, m)]) if k != TL.POS_FMODE and k != TL.POS_DTYPE] for m in range(5))
    check(ok_f and len({n[("f", 1, m)][TL.POS_FMODE] for m in range(5)}) == 5, f"drums, Shift: K5 = the colour of the filter mode ({[hex(n[('f', 1, m)][TL.POS_FMODE]) for m in range(5)]}; before {[hex(o[('f', 1, m)][TL.POS_FMODE]) for m in range(5)]}); the other LEDs as before")
    check(all(n[("d", 1, t)][TL.POS_DTYPE] == FULL | TL.COL_DTYPE[t] for t in range(4)), f"drums, Shift: K8 = the colour of the distortion type ({[hex(n[('d', 1, t)][TL.POS_DTYPE]) for t in range(4)]}; before {[hex(o[('d', 1, t)][TL.POS_DTYPE]) for t in range(4)]})")
    check(all(n[k] == o[k] for k in n if k[1] == 0), "drums without Shift: every knob LED as the previous build")
    gc.collect(); g, h = gran(img, man), gran(prev, prev_man)
    P6 = TL.POS_NMODE
    check(all(g[("gran", 1, nm, 1)][P6] == FULL | TL.COL_NMODE[nm] and g[("gran", 1, nm, 1)][:P6] + g[("gran", 1, nm, 1)][P6 + 1:] == h[("gran", 1, nm, 1)][:P6] + h[("gran", 1, nm, 1)][P6 + 1:] for nm in range(3)),
          f"granular page, Shift: K6 = the colour of the note mode ({[hex(g[('gran', 1, nm, 1)][P6]) for nm in range(3)]}; before {[hex(h[('gran', 1, nm, 1)][P6]) for nm in range(3)]}); the other LEDs as before")
    check(all(g[k] == h[k] for k in g if not (k[0] == "gran" and k[1] == 1 and k[3] == 1)), "without Shift, on another page or with the oscillator engine: as the previous build")
    print("SC39.5 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
