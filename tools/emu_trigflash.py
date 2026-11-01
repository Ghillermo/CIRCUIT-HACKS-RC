"""SC49.8 / Beta 5.1 tests: tools/trigled.py use_flash (with Shift held each track button flashes white for 100 ms on every note of its track), through
the controller, the real LED task, the stock's note path and the MIDI-in dispatcher.

    python tools/emu_trigflash.py BUILD.bin manifest.json
  * Shift and nothing played: the eight track buttons dark;
  * pads: a MIDI 1 pad = its button white with Shift, its own colour without; still white at 99 ms, dark at 100 ms with the pad still held; a second
    pad while the first is held = white again; Synth 1, Synth 2, MIDI 2: each its own button; Drum 1 / Drum 4 pads: each its own button;
  * the sequence: MIDI 1, the same note on three steps: a flash on each; tied over them: one; Drum 1's player: a hit = its button;
  * the arpeggio: MIDI 1 with the arpeggiator on: a sequenced chord = a flash on each note it plays; a held chord, stopped: the notes keep flashing;
  * MIDI in (0x08051720, as a DIN / USB message): a note-on on the channels of Synth 1, MIDI 1 and the drums (note 60 = Drum 1): each its button; a
    note-off / a note-on with velocity 0: nothing;
  * a note-off from a pad: nothing.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc48_8 as S  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import emu_arp as EAm  # noqa: E402
import emu_sc17_6 as T6  # noqa: E402
import arp as A  # noqa: E402
import kbin as K  # noqa: E402
import trigled as TG  # noqa: E402
import drumarp as D  # noqa: E402
import dpitch as DP  # noqa: E402

MGR, PRESS, RELEASE = S.MGR, T6.PRESS, T6.RELEASE
MSG, DISPATCH = 0x2006E100, 0x08051720
WHITE = TG.WHITE


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = S.ET(img, man)
    e.marks.pop(0x0802E5BC, None); e.marks.pop(0x0802E61C, None)
    t = [500000]
    def at(ms): t[0] += ms; e.w32(A.HAL_TICK, t[0])
    at(0)
    def btns(shift=True):
        e.shift(shift); f = X.frame(e)[32:40]; e.shift(False); return f
    lit = lambda f: [i for i, v in enumerate(f) if v == WHITE]
    hold = lambda q: e.call(PRESS, MGR, q, 100, maxins=8_000_000)
    let = lambda q: e.call(RELEASE, MGR, q, maxins=8_000_000)
    e.btn(2); e.btn(9)
    b0 = btns()
    check(b0 == [0] * 8, f"Shift, nothing played: the track buttons dark ({[hex(x) for x in b0]})")
    # pads
    hold(20); b1 = btns(); bn = btns(False); at(99); b2 = btns(); at(1); b3 = btns()
    check(lit(b1) == [2] and bn[2] != WHITE, f"a MIDI 1 pad: with Shift MIDI 1 white ({lit(b1)}), without its own colour ({bn[2]:#x})")
    check(lit(b2) == [2] and lit(b3) == [], f"still white at 99 ms ({lit(b2)}), dark at 100 ms with the pad held ({lit(b3)})")
    hold(21); b4 = btns(); at(100); let(20); let(21); b5 = btns()
    check(lit(b4) == [2] and lit(b5) == [], f"a second pad with the first held: white again ({lit(b4)}); note-offs: nothing ({lit(b5)})")
    for trk, btn_ in ((0, 0), (1, 1), (3, 3)):
        e.btn(btn_); e.btn(9); hold(20); f = btns(); let(20); at(100)
        check(lit(f) == [trk], f"track {trk}'s pad: its button ({lit(f)})")
    e.btn(4); e.btn(9); hold(28); b6 = btns(); at(100); hold(24); b7 = btns(); let(28); let(24); at(100)
    check(lit(b6) == [4] and lit(b7) == [7], f"Drum 1 / Drum 4 pads: each its button ({lit(b6)}, {lit(b7)})")
    # the sequence: MIDI 1, the same note on three steps, 126 ms apart: one flash a note; tied over them: one note, one flash
    e.btn(2); e.btn(9)
    e.call(int(man["report"]["vcf20"]["labels"]["c_sdpat"], 16), 0, maxins=1_000_000); pat = e.uc.reg_read(UC_ARM_REG_R0)
    P = A.PLAYER0 + A.PLAYER_SZ * 2; st = e.r32(A.ENG + 0x30 + 4 * 2)
    def seq3(length):
        s0 = bytearray(S.chord([(60, length, 0, 100)]))
        for s_ in (1, 2): s0[28 * s_:28 * (s_ + 1)] = s0[:28]
        e.uc.mem_write(pat, bytes(s0))
        e.transport(1); seen = []
        for s_ in range(4):
            EAm.EA.setp(e, st, 1, bytes([s_]))
            for k in range(6):
                EAm.EA.setp(e, st, 2, struct.pack("<I", k)); e.call(EAm.TICK_BUILD, P, maxins=3_000_000); e.call(EAm.TICK_PLAY, P, maxins=3_000_000)
                at(21)
                if k == 0: seen.append(lit(btns()))
        e.transport(0); at(200); X.frame(e)
        return seen
    s1_ = seq3(5); s2_ = seq3(0x80 | 6)
    check(s1_ == [[2], [2], [2], []], f"the sequence, the same note on three steps: a flash on each ({s1_})")
    check(s2_ == [[2], [], [], []], f"tied over the three steps = one note, one flash ({s2_})")
    e.transport(1)
    # Drum 1's player
    dst = e.r32(A.ENG + 0x30 + 4 * 4)
    p_d = e.r8(e.ptr(dst, 0))
    base = e.r32(DP.DP0 + 0x48) + DP.PAT_SZ * p_d
    e.uc.mem_write(base, bytes([100] + [0] * 31)); e.uc.mem_write(base + 0x20, bytes([7] * 32)); e.uc.mem_write(base + 0x60, bytes([1] + [0] * 31))
    at(200); slot2 = e.r32(D.DP_VT + 8) & ~1
    e.call(slot2, DP.DP0, p_d, 0, 0, maxins=3_000_000); b8 = btns()
    check(lit(b8) == [4], f"Drum 1's sequence: its button ({lit(b8)})")
    e.transport(0); at(200)
    # the arpeggio: the sequence's chord, one note a step; live, a held chord with the transport stopped
    R = man["report"]
    al = {k: int(v, 16) for k, v in R["arp"]["labels"].items()}
    pm = e.r8(e.ptr(st, 0))
    e.uc.mem_write(pat, S.chord([(60, 18, 0, 100), (64, 18, 0, 100), (67, 18, 0, 100)]))
    e.call(al["c_arset"], 2, pm, 0x80 | A.M_UP, maxins=1_000_000)
    seen = []
    e.transport(1)
    for s_ in range(3):
        EAm.EA.setp(e, st, 1, bytes([s_]))
        for k in range(6):
            EAm.EA.setp(e, st, 2, struct.pack("<I", k)); e.call(EAm.TICK_BUILD, P, maxins=3_000_000); e.call(EAm.TICK_PLAY, P, maxins=3_000_000)
            at(21)
            if k == 0: seen.append(lit(btns()))
    e.transport(0); at(200); X.frame(e)
    check(seen == [[2], [2], [2]], f"the arpeggio of a sequenced chord: a flash on each of its notes ({seen})")
    stamp = lambda: e.r32(TG.RAM2 + 4 + 4 * 2)
    e.uc.mem_write(pat, bytes(len(S.chord([]))))
    hold(20); hold(22); s1 = stamp(); st_ = []
    for k in range(40):
        at(25); X.frame(e); st_.append(stamp())
    let(20); let(22); at(200); X.frame(e)
    n = len({x for x in st_ if x != s1})
    check(n >= 3, f"the arpeggio of a held chord, stopped: its notes keep flashing ({n} notes in a second)")
    e.call(al["c_arset"], 2, pm, 0, maxins=1_000_000)
    # MIDI in
    Actx = e.r32(K.CTX); tab = list(e.uc.mem_read(Actx + 4, 5)); fl = e.r8(Actx + 0x14)
    e.uc.mem_write(Actx + 0x14, bytes([(fl | 1) & ~K.INJ]))
    def midi(st_, ch, n, v):
        e.uc.mem_write(MSG, bytes([st_ | ch, n, v, 0])); e.call(DISPATCH, Actx, MSG, maxins=20_000_000)
    for tr, ch, n in ((0, tab[0], 60), (2, tab[2], 62), (4, tab[4], 60)):
        if tr == 2 and tab[2] == tab[0]: continue
        midi(0x90, ch, n, 100); f = btns(); at(100); midi(0x80, ch, n, 0); g = btns(); midi(0x90, ch, n, 0); h_ = btns(); at(100)
        check(lit(f) == [tr] and lit(g) == [] and lit(h_) == [], f"MIDI in, channel {ch + 1}: note-on = track {tr}'s button ({lit(f)}); note-off, velocity 0: nothing ({lit(g)}, {lit(h_)})")
    del e; gc.collect()
    print(f"TRIGFLASH RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
