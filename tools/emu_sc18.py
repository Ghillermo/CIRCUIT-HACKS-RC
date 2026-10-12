"""SC18 ARM tests: chromatic drum pitch recorded only on its own step; drum knob controls (ARM side).

    python tools/emu_sc18.py SC17.8.bin SC18.bin SC18_manifest.json
Drives the real paths: drum Preset view pad handler (vtable 0x0805ABBC slot 0, SC08/SC11 chromatic press) -> setter ->
recorder gate -> 0x0803FC20, then the recorder's step listener 0x0803FE24 (the sequencer step store [rec+0x30]).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc08 import E8, VIEWS, DP_VT, MGR  # noqa: E402
import drums18 as K  # noqa: E402
import drums_dsp as DD  # noqa: E402
import build_sc14 as s14  # noqa: E402

GATE = 0x2003C168                     # automation recorder gate (from the dump)
STEP_LISTENER = 0x0803FE24


class E18(E8):
    def __init__(self, image):
        super().__init__(image)
        self.stubs.pop(0x0803FC20, None)                    # the real recorder, not the stub
        self.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1),
                         begin=0x0801BE78, end=0x0801BE78)   # sleep(): the emulated clock never advances
        self.writes = []
        def hw(uc, a, s, d):
            self.writes.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R3)))
        self.uc.hook_add(UC_HOOK_CODE, hw, begin=0x08040188, end=0x08040188)

    def rec(self, d): return self.r32(GATE + 0xC + 4 * (4 + d))
    def press(self, d, pad):
        fn = struct.unpack("<I", bytes(self.uc.mem_read(DP_VT, 4)))[0]
        self.call(fn & ~1, VIEWS[d], pad, 100, maxins=20000000)
    def step(self, d):
        self.writes.clear(); r = self.rec(d)
        self.call(STEP_LISTENER, r, self.r32(r + 0x30), 0, maxins=4000000)
        return [w for w in self.writes if w[0] == 0]                     # Pitch lane


def main(prev, img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    for d in range(4):
        res = {}
        for name, image in (("prev", prev), ("sc18", img)):
            gc.collect()
            e = E18(image); e.recording(True); e.setflag(VIEWS[d], True)
            e.press(d, 0x13); s = [e.step(d) for _ in range(3)]
            e.press(d, 0x15); s += [e.step(d) for _ in range(2)]
            res[name] = s
        v1, v2 = res["sc18"][0], res["sc18"][3]
        check(len(v1) == 1 and v1[0][1] != 0xFF and len(v2) == 1 and v2[0][1] not in (0xFF, v1[0][1]),
              f"drum {d+1} chromatic: each press recorded on its step ({v1}, {v2})")
        check(all(x == [] for i, x in enumerate(res["sc18"]) if i not in (0, 3)),
              f"drum {d+1} chromatic: nothing written on the following steps {res['sc18']}")
        check(all(x == [(0, 0xFF)] for i, x in enumerate(res["prev"]) if i not in (0, 3)),
              f"drum {d+1} SC17.8: the following steps were erased (0xFF) — the bug {res['prev']}")
    # not chromatic: same as SC17.8 (pitch set by the stock path is not involved; a touched lane keeps stock behaviour)
    res = {}
    for name, image in (("prev", prev), ("sc18", img)):
        gc.collect()
        e = E18(image); e.recording(True); e.setflag(VIEWS[0], True)
        e.press(0, 0x13); e.setflag(VIEWS[0], False)                   # lane touched, then chromatic mode off
        res[name] = [e.step(0) for _ in range(3)]
    check(res["sc18"] == res["prev"], f"chromatic mode off: identical to SC17.8 {res['sc18']}")
    knob_tests(prev, img, man, check)
    print("SC18 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


def knob_tests(prev, img, man, check):
    import drums2_dsp as DD2
    v2 = man["marker"] != "SC18"
    MAP = K.MAP2 if v2 else K.MAP1
    DDm = DD2 if v2 else DD
    L = {k: int(v, 16) for k, v in man["report"]["sc18"]["labels"].items()}
    import struct
    from thumb import bl as bl_enc, b_w
    B = 0x08010000
    check(struct.unpack_from("<I", img, K.MH_SLOT4 - B)[0] == L["c_dk18"] | 1, "drum macro handler slot 4 -> c_dk18")
    check(img[K.MH_CTOR_BL - B:K.MH_CTOR_BL - B + 4] == bl_enc(K.MH_CTOR_BL, L["c_mhinit"]), "constructor bl 0x0801A7E4 -> c_mhinit")
    fx = int(man["report"]["sc17"]["labels"]["c_fxtick"], 16)
    check(img[s14.SVC_HOOK - B:s14.SVC_HOOK - B + 4] == b_w(s14.SVC_HOOK, L["c_dtick"]) and L["svc_next"] == fx,
          f"DSP service chain: c_dtick first, then SC17's c_fxtick {hex(fx)}")

    def setup(image, d):
        gc.collect()
        e = E18(image)
        for v in VIEWS: e.uc.mem_write(v + 0x51, b"\x00\x00\x00")
        e.call(0x08033320, MGR, 4 + d, maxins=600000)                         # select drum d (track button)
        e.mh = [e.r32(e.r32(e.r32(e.r32(e.r32(0x200069E4) + 0x40) + 0x2C) + 0x158 + 4 * k)) and
                e.r32(e.r32(e.r32(e.r32(0x200069E4) + 0x40) + 0x2C) + 0x158 + 4 * k) for k in range(4)]
        for o in e.mh: e.uc.mem_write(o + K.O_EXT, b"\x00"); e.uc.mem_write(o + K.O_FLAGS, b"\x00\x00")   # constructor hook
        return e
    def knob(e, k, delta, shift=False):
        log = []
        def h(uc, a, s_, d_):
            if a == 0x08031A98: log.append(("param", uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2)))
            elif a == 0x0803BDCC: log.append(("mark", uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)))
        hk = e.uc.hook_add(UC_HOOK_CODE, h)
        if shift: e.set_p0(e.r32(MGR + 0xC), 1)
        e.call(0x08033848, MGR, k, delta & 0xFFFFFFFF, maxins=900000)
        if shift: e.set_p0(e.r32(MGR + 0xC), 0)
        e.uc.hook_del(hk); return log
    def st(e, d):
        o = e.mh[d]; f = e.r8(o + K.O_FLAGS); dl_ = e.r8(o + K.O_DELTA)
        return dict(code=f & 15, tag=f >> 7, dirty=(f >> 6) & 1, delta=dl_ - 256 if dl_ > 127 else dl_, ext=e.r8(o + K.O_EXT))
    def macro(e, d, m):
        e.call(0x0803542C, e.r32(e.mh[d] + 0xC), m); return e.r8(e.uc.reg_read(UC_ARM_REG_R0))
    chk = check
    for d in range(4):
        e = setup(img, d)
        log = knob(e, 0, 3) + knob(e, 0, 2)
        c0 = MAP["plain"][0]
        chk(st(e, d)["code"] == c0 and st(e, d)["delta"] == 5 and log == [], f"drum {d+1} K1 +3 +2: pending code {c0} +5, no parameter write {st(e, d)}")
        knob(e, 2, -1)
        chk(st(e, d)["code"] == MAP["plain"][2] and st(e, d)["delta"] == -1, f"drum {d+1} K3 -1 replaces the unsent K1 message {st(e, d)}")
        knob(e, 4, 1); chk(st(e, d)["code"] == MAP["plain"][4], f"K5 -> code {MAP['plain'][4]}")
        knob(e, 6, -70); knob(e, 6, -70); chk(st(e, d)["code"] == MAP["plain"][6] and st(e, d)["delta"] == -100, f"K7 -> code {MAP['plain'][6]}, delta clamped to -100 {st(e, d)}")
        for k, code in sorted(MAP["shift"].items()):
            log = knob(e, k, 4, shift=True)
            chk(st(e, d)["code"] == code and st(e, d)["delta"] == 4 and log == [], f"Shift + K{k+1} -> code {code}, no parameter write")
        # extended ranges K4 / K6: turn left until the stock value is 0, then the counter; right: counter first
        for k, m, sh in ((3, 1, 0), (5, 2, 4)):
            e = setup(img, d)
            v0 = macro(e, d, m)
            steps = 0
            while macro(e, d, m) > 0 and steps < 200: knob(e, k, -1); steps += 1
            ext0 = st(e, d)["ext"]
            log = knob(e, k, -1) + knob(e, k, -3)
            s_ = st(e, d)
            chk(macro(e, d, m) == 0 and ((s_["ext"] >> sh) & 15) == 4 and s_["dirty"] and not [x for x in log if x[0] == "param"] and ext0 == 0,
                f"drum {d+1} K{k+1}: stock {v0} -> 0 in {steps} clicks, then 4 clicks left -> extended {(s_['ext'] >> sh) & 15}, no parameter write")
            knob(e, k, -40); chk(((st(e, d)["ext"] >> sh) & 15) == 15, "extended value clamps at 15")
            knob(e, k, 10); log = knob(e, k, 3)
            chk(((st(e, d)["ext"] >> sh) & 15) == 2 and macro(e, d, m) == 0 and not [x for x in log if x[0] == "param"], "right turn: the extended value comes back first (15 -> 2)")
            log = knob(e, k, 5)
            chk(((st(e, d)["ext"] >> sh) & 15) == 0 and macro(e, d, m) == 0, "right turn past the extended range: stops at 0 (the rest of that click is dropped)")
            knob(e, k, 2); chk(macro(e, d, m) == 2, f"then the stock value moves again ({macro(e, d, m)})")
    # other knobs / Shift turns: exactly as SC17.8
    others = [(1, False), (1, True), (7, False), (3, False), (5, False)] + [(k, True) for k in (0, 2, 6) if k not in MAP["shift"]]
    for k, sh in others:
        e = setup(img, 1); ep = setup(prev, 1)
        if k in (3, 5) and not sh:
            a, b = knob(e, k, 2), knob(ep, k, 2)
        else:
            a, b = knob(e, k, -3, sh), knob(ep, k, -3, sh)
        chk(a == b, f"K{k+1}{' + Shift' if sh else ''}: same writes as SC17.8 {a}")
    # service tick: pending message -> DSP mailbox, extended values -> X:DB+2; then the previous chain head
    e = setup(img, 2)
    knob(e, 0, -7); knob(e, 3, -1)                                             # K1 -7 ; K4 at 0? (decay may be > 0)
    o = e.mh[2]; e.uc.mem_write(o + K.O_EXT, bytes([0x5A])); e.uc.mem_write(o + K.O_FLAGS, bytes([e.r8(o + K.O_FLAGS) | 0x40]))
    dw, chain = [], []
    def h(uc, a, s_, d_):
        if a == 0x080292F8:
            dw.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1) >> 8, uc.reg_read(UC_ARM_REG_R2)))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        elif a == L["svc_next"]:
            chain.append(1); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, h)
    e.call(L["c_dtick"], maxins=900000)
    mb = DDm.DB + 2 * DDm.STRIDE
    c0 = MAP["plain"][0]
    chk(dw == [(0, (1 << 23) | (c0 << 16) | ((-7) & 0xFFFF), mb), (0, 0x5A, mb + DDm.EXT)] and chain == [1],
        f"service tick: drum 3 mailbox = tag 1, code {c0}, delta -7; extended 0x5A; then the previous head {[(a, hex(v), hex(ad)) for a, v, ad in dw]}")
    s_ = st(e, 2)
    chk(s_["code"] == 0 and s_["delta"] == 0 and s_["tag"] == 1 and not s_["dirty"], f"pending cleared, tag kept for the next message {s_}")
    dw.clear(); chain.clear(); e.call(L["c_dtick"], maxins=900000)
    chk(dw == [] and chain == [1], "next tick with nothing pending: no DSP write")
    knob(e, 2, 5); dw.clear(); e.call(L["c_dtick"], maxins=900000)
    chk(dw == [(0, (0 << 23) | (MAP["plain"][2] << 16) | 5, mb)], f"next message toggles the tag back to 0 {[(hex(v)) for _, v, _ in dw]}")
    # constructor hook
    e = setup(img, 0); o = e.mh[0]
    e.uc.mem_write(o + K.O_EXT, b"\x77"); e.uc.mem_write(o + K.O_FLAGS, b"\x88\x99")
    seen = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d_: (seen.append(1), uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)),
                  begin=K.MH_CTOR_FN, end=K.MH_CTOR_FN)
    e.uc.reg_write(UC_ARM_REG_R7, o); e.call(L["c_mhinit"], o + 0x36, 4)
    chk(seen == [1] and e.r8(o + K.O_EXT) == 0 and e.r8(o + K.O_FLAGS) == 0 and e.r8(o + K.O_DELTA) == 0,
        "constructor hook: stock call kept, padding bytes +0x31 / +0x3E / +0x3F zeroed")


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes(), json.loads(Path(sys.argv[3]).read_text())) else 0)
