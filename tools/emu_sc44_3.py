"""SC44.3 ARM tests (vcf21.use_lfoshape2, modmx.use_v2), through the controller, the real LED task, the whole DSP service chain and the patch routines:
  * the own engine's LFO: a project without the tag = the triangle (c_vlsh 2, MIDI 1's ACT with 2 in bits 13-15); page 5, Shift + K8: four clicks
    a step up to 6 = slewed sample & hold (its LED violet), no wrap; a version 1 own-synth patch = the reverse saw, a version 2 one with shape 6 = 6;
  * the matrix's LFO 2 (K4): Shift + K4 = 5 zones of 32 (triangle green, saw magenta, square red, S&H white, slewed S&H violet), up to 159; K4 on
    RES: with the stepped S&H RES jumps (few values), with the slewed one it glides (many values, small steps).

    python tools/emu_sc44_3.py SC44.3.bin SC44.3_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R1, UC_ARM_REG_R2
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
import mpatch as MP  # noqa: E402
import packio as PK  # noqa: E402
import modmx as MX  # noqa: E402

V = T4.V
MGR = X.MGR
LS_SESSION, LS_TAIL, O_LS = 0x2003D71C, 0x27024, 561


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = X.EP(img, man)
    ml = {k: int(v, 16) for k, v in man["report"]["modmx"]["labels"].items()}
    mp = {k: int(v, 16) for k, v in man["report"]["modmx"]["prev"].items()}
    pl = {k: int(v, 16) for k, v in man["report"]["mpatch"]["labels"].items()}
    dw = []
    def w(uc, a, s, d): dw.append((uc.reg_read(UC_ARM_REG_R1) >> 8, uc.reg_read(UC_ARM_REG_R2)))
    e.uc.hook_add(UC_HOOK_CODE, w, begin=0x080292F8, end=0x080292F8)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    def tick(n=1, step=40):
        for _ in range(n): e.at(e.t + step); e.call(ml["c_mxtick"], maxins=6_000_000)
    tail = e.r32(LS_SESSION + 0x14) + LS_TAIL
    e.uc.mem_write(tail + O_LS, bytes([0, 0, 0]))                                     # a project without the tag
    tick(10)
    sh = e.r0(e.vl["c_vlsh"], 0)
    dw.clear(); e.uc.mem_write(V.TAIL + V.O_RT + V.RT_AUX, bytes([e.r8(V.TAIL + V.O_RT + V.RT_AUX) | 1])); tick(6)
    acts = [v for v, a in dw if a == V.VB0 and (v >> 16) & 0x7F == 19]
    check(sh == 2 and acts and all((v >> 13) & 7 == 2 for v in acts), f"no tag: the triangle (c_vlsh {sh}; MIDI 1's ACT {[hex(v) for v in acts[:2]]})")
    # page 5, Shift + K8
    e.btn(2); e.btn(8); e.call(e.vl["c_vsetpage"], 0, 4); e.shift(True)
    steps = []
    for _ in range(4 * 6): e.knob(7, 1); steps.append(e.r8(tail + O_LS))
    f = X.frame(e); e.shift(False)
    top = e.r8(tail + O_LS)
    check(steps[3] == 0xB3 and top == 0xB6 and f[67] == (127 + 2) << 8 | 0x49, f"Shift + K8: from the triangle a step every 4 clicks, up to 6 = slewed S&H ({top:#x}), its LED violet ({f[67]:#x})")
    # the patch
    e.call(pl["c_mpgather"], 0, maxins=4_000_000)
    buf = bytes(e.uc.mem_read(PK.BUF, MP.DATA))
    e.uc.mem_write(PK.BUF + 41, bytes([1])); e.call(pl["c_mpapply"], 0, maxins=8_000_000); a1 = e.r8(tail + O_LS)
    e.uc.mem_write(PK.BUF + 41, bytes([2, 6])); e.call(pl["c_mpapply"], 0, maxins=8_000_000); a2 = e.r8(tail + O_LS)
    check(buf[41] == 2 and buf[42] == 6 and a1 == 0xB0 and a2 == 0xB6, f"the patch: gathered shape {buf[42]}; a version 1 patch = the reverse saw ({a1:#x}), version 2 shape 6 = {a2:#x}")
    # the matrix's LFO 2
    zc = bytes(e.uc.mem_read(ml["t_zcol"], 5))
    nd = mp["pmax"] // MX.ZONE
    dcode = bytes(e.uc.mem_read(ml["t_dcode"], nd)); zone = {c: z for z, c in enumerate(dcode)}
    e.pad(5); e.shift(True)
    cols = []
    for z in range(5):
        cols.append(X.frame(e)[63] & 0xFF)
        for _ in range(32): e.knob(3, 1)
    for _ in range(40): e.knob(3, 1)
    par = e.r8(MX.MXR + MX.T0 + MX.B_PAR); e.shift(False)
    check(cols == list(zc) == [0x17, 0x32, 0x53, 0x01, 0x49] and par == 159, f"Shift + K4: the 5 shapes' colours {[hex(c) for c in cols]}, up to {par}")
    for _ in range(2 * (zone[2] * MX.ZONE + MX.ZONE)): e.knob(3, 1)                    # K4 on RES, full
    sent = lambda: [struct.unpack("<h", struct.pack("<H", v & 0xFFFF))[0] for v, a in dw if a == V.VB0 and (v >> 16) & 0x7F == 2]
    def run(p):
        e.uc.mem_write(MX.MXR + MX.T0 + MX.B_PAR, bytes([p])); dw.clear(); tick(250, 20); return sent()
    stepped, slewed = run(3 * 32 + 20), run(4 * 32 + 20)                                 # ~2.4 Hz: ~12 cycles in 5 s
    jumps = lambda vs: max((abs(b - a) for a, b in zip(vs, vs[1:])), default=0)
    check(len(set(stepped)) <= 12 and len(set(slewed)) > 3 * len(set(stepped)) and jumps(slewed) < jumps(stepped),
          f"RES: stepped S&H {len(set(stepped))} values (biggest jump {jumps(stepped)}), slewed {len(set(slewed))} values (biggest jump {jumps(slewed)})")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
