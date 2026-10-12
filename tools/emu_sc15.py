"""SC15 tests: synth noise -> line input.

    python tools/emu_sc15.py STOCK.bin SC14.2.bin SC15.bin SC15_manifest.json
ARM part on the live RAM dump (unicorn); DSP part on the whole-core session (dsptool, $DSPTOOL).
"""
from __future__ import annotations
import json, math, struct, sys, tempfile
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc08 import E8, MGR  # noqa: E402
from dsp_session import Session  # noqa: E402
import build_sc15 as B  # noqa: E402

VIEWS = (0x20042980, 0x20042A34)          # Synth 1 / Synth 2 Preset views
ST = 0x20044E38                           # SC14 state block
N_MODES, GAIN = 3, 1                      # SC16.1 / SC17.1: 5 modes (+ inverted), input x2


class E15(E8):
    def __init__(self, image):
        super().__init__(image)
        self.calls, self.dw = [], []
        def h(uc, a, s, d):
            if a == B.SP_PRESS:
                self.calls.append(('press', uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2)))
                uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
            elif a == B.MARK_DIRTY:
                self.calls.append(('dirty', uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)))
                uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
            elif a == B.SP_REPAINT:
                self.calls.append(('repaint', uc.reg_read(UC_ARM_REG_R0)))
            elif a == B.DSP_WRITE:
                self.dw.append((uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R1) >> 8))
                uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        self.uc.hook_add(UC_HOOK_CODE, h)

    def shift(self, on): self.set_p0(self.r32(MGR + 0xC), 1 if on else 0)

    def pad(self, view, p, vel=100, shift=False):
        self.calls.clear()
        if shift: self.shift(True)
        self.call(self.r32(self.r32(view)), view, p, vel, maxins=600000)
        if shift: self.shift(False)
        return list(self.calls)

    def leds(self, view):
        self.calls.clear()
        self.call(self.r32(self.r32(view) + 0x1C), view, maxins=600000); p = self.uc.reg_read(UC_ARM_REG_R0)
        return list(struct.unpack("<32H", bytes(self.uc.mem_read(p, 64))))

    def modes(self): return list(self.uc.mem_read(ST + B.S_MODE, 2))


def arm_tests(stock, img, check):
    # stock behaviour of the view slots
    for k, v in enumerate(VIEWS):
        e = E15(img)
        c = e.pad(v, 3)
        check(c == [('press', v, 3, 100)], f"Synth {k+1}: pad 4 without Shift -> stock press {c}")
        c = e.pad(v, 25)
        check(c == [('press', v, 25, 100)], f"Synth {k+1}: pad 26 without Shift -> stock press (patch select) {c}")
        c = e.pad(v, 10, shift=True)
        check(c == [('press', v, 10, 100)], f"Synth {k+1}: Shift + pad 11 -> stock press {c}")
        sp = 24 + N_MODES
        c = e.pad(v, sp, shift=True)
        check(c == [('press', v, sp, 100)], f"Synth {k+1}: Shift + pad {sp+1} -> stock press {c}")
        for p, m in [(24 + m, m) for m in range(1, N_MODES)] + [(24, 0)]:
            c = e.pad(v, p, shift=True)
            exp = [0, 0]; exp[k] = m
            check(c == [('dirty', 0x20, 48)] and e.modes() == exp, f"Synth {k+1}: Shift + pad {p+1} -> mode {m}, Audio In group resent ({c}, {e.modes()})")
    # both synths independent
    e = E15(img)
    e.pad(VIEWS[0], 26, shift=True); e.pad(VIEWS[1], 25, shift=True)
    check(e.modes() == [2, 1], f"Synth 1 = In 2, Synth 2 = In 1 independently {e.modes()}")
    # LEDs
    es = E15(stock)
    for k, v in enumerate(VIEWS):
        ref = es.leds(v)
        e = E15(img)
        e.pad(v, 25, shift=True)                    # mode 1
        l0 = e.leds(v)
        check(l0 == ref, f"Synth {k+1}: LEDs without Shift identical to stock")
        e.shift(True); l1 = e.leds(v)
        on, dim = B.COLORS[k]
        e24 = 24 + N_MODES
        check(l1[:24] == ref[:24] and l1[e24:] == ref[e24:] and l1[24:e24] == [dim, on] + [dim] * (N_MODES - 2),
              f"Synth {k+1}: Shift held -> pads 25-{e24} = mode 1 bright, others dim, rest unchanged {[hex(x) for x in l1[24:e24]]}")
        e.shift(False); l2 = e.leds(v)
        check(('repaint', v) in e.calls and l2 == ref, f"Synth {k+1}: Shift released -> stock repaint, LEDs back to stock")
        l3 = e.leds(v)
        check(('repaint', v) not in e.calls and l3 == ref, f"Synth {k+1}: no repaint on later refreshes")
    # H9: modes to the DSP, then SC10 (FX-return flag at X:$3A00)
    e = E15(img); e.pad(VIEWS[0], 25, shift=True); e.pad(VIEWS[1], 26, shift=True)
    e.dw.clear(); e.call(0x08028EA4, maxins=600000)
    es = E15(stock); es.call(0x08028EA4, maxins=600000)
    n = len(es.dw)
    check(e.dw[:n - 1] == es.dw[:n - 1] and e.dw[n - 1:n + 1] == [(B.MODE_S1, 1), (B.MODE_S2, 2)]
          and e.dw[n + 1] == es.dw[n - 1] and e.dw[n + 2:] == [(0x3A00, 0)],
          f"H9: stock writes, X:$3A01=1, X:$3A02=2 (at the SC10 hook), last stock write, SC10 flag {[(hex(a), v) for a, v in e.dw]}")


