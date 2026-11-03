"""SC50 / Beta 5.3 ARM tests: the redesign of the random-mutate (mutate39.use_mut2, stepmod, drumpat, mutfac) and the automation sweep (autorel.use_sweep),
through the controller, the real views, the stock's mask builder and player, the drum players and the LED task.

    python tools/emu_mutate2.py SC50.bin SC50_manifest.json
  * the view, Synth 1 (Pattern Settings pad 25, a step held): pads 17-24 = the level in the step's byte [2], pad 25 the dynamics on / off, 26-28 its three
    modes (bits 4-5 of byte [3]), 29-31 nothing, 32 the micro steps (bit 6); byte [1] and the frequency kept; the LEDs of each; a step without notes:
    nothing written, all dark; Pattern Settings twice: mode 1 as before;
  * the factor: Octave there = ± 1, 0..8, in the record's tail + 536 + track, Octave's LEDs dark at the ends, the number on the pads for 1.5 s; Shift or
    another view: Octave does not touch it; garbage in the byte = x 1;
  * the player (generator under control, against a model): each level at each factor; a tied unit / a note that already sounds keep the note; the
    dynamics (velocity and length) of the three modes, the stronger only shorter, the weaker only longer; a tied unit keeps its length; the micro
    steps (the mask builder): - 2..+ 2 by unit, one draw a step, inside the step; Record with the view on the screen: written, one start only;
    without it the step stays; the stock generator: the rates at x 1, x 4 and x 0;
  * the drums: the same pads in the byte + 0x88 + step (bits 0-1 dynamics, 2 + 6-7 level, 3-5 frequency), pad 27 dark, pad 32 by drum even without a
    hit; played: velocities, the hit 1 or 2 micro steps later and never earlier, the sample ± 1 inside its row, ± 8, a project not marked;
  * SC50.1 / Beta 5.4 (label c_mgup): pads 21 / 22 = octave up, one and two units; pads 23 / 24 = both ways, one and two units; drums + 8; the stock generator: as many up as
    down at x 8 on pads 23 and 24;
  * the sweep: a yellow step held + another = the lanes with a value at both on a straight line, all 6 micro steps, either order, Synth 1 and MIDI 1; the
    ends and the steps outside untouched, a lane with a value at one end only left alone, the notes untouched, no mark; a step without automation as
    the other end: nothing; two taps (not held): two previews, nothing written.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R2, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import emu_sc39 as T39  # noqa: E402
import emu_sc40_3 as T3  # noqa: E402
import emu_sc08 as T8  # noqa: E402
import mutate39 as MU  # noqa: E402
import stepmod as SM  # noqa: E402
import drumpat as Q  # noqa: E402
import drumarp as D  # noqa: E402
import drumstore as DS  # noqa: E402
import autorel as AR  # noqa: E402

MGR = T.MGR
PRESS, RELEASE = T.PRESS, T.RELEASE
STEP0, STEP1 = T39.STEP0, T39.STEP1
ID_DOWN, ID_UP = 19, 20
LED_DOWN, LED_UP = 51, 52


def fac_addr(e, t): return e.r32(MU.SESSION_OBJ + 0x14) + MU.TAIL + MU.O_FAC + t


ROLL = [False]                                               # drumpat.use_roll: a drum's pad 27 lit
ROLL2 = [False]                                              # drumpat.use_roll2: a drum's pads 25-27 = the dynamics 1-3, pad 28 dark
DYN4 = [False]                                               # SC50.9 (drumpat.use_dyn4): pad 25 off; ghost / accent staccato / length; drums lo + roller / hi; factor 0, 1, 2, 4, 8


def row(level, dyn, micro, note=True, drum=False):
    """the 16 LEDs of mode 2"""
    out = []
    for i, (dim, lit) in enumerate(MU.MG_COLS):
        on = i == level if i < 8 else (dyn != 0 if i == 8 else (micro if i == 15 else i - 8 == dyn))
        v = lit if on else dim
        if not note and not (drum and i == 15): v = 0
        if drum and i == 10 and not ROLL[0] and not ROLL2[0]: v = 0
        if drum and ROLL2[0] and 8 <= i <= 11 and DYN4[0]:
            v = v if note and i < 11 else 0
        elif drum and ROLL2[0] and 8 <= i <= 11:
            v = (lit if i - 7 == dyn else dim) if note and i < 11 else 0
        out.append(v)
    return out


def view_part(img, man, check):
    e = T.EL(img); e.at(300000); e.transport(0)
    hold = lambda q: e.call(PRESS, MGR, q, 100, maxins=8_000_000)
    let = lambda q: e.call(RELEASE, MGR, q, maxins=8_000_000)
    b = lambda: bytes(e.uc.mem_read(STEP0, 4))
    pads = lambda: [v & 0xFF for v in X.frame(e)[16:32]]
    e.btn(0); e.btn(12); e.btn(12); X.frame(e); X.frame(e)
    hold(0); e.pad(24 + 5); let(0); e.btn(12)                                          # (mode 1: the frequency = 6)
    for _ in range(4): X.frame(e)
    e.pad(24); X.frame(e); X.frame(e)
    sub = e.r8(MGR + 0x152)
    hold(0); X.frame(e)
    b0 = b(); L0 = pads()
    check(sub == 5, f"Pattern Settings pad 25: the probability view ({sub})")
    res, bad = [], []
    for k in list(range(1, 8)) + [0]:
        e.pad(16 + k); s = b(); L = pads(); res.append((k, s[2]))
        if s[2] != k or s[1] != b0[1] or s[3] != b0[3] or L[:8] != row(k, 0, False)[:8]: bad.append((k, s.hex(), [hex(x) for x in L[:8]]))
    check(not bad, f"pads 17-24: the level 0..7 in byte [2], the chosen one bright, bytes [1] / [3] kept {bad[:3]}")
    seq = []
    for q, want in ((8, 0), (9, 1), (8, 0), (10, 2), (11, 3), (8, 0), (11, 3)) if DYN4[0] else ((8, 1), (8, 0), (9, 1), (10, 2), (11, 3), (8, 0), (11, 3)):
        e.pad(16 + q); seq.append(((b()[3] >> 4) & 3, want))
    check(all(a_ == w for a_, w in seq), f"pad 25 {'off' if DYN4[0] else 'on / off'}, pads 26-28 the three modes, pad 25 turns any mode off ({seq})")
    L = pads()
    check(L == row(0, 3, False), f"their LEDs: pad 25 and the mode bright ({[hex(x) for x in L]})")
    s0 = b()
    for q in (12, 13, 14): e.pad(16 + q)
    check(b() == s0 and pads()[12:15] == [0, 0, 0], "pads 29-31: nothing, dark")
    e.pad(16 + 15); s1 = b(); L1 = pads(); e.pad(16 + 15); s2 = b()
    check(s1[3] == s0[3] | 0x40 and s2[3] == s0[3] and L1 == row(0, 3, True), f"pad 32: the micro steps on and off, bit 6 ({s1[3]:#x}, {s2[3]:#x}), its LED bright")
    check(s0[3] & 7 == 5 and s0[1] == b0[1], "the frequency and the probability kept")
    let(0)
    hold(1); before = bytes(e.uc.mem_read(STEP1, 4)); X.frame(e); Le = pads()
    for q in (2, 5, 8, 9, 15): e.pad(16 + q)
    check(bytes(e.uc.mem_read(STEP1, 4)) == before and before[0] == 0 and Le == [0] * 16, f"a step without notes: nothing written, all dark ({[hex(x) for x in Le]})")
    let(1)
    # the factor
    a = fac_addr(e, 0)
    e.uc.mem_write(a, bytes([0xAC])); e.btn(ID_UP); g_ = e.r8(a)
    check(g_ == MU.FAC_TAG | 2, f"0xAC (in two factory sessions) = x 1 too ({g_:#x})")
    e.at(e.t + 2000)
    e.uc.mem_write(a, bytes([0x5A])); fr = X.frame(e)
    d0, u0 = fr[LED_DOWN] & 0xFF, fr[LED_UP] & 0xFF
    check(d0 == MU.COL_LIT and u0 == MU.COL_LIT, f"garbage in the byte = x 1: Octave ▼ / ▲ in peach ({d0:#x}, {u0:#x})")
    t0 = e.t; n0 = X.frame(e)[:32]
    e.btn(ID_UP); e.btn(ID_UP); g3 = e.r8(a); n1 = X.frame(e)[:32]
    sh = 600 if "jumpoct" in man["report"] else 1500
    e.at(t0 + sh - 100); n2 = X.frame(e)[:32]; e.at(t0 + sh + 100); n3 = X.frame(e)[:32]
    check(g3 == MU.FAC_TAG | (4 if DYN4[0] else 3), f"Octave ▲ twice: x {4 if DYN4[0] else 3} ({g3:#x})")
    check(n1 != n0 and n2 == n1 and n3 == n0, f"the number on the pads for {sh} ms after a change, then the view again")
    for _ in range(9): e.btn(ID_UP)
    fr = X.frame(e); gm = e.r8(a)
    check(gm == MU.FAC_TAG | MU.FAC_MAX and fr[LED_UP] & 0xFF == 0 and fr[LED_DOWN] & 0xFF == MU.COL_LIT, f"the top: x 8, Octave ▲ dark ({gm:#x})")
    for _ in range(9): e.btn(ID_DOWN)
    fr = X.frame(e); g0 = e.r8(a)
    check(g0 == MU.FAC_TAG and fr[LED_DOWN] & 0xFF == 0 and fr[LED_UP] & 0xFF == MU.COL_LIT, f"the bottom: x 0, Octave ▼ dark ({g0:#x})")
    e.btn(ID_UP)
    e.set_p0(e.r32(MGR + 0xC), 1); e.btn(ID_UP); e.set_p0(e.r32(MGR + 0xC), 0); gs = e.r8(a)
    check(gs == MU.FAC_TAG | 1, f"Shift + Octave: not the factor ({gs:#x})")
    # mode 1
    e.btn(0); X.frame(e); X.frame(e); X.frame(e); X.frame(e); e.btn(12); e.btn(12); X.frame(e); X.frame(e)
    hold(0); Lm = pads(); e.btn(ID_UP); g1 = e.r8(a); let(0)
    check(Lm[8:] == [SM.COL_FREQ] * 6 + [SM.COL_DIM] * 2 and e.r8(MGR + 0x152) == 5, f"Pattern Settings twice: mode 1, row 4 the frequency ({[hex(x) for x in Lm[8:]]})")
    check(g1 == MU.FAC_TAG | 1, f"mode 1: Octave does not touch the factor ({g1:#x})")
    e.btn(0); e.btn(ID_UP); check(e.r8(a) == MU.FAC_TAG | 1, "the Note view: Octave as the stock")
    del e; gc.collect()


def roll(units, g, rnd):
    r = rnd & 0xFFFFFFFF
    return ((r >> 6) & 15) < units * g, r >> 10


MUT3 = [False]


def mut_model(n, level, g, rnd, mask, root):
    units = 1 << (level - 1) if level <= 3 else (1 + (level & 1) if MUT3[0] else (2 if level == 7 else 1))
    ok, bits = roll(units, g, rnd)
    if not ok: return n
    if level <= 3: return T39.scale_model(n, bits, mask, root)
    if (level == 4 and not MUT3[0]) or (level >= 6 and bits & 1):
        return n - 12 + (24 if n < 12 else 0)
    return n + 12 - (24 if n + 12 > 127 else 0)


def dyn_model(mode, g, rnd, vel, gate):
    ok, bits = roll(MU.DYN_UNITS, g, rnd)
    if not ok: return vel, gate
    lo, hi = bits & 0x3FF, bits >> 10
    if DYN4[0]:
        dv = (lo % 33 - 32, lo % 33, 0)[mode - 1]
    else:
        span, bias = (33, 16) if mode == 3 else (97, 32)
        dv = lo % span - bias
    v2 = min(max(vel + dv, 1), 127)
    if mode == 1 or gate & 0x80: return v2, gate
    s = hi % 65 - 32 if mode == 3 else (-dv if DYN4[0] else (-dv >> 1 if dv > 0 else -dv))
    L = gate + ((gate * s) >> 5 if s >= 0 else (gate * s + 63) >> 6)
    return v2, min(max(L, 1), SM.MAX_LEN)


def micro_model(m, g, wd, unit=0):
    if ((wd >> 27) & 7) >= 2 * g: return m
    return min(max(m + ((wd >> (3 + 4 * unit)) & 15) % 5 - 2, 0), SM.MAX_MICRO)


RNDS = [0, 0xFFFFFFFF, 0x12345678, 0x0BADF00D, 0x00010000, 0x3FFFFFC0, 0x2AAAAAAA, 0x15555555, 0x00F0F0F0, 0x05001F00, 0x02000400, 0x03002100, 0x01000100,
        0x40, 0x80, 0xC0, 0x100, 0x1C0, 0x7C0, 0xABCDEF, 0x7654321]


def player_part(img, man, check):
    L = {k: int(v, 16) for k, v in man["report"]["stepmod"]["labels"].items()}
    MUT3[0] = "c_mgup" in man["report"]["mutate39"]["labels"]
    e = T3.EM(img, man, L)
    rate0 = e.setup(); e.set_scale(T8.MASKS[0], 0)
    step = e.step; n0 = step[4]
    a = fac_addr(e, 0)
    def fac(g): e.uc.mem_write(a, bytes([MU.FAC_TAG | g]))
    def put(level=0, b3=0, gate=None, vel=None, note=None, micro=None):
        s = bytearray(step); s[2] = level; s[3] = b3
        if gate is not None: s[5] = gate
        if vel is not None: s[7] = vel
        if note is not None: s[4] = note
        if micro is not None: s[6] = micro
        e.uc.mem_write(STEP0, bytes(s)); return bytes(s)
    def ref(note, vel, gate):
        put(0, 0, gate, vel, note); return e.note(0)
    bad, n, ch = [], 0, 0
    for g in (0, 1, 2, 4, 8):
        fac(g)
        for level in range(1, 8):
            for nt in (n0, 5, 120):
                for r in RNDS:
                    want_n = mut_model(nt, level, g, r, T8.MASKS[0], 0)
                    if e.snap[MU.O_SOUND + want_n] != 0xFF: want_n = nt
                    s = put(level, note=nt); got = e.note(r); n += 1; ch += want_n != nt
                    w = ref(want_n, step[7], step[5])
                    if got != w or bytes(e.uc.mem_read(STEP0, 1)) != s[:1]: bad.append((g, level, nt, hex(r), got, w))
    check(not bad and ch > 300, f"the note: {n} plays, levels 1-7 at x 0..8 = the model ({ch} changed) {bad[:3]}")
    fac(8); put(0); e.note(0); c0 = e.rcalls
    check(c0 == 0, "level 0, no dynamics: no generator call")
    s = put(5, gate=step[5] | 0x80); t_ = e.note(0x40)
    fac(1); put(5, note=n0); sound = n0 + 12
    e.uc.mem_write(PLAYER_SOUND(sound), bytes([0])); keep = e.snap
    e.snap = bytes(e.uc.mem_read(T3.PLAYER, 0x200)); so = e.note(0); e.snap = keep
    check(t_ and t_[0][0] == n0 and so and so[0][0] == n0, f"a tied unit, a new note that already sounds: the step's note ({t_}, {so})")
    # the dynamics
    bad, n, ch, up_short, dn_long = [], 0, 0, 0, 0
    for g in (1, 2, 8):
        fac(g)
        for mode in (1, 2, 3):
            for vel, gate in ((100, 6), (1, 1), (127, 0x60), (20, 2), (110, 0x5F), (64, 0x86), (90, 24)):
                for r in RNDS:
                    v2, g2 = dyn_model(mode, g, r, vel, gate)
                    s = put(0, mode << 4, gate, vel); got = e.note(r); n += 1; ch += (v2, g2) != (vel, gate)
                    same = bytes(e.uc.mem_read(STEP0, 28)) == s
                    w = ref(step[4], v2, g2)
                    if got != w or not same: bad.append((g, mode, vel, hex(gate), hex(r), got, w))
                    if mode == 2 and not gate & 0x80:
                        if v2 > vel and g2 > gate: up_short += 1
                        if v2 < vel and g2 < gate: dn_long += 1
    check(not bad and ch > 200, f"velocity and length: {n} plays, the three modes = the model ({ch} changed), the step untouched {bad[:3]}")
    check((3 + ((3 * -32 + 63) >> 6)) == 2 and (6 + ((6 * -1 + 63) >> 6)) == 6, "(the model: a half of 3 = 2; the smallest shortening does not cost a micro step)")
    check(up_short == 0 and dn_long == 0, f"mode 2: a stronger note never longer, a weaker never shorter ({up_short}, {dn_long})")
    # the micro steps
    words = [0, 0x3FFFFFFF, 0x12345678 & 0x3FFFFFFF, 0x0BADF00D, 0x2AAAAAAA, 0x15555555, 0x00F0F0F0, 0x1F3, 0x7C5, 0x93C467, 0x30303030, 7, 0x38, 0x48, 0x08000000, 0x10000078, 0x18000048]
    e.setup(rate=rate0)
    bad, n, moved = [], 0, 0
    for g in (0, 1, 2, 4, 8):
        fac(g)
        for mm in (0, 1, 3, 5):
            for wd in words:
                put(0, 0x40, micro=mm); s = bytearray(step); s[1] = 7; s[3] = 0x40; s[6] = mm; e.uc.mem_write(STEP0, bytes(s))
                got = [e.build(mi, wd) for mi in range(6)]; want = micro_model(mm, g, wd); n += 1; moved += want != mm
                if got != [1 if mi == want else 0 for mi in range(6)] or e.uc.mem_read(STEP0 + 6, 1)[0] != mm: bad.append((g, mm, hex(wd), got, want))
    check(not bad and moved > 20, f"the micro steps: {n} steps at x 0..8: one start, the model's ({moved} moved), inside the step, the step untouched {bad[:3]}")
    fac(8); s = bytearray(step); s[1] = 7; s[3] = 0; s[6] = 3; e.uc.mem_write(STEP0, bytes(s))
    check([e.build(mi, 0x1F3) for mi in range(6)] == [0, 0, 0, 1, 0, 0], "bit 6 off: the unit where it is")
    s = bytearray(step); s[1] = 7; s[3] = 0x40; s[6] = 3; s[5] = 6 | 0x80; e.uc.mem_write(STEP0, bytes(s))
    tied = [[e.build(mi, wd) for mi in range(6)] for wd in words]
    s[5] = 6; e.uc.mem_write(STEP0, bytes(s)); nt = s[4]
    keep = e.snap; sn = bytearray(keep); o_ = 0x54 + 4 * (nt >> 5); w_ = int.from_bytes(sn[o_:o_ + 4], "little") | 1 << (nt & 31); sn[o_:o_ + 4] = w_.to_bytes(4, "little")
    e.snap = bytes(sn); cont = [[e.build(mi, wd) for mi in range(6)] for wd in words]; e.snap = keep
    want_ = [0, 0, 0, 1, 0, 0]
    check(all(t_ == want_ for t_ in tied) and all(t_ == want_ for t_ in cont), f"a tied unit and a unit that continues a tie stay on their micro step {[t_ for t_ in tied + cont if t_ != want_][:2]}")
    fac(1)
    # a second unit: its own four bits
    st2 = bytearray(step); st2[0] |= 4; st2[12:16] = bytes([60, 3, 2, 100]); st2[1] = 7; st2[3] = 0x40; st2[6] = 3
    bad = []
    for wd in words:
        e.uc.mem_write(STEP0, bytes(st2)); got = [e.build(mi, wd) for mi in range(6)]
        w0, w2 = micro_model(3, 1, wd, 0), micro_model(2, 1, wd, 2)
        if got != [(1 if mi == w0 else 0) | (4 if mi == w2 else 0) for mi in range(6)]: bad.append((hex(wd), got, w0, w2))
    check(not bad, f"two units: one draw for the step, each its own offset {bad[:3]}")
    # recording
    bad, n = [], 0
    for rec, scr in ((1, 1), (1, 0), (0, 1)):
        e.transport(1, rec, 0); e.screen(scr)
        for mm in (0, 2, 5):
            for wd in words:
                s = bytearray(step); s[1] = 7; s[3] = 0x40; s[6] = mm; e.uc.mem_write(STEP0, bytes(s)); want = micro_model(mm, 1, wd); cur = wd; got = []
                for mi in range(6):
                    e.uc.mem_write(T3.PLAYER, e.snap); e.w32(T3.PLAYER + 4, cur); e.uc.mem_write(0x2006F000, bytes(4))
                    e.call(T3.BUILD, T3.PLAYER, 0, 0, mi, maxins=400_000); got.append(e.r8(T3.PLAYER + 0x13C + mi)); cur = e.r32(T3.PLAYER + 4)
                after = e.uc.mem_read(STEP0 + 6, 1)[0]; n += 1
                if got != [1 if mi == want else 0 for mi in range(6)] or after != (want if rec and scr else mm): bad.append((rec, scr, mm, hex(wd), got, after, want))
    check(not bad, f"Record with mode 2 on the screen: the micro step written, one start only; else the step untouched ({n}) {bad[:3]}")
    e.transport(0, 0, 0); e.screen(0)
    # everything at once, recording
    fac(8); r = 0x00ABCD00 & ~0x3C0
    nm = mut_model(n0, 5, 8, r, T8.MASKS[0], 0); v2, g2 = dyn_model(3, 8, r, 90, 6)
    res = {}
    for name, rec, scr in (("rec+view", 1, 1), ("rec", 1, 0), ("view", 0, 1)):
        e.transport(1, rec, 0); e.screen(scr)
        put(5, 3 << 4, 6, 90); got = e.note(r); res[name] = (got, bytes(e.uc.mem_read(STEP0, 8)))
    e.transport(0, 0, 0); e.screen(0)
    a_, sa = res["rec+view"]; b_, sb = res["rec"]; c_, sc = res["view"]
    check(a_ == b_ == c_ and a_[0][0] == nm and a_[0][1] == v2 and nm != n0 and (v2, g2) != (90, 6), f"the mutate and the dynamics together: the same in the three cases ({a_}, model {nm}, {v2}, {g2})")
    check(sa[4] == nm and sa[7] == v2 and sa[5] == g2 and sb[4] == n0 and sb[7] == 90 and sb[5] == 6 and sc[4:8] == sb[4:8], "Record with mode 2 on the screen: note, velocity, length written; otherwise not")
    # only the selected track is written
    fac(8); res = {}
    for sel in (0, 1):
        e.transport(1, 1, 0); e.screen(1); e.set_p0(e.r32(T8.CONT + 0x188), sel)
        put(5, 3 << 4, 6, 90); got = e.note(r); res[sel] = (got, bytes(e.uc.mem_read(STEP0, 8)))
    e.transport(0, 0, 0); e.screen(0)
    check(res[0][1][4] == nm and res[1][1][4] == n0 and res[1][1][7] == 90 and res[1][1][5] == 6 and res[1][0] == res[0][0],
          f"Record with another track selected: the same sound, nothing written ({res[1][1][4:8].hex()})")
    # the stock generator
    e.real = True
    plays = 480
    u5 = 2 if MUT3[0] else 1
    for g, exp, tol in ((1, u5 / 16, 0.04), (4, 4 * u5 / 16, 0.07), (0, 0, 0)):
        fac(g); moved = 0
        for _ in range(plays):
            put(5, note=n0); got = e.note(0); moved += got[0][0] != n0
        check(abs(moved / plays - exp) <= tol, f"the stock generator, level 5 at x {g}: {moved} of {plays} moved ({100 * moved / plays:.0f} %, {100 * exp:.0f} % expected)")
    plays = 600                                                                       # the user: «hi/lo parece tener una probabilidad mucho mayor de provocar up» at x 8
    for level, kept in ((6, 0.5), (7, 0.0)):
        fac(8); up = dn = same = 0
        for _ in range(plays):
            put(level, note=n0); got = e.note(0)[0][0]; up += got > n0; dn += got < n0; same += got == n0
        check(abs(up - dn) <= 3 * (up + dn) ** 0.5 and abs(same / plays - kept) <= 0.08, f"the stock generator, level {level} at x 8: {up} up, {dn} down, {same} kept")
    if MUT3[0]:
        for level, exp in ((4, 8 / 16), (5, 16 / 16)):
            fac(8); up = dn = 0
            for _ in range(240):
                put(level, note=n0); got = e.note(0)[0][0]; up += got > n0; dn += got < n0
            check(dn == 0 and abs(up / 240 - exp) <= 0.1, f"level {level} (octave up) at x 8: {up} up, {dn} down")
    e.real = False
    del e; gc.collect()


def PLAYER_SOUND(note): return T3.PLAYER + MU.O_SOUND + note


def drum_part(img, man, check):
    lab = {k: int(v, 16) for k, v in man["report"]["drumpat"]["labels"].items()}
    e = T.EL(img); e.at(300000); e.transport(0)
    r0 = lambda fn, *a: (e.call(fn, *a, maxins=4_000_000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    dp = D.DP0; ifc = e.r32(dp + 0x4C); setter = e.r32(dp + 0x50)
    hits, sets, cur = [], [], [0]
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    def on(uc, a, s_, d):
        if uc.reg_read(UC_ARM_REG_R0) == ifc: hits.append((cur[0], uc.reg_read(UC_ARM_REG_R2)))
        skip(uc)
    def st_(uc, a, s_, d):
        if uc.reg_read(UC_ARM_REG_R0) == setter: sets.append((cur[0], uc.reg_read(UC_ARM_REG_R2)))
    e.uc.hook_add(UC_HOOK_CODE, on, begin=e.r32(e.r32(ifc)) & ~1, end=e.r32(e.r32(ifc)) & ~1)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: skip(uc), begin=e.r32(e.r32(ifc) + 4) & ~1, end=e.r32(e.r32(ifc) + 4) & ~1)
    e.uc.hook_add(UC_HOOK_CODE, st_, begin=e.r32(e.r32(setter)) & ~1, end=e.r32(e.r32(setter)) & ~1)
    pat = r0(int(man["report"]["drumarp"]["labels"]["c_dapat"], 16), 0)
    base = e.r32(dp + 0x48) + 0x6A8 * pat
    st = e.r32(e.r32(DS.PROB_VIEW0 + 0xC))
    arr = bytearray(bytes(32) + bytes([7]) * 32 + bytes([0xFF]) * 32 + bytes(32))
    arr[0] = 100; arr[0x40] = 10; arr[0x60] = 1                                          # step 1: a hit, sample flip 10, on its first micro step
    e.uc.mem_write(base, bytes(arr)); e.uc.mem_write(base + 0x80, bytes([3, 0]))
    for k0, off in DS.ARRAYS:
        for w in range(8):
            for fn in (DS.PARAM_GET, DS.PARAM_WPTR): e.call(fn, st, k0 + w); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes(arr[off + 4 * w:off + 4 * w + 4]))
    a = fac_addr(e, 4)
    byte = lambda: e.r8(base + Q.DQ_OFF)
    prob = lambda: e.r32(e.r32(DS.PROB_VIEW0 + 4))
    leds = lambda: list(struct.unpack("<16H", bytes(e.uc.mem_read(prob(), 32))))
    e.btn(4); e.btn(12); X.frame(e); e.pad(24); X.frame(e); X.frame(e)
    sub = e.r8(MGR + 0x152)
    e.pad(0); X.frame(e)                                                                 # the first step selected
    L0 = leds()
    check(sub == 41 and L0 == row(0, 0, False, True, True), f"Pattern Settings pad 25, a drum: mode 2, the same pads, pad 27 dark ({[hex(x) for x in L0]})")
    bad = []
    for k in list(range(1, 8)) + [0]:
        e.pad(16 + k); X.frame(e); b_ = byte(); lv = (b_ >> 6) | (b_ & 4)
        if lv != k or leds()[:8] != row(k, 0, False, True, True)[:8]: bad.append((k, hex(b_), [hex(x) for x in leds()[:8]]))
    check(not bad, f"pads 17-24: the level in bits 6-7 + bit 2 {bad[:3]}")
    flag = bytes(e.uc.mem_read(e.r32(T.LZ.SESSION_OBJ + 0x14) + 0x27024 + Q.O_FLAG, 2))
    check(flag == b"DQ", f"the project marked ({flag})")
    seq = []
    for q, want in ((9, 1), (9, 0), (10, 2), (11, 2), (9, 1), (8, 0), (10, 2), (9, 1)) if DYN4[0] else ((8, 1), (8, 0), (9, 2), (10, 3), (11, 3), (9, 2), (9, 0), (10, 3)) if ROLL2[0] else ((8, 1), (8, 0), (9, 1), (10, 2), (11, 3), (8, 0), (11, 3)) if ROLL[0] else ((8, 1), (8, 0), (9, 1), (11, 3), (10, 3), (8, 0), (11, 3)):
        e.pad(16 + q); X.frame(e); seq.append((byte() & 3, want))
    check(all(p == w for p, w in seq), f"pad 25 on / off, pads 26 / 28 the dynamics, pad 27 nothing ({seq})")
    check(leds() == row(0, 1 if DYN4[0] else 3, False, True, True), f"their LEDs ({[hex(x) for x in leds()]})")
    b0 = byte(); e.uc.mem_write(base + Q.DQ_OFF, bytes([b0 | 3 << 3])); e.pad(16 + 5); bm = byte()
    check((bm >> 3) & 7 == 3, f"the frequency kept ({bm:#x})")
    e.uc.mem_write(base + Q.DQ_OFF, bytes([0]))
    e.pad(16 + 15); X.frame(e); m1 = e.r8(a); L1 = leds(); e.pad(16 + 15); X.frame(e); m2 = e.r8(a)
    check(m1 & MU.FAC_MICRO and not m2 & MU.FAC_MICRO and L1[15] == MU.MG_COLS[15][1] and (m1 & 0xE0) == MU.FAC_TAG, f"pad 32: the drum's micro steps on and off ({m1:#x}, {m2:#x})")
    e.pad(1); X.frame(e); Le = leds(); e.pad(16 + 15); X.frame(e); m3 = e.r8(a); Lf = leds(); e.pad(16 + 15); e.pad(16 + 3); be = e.r8(base + Q.DQ_OFF + 1)
    check(Le == [0] * 15 + [MU.MG_COLS[15][0]] and m3 & MU.FAC_MICRO and Lf[15] == MU.MG_COLS[15][1] and be == 0, f"a step without a hit: dark but pad 32, that still works; nothing written ({[hex(x) for x in Le]})")
    e.pad(0); X.frame(e)
    # the factor
    e.uc.mem_write(a, bytes([MU.FAC_TAG | 1])); e.btn(ID_UP); e.btn(ID_UP); fr = X.frame(e); g3 = e.r8(a)
    e.btn(ID_DOWN); g2 = e.r8(a)
    up2, dn1 = (4, 2) if DYN4[0] else (3, 2)
    check(g3 == MU.FAC_TAG | up2 and g2 == MU.FAC_TAG | dn1 and fr[LED_UP] & 0xFF == MU.COL_LIT, f"Octave: the drum's factor ({g3:#x}, {g2:#x})")
    e.pad(16 + 15); X.frame(e); e.btn(ID_UP); m4 = e.r8(a); e.pad(16 + 15)
    check(m4 == MU.FAC_TAG | MU.FAC_MICRO | up2, f"the factor keeps the micro steps' bit ({m4:#x})")
    # played (the stock generator)
    e.transport(1)
    slot2 = e.r32(D.DP_VT + 8) & ~1
    def play(passes):
        hits.clear(); sets.clear()
        for ps in range(passes):
            for stp in range(4):
                for m in range(6):
                    cur[0] = (ps, stp, m); e.call(slot2, dp, pat, stp, m, maxins=3_000_000)
        return list(hits), list(sets)
    def setb(b_, g=8, micro=False): e.uc.mem_write(base + Q.DQ_OFF, bytes([b_])); e.uc.mem_write(a, bytes([MU.FAC_TAG | g | (MU.FAC_MICRO if micro else 0)]))
    setb(1); h_, _ = play(40); vs = [v for _, v in h_]
    if DYN4[0]:
        on = [v for c, v in h_ if c[2] == 0]; m_ = sorted(set(c[2] for c, _ in h_)); steps = {}
        for c, v in h_: steps.setdefault(c[:2], []).append((c[2], v))
        kinds = set(tuple(m for m, _ in hs) for hs in steps.values())
        check(len(on) == 40 and min(on) >= 68 and max(on) <= 100 and len(set(on)) > 5, f"pad 26 (lo) at x 8: velocity - 32..0 ({min(on)}..{max(on)}, {len(set(on))} kinds)")
        check(kinds == {(0, 3), (0, 2, 5)} and all(len(set(v for _, v in hs)) == 1 for hs in steps.values()), f"pad 26: a roller every time, one of the two at random, with the hit's velocity ({sorted(kinds)})")
        setb(2); h_, _ = play(40); vs = [v for _, v in h_]
        check(len(h_) == 40 and all(c[2] == 0 for c, _ in h_) and min(vs) >= 100 and max(vs) <= 127 and len(set(vs)) > 5, f"pad 27 (hi) at x 8: velocity 0..+ 32, no roller ({min(vs)}..{max(vs)})")
        setb(3); h_, _ = play(20); m_ = sorted(set(c[2] for c, _ in h_))
        check(m_ != [0] and all(v <= 100 for _, v in h_), f"an old 3 plays as lo ({m_})")
        setb(1, 1); h2, _ = play(200); r_ = len(set(c[:2] for c, _ in h2 if c[2] != 0)) / 200
        check(0.15 <= r_ <= 0.35, f"pad 26 at x 1: about a quarter of the hits ({r_:.2f})")
        setb(1, 3); h2, _ = play(200); r_ = len(set(c[:2] for c, _ in h2 if c[2] != 0)) / 200
        check(0.35 <= r_ <= 0.65, f"a saved x 3 plays as x 2: about half ({r_:.2f})")
    if ROLL2[0] and not DYN4[0]:
        check(len(vs) == 40 and min(vs) >= 84 and max(vs) <= 116 and len(set(vs)) > 5, f"pad 25 at x 8: velocity +- 16 ({min(vs)}..{max(vs)}, {len(set(vs))} kinds)")
        setb(2); h_, _ = play(40); m_ = sorted(set(c[2] for c, _ in h_))
        check(len(h_) == 80 and m_ == [0, 3] and all(v == 100 for _, v in h_), f"pad 26 at x 8: once more on micro step 4 ({len(h_)}, {m_})")
        setb(3); h_, _ = play(40); m_ = sorted(set(c[2] for c, _ in h_))
        check(len(h_) == 120 and m_ == [0, 2, 5] and all(v == 100 for _, v in h_), f"pad 27 at x 8: once more on micro steps 3 and 6 ({len(h_)}, {m_})")
        for d_, nm, mm in ((2, "pad 26", 3), (3, "pad 27", 2)):
            setb(d_, 1); h2, _ = play(200); r_ = sum(1 for c, _ in h2 if c[2] == mm) / 200
            check(0.15 <= r_ <= 0.35, f"{nm} at x 1: rolls in about a quarter of the hits ({r_:.2f})")
    if ROLL2[0]:
        def moved(mask, g=8, n=40):
            e.uc.mem_write(base + 0x60, bytes([mask])); setb(0, g, True); h3, _ = play(n); e.uc.mem_write(base + 0x60, bytes([1]))
            return h3, sorted(set(c[2] for c, _ in h3))
        h_, ms_ = moved(0x08); check(len(h_) == 40 and ms_ == [1, 2, 4, 5], f"pad 32 at x 8, a hit on micro step 4: 1 or 2 earlier or later ({ms_})")
        h_, ms_ = moved(0x01); check(len(h_) == 40 and ms_ == [1, 2], f"on micro step 1: only later ({ms_})")
        h_, ms_ = moved(0x20); check(len(h_) == 40 and ms_ == [3, 4], f"on micro step 6: only earlier ({ms_})")
        h_, ms_ = moved(0x07, n=32); check(len(h_) == 96 and set(ms_) <= {1, 2, 3, 4} and len(ms_) == 4, f"three hits: the whole step later, all of them sound ({len(h_)}, {ms_})")
        h_, ms_ = moved(0x21, n=16); check(len(h_) == 32 and ms_ == [0, 5], f"hits on micro steps 1 and 6: no room, not moved ({ms_})")
        h_, ms_ = moved(0x08, 1, 64); late = sum(1 for c, _ in h_ if c[2] != 3)
        check(len(h_) == 64 and 5 <= late <= 30, f"pad 32 at x 1: 25 % moved ({late} of 64)")
        setb(1, 0); h_, _ = play(8)
        check(all(v == 100 for _, v in h_) and len(h_) == 8, "x 0: no change")
        setb(0, 1); h_, _ = play(8)
        check(all(c[2] == 0 for c, _ in h_) and len(h_) == 8, "off: on its micro step")
    else:
        check(len(vs) == 40 and min(vs) >= 68 and max(vs) <= 127 and len(set(vs)) > 5, f"accents at x 8: 68..127 ({min(vs)}..{max(vs)}, {len(set(vs))} kinds)")
    if ROLL2[0]: pass
    elif ROLL[0]:
        setb(2); h_, _ = play(40); m_ = sorted(set(c[2] for c, _ in h_)); vs = [v for c, v in h_]; on = [v for c, v in h_ if c[2] == 0]
        check(len(h_) == 80 and m_ == [0, 3] and min(vs) >= 84 and max(vs) <= 116 and len(set(on)) > 5 and all(h_[i][1] == h_[i + 1][1] for i in range(0, 80, 2)), f"pad 27 at x 8: the hit at +- 16, repeated 3 micro steps later with its velocity ({len(h_)}, {m_}, {min(vs)}..{max(vs)})")
        setb(3); h_, _ = play(40); m_ = sorted(set(c[2] for c, _ in h_))
        check(len(h_) == 120 and m_ == [0, 2, 4] and all(v == 100 for _, v in h_), f"pad 28 at x 8: triplets, micro steps 0, 2, 4 ({len(h_)}, {m_})")
        for d_, nm in ((2, "pad 27"), (3, "pad 28")):
            setb(d_, 1); h2, _ = play(200); r_ = sum(1 for c, _ in h2 if c[2] == (3 if d_ == 2 else 2)) / 200
            check(0.15 <= r_ <= 0.35, f"{nm} at x 1: rolls in about a quarter of the hits ({r_:.2f})")
    else:
        setb(3); h_, _ = play(40); vs = [v for _, v in h_]
        check(len(vs) == 40 and min(vs) >= 84 and max(vs) <= 116 and len(set(vs)) > 5, f"pad 28 at x 8: velocity ± 16 ({min(vs)}..{max(vs)})")
    if not ROLL2[0]: old_micro(e, play, setb, base, man, check)
    up3 = "c_mgup" in man["report"]["mutate39"]["labels"]
    for level, want, name in ((1, {9, 10, 11}, "pad 18"), (3, {9, 11}, "pad 20"), (4, {10, 18} if up3 else {2, 10}, "pad 21"), (5, {18} if up3 else {10, 18}, "pad 22"), (6, {2, 10, 18}, "pad 23"), (7, {2, 18}, "pad 24")):
        setb((level & 3) << 6 | (level & 4), 8); h_, s_ = play(48); smp = set(v for c, v in s_)
        check(len(h_) == 48 and smp == want, f"{name} at x 8 ({'always' if 10 not in want else '50 %'}): the sample {sorted(smp)}")
    setb(3 << 6, 1); h_, s_ = play(64); moved = sum(1 for c, v in s_ if v in (9, 11))
    check(9 <= moved <= 28, f"pad 20 at x 1: 25 % ({moved} of 64)")
    e.uc.mem_write(e.r32(T.LZ.SESSION_OBJ + 0x14) + 0x27024 + Q.O_FLAG, bytes(2)); setb(3 | 3 << 3, 8); h_, _ = play(4)
    check(len(h_) == 4 and all(v == 100 for _, v in h_), f"a project not marked: the stock's hits ({h_})")
    del e; gc.collect()


def old_micro(e, play, setb, base, man, check):
    setb(1, 0); h_, _ = play(8)
    check(all(v == 100 for _, v in h_) and len(h_) == 8, "x 0: no change")
    setb(0, 8, True); h_, _ = play(40); ms_ = sorted(set(c[2] for c, _ in h_))
    rep32 = "mixsolo" in man["report"] and not ROLL[0]
    if rep32:                                                                           # drumpat.use_repeat
        check(len(h_) == 80 and ms_ == [0, 2, 3] and sum(1 for c, _ in h_ if c[2] == 0) == 40, f"pad 32 at x 8: the hit on time and once more 2 or 3 micro steps later ({len(h_)}, {ms_})")
        setb(0, 1, True); h2, _ = play(200); r_ = sum(1 for c, _ in h2 if c[2]) / 200
        check(0.15 <= r_ <= 0.35, f"at x 1: a repeat in about a quarter of the hits ({r_:.2f})")
    else: check(len(h_) == 40 and ms_ == [1, 2], f"the micro steps at x 8: the hit 1 or 2 micro steps later, never earlier ({ms_})")
    setb(0, 1, True); h_, _ = play(64); late = sum(1 for c, _ in h_ if c[2])
    check(len(h_) == 64 + (late if rep32 else 0) and 5 <= late <= 30, f"the micro steps at x 1: 25 % ({late} of 64)")
    setb(0, 1); h_, _ = play(8)
    check(all(c[2] == 0 for c, _ in h_) and len(h_) == 8, "off: on its micro step")
    e.uc.mem_write(base + 0x60, bytes([7])); setb(0, 8, True); h_, _ = play(32); e.uc.mem_write(base + 0x60, bytes([1]))
    check(len(h_) >= 96 if rep32 else len(h_) == 96, f"three hits in a step, the micro steps at x 8: all of them sound ({len(h_)} of 96)")


def sweep_part(img, man, check):
    e = X.EP(img, man); R = man["report"]
    pat = lambda t: e.r0(int(R["vcf20"]["labels"]["c_sdpat"], 16), (t + 2) % 4)
    OFF = lambda k, s: 0x3A8 + 192 * k + 6 * s
    def lane(t, k, s, v): e.uc.mem_write(pat(t) + OFF(k, s), bytes([v]) * 6)
    def lanes(t): return bytes(e.uc.mem_read(pat(t) + 0x3A8, 192 * 8))
    hold = lambda q: e.call(PRESS, MGR, q, 100, maxins=8_000_000)
    let = lambda q: e.call(RELEASE, MGR, q, maxins=8_000_000)
    for t in (0, 2):
        for k in range(8):
            for s in range(32): lane(t, k, s, 0xFF)
    line = lambda a, b, lo, hi, s: a + int((b - a) * (s - lo) / (hi - lo))              # truncates toward 0, as sdiv
    def setup(t):
        for k in range(8):
            for s in range(32): lane(t, k, s, 0xFF)
        lane(t, 4, 2, 20); lane(t, 4, 10, 100); lane(t, 1, 2, 60); lane(t, 1, 10, 0); lane(t, 6, 2, 50); lane(t, 3, 10, 70)
    def want(t, a4, b4, a1, b1, lo=2, hi=10):
        w = bytearray(lanes(t))
        for s in range(lo + 1, hi):
            w[OFF(4, s) - 0x3A8:OFF(4, s) - 0x3A8 + 6] = bytes([line(a4, b4, lo, hi, s)]) * 6
            w[OFF(1, s) - 0x3A8:OFF(1, s) - 0x3A8 + 6] = bytes([line(a1, b1, lo, hi, s)]) * 6
        return bytes(w)
    # MIDI 1
    e.btn(2); e.btn(10); setup(2); w = want(2, 20, 100, 60, 0)
    notes = bytes(e.uc.mem_read(pat(2), 28 * 32))
    e.shift(True); X.frame(e)
    hold(2); hold(10); let(10); let(2); X.frame(e); got = lanes(2); yl = X.frame(e)[:16]; e.shift(False); X.frame(e)
    check(got == w, f"MIDI 1, step 3 held + step 11: lanes 2 and 5 on the line, all 6 micro steps; the ends, the steps outside and the lanes with one end untouched")
    check(bytes(e.uc.mem_read(pat(2), 28 * 32)) == notes, "the notes and the marks untouched")
    check(all(yl[s] & 0xFF == AR.COL_AV for s in range(2, 11)), f"the steps between yellow now ({[hex(x) for x in yl]})")
    check([e.r8(pat(2) + OFF(4, s)) for s in range(3, 10)] == [line(20, 100, 2, 10, s) for s in range(3, 10)], f"lane 5: {[e.r8(pat(2) + OFF(4, s)) for s in range(2, 11)]}")
    setup(2); w = want(2, 20, 100, 60, 0)
    e.shift(True); X.frame(e); hold(10); hold(2); let(2); let(10); X.frame(e); got = lanes(2); e.shift(False); X.frame(e)
    check(got == w, "the other order: the same")
    setup(2); before = lanes(2)
    e.shift(True); X.frame(e); hold(2); hold(5); let(5); let(2); X.frame(e); got = lanes(2); m5 = e.r8(pat(2) + 28 * 5 + 3); e.shift(False); X.frame(e)
    check(got == before and not m5 & AR.MARK, f"a step without automation as the other end: nothing, no mark ({m5:#x})")
    e.shift(True); X.frame(e); e.pad(2); e.pad(10); X.frame(e); got = lanes(2); e.shift(False); X.frame(e)
    check(got == before, "two taps, not held: two previews, nothing written")
    e.shift(True); X.frame(e); hold(2); X.frame(e); e.shift(False); X.frame(e); let(2)
    e.shift(True); X.frame(e); e.pad(10); X.frame(e); got = lanes(2); e.shift(False); X.frame(e)
    check(got == before, "Shift let go with a step held: no sweep left pending")
    e.shift(True); X.frame(e); hold(5); let(5); m5 = e.r8(pat(2) + 28 * 5 + 3); e.pad(5); e.shift(False); X.frame(e)
    check(m5 & AR.MARK, f"a step without automation alone: the mark, as before ({m5:#x})")
    # Synth 1
    e.btn(0); e.btn(10); setup(0); w = want(0, 20, 100, 60, 0)
    e.shift(True); X.frame(e); hold(2); hold(10); let(10); let(2); X.frame(e); got = lanes(0); e.shift(False); X.frame(e)
    check(got == w, "Synth 1: the same")
    del e; gc.collect()


def main(img, man):
    if "jumpoct" in man["report"]: MU.use_white25()
    ROLL[0] = "c_dqroll" in man["report"]["drumpat"]["labels"]
    ROLL2[0] = "pl_le" in man["report"]["drumpat"]["labels"]
    DYN4[0] = "dv_b" in man["report"]["mutate39"]["labels"]
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    view_part(img, man, check)
    player_part(img, man, check)
    drum_part(img, man, check)
    sweep_part(img, man, check)
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())) else 0)
