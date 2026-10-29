"""SC48.7 (vcf21.use_edlock; issue #15): no CC editor while the track's own synth is on.

    python tools/emu_edlock.py BUILD.bin manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]

Through the controller (emu_lazysave's harness: the LED task, the clock), MIDI 2's Preset view:
  * own synth off: pad 25 lit (dim magenta), a press opens the editor; K1 turned to CC 26 and the Save pad: K1 sends CC 26;
  * own synth on (the oscillator, from the engine row): pad 25 dark; a press does nothing (the editor stays closed); K1 sends the own synth's
    CC (73), before and after;
  * the editor open with the own synth off, K1 changed, then the own synth switched on: the next LED frame leaves the editor and the change is
    discarded (the template's K1 back to its CC);
  * vcf21.use_vellock: in the FX sequencer (engine row 6) pad 31 dark and a press leaves the engine as it was (the previous build: lit, and a
    press turned it into the sample mode); in the VA-drum (row 3) pad 31 dim, a press = bright (velocity on);
  * modesel.use_vdfix: the VA-drum with pad 31 on = the engine row shows the VA-drum chosen (the previous build: the granular);
  * the previous build (expected): with the own synth on, pad 25 lit and a press opens the editor.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R2, UC_ARM_REG_R3
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import vcf21 as V  # noqa: E402
import modesel as MS  # noqa: E402

MGR, KNOB = 0x20040B10, 0x08033848
OSC_ROW = 1                                           # the engine row: pad 17 = none, pad 18 = the oscillator


def run(img, man):
    vl = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
    e = T.EL(img)
    def skip(uc, a, s, d): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, skip, begin=0x0803C920, end=0x0803C920)
    ccs = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: ccs.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3))),
                  begin=V.CC_HELPER, end=V.CC_HELPER)
    e.at(100000); e.transport(0)
    def tick(ms=20): e.at(e.t + ms); e.call(vl["c_vtick"], maxins=3_000_000); e.leds()
    def frame():
        e.leds()
        return [x & 0xFF for x in struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138)))]
    def knob(k, d=1):
        ccs.clear(); e.call(KNOB, MGR, k, d, maxins=8_000_000); tick(); return ccs[0][1] if ccs else None
    def engine(row): e.pad(26); e.pad(MS.ROW + row); e.pad(26)
    ed = lambda: e.r8(V.TAIL + V.O_ED)
    for _ in range(20): tick()
    e.btn(3); e.btn(8)
    for _ in range(5): tick()
    base = e.r32(e.r32(V.SETOBJ - 4) + 0xC)
    k1 = lambda: e.r8(base + 0x28 + 4)
    o = {}
    # ---- own synth off
    o["off_led"] = frame()[V.PAD_CC]
    e.pad(V.PAD_CC); tick(); o["off_open"] = ed()
    for _ in range(26): knob(0)
    e.pad(V.PAD_SAVE); tick()
    o["off_saved"] = (ed(), k1(), knob(0))
    # ---- own synth on
    engine(OSC_ROW)
    for _ in range(5): tick()
    o["on_led"] = frame()[V.PAD_CC]
    o["on_k1"] = knob(0)
    e.pad(V.PAD_CC); tick(); tick()
    o["on_open"] = ed(); o["on_led2"] = frame()[V.PAD_CC]; o["on_k1b"] = knob(0)
    if ed(): e.pad(V.PAD_CC); tick()                  # (the previous build) closed again
    # ---- own synth off, the editor open with a change, then the own synth on
    engine(0)
    for _ in range(5): tick()
    cc0 = k1()
    e.pad(V.PAD_CC); tick(); knob(0); knob(0); knob(0)
    o["pend"] = (ed(), k1())
    engine(OSC_ROW); tick(); tick()
    o["left"] = (ed(), k1(), cc0)
    # ---- pad 31: the FX sequencer, then the VA-drum
    def rowsel():
        e.pad(26); tick(); f = frame(); e.pad(26); tick()
        return [k for k in range(7) if f[MS.ROW + k] == MS.COLS[k][0]]
    if ed(): e.pad(V.PAD_CC); tick()                  # (the previous build: the editor still open) closed
    engine(6)
    for _ in range(3): tick()
    f = frame(); o["fx31"] = f[30]; e.pad(30); tick(); tick(); o["fx31_after"] = (rowsel(), frame()[26])
    engine(3)
    for _ in range(3): tick()
    o["vd31"] = frame()[30]; e.pad(30); tick(); tick(); o["vd31_on"] = frame()[30]; o["vd_row"] = rowsel()
    del e; gc.collect()
    return o


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    o = run(Path(img).read_bytes(), man)
    check(o["off_led"] == V.COL_CC[1] and o["off_open"] & 0x80, f"own synth off: pad 25 lit ({o['off_led']:#x}), a press opens the editor ({o['off_open']:#x})")
    st, cc, sent = o["off_saved"]
    check(st == 0 and cc == 26 and sent == 26, f"own synth off: K1 to CC {cc}, the Save pad (editor state {st:#x}): K1 sends CC {sent}")
    pst, pcc = o["pend"]
    lst, lcc, cc0 = o["left"]
    check(pst & 0x40 and pcc != cc0 and lst == 0 and lcc == cc0,
          f"editor open with a change ({pcc} from {cc0}), the own synth switched on: the editor left ({lst:#x}), the change discarded ({lcc})")
    check(o["on_led"] == 0 and o["on_led2"] == 0, f"own synth on: pad 25 dark ({o['on_led']:#x} / {o['on_led2']:#x})")
    check(o["on_open"] == 0, f"own synth on: a press of pad 25 does nothing (editor state {o['on_open']:#x})")
    check(o["on_k1"] == 73 and o["on_k1b"] == 73, f"own synth on: K1 sends the own synth's CC ({o['on_k1']} / {o['on_k1b']})")
    check(o["fx31"] == 0 and o["fx31_after"][0] == [6], f"FX sequencer: pad 31 dark ({o['fx31']:#x}), a press leaves the engine (row {o['fx31_after'][0]})")
    check(o["vd31"] == V.COL_VEL[1] and o["vd31_on"] == V.COL_VEL[0], f"VA-drum: pad 31 dim ({o['vd31']:#x}), a press = on ({o['vd31_on']:#x})")
    check(o["vd_row"] == [3], f"VA-drum with pad 31 on: the engine row shows the VA-drum (row {o['vd_row']})")
    if prev:
        p = run(Path(prev).read_bytes(), pman)
        check(p["fx31"] != 0 and p["fx31_after"][0] == [5], f"the previous build: FX sequencer pad 31 lit ({p['fx31']:#x}), a press = the sample mode (row {p['fx31_after'][0]})")
        check(p["vd_row"] == [4], f"the previous build: VA-drum with pad 31 on shown as the granular (row {p['vd_row']})")
        check(p["on_led"] != 0 and p["on_open"] & 0x80, f"the previous build: with the own synth on, pad 25 lit ({p['on_led']:#x}) and the editor opens ({p['on_open']:#x})")
    print(f"{Path(img).stem} EDLOCK RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text()), a[2] if len(a) > 2 else None,
                       json.loads(Path(a[3]).read_text()) if len(a) > 3 else None) else 0)
