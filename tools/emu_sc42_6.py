"""SC42.6 ARM tests (the step-drummer's page 2 and the pitch-vel toggle, tools/sdpv.py; cscale.use_mutroot), through the controller and the real
LED task:
  * MIDI 1 with its own engine: pad 30 dim with the step-drummer off (dark in SC42.5), bright on; in its view pad 32 = the toggle (dim / bright
    green, the block in the session tail), out of the view pad 32 dark again;
  * page 2 (Octave v): pads 17-24 = its destination (dim, the chosen one bright; the same pad again = none); knob 1 writes lane 1 of both steps of
    the pair (from 64), the velocity untouched; with the toggle the velocity too; without destination and toggle nothing; its knob LED = the
    value in the destination's colour;
  * c_sdfx: the offsets of both pages summed for their destinations (a single destination, the pitch of both / one oscillator);
  * lane 1 (REL) while the step-drummer is on: not applied on playback, not recorded; lane 2 as before;
  * the audition of a step with the toggle: its note moved in the scale, the note-off the same note;
  * Synth 1's step-drummer view: pad 32 = the toggle (not the macro editor); page 2's destination = a macro, knob 1 writes its lane from the
    macro's position;
  * playback (Synth 1's player): with the toggle each note moves by (page-1 value - 64) degrees of the scale (stock major, the custom scale), clamped;
    without the toggle as written;
  * c_pvdeg against a model; random-mutate with the custom scale and the root D picks degrees above D.

    python tools/emu_sc42_6.py SC42.6.bin SC42.6_manifest.json [SC42.5.bin SC42.5_manifest.json]
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
import vcf21 as V  # noqa: E402
import sdpv as P  # noqa: E402

MGR = T.MGR
KB = 0x20041044
MAJOR = [0, 2, 4, 5, 7, 9, 11]


def frame(e):
    e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR)
    e.call(0x08033B3E, maxins=40_000_000)
    return list(struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138))))


def model_deg(note, k, root, inscale):
    d = 1 if k > 0 else -1
    while k:
        while True:
            note += d
            if note < 0: return 0
            if note > 127: return 127
            if inscale(note - root): break
        k -= d
    return note


class EP(T.EL):
    def __init__(self, img, man):
        super().__init__(img)
        self.man = man
        self.vl = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
        self.pl = {k: int(v, 16) for k, v in man["report"]["sdpv"]["labels"].items()} if "sdpv" in man["report"] else {}
        self.ons, self.gates = [], []
        def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        def note(uc, a, s, d):
            self.ons.append(("on" if a == self.vl["c_vnon"] else "off", uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3))); skip(uc)
        for f in (self.vl["c_vnon"], self.vl["c_vnoff"]): self.uc.hook_add(UC_HOOK_CODE, note, begin=f, end=f)
        def gate(uc, a, s, d): self.gates.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2))); skip(uc)
        self.uc.hook_add(UC_HOOK_CODE, gate, begin=V.REC_GATE, end=V.REC_GATE)
        self.at(100000); self.transport(0)
        for _ in range(30): self.at(self.t + 40); self.call(self.vl["c_vtick"], maxins=3_000_000)
    def r0(self, fn, *a): self.call(fn, *a, maxins=4_000_000); return self.uc.reg_read(UC_ARM_REG_R0)
    def r1(self, fn, *a): self.call(fn, *a, maxins=4_000_000); return self.uc.reg_read(UC_ARM_REG_R1)
    def knob(self, k, d): self.call(0x08033848, MGR, k, d & 0xFFFFFFFF, maxins=8_000_000)
    def shift(self, on): self.set_p0(self.r32(MGR + 0xC), 1 if on else 0)
    def pv(self, t): return self.r0(self.pl["c_pvget"], t)
    def lane(self, t, step, ofs): return self.r8(self.r0(self.vl["c_sdlna"], self.r0(self.vl["c_sdpat"], t), step) + ofs)
    def val(self, t, code): return struct.unpack("b", bytes([self.r8(self.r0(self.vl["c_vvaddr"], t, code))]))[0]


def midi_part(img, man, check):
    e = EP(img, man)
    e.btn(2); e.btn(8)
    for _ in range(2): e.pad(26)                                                     # pad 27: off -> line in -> oscillator
    f = frame(e)
    check(f[29] == V.COL_SD[1], f"MIDI 1, the own engine on, the step-drummer off: pad 30 dim ({f[29]:#x})")
    e.pad(29)
    f = frame(e); h0 = e.r0(e.vl["c_sdhalf"], 0)
    check(f[29] == V.COL_SD[0] and f[31] == P.COL_PV[1] and e.r0(e.vl["c_sdscr"]) == 0, f"pad 30: its view (pad 30 bright, pad 32 dim green: {f[29]:#x}, {f[31]:#x})")
    e.pad(31); f = frame(e)
    check(e.pv(0) == 0x80 and f[31] == P.COL_PV[0], f"pad 32: the toggle on (byte {e.pv(0):#x}, LED {f[31]:#x})")
    e.pad(31); f = frame(e)
    check(e.pv(0) == 0 and f[31] == P.COL_PV[1], "pad 32 again: off")
    # page 2
    e.btn(19); f = frame(e)
    dim = [c + 1 if c != 0x32 else 0x37 for c in V.SD_DCOL]
    check(f[16:24] == dim, f"page 2 without a destination: pads 17-24 dim ({[hex(x) for x in f[16:24]]})")
    e.pad(18); f = frame(e)
    want = list(dim); want[2] = V.SD_DCOL[2]
    check(e.pv(0) == P.F_D2 | 2 and f[16:24] == want, f"pad 19 on page 2: its destination WAVE ({e.pv(0):#x}, {[hex(x) for x in f[16:24]]})")
    e.pad(18)
    check(e.pv(0) == 0, "pad 19 again: none")
    e.pad(18)
    v0 = e.r0(e.vl["c_sdpvel"], 0, h0); l0 = e.lane(0, h0, 0)
    e.knob(0, 5); f = frame(e)
    check([e.lane(0, h0 + s, 192 + m) for s in (0, 1) for m in range(6)] == [69] * 12 and e.r0(e.vl["c_sdpvel"], 0, h0) == v0 and e.lane(0, h0, 0) == l0,
          f"page 2, knob 1: lane 1 of the pair from 64 (+5 = {e.lane(0, h0, 192)}), the velocity ({v0}) and page 1's lane untouched")
    check(f[60] == V.SD_DCOL[2] | (69 + 2) << 8, f"its LED: the value in WAVE's colour ({f[60]:#x})")
    e.pad(31); e.knob(0, 5)
    check(e.lane(0, h0, 192) == 74 and e.r0(e.vl["c_sdpvel"], 0, h0) != v0, f"the toggle on: the lane (74) and the velocity ({v0} -> {e.r0(e.vl['c_sdpvel'], 0, h0)})")
    e.pad(31); e.pad(18)
    snap = lambda: ([e.lane(0, h0 + s, 192 + m) for s in (2, 3) for m in range(6)], e.r0(e.vl["c_sdpvel"], 0, h0 + 2), e.lane(0, h0 + 2, 0))
    b4 = snap(); e.knob(1, 9)
    check(snap() == b4 and e.pv(0) == 0, f"no destination, the toggle off: knob 2 changes nothing ({b4[1:]})")
    f = frame(e)
    check(f[61] & 0xFF == 0, f"its LED dark ({f[61]:#x})")
    # c_sdfx: WAVE on both pages
    e.pad(18)                                                                        # page 2 -> WAVE again
    e.btn(20); e.pad(18); e.knob(0, 3)                                               # page 1 -> WAVE, knob 1 +3
    gf = e.r0(int(man["report"]["sc17"]["labels"]["c_gfst"], 16)); e.uc.mem_write(gf + V.SD_AUD, bytes([h0 + 1]))   # the step that counts
    fx = e.r1(e.vl["c_sdfx"], 0, 40, 18)
    check(fx == 40 + 3 + 10, f"c_sdfx, WAVE on both pages: 40 + 3 + 10 = {fx}")
    e.btn(19); e.pad(17); e.btn(20); e.pad(16)                                        # page 2 -> pitch of OSC2, page 1 -> pitch of both
    t1, t2, fi2 = e.r1(e.vl["c_sdfx"], 0, 0, 16), e.r1(e.vl["c_sdfx"], 0, 0, 26), e.r1(e.vl["c_sdfx"], 0, 0, 27)
    s = lambda x: x - (1 << 32) if x >= 1 << 31 else x
    # TUNE / FINE stored 0: OSC1 = 24 x 3 (1 / 128 semitone) -> 1 semitone; OSC2 = 24 x (3 + 10) = 312 -> 2 semitones, fine 312 - 256 = 56
    check((s(t1), s(t2), s(fi2)) == (1, 2, 56), f"pitch: OSC1 page 1 only (1), OSC2 both pages (2, fine 56): ({s(t1)}, {s(t2)}, {s(fi2)})")
    # lane 1 belongs to page 2 while the step-drummer is on
    rel = e.val(0, 8); enva = e.val(0, 15)
    e.call(e.vl["c_vapply"], 0, 1, 100); e.call(e.vl["c_vapply"], 0, 2, 100)
    check(e.val(0, 8) == rel and e.val(0, 15) != enva, f"playback: lane 1 (REL {rel}) not applied, lane 2 (ENVA {enva} -> {e.val(0, 15)}) as before")
    e.gates.clear(); e.call(e.vl["c_vcc_rec"], 0, 8, 50); n1 = len(e.gates); e.call(e.vl["c_vcc_rec"], 0, 15, 50)
    check(n1 == 0 and len(e.gates) == 1, f"recording: REL not recorded, ENVA through the gate ({n1}, {len(e.gates) - n1})")
    # the audition with the toggle: page 1 = the pitch of both oscillators, knob 1 at +3 -> the note 3 degrees up
    e.uc.mem_write(gf + V.SD_AUD, bytes([0]))
    e.pad(31)
    e.ons.clear()
    root = e.r8(e.r32(KB + 0x10)); mask = e.r32(e.r32(KB + 0xC) + 4)
    ins = lambda r: (mask >> 2 * (r % 12)) & 3 == 0
    e.call(T.PRESS, MGR, 0, 100, maxins=8_000_000); e.call(T.RELEASE, MGR, 0, maxins=8_000_000)
    base = e.r0(e.vl["c_sdnnote"], 0, h0)
    want = model_deg(base, 3, root, ins)
    on = [x for x in e.ons if x[0] == "on"]; off = [x for x in e.ons if x[0] == "off"]
    check(len(on) == 1 and on[0][2] == want and len(off) == 1 and off[0][2] == want and want != base,
          f"the audition of step 1 with the toggle: {base} moved 3 degrees = {want} (on {on}, off {off})")
    e.pad(31); e.ons.clear()
    e.call(T.PRESS, MGR, 0, 100, maxins=8_000_000); e.call(T.RELEASE, MGR, 0, maxins=8_000_000)
    check([x[2] for x in e.ons] == [base, base], f"without the toggle: as written ({e.ons})")
    # out of the view: pad 32 dark again
    e.pad(29); f = frame(e)
    check(f[31] == 0 and f[29] == V.COL_SD[0], f"the view closed: pad 32 dark, pad 30 bright (on) ({f[31]:#x}, {f[29]:#x})")
    del e; gc.collect()


def synth_part(img, man, check):
    e = EP(img, man)
    gst = int(man["report"]["sc14"]["labels"]["c_gst"], 16)
    for _ in range(3):                                                               # Synth 1 again from its track view: its source view (SC19.1)
        e.btn(0)
        if e.r8(MGR + 0x152) == 0 and e.r8(e.r0(gst) + V.S_PAINT) & V.F_SRC: break
    e.pad(29)
    f = frame(e); sc = e.r0(e.vl["c_sdscr"])
    st = int(man["report"]["macroed"]["labels"]["c_mcst"], 16)
    e.pad(31); f = frame(e)
    sp = e.r0(st); ed = e.r8(sp + 1) if sp else 0
    check(sc == 2 and e.pv(2) == 0x80 and f[31] == P.COL_PV[0] and ed == 0, f"Synth 1's step-drummer view: pad 32 = the toggle, not the macro editor ({sc}, {e.pv(2):#x}, {f[31]:#x}, editor {ed:#x})")
    e.btn(19); e.pad(19)
    check(e.pv(2) == 0x80 | P.F_D2 | 3, f"page 2, pad 20: macro 4 ({e.pv(2):#x})")
    h0 = e.r0(e.vl["c_sdhalf"], 0)
    pos = e.r0(V.GETTER, 0, 174 + 17 * 3); pos = min(pos, 127)
    v0 = e.r0(e.vl["c_sdpvel"], 2, h0)
    e.knob(0, 4)
    check(e.lane(2, h0, 192 * 3) == min(127, pos + 4) and e.lane(2, h0 + 1, 192 * 3 + 5) == min(127, pos + 4), f"knob 1: macro 4's lane from its position ({pos} + 4 = {e.lane(2, h0, 192 * 3)})")
    e.pad(31); e.pad(29)                                                             # the toggle off, the step-drummer view closed
    e.pad(31); sp = e.r0(st)
    check(e.pv(2) == P.F_D2 | 3 and sp and e.r8(sp + 1) & 0x80, f"the source view without the step-drummer view: pad 32 = the macro editor as before ({e.pv(2):#x}, editor {e.r8(sp + 1) if sp else 0:#x})")
    del e; gc.collect()


def play_part(img, man, check):
    from emu_arp import EA, chord_steps
    e = EA(img, man)
    pl = {k: int(v, 16) for k, v in man["report"]["sdpv"]["labels"].items()}
    vl = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
    cs = {k: int(v, 16) for k, v in man["report"]["cscale"]["labels"].items()}
    r0 = lambda fn, *a: (e.call(fn, *a, maxins=4_000_000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    p = e.playing(0); base = e.settings(0, p) - 0x380
    notes = [(60, 3, 0, 100), (64, 3, 0, 100), (71, 3, 0, 100), (120, 3, 0, 100)]
    steps = bytearray()
    for s in range(8):
        n = notes[s] if s < len(notes) else None
        steps += bytes([1 if n else 0, 7, 0, 0]) + (bytes(n) if n else bytes([0, 0, 0, 0x60])) + bytes([0, 0, 0, 0x60]) * 5
    e.uc.mem_write(base, bytes(steps)); e.setpat(0, p, 0, 7)
    e.setp(e.r32(0x20040200 + 0x10), 1, bytes([3]))
    pat = r0(vl["c_sdpat"], 2)
    lofs = r0(vl["c_sdlofs"], 2)
    ks = (2, -1, 3, 5)
    for s, k in enumerate(ks):
        e.uc.mem_write(r0(vl["c_sdlna"], pat, s) + lofs, bytes([64 + k] * 6))
    root = e.r8(e.r32(KB + 0x10)); mask = e.r32(e.r32(KB + 0xC) + 4)
    ins = lambda r: (mask >> 2 * (r % 12)) & 3 == 0
    def run():
        e.transport(1); e.ons.clear(); e.run(p, 4); return [n for _, n, *_ in e.ons]
    plain = run()
    check(pat == base, f"the player reads the pattern the step-drummer writes ({pat:#x}, {base:#x})")
    e.call(pl["c_pvset"], 2, 0x80)
    moved = run()
    want = [model_deg(n[0], k, root, ins) for n, k in zip(notes, ks)]
    check(plain == [n[0] for n in notes] and moved == want, f"Synth 1, the toggle: notes {plain} moved {ks} degrees of the scale (mask {mask:#x}, root {root}) = {moved} (model {want})")
    e.call(cs["c_csput"], 1, 1 << 3 | 1 << 7 | 1 << 12)                            # a custom scale: 0, 3, 7, period 12
    cus = run()
    cin = lambda r: (r - 60) % 12 in (0, 3, 7)
    wantc = [model_deg(n[0], k, root, cin) for n, k in zip(notes, ks)]
    check(cus == wantc, f"the custom scale (0, 3, 7 / 12): {cus} (model {wantc})")
    e.call(pl["c_pvset"], 2, 0)
    check(run() == plain, "the toggle off: as written")
    # c_pvdeg against the model, stock scale with another root, clamps
    e.uc.mem_write(e.r32(KB + 0x10), bytes([2]))
    e.call(cs["c_csput"], 0, 0)
    bad = []
    for n in (0, 5, 61, 62, 100, 126, 127):
        for k in (-64, -9, -1, 1, 2, 7, 63):
            got = r0(pl["c_pvdeg"], n, k & 0xFFFFFFFF); exp = model_deg(n, k, 2, ins)
            if got != exp: bad.append((n, k, got, exp))
    check(not bad, f"c_pvdeg = the model on 49 cases, root D ({bad[:4]})")
    # random-mutate with the custom scale (0, 4, 7 / 12) and the root D: the other degrees of D's triad
    e.call(cs["c_csput"], 1, 1 << 4 | 1 << 7 | 1 << 12)
    mut = int(man["report"]["mutate39"]["labels"]["c_mutscale"], 16)
    outs = sorted({r0(mut, 62, r) for r in range(8)})
    check(outs == [66, 69], f"random-mutate, custom triad, root D: D (62) -> {outs} (F#, A)")
    del e; gc.collect()


def main(img, man, prev=None, prev_man=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    midi_part(img, man, check)
    synth_part(img, man, check)
    play_part(img, man, check)
    if prev:
        e = EP(prev, prev_man); e.btn(2); e.btn(8)
        for _ in range(2): e.pad(26)
        f = frame(e)
        check(f[29] == 0, f"SC42.5: pad 30 dark with the step-drummer off ({f[29]:#x})")
        del e; gc.collect()
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    pv = (Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) if len(a) > 4 else (None, None)
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), *pv) else 0)
