"""RC2.09 / SC46.5 (persist19.use_startfix): Shift + K3's start point of the drums over the whole sample.

  * ARM (the emulated firmware): with S = 16 / 32 / 64 / 120 in the drum's DRX1 block (c_k3put), c_k3w writes STARTF = S << 14 (the previous build
    S << 16) into the drum's DSP block; the cut (ENDC = E << 16) unchanged;
  * DSP (the real core-0 program, whole core, four hits through the ARM's trigger): with STARTF = S << 14 the voices keep playing for S = 64 and 120 and
    start at L x S / 128 (the playback index 4 x a1 + a0 >> 22 of x:(r3+4/5)); with the previous build's value (S << 16) S = 64 / 120 leave the voices
    silent after the hit's block (the bug).

    python tools/emu_startfix.py BUILD.bin manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]
"""
from __future__ import annotations
import gc, json, math, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import drums2_dsp as DD  # noqa: E402
from dsp_session import Session  # noqa: E402
from emu_masterfx_dsp import u24  # noqa: E402

DSP_WRITE = 0x080292F8
VOICE_R3 = 0x1E8D
SL = 0x2000                                     # the test sample's length (in samples): 120 / 128 still leaves 16 blocks


def arm(img, man):
    e = T.EL(Path(img).read_bytes())
    L = {k: int(v, 16) for k, v in man["report"]["persist19"]["labels"].items()}
    w = []
    def hk(uc, a, s, d): w.append((uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R1) >> 8)); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, hk, begin=DSP_WRITE, end=DSP_WRITE)
    e.call(L["c_k3blk"], maxins=1_000_000); from unicorn.arm_const import UC_ARM_REG_R0
    blk = e.uc.reg_read(UC_ARM_REG_R0)
    e.call(L["c_k3init"], blk, 0, maxins=1_000_000)
    out = {}
    for S in (16, 32, 64, 120):
        e.call(L["c_k3put"], 0, 1, S, maxins=1_000_000); e.call(L["c_k3put"], 0, 2, 0, maxins=1_000_000)
        w.clear(); e.call(L["c_k3w"], 0, maxins=1_000_000)
        out[S] = {addr - DD.DB: v for addr, v in w if DD.DB <= addr < DD.DB + DD.STRIDE}
    e.call(L["c_k3put"], 0, 1, 0, maxins=1_000_000); e.call(L["c_k3put"], 0, 2, 64, maxins=1_000_000)
    w.clear(); e.call(L["c_k3w"], 0, maxins=1_000_000)
    out["cut"] = {addr - DD.DB: v for addr, v in w if DD.DB <= addr < DD.DB + DD.STRIDE}
    del e; gc.collect()
    return out


def session(image, startf, blocks=6):
    s = Session(image)
    for d in range(4): s.capture(f'hit{d}', 0x08051B54, d, 100)
    extra = [('x', 0xA4 + 10 * d, 0x10000) for d in range(4)] + [('x', 0xA5 + 10 * d, 0x7FFFFF) for d in range(4)]
    for k in range(64): extra += [('x', 0x1D8D + 4 * k, 0x3B00), ('x', 0x1D8E + 4 * k, SL), ('x', 0x1D8F + 4 * k, 0x8000)]
    for i in range(SL + 0x40): extra.append(('y', 0x3B00 + i, u24(int(0x400000 * math.sin(i * 0.2)))))
    for d in range(4): extra.append(('x', DD.DB + DD.STRIDE * d + DD.STARTF, startf & 0xFFFFFF))
    res, _ = s.run(blocks=blocks, per_block=False, extra=extra, dumps=[('x', VOICE_R3, 4 * 18)])
    v = {(sp_, a): val for sp_, a, val in res}[('x', VOICE_R3)]
    return [v[18 * d + 6] for d in range(4)]


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    raw = Path(img).read_bytes()
    a = arm(img, man)
    check(all(a[S].get(DD.STARTF) == S << 14 for S in (16, 32, 64, 120)), f"c_k3w: STARTF = S << 14 ({[hex(a[S].get(DD.STARTF, -1)) for S in (16, 32, 64, 120)]})")
    check(a["cut"].get(DD.ENDC) == 64 << 16, f"the cut unchanged: ENDC = E << 16 ({hex(a['cut'].get(DD.ENDC, -1))})")
    for S in (64, 120):
        act = session(raw, S << 14)
        check(all(x != 0 for x in act), f"whole core, start S = {S} with the fix: the voices keep playing ({act})")
        bug = session(raw, S << 16)
        check(all(x == 0 for x in bug), f"whole core, the old value of S = {S} (S << 16): silent after the hit (the bug: {bug})")
    act = session(raw, 16 << 14)
    check(all(x != 0 for x in act), f"S = 16: playing ({act})")
    if prev:
        p = arm(prev, pman)
        check(all(p[S].get(DD.STARTF) == S << 16 for S in (16, 64)), f"the previous build: STARTF = S << 16 ({[hex(p[S].get(DD.STARTF, -1)) for S in (16, 64)]})")
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text()), a[2] if len(a) > 2 else None,
                       json.loads(Path(a[3]).read_text()) if len(a) > 3 else None) else 0)
