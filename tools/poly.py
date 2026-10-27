"""SC47 (the user, 2026-10-25: «Polifonía: todos los modos de MIDI, 4 voces si es posible. Voice stealing idealmente en la más antigua de su propio
canal. En caso de vcavcf compartidos, nueva nota abre Gate de nuevo. Noteoff desactiva el pitch correspondiente y cierra Gate cuando no quedan
pitchs activos»), phase 1: the ARM side of vcf21_dsp.use_poly (4 voices per track in the plain oscillator and the sample mode of MIDI 1 / 2).

  * The mode: Shift + pad 29 of MIDI 1 / 2's Preset view (the engine on) now goes retrigger -> legato -> POLY -> retrigger (retrig.py's byte, the
    record's tail + 159 = 0xA0 | bit t legato | bit 2 + t poly: saved with the project); with Shift pad 29 = green / yellow (retrig's) / magenta
    (poly).  Poly sounds in the plain oscillator (one oscillator, not FM) and the sample mode; in the others the track stays one voice.
  * The notes: the entries of vcf21's c_vnon / c_vnoff (every note of the engine goes through them: the transmitter's chain, the auditions) run
    them first, then, poly on: a note-on takes a voice (the free one off the longest; with all 4 held the track's oldest, which fades for 2 ms
    first), its note, its velocity (its level: the engine's VEL is set to 127), its sample (1, or $100 | s for the step's pending flip); a note-on
    with no note held turns the other voices off first (the last one was ringing through the release); a note-off of a voice while others are
    held turns it off (a 0.67 ms fade); the last one rings on (the engine's gate closes as before: the shared envelope's release).  The shared
    envelope restarts with every note (the engine's TRIG; poly is never legato).
  * The DSP (written from a head of the DSP service chain, as fmeng): per track 4 records at X:PV_REC0 + 112 t + 28 v (NOTE, the target, TRIG = a
    counter stepped for each start, TV); on the off -> on edge the records from scratch (G, the target, TRIG, TSEEN 0; K) and then OSC2 + PV_OFF =
    the records' base (0 when off); every tick the dirty targets and the starts; one voice a tick refreshed (and the base every 4): the DSP's
    boot clears the base, never the records.  K (smst's distance of the stereo's right) goes into each record's + 15 too: the exchange then leaves
    OSC1 + 43 alone.
RAM: modmx.MXR + 0x640 ("PLY1"; per track 64 B: + 0 active, + 1 the age counter, + 2 the refresh cursor, + 4 + 12 v the voices: note, velocity,
state (bit 0 sounding, 1 held, 2 start pending, 3 target to write), age, TV (u16), the ticks to the start, the ticks since off, TRIG (u16)).
In the hole (no card, no settings)."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm3, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bics_reg, bl, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp,  # noqa: E402
                   ldrb_imm, ldrh_imm, lsls_imm, lsls_reg, lsrs_imm, lsrs_reg, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list,
                   raw, str_imm, str_sp, strb_imm, strh_imm, subs_imm8, subs_reg, tst_reg, ldrb_w, strb_w, ldrb_reg)
import vcf21 as V  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
import mpatch as MP  # noqa: E402
import modmx as MX  # noqa: E402
import build_sc14 as S14  # noqa: E402

PY = MX.MXR + 0x640
SIG = 0x31594C50                      # "PLY1"
TBS, VS_ = 64, 12                     # the track blocks: PY + 4 + 64 t; the voices: + 4 + 12 v
O_ACT, O_CNT, O_RR = 0, 1, 2
VN, VV, VS, VA, VT, VP, VO, VG = 0, 1, 2, 3, 4, 6, 7, 8
SND, HELD, PEND, DIRTY = 1, 2, 4, 8
TMPL_VT, PAD29 = MP.TMPL_VT, 28
COL_POLY = 0x32                       # magenta (a steady code)
DSP_WRITE = 0x080292F8
RT0 = V.TAIL + V.O_RT
KW = VD.SM_K - 28                     # a record's word of OSC1 + 43
INV = V.INV
V2 = False                            # SC47.3 (use_v2)
V3 = False                            # SC47.4 (use_v3)
V4 = False                            # SC47.5 (use_v4)
VMR = MX.MXR + 0x980                  # (V4) vmode's RAM: + 8 + t the glide (0..127), + 10 + t the unison's detune (0..127), + 12 "VMD1"
O_DTW = VD.GO_OFF - 28                # (V4) the record's word of OSC1 + vcf21_dsp.GO_OFF (34): the voice's pitch offset (the unison's detune)
DT_K = 258                            # (V4) the detune knob -> the widest voice's offset (127 -> 32766 = 50 cents; 65536 a semitone)
MODE_N = 5                            # (V4) retrigger, legato, portamento, poly, unison
V5 = False                            # SC47.6 (use_v5)
NPEND = 0x10                          # (V5) a voice's state bit: its note to write (a unison's legato note: no new start)
FVSIG_AT = None                       # (V5) the FM voices' blocks' signature, after the six blocks
FVB = MX.MXR + 0x800                  # (V3) the FM voices' blocks (fmeng's layout, 64 B each; + 48 the TRIG seen), then "FPV1"
FVSIG = 0x31565046
O_VMAX, O_FMC, O_VPRV = 56, 57, 58    # (V3) a track block's bytes: the voices allowed (0 = 4), the FM update counter, the previous allowance
INCS = [round((1 << 24) * 440 * 2 ** ((n - 69) / 12) / 48000) for n in range(128)]     # (V3) a note's increment (2^24 = a cycle a sample)


def use_v3():
    """SC47.4 (the user, 2026-10-26: «add polyphony to the remaing voices», «FM: 4 voces en total»; vcf21_dsp.use_poly3, fmeng.use_poly): FM in poly
    too.  4 FM voices in all: a track in FM poly has 4, or 2 when the other one is in FM poly too (the voices above the allowance off; an
    allowance that changes = every voice of the track off); FM voice slot s = v, or 2 t + v with 2 each; the record's PV_FMB = X:FV0 + 48 s
    (written before its target, with NOTE / TV / TRIG); a voice's block (FVB + 64 s, fmeng's layout) gets the track's parameters every update, its
    velocity / note at its start (the attacks, the phase resets, the percussive operators from 0, as fmeng's note-on), then fmeng's c_fmenv
    (the gate = held) and c_fmsend with the context (its blocks, the note's increment, the record + 10 for the noise); each voice every second
    tick (2 ms); when it is let go and its four envelopes are down (< 64 / 32767) the voice is freed (its target 0).  As in the VA-drum, a
    note-off only lets the voice go (the release rings) and a note with none held leaves the others ringing."""
    global V3
    assert V2
    V3 = True


def use_v5():
    """SC47.6 (the user, 2026-10-26: «Add uni retrig, uni portamento and uni glide, increase FM polyphony to six shared voices if possible»):
      * seven voice modes: 0 retrigger, 1 legato, 2 portamento, 3 poly, 4 uni retrig (SC47.5's unison), 5 uni portamento (the unison gliding
        always), 6 uni glide (the unison gliding only from a held note); c_rtoff = 1 in 1 / 2 / 5 / 6 (a note over a held one: no new gate);
      * a unison note over a held one in 5 / 6: every voice only moves to it (NPEND: the tick writes NOTE; no new start, so FM / VA-drum keep
        their envelopes); a detached note in 6: a jump counter (O_JPEND / O_JCNT -> OSC2 + vcf21_dsp.JMP_OFF, written before the starts) so the DSP
        does not glide (vcf21_dsp.use_glide2: the glide follows the first record's note);
      * six records a track (vcf21_dsp.use_poly6): six FM voices for a track alone, 3 + 3 with both (the other modes stay at 4); FM slot s = v, or
        3 t + v; the slots' operator blocks from vcf21_dsp.FV_ADDRS; the track blocks of 128 B at a new place (PY, past fmeng's cache), the FM
        voices' ARM blocks six (FVB .. + 384), their signature at FVSIG_AT."""
    global V5, MODE_N, PY, TBS, O_VMAX, O_FMC, O_VPRV, FVSIG_AT
    assert V4 and VD.POLY6
    V5 = True
    MODE_N = 7
    PY = MX.MXR + 0x1800
    TBS = 128
    O_VMAX, O_FMC, O_VPRV = 120, 121, 122
    FVSIG_AT = MX.MXR + 0x9AC


O_JPEND, O_JCNT = 123, 124            # (V5) a track block's bytes: a jump to send, the counter
V6 = False                            # SC47.7 (use_v6)


V7 = False                                                                      # SC48 (use_v7)
O_NCNT = 125                                                                    # (V7) a track block's byte: the voices counted at the last tick
G7 = (181, 148, 128, 114, 105)                                                  # (V7) 256 / sqrt(n) for 2..6 voices


def use_v7():
    """SC48 (the user, 2026-10-27: «se oye crackling en algunos fm al tocar muchas 4 notas o más»; the choice «1.B»: the level by the size of the
    chord): in the poly mode (not unison) a voice's target = velocity << 16 x 256 / sqrt(n) / 256, n = the track's voices sounding or about to
    start (1: as before; 2: 0.71, 3: 0.58, 4: 0.5, 5: 0.45, 6: 0.41).  Measured on the emulated core 0: one FM voice peaks at 0.37 of full scale,
    three at 0.95 and from four the sum clips (study_fmcpu / the session's fmclip), the crackle.  Every tick the count is compared with the last
    one (O_NCNT); a change marks every sounding voice's target to be written again (DIRTY): the DSP ramps each voice's gain to it within a block.
    FM and the oscillator alike; mono / legato / glide and the unison modes unchanged."""
    global V7
    assert V4
    V7 = True


def use_v6():
    """SC47.7 (the user, 2026-10-26: «modes and order: retrigger (gate signal resets whith each new note) legato (no gate reset, change to new pitch
    when two keys are held) glide: same as legato, but notes glide continuosuly into the next (optional param: amount) uni retrig/legato/glide:
    same behavior with unison. Poly: plyphony»; «añadir uni always-glide: se produce el slide aunque el gate estuviera cerrado previamente»): the
    codes stay (0 retrigger, 1 legato, 2 glide, 3 poly, 4 uni retrig, 5 uni legato, 6 uni glide) + 7 uni always-glide (MODE_N 8: the unison
    gliding from every note, a detached one too: no jump; over a held one only moving the voices); vmode.use_v3 orders the pads; mode 2 is now a
    legato glide too: a detached mono note sends the jump (c_pywon: the engine holds one note), so the DSP only glides between held notes; the jump
    is written each tick before anything else of the track (a mono track has no records)."""
    global V6, MODE_N
    assert V5
    V6 = True
    MODE_N = 8


def use_v4():
    """SC47.5 (the user, 2026-10-26: «implementa portamento. asigna el toggle al pad 32, sin shift: retrig/legato/portamento/poly/unison. con un
    desplegable como el modo de voz»; «tengo la sensación de que el clock se vuelve inestable al usar FM poly»):
      * the voice mode of each track in retrig's byte (the record's tail + 159), new form 0xC0 | m0 | m1 << 3 (m: 0 retrigger, 1 legato,
        2 portamento, 3 poly, 4 unison); the old form 0xA0 | legato bit t | poly bit 2 + t is still read.  c_vmget / c_vmset; retrig's c_rtoff
        (legato or portamento: no new gate on a note played over another) and c_pyflag (poly or unison: the records) answer from it;
      * unison: a note-on starts every voice (4; 2 with both tracks in FM poly; 1 in the sample mode) on the note with no fade, each with its pitch
        offset (record word O_DTW = OSC1 + 34, vcf21_dsp.use_glide: spread evenly over +-DT_K x the detune knob), the target x 1/2 (4) or 3/4 (2);
        they are let go when the engine holds no note (RT_CNT); the engine retriggers;
      * the offset word written 0 in the other oscillator modes (never in the sample mode, where it is SM_L2);
      * less SPI traffic: the refresh one voice every 8 ticks (each voice every 32 ms), the FM voice's AMP_s / y[n - 2] zeroed only at its slot's
        first use, fmeng's shape read cleared a track a tick (fmeng.use_wcache)."""
    global V4
    assert V3
    V4 = True


def use_v2():
    """SC47.3 (the user, 2026-10-26: «add polyphony to the remaing voices»; «VA-drum: por voz»; vcf21_dsp.use_poly2): poly also with two
    oscillators and in the VA-drum (still not FM).  In the VA-drum a voice is a one-shot: a note-off only lets it go (it rings through its own
    envelope), a note with none held leaves the others ringing; a fifth hit takes the oldest voice (faded for 2 ms first) as before."""
    global V2
    V2 = True


def sdiv(rd, rn, rm): return h(0xFB90 | rn) + h(0xF0F0 | rd << 8 | rm)
def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
MRS7, CPSID, MSR7 = bytes([0xEF, 0xF3, 0x10, 0x87]), bytes([0x72, 0xB6]), bytes([0x87, 0xF3, 0x10, 0x88])    # mrs r7, primask; cpsid i; msr primask, r7


def arm_code(base, L, prev, head_on, head_off):
    a = Asm(base)
    E = a.emit
    T = {}
    NV = VD.PV_N                                                                 # the voices a track
    if V3:                                                                       # (V3) the notes' increments (a table at the start)
        T["inc"] = base; E(raw, struct.pack("<128I", *INCS))
    if V5: T["fva"] = base + 512; E(raw, struct.pack("<6I", *VD.FV_ADDRS))     # (V5) the FM slots' operator blocks
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_p{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    RET = h(0x4770)
    def vptr(rd, rv):                                                   # rd = the voice rv of the track block r5 (rd != rv)
        E(movs_imm, rd, VS_); E(muls, rd, rv); E(adds_reg, rd, rd, 5); E(adds_imm8, rd, 4)
    def wf(field, rv_src=None):                                         # the record field of (r4 = track, r6 = voice) = r3; clobbers r0-r3
        E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(movs_imm, 2, field); E(bl, "c_pywf")

    # ---- c_pyst() -> r0 = PY, zeroed with its signature at the first use; clobbers r1-r3
    a.label("c_pyst")
    imm32(0, PY); E(ldr_imm, 1, 0, 0); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "st_i", "ne"); E(raw, RET)
    a.label("st_i")
    E(push_list, [4], lr=True); E(mov_reg, 4, 2); E(mov_reg, 2, 0); E(adds_imm8, 2, 4); E(movs_imm, 1, 0); E(movs_imm, 3, 2 * TBS // 4)
    a.label("st_z"); E(str_imm, 1, 2, 0); E(adds_imm8, 2, 4); E(subs_imm8, 3, 1); E(b_cond, "st_z", "ne")
    E(str_imm, 4, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_pytb(r0 = track) -> r0 = its block; clobbers r1-r3
    a.label("c_pytb")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, "c_pyst"); E(lsls_imm, 1, 4, TBS.bit_length() - 1); E(adds_reg, 0, 0, 1); E(adds_imm8, 0, 4); E(pop_list, [4], pc=True)

    # ---- c_pyrec(r0 = track, r1 = voice) -> r0 = the record's DSP address; clobbers r1, r2
    a.label("c_pyrec")
    E(movs_imm, 2, VD.PV_RS * VD.PV_N); E(muls, 0, 2); E(movs_imm, 2, VD.PV_RS); E(muls, 1, 2); E(adds_reg, 0, 0, 1)
    imm32(1, VD.PV_REC0); E(adds_reg, 0, 0, 1); E(raw, RET)

    # ---- c_pyw(r0 = DSP X address, r1 = value): the DSP write (core 0); clobbers r0-r3
    a.label("c_pyw")
    if V4: E(b_w, L["c_fmw"])                                                    # (V4) through fmeng's cache (the records' ARM-owned words)
    else: E(mov_reg, 2, 0); E(lsls_imm, 1, 1, 8); E(movs_imm, 0, 0); E(b_w, DSP_WRITE)

    # ---- c_pywf(r0 = track, r1 = voice, r2 = field, r3 = value): a field of the record; clobbers r0-r3
    a.label("c_pywf")
    E(push_list, [2, 3], lr=True); E(bl, "c_pyrec"); E(pop_list, [2, 3]); E(adds_reg, 0, 0, 2); E(mov_reg, 1, 3); E(bl, "c_pyw"); E(pop_list, [], pc=True)

    # ---- c_pypvw(r0 = track, r1 = 0 off / 1 on): OSC2 + PV_OFF = the base of the records, or 0; clobbers r0-r3
    a.label("c_pypvw")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(movs_imm, 1, 0); E(bl, "c_pyrec"); E(mov_reg, 1, 0)
    E(cmp_imm, 5, 0); E(b_cond, "pv_on", "ne"); E(movs_imm, 1, 0)
    a.label("pv_on"); E(movs_imm, 0, 48); E(muls, 0, 4); imm32(2, VD.OS2B0 + VD.PV_OFF); E(adds_reg, 0, 0, 2); E(bl, "c_pyw"); E(pop_list, [4, 5], pc=True)

    if V4:
        # ---- c_vmget(r0 = track) -> r0 = its voice mode (0 retrigger, 1 legato, 2 portamento, 3 poly, 4 unison); clobbers r1-r3
        a.label("c_vmget")
        E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, L["c_rtb"]); E(cmp_imm, 0, 0); E(b_cond, "vg_0", "eq")
        E(ldrb_imm, 1, 0, 0); E(lsrs_imm, 2, 1, 6); E(cmp_imm, 2, 3); E(b_cond, "vg_o", "ne")
        E(lsls_imm, 2, 4, 1); E(adds_reg, 2, 2, 4); E(lsrs_reg, 1, 2); E(movs_imm, 0, 7); E(ands_reg, 0, 1)      # (b >> 3 t) & 7
        E(cmp_imm, 0, MODE_N - 1); E(b_cond, "vg_x", "ls")
        a.label("vg_0"); E(movs_imm, 0, 0)
        a.label("vg_x"); E(pop_list, [4], pc=True)
        a.label("vg_o"); E(lsrs_imm, 2, 1, 4); E(cmp_imm, 2, 0xA); E(b_cond, "vg_0", "ne")                       # the old form
        E(adds_imm3, 2, 4, 2); E(mov_reg, 3, 1); E(lsrs_reg, 3, 2); E(movs_imm, 0, 1); E(tst_reg, 3, 0); E(b_cond, "vg_l", "eq")
        E(movs_imm, 0, 3); E(pop_list, [4], pc=True)
        a.label("vg_l"); E(lsrs_reg, 1, 4); E(ands_reg, 0, 1); E(pop_list, [4], pc=True)

        # ---- c_vmset(r0 = track, r1 = mode): the byte in the new form (both tracks); clobbers r0-r3
        a.label("c_vmset")
        E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
        E(movs_imm, 0, 0); E(bl, "c_vmget"); E(mov_reg, 6, 0)
        E(movs_imm, 0, 1); E(bl, "c_vmget")
        E(cmp_imm, 4, 0); E(b_cond, "vs_1", "ne"); E(mov_reg, 6, 5); E(b, "vs_w")
        a.label("vs_1"); E(mov_reg, 0, 5)
        a.label("vs_w"); E(lsls_imm, 0, 0, 3); E(orrs_reg, 0, 6); E(adds_imm8, 0, 0xC0); E(mov_reg, 6, 0)
        E(bl, L["c_rtb"]); E(cmp_imm, 0, 0); E(b_cond, "vs_x", "eq"); E(strb_imm, 6, 0, 0)
        a.label("vs_x"); E(pop_list, [4, 5, 6], pc=True)

        # ---- c_vmrtoff(r0 = track) -> r0 = 1 with the retrigger off (legato, portamento); clobbers r1, r2 (retrig's c_rtoff, which jumps here)
        a.label("c_vmrtoff")
        E(push_list, [3], lr=True); E(bl, "c_vmget")
        if V5: E(cmp_imm, 0, 5); E(b_cond, "vr_1", "hs")                         # (V5) uni portamento / uni glide too
        E(subs_imm8, 0, 1); E(cmp_imm, 0, 1); E(b_cond, "vr_1", "ls")
        E(movs_imm, 0, 0); E(pop_list, [3], pc=True)
        a.label("vr_1"); E(movs_imm, 0, 1); E(pop_list, [3], pc=True)

        # ---- c_pyflag(r0 = track) -> r0 = 1 in poly or unison (the voice records); clobbers r1-r3
        a.label("c_pyflag")
        E(push_list, [], lr=True); E(bl, "c_vmget"); E(subs_imm8, 0, 3); E(cmp_imm, 0, MODE_N - 4); E(b_cond, "pf_1", "ls")
        E(movs_imm, 0, 0); E(pop_list, [], pc=True)
        a.label("pf_1"); E(movs_imm, 0, 1); E(pop_list, [], pc=True)

        # ---- c_pyuni(r0 = track) -> r0 = 1 in unison; clobbers r1-r3
        a.label("c_pyuni")
        E(push_list, [], lr=True); E(bl, "c_vmget"); E(subs_imm8, 0, 4); E(movs_imm, 1, 1)
        if V5: E(cmp_imm, 0, MODE_N - 5); E(b_cond, "pu_x", "ls")                 # (V5) 4..6
        else: E(cmp_imm, 0, 0); E(b_cond, "pu_x", "eq")
        E(movs_imm, 1, 0)
        a.label("pu_x"); E(mov_reg, 0, 1); E(pop_list, [], pc=True)

        # ---- c_pyun(r4 = track, r5 = block) -> r0 = the unison's voices (4, 2 with the allowance, 1 in the sample mode); clobbers r1-r3
        a.label("c_pyun")
        E(push_list, [], lr=True); E(mov_reg, 0, 4); E(bl, L["c_msmode"]); E(cmp_imm, 0, 5); E(movs_imm, 0, 1); E(b_cond, "un_x", "eq")
        E(ldrb_w, 0, 5, O_VMAX); E(cmp_imm, 0, 0); E(b_cond, "un_x", "ne"); E(movs_imm, 0, 4)
        a.label("un_x"); E(pop_list, [], pc=True)

        # ---- c_pydt(r4 = track, r5 = block, r6 = voice) -> r0 = 1 and r3 = the voice's pitch offset in the oscillator modes, else r0 = 0; clobbers r1-r3
        a.label("c_pydt")
        E(push_list, [7], lr=True)
        E(mov_reg, 0, 4); E(bl, L["c_msmode"]); E(cmp_imm, 0, 2); E(b_cond, "dt_o", "eq"); E(cmp_imm, 0, 3); E(b_cond, "dt_0", "ne")
        a.label("dt_o"); E(movs_imm, 7, 0)
        E(mov_reg, 0, 4); E(bl, "c_pyuni"); E(cmp_imm, 0, 0); E(b_cond, "dt_w", "eq")
        E(bl, "c_pyun"); E(subs_imm8, 0, 1); E(b_cond, "dt_w", "eq"); E(mov_reg, 3, 0)                            # r3 = N - 1 (0: one voice)
        imm32(0, VMR + 10); E(ldrb_reg, 0, 0, 4); E(movs_imm, 1, DT_K // 2); E(lsls_imm, 1, 1, 1); E(muls, 0, 1)    # h = the knob x DT_K
        E(lsls_imm, 1, 6, 1); E(subs_reg, 1, 1, 3); E(muls, 0, 1); E(raw, sdiv(7, 0, 3))         # h x (2 v - (N - 1)) / (N - 1)
        a.label("dt_w"); E(mov_reg, 3, 7); E(movs_imm, 0, 1); E(pop_list, [7], pc=True)
        a.label("dt_0"); E(movs_imm, 0, 0); E(pop_list, [7], pc=True)
    else:
        # ---- c_pyflag(r0 = track) -> r0 = 1 with its poly bit (retrig's byte, bit 2 + t); clobbers r1-r3
        a.label("c_pyflag")
        E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, L["c_rtb"]); E(cmp_imm, 0, 0); E(b_cond, "pf_0", "eq")
        E(ldrb_imm, 1, 0, 0); E(lsrs_imm, 2, 1, 4); E(cmp_imm, 2, 0xA); E(b_cond, "pf_0", "ne")
        E(adds_imm3, 0, 4, 2); E(lsrs_reg, 1, 0); E(movs_imm, 0, 1); E(ands_reg, 0, 1); E(pop_list, [4], pc=True)
        a.label("pf_0"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_pyok(r0 = track) -> r0 = 1 in the plain oscillator (not FM, one oscillator) or the sample mode; clobbers r1-r3
    a.label("c_pyok")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(bl, L["c_msmode"]); E(cmp_imm, 0, 5); E(b_cond, "ok_1", "eq")
    if V2: E(cmp_imm, 0, 3); E(b_cond, "ok_1", "eq")                                # (V2) the VA-drum
    E(cmp_imm, 0, 2); E(b_cond, "ok_0", "ne")
    if not V3: E(mov_reg, 0, 4); E(bl, L["c_fmact"]); E(cmp_imm, 0, 0); E(b_cond, "ok_0", "ne")     # (V3: FM too)
    if not V2: E(mov_reg, 0, 4); E(movs_imm, 1, V.RT_VEL); E(bl, L["c_vrt7"]); E(cmp_imm, 0, 0); E(b_cond, "ok_0", "ne")   # (V2: two oscillators too)
    a.label("ok_1"); E(movs_imm, 0, 1); E(pop_list, [4], pc=True)
    a.label("ok_0"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_pytv(r0 = track) -> r0 = a new note's TRIG value: $100 | s for the step's pending flip (left for the engine's TRIG), else 1; clobbers r1-r3
    a.label("c_pytv")
    E(push_list, [], lr=True); E(bl, L["c_vsmpb"]); E(movs_imm, 1, 1); E(cmp_imm, 0, 0); E(b_cond, "tv_x", "eq")
    E(ldrb_imm, 0, 0, 0); E(lsrs_imm, 2, 0, 6); E(cmp_imm, 2, 3); E(b_cond, "tv_x", "ne")
    E(movs_imm, 2, 63); E(ands_reg, 0, 2); E(lsls_imm, 1, 1, 8); E(orrs_reg, 1, 0)
    a.label("tv_x"); E(mov_reg, 0, 1); E(pop_list, [], pc=True)

    # ---- the entries of c_vnon / c_vnoff (obj, track id, note, velocity): the engine's first, then the voices
    for name, tramp, on in (("c_pywon", "py_tron", True), ("c_pywoff", "py_troff", False)):
        a.label(name)
        E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
        E(bl, tramp); E(str_sp, 0, 0)                                           # the engine's (and the chain's) answer
        E(ldr_sp, 4, 4); E(subs_imm8, 4, 2); E(cmp_imm, 4, 1); bc(name + "_x", "hi")
        if on: E(ldr_sp, 6, 12); E(cmp_imm, 6, 0); bc(name + "_x", "eq")
        E(mov_reg, 0, 4); E(bl, "c_pytb"); E(mov_reg, 5, 0)
        if V6 and on:                                                             # (V6) glide (2), a detached note: a jump (the DSP does not slide)
            E(mov_reg, 0, 4); E(bl, "c_vmget"); E(cmp_imm, 0, 2); E(b_cond, "pw_ng", "ne")
            imm32(0, RT0); E(lsls_imm, 1, 4, 3); E(adds_reg, 0, 0, 1); E(ldrb_imm, 0, 0, V.RT_CNT); E(movs_imm, 1, 15); E(ands_reg, 0, 1)
            E(cmp_imm, 0, 1); E(b_cond, "pw_ng", "ne"); E(movs_imm, 0, 1); E(strb_w, 0, 5, O_JPEND)
            a.label("pw_ng")
        E(ldrb_imm, 0, 5, O_ACT); E(cmp_imm, 0, 0); bc(name + "_x", "eq")
        if on:                                                                    # the engine's VEL at 127: each voice has its own level
            imm32(1, RT0); E(lsls_imm, 0, 4, 3); E(adds_reg, 1, 1, 0); E(ldrb_imm, 0, 1, V.RT_VEL); E(movs_imm, 2, 0x80); E(ands_reg, 0, 2)
            E(adds_imm8, 0, 127); E(strb_imm, 0, 1, V.RT_VEL)
        E(ldr_sp, 2, 8); E(bl, "c_pyalloc" if on else "c_pyrel")
        a.label(name + "_x"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(raw, RET)
    a.label("py_tron"); E(raw, head_on); E(b_w, L["c_vnon"] + 4)
    a.label("py_troff"); E(raw, head_off); E(b_w, L["c_vnoff"] + 4)

    # ---- c_pyalloc(r4 = track, r5 = its block, r2 = note, r6 = velocity): a voice for the note
    a.label("c_pyalloc")
    E(raw, pushw([4, 5, 6, 7, 8, 9, 10, 11], lr=True))
    E(mov_reg, 8, 2); E(mov_reg, 9, 6)
    E(mov_reg, 0, 4); E(bl, "c_pytv"); E(mov_reg, 10, 0)
    if V4:                                                                       # (V4) unison: every voice on the note, no fade
        E(mov_reg, 0, 4); E(bl, "c_pyuni"); E(cmp_imm, 0, 0); bc("al_nu", "eq")
        E(bl, "c_pyun"); E(mov_reg, 11, 0)
        if V5:                                                                   # (V5) 5 / 6 with another note held: the voices only move
            E(mov_reg, 0, 4); E(bl, "c_vmget"); E(cmp_imm, 0, 5); bc("au_st", "lo"); E(mov_reg, 7, 0)
            imm32(0, RT0); E(lsls_imm, 1, 4, 3); E(adds_reg, 0, 0, 1); E(ldrb_imm, 0, 0, V.RT_CNT); E(movs_imm, 1, 15); E(ands_reg, 0, 1)
            E(cmp_imm, 0, 2); E(b_cond, "au_dt", "lo")
            E(raw, MRS7); E(raw, CPSID); E(movs_imm, 6, 0)                       # (the mode in r7 is not needed past here)
            a.label("au_lg"); vptr(1, 6); E(cmp_reg, 6, 11); E(b_cond, "au_lg2", "hs")
            E(mov_reg, 2, 8); E(strb_imm, 2, 1, VN); E(ldrb_imm, 2, 1, VS); E(movs_imm, 3, NPEND); E(orrs_reg, 2, 3); E(strb_imm, 2, 1, VS)
            a.label("au_lg2"); E(adds_imm8, 6, 1); E(cmp_imm, 6, NV); E(b_cond, "au_lg", "lo")
            E(raw, MSR7)
            E(raw, popw([4, 5, 6, 7, 8, 9, 10, 11], lr=True)); E(raw, RET)
            a.label("au_dt"); E(cmp_imm, 7, 6); E(b_cond, "au_st", "ne"); E(movs_imm, 0, 1); E(strb_w, 0, 5, O_JPEND)   # uni glide, detached: a jump
            a.label("au_st")
        E(raw, MRS7); E(raw, CPSID); E(movs_imm, 6, 0)
        a.label("au_l"); vptr(1, 6); E(cmp_reg, 6, 11); E(b_cond, "au_on", "lo")
        E(ldrb_imm, 2, 1, VS); E(movs_imm, 3, 7); E(tst_reg, 2, 3); E(b_cond, "au_n", "eq")     # above the voices: off
        E(movs_imm, 2, DIRTY); E(strb_imm, 2, 1, VS); E(movs_imm, 2, 0); E(strb_imm, 2, 1, VO); E(b, "au_n")
        a.label("au_on")
        E(movs_imm, 2, 0); E(strb_imm, 2, 1, VP)
        E(ldrb_imm, 2, 5, O_CNT); E(adds_imm8, 2, 1); E(strb_imm, 2, 5, O_CNT); E(strb_imm, 2, 1, VA)
        E(mov_reg, 2, 8); E(strb_imm, 2, 1, VN); E(mov_reg, 2, 9); E(strb_imm, 2, 1, VV); E(mov_reg, 2, 10); E(strh_imm, 2, 1, VT)
        E(ldrb_imm, 2, 1, VS); E(movs_imm, 3, DIRTY | SND); E(ands_reg, 2, 3); E(adds_imm8, 2, HELD | PEND); E(strb_imm, 2, 1, VS)
        a.label("au_n"); E(adds_imm8, 6, 1); E(cmp_imm, 6, NV); E(b_cond, "au_l", "lo")
        E(raw, MSR7)
        E(raw, popw([4, 5, 6, 7, 8, 9, 10, 11], lr=True)); E(raw, RET)
        a.label("al_nu")
    if V2:                                                                       # (V2) the VA-drum: bit 16 of r10 (TV is stored as a halfword)
        E(mov_reg, 0, 4); E(bl, L["c_msmode"]); E(cmp_imm, 0, 3)
        if V3: E(b_cond, "al_rg", "eq"); E(mov_reg, 0, 4); E(bl, L["c_fmact"]); E(cmp_imm, 0, 0); E(b_cond, "al_nv", "eq"); a.label("al_rg")    # (V3) FM too
        else: E(b_cond, "al_nv", "ne")
        E(mov_reg, 0, 10); E(movs_imm, 1, 1); E(lsls_imm, 1, 1, 16); E(orrs_reg, 0, 1); E(mov_reg, 10, 0)
        a.label("al_nv")
    if V3:                                                                       # (V3) r12 = the voices allowed
        E(ldrb_w, 0, 5, O_VMAX); E(cmp_imm, 0, 0); E(b_cond, "al_vm", "ne"); E(movs_imm, 0, 4)
        a.label("al_vm"); E(mov_reg, 12, 0)
    E(raw, MRS7); E(raw, CPSID)
    E(movs_imm, 0, 0); E(movs_imm, 6, 0)                                        # r0 = the notes held
    a.label("al_h"); vptr(1, 6); E(ldrb_imm, 2, 1, VS); E(lsrs_imm, 2, 2, 2); E(b_cond, "al_h2", "lo"); E(adds_imm8, 0, 1)
    a.label("al_h2"); E(adds_imm8, 6, 1); E(cmp_imm, 6, NV); E(b_cond, "al_h", "lo")
    E(cmp_imm, 0, 0); E(b_cond, "al_c", "ne")
    if V2: E(mov_reg, 1, 10); E(lsrs_imm, 1, 1, 17); E(b_cond, "al_c", "hs")        # (V2) the VA-drum: the others ring on
    E(movs_imm, 6, 0)                                                            # no note held: every voice off (the last one rang through the release)
    a.label("al_o"); vptr(1, 6); E(ldrb_imm, 2, 1, VS); E(cmp_imm, 2, 0); E(b_cond, "al_o2", "eq")
    E(movs_imm, 2, DIRTY); E(strb_imm, 2, 1, VS); E(movs_imm, 2, 0); E(strb_imm, 2, 1, VO)
    a.label("al_o2"); E(adds_imm8, 6, 1); E(cmp_imm, 6, NV); E(b_cond, "al_o", "lo")
    a.label("al_c")                                                              # a free voice: the one off the longest
    E(movs_imm, 0, 0); E(mov_reg, 11, 0); E(movs_imm, 6, 0)
    a.label("al_f"); vptr(1, 6); E(ldrb_imm, 2, 1, VS); E(movs_imm, 3, 7); E(tst_reg, 2, 3); E(b_cond, "al_f2", "ne")
    E(ldrb_imm, 2, 1, VO); E(adds_imm8, 2, 1); E(cmp_reg, 2, 0); E(b_cond, "al_f2", "ls"); E(mov_reg, 0, 2); E(mov_reg, 11, 1)
    a.label("al_f2"); E(adds_imm8, 6, 1)
    if V3: E(cmp_reg, 6, 12)
    else: E(cmp_imm, 6, 4)
    E(b_cond, "al_f", "lo")
    E(mov_reg, 1, 11); E(cmp_imm, 1, 0); E(b_cond, "al_s", "eq")
    E(subs_imm8, 0, 1); E(movs_imm, 2, 0); E(cmp_imm, 0, 2); E(b_cond, "al_set", "hs")    # off for 2 ticks: now; else the rest of the fade
    E(movs_imm, 2, 2); E(subs_reg, 2, 2, 0); E(b, "al_set")
    a.label("al_s")                                                              # all busy: the oldest (counter - age), faded first
    E(ldrb_imm, 3, 5, O_CNT); E(movs_imm, 0, 0); E(mov_reg, 11, 0); E(movs_imm, 6, 0)
    a.label("al_t"); vptr(1, 6); E(ldrb_imm, 2, 1, VA); E(subs_reg, 2, 3, 2); E(lsls_imm, 2, 2, 24); E(lsrs_imm, 2, 2, 24); E(adds_imm8, 2, 1)
    E(cmp_reg, 2, 0); E(b_cond, "al_t2", "ls"); E(mov_reg, 0, 2); E(mov_reg, 11, 1)
    a.label("al_t2"); E(adds_imm8, 6, 1)
    if V3: E(cmp_reg, 6, 12)
    else: E(cmp_imm, 6, 4)
    E(b_cond, "al_t", "lo")
    E(mov_reg, 1, 11); E(ldrb_imm, 2, 1, VS); E(movs_imm, 3, SND); E(tst_reg, 2, 3); E(b_cond, "al_sp", "eq")
    E(movs_imm, 3, DIRTY); E(orrs_reg, 2, 3); E(strb_imm, 2, 1, VS); E(movs_imm, 2, 2); E(b, "al_set")     # sounding: its target 0, the start 2 ticks later
    a.label("al_sp"); E(ldrb_imm, 2, 1, VP)                                      # still pending: its wait kept
    a.label("al_set")                                                            # r1 = the voice, r2 = the ticks to its start
    E(strb_imm, 2, 1, VP)
    E(ldrb_imm, 0, 5, O_CNT); E(adds_imm8, 0, 1); E(strb_imm, 0, 5, O_CNT); E(strb_imm, 0, 1, VA)
    E(mov_reg, 0, 8); E(strb_imm, 0, 1, VN); E(mov_reg, 0, 9); E(strb_imm, 0, 1, VV); E(mov_reg, 0, 10); E(strh_imm, 0, 1, VT)
    E(ldrb_imm, 0, 1, VS); E(movs_imm, 2, DIRTY); E(ands_reg, 0, 2); E(adds_imm8, 0, HELD | PEND); E(strb_imm, 0, 1, VS)
    E(raw, MSR7)
    E(raw, popw([4, 5, 6, 7, 8, 9, 10, 11], lr=True)); E(raw, RET)

    # ---- c_pyrel(r5 = the track's block, r2 = note): the oldest held voice of the note let go
    a.label("c_pyrel")
    E(raw, pushw([4, 5, 6, 7, 8, 9, 10, 11], lr=True))
    if V4:                                                                       # (V4) unison: let go when the engine holds no note
        E(mov_reg, 9, 2); E(mov_reg, 0, 4); E(bl, "c_pyuni"); E(mov_reg, 2, 9); E(cmp_imm, 0, 0); bc("rl_nu", "eq")
        imm32(0, RT0); E(lsls_imm, 1, 4, 3); E(adds_reg, 0, 0, 1); E(ldrb_imm, 0, 0, V.RT_CNT); E(movs_imm, 1, 15); E(tst_reg, 0, 1); bc("rl_ux", "ne")
        E(raw, MRS7); E(raw, CPSID); E(movs_imm, 6, 0)
        a.label("ru_l"); vptr(1, 6); E(ldrb_imm, 2, 1, VS); E(movs_imm, 3, HELD); E(bics_reg, 2, 3); E(strb_imm, 2, 1, VS)
        E(adds_imm8, 6, 1); E(cmp_imm, 6, NV); E(b_cond, "ru_l", "lo")
        E(raw, MSR7)
        a.label("rl_ux"); E(raw, popw([4, 5, 6, 7, 8, 9, 10, 11], lr=True)); E(raw, RET)
        a.label("rl_nu")
    if V3:                                                                       # (V3) r10 = 1 in the VA-drum or FM (r4 = the track)
        E(mov_reg, 9, 2); E(mov_reg, 0, 4); E(bl, L["c_msmode"]); E(cmp_imm, 0, 3); E(b_cond, "rl_r1", "eq")
        E(mov_reg, 0, 4); E(bl, L["c_fmact"]); E(b, "rl_r2")
        a.label("rl_r1"); E(movs_imm, 0, 1)
        a.label("rl_r2"); E(mov_reg, 10, 0); E(mov_reg, 2, 9)
    elif V2: E(mov_reg, 9, 2); E(mov_reg, 0, 4); E(bl, L["c_msmode"]); E(mov_reg, 10, 0); E(mov_reg, 2, 9)    # (V2) r10 = the mode (r4 = the track)
    E(mov_reg, 4, 2)
    E(raw, MRS7); E(raw, CPSID)
    E(ldrb_imm, 3, 5, O_CNT); E(movs_imm, 0, 0); E(mov_reg, 11, 0); E(movs_imm, 6, 0)
    a.label("rl_f"); vptr(1, 6); E(ldrb_imm, 2, 1, VS); E(lsrs_imm, 2, 2, 2); E(b_cond, "rl_f2", "lo")
    E(ldrb_imm, 2, 1, VN); E(cmp_reg, 2, 4); E(b_cond, "rl_f2", "ne")
    E(ldrb_imm, 2, 1, VA); E(subs_reg, 2, 3, 2); E(lsls_imm, 2, 2, 24); E(lsrs_imm, 2, 2, 24); E(adds_imm8, 2, 1)
    E(cmp_reg, 2, 0); E(b_cond, "rl_f2", "ls"); E(mov_reg, 0, 2); E(mov_reg, 11, 1)
    a.label("rl_f2"); E(adds_imm8, 6, 1); E(cmp_imm, 6, NV); E(b_cond, "rl_f", "lo")
    E(mov_reg, 1, 11); E(cmp_imm, 1, 0); E(b_cond, "rl_x", "eq")
    E(ldrb_imm, 2, 1, VS); E(movs_imm, 3, HELD); E(bics_reg, 2, 3); E(strb_imm, 2, 1, VS)
    if V3: E(mov_reg, 0, 10); E(cmp_imm, 0, 0); E(b_cond, "rl_x", "ne")             # (V3) the VA-drum / FM: let go only (it rings through its envelope)
    elif V2: E(mov_reg, 0, 10); E(cmp_imm, 0, 3); E(b_cond, "rl_x", "eq")             # (V2) the VA-drum: let go only (it rings through its envelope)
    E(movs_imm, 0, 0); E(movs_imm, 6, 0)                                        # the others still held?
    a.label("rl_h"); vptr(3, 6); E(ldrb_imm, 3, 3, VS); E(lsrs_imm, 3, 3, 2); E(b_cond, "rl_h2", "lo"); E(adds_imm8, 0, 1)
    a.label("rl_h2"); E(adds_imm8, 6, 1); E(cmp_imm, 6, NV); E(b_cond, "rl_h", "lo")
    E(cmp_imm, 0, 0); E(b_cond, "rl_x", "eq")                                   # the last note: it rings on
    E(movs_imm, 3, SND); E(tst_reg, 2, 3); E(b_cond, "rl_np", "eq")
    E(movs_imm, 2, DIRTY); E(b, "rl_w")                                          # sounding: off (its target 0)
    a.label("rl_np"); E(movs_imm, 3, DIRTY); E(ands_reg, 2, 3)                  # not started: cancelled
    a.label("rl_w"); E(strb_imm, 2, 1, VS); E(movs_imm, 2, 0); E(strb_imm, 2, 1, VO)
    a.label("rl_x"); E(raw, MSR7)
    E(raw, popw([4, 5, 6, 7, 8, 9, 10, 11], lr=True)); E(raw, RET)

    # ---- c_pyvals(r4 = track, r6 = voice, r10 = its RAM, r9 = its state): NOTE, TV, the target (sounding: velocity << 16), TRIG; clobbers r0-r3
    a.label("c_pyvals")
    E(push_list, [], lr=True)
    if V3: E(bl, "c_pyfmb"); wf(VD.PV_FMB)                                      # (V3) the FM blocks before the target
    E(mov_reg, 1, 10); E(ldrb_imm, 3, 1, VN); wf(VD.PV_NOTE)
    E(mov_reg, 1, 10); E(ldrh_imm, 3, 1, VT); wf(VD.PV_TV)
    E(bl, "c_pytgt")
    E(mov_reg, 1, 10); E(ldrh_imm, 3, 1, VG); wf(VD.PV_TRIG)
    if V4: E(bl, "c_pydt"); E(cmp_imm, 0, 0); E(b_cond, "pv_nd", "eq"); wf(O_DTW); a.label("pv_nd")      # (V4) the pitch offset
    E(pop_list, [], pc=True)
    a.label("c_pytgt")                                                           # the target alone
    E(push_list, [], lr=True)
    E(movs_imm, 3, 0); E(mov_reg, 0, 9); E(lsrs_imm, 0, 0, 1); E(b_cond, "tg_w", "lo"); E(mov_reg, 1, 10); E(ldrb_imm, 3, 1, VV); E(lsls_imm, 3, 3, 16)
    if V4:                                                                       # (V4) unison: 4 voices x 1/2, 2 x 3/4
        E(push_list, [3]); E(mov_reg, 0, 4); E(bl, "c_pyuni"); E(cmp_imm, 0, 0); E(b_cond, "tg_p", "eq")
        E(bl, "c_pyun"); E(pop_list, [3]); E(cmp_imm, 0, 2); E(b_cond, "tg_w", "lo"); E(b_cond, "tg_h", "ne")
        E(lsrs_imm, 0, 3, 2); E(subs_reg, 3, 3, 0); E(b, "tg_w")
        a.label("tg_h"); E(lsrs_imm, 3, 3, 1); E(b, "tg_w")
        a.label("tg_p"); E(pop_list, [3])
        if V7:                                                                   # (V7) poly: x 1 / sqrt(the voices)
            E(push_list, [3]); E(bl, "c_pycnt"); E(pop_list, [3]); E(cmp_imm, 0, 1); E(b_cond, "tg_w", "ls")
            E(movs_imm, 1, G7[-1])
            for n_, g_ in zip(range(2, 6), G7):
                E(cmp_imm, 0, n_); E(b_cond, f"tg_{n_}", "ne"); E(movs_imm, 1, g_); E(b, "tg_m"); a.label(f"tg_{n_}")
            a.label("tg_m"); E(lsrs_imm, 3, 3, 8); E(muls, 3, 1)
    a.label("tg_w"); wf(VD.PV_TGT); E(pop_list, [], pc=True)
    if V7:                                                                       # (V7) c_pycnt(r5 = the track block) -> r0 = its voices sounding or about to start; clobbers r1-r3
        a.label("c_pycnt")
        E(movs_imm, 0, 0); E(movs_imm, 2, 0)
        a.label("pc_l"); vptr(1, 2); E(ldrb_imm, 1, 1, VS); E(movs_imm, 3, SND | PEND); E(tst_reg, 1, 3); E(b_cond, "pc_n", "eq"); E(adds_imm8, 0, 1)
        a.label("pc_n"); E(adds_imm8, 2, 1); E(cmp_imm, 2, NV); E(b_cond, "pc_l", "lo"); E(raw, RET)

    # ---- c_pytick: a head of the DSP service chain (RAM and DSP writes only)
    a.label("c_pytick")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], lr=True))
    E(movs_imm, 4, 0)
    a.label("tk_l")
    E(mov_reg, 0, 4); E(bl, "c_pytb"); E(mov_reg, 5, 0)
    if V3: E(bl, "c_pyvmx")                                                      # (V3) the voices allowed (r4 = track, r5 = block)
    if V6:                                                                       # (V6) a jump to send (mono too): before the track's NOTEs
        E(ldrb_w, 0, 5, O_JPEND); E(cmp_imm, 0, 0); E(b_cond, "tk_nj", "eq"); E(movs_imm, 0, 0); E(strb_w, 0, 5, O_JPEND)
        E(ldrb_w, 1, 5, O_JCNT); E(adds_imm8, 1, 1); E(strb_w, 1, 5, O_JCNT)
        E(movs_imm, 0, 48); E(muls, 0, 4); imm32(2, VD.OS2B0 + VD.JMP_OFF); E(adds_reg, 0, 0, 2); E(bl, "c_pyw")
        a.label("tk_nj")
    E(mov_reg, 0, 4); E(bl, "c_pyflag"); E(cmp_imm, 0, 0); E(b_cond, "tk_a", "eq")
    E(mov_reg, 0, 4); E(bl, "c_pyok")
    a.label("tk_a"); E(ldrb_imm, 1, 5, O_ACT); E(cmp_reg, 0, 1); bc("tk_e", "eq")
    E(strb_imm, 0, 5, O_ACT); E(cmp_imm, 0, 0); bc("tk_off", "eq")
    E(movs_imm, 6, 0)                                                            # on: the records from scratch, then the base
    a.label("tk_i"); vptr(1, 6); E(movs_imm, 0, 0); E(strb_imm, 0, 1, VS); E(strh_imm, 0, 1, VG); E(movs_imm, 0, 255); E(strb_imm, 0, 1, VO)
    if V3:                                                                       # (V3) its FM slot's TRIG seen from 0
        E(bl, "c_pyslot"); E(lsls_imm, 0, 0, 6); imm32(1, FVB + 48); E(adds_reg, 1, 1, 0); E(movs_imm, 0, 0); E(strh_imm, 0, 1, 0)
    for f in (VD.PV_G, VD.PV_TGT, VD.PV_TRIG, VD.PV_SEEN): E(movs_imm, 3, 0); wf(f)
    E(mov_reg, 0, 4); E(bl, L["c_ssk"]); E(mov_reg, 3, 0); wf(KW)
    E(adds_imm8, 6, 1); E(cmp_imm, 6, NV); bc("tk_i", "lo")
    E(mov_reg, 0, 4); E(movs_imm, 1, 1); E(bl, "c_pypvw"); E(b, "tk_n")
    a.label("tk_off")
    E(mov_reg, 0, 4); E(movs_imm, 1, 0); E(bl, "c_pypvw")
    E(movs_imm, 6, 0)
    a.label("tk_z"); vptr(1, 6); E(movs_imm, 0, 0); E(strb_imm, 0, 1, VS); E(adds_imm8, 6, 1); E(cmp_imm, 6, NV); E(b_cond, "tk_z", "lo")
    E(b, "tk_n")
    a.label("tk_e")
    E(ldrb_imm, 0, 5, O_ACT); E(cmp_imm, 0, 0); bc("tk_n", "eq")
    if V5 and not V6:                                                            # (V5) a jump to send: before the starts' NOTEs
        E(ldrb_w, 0, 5, O_JPEND); E(cmp_imm, 0, 0); E(b_cond, "tk_nj", "eq"); E(movs_imm, 0, 0); E(strb_w, 0, 5, O_JPEND)
        E(ldrb_w, 1, 5, O_JCNT); E(adds_imm8, 1, 1); E(strb_w, 1, 5, O_JCNT)
        E(movs_imm, 0, 48); E(muls, 0, 4); imm32(2, VD.OS2B0 + VD.JMP_OFF); E(adds_reg, 0, 0, 2); E(bl, "c_pyw")
        a.label("tk_nj")
    if V7:                                                                       # (V7) the count changed: every sounding voice's target again
        E(bl, "c_pycnt"); E(ldrb_w, 1, 5, O_NCNT); E(cmp_reg, 0, 1); E(b_cond, "tk_gs", "eq"); E(strb_w, 0, 5, O_NCNT)
        E(movs_imm, 6, 0)
        a.label("tk_gd"); vptr(1, 6); E(raw, MRS7); E(raw, CPSID)
        E(ldrb_imm, 0, 1, VS); E(movs_imm, 3, SND); E(tst_reg, 0, 3); E(b_cond, "tk_gn", "eq"); E(movs_imm, 3, DIRTY); E(orrs_reg, 0, 3); E(strb_imm, 0, 1, VS)
        a.label("tk_gn"); E(raw, MSR7); E(adds_imm8, 6, 1); E(cmp_imm, 6, NV); E(b_cond, "tk_gd", "lo")
        a.label("tk_gs")
    E(movs_imm, 6, 0)                                                            # the voices: the targets to write, the starts
    a.label("tk_v")
    vptr(1, 6); E(mov_reg, 10, 1)
    E(raw, MRS7); E(raw, CPSID)
    E(ldrb_imm, 0, 1, VS); E(movs_imm, 2, 0)
    E(movs_imm, 3, DIRTY); E(tst_reg, 0, 3); E(b_cond, "tv_1", "eq"); E(bics_reg, 0, 3); E(movs_imm, 2, 1)
    a.label("tv_1"); E(movs_imm, 3, PEND); E(tst_reg, 0, 3); E(b_cond, "tv_2", "eq")
    E(ldrb_imm, 3, 1, VP); E(cmp_imm, 3, 0); E(b_cond, "tv_s", "eq"); E(subs_imm8, 3, 1); E(strb_imm, 3, 1, VP); E(b, "tv_2")
    a.label("tv_s"); E(movs_imm, 3, PEND); E(bics_reg, 0, 3); E(movs_imm, 3, SND); E(orrs_reg, 0, 3)
    E(ldrh_imm, 3, 1, VG); E(adds_imm8, 3, 1); E(strh_imm, 3, 1, VG); E(movs_imm, 3, 2); E(orrs_reg, 2, 3)
    a.label("tv_2"); E(movs_imm, 3, 7); E(tst_reg, 0, 3); E(b_cond, "tv_3", "ne")
    E(ldrb_imm, 3, 1, VO); E(cmp_imm, 3, 255); E(b_cond, "tv_3", "eq"); E(adds_imm8, 3, 1); E(strb_imm, 3, 1, VO)
    a.label("tv_3")
    if V5: E(movs_imm, 3, NPEND); E(tst_reg, 0, 3); E(b_cond, "tv_3n", "eq"); E(bics_reg, 0, 3); E(adds_imm8, 2, 8); a.label("tv_3n")   # (V5) the note alone
    E(strb_imm, 0, 1, VS)
    E(raw, MSR7)
    E(mov_reg, 9, 0); E(mov_reg, 11, 2)
    TV5 = "tv_nt" if V5 else "tv_5"
    E(lsrs_imm, 2, 2, 2); E(b_cond, "tv_4", "lo"); E(bl, "c_pyvals"); E(b, TV5)      # a start
    a.label("tv_4"); E(mov_reg, 2, 11); E(lsrs_imm, 2, 2, 1); E(b_cond, TV5, "lo"); E(bl, "c_pytgt")
    if V5:
        a.label("tv_nt"); E(mov_reg, 2, 11); E(lsrs_imm, 2, 2, 4); E(b_cond, "tv_5", "lo")
        E(mov_reg, 1, 10); E(ldrb_imm, 3, 1, VN); wf(VD.PV_NOTE)
    a.label("tv_5"); E(adds_imm8, 6, 1); E(cmp_imm, 6, NV); bc("tk_v", "lo")
    if V5:                                                                       # (V5) the refresh: one voice every 8 ticks, six voices
        E(ldrb_imm, 6, 5, O_RR); E(adds_imm8, 6, 1); E(cmp_imm, 6, 8 * NV); E(b_cond, "tr_w", "lo"); E(movs_imm, 6, 0)
        a.label("tr_w"); E(strb_imm, 6, 5, O_RR)
        E(movs_imm, 0, 7); E(tst_reg, 6, 0); bc("tr_p", "ne"); E(lsrs_imm, 6, 6, 3)
    elif V4:                                                                     # (V4) the refresh: one voice every 8 ticks
        E(ldrb_imm, 6, 5, O_RR); E(adds_imm8, 6, 1); E(movs_imm, 0, 31); E(ands_reg, 6, 0); E(strb_imm, 6, 5, O_RR)
        E(movs_imm, 0, 7); E(tst_reg, 6, 0); bc("tr_p", "ne"); E(lsrs_imm, 6, 6, 3)
    else:
        E(ldrb_imm, 6, 5, O_RR); E(adds_imm8, 6, 1); E(movs_imm, 0, 3); E(ands_reg, 6, 0); E(strb_imm, 6, 5, O_RR)     # the refresh: one voice a tick
    vptr(1, 6); E(mov_reg, 10, 1); E(ldrb_imm, 0, 1, VS); E(mov_reg, 9, 0)
    E(movs_imm, 3, PEND); E(tst_reg, 0, 3); E(b_cond, "tr_p", "ne")
    E(bl, "c_pyvals")
    E(mov_reg, 0, 4); E(bl, L["c_ssk"]); E(mov_reg, 3, 0); wf(KW)
    E(mov_reg, 0, 9); E(movs_imm, 3, 7); E(tst_reg, 0, 3); E(b_cond, "tr_p", "ne")
    E(mov_reg, 1, 10); E(ldrb_imm, 0, 1, VO); E(cmp_imm, 0, 2); E(b_cond, "tr_p", "lo")
    E(movs_imm, 3, 0); wf(VD.PV_G)                                              # off for a while: G 0, TSEEN = TRIG
    E(mov_reg, 1, 10); E(ldrh_imm, 3, 1, VG); wf(VD.PV_SEEN)
    a.label("tr_p")
    if V3: E(bl, "c_pyfmv")                                                      # (V3) the FM voices (r4 / r5 kept)
    E(cmp_imm, 6, 0); E(b_cond, "tk_n", "ne"); E(mov_reg, 0, 4); E(movs_imm, 1, 1); E(bl, "c_pypvw")
    a.label("tk_n"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 2); bc("tk_l", "lo")
    E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], lr=True)); E(b_w, prev["svc"])

    if V3:
        import fmeng as FE
        # ---- c_pyfmp(r0 = track) -> r0 = 1 in FM with its poly selected; clobbers r1-r3
        a.label("c_pyfmp")
        E(push_list, [4], lr=True); E(mov_reg, 4, 0)
        E(bl, L["c_fmact"]); E(cmp_imm, 0, 0); E(b_cond, "fp_x", "eq")
        E(mov_reg, 0, 4); E(bl, "c_pyflag")
        a.label("fp_x"); E(pop_list, [4], pc=True)

        # ---- c_pyvmx(r4 = track, r5 = its block): + O_VMAX = 2 when both tracks are in FM poly, else 4; a change: every voice of the track off
        a.label("c_pyvmx")
        E(push_list, [6, 7], lr=True)
        E(movs_imm, 6, 4)
        E(mov_reg, 0, 4); E(bl, "c_pyfmp"); E(cmp_imm, 0, 0); E(b_cond, "vm_w", "eq")
        if V5: E(movs_imm, 6, NV)                                                # (V5) FM alone: six
        E(movs_imm, 0, 1); E(subs_reg, 0, 0, 4); E(bl, "c_pyfmp"); E(cmp_imm, 0, 0); E(b_cond, "vm_w", "eq"); E(movs_imm, 6, NV // 2 if V5 else 2)
        a.label("vm_w"); E(strb_w, 6, 5, O_VMAX)
        E(ldrb_w, 0, 5, O_VPRV); E(cmp_reg, 0, 6); E(b_cond, "vm_x", "eq"); E(strb_w, 6, 5, O_VPRV)
        E(movs_imm, 6, 0)
        a.label("vm_o"); vptr(2, 6); E(raw, MRS7); E(raw, CPSID); E(ldrb_imm, 3, 2, VS); E(movs_imm, 0, 7); E(tst_reg, 3, 0); E(b_cond, "vm_o2", "eq")
        E(movs_imm, 3, DIRTY); E(strb_imm, 3, 2, VS); E(movs_imm, 3, 0); E(strb_imm, 3, 2, VO)
        a.label("vm_o2"); E(raw, MSR7)
        E(movs_imm, 3, 0); wf(VD.PV_TGT); E(movs_imm, 3, 0); wf(VD.PV_G)              # silent at once (the DSP skips it: no slot shared while it fades)
        E(adds_imm8, 6, 1); E(cmp_imm, 6, NV); E(b_cond, "vm_o", "lo")
        a.label("vm_x"); E(pop_list, [6, 7], pc=True)

        # ---- c_pyslot(r4 = track, r5 = block, r6 = voice) -> r0 = its FM slot; clobbers r1
        a.label("c_pyslot")
        if V5: E(mov_reg, 0, 6); E(ldrb_w, 1, 5, O_VMAX); E(cmp_imm, 1, NV // 2); E(b_cond, "sl_x", "ne"); E(lsls_imm, 1, 4, 1); E(adds_reg, 1, 1, 4); E(adds_reg, 0, 0, 1)   # 3 t + v
        else: E(mov_reg, 0, 6); E(ldrb_w, 1, 5, O_VMAX); E(cmp_imm, 1, 2); E(b_cond, "sl_x", "ne"); E(lsls_imm, 1, 4, 1); E(adds_reg, 0, 0, 1)
        a.label("sl_x"); E(raw, RET)

        # ---- c_pyfmb(r4 = track, r6 = voice) -> r3 = the voice's FM blocks (X:FV0 + 48 slot) in FM, else 0; clobbers r0-r2
        a.label("c_pyfmb")
        E(push_list, [5], lr=True)
        E(mov_reg, 0, 4); E(bl, L["c_fmact"]); E(movs_imm, 3, 0); E(cmp_imm, 0, 0); E(b_cond, "fb_x", "eq")
        E(mov_reg, 0, 4); E(bl, "c_pytb"); E(mov_reg, 5, 0); E(bl, "c_pyslot")
        if V5: E(lsls_imm, 0, 0, 2); imm32(3, T["fva"]); E(raw, FE.ldr_reg(3, 3, 0))     # (V5) the slots' table
        else: E(movs_imm, 1, 48); E(muls, 0, 1); imm32(3, VD.FV0); E(adds_reg, 3, 3, 0)
        a.label("fb_x"); E(pop_list, [5], pc=True)

        # ---- c_pyfmv(r4 = track, r5 = block): the FM voices of a track in FM poly (each every second tick; a new one at once)
        a.label("c_pyfmv")
        E(raw, pushw([4, 5, 6, 7, 8, 9, 10, 11], lr=True))
        E(mov_reg, 0, 4); E(bl, L["c_fmact"]); E(cmp_imm, 0, 0); bc("fv_x", "eq")
        E(ldrb_imm, 0, 5, O_ACT); E(cmp_imm, 0, 0); bc("fv_x", "eq")
        imm32(0, FVSIG_AT if V5 else FVB + 256); E(ldr_imm, 1, 0, 0); imm32(2, FVSIG); E(cmp_reg, 1, 2); E(b_cond, "fv_s", "eq")   # the voices' blocks: signed
        E(str_imm, 2, 0, 0); imm32(0, FVB); E(movs_imm, 1, 0); E(movs_imm, 2, 16 * NV if V5 else 64)
        a.label("fv_z"); E(str_imm, 1, 0, 0); E(adds_imm8, 0, 4); E(subs_imm8, 2, 1); E(b_cond, "fv_z", "ne")
        a.label("fv_s")
        if V4: imm32(0, FE.SHC); E(movs_imm, 1, 0); E(str_imm, 1, 0, 0)               # (V4) fmeng reads the shape again
        E(mov_reg, 0, 4); E(bl, L["c_fmblk"]); E(mov_reg, 9, 0)                        # r9 = the track's FM block
        imm32(0, V.HAL_TICK); E(ldr_imm, 0, 0, 0); E(mov_reg, 10, 0)                   # r10 = now
        E(ldrb_w, 0, 5, O_FMC); E(adds_imm8, 0, 1); E(strb_w, 0, 5, O_FMC); E(mov_reg, 11, 0)   # r11 = the counter
        E(ldrb_w, 0, 5, O_VMAX); E(cmp_imm, 0, 0); E(b_cond, "fv_m", "ne"); E(movs_imm, 0, 4)
        a.label("fv_m"); E(mov_reg, 8, 0)                                               # r8 = the voices allowed
        E(movs_imm, 6, 0)
        a.label("fv_l")
        E(cmp_reg, 6, 8); bc("fv_d", "hs")
        E(bl, "c_pyslot"); E(mov_reg, 7, 0)                                             # r7 = the slot
        vptr(1, 6)                                                                      # r1 = the voice's RAM
        E(mov_reg, 0, 11); E(adds_reg, 0, 0, 6); E(movs_imm, 3, 1); E(ands_reg, 3, 0)   # r3 = 1: not its tick
        E(mov_reg, 0, 7); E(mov_reg, 2, 6); E(bl, "c_pyfm1")
        E(adds_imm8, 6, 1); E(b, "fv_l")
        a.label("fv_d"); E(movs_imm, 0, 0); E(mov_reg, 1, 9); E(strb_w, 0, 1, FE.B_DIRTY)
        a.label("fv_x"); E(raw, popw([4, 5, 6, 7, 8, 9, 10, 11], lr=True)); E(raw, RET)

        # ---- c_pyfm1(r0 = slot, r1 = the voice's RAM, r2 = voice, r3 = 1: not its tick, r4 = track, r9 = the track's FM block, r10 = now)
        #      frame: [sp] slot, [sp + 4] RAM, [sp + 8] voice, [sp + 12] track, [sp + 16] state, [sp + 20] new
        a.label("c_pyfm1")
        E(raw, pushw([4, 5, 6, 7, 8, 9, 10, 11], lr=True)); E(raw, h(0xB086))           # sub sp, #24
        E(str_sp, 0, 0); E(str_sp, 1, 4); E(str_sp, 2, 8); E(str_sp, 4, 12); E(mov_reg, 11, 3)
        E(lsls_imm, 0, 0, 6); imm32(7, FVB); E(adds_reg, 7, 7, 0)                       # r7 = the voice's block
        E(mov_reg, 1, 9); E(ldrb_w, 0, 1, FE.B_DIRTY); E(cmp_imm, 0, 0); E(b_cond, "p1_nd", "eq"); E(strb_w, 0, 7, FE.B_DIRTY)   # the track's dirty flag
        a.label("p1_nd"); E(ldr_sp, 1, 4)
        E(ldrb_imm, 2, 1, VS); E(str_sp, 2, 16)
        E(ldrh_imm, 3, 1, VG); E(ldrh_imm, 0, 7, 48); E(movs_imm, 5, 0); E(cmp_reg, 0, 3); E(b_cond, "p1_o", "eq")
        E(strh_imm, 3, 7, 48); E(lsrs_imm, 0, 2, 1); E(b_cond, "p1_o", "lo"); E(movs_imm, 5, 1)      # a new TRIG while sounding (else only seen)
        a.label("p1_o"); E(str_sp, 5, 20)
        E(cmp_imm, 5, 0); E(b_cond, "p1_g", "ne")
        E(lsrs_imm, 2, 2, 1); bc("p1_x", "lo")                                          # not sounding: nothing
        E(mov_reg, 0, 11); E(cmp_imm, 0, 0); bc("p1_x", "ne")                           # not its tick
        a.label("p1_g")
        E(ldr_imm, 0, 7, FE.B_LAST); E(mov_reg, 1, 10); E(str_imm, 1, 7, FE.B_LAST); E(subs_reg, 5, 1, 0)   # r5 = dt
        E(cmp_imm, 5, 50); E(b_cond, "p1_d", "ls"); E(movs_imm, 5, 50)
        a.label("p1_d"); E(cmp_imm, 5, 0); E(b_cond, "p1_d1", "eq"); E(ldr_sp, 0, 20); E(cmp_imm, 0, 0); E(b_cond, "p1_d2", "eq")
        a.label("p1_d1"); E(movs_imm, 5, 1)                                             # (a new note: 1 ms)
        a.label("p1_d2")
        if V5: E(ldr_sp, 1, 4); E(ldrb_imm, 0, 1, VN); E(strb_w, 0, 7, FE.B_NOTE)          # (V5) its note (a legato move)
        E(mov_reg, 1, 9)                                                                # the track's parameters (16 B)
        for k in range(4): E(ldr_imm, 0, 1, 4 * k); E(str_imm, 0, 7, 4 * k)
        E(mov_reg, 0, 7); E(bl, L["c_fmalg"]); E(mov_reg, 6, 0)                         # r6 = the algorithm
        E(ldr_sp, 0, 20); E(cmp_imm, 0, 0); E(b_cond, "p1_n", "eq")                     # a new note: as fmeng's
        E(ldr_sp, 1, 4); E(ldrb_imm, 0, 1, VV); E(strb_w, 0, 7, FE.B_VEL); E(ldrb_imm, 0, 1, VN); E(strb_w, 0, 7, FE.B_NOTE)
        E(movs_imm, 0, 1); E(strb_w, 0, 7, FE.B_DIRTY); E(movs_imm, 0, 15); E(strb_w, 0, 7, FE.B_ATK)
        E(ldrb_imm, 0, 6, FE.A_SUS); E(cmp_imm, 0, 0); E(b_cond, "p1_pz", "ne"); E(movs_imm, 0, 15); E(strb_w, 0, 7, FE.B_PHR)
        a.label("p1_pz"); E(movs_imm, 1, 0)
        a.label("p1_z")
        E(adds_reg, 0, 7, 1); E(ldrb_imm, 0, 0, FE.P_ATK); E(cmp_imm, 0, FE.CENTRE); E(b_cond, "p1_zz", "lo")
        E(ldrb_imm, 0, 6, FE.A_SUS); E(lsrs_reg, 0, 1); E(movs_imm, 2, 1); E(ands_reg, 0, 2); E(cmp_imm, 0, 0); E(b_cond, "p1_zn", "ne")
        a.label("p1_zz"); E(lsls_imm, 0, 1, 1); E(adds_reg, 0, 0, 7); E(movs_imm, 2, 0); E(strh_imm, 2, 0, FE.B_ENV)
        a.label("p1_zn"); E(adds_imm8, 1, 1); E(cmp_imm, 1, 4); E(b_cond, "p1_z", "lo")
        if V4: E(ldrb_w, 0, 7, 50); E(cmp_imm, 0, 0); E(b_cond, "p1_n", "ne"); E(movs_imm, 0, 1); E(strb_w, 0, 7, 50)   # (V4) the slot's first use only
        if V5: E(ldr_sp, 0, 0); E(lsls_imm, 0, 0, 2); imm32(1, T["fva"]); E(raw, FE.ldr_reg(0, 1, 0)); E(adds_imm8, 0, VD.F_AS); E(mov_reg, 8, 0)
        else: E(ldr_sp, 0, 0); E(movs_imm, 1, 48); E(muls, 0, 1); imm32(1, VD.FV0 + VD.F_AS); E(adds_reg, 0, 0, 1); E(mov_reg, 8, 0)   # the DSP's AMP_s / y[n - 2] 0
        E(movs_imm, 0, 4); E(mov_reg, 11, 0)
        a.label("p1_w"); E(mov_reg, 0, 8); E(movs_imm, 1, 0); E(bl, L["c_fmw"]); E(mov_reg, 0, 8); E(adds_imm8, 0, VD.F_O2 - VD.F_AS); E(movs_imm, 1, 0); E(bl, L["c_fmw"])
        E(mov_reg, 0, 8); E(adds_imm8, 0, VD.FMS); E(mov_reg, 8, 0); E(mov_reg, 0, 11); E(subs_imm8, 0, 1); E(mov_reg, 11, 0); E(b_cond, "p1_w", "ne")
        a.label("p1_n")
        E(movs_imm, 0, 1); E(ldr_sp, 1, 20); E(cmp_imm, 1, 0); E(b_cond, "p1_gt", "ne")   # the gate: new, or held
        E(ldr_sp, 1, 16); E(lsrs_imm, 1, 1, 2); E(b_cond, "p1_gt", "hs"); E(movs_imm, 0, 0)
        a.label("p1_gt")
        E(mov_reg, 4, 7); E(mov_reg, 7, 0); E(bl, L["c_fmenv"])                         # r4 = the block, r5 = dt, r6 = alg, r7 = gate
        if V5: imm32(3, FE.CTX); E(ldr_sp, 1, 0); E(lsls_imm, 1, 1, 2); imm32(0, T["fva"]); E(raw, FE.ldr_reg(0, 0, 1)); E(str_imm, 0, 3, 0)
        else: imm32(3, FE.CTX); E(ldr_sp, 1, 0); E(movs_imm, 2, 48); E(muls, 2, 1); imm32(0, VD.FV0); E(adds_reg, 0, 0, 2); E(str_imm, 0, 3, 0)   # its blocks
        E(ldrb_w, 1, 4, FE.B_NOTE); E(lsls_imm, 1, 1, 2); imm32(2, T["inc"]); E(FE.ldr_reg, 1, 2, 1); E(str_imm, 1, 3, 4)                  # its increment
        E(ldr_sp, 0, 12); E(ldr_sp, 1, 8); E(bl, "c_pyrec"); E(adds_imm8, 0, VD.NZ_OFF - 28); imm32(3, FE.CTX); E(str_imm, 0, 3, 8)        # its noise
        imm32(0, FE.CTXSIG); E(str_imm, 0, 3, 12)
        E(ldr_sp, 7, 12); E(bl, L["c_fmsend"])                                          # r4 = the block, r6 = alg, r7 = track
        imm32(3, FE.CTX); E(movs_imm, 0, 0); E(str_imm, 0, 3, 0); E(str_imm, 0, 3, 4); E(str_imm, 0, 3, 8); E(str_imm, 0, 3, 12)
        E(ldr_sp, 0, 20); E(cmp_imm, 0, 0); E(b_cond, "p1_x", "ne")                     # let go and its envelopes down: freed
        E(ldr_sp, 0, 16); E(movs_imm, 1, HELD | PEND); E(tst_reg, 0, 1); E(b_cond, "p1_x", "ne")
        E(movs_imm, 1, 0)
        a.label("p1_e"); E(lsls_imm, 2, 1, 1); E(adds_reg, 2, 2, 4); E(ldrh_imm, 2, 2, FE.B_ENV); E(cmp_imm, 2, 64); E(b_cond, "p1_x", "hs")
        E(adds_imm8, 1, 1); E(cmp_imm, 1, 4); E(b_cond, "p1_e", "lo")
        E(ldr_sp, 1, 4); E(raw, MRS7); E(raw, CPSID)
        E(ldrb_imm, 0, 1, VS); E(movs_imm, 2, HELD | PEND); E(tst_reg, 0, 2); E(b_cond, "p1_f", "ne")
        E(movs_imm, 2, SND); E(bics_reg, 0, 2); E(movs_imm, 2, DIRTY); E(orrs_reg, 0, 2); E(strb_imm, 0, 1, VS); E(movs_imm, 0, 0); E(strb_imm, 0, 1, VO)
        a.label("p1_f"); E(raw, MSR7)
        a.label("p1_x"); E(raw, h(0xB006)); E(raw, popw([4, 5, 6, 7, 8, 9, 10, 11], lr=True)); E(raw, RET)       # add sp, #24

    # ---- c_pypad (the template view's slot 0: view, pad, velocity): Shift + pad 29 with the engine on = retrigger -> legato -> poly
    a.label("c_pypad")
    E(cmp_imm, 1, PAD29); E(b_cond, "pp_c", "eq"); E(b_w, prev["pad"])
    a.label("pp_c")
    E(push_list, [0, 1, 2, 4, 5], lr=True)
    E(ldrb_imm, 4, 0, 0x10); E(movs_imm, 1, 1); E(ands_reg, 4, 1)
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "pp_p", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_von"]); E(cmp_imm, 0, 0); E(b_cond, "pp_p", "eq")
    E(bl, L["c_rtb"]); E(cmp_imm, 0, 0); E(b_cond, "pp_e", "eq")
    E(ldrb_imm, 1, 0, 0); E(lsrs_imm, 2, 1, 4); E(cmp_imm, 2, 0xA); E(b_cond, "pp_t", "eq"); E(movs_imm, 1, 0xA0)
    a.label("pp_t"); E(movs_imm, 2, 1); E(lsls_reg, 2, 4); E(lsls_imm, 3, 2, 2)  # r2 = the legato bit, r3 = the poly bit
    E(tst_reg, 1, 3); E(b_cond, "pp_po", "ne")
    E(tst_reg, 1, 2); E(b_cond, "pp_lg", "ne")
    E(orrs_reg, 1, 2); E(b, "pp_w")                                              # retrigger -> legato
    a.label("pp_lg"); E(bics_reg, 1, 2); E(orrs_reg, 1, 3); E(b, "pp_w")          # legato -> poly
    a.label("pp_po"); E(bics_reg, 1, 3); E(bics_reg, 1, 2)                        # poly -> retrigger
    a.label("pp_w"); E(strb_imm, 1, 0, 0)
    a.label("pp_e"); E(pop_list, [0, 1, 2, 4, 5], pc=True)
    a.label("pp_p"); E(raw, popw([0, 1, 2, 4, 5], lr=True)); E(b_w, prev["pad"])

    # ---- c_pyleds (the template view's slot 7: view -> the LED buffer): with Shift, the engine on and poly, pad 29 magenta
    a.label("c_pyleds")
    E(push_list, [4, 5], lr=True)
    E(ldrb_imm, 4, 0, 0x10); E(movs_imm, 1, 1); E(ands_reg, 4, 1)
    E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "pl_x", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_von"]); E(cmp_imm, 0, 0); E(b_cond, "pl_x", "eq")
    E(mov_reg, 0, 4); E(bl, "c_pyflag"); E(cmp_imm, 0, 0); E(b_cond, "pl_x", "eq")
    E(movs_imm, 1, COL_POLY); E(strh_imm, 1, 5, 2 * PAD29)
    a.label("pl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add, after smst); the heads: the entries of vcf21's c_vnon / c_vnoff (their first 4 bytes, the push, moved into
    trampolines), the DSP service chain, the template view's slots 0 / 7."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("vcf20", k) for k in ("c_von", "c_vsmpb", "c_vrt7", "c_vnon", "c_vnoff")}
    L["c_shift"] = lab("sc15", "c_shift"); L["c_rtb"] = lab("retrig", "c_rtb"); L["c_msmode"] = lab("modesel", "c_msmode")
    L["c_fmact"] = lab("fmeng", "c_fmact"); L["c_ssk"] = lab("smst", "c_ssk")
    if V4: L["c_rtoff"] = lab("retrig", "c_rtoff")
    if V3:
        for k in ("c_fmblk", "c_fmalg", "c_fmenv", "c_fmsend", "c_fmw"): L[k] = lab("fmeng", k)
        assert (FVB + 64 * VD.PV_N <= MX.MXR + 0x980 and FVSIG_AT + 4 <= MX.MXR + 0x9B0) if V5 else FVB + 260 <= MX.MXR + 0x980
    want = pushw([0, 1, 2, 3, 4, 5, 6], lr=True)
    head_on, head_off = bytes(img[L["c_vnon"] - BASE:L["c_vnon"] - BASE + 4]), bytes(img[L["c_vnoff"] - BASE:L["c_vnoff"] - BASE + 4])
    assert head_on == want and head_off == want, (head_on.hex(), head_off.hex())
    prev = dict(svc=MP.bw_target(img, S14.SVC_HOOK, BASE), pad=u(TMPL_VT) & ~1, leds=u(TMPL_VT + 28) & ~1)
    code, labels = arm_code(base_addr, L, prev, head_on, head_off)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    img[L["c_vnon"] - BASE:L["c_vnon"] - BASE + 4] = b_w(L["c_vnon"], labels["c_pywon"])
    img[L["c_vnoff"] - BASE:L["c_vnoff"] - BASE + 4] = b_w(L["c_vnoff"], labels["c_pywoff"])
    img[S14.SVC_HOOK - BASE:S14.SVC_HOOK - BASE + 4] = b_w(S14.SVC_HOOK, labels["c_pytick"])
    struct.pack_into("<I", img, TMPL_VT - BASE, labels["c_pypad"] | 1)
    struct.pack_into("<I", img, TMPL_VT + 28 - BASE, labels["c_pyleds"] | 1)
    if V4: img[L["c_rtoff"] - BASE:L["c_rtoff"] - BASE + 4] = b_w(L["c_rtoff"], labels["c_vmrtoff"])     # (V4) retrig's answer from the voice mode
    if V5: prev["v5"] = 1                                                        # (V5) the tests adopt the layout (adopt)
    if V6: prev["v6"] = 1
    return labels, code, prev


def adopt(report):
    """For the tests: poly's and vcf21_dsp's layout constants as the build's (V5: six records a track, the blocks moved)."""
    if report.get("poly", {}).get("prev", {}).get("v5"):
        g = globals()
        g.update(V3=True, V4=True, V5=True, MODE_N=7, PY=MX.MXR + 0x1800, TBS=128, O_VMAX=120, O_FMC=121, O_VPRV=122, FVSIG_AT=MX.MXR + 0x9AC)
        VD.POLY6 = True; VD.PV_N = 6
        VD.PV_SCR, VD.PV_PC, VD.PV_EFF, VD.PV_R2 = 0x3FE4, 0x3FE5, 0x3FE6, 0x3FE7
        VD.FV_ADDRS = [0x3C00 + 48 * s_ for s_ in range(5)] + [0x3FB4]
        if report["poly"]["prev"].get("v6"): g.update(V6=True, MODE_N=8)
        return True
    return False
