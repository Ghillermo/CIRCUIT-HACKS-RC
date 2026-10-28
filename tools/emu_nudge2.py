"""SC48.3 / Beta 3.40 (playmode.use_nudge2): the new Nudge, through the controller (emu_sc40_8's harness).

    python tools/emu_nudge2.py SC48.3.bin SC48.3_manifest.json

Pattern Settings of Synth 1, then of Drum 1; the pattern filled with known bytes (steps and lanes; the drums' four arrays, drumpat's bytes and
lanes); pad 26 = the first-to-last range one step back, Shift + pad 26 = forward:
  * a rotation by one over first - 1 .. last (back) or first .. last + 1 (forward): the step the range moves onto goes to the freed end; first and
    last move by one; the rest of the pattern untouched;
  * a range at step 1 (back) or at the pattern's end (forward, 16 or 32): the whole pattern rotates by one, first / last stay;
  * the drum pattern: its arrays, drumpat's step bytes and its 8 lanes the same way.
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


def plan(first, last, fwd):
    L = 32 if first >= 16 or last >= 16 else 16
    if not fwd:
        return (0, L, 1, first, last) if first == 0 else (first - 1, last - first + 2, 1, first - 1, last - 1)
    return (0, L, L - 1, first, last) if last >= L - 1 else (first, last - first + 2, last - first + 1, first + 1, last + 1)


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    LP = {k: int(v, 16) for k, v in man["report"]["patchain"]["labels"].items()}
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
        s, n, k, nf, nl = plan(first, last, fwd)
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
        s, n, k, nf, nl = plan(first, last, fwd)
        w = bytes(e.uc.mem_read(db, 0x6A8))
        ok = (w[:128] == b"".join(rot_sub(arrays[32 * j:32 * j + 32], 1, s, n, k) for j in range(4))
              and w[0x88:0x88 + 32] == rot_sub(dq, 1, s, n, k)
              and w[PM.D_AUTO_OFF:PM.D_AUTO_OFF + len(dl)] == b"".join(rot_sub(dl[192 * l:192 * l + 192], 6, s, n, k) for l in range(8))
              and (e.r8(DS + 1), e.r8(DS)) == (nf, nl))
        dres.append((first + 1, last + 1, "fwd" if fwd else "back", "->", e.r8(DS + 1) + 1, e.r8(DS) + 1, ok))
    check(all(r[-1] for r in dres), f"drum track: {dres}")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} NUDGE2 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
