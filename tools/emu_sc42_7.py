"""SC42.7 ARM tests (after SC42.6 on the device, 2026-10-16), through the controller and the real LED task with the clock moving:
  * MIDI 1's Preset view, the engine on: pad 29 (the chain order) in the VCA / VCF page's colours (dim / bright);
  * Synth 1's step-drummer: an empty pair shows 0 and starts from 0 (it showed and started from macro 1's position);
  * the transposition: one degree every 8 knob units (MIDI from 64, a synth from 0), the player's notes and the model agree; with the toggle on,
    page 1's pitch destination no longer moves the own synth's oscillators (off: as before);
  * pads 31 / 32 of the Micro Step view: the same toggle again = off (no selector), the other one = the old one off and the new one on, pad 31 with
    both off = the selector (a length chosen = on);
  * the rollers with the transport stopped: a roller of micro step 1 held = Drum 1 every step (125 ms at 120 BPM) from the first frame; one of
    micro step 4 = half a step later; let go: nothing more; playing: the LED task leaves them to the sequencer.

    python tools/emu_sc42_7.py SC42.7.bin SC42.7_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import vcf21 as V  # noqa: E402
import rollers as R  # noqa: E402
import drumnote as DN  # noqa: E402
DN.MIRROR = True

MGR, KB = T.MGR, X.KB


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    pl = {k: int(v, 16) for k, v in man["report"]["sdpv"]["labels"].items()}

    # ---- MIDI 1: pad 29, the transposition's scale, the pitch destination with the toggle
    e = X.EP(img, man)
    e.btn(2); e.btn(8)
    for _ in range(2): e.pad(26)
    f = X.frame(e); p0 = f[28]
    e.pad(28); f = X.frame(e); p1 = f[28]; e.pad(28)
    check((p0, p1) == (V.COL_PAGE[0][1], V.COL_PAGE[0][0]), f"pad 29 (the chain order): the VCA / VCF page's colours, dim / bright ({p0:#x}, {p1:#x})")
    e.pad(29)
    pat = e.r0(e.vl["c_sdpat"], 0)
    lane = lambda s: e.r0(e.vl["c_sdlna"], pat, s)
    ks = []
    e.call(pl["c_pvset"], 0, 0x80)
    for v in (64, 68, 80, 44, 127, 0):
        e.uc.mem_write(lane(3), bytes([v] * 6)); k = e.r0(pl["c_pvk"], 0, 3); ks.append(k - (1 << 32) if k >= 1 << 31 else k)
    check(ks == [0, 1, 2, -3, 8, -8], f"MIDI: (value - 64) / 8 degrees, rounded ({ks})")
    gf = e.r0(int(man["report"]["sc17"]["labels"]["c_gfst"], 16)); h0 = e.r0(e.vl["c_sdhalf"], 0)
    e.uc.mem_write(gf + V.SD_AUD, bytes([h0 + 1])); e.uc.mem_write(lane(h0), bytes([80] * 6))
    on = e.r1(e.vl["c_sdfx"], 0, 0, 16)
    e.call(pl["c_pvset"], 0, 0); off = e.r1(e.vl["c_sdfx"], 0, 0, 16)
    check(on == 0 and off == 3, f"the pitch destination (both oscillators), +16: the toggle on = the oscillators untouched ({on}), off = +3 semitones ({off})")
    del e; gc.collect()

    # ---- Synth 1's step-drummer: from 0
    e = X.EP(img, man)
    gst = int(man["report"]["sc14"]["labels"]["c_gst"], 16)
    for _ in range(3):
        e.btn(0)
        if e.r8(MGR + 0x152) == 0 and e.r8(e.r0(gst) + V.S_PAINT) & V.F_SRC: break
    e.pad(29); f = X.frame(e)
    m1 = e.r0(V.GETTER, 0, 174)
    check(all(x >> 8 == 2 for x in f[60:68]), f"an empty pair shows 0 (macro 1 at {m1}; LEDs {[hex(x) for x in f[60:68]]})")
    h0 = e.r0(e.vl["c_sdhalf"], 0); e.knob(0, 5)
    check(e.lane(2, h0, 0) == 5, f"knob 1: from 0 (+5 = {e.lane(2, h0, 0)})")
    pat = e.r0(e.vl["c_sdpat"], 2); ks = []
    e.call(pl["c_pvset"], 2, 0x80)
    for v in (0, 3, 4, 16, 127):
        e.uc.mem_write(e.r0(e.vl["c_sdlna"], pat, 5), bytes([v] * 6)); ks.append(e.r0(pl["c_pvk"], 2, 5))
    check(ks == [0, 0, 1, 2, 16], f"a synth: value / 8 degrees, rounded ({ks})")
    del e; gc.collect()

    # ---- playback with the new scale
    from emu_arp import EA
    e = EA(img, man)
    vl = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
    r0 = lambda fn, *a: (e.call(fn, *a, maxins=4_000_000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    p = e.playing(0); base = e.settings(0, p) - 0x380
    notes = [60, 64, 71, 120]
    steps = bytearray()
    for s in range(8):
        n = notes[s] if s < len(notes) else None
        steps += bytes([1 if n else 0, 7, 0, 0]) + (bytes([n, 3, 0, 100]) if n else bytes([0, 0, 0, 0x60])) + bytes([0, 0, 0, 0x60]) * 5
    e.uc.mem_write(base, bytes(steps)); e.setpat(0, p, 0, 7); e.setp(e.r32(0x20040200 + 0x10), 1, bytes([3]))
    pt, lofs = r0(vl["c_sdpat"], 2), r0(vl["c_sdlofs"], 2)
    vals = (16, 0, 24, 60)
    for s, v in enumerate(vals): e.uc.mem_write(r0(vl["c_sdlna"], pt, s) + lofs, bytes([v] * 6))
    root = e.r8(e.r32(KB + 0x10)); mask = e.r32(e.r32(KB + 0xC) + 4)
    ins = lambda r: (mask >> 2 * (r % 12)) & 3 == 0
    e.call(pl["c_pvset"], 2, 0x80)
    e.transport(1); e.ons.clear(); e.run(p, 4); got = [n for _, n, *_ in e.ons]
    want = [X.model_deg(n, (v + 4) // 8, root, ins) if (v + 4) // 8 else n for n, v in zip(notes, vals)]
    check(got == want, f"Synth 1 playing, the toggle: {notes} with the values {vals} = {got} (model {want})")
    del e; gc.collect()

    # ---- pads 31 / 32 of the Micro Step view
    import stepgate as SG
    from emu_arp import EA
    e = EA(img, man)
    lab = {k: int(v, 16) for k, v in man["report"]["stepgate"]["labels"].items()}
    from emu_arp import CONT
    e.set_p0(e.r32(CONT + 0x188), 0); e.press(0); e.release(0); e.transport(0)
    e.press(11); e.release(11); e.press(11); e.release(11)
    tail = e.r32(T.LZ.SESSION_OBJ + 0x14) + 0x27024
    def st():
        e.call(lab["c_sgfget"], 0); fx = e.uc.reg_read(UC_ARM_REG_R0); e.call(lab["c_sgon"], 0); ho = e.uc.reg_read(UC_ARM_REG_R0)
        return fx, ho, e.r8(tail + SG.O_FL + 6)
    seq = []
    e.w32(0x2000081C, 400000)
    for q in (30, 19, 30, 31, 31, 31, 30, 21, 31, 30):
        e.pad(q); seq.append(st())
    want = [(0, 0, 1), (0x84, 0, 0), (0x04, 0, 0), (0x04, 1, 0), (0x04, 0, 0), (0x04, 1, 0), (0x04, 0, 1), (0x86, 0, 0), (0x06, 1, 0), (0x06, 0, 1)]
    check(e.r8(MGR + 0x152) == 8 and seq == want, f"Micro Step: pad 31 = the selector, pad 20 = 4 steps on, pad 31 = off; pad 32 on / off; pad 32 on, pad 31 = it off and the selector, "
          f"pad 22 = 6 steps; pad 32 = the fixed length off and it on; pad 31 = it off and the selector ({[(hex(a_), b_, c_) for a_, b_, c_ in seq]})")
    f = e.pads()
    check(f[16:22] == [SG.COL_ON] * 6 and f[22] == SG.COL_OFF, f"the selector shows the length kept (6) ({[hex(x) for x in f[16:24]]})")
    e.pad(16 + 9); f = e.pads()
    check(st() == (0x8A, 0, 0) and f[30] == SG.COL_FIX and f[31] == SG.COL_OFF, f"pad 26 in the selector: 10 steps on; pad 31 orange, pad 32 dim ({st()}, {f[30]:#x}, {f[31]:#x})")
    del e; gc.collect()

    # ---- the rollers with the transport stopped
    e = T.EL(img); t = [300000]; e.at(t[0]); e.transport(0)
    hits = []
    iface = e.r32(R.DP0 + 0x4C); ivt = e.r32(iface)
    def on(uc, a, s, d): hits.append((e.r32(0x2000081C), uc.reg_read(UC_ARM_REG_R1))); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    def skip(uc, a, s, d): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, on, begin=e.r32(ivt) & ~1, end=e.r32(ivt) & ~1)
    e.uc.hook_add(UC_HOOK_CODE, skip, begin=e.r32(ivt + 4) & ~1, end=e.r32(ivt + 4) & ~1)
    e.btn(4)
    for _ in range(3):
        if e.r8(MGR + 0x152) == 42: break
        e.btn(9)
    def run(ms, step=10):
        for _ in range(ms // step): t[0] += step; e.at(t[0]); X.frame(e)
    X.frame(e)
    pad = lambda m: [q for q in range(24) if R.tables()[0][q] == 0 and R.tables()[1][q] == m][0]
    hits.clear(); t0 = t[0]
    e.call(T.PRESS, MGR, pad(0), 100, maxins=8_000_000)
    run(520)
    rel = [h - t0 for h, _ in hits]
    check(e.r8(MGR + 0x152) == 42 and len(rel) == 5 and rel[0] <= 10 and all(abs(r - rel[0] - 125 * i) <= 11 for i, r in enumerate(rel)), f"stopped, micro step 1 held: Drum 1 every step from the start ({rel} ms)")
    e.call(T.RELEASE, MGR, pad(0), maxins=8_000_000); hits.clear(); run(300)
    check(not hits, "let go: nothing more")
    t1 = t[0]; e.call(T.PRESS, MGR, pad(3), 100, maxins=8_000_000); run(300)
    rel = [h - t1 for h, _ in hits]
    check(len(rel) == 2 and abs(rel[0] - 72) <= 10 and abs(rel[1] - 197) <= 10, f"micro step 4: half a step later ({rel} ms)")
    e.transport(1); hits.clear(); run(300)
    check(not hits, "playing: the LED task plays none (the sequencer's)")
    e.call(T.RELEASE, MGR, pad(3), maxins=8_000_000)
    del e; gc.collect()
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
