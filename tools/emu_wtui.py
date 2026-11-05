"""SC52.1 ARM tests (tools/wtui.py: the wavetable engine's panel and its link to the DSP), through the controller and the real LED task (emu_fm8v2's
harness):
  * the engine row (pad 27): pad 21 = the oscillator + the wavetable on, pre-filled with Nova table DEF_T, FM off; pad 21 bright sand, pad 19 dim;
    pad 24 (FM) = the wavetable off; pad 21 again = on, FM off;
  * the row closed, playing: pads 7 / 8 dim sand; pad 7 held = pads 9-24 the 16 Nova tables (the table's one bright), 25-32 dark; pad 12 there =
    Nova table 3's 9 frames;
  * pad 8 held = pads 9-32 the samples of the page (sand; in the table bright); a tap adds the sample's frame (up to 9), a tap again takes it out;
    Octave up there = the next page;
  * the DSP service tick: WT_N / WT_B of the track's OSC2 block written; one copy at a time (source = the Nova table's frame in core 1's X, the
    slot's place in Y, $4800 words, a new seq last); X:$5214 = the seq = done, the next slot's copy; sample frames not copied (--smpcyc, SC52.2: core 1's sample job, bit 23 | the sample);
  * the patch: mpatch's save writes the record at padding + 150 (0xB7, on, frames, the frames, the check); a load brings it back; a patch without
    it = the wavetable off.

    python tools/emu_wtui.py build/sc52.1/circuittracks-4486-SC52.1.bin build/sc52.1/manifest.json
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import fmeng as FE  # noqa: E402
import fm8arm as A  # noqa: E402
import modesel as MS  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
import granular_dsp as GD  # noqa: E402
import packio as PK  # noqa: E402
import wtui as W  # noqa: E402

MGR = X.MGR


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]
    ml = {k: int(v, 16) for k, v in R["modesel"]["labels"].items()}
    wl = {k: int(v, 16) for k, v in R["wtui"]["labels"].items()}
    pl = {k: int(v, 16) for k, v in R["mpatch"]["labels"].items()}
    e = X.EP(img, man)
    e.w8 = lambda a_, v: e.uc.mem_write(a_, bytes([v]))
    xw = {}                                                                     # core 0's X as the ARM wrote it
    def dread(uc, a, s, d):
        uc.reg_write(UC_ARM_REG_R0, xw.get(uc.reg_read(UC_ARM_REG_R1), 0) << 8); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    def dwrite(uc, a, s, d):
        xw[uc.reg_read(UC_ARM_REG_R2)] = uc.reg_read(UC_ARM_REG_R1) >> 8; log.append((uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R1) >> 8))
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    log = []
    e.uc.hook_add(UC_HOOK_CODE, dread, begin=W.DSPR, end=W.DSPR)
    e.uc.hook_add(UC_HOOK_CODE, dwrite, begin=W.DSPW, end=W.DSPW)
    press = lambda q: e.call(PRESS, MGR, q, 100, maxins=8_000_000)
    release = lambda q: e.call(RELEASE, MGR, q, maxins=8_000_000)
    mode = lambda: e.r0(ml["c_msmode"], 0)
    lo = lambda f, a, b: [x & 0xFF for x in f[a:b]]
    tb = W.WTR + W.TB0
    on = lambda: e.r8(tb + W.T_ON)
    frames = lambda: [e.r8(tb + W.T_F + k) for k in range(e.r8(tb + W.T_N))]
    fm = lambda: e.r8(A.FM8R + A.TB0 + A.B_ON)
    S, D = W.COL

    # ---- the row
    e.btn(2); e.btn(8); e.pad(26)
    e.pad(W.ROWPAD); f = X.frame(e)
    check(mode() == 2 and on() == 1 and frames() == [W.DEF_T * 9 + k for k in range(9)] and fm() == 0,
          f"pad 21: the oscillator ({mode()}), the wavetable on, pre-filled with Nova table {W.DEF_T} ({frames()}), FM off")
    check(f[W.ROWPAD] & 0xFF == S and f[W.OSCPAD] & 0xFF == MS.COLS[2][1], f"pad 21 bright sand, pad 19 dim ({f[W.ROWPAD]:#x}, {f[W.OSCPAD]:#x})")
    e.pad(FE.ROWPAD)
    check(on() == 0 and fm() == 1, f"pad 24: FM on, the wavetable off ({on()}, {fm()})")
    e.pad(W.ROWPAD); f = X.frame(e)
    check(on() == 1 and fm() == 0 and mode() == 2 and f[FE.ROWPAD] & 0xFF != FE.COL_FM[0], "pad 21 again: the wavetable, FM off")
    e.pad(26); f = X.frame(e)
    check(lo(f, 6, 8) == [D, D], f"the row closed: pads 7 / 8 dim sand ({lo(f, 6, 8)})")

    # ---- pad 7 held: the Nova tables
    press(6); f = X.frame(e)
    exp = [S if j == W.DEF_T else D for j in range(16)] + [0] * 8
    check(lo(f, 8, 32) == exp and f[6] & 0xFF == S, f"pad 7 held: the 16 Nova tables, table {W.DEF_T} bright, 25-32 dark ({[hex(x) for x in lo(f, 8, 32)]})")
    press(11); release(11)
    check(frames() == [27 + k for k in range(9)], f"pad 12: Nova table 3's frames ({frames()})")
    release(6)

    # ---- pad 8 held: the samples
    e.w8(tb + W.T_N, 2)
    press(7); f = X.frame(e)
    check(lo(f, 8, 32) == [D] * 24 and f[7] & 0xFF == S, f"pad 8 held: the samples of page 1 dim sand ({set(lo(f, 8, 32))})")
    press(8); release(8); f = X.frame(e)
    check(frames() == [27, 28, 144] and f[8] & 0xFF == S, f"pad 9: sample 0 added ({frames()}), bright")
    e.btn(20)
    check(e.r8(W.WTR + 6) == 1, f"Octave up with pad 8 held: page 2 ({e.r8(W.WTR + 6)})")
    press(9); release(9)
    check(frames() == [27, 28, 144, 144 + 25], f"pad 10 on page 2: sample 25 ({frames()})")
    e.btn(19); press(8); release(8)
    check(frames() == [27, 28, 144 + 25], f"page 1, pad 9 again: sample 0 out, the next moved down ({frames()})")
    release(7)

    # ---- the DSP service tick
    log.clear()
    e.call(wl["c_wttick"], maxins=40_000_000)
    o2 = VD.OS2B0
    want0 = W.NOVA0 + 3 * W.NOVA_T + 0 * W.FRAME
    cmd = [v for a_, v in log if a_ in (GD.WC_X, GD.WC_X + 1, GD.WC_X + 2, GD.WC_X + 3)]
    check(xw.get(o2 + VD.WT_N) == 3 and xw.get(o2 + VD.WT_B) == W.WT_Y[0], f"the tick: WT_N = 3, WT_B = ${W.WT_Y[0]:x} ({xw.get(o2 + VD.WT_N)}, {xw.get(o2 + VD.WT_B, 0):#x})")
    ix = [a_ for a_, _ in log]
    check(cmd == [want0, W.WT_Y[0], W.FRAME, 1] and ix.index(GD.WC_X) > ix.index(GD.WC_X + 3), f"slot 1's copy: Nova table 3 frame 0 -> Y:${W.WT_Y[0]:x}, $4800 words, seq 1 last ({[hex(v) for v in cmd]})")
    log.clear(); e.call(wl["c_wttick"], maxins=40_000_000)
    check(not [1 for a_, _ in log if a_ == GD.WC_X], "not done yet: no other copy")
    xw[GD.WC_X + 4] = 1; log.clear(); e.call(wl["c_wttick"], maxins=40_000_000)
    cmd = [v for a_, v in log if a_ in (GD.WC_X, GD.WC_X + 1, GD.WC_X + 2, GD.WC_X + 3)]
    check(e.r8(tb + W.T_L) == 27 and cmd == [W.NOVA0 + 3 * W.NOVA_T + W.FRAME, W.WT_Y[0] + W.FRAME, W.FRAME, 2], f"done (seq 1 seen): slot 2's copy ({[hex(v) for v in cmd]})")
    xw[GD.WC_X + 4] = 2; log.clear(); e.call(wl["c_wttick"], maxins=40_000_000)
    if "--smpcyc" in sys.argv:                                                  # SC52.2 (wtui.use_smpcyc): core 1's sample job
        cmd = [v for a_, v in log if a_ in (GD.WC_X, GD.WC_X + 1, GD.WC_X + 2, GD.WC_X + 3)]
        check(cmd == [0x800000 | 25, W.WT_Y[0] + 2 * W.FRAME, W.FRAME, 3], f"the sample's frame: core 1's sample job (bit 23 | 25 -> slot 3, seq 3: {[hex(v) for v in cmd]})")
        xw[GD.WC_X + 4] = 3; log.clear(); e.call(wl["c_wttick"], maxins=40_000_000)
        check(e.r8(tb + W.T_L + 2) == 144 + 25 and not [1 for a_, _ in log if a_ == GD.WC_X], "seq 3 seen: slot 3 holds sample 25, nothing more to copy")
    else:
        check(e.r8(tb + W.T_L + 2) == 144 + 25 and not [1 for a_, _ in log if a_ == GD.WC_X], "the sample's frame: not copied (the slot taken as it is)")

    # ---- the patch (emu_sc39_4's harness: the card)
    del e
    import gc; gc.collect()
    import emu_sc39_4 as T39
    e = T39.E4(img, man); e.setup(man)
    e.btn(2); e.btn(8)
    w8 = lambda a_, v: e.uc.mem_write(a_, bytes([v]))
    e.call(wl["c_wtst"])
    for k, v in enumerate([27, 28, 169]): w8(tb + W.T_F + k, v)
    w8(tb + W.T_N, 3); w8(tb + W.T_ON, 1)
    stock = [bytes((3 + k + i) & 0x7F for i in range(340)) for k in range(8)]
    e.sd = {(3, 0, 0xFF): b"".join(stock[k] + bytes([0xFF]) * 172 for k in range(7)) + stock[7]}
    e.call(pl["c_mpsave"], 0, 3, maxins=40_000_000)
    f_ = e.sd[(3, 0, 0xFF)]; p0 = 512 * 3 + 340 + W.REC_AT; rec = bytes(f_[p0:p0 + W.REC_N])
    check(rec[0] == W.REC_SIG and rec[1] == 1 and list(rec[3:3 + rec[2]]) == [27, 28, 169], f"saved: the record at padding + 150 ({rec.hex()})")
    w8(tb + W.T_ON, 0); w8(tb + W.T_N, 0)
    e.call(pl["c_mpload"], 0, 3, maxins=40_000_000)
    got = [e.r8(tb + W.T_F + k) for k in range(e.r8(tb + W.T_N))]
    check(e.r8(tb + W.T_ON) == 1 and got == [27, 28, 169], f"loaded: the table back ({got})")
    e.call(pl["c_mpsave"], 0, 5, maxins=40_000_000)
    f_ = bytearray(e.sd[(3, 0, 0xFF)]); p5 = 512 * 5 + 340 + W.REC_AT; f_[p5:p5 + W.REC_N] = bytes([0xFF]) * W.REC_N; e.sd[(3, 0, 0xFF)] = bytes(f_)
    e.call(pl["c_mpload"], 0, 5, maxins=40_000_000)
    check(e.r8(tb + W.T_ON) == 0, f"an older patch (no record): the wavetable off ({e.r8(tb + W.T_ON)}; {bytes(e.uc.mem_read(PK.BUF + W.REC_AT, W.REC_N)).hex()})")
    print(f"{man.get('marker', '?')} WTUI ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
