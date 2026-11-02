"""SC50 / Beta 5.3 tests: tools/jumpseq.py (MIDI 1 / 2 pointing at another track: their notes make its pattern jump), through the controller, the real LED task,
the stock's tick and each player's own slot 0, in the order of a clock on the unit (the tick, then every TICK_BUILD, then every TICK_PLAY).

    python tools/emu_jumpseq.py BUILD.bin manifest.json
  * the row: pad 27 opens the engine row; pads 9-16 = the eight tracks dim in the stock's colours, the track itself dark; a press = bright, pad 27 in its colour;
    another one moves it; the same one again = off; the track's own pad and a closed row change nothing; a tail with garbage reads as off and a press cleans it;
  * the step: with four scales and roots, the Note view's pads 17-32 = steps 1-16, Octave up 17-32, the expanded view's 32 pads = steps 1-32, every pad lit; Synth 1
    keeps the project's keyboard; the drums' cents' table in 16 bits;
  * the jump: on each of the seven targets a note on MIDI 1's step 4 = the target plays the indicated step on that very clock, then goes on from there, and
    MIDI 2 the same; no note reaches the transmitter's next head, on and off; nothing pointing: the note goes through and nothing jumps;
  * a target at half the rate waits for its own next step; a muted track makes no jump; a step with 1-in-2 jumps on the second pass only;
  * a pad of the pointing track while it plays lands on the target's next step and still reaches the recorder; stopped: nothing; a new project clears the mode.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc48_8 as S  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import emu_arp as EAm  # noqa: E402
import emu_sc17_6 as T6  # noqa: E402
import arp as A  # noqa: E402
import jumpseq as J  # noqa: E402
import modesel as MS  # noqa: E402
import cscale as CS  # noqa: E402

MGR, PRESS, RELEASE = S.MGR, T6.PRESS, T6.RELEASE
ENG, SEQ_TICK, REC_ON = J.ENG, 0x0802C418, 0x0802E56A
DP0, DP_SZ = 0x20040810, 0x90
PLAYERS = [J.PLAYER0 + J.PLAYER_SZ * t for t in range(4)] + [DP0 + DP_SZ * d for d in range(4)]
MINOR = (0, 2, 3, 5, 7, 8, 10)
MAJOR = (0, 2, 4, 5, 7, 9, 11)


def mask_of(deg): return sum(0 if d in deg else 1 << (2 * d) for d in range(12))


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = S.ET(img, man)
    e.marks.pop(0x0802E5BC, None); e.marks.pop(0x0802E61C, None)
    R = man["report"]
    L = {k: int(v, 16) for k, v in R["jumpseq"]["labels"].items()}
    prev = {k: int(v, 16) for k, v in R["jumpseq"]["prev"].items()}
    t = [500000]
    def at(ms): t[0] += ms; e.w32(A.HAL_TICK, t[0])
    at(0)
    rec = e.r32(J.SESSION_OBJ + 0x14) + J.TAIL + J.O_JS
    tail = lambda: bytes(e.uc.mem_read(rec, 3))
    pad = lambda q: (e.call(PRESS, MGR, q, 100, maxins=8_000_000), e.call(RELEASE, MGR, q, maxins=8_000_000))
    pal = lambda i: struct.unpack_from("<H", img, J.PAL + 2 * i - 0x08010000)[0]
    bright, dim = [pal(1 + k) for k in range(8)], [pal(9 + k) for k in range(8)]
    V2 = "jumpx" in R
    blink = lambda k: (dim if V2 and t[0] & 0x100 else bright)[k]                       # SC50.2: pad 27 blinks
    # ---- the row
    e.uc.mem_write(rec, bytes(3))
    e.btn(2); e.btn(8); at(10)
    f0 = X.frame(e)
    pad(8); check(tail() == bytes(3), f"row closed: pad 9 is a patch, the mode stays off ({tail().hex()})")
    pad(J.PAD); at(10); f = X.frame(e)
    want = [dim[k] if k != 2 else 0 for k in range(8)]
    check(e.r8(MS.RAM) == 1 and f[8:16] == want, f"pad 27: the eight tracks dim, MIDI 1 dark ({[hex(x) for x in f[8:16]]})")
    p27 = f[J.PAD]
    pad(8); at(10); f = X.frame(e)
    check(tail() == bytes([1, 0, J.SIG]) and f[8] == bright[0] and f[J.PAD] == blink(0), f"pad 9: Synth 1 bright, pad 27 in its colour ({tail().hex()}, {f[8]:#x}, {f[J.PAD]:#x})")
    pad(12); at(10); f = X.frame(e)
    check(tail() == bytes([5, 0, J.SIG]) and f[12] == bright[4] and f[8] == dim[0] and f[J.PAD] == blink(4), f"pad 13: Drum 1 instead ({tail().hex()})")
    pad(10); check(tail() == bytes([5, 0, J.SIG]), "the track's own pad: nothing")
    if V2:
        at(256); f1 = X.frame(e); at(256); f2 = X.frame(e)
        check({f1[J.PAD], f2[J.PAD]} == {bright[4], dim[4]}, f"pad 27 blinks, bright / dim of the target's colour, 256 ms each ({f1[J.PAD]:#x}, {f2[J.PAD]:#x})")
        von = lambda: (e.call(int(R["vcf20"]["labels"]["c_von"], 16), 0, maxins=1_000_000), e.uc.reg_read(UC_ARM_REG_R0))[1]
        check(von() == 0, "an engine off while pointing")
        pad(17); at(10); f = X.frame(e)
        check(von() != 0 and tail()[0] == 0 and f[12] == dim[4], f"an engine on stops the pointing ({von()}, {tail().hex()})")
        pad(12); at(10); f = X.frame(e)
        check(von() == 0 and tail()[0] == 5 and f[12] == bright[4], f"pointing turns the engine off ({von()}, {tail().hex()})")
    pad(12); at(10); f = X.frame(e)
    check(tail()[0] == 0 and f[12] == dim[4] and f[J.PAD] == p27, f"the same pad again: off, pad 27 back ({tail().hex()}, {f[J.PAD]:#x})")
    e.uc.mem_write(rec, bytes([0x5B, 0x5B, 0x5B])); at(10); f = X.frame(e)
    check(f[8:16] == want, "a tail with garbage reads as off")
    pad(9); check(tail() == bytes([2, 0, J.SIG]), f"and a press cleans it ({tail().hex()})")
    e.btn(3); e.btn(8); at(400); X.frame(e); at(10); X.frame(e)
    pad(J.PAD); at(10); f = X.frame(e)
    check(f[11] == 0 and f[10] == dim[2] and e.r8(MS.RAM) == 2, f"MIDI 2: its pad dark, MIDI 1's dim ({[hex(x) for x in f[8:16]]})")
    pad(8); check(tail() == bytes([2, 1, J.SIG]), f"MIDI 2 points on its own ({tail().hex()})")
    pad(J.PAD); e.uc.mem_write(rec, bytes(3))
    # ---- the step: the pads, whatever the scale
    kb_scale = e.r32(J.MU.KB_CTX + 0xC); kb_root = e.r32(J.MU.KB_CTX + 0x10)
    scale = lambda root, deg: (e.uc.mem_write(kb_root, bytes([root])), e.w32(kb_scale + 4, mask_of(deg)))
    table0 = None
    def pads(m):
        """every keyboard pad of the screen -> the step it sends (the transport running)"""
        e.transport(1); got = {}
        for q in range(32):
            e.uc.mem_write(J.RAM + 4, bytes(8)); e.call(PRESS, MGR, q, 100, maxins=8_000_000); e.call(RELEASE, MGR, q, maxins=8_000_000)
            v = bytes(e.uc.mem_read(J.RAM + 4, 8))[m]
            if v: got[q] = v - 1
        e.transport(0); e.uc.mem_write(J.RAM + 4, bytes(8))
        return got
    def goto(cur):
        e.btn(2)
        for _ in range(4):
            if e.r8(MGR + 0x152) == cur: break
            e.btn(9)
        check(e.r8(MGR + 0x152) == cur, f"(view {e.r8(MGR + 0x152)})") if e.r8(MGR + 0x152) != cur else None
        at(10); X.frame(e); X.frame(e)
    NOTE, EXP = 19, 24
    e.uc.mem_write(rec, bytes([1, 0, J.SIG])); goto(NOTE)
    for name, root, deg in (("C minor", 0, MINOR), ("D major", 2, MAJOR), ("G pentatonic", 7, (0, 3, 5, 7, 10)), ("B chromatic", 11, tuple(range(12)))):
        scale(root, deg); goto(NOTE)
        p1 = pads(0)
        e.btn(20); at(10); X.frame(e); X.frame(e); p2 = pads(0); e.btn(19); at(10); X.frame(e); X.frame(e)
        check(p1 == {16 + k: k for k in range(16)}, f"{name}, Note view: pads 17-32 = steps 1-16 ({sorted(p1.items())[:3]}…)")
        check(p2 == {16 + k: 16 + k for k in range(16)}, f"{name}, Octave up: steps 17-32 ({sorted(p2.items())[:3]}…)")
        goto(EXP); p3 = pads(0); goto(NOTE)
        check(p3 == {k: k for k in range(32)}, f"{name}, expanded view: pads 1-32 = steps 1-32 ({sorted(p3.items())[:3]}…, {len(p3)})")
    scale(0, (0, 3, 5, 7, 10)); goto(EXP); f = X.frame(e)
    check(all(f[:32]), f"pentatonic, expanded: all 32 pads lit ({[hex(x) for x in f[:4]]}…)")
    scale(0, MINOR); goto(NOTE); f = X.frame(e)
    check(all(f[16:32]), f"Note view: pads 17-32 lit ({[hex(x) for x in f[16:20]]}…)")
    e.btn(0); e.btn(9); at(10); X.frame(e); X.frame(e)
    t_s = bytes(e.uc.mem_read(J.MU.KB_CTX + 0x14, 224))
    e.uc.mem_write(rec, bytes(3)); at(10); X.frame(e); X.frame(e); t_0 = bytes(e.uc.mem_read(J.MU.KB_CTX + 0x14, 224))
    check(t_s == t_0, "Synth 1 keeps the project's keyboard while MIDI 1 points")
    # ---- the cents' table in 16 bits
    tab = int(R["sc12"]["table"], 16)
    bad = [c_ for c_ in range(-100, 101) if abs(2 * e.uc.mem_read(tab + 2 * (c_ + 100), 2)[0] + 512 * e.uc.mem_read(tab + 2 * (c_ + 100) + 1, 1)[0] - round(65536 * 2 ** (c_ / 1200))) > 1]
    check(not bad, f"the drums' cents: the table in 16 bits within 1 of the original ({bad[:4]})")
    e.uc.mem_write(rec, bytes(3)); scale(0, MINOR)
    note_of = lambda s_: 59 + (s_ & 16) + 2 * (s_ & 7) + (s_ >> 3 & 1)                # what the pattern holds for a step, with the root at C
    # ---- the clock
    seen = []
    tx = [[], []]
    def thru(i):
        def f(uc, a, s_, d):
            if uc.reg_read(UC_ARM_REG_R1) in (2, 3): tx[i].append(uc.reg_read(UC_ARM_REG_R1))
        return f
    e.uc.hook_add(UC_HOOK_CODE, thru(0), begin=prev["on"], end=prev["on"]); e.uc.hook_add(UC_HOOK_CODE, thru(1), begin=prev["off"], end=prev["off"])
    def clock():
        at(21); e.call(SEQ_TICK, ENG, maxins=5_000_000)
        for k in range(8):                                                              # what each TICK_BUILD of this clock will read
            st = e.r32(ENG + 0x30 + 4 * k)
            if e.r32(e.ptr(st, 2)) == 0: seen.append((k, e.r8(e.ptr(st, 1))))
        for o in (0x14, 0x18):
            for p in PLAYERS: e.call(e.r32(e.r32(p)) & ~1, p, e.r32(p + o), maxins=3_000_000)
    def rewind():
        e.transport(0)
        for k in range(8):
            st = e.r32(ENG + 0x30 + 4 * k)
            EAm.EA.setp(e, st, 1, bytes([0])); EAm.EA.setp(e, st, 2, struct.pack("<I", 5))    # the last tick of "the step before": the first clock starts step 0
            EAm.EA.setp(e, e.r32(ENG + 0x70 + 4 * k), 1, bytes([0]))
        e.uc.mem_write(J.RAM + 4, bytes(8))
        seen.clear(); tx[0].clear(); tx[1].clear()
        e.transport(1)
    def run(n):
        for _ in range(n): clock()
    def steps(k): return [s for tr, s in seen if tr == k]
    pats = {}
    for m in (0, 1):
        e.call(int(R["vcf20"]["labels"]["c_sdpat"], 16), m, maxins=1_000_000); pats[m] = e.uc.reg_read(UC_ARM_REG_R0)
    empty = bytes(S.chord([], 32))
    def seq(m, stepno, note, b3=0, length=3):
        for q in (0, 1): e.uc.mem_write(pats[q], empty)
        s0 = bytearray(S.chord([(note, length, 0, 100)], 1)); s0[3] = b3
        e.uc.mem_write(pats[m] + 28 * stepno, bytes(s0))
    def point(m, target): e.uc.mem_write(rec, bytes([target + 1 if m == 0 and target is not None else 0, target + 1 if m == 1 and target is not None else 0, J.SIG]))
    for k in range(8):                                                                  # every track: 16 steps, 6 ticks a step, forward
        st = e.r32(ENG + 0x50 + 4 * k)
        EAm.EA.setp(e, st, 0, bytes([15, 0])); EAm.EA.setp(e, st, 1, bytes([3])); EAm.EA.setp(e, st, 2, bytes([0]))
    # nothing pointing
    seq(0, 4, note_of(9)); point(0, None); rewind(); run(6 * 7)
    check(steps(0)[:7] == list(range(1, 8)) and tx[0] != [], f"nothing pointing: the target runs ({steps(0)[:7]}), the note goes on ({len(tx[0])} note-on)")
    res = {}
    for m in (0, 1):
        for tg in range(8):
            if tg == m + 2: continue
            seq(m, 4, note_of(9)); point(m, tg); rewind(); run(6 * 8)
            res[(m, tg)] = (steps(tg)[:8], list(tx[0]), list(tx[1]))
    want = [1, 2, 3, 9, 10, 11, 12, 13]                                              # (the first clock starts step 1)
    bad = {k: v[0] for k, v in res.items() if v[0] != want}
    check(not bad and len(res) == 14, f"a note on step 5 of MIDI 1 / 2 = each of the seven targets on step 10 on that clock, and on from there {bad or want}")
    check(all(not v[1] and not v[2] for v in res.values()), "and no note goes on, on or off")
    # the note's track itself runs on
    seq(0, 4, note_of(9)); point(0, 4); rewind(); run(6 * 8)
    check(steps(2)[:8] == list(range(1, 9)) and steps(4)[:8] == want, f"the pointing track runs on ({steps(2)[:8]})")
    # half the rate
    st = e.r32(ENG + 0x50); seq(0, 5, note_of(9)); point(0, 0); EAm.EA.setp(e, st, 1, bytes([5])); rewind(); run(6 * 10)
    EAm.EA.setp(e, st, 1, bytes([3]))
    check(steps(0)[:5] == [1, 2, 9, 10, 11], f"a target at half the rate waits for its next step ({steps(0)[:6]})")
    # muted
    mu = e.r32(PLAYERS[2] + 0x28); seq(0, 4, note_of(9)); point(0, 0); EAm.EA.setp(e, mu, 0, bytes([1])); rewind(); run(6 * 8)
    EAm.EA.setp(e, mu, 0, bytes([0]))
    check(steps(0)[:8] == list(range(1, 9)), f"MIDI 1 muted in the Mixer: no jump ({steps(0)[:8]})")
    # both at once; a step past the pattern's end
    e.uc.mem_write(pats[0], empty); e.uc.mem_write(pats[1], empty)
    for m_, n_ in ((0, 9), (1, 5)): e.uc.mem_write(pats[m_] + 28 * 4, S.chord([(note_of(n_), 3, 0, 100)], 1))
    e.uc.mem_write(rec, bytes([1, 2, J.SIG])); rewind(); run(6 * 6)
    check(steps(0)[:6] == [1, 2, 3, 9, 10, 11] and steps(1)[:6] == [1, 2, 3, 5, 6, 7], f"both at once: each its target ({steps(0)[:6]}, {steps(1)[:6]})")
    seq(0, 4, note_of(9)); point(0, 0); scale(2, MAJOR); rewind(); run(6 * 6); s_r = steps(0)[:5]; scale(0, MINOR)
    check(s_r == [1, 2, 3, 9, 10], f"a step recorded with one scale and root plays the same with another ({s_r})")
    seq(0, 4, note_of(20)); point(0, 0); rewind(); run(6 * 6)
    check(steps(0)[:6] == [1, 2, 3, 20, 0, 1], f"a step past the last one plays, then the pattern ends ({steps(0)[:6]})")
    # a pad, playing and stopped: bottom row = steps 1-8 with a MIDI track's default octave (64)
    seq(0, 31, 40); point(0, 0); goto(NOTE); rewind(); run(6 * 2 + 2)
    rec_on = []
    def recorder(uc, a, s_, d): rec_on.append(uc.reg_read(UC_ARM_REG_R3))
    e.uc.hook_add(UC_HOOK_CODE, recorder, begin=REC_ON, end=REC_ON)
    e.call(PRESS, MGR, 26, 100, maxins=8_000_000); e.call(RELEASE, MGR, 26, maxins=8_000_000)
    pending = bytes(e.uc.mem_read(J.RAM + 4, 1))[0]
    check(rec_on == [2], f"the pad still reaches the recorder's gate for its own track ({rec_on})")
    run(6)
    check(pending == 11 and steps(0)[3] == 10, f"pad 27 while it plays: step 11 on the target's next step (pending {pending}, {steps(0)[:5]})")
    e.transport(0); e.uc.mem_write(J.RAM + 4, bytes(8))
    e.call(PRESS, MGR, 26, 100, maxins=8_000_000); e.call(RELEASE, MGR, 26, maxins=8_000_000)
    check(bytes(e.uc.mem_read(J.RAM + 4, 8)) == bytes(8), "stopped: a pad makes no jump")
    if "c_jsa" in R.get("jumpx", {}).get("labels", {}):                                  # SC50.2: stopped, a pad sounds the target's step
        heard = []
        ifc = e.r32(PLAYERS[0] + 0x4C); on_ = e.r32(e.r32(ifc)) & ~1; off_ = e.r32(e.r32(ifc) + 4) & ~1
        def h_on(uc, a, s_, d):
            if uc.reg_read(UC_ARM_REG_R0) == ifc: heard.append(("on", uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2)))
        def h_of(uc, a, s_, d):
            if uc.reg_read(UC_ARM_REG_R0) == ifc: heard.append(("off", uc.reg_read(UC_ARM_REG_R1), 0))
        e.uc.hook_add(UC_HOOK_CODE, h_on, begin=on_, end=on_); e.uc.hook_add(UC_HOOK_CODE, h_of, begin=off_, end=off_)
        e.call(int(R["vcf20"]["labels"]["c_sdpat"], 16), 2, maxins=1_000_000); bs = e.uc.reg_read(UC_ARM_REG_R0)
        e.uc.mem_write(bs, empty); e.uc.mem_write(bs + 28 * 10, S.chord([(70, 3, 0, 90)], 1))
        heard.clear(); e.transport(0); e.call(PRESS, MGR, 26, 100, maxins=8_000_000); on_h = list(heard); e.call(RELEASE, MGR, 26, maxins=8_000_000)
        check(on_h == [("on", 70, 90)] and heard[1:] == [("off", 70, 0)], f"stopped: the pad sounds the target's step until it is let go ({heard})")
        DP = 0x20040810
        dh = []
        ifd = e.r32(DP + 0x4C); don = e.r32(e.r32(ifd)) & ~1; dof = e.r32(e.r32(ifd) + 4) & ~1
        def d_on(uc, a, s_, d):
            if uc.reg_read(UC_ARM_REG_R0) == ifd: dh.append(("on", uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2)))
        def d_of(uc, a, s_, d):
            if uc.reg_read(UC_ARM_REG_R0) == ifd: dh.append(("off", uc.reg_read(UC_ARM_REG_R1), 0))
        e.uc.hook_add(UC_HOOK_CODE, d_on, begin=don, end=don); e.uc.hook_add(UC_HOOK_CODE, d_of, begin=dof, end=dof)
        point(0, 4)
        e.call(int(R["drumarp"]["labels"]["c_dapat"], 16), 0, maxins=1_000_000); pn = e.uc.reg_read(UC_ARM_REG_R0)
        vbase = e.r32(DP + 0x48) + pn * 0x6A8
        e.uc.mem_write(vbase + 10, bytes([77])); dnote = e.r8(DP + 0x58)
        e.call(PRESS, MGR, 26, 100, maxins=8_000_000); d1 = list(dh); e.call(RELEASE, MGR, 26, maxins=8_000_000)
        check(d1 == [("on", dnote, 77)] and dh[1:] == [("off", dnote, 0)], f"stopped: a drum target sounds its hit with its step's velocity ({dh})")
        e.uc.mem_write(vbase + 10, bytes(1)); dh.clear()
        e.call(PRESS, MGR, 26, 100, maxins=8_000_000); e.call(RELEASE, MGR, 26, maxins=8_000_000)
        check(dh == [], f"and an empty step is silent ({dh})")
    # the octave of a pointing track: 64 / 65 only
    if "jumpoct" in R:
        VIEW = 0x200412E0 + 0x2F4 * 2
        ost = e.r32(VIEW + 0x34)
        oc = lambda: e.r8(e.ptr(ost, 8))
        fr2 = lambda: (at(10), X.frame(e), X.frame(e))[2]
        e.transport(0); e.uc.mem_write(rec, bytes(3)); goto(NOTE)
        for o0 in (61, 67):
            e.uc.mem_write(rec, bytes(3)); fr2(); EAm.EA.setp(e, ost, 8, bytes([o0])); fr2()
            k0 = oc(); e.uc.mem_write(rec, bytes([1, 0, J.SIG])); fr2()
            check(k0 == o0 and oc() == 64, f"starting to point with the octave at {o0}: 64 ({k0} -> {oc()})")
        f = fr2(); check(f[51] & 0xFF == 0 and f[52] & 0xFF != 0, f"steps 1-16: Octave ▼ dark, ▲ lit ({f[51]:#x}, {f[52]:#x})")
        e.btn(19); f = fr2(); check(oc() == 64, f"Octave ▼ there: nothing below ({oc()})")
        e.btn(20); f = fr2(); check(oc() == 65 and f[52] & 0xFF == 0 and f[51] & 0xFF != 0, f"Octave ▲: steps 17-32, ▲ dark, ▼ lit ({oc()}, {f[51]:#x}, {f[52]:#x})")
        e.btn(20); e.btn(20); f = fr2(); check(oc() == 65, f"Octave ▲ again: nothing above ({oc()})")
        goto(EXP); f = fr2(); check(f[51] & 0xFF == 0 and f[52] & 0xFF == 0, f"expanded view: both dark ({f[51]:#x}, {f[52]:#x})")
        goto(NOTE); e.uc.mem_write(rec, bytes(3)); fr2(); e.btn(20); fr2(); check(oc() == 66, f"not pointing: the octave free ({oc()})")
        EAm.EA.setp(e, ost, 8, bytes([64])); fr2()
        import semitab as ST
        bad = [v for v in range(128) if (e.call(0x0802878C, v, maxins=1_000), e.uc.reg_read(UC_ARM_REG_R0))[1] != ST.word(v)]
        check(not bad, f"the drums' semitones from one octave: the 128 words ({bad[:4]})")
        goto(NOTE); point(0, 0); fr2()
    # 1 in 2
    e.transport(1); seq(0, 4, note_of(9), b3=1); point(0, 4); rewind(); run(6 * 34)
    s4 = steps(4)
    check(s4[:6] == [1, 2, 3, 4, 5, 6], f"1 in 2: the first pass plays on ({s4[:6]})")
    check(s4[16:21] == [1, 2, 3, 9, 10], f"and the second pass jumps ({s4[16:21]})")
    # a new project
    e.uc.mem_write(rec, bytes([3, 0, J.SIG])); e.call(L["c_jsnew"], 0, 0x10000, 1, maxins=3_000_000)
    check(tail()[2] != J.SIG, f"a new project clears the mode ({tail().hex()})")
    print("ALL PASS" if not fails else f"{fails} FAILED")
    return fails


if __name__ == "__main__":
    gc.collect()
    sys.exit(1 if main(open(sys.argv[1], "rb").read(), json.load(open(sys.argv[2], encoding="utf-8"))) else 0)
