"""SC19.9 ARM tests: distortion type (Shift + K8) per drum saved with the project (persist19.EXTRAS), the Master FX step jump that repeats while its step pad is held,
and the Master FX knob LEDs with the value as brightness.

    python tools/emu_sc19_9.py SC19.8.bin SC19.9.bin SC19.8_manifest.json SC19.9_manifest.json
Real routes: the controller's knob and pad paths, the DSP service tick (c_dtick19), the sequencer tick (c_sptick), the stock save and apply, on the live RAM dump.
Distortion type:
  * Shift + K8: type + 1 / - 1 (wraps 0..3); Shift + K6 does nothing (the filter slope was discarded); the other bits of the byte are untouched;
  * the 12 bits (3 per drum, the third unused) sit in the bytes of XT_BITS; the bits of drum 0 are in the byte 8 of drums 1 and 2;
  * the tick sends the extended-values word with the type in bits 8-9 (the start point / bitcrush nibbles as before) to the drum's mailbox;
  * save -> wipe -> load: the types come back; a project without them (zero bits) reads the stock distortion; the LED of K8 with Shift shows the type (0 / 42 / 84 / 126).
Step jump (pad 7 held or sticky enables it; then a step pad 1-16):
  * the step plays at the next step boundary and is repeated at every boundary while that step pad stays pressed; released: no more jumps, the song goes on;
  * a tap that ends before the boundary jumps once; a second step pad moves the target (the older pad's release changes nothing); pad 7 released while the step pad is held:
    still repeats; pad 8 ends it; without pad 7 a step pad is the normal song pointer.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc19_8 import EW  # noqa: E402
from emu_sc19_6 import MGR, DCODE  # noqa: E402
from emu_sc17_7 import E7  # noqa: E402
import emu_sc19 as T19  # noqa: E402
import build_sc17 as B  # noqa: E402
import persist19 as P  # noqa: E402
import drums2_dsp as DD  # noqa: E402

JT = B.GFX_OFF + B.S_JT


def main(prev, img, man8, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]["persist19"]
    lab = {k: int(v, 16) for k, v in rep["labels"].items()}
    check(rep.get("extras") is True and not rep.get("extras_slope") and not man8["report"]["persist19"].get("extras"), "manifest: extras on, no slope (SC19.9); off in SC19.8")
    check(man["report"]["sc17"].get("jump_hold") is True and man["report"]["sc17"].get("knob_bright") is True, "manifest: jump_hold, knob_bright")
    gc.collect(); e = EW(img, man)
    xt = lambda d: sum(((e.xm(P.XT_BITS[3 * d + j][0]) & P.XT_BITS[3 * d + j][1]) != 0) << j for j in range(3))
    check(len(set(P.XT_BITS)) == 12 and all(i != P.XM_SIG for i, m in P.XT_BITS) and all(m & 7 == 0 for i, m in P.XT_BITS), "the 12 bits are distinct, outside the mode bits and the signature byte")
    for i in range(P.N_XM): e.setxm(i, 0)
    e.setxm(P.XM_SIG, P.SIG << 3 | 3)
    for d in range(4):
        e.sel(d)
        before = e.xmall(); e.knob19(5, 1, shift=True); e.knob19(5, -1, shift=True)
        check(e.xmall() == before and xt(d) == 0, f"drum {d + 1}: Shift + K6 does nothing")
        for step, want in ((1, 1), (1, 2), (1, 3), (1, 0), (-1, 3)):
            before = e.xmall()
            e.knob19(7, step, shift=True)
            after = e.xmall(); chg = [i for i in range(P.N_XM) if after[i] != before[i]]
            check(xt(d) == want and all(i in [x[0] for x in P.XT_BITS[3 * d:3 * d + 3]] for i in chg), f"drum {d + 1}: Shift + K8 {step:+d} -> type {want}, only its bits changed {chg}")
    check(all(xt(d) == 3 for d in range(4)) and e.xm(P.XM_SIG) == (P.SIG << 3 | 3), "the four drums independent; signature and mode of drum 0 untouched")
    e.drain(8)
    for d in range(4): e.sel(d); e.knob19(7, 1, shift=True)
    for d in range(4): e.setxm(P.XM_DRUMS + 9 * d + 3, e.xm(P.XM_DRUMS + 9 * d + 3) | 0x80)
    out = e.drain(14)
    ext = {}
    for m in out:
        for (_, w, ad) in m:
            for d in range(4):
                if ad == DD.DB + DD.STRIDE * d + DD.EXT: ext[d] = w
    check(all(d in ext for d in range(4)), f"the tick sends the extended-values word of the four drums {[hex(ext.get(d, -1)) for d in range(4)]}")
    check(all(((ext[d] >> 8) & 7) == xt(d) for d in ext) and all(ext[d] & 0xFF == e.dext(d) for d in ext), "word = extended nibbles | type << 8")
    vals = {0: 1, 1: 2, 2: 3, 3: 1}
    for d, v in vals.items():
        for j in range(3):
            i, m = P.XT_BITS[3 * d + j]; b = e.xm(i); e.setxm(i, (b | m) if (v >> j) & 1 else (b & ~m))
    e.call(lab["c_pl_save"], T19.OBJ, maxins=8_000_000)
    saved = e.xmall()
    for i in range(P.N_XM): e.setxm(i, 0)
    e.drain(12); e.apply(0); e.drain(14)
    check(e.xmall() == saved and [xt(d) for d in range(4)] == [1, 2, 3, 1], f"save -> wipe -> load: the types come back {[xt(d) for d in range(4)]}")
    for i, m in P.XT_BITS: e.setxm(i, e.xm(i) & ~m)
    check([xt(d) for d in range(4)] == [0, 0, 0, 0], "a project saved before: the stock distortion")
    for d in range(4):
        e.track(4 + d)
        for typ in range(4):
            for j in range(3):
                i, m = P.XT_BITS[3 * d + j]; b = e.xm(i); e.setxm(i, (b | m) if (typ >> j) & 1 else (b & ~m))
            e.set_p0(e.r32(MGR + 0xC), 1); f = e.frame(); f2 = e.frame(); e.set_p0(e.r32(MGR + 0xC), 0)
            k = f[60:68]
            if not (f == f2 and (k[7] >> 8) - 2 == typ * 42 and (k[7] & 0xFF) == DCODE[d] and (k[5] & 0xFF) == DCODE[d]): check(False, f"drum {d + 1}: type {typ}: LEDs {[hex(x) for x in k]}")
        check(True, f"drum {d + 1}: Shift + K8 LED follows the type")

    # ---- the step jump: repeats while its step pad is held
    jstate = lambda x: x.s14b(JT)
    def fresh():
        gc.collect(); x = E7(img, man); x.grid(); x.setsp(); return x
    x = fresh(); P_ = x.step_pad
    x.pad(6); x.pad(P_(9)); x.rel(6)                                              # pad 7 released, the step pad still held
    check(jstate(x) == (9 | 0x40), f"pad 7 held + step 9 (pressed): target 9, pad held {jstate(x):#x}")
    x.set_ticks(20); seq = x.tick(3 + 6 * 3)
    check(seq[:3] == [21, 22, 23] and seq[3:] == [48, 49, 50, 51, 52, 53] * 3 and x.sets == [47] * 3, f"the step pad held (pad 7 already released): 21, 22, 23, then step 9 again and again {seq[:12]}")
    check(jstate(x) == (9 | 0x40 | 0x80), f"target kept, jumped-once mark {jstate(x):#x}")
    x.rel(P_(9)); check(jstate(x) == 0, "the step pad released: the jump state is cleared at once")
    seq2 = x.tick(12)
    check(seq2 == list(range(54, 66)) and len(x.sets) == 3, f"released in the middle: no more jumps, the song goes on {seq2[:6]}")
    x = fresh()
    x.pad(6); x.pad(P_(9)); x.rel(P_(9)); x.rel(6)
    check(jstate(x) == 9, f"a tap that ends before the boundary: one jump pending {jstate(x):#x}")
    x.set_ticks(20); seq = x.tick(3 + 6 + 2)
    check(seq == [21, 22, 23, 48, 49, 50, 51, 52, 53, 54, 55] and jstate(x) == 0 and x.sets == [47], f"one jump, then the song goes on {seq}")
    x = fresh()
    x.pad(6, shift=True); x.rel(6)                                                # sticky
    x.pad(P_(3)); x.set_ticks(38)
    seq = x.tick(3 + 12)
    check(seq == [39, 40, 41] + [12, 13, 14, 15, 16, 17] * 2, f"sticky pad 7 + step 3 held: repeats {seq[:10]}")
    x.rel(P_(3))
    seq = x.tick(8)
    check(jstate(x) == 0 and seq == list(range(18, 26)) and x.s14b(B.GFX_OFF + B.S_JF) == 2, f"released: stops; pad 7 stays sticky {seq[:5]}")
    x = fresh()
    x.pad(6); x.pad(P_(9)); x.pad(P_(3)); x.set_ticks(20)
    check(jstate(x) == (3 | 0x40), f"a second step pad moves the target {jstate(x):#x}")
    seq = x.tick(3 + 6)
    check(seq == [21, 22, 23] + [12, 13, 14, 15, 16, 17], f"the last pad is the target {seq}")
    x.rel(P_(9))
    seq = x.tick(7)
    check(seq == [12, 13, 14, 15, 16, 17, 12], f"the older pad's release changes nothing: keeps repeating step 3 {seq}")
    x.rel(P_(3)); check(jstate(x) == 0, "the target pad released: stops")
    x = fresh()
    x.pad(P_(5)); check(jstate(x) == 0 and x.sp()[2] == 5, f"without pad 7 a step pad is the normal song pointer {x.sp()} {jstate(x)}")
    x.rel(P_(5))
    x = fresh()
    x.pad(6); x.pad(P_(9)); x.set_ticks(20); x.tick(5)
    x.pad(7); x.rel(7)
    check(jstate(x) == 0, "pad 8 clears the jump")

    # ---- Master FX knob LEDs: colour | (value + 2) << 8
    x = fresh()
    pal = [(int(a, 16), int(b, 16)) for a, b in man["report"]["sc17"]["pal_codes"]]
    from unicorn.arm_const import UC_ARM_REG_R0
    import struct
    def task(y):
        buf = 0x2006E000; y.call(0x08034196, MGR, buf, maxins=900000)
        return list(struct.unpack("<69H", bytes(y.uc.mem_read(buf, 138))))
    t = task(x)
    want = [pal[0][0] | ((B.DEFAULTS[B.SETMAP[0]][k] + 2) << 8) for k in range(4)]
    check(t[60:64] == want and t[64:68] == [0] * 4, f"Master FX knob LEDs: Gater colour + value brightness {[hex(v) for v in t[60:68]]}")
    x.call(0x08033848, MGR, 0, (-20) & 0xFFFFFFFF, maxins=900000)
    t2 = task(x)
    check((t2[60] >> 8) == (t[60] >> 8) - 20 and t2[61:64] == t[61:64], f"a knob turn changes its LED brightness ({(t[60] >> 8) - 2} -> {(t2[60] >> 8) - 2})")
    print("SC19.9 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text()), json.loads(Path(a[4]).read_text())) else 0)
