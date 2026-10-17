"""SC44 ARM tests (vcf21.use_sampler, tools/smpick.py), through the controller, the real LED task, the engine's tick and the player's slot 2:
  * MIDI 1's own engine from the oscillator: pad 27 three times = VA-drum, granular, the sample (c_vsmode = 1, pad 27 cyan); the tick's ACT
    message = 3 (the granular bit gone); pad 27 once more = the FX sequencer (c_vsmode = 0);
  * its expanded Note view (Note twice) in the sample mode = the picker: a sample pad = code 25 (the track's sample), its note 60 through the
    transmitter (MIDI 1, velocity of the pad) and the pending flip 0xC0 | s; the release = the note-off; Octave down / up = the pages (16 more,
    no wrap; Octave LEDs lit when there is a page that way); its LEDs: the track's sample cyan, the others dim;
  * a step held + a sample = that step's flip (lane 8, its six micro steps, 0x80 | s); Clear + step = none (0xFF); the step LEDs: a flip peach, none dim cyan (the background);
  * the stock's lane player of MIDI 1 (0x0804BA8C every micro step, 0x0804BB02 at the start; lane 8 = the track's level, id 62): a level value
    (0x27) is still sent, a flip (0x80 | s) is not;
  * the tick: TRIG = $100 | s with a pending flip (taken: the byte back to 0), else 1;
  * the player's slot 2 (MIDI 1's player): a micro step of a step with a flip = the pending byte 0xC0 | flip; one without = 0;
  * recording (Play + Record): a sample pad = the recorder's note-on gate (note 60) and the flip in the step playing;
  * out of the sample mode: the picker's pads are the stock's (code 25 untouched), the player's slot 2 leaves the pending byte;
  * the FX sequencer one press later (pad 27 six times from off): emu_sc40_9.seq_part as before (emu_sc41's check presses five times: the sample).

    python tools/emu_sc44.py SC44.bin SC44_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import smpick as SP  # noqa: E402
import arp as A  # noqa: E402

V = T4.V
MGR = X.MGR
BASE = 0x08010000
LP_VT, LP_STEP, LP_START = 0x0805ADB4, 0x0804BA8C, 0x0804BB02   # the note tracks' lane player: its class, a micro step, the pattern's start


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    e = X.EP(img, man)
    sl = {k: int(v, 16) for k, v in man["report"]["smpick"]["labels"].items()}
    al = {k: int(v, 16) for k, v in man["report"]["arp"]["labels"].items()}
    dw, recs = [], []
    def w(uc, a, s, d): dw.append((uc.reg_read(UC_ARM_REG_R1) >> 8, uc.reg_read(UC_ARM_REG_R2)))
    e.uc.hook_add(UC_HOOK_CODE, w, begin=0x080292F8, end=0x080292F8)
    def rec(uc, a, s, d):
        recs.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3))); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    for f in (SP.REC_ON, SP.REC_OFF): e.uc.hook_add(UC_HOOK_CODE, rec, begin=f, end=f)
    tick = lambda n=1: [(e.at(e.t + 40), e.call(e.vl["c_vtick"], maxins=3_000_000)) for _ in range(n)]
    smode = lambda t=0: e.r0(e.vl["c_vsmode"], t)
    tail = e.r32(V.LS_SESSION + 0x14) + V.LS_TAIL
    pend = lambda t=0: e.r8(tail + V.SM_PEND[t])
    lane = lambda step, t=0: bytes(e.uc.mem_read(e.r0(sl["c_splb"], t, step), 6))
    # pad 27: oscillator -> VA-drum -> granular -> the sample
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    tick(10)
    e.btn(2); e.btn(8)
    seq = []
    for _ in range(3): e.pad(26); seq.append(smode())
    f = X.frame(e)
    check(seq == [0, 0, 1] and f[26] & 0xFF == V.COL_SM, f"pad 27 three times from the oscillator: the sample on the third ({seq}), pad 27 cyan ({f[26]:#x})")
    e.pad(26); e.pad(26); e.pad(26); e.pad(26); e.pad(26); e.pad(26)        # around the cycle (FX sequencer, off, line, osc, VA-drum, granular)
    e.pad(26); back = smode()
    dw.clear(); tick(12)
    acts = [v for v, a_ in dw if a_ == V.VB0 and (v >> 16) & 0x7F == 19]
    check(back == 1 and acts and all(v & 3 == 3 and not v & 0x1000 for v in acts), f"once around the cycle: the sample again ({back}); the tick's ACT = 3 ({[hex(v) for v in acts[:3]]})")
    # the picker
    for _ in range(3):
        if e.r8(MGR + SP.S_CUR) == SP.PICK[0]: break
        e.btn(9)
    cur = e.r8(MGR + SP.S_CUR)
    check(cur == SP.PICK[0] and e.r0(sl["c_spk"]) == 0, f"Note twice: the expanded Note view ({cur}), the picker of MIDI 1 (c_spk {e.r0(sl['c_spk'])})")
    e.ons.clear()
    e.call(PRESS, MGR, 16 + 5, 90, maxins=8_000_000)
    v25, p5, on = e.val(0, 25), pend(), list(e.ons)
    e.call(RELEASE, MGR, 16 + 5, maxins=8_000_000); off = e.ons[len(on):]
    check(v25 == 5 and p5 == 0xC5 and on == [("on", 2, 60, 90)] and off and off[0][:3] == ("off", 2, 60),
          f"a sample pad: code 25 = {v25}, pending {p5:#x}, the note {on}, its release {off}")
    f = X.frame(e)
    check(f[16 + 5] & 0xFF == SP.COL_SEL and f[16 + 6] & 0xFF == SP.COL_DIM and f[SP.LED_DOWN] & 0xFF == SP.COL_BTN and f[SP.LED_UP] & 0xFF == 0,
          f"the LEDs: the sample cyan ({f[21]:#x}), the others dim ({f[22]:#x}); Octave down lit ({f[SP.LED_DOWN]:#x}), up dark ({f[SP.LED_UP]:#x})")
    for _ in range(5): e.btn(SP.ID_DOWN)
    e.pad(16 + 1); v_last = e.val(0, 25); f3 = X.frame(e)
    e.btn(SP.ID_UP); e.pad(16 + 2); v_mid = e.val(0, 25)
    check(v_last == 49 and v_mid == 34 and f3[SP.LED_DOWN] & 0xFF == 0 and f3[SP.LED_UP] & 0xFF == SP.COL_BTN,
          f"Octave down x5 = the last page (sample {v_last}), up = page 3 (sample {v_mid}); on the last page Octave down dark, up lit")
    # flips
    e.call(PRESS, MGR, 3, 100, maxins=8_000_000)
    e.pad(16 + 7)
    held = e.r8(e.r0(sl["c_spst"]) + 1)
    f = X.frame(e)
    e.call(RELEASE, MGR, 3, maxins=8_000_000)
    l3 = lane(3)
    check(l3 == bytes([0x80 | 39]) * 6 and e.val(0, 25) == 34 and held == 4 and f[3] & 0xFF == SP.COL_HELD and f[16 + 7] & 0xFF == SP.COL_HF,
          f"step 4 held + sample 39: its flip ({l3.hex()}), the track's sample unchanged ({e.val(0, 25)}); LEDs held step / its flip ({f[3]:#x}, {f[23]:#x})")
    e.call(PRESS, MGR, 9, 100, maxins=8_000_000); e.pad(16 + 0); e.call(RELEASE, MGR, 9, maxins=8_000_000)
    f = X.frame(e)
    check(lane(9) == bytes([0x80 | 32]) * 6 and f[3] & 0xFF == SP.COL_FLIP and f[9] & 0xFF == SP.COL_FLIP and f[4] & 0xFF == SP.COL_STEP and e.r8(e.r0(sl["c_spst"]) + 1) == 0,
          f"step 10 + sample 32 ({lane(9).hex()}); the step LEDs: flips peach ({f[3]:#x}, {f[9]:#x}), none dim cyan ({f[4]:#x}); no step held after the release")
    clr = e.r32(e.r32(MGR + SP.HELD) + 0xC)
    e.set_p0(clr, 1); e.pad(9); e.set_p0(clr, 0)
    check(lane(9) == b"\xff" * 6 and lane(3) == bytes([0x80 | 39]) * 6, f"Clear + step 10: no flip ({lane(9).hex()}); step 4 kept")
    e.btn(SP.ID_HALF); e.call(PRESS, MGR, 0, 100, maxins=8_000_000); e.pad(16 + 3); e.call(RELEASE, MGR, 0, maxins=8_000_000); e.btn(SP.ID_HALF)
    f = X.frame(e)
    check(lane(16) == bytes([0x80 | 35]) * 6 and lane(0) == b"\xff" * 6 and f[0] & 0xFF == SP.COL_STEP, f"1-16 / 17-32: step 17 + sample 35 ({lane(16).hex()}), step 1 untouched")
    # the stock's lane player of MIDI 1 (its object: vtable 0x0805ADB4, lane ids [+ 0x58] from 20): lane 8 = the level (id 62)
    ram = bytes(e.uc.mem_read(0x20000000, 0x50000)); ur = lambda a_: struct.unpack_from("<I", ram, a_ - 0x20000000)[0]
    lp = next(o for o in range(0x20000000, 0x2004FF80, 4) if ur(o) == LP_VT and 0x20000000 <= ur(o + 0x58) < 0x20050000 or
              ur(o) == LP_VT and 0x08010000 <= ur(o + 0x58) < 0x08080000 and e.r8(ur(o + 0x58)) == 20)
    ids = bytes(e.uc.mem_read(e.r32(lp + 0x58), 12))
    emit = e.r32(e.r32(e.r32(lp + 0x54))) & ~1; sent = []
    def em(uc, a_, s_, d_): sent.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2))); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, em, begin=emit, end=emit)
    stp = e.r32(lp + 0x18)
    for fn in (0x080354FA, 0x0803542C): e.call(fn, stp, 1); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes([3]))
    l8 = e.r0(sl["c_splb"], 0, 3)
    def play(byte, fn):
        e.uc.mem_write(l8, bytes([byte]) * 6); e.uc.mem_write(lp + 0x7E, bytes([0xFF])); sent.clear()
        e.call(fn, lp, maxins=4_000_000); return [v for i_, v in sent if i_ == ids[8]]
    lv1, lv2, fl1, fl2 = play(0x27, LP_STEP), play(0x27, LP_START), play(0x80 | 39, LP_STEP), play(0x80 | 39, LP_START)
    check(ids[8] == 62 and lv1 == [0x27] and lv2 == [0x27] and fl1 == [] and fl2 == [],
          f"the stock's lane player: lane 8 = the level (id {ids[8]}); level automation 0x27 sent ({lv1}, at the start {lv2}), a flip not ({fl1}, {fl2})")
    e.uc.mem_write(l8, bytes([0x80 | 39]) * 6)
    # the tick's TRIG
    def trig(byte):
        e.uc.mem_write(tail + V.SM_PEND[0], bytes([byte]))
        rt = V.TAIL + V.O_RT; e.uc.mem_write(rt + V.RT_AUX, bytes([e.r8(rt + V.RT_AUX) | 0x10]))
        dw.clear(); tick(6)
        return [v & 0xFFFF for v, a_ in dw if a_ == V.VB0 and (v >> 16) & 0x7F == 21], pend()
    t1, p1 = trig(0xC0 | 39); t2, p2 = trig(0)
    check(t1[:1] == [0x127] and p1 == 0 and t2[:1] == [1], f"the tick: TRIG with a pending flip {[hex(x) for x in t1]} (pending after: {p1:#x}), without {t2}")
    # the player's slot 2
    ply, pat = e.r0(al["c_arply"], 2), e.r0(al["c_arpat"], 2)
    slot2 = u(A.PLAYER_VT + 8)
    def micro(step, m, before=0x55):
        e.uc.mem_write(tail + V.SM_PEND[0], bytes([before])); e.call(slot2 & ~1, ply, pat, step, m, maxins=8_000_000); return pend()
    e.uc.mem_write(e.r0(sl["c_splb"], 0, 5), bytes([0x27]) * 6)
    m1, m2, m3, m4 = micro(3, 0), micro(3, 5), micro(4, 0), micro(5, 0)
    check(slot2 == sl["c_spply"] | 1 and m1 == 0xC0 | 39 and m2 == 0xC0 | 39 and m3 == 0 and m4 == 0,
          f"the player's slot 2: step 4 micro 0 / 5 = {m1:#x} / {m2:#x}, step 5 (none) = {m3:#x}, step 6 (level automation 0x27) = {m4:#x}")
    # recording
    e.transport(1)
    for fn in (0x080354FA, 0x0803542C):
        e.call(fn, SP.TRANSPORT, 1); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes([1]))
    st = e.r0(sl["c_spstep"], 0)
    recs.clear(); e.pad(16 + 12); r = list(recs)
    check(r[:2] == [(60, 100, 2), (60, 2, 0)] or (r and r[0] == (60, 100, 2)), f"recording: the recorder's gate gets note 60 ({r})")
    check(lane(st) == bytes([0x80 | 44]) * 6, f"recording: the flip in the step playing ({st + 1}: {lane(st).hex()})")
    e.transport(0)
    for fn in (0x080354FA, 0x0803542C):
        e.call(fn, SP.TRANSPORT, 1); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes([0]))
    # out of the sample mode
    e.btn(2); e.btn(8); e.pad(26); nm = smode()
    for _ in range(3):
        if e.r8(MGR + SP.S_CUR) == SP.PICK[0]: break
        e.btn(9)
    v0 = e.val(0, 25); e.pad(16 + 9); v1 = e.val(0, 25)
    m5 = micro(3, 0)
    check(nm == 0 and e.r0(sl["c_spk"]) == 0xFF and v0 == v1 and m5 == 0x55, f"the FX sequencer: no picker (code 25 {v0} -> {v1}), the slot 2 leaves the pending byte ({m5:#x})")
    del e; gc.collect()
    import emu_sc40_9 as T9
    fsq, step, s2 = T9.seq_part(img, man, presses=6)
    check(fsq == 1 and step == 7 and s2 == [0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 5, 0, 0], f"pad 27 six times from off = the FX sequencer (after the sample), as before: its track's step, its selector knob ({s2})")
    gc.collect()
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
