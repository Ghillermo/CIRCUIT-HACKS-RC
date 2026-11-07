"""SC52.8 ARM tests (oscmod.use_solo, rowswap.use_fmov): the one-oscillator mode's own knobs, through the controller and the real LED task.

    python tools/emu_osc1x.py SC52.8.bin manifest.json

  * one oscillator, OSC 1's page: K5 = the sub's level, Shift + K5 = env -> sub, K6 = the noise's level, Shift + K6 = env -> noise, K8 = LFO ->
    sub, Shift + K8 = LFO -> noise; their own bytes (the two-oscillator depths untouched); the levels from off (-64);
  * the LEDs: K5 (a level) brightness = level + 1 in the track's colour;
  * Clear held + K5 = the level off;
  * the tick: each value once to OM_T + 48 t + 8.. (the levels as 0..127), track 1 (not in the mode) zeros;
  * two oscillators on: K5 = LFO / env -> FM again (oscmod's depth), the tick sends track 0's one-oscillator words as zeros;
  * the patch: c_omgath writes 0xC5, the 6 values, the check at padding + 142; c_omappl brings them back; a patch without = levels off, depths 0.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R5, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402
import oscmod as OM  # noqa: E402
import packio as PK  # noqa: E402
import mpatch as MP  # noqa: E402

V = T4.V
MGR = X.MGR
CLEAR = 23


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    OM.use_solo()
    e = X.EP(img, man)
    R = man["report"]
    ol = {k: int(v, 16) for k, v in {**R["oscmod"]["labels"], **R["oscmod2"]["labels"]}.items()}
    om_t = 0x5400
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    e.btn(2); e.btn(8); e.pad(1)
    sv = lambda t=0: [int.from_bytes(bytes([b]), "little", signed=True) for b in e.uc.mem_read(OM.SOLR + 4 + 6 * t, 6)]
    dep = lambda t=0: [int.from_bytes(bytes([b]), "little", signed=True) for b in e.uc.mem_read(OM.OMR + 4 + 6 * t, 6)]
    e.call(ol["c_omst"], maxins=200_000); d0 = dep()
    e.knob(4, 20); e.shift(True); e.knob(4, 10); e.shift(False)
    e.knob(5, 30); e.shift(True); e.knob(5, -5); e.shift(False)
    e.knob(7, 7); e.shift(True); e.knob(7, -9); e.shift(False)
    check(sv() == [7, -9, -34, -5, -44, 10] and dep() == d0, f"the six values ({sv()}), the depths untouched ({dep()})")
    f = X.frame(e)
    check(f[64] >> 8 == 21 and f[64] & 0xFF == V.COL_TRACK[0], f"K5's LED: level 20 -> brightness 21 ({f[64]:#x})")
    e.call(0x08033320, MGR, CLEAR, maxins=8_000_000); e.knob(4, 1); e.call(0x0803381A, MGR, CLEAR, maxins=8_000_000)
    check(sv()[4] == -64, f"Clear + K5: the sub off ({sv()[4]})")
    e.knob(4, 20)
    writes = []
    def dw(uc, a, s, dd): writes.append((uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R1))); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, dw, begin=OM.DSPW, end=OM.DSPW)
    for _ in range(24): e.call(ol["c_omtick"], maxins=2_000_000)
    got = {a: ((v >> 8) & 0xFFFFFF) for a, v in writes if (om_t + 8 <= a < om_t + 16) or (om_t + 56 <= a < om_t + 64)}
    sx = lambda v: v - (1 << 24) if v & 0x800000 else v
    exp0 = {om_t + 9: 7, om_t + 13: -9, om_t + 12: 30, om_t + 14: -5, om_t + 8: 20, om_t + 10: 10}
    ok0 = all(sx(got.get(a, 999)) == v for a, v in exp0.items())
    ok1 = all(got.get(om_t + 48 + w, 999) == 0 for w in OM.SO_MAP)
    check(ok0 and ok1 and len(got) == 12, f"the tick: track 0's six ({ {hex(a): sx(v) for a, v in got.items() if a < om_t + 48} }), track 1's zeros ({ok1})")
    e.pad(27); e.pad(1)                                                     # two oscillators (pad 28), OSC 1's page
    s0 = sv(); e.knob(4, 3)
    check(sv() == s0 and dep()[4] == 3, f"two oscillators: K5 = LFO -> FM again ({dep()}), the one-oscillator values kept")
    writes.clear()
    for _ in range(24): e.call(ol["c_omtick"], maxins=2_000_000)
    z = {a: v for a, v in writes if om_t + 8 <= a < om_t + 16}
    check(len(z) == 6 and all(v == 0 for v in z.values()), f"two oscillators: track 0's one-oscillator words sent as 0 ({len(z)})")
    e.pad(27); e.pad(1)                                                     # back to one oscillator
    # the patch
    e.call(ol["c_omgath"], 0, maxins=8_000_000)
    buf = bytes(e.uc.mem_read(PK.BUF + OM.SO_AT, OM.SO_N))
    sm = (0x5A + sum(buf[:7])) & 0xFF
    check(buf[0] == OM.SO_SIG and [sx(b) if b < 128 else b - 256 for b in buf[1:7]] == sv() and buf[7] == sm, f"gather at padding + 142: {buf.hex()}")
    keep = {}
    def rd(uc, a, s, dd):
        n, off = uc.reg_read(UC_ARM_REG_R3), uc.reg_read(UC_ARM_REG_R1) % 512
        uc.mem_write(uc.reg_read(UC_ARM_REG_R2), keep.get(off, bytes(n))); uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_R1, n)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    mpr = int(R["mpatch"]["labels"]["c_mpr"], 16)
    e.uc.hook_add(UC_HOOK_CODE, rd, begin=mpr, end=mpr)
    saved = sv(); keep[(MP.OFF + OM.SO_AT) % 512] = buf
    e.uc.mem_write(OM.SOLR + 4, bytes(6))
    e.uc.reg_write(UC_ARM_REG_R5, 11); e.call(ol["c_omappl"], 0, maxins=12_000_000)
    check(sv() == saved, f"apply: the values back ({sv()})")
    keep.clear(); e.uc.reg_write(UC_ARM_REG_R5, 11); e.call(ol["c_omappl"], 0, maxins=12_000_000)
    check(sv() == [0, 0, -64, 0, -64, 0], f"a patch without the block: levels off, depths 0 ({sv()})")
    print(f"{man.get('marker', '?')} OSC1X RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
