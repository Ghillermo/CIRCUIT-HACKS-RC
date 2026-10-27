"""SC36.1 ARM tests (build_sc17.use_glitch2, vcf21.use_fxseq2) through the real routes, after the SC36 tests:

    python tools/emu_sc36_1.py SC36.1.bin SC36.1_manifest.json
  * every SC36 test (emu_sc36) except the FX sequencer's zones (now slots);
  * Master FX: pad 31 held + pad 27 = slot 1 is the Glitch with a copy of K1..K4; that slot plays it while held (K1..K4 from the slot, the magic), lit in the Glitch's colour;
    Shift + pad 27 with pad 31 held assigns nothing;
  * the FX sequencer: its pair knob moves one value per turn in 0..6; c_fsqbits = the slot of the value (1..6 -> slots 0..5); through the Master FX tick: a slot of the Gater
    switches the Gater on and loads its copy of the knobs, a slot of the Glitch / pad 31 switches the Glitch on; c_slotcol = the colour of what a slot holds.
  * SC36.2 / SC362S (vcf21.use_fxseq3, chosen by the marker in the manifest): the pair keeps a position 0..96 moved by the knob delta, the value = the nearest 0..6
    (16 units each; many small events no longer race to the ends), and the knob LED takes the colour of that slot.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc36 as T36  # noqa: E402
from emu_sc36 import B, V, VD, GD, G, E20, TMPL, TICK, KG  # noqa: E402
B.use_glitch2(); V.use_fxseq2()
from unicorn.arm_const import UC_ARM_REG_R0  # noqa: E402


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    check(man["report"]["sc17"].get("glitch2") is True, "manifest: glitch2")
    v3 = man.get("marker", "") not in ("SC36", "SC36.1", "SC361S")                   # the FX sequencer knob of SC36.2 (use_fxseq3) in every later build
    if v3: V.use_fxseq3()
    U = V.FSQ_U if v3 else 1                                                       # knob units / lane units per value
    L17 = {k: int(v, 16) for k, v in man["report"]["sc17"]["labels"].items()}
    pal = [(int(x, 16), int(y, 16)) for x, y in man["report"]["sc17"]["pal_codes"]]

    # ================================================================ Master FX: the Glitch assigned to a bottom pad
    x = T36.T34.E7(img, man); x.grid(); x.setsp(); x.uc.mem_write(x.blk + B.S_JF, b"\0\0"); x.w32(x.blk + B.S_SMT, 0); x.uc.mem_write(x.blk + B.S_SLOT, bytes(28))
    def ftick(ms):
        x.w32(TICK, ms); x.dw.clear(); x.call(x.L["c_fxtick"], maxins=3_000_000); return list(x.dw)
    stype = lambda j: (lambda b_: None if not b_[3] >> 7 else (b_[0] >> 7 | (b_[1] >> 7) << 1 | (b_[2] >> 7) << 2, [v & 0x7F for v in b_]))(x.blkb(B.S_SLOT + 4 * j, 4))
    x.uc.mem_write(x.blk + KG, bytes([90, 20, 30, 40])); ftick(500)
    x.pad(B.GL_PAD); x.pad(26); x.rel(26); x.rel(B.GL_PAD)
    check(stype(1) == (B.GL_SEL, [90, 20, 30, 40]), f"pad 31 held + pad 27: slot 1 = the Glitch with K1..K4 {stype(1)}")
    x.pad(B.GL_PAD); x.pad(27, shift=True); x.rel(27); x.rel(B.GL_PAD)
    check(stype(2) is None, "with Shift: nothing assigned")
    ftick(600)
    x.uc.mem_write(x.blk + KG, bytes([1, 2, 3, 4]))
    x.pad(26); w = ftick(700); d = dict(w)
    check(x.blkb(B.S_SEL)[0] == B.GL_SEL and [d.get(GD.GARM + 1 + k) for k in range(4)] == [90, 20, 30, 40] and [v for a, v in w if a == GD.GARM][-1:] == [GD.GMAGIC],
          f"slot pad 27: the Glitch with the slot's knobs, the magic ({[(hex(a), v) for a, v in w if a >= GD.GARM]}, S_SEL {x.blkb(B.S_SEL)[0]})")
    g = x.gleds()
    check(g[26] == B.GL_ON, f"slot pad 27 lit in the Glitch's colour ({g[26]:#x})")
    x.rel(26); w = ftick(800)
    check((GD.GARM, 0) in w and x.gleds()[26] == B.GL_DIM, "released: off, dim")
    # two bottom pads with the Glitch and different knobs held together (SC37.3 on the device: one's knobs copied into the other)
    gl3 = man["report"]["sc17"].get("glitch3") is True
    x.uc.mem_write(x.blk + KG, bytes([11, 22, 33, 44])); ftick(900)
    x.pad(B.GL_PAD); x.pad(28); x.rel(28); x.rel(B.GL_PAD)
    check(stype(3) == (B.GL_SEL, [11, 22, 33, 44]), f"pad 31 held + pad 29: slot 3 = the Glitch with K1..K4 {stype(3)}")
    x.pad(26); ftick(1000); x.pad(28); d = dict(ftick(1100))
    if gl3:
        check(stype(1) == (B.GL_SEL, [90, 20, 30, 40]) and stype(3) == (B.GL_SEL, [11, 22, 33, 44]), f"slots 27 and 29 held together: each keeps its knobs ({stype(1)}, {stype(3)})")
        check([d.get(GD.GARM + 1 + k) for k in range(4)] == [11, 22, 33, 44], f"the last one pressed plays ({[d.get(GD.GARM + 1 + k) for k in range(4)]})")
        x.rel(28); w = ftick(1200); d = dict(w)
        check([d.get(GD.GARM + 1 + k) for k in range(4)] == [90, 20, 30, 40] and (GD.GARM, 0) not in w and x.blkb(KG)[0] >> 7,
              f"pad 29 released, pad 27 still held: the Glitch plays on with pad 27's knobs ({[(hex(a), v) for a, v in w if a >= GD.GARM]})")
        x.rel(26); w = ftick(1300)
        check((GD.GARM, 0) in w and stype(1) == (B.GL_SEL, [90, 20, 30, 40]) and stype(3) == (B.GL_SEL, [11, 22, 33, 44]), "both released: off, the slots unchanged")
        x.pad(B.GL_PAD); x.pad(0); x.rel(0); x.rel(B.GL_PAD)
        check(stype(B.GL_SLOT) is None, "pad 31 held + a top effect: pad 31 is not a slot (nothing assigned to it)")
        g = x.gleds()
        check(g[5] == 0x6B and pal[5] == (0x6A, 0x6B), f"Vinyl (pad 6) in peach: {g[5]:#x}, its codes {pal[5]}")
    else:
        check(stype(3) == (B.GL_SEL, [90, 20, 30, 40]), f"(the fault of the device) slot 29 pressed while slot 27 plays: it gets slot 27's knobs {stype(3)}")
        x.rel(28); x.rel(26); ftick(1200)
    # slot 0 = the Gater (pad 1 held + pad 26) for the sequencer below
    del x; gc.collect()

    # ================================================================ the FX sequencer (MIDI 1)
    e = E20(img, man)
    for _ in range(30): e.vtick()
    pad = lambda p: (e.padr(p), e.rel(p))
    e.btn(2); e.track(2); e.btn(8)
    for _ in range(5): pad(V.PAD_OSC)                                              # off -> line -> osc -> VA -> granular -> FX sequencer
    def r0(fn, *a): e.call(fn, *a); return e.uc.reg_read(UC_ARM_REG_R0)
    check(r0(e.vl["c_fsq"], 0) == 1, "MIDI 1 in the FX sequencer state")
    pad(V.PAD_SD)                                                                  # its view: the knobs are the pairs
    pat = r0(e.vl["c_sdpat"], 0)
    lane = lambda st: e.r8(r0(e.vl["c_sdlna"], pat, st))
    h0 = r0(e.vl["c_sdhalf"], 0)
    if v3:
        seq = []
        for d in (5, 4, 16): e.knob_raw(0, d); seq.append(lane(h0))
        for _ in range(8): e.knob_raw(0, 20)
        seq.append(lane(h0)); e.knob_raw(0, -20); seq.append(lane(h0))
        check(seq == [5, 9, 25, 96, 76], f"the pair knob: a position 0..96 moved by the delta ({seq})")
        for _ in range(100): e.knob_raw(0, -1)
        for _ in range(30): e.knob_raw(0, 1)
        check(lane(h0) == 30, f"100 events down, 30 up: position 30 = value 2, not the end ({lane(h0)})")
        e.knob_raw(0, -100)
    else:
        e.knob_raw(0, 5)
        v1 = lane(h0); e.knob_raw(0, 9); v2 = lane(h0)
        for _ in range(8): e.knob_raw(0, 3)
        v3_ = lane(h0); e.knob_raw(0, -20); v4 = lane(h0)
        check((v1, v2, v3_, v4) == (1, 2, 6, 5), f"the pair knob: one value per turn, 0..6 ({v1}, {v2}, {v3_}, {v4})")
    stp = r0(e.vl["c_sdeng"], 0, 1)
    def setstep(st, notes, v):
        e.uc.mem_write(r0(e.vl["c_sdstp"], pat, st), bytes([notes])); e.uc.mem_write(r0(e.vl["c_sdlna"], pat, st), bytes([v]))
    e.call(V.PARAM_GET, V.PLAY_STORE, 0); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), b"\x01")
    e.uc.mem_write(stp, b"\x05")
    cases = ((16, 1), (32, 2), (24, 2), (96, 1 << 5), (0, 0), (7, 0), (97, 0), (127, 0)) if v3 else ((1, 1), (2, 2), (6, 1 << 5), (0, 0), (7, 0), (40, 0))
    for v, want in cases:
        setstep(5, 1, v)
        check(r0(e.vl["c_fsqbits"]) == want, f"value {v}: slots {r0(e.vl['c_fsqbits']):#x} (want {want:#x})")
    # through the Master FX tick: slot 0 = the Gater (assigned here directly), slot 1 = the Glitch, slot 5 = pad 31
    gf = r0(L17["c_gfst"])
    e.uc.mem_write(gf + B.S_SLOT, bytes([0x0A, 0x14, 0x1E, 0xA8]))                 # slot 0: effect 0 (bits 0), assigned, knobs 10, 20, 30, 40
    e.uc.mem_write(gf + B.S_SLOT + 4, bytes([0x80 | 50, 0x80 | 60, 0x80 | 70, 0x80 | 80]))   # slot 1: effect 7 = the Glitch
    e.uc.mem_write(gf + B.S_KNOB, bytes([1, 1, 1, 1]))
    FXT = int(man["report"]["sc17"]["labels"]["c_fxtick"], 16)
    def fxt():
        nx = e.s18["svc_next"]; e.s18["svc_next"] = 0
        e.dw.clear(); e.call(FXT, maxins=3_000_000); e.s18["svc_next"] = nx
        return [(x_[2], x_[1]) for x_ in e.dw if len(x_) == 3]
    setstep(5, 1, U); w = fxt()
    fx = [v for a, v in w if a == G.FX_ON]
    check(fx and fx[-1] == B.FXBITS[0] and list(e.uc.mem_read(gf + B.S_KNOB, 4)) == [10, 20, 30, 40], f"value 1: slot 0 = the Gater on (FX_ON {fx}), its copy of the knobs loaded")
    setstep(5, 1, 2 * U); w = fxt()
    gm = [v for a, v in w if a == GD.GARM]; d = dict(w)
    check(gm and gm[-1] == GD.GMAGIC and [d.get(GD.GARM + 1 + k) for k in range(4)] == [50, 60, 70, 80], f"value 2: slot 1 = the Glitch with the slot's knobs ({gm})")
    setstep(5, 1, 6 * U); w = fxt(); gm = [v for a, v in w if a == GD.GARM]
    check(gm == [] or gm[-1] == GD.GMAGIC, "value 6: pad 31 = the Glitch (still on)")
    setstep(5, 0, 6 * U); w = fxt(); gm = [v for a, v in w if a == GD.GARM]
    check(gm and gm[-1] == 0, "no note: off")
    fsqdef = "fq_t" in man["report"]["sc17"]["labels"]                             # SC48 (build_sc17.use_fsqdef): an empty slot = its default effect
    if fsqdef:
        setstep(5, 1, 3 * U); w = fxt(); fx = [v for a, v in w if a == G.FX_ON]
        check(fx and fx[-1] == B.FXBITS[2], f"(SC48) value 3: the empty slot 2 = the top pad of its column, Digitise (FX_ON {fx})")
        setstep(5, 0, 3 * U); fxt()
    cols = [r0(L17["c_slotcol"], j) for j in range(6)]
    check(cols[0] == pal[0][0] and cols[1] == B.GL_ON and cols[2] == (pal[2][0] if fsqdef else 0x03) and cols[5] == B.GL_ON,
          f"c_slotcol: Gater {cols[0]:#x}, the Glitch {cols[1]:#x}, empty {cols[2]:#x}{' (its default effect)' if fsqdef else ''}, pad 31 {cols[5]:#x}")
    if v3:                                                                         # the knob LEDs (c_sdkleds): pair 0 = slot 0 (the Gater), pair 1 = slot 1 (the Glitch), pair 2 empty
        for st, v in ((r0(e.vl["c_sdhalf"], 0), 16), (r0(e.vl["c_sdhalf"], 2), 30), (r0(e.vl["c_sdhalf"], 4), 0xFF)):
            for k in (0, 1): e.uc.mem_write(r0(e.vl["c_sdlna"], pat, st + k), bytes([v]))
        e.call(V.PARAM_GET, V.PLAY_STORE, 0); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes(1))      # stopped: no pair in white
        BUF = 0x30000000
        try: e.uc.mem_map(BUF, 0x1000)
        except Exception: pass
        e.call(e.vl["c_sdkleds"], 0, BUF); kl = struct.unpack("<8H", bytes(e.uc.mem_read(BUF, 16)))
        check(kl[0] & 0xFF == pal[0][0] and kl[1] & 0xFF == B.GL_ON and kl[2] == 0, f"knob LEDs: Gater {kl[0]:#x}, the Glitch {kl[1]:#x}, empty {kl[2]:#x}")
    if "c_vosc" in man["report"]["vcf20"]["labels"]:                                                                         # pad 28 (one / two oscillators) only with oscillators
        del e; gc.collect()
        e = E20(img, man)
        for _ in range(30): e.vtick()
        e.btn(2); e.track(2); e.btn(8)
        pad = lambda p_: (e.padr(p_), e.rel(p_))
        leds, flips = [], []
        for k in range(6):                                                        # off, line in, oscillator, VA-drum, granular, FX sequencer
            leds.append(e.tleds(TMPL[0])[V.PAD_PAGE])
            before = e.rt(0, V.RT_VEL) & 0x80; pad(V.PAD_PAGE); after = e.rt(0, V.RT_VEL) & 0x80
            flips.append(before != after)
            if before != after: pad(V.PAD_PAGE)                                   # back
            pad(V.PAD_OSC)
        names = ("off", "line", "osc", "VA", "granular", "FX seq")
        check([x != 0 for x in leds] == [False, False, True, True, False, False], f"pad 28 lit only with oscillators ({dict(zip(names, [hex(x) for x in leds]))})")
        check(flips == [False, False, True, True, False, False], f"pad 28 toggles one / two oscillators only with oscillators ({dict(zip(names, flips))})")
    print("SC36.1 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
