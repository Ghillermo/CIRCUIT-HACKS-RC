"""SC14.2 whole-core DSP tests: the SC10 flag no longer touches the voice-slot table.

    python tools/emu_sc14_2.py STOCK.bin SC14.bin SC14.2.bin
Needs dsptool with the memtrace patch ($DSPTOOL).
"""
from __future__ import annotations
import sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dsp_session import Session  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_R0  # noqa: E402

AUDIO_IN_GROUP = 0x08028EA4
FLAGS = 0x3A00
SLOTS = (0xEB, 0x15B)


def voice_state(img, p2bits=0):
    """Audio In group (H9) + a Synth 1 note, 8 blocks -> slot table, voice 0 state, core-1 fetch list, flag."""
    s = Session(img)
    if p2bits:
        st = s.e.r32(s.e.r32(s.e.r32(0x200069E4)) + 0x54)
        s.e.call(0x080354FA, st, 2); p = s.e.uc.reg_read(UC_ARM_REG_R0)
        s.e.w32(p, s.e.r32(p) | p2bits << 28); s.e.call(0x080353C0, st)
    s.capture('audio in', AUDIO_IN_GROUP)
    s.midi(bytes([0x90, 60, 100]))
    t = tempfile.mktemp()
    res, rans = s.run(blocks=8, per_block=False, trace=t,
                      dumps=[('x', SLOTS[0], SLOTS[1] - SLOTS[0]), ('x', 0, 0x40), ('y', 0x1960, 12),
                             ('x', 0x30000, 0x210), ('x', FLAGS, 1), ('x', 0xEC, 1)])
    tr = open(t, 'rb').read()
    return {(sp, a): v for sp, a, v in res}, rans, tr, s.events


def main(stock, sc14, img):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    S, _, trs, _ = voice_state(stock)
    O, _, _, _ = voice_state(sc14)
    N, rans, trn, ev = voice_state(img)
    keys = [('x', SLOTS[0]), ('x', 0), ('y', 0x1960), ('x', 0x30000)]
    check(O[('x', 0xEC)] == [0] and S[('x', 0xEC)] == [0x1960], "reference: SC14 overwrites X:$EC (voice slot 0 r0 $1960 -> 0)")
    check(any(O[k] != S[k] for k in keys), "reference: SC14 voice 0 state / core-1 fetch list differ from stock")
    for k in keys:
        check(N[k] == S[k], f"SC14.2: {k[0].upper()}:${k[1]:X} block identical to stock")
    arm = [(a, v) for name, ws in ev for _, sp, a, v in ws if sp == 'x' and a in (0xEC, FLAGS)]
    check(arm == [(FLAGS, 0)], f"SC14.2: Audio In group writes only X:$3A00 (={arm})")
    check(not trs[FLAGS], "stock never touches X:$3A00 in the audio blocks")
    check(trn[FLAGS] == 1, f"SC14.2: X:$3A00 only read by the SC10 code in the audio blocks (bits {trn[FLAGS]})")
    for bits in (1, 2, 3):
        B, _, _, evb = voice_state(img, bits)
        armb = [(a, v) for name, ws in evb for _, sp, a, v in ws if sp == 'x' and a in (0xEC, FLAGS)]
        check(armb == [(FLAGS, bits)] and B[('x', FLAGS)] == [bits] and B[('x', SLOTS[0])] == S[('x', SLOTS[0])],
              f"SC14.2 flags={bits}: X:$3A00={bits}, slot table intact")
    print("SC14.2 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(*(Path(p).read_bytes() for p in sys.argv[1:4])) else 0)
