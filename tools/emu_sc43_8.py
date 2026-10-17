"""SC43.8 ARM tests, through the controller, the real LED task and the players' note-on:
  * the drums' side-chain from patterns (scpat.use_drums): Sidechain view (Shift + FX), Octave down twice = the page of Drums 1 / 2; pad 18 =
    Drum 1's first preset; row 1 pad 1 = Synth 1 as its trigger (SC16's trigger byte = 4); LEDs: pad 1 in the colour of SC16's chosen source,
    pads 2-8 dim; a Synth 1 pattern note writes word 0 of Drum 1's block (X:$3A10 = 1), a MIDI 1 note nothing; pad 4 = MIDI 2: a MIDI 2 note
    fires it; pad 5 (Drum 1) = back to SC16's drum trigger (byte 0): a Synth 1 note nothing; Drum 2 with Synth 2; a preset OFF fires nothing;
  * the own engine over a power cycle (engsave, vcf21.use_v2save): the stock's settings save (the real 0x0802D2AC, its write call captured) writes
    codes 27..34 of both tracks, the toggles (two oscillators, chain order, knob page), 0xE7 and the sum in the runtime bytes of its copy, the
    live record untouched; a power-up (the DSP service chain's head, vcf21 not initialised) with that record = codes 27..34 and the bits back,
    ACT to be sent; a record without the signature or with a wrong sum = the defaults; the written record booted again = the same values;
    an OSC 2 knob (code 32), pad 28 (two oscillators) and the granular page's Shift + K1 (code 28) of MIDI 1 now ask for the save.

    python tools/emu_sc43_8.py SC43.8.bin SC43.8_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_SP, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import scpat as SP  # noqa: E402

MGR = T.MGR
DSP_W = 0x080292F8
PLAYER0, PLAYER_SZ = 0x20040200, 0x184


def lab(man, m, k): return int(man["report"][m]["labels"][k], 16)


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    sc_tests(img, man, check)
    save_tests(img, man, check)
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


def sc_tests(img, man, check):
    gc.collect(); e = T.EL(img); e.at(300000); e.transport(0)
    dsp = []
    def w(uc, a, s, d): dsp.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1) >> 8, uc.reg_read(UC_ARM_REG_R2)))
    e.uc.hook_add(UC_HOOK_CODE, w, begin=DSP_W, end=DSP_W)
    def rest(uc, a, s, d):                                                            # the rest of the note-on: pop {r4-r8, pc} (the sound path waits for the DSP)
        sp = uc.reg_read(UC_ARM_REG_SP); ws = struct.unpack("<6I", bytes(uc.mem_read(sp, 24)))
        for r, v in zip((UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8), ws[:5]): uc.reg_write(r, v)
        uc.reg_write(UC_ARM_REG_SP, sp + 24); uc.reg_write(UC_ARM_REG_PC, ws[5])
    e.uc.hook_add(UC_HOOK_CODE, rest, begin=0x08040FA6, end=0x08040FA6)
    st = int(man["report"]["sc16"]["sc16_state"], 16)
    note = lambda t: (dsp.clear(), e.call(0x08040FA2, PLAYER0 + t * PLAYER_SZ, 60, 100, 6, maxins=3_000_000), [x for x in dsp if 0x3A10 <= x[2] < 0x3A34])[2]
    e.set_p0(e.r32(MGR + 0xC), 1); e.btn(15); e.set_p0(e.r32(MGR + 0xC), 0)
    e.btn(19); e.btn(19); X.frame(e)
    page = e.r8(st + 12)
    e.pad(17); e.pad(0); f = X.frame(e)
    tr, pre, d = e.r8(st + 8), e.r8(st + 4), e.r8(st + 13)
    pal = lambda i: struct.unpack_from("<H", img, SP.PAL - 0x08010000 + 2 * i)[0]
    check(page == 2 and d == 0 and pre == 1 and tr == SP.OWN0, f"the Drums 1 / 2 page ({page}); pad 18 = Drum 1's preset 1 ({pre}, drum {d}); pad 1 = Synth 1 as its trigger ({tr})")
    check(f[0] == pal(5) and all(x == pal(SP.DIM_I) for x in f[1:8]), f"LEDs: pad 1 in the chosen source's colour ({f[0]:#x} = {pal(5):#x}), pads 2-8 dim ({[hex(x) for x in f[1:8]]})")
    n0, n2 = note(0), note(2)
    check(n0 == [(0, 1, 0x3A10)] and n2 == [], f"a Synth 1 pattern note: Drum 1's trigger word X:$3A10 = 1 ({n0}); a MIDI 1 note nothing ({n2})")
    e.pad(3); n3, n0b = note(3), note(0)
    check(e.r8(st + 8) == SP.OWN0 + 3 and n3 == [(0, 1, 0x3A10)] and n0b == [], f"pad 4 = MIDI 2: a MIDI 2 note fires it ({n3}), Synth 1 no longer ({n0b})")
    e.pad(4); n0c = note(0); f2 = X.frame(e)
    check(e.r8(st + 8) == 0 and n0c == [] and f2[4] == pal(5) and all(x == pal(SP.DIM_I) for x in f2[:4]),
          f"pad 5 (Drum 1) = SC16's drum trigger again ({e.r8(st + 8)}): a Synth 1 note nothing ({n0c}); pad 5 lit, pads 1-4 dim ({[hex(x) for x in f2[:8]]})")
    e.pad(25); e.pad(1); n1 = note(1)                                                 # Drum 2's preset 1 (pad 26), then pad 2 = Synth 2
    check(e.r8(st + 13) == 1 and e.r8(st + 9) == SP.OWN0 + 1 and n1 == [(0, 1, 0x3A10 + 9)], f"Drum 2, pad 2 = Synth 2: a Synth 2 note fires Drum 2's block X:$3A19 ({n1})")
    e.pad(24); n1b = note(1)
    check(e.r8(st + 5) == 0 and n1b == [], f"Drum 2's preset OFF (pad 25): its trigger fires nothing ({n1b})")
    del e; gc.collect()


def save_tests(img, man, check):
    import emu_sc22_4 as T4                                                           # (its import sets vcf21's options: O_RT 53, O_SAVED 69)
    import engsave as ES, lazysave as LZ
    V = T4.V
    gfst = lab(man, "sc17", "c_gfst"); boot = lab(man, "engsave", "c_esboot")
    vals = [5, -7, 100, 33, 90, 64, -60, 127, -24, 63, 0, 12, 1, 99, -1, 50]
    tog = 0x69                                                                        # MIDI 1 two oscillators, MIDI 2 chain order; pages 2 / 1
    def fresh():
        gc.collect(); e = T.EL(img); e.at(300000); e.transport(0)
        e.call(gfst); blk = e.uc.reg_read(UC_ARM_REG_R0)
        e.uc.mem_write(blk + V.FLAGS_BYTE, bytes([e.r8(blk + V.FLAGS_BYTE) & ~V.B_BOOT]))  # not initialised: a power-up
        return e, blk
    def record(e, sig=ES.SIG, bad=0):
        b = bytes(v & 0xFF for v in vals)
        e.uc.mem_write(V.TAIL + V.O_RT, b); e.uc.mem_write(V.TAIL + V.O_SAVED, bytes([tog]))
        e.uc.mem_write(V.TAIL + V.O_ED, bytes([sig, ((sum(b) + tog) & 0xFF) ^ ES.SUMX ^ bad]))
    rt = lambda e, t, f: e.r8(V.TAIL + V.O_RT + 8 * t + f)
    v2 = lambda e, blk: [struct.unpack("b", bytes([e.r8(blk + V.V2_OFF + k)]))[0] for k in range(16)]
    e, blk = fresh(); record(e)
    e.call(boot, maxins=20_000_000)
    got = v2(e, blk)
    bits = (rt(e, 0, V.RT_VEL) >> 7, rt(e, 1, V.RT_VEL) >> 7, rt(e, 0, V.RT_NOTE) >> 7, rt(e, 1, V.RT_NOTE) >> 7, (rt(e, 0, V.RT_TAG) >> 1) & 3, (rt(e, 1, V.RT_TAG) >> 1) & 3)
    check(e.r8(blk + V.FLAGS_BYTE) & V.B_BOOT and got == vals, f"power-up with our record: codes 27..34 back ({got})")
    check(bits == (1, 0, 0, 1, 2, 1) and rt(e, 0, V.RT_AUX) & 1 and rt(e, 1, V.RT_AUX) & 1 and rt(e, 0, V.RT_NOTE) & 0x7F == 60,
          f"the toggles back: two oscillators / chain order / page {bits}, ACT to be sent, the note 60 kept")
    # the save: its write captured
    cap = []
    from unicorn.arm_const import UC_ARM_REG_R3
    def wr(uc, a, s_, d): cap.append(bytes(uc.mem_read(uc.reg_read(UC_ARM_REG_R3), 128)))
    e.uc.hook_add(UC_HOOK_CODE, wr, begin=ES.WRITE, end=ES.WRITE)
    e.uc.mem_write(blk + V.V2_OFF + 3, bytes([77])); vals2 = list(vals); vals2[3] = 77
    live = bytes(e.uc.mem_read(V.TAIL + V.O_RT, 16)) + bytes(e.uc.mem_read(V.TAIL + V.O_SAVED, 4))
    e.stock_save()
    c = cap[-1] if cap else bytes(128)
    o = ES.T_IN_REC
    w_v2 = [struct.unpack("b", bytes([x]))[0] for x in c[o + V.O_RT:o + V.O_RT + 16]]
    w_tog, w_sig, w_sum = c[o + V.O_SAVED], c[o + V.O_ED], c[o + V.O_ED + 1]
    live2 = bytes(e.uc.mem_read(V.TAIL + V.O_RT, 16)) + bytes(e.uc.mem_read(V.TAIL + V.O_SAVED, 4))
    check(len(cap) == 1 and w_v2 == vals2 and w_tog == tog and w_sig == ES.SIG and w_sum == ((sum(c[o + V.O_RT:o + V.O_RT + 16]) + tog) & 0xFF) ^ ES.SUMX,
          f"the save writes codes 27..34 ({w_v2}), the toggles {w_tog:#x}, {w_sig:#x}, the sum {w_sum:#x} ({len(cap)} write)")
    check(live2 == live and c[:o] == bytes(e.uc.mem_read(V.SETOBJ + 8, o)), "the live record untouched; the rest of the record as the stock's")
    del e; gc.collect()
    # the written record, booted again
    e, blk = fresh(); e.uc.mem_write(V.TAIL + V.O_RT, c[o + V.O_RT:o + V.O_RT + 16]); e.uc.mem_write(V.TAIL + V.O_SAVED, bytes([w_tog]))
    e.uc.mem_write(V.TAIL + V.O_ED, bytes([w_sig, w_sum])); e.call(boot, maxins=20_000_000)
    check(v2(e, blk) == vals2, f"that record at the next power-up: the same ({v2(e, blk)})")
    del e; gc.collect()
    for sig, bad, what in ((0x00, 0, "without the signature"), (ES.SIG, 1, "a wrong sum")):
        e, blk = fresh(); record(e, sig, bad); e.call(boot, maxins=20_000_000)
        got = v2(e, blk)
        check(got == list(V.DEFAULTS_V2) * 2 and rt(e, 0, V.RT_VEL) >> 7 == 0, f"a record {what}: the defaults ({got})")
        del e; gc.collect()
    # the knobs and pad 28 ask for the save (the calls of the save from the mod's code: lazysave keeps them pending)
    e = T4.E20(img, man)
    asks = []
    from unicorn.arm_const import UC_ARM_REG_LR
    def sv(uc, a, s_, d):
        if uc.reg_read(UC_ARM_REG_LR) >= 0x0805CDDC: asks.append(1)
    e.uc.hook_add(UC_HOOK_CODE, sv, begin=LZ.SAVE_IN, end=LZ.SAVE_IN)
    L = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
    for _ in range(30): e.vtick()
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.tailb(V.O_FLAGS) | 0x05]))
    for _ in range(20): e.vtick()
    e.btn(2); e.btn(8); e.call(L["c_vsetpage"], 0, 2)
    later = lambda: e.w32(LZ.HAL_TICK, e.r32(LZ.HAL_TICK) + 2000)                    # past c_vsave's 700 ms
    later(); asks.clear(); e.knob_raw(5, 4); p1 = len(asks)
    later(); asks.clear(); e.padr(27); e.rel(27); p2 = len(asks); d = e.r8(V.TAIL + V.O_RT + V.RT_VEL) >> 7
    check(p1 >= 1 and p2 >= 1 and d == 1, f"OSC 2's K6 (code 32) and pad 28 (two oscillators: {d}) ask for the save ({p1}, {p2})")
    gf = (e.call(gfst), e.uc.reg_read(UC_ARM_REG_R0))[1]
    e.padr(26); e.rel(26); e.padr(26); e.rel(26); e.call(L["c_vsetpage"], 0, 1)          # pad 27 twice: VA-drum, then granular; its page
    c28 = lambda: struct.unpack("b", bytes([e.r8(gf + V.V2_OFF + 1)]))[0]
    g0 = c28(); later(); asks.clear(); e.knob_raw(0, 3, shift=True); g1 = c28(); p3 = len(asks)
    check(g1 == g0 + 3 and p3 >= 1, f"the granular page, Shift + K1 (code 28): {g0} -> {g1}, asks for the save ({p3})")
    del e; gc.collect()


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
