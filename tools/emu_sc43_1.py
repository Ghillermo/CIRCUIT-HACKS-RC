"""SC43.1 ARM tests (the user, 2026-10-16: «en el roller, la fila inferior se ve parcialmente blanca (pads 27 al 30)»), through the controller and
the real LED task with the clock moving, and the drums' real note-on / note-off (their interface returns in emulation):
  * Drum 1's Note view, stopped: a roller held = Drum 1's two boxes (pads 28 / 29) white while its hits sound; every hit gets its note-off 100 ms
    later (or the next hit's, which turns it off first); let go: the boxes in the drum's colour again and the player not sounding (the build
    before: white for ever, no note-off);
  * playing: a note-off time left pending is dropped (the sequencer's), no note-off of ours;
  * Drum 1's arpeggio, stopped (Preset view, pads 1 + 4 held, 1/8): each hit's note-off 100 ms later; let go: not sounding.

    python tools/emu_sc43_1.py SC43.1.bin SC43.1_manifest.json [SC43.bin SC43_manifest.json]
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import rollers as R  # noqa: E402
import drumarp as D  # noqa: E402
import drumnote as DN  # noqa: E402
DN.MIRROR = True

MGR = T.MGR
WHITE = 0x01


def note_view(img):
    e = T.EL(img); t = [300000]; e.at(t[0]); e.transport(0)
    ifc = [e.r32(R.DP0 + R.DP_SZ * d + 0x4C) for d in range(4)]
    offs = []
    on_fn, off_fn = e.r32(e.r32(ifc[0])) & ~1, e.r32(e.r32(ifc[0]) + 4) & ~1
    def ev(kind):
        def f(uc, a, s, d_):
            r = uc.reg_read(UC_ARM_REG_R0)
            if r in ifc: offs.append((kind, ifc.index(r), e.r32(0x2000081C)))
        return f
    e.uc.hook_add(UC_HOOK_CODE, ev("on"), begin=on_fn, end=on_fn)
    e.uc.hook_add(UC_HOOK_CODE, ev("off"), begin=off_fn, end=off_fn)
    def run(ms, step=10):
        fs = []
        for _ in range(ms // step): t[0] += step; e.at(t[0]); fs.append(X.frame(e))
        return fs
    return e, t, offs, run


def roller_case(img):
    e, t, offs, run = note_view(img)
    e.btn(4)
    for _ in range(3):
        if e.r8(MGR + 0x152) == 42: break
        e.btn(9)
    f0 = X.frame(e)
    pad = [q for q in range(24) if R.tables()[0][q] == 0 and R.tables()[1][q] == 0][0]
    offs.clear(); t0 = t[0]
    e.call(T.PRESS, MGR, pad, 100, maxins=8_000_000)
    held = run(300)
    e.call(T.RELEASE, MGR, pad, maxins=8_000_000)
    after = run(200)
    res = dict(sub=e.r8(MGR + 0x152), idle=(f0[27], f0[28]), white=any(f[27] == WHITE and f[28] == WHITE for f in held),
               end=(after[-1][27], after[-1][28]), sounding=e.r8(R.DP0 + 0x59), ev=[(k, d, ms - t0) for k, d, ms in offs])
    del e; gc.collect()
    return res


def main(img, man, old=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    col = R.DRUM_COL[0]

    # ---- the rollers, stopped
    r = roller_case(img)
    check(r["sub"] == 42 and r["idle"] == (col, col) and r["white"], f"Drum 1's Note view: boxes {r['idle'][0]:#x} idle, white while its roller's hits sound")
    ons = [ms for k, d, ms in r["ev"] if k == "on" and d == 0]; ofs = [ms for k, d, ms in r["ev"] if k == "off" and d == 0]
    check(len(ons) == 3 and len(ofs) == 3 and all(90 <= b_ - a_ <= 110 for a_, b_ in zip(ons, ofs)),
          f"each roller hit's note-off 100 ms later (on {ons}, off {ofs} ms)")
    check(r["end"] == (col, col) and r["sounding"] == 0, f"let go: the boxes {r['end'][0]:#x} / {r['end'][1]:#x}, not sounding ({r['sounding']})")
    if old is not None:
        o = roller_case(old)
        last = [k for k, d, _ in o["ev"] if d == 0][-1:]
        check(o["end"] == (WHITE, WHITE) and last == ["on"], f"the build before: white for ever ({o['end'][0]:#x}), the last hit without its note-off ({last})")

    # ---- playing: a pending time dropped
    lab = {k: int(v, 16) for k, v in man["report"]["rollers"]["labels"].items()}
    e, t, offs, run = note_view(img)
    tail = e.r32(R.SESSION_OBJ + 0x14) + R.TAIL
    e.w32(tail + R.O_OFF + 4, t[0] + 50); e.uc.mem_write(R.DP0 + R.DP_SZ + 0x59, bytes([1]))
    e.transport(1); offs.clear(); run(150)
    check(e.r32(tail + R.O_OFF + 4) == 0 and not [o for o in offs if o[1] == 1], f"playing: Drum 2's pending note-off dropped, none of ours ({offs})")
    e.transport(0)
    del e; gc.collect()

    # ---- the drum arpeggio, stopped
    dl = {k: int(v, 16) for k, v in man["report"]["drumarp"]["labels"].items()}
    e, t, offs, run = note_view(img)
    e.btn(4); e.btn(12)
    e.call(dl["c_dapat"], 0); pat = e.uc.reg_read(UC_ARM_REG_R0)
    e.call(dl["c_daset"], 0, pat, 0x80 | 6 << 3)                                                       # on, 1/8
    e.btn(4); e.btn(8); X.frame(e)
    e.call(T.PRESS, MGR, 0, 90, maxins=8_000_000); offs.clear(); t0 = t[0]; e.call(T.PRESS, MGR, 3, 110, maxins=8_000_000)
    run(600)
    e.call(T.RELEASE, MGR, 3, maxins=8_000_000); e.call(T.RELEASE, MGR, 0, maxins=8_000_000)
    run(200)
    ons = [ms - t0 for k, d, ms in offs if k == "on" and d == 0]; ofs = [ms - t0 for k, d, ms in offs if k == "off" and d == 0]
    check(e.r8(MGR + 0x152) == 36 and len(ons) >= 2 and len(ofs) == len(ons) and all(90 <= b_ - a_ <= 110 for a_, b_ in zip(ons, ofs)) and e.r8(R.DP0 + 0x59) == 0,
          f"Drum 1's arpeggio: each hit's note-off 100 ms later (on {ons}, off {ofs} ms); let go: not sounding ({e.r8(R.DP0 + 0x59)})")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    old = Path(a[3]).read_bytes() if len(a) > 3 else None
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), old) else 0)
