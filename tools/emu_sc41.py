"""SC41 / RC0.8 ARM tests: the pitch knobs of the step-drummer keep their value (vcf21.use_sdknobfix).

    python tools/emu_sc41.py NEW.bin NEW_manifest.json PREVIOUS.bin PREVIOUS_manifest.json
  * MIDI 1 with its own engine, the step-drummer view open (pad 30), knob 1 through the controller (0x08033848): an empty pair starts at the
    middle (64) and every event adds its delta; the knob LED follows; the previous build wrote only the delta of each event;
  * the FX sequencer's selector knob as before (one unit every three events).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R4
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import MGR  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
import emu_sc40_9 as T9  # noqa: E402


def knobs(img, man):
    import emu_sc36_1 as T361
    V = T361.V
    e = T361.E20(img, man)
    for _ in range(30): e.vtick()
    pad = lambda p: (e.padr(p), e.rel(p))
    def r0(fn, *a): e.call(fn, *a); return e.uc.reg_read(UC_ARM_REG_R0)
    def led():
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR); e.call(0x08033B3E, maxins=40_000_000)
        return struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138)))[60] >> 8
    e.btn(2); e.track(2); e.btn(8)
    for _ in range(2): pad(V.PAD_OSC)
    pad(V.PAD_SD)
    pat = r0(e.vl["c_sdpat"], 0); h0 = r0(e.vl["c_sdhalf"], 0)
    lane = lambda: e.r8(r0(e.vl["c_sdlna"], pat, h0))
    seq, leds = [lane()], [led()]
    for d in (5, 5, -3, 100, -127, -127, 1):
        e.call(0x08033848, MGR, 0, d & 0xFFFFFFFF, maxins=6_000_000); seq.append(lane()); leds.append(led())
    del e; gc.collect()
    return seq, leds


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    seq, leds = knobs(img, man)
    gc.collect(); pseq, pleds = knobs(prev, prev_man)
    check(seq == [255, 69, 74, 71, 127, 0, 0, 1] and pseq == [255, 5, 5, 0, 100, 0, 0, 1], f"the pitch knob of a pair through the controller: from the middle, every event adds, limited to 0..127 ({seq}); the previous build: only the delta ({pseq})")
    check(len(set(leds[1:5])) == 4 and leds[4] > leds[1], f"its LED follows the value ({[hex(x) for x in leds]})")
    fsq, step, s2 = T9.seq_part(img, man)
    check(fsq == 1 and step == 7 and s2 == [0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 5, 0, 0], f"the FX sequencer: its own track, its selector knob as before ({s2})")
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
