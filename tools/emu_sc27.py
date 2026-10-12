"""SC27 ARM tests (the rest of the step-drummer) through the real routes (pads 0x08033282 / release 0x0803381A, knobs 0x08033848, buttons 0x08033320, the LED frame):

    python tools/emu_sc27.py SC27.bin SC27_manifest.json
  * MIDI tracks: with the view open Octave v / ^ (panel LEDs 51 / 52) and 1-16 / 17-32 (LED 53) are lit and follow the page / the half; the knob of the pair that plays is white; with the view closed
    the pads 9-24 are dark and the panel LEDs are the stock ones;
  * the knob pages: pads 4 / 5 of the page row = the lanes page (TUNE, REL, ENVA, ENVF, FILT, RES, LRATE, FXAMT) and the modulation page (ADSR / LFO; Shift = the amounts); the third page bit lives
    in bit 0 of the nibble of the synth with the same index and does not disturb its macro;
  * Synth 1 / 2: pad 30 of the source view opens / closes the view (the notes become the tonic); pads 17-24 = the macro; the pitch page writes the lane of that macro (a pair with no value starts
    from the position of the macro), the velocity page the notes; the audition is an internal note (c_inject) with its note-off at the release; the five source pads keep working; a Synth button
    closes the view; nothing of this reaches the DSP mailbox of the MIDI tracks.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc26 as T26  # noqa: E402,F401  (applies the SC25 / SC26 options)
import emu_sc22_4 as T4  # noqa: E402
import emu_sc19_1 as T191  # noqa: E402
import build_sc15 as B15  # noqa: E402
V = T4.V
V.use_sdrum2(); V.use_pages5()
E20, MGR, TMPL = T4.E20, T4.MGR, T4.TMPL
SYN = T191.VIEWS
EMPTY = bytes([0, 0, 0, 0x60])


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
    s6 = {k: int(v, 16) for k, v in man["report"]["sc06"]["labels"].items()}
    gfst = int(man["report"]["sc17"]["labels"]["c_gfst"], 16)
    w = lambda a: struct.unpack_from("<I", img, a - 0x08010000)[0]
    check(w(V.SP_VT) == L["c_sxpad"] | 1 and w(V.SP_VT + 4) == L["c_sxrel"] | 1 and w(V.SP_VT + 28) == L["c_sxleds"] | 1, "the synth Preset view: slots 0 / 1 / 7 -> c_sxpad / c_sxrel / c_sxleds")
    check(0x20044E58 - int(man["report"]["sc17"]["sc14_state"], 16) == 236, "RAM reservation unchanged (236)")

    gc.collect(); e = E20(img, man)
    inj = []
    def hk(uc, a, s, d):
        inj.append(bytes(uc.mem_read(uc.reg_read(UC_ARM_REG_R0), 3))); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, hk, begin=s6["c_inject"], end=s6["c_inject"])
    for _ in range(30): e.vtick()
    flag = lambda m: e.tailb(V.O_FLAGS) & m
    def eng(tr, idx):                                                             # tr: 0 / 1 MIDI, 2 / 3 synth
        e.call(0x0803542C, e.r32(V.ENGINE + 0x30 + 4 * ((tr + 2) & 3)), idx); return e.uc.reg_read(UC_ARM_REG_R0)
    def base(tr): return e.r32(e.r32(V.REC_GATE_OBJ + 0xC + 4 * ((tr + 2) & 3)) + 0x48)
    pat = lambda tr: base(tr) + 0xCA8 * (e.r8(eng(tr, 0)) & 7)
    step = lambda tr, s: bytes(e.uc.mem_read(pat(tr) + 28 * s, 28))
    lane = lambda tr, ln, s: bytes(e.uc.mem_read(pat(tr) + 0x3A8 + 192 * ln + 6 * s, 6))
    def setstep(tr, s, mask, *units):
        e.uc.mem_write(pat(tr) + 28 * s, bytes(bytearray([mask, 7, 0, 0]) + b"".join(bytes(u) for u in units) + EMPTY * (6 - len(units))))
    def clearpat(tr):
        for s in range(32): setstep(tr, s, 0)
        e.uc.mem_write(pat(tr) + 0x3A8, bytes([0xFF] * (192 * 8)))
    e.call(L["c_sdtonic"]); tonic = e.uc.reg_read(UC_ARM_REG_R0)
    note1 = lambda ln, mic, vel: bytes([1, 7, 0, 0, tonic, ln, mic, vel]) + EMPTY * 5
    none = bytes([0, 7, 0, 0]) + EMPTY * 6
    pad = lambda p: (e.padr(p), e.rel(p))
    def spad(p):
        e.set_p0(e.r32(MGR + 0xC), 1); e.padr(p); e.rel(p); e.set_p0(e.r32(MGR + 0xC), 0)
    btn = lambda b: e.call(0x08033320, MGR, b, maxins=900000)
    kled = lambda: e.frame()[60:68]
    def val(tr, code):
        if code <= 26: return e.val(tr, code)
        e.call(gfst); return struct.unpack("b", bytes([e.r8(e.uc.reg_read(UC_ARM_REG_R0) + V.V2_OFF + 8 * tr + code - 27)]))[0]

    # ================================================================ MIDI 1
    clearpat(0); setstep(0, 0, 1, (60, 6, 0, 100)); setstep(0, 9, 1, (62, 6, 0, 90))
    e.btn(2); e.track(2); e.btn(8)
    led = lambda: e.tleds(TMPL[0])
    pad(V.PAD_OSC); pad(V.PAD_OSC)
    for _ in range(40): e.vtick()
    f0 = e.frame()
    check(led()[8:24] == [0] * 16, "the mode on, the view closed: the pads 9-24 are dark")
    pad(V.PAD_SD)
    Ls = led()
    check(flag(V.F_SDOPEN) and all(Ls[8:24]) and Ls[V.PAD_SD] == V.COL_SD[0], f"pad 30: the view open, the pads 9-24 lit ({[hex(x) for x in Ls[8:24]]})")
    f = e.frame()
    check(f[52] == V.COL_SD[0] and f[51] == V.COL_SD[1] and f[53] == V.COL_SD[1], f"the panel: Octave ^ bright (the pitch page), Octave v dim, 1-16 / 17-32 dim ({f[51]:#x} {f[52]:#x} {f[53]:#x})")
    btn(19); f = e.frame()
    check(f[51] == V.COL_SD[0] and f[52] == V.COL_SD[1], "Octave v: the velocity page, the two LEDs swap")
    btn(20); btn(21); f = e.frame()
    check(f[53] == V.COL_SD[0], f"1-16 / 17-32: bright with the second half ({f[53]:#x})")
    btn(21)
    # the knob of the pair that plays
    e.knob_raw(1, 6)
    k0 = kled()
    e.set_p0(V.PLAY_STORE, 1); e.uc.mem_write(eng(0, 1), bytes([3]))
    k = kled()
    check(k[1] == (V.SD_HEAD | 129 << 8) and k[0] == k0[0] and k[2:] == k0[2:], f"the transport runs at step 4: K2 is white ({k[1]:#x}), the others as before")
    e.uc.mem_write(eng(0, 1), bytes([14])); k = kled()
    check(k[7] == (V.SD_HEAD | 129 << 8) and k[1] == k0[1], "step 15: K8")
    e.uc.mem_write(eng(0, 1), bytes([20])); k = kled()
    check(k == k0, "a step of the other half: no white knob")
    btn(21); k = kled()
    check(k[2] == (V.SD_HEAD | 129 << 8), "the second half on the screen: step 21 = K3")
    btn(21)
    e.set_p0(V.PLAY_STORE, 0); e.uc.mem_write(eng(0, 1), bytes([3]))
    check(kled() == k0, "stopped: no white knob")
    e.uc.mem_write(eng(0, 1), bytes([0]))
    # closing: the rows 2 and 3 go dark, the panel LEDs are stock again
    pad(V.PAD_SD)
    Ls = led(); f = e.frame()
    check(not flag(V.F_SDOPEN) and Ls[8:24] == [0] * 16 and Ls[V.PAD_SD] == V.COL_SD[1], f"pad 30: closed, the pads 9-24 dark ({[hex(x) for x in Ls[8:24]]}), pad 30 dim")
    check(f[51:54] == f0[51:54], f"the panel LEDs are the stock ones again ({[hex(x) for x in f[51:54]]})")
    check(Ls[:5] == [V.COL_PAGE[0][0], V.COL_PAGE[1][1], 0, V.COL_PAGE2[0][1], V.COL_PAGE2[1][1]], f"the page row: 5 pages (the third one only with two oscillators): {[hex(x) for x in Ls[:8]]}")
    spad(V.PAD_SD); Ls = led()
    check(Ls[8:24] == [0] * 16 and Ls[V.PAD_SD] == 0, "Shift + pad 30 (disabled): the pads 9-24 stay dark")

    # ---------------------------------------------------------------- the knob pages
    page = lambda tr: (e.rt(tr, V.RT_TAG) >> 1 & 3) | ((e.tailb(V.O_SD + 1) >> (4 * tr)) & 1) << 2
    pad(3)
    check(page(0) == 3 and led()[3] == V.COL_PAGE2[0][0] and led()[0] == V.COL_PAGE[0][1], f"pad 4: the lanes page (page {page(0)})")
    for kn, code in enumerate(V.KNOB_CODES_D[:8]):
        b = val(0, code); d = 3 if b < 50 else -3
        e.knob_raw(kn, d)
        check(val(0, code) == b + d, f"   K{kn + 1} = code {code}: {b} -> {val(0, code)}")
    snap = e.tail(); e.knob_raw(0, 5, shift=True)
    check(e.tail()[V.O_PAR:V.O_PAR + 52] == snap[V.O_PAR:V.O_PAR + 52], "   Shift + a knob of the lanes page: no function")
    pad(4)
    check(page(0) == 4 and e.tailb(V.O_SD + 1) & 1 and led()[4] == V.COL_PAGE2[1][0] and led()[3] == V.COL_PAGE2[0][1], f"pad 5: the modulation page (page {page(0)}, the third bit in the tail byte {e.tailb(V.O_SD + 1):#x})")
    for kn, code in enumerate(V.KNOB_CODES_E):
        if not code: continue
        b = val(0, code); d = 3 if b < 50 else -3
        e.knob_raw(kn & 7, d, shift=kn >= 8)
        check(val(0, code) == b + d, f"   {'Shift + ' if kn >= 8 else ''}K{(kn & 7) + 1} = code {code}: {b} -> {val(0, code)}")
    k = kled()
    check(all(x & 0xFF == V.COL_TRACK[0] for x in k), f"   the knob LEDs: the track colour ({[hex(x) for x in k]})")
    e.btn(3); e.track(3); e.btn(8)
    e.call(L["c_vset"], 1, 1); e.vtick()
    e.padr(3); e.rel(3)
    check(page(1) == 3 and page(0) == 4, f"MIDI 2 has its own page ({page(1)}; MIDI 1 {page(0)})")
    e.padr(4); e.rel(4)
    check(page(1) == 4 and e.tailb(V.O_SD + 1) == 0x11, f"its third bit is bit 4 of the byte ({e.tailb(V.O_SD + 1):#x})")
    e.padr(0); e.rel(0)
    check(page(1) == 0 and e.tailb(V.O_SD + 1) == 0x01, "pad 1: back to the first page, the bit cleared")
    e.btn(2); e.track(2); e.btn(8)
    pad(1)
    check(page(0) == 1 and e.tailb(V.O_SD + 1) == 0, "MIDI 1 pad 2: the OSC1 page")
    pad(4)                                                                        # leave MIDI 1 on page 4: its bit must survive the synth using the same nibble

    # ================================================================ Synth 1
    clearpat(2); setstep(2, 0, 1, (60, 6, 0, 100)); setstep(2, 3, 3, (64, 12, 0, 90), (67, 12, 0, 80))
    e.btn(0); e.track(0)                                                          # the track view of Synth 1 ...
    if not e.flag(): e.btn(0)                                                     # ... and its button again: the source view
    check(e.flag() and e.cur() == 0, f"Synth 1 twice: the source view (index {e.cur()})")
    check(not flag(V.F_SDOPEN), "a Synth button closes a step-drummer view that was open")
    sled = lambda: e.pleds(SYN[0])
    Ls = sled()
    check(Ls[V.PAD_SD] == V.COL_SD[1] and Ls[:24] == [0] * 24 and Ls[B15.PAD0] != 0, f"the source view: its five pads, pad 30 dim ({Ls[V.PAD_SD]:#x}), the rest dark")
    c = e.padr(V.PAD_SD); e.rel(V.PAD_SD)
    check(c == [] and flag(V.F_SDOPEN), "pad 30: the step-drummer view of the synth opens (no stock press)")
    check(step(2, 0) == note1(6, 0, 100) and step(2, 3) == note1(12, 0, 90) and step(2, 1) == none, f"the notes of the pattern of Synth 1 became the tonic: {step(2, 0)[:8].hex()} {step(2, 3)[:12].hex()}")
    Ls = sled()
    exp = []
    for i in range(16):
        dim = V.SD_STEPCOL[(i >> 1) & 1][1]
        exp.append(dim - 1 if i in (0, 3) else dim)
    dexp = [V.SD_DCOL[0]] + [(0x37 if c == 0x32 else c + 1) for c in V.SD_DCOL[1:]]
    check(Ls[:16] == exp and Ls[16:24] == dexp and Ls[V.PAD_SD] == V.COL_SD[0], f"the steps, the macros (macro 1 selected), pad 30 bright: {[hex(x) for x in Ls[:24]]}")
    check(Ls[B15.PAD0] != 0, "the source pads are still shown")
    f = e.frame()
    check(f[52] == V.COL_SD[0] and f[51] == V.COL_SD[1] and f[53] == V.COL_SD[1], "the panel LEDs of the view")
    # the macro and the pitch page
    e.call(V.GETTER, 0, 174); m0 = e.uc.reg_read(UC_ARM_REG_R0) & 0xFF
    e.call(V.GETTER, 0, 174 + 17 * 2); m2 = e.uc.reg_read(UC_ARM_REG_R0) & 0xFF
    k = kled()
    check(k[0] == (V.SD_DCOL[0] | (m0 + 2) << 8), f"a pair with no value shows the position of the macro ({m0}): {k[0]:#x}")
    d = 10 if m0 < 100 else -10
    e.knob_raw(0, d)
    check(lane(2, 0, 0) == bytes([m0 + d] * 6) and lane(2, 0, 1) == bytes([m0 + d] * 6) and lane(2, 0, 2) == bytes([0xFF] * 6), f"K1 {d:+d}: the lane of macro 1 at the steps 1-2 = {m0 + d} ({lane(2, 0, 0).hex()})")
    check(lane(2, 1, 0) == bytes([0xFF] * 6), "the lane of the next macro is untouched")
    c = e.padr(16 + 2); e.rel(16 + 2)
    check(c == [] and e.tailb(V.O_SD + 1) == (2 << 1 | 1), f"pad 19: macro 3 (tail byte {e.tailb(V.O_SD + 1):#x}: the page bit of MIDI 1 survives)")
    check(page(0) == 4, "MIDI 1 is still on its page")
    Ls = sled()
    check(Ls[16 + 2] == V.SD_DCOL[2] and Ls[16] == V.SD_DCOL[0] + 1, "its LED")
    d2 = 7 if m2 < 100 else -7
    e.knob_raw(3, d2)
    check(lane(2, 2, 6) == bytes([m2 + d2] * 6) and lane(2, 2, 7) == bytes([m2 + d2] * 6) and lane(2, 0, 6) == bytes([0xFF] * 6), f"K4 {d2:+d}: the lane of macro 3 at the steps 7-8 = {m2 + d2}")
    e.knob_raw(3, 127); e.knob_raw(3, 127)
    check(lane(2, 2, 6) == bytes([127] * 6), "clamped at 127")
    k = kled()
    check(k[3] == (V.SD_DCOL[2] | 129 << 8) and k[0] == (V.SD_DCOL[2] | (m2 + 2) << 8), f"the knob LEDs: the colour of the macro ({[hex(x) for x in k[:4]]})")
    e.set_p0(V.PLAY_STORE, 1); e.uc.mem_write(eng(2, 1), bytes([5])); k = kled()
    check(k[2] == (V.SD_HEAD | 129 << 8), "the pair that plays: white")
    e.set_p0(V.PLAY_STORE, 0); e.uc.mem_write(eng(2, 1), bytes([0]))
    # the velocity page
    btn(19)
    check(flag(V.F_SDPAGE) and e.flag(), "Octave v: the velocity page (the source view stays)")
    e.knob_raw(0, 5)
    check(step(2, 0)[7] == 105, f"K1 +5: the velocity of the pair {step(2, 0)[7]}")
    e.knob_raw(4, 40)
    check(step(2, 8) == note1(V.SD_LEN, 0, 40), "K5 +40 on an empty pair: a new note")
    k = kled()
    check(k[0] == (0x32 | 107 << 8), f"the knob LEDs: the colour of Synth 1 ({k[0]:#x})")
    btn(20)
    spad(6)
    check(step(2, 6) == note1(V.SD_LEN, 0, 90), f"Shift + pad 7: a note with the velocity of the nearest earlier one ({step(2, 6)[7]})")
    spad(6)
    check(step(2, 6) == none, "again: removed")
    # the audition
    inj.clear(); e.notes.clear(); sent0 = len(getattr(e, "sent", []))
    c = e.padr(3)
    chan = e.r8(e.r32(V.TXOBJ + 0xC))
    check(c == [] and inj == [bytes([0x90 | chan, tonic, 90])] and not e.notes, f"a tap on pad 4: an internal note-on of the tonic on the channel of Synth 1 with the velocity of the step ({[x.hex() for x in inj]}), nothing on the MIDI tracks")
    e.rel(3)
    check(inj[1:] == [bytes([0x80 | chan, tonic, 0])], f"the release: the note-off ({[x.hex() for x in inj[1:]]})")
    inj.clear(); e.padr(4); e.rel(4)
    check(inj and inj[0][2] == 100, f"a step of an empty pair: velocity 100 ({[x.hex() for x in inj]})")
    for _ in range(10): e.vtick()
    # the five source pads
    c = e.padr(B15.PAD0 + 1); e.rel(B15.PAD0 + 1)
    check(e.modes()[0] == 1 and flag(V.F_SDOPEN), f"pad 26: the source of Synth 1 = input 1 ({e.modes()}); the view stays open")
    e.padr(B15.PAD0); e.rel(B15.PAD0)
    c = e.padr(31)
    check(c == [] and e.modes()[0] == 0, "pad 32: swallowed as before")
    # closing
    pad(V.PAD_SD); Ls = sled()
    check(not flag(V.F_SDOPEN) and Ls[:24] == [0] * 24 and Ls[V.PAD_SD] == V.COL_SD[1], "pad 30: closed, the rows 1-3 dark")
    b = lane(2, 2, 0); e.knob_raw(0, 3)
    check(lane(2, 2, 0) == b, "the knobs are the stock macros again (the lane is not written)")
    c = e.padr(3)
    check(c == [] and step(2, 3) == note1(12, 0, 90), "a pad of the rows 1-3: swallowed by the source view")
    pad(V.PAD_SD)
    e.btn(8)
    check(not e.flag(), "Preset: the source view closes")
    Ls = sled(); Lr = sled()
    check(Lr[V.PAD_SD] != V.COL_SD[0] and Lr[V.PAD_SD] != V.COL_SD[1], f"and the Preset view of the synth is the stock one (pad 30 {Lr[V.PAD_SD]:#x})")
    c = e.padr(3)
    check(any(x[0] == "press" for x in c), "its pads are the stock patch pads")
    # Synth 2 has its own macro
    e.btn(1); e.track(1)
    if not e.flag(): e.btn(1)
    clearpat(3)
    e.padr(V.PAD_SD); e.rel(V.PAD_SD); e.padr(16 + 5); e.rel(16 + 5)
    check(flag(V.F_SDOPEN) and e.tailb(V.O_SD + 1) == (5 << 5 | 2 << 1 | 1), f"Synth 2: macro 6 in the high nibble ({e.tailb(V.O_SD + 1):#x})")
    e.call(V.GETTER, 1, 174 + 17 * 5); m5 = e.uc.reg_read(UC_ARM_REG_R0) & 0xFF
    d = 4 if m5 < 100 else -4
    e.knob_raw(7, d)
    check(lane(3, 5, 14) == bytes([m5 + d] * 6) and lane(2, 5, 14) == bytes([0xFF] * 6), f"K8: the lane of macro 6 of Synth 2 at the steps 15-16 = {m5 + d}")
    Ls = e.pleds(SYN[1])
    check(Ls[16 + 5] == V.SD_DCOL[5] and Ls[V.PAD_SD] == V.COL_SD[0], "its LEDs")
    # back on MIDI 1: the page and the state are where they were
    e.btn(2); e.track(2); e.btn(8)
    check(page(0) == 4 and led()[4] == V.COL_PAGE2[1][0], "MIDI 1: still on the modulation page")
    print("SC27 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
