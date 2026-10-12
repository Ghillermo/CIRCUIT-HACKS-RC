"""SC23.5: the Master FX song pointer playhead comes from the tick hook (16 steps, linear, no dependence on the transport store) and pad 8 = the FX bypass pad.

    python tools/emu_sc23_5_gfx.py SC23.5.bin SC23.5_manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc17_7 import E7  # noqa: E402
import build_sc17 as B  # noqa: E402
B.use_jump(hold=True, white=True); B.CLR_ON, B.CLR_DIM = 0x01, 0x03; B.JMP_ON, B.JMP_OFF = 0x2D, 0x2E
B.use_spcache(); B.CLR_COPY = True
HAL = 0x2000081C


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    import struct
    stock_pal = [struct.unpack_from("<H", img, B.PAL - 0x08010000 + 2 * i)[0] for i in range(16)]
    pal = [(stock_pal[on], stock_pal[dim]) for on, dim in B.PAL_IDX]           # the song pointer keeps the palette's colours (build_sc17.use_vinyl_peach changes only Vinyl's pads)
    base_c, head_c = B.SP_COLORS(pal)[0], B.SP_HEAD
    gc.collect(); x = E7(img, man); x.grid(); x.setsp()
    x.w32(HAL, 100000)
    # the playhead follows the tick, step = (ticks / 6) mod 16, over three bars, without the transport store
    x.set_ticks(0)
    bad = []
    for _ in range(3 * 96 + 10):
        t = x.tick(1)[0]
        g = x.gleds()[8:24]
        want = (t // 6) & 15
        if g != [head_c if i == want else base_c for i in range(16)]: bad.append((t, g))
    check(not bad, f"the lit step is the step of the tick about to run, 16 steps linearly for 3 bars (wrong: {bad[:2]})")
    x.set_ticks(6 * 7 + 1); x.tick(1)
    g = x.gleds()[8:24]
    check(g[7] == head_c and g.count(head_c) == 1, f"tick 44 -> step 8 lit ({[hex(v) for v in g]})")
    # stopped: no ticks for more than 2 s -> no playhead, and it stays off (the 8 bit stamp does not wrap into 'fresh')
    x.w32(HAL, 100000 + 3000)
    check(all(v == base_c for v in x.gleds()[8:24]), "2 s without a tick (stopped): no playhead")
    for dt in (10000, 17000, 30000, 40000, 70000, 3_000_000, 100_000_000):
        x.w32(HAL, 100000 + 3000 + dt)
        if any(v == head_c for v in x.gleds()[8:24]): check(False, f"a ghost playhead after {dt} ms"); break
    else: check(True, "and no ghost playhead later (24-bit stamp)")
    x.tick(1)
    check(any(v == head_c for v in x.gleds()[8:24]), "the next tick brings it back")
    # the cache words are not the effect start times
    c0 = tuple(x.s14b(B.GFX_OFF + B.S_SPS + i) for i in range(4))
    x.pad(3, shift=True); x.rel(3); x.pad(2, shift=True); x.rel(2)
    check(tuple(x.s14b(B.GFX_OFF + B.S_SPS + i) for i in range(4)) == c0, "latching effects (Digitise included) does not touch the playhead cache")
    # pad 8 = pad 25
    g = x.gleds()
    check(g[7] == g[24], f"pad 8 = the FX bypass pad ({g[7]:#x} = {g[24]:#x})")
    x.setsp(ls=3); g = x.gleds()
    check(g[7] == g[24], "with a song pointer range set: still the same as pad 25")
    print("SC23.5 MASTER FX RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
