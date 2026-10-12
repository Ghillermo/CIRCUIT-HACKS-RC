"""SC32D2 tests: the zone survey with probe32_dsp.V2 (16-bit memory pattern, M0 linear, flags in Y:STF) and the MIDI dump of tools/probe32c.py.

    python tools/emu_sc32d_2.py SC32D2.bin SC32D2_manifest.json
DSP (interpreter, areas in its 512 K words, M0 = $FFFF on entry as on the device):
  * the 32 reads cover the whole area (a word 0x28000 past the start, outside the 64 K window of M0 = $FFFF, is seen); M0 restored;
  * the write test pattern is $5A5A00 + (k << 8) (low byte 0: the alias check finds it), states as SC32D, flags mirrored in Y:STF + k;
  * the image's probe = code(v2=True) word for word.
ARM (real routes): service chain head c_dtick32c -> c_dtick32 -> c_dtick19; one flag byte per call into the buffer, the sweep count at index 38; pad 9 of the
open source view sends CC 20 = 127, (CC 21 = k, CC 22 = flags) for areas 0..18 (pad 10: 19..37), CC 23 / 24 = sweeps, CC 20 = 0 on channel 16; the LED pages use red 0x53 for code 1.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc32d as T32  # noqa: E402
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import probe32 as PR  # noqa: E402
import probe32c as PC  # noqa: E402
import probe32_dsp as PD  # noqa: E402
import build_sc14 as s14  # noqa: E402
import drums18  # noqa: E402

VIEWS = PR.VIEWS
CODE_AT, RET_AT, DRV_AT, POST_AT = 0x3900, 0x3F00, 0x3E00, 0x3D00
TB, TSTR, TOFF = 0x40000, 0x2000, (0x1FFF, 0x30000)
TAREAS = (TB, TB + 0x8000, TB + 0x10000)                      # overlapping reach on purpose: only the first words matter


def T_(*l): return G.T(*l)


class E2(T32.E32):
    def __init__(self, image, man):
        super().__init__(image, man)
        self.pc_ = {k: int(v, 16) for k, v in man["report"]["probe32c"]["labels"].items()}
        self.sent, self.sleeps = [], []
        def snd(uc, a, s, d):
            self.sent.append((uc.reg_read(UC_ARM_REG_R0), tuple(uc.mem_read(uc.reg_read(UC_ARM_REG_R1), 3))))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        self.uc.hook_add(UC_HOOK_CODE, snd, begin=PC.SEND, end=PC.SEND)
        def slp(uc, a, s, d):
            self.sleeps.append(uc.reg_read(UC_ARM_REG_R0)); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        self.uc.hook_add(UC_HOOK_CODE, slp, begin=PC.SLEEP, end=PC.SLEEP)
    def tickc(self, uptime=0):
        self.uc.mem_write(PR.HAL_TICK, struct.pack("<I", uptime))
        self.reads.clear(); self.chain.clear()
        self.call(self.pc_["c_dtick32c"], maxins=3_000_000)
        return list(self.reads)
    def bytes_(self, n): return bytes(self.uc.mem_read(self.st + PC.BUF, n))
    def ours(self): return [m for k, m in self.sent if k == 7 and m[0] == PC.STATUS]


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]
    dl = {k: int(v, 16) for k, v in rep["sc16"]["dsp_labels"].items()}
    sp = dsp_program(img)
    P0 = [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]
    check(len(P0) <= 0x3800 and P0[0x23C:0x23E] == [0x0BF080, dl["pprobe"]], f"P:$23C = jsr pprobe; program ends at P:${len(P0):x}")
    real, _ = PD.code(dl["pprobe"], PD.PREMIX, v2=True)
    check(P0[dl["pprobe"]:dl["pprobe"] + len(real)] == real, "the image's probe = code(v2=True)")

    tw, _ = PD.code(CODE_AT, RET_AT, TAREAS, TSTR, TB, TOFF, v2=True)
    P = P0 + [0] * (0x4000 - len(P0))
    P[CODE_AT:CODE_AT + len(tw)] = tw
    P[RET_AT] = 0x00000C
    n = 2 * len(TAREAS)
    drv = [0x0BF080, CODE_AT] * n + [0x00000C]
    P[DRV_AT:DRV_AT + len(drv)] = drv
    post = [0x0BF080, DRV_AT] + T_("move m0,x:>$3a01") + [0x00000C]
    P[POST_AT:POST_AT + len(post)] = post
    far = TB + 20 * TSTR                                        # $68000: outside the 64 K block of $40000
    mem = [('y', far, [0x123400]), ('y', TAREAS[2] - TOFF[0], [PD.PAT + (2 << 8)])]
    res, ran = run(P, POST_AT, mem=mem, regs_code=T_("move #>$ffff,m0"), maxins=3_000_000,
                   dumps=[('y', PD.STC, len(TAREAS)), ('y', PD.STF, len(TAREAS)), ('x', PD.FL, len(TAREAS)), ('x', 0x3A01, 1), ('y', PD.SWEEP, 1)] + [('y', a, 1) for a in TAREAS])
    codes, stf, fl = res[('y', PD.STC)], res[('y', PD.STF)], res[('x', PD.FL)]
    check(codes[0] == PD.S_STATIC, f"area 0: the word at +$28000 (outside M0's 64 K window) is seen -> static ({codes}, flags {[hex(f) for f in fl]}, {ran})")
    check(codes[2] == PD.S_ALIAS, "area 2: the pattern $5A5A00 + (2 << 8) at the alias address -> alias")
    check(stf == fl, f"flags mirrored in Y:STF ({[hex(x) for x in stf]})")
    check(res[('x', 0x3A01)] == [0xFFFF], f"M0 restored ({res[('x', 0x3A01)]})")
    check(res[('y', PD.SWEEP)] == [2] and [res[('y', a)][0] for a in TAREAS] == [0, 0, 0], "two sweeps; the tested words restored")

    # ---------------------------------------------------------------- ARM
    L = {k: int(v, 16) for k, v in rep["probe32c"]["labels"].items()}
    L32 = {k: int(v, 16) for k, v in rep["probe32"]["labels"].items()}
    check(drums18.decode_bw(bytearray(img), s14.SVC_HOOK) == L["c_dtick32c"], "DSP service chain head -> c_dtick32c")
    check(drums18.decode_bw(bytearray(img), L["dc_out"] + 4) == L32["c_dtick32"], "c_dtick32c goes on to c_dtick32")
    check(struct.unpack_from("<I", img, PC.SP_VT - 0x08010000)[0] == L["c_dpad"] | 1, "slot 0 of the synth Preset view -> c_dpad")
    gc.collect(); e = E2(img, man)
    e.btn(0)
    check(e.flag(), "source view open")
    flags = [(k * 7) & 0x1F for k in range(PD.NA)]
    e.read_map = {0x8000 | (PD.STF + k): f for k, f in enumerate(flags)}
    e.read_map[0x8000 | PD.SWEEP] = 300
    e.read_map[0x8000 | PD.YR] = PD.MAGIC
    e.read_map[0x8000 | PD.PK] = sum(1 << 3 * j for j in range(8))
    bad = []
    for i in range(64):
        r = e.tickc(uptime=(i << 3) | (1 << 9))
        ad = [x for _, x in r]
        if i < PD.NA and (0x8000 | (PD.STF + i)) not in ad: bad.append(i)
        if i == PD.NA and (0x8000 | PD.SWEEP) not in ad: bad.append(i)
    check(not bad and e.bytes_(PD.NA + 2) == bytes(flags) + struct.pack("<H", 300), f"one flag byte per call, sweeps at 38 / 39 (missing {bad})")
    check(len(e.chain) == 1, "the chain goes on (c_dtick32 then c_dtick19)")
    e.tickc(uptime=(0 << 12) | (1 << 9))
    check(e.row(VIEWS[0], 8, 8) == [0x53] * 8, f"LED page 0: code 1 in red 0x53 ({[hex(x) for x in e.row(VIEWS[0], 8, 8)]})")
    for pad, rng in ((8, range(0, PC.HALF)), (9, range(PC.HALF, PD.NA))):
        e.sent.clear(); e.sleeps.clear()
        e.padr(pad)
        m = e.ours()
        want = [(0xBF, 20, 127)] + [x for k in rng for x in ((0xBF, 21, k), (0xBF, 22, flags[k]))] + [(0xBF, 23, 300 & 127), (0xBF, 24, 300 >> 7), (0xBF, 20, 0)]
        check(m == want and len(m) < 64, f"pad {pad + 1}: areas {rng.start}..{rng.stop - 1} ({len(m)} messages, under 64)")
        check(e.sleeps == [1] * len(rng), "1 ms after each area")
    e.sent.clear(); e.padr(10)
    check(e.ours() == [], "pad 11: no dump")
    print("SC32D2 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
