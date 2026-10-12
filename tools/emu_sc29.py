"""SC29 ARM tests (the VA-drum engine: the fourth state of pad 27, pad 31, the engine nibble in the signature byte, the ACT message) through the real routes (pads, the LED handler, the DSP service tick):

    python tools/emu_sc29.py SC29.bin SC29_manifest.json
  * boot: a saved state with any engine nibble (signature 0xB0..0xBF) is kept as it is; another signature starts from the defaults (0xB0);
  * pad 27: off -> line in -> oscillator -> VA-drum -> off; its LED; the ACT message carries the flag in bit 10 (with the chain order and the two-oscillator flag);
  * pad 31: only in the VA-drum state: velocity -> envelopes on / off (ACT bit 11), its LED; dark and without function in the other states and while the CC editor draws its numbers;
  * each track has its own two bits; the settings save is requested.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc27 as T27  # noqa: E402,F401  (applies the options of SC25..SC27)
import emu_sc22_4 as T4  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
V = T4.V
V.use_vadrum()
E20, MGR, TMPL = T4.E20, T4.MGR, T4.TMPL


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}

    # ---------------------------------------------------------------- boot
    for sig, keep in ((0xB5, True), (0xBF, True), (0xB0, True), (0xC0, False), (0xA5, False)):
        gc.collect(); e = E20(img, man)
        t = bytearray(75); t[V.O_FLAGS] = 0x85; t[V.O_SIG] = sig
        for i in range(52): t[V.O_PAR + i] = (i * 5) % 50
        e.uc.mem_write(V.TAIL, bytes(t))
        for _ in range(12): e.vtick()
        same = [e.tailb(V.O_PAR + i) == (i * 5) % 50 for i in range(52) if i not in (13, 39)]
        if keep: check(e.tailb(V.O_SIG) == sig and all(same) and e.tailb(V.O_FLAGS) & 0x8F == 0x85, f"a saved state with the signature {sig:#x}: kept (signature {e.tailb(V.O_SIG):#x}, flags {e.tailb(V.O_FLAGS):#x})")
        else: check(e.tailb(V.O_SIG) == 0xB0 and not all(same) and e.tailb(V.O_FLAGS) == 0x80, f"the signature {sig:#x}: the defaults (signature {e.tailb(V.O_SIG):#x}, flags {e.tailb(V.O_FLAGS):#x})")
        del e
    gc.collect(); e = E20(img, man)
    for _ in range(30): e.vtick()
    sig = lambda: e.tailb(V.O_SIG)
    pad = lambda p: (e.padr(p), e.rel(p))
    def mbox(n=60, voice=0):
        got = {}
        for _ in range(n):
            for w, ad in e.vtick():
                if ad == VD.VB0 + voice * VD.VBS: got[(w >> 16) & 0x7F] = w & 0xFFFF
        return got
    e.btn(2); e.track(2); e.btn(8)
    led = lambda t=0: e.tleds(TMPL[t])
    on = lambda t=0: (e.tailb(V.O_FLAGS) >> t) & 1
    osc = lambda t=0: (e.tailb(V.O_FLAGS) >> (2 + t)) & 1

    # ---------------------------------------------------------------- pad 27
    check(sig() == 0xB0 and not on() and led()[V.PAD_OSC] == 0 and led()[V.PAD_VEL] == 0, "start: off, signature 0xb0, pads 27 / 31 dark")
    pad(V.PAD_OSC); g = mbox()
    check(on() and not osc() and sig() == 0xB0 and led()[V.PAD_OSC] == V.COL_ON and g.get(19) == 1, f"pad 27: line in (ACT {g.get(19)}), LED {led()[V.PAD_OSC]:#x}")
    pad(V.PAD_OSC); g = mbox()
    check(on() and osc() and sig() == 0xB0 and led()[V.PAD_OSC] == V.COL_OSC[0] and g.get(19) == 2, f"again: the oscillator (ACT {g.get(19)}), LED {led()[V.PAD_OSC]:#x}")
    pad(V.PAD_VEL); g = mbox(20)
    check(sig() == 0xB0 and 19 not in g and led()[V.PAD_VEL] == 0, "pad 31 in the oscillator state: nothing, dark")
    e.saves.clear(); pad(V.PAD_OSC); g = mbox()
    check(on() and osc() and sig() == 0xB1 and led()[V.PAD_OSC] == V.COL_VD and g.get(19) == (2 | 1 << 10) and e.saves, f"again: VA-drum (signature {sig():#x}, ACT {g.get(19):#x}), LED {led()[V.PAD_OSC]:#x}, the settings save requested")
    check(led()[V.PAD_VEL] == V.COL_VEL[1], f"pad 31 shows (off: {led()[V.PAD_VEL]:#x})")
    pad(V.PAD_PAGE); g = mbox()                                                   # two oscillators
    check(g.get(19) == (2 | 1 << 9 | 1 << 10), f"with two oscillators: ACT {g.get(19):#x}")
    pad(V.PAD_VCF); g = mbox()                                                    # the chain order
    check(g.get(19) == (2 | 1 << 8 | 1 << 9 | 1 << 10), f"and the other chain order: ACT {g.get(19):#x}")
    pad(V.PAD_VCF); pad(V.PAD_PAGE); mbox()
    # ---------------------------------------------------------------- pad 31
    e.saves.clear(); pad(V.PAD_VEL); g = mbox()
    check(sig() == 0xB5 and g.get(19) == (2 | 1 << 10 | 1 << 11) and led()[V.PAD_VEL] == V.COL_VEL[0] and e.saves, f"pad 31: velocity -> envelopes (signature {sig():#x}, ACT {g.get(19):#x}), LED {led()[V.PAD_VEL]:#x}")
    pad(V.PAD_VEL); g = mbox()
    check(sig() == 0xB1 and g.get(19) == (2 | 1 << 10) and led()[V.PAD_VEL] == V.COL_VEL[1], "again: off")
    pad(V.PAD_VEL); mbox()
    # the CC editor draws with all the pads
    pad(V.PAD_CC)
    s0 = sig(); pad(V.PAD_VEL)
    check(sig() == s0, "with the CC editor on pad 31 has no function")
    pad(V.PAD_CC)
    check(led()[V.PAD_VEL] == V.COL_VEL[0], "the editor off: its LED is back")
    # the step-drummer still opens in this state
    pad(V.PAD_SD)
    check(e.tailb(V.O_FLAGS) & V.F_SDOPEN and led()[V.PAD_VEL] == V.COL_VEL[0] and led()[V.PAD_OSC] == V.COL_VD, "pad 30: the step-drummer view opens in the VA-drum state (pads 27 / 31 keep their LEDs)")
    pad(V.PAD_SD)
    # ---------------------------------------------------------------- the second track
    e.btn(3); e.track(3); e.btn(8)
    for _ in range(3): e.padr(V.PAD_OSC); e.rel(V.PAD_OSC)
    g = mbox(voice=1)
    check(sig() == 0xB7 and g.get(19) == (2 | 1 << 10) and led(1)[V.PAD_OSC] == V.COL_VD and led(1)[V.PAD_VEL] == V.COL_VEL[1], f"MIDI 2: its own bits (signature {sig():#x}, ACT {g.get(19):#x})")
    e.padr(V.PAD_VEL); e.rel(V.PAD_VEL); g = mbox(voice=1)
    check(sig() == 0xBF and g.get(19) == (2 | 1 << 10 | 1 << 11), f"its pad 31 (signature {sig():#x})")
    e.padr(V.PAD_OSC); e.rel(V.PAD_OSC); g = mbox(voice=1)
    check(sig() == 0xB5 and not on(1) and g.get(19) == 0 and led(1)[V.PAD_OSC] == 0 and led(1)[V.PAD_VEL] == 0, f"pad 27 again: off (signature {sig():#x}: the two bits of the track cleared, ACT {g.get(19)}), pads 27 / 31 dark")
    e.padr(V.PAD_OSC); e.rel(V.PAD_OSC); e.padr(V.PAD_OSC); e.rel(V.PAD_OSC); g = mbox(voice=1)
    check(g.get(19) == 2 and led(1)[V.PAD_VEL] == 0, f"and the cycle starts again at line in, then the oscillator (ACT {g.get(19)}), pad 31 dark")
    e.btn(2); e.track(2); e.btn(8)
    check(led()[V.PAD_OSC] == V.COL_VD and sig() & 5 == 5, "MIDI 1 is still in VA-drum with its pad 31 on")
    # the values of the mode are the same ones: a knob still moves them
    b = e.val(0, 6); e.knob_raw(1, 4, shift=True)
    check(e.val(0, 6) == b + 4, f"the knobs keep their values (DEC {b} -> {e.val(0, 6)}; in VA-drum = the decay of the VCA)")
    print("SC29 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
