"""SC36 ARM tests through the real routes (pads 0x08033282 / release, the view slots, the knob handlers, the DSP service tick):

    python tools/emu_sc36.py SC36.bin SC36_manifest.json
  * MIDI 1 / 2 (vcf21.use_gran / use_fxseq): pad 27 = off -> line in -> oscillator -> VA-drum -> granular -> FX sequencer -> off; the signature nibble, the ACT message
    (granular = 2 | 1 << 12, the FX sequencer = 0), the LED of pad 27, pad 31 dark out of the VA-drum state, the step-drummer enabled by the FX sequencer;
  * the granular knob page (page row pad 2 = OSC1): K1 pitch clamped +-24, K5 density 0..100, Shift + K8 source one step per turn (-1 = the capture .. 63), Shift + K6
    note mode 0 / 1, Shift + K2 a volatile value (code 33), the mailbox messages, the knob LEDs (bipolar, value, value + 64, steps); page 0 is still the VCA / VCF page;
  * the FX sequencer: while the transport runs, a step with notes and a pair value v (1..127) switches on the effect of zone (v - 1) x 7 / 128 (0..5 the top pads, 6 the
    Glitch); no note / v = 0 / stopped / not in the state = nothing; the Master FX tick sends it (FX_ON) and the Glitch magic;
  * Master FX / FX view (build_sc17.use_glitch): pad 31 = the Glitch: selected, held, the tick writes K1..K4 and the magic (released: 0), lit while it plays, its knobs (clamped,
    bit 7 kept), its knob LEDs; a held top effect + pad 31 assigns nothing; the FX view's pad 31 too; leaving the views releases it.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc34 as T34  # noqa: E402  (configures build_sc17 as SC34)
import build_sc17 as B  # noqa: E402
B.use_loophold(); B.use_glitch()
import emu_sc29 as T29  # noqa: E402,F401  (configures vcf21 as SC29)
import emu_sc22_4 as T4  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
import granular_dsp as GD  # noqa: E402
import masterfx_dsp as G  # noqa: E402
from emu_sc17_6 import TICK, MGR  # noqa: E402
V = T4.V
V.use_gran(); V.use_fxseq()
E20, TMPL = T4.E20, T4.TMPL
KG = B.S_SLOT + 4 * B.GL_SLOT


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    check(man["report"]["sc17"].get("glitch") is True and "granular" in man["report"], "manifest: glitch, granular")

    # ================================================================ MIDI 1: pad 27
    gc.collect(); e = E20(img, man)
    for _ in range(30): e.vtick()
    sig = lambda: e.tailb(V.O_SIG)
    pad = lambda p: (e.padr(p), e.rel(p))
    def mbox(n=60, voice=0):
        got = {}
        for _ in range(n):
            for w, ad in e.vtick():
                if ad == VD.VB0 + voice * VD.VBS: got[(w >> 16) & 0x7F] = w & 0xFFFF
        return got
    e.btn(2); e.track(2); e.btn(8)
    led = lambda t=0: e.tleds(TMPL[t])
    on = lambda t=0: (e.tailb(V.O_FLAGS) >> t) & 1
    osc = lambda t=0: (e.tailb(V.O_FLAGS) >> (2 + t)) & 1
    nib = lambda t=0: (e.tailb(V.O_SD) >> (4 * t)) & 15
    pad(V.PAD_OSC); g = mbox()
    check(on() and not osc() and g.get(19) == 1 and led()[V.PAD_OSC] == V.COL_ON, f"pad 27: line in (ACT {g.get(19)})")
    pad(V.PAD_OSC); g = mbox()
    check(osc() and g.get(19) == 2 and led()[V.PAD_OSC] == V.COL_OSC[0], f"the oscillator (ACT {g.get(19)})")
    pad(V.PAD_OSC); g = mbox()
    check(sig() == 0xB1 and g.get(19) == (2 | 1 << 10) and led()[V.PAD_OSC] == V.COL_VD, f"VA-drum (signature {sig():#x}, ACT {g.get(19):#x})")
    pad(V.PAD_VEL); mbox()
    check(sig() == 0xB5, "VA-drum with pad 31 on (0xb5)")
    e.saves.clear(); pad(V.PAD_OSC); g = mbox()
    check(sig() == 0xB4 and osc() and g.get(19) == (2 | 1 << 12) and led()[V.PAD_OSC] == V.COL_GR and led()[V.PAD_VEL] == 0 and e.saves,
          f"granular (signature {sig():#x}: VA-drum bit 0, velocity bit 1; ACT {g.get(19):#x}), pad 27 {led()[V.PAD_OSC]:#x}, pad 31 dark, saved")
    s0 = sig(); pad(V.PAD_VEL)
    check(sig() == s0, "pad 31 does nothing in the granular state")

    # ---------------------------------------------------------------- the granular knob page
    pad(1); mbox()                                                                # the page row: OSC1
    vaddr = lambda code, t=0: (e.call(e.vl["c_vvaddr"], t, code), e.uc.reg_read(T4.UC_ARM_REG_R0) if hasattr(T4, "UC_ARM_REG_R0") else None)[1]
    from unicorn.arm_const import UC_ARM_REG_R0
    def gval(code, t=0):
        e.call(e.vl["c_vvaddr"], t, code); return struct.unpack("b", bytes([e.r8(e.uc.reg_read(UC_ARM_REG_R0))]))[0]
    e.knob_raw(0, 40); g = mbox(20)
    check(gval(17) == 24 and g.get(22) == 24, f"K1 +40: pitch clamped at +24 (code 17 = {gval(17)}, mailbox 22 = {g.get(22)})")
    e.knob_raw(0, -100); g = mbox(20)
    check(gval(17) == -24 and g.get(22) == (-24) & 0xFFFF, f"K1 -100: -24 ({gval(17)})")
    e.knob_raw(4, 120); mbox(20)
    check(gval(20) == 100, f"K5 +120: density clamped at 100 ({gval(20)})")
    b25 = gval(25); e.knob_raw(7, 5, shift=True); mbox(10)
    check(gval(25) == min(63, b25 + 1), f"Shift + K8 +5: the source one step ({b25} -> {gval(25)})")
    for _ in range(80): e.knob_raw(7, -3, shift=True)
    mbox(10)
    check(gval(25) == -1, f"Shift + K8 down: the capture (-1) is the floor ({gval(25)})")
    e.knob_raw(5, 4, shift=True); a1 = gval(26); e.knob_raw(5, 4, shift=True); a2 = gval(26); e.knob_raw(5, -1, shift=True); a3 = gval(26)
    check((a1, a2, a3) == (1, 1, 0), f"Shift + K6: the note mode 0 / 1 one step per turn ({a1}, {a2}, {a3})")
    b33 = gval(33); e.knob_raw(1, 20, shift=True)
    check(gval(33) == min(127, max(0, b33 + 20)), f"Shift + K2: the position spray (volatile code 33: {b33} -> {gval(33)})")
    e.knob_raw(3, -200); mbox(10)
    check(gval(18) == -64, f"K4 down: the size at its minimum (stored -64, {gval(18)})")
    fr = e.frame()
    col = V.COL_TRACK[0]
    want = [(24 * 2 - 2 + 2 if False else ((23 * 2) + 2)) << 8 | col]
    check(fr[60] == ((23 * 2 + 2) << 8 | col) and fr[63] == ((0 + 2) << 8 | col) and fr[64] == ((100 + 2) << 8 | col),
          f"knob LEDs: K1 bipolar |-24| ({fr[60]:#x}), K4 value + 64 = 0 ({fr[63]:#x}), K5 the value 100 ({fr[64]:#x})")
    pad(0); mbox()
    v5 = e.val(0, 5); e.knob_raw(0, 3); mbox(10)
    check(e.val(0, 5) == min(127, v5 + 3) and gval(17) == -24, f"page 0 (VCA / VCF): K1 is code 5 again ({v5} -> {e.val(0, 5)}), the pitch untouched")

    # ---------------------------------------------------------------- the FX sequencer
    e.saves.clear(); pad(V.PAD_OSC); g = mbox()
    check(sig() == 0xB1 and on() and not osc() and g.get(19) == 0 and led()[V.PAD_OSC] == V.COL_FS and nib() & 1 and e.saves,
          f"pad 27: the FX sequencer (signature {sig():#x}, mode on, no oscillator, ACT {g.get(19)}, LED {led()[V.PAD_OSC]:#x}, step-drummer enabled)")
    def r0(fn, *a): e.call(fn, *a); return e.uc.reg_read(UC_ARM_REG_R0)
    pat = r0(e.vl["c_sdpat"], 0)
    def setstep(st, notes, v):
        e.uc.mem_write(r0(e.vl["c_sdstp"], pat, st), bytes([notes])); e.uc.mem_write(r0(e.vl["c_sdlna"], pat, st), bytes([v]))
    stp = r0(e.vl["c_sdeng"], 0, 1)
    def play(on_):
        e.call(V.PARAM_GET, V.PLAY_STORE, 0); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes([(on_) & 0xFF]))
    fsq = lambda: r0(e.vl["c_fsqbits"])
    e.uc.mem_write(stp, bytes([(5) & 0xFF])); play(1)
    for notes, v, want, name in ((1, 40, 1 << ((39 * 7) >> 7), "a note, v 40"), (0, 40, 0, "no note"), (1, 0, 0, "v 0"), (1, 0xFF, 0, "no value"),
                                 (1, 1, 1, "v 1 = pad 1"), (1, 127, 1 << 6, "v 127 = the Glitch")):
        setstep(5, notes, v)
        check(fsq() == want, f"FX sequencer, step 5 with {name}: bits {fsq():#x} (want {want:#x})")
    setstep(5, 1, 40); play(0)
    check(fsq() == 0, "stopped: nothing")
    play(1)
    FXT = int(man["report"]["sc17"]["labels"]["c_fxtick"], 16)
    def fxt():                                                                    # (the harness stubs the next link of the service chain = c_fxtick: not for this call)
        nx = e.s18["svc_next"]; e.s18["svc_next"] = 0
        e.dw.clear(); e.call(FXT, maxins=3_000_000)
        e.s18["svc_next"] = nx
    fxt()
    fxon = [x for x in e.dw if len(x) == 3 and x[2] == G.FX_ON]
    check(fxon and fxon[-1][1] == B.FXBITS[(39 * 7) >> 7], f"the Master FX tick: FX_ON = the effect of zone {(39 * 7) >> 7} ({[hex(x[1]) for x in fxon]})")
    setstep(5, 1, 127); fxt()
    gm = [x[1] for x in e.dw if len(x) == 3 and x[2] == GD.GARM]
    check(gm and gm[-1] == GD.GMAGIC, f"v 127: the Glitch magic sent ({[hex(x) for x in gm]})")
    setstep(5, 0, 127); fxt()
    gm = [x[1] for x in e.dw if len(x) == 3 and x[2] == GD.GARM]
    check(gm == [0], f"no note any more: the Glitch off ({gm})")
    pad(V.PAD_OSC); g = mbox()
    check(sig() == 0xB0 and not on() and g.get(19) == 0 and led()[V.PAD_OSC] == 0 and fsq() == 0 and not nib() & 1, f"pad 27: off (signature {sig():#x}), the step-drummer off again")
    del e; gc.collect()

    # ================================================================ Master FX: the Glitch on pad 31
    x = T34.E7(img, man); x.grid(); x.setsp(); x.uc.mem_write(x.blk + B.S_JF, b"\0\0"); x.w32(x.blk + B.S_SMT, 0); x.uc.mem_write(x.blk + B.S_SLOT, bytes(28))
    def ftick(ms):
        x.w32(TICK, ms); x.dw.clear(); x.call(x.L["c_fxtick"], maxins=3_000_000); return list(x.dw)
    MIXV = 0x200447D4
    def knob(k, d): x.call(x.r32(B.MIX_VT + 16), MIXV, k, d & 0xFFFFFFFF, maxins=900000)
    kg = lambda: list(x.blkb(KG, 4))
    x.uc.mem_write(x.blk + KG, bytes([100, 30, 40, 50])); ftick(500)
    x.pad(B.GL_PAD)
    check(x.blkb(B.S_SEL)[0] == B.GL_SEL and kg()[0] == 0x80 | 100 and kg()[1] & 0x80, f"pad 31: the Glitch selected, held, to send {[hex(v) for v in kg()]}")
    w = ftick(1000); d = dict(w)
    check([d.get(GD.GARM + 1 + k) for k in range(4)] == [100, 30, 40, 50] and w[-1] == (GD.GARM, GD.GMAGIC) and not kg()[1] & 0x80, f"tick: K1..K4 then the magic ({[(hex(a), hex(v)) for a, v in w if a >= GD.GARM]})")
    check(ftick(1100) == [] or all(a < GD.GARM for a, _ in ftick(1150)), "next tick: nothing more for the Glitch")
    g = x.gleds()
    check(g[B.GL_PAD] == B.GL_ON and g[34] == ((100 + 2) << 8 | B.GL_ON) and g[38] == 0, f"pad 31 bright, K1 LED {g[34]:#x}, K5 dark")
    knob(0, 20)
    check(kg()[0] == 0x80 | 120, f"K1 +20: 120, bit 7 kept ({kg()[0]:#x})")
    knob(0, 30)
    check(kg()[0] == 0x80 | 127, "K1 +30: clamped at 127")
    d = dict(ftick(1200))
    check(d.get(GD.GARM + 1) == 127 and d.get(GD.GARM) == GD.GMAGIC, "the tick sends the new K1")
    x.rel(B.GL_PAD); w = ftick(1300)
    check(kg()[0] == 127 and (GD.GARM, 0) in w and x.gleds()[B.GL_PAD] == B.GL_DIM, f"released: the tick writes 0, pad 31 dim ({w[-3:]})")
    x.pad(0); x.pad(B.GL_PAD); x.rel(B.GL_PAD); x.rel(0)
    check(not kg()[3] & 0x80 and x.blkb(B.S_SLOT + 4 * 5 + 3)[0] >> 7 == 0, "pad 1 held + pad 31: nothing assigned (the Glitch played instead)")
    ftick(1400)
    # ---------------------------------------------------------------- the FX view
    x.btn(15)
    x.pad(B.GL_PAD); w = ftick(1500)
    check(w and w[-1] == (GD.GARM, GD.GMAGIC) and x.fxleds()[B.GL_PAD] == B.GL_ON, "FX view pad 31: the Glitch plays, lit")
    x.rel(B.GL_PAD); w = ftick(1600)
    check((GD.GARM, 0) in w and x.fxleds()[B.GL_PAD] == B.GL_DIM, "released: off, dim")
    x.pad(B.GL_PAD); ftick(1700)
    x.btn(0); w = ftick(1800)
    check(not kg()[0] & 0x80 and (GD.GARM, 0) in w, "held, then another view: released, 0 sent")
    print("SC36 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
