"""SC43.5 ARM tests, through the controller and the real drum DSP handler (0x080287DE, Drum 1's group):
  * drum pitch (dpitch): neutral = word 0x10000; K1 +5 = S 69 (the block in the tail), word = the semitone table's 2^(5/12); Shift + K6 +10 = the
    stock Pitch 74 (S stays), word = 2^(5/12) x the stock's linear factor (256 + 2 x 15) / 256; LEDs: K1 at 2 + 10, with Shift K6 at 2 + 20; the
    chromatic view's pad sets S (P stays); Clear + K1 right = S 64, Clear + K6 right = P 64;
  * Clear + Synth 1 (clrtrk.use_synth) on its view: the eight macro positions of the patch's record (the pack read is faked with a known record)
    set again; the source view does not open.

    python tools/emu_sc43_5.py SC43.5.bin SC43.5_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import dpitch as DP  # noqa: E402
import build_sc09 as S09  # noqa: E402
import packio as PK  # noqa: E402

MGR = T.MGR
DRUM1_GROUP, DSP_W = 0x080287DE, 0x080292F8


def lab(man, m, k): return int(man["report"][m]["labels"][k], 16)


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    tab = S09.table() if hasattr(S09, "table") else None
    e = T.EL(img); e.at(300000); e.transport(0)
    r0 = lambda fn, *a: (e.call(fn, *a, maxins=4_000_000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    dsp = []
    def w(uc, a, s, d): dsp.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2)))
    e.uc.hook_add(UC_HOOK_CODE, w, begin=DSP_W, end=DSP_W)
    wordc = lambda P: r0(lab(man, "dpitch", "c_dpc0"), P)
    def group_word():
        dsp.clear(); e.call(DRUM1_GROUP, maxins=4_000_000)
        return [v for v, a_ in dsp]
    mh = r0(lab(man, "sc18", "c_mh"), 0)
    P = lambda: e.r8(r0(0x0803542C, e.r32(mh + 0xC), 0))
    S = lambda: r0(lab(man, "dpitch", "c_dpnow"), 0)
    knob = lambda k, d: e.call(0x08033848, MGR, k, d & 0xFFFFFFFF, maxins=8_000_000)
    def shift(on): e.set_p0(e.r32(MGR + 0xC), 1 if on else 0)
    e.btn(4); f = X.frame(e)
    conv = lambda v: r0(lab(man, "sc12", "c_conv0"), v)                              # SC12's word of a value (the semitone table x the cents)
    w0 = wordc(64)
    check(S() == 64 and P() == 64 and w0 == conv(64), f"neutral: S {S()}, P {P()}, word {w0:#x} = SC12's of 64 ({conv(64):#x}: the dump's cents)")
    knob(0, 5); f = X.frame(e)
    tail = e.r32(DP.SESSION_OBJ + 0x14) + DP.TAIL; blk = bytes(e.uc.mem_read(tail + DP.O_BLK, 6))
    w1 = wordc(P()); want1 = conv(69)
    check(S() == 69 and P() == 64 and blk[0] == DP.MAGIC and blk[1] == 69 and w1 == want1 and f[60] >> 8 == 12,
          f"K1 +5: S 69 (block {blk.hex()}), P untouched, word {w1:#x} = SC12's of 69 {want1:#x}; K1 LED {f[60] >> 8}")
    g = group_word()
    check(w1 in g, f"the drum's DSP group sends that word ({[hex(x) for x in g][:6]})")
    shift(True); knob(5, 10); f = X.frame(e); shift(False)
    w2 = wordc(P()); want2 = (conv(69) * (256 + 2 * (10 + 5))) >> 8
    check(S() == 69 and P() == 74 and w2 == want2 and f[65] >> 8 == 22, f"Shift + K6 +10: P 74, S 69, word {w2:#x} = {want2:#x}; K6 LED with Shift {f[65] >> 8}")
    e.call(0x08033320, MGR, 23, maxins=8_000_000)                                  # Clear held
    knob(0, 1); s3 = S(); knob(5, 1); p3 = P()
    e.call(0x0803381A, MGR, 23, maxins=8_000_000)
    check(s3 == 64 and p3 == 64, f"Clear + K1 right: S {s3}; Clear + K6 right: P {p3}")
    # the chromatic view
    shift(True); e.btn(8); shift(False)                                            # Shift + Preset
    view = r0(lab(man, "sc11", "c_dview"), 0); flag = e.r8(view + 0x51) & 1
    p4 = P(); e.pad(8); s4 = S()
    check(flag == 1 and P() == p4 and s4 != 64, f"chromatic view: a pad sets S ({s4}), P stays ({p4})")
    del e; gc.collect()

    # ---- Clear + Synth 1
    e = T.EL(img); e.at(300000); e.transport(0)
    r0 = lambda fn, *a: (e.call(fn, *a, maxins=4_000_000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    rec = bytearray((7 * i + 3) % 128 for i in range(340)); want = [rec[30 + 174 + 17 * m] for m in range(8)]
    reads = []
    def fake(uc, a, s, d):
        reads.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R3)))
        uc.mem_write(uc.reg_read(UC_ARM_REG_R2), bytes(rec)); uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_R1, 340)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    mpr = lab(man, "mpatch", "c_mpr"); e.uc.hook_add(UC_HOOK_CODE, fake, begin=mpr, end=mpr)
    mac = lambda: [r0(0x08036192, 0, 174 + 17 * m) for m in range(8)]
    e.btn(0); X.frame(e); before = mac()
    view = e.r32(0x20040DB8 + 0x78); e.call(0x0803542C, e.r32(view + 0x14), 10); patch = e.r8(e.uc.reg_read(UC_ARM_REG_R0))
    e.call(0x08033320, MGR, 23, maxins=8_000_000); e.call(0x08033320, MGR, 0, maxins=8_000_000); e.call(0x0803381A, MGR, 23, maxins=8_000_000)
    after = mac()
    check(reads == [(patch >> 3, 512 * (patch & 7), PK.PATCH_SZ)] and after == want and e.r8(MGR + 0x152) <= 1,
          f"Clear + Synth 1: patch {patch} read ({reads}), macros {before} -> {after} (the record's {want}), still on its view ({e.r8(MGR + 0x152)})")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
