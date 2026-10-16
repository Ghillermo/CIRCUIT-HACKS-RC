"""SC42.8 ARM tests (the drums' arpeggiator, tools/drumarp.py), through the controller and the real LED task with the clock moving:
  * Drum 1's Pattern Settings, Shift: pad 25 = on (its LED green, with and without Shift), pad 29 = up (green with Shift), pad 20 = 1/16, pad 22 =
    1/8; a note track's Shift + pad 25 still the note arpeggiator's;
  * Drum 1's Preset view, stopped: pad 1 held (the stock's: its sample), pad 4 held with it = not the stock's (the selection stays) and the
    arpeggio: the drum's sample set through its player (0, 3, 0, 3 …) and a hit through its interface every arpeggio step (250 ms at 1/8, 120 BPM);
    let go: the drum's selected sample again, nothing more;
  * playing (the drum player's slot 2, micro step by micro step): on the grid (1/16: micro step 0 of each step; 1/32: 0 and 3);
  * the arpeggiator off: two pads held = the stock's (no hit of ours); another view: over after 200 ms.

    python tools/emu_sc42_8.py SC42.8.bin SC42.8_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import drumarp as D  # noqa: E402

MGR = T.MGR


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    lab = {k: int(v, 16) for k, v in man["report"]["drumarp"]["labels"].items()}
    arl = {k: int(v, 16) for k, v in man["report"]["arp"]["labels"].items()}
    e = T.EL(img); t = [300000]; e.at(t[0]); e.transport(0)
    r0 = lambda fn, *a: (e.call(fn, *a, maxins=4_000_000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    hits, sets = [], []
    dp = D.DP0; ifc = e.r32(dp + 0x4C); setter = e.r32(dp + 0x50)
    on_fn = e.r32(e.r32(ifc)) & ~1; off_fn = e.r32(e.r32(ifc) + 4) & ~1; set_fn = e.r32(e.r32(setter)) & ~1
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    def on(uc, a, s, d):
        if uc.reg_read(UC_ARM_REG_R0) == ifc: hits.append((e.r32(0x2000081C), uc.reg_read(UC_ARM_REG_R2)))
        skip(uc)
    def st(uc, a, s, d):
        if uc.reg_read(UC_ARM_REG_R0) == setter: sets.append(uc.reg_read(UC_ARM_REG_R2))
    e.uc.hook_add(UC_HOOK_CODE, on, begin=on_fn, end=on_fn)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: skip(uc), begin=off_fn, end=off_fn)
    e.uc.hook_add(UC_HOOK_CODE, st, begin=set_fn, end=set_fn)
    def run(ms, step=10):
        for _ in range(ms // step): t[0] += step; e.at(t[0]); X.frame(e)
    def shpad(q):
        e.set_p0(e.r32(MGR + 0xC), 1); e.pad(q); e.set_p0(e.r32(MGR + 0xC), 0)
    # ---- Pattern Settings of Drum 1
    e.btn(4); e.btn(12)
    pat = r0(lab["c_dapat"], 0)
    shpad(24); c1 = r0(lab["c_dacfg"], 0, pat)
    shpad(28); shpad(19); c2 = r0(lab["c_dacfg"], 0, pat)
    f = X.frame(e); e.set_p0(e.r32(MGR + 0xC), 1); fs = X.frame(e); e.set_p0(e.r32(MGR + 0xC), 0)
    check(c1 == 0x80 and c2 == 0x80 | 4 << 3 | 0 and f[24] == D.COL_ON and fs[24] == D.COL_ON and fs[28] == D.COL_ON and fs[19] == D.COL_ON,
          f"Drum 1's Pattern Settings, Shift: pad 25 on, pad 29 up, pad 20 1/16 ({c1:#x}, {c2:#x}; LEDs {f[24]:#x} / {fs[24]:#x} {fs[28]:#x} {fs[19]:#x})")
    shpad(21); c3 = r0(lab["c_dacfg"], 0, pat)
    check(c3 == 0x80 | 6 << 3, f"pad 22: 1/8 ({c3:#x})")
    e.btn(0); e.btn(12); np_ = r0(arl["c_arcfg"], 0, 0); shpad(24)
    check(r0(arl["c_arcfg"], 0, 0) == np_ ^ 0x80 and r0(lab["c_dacfg"], 0, pat) == c3, "Synth 1's Pattern Settings, Shift + pad 25: the note arpeggiator's (the drum's untouched)")
    shpad(24)
    # ---- Drum 1's Preset view, stopped
    e.btn(4); e.btn(8)
    view = e.r32(e.r32(MGR + 0x2C) + 0x8C)
    selst = e.r32(dp + 0x5C)
    sel = lambda: (e.call(0x0803542C, selst, 0), e.r8(e.uc.reg_read(UC_ARM_REG_R0)))[1]
    X.frame(e); hits.clear(); sets.clear()
    e.call(T.PRESS, MGR, 0, 90, maxins=8_000_000); run(30)
    s_first = list(sets); h_first = list(hits); sets.clear(); hits.clear()
    t0 = t[0]; e.call(T.PRESS, MGR, 3, 110, maxins=8_000_000); after = list(sets)
    run(760)
    rel = [(h - t0, v) for h, v in hits]
    check(e.r8(MGR + 0x152) == 36 and not after, f"pad 4 held with pad 1: not the stock's (no sample set at the press: {after})")
    check(len(rel) == 4 and all(abs(r - rel[0][0] - 250 * i) <= 11 for i, (r, _) in enumerate(rel)) and [v for _, v in rel] == [90, 110, 90, 110] and sets[:4] == [0, 3, 0, 3],
          f"the arpeggio at 1/8 (250 ms at 120 BPM): samples {sets[:6]}, hits {rel}")
    st_ = r0(lab["c_dast"])
    check(st_ and e.r8(st_) == 2 and e.r8(st_ + D.S_FL) & 1, f"the state: 2 samples, running")
    sets.clear(); hits.clear()
    e.call(T.RELEASE, MGR, 3, maxins=8_000_000); e.call(T.RELEASE, MGR, 0, maxins=8_000_000); run(300)
    check(not hits and sets == [sel()] and e.r8(st_) == 0, f"let go: the drum's selected sample again ({sets}, selection {sel()}), nothing more")
    # ---- playing: the grid (the pattern's own hits out of the way)
    pbase = e.r32(dp + 0x48) + 0x6A8 * pat; e.uc.mem_write(pbase, bytes(32))
    e.call(T.PRESS, MGR, 0, 90, maxins=8_000_000); e.call(T.PRESS, MGR, 3, 100, maxins=8_000_000); X.frame(e)
    e.transport(1); hits.clear(); sets.clear()
    slot2 = e.r32(D.DP_VT + 8) & ~1
    seen = []
    for stp in range(4):
        for m in range(6):
            n0 = len(hits); e.call(slot2, dp, pat, stp, m, maxins=3_000_000); X.frame(e)
            if len(hits) > n0: seen.append((stp, m))
    e.call(int(man["report"]["drumarp"]["labels"]["c_daset"], 16), 0, pat, 0x80 | 2 << 3)              # 1/32
    seen2 = []
    for stp in range(2):
        for m in range(6):
            n0 = len(hits); e.call(slot2, dp, pat, stp, m, maxins=3_000_000)
            if len(hits) > n0: seen2.append((stp, m))
    check(seen == [(0, 0), (2, 0)], f"playing, 1/8: micro step 0 of every other step ({seen})")
    check(seen2 == [(0, 0), (0, 3), (1, 0), (1, 3)], f"1/32: micro steps 0 and 3 ({seen2})")
    e.transport(0)
    e.call(T.RELEASE, MGR, 3, maxins=8_000_000); e.call(T.RELEASE, MGR, 0, maxins=8_000_000); run(50)
    # ---- off: the stock's; another view: over
    e.call(lab["c_daset"], 0, pat, 0); X.frame(e); hits.clear()
    e.call(T.PRESS, MGR, 0, 90, maxins=8_000_000); e.call(T.PRESS, MGR, 3, 100, maxins=8_000_000); run(300)
    check(len(hits) == 0 and e.r8(st_) == 0, f"the arpeggiator off: two pads held = the stock's, no arpeggio ({hits})")
    e.call(T.RELEASE, MGR, 3, maxins=8_000_000); e.call(T.RELEASE, MGR, 0, maxins=8_000_000)
    e.call(lab["c_daset"], 0, pat, 0x80 | 4 << 3)
    e.call(T.PRESS, MGR, 0, 90, maxins=8_000_000); e.call(T.PRESS, MGR, 3, 100, maxins=8_000_000); run(50)
    e.btn(0); run(260)
    check(e.r8(st_) == 0, "another view: the arpeggio over after 200 ms")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
