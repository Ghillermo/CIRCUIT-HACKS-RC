"""SC48.3 / Beta 3.40 (playmode.use_nudge2): the new Nudge, through the controller (emu_sc40_8's harness).

    python tools/emu_nudge2.py SC48.3.bin SC48.3_manifest.json

Pattern Settings of Synth 1, then of Drum 1; the pattern filled with known bytes (steps and lanes; the drums' four arrays, drumpat's bytes and
lanes); pad 26 = the first-to-last range one step back, Shift + pad 26 = forward:
  * a rotation by one over first - 1 .. last (back) or first .. last + 1 (forward): the step the range moves onto goes to the freed end; first and
    last move by one; the rest of the pattern untouched;
  * a range at step 1 (back) or at the pattern's end (forward, 16 or 32): the whole pattern rotates by one, first / last stay;
  * the drum pattern: its arrays, drumpat's step bytes and its 8 lanes the same way.
SC50 / RC4.04 (playmode.use_nudge3): the rotation inside first .. last (what leaves at one end comes in at the other), first and last stay; a range of
one step: nothing; the Note view (MIDI 1, Drum 1), back from Pattern Settings without Play, shows the steps where they went, and an edit of the stock
afterwards keeps them.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc40_8 as T  # noqa: E402
from emu_sc35 import MGR  # noqa: E402
from emu_sc08 import CONT  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import playmode as PM  # noqa: E402


def rot_sub(data, size, s, n, k):
    """elements s .. s + n - 1 rotated k to the left (the rest as it is)"""
    el = [data[size * i:size * i + size] for i in range(len(data) // size)]
    sub = el[s:s + n]; el[s:s + n] = sub[k:] + sub[:k]
    return b"".join(el)


def plan(first, last, fwd, v3=False):
    if v3:
        n = last - first + 1
        return (first, n, n - 1 if fwd else 1, first, last)
    L = 32 if first >= 16 or last >= 16 else 16
    if not fwd:
        return (0, L, 1, first, last) if first == 0 else (first - 1, last - first + 2, 1, first - 1, last - 1)
    return (0, L, L - 1, first, last) if last >= L - 1 else (first, last - first + 2, last - first + 1, first + 1, last + 1)


def view_part(img, man, check):
    """the Note view, without Play"""
    import emu_sc42_6 as X
    import emu_sc22_4 as T4
    import smnote as SN
    import drumarp as DA
    import drumstore as DS
    from unicorn.arm_const import UC_ARM_REG_R0
    EMPTY = bytes([0, 0, 0, 0]) + bytes([0, 0, 0, 0x60]) * 6
    NOTE = bytes([1, 7, 0, 0, 60, 6, 0, 100]) + bytes([0, 0, 0, 0x60]) * 5
    R = man["report"]
    e = X.EP(img, man)
    def go(sub):
        for _ in range(4):
            if e.r8(MGR + 0x152) == sub: return
            e.btn(9)
    def lit(col): return [s for s, v in enumerate(X.frame(e)[:16]) if v & 0xFF == col]
    # MIDI 1
    e.btn(2); pat = e.r0(e.vl["c_sdpat"], 0); st = pat + PM.SET_OFF
    ed = e.r32(SN.EDITOR + 2 * SN.ED_SZ + 0x18)
    for s_ in range(16): e.uc.mem_write(pat + 28 * s_, EMPTY)
    for s_ in (6, 7, 9): e.uc.mem_write(pat + 28 * s_, NOTE)
    e.uc.mem_write(st, bytes([12, 6]))
    e.call(SN.STORE_W, ed); e.call(SN.COMMIT, ed)
    go(19); v0 = lit(SN.NV_NOTE)
    e.btn(12); X.frame(e); e.pad(PM.PAD_NUDGE); X.frame(e); go(19); v1 = lit(SN.NV_NOTE); a1 = (e.r8(st + 1), e.r8(st))
    e.btn(12); X.frame(e); e.pad(PM.PAD_NUDGE); X.frame(e); go(19); v2 = lit(SN.NV_NOTE)
    e.btn(12); X.frame(e); e.set_p0(e.r32(MGR + 0xC), 1); e.pad(PM.PAD_NUDGE); e.set_p0(e.r32(MGR + 0xC), 0); X.frame(e); go(19); v3 = lit(SN.NV_NOTE)
    e.btn(12); X.frame(e); e.pad(PM.PAD_NUDGE); e.pad(PM.PAD_NUDGE); X.frame(e); go(19); v4 = lit(SN.NV_NOTE); a4 = (e.r8(st + 1), e.r8(st))
    check(v0 == [6, 7, 9] and v1 == [6, 8, 12] and a1 == (6, 12), f"MIDI 1, range 7-13, the Note view: {v0}, one back = {v1} (the step at the start comes in at the end), first and last stay {a1}")
    check(v2 == [7, 11, 12] and v3 == [6, 8, 12] and v4 == [6, 10, 11] and a4 == (6, 12), f"again {v2}, Shift = forward {v3}, twice back {v4}")
    e.uc.mem_write(st, bytes([9, 9]))
    before = bytes(e.uc.mem_read(pat, 28 * 16)); e.btn(12); X.frame(e); e.pad(PM.PAD_NUDGE); X.frame(e)
    check(bytes(e.uc.mem_read(pat, 28 * 16)) == before and (e.r8(st + 1), e.r8(st)) == (9, 9), "a range of one step: nothing")
    # Drum 1
    e.btn(4); X.frame(e)
    dpat = e.r0(int(R["drumarp"]["labels"]["c_dapat"], 16), 0); base = e.r32(DA.DP0 + 0x48) + 0x6A8 * dpat
    stp = e.r32(e.r32(DS.PROB_VIEW0 + 0xC))
    arr = bytearray(bytes(32) + bytes([7]) * 32 + bytes([0xFF]) * 32 + bytes(32))
    for s_ in (6, 7, 9): arr[s_] = 100; arr[0x60 + s_] = 1
    e.uc.mem_write(base, bytes(arr)); e.uc.mem_write(base + 0x80, bytes([12, 6]))
    for k0, off in DS.ARRAYS:
        for w in range(8):
            for fn in (DS.PARAM_GET, DS.PARAM_WPTR): e.call(fn, stp, k0 + w); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes(arr[off + 4 * w:off + 4 * w + 4]))
    e.call(SN.COMMIT, stp)
    go(37); d0 = lit(0x13)
    e.btn(12); X.frame(e); e.pad(PM.PAD_NUDGE); X.frame(e); go(37); d1 = lit(0x13); ad = (e.r8(base + 0x81), e.r8(base + 0x80))
    check(d0 == [6, 7, 9] and d1 == [6, 8, 12] and ad == (6, 12), f"Drum 1, the same: {d0}, one back = {d1}, first and last stay {ad}")
    e.btn(12); X.frame(e); e.btn(12); X.frame(e); X.frame(e); e.pad(9); X.frame(e); e.pad(16 + 3); X.frame(e)         # the stock's probability view: an edit of step 10
    raw = [s_ for s_ in range(16) if e.r8(base + s_)]
    check(raw == [6, 8, 9, 12], f"after an edit of the stock (a tap on empty step 10 adds a hit), the hits stay ({raw})")
    del e; gc.collect()


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    LP = {k: int(v, 16) for k, v in man["report"]["patchain"]["labels"].items()}
    v3 = "n2_k" in man["report"]["playmode"]["labels"]
    e = T.E8(img, man, LP)
    e.live(0x00)
    for t in range(8): e.chain(t, e.playing(t), e.playing(t))
    press = lambda i: e.call(0x08033320, MGR, i, maxins=8_000_000)
    release = lambda i: e.call(0x0803381A, MGR, i, maxins=8_000_000)
    def pad(q, shift=False):
        if shift: e.set_p0(e.r32(MGR + 0xC), 1)
        e.call(PRESS, MGR, q, 100, maxins=8_000_000); e.call(RELEASE, MGR, q, maxins=8_000_000)
        if shift: e.set_p0(e.r32(MGR + 0xC), 0)
    e.set_p0(e.r32(CONT + 0x188), 0); press(0); release(0); press(12); release(12)
    pat = e.playing(0); S = e.settings(0, pat); base = S - PM.SET_OFF
    res = []
    for first, last, fwd in ((5, 12, 0), (5, 12, 1), (0, 9, 0), (3, 15, 1), (20, 27, 0), (4, 31, 1), (16, 30, 1)):
        e.setpat(0, pat, first, last, 0, 0)
        steps = b"".join(bytes([0x10 + s, s]) + bytes((7 * s + i) & 0xFF for i in range(26)) for s in range(32))
        lanes = b"".join(bytes((l * 37 + s * 5 + i) & 0xFF for s in range(32) for i in range(6)) for l in range(12))
        e.uc.mem_write(base, steps); e.uc.mem_write(base + PM.AUTO_OFF, lanes)
        w0 = bytes(e.uc.mem_read(base, 0xCA8))
        pad(PM.PAD_NUDGE, shift=bool(fwd))
        w = bytes(e.uc.mem_read(base, 0xCA8))
        s, n, k, nf, nl = plan(first, last, fwd, v3)
        ok = (w[:len(steps)] == rot_sub(steps, 28, s, n, k)
              and w[PM.AUTO_OFF:PM.AUTO_OFF + len(lanes)] == b"".join(rot_sub(lanes[192 * l:192 * l + 192], 6, s, n, k) for l in range(12))
              and (e.r8(S + 1), e.r8(S)) == (nf, nl))
        rest = w[len(steps):PM.SET_OFF] == w0[len(steps):PM.SET_OFF] and w[PM.SET_OFF + 2:PM.AUTO_OFF] == w0[PM.SET_OFF + 2:PM.AUTO_OFF]
        res.append((first + 1, last + 1, "fwd" if fwd else "back", "->", e.r8(S + 1) + 1, e.r8(S) + 1, ok and rest))
    check(all(r[-1] for r in res), f"note track: {res}")
    # a drum track
    press(12); release(12); press(12); release(12)
    e.set_p0(e.r32(CONT + 0x188), 4); press(4); release(4); press(12); release(12)
    dp = e.playing(4); DS = e.settings(4, dp); db = DS - PM.D_SET_OFF
    dres = []
    for first, last, fwd in ((2, 9, 0), (2, 9, 1), (0, 5, 0)):
        e.setpat(4, dp, first, last, 0, 0)
        arrays = bytes((j * 41 + s * 3) & 0xFF for j in range(4) for s in range(32))
        dq = bytes((0x40 + s) for s in range(32))
        dl = b"".join(bytes((l * 13 + s * 7 + i) & 0xFF for s in range(32) for i in range(6)) for l in range(8))
        e.uc.mem_write(db, arrays); e.uc.mem_write(db + 0x88, dq); e.uc.mem_write(db + PM.D_AUTO_OFF, dl)
        pad(PM.PAD_NUDGE, shift=bool(fwd))
        s, n, k, nf, nl = plan(first, last, fwd, v3)
        w = bytes(e.uc.mem_read(db, 0x6A8))
        ok = (w[:128] == b"".join(rot_sub(arrays[32 * j:32 * j + 32], 1, s, n, k) for j in range(4))
              and w[0x88:0x88 + 32] == rot_sub(dq, 1, s, n, k)
              and w[PM.D_AUTO_OFF:PM.D_AUTO_OFF + len(dl)] == b"".join(rot_sub(dl[192 * l:192 * l + 192], 6, s, n, k) for l in range(8))
              and (e.r8(DS + 1), e.r8(DS)) == (nf, nl))
        dres.append((first + 1, last + 1, "fwd" if fwd else "back", "->", e.r8(DS + 1) + 1, e.r8(DS) + 1, ok))
    check(all(r[-1] for r in dres), f"drum track: {dres}")
    del e; gc.collect()
    if v3: view_part(img, man, check)
    print(f"{man.get('marker', '?')} NUDGE2 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
