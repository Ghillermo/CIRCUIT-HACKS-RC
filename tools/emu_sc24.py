"""SC24 ARM tests (the VCA-VCF mode of the MIDI tracks) through the real routes (pads 0x08033282, knobs 0x08033848, the LED frame, the note vtable, the DSP service tick):

    python tools/emu_sc24.py SC24.bin SC24_manifest.json
  * boot: the volatile values of the second oscillator in the Master FX block, the default note of the second oscillator;
  * pad 27: off -> line in with VCA / VCF (orange) -> oscillator (green) -> off; the page starts at VCA / VCF; ACT = 1 / 2 / 0 reaches the DSP;
  * pads 28 / 29 (one / two oscillators, the chain order) only with the mode on; ACT carries bit 9 / bit 8; the LEDs;
  * pads 1-8: the page row (1 VCA / VCF, 2 OSC1, 3 OSC2 with two oscillators) with the mode on; the stock templates otherwise and while the CC editor is on;
  * the knob pages: page B has MIX (Shift + K2) and BITSYNC (Shift + K3), page C the second oscillator (TUNE2 / SHAPE2 / WAVE2, FINE2 / FM / RING); the values are volatile (heap block) and swept to the DSP
    as the codes 32..39; clamps; Clear + a knob;
  * paraphonic notes: one note = both oscillators, two notes = one each, the third replaces the older, a release hands the note over.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc23_5 as T5  # noqa: E402,F401  (applies the SC23.x options)
import emu_sc22_4 as T4  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
V = T4.V
V.use_pads2(); V.use_edv2(); V.use_saveled(); V.use_typezones(); V.use_dualui()
E20, MGR, TMPL = T4.E20, T4.MGR, T4.TMPL
HAL = 0x2000081C


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
    gc.collect(); e = E20(img, man)
    sgn = lambda v: v - 0x10000 if v & 0x8000 else v
    gfst = int(man["report"]["sc17"]["labels"]["c_gfst"], 16)
    def block():
        e.call(gfst); return e.uc.reg_read(UC_ARM_REG_R0)
    v2 = lambda t, k: struct.unpack("b", bytes([e.r8(block() + V.V2_OFF + 8 * t + k)]))[0]
    n2 = lambda t: e.tailb(V.O_PAR + V.STRIDE * t + 13)
    n1 = lambda t: e.rt(t, V.RT_NOTE) & 0x7F
    cnt = lambda t: e.rt(t, V.RT_CNT) & 15
    page = lambda t: (e.rt(t, V.RT_TAG) >> 1) & 3
    def ticks(n=40, voice=0):
        out = []
        for _ in range(n):
            for w, ad in e.vtick():
                if ad == VD.VB0 + voice * VD.VBS: out.append(((w >> 16) & 0x7F, sgn(w & 0xFFFF)))
        return out
    for _ in range(30): e.vtick()
    check(block() != 0, "the Master FX block exists")
    check(all(v2(t, k) == V.DEFAULTS_V2[k] for t in (0, 1) for k in range(8)), f"volatile values at boot: {[v2(0, k) for k in range(8)]}")
    check(n2(0) == 60 and n2(1) == 60 and e.tailb(V.O_SIG) == (0xB0 if man["marker"] in ("SC26", "SC27", "SC28", "SC29", "SC30", "SC31", "SC32", "SC33", "SC34") else 0xAF), f"the default note of the second oscillator {n2(0)} / {n2(1)}, signature {e.tailb(V.O_SIG):#x}")
    check(block() + V.V2_OFF + 16 == 0x20044E58, "the block (with the 16 new bytes) ends at the stock heap limit")

    # ---------------------------------------------------------------- pad 27
    e.btn(2); e.btn(8)
    check(e.cur() == 18, f"MIDI 1 + Preset: view index {e.cur()}")
    pad = lambda p: (e.padr(p), e.rel(p))
    led = lambda: e.tleds(TMPL[0])
    L0 = led()
    check(L0[V.PAD_OSC] == 0 and L0[V.PAD_PAGE] == 0 and L0[V.PAD_VCF] == 0, f"mode off: pads 27 / 28 / 29 dark ({L0[V.PAD_OSC]:#x}, {L0[V.PAD_PAGE]:#x}, {L0[V.PAD_VCF]:#x})")
    ticks(20)
    pad(V.PAD_PAGE); pad(V.PAD_VCF)
    check(e.rt(0, V.RT_VEL) & 0x80 == 0 and e.rt(0, V.RT_NOTE) & 0x80 == 0, "pads 28 / 29 do nothing with the mode off")
    pad(3); pad(1)
    check(page(0) == 0, "pads 1-8 are stock with the mode off (the page does not move)")
    pad(V.PAD_OSC)
    check(e.tailb(V.O_FLAGS) & 0x05 == 0x01 and led()[V.PAD_OSC] == V.COL_ON, f"pad 27 once: mode on, source line (flags {e.tailb(V.O_FLAGS):#x}), orange {led()[V.PAD_OSC]:#x}")
    ms = ticks(40)
    act = [v for c, v in ms if c == 19]
    check(act and act[0] == 1, f"ACT = 1 reaches the DSP {act[:3]}")
    pad(V.PAD_OSC)
    check(e.tailb(V.O_FLAGS) & 0x05 == 0x05 and led()[V.PAD_OSC] == V.COL_OSC[0], f"pad 27 twice: oscillator (flags {e.tailb(V.O_FLAGS):#x}), green {led()[V.PAD_OSC]:#x}")
    act = [v for c, v in ticks(30) if c == 19]
    check(act and act[0] == 2, f"ACT = 2 {act[:3]}")
    pad(V.PAD_OSC)
    if man["marker"] in ("SC29", "SC30", "SC31", "SC32", "SC33", "SC34"): pad(V.PAD_OSC)                                    # SC29: a fourth state (VA-drum) before off
    check(e.tailb(V.O_FLAGS) & 0x05 == 0 and led()[V.PAD_OSC] == 0, f"pad 27 three times: off (flags {e.tailb(V.O_FLAGS):#x}), dark")
    act = [v for c, v in ticks(30) if c == 19]
    check(act and act[0] == 0, f"ACT = 0 {act[:3]}")
    pad(V.PAD_OSC); pad(V.PAD_OSC)                                                # oscillator, for the rest
    # ---------------------------------------------------------------- pads 28 / 29 and the ACT flags
    L0 = led()
    check(L0[V.PAD_PAGE] == V.COL_OSC[1] and L0[V.PAD_VCF] == V.COL_ROUTE[1], f"mode on: pads 28 / 29 dim ({L0[V.PAD_PAGE]:#x}, {L0[V.PAD_VCF]:#x})")
    pad(V.PAD_VCF)
    check(e.rt(0, V.RT_NOTE) & 0x80 and led()[V.PAD_VCF] == V.COL_ROUTE[0], f"pad 29: chain order VCF, VCA, FX (bit 7 of RT_NOTE), lit {led()[V.PAD_VCF]:#x}")
    act = [v for c, v in ticks(30) if c == 19]
    check(act and act[0] == 2 | (1 << 8), f"ACT = 2 | route << 8 = {act[:2]}")
    pad(V.PAD_PAGE)
    check(e.rt(0, V.RT_VEL) & 0x80 and led()[V.PAD_PAGE] == V.COL_OSC[0], f"pad 28: two oscillators (bit 7 of RT_VEL), lit {led()[V.PAD_PAGE]:#x}")
    act = [v for c, v in ticks(30) if c == 19]
    check(act and act[0] == 2 | (1 << 8) | (1 << 9), f"ACT = 2 | route << 8 | dual << 9 = {act[:2]}")
    # the second track is independent
    check(e.rt(1, V.RT_VEL) & 0x80 == 0 and e.rt(1, V.RT_NOTE) & 0x80 == 0, "MIDI 2 keeps one oscillator and the VCA, FX, VCF order")
    pad(V.PAD_VCF); pad(V.PAD_PAGE)                                               # back to one oscillator / the first order
    check(e.rt(0, V.RT_VEL) & 0x80 == 0 and e.rt(0, V.RT_NOTE) & 0x80 == 0, "pads 28 / 29 again: back")
    act = [v for c, v in ticks(30) if c == 19]
    check(act and act[0] == 2, f"ACT = 2 {act[:2]}")

    # ---------------------------------------------------------------- the page row
    L0 = led()
    cols = [L0[k] for k in range(8)]
    p5 = [0x2E, 0x37] if man["marker"] in ("SC27", "SC28", "SC29", "SC30", "SC31", "SC32", "SC33", "SC34") else [0, 0]         # SC27: two more pages (pads 4 / 5), dim
    check(cols == [V.COL_PAGE[0][0], V.COL_PAGE[1][1], 0] + p5 + [0, 0, 0] and page(0) == 0, f"page row (pages VCA / VCF selected, one oscillator): {[hex(c) for c in cols]}")
    pad(2)
    check(page(0) == 0, "pad 3 with one oscillator: nothing")
    pad(1)
    check(page(0) == 1 and [led()[k] for k in range(3)] == [V.COL_PAGE[0][1], V.COL_PAGE[1][0], 0], f"pad 2: OSC1 page {page(0)}, LEDs {[hex(led()[k]) for k in range(3)]}")
    pad(5)
    check(page(0) == 1, "pads 6-8: nothing")
    pad(V.PAD_PAGE); pad(2)
    check(page(0) == 2 and [led()[k] for k in range(3)] == [V.COL_PAGE[0][1], V.COL_PAGE[1][1], V.COL_PAGE[2][0]], f"two oscillators, pad 3: OSC2 page {page(0)}, LEDs {[hex(led()[k]) for k in range(3)]}")
    pad(V.PAD_PAGE)
    check(page(0) == 0 and led()[2] == 0, "back to one oscillator: the OSC2 page is gone (page 0)")
    pad(V.PAD_PAGE); pad(2)                                                       # for the knob tests: OSC2 page
    # ---------------------------------------------------------------- knobs
    e.btn(2)                                                                      # the track view
    e.track(2)
    # page C (OSC2)
    e.knob_raw(0, 12); e.knob_raw(0, 7, True); e.knob_raw(1, 80); e.knob_raw(6, 5); e.knob_raw(1, 33, True); e.knob_raw(2, 44, True)
    check((v2(0, 0), v2(0, 1), v2(0, 3), v2(0, 2), v2(0, 6), v2(0, 7)) == (12, 7, 100, 5, 33, 44), f"OSC2 page: TUNE2 {v2(0, 0)}, FINE2 {v2(0, 1)}, SHAPE2 {v2(0, 3)} (clamped to 100), WAVE2 {v2(0, 2)}, FM {v2(0, 6)}, RING {v2(0, 7)}")
    e.knob_raw(0, -127); e.knob_raw(0, 127)
    check(v2(0, 0) == 63, f"TUNE2 clamps at +63 ({v2(0, 0)})"); e.knob_raw(0, -127, False)
    check(v2(0, 0) == -64, "and at -64")
    e.knob_raw(6, 500); check(v2(0, 2) == 127, f"WAVE2 clamps at 127 ({v2(0, 2)})")
    e.knob_raw(1, -500, True); check(v2(0, 6) == 0, "FM clamps at 0")
    check(e.val(0, 1) == V.DEFAULTS[0] and e.val(0, 19) == 0, "the tail values are untouched by the OSC2 page")
    fr = e.frame()
    check(fr[60] != fr[61], "knob LEDs drawn")
    # the LED of K7 (WAVE2) is a type LED like WAVE
    def tled(code, p):
        if code == 29:
            t, m = 0, p
            while m >= 42: m -= 42; t += 1
            f, col = m * 3, V.TCOL_WV[t]
        else:
            t, f = (7 * p) >> 7, (7 * p) & 127
            col = V.TCOL_BS[t]
        return col | ((V.TZ_MINB + ((f * (127 - V.TZ_MINB)) >> 7) + 2) << 8)
    e.knob_raw(6, -500); e.knob_raw(6, 50)
    fr = e.frame()
    check(fr[66] == tled(29, 50), f"WAVE2 LED: colour of the wave + brightness of the morph {fr[66]:#x} (expected {tled(29, 50):#x})")
    # page B: MIX / BITSYNC
    e.padr(1); e.rel(1)                                                           # (the view is the track view: the pad is a track pad) -> go to the Preset view to select the page
    e.btn(2); e.btn(8)
    pad(1)
    check(page(0) == 1, "page B selected in the Preset view")
    e.btn(2)
    e.track(2)
    e.knob_raw(1, 10, True); e.knob_raw(2, 60, True)
    check(v2(0, 4) == 74 and v2(0, 5) == 60, f"page B: MIX (Shift + K2) {v2(0, 4)}, BITSYNC (Shift + K3) {v2(0, 5)}")
    e.knob_raw(2, -127, True); e.knob_raw(2, 127, True)
    check(v2(0, 5) == 127, "BITSYNC clamps at 127 (no wrap-around)")
    HELD = lambda: e.set_p0(e.r32(MGR + 0xC), 1)
    FREE = lambda: e.set_p0(e.r32(MGR + 0xC), 0)
    HELD(); fs = e.frame(); FREE()
    check(fs[62] == tled(32, 127), f"BITSYNC LED {fs[62]:#x} (expected {tled(32, 127):#x}: the nand colour, the end of the zone)")
    e.knob_raw(2, -127, True); e.knob_raw(2, 40, True)
    HELD(); fs = e.frame(); FREE()
    check(fs[62] == tled(32, 40), f"BITSYNC 40: zone {(7 * 40) >> 7}, LED {fs[62]:#x} (expected {tled(32, 40):#x})")
    # the sweep: the volatile values reach the DSP as the codes 32..39
    ms = ticks(60)
    sw = {c: v for c, v in ms if 32 <= c <= 39}
    check(set(sw) == set(range(32, 40)) and sw[36] == 74 and sw[37] == 40 and sw[32] == -64 and sw[34] == 50 and sw[38] == 0 and sw[39] == 44 and sw[35] == 100,
          f"the sweep sends the eight values: {sw}")
    order = [c for c, v in ms if 32 <= c <= 39]
    check(all(order[k + 1] == (order[k] - 31) % 8 + 32 for k in range(len(order) - 1)), f"round robin ({order[:10]})")
    # Clear + a knob on page C / B
    clr_dn = lambda: e.call(0x08033320, MGR, 23, maxins=900000)
    clr_up = lambda: e.call(0x0803381A, MGR, 23, maxins=900000)
    clr_dn(); e.knob_raw(2, 1); clr_up()
    check(v2(0, 5) == 0, f"Clear + K3 on page B: BITSYNC (Shift layer) back to 0 ({v2(0, 5)})")
    clr_dn(); e.knob_raw(1, 1); clr_up()
    check(v2(0, 4) == 64, f"Clear + K2 on page B: MIX back to the centre ({v2(0, 4)})")
    # ---------------------------------------------------------------- the paraphonic notes
    NON, NOFF = e.r32(V.NOTE_VT[0]) & ~1, e.r32(V.NOTE_VT[1]) & ~1
    note_on = lambda n, vel=90: e.call(NON, 0x20011334, 2, n, vel)
    note_off = lambda n: e.call(NOFF, 0x20011334, 2, n, 0)
    # MIDI 1 is the track with the mode on; the dual flag is on
    e.btn(2); e.btn(8)
    if not e.rt(0, V.RT_VEL) & 0x80: pad(V.PAD_PAGE)
    for _ in range(40): e.vtick()
    check(cnt(0) == 0, "no notes held")
    note_on(60)
    check(cnt(0) == 1 and n1(0) == 60 and n2(0) == 60, f"one note: both oscillators {n1(0)} / {n2(0)}, count {cnt(0)}")
    check(e.rt(0, V.RT_VEL) & 0x80, "the two-oscillator flag (bit 7 of RT_VEL) survives a note")
    note_on(64)
    check(cnt(0) == 2 and n1(0) == 60 and n2(0) == 64, f"two notes: OSC1 {n1(0)}, OSC2 {n2(0)}")
    note_on(67)
    check(cnt(0) == 3 and n1(0) == 67 and n2(0) == 64 and e.rt(0, V.RT_CNT) & 0x80, f"a third note replaces the older oscillator: {n1(0)} / {n2(0)}")
    note_on(72)
    check(n1(0) == 67 and n2(0) == 72, f"a fourth note replaces the other one: {n1(0)} / {n2(0)}")
    note_off(60)
    check(cnt(0) == 3 and n1(0) == 67 and n2(0) == 72, f"a note that sounds nowhere is released: nothing changes ({n1(0)} / {n2(0)})")
    note_off(72)
    check(cnt(0) == 2 and n1(0) == 67 and n2(0) == 67, f"the note of OSC2 is released: unison on the other one ({n1(0)} / {n2(0)})")
    note_off(67)
    check(cnt(0) == 1 and n1(0) == 67 and n2(0) == 67, "the note that sounds on both is released while another one is held (forgotten): it stays")
    note_off(64)
    check(cnt(0) == 0, f"all released: count {cnt(0)}")
    ms = ticks(30)
    check([v for c, v in ms if c == 17][-1:] == [0], f"the gate closes {[v for c, v in ms if c == 17][-2:]}")
    note_on(50, 100); note_on(55, 80)
    ms = ticks(30)
    codes = [(c, v) for c, v in ms if c in (14, 17, 18, 20, 21)]
    d = {}
    for c, v in codes: d[c] = v
    check(d.get(18) == 50 and d.get(14) == 55 and d.get(20) == 80 and d.get(17) == 1 and 21 in d, f"the DSP gets NOTE {d.get(18)}, NOTE2 (code 14) {d.get(14)}, VEL (the last note) {d.get(20)}, GATE {d.get(17)}, TRIG {21 in d}")
    note_off(50); note_off(55)
    # ---------------------------------------------------------------- the transport: one message per voice every 2 ms at most, the switch-on delivers everything, the heartbeat repeats ACT
    gc.collect(); e = E20(img, man)
    for _ in range(30): e.vtick()
    e.btn(2); e.btn(8)
    pad(V.PAD_OSC); pad(V.PAD_OSC); pad(V.PAD_PAGE)
    e.rl = 0
    times = []; seen = []
    for i in range(400):
        e.w32(HAL, 9000 + i)                                                       # 1 ms per service tick
        for w, ad in e.vtick():
            if ad == VD.VB0: times.append(9000 + i); seen.append(((w >> 16) & 0x7F, sgn(w & 0xFFFF)))
    gaps = [b_ - a_ for a_, b_ in zip(times, times[1:])]
    check(gaps and min(gaps) >= 2, f"{len(times)} messages in 400 ms, never closer than 2 ms (smallest gap {min(gaps)} ms)")
    check(set(range(1, 17)) | {17, 18, 19, 20} | set(range(22, 32)) | set(range(32, 40)) <= {c for c, v in seen} - {0}, f"the switch-on delivers every code ({sorted({c for c, v in seen})})")
    acts = [v for c, v in seen if c == 19]
    check(len(acts) >= 4 and set(acts) == {2 | (1 << 9)}, f"the heartbeat repeats ACT with the flags ({acts[:4]}, {len(acts)} times)")
    sweeps = [t for t, (c, v) in zip(times, seen) if 32 <= c <= 39]
    check(len(sweeps) >= 16, f"the eight volatile values are swept again and again ({len(sweeps)} messages)")
    # ---------------------------------------------------------------- the whole way: the messages of the ARM replayed into the DSP program
    from dspemu import run
    from dsp_session import dsp_program
    gc.collect(); e = E20(img, man)
    for _ in range(30): e.vtick()
    e.sent = []                                                                   # (every message from here on goes to the DSP, in order)
    e.btn(2); e.btn(8)
    pad(V.PAD_OSC); pad(V.PAD_OSC); pad(V.PAD_PAGE); pad(V.PAD_VCF)               # oscillator, two oscillators, chain order 2
    pad(1)
    e.btn(2); e.track(2)
    e.knob_raw(1, 10, True); e.knob_raw(2, 60, True)                              # page B: MIX 74, BITSYNC 60
    e.knob_raw(4, 9, True); e.knob_raw(7, 21, True); e.knob_raw(3, 12)             # (Shift + K5 = filter type, Shift + K8 = FX type on page A are not on this page: no function)
    e.btn(2); e.btn(8); pad(2); e.btn(2); e.track(2)
    e.knob_raw(0, 12); e.knob_raw(0, -7, True); e.knob_raw(1, 33); e.knob_raw(6, 70); e.knob_raw(1, 40, True); e.knob_raw(2, 50, True)
    e.btn(2); e.btn(8); pad(0); e.btn(2); e.track(2)
    e.knob_raw(4, 5, True); e.knob_raw(7, 30, True); e.knob_raw(0, 6)             # page A: filter type, FX type, ATK
    NON, NOFF = e.r32(V.NOTE_VT[0]) & ~1, e.r32(V.NOTE_VT[1]) & ~1
    e.call(NON, 0x20011334, 2, 55, 90); e.call(NON, 0x20011334, 2, 62, 100)
    e.rl = 0                                                                      # a clock that passes the heartbeat windows: the very first message after boot (tag 0) is ignored by the DSP, the heartbeat repeats ACT
    for i in range(240): e.w32(HAL, 4097 + 3 * i); e.vtick()
    msgs = e.sent
    sp = dsp_program(img); P0 = [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]
    dl = {k: int(v, 16) for k, v in man["report"]["sc16"]["dsp_labels"].items()}
    blk = [0] * (2 * VD.VBS); osb = [0] * 96; os2 = [0] * 96
    for w, ad in msgs:
        blk[ad - VD.VB0 + VD.MB] = w & 0xFFFFFF
        res, ran = run(P0, dl["vpre"], mem=[('x', 0x3A, [32]), ('x', VD.VB0, blk), ('x', VD.FLAGS, [0]), ('y', VD.RING_PTR, [0x1000]), ('y', 0x1000, [0] * 64), ('x', VD.OSB0, osb), ('x', VD.OS2B0, os2)],
                       dumps=[('x', VD.VB0, 2 * VD.VBS), ('x', VD.OSB0, 96), ('x', VD.OS2B0, 96)], regs_code=[])
        blk, osb, os2 = res[('x', VD.VB0)], res[('x', VD.OSB0)], res[('x', VD.OS2B0)]
    sx = lambda v: v - (1 << 24) if v & 0x800000 else v
    check(len(msgs) > 100, f"{len(msgs)} messages replayed")
    check(blk[VD.ACT] == 2 and osb[VD.DFLAGS_OFF] == 3, f"the DSP: ACT {blk[VD.ACT]}, DFLAGS {osb[VD.DFLAGS_OFF]} (oscillator, route 1, two oscillators)")
    check(blk[VD.NOTE] == n1(0) == 55 and osb[VD.NOTE2_OFF] == n2(0) == 62, f"the DSP notes {blk[VD.NOTE]} / {osb[VD.NOTE2_OFF]} (the two held notes)")
    raw = [sx(os2[k]) for k in range(8)]
    want = [v2(0, 0), v2(0, 1), v2(0, 2), v2(0, 3), v2(0, 4), (7 * v2(0, 5)) >> 7, v2(0, 6), v2(0, 7)]
    check(raw == want and os2[8] == (7 * v2(0, 5)) & 127, f"the OSC2 block of the DSP {raw} = the values of the ARM {want} (BITSYNC split in zone and position {os2[8]})")
    tail_ok = all(sx(blk[1 + c]) == e.val(0, c) for c in range(1, 13)) and sx(blk[1 + 15]) == e.val(0, 15)
    check(tail_ok and blk[1 + 13] == (7 * e.val(0, 13)) >> 7 and blk[1 + 16] == (7 * e.val(0, 16)) >> 7, f"the old codes of voice 1 arrived; the FX / filter types as zones ({blk[1 + 13]}, {blk[1 + 16]})")
    check(blk[VD.VBS + VD.ACT] == 0, f"voice 2 stays off (ACT {blk[VD.VBS + VD.ACT]})")
    print("SC24 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
