"""SC57.9 / Beta 5.64 ARM tests (vcf21.use_fsqmute + build_sc17.use_fsqmute): the FX sequencer's eighth value = mute.
MIDI 1 in the FX sequencer state, a note on step 1, its pair at position 127 (the eighth zone):
  * c_fsqbits = bit 7 only (no slot, no random seed); at position 112 (value 7) bit 6 + a seed as before; at 96 (value 6) bit 5;
  * the DSP service tick (c_fxtick) writes FX_ON to the DSP with bit 7 while the step holds the mute and without it after (one write per change);
  * the knob LED of the pair: red (0x53);
  * the previous build: position 127 is past its range (nothing, LED dark).

    python tools/emu_fsqmute.py BUILD.bin manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R4
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import MGR  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
import emu_sc36_1 as T361  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import patchain as PC  # noqa: E402

ENG = PC.ENG


def seq_part(img, man):
    V = T361.V
    e = T361.E20(img, man)
    L17 = {k: int(v, 16) for k, v in man["report"]["sc17"]["labels"].items()}
    def fxtick(maxins=8_000_000):                                            # the harness stubs c_fxtick as the next link of the service chain: not for this call
        nx = e.s18["svc_next"]; e.s18["svc_next"] = 0
        e.dw.clear(); e.call(L17["c_fxtick"], maxins=maxins)
        e.s18["svc_next"] = nx
        return [x[1] for x in e.dw if len(x) == 3 and x[2] == G.FX_ON]
    for _ in range(30): e.vtick()
    pad = lambda p: (e.padr(p), e.rel(p))
    def r0(fn, *a): e.call(fn, *a, maxins=8_000_000); return e.uc.reg_read(UC_ARM_REG_R0)
    def put(store, k, data):
        for fn in (0x080354FA, 0x0803542C): e.uc.mem_write(r0(fn, store, k), data)
    def led60():
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR); e.call(0x08033B3E, maxins=40_000_000)
        return struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138)))[60]
    e.btn(2); e.track(2); e.btn(8)
    pad(30)                                                                   # (modesel ROW2) pad 31 with no voice = the FX sequencer on
    assert r0(e.vl["c_fsq"], 0) == 1, "MIDI 1 not in the FX sequencer state"
    pad(V.PAD_SD)
    e.set_p0(e.r32(MGR + 0xC), 1); pad(0); e.set_p0(e.r32(MGR + 0xC), 0)        # a note on step 1
    pat = r0(e.vl["c_sdpat"], 0); h0 = r0(e.vl["c_sdhalf"], 0)
    put(0x20011034, 0, b"")
    pl = e.r32(ENG + 0x30 + 4 * 2); put(pl, 1, bytes([h0])); put(pl, 2, struct.pack("<I", 0))
    put(e.r32(ENG + 0x90), 0, struct.pack("<I", 0x1234))
    fxtick(400_000_000)                                                       # the first call generates the Master FX tables (gentab): long
    out = {}
    for pos in (127, 112, 96, 127):
        for st in (h0, h0 + 1): e.uc.mem_write(r0(e.vl["c_sdlna"], pat, st), bytes([pos]) * 12)
        bits = r0(e.vl["c_fsqbits"])
        writes = []
        for _ in range(3): writes += fxtick()                                  # the DSP service tick's Master FX part: FX_ON sent on change
        put(pl, 1, bytes([h0 + 8]))                                           # the LED task: the playing pair shows the head in white, not its value
        led = led60(); put(pl, 1, bytes([h0]))
        out[pos] = (bits, list(writes), led)
    e.set_p0(e.r32(MGR + 0xC), 1); pad(0); e.set_p0(e.r32(MGR + 0xC), 0)        # the note off the step
    writes = []
    for _ in range(3): writes += fxtick()
    out["off"] = writes
    del e; gc.collect()
    return out


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    out = seq_part(img, man)
    b127, w127, l127 = out[127]; b112, w112, l112 = out[112]; b96, w96, l96 = out[96]
    check(b127 == 0x80, f"position 127: c_fsqbits = bit 7 only ({b127:#x})")
    check(b112 & 0x7F == 0x40 and b112 >> 8 and b96 == 0x20, f"positions 112 / 96: random with a seed, slot 6 as before ({b112:#x}, {b96:#x})")
    check(w127 and w127[-1] & 0x80 and len(w127) == 1, f"c_fxtick sends FX_ON with bit 7 once while the step holds the mute ({[hex(x) for x in w127]})")
    check(w112 and not (w112[-1] & 0x80) and w96 and not (w96[-1] & 0x80), f"at values 7 / 6 the next FX_ON goes without bit 7 ({[hex(x) for x in w112]}, {[hex(x) for x in w96]})")
    check(l127 & 0xFF == 0x53 and l112 & 0xFF == 0x01, f"the knob LED of the pair: red at the mute, white at random ({l127:#x}, {l112:#x})")
    check(out["off"] and not (out["off"][-1] & 0x80), f"the note off the step: FX_ON sent without the bit ({[hex(x) for x in out['off']]})")
    if prev:
        gc.collect(); pout = seq_part(prev, pman)
        check(pout[127][0] == 0 and not any(w & 0x80 for w in pout[127][1]) and pout[127][2] & 0xFF != 0x53, f"the previous build: position 127 = nothing (bits {pout[127][0]:#x}, LED {pout[127][2]:#x})")
    print(f"{man.get('marker', '?')} FSQMUTE ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    prev = (Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) if len(a) > 4 else (None, None)
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), *prev) else 0)