def dsp_tests(stock, img, check):
    def s24(v): return v - (1 << 24) if v & 0x800000 else v
    ring = []
    for k in range(512):
        ring += [int(0x200000 * math.sin(k * 0.3)) & 0xFFFFFF, (-0x300000 - 0x1000 * (k % 7)) & 0xFFFFFF]
    def run(image, synth, modes, blocks=40):
        s = Session(image)
        ch = synth
        s.midi(bytes([0xB0 | ch, 56, 127])); s.midi(bytes([0x90 | ch, 60, 100]))
        extra = [('y', 0x1000 + i, v) for i, v in enumerate(ring)]
        if modes is not None: extra += [('x', B.MODE_S1, modes[0]), ('x', B.MODE_S2, modes[1])]
        wf = tempfile.mktemp()
        s.run(blocks=blocks, per_block=False, extra=extra, watchfile=wf,
              watch=[('x', 0x2c46, 32), ('x', 0x1400, 6 * 32), ('y', 0xffd, 1)])
        blk, cur, ffd = [], None, 0x1000
        for l in open(wf):
            pc, ad, rw, v = l.split(); a = int(ad[2:], 16); v = s24(int(v, 16))
            if pc == '0009ac' and rw == 'W' and a == 0x1405:
                cur = dict(ffd=ffd, lv=[], out=[]); blk.append(cur)
            if ad == 'Y:000ffd' and rw == 'W': ffd = v
            if cur is None: continue
            if pc == '0009ac' and rw == 'W' and (a - 0x1400) % 6 == 5: cur['lv'].append(v)
            if pc == '0009c6' and rw == 'W' and 0x2c46 <= a < 0x2c66: cur['out'].append(v)
        return blk
    for synth in (0, 1):
        ref = run(stock, synth, None)
        r0 = run(img, synth, (0, 0))
        check([b['out'] for b in r0] == [b['out'] for b in ref] and any(any(b['out']) for b in ref),
              f"Synth {synth+1}, mode Noise: voice mix identical to stock ({len(ref)} voice blocks)")
        for mode in range(1, N_MODES):
            modes = [0, 0]; modes[synth] = mode
            r = run(img, synth, modes)
            worst, n = 0, 0
            for b in r[-10:]:
                base = b['ffd'] - 0x1000
                for i, (o, l) in enumerate(zip(b['out'], b['lv'])):
                    x = s24(ring[base + 2 * i + (mode - 1) % 2]) * GAIN * (-1 if mode >= 3 else 1)
                    x = max(-0x800000, min(0x7FFFFF, x))
                    exp = (x * l) >> 23
                    worst = max(worst, abs(o - exp)); n += 1
            check(n and worst <= 2, f"Synth {synth+1}, mode {mode}: voice mix = {'-' if mode >= 3 else ''}{GAIN} x input {(mode - 1) % 2 + 1} x noise level ({n} samples, max err {worst})")
            other = [0, 0]; other[1 - synth] = mode
            ro = run(img, synth, other)
            check([b['out'] for b in ro] == [b['out'] for b in ref], f"Synth {synth+1} unaffected when only Synth {2-synth} is set to In {mode}")


def main(stock, s142, img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    arm_tests(stock, img, check)
    dsp_tests(stock, img, check)
    print("SC15 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    # python tools/emu_sc15.py STOCK.bin SC14.2.bin IMG.bin manifest.json [--v2]
    #   --v2: line input v2 (SC16.1 / SC17.1+): 5 modes, gain 2; state block address from the manifest
    args = [a for a in sys.argv[1:] if a != "--v2"]
    st, s142, im = (Path(p).read_bytes() for p in args[0:3])
    man = json.loads(Path(args[3]).read_text())
    if "--v2" in sys.argv:
        N_MODES, GAIN = 5, 2; B.N_MODES = 5
    rep = man["report"]
    if "sc17" in rep: ST = int(rep["sc17"]["sc14_state"], 16)
    elif "sc16" in rep: ST = int(rep["sc16"]["sc14_state"], 16)
    sys.exit(1 if main(st, s142, im, man) else 0)
