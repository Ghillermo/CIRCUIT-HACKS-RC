"""SC25 ARM tests (MIDI CC / NRPN out and in, the automation lanes, the pad 27 fix) through the real routes (pads, knobs, the LED frame, the stock MIDI-in function 0x08051720, the stock macro sender):

    python tools/emu_sc25.py SC25.bin SC25_manifest.json
  * the hooks: the stock macro sender 0x080313C4 and the CC section of the MIDI-in function 0x08051834 jump into our caves; the displaced instructions are kept;
  * pad 27 fix: after the mode went on and off again the template row (pads 1-8) is the stock one again (not the page row);
  * MIDI out: a knob turn sends the CC of the code on the channel of the track (stock numbers: CC 74 filter, 73 attack, NRPN 0:76 LFO rate, NRPN 4:code for the rest), bipolar values + 64; Clear too;
  * automation: the same turn goes through the stock automation gate (id 20 + lane, 30 + lane; the lane table), only for the 8 values of the table;
  * playback: the stock macro sender, called by the sequencer with a lane value while the transport runs and the mode is on, sets the value of the lane (and sends the CC); with the transport stopped,
    the mode off, another sender or a knob above 7 the stock function runs;
  * MIDI in: CC / NRPN on the channel of a MIDI track with the mode on set the values; wrong channel, mode off, Setup CC Rx off and internal copies are ignored; nothing is sent back.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_SP
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc24 as T24  # noqa: E402,F401  (applies the SC24 options)
import emu_sc22_4 as T4  # noqa: E402
import drums18  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
V = T4.V
V.use_tdraw(); V.use_ccio()
E20, MGR, TMPL = T4.E20, T4.MGR, T4.TMPL
SEND, GATE, STK_EMIT, STK_RET = 0x0803BEDA, V.REC_GATE, V.STK_EMIT, V.STK_EMIT + 4
MIDI_IN, CTX_PTR = 0x08051720, 0x200069E4
SCR = 0x20065000


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
    gc.collect(); e = E20(img, man)
    sends, gates, stock = [], [], []
    def hk(uc, a, s, d):
        r = lambda x: uc.reg_read(x)
        if a == SEND:
            sends.append(bytes(uc.mem_read(r(UC_ARM_REG_R1), 3))); uc.reg_write(UC_ARM_REG_PC, r(UC_ARM_REG_LR) | 1)
        elif a == GATE:
            gates.append((r(UC_ARM_REG_R0), r(UC_ARM_REG_R1), r(UC_ARM_REG_R2))); uc.reg_write(UC_ARM_REG_PC, r(UC_ARM_REG_LR) | 1)
        elif a == STK_RET:
            stock.append((r(UC_ARM_REG_R0), r(UC_ARM_REG_R1), r(UC_ARM_REG_R2))); uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_SP, r(UC_ARM_REG_SP) + 24); uc.reg_write(UC_ARM_REG_PC, r(UC_ARM_REG_LR) | 1)   # skip the stock body: pop its 6-register frame
    for fa in (SEND, GATE, STK_RET): e.uc.hook_add(UC_HOOK_CODE, hk, begin=fa, end=fa)
    for _ in range(30): e.vtick()
    BASE = 0x08010000
    n28 = man["report"].get("nrpn28")                                              # SC28: its MIDI-in stage sits in front of c_vmin
    min_ = int(n28["labels"]["c_nmin"], 16) if n28 else L["c_vmin"]
    check(drums18.decode_bw(img, STK_EMIT) == L["c_vplay"] and drums18.decode_bw(img, V.STK_MIDIIN) == min_, "the two stock functions jump into c_vplay / c_vmin" + (" (through c_nmin)" if n28 else ""))
    ch = lambda t: e.r8(e.r32(V.TXOBJ + 0x0C) + 2 + t)
    check((ch(0), ch(1)) == (2, 3), f"the channels of MIDI 1 / MIDI 2: {ch(0)} / {ch(1)}")
    G = e.r32(V.SETOBJ - 8)
    gfst = int(man["report"]["sc17"]["labels"]["c_gfst"], 16)
    def v2(t, code):                                                              # the volatile values (codes 27..34) live in the Master FX block
        e.call(gfst); blk = e.uc.reg_read(UC_ARM_REG_R0)
        return struct.unpack("b", bytes([e.r8(blk + V.V2_OFF + 8 * t + code - 27)]))[0]
    snd = (G + 0x110, G + 0x158)

    # ---------------------------------------------------------------- the pad 27 fix
    e.btn(2); e.btn(8)
    pad = lambda p: (e.padr(p), e.rel(p))
    led = lambda: e.tleds(TMPL[0])
    stock_row = led()[:8]
    check(any(stock_row), f"the stock template row at the start: {[hex(x) for x in stock_row]}")
    pad(V.PAD_OSC)
    row_on = led()[:8]
    check(row_on != stock_row, f"mode on: the page row {[hex(x) for x in row_on]}")
    pad(V.PAD_OSC); pad(V.PAD_OSC)
    if man["marker"] in ("SC29", "SC30", "SC31", "SC32", "SC33", "SC34", "SC34.1", "SC34.2", "SC35"): pad(V.PAD_OSC)          # SC29: a fourth state (VA-drum) before off
    if "granular" in man["report"]:                                                                                             # SC36: VA-drum, granular, the FX sequencer
        for _ in range(3): pad(V.PAD_OSC)
    check(e.tailb(V.O_FLAGS) & 0x05 == 0 and led()[:8] == stock_row, f"mode off again: the stock template row is back ({[hex(x) for x in led()[:8]]})")
    pad(5)
    row2 = led()[:8]
    check(row2 != stock_row and led()[:8] == row2, "a template pad changes the row as in stock (the redraw follows the selection)")
    pad(0)
    check(led()[:8] == stock_row, "template 1 again: the original row")

    # ---------------------------------------------------------------- MIDI out + automation
    pad(V.PAD_OSC)                                                                # line in, mode on
    sends.clear(); gates.clear()
    e.knob_raw(4, 5)                                                              # K5 = FILT (code 1, bipolar): 0 -> 5
    check(e.val(0, 1) == 5 and sends == [bytes([0xB0 | ch(0), 74, 69])], f"K5 +5: FILT 5 goes out as CC 74 = 69 on channel {ch(0)}: {[s.hex() for s in sends]}")
    check(gates == [(V.REC_GATE_OBJ, 24, 69)], f"and is recorded in the lane 4 (id 24) with 69: {gates}")
    sends.clear(); gates.clear()
    e.knob_raw(0, 3)                                                              # K1 = ATK (code 5): CC 73, no lane
    check(sends == [bytes([0xB0 | ch(0), 73, 3])] and gates == [], f"K1 +3: ATK 3 = CC 73 = 3, no lane: {[s.hex() for s in sends]} {gates}")
    sends.clear(); gates.clear()
    e.knob_raw(6, 3)                                                              # K7 = LRATE (code 11, default 40): NRPN 0:76
    c = ch(0)
    check(sends == [bytes([0xB0 | c, 99, 0]), bytes([0xB0 | c, 98, 76]), bytes([0xB0 | c, 6, 43])], f"K7 +3: LRATE 43 = NRPN 0:76 = 43: {[s.hex() for s in sends]}")
    check(gates == [(V.REC_GATE_OBJ, 26, 43)], f"lane 6 (id 26): {gates}")
    sends.clear(); gates.clear()
    e.knob_raw(3, 2, True)                                                        # Shift + K4 = LFOF (code 4, bipolar): NRPN 4:4
    check(sends == [bytes([0xB0 | c, 99, 4]), bytes([0xB0 | c, 98, 4]), bytes([0xB0 | c, 6, 66])] and gates == [], f"Shift + K4: LFOF 2 = NRPN 4:4 = 66, no lane: {[s.hex() for s in sends]} {gates}")
    sends.clear(); gates.clear()
    pad(V.PAD_OSC)                                                                # oscillator source (page A still)
    pad(1)                                                                        # page B (OSC1)
    e.knob_raw(0, 3)                                                              # K1 = TUNE (code 17, bipolar): CC 26, lane 0
    check(e.val(0, 17) == 3 and sends == [bytes([0xB0 | c, 26, 67])] and gates == [(V.REC_GATE_OBJ, 20, 67)], f"page B K1 +3: TUNE 3 = CC 26 = 67, lane 0 (id 20): {[s.hex() for s in sends]} {gates}")
    sends.clear(); gates.clear()
    pad(V.PAD_PAGE); pad(2)                                                       # two oscillators, page C (OSC2)
    e.knob_raw(0, 2)                                                              # TUNE2 (code 27, volatile): CC 37, no lane
    check(v2(0, 27) == 2 and sends == [bytes([0xB0 | c, 37, 66])] and gates == [], f"page C K1 +2: TUNE2 2 = CC 37 = 66: {[s.hex() for s in sends]} {gates}")
    sends.clear(); gates.clear()
    e.knob_raw(1, 5, True)                                                        # Shift + K2 = FM (code 33): NRPN 4:33
    check(sends == [bytes([0xB0 | c, 99, 4]), bytes([0xB0 | c, 98, 33]), bytes([0xB0 | c, 6, 5])], f"Shift + K2: FM 5 = NRPN 4:33 = 5: {[s.hex() for s in sends]}")
    sends.clear()
    pad(V.PAD_PAGE); pad(0)                                                       # one oscillator, page A
    # the second track: its own channel and its own lane ids
    e.btn(3); e.track(3); e.btn(8)
    e.call(L["c_vset"], 1, 1); e.vtick()
    sends.clear(); gates.clear()
    e.knob_raw(4, 4)
    check(sends == [bytes([0xB0 | ch(1), 74, 68])] and gates == [(V.REC_GATE_OBJ, 34, 68)], f"MIDI 2: FILT 4 = CC 74 = 68 on channel {ch(1)}, lane id 34: {[s.hex() for s in sends]} {gates}")
    # Clear + a knob sends the default
    sends.clear(); gates.clear()
    e.btn(2); e.track(2); e.btn(8)
    clr_dn = lambda: e.call(0x08033320, MGR, 23, maxins=900000)
    clr_up = lambda: e.call(0x0803381A, MGR, 23, maxins=900000)
    clr_dn(); e.knob_raw(0, 1); clr_up()
    check(e.val(0, 5) == V.DEFAULTS[4] and any(s[1] == 73 and s[2] == V.DEFAULTS[4] for s in sends), f"Clear + K1: ATK back to {V.DEFAULTS[4]} and CC 73 = {V.DEFAULTS[4]} sent: {[s.hex() for s in sends]}")

    # ---------------------------------------------------------------- the lane playback (the stock macro sender)
    check(True, f"the senders: MIDI 1 {snd[0]:#x}, MIDI 2 {snd[1]:#x}")
    e.set_p0(V.PLAY_STORE, 0)
    e.knob_raw(0, 3)                                                              # (mode on: our handler; nothing from the stock sender)
    sends.clear(); stock.clear()
    e.call(0x080313C4, snd[0], 4, 100)
    check(len(stock) == 1 and e.val(0, 1) == 5 and sends == [], f"transport stopped: the stock function runs ({len(stock)}), FILT untouched ({e.val(0, 1)})")
    e.set_p0(V.PLAY_STORE, 1)
    stock.clear(); sends.clear(); gates.clear()
    e.call(0x080313C4, snd[0], 4, 100)
    r0 = e.uc.reg_read(UC_ARM_REG_R0)
    check(stock == [] and r0 == 0 and e.val(0, 1) == 36 and sends == [bytes([0xB0 | ch(0), 74, 100])] and gates == [], f"playing, lane 4 = 100: FILT {e.val(0, 1)} (36), CC 74 = 100 out, no stock, no recording: {[s.hex() for s in sends]}")
    check(e.rt(0, V.RT_DLO) & 1, "the value is marked for the DSP")
    sends.clear()
    e.call(0x080313C4, snd[0], 4, 100)
    check(sends == [] and stock == [], "the same value again: nothing is sent")
    e.call(0x080313C4, snd[0], 0, 70)
    check(e.val(0, 17) == 6 and sends == [bytes([0xB0 | ch(0), 26, 70])], f"lane 0 = 70: TUNE {e.val(0, 17)} (6), CC 26 = 70: {[s.hex() for s in sends]}")
    sends.clear(); stock.clear()
    e.call(0x080313C4, snd[0], 8, 50)
    check(len(stock) == 1 and sends == [], "a knob above 7: the stock function")
    stock.clear()
    e.call(0x080313C4, 0x20000100, 4, 50)
    check(len(stock) == 1, "another sender: the stock function")
    stock.clear()
    e.call(0x080313C4, snd[1], 4, 50)                                             # MIDI 2: the mode is on (set above)
    check(stock == [] and e.val(1, 1) == -14 and sends[-1:] == [bytes([0xB0 | ch(1), 74, 50])], f"MIDI 2 lane 4 = 50: FILT {e.val(1, 1)} (-14): {[s.hex() for s in sends]}")
    e.call(L["c_vset"], 1, 0)
    stock.clear(); sends.clear()
    e.call(0x080313C4, snd[1], 4, 80)
    check(len(stock) == 1 and e.val(1, 1) == -14 and sends == [], "MIDI 2 mode off: the stock function")
    # the sender that the stock macro handler really uses is the one the table says (a stock knob turn on a track with the mode off)
    e.set_p0(V.PLAY_STORE, 0)
    stock.clear()
    e.btn(3); e.track(3); e.btn(8)
    e.knob_raw(0, 1)
    check(len(stock) == 1 and stock[0][0] == snd[1], (f"a stock knob turn of MIDI 2 reaches the sender {stock[0][0]:#x} = G + 0x158") if stock else "a stock knob turn reaches the sender")
    e.btn(2); e.track(2); e.btn(8)
    e.set_p0(V.PLAY_STORE, 1)

    # ---------------------------------------------------------------- MIDI in
    ctx = e.r32(CTX_PTR)
    def midi(status, d1, d2):
        e.uc.mem_write(SCR, bytes([status, d1, d2]))
        e.call(MIDI_IN, ctx, SCR, maxins=3_000_000)
    e.btn(2); e.track(2)
    check(e.tailb(V.O_FLAGS) & 3 == 1, f"MIDI 1 on, MIDI 2 off (flags {e.tailb(V.O_FLAGS):#x})")
    sends.clear()
    e.uc.mem_write(ctx + 0x14, bytes([0x0F]))
    midi(0xB0 | ch(0), 74, 100)
    check(e.val(0, 1) == 36 and e.rt(0, V.RT_DLO) & 1, f"CC 74 = 100 on the channel of MIDI 1: FILT {e.val(0, 1)}")
    midi(0xB0 | ch(0), 71, 90)
    check(e.val(0, 2) == 90, f"CC 71: RES {e.val(0, 2)}")
    midi(0xB0 | ch(0), 79, 100)
    check(e.val(0, 3) == 36, f"CC 79: ENVF {e.val(0, 3)}")
    midi(0xB0 | ch(0), 21, 127)
    check(e.val(0, 20) == 100, f"CC 21: PW clamped to 100 ({e.val(0, 20)})")
    midi(0xB0 | ch(0), 37, 80)
    check(v2(0, 27) == 16, f"CC 37: TUNE2 (volatile) {v2(0, 27)} (16)")
    midi(0xB0 | ch(0), 99, 4); midi(0xB0 | ch(0), 98, 21); midi(0xB0 | ch(0), 6, 90)
    check(e.val(0, 21) == 26, f"NRPN 4:21 = 90: LFOP {e.val(0, 21)} (26)")
    midi(0xB0 | ch(0), 99, 0); midi(0xB0 | ch(0), 98, 76); midi(0xB0 | ch(0), 6, 100)
    check(e.val(0, 11) == 100, f"NRPN 0:76 = 100: LRATE {e.val(0, 11)}")
    before = e.val(0, 1)
    midi(0xB0 | ch(0), 99, 3); midi(0xB0 | ch(0), 98, 1); midi(0xB0 | ch(0), 6, 5)
    check(e.val(0, 1) == before, "an NRPN of the stock synth (3:1) is not ours")
    midi(0xB0 | 5, 74, 10)
    check(e.val(0, 1) == before, "a channel no track listens to: ignored")
    midi(0xB0 | ch(1), 74, 10)
    check(e.val(1, 1) == -14, f"MIDI 2 (mode off): ignored (FILT {e.val(1, 1)}, flags {e.tailb(V.O_FLAGS):#x})")
    e.uc.mem_write(ctx + 0x14, bytes([0x0D]))
    midi(0xB0 | ch(0), 74, 10)
    check(e.val(0, 1) == before, "Setup CC Rx off: ignored")
    e.uc.mem_write(ctx + 0x14, bytes([0x2F]))
    midi(0xB0 | ch(0), 74, 10)
    check(e.val(0, 1) == before, "an internal copy (the loopback of SC05): ignored")
    e.uc.mem_write(ctx + 0x14, bytes([0x0F]))
    midi(0x90 | ch(0), 74, 10)
    check(e.val(0, 1) == before, "a note is not a CC")
    check(sends == [], f"nothing is sent back by any incoming message ({[s.hex() for s in sends]})")
    # the loopback: MIDI 1 on the channel of Synth 1 -> the CC also goes into the stock receiver (marked internal): our own hook ignores that copy
    tbl = e.r32(V.TXOBJ + 0x0C); e.uc.mem_write(tbl + 2, bytes([0]))
    sends.clear()
    e.knob_raw(4, 1)
    check(e.val(0, 1) == before + 1 and sends and sends[0][0] == 0xB0, f"MIDI 1 on the channel of Synth 1: the knob turn still works ({e.val(0, 1)}), sent {[s.hex() for s in sends]}")
    e.uc.mem_write(tbl + 2, bytes([2]))
    # the DSP gets the values set by the incoming CC and the playback
    got = {}
    for _ in range(80):
        for w, ad in e.vtick():
            if ad == VD.VB0: got[(w >> 16) & 0x7F] = w & 0xFFFF
    check(got.get(1) == e.val(0, 1) & 0xFFFF and got.get(3) == e.val(0, 3) & 0xFFFF and got.get(2) == e.val(0, 2), f"the DSP mailbox of voice 0 holds the values set by CC / playback: FILT {got.get(1)}, RES {got.get(2)}, ENVF {got.get(3)}")
    print("SC25 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
