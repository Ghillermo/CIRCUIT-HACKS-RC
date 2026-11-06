"""SC52.6 tests (ingain + vcf21_dsp.use_ingain): Advanced Setup K3 = the external inputs' gain.

    python tools/emu_ingain.py SC52.6.bin SC52.6_manifest.json

ARM (the controller's knobs, the real LED task, emu_gmdrum's harness):
  * the default: no tag in parameter 7 byte 2 = 0 dB; the DSP service head writes X:$3FF9 = 0 at most once;
  * Advanced Setup, K3 six steps right (12 clicks): 0x40 + 6 in both copies, the save asked; the pads show 6, K3's LED brighter; the head writes
    gain_word(6) once, then nothing until the refresh;
  * K3 far right: 24 (clamped); far left: 0 and X:$3FF9 = 0 again;
  * the normal Setup view: K3 changes nothing of ours.
DSP (core 0 from vpre, the voices off, emu_wt_dsp's set-up):
  * X:$3FF9 = 0: the inputs bit for bit; gain_word(6): x 1.995 (± 1 LSB of 16 bits); gain_word(24) on a loud input: clipped at full scale.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_gmdrum as EGM  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import ingain as IG  # noqa: E402

MGR = EGM.MGR


def arm(img, man, check):
    raw = Path(img).read_bytes()
    e = EGM.EG(raw, man)
    L = {k: int(v, 16) for k, v in man["report"]["ingain"]["labels"].items()}
    P = {k: int(v, 16) for k, v in man["report"]["ingain"]["prev"].items()}
    writes = []
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    def dw(uc, a, s, d):
        if uc.reg_read(UC_ARM_REG_R2) == IG.GAIN: writes.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1) >> 8))
        skip(uc)
    e.uc.hook_add(UC_HOOK_CODE, dw, begin=IG.DSP_WRITE, end=IG.DSP_WRITE)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: skip(uc), begin=P["svc"], end=P["svc"])
    tick = lambda n=1: [e.call(L["c_ighead"], maxins=2_000_000) for _ in range(n)]
    byte = lambda c: e.param(IG.PARAM, c)[IG.BYTE]
    tick(3)
    check(writes in ([], [(0, 0)]), f"the default: X:$3FF9 = 0 at most once ({writes})")
    e.setup(True, adv=1); e.call(0x08047494, e.r32(MGR + 0x68), 1, maxins=4_000_000); e.unpend(); fA = X.frame(e)
    for _ in range(12): e.knob(IG.KNOB, 1)
    f = X.frame(e)
    check(byte(0) == byte(1) == IG.TAG + 6 and e.pending(), f"K3 six steps right: 0x46 in both copies ({byte(0):#x}, {byte(1):#x}), the save asked")
    led = f[IG.LED_K3]
    check(f[:32] != fA[:32] and any(x & 0xFF == IG.COL_NUM for x in f[:32]) and led >> 8 == 6 + 5 * 6 + 2 and fA[IG.LED_K3] >> 8 == 8,
          f"the number on the pads, K3's LED {led:#x} (before {fA[IG.LED_K3]:#x})")
    writes.clear(); tick()
    check(writes == [(0, IG.gain_word(6))], f"the head: X:$3FF9 = {IG.gain_word(6):#x} ({[(c, hex(v)) for c, v in writes]})")
    writes.clear(); tick(IG.REFRESH - 1); n_mid = len(writes); tick()
    check(n_mid == 0 and writes == [(0, IG.gain_word(6))], f"no write for {IG.REFRESH - 1} ticks ({n_mid}), then the refresh ({len(writes)})")
    for _ in range(80): e.knob(IG.KNOB, 1)
    check(byte(0) == IG.TAG + IG.DBMAX, f"far right: 24 dB ({byte(0):#x})")
    for _ in range(80): e.knob(IG.KNOB, -1)
    writes.clear(); tick()
    check(byte(0) == IG.TAG and writes == [(0, 0)], f"far left: 0 dB, X:$3FF9 = 0 ({byte(0):#x}, {writes})")
    e.setup(True, adv=0); b0 = byte(0)
    for _ in range(12): e.knob(IG.KNOB, 1)
    check(byte(0) == b0, f"the normal Setup view: K3 changes nothing of ours ({byte(0):#x})")
    del e; gc.collect()


def dsp(img, man, check):
    import numpy as np
    from dspemu import run
    from dsp_session import dsp_program
    import emu_wt_dsp as W
    import granular_dsp as GD
    V, N, RING, OSB = W.V, W.N, W.RING, W.OSB
    sp = dsp_program(Path(img).read_bytes())
    P = [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]
    vpre = int(man["report"]["sc16"]["dsp_labels"]["vpre"], 16)
    gt = W.gentabs(True)
    t = np.arange(2 * N)
    src = [int(round(0.3 * np.sin(2 * np.pi * k / 23) * 32767)) << 8 & 0xFFFFFF for k in t]
    loud = [int(round(0.5 * np.sin(2 * np.pi * k / 23) * 32767)) << 8 & 0xFFFFFF for k in t]
    def go(g, ring):
        mem = [('x', 0x3A, [N]), ('x', V.VB0, [0] * (2 * V.VBS)), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, ring),
               ('x', OSB, [0] * 144), ('x', GD.RDOFS, [0x40]), ('x', GD.SOUT, [0] * 128), ('x', V.SIDE0, [0, 0]), ('x', IG.GAIN, [g])] + gt
        res, ran = run(P, vpre, mem=mem, dumps=[('y', RING, 2 * N)], regs_code=[], maxins=20_000_000)
        assert 'pc=00' in ran, ran
        gc.collect()
        return res[('y', RING)]
    s24 = lambda v: v - (1 << 24) if v & 0x800000 else v
    out = go(0, src)
    check(out == src, "X:$3FF9 = 0: the inputs bit for bit")
    out = go(IG.gain_word(6), src)
    r = [s24(o) / s24(i) for o, i in zip(out, src) if abs(s24(i)) > 0x100000]
    g = 10 ** (6 / 20)
    check(r and all(abs(x - g) < 0.002 for x in r), f"6 dB: x {min(r):.4f} .. {max(r):.4f} (want {g:.4f})")
    out = go(IG.gain_word(24), loud)
    pk = max(abs(s24(o)) for o in out)
    check(pk == 0x7FFFFF or pk == 0x800000, f"24 dB on a loud input: clipped at full scale (peak {pk:#x})")


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    arm(img, man, check)
    dsp(img, man, check)
    print(f"{man.get('marker', '?')} INGAIN RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1], json.loads(Path(sys.argv[2]).read_text())) else 0)
