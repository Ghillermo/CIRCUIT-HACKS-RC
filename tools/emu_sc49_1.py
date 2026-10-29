"""SC49.1 / Beta 3.46 / RC4.01 ARM tests: autorel.use_init() (a marked step = the lanes back to Project init), autorel.use_v3() (the knob LEDs
yellow on a previewed step; Clear + step = the step's knob automation erased) and tools/projinit.py (Shift + Preset = the voice back to Project
init), through the controller, the real LED task and the stock's automation playback (0x08031AFC, as emu_autorel drives it).

    python tools/emu_sc49_1.py BUILD.bin BUILD_manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]
  * init: Synth 1, macro 1 turned by hand away from the record's value, lane 0 = 100 at step 3, step 5 marked: steps 2..5 = the knob, 100, 100,
    the record's value (the previous build: the knob); MIDI 1 with the own engine on, the lane-4 code saved in the project's own-synth blocks
    (projsyn's c_ysput): step 5 = that value as a lane value; the blocks gone: the code's default (t_def);
  * v3 (with the labels): MIDI 1's Velocity view, Clear held + pad 4 = lanes 0..7 of step 4 erased, lane 9 and the step's 28 bytes kept, the
    press swallowed; the same with Clear then Shift held; Synth 1's Velocity view, Shift + a yellow step = knob LEDs 4 / 7 yellow with the
    values' brightness; Shift let go = not yellow, nothing previewed;
  * projinit (with the labels): Shift in Synth 1's views = Preset (LED 40) yellow, in the Mixer not; Shift + Preset in Synth 1 = macro 1 back to
    the record's value (the patch in use = the record's from byte 30 on, but persist19's bytes); MIDI 1 with the own engine on: the code back to
    the project's value; the blocks gone: back to the default.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402
import autorel as AR  # noqa: E402
import projinit as PI  # noqa: E402

V = T4.V
MGR = X.MGR
O = AR.MACRO_OBJ
USE = 0x20010044
CLEAR = 23


def harness(img, man):
    e = X.EP(img, man)
    R = man["report"]
    e.pat = lambda t: e.r0(int(R["vcf20"]["labels"]["c_sdpat"], 16), (t + 2) % 4)
    e.lanew = lambda t, k, s, v: e.uc.mem_write(e.pat(t) + 0x3A8 + 192 * k + 6 * s, bytes([v]) * 6)
    e.laner = lambda t, k, s: bytes(e.uc.mem_read(e.pat(t) + 0x3A8 + 192 * k + 6 * s, 6))
    e.b3 = lambda t, s: e.r8(e.pat(t) + 28 * s + 3)
    def mark(t, s): a = e.pat(t) + 28 * s + 3; e.uc.mem_write(a, bytes([e.r8(a) | 0x80]))
    e.mark = mark
    for t in (0, 2):
        for k in range(12):
            for s in range(32): e.lanew(t, k, s, 0xFF)
    e.rec = e.r32(AR.SESSION_OBJ + 0x14)
    e.g = lambda s, m: e.r0(V.GETTER, s, 174 + 17 * m)
    return e


def project_code(e, R, code, v):
    """the own synth of MIDI 1 gathered by projsyn, the code set to v, written into the record's blocks (the save's path), the RAM value as before"""
    ys = {k: int(x, 16) for k, x in R["projsyn"]["labels"].items()}
    e.call(ys["c_ysst"], maxins=200000)
    e.call(ys["c_ysrun"], 0, 0, maxins=40_000_000)
    img0 = 0x20045000 + 0x310
    e.uc.mem_write(img0 + AR.MPCODE + code, struct.pack("b", v))
    e.uc.mem_write(img0 + 40, bytes([sum(e.uc.mem_read(img0 + 4, 36)) & 0xFF]))      # mpatch's own sum of [4..39]
    e.call(ys["c_ysput"], 0, maxins=4_000_000)


def init_part(img, man, check, previous=False):
    e = harness(img, man)
    R = man["report"]
    def pget(st, i): e.call(0x0803542C, st, i, maxins=100000); return e.uc.reg_read(UC_ARM_REG_R0)
    def pset(st, i, v):
        e.call(0x080354FA, st, i, maxins=100000); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes([v])); e.call(0x080353C0, st, maxins=4_000_000)
    def step(t, s):
        sub = e.r32(e.r32(O + 0x38) + 4 * t)
        pset(e.r32(sub + 0xC), 1, s); pset(e.r32(sub + 0x28), 0, 1)
        e.call(0x08031AFC, O + 4, e.r32(sub + 0x28), 0, maxins=8_000_000)
    store = lambda t, k: e.r8(pget(e.r32(e.r32(O + 0x2C) + 4 * t), k))
    pv = e.r8(e.rec + AR.REC_SYN + AR.MACRO_REC)
    e.btn(0); e.knob(0, -30 if pv > 60 else 30)
    kp = e.g(0, 0)
    e.transport(1)
    e.lanew(0, 0, 2, 100); e.mark(0, 4)
    seq = []
    for s in (1, 2, 3, 4):
        step(0, s); seq.append(store(0, 0))
    want = pv if not previous else kp
    check(kp != pv and seq == [kp, 100, 100, want],
          f"Synth 1, macro 1 turned to {kp} (the record's {pv}); lane 0 = 100 at step 3, step 5 marked: steps 2..5 = {seq} (step 5 = {'the knob' if previous else 'Project init'} {want})")
    if previous:
        del e; gc.collect(); return
    # MIDI 1, the own engine on: lane 4's code in the project's own-synth blocks
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    row = bytes(e.uc.mem_read(e.r0(e.vl["c_vrow"], 0), 8)); code = row[4]
    v_now = e.val(0, code)
    pj = 20 if v_now != 20 else 30
    project_code(e, R, code, pj)
    u_pj = e.r0(e.vl["c_vtou"], code, pj & 0xFFFFFFFF)
    e.lanew(2, 4, 2, 120); e.mark(2, 4)
    vals = []
    for s in (2, 3, 4):
        step(2, s); vals.append(store(2, 4))
    check(vals == [120, 120, u_pj], f"MIDI 1 (code {code}, now {v_now}, saved {pj}): steps 3..5 = {vals} (step 5 = the project's, {u_pj})")
    blk0 = e.rec + AR.PJ_BLK0
    e.uc.mem_write(blk0, b"\x00")                                                 # no project data
    tdef = struct.unpack("b", bytes([e.r8(e.vl["t_def"] + code)]))[0]
    u_def = e.r0(e.vl["c_vtou"], code, tdef & 0xFFFFFFFF)
    vals = []
    for s in (2, 3, 4):
        step(2, s); vals.append(store(2, 4))
    check(vals[-1] == u_def, f"MIDI 1, the project without its blocks: step 5 = the default ({vals}, t_def {tdef} -> {u_def})")
    del e; gc.collect()


def v3_part(img, man, check):
    e = harness(img, man)
    # Clear + step in MIDI 1's Velocity view
    e.btn(2); e.btn(10)
    check(e.r8(MGR + 0x152) == 9 * 2 + 2, f"MIDI 1's Velocity view (subview {e.r8(MGR + 0x152)})")
    for k in (0, 5, 9): e.lanew(2, k, 3, 50 + k)
    sb = bytes(e.uc.mem_read(e.pat(2) + 28 * 3, 28))
    e.call(0x08033320, MGR, CLEAR, maxins=8_000_000); e.pad(3); e.call(0x0803381A, MGR, CLEAR, maxins=8_000_000)
    after = [e.laner(2, k, 3) for k in range(12)]
    sa = bytes(e.uc.mem_read(e.pat(2) + 28 * 3, 28))
    check(all(after[k] == b"\xff" * 6 for k in range(8)) and after[9] == bytes([59]) * 6 and sa == sb,
          f"Clear + pad 4: lanes 0..7 of step 4 erased ({[a.hex() for a in after[:8:5]]}), lane 9 kept ({after[9].hex()}), the step's notes kept ({sa == sb})")
    for k in (1, 7): e.lanew(2, k, 5, 30 + k)
    e.call(0x08033320, MGR, CLEAR, maxins=8_000_000); e.shift(True); e.pad(5); e.shift(False); e.call(0x0803381A, MGR, CLEAR, maxins=8_000_000)
    check(e.laner(2, 1, 5) == b"\xff" * 6 and e.laner(2, 7, 5) == b"\xff" * 6 and not e.b3(2, 5) & 0x80,
          f"Clear, then Shift + pad 6: erased too, no mark ({e.b3(2, 5):#x})")
    # Synth 1's Velocity view: Shift + a yellow step = the knob LEDs
    e.btn(0); e.btn(10)
    e.lanew(0, 3, 2, 77); e.lanew(0, 6, 2, 20)
    e.shift(True); e.pad(2); f = X.frame(e)
    k4, k7, k1 = f[AR.KNOB_LED0 + 3], f[AR.KNOB_LED0 + 6], f[AR.KNOB_LED0]
    check(k4 == AR.COL_AV | 79 << 8 and k7 == AR.COL_AV | 22 << 8 and k1 & 0xFF != AR.COL_AV and e.r8(AR.PVM) == 1 and e.r8(AR.PVM + 1) == 2,
          f"Synth 1, Shift + pad 3: knob LEDs 4 / 7 yellow ({k4:#06x} {k7:#06x}), knob 1 not ({k1:#06x}); previewed {e.r8(AR.PVM)} / {e.r8(AR.PVM + 1)}")
    e.shift(False); f = X.frame(e)
    check(f[AR.KNOB_LED0 + 3] & 0xFF != AR.COL_AV and e.r8(AR.PVM) == 0, f"Shift let go: knob 4 not yellow ({f[AR.KNOB_LED0 + 3]:#06x}), nothing previewed")
    del e; gc.collect()


def projinit_part(img, man, check):
    e = harness(img, man)
    R = man["report"]
    e.btn(0)
    e.shift(True); f = X.frame(e); e.shift(False)
    y_syn = f[PI.LED_PRESET]
    e.btn(14); e.shift(True); f = X.frame(e); e.shift(False)
    y_mix = f[PI.LED_PRESET]
    check(y_syn == PI.COL_SHIFT and y_mix != PI.COL_SHIFT, f"Shift: Preset yellow in Synth 1's view ({y_syn:#x}), not in the Mixer ({y_mix:#x})")
    pv = e.r8(e.rec + AR.REC_SYN + AR.MACRO_REC)
    e.btn(0); e.knob(0, -30 if pv > 60 else 30); kp = e.g(0, 0)
    e.shift(True); e.btn(8); e.shift(False)
    g1 = e.g(0, 0)
    use = bytes(e.uc.mem_read(USE + 30, 300)); recb = bytes(e.uc.mem_read(e.rec + AR.REC_SYN + 30, 300))
    diff = [i + 30 for i in range(300) if use[i] != recb[i]]
    check(kp != pv and g1 == pv and len(diff) <= 22, f"Synth 1: macro 1 {kp} -> Shift + Preset -> {g1} (the record's {pv}); the patch in use = the record's but {diff}")
    # MIDI 1 with the own engine on
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    row = bytes(e.uc.mem_read(e.r0(e.vl["c_vrow"], 0), 8)); code = row[4]
    v_now = e.val(0, code); pj = 20 if v_now != 20 else 30
    project_code(e, R, code, pj)
    check(e.val(0, code) == v_now, f"MIDI 1: the code {code} still {e.val(0, code)} after the blocks were written")
    e.btn(2); e.shift(True); e.btn(8); e.shift(False)
    check(e.val(0, code) == pj, f"MIDI 1: Shift + Preset = the code {code} back to the project's {pj} (now {e.val(0, code)})")
    e.uc.mem_write(e.rec + AR.PJ_BLK0, b"\x00")
    tdef = struct.unpack("b", bytes([e.r8(e.vl["t_def"] + code)]))[0]
    e.uc.mem_write(e.r0(e.vl["c_vvaddr"], 0, code), struct.pack("b", tdef + 9))
    e.shift(True); e.btn(8); e.shift(False)
    check(e.val(0, code) == tdef, f"MIDI 1, the project without its blocks: Shift + Preset = the default ({e.val(0, code)} = {tdef})")
    del e; gc.collect()


def main(img, man, prev=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m)
        if not c: fails += 1
    labels = set()
    for mod in ("autorel", "projinit"):
        labels |= set(man["report"].get(mod, {}).get("labels", {}))
    init_part(img, man, check)
    if "c_arkled" in labels: v3_part(img, man, check)
    if "c_pibtn" in labels: projinit_part(img, man, check)
    if prev:
        print("-- the previous build")
        init_part(*prev, check, previous=True)
    name = man.get("name", "?")
    print(f"{name} ARM RESULT: {'ALL PASS' if not fails else f'{fails} FAILURES'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    img = open(a[0], "rb").read(); man = json.load(open(a[1]))
    prev = (open(a[2], "rb").read(), json.load(open(a[3]))) if len(a) >= 4 else None
    sys.exit(1 if main(img, man, prev) else 0)
