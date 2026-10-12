"""SC26 ARM tests (the step-drummer of the MIDI tracks) through the real routes (pads 0x08033282 / release 0x0803381A, knobs 0x08033848, buttons 0x08033320, the LED frame, the note vtable, the DSP service tick):

    python tools/emu_sc26.py SC26.bin SC26_manifest.json
  * boot: the state of SC24 / SC25 (signature 0xAF) is kept, the two step-drummer bytes start at 0, the signature becomes 0xB0;
  * pad 30: nothing with the mode off; with it on: enabled + view open (the notes of the pattern become the tonic, one per step), closed (still enabled), open again; Shift + pad 30 disables;
  * the view: pads 1-16 = the steps (pair colours, bright with a note), pads 17-24 = the destinations, pad 30; the 8 knobs = the pairs: the pitch page writes lane 0 of both steps (12 bytes), the velocity
    page sets / creates / deletes the notes of the pair; Octave v / ^ and 1-16 / 17-32; Shift + a step pad adds / removes its note (velocity of the pair / of the nearest earlier note / 64);
  * the offset: the value of the destination that goes to the DSP = the stored value + the pitch value of the step that plays (pitch: 128 TUNE + FINE + 24 offset, split again; the others value + offset,
    clamped); a note start sends it; an auditioned step counts instead of the playing one while its pad is held; disabled = the plain values;
  * SC25: with the step-drummer enabled lane 0 is neither played back as TUNE nor recorded.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_SP
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc25 as T25  # noqa: E402,F401  (applies the SC25 options)
import emu_sc22_4 as T4  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
V = T4.V
V.use_sdrum()
E20, MGR, TMPL = T4.E20, T4.MGR, T4.TMPL
EMPTY = bytes([0, 0, 0, 0x60])


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
    gfst = int(man["report"]["sc17"]["labels"]["c_gfst"], 16)

    # ---------------------------------------------------------------- boot: the state of SC25 is kept
    gc.collect(); e = E20(img, man)
    t = bytearray(75); t[V.O_FLAGS] = 0x81 | 0x70; t[V.O_SIG] = 0xAF; t[V.O_SD] = 0x55; t[V.O_SD + 1] = 0x2A
    for i in range(52): t[V.O_PAR + i] = (i * 3) % 60
    e.uc.mem_write(V.TAIL, bytes(t))
    for _ in range(20): e.vtick()
    check(e.tailb(V.O_SIG) == 0xB0 and e.tailb(V.O_SD) == 0 and e.tailb(V.O_SD + 1) == 0, f"a tail of SC25: signature {e.tailb(V.O_SIG):#x}, the step-drummer bytes {e.tailb(V.O_SD):#x} {e.tailb(V.O_SD + 1):#x}")
    bad = [i for i in range(52) if e.tailb(V.O_PAR + i) != (i * 3) % 60 and i not in (13, 39)]             # (code 14 = the note of the second oscillator: set at every power-up)
    check(e.tailb(V.O_FLAGS) == 0x81 and not bad, f"flags {e.tailb(V.O_FLAGS):#x} (the three view bits cleared), the 52 values kept (changed: {bad})")
    del e; gc.collect(); e = E20(img, man)
    sends, gates, stock = [], [], []
    def hk(uc, a, s, d):
        r = lambda x: uc.reg_read(x)
        if a == T25.SEND:
            sends.append(bytes(uc.mem_read(r(UC_ARM_REG_R1), 3))); uc.reg_write(UC_ARM_REG_PC, r(UC_ARM_REG_LR) | 1)
        elif a == T25.GATE:
            gates.append((r(UC_ARM_REG_R1), r(UC_ARM_REG_R2))); uc.reg_write(UC_ARM_REG_PC, r(UC_ARM_REG_LR) | 1)
        elif a == T25.STK_RET:
            stock.append(r(UC_ARM_REG_R1)); uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_SP, r(UC_ARM_REG_SP) + 24); uc.reg_write(UC_ARM_REG_PC, r(UC_ARM_REG_LR) | 1)
    for fa in (T25.SEND, T25.GATE, T25.STK_RET): e.uc.hook_add(UC_HOOK_CODE, hk, begin=fa, end=fa)
    for _ in range(30): e.vtick()
    check(e.tailb(V.O_SIG) == 0xB0 and e.tailb(V.O_SD) == 0, f"first use: signature {e.tailb(V.O_SIG):#x}, state 0")

    def block():
        e.call(gfst); return e.uc.reg_read(UC_ARM_REG_R0)
    def val(tr, code):
        if code <= 26: return e.val(tr, code)
        return struct.unpack("b", bytes([e.r8(block() + V.V2_OFF + 8 * tr + code - 27)]))[0]
    def setval(tr, code, v):
        e.call(L["c_vvaddr"], tr, code); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes([v & 0xFF]))
    nib = lambda tr: (e.tailb(V.O_SD) >> (4 * tr)) & 15
    flag = lambda m: e.tailb(V.O_FLAGS) & m
    rec = e.r32(V.REC_GATE_OBJ + 0x14); base = e.r32(rec + 0x48)
    def eng(tr, idx):
        e.call(0x0803542C, e.r32(V.ENGINE + 0x38 + 4 * tr), idx); return e.uc.reg_read(UC_ARM_REG_R0)
    pat = lambda: base + 0xCA8 * (e.r8(eng(0, 0)) & 7)
    step = lambda s: bytes(e.uc.mem_read(pat() + 28 * s, 28))
    lane = lambda s: bytes(e.uc.mem_read(pat() + 0x3A8 + 6 * s, 6))
    def setstep(s, mask, *units):
        b = bytearray([mask, 7, 0, 0]) + b"".join(bytes(u) for u in units) + EMPTY * (6 - len(units))
        e.uc.mem_write(pat() + 28 * s, bytes(b))
    e.call(L["c_sdtonic"]); tonic = e.uc.reg_read(UC_ARM_REG_R0)
    check(48 <= tonic <= 59, f"the tonic: {tonic} (48 + the root of the scale)")
    note1 = lambda ln, mic, vel: bytes([1, 7, 0, 0, tonic, ln, mic, vel]) + EMPTY * 5
    none = bytes([0, 7, 0, 0]) + EMPTY * 6
    # the pattern of the test: step 0 one note, step 3 a chord, step 5 a note in the second unit only
    for s in range(32): setstep(s, 0)
    for s in range(32): e.uc.mem_write(pat() + 0x3A8 + 6 * s, bytes([0xFF] * 6))
    setstep(0, 1, (60, 6, 0, 100)); setstep(3, 3, (64, 12, 0, 90), (67, 12, 0, 80)); setstep(5, 2, (0, 0, 0, 0x60), (72, 3, 2, 70))

    e.btn(2); e.track(2); e.btn(8)
    pad = lambda p: (e.padr(p), e.rel(p))
    def spad(p):
        e.set_p0(e.r32(MGR + 0xC), 1); e.padr(p); e.rel(p); e.set_p0(e.r32(MGR + 0xC), 0)
    led = lambda: e.tleds(TMPL[0])
    kled = lambda: e.frame()[60:68]
    # ---------------------------------------------------------------- pad 30
    pad(V.PAD_SD)
    check(nib(0) == 0 and led()[V.PAD_SD] == 0, "pad 30 with the mode off: nothing, dark")
    pad(V.PAD_OSC); pad(V.PAD_OSC)                                                # oscillator
    for _ in range(40): e.vtick()
    pad(V.PAD_SD)
    check(nib(0) == 1 and flag(V.F_SDOPEN) and led()[V.PAD_SD] == V.COL_SD[0], f"pad 30: enabled, the view open (nibble {nib(0)}, flags {e.tailb(V.O_FLAGS):#x}), bright")
    check(step(0) == note1(6, 0, 100) and step(3) == note1(12, 0, 90) and step(5) == note1(3, 2, 70) and step(1) == none,
          f"the notes became the tonic, one per step, with their length / micro step / velocity: {step(0)[:8].hex()} {step(3)[:12].hex()} {step(5)[:12].hex()}")
    Ls = led()
    exp = []
    for i in range(16):
        dim = V.SD_STEPCOL[(i >> 1) & 1][1]
        exp.append(dim - 1 if i in (0, 3, 5) else dim)
    check(Ls[:16] == exp, f"the steps: {[hex(x) for x in Ls[:16]]}")
    dexp = [V.SD_DCOL[0]] + [(0x37 if c == 0x32 else c + 1) for c in V.SD_DCOL[1:]]
    check(Ls[16:24] == dexp, f"the destinations (the first one selected): {[hex(x) for x in Ls[16:24]]}")
    e.set_p0(V.PLAY_STORE, 1); e.uc.mem_write(eng(0, 1), bytes([3]))
    check(led()[3] == V.SD_HEAD and led()[:3] == exp[:3], f"the transport runs at step 4: its pad is white ({led()[3]:#x})")
    e.uc.mem_write(eng(0, 1), bytes([19]))
    check(led()[:16] == exp, "a step of the other half: no pad")
    e.set_p0(V.PLAY_STORE, 0); e.uc.mem_write(eng(0, 1), bytes([3]))
    check(led()[3] == exp[3], "stopped: no white pad")
    e.uc.mem_write(eng(0, 1), bytes([0]))
    # ---------------------------------------------------------------- the knobs: the pitch page
    e.knob_raw(0, 10)
    check(lane(0) == bytes([74] * 6) and lane(1) == bytes([74] * 6) and lane(2) == bytes([0xFF] * 6), f"K1 +10: lane 0 of the steps 1-2 = 74 ({lane(0).hex()} {lane(1).hex()}), the next pair untouched")
    e.knob_raw(1, -20)
    check(lane(2) == bytes([44] * 6) and lane(3) == bytes([44] * 6), f"K2 -20: 44 ({lane(2).hex()})")
    e.knob_raw(7, 100); e.knob_raw(7, 100)
    check(lane(14) == bytes([127] * 6) and lane(15) == bytes([127] * 6), "K8: clamped at 127")
    e.knob_raw(7, -127); e.knob_raw(7, -127)
    check(lane(14) == bytes([0] * 6), "and at 0")
    k = kled()
    check(k[0] == (V.SD_DCOL[0] | (74 + 2) << 8) and k[1] == (V.SD_DCOL[0] | (44 + 2) << 8) and k[2] == (V.SD_DCOL[0] | (64 + 2) << 8),
          f"the knob LEDs: the colour of the destination with the value ({[hex(x) for x in k[:3]]}; a pair with no value = the centre)")
    check(val(0, 5) == V.DEFAULTS[4], "the values of the mode are not touched by the knobs of the view")
    # ---------------------------------------------------------------- the velocity page
    btn = lambda b: e.call(0x08033320, MGR, b, maxins=900000)
    btn(19)
    check(flag(V.F_SDPAGE), "Octave v: the velocity page")
    e.knob_raw(0, 5)
    check(step(0)[7] == 105, f"K1 +5: the velocity of the note of the pair {step(0)[7]}")
    e.knob_raw(1, -127)
    check(step(2) == none and step(3) == none, "K2 to 0: the notes of the pair are removed")
    e.knob_raw(1, 30)
    check(step(2) == note1(V.SD_LEN, 0, 30) and step(3) == none, f"K2 +30: a note on the first step of the pair, velocity 30 ({step(2)[:8].hex()})")
    e.knob_raw(3, 50)
    check(step(6) == note1(V.SD_LEN, 0, 50), "K4 +50 on an empty pair: a new note")
    k = kled()
    check(k[0] == (V.COL_TRACK[0] | (105 + 2) << 8) and k[1] == (V.COL_TRACK[0] | (30 + 2) << 8) and k[4] == (V.COL_TRACK[0] | 2 << 8), f"the knob LEDs: the track colour with the velocity ({[hex(x) for x in k[:5]]})")
    btn(20)
    check(not flag(V.F_SDPAGE), "Octave ^: the pitch page")
    # ---------------------------------------------------------------- Shift + a step pad
    spad(7)
    check(step(7) == note1(V.SD_LEN, 0, 50), f"Shift + pad 8: a note with the velocity of its pair ({step(7)[:8].hex()})")
    spad(7)
    check(step(7) == none, "again: removed")
    spad(9)
    check(step(9) == note1(V.SD_LEN, 0, 50), f"Shift + pad 10 (an empty pair): the velocity of the nearest earlier note ({step(9)[7]})")
    spad(9)
    for s in (0, 2, 5, 6): setstep(s, 0)
    spad(12)
    check(step(12) == note1(V.SD_LEN, 0, 64), f"no note anywhere: velocity 64 ({step(12)[7]})")
    setstep(0, 1, (tonic, 6, 0, 100))
    # ---------------------------------------------------------------- the half
    btn(21)
    check(flag(V.F_SDHALF), "1-16 / 17-32: the second half")
    e.knob_raw(0, 6)
    check(lane(16) == bytes([70] * 6) and lane(17) == bytes([70] * 6) and lane(0) == bytes([74] * 6), "K1 now moves the steps 17-18")
    spad(3)
    check(step(19) == note1(V.SD_LEN, 0, 64) or step(19)[0] == 1, f"Shift + pad 4 = step 20 ({step(19)[:8].hex()})")
    check(led()[3] == V.SD_STEPCOL[1][0], "and its LED")
    btn(21)
    check(not flag(V.F_SDHALF), "back to the first half")
    # ---------------------------------------------------------------- the offset on the way to the DSP
    def stepnow(s): e.uc.mem_write(eng(0, 1), bytes([s]))
    def mbox(n=80):
        got = {}
        for _ in range(n):
            for w, ad in e.vtick():
                if ad == VD.VB0: got[(w >> 16) & 0x7F] = struct.unpack("<h", struct.pack("<H", w & 0xFFFF))[0]
        return got
    def noteon(vel=100): e.call(L["c_vnon"], V.TXOBJ, 2, tonic, vel, maxins=2_000_000)
    def noteoff(): e.call(L["c_vnoff"], V.TXOBJ, 2, tonic, 0, maxins=2_000_000)
    setval(0, 17, 0); setval(0, 18, 0); setval(0, 27, 0); setval(0, 28, 0)
    stepnow(0); mbox(60); noteon(); g = mbox()
    check(g.get(22) == 2 and g.get(23) == -16, f"step 1 (pitch value 74 = +10): TUNE 2, FINE -16 reach the DSP (128 x 2 - 16 = 240 = 24 x 10): {g.get(22)}, {g.get(23)}")
    check(g.get(32) == 2 and g.get(33) == -16, f"and the second oscillator: TUNE2 {g.get(32)}, FINE2 {g.get(33)}")
    check(val(0, 17) == 0 and val(0, 18) == 0, "the stored values stay (the knob is the base)")
    noteoff(); stepnow(2); noteon(); g = mbox()
    check(g.get(22) == -4 and g.get(23) == 32, f"step 3 (44 = -20): TUNE -4, FINE 32 (-480 = -512 + 32): {g.get(22)}, {g.get(23)}")
    noteoff(); setval(0, 17, 5); setval(0, 18, -10); stepnow(0); noteon(); g = mbox()
    check(g.get(22) == 7 and g.get(23) == -26, f"with the base TUNE 5, FINE -10: 640 - 10 + 240 = 870 = 7 x 128 - 26: {g.get(22)}, {g.get(23)}")
    noteoff(); stepnow(8); noteon(); g = mbox()
    check(g.get(22) == 5 and g.get(23) == -10, f"a step with no pitch value: the plain values {g.get(22)}, {g.get(23)}")
    noteoff(); setval(0, 17, 0); setval(0, 18, 0)
    # the order: the pitch goes before the gate
    stepnow(0); mbox(40); e.sent = []
    noteon()
    seq = []
    for _ in range(40):
        for w, ad in e.vtick():
            if ad == VD.VB0: seq.append((w >> 16) & 0x7F)
    check(22 in seq and 17 in seq and seq.index(22) < seq.index(17) and seq.index(23) < seq.index(17), f"TUNE / FINE are sent before the gate: {seq[:8]}")
    noteoff()
    # another destination: env -> filter (code 3)
    pad(16 + 5)
    check(nib(0) == (1 | 5 << 1) and led()[16 + 5] == V.SD_DCOL[5] and led()[16] == V.SD_DCOL[0] + 1, f"pad 22: the destination env -> filter (nibble {nib(0):#x})")
    check(kled()[0] == (V.SD_DCOL[5] | (74 + 2) << 8), "the knob LEDs take its colour")
    setval(0, 3, 10); stepnow(0); g0 = mbox(40); noteon(); g = mbox()
    check(g0.get(22) == 0 and g0.get(23) == 0, f"the old destination went to the DSP as its plain values: TUNE {g0.get(22)}, FINE {g0.get(23)}")
    check(g.get(3) == 20 and 22 not in g, f"ENVF 10 + 10 = 20 reaches the DSP at the note start (and TUNE is left alone): {g.get(3)}")
    noteoff(); setval(0, 3, 60); stepnow(0); noteon(); g = mbox()
    check(g.get(3) == 63, f"clamped at the top of the range: {g.get(3)}")
    noteoff(); setval(0, 3, 0)
    pad(16 + 6)                                                                   # SHAPE (code 20, 0..100)
    setval(0, 20, 95); stepnow(0); mbox(40); noteon(); g = mbox()
    check(g.get(25) == 100, f"SHAPE 95 + 10 clamped at 100: {g.get(25)}")
    noteoff(); setval(0, 20, 50)
    pad(16 + 3)                                                                   # FM (code 33, volatile: the sweep)
    setval(0, 33, 20); stepnow(2); mbox(40); noteon(); g = mbox()
    check(g.get(38) == 0, f"FM 20 - 20 = 0 (a volatile value, through the sweep): {g.get(38)}")
    noteoff(); stepnow(0); noteon(); g = mbox()
    check(g.get(38) == 30, f"FM 20 + 10 = 30: {g.get(38)}")
    noteoff(); setval(0, 33, 0)
    pad(16)                                                                       # back to the pitch of both oscillators
    # ---------------------------------------------------------------- audition
    stepnow(8); mbox(40); e.notes.clear()
    e.padr(2)                                                                     # step 3 (pitch value 44)
    blk = block()
    check(e.r8(blk + V.SD_AUD) == 3, f"a tap on pad 3: the step is auditioned (byte {e.r8(blk + V.SD_AUD)})")
    check(any(n[1:] == (V.TXOBJ, 2, tonic, 100) or (n[2], n[3]) == (2, tonic) for n in e.notes), f"a note-on of the tonic goes out: {[(hex(n[0]), n[2], n[3], n[4]) for n in e.notes]}")
    g = mbox()
    check(g.get(22) == -4 and g.get(23) == 32, f"with the pitch of the auditioned step (not of the playing one): {g.get(22)}, {g.get(23)}")
    e.notes.clear(); e.rel(2)
    check(e.r8(blk + V.SD_AUD) == 0 and len(e.notes) == 1, f"the release ends it (byte {e.r8(blk + V.SD_AUD)}, {len(e.notes)} note-off)")
    # ---------------------------------------------------------------- SC25: lane 0 is the pitch row
    e.set_p0(V.PLAY_STORE, 1)
    G = e.r32(V.SETOBJ - 8); stock.clear(); sends.clear()
    e.call(0x080313C4, G + 0x110, 0, 100)
    check(val(0, 17) == 0 and stock == [] and sends == [], "the playback of lane 0 does not move TUNE while the step-drummer is enabled (and no stock CC)")
    e.call(0x080313C4, G + 0x110, 4, 100)
    check(val(0, 1) == 36, "the other lanes still play (lane 4 = FILT)")
    e.set_p0(V.PLAY_STORE, 0)
    # ---------------------------------------------------------------- view closed / disabled
    pad(V.PAD_SD)
    check(nib(0) & 1 and not flag(V.F_SDOPEN) and led()[V.PAD_SD] == V.COL_SD[1], "pad 30 again: the view closed, still enabled (dim)")
    check(led()[:3] == [V.COL_PAGE[0][0], V.COL_PAGE[1][1], 0], f"the page row is back: {[hex(x) for x in led()[:3]]}")
    before = val(0, 5); e.knob_raw(0, 3)
    check(val(0, 5) == before + 3, "the knobs are the values of the mode again")
    gates.clear(); pad(1); e.knob_raw(0, 2)
    check(val(0, 17) == 2 and gates == [], f"TUNE is not recorded in lane 0 while the step-drummer is enabled ({gates})")
    setval(0, 17, 0); pad(0)
    stepnow(0); mbox(40); noteon(); g = mbox()
    check(g.get(22) == 2 and g.get(23) == -16, f"the pitch row keeps working with the view closed: {g.get(22)}, {g.get(23)}")
    noteoff()
    f0 = e.tailb(V.O_FLAGS); btn(19); btn(21)
    check(e.tailb(V.O_FLAGS) == f0, "with the view closed Octave v and 1-16 / 17-32 are the stock buttons")
    pad(V.PAD_SD)
    check(flag(V.F_SDOPEN), "pad 30: open again")
    spad(V.PAD_SD)
    check(nib(0) & 1 == 0 and led()[V.PAD_SD] == 0, f"Shift + pad 30: disabled (nibble {nib(0):#x})")
    g = mbox()
    check(g.get(22) == 0 and g.get(23) == 0, f"TUNE / FINE go to the DSP as the plain values again: {g.get(22)}, {g.get(23)}")
    stock.clear(); e.set_p0(V.PLAY_STORE, 1)
    e.call(0x080313C4, G + 0x110, 0, 70)
    check(val(0, 17) == 6, "lane 0 is TUNE again (SC25)")
    e.set_p0(V.PLAY_STORE, 0)
    # the second track has its own nibble
    e.btn(3); e.track(3); e.btn(8)
    e.call(L["c_vset"], 1, 1); e.vtick()
    e.padr(V.PAD_SD); e.rel(V.PAD_SD)
    check(nib(1) == 1 and nib(0) & 1 == 0, f"MIDI 2: its own state ({e.tailb(V.O_SD):#x})")
    print("SC26 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
