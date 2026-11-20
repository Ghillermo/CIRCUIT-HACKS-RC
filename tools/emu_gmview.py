"""Alpha 7.16 test (tools/gmview.py, the global macro view), through the controller's entries (0x08033320 / 0x0803381A / 0x08033282 /
0x080332FE / 0x08033848) and the LED task frame:
  * Mixer held + Patterns = on (the Mixer comes up, Patterns' press and release go nowhere); the frame: pads 1-8 in the stock's dim track colours,
    Patterns / Mixer white;
  * a knob with no tracks: nothing called, it becomes the selected one (dim white LED);
  * pads 1, 3, 5 = Synth 1, MIDI 1, Drum 1 linked to it (bright), the pads not passed on;
  * the knob again: the knob handlers of those three tracks (slot 4, the same knob and delta), MIDI 1 on page 4 for the call and its page put back;
    the view's own knob entry not reached; its LED = Synth 1's colour, full;
  * the master filter knob, Play: the stock's (the view stays); a pad pressed in the view and released after it closed: dropped;
  * Patterns held + Mixer = off; on again, Mixer alone (tapped) = off; Note closes it too;
  * save / load: the masks into MIDI 2's pattern 8 settings + 8 (0xD7, masks, sum ^ 0xA5) and back.

    python tools/emu_gmview.py firmware/a7.16/circuittracks-4486-A7.16.bin firmware/a7.16/manifest.json
"""
import gc, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_LR, UC_ARM_REG_SP
import emu_sc48_8 as S
import emu_sc42_6 as X
import jumpseq as J
import gmview as G
from emu_sc05 import STOP

MGR = S.MGR


