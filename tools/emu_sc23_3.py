"""SC23.3 ARM tests (neutral defaults, Clear + knob); SC23.2 ARM tests (the pads of the Preset view: 27 = oscillator source only, 28 = oscillator view, 29 = VCA / VCF view, the mode on while one is lit); the rest as SC23: SC23 ARM tests (SC22.4 + the CC editor on pad 25; the editor itself: tools/emu_sc23_ed.py; SC22.4: SC22.3 + distinct pad colours (VCF / VCA pad orange, the two oscillator pads green) and the new pad order (25 free, 26 patch flip, 27 oscillator source, 28 oscillator edit, 29 VCF / VCA); SC22.3: SC22.2 + the oscillator v3: 26 values per track (the dirty bits 25 / 26 in the AUX byte), WAVE = a continuous morph, PW 0..100, K5 = ENVM / LFOM, mailbox codes 22..31; SC22.2: SC22.1 + the oscillator v2: pad 27 = the knob page B, pad 28 = the oscillator source, 24 values per track, mailbox codes 22..29; SC22.1: SC22 + the oscillator source, stride 24 values, three dirty bytes, ACT 0 / 1 / 2; SC22: SC21.4's VCF / VCA / FX mode of the MIDI tracks, tools/vcf21.py, plus 7 FX types (soft, hard, fold, wavefold, ring mod, comb, chorus) and the bipolar sends of K3 / Shift + K3 (ENVA, LFOV); signature 0xA9), through the real controller routes on the live RAM dump.

    python tools/emu_sc23_2.py SC19.9.bin SC23.2.bin SC19.9_manifest.json SC23.2_manifest.json
  * installation: the image differs from SC19.9 only at the hooks (pad site, note vtable, macro handler slots 4 / 7, template slot 7, the head of the DSP chain);
  * pad 26 of the Preset view of MIDI 1 / 2 toggles the mode of the track (bright / dim yellow); the patch flip pad turns it off when the flip turns on, and the mode turns the flip off;
  * knobs: with the mode on the 8 knobs (and Shift) change the 16 values of the track in their ranges (bipolar -64..63, unipolar 0..127, shape 0..3 wrapping, VCA mode 0 / 1) and the
    stock parameters of the track are untouched; with the mode off the stock handler runs as in SC19.9 (same stock parameter writes);
  * LEDs: the knob LEDs show the track colour with the brightness of each value (Shift layer with Shift); the other tracks and views as SC19.9;
  * notes: the pads of the track (through the note wrappers) count held notes, remember note / velocity and flag NOTE / VEL / GATE / TRIG; the stock note path still runs (same calls);
  * the DSP tick: first tick after power-up sends ACT and all the values (defaults on the first use), then NOTE / VEL / GATE / TRIG on notes, a value on a knob turn; one message per voice
    per tick, tags toggling; nothing when idle; the persistent drum tick (SC19) still runs behind it;
  * the settings save (stock 0x0802D2AC) is requested on a toggle and, throttled, on knob turns; the state lives in the tail of the settings record (inside the 0x80 bytes the stock save writes).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc19_1 import E191  # noqa: E402
from emu_sc19_6 import MGR, CONT, STOP  # noqa: E402
import vcf21 as V  # noqa: E402
V.FTYPE_N, V.FXTYPE_N, V.SIG_VAL, V.BISEND = 7, 7, 0xA9, True
V.BIPOLAR_MASK |= (1 << 11) | (1 << 14)
V.use_osc3(); V.use_colors(); V.use_layout(); V.use_cced(); V.use_pads2(); V.use_neutral(); V.use_clearknob(); V.use_octleds(); V.use_cced2()
import vcf21_dsp as VD  # noqa: E402
import drums18  # noqa: E402

BASE = 0x08010000
TMPL = (0x20042AE8, 0x20042B50)
SEL_TRACK = 0x188


class E20(E191):
    def __init__(self, image, man):
        super().__init__(image, man)
        self.saves = []
        def sv(uc, a, s, d):
            self.saves.append(uc.reg_read(UC_ARM_REG_R0)); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        self.uc.hook_add(UC_HOOK_CODE, sv, begin=V.SAVE_FN, end=V.SAVE_FN)
        self.vl = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
        self.rl = man["report"]["vcf20"].get("ratelimit", 0)          # SC23.5: one message per voice every N ms, the emulated HAL clock does not run: 40 ms per service tick
        self.notes = []
        def nt(uc, a, s, d): self.notes.append((a, uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3)))
        s6 = {k: int(v, 16) for k, v in man["report"]["sc06"]["labels"].items()}
        self.s6 = s6
        for fa in (s6["c_non"], s6["c_noff"]): self.uc.hook_add(UC_HOOK_CODE, nt, begin=fa, end=fa)
        self.knob_calls = []
    def knob_raw(self, k, delta, shift=False): self._knob19(k, delta, shift)
    def tailb(self, off): return self.r8(V.TAIL + off)
    def tail(self): return bytes(self.uc.mem_read(V.TAIL, 75))
    def val(self, t, code): return struct.unpack("b", bytes([self.tailb(V.O_PAR + V.STRIDE * t + code - 1)]))[0]
    def rt(self, t, off): return self.tailb(V.O_RT + 8 * t + off)
    def settings_p2(self):
        self.call(self.s6["c_settings"]); st = self.uc.reg_read(UC_ARM_REG_R0)
        self.call(0x0803542C, st, 2); return self.r32(self.uc.reg_read(UC_ARM_REG_R0))
    def vtick(self):
        if self.rl: self.w32(0x2000081C, (((self.r32(0x2000081C) & ~7) + 40) | 2))  # +40 ms keeps HAL & 7 = 2 (no heartbeat window, HAL & 7 = 0; the SC24 sweep slot, HAL & 3 = 2) and HAL & 31 moving by 8 (the 5-bit stamp of the 2 ms gate never aliases to 'just now')
        self.dw.clear(); self.chain.clear()
        self.call(self.vl["c_vtick"], maxins=3_000_000)
        out = [(x[1], x[2]) for x in self.dw if len(x) == 3 and VD.VB0 <= x[2] < VD.VB0 + 2 * VD.VBS]
        self.sent = getattr(self, "sent", []) + out
        return out
    def frame(self):
        self.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1))
        self.uc.reg_write(UC_ARM_REG_R4, MGR)
        self.call(0x08033B3E, maxins=5_000_000)
        return list(struct.unpack("<69H", bytes(self.uc.mem_read(self.r32(self.r32(MGR + 0x90)), 138))))
    def track(self, t): self.set_p0(self.r32(CONT + SEL_TRACK), t)
    def tleds(self, v):
        self.call(self.r32(self.r32(v) + 0x1C), v, maxins=600000)
        return list(struct.unpack("<32H", bytes(self.uc.mem_read(self.uc.reg_read(UC_ARM_REG_R0), 64))))


def level(t, code, byte):
    v = struct.unpack("b", bytes([byte & 0xFF]))[0]
    if code == 13: return (v % V.FXTYPE_N) * (126 // (V.FXTYPE_N - 1))
    if code == 16: return v * (126 // (V.FTYPE_N - 1))
    if (V.BIPOLAR_MASK >> (code - 1)) & 1: return min(126, ((-v - 1) if v < 0 else v) * 2)
    return max(0, v)


def main(prev, img, man9, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]["vcf20"]
    TZ = man["marker"] == "SC23.6"
    if TZ: V.use_typezones()                                                         # SC23.6: the type knobs (the options of the older builds stay as they are)
    check(rep["tail"] == hex(V.TAIL), f"settings tail at {rep['tail']}")
    # ---- installation (the appended code moves with the new DSP words, so the pointers into it change: the hook sites are checked one by one)
    s6 = {k: int(v, 16) for k, v in man["report"]["sc06"]["labels"].items()}
    L = {k: int(v, 16) for k, v in rep["labels"].items()}
    import build_sc14 as s14
    w = lambda a: struct.unpack_from("<I", img, a - BASE)[0]
    check(w(V.AC64_VT + 0x10) == L["c_vknob"] | 1 and w(V.AC64_VT + 0x1C) == L["c_vkleds"] | 1 and w(V.NOTE_VT[0]) == L["c_vnon"] | 1 and w(V.NOTE_VT[1]) == L["c_vnoff"] | 1
          and w(V.TMPL_VT_LEDS) == L["c_vleds"] | 1, "macro handler slots 4 / 7, note vtable, template slot 7 -> ours")
    check(drums18.decode_bw(img, V.T_PAD_SITE) == L["c_vpad"] and drums18.decode_bw(img, s14.SVC_HOOK) == L["c_vtick"], "pad site -> c_vpad, head of the DSP chain -> c_vtick")
    check(len(img) <= 0x70000 and 0x20044E58 - int(man["report"]["sc17"]["sc14_state"], 16) == 220, f"image {len(img):#x} bytes, RAM reservation unchanged (220)")

    gc.collect(); e = E20(img, man)
    # ---- power-up tick: defaults, ACT, then every value; one message per voice per tick
    msgs = []
    for _ in range(30): msgs += [(i, w, ad) for i, (w, ad) in enumerate(e.vtick())]
    per = {0: [w for (_, w, ad) in msgs if ad == VD.VB0], 1: [w for (_, w, ad) in msgs if ad == VD.VB0 + VD.VBS]}
    exp = [(19, 0), (18, 60)] + [(c + 1 + (5 if c >= 16 else 0), V.DEFAULTS[c]) for c in range(26)]
    for t in (0, 1):
        want = [((i & 1) << 23) | (code << 16) | (val & 0xFFFF) for i, (code, val) in enumerate(exp)]
        check(per[t] == want, f"voice {t + 1}: power-up sends ACT = 0, NOTE = 60 (key tracking neutral) and the 26 default values (codes 1..16, then 22..31 of the oscillator page), one per tick, tags toggling ({len(per[t])} messages)")
    check(e.vtick() == [] and e.tailb(V.O_FLAGS) == 0x80, "then nothing while idle; the tail is initialised (flag bit 7)")
    check(all(e.val(t, c + 1) == V.DEFAULTS[c] for t in (0, 1) for c in range(26)) and e.val(0, 19) == 0 and e.val(0, 20) == 50 and e.val(0, 10) == 0 and e.val(0, 15) == 63 and e.val(0, 7) == 127 and e.val(0, 6) == 0 and e.val(0, 8) == 0, "the defaults are in the tail (neutral gate: GAIN 0, ENVA 63, SUS 127, DEC / REL 0; WAVE 0 = sine, PW 50 = the centre)")

    # ---- the Preset view of MIDI 1: toggle pad
    e.btn(2); e.btn(8)
    v = e.r32(MGR + 0x6C)
    check(e.cur() == 0 + 9 * 2 + 0, f"MIDI 1 + Preset: view index {e.cur()}")
    led = e.tleds(TMPL[0])
    check(led[V.PAD_VCF] == V.COL_OFF, f"pad 26 dim yellow ({led[V.PAD_VCF]:#x}), the patch flip pad {led[V.PAD_FLIP]:#x}")
    e.padr(V.PAD_VCF); e.rel(V.PAD_VCF)
    check(e.tailb(V.O_FLAGS) == 0x81 and e.tleds(TMPL[0])[V.PAD_VCF] == V.COL_ON and e.saves, f"pad 26: mode on for MIDI 1 (flags {e.tailb(V.O_FLAGS):#x}), bright yellow, the settings save requested")
    out = e.vtick()
    check(out and out[0][1] == VD.VB0 and (out[0][0] & 0x7FFFFF) == (19 << 16 | 1), f"tick: ACT = 1 to voice 1 {[hex(w) for w, a in out]}")
    got = []
    for _ in range(26): got += [w for w, ad in e.vtick() if ad == VD.VB0]
    check([(w >> 16) & 0x1F for w in got] == list(range(1, 17)) + list(range(22, 32)), "then all 26 values are sent again (switching on): codes 1..16 and 22..31")
    # patch flip: pressing it turns the mode off when the flip turns on
    p2 = e.settings_p2()
    e.padr(V.PAD_FLIP); e.rel(V.PAD_FLIP)
    check(e.tailb(V.O_FLAGS) == 0x80 and (e.settings_p2() >> 26) & 1 == 1 and (p2 >> 26) & 1 == 0, "patch flip pressed (turning on): the mode of the track turns off")
    e.padr(V.PAD_VCF); e.rel(V.PAD_VCF)
    check(e.tailb(V.O_FLAGS) == 0x81 and (e.settings_p2() >> 26) & 1 == 0, "pad 26 pressed: the mode turns on and the patch flip of the track turns off")
    e.padr(V.PAD_VCF); e.rel(V.PAD_VCF)
    check(e.tailb(V.O_FLAGS) == 0x80, "pad 26 again: off")
    e.padr(V.PAD_VCF); e.rel(V.PAD_VCF)                                                           # on again for the next tests
    # ---- SC23.2: pad 27 = the start of the chain only, pad 28 = oscillator view, pad 29 = VCA / VCF view
    for _ in range(40): e.vtick()
    led = e.tleds(TMPL[0])
    check(led[V.PAD_OSC] == V.COL_OSC[1] and led[V.PAD_PAGE] == V.COL_OSC[1] and led[V.PAD_VCF] == V.COL_ON != V.COL_OSC[0] and e.tailb(V.O_FLAGS) == 0x81, f"pad 29 lit (VCA / VCF view), 27 / 28 dim ({led[V.PAD_OSC]:#x}, {led[V.PAD_PAGE]:#x})")
    e.saves.clear()
    e.padr(V.PAD_PAGE); e.rel(V.PAD_PAGE)
    led = e.tleds(TMPL[0])
    check(e.tailb(V.O_FLAGS) == 0x91 and led[V.PAD_PAGE] == V.COL_OSC[0] and led[V.PAD_VCF] == V.COL_OFF and e.saves, f"pad 28 (mode on, page A): the oscillator view, the mode stays on (flags {e.tailb(V.O_FLAGS):#x}), 28 bright and 29 dim, the settings save requested")
    check(e.tleds(TMPL[1])[V.PAD_PAGE] == V.COL_OSC[1], "MIDI 2's pads stay dim")
    check([w for _ in range(6) for (w, ad) in e.vtick()] == [], "switching the view sends nothing to the DSP")
    e.padr(V.PAD_VCF); e.rel(V.PAD_VCF)
    led = e.tleds(TMPL[0])
    check(e.tailb(V.O_FLAGS) == 0x81 and led[V.PAD_VCF] == V.COL_ON and led[V.PAD_PAGE] == V.COL_OSC[1], f"pad 29: back to the VCA / VCF view, mode on (flags {e.tailb(V.O_FLAGS):#x}), 29 bright and 28 dim")
    e.padr(V.PAD_PAGE); e.rel(V.PAD_PAGE)
    out = [(w, ad) for _ in range(6) for (w, ad) in e.vtick()]
    e.padr(V.PAD_PAGE); e.rel(V.PAD_PAGE)
    led = e.tleds(TMPL[0])
    check(e.tailb(V.O_FLAGS) & 1 == 0 and led[V.PAD_PAGE] == V.COL_OSC[1] and led[V.PAD_VCF] == V.COL_OFF, f"pad 28 again (it was lit): the mode goes off, both views dim (flags {e.tailb(V.O_FLAGS):#x})")
    out = [(w, ad) for _ in range(6) for (w, ad) in e.vtick()]
    check([((w >> 16) & 0x1F, w & 0xFFFF) for w, ad in out if ad == VD.VB0] == [(19, 0)] and e.tailb(V.O_FLAGS) & 1 == 0, f"ACT = 0 sent {[((w >> 16) & 0x1F, w & 0xFFFF) for w, ad in out]}")
    e.padr(V.PAD_PAGE); e.rel(V.PAD_PAGE)
    got = []
    for _ in range(30): got += [(w >> 16) & 0x1F for w, ad in e.vtick() if ad == VD.VB0]
    check(e.tailb(V.O_FLAGS) == 0x91 and got[0] == 19 and sorted(got[1:]) == list(range(1, 17)) + list(range(22, 32)), f"pad 28 with the mode off: the mode goes on in the oscillator view (flags {e.tailb(V.O_FLAGS):#x}), ACT and all 26 values are sent")
    e.padr(V.PAD_VCF); e.rel(V.PAD_VCF); e.padr(V.PAD_VCF); e.rel(V.PAD_VCF)
    check(e.tailb(V.O_FLAGS) == 0x80, f"pad 29 (page A), pad 29 again: the mode goes off (flags {e.tailb(V.O_FLAGS):#x})")
    for _ in range(40): e.vtick()
    # patch flip: it turns the mode off, and the mode turns it off
    e.padr(V.PAD_VCF); e.rel(V.PAD_VCF)
    p2 = e.settings_p2()
    e.padr(V.PAD_FLIP); e.rel(V.PAD_FLIP)
    check(e.tailb(V.O_FLAGS) == 0x80 and (e.settings_p2() >> 26) & 1 == 1 and (p2 >> 26) & 1 == 0, "patch flip pressed (turning on): the mode of the track turns off")
    e.padr(V.PAD_PAGE); e.rel(V.PAD_PAGE)
    check(e.tailb(V.O_FLAGS) == 0x91 and (e.settings_p2() >> 26) & 1 == 0, f"pad 28 pressed: the mode turns on (oscillator view) and the patch flip of the track turns off (flags {e.tailb(V.O_FLAGS):#x})")
    e.padr(V.PAD_VCF); e.rel(V.PAD_VCF)
    for _ in range(40): e.vtick()
    # the source pad: only the start of the chain
    e.saves.clear()
    e.padr(V.PAD_OSC); e.rel(V.PAD_OSC)
    check(e.tailb(V.O_FLAGS) == 0x85 and e.val(0, 10) == 0 and e.val(0, 15) == 63 and e.tleds(TMPL[0])[V.PAD_OSC] == V.COL_OSC[0] and e.saves,
          f"pad 27 (mode on): oscillator on for MIDI 1 (flags {e.tailb(V.O_FLAGS):#x}), bright, GAIN {e.val(0, 10)} ENVA {e.val(0, 15)} (the neutral gate, untouched), the settings save requested")
    out = [(w, ad) for _ in range(6) for (w, ad) in e.vtick()]
    check([((w >> 16) & 0x1F, w & 0xFFFF) for w, ad in out if ad == VD.VB0] == [(19, 2)] and not [1 for w, ad in out if ad != VD.VB0], f"ticks: ACT = 2 to voice 1 only (GAIN / ENVA are not touched) {[((w >> 16) & 0x1F, w & 0xFFFF) for w, ad in out]}")
    check(e.tleds(TMPL[0])[V.PAD_VCF] == V.COL_ON and e.tleds(TMPL[1])[V.PAD_OSC] == V.COL_OSC[1], "the view pad stays bright; MIDI 2's oscillator pad stays dim")
    e.padr(V.PAD_OSC); e.rel(V.PAD_OSC)
    out = [(w, ad) for _ in range(6) for (w, ad) in e.vtick()]
    check(e.tailb(V.O_FLAGS) == 0x81 and e.val(0, 10) == 0 and e.val(0, 15) == 63 and [((w >> 16) & 0x1F, w & 0xFFFF) for w, ad in out] == [(19, 1)] and e.tleds(TMPL[0])[V.PAD_OSC] == V.COL_OSC[1],
          "pad 27 again: oscillator off, ACT = 1 (GAIN / ENVA stay at the neutral gate)")
    e.padr(V.PAD_VCF); e.rel(V.PAD_VCF)                                                           # the mode off
    for _ in range(40): e.vtick()
    e.padr(V.PAD_OSC); e.rel(V.PAD_OSC)
    out = [(w, ad) for _ in range(6) for (w, ad) in e.vtick()]
    check(e.tailb(V.O_FLAGS) == 0x84 and e.tleds(TMPL[0])[V.PAD_OSC] == V.COL_OSC[0] and e.tleds(TMPL[0])[V.PAD_VCF] == V.COL_OFF and [((w >> 16) & 0x1F, w & 0xFFFF) for w, ad in out] == [(19, 0)],
          f"pad 27 with the mode off: only the source changes, the mode stays off (flags {e.tailb(V.O_FLAGS):#x}), ACT stays 0")
    e.padr(V.PAD_VCF); e.rel(V.PAD_VCF)
    got = []
    for _ in range(30): got += [((w >> 16) & 0x1F, w & 0xFFFF) for w, ad in e.vtick() if ad == VD.VB0]
    check(e.tailb(V.O_FLAGS) == 0x85 and got[0] == (19, 2), f"then pad 29 switches the mode on with the oscillator source: ACT = 2 (flags {e.tailb(V.O_FLAGS):#x})")
    e.padr(V.PAD_OSC); e.rel(V.PAD_OSC)
    for _ in range(40): e.vtick()
    check(e.tailb(V.O_FLAGS) == 0x81, f"oscillator off: the plain VCA / VCF mode for the next tests (flags {e.tailb(V.O_FLAGS):#x})")
    check((V.PAD_FLIP, V.PAD_OSC, V.PAD_PAGE, V.PAD_VCF) == (25, 26, 27, 28) and led[24] == V.COL_CC[1], f"pad order: 25 (index 24) the CC editor ({led[24]:#x}), 26 patch flip, 27 oscillator source, 28 oscillator edit, 29 VCF / VCA mode")
    check(len({V.COL_ON, V.COL_OFF, V.COL_OSC[0], V.COL_OSC[1], 0x02, 0x12}) == 6, "the VCF / VCA pad (orange), the oscillator pads (green) and the stock patch flip colours (0x02 / 0x12) are all different")
    # the knob page B
    e.btn(2); e.track(2)
    snap = e.tail()[1:25]
    e.knob_raw(0, 3)
    check(e.val(0, 5) == V.DEFAULTS[4] + 3, "page A: K1 is ATK")
    e.knob_raw(0, -3)
    e.btn(8)
    e.padr(V.PAD_PAGE); e.rel(V.PAD_PAGE)
    check(e.tailb(V.O_FLAGS) == 0x91 and e.tleds(TMPL[0])[V.PAD_PAGE] == V.COL_OSC[0] and e.tleds(TMPL[1])[V.PAD_PAGE] == V.COL_OSC[1], f"pad 28: knob page B for MIDI 1 (flags {e.tailb(V.O_FLAGS):#x}), the pad lights green")
    for _ in range(30): e.vtick()
    e.btn(2); e.track(2)
    snap = e.tail()[1:53]
    e.knob_raw(0, 3); check(e.val(0, 17) == 3 and e.val(0, 5) == V.DEFAULTS[4], "page B: K1 = TUNE (3), ATK untouched")
    e.knob_raw(0, 5, True); check(e.val(0, 18) == 5 and e.val(0, 11) == V.DEFAULTS[10], "page B: Shift + K1 = FINE (5)")
    e.knob_raw(0, 127); check(e.val(0, 17) == 63, "TUNE clamps at 63"); e.knob_raw(0, -127); check(e.val(0, 17) == -64, "TUNE clamps at -64")
    e.knob_raw(6, 4); check(e.val(0, 19) == 4, "page B: K7 = WAVE (the morph position) moves by the turn: 0 -> 4")
    e.knob_raw(6, 127); check(e.val(0, 19) == 127, "WAVE clamps at 127"); e.knob_raw(6, -127); check(e.val(0, 19) == 0, "WAVE clamps at 0 (no wrap: it is a continuous position now)")
    e.knob_raw(1, 10); check(e.val(0, 20) == 60, "page B: K2 = SHAPE / PW (50 -> 60)")
    e.knob_raw(1, 127); check(e.val(0, 20) == 100, "PW clamps at 100"); e.knob_raw(1, -127); check(e.val(0, 20) == 0, "PW clamps at 0")
    e.knob_raw(2, 127); check(e.val(0, 22) == 63, "page B: K3 = ENVP (envelope -> pitch, bipolar) clamps at 63"); e.knob_raw(2, -127); check(e.val(0, 22) == -64, "ENVP clamps at -64")
    e.knob_raw(3, 127); check(e.val(0, 23) == 63, "page B: K4 = ENVW (envelope -> shape) clamps at 63"); e.knob_raw(3, -127); check(e.val(0, 23) == -64, "ENVW clamps at -64")
    e.knob_raw(4, 127); check(e.val(0, 21) == 63, "page B: K5 = LFOP (LFO -> pitch) clamps at 63"); e.knob_raw(4, -127); check(e.val(0, 21) == -64, "LFOP clamps at -64")
    e.knob_raw(5, 127); check(e.val(0, 24) == 63, "page B: K6 = LFOW (LFO -> shape) clamps at 63"); e.knob_raw(5, -127); check(e.val(0, 24) == -64, "LFOW clamps at -64")
    e.knob_raw(7, 127); check(e.val(0, 26) == 63, "page B: K8 = LFOM (LFO -> morph) clamps at 63"); e.knob_raw(7, -127); check(e.val(0, 26) == -64, "LFOM clamps at -64")
    e.knob_raw(7, 127, True); check(e.val(0, 25) == 63, "page B: Shift + K8 = ENVM (envelope -> morph) clamps at 63"); e.knob_raw(7, -127, True); check(e.val(0, 25) == -64, "ENVM clamps at -64")
    before = e.tail()
    for k in range(1, 7): e.knob_raw(k, 5, True)
    check(e.tail()[1:53] == before[1:53], "page B: Shift + K2..K7 have no function (the values do not change)")
    out = [(w, ad) for _ in range(40) for (w, ad) in e.vtick()]
    codes = [((w >> 16) & 0x1F) for w, ad in out if ad == VD.VB0]
    check(codes and all(c in range(22, 32) for c in codes) and set(codes) == set(range(22, 32)) and not [1 for w, ad in out if ad != VD.VB0], f"page B values go to the DSP as codes 22..31 {sorted(set(codes))} (voice 1 only)")
    fr = e.frame()
    cols = V.COL_TRACK[0]
    want = [level(0, c, e.tailb(V.O_PAR + c - 1)) if c else 0 for c in V.KNOB_CODES_B[:8]]
    kb = [k for k in range(8) if not (TZ and V.KNOB_CODES_B[k] == 19)]                                  # SC23.6: the waveform knob shows the mode colour (emu_sc23_6.py)
    check([((fr[60 + k] >> 8) - 2) for k in kb] == [want[k] for k in kb] and all((fr[60 + k] & 0xFF) == cols for k in kb), f"page B knob LEDs: levels {[(fr[60 + k] >> 8) - 2 for k in range(8)]} (Shift layer: K1 and K8 only)")
    e.set_p0(e.r32(MGR + 0xC), 1); fs = e.frame(); e.set_p0(e.r32(MGR + 0xC), 0)
    want = [level(0, c, e.tailb(V.O_PAR + c - 1)) if c else 0 for c in V.KNOB_CODES_B[8:]]
    check([((fs[60 + k] >> 8) - 2) for k in range(8)] == want, f"page B with Shift: the second layer {[(fs[60 + k] >> 8) - 2 for k in range(8)]}")
    e.btn(8); e.padr(V.PAD_VCF); e.rel(V.PAD_VCF)
    check(e.tailb(V.O_FLAGS) == 0x81, "pad 29: page A, the mode stays on")
    e.btn(2); e.track(2)
    e.knob_raw(0, 3); check(e.val(0, 5) == V.DEFAULTS[4] + 3 and e.val(0, 17) == -64, "back on page A: K1 is ATK again"); e.knob_raw(0, -3)
    # MIDI 2: its own flags (bits 3 / 5), voice 2
    e.btn(3); e.btn(8)
    for _ in range(40): e.vtick()
    e.padr(V.PAD_VCF); e.rel(V.PAD_VCF); e.padr(V.PAD_OSC); e.rel(V.PAD_OSC)
    check(e.tailb(V.O_FLAGS) == 0x8B and e.val(1, 10) == 0 and e.val(1, 15) == 63 and e.val(0, 10) == V.DEFAULTS[9], f"MIDI 2: mode + oscillator (flags {e.tailb(V.O_FLAGS):#x}), its GAIN / ENVA changed, MIDI 1's untouched")
    out = [(w, ad) for _ in range(40) for (w, ad) in e.vtick()]
    acts = [(w & 0xFFFF) for w, ad in out if ad == VD.VB0 + VD.VBS and (w >> 16) & 0x1F == 19]
    check(acts and acts[-1] == 2 and not [1 for w, ad in out if ad == VD.VB0], f"ACT = 2 to voice 2 {acts}, voice 1 silent")
    e.padr(V.PAD_PAGE); e.rel(V.PAD_PAGE)
    check(e.tailb(V.O_FLAGS) == 0xAB, f"MIDI 2 page B (flags {e.tailb(V.O_FLAGS):#x})")
    e.padr(V.PAD_OSC); e.rel(V.PAD_OSC); e.padr(V.PAD_VCF); e.rel(V.PAD_VCF); e.padr(V.PAD_VCF); e.rel(V.PAD_VCF)
    check(e.tailb(V.O_FLAGS) == 0x81, f"MIDI 2 back to off (flags {e.tailb(V.O_FLAGS):#x})")
    for _ in range(40): e.vtick()
    e.btn(2); e.btn(8)
    for _ in range(40): e.vtick()

    # ---- knobs
    e.btn(2)                                                                         # the track view of MIDI 1
    check(e.view() != TMPL[0], "MIDI 1 pressed again: its track view")
    h = e.mh_obj() if hasattr(e, "mh_obj") else None
    stock_before = bytes(e.uc.mem_read(e.r32(MGR + 0x198 + 4 * 2) + 0xC, 24))
    for idx in range(16):
        code, k, shift = V.KNOB_CODES[idx], idx % 8, idx >= 8
        if code == 0: continue                                                       # SC23.6: Shift + K7 has no function (emu_sc23_6.py)
        old = e.val(0, code)
        e.knob_raw(k, 3, shift)
        new = e.val(0, code)
        if code == 13 and not TZ: want = (old + 1) % V.FXTYPE_N
        elif code == 16 and not TZ: want = (old + 1) % V.FTYPE_N
        elif (V.BIPOLAR_MASK >> (code - 1)) & 1: want = max(-64, min(63, old + 3))
        else: want = max(0, min(127, old + 3))
        check(new == want, f"knob {k + 1}{' + Shift' if shift else ''}: code {code} {old} -> {new}")
    e.knob_raw(4, -127, False); check(e.val(0, 1) == -64, "K5 (FILT) clamps at -64")
    e.knob_raw(4, 127, False); check(e.val(0, 1) == 63, "K5 (FILT) clamps at 63")
    e.knob_raw(5, 127, False); check(e.val(0, 2) == 127, "K6 (RES) clamps at 127"); e.knob_raw(5, -127, False); check(e.val(0, 2) == 0, "K6 (RES) clamps at 0")
    if not TZ:                                                                       # SC23.6: the type knobs clamp instead (emu_sc23_6.py)
        e.knob_raw(7, -3, True); e.knob_raw(7, -3, True); check(e.val(0, 13) == V.FXTYPE_N - 1, "Shift + K8 (FX type) wraps below 0 to 6 (chorus)")
        e.knob_raw(4, 3, True); e.knob_raw(4, 3, True); e.knob_raw(4, 3, True); e.knob_raw(4, 3, True); check(e.val(0, 16) == (V.DEFAULTS[15] + 1 + 4) % V.FTYPE_N, "Shift + K5 (filter type) steps one per turn and wraps 0..6 (DJ, LP 12, HP 12, band-pass, notch, LP 24, HP 24)")
        e.knob_raw(4, 3, True); e.knob_raw(4, 3, True); e.knob_raw(4, 3, True)
        while e.val(0, 16) != 0: e.knob_raw(4, 3, True)
        e.knob_raw(4, -3, True); check(e.val(0, 16) == V.FTYPE_N - 1, "Shift + K5 to the left from 0: wraps to the last type (6 = HP 24)")
    e.knob_raw(5, 127, True); check(e.val(0, 10) == 127, "Shift + K6 (GAIN) clamps at 127"); e.knob_raw(5, -127, True); check(e.val(0, 10) == 0, "Shift + K6 (GAIN) clamps at 0 (closed)")
    e.knob_raw(3, 127, False); check(e.val(0, 3) == 63, "K4 (ENVF, bipolar) clamps at 63")
    e.knob_raw(2, 127, False); check(e.val(0, 15) == 63, "K3 (ENVA, bipolar send) clamps at 63"); e.knob_raw(2, -127, False); check(e.val(0, 15) == -64, "K3 (ENVA) goes negative: clamps at -64")
    e.knob_raw(2, 127, True); check(e.val(0, 12) == 63, "Shift + K3 (LFOV, bipolar send) clamps at 63"); e.knob_raw(2, -127, True); check(e.val(0, 12) == -64, "Shift + K3 (LFOV) clamps at -64")
    check(V.DEFAULTS[14] == 63 and V.DEFAULTS[11] == 0, "the defaults: ENVA +63 (the envelope opens the VCA), LFOV 0 (no tremolo)")
    check(bytes(e.uc.mem_read(e.r32(MGR + 0x198 + 4 * 2) + 0xC, 24)) == stock_before, "the stock macro store of the track is untouched by the knobs")
    sends = [(w, ad) for _ in range(60) for (w, ad) in e.vtick()]
    check(sends and all(ad == VD.VB0 for w, ad in sends), f"the changed values go to voice 1 only ({len(sends)} messages)")
    check(e.saves, f"settings save requested ({len(e.saves)} calls: throttled)")
    # the second track's knobs and the synths' are stock
    e.btn(3)
    def stock_el(t, i):
        e.call(0x0803542C, e.r32(MGR + 0x198 + 4 * t), i); return e.r8(e.uc.reg_read(UC_ARM_REG_R0))
    s0 = stock_el(3, 0)
    e.knob_raw(0, 5, False)
    check(e.val(1, 1) == V.DEFAULTS[0] and stock_el(3, 0) == min(127, s0 + 5), f"MIDI 2 (mode off): its knobs are the stock ones (macro 1 {s0} -> {stock_el(3, 0)}), not ours")
    e.btn(0)
    s1 = stock_el(0, 0); e.knob_raw(0, 3, False)
    check(stock_el(0, 0) == min(127, s1 + 3), "Synth 1: the knobs are the stock ones")

    # ---- knob LEDs
    e.btn(2)
    e.track(2)
    fr = e.frame(); fs = None
    cols = V.COL_TRACK[0]
    byt = [e.tailb(V.O_PAR + c) for c in range(16)]
    ok = all(((fr[60 + k] >> 8) - 2) == level(0, V.KNOB_CODES[k], byt[V.KNOB_CODES[k] - 1]) and (fr[60 + k] & 0xFF) == cols for k in range(8))
    check(ok, f"MIDI 1 knob LEDs: track colour {cols:#x} + brightness of the values {[hex(x) for x in fr[60:68]]}")
    e.set_p0(e.r32(MGR + 0xC), 1); fs = e.frame(); fs2 = e.frame(); e.set_p0(e.r32(MGR + 0xC), 0)
    ok = all(((fs[60 + k] >> 8) - 2) == level(0, V.KNOB_CODES[8 + k], byt[V.KNOB_CODES[8 + k] - 1]) for k in range(8) if not (TZ and V.KNOB_CODES[8 + k] in (0, 13, 16))) and fs == fs2
    check(ok, "with Shift: the second layer, a second frame identical")
    e.track(3)
    f3 = e.frame()
    check(all(f3[60 + k] >> 8 == 0 or f3[60 + k] >= 0xC1 for k in range(8)), f"MIDI 2 (mode off): the stock LED codes {[hex(x) for x in f3[60:68]]}")

    # ---- notes: a fresh power-up, MIDI 1 selected, the mode set; pads 20..31 of the track view play notes 79.. / 60.. through the note vtable
    gc.collect(); e = E20(img, man)
    for _ in range(24): e.vtick()
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([0x81]))
    e.btn(2); e.notes.clear()
    e.padr(24)
    check(e.rt(0, V.RT_CNT) == 1 and e.rt(0, V.RT_AUX) & 0x1E == 0x1E and e.notes and e.notes[0][2] == 2 and e.rt(0, V.RT_NOTE) == e.notes[0][3] == 60 and e.rt(0, V.RT_VEL) == e.notes[0][4] == 96,
          f"note on (pad 24): 1 held, note {e.rt(0, V.RT_NOTE)} / velocity {e.rt(0, V.RT_VEL)} remembered, NOTE VEL GATE TRIG flagged; SC06's wrapper still gets the call {[(r1, r2, r3) for a_, r0, r1, r2, r3 in e.notes[:1]]}")
    msgs = [w for _ in range(8) for (w, ad) in e.vtick() if ad == VD.VB0]
    codes = [(w >> 16) & 0x1F for w in msgs]
    check(codes[:4] == [18, 20, 17, 21] and (msgs[2] & 0xFFFF) == 1 and (msgs[0] & 0xFFFF) == 60 and (msgs[1] & 0xFFFF) == 96, f"ticks: NOTE 60, VEL 96, GATE = 1, TRIG {codes[:5]}")
    e.rel(24)
    check(e.rt(0, V.RT_CNT) == 0 and e.rt(0, V.RT_AUX) & 8, "note off: gate flagged, nothing else")
    msgs = [w for _ in range(4) for (w, ad) in e.vtick() if ad == VD.VB0]
    check([(w >> 16) & 0x1F for w in msgs][:1] == [17] and (msgs[0] & 0xFFFF) == 0, "tick: GATE = 0")
    e.padr(24); e.padr(25)
    check(e.rt(0, V.RT_CNT) == 2 and e.rt(0, V.RT_NOTE) == 62, "two notes held (the last note is remembered)")
    e.vtick(); e.vtick(); e.vtick(); e.vtick(); e.vtick()
    e.rel(24)
    check(e.rt(0, V.RT_CNT) == 1 and not e.rt(0, V.RT_AUX) & 8, "one released: the gate stays on (nothing flagged)")
    e.rel(25)
    check(e.rt(0, V.RT_CNT) == 0 and e.rt(0, V.RT_AUX) & 8, "both released: gate off flagged")
    for _ in range(12): e.vtick()
    # a note with the mode off: not counted (MIDI 2)
    e.btn(3); e.padr(24); e.rel(24)
    check(e.rt(1, V.RT_CNT) == 0 and e.rt(1, V.RT_AUX) == 0, "MIDI 2 (mode off): no note bookkeeping")
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([0x80]))
    e.btn(2); e.padr(24); e.rel(24)
    check(e.rt(0, V.RT_CNT) == 0, "mode off again: MIDI 1 notes are not counted")
    # ---- end to end: every message the ARM sent in a session, played into the real DSP program one per block, ends in the DSP with the values / gate / note of the tail
    from dspemu import run
    from dsp_session import dsp_program
    gc.collect(); e = E20(img, man)
    for _ in range(24): e.vtick()
    e.call(L["c_vset"], 0, 1); e.vtick()                                              # as the toggle pad does: mode on, ACT and every value flagged
    e.btn(2)
    e.knob_raw(0, -30); e.knob_raw(1, 20); e.knob_raw(2, 25); e.knob_raw(4, 10); e.knob_raw(0, 7, True); e.knob_raw(4, 5, True); e.knob_raw(7, 5, True)
    e.padr(24)
    e.call(L["c_vsetosc"], 0, 1)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.tailb(V.O_FLAGS) | 0x10]))
    e.knob_raw(0, -7); e.knob_raw(6, 1); e.knob_raw(0, 9, True); e.knob_raw(1, 5); e.knob_raw(2, 12); e.knob_raw(4, 5); e.knob_raw(3, 6); e.knob_raw(5, -7); e.knob_raw(7, -4); e.knob_raw(7, 9, True)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.tailb(V.O_FLAGS) & ~0x10]))
    for _ in range(120): e.vtick()
    msgs = e.sent
    check(len(msgs) > 40, f"{len(msgs)} messages in the session")
    sp = dsp_program(img); P0 = [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]
    dl = {k: int(v, 16) for k, v in man["report"]["sc16"]["dsp_labels"].items()}
    blk = [0] * (2 * VD.VBS); osb = [0] * 96
    for w, ad in msgs:
        blk[ad - VD.VB0 + VD.MB] = w & 0xFFFFFF
        res, ran = run(P0, dl["vpre"], mem=[('x', 0x3A, [32]), ('x', VD.VB0, blk), ('x', VD.FLAGS, [0]), ('y', VD.RING_PTR, [0x1000]), ('y', 0x1000, [0] * 64), ('x', VD.OSB0, osb)], dumps=[('x', VD.VB0, 2 * VD.VBS), ('x', VD.OSB0, 96)], regs_code=[])
        blk = res[('x', VD.VB0)]; osb = res[('x', VD.OSB0)]
    sx = lambda v: v - (1 << 24) if v & 0x800000 else v
    cs = [c for c in range(1, 17) if not (TZ and c in (13, 14, 16))]                                    # SC23.6: the DSP derives these (zone and parameter); emu_sc23_6_dsp.py
    ok = all(sx(blk[1 + c]) == e.val(0, c) for c in cs) and blk[VD.ACT] == 2 and all(blk[VD.VBS + 1 + c] == V.DEFAULTS[c - 1] for c in cs) and blk[VD.VBS + VD.ACT] == 0
    check(ok, f"the DSP block of voice 1 = the 16 values of the tail {[sx(blk[1 + c]) for c in range(1, 17)]}, ACT 1; voice 2 = defaults, ACT 0")
    check(blk[VD.GATE] == 1 and blk[VD.NOTE] == 60 and blk[VD.VEL] == 96, f"gate on, note {blk[VD.NOTE]}, velocity {blk[VD.VEL]} reached the DSP")
    check([sx(osb[k]) for k in range(10)] == [e.val(0, 17 + k) for k in range(10)] and [e.val(0, 17 + k) for k in range(10)] == [-7, 9, 1, 55, 5, 12, 6, -7, 9, -4] and osb[48:58] == [0, 0, 0, 50, 0, 0, 0, 0, 0, 0], f"the oscillator block of voice 1 = the page B values {[sx(osb[k]) for k in range(10)]} (tune -7, fine 9, wave 1, shape 55, LFO pitch 5, envelope pitch 12, envelope shape 6, LFO shape -7, envelope morph 9, LFO morph -4); voice 2 = defaults")
    check(V.TAIL >= V.SETOBJ + 8 and V.TAIL + 75 <= V.SETOBJ + 0x88, "the tail lies inside the 0x80 bytes of the settings record (obj + 8 .. obj + 0x88) that the stock save writes")
        # ---- the state of the tail is validated: a tail of 0xFF / garbage (or the SC20 state, another signature) is re-initialised instead of read as "modes on"
    gc.collect(); e = E20(img, man)
    e.uc.mem_write(V.TAIL, bytes([0xFF]) * 75)
    for _ in range(4): e.vtick()
    check(e.tailb(V.O_FLAGS) == 0x80 and e.tailb(V.O_SIG) == V.SIG_VAL and all(e.val(t, c + 1) == V.DEFAULTS[c] for t in (0, 1) for c in range(26)), "a tail of 0xFF: both modes off, defaults, signature written")
    e.uc.mem_write(V.TAIL, bytes([0x81]) + bytes(74)); e.uc.mem_write(V.TAIL + V.O_SIG, bytes([0xA5]))
    gc.collect(); e2 = E20(img, man); e2.uc.mem_write(V.TAIL, bytes([0x81]) + bytes(74)); e2.uc.mem_write(V.TAIL + V.O_SIG, bytes([0xA5]))
    for _ in range(4): e2.vtick()
    check(e2.tailb(V.O_FLAGS) == 0x80 and e2.val(0, 10) == V.DEFAULTS[9], "the state of SC20 / SC20.1 (signature 0xA5, flags 0x81): re-initialised (the values mean other things now)")
    gc.collect(); e3 = E20(img, man); e3.uc.mem_write(V.TAIL, bytes([0x81]) + bytes([7]) * 48 + bytes(26)); e3.uc.mem_write(V.TAIL + V.O_SIG, bytes([V.SIG_VAL]))
    for _ in range(4): e3.vtick()
    check(e3.tailb(V.O_FLAGS) == 0x81 and e3.val(0, 5) == 7, "a tail with our signature is kept as saved")
    gc.collect(); e4 = E20(img, man); e4.uc.mem_write(V.TAIL, bytes([0x81]) + bytes([3]) * 48 + bytes(26)); e4.uc.mem_write(V.TAIL + V.O_SIG, bytes([0xA6]))
    for _ in range(4): e4.vtick()
    check(e4.tailb(V.O_FLAGS) == 0x80 and e4.val(0, 16) == 0, "the state of SC21 (signature 0xA6, a filter type of 3 = tilt possible): re-initialised")
    gc.collect(); e5 = E20(img, man); e5.uc.mem_write(V.TAIL, bytes([0x81]) + bytes([3]) * 32 + bytes(42)); e5.uc.mem_write(V.TAIL + V.O_SIG, bytes([0xA9]))
    for _ in range(4): e5.vtick()
    check(e5.tailb(V.O_FLAGS) == 0x80 and e5.val(0, 16) == 0, "the state of SC22 (signature 0xA9, values at stride 16): re-initialised")
    gc.collect(); e6 = E20(img, man); e6.uc.mem_write(V.TAIL, bytes([0x81]) + bytes([3]) * 48 + bytes(26)); e6.uc.mem_write(V.TAIL + 66, bytes([0xAA]))
    for _ in range(4): e6.vtick()
    check(e6.tailb(V.O_FLAGS) == 0x80 and e6.val(0, 16) == 0, "the state of SC22.1 (signature 0xAA, five oscillator values): re-initialised")
    gc.collect(); e7 = E20(img, man); e7.uc.mem_write(V.TAIL, bytes([0x81]) + bytes([3]) * 48 + bytes(26)); e7.uc.mem_write(V.TAIL + 66, bytes([0xAB]))
    for _ in range(4): e7.vtick()
    check(e7.tailb(V.O_FLAGS) == 0x80 and e7.val(0, 16) == 0, "the state of SC22.2 (signature 0xAB, values at stride 24): re-initialised")
    # ---- SC23.3: Clear + a knob puts the value back to its default; the knob is red while Clear is held
    gc.collect(); e8 = E20(img, man)
    for _ in range(24): e8.vtick()
    e8.call(L["c_vset"], 0, 1); e8.vtick(); e8.btn(2)
    clr_dn = lambda: e8.call(0x08033320, MGR, 23, maxins=900000)
    clr_up = lambda: e8.call(0x0803381A, MGR, 23, maxins=900000)
    e8.knob_raw(0, 25); e8.knob_raw(2, -73); e8.knob_raw(0, -77, True); e8.knob_raw(4, -30)
    check((e8.val(0, 5), e8.val(0, 15), e8.val(0, 7), e8.val(0, 1)) == (25, -10, 50, -30), f"values changed: ATK {e8.val(0, 5)}, ENVA {e8.val(0, 15)}, SUS {e8.val(0, 7)}, FILT {e8.val(0, 1)}")
    for _ in range(60): e8.vtick()
    fr0 = e8.frame()
    clr_dn()
    e8.vtick()
    e8.knob_raw(0, 1)
    fr = e8.frame()
    check(e8.val(0, 5) == V.DEFAULTS[4] == 0 and e8.val(0, 15) == -10, f"Clear + K1: ATK back to its default ({e8.val(0, 5)}); the other values are kept")
    check(fr[60] == V.CLR_RED and all(fr[60 + k] == fr0[60 + k] for k in range(1, 8)), f"K1 is red while Clear is held ({fr[60]:#x}), the other knobs as before")
    out = [(w >> 16) & 0x1F for _ in range(8) for (w, ad) in e8.vtick() if ad == VD.VB0]
    check(5 in out, f"the new value is sent to the DSP (codes {out})")
    e8.knob_raw(2, 4)
    check(e8.val(0, 15) == V.DEFAULTS[14] == 63, f"Clear + K3 (bipolar): ENVA back to its default +63 ({e8.val(0, 15)}), whichever the direction of the turn")
    fr = e8.frame()
    check(fr[60] == V.CLR_RED and fr[62] == V.CLR_RED, "K1 and K3 are red")
    e8.knob_raw(0, -77 + 77, True) if False else None
    e8.knob_raw(0, 1, True)
    check(e8.val(0, 7) == V.DEFAULTS[6] == 127, f"Clear + Shift + K1: SUS back to its default 127 ({e8.val(0, 7)})")
    e8.knob_raw(4, -3)
    check(e8.val(0, 1) == V.DEFAULTS[0] == 0, f"Clear + K5: FILT (bipolar, centre) back to 0 ({e8.val(0, 1)})")
    clr_up()
    fr = e8.frame()
    check(all(fr[60 + k] & 0xFF == V.COL_TRACK[0] for k in range(8)) and all(e8.uc.mem_read(0, 1) is not None for _ in (0,)), f"Clear released: no red knob ({[hex(fr[60 + k]) for k in range(8)]})")
    e8.knob_raw(0, 5)
    check(e8.val(0, 5) == 5, "Clear released: the knob turns the value as usual")
    # page B
    e8.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e8.tailb(V.O_FLAGS) | 0x10]))
    e8.knob_raw(6, 9); e8.knob_raw(1, 30); e8.knob_raw(2, 20)
    check((e8.val(0, 19), e8.val(0, 20), e8.val(0, 22)) == (9, 80, 20), "page B: WAVE 9, SHAPE 80, ENVP 20")
    clr_dn()
    e8.knob_raw(6, 1); e8.knob_raw(1, 1); e8.knob_raw(2, 1)
    check((e8.val(0, 19), e8.val(0, 20), e8.val(0, 22)) == (0, 50, 0), f"Clear on page B: WAVE 0 (sine), SHAPE 50 (the centre), ENVP 0 ({e8.val(0, 19)}, {e8.val(0, 20)}, {e8.val(0, 22)})")
    fr = e8.frame()
    check(fr[66] == V.CLR_RED and fr[61] == V.CLR_RED and fr[62] == V.CLR_RED, "the three knobs of page B are red")
    clr_up()
    fr = e8.frame()
    check(all((fr[60 + k] & 0xFF) != V.CLR_RED for k in range(8)), "released: not red")
    # ---- the gate does not depend on the view on screen: the sequencer (and the pads) play the MIDI track through the Tx note vtable whatever view is shown
    gc.collect(); e9 = E20(img, man)
    for _ in range(24): e9.vtick()
    e9.call(L["c_vset"], 0, 1); e9.vtick()
    non, noff = e9.r32(V.NOTE_VT[0]) & ~1, e9.r32(V.NOTE_VT[1]) & ~1
    for view_btn, name in ((0, "Synth 1"), (14, "Mixer"), (4, "Drum 1"), (15, "FX")):
        e9.btn(view_btn)
        e9.call(non, 0x20011334, 2, 64, 100)
        ok_on = e9.rt(0, V.RT_CNT) == 1 and e9.rt(0, V.RT_NOTE) == 64 and e9.rt(0, V.RT_VEL) == 100 and e9.rt(0, V.RT_AUX) & 0x1E == 0x1E
        out = [(w >> 16) & 0x1F for _ in range(8) for (w, ad) in e9.vtick() if ad == VD.VB0]
        e9.call(noff, 0x20011334, 2, 64, 0)
        out2 = [(w >> 16) & 0x1F for _ in range(4) for (w, ad) in e9.vtick() if ad == VD.VB0]
        check(ok_on and {17, 18, 20, 21} <= set(out) and e9.rt(0, V.RT_CNT) == 0 and 17 in out2, f"{name} on screen: a Tx note-on of MIDI 1 flags gate / note / velocity / trigger for the DSP ({sorted(set(out))}) and the note-off closes the gate ({sorted(set(out2))})")
    print("SC23.3 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text()), json.loads(Path(a[4]).read_text())) else 0)