def main(a):
    img, man = Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())
    R = man["report"]
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in R["gmview"]["labels"].items()}
    P = {k: int(v, 16) for k, v in R["gmview"]["prev"].items()}
    rows = "c_gmsum" in L                                                              # Alpha 7.17: level / reverb / delay rows
    if rows: G.use_rows()
    vpage = int(R["vcf20"]["labels"]["c_vpage"], 16)
    B = 0x08010000
    ins = struct.unpack_from("<H", img, vpage - B)[0]
    assert ins & 0xF800 == 0x4800 and (ins >> 8) & 7 == 2, hex(ins)                  # ldr r2, [pc, #imm]
    vbase = struct.unpack_from("<I", img, ((vpage + 4) & ~3) + 4 * (ins & 0xFF) - B)[0]
    e = S.ET(img, man); uc = e.uc
    def page(t): return ((e.r8(vbase + 8 * t + 0x3B) >> 1) & 3) | ((e.r8(vbase + 0x4A) >> (4 * t)) & 1) << 2
    cols = struct.unpack_from("<17H", img, G.COLS - B)
    calls, hits = [], {"knob": 0, "padup": 0, "pad": 0}
    slot4 = {struct.unpack_from("<I", img, vt + 0x10 - B)[0] & ~1 for vt in (0x0805AC64, 0x0805AADC)}
    def on_slot4(u, addr, size, ud):
        h_ = u.reg_read(UC_ARM_REG_R0)
        calls.append((h_, u.reg_read(UC_ARM_REG_R1), u.reg_read(UC_ARM_REG_R2), page(0), page(1)))
    for s in slot4: uc.hook_add(UC_HOOK_CODE, on_slot4, begin=s, end=s)
    for k in ("knob", "padup", "pad"):
        uc.hook_add(UC_HOOK_CODE, lambda u, ad, sz, ud, k=k: hits.__setitem__(k, hits[k] + 1), begin=P[k], end=P[k])
    t = [500000]
    def at(ms): t[0] += ms; e.w32(J.HAL_TICK, t[0])
    def drain():
        r = e.r32(0x200069F4)
        for k in range(e.r8(r + 0x18)): uc.mem_write(e.r32(e.r32(e.r32(r + 0x14) + 4 * k) + 0x10), bytes(4))
    def press(b_): drain(); e.call(0x08033320, MGR, b_, maxins=20_000_000); at(20)
    def release(b_): drain(); e.call(0x0803381A, MGR, b_, maxins=20_000_000); at(20)
    def pad(p): drain(); e.call(0x08033282, MGR, p, 100, maxins=20_000_000); at(10)
    def padup(p): drain(); e.call(0x080332FE, MGR, p, maxins=20_000_000); at(10)
    def knob(k, d): drain(); e.call(0x08033848, MGR, k, d & 0xFFFFFFFF, maxins=40_000_000); at(10)
    on = lambda: e.r8(G.GM + G.O_ON)
    mask = lambda k: e.r8(G.GM + G.O_M + k)
    H = [e.r32(G.CONT + G.HANDLERS + 4 * k) for k in range(8)]

    at(0); press(0); release(0); X.frame(e)
    p0 = (page(0), page(1))
    press(14); press(13); release(13); release(14); f = X.frame(e)
    view = e.r32(MGR + 0x6C)
    check(on() == 1 and view and e.r32(view) == 0x0805A668, f"Mixer held + Patterns: on, the Mixer underneath (on {on()}, view vtable {e.r32(view):#x})")
    if rows:
        check(f[:32] == [cols[9 + k % 8] for k in range(32)] and f[45] == G.COL_WHITE and f[46] == G.COL_WHITE,
              f"  the four rows of pads in the dim track colours, Patterns / Mixer white ({[hex(x) for x in f[:9]]})")
    else:
        check(f[:8] == [cols[9 + k] for k in range(8)] and f[45] == G.COL_WHITE and f[46] == G.COL_WHITE and all(x == 0 for x in f[8:32]),
              f"  pads 1-8 dim track colours, 9-32 dark, Patterns / Mixer white ({[hex(x) for x in f[:8]]})")
    calls.clear(); hits["knob"] = 0
    knob(2, 3); f = X.frame(e)
    check(not calls and hits["knob"] == 0 and e.r8(G.GM + G.O_LAST) == 2 and f[62] == G.COL_WHITE | G.BR_IDLE << 8,
          f"K3 with no tracks: nothing called, selected, LED dim white ({hex(f[62])})")
    hits["pad"] = 0
    for p in (0, 2, 4): pad(p); padup(p)
    f = X.frame(e)
    check(mask(2) == 0x15 and hits["pad"] == 0 and [f[k] for k in range(8)] == [cols[1 + k] if k in (0, 2, 4) else cols[9 + k] for k in range(8)],
          f"pads 1, 3, 5: Synth 1, MIDI 1, Drum 1 linked to K3 (mask {mask(2):#x}), shown bright, not passed on")
    calls.clear(); hits["knob"] = 0
    knob(2, 5); f = X.frame(e)
    got = [(H.index(c[0]) if c[0] in H else hex(c[0]), c[1], c[2]) for c in calls]
    check(got == [(0, 2, 5), (2, 2, 5), (4, 2, 5)], f"K3 +5: the knob handlers of Synth 1, MIDI 1, Drum 1, same knob and delta ({got})")
    mid = [c[3] for c in calls if c[0] == H[2]]
    check(mid == [G.MIDI_PAGE] and (page(0), page(1)) == p0, f"  MIDI 1 on page 4 for its call ({mid}), its page put back ({(page(0), page(1))} = {p0})")
    check(hits["knob"] == 0 and f[62] == cols[1] | G.BR_SEL << 8, f"  the view's knob entry not reached; LED = Synth 1's colour, full ({hex(f[62])})")
    if rows:
        from unicorn.arm_const import UC_ARM_REG_R0 as R0_
        def pget(store, k): e.call(0x0803542C, store, k, maxins=2_000_000); return e.r8(uc.reg_read(R0_))
        sub_r, sub_d = e.r32(G.FXV + 0x10), e.r32(G.FXV + 0xC)
        lvl, rev, dly = (lambda t: pget(e.r32(G.MIXV + 0x6C), t)), (lambda t: pget(e.r32(sub_r + 0x14), t)), (lambda t: pget(e.r32(sub_d + 0x14), t))
        seen = []
        uc.hook_add(UC_HOOK_CODE, lambda u, ad, sz, ud: seen.append(("lv", u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1), u.reg_read(UC_ARM_REG_R2),
                    e.r8(G.MIXV + G.MIX_PAGE))), begin=G.MIX_KNOB, end=G.MIX_KNOB)
        fxs = {e.r32(e.r32(sub_r) + 0x10) & ~1, e.r32(e.r32(sub_d) + 0x10) & ~1}
        for s4 in fxs:
            uc.hook_add(UC_HOOK_CODE, lambda u, ad, sz, ud: seen.append(("fx", u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1), u.reg_read(UC_ARM_REG_R2))),
                        begin=s4, end=s4)
        for p_ in (8, 17, 27): pad(p_); padup(p_)
        f = X.frame(e)
        check([mask(8 + 2), mask(16 + 2), mask(24 + 2)] == [0x01, 0x02, 0x08] and f[8] == cols[1] and f[17] == cols[2] and f[27] == cols[4] and f[9] == cols[10],
              f"pads 9, 18, 28: Synth 1's level, Synth 2's reverb, MIDI 2's delay linked to K3, bright ({hex(mask(10))}, {hex(mask(18))}, {hex(mask(26))})")
        uc.mem_write(G.MIXV + G.MIX_PAGE, bytes([1]))
        b0 = (lvl(0), rev(1), dly(3)); seen.clear(); calls.clear()
        knob(2, 5); a0 = (lvl(0), rev(1), dly(3))
        got = [(H.index(c[0]) if c[0] in H else hex(c[0]), c[1], c[2]) for c in calls]
        check(got == [(0, 2, 5), (2, 2, 5), (4, 2, 5)], f"K3 +5: the three main knobs as before ({got})")
        check(("lv", G.MIXV, 0, 5, 0) in seen and ("fx", sub_r, 1, 5) in seen and ("fx", sub_d, 3, 5) in seen and len(seen) == 3,
              f"  the stock level handler (Synth 1, on the levels page), the reverb sub-view (Synth 2), the delay sub-view (MIDI 2) ({[tuple(hex(x) if isinstance(x, int) and x > 255 else x for x in c) for c in seen]})")
        check(a0 == tuple(min(127, v + 5) for v in b0), f"  Synth 1's level, Synth 2's reverb send, MIDI 2's delay send +5 ({b0} -> {a0})")
        check(e.r8(G.MIXV + G.MIX_PAGE) == 1, "  the Mixer's page put back (pans)")
        uc.mem_write(G.MIXV + G.MIX_PAGE, bytes([0]))
        f = X.frame(e)
        check(f[62] == cols[1] | G.BR_SEL << 8, f"  K3's LED = its first track's colour ({hex(f[62])})")
        dim = "ld_bs" in L                                                             # (use_dimled)
        knob(4, 1); f = X.frame(e)                                                     # K5 picked (no links): K3 no longer the picked one
        want = (cols[9] | G.BR_SEL << 8) if dim else (cols[1] | G.BR_ON << 8)
        check(f[62] == want and f[64] == G.COL_WHITE | G.BR_IDLE << 8,
              f"  K5 picked: K3 = Synth 1's {'dim colour, full' if dim else 'colour at a third'} ({hex(f[62])}), K5 dim white ({hex(f[64])})")
        knob(2, 0); f = X.frame(e)
        check(f[62] == cols[1] | G.BR_SEL << 8, f"  K3 picked again: its bright colour ({hex(f[62])})")
    hits["knob"] = 0; knob(8, 4)
    check(hits["knob"] == 1, "the master filter knob: the stock's")
    press(17); release(17)
    check(on() == 1, "Play: the view stays")
    hits["padup"] = 0; pad(6)
    press(13); press(14); release(14); release(13)
    check(on() == 0, "Patterns held + Mixer: off")
    padup(6)
    check(hits["padup"] == 0, "a pad pressed in the view and released after it closed: dropped")
    press(14); press(13); release(13); release(14)
    check(on() == 1, "on again")
    press(14); release(14)
    check(on() == 0, "Mixer alone: off")
    press(14); press(13); release(13); release(14); press(9); release(9)
    check(on() == 0, "Note: off")

    rec = e.r32(0x2003D71C + 0x14)
    if not rec:
        print("skip: no session record in the emulation (save / load)")
    else:
        blk = rec + G.BLK
        for nm, adr in (("save", P["save"]), ("resend", P["resend"])):
            uc.hook_add(UC_HOOK_CODE, lambda u, ad, sz, ud: u.emu_stop(), begin=adr, end=adr)
        def run(lab):
            uc.reg_write(UC_ARM_REG_SP, 0x20047C00); uc.reg_write(UC_ARM_REG_LR, STOP | 1); uc.emu_start(L[lab] | 1, STOP, count=2_000_000)
        run("c_gmsave")
        if rows:
            ms = bytes(mask(k) for k in range(32)); b_ = bytes(uc.mem_read(blk, 36))
            check(b_[0] == G.BSIG2 and b_[1] == (sum(ms) ^ 0xA5) & 0xFF and b_[4:36] == ms and any(ms[8:]),
                  f"save: 0xD8 and the sum in MIDI 2's pattern 8 settings + 4 / 5, the 32 masks at + 8 ({b_.hex()})")
            uc.mem_write(G.GM + G.O_M, bytes(32)); run("c_gmload")
            check(bytes(mask(k) for k in range(32)) == ms, "load: the four rows back")
            uc.mem_write(blk + 1, bytes([b_[1] ^ 1])); run("c_gmload")
            check(all(mask(k) == 0 for k in range(32)), "load: a wrong sum = none linked")
            old = bytes([0x01, 0, 0x30, 0, 0, 0, 0, 0x80])                             # 7.16's block at settings + 8: 0xD7, 8 masks, sum ^ 0xA5
            uc.mem_write(blk, bytes(4) + bytes([G.BSIG]) + old + bytes([(sum(old) ^ 0xA5) & 0xFF]))
            run("c_gmload")
            check([mask(k) for k in range(8)] == list(old) and all(mask(k) == 0 for k in range(8, 32)), "load: a 7.16 project's links into row 1")
            pz = int(R["patchain"]["labels"]["c_pczr"], 16)
            check(struct.unpack_from("<H", img, pz - B)[0] == 0x4770, "patchain: Clear + pattern keeps the settings bytes 4..6 (c_pczr returns at once)")
        else:
            b_ = e.r8s(blk, 10) if hasattr(e, "r8s") else bytes(uc.mem_read(blk, 10))
            want = bytes([G.BSIG]) + bytes(mask(k) for k in range(8)) + bytes([(sum(mask(k) for k in range(8)) ^ 0xA5) & 0xFF])
            check(b_ == want, f"save: the block in MIDI 2's pattern 8 settings + 8 ({b_.hex()})")
            uc.mem_write(G.GM + G.O_M, bytes(8)); run("c_gmload")
            check([mask(k) for k in range(8)] == list(want[1:9]), "load: the masks back")
            uc.mem_write(blk + 9, bytes([want[9] ^ 1])); run("c_gmload")
            check([mask(k) for k in range(8)] == [0] * 8, "load: a wrong sum = none linked")
    del e; gc.collect()
    print(f"{man.get('marker')} GMVIEW RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:]) else 0)
