"""SC21: the VCF / VCA mode of SC20 with the controls rearranged and new functions (ARM side; the DSP side is tools/vcf21_dsp.py).
Codes (the saved value of each, mailbox code = index + 1): 1 FILT (bipolar), 2 RES, 3 ENVF (envelope -> filter, bipolar), 4 LFOF (LFO -> filter, bipolar), 5 ATK, 6 DEC, 7 SUS, 8 REL,
9 FXAMT, 10 GAIN (64 = x1, 0 = closed, 127 = +18 dB with saturation), 11 LRATE, 12 LFOV (LFO -> VCA), 13 FXTYPE (0..3), 14 FXMOD (parameter of the effect), 15 ENVA (envelope -> VCA), 16 FTYPE (0..3).
Knobs, plain / Shift: K1 ATK / SUS, K2 REL / DEC, K3 ENVA / LFOV, K4 ENVF / LFOF, K5 FILT / FTYPE, K6 RES / GAIN, K7 LRATE / FXMOD, K8 FXAMT / FXTYPE (KNOB_CODES).
Original text of SC20:
SC20: VCF / VCA for the audio inputs of the MIDI tracks.

A toggle pad (pad 26, the one right of the patch flip) in the Preset view of MIDI 1 / MIDI 2 switches the mode of that track: the audio input of the track (line input 1 / 2, or the reverb /
delay return when the Setup sends it to strip 3 / 4) goes through a bipolar VCF, drive + saturation and a VCA with an ADSR envelope and an LFO, in front of the mixer strip.
Patch flip and this mode exclude each other (turning one on turns the other off).
  * the 8 knobs of the track are the VCF / VCA controls (Shift = second layer, see KNOBS); the track's notes (sequenced, recorded or played) are still sent as MIDI as always and also
    open the gate of the envelope (the note wrappers of the note vtable 0x08059FC4 / C8 count the held notes);
  * state: the 75 reserved bytes at the end of the global settings record (settings object 0x2003974C + 0x3D ...): the toggles, 2 x 16 values, and the volatile bookkeeping (held notes, dirty
    bits, tags); saved by the stock save 0x0802D2AC (throttled, called from the knob / pad handlers: the UI thread, like the stock listener); the values belong to the unit, not to the project;
  * the DSP is told through a mailbox at X:$3B80 + 48 t (tag << 23 | code << 16 | value): one message per voice per tick of the DSP service chain (head of the chain, in front of SC19's tick).
Tail layout (offset from SETOBJ + 0x3D): +0 flags (bit 0 MIDI 1 on, bit 1 MIDI 2 on, bit 7 initialised), +1..16 values of track 0, +17..32 of track 1 (code 1..16, signed bytes), +33 / +41 volatile blocks
of 8 bytes [held notes, note, velocity, aux (bit 0 ACT, 1 NOTE, 2 VEL, 3 GATE, 4 TRIG dirty), dirty mask lo, hi, tag, -], +49 time of the last save (units of 32 ms).
Boot / project load: the Master FX block byte 179 bit 3 (zero when the block is created = at power-up) marks "initialised this session": the volatile blocks are cleared and everything is sent.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, ldrh_imm, ldrb_w, strb_w, strb_imm, strh_imm, lsls_imm, lsrs_imm, mov_reg,  # noqa: E402
                   movs_imm, movt, movw, pop_list, push_list, raw, h, adds_imm8, subs_imm8, adds_reg, subs_reg, ands_reg, orrs_reg, bics_reg,
                   eors_reg, muls, tst_reg, lsls_reg, lsrs_reg, str_imm, ldr_sp, ldrb_reg, ldrh_reg, strh_reg, blx_reg)

SETOBJ = 0x2003974C
TAIL = SETOBJ + 0x3D
SAVE_FN = 0x0802D2AC
CTX_PTR = 0x200069E4
STOCK_KNOB = 0x0804C062
STOCK_LEDS = 0x08047592
TMPL_VT_LEDS = 0x0805AE5C + 0x1C
AC64_VT = 0x0805AC64
NOTE_VT = (0x08059FC4, 0x08059FC8)
T_PAD_SITE, T_PAD_RET, T_DRAW = 0x0804D59E, 0x0804D5C0, 0x0804D5CA
PARAM_GET, PARAM_PTR, COMMIT = 0x0803542C, 0x080354FA, 0x080353C0
DSP_WRITE = 0x080292F8
HAL_TICK = 0x2000081C
VB0, VBS = 0x3B80, 48
FLAGS_BYTE, B_BOOT = 179, 8                      # persist19.FLAGS in the Master FX block; bit 3 = "initialised this session"
PAD_VCF = 25                                      # pad 26 (index 25); the patch flip is index 24
PAD_FLIP = 24                                     # the patch flip of SC06 (build_sc06.PF_PAD)
COL_ON, COL_OFF = 0x13, 0x14                      # yellow bright / dim (the RGB table of 0x0803423C: 19 = 255, 221, 68)
CCED = False                                      # SC23: the on-device editor of the CC assignments of the MIDI macros (see use_cced)
NEUTRAL = False                                   # SC23.3: neutral defaults (a basic gate: filter open, no resonance, envelope -> VCA at the maximum, sustain maximum, A / D / R 0, no LFO, no FX; the oscillator a plain sine)
CLEARK = False                                    # SC23.3: Clear + a knob of the mode: the value goes back to its default, the knob LED is red while Clear is held
OCTLED = False                                    # SC23.3: the editor lights Octave v (a next field exists) and Octave ^ (a previous one exists)
CLR_RED = 0x53                                    # the stock LED code of the Clear feedback
FXCAP = False                                     # SC23.3: with the Setup's "FX return to the line input" of a strip on, its sends (both effects) are capped at half and the knob moves them at half speed
FX_SUB_VT = 0x0805AF3C                            # the class of the two sub-views of the FX view: slot 4 = the knob
LEDCLEAN = False                                  # SC23.3: the pads the CC editor drew (the numbers) are cleaned when the numbers go away (the stock view only redraws pads 1-8)
RATE_MS = 2
RATELIMIT = False                                 # SC23.5: at most one mailbox message per voice every 2 ms (the DSP reads its mailbox once per block, 0.67 ms: two writes in a block lose BOTH, the 1-bit tag then equals the old one)
HEARTBEAT = False                                 # SC23.5: the ARM repeats ACT / NOTE / VEL / GATE every ~32 ms (one of them each ~8 ms) so a message the DSP missed heals; the velocity starts at 100
TYPEZONE = False                                  # SC23.6: the type knobs (FX type, filter type, waveform) have wide zones, no wrap-around, a colour per mode and the brightness of the parameter inside the mode
TCOL_FX = (0x2D, 0x2B, 0x45, 0x32, 0x49, 0x09, 0x4D)   # soft yellow, hard orange, fold red, wavefold magenta, ring mod violet, comb blue, chorus teal
TCOL_FT = (0x01, 0x17, 0x13, 0x2D, 0x32, 0x4D, 0x09)   # DJ white, LP 12 green, HP 12 light blue, band-pass yellow, notch magenta, LP 24 teal, HP 24 blue
TCOL_WV = (0x13, 0x17, 0x2D, 0x45)                      # sine light blue, triangle green, saw yellow, square red
TZ_MINB = 32                                      # the dimmest the type LED gets (0..127), so the colour stays readable
DUALUI = False                                    # SC24: pad 27 = off / line in / oscillator, the page row (pads 1-8), pad 28 = two oscillators, pad 29 = chain order, the second oscillator's values, paraphonic notes
V2_OFF = 180                                      # the volatile values (codes 27..34, 8 per track) live in the Master FX block (c_gfst), after its 180 bytes (build_sc24 grows the block by 16)
KNOB_CODES_C = (27, 30, 0, 0, 0, 0, 29, 0,  28, 33, 34, 0, 0, 0, 0, 0)      # the OSC2 page: K1 TUNE2, K2 SHAPE2 (PW2), K7 WAVE2; Shift: K1 FINE2, K2 FM, K3 RING
DEFAULTS_V2 = (0, 0, 0, 50, 64, 0, 0, 0)                                    # TUNE2 FINE2 WAVE2 PW2 MIX BITSYNC FM RING
TCOL_BS = (0x01, 0x13, 0x32, 0x2D, 0x45, 0x17, 0x4D)                        # BITSYNC zones: none white, sync light blue, xor magenta, or yellow, nor red, and green, nand teal
COL_PAGE = ((0x2B, 0x2C), (0x17, 0x18), (0x4D, 0x4E))                       # the page pads (VCA / VCF, OSC1, OSC2): bright / dim
COL_ROUTE = (0x13, 0x14)
TDRAW = False                                     # SC25: with the mode off the stock template row (pads 1-8) is redrawn every frame (the page row of the mode had overwritten it)
CCIO = False                                      # SC25: MIDI CC / NRPN out and in for the values of the mode, automation of 8 of them through the macro lanes of the sequencer
TXOBJ = 0x20011334                                # the stock Tx interface: [+0xC] = the table of the channels of the tracks (index = track id; MIDI 1 / 2 = 2 / 3)
REC_GATE_OBJ, REC_GATE = 0x2003C168, 0x0802E62C   # the automation gate: (gate, id, value) -> the recorder of the track; ids 20 + k (MIDI 1) / 30 + k (MIDI 2) = the lane k = macro k
PLAY_STORE = 0x20011034                           # the store the Play button toggles
MIDI_IN_FLAG = 0x20000A6C                         # bit 2 set = MIDI input disabled
CC_HELPER = 0x0804A356                            # the (SC05) template CC helper: (channel, 0xB0, cc, value)
STK_EMIT, STK_MIDIIN = 0x080313C4, 0x08051834     # the sender of the macro CCs (also what the sequencer calls on playback) and the CC section of the MIDI-in function
# code (1..34) -> (type, number): type 0 = CC number; 0x80 | MSB = NRPN (MSB, number = LSB); 0xFF = none.  The CC / NRPN numbers of the stock synth where the function is the same (or close), NRPN 4:code otherwise
CC_TAB = {1: (0, 74), 2: (0, 71), 3: (0, 79), 4: (0x84, 4), 5: (0, 73), 6: (0, 75), 7: (0, 70), 8: (0, 72), 9: (0, 91), 10: (0, 59), 11: (0x80, 76), 12: (0x84, 12), 13: (0x84, 13), 14: (0xFF, 0),
          15: (0x84, 15), 16: (0x84, 16), 17: (0, 26), 18: (0, 27), 19: (0, 20), 20: (0, 21), 21: (0x84, 21), 22: (0x84, 22), 23: (0x84, 23), 24: (0x84, 24), 25: (0x84, 25), 26: (0x84, 26),
          27: (0, 37), 28: (0, 39), 29: (0, 30), 30: (0, 31), 31: (0, 52), 32: (0x84, 32), 33: (0x84, 33), 34: (0, 54)}
SDRUM = False                                     # SC26: the step-drummer of the MIDI tracks (see use_sdrum)
O_SD = 73                                         # tail byte: one nibble per MIDI track (bit 0 = step-drummer enabled, bits 1-3 = destination of the pitch row); the editor no longer keeps its view pointer there
F_SDOPEN, F_SDPAGE, F_SDHALF = 0x10, 0x20, 0x40   # flags byte: the step-drummer view is open / its knob page (0 pitch, 1 velocity) / the half of the pattern shown (0 = steps 1-16, 1 = 17-32)
SD_AUD = 31                                       # Master FX block byte (unused otherwise): the step being auditioned (track << 6 | step + 1), 0 = none
ENGINE = 0x20038ECC                               # the sequencer engine: store [+0x30 + 4 track]: param 0 = pattern, 1 = step, 2 = tick inside the step
MGR_OBJ = 0x20040B10
PAD_SD = 29                                       # pad 30 of the MIDI Preset view: the step-drummer
SD_DEST = (17, 27, 19, 33, 31, 3, 20, 6)          # the destinations of the pitch row (pads 17-24): pitch of both oscillators (TUNE + FINE of both), pitch of OSC2 only, WAVE, FM, MIX, ENVF, SHAPE, DEC
SD_DCOL = (0x17, 0x4D, 0x2D, 0x32, 0x13, 0x2B, 0x45, 0x49)   # their colours (bright; the dim one is the next code, 0x37 for magenta)
SD_STEPCOL = ((0x13, 0x14), (0x45, 0x46))         # the steps: even pairs / odd pairs (bright = a note, dim = empty)
COL_SD = (0x49, 0x4A)                             # pad 30: view open / enabled (view closed)
SD_HEAD = 0x01                                    # the step that sounds: white
SD_TONIC, SD_LEN = 48, 6                          # the note of every step = the root of the scale in octave 2 (MIDI 48 + root); the length of a new note = one step (6 ticks)
TMPL_VT_REL = 0x0805AE5C + 4                      # slot 1 of the template view: the pad release (a stock no-op)
STK_REL = 0x0804759A
SD2 = False                                       # SC27: the step-drummer also on Synth 1 / 2 (the pitch row writes the lane of one of the 8 macros), the panel LEDs of its buttons, the knob of the pair that
                                                  # plays in white, the rows 2-3 dark again when the view closes (see use_sdrum2).  Tracks of the step-drummer: 0 / 1 = MIDI 1 / 2, 2 / 3 = Synth 1 / 2
PAGES5 = False                                    # SC27: two more knob pages (pads 4 / 5 of the page row): the 8 values the sequencer automates, and the modulation (ADSR on the top row, LFO on the bottom row)
VADRUM = False                                    # SC29: the VA-drum engine: a fourth state of pad 27 (off -> line in -> oscillator -> VA-drum -> off) and pad 31 = the velocity also sets the start level of
                                                  # the pitch and the filter envelopes.  The four bits live in the low nibble of the signature byte (0xB0..0xBF are all valid): bit t = VA-drum of track t,
                                                  # bit 2 + t = velocity -> envelopes; they go to the DSP in the ACT message (bits 10 / 11 of its value)
PAD_VEL = 30                                      # pad 31 (index 30)
GRAN = False                                      # SC36: the granular engine (DSP core 1, granular_dsp): pad 27 = off -> line in -> oscillator -> VA-drum -> granular -> off; the engine
                                                  # bits of the signature nibble: (VA-drum t, velocity 2 + t) = (0, 0) oscillator, (1, x) VA-drum, (0, 1) granular; ACT bit 12 = granular;
                                                  # the knob page of OSC1 becomes the granular page (GR_TAB: the values of the OSC pages are shared)
COL_GR = 0x32                                     # pad 27 in the granular state (magenta)
FXSEQ = False                                     # SC36: the FX step sequencer: pad 27 = ... -> granular -> FX sequencer -> off; the state = the mode on, the oscillator source off, the
                                                  # VA-drum bit set (the line in state has it clear); the voice is off in the DSP (ACT 0) and the step-drummer is enabled; while the
                                                  # transport runs, a step with notes switches on the Master FX effect its pair value picks (0 / no value = none; 1..127 in 7 zones:
                                                  # the top pads 1-6, then the Glitch) through build_sc17's hook c_fxsq
COL_FS = 0x09                                     # pad 27 in the FX sequencer state (blue)
FXSEQ2 = False                                    # SC36.1 (see use_fxseq2)
DUALHIDE = False                                  # SC37.4 (see use_dualhide)
STRETCH = False                                   # SC38.1 (see use_stretch)
RESETALL = False                                  # SC38.7 (see use_resetall)
RESETVIEW = False                                 # SC39.1 (see use_resetview)
GRSRC = False                                     # SC39.1 (see use_grsrc)
GRS_COL = (0x53, 0x45, 0x2D, 0x49, 0x4D)          # the source of the granular engine: the capture red, the sample of Drum 1..4 orange, yellow, violet, teal
GRS_MID = (12, 38, 64, 89, 115)                   # the middle of each zone of the 0..127 travel (zone = 5 p >> 7)
GRS_POS = S_SCR_POS = 64 + 82                     # Master FX block: the travel's position, one byte per track (the two bytes of the idle LED buffer the CC editor's scratch leaves free)
ST_STEPS = (1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64)   # SC38.1: the stretch lengths in steps (K3: (v + 64) x 12 / 128)
ST_TICKS = 6                                      # SC38.1: sequencer ticks per step (the transport's tick count, [[ENGINE + 0x90]] parameter 0)
FXSEQ3 = False                                    # SC36.2 (see use_fxseq3)
FSQ_U = 16                                        # SC36.2: knob units per FX sequencer value (the lane holds 0..6 * FSQ_U; value = (p + FSQ_U / 2) / FSQ_U)
FSQ_MAX = 6 * FSQ_U
SDKFIX = False                                    # SC41 (see use_sdknobfix)
FSQ_DIV = 1                                       # SC40.9 (see use_fxseq4): knob events per unit of the FX sequencer's position
# the granular page: (code, min, max, flags) per knob K1..K8, Shift + K1..K8; flags bit 0 = one step per turn; bits 1-3 = the LED: 0 bipolar, 1 the value,
# 2 the value + 64 (stored -64..63, shown 0..127), 3 (the value - min) x 2, 4 on / off
GR_TAB = ((17, -24, 24, 0), (19, 0, 126, 1 << 1), (21, -64, 63, 0), (18, -64, 63, 2 << 1), (20, 0, 100, 1 << 1), (23, -64, 63, 2 << 1), (24, -64, 63, 0), (22, -64, 63, 0),
          (28, -64, 63, 0), (33, 0, 127, 1 << 1), (34, 0, 127, 1 << 1), (29, 0, 126, 1 << 1), (30, 0, 100, 1 << 1), (26, 0, 1, 1 | 4 << 1), (27, -64, 63, 0), (25, -1, 63, 1 | 3 << 1))
KEEPNOTE = False                                  # SC31: the step-drummer keeps the note of every step (the conversion leaves the pitch of the first note of the step); a new note takes the
                                                  # note of its pair, else of the nearest earlier note (as its velocity), else the tonic; the audition plays that same note
RTREC = False                                     # SC33: while the unit records (transport store params 0 / 1 set, 2 clear), a step pad of the step-drummer (no Shift) also writes its note into the
                                                  # step that plays, with the micro step of the moment (tick in the step x 6 / ticks per step); the pad still auditions
TPS_TAB = 0x0805B8B8                              # ticks per step by the pattern's sync index (pattern + 0x382): 2, 3, 4, 6, 8, 12, 16, 24 (u32)
COL_VD = 0x45                                     # pad 27 in the VA-drum state
COL_VEL = (0x4D, 0x4E)                            # pad 31: on / off
KNOB_CODES_D = (17, 8, 15, 3, 1, 2, 11, 9,  0, 0, 0, 0, 0, 0, 0, 0)           # the lanes, in their order: TUNE, REL, ENVA, ENVF, FILT, RES, LRATE, FXAMT
KNOB_CODES_E = (5, 6, 7, 8, 11, 4, 12, 21,  15, 3, 22, 23, 24, 26, 25, 0)     # ATK DEC SUS REL / LRATE LFOF LFOV LFOP; Shift: ENVA ENVF ENVP ENVW / LFOW LFOM ENVM -
COL_PAGE2 = ((0x2D, 0x2E), (0x32, 0x37))          # the two new page pads: yellow, magenta (bright / dim)
SP_VT = 0x0805AC9C                                # the Preset view of the synths: slots 0 / 1 / 7 = pad press / release / LEDs
S_PAINT, F_SRC = 20, 4                            # the SC14 state byte with the "source view open" flag of SC19.1
GETTER = 0x08036192                               # (type, index) -> the value of a parameter of the session (type 0 / 1 = the patch of Synth 1 / 2; macro k position = index 174 + 17 k)
LANE_TAB = (17, 8, 15, 3, 1, 2, 11, 9)           # lane k of the sequencer (= macro k + 1) -> the code it automates: TUNE, REL, ENVA, ENVF, FILT, RES, LRATE, FXAMT
CLEARBOTH = False                                 # SC23.5: Clear + a knob resets both layers of the knob (plain and Shift): with Shift the Clear button loses its function
SAVELED = False                                   # SC23.5: the Save button of the top row (panel LED 57, after Duplicate) blinks with the Save pad at the save step
EDV2 = False                                      # SC23.4: the CC number picks the type (99 / 98 / 6 = NRPN with a 7-bit value, 38 = NRPN with a 14-bit value), after the last field a save step (the Save pad blinks,
                                                  # one more Octave v saves), the Save pad (next to pad 25) saves, the button of the track discards like any other view button
COL_SAVE = (0x17, 0x18)                           # the Save pad: green bright / dim
PAD_SAVE = 25                                     # the pad next to pad 25 (index 25): the patch flip pad while the editor is off
PADS2 = False                                    # SC23.2: pad 27 = source only, pad 28 = OSC view, pad 29 = VCF / VCA view (radio; the mode is on while one is lit)
CCED2 = False                                    # SC23.1: Octave v / ^ cycle the fields, the track button saves, other view buttons discard
O_ED = 71                                         # tail bytes: +71 editor state (bit 7 active, bit 6 knob selected, bits 3..5 field, bits 0..2 knob), +72 (bit 0 track, bit 1 changed), +73 / +74 the low half of the Preset view
S_SCR = 64                                        # scratch of the editor: the idle LED buffer of the Master FX block (84 B): 80 B of records + the template index at +80
PAD_CC = 24                                       # pad 25 (index 24) of the MIDI Preset view: the editor
COL_CC = (0x32, 0x37)                             # magenta bright / dim
ID_MIDI1, ID_SHIFT_BTN = 2, 27
BTN_STOCK, BTN_REL = 0x08033320, 0x0803381A
S_CUR = 0x152                                     # controller: 9 * track + sub-mode (0 = Preset view)
TPL_SAVE = 0x08031320                             # (store, template, index): writes one template (0x78 bytes, key 0x1F + index) to the persistent store
COLORS = False                                    # SC22.4: distinct pad colours (see use_colors)
COL_OSC = (0x17, 0x18)                            # oscillator pads (27 edit, 28 source), SC22.4: green bright / dim
COL_TRACK = (0x09, 0x3B)                          # MIDI 1 orange, MIDI 2 purple (the colours of the stock dynamic codes 0xD1 / 0xD9)
DEFAULTS = (0, 0, 0, 0, 0, 40, 100, 40, 0, 64, 40, 0, 0, 64, 0, 0)   # FILT RES ENVF LFOF ATK DEC SUS REL FXAMT GAIN LRATE LFOV FXTYPE FXMOD ENVA FTYPE
KNOB_CODES = (5, 8, 15, 3, 1, 2, 11, 9,  7, 6, 12, 4, 16, 10, 14, 13)   # code of K1..K8, then of Shift + K1..K8
BISEND = False                                    # SC22: ENVA (code 15) and LFOV (code 12) bipolar too
BIPOLAR_MASK = (1 << 0) | (1 << 2) | (1 << 3)                      # codes 1 (FILT), 3 (ENVF), 4 (LFOF) -> bit code - 1
O_FLAGS, O_PAR, O_RT = 0, 1, 33
RT_CNT, RT_NOTE, RT_VEL, RT_AUX, RT_DLO, RT_DHI, RT_TAG = range(7)
RT_DX = 7
OSC = False                                       # SC22.1: oscillator source + the knob page of the oscillator (see use_osc)
STRIDE = 16                                       # bytes of values per track (codes 1..16; with OSC 1..24: 17..21 = TUNE, FINE, WAVE, PW, LFOP)
PAD_OSC, PAD_PAGE = 26, 27                        # pads 27 / 28 (indices 26 / 27) of the Preset view of the MIDI tracks: oscillator source, knob page
KNOB_CODES_B = (17, 19, 21, 0, 0, 0, 0, 0,  18, 20, 0, 0, 0, 0, 0, 0)   # the oscillator page: K1 tune, K2 waveform, K3 vibrato; Shift: K1 fine, K2 pulse width (0 = no function)
OSC_DEFAULTS = (0, 0, 2, 64, 0)                   # TUNE FINE WAVE (2 = saw) PW (64 = 50 %) LFOP
DX_MASK = 0x1F                                    # codes 17..21 have a dirty bit in the third byte (17..24 with OSC2)
OSC3 = False                                      # SC22.3: 26 codes per track (the dirty bits of the codes 25 / 26 live in the bits 5 / 6 of the AUX byte), WAVE = a continuous morph (0..126), PW 0..100
FXTYPE_N = 4                                      # SC22: 7 FX types (soft, hard, fold, wavefold, ring mod, comb, chorus)
FTYPE_N = 4                                       # SC21.1: 3 (no tilt EQ): the filter type wraps 0..2
SIGNED = True                                    # SC20.1: byte +50 of the tail = SIG_VAL once the state was initialised by us
O_SIG, SIG_VAL = 50, 0xA6                         # SC21: another value than SC20.1 (0xA5): the saved values of SC20 mean other things
O_SAVED = 49                                      # 8-bit time of the last save (units of 32 ms)
SAVE_MS = 700
INV = {"eq": "ne", "ne": "eq", "cc": "cs", "cs": "cc", "lo": "hs", "hs": "lo", "hi": "ls", "ls": "hi",
       "ge": "lt", "lt": "ge", "gt": "le", "le": "gt", "mi": "pl", "pl": "mi"}


def use_osc():
    """SC22.1: values of 24 codes per track (stride 24), the dirty mask of 24 bits, flags bits 2 / 3 (oscillator source of MIDI 1 / 2) and 4 / 5 (knob page B), the second knob table."""
    global OSC, STRIDE, O_RT, O_SAVED, O_SIG, DEFAULTS, BIPOLAR_MASK
    OSC, STRIDE, O_RT, O_SAVED, O_SIG = True, 24, 49, 65, 66
    DEFAULTS = tuple(DEFAULTS[:16]) + OSC_DEFAULTS
    BIPOLAR_MASK |= (1 << 16) | (1 << 17) | (1 << 20)         # codes 17 (TUNE), 18 (FINE), 21 (LFOP)


def use_osc2():
    """SC22.2: use_osc() + the oscillator v2 page: pad 27 = the knob page B (the oscillator controls), pad 28 = the oscillator source (line in <-> oscillator); page B: K1 TUNE / FINE, K2 WAVE / SHAPE (PW),
    K3 ENVP (envelope -> pitch) / LFOP (LFO -> pitch), K4 ENVW (envelope -> shape) / LFOW (LFO -> shape); stored codes 17 TUNE, 18 FINE, 19 WAVE, 20 PW, 21 LFOP, 22 ENVP, 23 ENVW, 24 LFOW."""
    global PAD_OSC, PAD_PAGE, KNOB_CODES_B, OSC_DEFAULTS, DX_MASK, DEFAULTS, BIPOLAR_MASK
    use_osc()
    PAD_PAGE, PAD_OSC = 26, 27
    KNOB_CODES_B = (17, 19, 22, 23, 0, 0, 0, 0,  18, 20, 21, 24, 0, 0, 0, 0)
    OSC_DEFAULTS = (0, 0, 2, 64, 0, 0, 0, 0)
    DEFAULTS = tuple(DEFAULTS[:16]) + OSC_DEFAULTS
    DX_MASK = 0xFF
    BIPOLAR_MASK |= (1 << 21) | (1 << 22) | (1 << 23)         # codes 22 (ENVP), 23 (ENVW), 24 (LFOW)


def use_osc3():
    """SC22.3: use_osc2() + the oscillator v3 page (K1..K8): TUNE, SHAPE (PW 0..100, 50 = centre), ENVP (envelope -> pitch), ENVW (envelope -> shape), LFOP (LFO -> pitch), LFOW (LFO -> shape),
    WAVE (the morph position over sine - triangle - saw - square, 0..126), LFOM (LFO -> morph); with Shift: K1 FINE, K8 ENVM (envelope -> morph); stored codes 17..26 (TUNE, FINE, WAVE, PW, LFOP, ENVP, ENVW,
    LFOW, ENVM, LFOM), mailbox codes 22..31."""
    global OSC3, STRIDE, O_RT, O_SAVED, O_SIG, KNOB_CODES_B, OSC_DEFAULTS, DEFAULTS, BIPOLAR_MASK
    use_osc2()
    OSC3, STRIDE, O_RT, O_SAVED, O_SIG = True, 26, 53, 69, 70
    KNOB_CODES_B = (17, 20, 22, 23, 21, 24, 19, 26,  18, 0, 0, 0, 0, 0, 0, 25)
    OSC_DEFAULTS = (0, 0, 84, 50, 0, 0, 0, 0, 0, 0)
    DEFAULTS = tuple(DEFAULTS[:16]) + OSC_DEFAULTS
    BIPOLAR_MASK |= (1 << 24) | (1 << 25)                     # codes 25 (ENVM), 26 (LFOM)


def use_colors():
    """SC22.4: the pad colours of the MIDI Preset view are told apart: patch flip = stock (white / periwinkle), VCF / VCA mode (pad 26) = orange (0x2B bright, 0x2C dim), oscillator edit and oscillator source
    (pads 27 / 28) = the same green (0x17 / 0x18).  Palette codes read as (R, G, B) = bytes 2, 1, 0 of the RGB table (0x13 = 68, 221, 255 is the light blue seen on the unit)."""
    global COLORS, COL_ON, COL_OFF
    COLORS, COL_ON, COL_OFF = True, 0x2B, 0x2C


def use_cced():
    """SC23: the editor of the CC assignments (pad 25 of the MIDI Preset view).  Needs use_osc3 / use_layout (the pad order) and the stock button hook of SC19.1 (c_bentry)."""
    global CCED
    CCED = True


def use_neutral():
    """SC23.3: the default values are the neutral gate state: FILT 0 (open), RES 0, ENVF 0, LFOF 0, ATK 0, DEC 0, SUS 127, REL 0, FXAMT 0, GAIN 0 (the VCA is closed without the envelope), LRATE 40, LFOV 0, FXTYPE 0,
    FXMOD 64, ENVA +63 (the envelope opens the VCA completely, scaled by the velocity), FTYPE 0; oscillator: TUNE 0, FINE 0, WAVE 0 (sine), SHAPE 50 (the centre), every send 0.  The oscillator pad no longer touches GAIN / ENVA.
    The saved state of the older builds is dropped (another signature).  Needs use_osc3."""
    global NEUTRAL, DEFAULTS, OSC_DEFAULTS, SIG_VAL
    assert OSC3
    NEUTRAL = True
    OSC_DEFAULTS = (0, 0, 0, 50, 0, 0, 0, 0, 0, 0)
    DEFAULTS = (0, 0, 0, 0, 0, 0, 127, 0, 0, 0, 40, 0, 0, 64, 63, 0) + OSC_DEFAULTS
    SIG_VAL = 0xAD


def use_clearknob():
    """SC23.3: Clear + a knob of the VCA / VCF / FX and oscillator pages puts that value back to its default (DEFAULTS); the knob is red while Clear is held.  Needs use_osc3."""
    global CLEARK
    CLEARK = True


def use_fxcap():
    """SC23.3: the feedback of the FX returns (SC21.1) breaks the effect if the strip that takes the return sends much of it back (above all the reverb).  With the Setup's reverb -> strip 3 (bit 28 of the
    settings parameter 2) / delay -> strip 4 (bit 29) on, the FX view knobs of MIDI 1 (K3) / MIDI 2 (K4), on both pages, are capped at 63 (half of 127) and a click moves the send by half a step (the odd
    click carries over to the next one: the carry of each strip lives in bits 4-7 of the editor byte +72, which the editor clears when it starts).  Needs fxparams (the slot 4 chain)."""
    global FXCAP
    FXCAP = True


def use_ledclean():
    """SC23.3: the Preset view keeps its LED buffer between frames and the stock redraws only the template pads (1-8); the numbers of the CC editor, drawn on all 32 pads, stayed when the editor ended.  Now,
    the frame after the last number (and at once when the editor is left) pads 9-32 are zeroed (our own pads and the patch flip are written again each frame) and the stock redraw puts pads 1-8 back.
    The 'numbers drawn' flag is bit 2 of the editor byte +72.  Needs use_cced / use_cced2."""
    global LEDCLEAN
    assert CCED and CCED2
    LEDCLEAN = True


def use_ratelimit(ms=2):
    """SC23.5: the DSP reads the mailbox of a voice once per audio block and only the last word written survives; with a 1-bit tag an even number of writes between two reads is not even seen.  The service
    chain can run more often than the blocks (a note = 4 messages, the switch-on = 28), so messages were lost at random: values of the oscillator that never arrived (the 'erratic' sound), gates that never
    opened.  Now c_vsend writes at most once per voice every 2 ms (the 5-bit stamp lives in the bits 3-7 of the tag byte).  Needs nothing on the DSP side."""
    global RATELIMIT, RATE_MS
    assert 1 <= ms <= 16
    RATELIMIT = True; RATE_MS = ms


def use_heartbeat():
    """SC23.5: notes did not always sound (user, 2026-10-06).  Every message of the gate path (ACT, NOTE, VEL, GATE) is repeated in turn about every 32 ms while the track is on (ACT also while off), so a
    message the DSP missed (written twice between two blocks, lost around a mode change...) is recovered; the first velocity is 100 instead of 0 (velocity 0 = a closed VCA).  Pair it with
    vcf21_dsp.use_gatefix (a gate that is high with the envelope idle starts the envelope)."""
    global HEARTBEAT
    HEARTBEAT = True


CLRAUTO = False                                   # SC42.4 (use_clrauto): Clear + knob right = default (lavender), left = the knob's automation cleared (red)
CLR_LAV = 0x07                                    # the stock's colour of a knob put back to its default (persist19.use_blue7)
EDITOR0, EDITOR_SZ, LANE_CLEAR = 0x20039E50, 0x3A0, 0x0803D3B8   # the note tracks' pattern editors (Synth 1, 2, MIDI 1, 2); (editor, lane): the lane to 0xFF


def use_routecol():
    """SC42.7 (the user, 2026-10-16: «cambiar color del pad 29 a amarillo (color del filtro)»): pad 29 of the MIDI Preset view (the chain order) in
    the colours of the VCA / VCF page pad."""
    global COL_ROUTE
    COL_ROUTE = COL_PAGE[0]


def use_clrauto():
    """SC42.4 (the user, 2026-10-16: «clearing a knob successfully must show lavender to stay consistent with the stock interface. Red for automation clear»;
    «automation clear is not currently working on synths» = the own synth of MIDI 1 / 2): with Clear held, a knob of the engine turned right goes back to
    its default (both layers, as before) and shows the stock's colour 0x07; turned left, the automation of its lanes (the plain and the Shift layer's
    codes found in LANE_TAB) is cleared in the pattern the track plays (the stock's own 0x0803D3B8 on the track's pattern editor, as Clear + a knob of
    Synth 1 / 2 does after 40 clicks: the lane's 192 bytes to 0xFF, or only the held step's) and shows red."""
    global CLRAUTO
    assert CLEARK and CLEARBOTH and DUALUI
    CLRAUTO = True


def use_clearboth():
    """SC23.5: with Shift the Clear button has no function (the stock ignores it), so Clear + a knob (no Shift) puts back both the plain and the Shift value of that knob."""
    global CLEARBOTH
    assert CLEARK
    CLEARBOTH = True


def use_typezones():
    """SC23.6: the type knobs (user, 2026-10-06: too sensitive and they cycle).  FX type (Shift + K8, code 13) and filter type (Shift + K5, code 16) are plain 0..127 knobs, clamped at both ends (no
    wrap-around): 7 zones of ~18 clicks; the DSP takes the zone as the type and the position inside the zone as the parameter of the type (FX: FXMOD, the 'morph'; filter: the key follow to the
    cutoff), so Shift + K7 (FXMOD) has no function any more.  WAVE (code 19, page B) is the morph position it already was (pure waves 42 apart).  The LEDs: colour = the selected mode (TCOL_*), brightness =
    the parameter inside the mode (the morph / the follow).  The saved state of SC23.5 is dropped (the stored values of codes 13 / 16 mean something else).  Needs use_neutral (and
    vcf21_dsp.use_typezones)."""
    global TYPEZONE, KNOB_CODES, SIG_VAL
    assert NEUTRAL and SIG_VAL == 0xAD and OSC3 and FXTYPE_N == 7 and FTYPE_N == 7
    TYPEZONE = True
    KNOB_CODES = tuple(KNOB_CODES[:14]) + (0,) + tuple(KNOB_CODES[15:])
    SIG_VAL = 0xAE


def use_dualui():
    """SC24: see DUALUI.  Needs the SC23.5 / SC23.6 options (use_typezones, use_pads2, use_cced, use_edv2, use_clearknob / use_clearboth, use_ratelimit, use_heartbeat).  Knob page B gets MIX (Shift + K2) and the
    BITSYNC zones (Shift + K3), page C the second oscillator; code 14 (the dead FXMOD value) is the note of the second oscillator; the signature changes."""
    global DUALUI, KNOB_CODES_B, BIPOLAR_MASK, DEFAULTS, SIG_VAL
    assert TYPEZONE and PADS2 and CCED and EDV2 and CLEARK and CLEARBOTH and RATELIMIT and HEARTBEAT and SIG_VAL == 0xAE
    DUALUI = True
    KNOB_CODES_B = (17, 20, 22, 23, 21, 24, 19, 26,  18, 31, 32, 0, 0, 0, 0, 25)
    BIPOLAR_MASK |= (1 << 26) | (1 << 27)                                         # codes 27 (TUNE2), 28 (FINE2)
    DEFAULTS = tuple(DEFAULTS[:13]) + (60,) + tuple(DEFAULTS[14:])
    SIG_VAL = 0xAF


def use_tdraw():
    """SC25: the template row (pads 1-8) of the Preset view of a MIDI track is redrawn by the stock routine every frame while the mode of the track is off (and the CC editor is not drawing): after the mode
    had put its page row there, turning it off with pad 27 left the row dark.  Needs use_dualui."""
    global TDRAW
    assert DUALUI
    TDRAW = True


def use_ccio():
    """SC25: the values of the mode go out as MIDI (CC with the numbers of the stock synth where the function is the same, NRPN otherwise: CC_TAB; through the stock template CC helper, so the Setup filters
    and the internal loopback of SC05 apply) and come in (CC / NRPN on the channel of the track, mode on, Setup CC Rx on); 8 of them are automated by the sequencer through the macro lanes 0..7 of the track
    (LANE_TAB: lane 0 = TUNE): a knob turn is recorded through the stock automation gate and the playback (the stock macro sender, called with the lane value while the transport runs) sets the value.
    Needs use_dualui and use_tdraw."""
    global CCIO
    assert DUALUI and TDRAW
    CCIO = True


def use_sdrum():
    """SC26: the step-drummer of the MIDI tracks (inspired by other step-based percussive synthesizers, on top of the stock pattern).  Pad 30 of the Preset view opens / closes its view (Shift + pad 30 disables it);
    pads 1-16 = the steps of the half shown (tap = audition the step with its pitch, Shift + tap = add / remove the note), pads 17-24 = the destination of the pitch row, the 8 knobs = the 8 pairs of steps:
    page pitch (Octave ^) = the value of lane 0 of the two steps of the pair (0..127, 64 = centre), page velocity (Octave v) = the velocity of the notes of the pair (0 = no note); button 1-16 / 17-32 = the half.
    While it is enabled, lane 0 is an OFFSET added to the destination when its value goes to the DSP (+-12 semitones for the two pitch destinations, +-64 steps for the others), read from the pattern at the
    step that plays; every note becomes the root of the scale in octave 2 (one note per step).  State: one nibble per track in the two tail bytes the CC editor used for its view pointer (the editor derives
    the view from its track bit), three bits of the flags byte, one byte of the Master FX block; the signature becomes 0xB0 (the state of SC24 / SC25 is kept).  Needs use_ccio."""
    global SDRUM, SIG_VAL
    assert CCIO and SIG_VAL == 0xAF and O_SD == O_ED + 2
    SDRUM = True
    SIG_VAL = 0xB0


def use_sdrum2():
    """SC27: use_sdrum plus: the step-drummer on Synth 1 / 2 (pad 30 of the source view of SC19.1; pads 17-24 choose which of the 8 macros the pitch row writes: the lane holds the macro position, a pair
    with no value starts from the present position of the macro; the stock engine plays the lane; the audition is an internal note); Octave v / ^ and 1-16 / 17-32 lit in the view; the knob of the pair
    that plays is white; the rows 2 and 3 go dark when the view is closed.  The nibble of a synth = bits 1-3 the macro (bit 0 belongs to the knob pages, see use_pages5)."""
    global SD2
    assert SDRUM and OCTLED
    SD2 = True


def use_rtrec():
    """SC33: real-time recording in the step-drummer (see RTREC).  Needs use_keepnote and use_sdrum2 (the synths)."""
    global RTREC
    assert KEEPNOTE and SD2
    RTREC = True


def use_keepnote():
    """SC31: the step-drummer keeps the notes of the pattern instead of turning them into the tonic (see KEEPNOTE).  Needs use_sdrum."""
    global KEEPNOTE
    assert SDRUM
    KEEPNOTE = True


def use_vadrum():
    """SC29: the VA-drum engine (see VADRUM; the DSP side is vcf21_dsp.use_vadrum).  Needs use_sdrum2 (the signature 0xB0)."""
    global VADRUM
    assert SD2 and SIG_VAL == 0xB0
    VADRUM = True


def use_gran():
    """SC36: the granular engine (see GRAN; the DSP side is vcf21_dsp.GRAN + granular_dsp).  Needs use_vadrum and use_pages5."""
    global GRAN
    assert VADRUM and PAGES5
    GRAN = True


def use_fxseq():
    """SC36: the FX step sequencer (see FXSEQ).  Needs use_gran (and build_sc17.use_glitch for the hook)."""
    global FXSEQ
    assert GRAN and SDRUM
    FXSEQ = True


def use_fxseq2():
    """SC36.1 (the user, 2026-10-09): the FX step sequencer picks the bottom row of Master FX: a pair value 0 = nothing, 1..6 = the slot of pads 26..31 (whatever it holds:
    an effect with its copy of the knobs, the Glitch; pad 31 = the Glitch); its knob moves one value per turn and shows the colour of that slot (build_sc17.use_glitch2)."""
    global FXSEQ2
    assert FXSEQ
    FXSEQ2 = True


def use_grsrc():
    """SC39.1 (the user, 2026-10-11: «el selector de sample (Shift + K8) selecciona entre el sample capturado (izquierda, rojo) y el sample de banco
    seleccionado actualmente por drum 1 (naranja), 2 (amarillo), 3 (purple) o 4 (derecha, teal). Haz el recorrido largo y cambia de color. Al soltar Shift,
    el pad queda fijado hasta que se vuelva a tocar Shift + K8»): Shift + K8 of the granular page (code 25: -1 = the capture, N = the sample N) is a
    travel of 128 clicks over five zones.  Each click writes the sample of its zone (the capture, or the sample Drum 1..4 has now) into code 25, so the
    value is fixed there whatever the drums load later.  The position is one byte per track in the Master FX block's idle LED buffer; it is trusted only
    while its zone still gives the stored value, else the travel starts in the middle of the zone that does (Drum 1's when none).  The LED: the zone's
    colour (dim white when no drum has the stored sample), brighter along the zone while the position is the one of the travel."""
    global GRSRC
    assert GRAN and TYPEZONE and CCIO
    GRSRC = True


def use_resetview():
    """SC39.1 (the user, 2026-10-12: «debería ocurrir al pulsar clear+vista, no clear+toggle»): Clear + pad 27 no longer resets the engine (the pad is a
    toggle again); Clear + a page pad (pads 1-5: a view of the knobs) resets the values of that page, in tools/mpatch.py (c_mprst)."""
    global RESETVIEW
    assert RESETALL
    RESETVIEW = True


def use_resetall():
    """SC38.7 (the user, 2026-10-11: «atajo en sintes propios: restablece con una pulsación todos los estados al inicial»): in the Preset view of MIDI 1 / 2,
    Clear + pad 27 (the engine pad; the stock's Preset view uses only the template pads 1-8, and Clear + 27 only stepped the engine) puts every value of
    that track's engine back to its default (DEFAULTS: codes 1..26, both knob layers of every page; DEFAULTS_V2: the volatile codes 27..34 of OSC 2), marks
    them all to go to the DSP again and saves; the engine itself (pad 27's state) is kept (c_vreset)."""
    global RESETALL
    assert GRAN and DUALUI
    RESETALL = True


def use_stretch():
    """SC38.1 (the user, 2026-10-11: «sample stretch que altera el tempo / duración pero no el pitch»): a third note mode of the granular engine (Shift + K6:
    pitch / slicer / stretch).  In the stretch mode the sample, from the position K2 to its end, lasts N steps of the transport (K3: ST_STEPS) whatever the
    pitch (K1, the notes): the ARM sends the DSP the pitch mode (0), the scan frozen (0), the smallest zone (-64: Z = L / 128, so the frozen playhead is at
    most 1/128 of the sample away) and, every 4 ms, the position s + (126 - s) x p / (6 N), p = the transport's ticks mod 6 N (c_stx in c_vsend; core 1 is not
    changed).  The stored values (K2, K3, K6's zone) are kept: leaving the mode sends them again."""
    global STRETCH
    assert GRAN
    STRETCH = True


def use_dualhide():
    """SC37.4 (the user, 2026-10-10): pad 28 (one / two oscillators) is dark and does nothing unless the engine plays oscillators (the oscillator or
    VA-drum; not off, line in, granular or the FX sequencer): c_vosc."""
    global DUALHIDE
    assert GRAN
    DUALHIDE = True


def use_fxseq3():
    """SC36.2 (the user, 2026-10-09, on the device: SC36.1's knob only went between nothing and pad 31): a turn of a knob sends many events, so one value per event
    raced to the ends.  The pair keeps a position 0..FSQ_MAX (FSQ_U knob units per value) and the value is the nearest multiple; an empty pair starts at 0."""
    global FXSEQ3
    assert FXSEQ2
    FXSEQ3 = True


def use_engfix():
    """SC40.9 (the user, 2026-10-14, on the unit: «la pista [del secuenciador de efectos] se corta con la longitud de Synth 1, en vez de durar lo
    que dura la pista de MIDI 1»): ENGINE was the engine's interface (0x20038ECC = the engine + 0xC), so «the playing store of track t»
    (+ 0x30 + 4 t) was the one of track t + 3 and «the ticks» (+ 0x90) the chain store.  The step-drummer, the FX sequencer and the stretch read
    the pattern, the step and the ticks of another track: unseen while every track had the same length.  Now the engine itself, 0x20038EC0
    (found for SC40.4, tools/stepmod.py)."""
    global ENGINE
    ENGINE = 0x20038EC0


FSQRAND = False                                   # SC41.1 (see use_fxseqrand)


def use_fxseqrand():
    """SC41.1 (the user, 2026-10-14: «en el secuenciador de efectos master, añade una opción random: activa un efecto de la lista al azar»): a seventh
    value of the selector knob (the position 0..7 x FSQ_U, its LED white) = random: c_fsqbits sets bit 6 and a seed in bits 8-15 = the hash of the
    tick at which the step started (the engine's global tick minus the tick inside the step), so the choice holds for the whole step and changes
    from one pass to the next; build_sc17's c_fsqfx picks one of the slots that play something (build_sc17.use_fxseqrand).  Needs use_engfix."""
    global FSQRAND, FSQ_MAX
    assert FXSEQ3 and ENGINE == 0x20038EC0
    FSQRAND = True
    FSQ_MAX = 7 * FSQ_U


def use_sdknobfix():
    """SC41 (the user, 2026-10-14, on the unit, in the step-drummer view: «los knobs no se mueven (no muestran brillo ni cambio en el sonido)»): since
    SC36.2 (use_fxseq3) the pitch knob of a pair lost its value: the test «is this track the FX sequencer?» left its answer in r0, where the pair's
    value had just been loaded, so out of the FX sequencer every knob event wrote 0 + the event's delta (0..5) instead of the value + the delta.
    The value is kept across the test, as SC36.1 (use_fxseq2) did.  The velocity page and the FX sequencer were not affected."""
    global SDKFIX
    assert FXSEQ3
    SDKFIX = True


def use_fxseq4(div=3):
    """SC40.9 (the user, 2026-10-14: «hacer el knob selector más lento»): the selector knob of the FX sequencer moves its position one unit every
    `div` knob events (16 x div events per value); what is left over waits in a signed nibble, bits 4-7 of the editor byte + 72 (the carry bits of
    the half-speed sends of the FX view: both are only what is left of a turn, so sharing them costs at most a couple of events).  The values
    stored in the patterns do not change."""
    global FSQ_DIV
    assert FXSEQ3 and 2 <= div <= 8
    FSQ_DIV = div


def use_pages5():
    """SC27: two more knob pages for the MIDI tracks (pads 4 and 5 of the page row; same values, another layout): KNOB_CODES_D = the 8 values of the lanes, KNOB_CODES_E = the modulation.  The page number
    needs a third bit: bit 0 of the nibble of Synth 1 / 2 (tail byte O_SD + 1) for MIDI 1 / 2.  Needs use_sdrum2."""
    global PAGES5
    assert SD2
    PAGES5 = True


def use_saveled():
    """SC23.5: at the save step of the CC editor the Save button of the top row (panel LED 57, between Duplicate and Projects) blinks with the Save pad.  Needs use_edv2 and use_octleds."""
    global SAVELED
    assert EDV2 and OCTLED
    SAVELED = True


def use_edv2():
    """SC23.4: CC editor v2.  Fields (the first one is the CC number; its value picks the type): CC = [number, start, end]; NRPN with a 7-bit value (number 99, 98 or 6) = [number, MSB, LSB, start, end];
    NRPN with a 14-bit value (number 38) = [number, MSB, LSB, start MSB, start LSB, end MSB, end LSB]; RPN records made in Components keep their fields without the number.  After the last field comes the
    save step: the Save pad (index 25, next to pad 25) blinks and one more Octave v saves; Octave ^ goes back; the Save pad saves at any time; every view button (the own track's included), pad 25 off or a
    template pad discards.  Needs use_cced / use_cced2."""
    global EDV2
    assert CCED and CCED2
    EDV2 = True


def use_octleds():
    """SC23.3: while a number is shown by the CC editor Octave v lights when there is a next field and Octave ^ when there is a previous one (the colour of the field).  Needs use_cced / use_cced2."""
    global OCTLED
    assert CCED
    OCTLED = True


def use_pads2():
    """SC23.2: the toggles of the MIDI Preset view as asked: pad 27 only switches the start of the chain (line in <-> oscillator, lit = oscillator); pads 28 (oscillator parameters = knob page B) and 29
    (VCA / VCF parameters = knob page A) are two views of the mode: pressing one selects it (lit) and switches the mode on, pressing the lit one switches the mode off.  Needs use_colors / use_layout."""
    global PADS2
    assert COLORS and OSC3
    PADS2 = True


def use_cced2():
    """SC23.1: the editor with Octave v / ^ cycling the fields, the button of the track saving and any other view button discarding (needs use_cced)."""
    global CCED2
    CCED2 = True


def use_layout():
    """SC22.4: the toggle pads of the MIDI Preset view, left to right on the bottom row: pad 25 (index 24) free for the CC editor, pad 26 patch flip (SC06's PF_PAD = 25: the builder sets it), pad 27 oscillator
    source (line in <-> oscillator), pad 28 oscillator edit (the knob page B), pad 29 VCF / VCA mode.  Call after use_osc2 / use_osc3."""
    global PAD_FLIP, PAD_VCF, PAD_OSC, PAD_PAGE
    PAD_FLIP, PAD_VCF, PAD_OSC, PAD_PAGE = 25, 28, 26, 27


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def ldrsb_w(rt, rn, imm12): return h(0xF990 | rn) + h(rt << 12 | imm12)          # LDRSB.W Rt,[Rn,#imm12]
def sxtb(rd, rm): return h(0xB240 | rm << 3 | rd)
def strb_reg(rt, rn, rm): return h(0x5400 | rm << 6 | rn << 3 | rt)                 # STRB Rt,[Rn,Rm]


def cced_routines(a, L, t_ed, tail, bc):
    """The CC editor (SC23).  State: tail +71 (bit 7 active, bit 6 a knob is selected, bits 3..5 the field, bits 0..2 the knob), +72 (bit 0 track, bit 1 changed), +73 / +74 the low half of the address of the Preset
    view of the track (the views live in 0x2004xxxx).  The record of knob k of the template shown by the view V:  base + 0x78 * template + 0x28 + 10 k  with base = [[SETOBJ - 4] + 0xC] and the template
    index read through the selection reference [V + 0x14] (as the stock pad handler does).  The change is applied by selecting the same template again through the router [V + 0xC] (what the stock
    pad handler does), which rebuilds the 8 descriptors of the sender, and persisted with TPL_SAVE."""
    def ted(rd, off=0): a.emit(movw, rd, (t_ed + off) & 0xFFFF); a.emit(movt, rd, (t_ed + off) >> 16)
    def setobj4(rd):
        a.emit(movw, rd, (SETOBJ - 4) & 0xFFFF); a.emit(movt, rd, (SETOBJ - 4) >> 16); a.emit(ldr_imm, rd, rd, 0)

    # ---- c_edview() -> r0 = the Preset view of the editor
    a.label("c_edview")
    if SDRUM:                                                                     # the Preset view of MIDI 1 / MIDI 2 (0x20042AE8 / 0x20042B50) from the track bit of the editor
        tail(1); a.emit(ldrb_w, 0, 1, O_ED + 1); a.emit(movs_imm, 2, 1); a.emit(ands_reg, 0, 2); a.emit(movs_imm, 2, 0x68); a.emit(muls, 0, 2)
        a.emit(movw, 1, 0x2AE8); a.emit(movt, 1, 0x2004); a.emit(adds_reg, 0, 0, 1); a.emit(raw, h(0x4770))
    else:
        tail(1); a.emit(ldrb_w, 0, 1, O_ED + 2); a.emit(ldrb_w, 2, 1, O_ED + 3); a.emit(lsls_imm, 2, 2, 8); a.emit(orrs_reg, 0, 2)
        a.emit(movw, 1, 0); a.emit(movt, 1, 0x2004); a.emit(orrs_reg, 0, 1); a.emit(raw, h(0x4770))

    # ---- c_edrec(r0 = view, r1 = knob) -> r0 = the record of the knob, r1 = the template index
    a.label("c_edrec")
    a.emit(push_list, [4, 5], lr=True)
    a.emit(mov_reg, 4, 1); a.emit(mov_reg, 5, 0)
    a.emit(ldr_imm, 2, 5, 0x14); a.emit(ldr_imm, 0, 2, 0); a.emit(ldrb_imm, 1, 2, 4); a.emit(bl, PARAM_GET)
    a.emit(ldrb_imm, 5, 0, 0)
    setobj4(2)
    a.emit(ldr_imm, 0, 2, 0xC)
    a.emit(movs_imm, 1, 0x78); a.emit(muls, 1, 5); a.emit(adds_reg, 0, 0, 1); a.emit(adds_imm8, 0, 0x28)
    a.emit(movs_imm, 1, 10); a.emit(muls, 1, 4); a.emit(adds_reg, 0, 0, 1)
    a.emit(mov_reg, 1, 5)
    a.emit(pop_list, [4, 5], pc=True)

    # ---- c_edapply(r0 = view, r1 = template): the router call of the stock pad handler (a tail call)
    a.label("c_edapply")
    a.emit(mov_reg, 2, 1); a.emit(ldr_imm, 3, 0, 0xC); a.emit(ldrb_imm, 1, 0, 0x10); a.emit(mov_reg, 0, 3)
    a.emit(ldr_imm, 3, 0, 0); a.emit(ldr_imm, 3, 3, 0); a.emit(raw, h(0x4718))                                   # bx r3

    # ---- c_edsave(r0 = view, r1 = template): persist the template, then apply it
    a.label("c_edsave")
    a.emit(push_list, [4, 5], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
    setobj4(2)
    a.emit(ldr_imm, 0, 2, 0x10); a.emit(ldr_imm, 1, 2, 0xC); a.emit(movs_imm, 3, 0x78); a.emit(muls, 3, 5); a.emit(adds_reg, 1, 1, 3)
    a.emit(mov_reg, 2, 5); a.emit(bl, TPL_SAVE)
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(bl, "c_edapply")
    a.emit(pop_list, [4, 5], pc=True)

    # ---- c_edfield(r0 = record, r1 = field) -> r0 = address of the halfword (0: not editable), r1 = shift, r2 = palette code of the field, r3 = number of fields of the record
    a.label("c_edfield")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
    a.emit(ldrb_imm, 2, 4, 0); a.emit(subs_imm8, 2, 1); a.emit(cmp_imm, 2, 4); a.emit(b_cond, "ef_bad", "hi")
    ted(7)
    a.emit(ldrb_reg, 6, 7, 2)                                                                  # class
    a.emit(movs_imm, 2, 6); a.emit(muls, 2, 6)                                                 # 6 * class
    a.emit(adds_reg, 1, 2, 5); a.emit(mov_reg, 3, 7); a.emit(adds_imm8, 3, 8); a.emit(ldrb_reg, 3, 3, 1)      # r3 = role
    a.emit(adds_reg, 1, 2, 3); a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 26); a.emit(ldrb_reg, 1, 0, 1)    # r1 = shift
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 44); a.emit(ldrb_reg, 0, 0, 3); a.emit(adds_reg, 0, 0, 4)    # r0 = record + offset
    a.emit(mov_reg, 2, 7); a.emit(adds_imm8, 2, 50); a.emit(ldrb_reg, 2, 2, 3)                              # r2 = colour
    a.emit(mov_reg, 3, 7); a.emit(adds_imm8, 3, 5); a.emit(ldrb_reg, 3, 3, 6)                               # r3 = number of fields
    a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("ef_bad")
    a.emit(movs_imm, 0, 0)
    a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_eddig(r0 = LED buffer, r1 = glyph (12 bits, 4 rows x 3 columns), r2 = palette code, r3 = base column): draws one glyph, keeps r4-r7
    a.label("c_eddig")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(movs_imm, 4, 0)
    a.label("ed_row")
    a.emit(movs_imm, 5, 0)
    a.label("ed_col")
    a.emit(movs_imm, 6, 3); a.emit(muls, 6, 4); a.emit(movs_imm, 7, 11); a.emit(subs_reg, 7, 7, 6); a.emit(subs_reg, 7, 7, 5)
    a.emit(mov_reg, 6, 1); a.emit(lsrs_reg, 6, 7); a.emit(movs_imm, 7, 1); a.emit(ands_reg, 6, 7); a.emit(b_cond, "ed_skip", "eq")
    a.emit(lsls_imm, 6, 4, 3); a.emit(adds_reg, 6, 6, 5); a.emit(adds_reg, 6, 6, 3); a.emit(lsls_imm, 6, 6, 1); a.emit(strh_reg, 2, 0, 6)
    a.label("ed_skip")
    a.emit(adds_imm8, 5, 1); a.emit(cmp_imm, 5, 3); a.emit(b_cond, "ed_col", "lo")
    a.emit(adds_imm8, 4, 1); a.emit(cmp_imm, 4, 4); a.emit(b_cond, "ed_row", "lo")
    a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_ednum(r0 = LED buffer, r1 = value 0..255, r2 = palette code): the 32 pads show the number (the font and the layout of the stock tempo display: 3 x 4 pixel glyphs,
    #      hundreds in the first 2 columns of the 8, tens in columns 2-4, units in 5-7; the glyphs are the stock table at 0x08050DB8)
    a.label("c_ednum")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2)
    a.emit(movs_imm, 3, 0)
    for i in range(32): a.emit(strh_imm, 3, 4, 2 * i)
    a.emit(movs_imm, 7, 0)
    a.emit(cmp_imm, 5, 100); a.emit(b_cond, "nd_t", "lo")
    a.emit(movs_imm, 7, 1); a.emit(movs_imm, 1, 0)
    a.label("nd_h")
    a.emit(subs_imm8, 5, 100); a.emit(adds_imm8, 1, 1); a.emit(cmp_imm, 5, 100); a.emit(b_cond, "nd_h", "hs")
    a.emit(lsls_imm, 1, 1, 1); a.emit(movw, 2, 0x0DB8); a.emit(movt, 2, 0x0805); a.emit(ldrh_reg, 1, 2, 1)
    a.emit(movw, 2, 0x06DB); a.emit(ands_reg, 1, 2)                                            # hundreds: the first column of the glyph is dropped
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 2, 6); a.emit(movs_imm, 3, 0); a.emit(subs_imm8, 3, 1); a.emit(bl, "c_eddig")
    a.label("nd_t")
    a.emit(movs_imm, 1, 0)
    a.label("nd_t1")
    a.emit(cmp_imm, 5, 10); a.emit(b_cond, "nd_t2", "lo"); a.emit(subs_imm8, 5, 10); a.emit(adds_imm8, 1, 1); a.emit(b, "nd_t1")
    a.label("nd_t2")
    a.emit(cmp_imm, 1, 0); a.emit(b_cond, "nd_td", "ne"); a.emit(cmp_imm, 7, 0); a.emit(b_cond, "nd_u", "eq")
    a.label("nd_td")
    a.emit(lsls_imm, 1, 1, 1); a.emit(movw, 2, 0x0DB8); a.emit(movt, 2, 0x0805); a.emit(ldrh_reg, 1, 2, 1)
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 2, 6); a.emit(movs_imm, 3, 2); a.emit(bl, "c_eddig")
    a.label("nd_u")
    a.emit(lsls_imm, 1, 5, 1); a.emit(movw, 2, 0x0DB8); a.emit(movt, 2, 0x0805); a.emit(ldrh_reg, 1, 2, 1)
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 2, 6); a.emit(movs_imm, 3, 5); a.emit(bl, "c_eddig")
    a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_edact(r0 = track) -> r0 = 1 when the editor is on for that track
    a.label("c_edact")
    tail(2); a.emit(ldrb_w, 1, 2, O_ED); a.emit(movs_imm, 3, 0x80); a.emit(tst_reg, 1, 3); a.emit(b_cond, "ea0", "eq")
    a.emit(ldrb_w, 3, 2, O_ED + 1); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 3, 1); a.emit(cmp_reg, 3, 0); a.emit(b_cond, "ea0", "ne")
    a.emit(movs_imm, 0, 1); a.emit(raw, h(0x4770))
    a.label("ea0")
    a.emit(movs_imm, 0, 0); a.emit(raw, h(0x4770))

    # ---- c_edflush(): persist the template of the editor when something changed
    a.label("c_edflush")
    a.emit(push_list, [4], lr=True)
    tail(2); a.emit(ldrb_w, 3, 2, O_ED + 1); a.emit(movs_imm, 1, 2); a.emit(tst_reg, 3, 1); a.emit(b_cond, "ef_done", "eq")
    a.emit(bics_reg, 3, 1); a.emit(strb_w, 3, 2, O_ED + 1)
    a.emit(bl, "c_edview"); a.emit(mov_reg, 4, 0); a.emit(movs_imm, 1, 0); a.emit(bl, "c_edrec")
    a.emit(mov_reg, 0, 4); a.emit(bl, "c_edsave")
    a.label("ef_done")
    a.emit(pop_list, [4], pc=True)

    if LEDCLEAN:
        # ---- c_edclean(r0 = view): the pads 9-32 of the Preset view buffer to 0, then the stock redraw (template pads 1-8)
        a.label("c_edclean")
        a.emit(push_list, [4], lr=True)
        a.emit(mov_reg, 4, 0); a.emit(ldr_imm, 1, 4, 4); a.emit(ldr_imm, 1, 1, 0); a.emit(movs_imm, 0, 0)
        for i in range(8, 32): a.emit(strh_imm, 0, 1, 2 * i)
        a.emit(mov_reg, 0, 4); a.emit(bl, T_DRAW)
        a.emit(pop_list, [4], pc=True)

    if CCED2:
        # ---- c_edbak(r0 = view): before the first unsaved change, copy the 8 records of the template (80 B) and its index to the scratch of the editor: the (idle) LED buffer of the Master FX block (S_LED, 84 B)
        a.label("c_edbak")
        a.emit(push_list, [4, 5, 6], lr=True)
        a.emit(mov_reg, 4, 0)
        tail(2); a.emit(ldrb_w, 3, 2, O_ED + 1); a.emit(movs_imm, 1, 2); a.emit(tst_reg, 3, 1); a.emit(b_cond, "eb_done", "ne")
        a.emit(bl, L["c_gfst"]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "eb_done", "eq")
        a.emit(adds_imm8, 0, S_SCR); a.emit(mov_reg, 6, 0)
        a.emit(mov_reg, 0, 4); a.emit(movs_imm, 1, 0); a.emit(bl, "c_edrec")
        a.emit(strb_w, 1, 6, 80)
        a.emit(movs_imm, 2, 0)
        a.label("eb_l")
        a.emit(raw, h(0x5C83)); a.emit(raw, h(0x54B3))                                              # ldrb r3,[r0,r2] ; strb r3,[r6,r2]
        a.emit(adds_imm8, 2, 1); a.emit(cmp_imm, 2, 80); a.emit(b_cond, "eb_l", "lo")
        a.label("eb_done")
        a.emit(pop_list, [4, 5, 6], pc=True)

        # ---- c_eddiscard(): throw the unsaved changes away: the saved copy goes back into the template and the router rebuilds the sender
        a.label("c_eddiscard")
        a.emit(push_list, [4, 5, 6, 7], lr=True)
        tail(2); a.emit(ldrb_w, 3, 2, O_ED + 1); a.emit(movs_imm, 1, 2); a.emit(tst_reg, 3, 1); a.emit(b_cond, "dc_done", "eq")
        a.emit(bics_reg, 3, 1); a.emit(strb_w, 3, 2, O_ED + 1)
        a.emit(bl, L["c_gfst"]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "dc_done", "eq")
        a.emit(adds_imm8, 0, S_SCR); a.emit(mov_reg, 6, 0)
        a.emit(bl, "c_edview"); a.emit(mov_reg, 4, 0)
        a.emit(ldrb_w, 5, 6, 80)
        setobj4(2)
        a.emit(ldr_imm, 0, 2, 0xC)
        a.emit(movs_imm, 1, 0x78); a.emit(muls, 1, 5); a.emit(adds_reg, 0, 0, 1); a.emit(adds_imm8, 0, 0x28)
        a.emit(movs_imm, 2, 0)
        a.label("dc_l")
        a.emit(raw, h(0x5CB3)); a.emit(raw, h(0x5483))                                              # ldrb r3,[r6,r2] ; strb r3,[r0,r2]
        a.emit(adds_imm8, 2, 1); a.emit(cmp_imm, 2, 80); a.emit(b_cond, "dc_l", "lo")
        a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(bl, "c_edapply")
        a.label("dc_done")
        a.emit(pop_list, [4, 5, 6, 7], pc=True)

        # ---- c_edoff(): leave the editor (the unsaved changes are discarded)
        a.label("c_edoff")
        a.emit(push_list, [4], lr=True)
        a.emit(bl, "c_eddiscard")
        if LEDCLEAN:
            tail(2); a.emit(ldrb_w, 3, 2, O_ED + 1); a.emit(movs_imm, 1, 4); a.emit(tst_reg, 3, 1); a.emit(b_cond, "co_n", "eq")
            a.emit(bl, "c_edview"); a.emit(bl, "c_edclean")
            a.label("co_n")
        tail(2); a.emit(movs_imm, 1, 0)
        for j in range(2 if SDRUM else 4): a.emit(strb_w, 1, 2, O_ED + j)
        a.emit(pop_list, [4], pc=True)

    else:
        # ---- c_edoff(): leave the editor (persists first)
        a.label("c_edoff")
        a.emit(push_list, [4], lr=True)
        a.emit(bl, "c_edflush")
        tail(2); a.emit(movs_imm, 1, 0)
        for j in range(2 if SDRUM else 4): a.emit(strb_w, 1, 2, O_ED + j)
        a.emit(pop_list, [4], pc=True)

    # ---- c_edon(r0 = view, r1 = track): enter the editor
    a.label("c_edon")
    tail(2); a.emit(movs_imm, 3, 0x80); a.emit(strb_w, 3, 2, O_ED); a.emit(strb_w, 1, 2, O_ED + 1)
    if not SDRUM: a.emit(strb_w, 0, 2, O_ED + 2); a.emit(lsrs_imm, 3, 0, 8); a.emit(strb_w, 3, 2, O_ED + 3)
    a.emit(raw, h(0x4770))

    # ---- c_edknob(r0 = knob 0..7, r1 = delta): first touch of a knob selects it (and shows its field), the next ones change the value
    a.label("c_edknob")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
    tail(2); a.emit(ldrb_w, 6, 2, O_ED)
    a.emit(movs_imm, 3, 0x40); a.emit(tst_reg, 6, 3); a.emit(b_cond, "ek_sel", "eq")
    a.emit(movs_imm, 3, 7); a.emit(mov_reg, 7, 6); a.emit(ands_reg, 7, 3); a.emit(cmp_reg, 7, 4); a.emit(b_cond, "ek_sel", "ne")
    a.emit(bl, "c_edview"); a.emit(mov_reg, 7, 0)
    if CCED2: a.emit(bl, "c_edbak")
    a.emit(mov_reg, 1, 4); a.emit(mov_reg, 0, 7); a.emit(bl, "c_edrec")
    a.emit(push_list, [1])
    a.emit(lsrs_imm, 1, 6, 3); a.emit(movs_imm, 3, 7); a.emit(ands_reg, 1, 3); a.emit(bl, "c_edfield")
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "ek_end", "eq")
    a.emit(mov_reg, 6, 1)
    a.emit(ldrh_imm, 2, 0, 0); a.emit(mov_reg, 3, 2); a.emit(lsrs_reg, 3, 6); a.emit(movs_imm, 1, 0x7F); a.emit(ands_reg, 3, 1)
    a.emit(mov_reg, 1, 3); a.emit(adds_reg, 1, 1, 5)
    a.emit(cmp_imm, 1, 0); a.emit(b_cond, "ek_c1", "ge"); a.emit(movs_imm, 1, 0)
    a.label("ek_c1")
    a.emit(cmp_imm, 1, 127); a.emit(b_cond, "ek_c2", "le"); a.emit(movs_imm, 1, 127)
    a.label("ek_c2")
    a.emit(cmp_reg, 1, 3); a.emit(b_cond, "ek_end", "eq")
    a.emit(movs_imm, 3, 0x7F); a.emit(lsls_reg, 3, 6); a.emit(bics_reg, 2, 3); a.emit(lsls_reg, 1, 6); a.emit(orrs_reg, 2, 1); a.emit(strh_imm, 2, 0, 0)
    tail(2); a.emit(ldrb_w, 3, 2, O_ED + 1); a.emit(movs_imm, 1, 2); a.emit(orrs_reg, 3, 1); a.emit(strb_w, 3, 2, O_ED + 1)
    a.emit(mov_reg, 0, 7); a.emit(pop_list, [1]); a.emit(bl, "c_edapply")
    a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("ek_end")
    a.emit(pop_list, [1])
    a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("ek_sel")
    if not CCED2: a.emit(bl, "c_edflush")
    tail(2); a.emit(movs_imm, 3, 0xC0); a.emit(orrs_reg, 3, 4); a.emit(strb_w, 3, 2, O_ED)
    a.emit(pop_list, [4, 5, 6, 7], pc=True)

    if CCED2:
        # ---- c_edcyc(r0 = direction: 0 forward, 1 back): Octave v / ^: the next / previous field of the selected knob (wraps, saves nothing)
        a.label("c_edcyc")
        a.emit(push_list, [4, 5, 6, 7], lr=True)
        a.emit(mov_reg, 5, 0)
        tail(2); a.emit(ldrb_w, 6, 2, O_ED)
        a.emit(movs_imm, 3, 0x40); a.emit(tst_reg, 6, 3); a.emit(b_cond, "ec_end", "eq")
        a.emit(bl, "c_edview"); a.emit(mov_reg, 7, 0)
        a.emit(mov_reg, 1, 6); a.emit(movs_imm, 3, 7); a.emit(ands_reg, 1, 3); a.emit(mov_reg, 0, 7); a.emit(bl, "c_edrec")
        a.emit(lsrs_imm, 1, 6, 3); a.emit(movs_imm, 3, 7); a.emit(ands_reg, 1, 3); a.emit(mov_reg, 4, 1)
        a.emit(bl, "c_edfield")
        a.emit(cmp_imm, 0, 0); a.emit(b_cond, "ec_end", "eq")
        a.emit(cmp_imm, 5, 0); a.emit(b_cond, "ec_back", "ne")
        a.emit(adds_imm8, 4, 1); a.emit(cmp_reg, 4, 3); a.emit(b_cond, "ec_set", "lo"); a.emit(movs_imm, 4, 0); a.emit(b, "ec_set")
        a.label("ec_back")
        a.emit(cmp_imm, 4, 0); a.emit(b_cond, "ec_wrap", "eq"); a.emit(subs_imm8, 4, 1); a.emit(b, "ec_set")
        a.label("ec_wrap")
        a.emit(mov_reg, 4, 3); a.emit(subs_imm8, 4, 1)
        a.label("ec_set")
        tail(2); a.emit(movs_imm, 3, 0x38); a.emit(bics_reg, 6, 3); a.emit(lsls_imm, 1, 4, 3); a.emit(orrs_reg, 6, 1); a.emit(strb_w, 6, 2, O_ED)
        a.label("ec_end")
        a.emit(pop_list, [4, 5, 6, 7], pc=True)


    else:
        # ---- c_edadv(): the button of the track: next field; after the last one the knob is saved and deselected
        a.label("c_edadv")
        a.emit(push_list, [4, 5, 6, 7], lr=True)
        tail(2); a.emit(ldrb_w, 6, 2, O_ED)
        a.emit(movs_imm, 3, 0x40); a.emit(tst_reg, 6, 3); a.emit(b_cond, "ea_end", "eq")
        a.emit(bl, "c_edview"); a.emit(mov_reg, 7, 0)
        a.emit(mov_reg, 1, 6); a.emit(movs_imm, 3, 7); a.emit(ands_reg, 1, 3); a.emit(mov_reg, 0, 7); a.emit(bl, "c_edrec")
        a.emit(lsrs_imm, 1, 6, 3); a.emit(movs_imm, 3, 7); a.emit(ands_reg, 1, 3); a.emit(mov_reg, 4, 1)
        a.emit(bl, "c_edfield")
        a.emit(cmp_imm, 0, 0); a.emit(b_cond, "ea_desel", "eq")
        a.emit(adds_imm8, 4, 1); a.emit(cmp_reg, 4, 3); a.emit(b_cond, "ea_save", "hs")
        tail(2); a.emit(movs_imm, 3, 0x38); a.emit(bics_reg, 6, 3); a.emit(lsls_imm, 1, 4, 3); a.emit(orrs_reg, 6, 1); a.emit(strb_w, 6, 2, O_ED)
        a.emit(bl, "c_edflush"); a.emit(b, "ea_end")
        a.label("ea_save")
        a.emit(bl, "c_edflush")
        a.label("ea_desel")
        tail(2); a.emit(movs_imm, 3, 0x80); a.emit(strb_w, 3, 2, O_ED)
        a.label("ea_end")
        a.emit(pop_list, [4, 5, 6, 7], pc=True)

    if CCED2:
        # ---- c_vbtn(ctrl = r0, id = r1): in front of the button hook of SC19.1 (c_bentry).  With the editor on: Octave v / ^ (ids 19 / 20) cycle the fields of the selected knob; the button of its track
        #      (while its Preset view is the current one) saves what changed and deselects the knob (with nothing to save it leaves the editor and the stock handler runs); any other view button discards
        a.label("c_vbtn")
        a.emit(raw, pushw([4, 5, 6], lr=True))
        a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
        if SDRUM:                                                                 # the step-drummer view (the editor off): Octave v / ^ = the page, 1-16 / 17-32 = the half
            a.emit(cmp_imm, 5, 19); a.emit(b_cond, "vb_nsd", "lo"); a.emit(cmp_imm, 5, 21); a.emit(b_cond, "vb_nsd", "hi")
            tail(2); a.emit(ldrb_w, 3, 2, O_ED); a.emit(movs_imm, 6, 0x80); a.emit(tst_reg, 3, 6); a.emit(b_cond, "vb_nsd", "ne")
            if SD2:
                a.emit(bl, "c_sdscr"); a.emit(cmp_imm, 0, 0xFF); a.emit(b_cond, "vb_nsd", "eq")
                a.emit(mov_reg, 1, 5); a.emit(bl, "c_sdbtn")
            else:
                a.emit(ldrb_w, 3, 4, S_CUR); a.emit(movs_imm, 6, 0); a.emit(cmp_imm, 3, 18); a.emit(b_cond, "vb_sdt", "eq")
                a.emit(movs_imm, 6, 1); a.emit(cmp_imm, 3, 27); a.emit(b_cond, "vb_nsd", "ne")
                a.label("vb_sdt")
                a.emit(mov_reg, 0, 6); a.emit(bl, "c_sdopen"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vb_nsd", "eq")
                a.emit(mov_reg, 0, 6); a.emit(mov_reg, 1, 5); a.emit(bl, "c_sdbtn")
            a.emit(pop_list, [4, 5, 6], pc=True)
            a.label("vb_nsd")
            if SD2:                                                               # a Synth button: the view closes (on a synth only pad 30 of its source view opens it)
                a.emit(cmp_imm, 5, 1); a.emit(b_cond, "vb_nsy", "hi")
                a.emit(bl, "c_sdaoff"); a.emit(movs_imm, 0, F_SDOPEN); a.emit(movs_imm, 1, 0); a.emit(bl, "c_sdfset")
                a.label("vb_nsy")
        tail(2); a.emit(ldrb_w, 3, 2, O_ED); a.emit(movs_imm, 6, 0x80); a.emit(tst_reg, 3, 6); a.emit(b_cond, "vb_pass", "eq")
        a.emit(cmp_imm, 5, 15); a.emit(b_cond, "vb_view", "ls")
        a.emit(movs_imm, 0, 0); a.emit(cmp_imm, 5, 19); a.emit(b_cond, "vb_oct", "eq")
        a.emit(movs_imm, 0, 1); a.emit(cmp_imm, 5, 20); a.emit(b_cond, "vb_pass", "ne")
        a.label("vb_oct")
        a.emit(bl, "c_edcyc2" if EDV2 else "c_edcyc")
        a.emit(pop_list, [4, 5, 6], pc=True)
        a.label("vb_view")
        if EDV2: a.emit(b, "vb_other")                                            # every view button discards (the own track's too); saving = the Save pad / the save step
        a.emit(mov_reg, 6, 5); a.emit(subs_imm8, 6, ID_MIDI1); a.emit(cmp_imm, 6, 1); a.emit(b_cond, "vb_other", "hi")
        a.emit(ldrb_w, 3, 2, O_ED + 1); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 3, 1); a.emit(cmp_reg, 3, 6); a.emit(b_cond, "vb_other", "ne")
        a.emit(ldrb_w, 3, 4, S_CUR); a.emit(lsls_imm, 1, 5, 3); a.emit(adds_reg, 1, 1, 5); a.emit(cmp_reg, 3, 1); a.emit(b_cond, "vb_other", "ne")
        a.emit(ldrb_w, 3, 2, O_ED); a.emit(movs_imm, 1, 0x40); a.emit(tst_reg, 3, 1); a.emit(b_cond, "vb_sv", "ne")
        a.emit(ldrb_w, 3, 2, O_ED + 1); a.emit(movs_imm, 1, 2); a.emit(tst_reg, 3, 1); a.emit(b_cond, "vb_other", "eq")
        a.label("vb_sv")
        a.emit(bl, "c_edflush")
        tail(2); a.emit(movs_imm, 3, 0x80); a.emit(strb_w, 3, 2, O_ED)
        a.emit(pop_list, [4, 5, 6], pc=True)
        a.label("vb_other")
        a.emit(bl, "c_edoff")
        a.label("vb_pass")
        a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5)
        a.emit(raw, popw([4, 5, 6], lr=True)); a.emit(b_w, L["c_bentry"])
    else:
        # ---- c_vbtn(ctrl = r0, id = r1): in front of the button hook of SC19.1 (c_bentry): with the editor on, the button of its track (while its Preset view is the current one) is the
        #      "next field" button; any other view button leaves the editor
        a.label("c_vbtn")
        a.emit(raw, pushw([4, 5, 6], lr=True))
        a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
        tail(2); a.emit(ldrb_w, 3, 2, O_ED); a.emit(movs_imm, 6, 0x80); a.emit(tst_reg, 3, 6); a.emit(b_cond, "vb_pass", "eq")
        a.emit(cmp_imm, 5, 15); a.emit(b_cond, "vb_pass", "hi")                                   # only the view buttons (ids 0..15) concern the editor
        a.emit(mov_reg, 6, 5); a.emit(subs_imm8, 6, ID_MIDI1); a.emit(cmp_imm, 6, 1); a.emit(b_cond, "vb_other", "hi")
        a.emit(ldrb_w, 3, 2, O_ED + 1); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 3, 1); a.emit(cmp_reg, 3, 6); a.emit(b_cond, "vb_other", "ne")
        a.emit(ldrb_w, 3, 4, S_CUR); a.emit(lsls_imm, 1, 5, 3); a.emit(adds_reg, 1, 1, 5); a.emit(cmp_reg, 3, 1); a.emit(b_cond, "vb_other", "ne")
        a.emit(bl, "c_edadv")
        a.emit(pop_list, [4, 5, 6], pc=True)
        a.label("vb_other")
        a.emit(bl, "c_edoff")
        a.label("vb_pass")
        a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5)
        a.emit(raw, popw([4, 5, 6], lr=True)); a.emit(b_w, L["c_bentry"])


def fxcap_routines(a, L, tail, bc):
    """SC23.3: slot 4 of the FX sub-views (in front of fxparams' c_fxknob): the knobs of the strips that take an FX return are slowed down and capped (see use_fxcap)."""
    a.label("c_fxcap")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2)
    a.emit(cmp_imm, 5, 2); bc("fc_pass", "lo"); a.emit(cmp_imm, 5, 3); bc("fc_pass", "hi")                      # knobs 3 / 4 = MIDI 1 / MIDI 2
    a.emit(bl, L["c_shift"]); a.emit(cmp_imm, 0, 0); bc("fc_pass", "ne")                                         # Shift = the effect parameters (fxparams)
    a.emit(mov_reg, 0, 4); a.emit(bl, L["c_fxsub"]); a.emit(cmp_imm, 0, 0); bc("fc_pass", "eq")                  # not one of the sub-views of the FX view in front
    a.emit(ldr_imm, 0, 4, 0x24); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1); bc("fc_pass", "ne")   # Clear held: stock
    a.emit(bl, L["c_settings"]); a.emit(cmp_imm, 0, 0); bc("fc_pass", "eq")
    a.emit(movs_imm, 1, 2); a.emit(bl, PARAM_GET); a.emit(ldr_imm, 0, 0, 0)
    a.emit(movs_imm, 1, 26); a.emit(adds_reg, 1, 1, 5); a.emit(lsrs_reg, 0, 1); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1); bc("fc_pass", "eq")      # bit 28 (K3) / 29 (K4)
    # the carry of this strip: bits 4-5 (K3) / 6-7 (K4) of the editor byte +72: 0 = none, 1 = +1, 2 = -1
    tail(2); a.emit(ldrb_w, 3, 2, O_ED + 1); a.emit(lsls_imm, 0, 5, 1); a.emit(mov_reg, 1, 3); a.emit(lsrs_reg, 1, 0); a.emit(lsls_imm, 1, 1, 30); a.emit(lsrs_imm, 1, 1, 30)
    a.emit(cmp_imm, 1, 3); a.emit(b_cond, "fc_n3", "ne"); a.emit(movs_imm, 1, 0)
    a.label("fc_n3")
    a.emit(cmp_imm, 1, 2); a.emit(b_cond, "fc_n2", "ne"); a.emit(movs_imm, 1, 0); a.emit(subs_imm8, 1, 1)
    a.label("fc_n2")
    a.emit(adds_reg, 1, 1, 6)                                                                                     # acc = delta + carry
    a.emit(lsrs_imm, 0, 1, 31); a.emit(adds_reg, 0, 1, 0); a.emit(raw, h(0x1040))                                 # r0 = acc / 2 (towards 0): asrs r0, r0, #1
    a.emit(lsls_imm, 6, 0, 1); a.emit(subs_reg, 6, 1, 6); a.emit(mov_reg, 7, 0)                                   # r6 = the new carry (-1, 0, 1), r7 = the half-speed delta
    a.emit(movs_imm, 1, 0); a.emit(cmp_imm, 6, 0); a.emit(b_cond, "fc_c0", "eq"); a.emit(movs_imm, 1, 1); a.emit(cmp_imm, 6, 0); a.emit(b_cond, "fc_c0", "gt"); a.emit(movs_imm, 1, 2)
    a.label("fc_c0")
    tail(2); a.emit(ldrb_w, 3, 2, O_ED + 1); a.emit(lsls_imm, 0, 5, 1); a.emit(movs_imm, 6, 3); a.emit(lsls_reg, 6, 0); a.emit(bics_reg, 3, 6); a.emit(lsls_reg, 1, 0); a.emit(orrs_reg, 3, 1)
    a.emit(strb_w, 3, 2, O_ED + 1)
    # the cap: the new value old + delta may not exceed 63 (a larger old value comes down to 63 with the next turn up)
    a.emit(ldr_imm, 0, 4, 0x14); a.emit(mov_reg, 1, 5); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
    a.emit(movs_imm, 1, 63); a.emit(subs_reg, 1, 1, 0); a.emit(cmp_reg, 7, 1); a.emit(b_cond, "fc_ok", "le"); a.emit(mov_reg, 7, 1)
    a.label("fc_ok")
    a.emit(cmp_imm, 7, 0); a.emit(b_cond, "fc_run", "ne")
    a.emit(pop_list, [4, 5, 6, 7], pc=True)                                                                       # half a click: nothing yet
    a.label("fc_run")
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 7)
    a.emit(raw, popw([4, 5, 6, 7], lr=True)); a.emit(b_w, L["c_fxknob"])
    a.label("fc_pass")
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6)
    a.emit(raw, popw([4, 5, 6, 7], lr=True)); a.emit(b_w, L["c_fxknob"])


def edv2_routines(a, L, t_ft, tail, bc):
    """SC23.4: the routines of the v2 editor (see use_edv2).  c_edfield2(record, field) -> r0 = address of the halfword (0: not editable; 1 at the save step), r1 = shift | 0x100 (the CC number field),
    r2 = colour, r3 = number of fields.  Field number nf is the save step."""
    def ted2(rd):
        a.emit(movw, rd, t_ft & 0xFFFF); a.emit(movt, rd, t_ft >> 16)

    a.label("c_edfield2")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
    a.emit(ldrb_imm, 2, 4, 0); a.emit(subs_imm8, 2, 1); a.emit(cmp_imm, 2, 4); a.emit(b_cond, "f2_bad", "hi")
    ted2(7); a.emit(ldrb_reg, 6, 7, 2)                                                        # r6 = class
    a.emit(adds_imm8, 7, 5); a.emit(ldrb_reg, 3, 7, 6); a.emit(subs_imm8, 7, 5)               # r3 = number of fields
    a.emit(cmp_reg, 5, 3); a.emit(b_cond, "f2_sv", "eq"); a.emit(b_cond, "f2_bad", "hi")
    a.emit(lsls_imm, 2, 6, 5); a.emit(lsls_imm, 1, 5, 2); a.emit(adds_reg, 2, 2, 1); a.emit(adds_reg, 2, 2, 7); a.emit(adds_imm8, 2, 10)       # r2 = the entry
    a.emit(ldrb_imm, 0, 2, 0); a.emit(adds_reg, 0, 0, 4)                                      # record + offset
    a.emit(ldrb_imm, 1, 2, 1); a.emit(ldrb_imm, 6, 2, 3); a.emit(lsls_imm, 6, 6, 8); a.emit(orrs_reg, 1, 6)
    a.emit(ldrb_imm, 2, 2, 2)
    a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("f2_sv")                                                                          # the save step
    a.emit(movs_imm, 0, 1); a.emit(movw, 1, 0x200); a.emit(movs_imm, 2, COL_SAVE[0])
    a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("f2_bad")
    a.emit(movs_imm, 0, 0)
    a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_edcc_get(r0 = record) -> r0 = the CC number shown: CC = its number, NRPN 14 = 38, NRPN 7 = the one chosen (99 / 98 / 6; 6 until one is chosen)
    a.label("c_edcc_get")
    a.emit(push_list, [4], lr=True)
    a.emit(mov_reg, 4, 0)
    a.emit(ldrb_imm, 0, 4, 0); a.emit(cmp_imm, 0, 1); a.emit(b_cond, "cg_n1", "ne")
    a.emit(ldrh_imm, 0, 4, 4); a.emit(movs_imm, 1, 0x7F); a.emit(ands_reg, 0, 1); a.emit(pop_list, [4], pc=True)
    a.label("cg_n1")
    a.emit(cmp_imm, 0, 2); a.emit(b_cond, "cg_n2", "ne"); a.emit(movs_imm, 0, 38); a.emit(pop_list, [4], pc=True)
    a.label("cg_n2")
    tail(2); a.emit(ldrb_w, 1, 2, O_ED + 1); a.emit(movs_imm, 3, 8); a.emit(tst_reg, 1, 3); a.emit(b_cond, "cg_d", "eq")
    a.emit(bl, L["c_gfst"]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "cg_d", "eq")
    a.emit(ldrb_w, 0, 0, S_SCR + 81); a.emit(pop_list, [4], pc=True)
    a.label("cg_d")
    a.emit(movs_imm, 0, 6); a.emit(pop_list, [4], pc=True)

    # ---- c_edcc_set(r0 = record, r1 = delta) -> r0 = 1 when the record changed: the new number picks the type (99 / 98 / 6 NRPN 7-bit, 38 NRPN 14-bit, else CC); a type change resets the parameter and the range
    a.label("c_edcc_set")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
    a.emit(bl, "c_edcc_get"); a.emit(mov_reg, 6, 0)
    a.emit(adds_reg, 7, 6, 5)
    a.emit(cmp_imm, 7, 0); a.emit(b_cond, "cs_p", "ge"); a.emit(movs_imm, 7, 0)
    a.label("cs_p")
    a.emit(cmp_imm, 7, 127); a.emit(b_cond, "cs_c", "le"); a.emit(movs_imm, 7, 127)
    a.label("cs_c")
    a.emit(cmp_reg, 7, 6); a.emit(b_cond, "cs_none", "eq")
    a.emit(movs_imm, 1, 1)
    for n in (99, 98, 6): a.emit(cmp_imm, 7, n); a.emit(b_cond, "cs_k4", "eq")
    a.emit(cmp_imm, 7, 38); a.emit(b_cond, "cs_kk", "ne"); a.emit(movs_imm, 1, 2); a.emit(b, "cs_kk")
    a.label("cs_k4"); a.emit(movs_imm, 1, 4)
    a.label("cs_kk")
    a.emit(ldrb_imm, 0, 4, 0); a.emit(cmp_reg, 0, 1); a.emit(b_cond, "cs_same", "eq")
    a.emit(strb_w, 1, 4, 0)                                                                    # another type: parameter, start and end are reset
    a.emit(movs_imm, 2, 0); a.emit(cmp_imm, 1, 1); a.emit(b_cond, "cs_np", "ne"); a.emit(mov_reg, 2, 7)
    a.label("cs_np")
    a.emit(strh_imm, 2, 4, 4); a.emit(movs_imm, 2, 0); a.emit(strh_imm, 2, 4, 6)
    a.emit(movs_imm, 2, 127); a.emit(cmp_imm, 1, 2); a.emit(b_cond, "cs_e1", "ne"); a.emit(movw, 2, 16383)
    a.label("cs_e1")
    a.emit(strh_imm, 2, 4, 8); a.emit(b, "cs_virt")
    a.label("cs_same")
    a.emit(cmp_imm, 1, 1); a.emit(b_cond, "cs_virt", "ne")
    a.emit(ldrh_imm, 2, 4, 4); a.emit(movs_imm, 3, 0x7F); a.emit(bics_reg, 2, 3); a.emit(orrs_reg, 2, 7); a.emit(strh_imm, 2, 4, 4); a.emit(b, "cs_done")
    a.label("cs_virt")                                                                         # an NRPN type keeps the number chosen in the scratch (the number is not in the record)
    a.emit(cmp_imm, 1, 1); a.emit(b_cond, "cs_done", "eq")
    a.emit(bl, L["c_gfst"]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "cs_done", "eq")
    a.emit(strb_w, 7, 0, S_SCR + 81)
    tail(2); a.emit(ldrb_w, 3, 2, O_ED + 1); a.emit(movs_imm, 1, 8); a.emit(orrs_reg, 3, 1); a.emit(strb_w, 3, 2, O_ED + 1)
    a.label("cs_done")
    a.emit(movs_imm, 0, 1); a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("cs_none")
    a.emit(movs_imm, 0, 0); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_edshow(r0 = view) -> r0 = value, r1 = state (0 nothing to show, 1 a number, 2 the save step), r2 = colour, r3 = field | fields << 4
    a.label("c_edshow")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0)
    tail(2); a.emit(ldrb_w, 6, 2, O_ED); a.emit(movs_imm, 1, 0x40); a.emit(tst_reg, 6, 1); a.emit(b_cond, "sh_no", "eq")
    a.emit(movs_imm, 1, 7); a.emit(ands_reg, 1, 6); a.emit(mov_reg, 0, 4); a.emit(bl, "c_edrec"); a.emit(mov_reg, 7, 0)
    a.emit(lsls_imm, 5, 6, 26); a.emit(lsrs_imm, 5, 5, 29)                                     # r5 = the field
    a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 5); a.emit(bl, "c_edfield2")
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sh_no", "eq")
    a.emit(lsls_imm, 6, 3, 4); a.emit(orrs_reg, 6, 5)                                          # r6 = field | fields << 4
    a.emit(cmp_reg, 5, 3); a.emit(b_cond, "sh_nsv", "ne")
    a.emit(mov_reg, 3, 6); a.emit(movs_imm, 0, 0); a.emit(movs_imm, 1, 2); a.emit(pop_list, [4, 5, 6, 7], pc=True)           # the save step
    a.label("sh_nsv")
    a.emit(lsrs_imm, 3, 1, 8); a.emit(cmp_imm, 3, 0); a.emit(b_cond, "sh_cc", "ne")
    a.emit(ldrh_imm, 3, 0, 0); a.emit(movs_imm, 0, 0xFF); a.emit(ands_reg, 1, 0); a.emit(lsrs_reg, 3, 1); a.emit(movs_imm, 0, 0x7F); a.emit(ands_reg, 3, 0)
    a.emit(mov_reg, 0, 3); a.emit(movs_imm, 1, 1); a.emit(mov_reg, 3, 6); a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("sh_cc")                                                                           # the CC number field
    a.emit(mov_reg, 5, 2); a.emit(mov_reg, 0, 7); a.emit(bl, "c_edcc_get")
    a.emit(movs_imm, 1, 1); a.emit(mov_reg, 2, 5); a.emit(mov_reg, 3, 6); a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("sh_no")
    a.emit(movs_imm, 0, 0); a.emit(movs_imm, 1, 0); a.emit(movs_imm, 2, 0); a.emit(movs_imm, 3, 0); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_edknob2(r0 = knob 0..7, r1 = delta): the first touch selects the knob, the next turns change the field shown (the CC number field changes the type)
    a.label("c_edknob2")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
    tail(2); a.emit(ldrb_w, 6, 2, O_ED)
    a.emit(movs_imm, 3, 0x40); a.emit(tst_reg, 6, 3); bc("k2_sel", "eq")
    a.emit(movs_imm, 3, 7); a.emit(mov_reg, 7, 6); a.emit(ands_reg, 7, 3); a.emit(cmp_reg, 7, 4); bc("k2_sel", "ne")
    a.emit(bl, "c_edview"); a.emit(mov_reg, 7, 0)
    a.emit(bl, "c_edbak")
    a.emit(mov_reg, 1, 4); a.emit(mov_reg, 0, 7); a.emit(bl, "c_edrec")
    a.emit(push_list, [1])
    a.emit(lsls_imm, 1, 6, 26); a.emit(lsrs_imm, 1, 1, 29); a.emit(mov_reg, 6, 1)               # r6 = the field
    a.emit(bl, "c_edfield2")
    a.emit(cmp_imm, 0, 0); bc("k2_end", "eq")
    a.emit(cmp_reg, 6, 3); bc("k2_end", "eq")                                                   # the save step: the knob does nothing
    a.emit(lsrs_imm, 2, 1, 8); a.emit(cmp_imm, 2, 0); bc("k2_cc", "ne")
    a.emit(mov_reg, 6, 1)                                                                      # r6 = shift
    a.emit(ldrh_imm, 2, 0, 0); a.emit(mov_reg, 3, 2); a.emit(lsrs_reg, 3, 6); a.emit(movs_imm, 1, 0x7F); a.emit(ands_reg, 3, 1)
    a.emit(mov_reg, 1, 3); a.emit(adds_reg, 1, 1, 5)
    a.emit(cmp_imm, 1, 0); a.emit(b_cond, "k2_c1", "ge"); a.emit(movs_imm, 1, 0)
    a.label("k2_c1")
    a.emit(cmp_imm, 1, 127); a.emit(b_cond, "k2_c2", "le"); a.emit(movs_imm, 1, 127)
    a.label("k2_c2")
    a.emit(cmp_reg, 1, 3); bc("k2_end", "eq")
    a.emit(movs_imm, 3, 0x7F); a.emit(lsls_reg, 3, 6); a.emit(bics_reg, 2, 3); a.emit(lsls_reg, 1, 6); a.emit(orrs_reg, 2, 1); a.emit(strh_imm, 2, 0, 0)
    a.emit(b, "k2_chg")
    a.label("k2_cc")                                                                           # the CC number: the type follows it
    a.emit(subs_imm8, 0, 4); a.emit(mov_reg, 1, 5); a.emit(bl, "c_edcc_set"); a.emit(cmp_imm, 0, 0); bc("k2_end", "eq")
    a.label("k2_chg")
    tail(2); a.emit(ldrb_w, 3, 2, O_ED + 1); a.emit(movs_imm, 1, 2); a.emit(orrs_reg, 3, 1); a.emit(strb_w, 3, 2, O_ED + 1)
    a.emit(mov_reg, 0, 7); a.emit(pop_list, [1]); a.emit(bl, "c_edapply")
    a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("k2_end")
    a.emit(pop_list, [1])
    a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("k2_sel")                                                                          # select the knob; the number chosen for an NRPN type is forgotten
    tail(2); a.emit(movs_imm, 3, 0xC0); a.emit(orrs_reg, 3, 4); a.emit(strb_w, 3, 2, O_ED)
    a.emit(ldrb_w, 3, 2, O_ED + 1); a.emit(movs_imm, 1, 8); a.emit(bics_reg, 3, 1); a.emit(strb_w, 3, 2, O_ED + 1)
    a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_edcyc2(r0 = direction: 0 = Octave v, 1 = Octave ^): v = next field, after the last one the save step, then save; ^ = the previous one (from the first: the last)
    a.label("c_edcyc2")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 5, 0)
    tail(2); a.emit(ldrb_w, 6, 2, O_ED)
    a.emit(movs_imm, 3, 0x40); a.emit(tst_reg, 6, 3); a.emit(b_cond, "y2_end", "eq")
    a.emit(bl, "c_edview"); a.emit(mov_reg, 7, 0)
    a.emit(movs_imm, 1, 7); a.emit(ands_reg, 1, 6); a.emit(mov_reg, 0, 7); a.emit(bl, "c_edrec")
    a.emit(lsls_imm, 1, 6, 26); a.emit(lsrs_imm, 1, 1, 29); a.emit(mov_reg, 4, 1)
    a.emit(bl, "c_edfield2")
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "y2_end", "eq")
    a.emit(cmp_imm, 5, 0); a.emit(b_cond, "y2_back", "ne")
    a.emit(cmp_reg, 4, 3); a.emit(b_cond, "y2_inc", "ne")
    a.emit(bl, "c_edsavepad"); a.emit(b, "y2_end")                                              # at the save step: save and deselect
    a.label("y2_inc")
    a.emit(adds_imm8, 4, 1); a.emit(b, "y2_set")
    a.label("y2_back")
    a.emit(cmp_imm, 4, 0); a.emit(b_cond, "y2_dec", "ne"); a.emit(mov_reg, 4, 3); a.emit(subs_imm8, 4, 1); a.emit(b, "y2_set")
    a.label("y2_dec")
    a.emit(subs_imm8, 4, 1)
    a.label("y2_set")
    tail(2); a.emit(movs_imm, 3, 0x38); a.emit(bics_reg, 6, 3); a.emit(lsls_imm, 1, 4, 3); a.emit(orrs_reg, 6, 1); a.emit(strb_w, 6, 2, O_ED)
    a.label("y2_end")
    a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_edsavepad(): save what changed and deselect the knob (the Save pad, the save step)
    a.label("c_edsavepad")
    a.emit(push_list, [4], lr=True)
    a.emit(bl, "c_edflush")
    tail(2); a.emit(movs_imm, 3, 0x80); a.emit(strb_w, 3, 2, O_ED)
    a.emit(pop_list, [4], pc=True)



def clrauto_routine(a, base, bc):
    """SC42.4: c_vclrauto, emitted at the end (out of the way of the short branches of the clear routines)."""
    if CLRAUTO:
        # ---- c_vclrauto(r0 = macro handler, r1 = knob 0..7, r2 = track 0 / 1): the lanes of the knob's two codes cleared; the knob marked red
        a.label("c_vclrauto")
        a.emit(push_list, [4, 5, 6, 7], lr=True)
        a.emit(mov_reg, 4, 0); a.emit(mov_reg, 6, 1); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 7, 2)
        a.emit(mov_reg, 0, 7); a.emit(bl, "c_vpage"); a.emit(lsls_imm, 0, 0, 4); a.emit(adds_reg, 5, 5, 0)                   # r5 = page x 16 + knob
        a.emit(movs_imm, 0, 0x2A); a.emit(adds_reg, 1, 4, 6); a.emit(raw, strb_w(0, 1, 0x40))                              # the mark: red
        for layer in (0, 8):
            a.emit(movw, 3, base & 0xFFFF); a.emit(movt, 3, base >> 16); a.emit(adds_reg, 3, 3, 5)
            a.emit(ldrb_imm, 0, 3, layer); a.emit(cmp_imm, 0, 0); bc(f"va_n{layer}", "eq")                                  # r0 = the code
            a.emit(movs_imm, 1, 0)
            for k_, code in enumerate(LANE_TAB):
                a.emit(cmp_imm, 0, code); a.emit(b_cond, f"va_f{layer}_{k_}", "ne"); a.emit(movs_imm, 1, k_ + 1); a.label(f"va_f{layer}_{k_}")
            a.emit(cmp_imm, 1, 0); bc(f"va_n{layer}", "eq")
            a.emit(subs_imm8, 1, 1)                                                                                       # r1 = the lane
            a.emit(movw, 0, EDITOR_SZ); a.emit(mov_reg, 2, 7); a.emit(adds_imm8, 2, 2); a.emit(muls, 0, 2)
            a.emit(movw, 2, EDITOR0 & 0xFFFF); a.emit(movt, 2, EDITOR0 >> 16); a.emit(adds_reg, 0, 0, 2)
            a.emit(bl, LANE_CLEAR)
            a.label(f"va_n{layer}")
        a.emit(pop_list, [4, 5, 6, 7], pc=True)


def clear_routines(a, L, base, t_def, tail, mulstride, bc):
    """SC23.3: Clear + a knob.  The stock macro handler tests the Clear button at [[obj + 0x20] + 0] bit 0 and keeps a counter per knob at obj + 0x40 + k (0x28 = cleared: its LED is red); here the mode puts the
    value of the knob back to its default and marks the counter; the LED routine shows the marked knobs red while Clear is held and drops the marks when it is released."""
    # ---- c_vclr(r0 = macro handler) -> r0 = 1 while Clear is held
    a.label("c_vclr")
    a.emit(push_list, [], lr=True)
    a.emit(ldr_imm, 0, 0, 0x20); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1)
    a.emit(pop_list, [], pc=True)

    # ---- c_vobj(r0 = track 0 / 1) -> r0 = the macro handler of the track (0 if the controller is not there)
    a.label("c_vobj")
    a.emit(movw, 1, CTX_PTR & 0xFFFF); a.emit(movt, 1, CTX_PTR >> 16)
    a.emit(ldr_imm, 1, 1, 0); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "vo_no", "eq")
    a.emit(ldr_imm, 1, 1, 0x40); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "vo_no", "eq")
    a.emit(ldr_imm, 1, 1, 0x2C); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "vo_no", "eq")
    a.emit(lsls_imm, 0, 0, 2); a.emit(adds_reg, 1, 1, 0)
    a.emit(raw, h(0xF8D1) + h(0 << 12 | 0x150))                                   # ldr.w r0,[r1,#0x150 + 4 track]  (track 2 = MIDI 1)
    a.emit(raw, h(0x4770))
    a.label("vo_no")
    a.emit(movs_imm, 0, 0); a.emit(raw, h(0x4770))

    if CLEARBOTH:
        # ---- c_vclr1(r0 = track, r1 = index into the knob table 0..31): the value of that knob position back to its default (nothing if the position has no function or is at the default)
        a.label("c_vclr1")
        a.emit(push_list, [4, 5], lr=True)
        a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
        a.emit(movw, 3, base & 0xFFFF); a.emit(movt, 3, base >> 16); a.emit(ldrb_reg, 0, 3, 5); a.emit(cmp_imm, 0, 0); bc("c1_x", "eq")
        a.emit(mov_reg, 5, 0)
        a.label("c1_code")                                                        # (r4 = track, r5 = code: c_vclrcode of SC39.1 enters here)
        a.emit(movw, 3, t_def & 0xFFFF); a.emit(movt, 3, t_def >> 16); a.emit(ldrb_reg, 0, 3, 5); a.emit(raw, sxtb(0, 0))
        if DUALUI:
            a.emit(mov_reg, 3, 0); a.emit(raw, h(0xB408))                          # push {r3}: the default
            a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(bl, "c_vvaddr"); a.emit(mov_reg, 2, 0)
            a.emit(raw, h(0xBC08))                                                 # pop {r3}
            a.emit(raw, ldrsb_w(1, 2, 0)); a.emit(cmp_reg, 3, 1); bc("c1_x", "eq")
            a.emit(strb_imm, 3, 2, 0)
            if CCIO: a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 3); a.emit(bl, "c_vcc_emit")
            a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(bl, "c_vmark")
            a.emit(cmp_imm, 5, 26); bc("c1_x", "hi")
            a.emit(bl, "c_vsave")
        else:
            tail(2); mulstride(3, 4); a.emit(adds_reg, 2, 2, 3); a.emit(adds_reg, 2, 2, 5)
            a.emit(raw, ldrsb_w(1, 2, 0)); a.emit(cmp_reg, 0, 1); bc("c1_x", "eq")
            a.emit(strb_imm, 0, 2, 0)
            a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(bl, "c_vmark")
            a.emit(bl, "c_vsave")
        a.label("c1_x")
        a.emit(pop_list, [4, 5], pc=True)

        # ---- c_vclear(r0 = macro handler, r1 = knob 0..7, r2 = track): both layers of the knob (plain, Shift) on the page shown go back to their defaults
        a.label("c_vclear")
        a.emit(push_list, [4, 5, 6, 7], lr=True)
        a.emit(mov_reg, 4, 0); a.emit(mov_reg, 6, 1); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 7, 2)
        if DUALUI:
            a.emit(mov_reg, 0, 7); a.emit(bl, "c_vpage"); a.emit(lsls_imm, 0, 0, 4); a.emit(adds_reg, 5, 5, 0)
        else:
            tail(2); a.emit(ldrb_w, 3, 2, O_FLAGS); a.emit(mov_reg, 1, 7); a.emit(adds_imm8, 1, 4); a.emit(lsrs_reg, 3, 1); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 3, 1)
            a.emit(cmp_imm, 3, 0); a.emit(b_cond, "vc_np", "eq"); a.emit(adds_imm8, 5, 16)
            a.label("vc_np")
        a.emit(movs_imm, 0, 0x28); a.emit(adds_reg, 1, 4, 6); a.emit(raw, strb_w(0, 1, 0x40))                         # the mark of the cleared knob
        a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 5); a.emit(bl, "c_vclr1")
        a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 5); a.emit(adds_imm8, 1, 8); a.emit(bl, "c_vclr1")
        a.emit(pop_list, [4, 5, 6, 7], pc=True)
    else:
        # ---- c_vclear(r0 = macro handler, r1 = knob 0..7, r2 = track): the value of the knob (Shift layer, page) goes back to its default
        a.label("c_vclear")
        a.emit(push_list, [4, 5, 6, 7], lr=True)
        a.emit(mov_reg, 4, 0); a.emit(mov_reg, 6, 1); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 7, 2)
        a.emit(bl, L["c_shift"]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vc_ns", "eq"); a.emit(adds_imm8, 5, 8)
        a.label("vc_ns")
        tail(2); a.emit(ldrb_w, 3, 2, O_FLAGS); a.emit(mov_reg, 1, 7); a.emit(adds_imm8, 1, 4); a.emit(lsrs_reg, 3, 1); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 3, 1)
        a.emit(cmp_imm, 3, 0); a.emit(b_cond, "vc_np", "eq"); a.emit(adds_imm8, 5, 16)
        a.label("vc_np")
        a.emit(movw, 3, base & 0xFFFF); a.emit(movt, 3, base >> 16); a.emit(ldrb_reg, 5, 3, 5)                       # r5 = the code of the knob (0 = no function)
        a.emit(cmp_imm, 5, 0); bc("vc_done", "eq")
        a.emit(movs_imm, 0, 0x28); a.emit(adds_reg, 1, 4, 6); a.emit(raw, strb_w(0, 1, 0x40))                         # the mark of the cleared knob
        a.emit(movw, 3, t_def & 0xFFFF); a.emit(movt, 3, t_def >> 16); a.emit(ldrb_reg, 0, 3, 5); a.emit(raw, sxtb(0, 0))
        tail(2); mulstride(3, 7); a.emit(adds_reg, 2, 2, 3); a.emit(adds_reg, 2, 2, 5)
        a.emit(raw, ldrsb_w(1, 2, 0)); a.emit(cmp_reg, 0, 1); bc("vc_done", "eq")
        a.emit(strb_imm, 0, 2, 0)
        a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 5); a.emit(bl, "c_vmark")
        a.emit(bl, "c_vsave")
        a.label("vc_done")
        a.emit(pop_list, [4, 5, 6, 7], pc=True)


    # ---- c_vclrled(r0 = track, r1 = LED buffer of the knobs): Clear held: the marked knobs red; released: the marks are dropped
    a.label("c_vclrled")
    a.emit(push_list, [4, 5], lr=True)
    a.emit(mov_reg, 5, 1); a.emit(bl, "c_vobj"); a.emit(mov_reg, 4, 0); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "cl_x", "eq")
    a.emit(bl, "c_vclr"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "cl_rel", "eq")
    for k in range(8):
        if CLRAUTO:
            a.emit(raw, ldrb_w(1, 4, 0x40 + k)); a.emit(movs_imm, 0, CLR_LAV); a.emit(cmp_imm, 1, 0x28); a.emit(b_cond, f"cl_w{k}", "eq")
            a.emit(movs_imm, 0, CLR_RED); a.emit(cmp_imm, 1, 0x2A); a.emit(b_cond, f"cl_n{k}", "ne")
            a.label(f"cl_w{k}"); a.emit(strh_imm, 0, 5, 2 * k)
        else:
            a.emit(raw, ldrb_w(1, 4, 0x40 + k)); a.emit(cmp_imm, 1, 0x28); a.emit(b_cond, f"cl_n{k}", "ne")
            a.emit(movs_imm, 0, CLR_RED); a.emit(strh_imm, 0, 5, 2 * k)
        a.label(f"cl_n{k}")
    a.emit(b, "cl_x")
    a.label("cl_rel")
    a.emit(movs_imm, 0, 0)
    for k in range(8): a.emit(raw, strb_w(0, 4, 0x40 + k))
    a.label("cl_x")
    a.emit(pop_list, [4, 5], pc=True)


def octled_routines(a, L, tail):
    """SC23.3: c_vledtask(ctrl, out) replaces c_ledtask at the two LED task calls: the SC18.2 task first, then, while the CC editor shows a number, Octave v (panel LED 51) lights if a next field exists and
    Octave ^ (LED 52) if a previous one exists, in the colour of the field."""
    a.label("c_vledtask")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
    a.emit(bl, L["c_ledtask"])
    tail(2); a.emit(ldrb_w, 6, 2, O_ED); a.emit(movs_imm, 1, 0x40); a.emit(tst_reg, 6, 1); a.emit(b_cond, "lo_x", "eq")
    a.emit(ldr_imm, 1, 4, 0x6C); a.emit(ldr_imm, 0, 4, 0x2C); a.emit(cmp_reg, 0, 1); a.emit(b_cond, "lo_x", "ne")                  # the active view is the container of the track views...
    a.emit(ldrb_w, 3, 2, O_ED + 1); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 3, 1); a.emit(adds_imm8, 3, ID_MIDI1); a.emit(lsls_imm, 1, 3, 3); a.emit(adds_reg, 1, 1, 3)
    a.emit(ldrb_w, 0, 4, S_CUR); a.emit(cmp_reg, 0, 1); a.emit(b_cond, "lo_x", "ne")                                              # ...showing the Preset view of the editor's track
    if EDV2:
        a.emit(bl, "c_edview"); a.emit(bl, "c_edshow")                                                                         # r1 = state (0 none, 1 number, 2 save step), r2 = colour, r3 = field | fields << 4
        a.emit(cmp_imm, 1, 0); a.emit(b_cond, "lo_x", "eq")
        a.emit(cmp_imm, 1, 2); a.emit(b_cond, "lo_nv", "ne")
        a.emit(movw, 1, 2 * 51); a.emit(strh_reg, 2, 5, 1); a.emit(movw, 1, 2 * 52); a.emit(strh_reg, 2, 5, 1)                           # the save step: both
        if SAVELED:                                                                                                                       # the Save button blinks like the Save pad
            a.emit(movw, 0, HAL_TICK & 0xFFFF); a.emit(movt, 0, HAL_TICK >> 16); a.emit(ldr_imm, 0, 0, 0); a.emit(lsrs_imm, 0, 0, 8); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1)
            a.emit(movs_imm, 3, COL_SAVE[1]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "lo_sb", "eq"); a.emit(movs_imm, 3, COL_SAVE[0])
            a.label("lo_sb"); a.emit(movw, 1, 2 * 57); a.emit(strh_reg, 3, 5, 1)
        a.emit(b, "lo_x")
        a.label("lo_nv")
        a.emit(movs_imm, 1, 15); a.emit(mov_reg, 6, 3); a.emit(ands_reg, 6, 1); a.emit(lsrs_imm, 3, 3, 4)                      # r6 = field, r3 = fields
    else:
        a.emit(bl, "c_edview"); a.emit(mov_reg, 7, 0)
        a.emit(movs_imm, 1, 7); a.emit(ands_reg, 1, 6); a.emit(mov_reg, 0, 7); a.emit(bl, "c_edrec")
        a.emit(lsrs_imm, 6, 6, 3); a.emit(movs_imm, 1, 7); a.emit(ands_reg, 6, 1); a.emit(mov_reg, 1, 6); a.emit(bl, "c_edfield")        # r0 = halfword (0: not editable), r2 = colour, r3 = fields
        a.emit(cmp_imm, 0, 0); a.emit(b_cond, "lo_x", "eq")
    a.emit(adds_imm8, 6, 1); a.emit(cmp_reg, 6, 3); a.emit(b_cond, "lo_dn", "hs")
    a.emit(movw, 1, 2 * 51); a.emit(strh_reg, 2, 5, 1)
    a.label("lo_dn")
    a.emit(cmp_imm, 6, 1); a.emit(b_cond, "lo_x", "ls")
    a.emit(movw, 1, 2 * 52); a.emit(strh_reg, 2, 5, 1)
    a.label("lo_x")
    if SD2: a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(bl, "c_sdpanel")
    a.emit(pop_list, [4, 5, 6, 7], pc=True)


def ed2_tables(a):
    """Tables of the v2 editor: KC2 (kind 1..5 -> class), NF2 (fields of a class), FT (class, field) -> (record offset, shift, colour, flags); 170 bytes."""
    M, L_, S_, E_ = 0x32, 0x44, 0x2B, 0x13                                    # colours: number / MSB, LSB, start, end
    SL, EL = 0x2D, 0x4D                                                       # LSBs of start / end

    def row(*fields):
        r = b"".join(bytes(f) for f in fields)
        return r + bytes(32 - len(r))
    ccf = (4, 0, M, 1)                                                        # the CC number (flag 1: virtual for the NRPN types)
    cls = [row(ccf, (6, 0, S_, 0), (8, 0, E_, 0)),                                                                              # 0 CC
           row(ccf, (4, 7, M, 0), (4, 0, L_, 0), (6, 7, S_, 0), (6, 0, SL, 0), (8, 7, E_, 0), (8, 0, EL, 0)),                    # 1 NRPN, 14-bit value
           row((4, 7, M, 0), (4, 0, L_, 0), (6, 7, S_, 0), (6, 0, SL, 0), (8, 7, E_, 0), (8, 0, EL, 0)),                          # 2 RPN, 14-bit value
           row(ccf, (4, 7, M, 0), (4, 0, L_, 0), (6, 0, S_, 0), (8, 0, E_, 0)),                                                  # 3 NRPN, 7-bit value
           row((4, 7, M, 0), (4, 0, L_, 0), (6, 0, S_, 0), (8, 0, E_, 0))]                                                       # 4 RPN, 7-bit value
    kc2 = bytes([0, 1, 2, 3, 4])                                              # kind 1 CC, 2 NRPN14, 3 RPN14, 4 NRPN7, 5 RPN7 -> class 0, 1, 2, 3, 4
    nf2 = bytes([3, 7, 6, 5, 4])
    blob = kc2 + nf2 + b"".join(cls)
    assert len(blob) == 170
    for i in range(0, len(blob), 2): a.emit(raw, blob[i:i + 2])


def dualui_routines(a, L, tail, mulstride, bc):
    """SC24 helpers.  c_vvaddr(track, code) = the address of the value byte (the tail for the codes 1..26, the Master FX block for 27..34); c_vpage / c_vsetpage = the knob page of the track (RT_TAG bits 1-2);
    c_vrt7 / c_vflip7 = bit 7 of RT_NOTE (chain order) / RT_VEL (two oscillators); c_vsetn = a note or a velocity with bit 7 kept; c_vnote_on / c_vnote_off = the paraphonic assignment."""
    a.label("c_vvaddr")                                                           # r0 = track, r1 = code -> r0 = address; clobbers r1-r3
    a.emit(cmp_imm, 1, 26); bc("vva_h", "hi")
    tail(2); mulstride(3, 0); a.emit(adds_reg, 2, 2, 3); a.emit(adds_reg, 0, 2, 1); a.emit(raw, h(0x4770))
    a.label("vva_h")
    a.emit(push_list, [4, 5], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
    a.emit(bl, L["c_gfst"]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vva_n", "ne")
    a.emit(movw, 0, (TAIL + O_RT + RT_DX) & 0xFFFF); a.emit(movt, 0, (TAIL + O_RT + RT_DX) >> 16); a.emit(b, "vva_x")      # no Master FX block (the reservation failed): a harmless dummy byte
    a.label("vva_n")
    a.emit(adds_imm8, 0, V2_OFF)
    a.emit(lsls_imm, 1, 4, 3); a.emit(adds_reg, 0, 0, 1); a.emit(adds_reg, 0, 0, 5); a.emit(subs_imm8, 0, 27)
    a.label("vva_x"); a.emit(pop_list, [4, 5], pc=True)

    if PAGES5:
        a.label("c_vpage")                                                        # r0 = track -> r0 = page 0..4 (RT_TAG bits 1-2 + bit 0 of the synth nibble << 2); clobbers r2, r3
        tail(2); a.emit(lsls_imm, 3, 0, 3); a.emit(adds_reg, 3, 2, 3); a.emit(ldrb_w, 3, 3, O_RT + RT_TAG); a.emit(lsls_imm, 3, 3, 29); a.emit(lsrs_imm, 3, 3, 30)
        a.emit(ldrb_w, 2, 2, O_SD + 1); a.emit(lsls_imm, 0, 0, 2); a.emit(lsrs_reg, 2, 0); a.emit(lsls_imm, 2, 2, 31); a.emit(lsrs_imm, 2, 2, 29)
        a.emit(orrs_reg, 3, 2); a.emit(mov_reg, 0, 3); a.emit(raw, h(0x4770))

        a.label("c_vsetpage")                                                     # r0 = track, r1 = page 0..4; clobbers r0-r3
        a.emit(push_list, [4, 5])
        tail(2); a.emit(lsls_imm, 3, 0, 3); a.emit(adds_reg, 3, 2, 3)
        a.emit(ldrb_w, 4, 3, O_RT + RT_TAG); a.emit(movs_imm, 5, 6); a.emit(bics_reg, 4, 5)
        a.emit(lsls_imm, 5, 1, 30); a.emit(lsrs_imm, 5, 5, 29); a.emit(orrs_reg, 4, 5); a.emit(strb_w, 4, 3, O_RT + RT_TAG)       # RT_TAG bits 1-2 = page & 3
        a.emit(ldrb_w, 4, 2, O_SD + 1); a.emit(lsls_imm, 0, 0, 2); a.emit(movs_imm, 3, 1); a.emit(lsls_reg, 3, 0); a.emit(bics_reg, 4, 3)
        a.emit(lsrs_imm, 1, 1, 2); a.emit(lsls_reg, 1, 0); a.emit(orrs_reg, 4, 1); a.emit(strb_w, 4, 2, O_SD + 1)                  # bit 0 of the synth nibble = page >> 2
        a.emit(pop_list, [4, 5]); a.emit(raw, h(0x4770))
    else:
        a.label("c_vpage")                                                        # r0 = track -> r0 = page 0..2; clobbers r2, r3
        tail(2); a.emit(lsls_imm, 3, 0, 3); a.emit(adds_reg, 2, 2, 3)
        a.emit(ldrb_w, 0, 2, O_RT + RT_TAG); a.emit(lsrs_imm, 0, 0, 1); a.emit(movs_imm, 3, 3); a.emit(ands_reg, 0, 3); a.emit(raw, h(0x4770))

        a.label("c_vsetpage")                                                     # r0 = track, r1 = page; clobbers r0-r3
        tail(2); a.emit(lsls_imm, 3, 0, 3); a.emit(adds_reg, 2, 2, 3)
        a.emit(ldrb_w, 0, 2, O_RT + RT_TAG); a.emit(movs_imm, 3, 6); a.emit(bics_reg, 0, 3); a.emit(lsls_imm, 1, 1, 1); a.emit(orrs_reg, 0, 1); a.emit(strb_w, 0, 2, O_RT + RT_TAG); a.emit(raw, h(0x4770))

    a.label("c_vrt7")                                                             # r0 = track, r1 = RT_NOTE / RT_VEL -> r0 = bit 7; clobbers r1-r3
    tail(2); a.emit(lsls_imm, 3, 0, 3); a.emit(adds_reg, 2, 2, 3); a.emit(adds_reg, 2, 2, 1)
    a.emit(ldrb_w, 0, 2, O_RT); a.emit(lsrs_imm, 0, 0, 7); a.emit(raw, h(0x4770))

    a.label("c_vflip7")                                                           # r0 = track, r1 = RT_NOTE / RT_VEL: toggle bit 7, ACT is sent again; r0 = the new bit; clobbers r1-r3
    tail(2); a.emit(lsls_imm, 3, 0, 3); a.emit(adds_reg, 2, 2, 3)
    a.emit(adds_reg, 3, 2, 1); a.emit(ldrb_w, 0, 3, O_RT); a.emit(movs_imm, 1, 0x80); a.emit(eors_reg, 0, 1); a.emit(strb_w, 0, 3, O_RT)
    a.emit(ldrb_w, 1, 2, O_RT + RT_AUX); a.emit(movs_imm, 3, 1); a.emit(orrs_reg, 1, 3); a.emit(strb_w, 1, 2, O_RT + RT_AUX)
    a.emit(lsrs_imm, 0, 0, 7); a.emit(raw, h(0x4770))

    if VADRUM:
        a.label("c_vdbit")                                                        # r0 = bit 0..3 of the engine nibble (t = VA-drum, 2 + t = velocity -> envelopes) -> r0 = 0 / 1; clobbers r1
        tail(1); a.emit(ldrb_w, 1, 1, O_SIG); a.emit(lsrs_reg, 1, 0); a.emit(movs_imm, 0, 1); a.emit(ands_reg, 0, 1); a.emit(raw, h(0x4770))

        a.label("c_vdput")                                                        # r0 = bit 0..3, r1 = 0 / 1: set it; the ACT message of its track is sent again; clobbers r0-r3
        a.emit(push_list, [4])
        tail(2); a.emit(ldrb_w, 3, 2, O_SIG); a.emit(movs_imm, 4, 1); a.emit(lsls_reg, 4, 0); a.emit(bics_reg, 3, 4); a.emit(lsls_reg, 1, 0); a.emit(orrs_reg, 3, 1); a.emit(strb_w, 3, 2, O_SIG)
        a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1); a.emit(lsls_imm, 0, 0, 3); a.emit(adds_reg, 2, 2, 0)
        a.emit(ldrb_w, 3, 2, O_RT + RT_AUX); a.emit(orrs_reg, 3, 1); a.emit(strb_w, 3, 2, O_RT + RT_AUX)
        a.emit(pop_list, [4]); a.emit(raw, h(0x4770))

    a.label("c_vsetn")                                                            # r5 = the RT block, r0 = RT_NOTE / RT_VEL, r2 = the value 0..127 (bit 7 of the byte is kept); clobbers r3
    a.emit(ldrb_reg, 3, 5, 0); a.emit(lsrs_imm, 3, 3, 7); a.emit(lsls_imm, 3, 3, 7); a.emit(orrs_reg, 3, 2); a.emit(raw, strb_reg(3, 5, 0)); a.emit(raw, h(0x4770))

    a.label("c_vnote_on")                                                         # r4 = track, r5 = the RT block, r2 = the note; clobbers r0, r1, r3, r6
    a.emit(push_list, [7], lr=True)
    a.emit(ldrb_imm, 7, 5, RT_CNT); a.emit(movs_imm, 1, 15); a.emit(ands_reg, 1, 7)                    # r1 = the notes held before
    tail(6); mulstride(3, 4); a.emit(adds_reg, 6, 6, 3); a.emit(adds_imm8, 6, 14)                      # r6 = the address of n2 (the value of code 14)
    a.emit(mov_reg, 3, 1); a.emit(adds_imm8, 3, 1); a.emit(cmp_imm, 3, 15); a.emit(b_cond, "no_c", "ls"); a.emit(movs_imm, 3, 15)
    a.label("no_c")
    a.emit(lsrs_imm, 7, 7, 4); a.emit(lsls_imm, 7, 7, 4); a.emit(orrs_reg, 7, 3)                      # r7 = the new RT_CNT byte
    a.emit(cmp_imm, 1, 0); a.emit(b_cond, "no_f", "eq")
    a.emit(cmp_imm, 1, 1); a.emit(b_cond, "no_2", "eq")
    a.emit(movs_imm, 3, 0x80); a.emit(tst_reg, 7, 3); a.emit(b_cond, "no_s2", "ne")
    a.emit(movs_imm, 0, RT_NOTE); a.emit(bl, "c_vsetn"); a.emit(movs_imm, 3, 0x80); a.emit(orrs_reg, 7, 3); a.emit(b, "no_d")   # three or more: the older oscillator takes the note (OSC1 first)
    a.label("no_s2")
    a.emit(strb_imm, 2, 6, 0); a.emit(movs_imm, 3, 0x80); a.emit(bics_reg, 7, 3); a.emit(b, "no_d")
    a.label("no_f")                                                               # the first note: both oscillators (unison)
    a.emit(movs_imm, 0, RT_NOTE); a.emit(bl, "c_vsetn"); a.emit(strb_imm, 2, 6, 0); a.emit(movs_imm, 3, 0x80); a.emit(bics_reg, 7, 3); a.emit(b, "no_d")
    a.label("no_2")                                                               # the second note: OSC2 (OSC1 keeps the first)
    a.emit(strb_imm, 2, 6, 0); a.emit(movs_imm, 3, 0x80); a.emit(bics_reg, 7, 3)
    a.label("no_d")
    a.emit(strb_imm, 7, 5, RT_CNT)
    a.emit(pop_list, [7], pc=True)

    a.label("c_vnote_off")                                                        # r4 = track, r5 = the RT block, r2 = the note
    a.emit(push_list, [7], lr=True)
    a.emit(ldrb_imm, 7, 5, RT_CNT); a.emit(movs_imm, 1, 15); a.emit(ands_reg, 1, 7)
    a.emit(cmp_imm, 1, 0); bc("nf_x", "eq")
    a.emit(subs_imm8, 1, 1)
    a.emit(lsrs_imm, 7, 7, 4); a.emit(lsls_imm, 7, 7, 4); a.emit(orrs_reg, 7, 1); a.emit(strb_imm, 7, 5, RT_CNT)
    a.emit(cmp_imm, 1, 0); a.emit(b_cond, "nf_s", "ne")
    a.emit(ldrb_imm, 0, 5, RT_AUX); a.emit(movs_imm, 1, 8); a.emit(orrs_reg, 0, 1); a.emit(strb_imm, 0, 5, RT_AUX); a.emit(b, "nf_x")                # the last note is up: the gate
    a.label("nf_s")
    tail(6); mulstride(3, 4); a.emit(adds_reg, 6, 6, 3); a.emit(adds_imm8, 6, 14)
    a.emit(ldrb_imm, 0, 5, RT_NOTE); a.emit(movs_imm, 3, 0x7F); a.emit(ands_reg, 0, 3)                  # r0 = n1
    a.emit(ldrb_imm, 3, 6, 0)                                                     # r3 = n2
    a.emit(cmp_reg, 0, 2); a.emit(b_cond, "nf_n2", "ne")
    a.emit(cmp_reg, 3, 2); bc("nf_x", "eq")                                       # both oscillators on this note (other notes held, forgotten): it stays
    a.emit(mov_reg, 2, 3); a.emit(movs_imm, 0, RT_NOTE); a.emit(bl, "c_vsetn")                                 # n1 := n2: unison on the note that is still held
    a.emit(ldrb_imm, 0, 5, RT_AUX); a.emit(movs_imm, 1, 2); a.emit(orrs_reg, 0, 1); a.emit(strb_imm, 0, 5, RT_AUX); a.emit(b, "nf_o")
    a.label("nf_n2")
    a.emit(cmp_reg, 3, 2); a.emit(b_cond, "nf_x", "ne")
    a.emit(strb_imm, 0, 6, 0)                                                     # n2 := n1
    a.emit(ldrb_imm, 0, 5, RT_DHI); a.emit(movs_imm, 1, 0x20); a.emit(orrs_reg, 0, 1); a.emit(strb_imm, 0, 5, RT_DHI)
    a.label("nf_o")
    a.emit(ldrb_imm, 7, 5, RT_CNT); a.emit(movs_imm, 3, 0x80); a.emit(bics_reg, 7, 3); a.emit(strb_imm, 7, 5, RT_CNT)
    a.label("nf_x")
    a.emit(pop_list, [7], pc=True)


def grsrc_routines(a, L, t_gr):
    """SC39.1: the source of the granular engine as a travel over the capture and the samples of the four drums (see use_grsrc)."""
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    RET = h(0x4770)
    # ---- c_grzv(r0 = zone 0..4) -> r0 = its value: -1 the capture, else the sample of Drum zone (the session's parameter type 0x10, index 7 d)
    a.label("c_grzv")
    E(cmp_imm, 0, 0); E(b_cond, "gz_d", "ne"); E(movs_imm, 0, 0); E(raw, h(0x43C0)); E(raw, RET)       # mvns r0, r0
    a.label("gz_d")
    E(push_list, [4], lr=True)
    E(subs_imm8, 0, 1); E(movs_imm, 1, 7); E(muls, 1, 0); E(movs_imm, 0, 0x10); E(bl, GETTER)
    E(movs_imm, 1, 0xFF); E(ands_reg, 0, 1); E(pop_list, [4], pc=True)
    # ---- c_grzo(r0 = a value, signed) -> r0 = the first zone that gives it (0..4), 5 when none
    a.label("c_grzo")
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0); E(movs_imm, 5, 0); E(cmp_imm, 4, 0); E(b_cond, "go_x", "lt")
    E(movs_imm, 5, 1)
    a.label("go_l"); E(mov_reg, 0, 5); E(bl, "c_grzv"); E(cmp_reg, 0, 4); E(b_cond, "go_x", "eq"); E(adds_imm8, 5, 1); E(cmp_imm, 5, 5); E(b_cond, "go_l", "lo")
    a.label("go_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5], pc=True)
    # ---- c_grpos(r0 = track) -> r0 = the address of its position byte (0 without the Master FX block), r1 = the stored value of code 25 (signed),
    #      r2 = the position when its zone gives that value, else 0xFF
    a.label("c_grpos")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(movs_imm, 1, 25); E(bl, "c_vvaddr"); E(raw, ldrsb_w(6, 0, 0))            # r6 = the value
    E(bl, L["c_gfst"]); E(mov_reg, 5, 0); E(cmp_imm, 5, 0); E(b_cond, "gq_n", "eq")
    E(adds_imm8, 5, GRS_POS); E(adds_reg, 5, 5, 4)
    E(ldrb_imm, 7, 5, 0); E(cmp_imm, 7, 127); E(b_cond, "gq_n", "hi")
    E(movs_imm, 0, 5); E(muls, 0, 7); E(lsrs_imm, 0, 0, 7); E(bl, "c_grzv")
    E(raw, h(0xB240))                                                                            # sxtb r0, r0
    E(cmp_reg, 0, 6); E(b_cond, "gq_x", "eq")
    a.label("gq_n"); E(movs_imm, 7, 0xFF)
    a.label("gq_x"); E(mov_reg, 0, 5); E(mov_reg, 1, 6); E(mov_reg, 2, 7); E(pop_list, [4, 5, 6, 7], pc=True)
    # ---- c_grsrc(r0 = track, r1 = delta): one click of the travel; the sample of the new zone into code 25 (sent, out as MIDI, saved)
    a.label("c_grsrc")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 6, 1); E(cmp_imm, 6, 0); E(b_cond, "gs_x", "eq")
    E(bl, "c_grpos"); E(mov_reg, 5, 0); E(mov_reg, 7, 2); E(cmp_imm, 5, 0); E(b_cond, "gs_x", "eq")
    E(raw, h(0xB082))                                                                  # sub sp, #8
    E(raw, h(0x9100))                                                                            # str r1, [sp]: the value now
    E(cmp_imm, 7, 0xFF); E(b_cond, "gs_p", "ne")
    E(ldr_sp, 0, 0); E(bl, "c_grzo"); E(cmp_imm, 0, 5); E(b_cond, "gs_z", "lo"); E(movs_imm, 0, 1)
    a.label("gs_z"); E(lsls_imm, 0, 0, 7); E(adds_imm8, 0, 64); E(movs_imm, 1, 5); E(raw, h(0xFBB0) + h(0xF0F1)); E(mov_reg, 7, 0)   # the middle of that zone: (128 z + 64) / 5
    a.label("gs_p")
    E(cmp_imm, 6, 0); E(b_cond, "gs_up", "gt")
    E(cmp_imm, 7, 0); E(b_cond, "gs_w", "eq"); E(subs_imm8, 7, 1); E(b, "gs_w")
    a.label("gs_up"); E(cmp_imm, 7, 127); E(b_cond, "gs_w", "hs"); E(adds_imm8, 7, 1)
    a.label("gs_w"); E(strb_imm, 7, 5, 0)
    E(movs_imm, 0, 5); E(muls, 0, 7); E(lsrs_imm, 0, 0, 7); E(bl, "c_grzv"); E(raw, h(0xB240)); E(mov_reg, 6, 0)     # r6 = the zone's value
    E(ldr_sp, 1, 0); E(cmp_reg, 6, 1); E(b_cond, "gs_d", "eq")
    E(mov_reg, 0, 4); E(movs_imm, 1, 25); E(bl, "c_vvaddr"); E(strb_imm, 6, 0, 0)
    E(mov_reg, 0, 4); E(movs_imm, 1, 25); E(bl, "c_vmark")
    E(mov_reg, 0, 4); E(movs_imm, 1, 25); E(mov_reg, 2, 6); E(bl, "c_vsync")
    E(bl, "c_vsave")
    a.label("gs_d"); E(raw, h(0xB002))                                                           # add sp, #8
    a.label("gs_x"); E(pop_list, [4, 5, 6, 7], pc=True)
    # ---- c_vclrcode(r0 = track, r1 = code): that value back to its default (the tail of c_vclr1)
    a.label("c_vclrcode")
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(b_w if CLRAUTO else b, "c1_code")                                  # (SC42.4: further away)
    # ---- c_grclear(r0 = track, r1 = knob 0..7): Clear + a knob on the granular page: the two values of the knob (plain, Shift) of GR_TAB back to
    #      their defaults; the source (Shift + K8) = the capture
    a.label("c_grclear")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    imm32(6, t_gr); E(lsls_imm, 0, 5, 2); E(adds_reg, 6, 6, 0)
    E(mov_reg, 0, 4); E(ldrb_imm, 1, 6, 0); E(bl, "c_vclrcode")
    E(mov_reg, 0, 4); E(ldrb_w, 1, 6, 32); E(bl, "c_vclrcode")
    E(cmp_imm, 5, 7); E(b_cond, "gc_x", "ne")
    E(mov_reg, 0, 4); E(movs_imm, 1, 25); E(bl, "c_vvaddr"); E(movs_imm, 1, 0xFF); E(strb_imm, 1, 0, 0)
    E(mov_reg, 0, 4); E(movs_imm, 1, 25); E(bl, "c_vmark")
    E(bl, "c_vsave")
    a.label("gc_x"); E(pop_list, [4, 5, 6], pc=True)
    # ---- c_grsled(r0 = track) -> r0 = the LED halfword of Shift + K8: the zone's colour | (brightness + 2) << 8
    a.label("c_grsled")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(bl, "c_grpos"); E(mov_reg, 6, 1); E(mov_reg, 7, 2)
    E(mov_reg, 0, 6); E(bl, "c_grzo"); E(mov_reg, 4, 0)
    E(cmp_imm, 4, 5); E(b_cond, "gd_z", "lo")
    E(movw, 0, 0x01 | (16 + 2) << 8); E(pop_list, [4, 5, 6, 7], pc=True)                         # no drum has it: dim white
    a.label("gd_z")
    E(movs_imm, 5, 127); E(cmp_imm, 7, 0xFF); E(b_cond, "gd_c", "eq")
    E(movs_imm, 0, 5); E(muls, 0, 7); E(lsrs_imm, 1, 0, 7); E(cmp_reg, 1, 4); E(b_cond, "gd_c", "ne")
    E(movs_imm, 1, 127); E(ands_reg, 0, 1); E(lsrs_imm, 0, 0, 1); E(adds_imm8, 0, 48); E(mov_reg, 5, 0)     # 48..111 along the zone
    a.label("gd_c")
    for z, c in enumerate(GRS_COL):
        E(movs_imm, 0, c)
        if z < 4: E(cmp_imm, 4, z); E(b_cond, "gd_k", "eq")
    a.label("gd_k")
    E(adds_imm8, 5, 2); E(lsls_imm, 5, 5, 8); E(orrs_reg, 0, 5)
    E(pop_list, [4, 5, 6, 7], pc=True)


def gran_routines(a, tail, bc, t_gr, t_st=None):
    """SC36: c_grpg(track) -> 1 when the knobs show the granular page; c_grknob(track, index 0..15, delta); c_grlvl(track, index) -> brightness."""
    def gtab(rd, ridx):                                                           # rd = &GR_TAB[ridx] (ridx kept)
        a.emit(movw, rd, t_gr & 0xFFFF); a.emit(movt, rd, t_gr >> 16); a.emit(lsls_imm, 3, ridx, 2); a.emit(adds_reg, rd, rd, 3)

    if DUALHIDE:
        a.label("c_vosc")                                                         # r0 = track -> r0 = 1 when its oscillators sound (mode on, oscillator source, not granular); clobbers r1-r3
        a.emit(push_list, [4], lr=True); a.emit(mov_reg, 4, 0)
        a.emit(bl, "c_von"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vo_0", "eq")
        a.emit(mov_reg, 0, 4); a.emit(movs_imm, 1, 2); a.emit(bl, "c_vflag"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vo_0", "eq")
        a.emit(mov_reg, 0, 4); a.emit(bl, "c_vdbit"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vo_1", "ne")          # VA-drum
        a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 2); a.emit(bl, "c_vdbit"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vo_0", "ne")   # granular
        a.label("vo_1"); a.emit(movs_imm, 0, 1); a.emit(pop_list, [4], pc=True)
        a.label("vo_0"); a.emit(movs_imm, 0, 0); a.emit(pop_list, [4], pc=True)

    a.label("c_grpg")                                                             # r0 = track -> r0 = 1: page 1 (OSC1), the mode on, the oscillator source, engine bits (0, 1); clobbers r1-r3
    a.emit(push_list, [4], lr=True)
    a.emit(mov_reg, 4, 0)
    a.emit(bl, "c_vpage"); a.emit(cmp_imm, 0, 1); a.emit(b_cond, "gp_0", "ne")
    a.emit(mov_reg, 0, 4); a.emit(bl, "c_von"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "gp_0", "eq")
    a.emit(mov_reg, 0, 4); a.emit(movs_imm, 1, 2); a.emit(bl, "c_vflag"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "gp_0", "eq")
    a.emit(mov_reg, 0, 4); a.emit(bl, "c_vdbit"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "gp_0", "ne")
    a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 2); a.emit(bl, "c_vdbit"); a.emit(pop_list, [4], pc=True)
    a.label("gp_0"); a.emit(movs_imm, 0, 0); a.emit(pop_list, [4], pc=True)

    if FXSEQ:
        a.label("c_fsq")                                                          # r0 = track -> r0 = 1 in the FX sequencer state (mode on, oscillator source off, VA-drum bit); clobbers r1-r3
        a.emit(push_list, [4], lr=True)
        a.emit(mov_reg, 4, 0); a.emit(bl, "c_von"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "fq_0", "eq")
        a.emit(mov_reg, 0, 4); a.emit(movs_imm, 1, 2); a.emit(bl, "c_vflag"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "fq_0", "ne")
        a.emit(mov_reg, 0, 4); a.emit(bl, "c_vdbit"); a.emit(pop_list, [4], pc=True)
        a.label("fq_0"); a.emit(movs_imm, 0, 0); a.emit(pop_list, [4], pc=True)

        a.label("c_fsqbits")                                                      # -> r0 = the effects of the FX sequencer (bits 0-5 top pads, bit 6 the Glitch); from the DSP service tick (no lock taken)
        a.emit(push_list, [4, 5, 6, 7], lr=True)
        a.emit(movs_imm, 7, 0)
        a.emit(movw, 0, PLAY_STORE & 0xFFFF); a.emit(movt, 0, PLAY_STORE >> 16); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
        a.emit(cmp_imm, 0, 0); bc("fb_x", "eq")
        a.emit(movs_imm, 4, 0)
        a.label("fb_t")
        a.emit(mov_reg, 0, 4); a.emit(bl, "c_fsq"); a.emit(cmp_imm, 0, 0); bc("fb_n", "eq")
        a.emit(mov_reg, 0, 4); a.emit(bl, "c_sdnib"); a.emit(movs_imm, 1, 1); a.emit(tst_reg, 0, 1); bc("fb_n", "eq")
        a.emit(mov_reg, 0, 4); a.emit(bl, "c_sdpos"); a.emit(mov_reg, 5, 0)
        a.emit(mov_reg, 0, 4); a.emit(bl, "c_sdpat"); a.emit(mov_reg, 6, 0)
        a.emit(mov_reg, 1, 5); a.emit(bl, "c_sdstp"); a.emit(ldrb_imm, 0, 0, 0); a.emit(cmp_imm, 0, 0); bc("fb_n", "eq")          # no note in the step
        a.emit(mov_reg, 0, 6); a.emit(mov_reg, 1, 5); a.emit(bl, "c_sdlna"); a.emit(ldrb_imm, 0, 0, 0)
        if FXSEQ3:                                                                # position 0..FSQ_MAX -> value 1..6 = the slot of pads 26..31; 0 / more / no value: none
            a.emit(cmp_imm, 0, FSQ_MAX); bc("fb_n", "hi"); a.emit(adds_imm8, 0, FSQ_U // 2); a.emit(lsrs_imm, 0, 0, FSQ_U.bit_length() - 1)
            a.emit(cmp_imm, 0, 0); bc("fb_n", "eq"); a.emit(subs_imm8, 0, 1)
        elif FXSEQ2:                                                              # 1..6 = the slot of pads 26..31; 0 / more / no value: none
            a.emit(cmp_imm, 0, 0); bc("fb_n", "eq"); a.emit(cmp_imm, 0, 6); bc("fb_n", "hi"); a.emit(subs_imm8, 0, 1)
        else:
            a.emit(cmp_imm, 0, 0); bc("fb_n", "eq"); a.emit(cmp_imm, 0, 127); bc("fb_n", "hi")                              # 0 / no value: none
            a.emit(subs_imm8, 0, 1); a.emit(movs_imm, 1, 7); a.emit(muls, 0, 1); a.emit(lsrs_imm, 0, 0, 7)                   # zone 0..6
        a.emit(movs_imm, 1, 1); a.emit(lsls_reg, 1, 0); a.emit(orrs_reg, 7, 1)
        if FSQRAND:                                                               # value 7 = random: a seed for the whole step (bits 8-15)
            a.emit(cmp_imm, 0, 6); bc("fb_n", "ne")
            a.emit(mov_reg, 0, 4); a.emit(movs_imm, 1, 2); a.emit(bl, "c_sdeng"); a.emit(ldr_imm, 5, 0, 0)          # r5 = the tick inside the step
            a.emit(movw, 0, (ENGINE + 0x90) & 0xFFFF); a.emit(movt, 0, (ENGINE + 0x90) >> 16); a.emit(ldr_imm, 0, 0, 0)
            a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldr_imm, 0, 0, 0); a.emit(subs_reg, 0, 0, 5)       # the tick the step started at
            a.emit(movw, 1, 0x79B1); a.emit(movt, 1, 0x9E37); a.emit(muls, 0, 1); a.emit(lsrs_imm, 0, 0, 24); a.emit(lsls_imm, 0, 0, 8); a.emit(orrs_reg, 7, 0)
        a.label("fb_n")
        a.emit(adds_imm8, 4, 1); a.emit(cmp_imm, 4, 2); bc("fb_t", "lo")
        a.label("fb_x"); a.emit(mov_reg, 0, 7); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    a.label("c_grknob")                                                           # r0 = track, r1 = index, r2 = delta: the value of the code of GR_TAB[index], clamped to its range
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 7, 0); a.emit(mov_reg, 6, 2)
    gtab(4, 1)                                                                    # r4 = the entry, r5 = its code
    a.emit(ldrb_imm, 5, 4, 0)
    a.emit(ldrb_imm, 3, 4, 3); a.emit(movs_imm, 2, 1); a.emit(tst_reg, 3, 2); a.emit(b_cond, "gk_d", "eq")          # one step per turn: delta = sign(delta)
    a.emit(cmp_imm, 6, 0); a.emit(b_cond, "gk_d", "eq"); a.emit(b_cond, "gk_p", "gt"); a.emit(movs_imm, 6, 0); a.emit(subs_imm8, 6, 1); a.emit(b, "gk_d")
    a.label("gk_p"); a.emit(movs_imm, 6, 1)
    a.label("gk_d")
    a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 5); a.emit(bl, "c_vvaddr"); a.emit(raw, ldrsb_w(1, 0, 0))          # r0 = the address, r1 = old
    a.emit(adds_reg, 2, 1, 6)                                                     # r2 = new
    a.emit(raw, ldrsb_w(3, 4, 1)); a.emit(cmp_reg, 2, 3); a.emit(b_cond, "gk_1", "ge"); a.emit(mov_reg, 2, 3)
    a.label("gk_1"); a.emit(raw, ldrsb_w(3, 4, 2)); a.emit(cmp_reg, 2, 3); a.emit(b_cond, "gk_2", "le"); a.emit(mov_reg, 2, 3)
    a.label("gk_2"); a.emit(cmp_reg, 2, 1); a.emit(b_cond, "gk_x", "eq")
    a.emit(strb_imm, 2, 0, 0); a.emit(mov_reg, 6, 2)
    a.emit(cmp_imm, 5, 26); a.emit(b_cond, "gk_s", "ls")                          # a volatile value: the sweep goes there next (its cursor = code - 27)
    tail(2); a.emit(lsls_imm, 3, 7, 3); a.emit(adds_reg, 2, 2, 3); a.emit(ldrb_w, 0, 2, O_RT + RT_CNT); a.emit(movs_imm, 1, 0x70); a.emit(bics_reg, 0, 1)
    a.emit(mov_reg, 1, 5); a.emit(subs_imm8, 1, 27); a.emit(lsls_imm, 1, 1, 4); a.emit(orrs_reg, 0, 1); a.emit(strb_w, 0, 2, O_RT + RT_CNT)
    a.label("gk_s")
    a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 5); a.emit(bl, "c_vmark")
    if CCIO: a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6); a.emit(bl, "c_vsync")
    a.emit(cmp_imm, 5, 26); a.emit(b_cond, "gk_x", "hi")                          # the volatile codes (27..34) are not saved
    a.emit(bl, "c_vsave")
    a.label("gk_x"); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    a.label("c_grlvl")                                                            # r0 = track, r1 = index -> r0 = the brightness of the knob LED; clobbers r1-r3
    if STRETCH:
        a.emit(push_list, [4, 5, 6], lr=True)
        a.emit(mov_reg, 5, 0)
        gtab(4, 1)
        a.emit(ldrb_imm, 1, 4, 0); a.emit(bl, "c_vvaddr"); a.emit(raw, ldrsb_w(6, 0, 0))
        a.emit(ldrb_imm, 1, 4, 3); a.emit(lsrs_imm, 1, 1, 1)
        a.emit(ldrb_imm, 0, 4, 0); a.emit(cmp_imm, 0, 21); a.emit(b_cond, "gl_k", "ne")                        # K3 in the stretch mode: its length (the value + 64)
        a.emit(mov_reg, 0, 5); a.emit(bl, "c_strm"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "gl_kr", "eq"); a.emit(movs_imm, 1, 2); a.emit(b, "gl_k")
        a.label("gl_kr"); a.emit(ldrb_imm, 1, 4, 3); a.emit(lsrs_imm, 1, 1, 1)
        a.label("gl_k")
        a.emit(mov_reg, 0, 6)
        a.emit(cmp_imm, 1, 5); a.emit(b_cond, "gl_3", "ne")                        # three levels: 0 dim, 1 half, 2 full
        a.emit(movs_imm, 1, 16); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "gl_3x", "le"); a.emit(movs_imm, 1, 64); a.emit(cmp_imm, 0, 1); a.emit(b_cond, "gl_3x", "eq"); a.emit(movs_imm, 1, 127)
        a.label("gl_3x"); a.emit(mov_reg, 0, 1); a.emit(b, "gl_x")
        a.label("gl_3")
    else:
        a.emit(push_list, [4], lr=True)
        gtab(4, 1)
        a.emit(ldrb_imm, 1, 4, 0); a.emit(bl, "c_vvaddr"); a.emit(raw, ldrsb_w(0, 0, 0))
        a.emit(ldrb_imm, 1, 4, 3); a.emit(lsrs_imm, 1, 1, 1)
    a.emit(cmp_imm, 1, 1); a.emit(b_cond, "gl_v", "eq"); a.emit(cmp_imm, 1, 2); a.emit(b_cond, "gl_o", "eq")
    a.emit(cmp_imm, 1, 3); a.emit(b_cond, "gl_m", "eq"); a.emit(cmp_imm, 1, 4); a.emit(b_cond, "gl_b", "eq")
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "gl_p", "ge"); a.emit(raw, h(0x43C0))                                  # bipolar: |v| x 2 (mvns r0, r0: -v - 1)
    a.label("gl_p"); a.emit(lsls_imm, 0, 0, 1); a.emit(cmp_imm, 0, 126); a.emit(b_cond, "gl_x", "ls"); a.emit(movs_imm, 0, 126); a.emit(b, "gl_x")
    a.label("gl_v"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "gl_x", "ge"); a.emit(movs_imm, 0, 0); a.emit(b, "gl_x")
    a.label("gl_o"); a.emit(adds_imm8, 0, 64); a.emit(b, "gl_x")
    a.label("gl_m"); a.emit(raw, ldrsb_w(1, 4, 1)); a.emit(subs_reg, 0, 0, 1); a.emit(lsls_imm, 0, 0, 1); a.emit(cmp_imm, 0, 127); a.emit(b_cond, "gl_x", "ls"); a.emit(movs_imm, 0, 127); a.emit(b, "gl_x")
    a.label("gl_b"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "gl_bt", "gt"); a.emit(movs_imm, 0, 16); a.emit(b, "gl_x")
    a.label("gl_bt"); a.emit(movs_imm, 0, 127)
    a.label("gl_x"); a.emit(pop_list, [4, 5, 6] if STRETCH else [4], pc=True)

    if STRETCH:
        a.label("c_strm")                                                         # r0 = track -> r0 = 1 in the stretch mode (the granular engine, note mode 2); clobbers r1-r3
        a.emit(push_list, [4], lr=True); a.emit(mov_reg, 4, 0)
        a.emit(bl, "c_von"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sm_0", "eq")
        a.emit(mov_reg, 0, 4); a.emit(movs_imm, 1, 2); a.emit(bl, "c_vflag"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sm_0", "eq")
        a.emit(mov_reg, 0, 4); a.emit(bl, "c_vdbit"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sm_0", "ne")
        a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 2); a.emit(bl, "c_vdbit"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sm_0", "eq")
        a.emit(mov_reg, 0, 4); a.emit(movs_imm, 1, 26); a.emit(bl, "c_vvaddr"); a.emit(raw, ldrsb_w(0, 0, 0)); a.emit(cmp_imm, 0, 2); a.emit(b_cond, "sm_0", "ne")
        a.emit(movs_imm, 0, 1); a.emit(pop_list, [4], pc=True)
        a.label("sm_0"); a.emit(movs_imm, 0, 0); a.emit(pop_list, [4], pc=True)

        # c_stx (in c_vsend): r0 = track, r1 = the value of code j + 1, r2 = j, r7 = the track's RT bytes -> r1 = the value to send; r2, r4-r7 kept
        a.label("c_stx")
        a.emit(push_list, [2, 4, 5, 6], lr=True)
        a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2)
        a.emit(cmp_imm, 6, 25); a.emit(b_cond, "sx_26", "eq")
        a.emit(cmp_imm, 6, 18); a.emit(b_cond, "sx_go", "eq")
        a.emit(cmp_imm, 6, 20); a.emit(b_cond, "sx_go", "eq")
        a.emit(cmp_imm, 6, 22); a.emit(b_cond, "sx_k", "ne")
        a.label("sx_go")
        a.emit(mov_reg, 0, 4); a.emit(bl, "c_strm"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sx_k", "eq")
        a.emit(cmp_imm, 6, 20); a.emit(b_cond, "sx_z", "ne"); a.emit(movs_imm, 5, 0); a.emit(b, "sx_k")             # the scan: frozen
        a.label("sx_z")
        a.emit(cmp_imm, 6, 22); a.emit(b_cond, "sx_p", "ne"); a.emit(movs_imm, 5, 0); a.emit(subs_imm8, 5, 64); a.emit(b, "sx_k")   # the zone: the smallest
        a.label("sx_p")                                                           # the position: s + (126 - s) x p / period, s = the stored position (0..126)
        a.emit(cmp_imm, 5, 0); a.emit(b_cond, "sx_p1", "ge"); a.emit(movs_imm, 5, 0)
        a.label("sx_p1"); a.emit(cmp_imm, 5, 126); a.emit(b_cond, "sx_p2", "le"); a.emit(movs_imm, 5, 126)
        a.label("sx_p2")
        a.emit(mov_reg, 0, 4); a.emit(movs_imm, 1, 21); a.emit(bl, "c_vvaddr"); a.emit(raw, ldrsb_w(0, 0, 0))     # K3: the length
        a.emit(adds_imm8, 0, 64); a.emit(movs_imm, 1, len(ST_STEPS)); a.emit(muls, 0, 1); a.emit(lsrs_imm, 0, 0, 7)
        a.emit(movw, 1, t_st & 0xFFFF); a.emit(movt, 1, t_st >> 16); a.emit(ldrb_reg, 6, 1, 0)
        a.emit(movs_imm, 1, ST_TICKS); a.emit(muls, 6, 1)                        # r6 = the period in ticks
        a.emit(movw, 0, ENGINE & 0xFFFF); a.emit(movt, 0, ENGINE >> 16); a.emit(raw, ldr_w(0, 0, 0x90))
        a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldr_imm, 0, 0, 0)  # the transport's ticks
        a.emit(raw, udiv_w(1, 0, 6)); a.emit(raw, mls_w(0, 1, 6, 0))            # p = ticks mod period
        a.emit(movs_imm, 1, 126); a.emit(subs_reg, 1, 1, 5); a.emit(muls, 1, 0); a.emit(raw, udiv_w(1, 1, 6)); a.emit(adds_reg, 5, 5, 1)
        a.emit(b, "sx_k")
        a.label("sx_26")                                                          # the note mode: codes 19 / 21 / 23 go again (in or out of the stretch); the stretch = the pitch mode
        a.emit(ldrb_imm, 0, 7, RT_DX); a.emit(movs_imm, 3, 0x54); a.emit(orrs_reg, 0, 3); a.emit(strb_imm, 0, 7, RT_DX)
        a.emit(cmp_imm, 5, 2); a.emit(b_cond, "sx_k", "ne")
        a.emit(mov_reg, 0, 4); a.emit(bl, "c_strm"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sx_k", "eq"); a.emit(movs_imm, 5, 0)
        a.label("sx_k"); a.emit(mov_reg, 1, 5); a.emit(pop_list, [2, 4, 5, 6], pc=True)


def asrs_imm(rd, rm, imm): return h(0x1000 | imm << 6 | rm << 3 | rd)                   # ASRS Rd,Rm,#imm
def ldr_w(rt, rn, imm12): return h(0xF8D0 | rn) + h(rt << 12 | imm12)                # LDR.W Rt,[Rn,#imm12]
def udiv_w(rd, rn, rm): return h(0xFBB0 | rn) + h(0xF0F0 | rd << 8 | rm)                   # UDIV Rd,Rn,Rm
def mls_w(rd, rn, rm, ra): return h(0xFB00 | rn) + h(ra << 12 | 0x10 | rd << 8 | rm)      # MLS Rd,Rn,Rm,Ra (Ra - Rn x Rm)


def sd_routines(a, L, tail, bc, t_sd):
    """SC26 (SDRUM): the step-drummer.  t_sd = the tables: 8 destination codes, then 8 destination colours."""
    from thumb import add_sp_imm
    E = a.emit
    RET = h(0x4770)

    def clamp(r, lo, hi, tmp, tag):                                              # r = max(lo, min(hi, r)) (signed); lo may be negative
        E(cmp_imm, r, hi); E(b_cond, tag + "h", "le"); E(movs_imm, r, hi)
        a.label(tag + "h")
        if lo >= 0:
            E(cmp_imm, r, lo); E(b_cond, tag + "l", "ge"); E(movs_imm, r, lo)
        else:
            E(movs_imm, tmp, 0); E(subs_imm8, tmp, -lo); E(cmp_reg, r, tmp); E(b_cond, tag + "l", "ge"); E(mov_reg, r, tmp)
        a.label(tag + "l")

    a.label("c_sdflag")                                                           # r0 = mask -> r0 = flags & mask; clobbers r1
    tail(1); E(ldrb_w, 1, 1, O_FLAGS); E(ands_reg, 0, 1); E(raw, RET)

    a.label("c_sdfset")                                                           # r0 = mask, r1 = 0 clear / 1 set / 2 toggle; clobbers r0-r3
    tail(2); E(ldrb_w, 3, 2, O_FLAGS)
    E(cmp_imm, 1, 1); E(b_cond, "fs_c", "lo"); E(b_cond, "fs_t", "hi"); E(orrs_reg, 3, 0); E(b, "fs_w")
    a.label("fs_c"); E(bics_reg, 3, 0); E(b, "fs_w")
    a.label("fs_t"); E(eors_reg, 3, 0)
    a.label("fs_w"); E(strb_w, 3, 2, O_FLAGS); E(raw, RET)

    if not SD2:
        a.label("c_sdnib")                                                            # r0 = track -> r0 = its nibble (bit 0 enabled, bits 1-3 destination); clobbers r1
        tail(1); E(ldrb_w, 1, 1, O_SD); E(lsls_imm, 0, 0, 2); E(lsrs_reg, 1, 0); E(movs_imm, 0, 15); E(ands_reg, 0, 1); E(raw, RET)
    else:
        a.label("c_sdnib")                                                            # r0 = track 0..3 -> r0 = its nibble; clobbers r1, r2
        tail(1); E(lsrs_imm, 2, 0, 1); E(adds_reg, 1, 1, 2); E(ldrb_w, 1, 1, O_SD)
        E(movs_imm, 2, 1); E(ands_reg, 0, 2); E(lsls_imm, 0, 0, 2); E(lsrs_reg, 1, 0); E(movs_imm, 0, 15); E(ands_reg, 0, 1); E(raw, RET)


    if not SD2:
        a.label("c_sdsetnib")                                                         # r0 = track, r1 = nibble; clobbers r0-r3
        E(push_list, [4])
        tail(2); E(ldrb_w, 3, 2, O_SD); E(lsls_imm, 0, 0, 2); E(movs_imm, 4, 15); E(lsls_reg, 4, 0); E(bics_reg, 3, 4); E(lsls_reg, 1, 0); E(orrs_reg, 3, 1); E(strb_w, 3, 2, O_SD)
        E(pop_list, [4]); E(raw, RET)
    else:
        a.label("c_sdsetnib")                                                         # r0 = track 0..3, r1 = nibble; clobbers r0-r3
        E(push_list, [4])
        tail(2); E(lsrs_imm, 3, 0, 1); E(adds_reg, 2, 2, 3); E(ldrb_w, 3, 2, O_SD)
        E(movs_imm, 4, 1); E(ands_reg, 0, 4); E(lsls_imm, 0, 0, 2); E(movs_imm, 4, 15); E(lsls_reg, 4, 0); E(bics_reg, 3, 4); E(lsls_reg, 1, 0); E(orrs_reg, 3, 1); E(strb_w, 3, 2, O_SD)
        E(pop_list, [4]); E(raw, RET)


    if not SD2:
        a.label("c_sden")                                                             # r0 = track -> r0 = 1 when the step-drummer of the track is enabled and its mode is on; clobbers r1-r3
        E(push_list, [4], lr=True)
        E(mov_reg, 4, 0); E(bl, "c_sdnib"); E(movs_imm, 1, 1); E(ands_reg, 0, 1); E(cmp_imm, 0, 0); E(b_cond, "se_x", "eq")
        E(mov_reg, 0, 4); E(bl, "c_von")
        a.label("se_x"); E(pop_list, [4], pc=True)
    else:
        a.label("c_sden")                                                             # r0 = track -> r0 = 1: a MIDI track with the step-drummer enabled and its mode on; a synth always (its lanes are stock)
        E(cmp_imm, 0, 2); E(b_cond, "se_m", "lo"); E(movs_imm, 0, 1); E(raw, RET)
        a.label("se_m")
        E(push_list, [4], lr=True)
        E(mov_reg, 4, 0); E(bl, "c_sdnib"); E(movs_imm, 1, 1); E(ands_reg, 0, 1); E(cmp_imm, 0, 0); E(b_cond, "se_x", "eq")
        E(mov_reg, 0, 4); E(bl, "c_von")
        a.label("se_x"); E(pop_list, [4], pc=True)


    a.label("c_sdopen")                                                           # r0 = track -> r0 != 0 when the step-drummer view is open and the track has it enabled
    E(push_list, [4], lr=True)
    E(mov_reg, 4, 0); E(movs_imm, 0, F_SDOPEN); E(bl, "c_sdflag"); E(cmp_imm, 0, 0); E(b_cond, "so_x", "eq")
    E(mov_reg, 0, 4); E(bl, "c_sden")
    a.label("so_x"); E(pop_list, [4], pc=True)

    if not SD2:
        a.label("c_sdview")                                                           # r0 = track -> r0 = 1 when the view is open and the Preset view of that MIDI track is the current view (the knobs are the pairs)
        E(push_list, [4], lr=True)
        E(mov_reg, 4, 0); E(bl, "c_sdopen"); E(cmp_imm, 0, 0); E(b_cond, "sv_x", "eq")
        E(movw, 1, MGR_OBJ & 0xFFFF); E(movt, 1, MGR_OBJ >> 16); E(ldrb_w, 1, 1, S_CUR)
        E(movs_imm, 2, 9); E(muls, 2, 4); E(adds_imm8, 2, 18); E(movs_imm, 0, 0); E(cmp_reg, 1, 2); E(b_cond, "sv_x", "ne"); E(movs_imm, 0, 1)
        a.label("sv_x"); E(pop_list, [4], pc=True)
    else:
        a.label("c_sdscr")                                                            # -> r0 = the track whose step-drummer view is on the screen (0..3), or 0xFF
        E(push_list, [4], lr=True)
        E(movw, 4, MGR_OBJ & 0xFFFF); E(movt, 4, MGR_OBJ >> 16)
        E(ldr_imm, 1, 4, 0x6C); E(ldr_imm, 2, 4, 0x2C); E(cmp_reg, 1, 2); bc("cu_n", "ne")       # the active view is the container of the track views
        E(ldrb_w, 0, 4, S_CUR)
        E(movs_imm, 4, 0); E(cmp_imm, 0, 18); E(b_cond, "cu_t", "eq")
        E(movs_imm, 4, 1); E(cmp_imm, 0, 27); E(b_cond, "cu_t", "eq")
        E(movs_imm, 4, 2); E(cmp_imm, 0, 0); E(b_cond, "cu_s", "eq")
        E(movs_imm, 4, 3); E(cmp_imm, 0, 9); bc("cu_n", "ne")
        a.label("cu_s")                                                                   # the Preset view of a synth: only as the source view of SC19.1
        E(bl, L["c_gst"]); E(cmp_imm, 0, 0); bc("cu_n", "eq")
        E(ldrb_imm, 0, 0, S_PAINT); E(movs_imm, 1, F_SRC); E(tst_reg, 0, 1); bc("cu_n", "eq")
        a.label("cu_t")
        E(mov_reg, 0, 4); E(bl, "c_sdopen"); E(cmp_imm, 0, 0); bc("cu_n", "eq")
        E(mov_reg, 0, 4); E(pop_list, [4], pc=True)
        a.label("cu_n"); E(movs_imm, 0, 0xFF); E(pop_list, [4], pc=True)

        a.label("c_sdview")                                                           # r0 = track -> r0 = 1 when its step-drummer view is on the screen
        E(push_list, [4], lr=True)
        E(mov_reg, 4, 0); E(bl, "c_sdscr"); E(movs_imm, 1, 0); E(cmp_reg, 0, 4); E(b_cond, "sv_x", "ne"); E(movs_imm, 1, 1)
        a.label("sv_x"); E(mov_reg, 0, 1); E(pop_list, [4], pc=True)

        a.label("c_sdsyn")                                                            # r0 = a macro handler -> r0 = 2 / 3 when it is the handler of Synth 1 / 2 and the step-drummer view of that synth is on the screen, else 0xFF
        E(push_list, [4], lr=True)
        E(mov_reg, 4, 0)
        E(movw, 1, CTX_PTR & 0xFFFF); E(movt, 1, CTX_PTR >> 16)
        E(ldr_imm, 1, 1, 0); E(cmp_imm, 1, 0); bc("sy_n", "eq")
        E(ldr_imm, 1, 1, 0x40); E(cmp_imm, 1, 0); bc("sy_n", "eq")
        E(ldr_imm, 1, 1, 0x2C); E(cmp_imm, 1, 0); bc("sy_n", "eq")
        E(raw, ldr_w(2, 1, 0x148)); E(movs_imm, 3, 2); E(cmp_reg, 2, 4); E(b_cond, "sy_f", "eq")
        E(raw, ldr_w(2, 1, 0x14C)); E(movs_imm, 3, 3); E(cmp_reg, 2, 4); bc("sy_n", "ne")
        a.label("sy_f")
        E(mov_reg, 4, 3); E(bl, "c_sdscr"); E(cmp_reg, 0, 4); bc("sy_n", "ne")
        E(mov_reg, 0, 4); E(pop_list, [4], pc=True)
        a.label("sy_n"); E(movs_imm, 0, 0xFF); E(pop_list, [4], pc=True)


    if not SD2:
        a.label("c_sdrec")                                                            # r0 = track -> r0 = the recorder of the MIDI track; clobbers r1
        E(movw, 1, REC_GATE_OBJ & 0xFFFF); E(movt, 1, REC_GATE_OBJ >> 16); E(lsls_imm, 0, 0, 2); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0x14); E(raw, RET)
    else:
        a.label("c_sdrec")                                                            # r0 = track 0..3 -> r0 = its recorder (index 2, 3, 0, 1); clobbers r1
        E(adds_imm8, 0, 2); E(movs_imm, 1, 3); E(ands_reg, 0, 1)
        E(movw, 1, REC_GATE_OBJ & 0xFFFF); E(movt, 1, REC_GATE_OBJ >> 16); E(lsls_imm, 0, 0, 2); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0x0C); E(raw, RET)


    if not SD2:
        a.label("c_sdeng")                                                            # r0 = track, r1 = param -> r0 = pointer to that param of the engine store of the track (0 pattern, 1 step, 2 tick)
        E(push_list, [4], lr=True)
        E(mov_reg, 4, 1); E(movw, 1, ENGINE & 0xFFFF); E(movt, 1, ENGINE >> 16); E(lsls_imm, 0, 0, 2); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0x38)
        E(mov_reg, 1, 4); E(bl, PARAM_GET)
        E(pop_list, [4], pc=True)
    else:
        a.label("c_sdeng")                                                            # r0 = track 0..3, r1 = param -> r0 = pointer to that param of the engine store of the track
        E(push_list, [4], lr=True)
        E(mov_reg, 4, 1); E(adds_imm8, 0, 2); E(movs_imm, 1, 3); E(ands_reg, 0, 1)
        E(movw, 1, ENGINE & 0xFFFF); E(movt, 1, ENGINE >> 16); E(lsls_imm, 0, 0, 2); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0x30)
        E(mov_reg, 1, 4); E(bl, PARAM_GET)
        E(pop_list, [4], pc=True)

        a.label("c_sdlofs")                                                           # r0 = track -> r0 = the offset of its pitch lane inside the lanes: 0 (lane 0) for a MIDI track, 192 x the macro for a synth
        E(cmp_imm, 0, 2); E(b_cond, "lo_s", "hs"); E(movs_imm, 0, 0); E(raw, RET)
        a.label("lo_s")
        E(push_list, [4], lr=True); E(bl, "c_sdnib"); E(lsrs_imm, 0, 0, 1); E(movs_imm, 1, 192); E(muls, 0, 1); E(pop_list, [4], pc=True)

        a.label("c_sdbase")                                                           # r0 = track -> r0 = what a pair with no pitch value shows / starts from: the centre for a MIDI track, the present position of the macro for a synth
        if FXSEQ:                                                                     # (the FX sequencer: 0 = no effect)
            E(cmp_imm, 0, 2); E(b_cond, "ba_s", "hs")
            E(push_list, [4], lr=True); E(bl, "c_fsq"); E(movs_imm, 1, 64); E(cmp_imm, 0, 0); E(b_cond, "ba_f", "eq"); E(movs_imm, 1, 0)
            a.label("ba_f"); E(mov_reg, 0, 1); E(pop_list, [4], pc=True)
        else:
            E(cmp_imm, 0, 2); E(b_cond, "ba_s", "hs"); E(movs_imm, 0, 64); E(raw, RET)
        a.label("ba_s")
        E(push_list, [4], lr=True)
        E(mov_reg, 4, 0); E(bl, "c_sdnib"); E(lsrs_imm, 1, 0, 1); E(movs_imm, 2, 17); E(muls, 1, 2); E(adds_imm8, 1, 174)
        E(mov_reg, 0, 4); E(subs_imm8, 0, 2); E(bl, GETTER)
        E(cmp_imm, 0, 127); E(b_cond, "ba_x", "ls"); E(movs_imm, 0, 127)
        a.label("ba_x"); E(pop_list, [4], pc=True)

        # ---- c_sdio(r0 = track, r1 = 1 note on / 0 note off, r2 = velocity): the note of the audition: a note of the MIDI track (through the note wrappers), or an internal note on the channel of the synth
        a.label("c_sdio")
        E(push_list, [4, 5, 6, 7], lr=True)
        E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
        if KEEPNOTE: E(mov_reg, 7, 3)                                                       # r3 = the note (KEEPNOTE)
        else: E(bl, "c_sdtonic"); E(mov_reg, 7, 0)
        E(cmp_imm, 4, 2); E(b_cond, "io_s", "hs")
        E(mov_reg, 2, 7); E(mov_reg, 3, 6); E(movw, 0, TXOBJ & 0xFFFF); E(movt, 0, TXOBJ >> 16); E(mov_reg, 1, 4); E(adds_imm8, 1, 2)
        E(cmp_imm, 5, 0); E(b_cond, "io_f", "eq"); E(bl, "c_vnon"); E(b, "io_x")
        a.label("io_f"); E(bl, "c_vnoff"); E(b, "io_x")
        a.label("io_s")
        E(raw, h(0xB082))                                                                 # sub sp, #8
        E(movw, 1, TXOBJ & 0xFFFF); E(movt, 1, TXOBJ >> 16); E(ldr_imm, 1, 1, 0x0C); E(mov_reg, 0, 4); E(subs_imm8, 0, 2); E(ldrb_reg, 0, 1, 0)
        E(movs_imm, 1, 0x80); E(cmp_imm, 5, 0); E(b_cond, "io_t", "eq"); E(movs_imm, 1, 0x90)
        a.label("io_t"); E(orrs_reg, 0, 1); E(mov_reg, 1, 13)
        E(strb_imm, 0, 1, 0); E(strb_imm, 7, 1, 1); E(strb_imm, 6, 1, 2)
        E(mov_reg, 0, 1); E(bl, L["c_inject"])
        E(raw, h(0xB002))                                                                 # add sp, #8
        a.label("io_x"); E(pop_list, [4, 5, 6, 7], pc=True)


    a.label("c_sdpat")                                                            # r0 = track -> r0 = the address of the pattern of the track that is selected / plays
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0); E(movs_imm, 1, 0); E(bl, "c_sdeng"); E(ldrb_imm, 5, 0, 0); E(movs_imm, 1, 7); E(ands_reg, 5, 1)
    E(mov_reg, 0, 4); E(bl, "c_sdrec"); E(ldr_imm, 0, 0, 0x48)
    E(movw, 1, 0xCA8); E(muls, 1, 5); E(adds_reg, 0, 0, 1)
    E(pop_list, [4, 5], pc=True)

    a.label("c_sdstp")                                                            # r0 = pattern, r1 = step -> r0 = the step record (28 bytes); clobbers r2
    E(movs_imm, 2, 28); E(muls, 2, 1); E(adds_reg, 0, 0, 2); E(raw, RET)

    a.label("c_sdlna")                                                            # r0 = pattern, r1 = step -> r0 = the 6 lane-0 bytes of the step; clobbers r2
    E(movs_imm, 2, 6); E(muls, 2, 1); E(adds_reg, 0, 0, 2); E(movw, 2, 0x3A8); E(adds_reg, 0, 0, 2); E(raw, RET)

    a.label("c_sdtonic")                                                          # -> r0 = the note of every step: the root of the scale (the drum Preset view's pointer to it) in octave 2; clobbers r1
    E(movw, 1, CTX_PTR & 0xFFFF); E(movt, 1, CTX_PTR >> 16)
    E(movs_imm, 0, 0)
    E(ldr_imm, 1, 1, 0); E(cmp_imm, 1, 0); E(b_cond, "tn_x", "eq")
    E(ldr_imm, 1, 1, 0x40); E(cmp_imm, 1, 0); E(b_cond, "tn_x", "eq")
    E(ldr_imm, 1, 1, 0x2C); E(cmp_imm, 1, 0); E(b_cond, "tn_x", "eq")
    E(raw, ldr_w(1, 1, 0x8C)); E(cmp_imm, 1, 0); E(b_cond, "tn_x", "eq")
    E(ldr_imm, 1, 1, 0x0C); E(cmp_imm, 1, 0); E(b_cond, "tn_x", "eq")
    E(ldr_imm, 1, 1, 0x48); E(cmp_imm, 1, 0); E(b_cond, "tn_x", "eq")
    E(ldrb_imm, 0, 1, 0); E(cmp_imm, 0, 11); E(b_cond, "tn_x", "ls"); E(movs_imm, 0, 0)
    a.label("tn_x"); E(adds_imm8, 0, SD_TONIC); E(raw, RET)

    a.label("c_sdpos")                                                            # r0 = track -> r0 = the step whose pitch value counts: the one being auditioned, else the one that plays
    E(push_list, [4], lr=True)
    E(mov_reg, 4, 0); E(bl, L["c_gfst"]); E(cmp_imm, 0, 0); E(b_cond, "dp_p", "eq")
    E(ldrb_w, 1, 0, SD_AUD); E(cmp_imm, 1, 0); E(b_cond, "dp_p", "eq")
    E(lsrs_imm, 2, 1, 6); E(cmp_reg, 2, 4); E(b_cond, "dp_p", "ne")
    E(movs_imm, 2, 0x3F); E(ands_reg, 1, 2); E(subs_imm8, 1, 1); E(mov_reg, 0, 1); E(pop_list, [4], pc=True)
    a.label("dp_p")
    E(mov_reg, 0, 4); E(movs_imm, 1, 1); E(bl, "c_sdeng"); E(ldrb_imm, 0, 0, 0); E(movs_imm, 1, 31); E(ands_reg, 0, 1)
    E(pop_list, [4], pc=True)

    a.label("c_sdoff")                                                            # r0 = track -> r0 = the offset of the pitch row at that step (-64..63; no value in the lane = 0)
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0); E(bl, "c_sdpos"); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(bl, "c_sdpat"); E(mov_reg, 1, 5); E(bl, "c_sdlna"); E(ldrb_imm, 0, 0, 0)
    E(cmp_imm, 0, 127); E(b_cond, "do_v", "ls"); E(movs_imm, 0, 64)
    a.label("do_v"); E(subs_imm8, 0, 64)
    E(pop_list, [4, 5], pc=True)

    # ---- c_sdfx(r0 = track, r1 = the stored value of a code, r2 = code - 1) -> r1 = the value that goes to the DSP: with the step-drummer enabled the destination of the pitch row gets the offset of the step;
    #      r2 and r4-r7 are kept; clobbers r0, r3
    a.label("c_sdfx")
    E(push_list, [2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2); E(adds_imm8, 6, 1)
    E(mov_reg, 0, 4); E(bl, "c_sden"); E(cmp_imm, 0, 0); bc("fx_x", "eq")
    E(mov_reg, 0, 4); E(bl, "c_sdnib"); E(lsrs_imm, 7, 0, 1)                          # r7 = the destination 0..7
    E(cmp_imm, 7, 1); bc("fx_s", "hi")
    E(cmp_imm, 6, 27); E(b_cond, "fx_p2", "hs")
    E(cmp_imm, 7, 0); bc("fx_x", "ne")                                                # destination 1 leaves the first oscillator alone
    E(cmp_imm, 6, 17); E(b_cond, "fx_p1", "eq"); E(cmp_imm, 6, 18); bc("fx_x", "ne")
    a.label("fx_p1"); E(movs_imm, 7, 17); E(b, "fx_p")
    a.label("fx_p2"); E(cmp_imm, 6, 28); bc("fx_x", "hi"); E(movs_imm, 7, 27)
    a.label("fx_p")                                                                   # r7 = the TUNE code of the oscillator: total = 128 TUNE + FINE + 24 offset (1 / 128 semitone)
    E(mov_reg, 0, 4); E(mov_reg, 1, 7); E(bl, "c_vvaddr"); E(raw, ldrsb_w(0, 0, 0)); E(lsls_imm, 5, 0, 7)
    E(mov_reg, 0, 4); E(mov_reg, 1, 7); E(adds_imm8, 1, 1); E(bl, "c_vvaddr"); E(raw, ldrsb_w(0, 0, 0)); E(adds_reg, 5, 5, 0)
    E(mov_reg, 0, 4); E(bl, "c_sdoff"); E(movs_imm, 1, 24); E(muls, 0, 1); E(adds_reg, 5, 5, 0)
    E(mov_reg, 0, 5); E(adds_imm8, 0, 64); E(raw, asrs_imm(0, 0, 7))                   # r0 = the semitones
    clamp(0, -64, 63, 1, "fx_t")
    E(cmp_reg, 6, 7); E(b_cond, "fx_f", "ne"); E(mov_reg, 5, 0); E(b, "fx_x")
    a.label("fx_f"); E(lsls_imm, 1, 0, 7); E(subs_reg, 5, 5, 1)
    clamp(5, -64, 63, 1, "fx_g")
    E(b, "fx_x")
    a.label("fx_s")                                                                   # a single destination: value + offset, in the range of the code
    E(movw, 3, t_sd & 0xFFFF); E(movt, 3, t_sd >> 16); E(ldrb_reg, 0, 3, 7); E(cmp_reg, 0, 6); bc("fx_x", "ne")
    E(mov_reg, 0, 4); E(bl, "c_sdoff"); E(adds_reg, 5, 5, 0)
    E(cmp_imm, 6, 3); E(b_cond, "fx_u", "ne")
    clamp(5, -64, 63, 1, "fx_b")
    E(b, "fx_x")
    a.label("fx_u")
    E(cmp_imm, 6, 20); E(b_cond, "fx_w", "ne")
    clamp(5, 0, 100, 1, "fx_c")
    E(b, "fx_x")
    a.label("fx_w")
    clamp(5, 0, 127, 1, "fx_d")
    a.label("fx_x"); E(mov_reg, 1, 5); E(pop_list, [2, 4, 5, 6, 7], pc=True)

    a.label("c_sdcur")                                                            # r0 = track, r1 = a volatile code 27..34: the sweep sends it next; clobbers r0-r3
    tail(2); E(lsls_imm, 3, 0, 3); E(adds_reg, 2, 2, 3); E(ldrb_w, 0, 2, O_RT + RT_CNT); E(movs_imm, 3, 0x70); E(bics_reg, 0, 3)
    E(subs_imm8, 1, 27); E(lsls_imm, 1, 1, 4); E(orrs_reg, 0, 1); E(strb_w, 0, 2, O_RT + RT_CNT); E(raw, RET)

    a.label("c_sdmark")                                                           # r0 = track: (a note starts, a pair value changed) the destination of the pitch row is sent to the DSP again
    if SD2:
        E(cmp_imm, 0, 2); E(b_cond, "mk_m", "lo"); E(raw, RET)                        # a synth: the stock engine plays its lanes
        a.label("mk_m")
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0); E(bl, "c_sden"); E(cmp_imm, 0, 0); bc("mk_x", "eq")
    E(mov_reg, 0, 4); E(bl, "c_sdnib"); E(lsrs_imm, 5, 0, 1)
    E(cmp_imm, 5, 1); E(b_cond, "mk_s", "hi")
    E(cmp_imm, 5, 0); E(b_cond, "mk_2", "ne")
    E(mov_reg, 0, 4); E(movs_imm, 1, 17); E(bl, "c_vmark"); E(mov_reg, 0, 4); E(movs_imm, 1, 18); E(bl, "c_vmark")
    a.label("mk_2"); E(mov_reg, 0, 4); E(movs_imm, 1, 27); E(bl, "c_sdcur"); E(b, "mk_x")
    a.label("mk_s")
    E(movw, 3, t_sd & 0xFFFF); E(movt, 3, t_sd >> 16); E(ldrb_reg, 1, 3, 5)
    E(mov_reg, 0, 4); E(cmp_imm, 1, 26); E(b_cond, "mk_v", "hi"); E(bl, "c_vmark"); E(b, "mk_x")
    a.label("mk_v"); E(bl, "c_sdcur")
    a.label("mk_x"); E(pop_list, [4, 5], pc=True)

    a.label("c_sdconv")                                                           # r0 = track: every step of the pattern with notes keeps one note (unit 0, with the length / micro step / velocity of its first note) = the tonic
    E(push_list, [4, 5, 6, 7], lr=True)
    E(bl, "c_sdpat"); E(mov_reg, 5, 0); E(bl, "c_sdtonic"); E(mov_reg, 7, 0); E(movs_imm, 6, 0)
    a.label("cv_l")
    E(ldrb_imm, 1, 5, 0); E(movs_imm, 2, 0x3F); E(ands_reg, 1, 2); E(cmp_imm, 1, 0); E(b_cond, "cv_n", "eq")
    E(mov_reg, 3, 5)
    a.label("cv_b"); E(movs_imm, 2, 1); E(tst_reg, 1, 2); E(b_cond, "cv_f", "ne"); E(lsrs_imm, 1, 1, 1); E(adds_imm8, 3, 4); E(b, "cv_b")
    a.label("cv_f")                                                                   # r3 = the step record + 4 x the first unit with a note
    E(ldrb_imm, 0, 3, 5); E(ldrb_imm, 1, 3, 6); E(ldrb_imm, 2, 3, 7)
    if KEEPNOTE: E(ldrb_imm, 7, 3, 4)                                               # the note of the step stays (r7 is reloaded: the tonic is not used)
    E(strb_imm, 7, 5, 4); E(strb_imm, 0, 5, 5); E(strb_imm, 1, 5, 6); E(strb_imm, 2, 5, 7)
    E(movs_imm, 0, 0); E(movs_imm, 1, 0x60)
    for k in range(1, 6):
        for j in range(3): E(strb_imm, 0, 5, 4 + 4 * k + j)
        E(strb_imm, 1, 5, 4 + 4 * k + 3)
    E(movs_imm, 0, 1); E(strb_imm, 0, 5, 0)
    a.label("cv_n"); E(adds_imm8, 5, 28); E(adds_imm8, 6, 1); E(cmp_imm, 6, 32); E(b_cond, "cv_l", "lo")
    E(pop_list, [4, 5, 6, 7], pc=True)

    a.label("c_sdpvel")                                                           # r0 = track, r1 = a step -> r0 = the velocity of the pair of that step (its first note), 0 = no note
    E(push_list, [4, 5], lr=True)
    E(lsrs_imm, 5, 1, 1); E(lsls_imm, 5, 5, 1)
    E(bl, "c_sdpat"); E(mov_reg, 1, 5); E(bl, "c_sdstp"); E(mov_reg, 4, 0)
    E(ldrb_imm, 1, 4, 0); E(movs_imm, 2, 1); E(tst_reg, 1, 2); E(b_cond, "pv_2", "eq"); E(ldrb_imm, 0, 4, 7); E(pop_list, [4, 5], pc=True)
    a.label("pv_2"); E(adds_imm8, 4, 28); E(ldrb_imm, 1, 4, 0); E(tst_reg, 1, 2); E(b_cond, "pv_0", "eq"); E(ldrb_imm, 0, 4, 7); E(pop_list, [4, 5], pc=True)
    a.label("pv_0"); E(movs_imm, 0, 0); E(pop_list, [4, 5], pc=True)

    a.label("c_sdnvel")                                                           # r0 = track, r1 = a step -> r0 = the velocity a new note takes: its pair's, else the nearest earlier note's (going round the 32 steps), else 64
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_sdpvel"); E(cmp_imm, 0, 0); E(b_cond, "nv_x", "ne")
    E(mov_reg, 0, 4); E(bl, "c_sdpat"); E(mov_reg, 6, 0); E(movs_imm, 7, 31)
    a.label("nv_l")
    E(cmp_imm, 5, 0); E(b_cond, "nv_d", "ne"); E(movs_imm, 5, 32)
    a.label("nv_d"); E(subs_imm8, 5, 1)
    E(mov_reg, 0, 6); E(mov_reg, 1, 5); E(bl, "c_sdstp"); E(ldrb_imm, 1, 0, 0); E(movs_imm, 2, 1); E(tst_reg, 1, 2); E(b_cond, "nv_n", "eq")
    E(ldrb_imm, 0, 0, 7); E(b, "nv_x")
    a.label("nv_n"); E(subs_imm8, 7, 1); E(b_cond, "nv_l", "ne")
    E(movs_imm, 0, 64)
    a.label("nv_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    if KEEPNOTE:
        a.label("c_sdnnote")                                                      # r0 = track, r1 = a step -> r0 = the note of that step: its pair's (first note), else the nearest earlier note's (going round the 32 steps), else the tonic
        E(push_list, [4, 5, 6, 7], lr=True)
        E(mov_reg, 4, 0); E(mov_reg, 5, 1)
        E(lsrs_imm, 5, 5, 1); E(lsls_imm, 5, 5, 1)                                    # the first step of the pair
        E(bl, "c_sdpat"); E(mov_reg, 6, 0)
        E(mov_reg, 1, 5); E(bl, "c_sdstp"); E(ldrb_imm, 1, 0, 0); E(movs_imm, 2, 1); E(tst_reg, 1, 2); E(b_cond, "nn_y", "ne")
        E(adds_imm8, 0, 28); E(ldrb_imm, 1, 0, 0); E(tst_reg, 1, 2); E(b_cond, "nn_y", "ne")
        E(movs_imm, 7, 31)
        a.label("nn_l")
        E(cmp_imm, 5, 0); E(b_cond, "nn_d", "ne"); E(movs_imm, 5, 32)
        a.label("nn_d"); E(subs_imm8, 5, 1)
        E(mov_reg, 0, 6); E(mov_reg, 1, 5); E(bl, "c_sdstp"); E(ldrb_imm, 1, 0, 0); E(movs_imm, 2, 1); E(tst_reg, 1, 2); E(b_cond, "nn_y", "ne")
        E(subs_imm8, 7, 1); E(b_cond, "nn_l", "ne")
        E(bl, "c_sdtonic"); E(b, "nn_x")
        a.label("nn_y"); E(ldrb_imm, 0, 0, 4)
        a.label("nn_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    a.label("c_sdnote")                                                           # r0 = a step record, r1 = velocity: one note (unit 0) = the tonic, one step long; clobbers r0-r3
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    if KEEPNOTE: E(mov_reg, 0, 2)                                                   # r2 = the note (KEEPNOTE)
    else: E(bl, "c_sdtonic")
    E(strb_imm, 0, 4, 4); E(movs_imm, 0, SD_LEN); E(strb_imm, 0, 4, 5); E(movs_imm, 0, 0); E(strb_imm, 0, 4, 6); E(strb_imm, 5, 4, 7)
    E(movs_imm, 0, 1); E(strb_imm, 0, 4, 0)
    E(pop_list, [4, 5], pc=True)

    a.label("c_sdnone")                                                           # r0 = a step record: no note; clobbers r1
    E(movs_imm, 1, 0); E(strb_imm, 1, 0, 0); E(strb_imm, 1, 0, 4); E(strb_imm, 1, 0, 5); E(strb_imm, 1, 0, 6); E(movs_imm, 1, 0x60); E(strb_imm, 1, 0, 7); E(raw, RET)

    a.label("c_sdhalf")                                                           # r0 = a step 0..15 of the half shown -> r0 = the step of the pattern; clobbers r1, r2
    E(mov_reg, 2, 0); E(movs_imm, 0, F_SDHALF); tail(1); E(ldrb_w, 1, 1, O_FLAGS); E(ands_reg, 0, 1); E(cmp_imm, 0, 0); E(b_cond, "hf_x", "eq"); E(adds_imm8, 2, 16)
    a.label("hf_x"); E(mov_reg, 0, 2); E(raw, RET)

    # ---- c_sdknob(r0 = track, r1 = knob 0..7, r2 = delta): the pair of steps of the knob: its pitch value (lane 0 of both steps) or the velocity of its notes
    a.label("c_sdknob")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(bl, "c_sdconv")
    E(lsls_imm, 0, 5, 1); E(bl, "c_sdhalf"); E(mov_reg, 5, 0)                         # r5 = the first step of the pair
    E(movs_imm, 0, F_SDPAGE); E(bl, "c_sdflag"); E(cmp_imm, 0, 0); bc("kn_v", "ne")
    E(mov_reg, 0, 4); E(bl, "c_sdpat"); E(mov_reg, 1, 5); E(bl, "c_sdlna"); E(mov_reg, 7, 0)
    if SD2:                                                                       # the lane of the macro of a synth; a pair with no value starts from the base
        E(mov_reg, 0, 4); E(bl, "c_sdlofs"); E(adds_reg, 7, 7, 0)
        E(ldrb_imm, 0, 7, 0); E(cmp_imm, 0, 127); E(b_cond, "kn_a", "ls"); E(mov_reg, 0, 4); E(bl, "c_sdbase")
    else:
        E(ldrb_imm, 0, 7, 0); E(cmp_imm, 0, 127); E(b_cond, "kn_a", "ls"); E(movs_imm, 0, 64)
    a.label("kn_a")
    if FXSEQ3:                                                                    # the FX sequencer: the position 0..FSQ_MAX of the pair (an empty pair = 0) + delta
        if SDKFIX: E(push_list, [0]); E(mov_reg, 0, 4); E(bl, "c_fsq"); E(mov_reg, 1, 0); E(pop_list, [0]); E(cmp_imm, 1, 0); E(b_cond, "kn_nf", "eq")
        else: E(mov_reg, 0, 4); E(bl, "c_fsq"); E(cmp_imm, 0, 0); E(b_cond, "kn_nf", "eq")
        E(ldrb_imm, 0, 7, 0); E(cmp_imm, 0, FSQ_MAX); E(b_cond, "kn_f0", "ls"); E(movs_imm, 0, 0)
        a.label("kn_f0")
        if FSQ_DIV > 1:                                                           # (r6 = the events of this call) -> r6 = the units, the rest kept
            E(push_list, [0])
            tail(2); E(ldrb_w, 3, 2, O_ED + 1); E(lsrs_imm, 1, 3, 4); E(lsls_imm, 1, 1, 28); E(raw, h(0x1000 | 28 << 6 | 1 << 3 | 1))     # asrs r1, r1, #28: the signed rest
            E(adds_reg, 1, 1, 6)
            E(movs_imm, 0, 0); E(cmp_imm, 1, 0); E(b_cond, "kn_fq", "ge"); E(raw, h(0x4240 | 1 << 3 | 1)); E(movs_imm, 0, 1)             # negs r1, r1
            a.label("kn_fq")
            E(movs_imm, 2, FSQ_DIV); E(raw, udiv_w(6, 1, 2)); E(raw, mls_w(1, 6, 2, 1))                                                    # r6 = |acc| / div, r1 = the rest
            E(cmp_imm, 0, 0); E(b_cond, "kn_fr", "eq"); E(raw, h(0x4240 | 6 << 3 | 6)); E(raw, h(0x4240 | 1 << 3 | 1))
            a.label("kn_fr")
            tail(2); E(ldrb_w, 3, 2, O_ED + 1); E(movs_imm, 0, 0x0F); E(ands_reg, 3, 0); E(lsls_imm, 1, 1, 28); E(lsrs_imm, 1, 1, 24); E(orrs_reg, 3, 1)
            E(strb_w, 3, 2, O_ED + 1)
            E(pop_list, [0])
        E(adds_reg, 0, 0, 6); clamp(0, 0, FSQ_MAX, 1, "kn_fc"); E(b, "kn_st")
        a.label("kn_nf")
    elif FXSEQ2:                                                                  # the FX sequencer: one value per turn, 0..6
        E(push_list, [0]); E(mov_reg, 0, 4); E(bl, "c_fsq"); E(mov_reg, 1, 0); E(pop_list, [0]); E(cmp_imm, 1, 0); E(b_cond, "kn_nf", "eq")
        E(cmp_imm, 6, 0); E(b_cond, "kn_fs", "eq"); E(b_cond, "kn_fp", "gt"); E(subs_imm8, 0, 1); E(b, "kn_fs")
        a.label("kn_fp"); E(adds_imm8, 0, 1)
        a.label("kn_fs"); clamp(0, 0, 6, 1, "kn_fc"); E(b, "kn_st")
        a.label("kn_nf")
    E(adds_reg, 0, 0, 6)
    clamp(0, 0, 127, 1, "kn_c")
    if FXSEQ2: a.label("kn_st")
    for i in range(12): E(strb_imm, 0, 7, i)
    E(mov_reg, 0, 4); E(bl, "c_sdmark")
    E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("kn_v")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_sdpvel"); E(adds_reg, 7, 0, 6)
    clamp(7, 0, 127, 1, "kn_d")
    E(mov_reg, 0, 4); E(bl, "c_sdpat"); E(mov_reg, 1, 5); E(bl, "c_sdstp"); E(mov_reg, 6, 0)   # r6 = the record of the first step, r7 = the new velocity
    E(cmp_imm, 7, 0); E(b_cond, "kv_s", "ne")
    if KEEPNOTE: E(bl, "c_sdaoff")                                                # a held audition ends before its note goes (the note-off finds the same note)
    E(mov_reg, 0, 6); E(bl, "c_sdnone"); E(mov_reg, 0, 6); E(adds_imm8, 0, 28); E(bl, "c_sdnone")
    E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("kv_s")
    E(ldrb_imm, 0, 6, 0); E(ldrb_imm, 1, 6, 28); E(orrs_reg, 0, 1); E(movs_imm, 1, 1); E(tst_reg, 0, 1); E(b_cond, "kv_h", "ne")
    if KEEPNOTE: E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_sdnnote"); E(mov_reg, 2, 0)
    E(mov_reg, 0, 6); E(mov_reg, 1, 7); E(bl, "c_sdnote")
    a.label("kv_h")
    E(movs_imm, 1, 1)
    E(ldrb_imm, 0, 6, 0); E(tst_reg, 0, 1); E(b_cond, "kv_2", "eq"); E(strb_imm, 7, 6, 7)
    a.label("kv_2"); E(adds_imm8, 6, 28); E(ldrb_imm, 0, 6, 0); E(tst_reg, 0, 1); E(b_cond, "kv_x", "eq"); E(strb_imm, 7, 6, 7)
    a.label("kv_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    if not SD2:
        # ---- c_sdaoff(): the auditioned note ends
        a.label("c_sdaoff")
        E(push_list, [4, 5], lr=True)
        E(bl, L["c_gfst"]); E(cmp_imm, 0, 0); E(b_cond, "ao_x", "eq")
        E(mov_reg, 4, 0); E(ldrb_w, 5, 4, SD_AUD); E(cmp_imm, 5, 0); E(b_cond, "ao_x", "eq")
        E(movs_imm, 1, 0); E(strb_w, 1, 4, SD_AUD)
        if KEEPNOTE: E(lsrs_imm, 0, 5, 6); E(movs_imm, 1, 63); E(ands_reg, 1, 5); E(subs_imm8, 1, 1); E(bl, "c_sdnnote")
        else: E(bl, "c_sdtonic")
        E(mov_reg, 2, 0); E(movs_imm, 3, 0)
        E(movw, 0, TXOBJ & 0xFFFF); E(movt, 0, TXOBJ >> 16); E(lsrs_imm, 1, 5, 6); E(adds_imm8, 1, 2); E(bl, "c_vnoff")
        a.label("ao_x"); E(pop_list, [4, 5], pc=True)
    else:
        a.label("c_sdaoff")
        E(push_list, [4, 5], lr=True)
        E(bl, L["c_gfst"]); E(cmp_imm, 0, 0); E(b_cond, "ao_x", "eq")
        E(mov_reg, 4, 0); E(ldrb_w, 5, 4, SD_AUD); E(cmp_imm, 5, 0); E(b_cond, "ao_x", "eq")
        E(movs_imm, 1, 0); E(strb_w, 1, 4, SD_AUD)
        if KEEPNOTE: E(lsrs_imm, 0, 5, 6); E(movs_imm, 1, 63); E(ands_reg, 1, 5); E(subs_imm8, 1, 1); E(bl, "c_sdnnote"); E(mov_reg, 3, 0)
        E(lsrs_imm, 0, 5, 6); E(movs_imm, 1, 0); E(movs_imm, 2, 0); E(bl, "c_sdio")
        a.label("ao_x"); E(pop_list, [4, 5], pc=True)


    if not SD2:
        # ---- c_sdpad(r0 = track, r1 = pad 0..23): a step (tap = audition, Shift + tap = add / remove its note) or a destination of the pitch row
        a.label("c_sdpad")
        E(push_list, [4, 5, 6, 7], lr=True)
        E(mov_reg, 4, 0); E(mov_reg, 5, 1)
        E(cmp_imm, 5, 16); bc("pd_d", "hs")
        E(bl, "c_sdconv")
        E(mov_reg, 0, 5); E(bl, "c_sdhalf"); E(mov_reg, 5, 0)
        E(bl, L["c_shift"]); E(cmp_imm, 0, 0); bc("pd_t", "ne")
        E(bl, "c_sdaoff")                                                                 # audition: the step counts for the pitch row while its pad is held
        E(bl, L["c_gfst"]); E(cmp_imm, 0, 0); bc("pd_x", "eq")
        E(lsls_imm, 1, 4, 6); E(adds_reg, 1, 1, 5); E(adds_imm8, 1, 1); E(strb_w, 1, 0, SD_AUD)
        E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_sdpvel"); E(cmp_imm, 0, 0); E(b_cond, "pd_v", "ne"); E(movs_imm, 0, 100)
        a.label("pd_v"); E(mov_reg, 6, 0)
        if KEEPNOTE: E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_sdnnote")
        else: E(bl, "c_sdtonic")
        E(mov_reg, 2, 0); E(mov_reg, 3, 6)
        E(movw, 0, TXOBJ & 0xFFFF); E(movt, 0, TXOBJ >> 16); E(mov_reg, 1, 4); E(adds_imm8, 1, 2); E(bl, "c_vnon")
        E(b, "pd_x")
        a.label("pd_t")                                                                   # Shift: the note of the step on / off
        if KEEPNOTE: E(bl, "c_sdaoff")                                                    # a held audition ends first (its note-off must find the note it played)
        E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_sdnvel"); E(mov_reg, 6, 0)
        E(mov_reg, 0, 4); E(bl, "c_sdpat"); E(mov_reg, 1, 5); E(bl, "c_sdstp"); E(mov_reg, 7, 0)
        E(ldrb_imm, 1, 7, 0); E(movs_imm, 2, 1); E(tst_reg, 1, 2); E(b_cond, "pd_a", "eq")
        E(mov_reg, 0, 7); E(bl, "c_sdnone"); E(b, "pd_x")
        a.label("pd_a")
        if KEEPNOTE: E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_sdnnote"); E(mov_reg, 2, 0)
        E(mov_reg, 0, 7); E(mov_reg, 1, 6); E(bl, "c_sdnote"); E(b, "pd_x")
        a.label("pd_d")                                                                   # a destination pad
        E(mov_reg, 0, 4); E(bl, "c_sdmark")                                                # the old destination goes to the DSP again (as its plain value: the nibble changes before it is sent)
        E(subs_imm8, 5, 16); E(lsls_imm, 1, 5, 1); E(adds_imm8, 1, 1); E(mov_reg, 0, 4); E(bl, "c_sdsetnib")
        E(mov_reg, 0, 4); E(bl, "c_sdmark")
        E(bl, "c_vsave")
        a.label("pd_x"); E(pop_list, [4, 5, 6, 7], pc=True)
    else:
        a.label("c_sdpad")
        E(push_list, [4, 5, 6, 7], lr=True)
        E(mov_reg, 4, 0); E(mov_reg, 5, 1)
        E(cmp_imm, 5, 16); bc("pd_d", "hs")
        E(bl, "c_sdconv")
        E(mov_reg, 0, 5); E(bl, "c_sdhalf"); E(mov_reg, 5, 0)
        E(bl, L["c_shift"]); E(cmp_imm, 0, 0); bc("pd_t", "ne")
        if RTREC: E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_sdrtrec")                 # recording: the note goes into the step that plays
        E(bl, "c_sdaoff")                                                                 # audition: the step counts for the pitch row while its pad is held
        E(bl, L["c_gfst"]); E(cmp_imm, 0, 0); bc("pd_x", "eq")
        E(lsls_imm, 1, 4, 6); E(adds_reg, 1, 1, 5); E(adds_imm8, 1, 1); E(strb_w, 1, 0, SD_AUD)
        E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_sdpvel"); E(cmp_imm, 0, 0); E(b_cond, "pd_v", "ne"); E(movs_imm, 0, 100)
        if KEEPNOTE:
            a.label("pd_v"); E(mov_reg, 6, 0); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_sdnnote"); E(mov_reg, 3, 0)
            E(mov_reg, 2, 6); E(mov_reg, 0, 4); E(movs_imm, 1, 1); E(bl, "c_sdio")
        else:
            a.label("pd_v"); E(mov_reg, 2, 0); E(mov_reg, 0, 4); E(movs_imm, 1, 1); E(bl, "c_sdio")
        E(b, "pd_x")
        a.label("pd_t")                                                                   # Shift: the note of the step on / off
        if KEEPNOTE: E(bl, "c_sdaoff")                                                    # a held audition ends first (its note-off must find the note it played)
        E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_sdnvel"); E(mov_reg, 6, 0)
        E(mov_reg, 0, 4); E(bl, "c_sdpat"); E(mov_reg, 1, 5); E(bl, "c_sdstp"); E(mov_reg, 7, 0)
        E(ldrb_imm, 1, 7, 0); E(movs_imm, 2, 1); E(tst_reg, 1, 2); E(b_cond, "pd_a", "eq")
        E(mov_reg, 0, 7); E(bl, "c_sdnone"); E(b, "pd_x")
        a.label("pd_a")
        if KEEPNOTE: E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_sdnnote"); E(mov_reg, 2, 0)
        E(mov_reg, 0, 7); E(mov_reg, 1, 6); E(bl, "c_sdnote"); E(b, "pd_x")
        a.label("pd_d")                                                                   # a destination pad (bit 0 of the nibble is kept)
        E(mov_reg, 0, 4); E(bl, "c_sdmark")
        E(mov_reg, 0, 4); E(bl, "c_sdnib"); E(movs_imm, 1, 1); E(ands_reg, 0, 1)
        E(subs_imm8, 5, 16); E(lsls_imm, 1, 5, 1); E(orrs_reg, 1, 0); E(mov_reg, 0, 4); E(bl, "c_sdsetnib")
        E(mov_reg, 0, 4); E(bl, "c_sdmark")
        E(bl, "c_vsave")
        a.label("pd_x"); E(pop_list, [4, 5, 6, 7], pc=True)

        if RTREC:
            # ---- c_sdrtrec(r0 = track, r1 = the step of the pad): while recording, one note (the pad's note and velocity, as its audition) into the step that plays,
            #      with the micro step of the moment; the step keeps one note (c_sdnote replaces it); clobbers r0-r3
            a.label("c_sdrtrec")
            E(push_list, [4, 5, 6, 7], lr=True)
            E(mov_reg, 4, 0); E(mov_reg, 5, 1)
            for k, want in ((0, "ne"), (1, "ne"), (2, "eq")):                              # the stock recorder gate's test: playing, recording, not the count-in
                E(movw, 0, PLAY_STORE & 0xFFFF); E(movt, 0, PLAY_STORE >> 16); E(movs_imm, 1, k); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
                E(cmp_imm, 0, 0); bc("rt_x", "eq" if want == "ne" else "ne")
            E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_sdpvel"); E(cmp_imm, 0, 0); E(b_cond, "rt_v", "ne"); E(movs_imm, 0, 100)
            a.label("rt_v"); E(mov_reg, 6, 0)                                              # r6 = velocity
            E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_sdnnote"); E(mov_reg, 7, 0)       # r7 = note
            E(mov_reg, 0, 4); E(movs_imm, 1, 1); E(bl, "c_sdeng"); E(ldrb_imm, 5, 0, 0); E(movs_imm, 1, 31); E(ands_reg, 5, 1)   # the step that plays
            E(mov_reg, 0, 4); E(bl, "c_sdpat"); E(mov_reg, 1, 5); E(bl, "c_sdstp"); E(mov_reg, 5, 0)                           # r5 = its record
            E(mov_reg, 0, 5); E(mov_reg, 1, 6); E(mov_reg, 2, 7); E(bl, "c_sdnote")
            E(mov_reg, 0, 4); E(movs_imm, 1, 2); E(bl, "c_sdeng"); E(ldrb_imm, 6, 0, 0)    # r6 = the tick in the step
            E(mov_reg, 0, 4); E(bl, "c_sdpat"); E(movw, 1, 0x382); E(ldrb_reg, 1, 0, 1); E(movs_imm, 2, 7); E(ands_reg, 1, 2)
            E(lsls_imm, 1, 1, 2); E(movw, 2, TPS_TAB & 0xFFFF); E(movt, 2, TPS_TAB >> 16); E(adds_reg, 2, 2, 1); E(ldr_imm, 1, 2, 0)   # ticks per step
            E(movs_imm, 2, 6); E(muls, 6, 2); E(raw, h(0xFBB6) + h(0xF6F1))                # udiv r6, r6, r1
            E(cmp_imm, 6, 5); E(b_cond, "rt_m", "ls"); E(movs_imm, 6, 5)
            a.label("rt_m"); E(strb_imm, 6, 5, 6)                                          # the micro step of the note
            a.label("rt_x"); E(pop_list, [4, 5, 6, 7], pc=True)

        # ---- c_sdtog2(r0 = a synth track 2 / 3): pad 30 of the source view: the step-drummer view open / closed
        a.label("c_sdtog2")
        E(push_list, [4], lr=True)
        E(mov_reg, 4, 0); E(bl, "c_sdaoff")
        E(movs_imm, 0, F_SDOPEN); E(bl, "c_sdflag"); E(cmp_imm, 0, 0); E(b_cond, "t2_o", "eq")
        E(movs_imm, 0, F_SDOPEN); E(movs_imm, 1, 0); E(bl, "c_sdfset"); E(pop_list, [4], pc=True)
        a.label("t2_o")
        E(movs_imm, 0, F_SDOPEN); E(movs_imm, 1, 1); E(bl, "c_sdfset")
        E(mov_reg, 0, 4); E(bl, "c_sdconv")
        E(pop_list, [4], pc=True)

        # ---- the Preset view of the synths (slots 0 / 1 / 7), in front of the source view of SC19.1: with the source view open pad 30 = the step-drummer, and with its view open the rows 1-3 are its pads
        a.label("c_sxtrk")                                                            # r0 = a synth Preset view -> r0 = 2 / 3 when the source view of that synth is open, else 0xFF
        E(push_list, [4], lr=True)
        E(mov_reg, 4, 0); E(bl, L["c_gst"]); E(cmp_imm, 0, 0); bc("xt_n", "eq")
        E(ldrb_imm, 0, 0, S_PAINT); E(movs_imm, 1, F_SRC); E(tst_reg, 0, 1); bc("xt_n", "eq")
        E(mov_reg, 0, 4); E(bl, L["c_synth"]); E(cmp_imm, 0, 1); bc("xt_n", "hi")
        E(adds_imm8, 0, 2); E(pop_list, [4], pc=True)
        a.label("xt_n"); E(movs_imm, 0, 0xFF); E(pop_list, [4], pc=True)

        a.label("c_sxpad")
        E(push_list, [4, 5, 6, 7], lr=True)
        E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
        E(bl, "c_sxtrk"); E(mov_reg, 7, 0); E(cmp_imm, 7, 0xFF); bc("xq_s", "eq")
        E(cmp_imm, 5, PAD_SD); E(b_cond, "xq_n", "ne")
        E(mov_reg, 0, 7); E(bl, "c_sdtog2"); E(pop_list, [4, 5, 6, 7], pc=True)
        a.label("xq_n")
        E(cmp_imm, 5, 24); bc("xq_s", "hs")
        E(mov_reg, 0, 7); E(bl, "c_sdopen"); E(cmp_imm, 0, 0); bc("xq_s", "eq")
        E(mov_reg, 0, 7); E(mov_reg, 1, 5); E(bl, "c_sdpad"); E(pop_list, [4, 5, 6, 7], pc=True)
        a.label("xq_s")
        E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(mov_reg, 2, 6); E(raw, popw([4, 5, 6, 7], lr=True)); E(b_w, L["sx_pad"])

        a.label("c_sxrel")
        E(push_list, [0, 1, 2, 3], lr=True); E(bl, "c_sdaoff"); E(raw, popw([0, 1, 2, 3], lr=True)); E(b_w, L["sx_rel"])

        a.label("c_sxleds")
        E(push_list, [4, 5], lr=True)
        E(mov_reg, 4, 0); E(bl, L["sx_leds"]); E(mov_reg, 5, 0)
        E(mov_reg, 0, 4); E(bl, "c_sxtrk"); E(cmp_imm, 0, 0xFF); E(b_cond, "xl_x", "eq")
        E(mov_reg, 1, 5); E(bl, "c_sdleds")
        a.label("xl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5], pc=True)

        # ---- c_sdpanel(r0 = the controller, r1 = the 69 LED codes of the frame): with a step-drummer view on the screen Octave v / ^ (LEDs 51 / 52) show the knob page and 1-16 / 17-32 (LED 53) the half
        a.label("c_sdpanel")
        E(push_list, [4, 5], lr=True)
        E(mov_reg, 5, 1); E(bl, "c_sdscr"); E(cmp_imm, 0, 0xFF); E(b_cond, "pn_x", "eq")
        E(mov_reg, 4, 0); E(bl, "c_edact"); E(cmp_imm, 0, 0); E(b_cond, "pn_x", "ne")
        E(movs_imm, 0, F_SDPAGE); E(bl, "c_sdflag")
        E(movs_imm, 2, COL_SD[0]); E(movs_imm, 3, COL_SD[1]); E(cmp_imm, 0, 0); E(b_cond, "pn_p", "eq"); E(movs_imm, 2, COL_SD[1]); E(movs_imm, 3, COL_SD[0])
        a.label("pn_p")                                                                   # r2 = Octave ^ (the pitch page), r3 = Octave v (the velocity page)
        E(movw, 1, 2 * 52); E(strh_reg, 2, 5, 1); E(movw, 1, 2 * 51); E(strh_reg, 3, 5, 1)
        E(movs_imm, 0, F_SDHALF); E(bl, "c_sdflag"); E(movs_imm, 2, COL_SD[1]); E(cmp_imm, 0, 0); E(b_cond, "pn_h", "eq"); E(movs_imm, 2, COL_SD[0])
        a.label("pn_h"); E(movw, 1, 2 * 53); E(strh_reg, 2, 5, 1)
        a.label("pn_x"); E(pop_list, [4, 5], pc=True)


    # ---- c_sdtog(r0 = track): pad 30: open / close the view (the first time: enable, and the notes become the tonic); Shift = disable
    a.label("c_sdtog")
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0); E(bl, "c_von"); E(cmp_imm, 0, 0); bc("tg_x", "eq")
    E(bl, "c_sdaoff")
    E(mov_reg, 0, 4); E(bl, "c_sdnib"); E(mov_reg, 5, 0)
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "tg_n", "eq")
    E(mov_reg, 0, 4); E(bl, "c_sdmark")                                                # the destination goes to the DSP again (as the plain value: the bit is cleared before it is sent)
    E(movs_imm, 1, 1); E(bics_reg, 5, 1); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_sdsetnib")
    E(b, "tg_s")
    a.label("tg_n")
    E(movs_imm, 1, 1); E(tst_reg, 5, 1); E(b_cond, "tg_e", "eq")
    E(movs_imm, 0, F_SDOPEN); E(bl, "c_sdflag"); E(cmp_imm, 0, 0); E(b_cond, "tg_o", "eq")
    E(movs_imm, 0, F_SDOPEN); E(movs_imm, 1, 0); E(bl, "c_sdfset"); E(b, "tg_x")       # open -> closed (still enabled)
    a.label("tg_e"); E(movs_imm, 1, 1); E(orrs_reg, 5, 1); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_sdsetnib")
    a.label("tg_o")
    E(movs_imm, 0, F_SDOPEN); E(movs_imm, 1, 1); E(bl, "c_sdfset")
    E(mov_reg, 0, 4); E(bl, "c_sdconv")
    E(mov_reg, 0, 4); E(bl, "c_sdmark")
    a.label("tg_s"); E(bl, "c_vsave")
    a.label("tg_x"); E(pop_list, [4, 5], pc=True)

    # ---- c_sdrel(view, pad): slot 1 of the template view (a stock no-op): a pad is released: the audition ends
    a.label("c_sdrel")
    E(push_list, [4], lr=True); E(bl, "c_sdaoff"); E(pop_list, [4], pc=True)

    # ---- c_sdbtn(r0 = track, r1 = button id 19 / 20 / 21): Octave v = the velocity page, Octave ^ = the pitch page, 1-16 / 17-32 = the other half
    a.label("c_sdbtn")
    E(push_list, [4], lr=True)
    E(cmp_imm, 1, 21); E(b_cond, "bt_h", "eq")
    E(movs_imm, 0, F_SDPAGE); E(cmp_imm, 1, 19); E(b_cond, "bt_p", "eq"); E(movs_imm, 1, 0); E(bl, "c_sdfset"); E(pop_list, [4], pc=True)
    a.label("bt_p"); E(movs_imm, 1, 1); E(bl, "c_sdfset"); E(pop_list, [4], pc=True)
    a.label("bt_h"); E(movs_imm, 0, F_SDHALF); E(movs_imm, 1, 2); E(bl, "c_sdfset"); E(pop_list, [4], pc=True)

    if not SD2:
        # ---- c_sdkleds(r0 = track, r1 = the LED buffer of the 8 knobs): the pairs: the pitch value in the colour of the destination, or the velocity in the colour of the track
        a.label("c_sdkleds")
        E(raw, pushw([4, 5, 6, 7, 8], lr=True))
        E(mov_reg, 4, 0); E(mov_reg, 5, 1)
        E(movs_imm, 0, F_SDPAGE); E(bl, "c_sdflag"); E(mov_reg, 8, 0)
        E(movs_imm, 6, 0)
        a.label("kl_l")
        E(lsls_imm, 0, 6, 1); E(bl, "c_sdhalf"); E(mov_reg, 7, 0)
        E(mov_reg, 0, 8); E(cmp_imm, 0, 0); E(b_cond, "kl_v", "ne")
        E(mov_reg, 0, 4); E(bl, "c_sdpat"); E(mov_reg, 1, 7); E(bl, "c_sdlna"); E(ldrb_imm, 7, 0, 0)
        E(cmp_imm, 7, 127); E(b_cond, "kl_p", "ls"); E(movs_imm, 7, 64)
        a.label("kl_p")
        E(mov_reg, 0, 4); E(bl, "c_sdnib"); E(lsrs_imm, 0, 0, 1); E(adds_imm8, 0, 8); E(movw, 3, t_sd & 0xFFFF); E(movt, 3, t_sd >> 16); E(ldrb_reg, 0, 3, 0)
        E(b, "kl_w")
        a.label("kl_v")
        E(mov_reg, 0, 4); E(mov_reg, 1, 7); E(bl, "c_sdpvel"); E(mov_reg, 7, 0)
        E(movs_imm, 0, COL_TRACK[0]); E(cmp_imm, 4, 0); E(b_cond, "kl_w", "eq"); E(movs_imm, 0, COL_TRACK[1])
        a.label("kl_w")                                                                   # r0 = colour, r7 = value 0..127
        E(adds_imm8, 7, 2); E(lsls_imm, 7, 7, 8); E(orrs_reg, 0, 7); E(lsls_imm, 1, 6, 1); E(strh_reg, 0, 5, 1)
        E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); bc("kl_l", "lo")
        E(raw, popw([4, 5, 6, 7, 8])); E(raw, h(0xBD00))
    else:
        a.label("c_sdkleds")
        E(raw, pushw([4, 5, 6, 7, 8, 9], lr=True))
        E(mov_reg, 4, 0); E(mov_reg, 5, 1)
        E(movs_imm, 0, F_SDPAGE); E(bl, "c_sdflag"); E(mov_reg, 8, 0)
        # the pair that plays (only while the transport runs), as a knob of the half shown (else 0xFF)
        E(movs_imm, 6, 0xFF)
        E(movw, 0, PLAY_STORE & 0xFFFF); E(movt, 0, PLAY_STORE >> 16); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "kl_h", "eq")
        E(mov_reg, 0, 4); E(movs_imm, 1, 1); E(bl, "c_sdeng"); E(ldrb_imm, 6, 0, 0); E(movs_imm, 1, 31); E(ands_reg, 6, 1)
        E(movs_imm, 0, 0); E(bl, "c_sdhalf"); E(subs_reg, 6, 6, 0); E(cmp_imm, 6, 15); E(b_cond, "kl_g", "ls"); E(movs_imm, 6, 0xFF); E(b, "kl_h")
        a.label("kl_g"); E(lsrs_imm, 6, 6, 1)
        a.label("kl_h"); E(mov_reg, 9, 6)
        E(movs_imm, 6, 0)
        a.label("kl_l")
        E(cmp_reg, 6, 9); E(b_cond, "kl_n", "ne")
        E(movw, 0, SD_HEAD | (127 + 2) << 8); E(b, "kl_s")                                 # the pair that plays: white
        a.label("kl_n")
        E(lsls_imm, 0, 6, 1); E(bl, "c_sdhalf"); E(mov_reg, 7, 0)
        E(mov_reg, 0, 8); E(cmp_imm, 0, 0); E(b_cond, "kl_v", "ne")
        E(mov_reg, 0, 4); E(bl, "c_sdpat"); E(mov_reg, 1, 7); E(bl, "c_sdlna"); E(mov_reg, 7, 0)
        E(mov_reg, 0, 4); E(bl, "c_sdlofs"); E(adds_reg, 7, 7, 0); E(ldrb_imm, 7, 7, 0)
        if FXSEQ3:                                                                # the FX sequencer: the colour of the slot of the nearest value, full brightness (0 / empty = dark)
            E(mov_reg, 0, 4); E(bl, "c_fsq"); E(cmp_imm, 0, 0); E(b_cond, "kl_nf", "eq")
            E(movs_imm, 0, 0); E(cmp_imm, 7, FSQ_MAX); E(b_cond, "kl_s", "hi"); E(adds_imm8, 7, FSQ_U // 2); E(lsrs_imm, 7, 7, FSQ_U.bit_length() - 1)
            E(cmp_imm, 7, 0); E(b_cond, "kl_s", "eq")
            E(subs_imm8, 7, 1)
            if FSQRAND: E(movs_imm, 0, 0x01); E(cmp_imm, 7, 6); E(b_cond, "kl_rw", "eq")                       # random: white
            E(mov_reg, 0, 7); E(bl, L["c_slotcol"])
            if FSQRAND: a.label("kl_rw")
            E(movs_imm, 7, 127); E(b, "kl_w")
            a.label("kl_nf")
        E(cmp_imm, 7, 127); E(b_cond, "kl_p", "ls"); E(mov_reg, 0, 4); E(bl, "c_sdbase"); E(mov_reg, 7, 0)
        a.label("kl_p")
        if FXSEQ2 and not FXSEQ3:                                                                # the FX sequencer: the colour of the slot, full brightness (0 = dark)
            E(mov_reg, 0, 4); E(bl, "c_fsq"); E(cmp_imm, 0, 0); E(b_cond, "kl_nf", "eq")
            E(movs_imm, 0, 0); E(cmp_imm, 7, 0); E(b_cond, "kl_s", "eq"); E(cmp_imm, 7, 6); E(b_cond, "kl_s", "hi")
            E(subs_imm8, 7, 1); E(mov_reg, 0, 7); E(bl, L["c_slotcol"]); E(movs_imm, 7, 127); E(b, "kl_w")
            a.label("kl_nf")
        E(mov_reg, 0, 4); E(bl, "c_sdnib"); E(lsrs_imm, 0, 0, 1); E(adds_imm8, 0, 8); E(movw, 3, t_sd & 0xFFFF); E(movt, 3, t_sd >> 16); E(ldrb_reg, 0, 3, 0)
        E(b, "kl_w")
        a.label("kl_v")
        E(mov_reg, 0, 4); E(mov_reg, 1, 7); E(bl, "c_sdpvel"); E(mov_reg, 7, 0)
        E(movs_imm, 0, COL_TRACK[0]); E(cmp_imm, 4, 0); E(b_cond, "kl_w", "eq"); E(movs_imm, 0, COL_TRACK[1])
        E(cmp_imm, 4, 1); E(b_cond, "kl_w", "eq"); E(movs_imm, 0, 0x32); E(cmp_imm, 4, 2); E(b_cond, "kl_w", "eq"); E(movs_imm, 0, 0x17)   # (the colours of Synth 1 / Synth 2)
        a.label("kl_w")                                                                   # r0 = colour, r7 = value 0..127
        E(adds_imm8, 7, 2); E(lsls_imm, 7, 7, 8); E(orrs_reg, 0, 7)
        a.label("kl_s"); E(lsls_imm, 1, 6, 1); E(strh_reg, 0, 5, 1)
        E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); bc("kl_l", "lo")
        E(raw, popw([4, 5, 6, 7, 8, 9])); E(raw, h(0xBD00))


    # ---- c_sdleds(r0 = track, r1 = the pad LED buffer of the Preset view): pad 30; with the view open the steps (pads 1-16) and the destinations (pads 17-24)
    a.label("c_sdleds")
    E(raw, pushw([4, 5, 6, 7, 8], lr=True))
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_edact"); E(cmp_imm, 0, 0); bc("sl_x", "ne")                               # the CC editor draws its numbers with all the pads: nothing of ours
    if VADRUM:                                                                    # pad 31 of a MIDI track: lit only in the VA-drum state
        E(cmp_imm, 4, 2); E(b_cond, "sl_nv", "hs")
        E(movs_imm, 6, 0)
        E(mov_reg, 0, 4); E(bl, "c_von"); E(cmp_imm, 0, 0); E(b_cond, "sl_wv", "eq")
        E(mov_reg, 0, 4); E(bl, "c_vdbit"); E(cmp_imm, 0, 0); E(b_cond, "sl_wv", "eq")
        E(mov_reg, 0, 4); E(adds_imm8, 0, 2); E(bl, "c_vdbit"); E(movs_imm, 6, COL_VEL[1]); E(cmp_imm, 0, 0); E(b_cond, "sl_wv", "eq"); E(movs_imm, 6, COL_VEL[0])
        a.label("sl_wv"); E(strh_imm, 6, 5, 2 * PAD_VEL)
        a.label("sl_nv")
    E(mov_reg, 0, 4); E(bl, "c_sden"); E(movs_imm, 1, 0); E(cmp_imm, 0, 0); E(b_cond, "sl_p", "eq")
    E(movs_imm, 0, F_SDOPEN); E(bl, "c_sdflag"); E(movs_imm, 1, COL_SD[1]); E(cmp_imm, 0, 0); E(b_cond, "sl_p", "eq"); E(movs_imm, 1, COL_SD[0])
    a.label("sl_p"); E(strh_imm, 1, 5, 2 * PAD_SD)
    if SD2:
        E(cmp_imm, 1, COL_SD[0]); E(b_cond, "sl_op", "eq")
        E(movs_imm, 0, 0)
        for k in range(8, 24): E(strh_imm, 0, 5, 2 * k)                               # closed: the pads 9-24 dark (the steps of the second row and the destinations stayed lit)
        E(b, "sl_x")
        a.label("sl_op")
    else:
        E(cmp_imm, 1, COL_SD[0]); bc("sl_x", "ne")
    # the step that sounds (only while the transport runs), as an index into the half shown (else 0xFF)
    E(movs_imm, 7, 0xFF)
    E(movw, 0, PLAY_STORE & 0xFFFF); E(movt, 0, PLAY_STORE >> 16); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "sl_h", "eq")
    E(mov_reg, 0, 4); E(movs_imm, 1, 1); E(bl, "c_sdeng"); E(ldrb_imm, 7, 0, 0); E(movs_imm, 1, 31); E(ands_reg, 7, 1)
    a.label("sl_h"); E(mov_reg, 8, 7)
    E(movs_imm, 0, 0); E(bl, "c_sdhalf"); E(mov_reg, 7, 0)                             # r7 = the first step shown
    E(mov_reg, 0, 4); E(bl, "c_sdpat"); E(mov_reg, 1, 7); E(bl, "c_sdstp"); E(mov_reg, 6, 0)   # r6 = its record
    E(mov_reg, 0, 8); E(subs_reg, 0, 0, 7); E(mov_reg, 8, 0)                           # r8 = the pad of the step that sounds (anything else = none)
    E(movs_imm, 7, 0)
    a.label("sl_l")
    E(ldrb_imm, 0, 6, 0); E(movs_imm, 1, 1); E(ands_reg, 0, 1)                         # r0 = 1 with a note
    E(lsrs_imm, 2, 7, 1); E(ands_reg, 2, 1)                                            # r2 = the pair is odd
    E(movs_imm, 3, SD_STEPCOL[0][1]); E(cmp_imm, 2, 0); E(b_cond, "sl_c", "eq"); E(movs_imm, 3, SD_STEPCOL[1][1])
    a.label("sl_c"); E(subs_reg, 3, 3, 0)                                              # the bright code is the dim one - 1
    E(cmp_reg, 7, 8); E(b_cond, "sl_w", "ne"); E(movs_imm, 3, SD_HEAD)
    a.label("sl_w"); E(lsls_imm, 1, 7, 1); E(strh_reg, 3, 5, 1)
    E(adds_imm8, 6, 28); E(adds_imm8, 7, 1); E(cmp_imm, 7, 16); bc("sl_l", "lo")
    E(mov_reg, 0, 4); E(bl, "c_sdnib"); E(lsrs_imm, 6, 0, 1)                           # r6 = the destination
    E(movs_imm, 7, 0)
    a.label("sl_d")
    E(mov_reg, 0, 7); E(adds_imm8, 0, 8); E(movw, 3, t_sd & 0xFFFF); E(movt, 3, t_sd >> 16); E(ldrb_reg, 0, 3, 0)
    E(cmp_reg, 7, 6); E(b_cond, "sl_e", "eq")
    E(cmp_imm, 0, 0x32); E(b_cond, "sl_m", "ne"); E(movs_imm, 0, 0x36)                 # the dim magenta is 0x37
    a.label("sl_m"); E(adds_imm8, 0, 1)
    a.label("sl_e"); E(mov_reg, 1, 7); E(adds_imm8, 1, 16); E(lsls_imm, 1, 1, 1); E(strh_reg, 0, 5, 1)
    E(adds_imm8, 7, 1); E(cmp_imm, 7, 8); E(b_cond, "sl_d", "lo")
    a.label("sl_x"); E(raw, popw([4, 5, 6, 7, 8])); E(raw, h(0xBD00))


def ccio_routines(a, tail, bc, movmask, t_cc, t_ln, stk_emit, stk_mid):
    """SC25 (CCIO): MIDI CC / NRPN out and in and the automation lanes.  c_vsync(track, code, value) = a knob turn: the value goes out as CC / NRPN and is recorded in its lane (if it has one);
    c_vplay = the cave of the stock macro sender (the sequencer plays the lanes through it); c_vmin = the cave of the CC section of the stock MIDI-in function (CC / NRPN in on the channel of the track).
    t_cc = the table code -> (type, number), t_ln = lane -> code; stk_emit / stk_mid = the 4 stock bytes the caves displace."""
    from thumb import add_sp_imm
    E = a.emit

    a.label("c_vchan")                                                            # r0 = track 0 / 1 -> r0 = its MIDI channel (the stock channel table, index = track id); clobbers r1
    E(movw, 1, TXOBJ & 0xFFFF); E(movt, 1, TXOBJ >> 16)
    E(ldr_imm, 1, 1, 0x0C); E(adds_imm8, 0, 2); E(ldrb_reg, 0, 1, 0); E(raw, h(0x4770))

    a.label("c_vsndr")                                                            # r0 = a macro sender -> r0 = 0 / 1 (the sender of MIDI 1 / MIDI 2: G + 0x110 / G + 0x158, G = [SETOBJ - 8]) or 0xFF; clobbers r1, r2
    E(movw, 1, (SETOBJ - 8) & 0xFFFF); E(movt, 1, (SETOBJ - 8) >> 16); E(ldr_imm, 1, 1, 0); E(cmp_imm, 1, 0); E(b_cond, "sn_no", "eq")
    E(movw, 2, 0x110); E(adds_reg, 2, 2, 1); E(cmp_reg, 0, 2); E(b_cond, "sn_0", "eq")
    E(movw, 2, 0x158); E(adds_reg, 2, 2, 1); E(cmp_reg, 0, 2); E(b_cond, "sn_1", "eq")
    a.label("sn_no"); E(movs_imm, 0, 0xFF); E(raw, h(0x4770))
    a.label("sn_0"); E(movs_imm, 0, 0); E(raw, h(0x4770))
    a.label("sn_1"); E(movs_imm, 0, 1); E(raw, h(0x4770))

    a.label("c_vtou")                                                             # r0 = code, r1 = value (signed) -> r0 = 0..127 (bipolar values + 64); clobbers r1-r3
    movmask(2); E(mov_reg, 3, 0); E(subs_imm8, 3, 1); E(lsrs_reg, 2, 3); E(movs_imm, 3, 1); E(ands_reg, 2, 3); E(cmp_imm, 2, 0); E(b_cond, "tu_u", "eq"); E(adds_imm8, 1, 64)
    a.label("tu_u"); E(cmp_imm, 1, 0); E(b_cond, "tu_a", "ge"); E(movs_imm, 1, 0)
    a.label("tu_a"); E(cmp_imm, 1, 127); E(b_cond, "tu_b", "le"); E(movs_imm, 1, 127)
    a.label("tu_b"); E(mov_reg, 0, 1); E(raw, h(0x4770))

    a.label("c_vfromu")                                                           # r0 = code, r1 = value 0..127 -> r0 = the stored value (bipolar - 64; the two PW codes at most 100); clobbers r1-r3
    E(mov_reg, 2, 0); movmask(0); E(mov_reg, 3, 2); E(subs_imm8, 3, 1); E(lsrs_reg, 0, 3); E(movs_imm, 3, 1); E(ands_reg, 0, 3)
    E(cmp_imm, 0, 0); E(b_cond, "fu_u", "eq"); E(subs_imm8, 1, 64); E(b, "fu_x")
    a.label("fu_u"); E(cmp_imm, 2, 20); E(b_cond, "fu_p", "eq"); E(cmp_imm, 2, 30); E(b_cond, "fu_x", "ne")
    a.label("fu_p"); E(cmp_imm, 1, 100); E(b_cond, "fu_x", "le"); E(movs_imm, 1, 100)
    a.label("fu_x"); E(mov_reg, 0, 1); E(raw, h(0x4770))

    a.label("c_vrev")                                                             # r0 = type, r1 = number -> r0 = the code (1..34) with that entry in the table, or 0; clobbers r2, r3
    E(push_list, [4])
    E(movw, 2, t_cc & 0xFFFF); E(movt, 2, t_cc >> 16); E(movs_imm, 3, 0)
    a.label("rv_l"); E(ldrb_imm, 4, 2, 0); E(cmp_reg, 4, 0); E(b_cond, "rv_n", "ne"); E(ldrb_imm, 4, 2, 1); E(cmp_reg, 4, 1); E(b_cond, "rv_f", "eq")
    a.label("rv_n"); E(adds_imm8, 2, 2); E(adds_imm8, 3, 1); E(cmp_imm, 3, 34); E(b_cond, "rv_l", "lo")
    E(movs_imm, 0, 0); E(pop_list, [4]); E(raw, h(0x4770))
    a.label("rv_f"); E(adds_imm8, 3, 1); E(mov_reg, 0, 3); E(pop_list, [4]); E(raw, h(0x4770))

    a.label("c_vcc_emit")                                                         # r0 = track, r1 = code, r2 = value (signed): the CC (or the NRPN: 99, 98, 6) of the code on the channel of the track; clobbers r0-r3
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(mov_reg, 0, 5); E(mov_reg, 1, 2); E(bl, "c_vtou"); E(mov_reg, 6, 0)          # r6 = the value on the wire 0..127
    E(subs_imm8, 5, 1); E(lsls_imm, 5, 5, 1); E(movw, 3, t_cc & 0xFFFF); E(movt, 3, t_cc >> 16); E(adds_reg, 3, 3, 5)
    E(ldrb_imm, 7, 3, 0); E(ldrb_imm, 5, 3, 1)                                    # r7 = type, r5 = number
    E(cmp_imm, 7, 0xFF); E(b_cond, "ce_x", "eq")
    E(mov_reg, 0, 4); E(bl, "c_vchan"); E(mov_reg, 4, 0)                          # r4 = the channel
    E(cmp_imm, 7, 0x80); E(b_cond, "ce_n", "hs")
    E(mov_reg, 0, 4); E(movs_imm, 1, 0xB0); E(mov_reg, 2, 5); E(mov_reg, 3, 6); E(bl, CC_HELPER); E(b, "ce_x")
    a.label("ce_n")
    E(movs_imm, 0, 0x7F); E(ands_reg, 7, 0)
    E(mov_reg, 0, 4); E(movs_imm, 1, 0xB0); E(movs_imm, 2, 99); E(mov_reg, 3, 7); E(bl, CC_HELPER)
    E(mov_reg, 0, 4); E(movs_imm, 1, 0xB0); E(movs_imm, 2, 98); E(mov_reg, 3, 5); E(bl, CC_HELPER)
    E(mov_reg, 0, 4); E(movs_imm, 1, 0xB0); E(movs_imm, 2, 6); E(mov_reg, 3, 6); E(bl, CC_HELPER)
    a.label("ce_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    a.label("c_vcc_rec")                                                          # r0 = track, r1 = code, r2 = value (signed): record it in its lane (the stock automation gate: nothing unless the unit records)
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(movw, 3, t_ln & 0xFFFF); E(movt, 3, t_ln >> 16); E(movs_imm, 7, 0)
    a.label("cr_l"); E(ldrb_reg, 0, 3, 7); E(cmp_reg, 0, 5); E(b_cond, "cr_f", "eq"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 8); E(b_cond, "cr_l", "lo"); E(b, "cr_x")
    a.label("cr_f")
    if SDRUM:
        E(cmp_imm, 7, 0); E(b_cond, "cr_g", "ne"); E(mov_reg, 0, 4); E(bl, "c_sden"); E(cmp_imm, 0, 0); E(b_cond, "cr_x", "ne")
        a.label("cr_g")
    E(mov_reg, 0, 5); E(mov_reg, 1, 6); E(bl, "c_vtou"); E(mov_reg, 6, 0)
    E(movs_imm, 1, 20); E(cmp_imm, 4, 0); E(b_cond, "cr_i", "eq"); E(movs_imm, 1, 30)
    a.label("cr_i"); E(adds_reg, 1, 1, 7); E(mov_reg, 2, 6)
    E(movw, 0, REC_GATE_OBJ & 0xFFFF); E(movt, 0, REC_GATE_OBJ >> 16); E(bl, REC_GATE)
    a.label("cr_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    a.label("c_vsync")                                                            # r0 = track, r1 = code, r2 = value (signed): a value changed by a knob: out as MIDI, recorded
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(bl, "c_vcc_emit")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(mov_reg, 2, 6); E(bl, "c_vcc_rec")
    E(pop_list, [4, 5, 6], pc=True)

    a.label("c_vstore")                                                           # r0 = track, r1 = code, r2 = value (signed) -> r0 = 1 when it changed (stored, dirty / sweep cursor set; no save, no MIDI)
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(bl, "c_vvaddr"); E(mov_reg, 7, 0)
    E(raw, ldrsb_w(1, 7, 0)); E(cmp_reg, 1, 6); E(b_cond, "st_no", "eq")
    E(strb_imm, 6, 7, 0)
    E(cmp_imm, 5, 26); E(b_cond, "st_m", "ls")                                    # a volatile value: the sweep goes there next
    tail(2); E(lsls_imm, 3, 4, 3); E(adds_reg, 2, 2, 3); E(ldrb_w, 0, 2, O_RT + RT_CNT); E(movs_imm, 1, 0x70); E(bics_reg, 0, 1)
    E(mov_reg, 1, 5); E(subs_imm8, 1, 27); E(lsls_imm, 1, 1, 4); E(orrs_reg, 0, 1); E(strb_w, 0, 2, O_RT + RT_CNT)
    a.label("st_m"); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_vmark")
    E(movs_imm, 0, 1); E(b, "st_x")
    a.label("st_no"); E(movs_imm, 0, 0)
    a.label("st_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    a.label("c_vapply")                                                           # r0 = track, r1 = lane 0..7, r2 = the lane value 0..127 (the sequencer played it): set the value and send it out
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 2)
    E(movw, 3, t_ln & 0xFFFF); E(movt, 3, t_ln >> 16); E(ldrb_reg, 6, 3, 1)       # r6 = the code of the lane
    E(mov_reg, 0, 6); E(mov_reg, 1, 5); E(bl, "c_vfromu"); E(mov_reg, 7, 0)       # r7 = the stored value
    E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(mov_reg, 2, 7); E(bl, "c_vstore"); E(cmp_imm, 0, 0); E(b_cond, "ap_x", "eq")
    E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(mov_reg, 2, 7); E(bl, "c_vcc_emit")
    a.label("ap_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_vplay: the head of the stock macro sender (this, knob, value; the sequencer calls it with the lane value, a knob of the stock handler with the knob value).  A MIDI track whose mode is on, the transport
    #      running and a knob 0..7: the lane value sets the value of that lane and the stock CC is not sent; everything else runs the stock function
    a.label("c_vplay")
    E(push_list, [0, 1, 2, 3, 4], lr=True)
    E(mov_reg, 4, 0)
    E(movw, 0, PLAY_STORE & 0xFFFF); E(movt, 0, PLAY_STORE >> 16); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); bc("pl_stock", "eq")
    E(mov_reg, 0, 4); E(bl, "c_vsndr"); E(cmp_imm, 0, 0xFF); bc("pl_stock", "eq")
    E(mov_reg, 4, 0); E(bl, "c_von"); E(cmp_imm, 0, 0); bc("pl_stock", "eq")
    E(ldr_sp, 1, 4); E(cmp_imm, 1, 7); bc("pl_stock", "hi")
    if SDRUM:
        E(cmp_imm, 1, 0); E(b_cond, "pl_ap", "ne"); E(mov_reg, 0, 4); E(bl, "c_sden"); E(cmp_imm, 0, 0); E(b_cond, "pl_sw", "ne"); E(ldr_sp, 1, 4)
        a.label("pl_ap")
    E(ldr_sp, 2, 8); E(mov_reg, 0, 4); E(bl, "c_vapply")
    if SDRUM: a.label("pl_sw")
    E(add_sp_imm, 16); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)
    a.label("pl_stock")
    E(raw, popw([0, 1, 2, 3, 4], lr=True)); E(raw, stk_emit); E(b_w, STK_EMIT + 4)

    # ---- c_vin(ctx, msg): a CC message on the channel of a MIDI track whose mode is on (and the Setup CC Rx on, not an internal copy): CC / NRPN -> the value of the code.  The NRPN select CCs are kept in the
    #      stock record of the "other" channels (the stock handler of the CC section ignores the channels of no synth); the stock code runs afterwards for every message
    a.label("c_vin")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 6, 0); E(mov_reg, 5, 1)
    E(ldrb_imm, 2, 5, 0); E(lsrs_imm, 3, 2, 4); E(cmp_imm, 3, 0xB); bc("in_x", "ne")
    E(ldrb_imm, 3, 6, 0x14); E(movs_imm, 4, 0x22); E(ands_reg, 3, 4); E(cmp_imm, 3, 2); bc("in_x", "ne")
    E(movw, 3, MIDI_IN_FLAG & 0xFFFF); E(movt, 3, MIDI_IN_FLAG >> 16); E(ldr_imm, 3, 3, 0); E(lsls_imm, 3, 3, 29); bc("in_x", "mi")
    E(movs_imm, 3, 0x0F); E(ands_reg, 2, 3); E(mov_reg, 7, 2)
    E(movs_imm, 4, 0)
    a.label("in_t")
    E(mov_reg, 0, 4); E(bl, "c_vchan"); E(cmp_reg, 0, 7); E(b_cond, "in_n", "ne")
    E(mov_reg, 0, 4); E(bl, "c_von"); E(cmp_imm, 0, 0); bc("in_go", "ne")
    a.label("in_n"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 2); bc("in_t", "lo"); E(b, "in_x")
    a.label("in_go")
    E(ldr_imm, 3, 6, 0x10); E(adds_imm8, 3, 15)                                    # r3 = the NRPN state of the "other" channels (this + 3 * 5): +0xA LSB, +0xB MSB, +0xC set
    E(ldrb_imm, 1, 5, 1); E(ldrb_imm, 2, 5, 2)
    E(cmp_imm, 1, 99); E(b_cond, "in_a", "ne"); E(strb_imm, 2, 3, 0x0B); E(b, "in_f")
    a.label("in_a"); E(cmp_imm, 1, 98); E(b_cond, "in_b", "ne"); E(strb_imm, 2, 3, 0x0A)
    a.label("in_f"); E(movs_imm, 0, 1); E(strb_imm, 0, 3, 0x0C); E(b, "in_x")
    a.label("in_b"); E(cmp_imm, 1, 6); E(b_cond, "in_cc", "ne")
    E(ldrb_imm, 0, 3, 0x0C); E(cmp_imm, 0, 0); bc("in_x", "eq")
    E(ldrb_imm, 0, 3, 0x0B); E(movs_imm, 1, 0x80); E(orrs_reg, 0, 1); E(ldrb_imm, 1, 3, 0x0A); E(b, "in_look")
    a.label("in_cc"); E(movs_imm, 0, 0)
    a.label("in_look")
    E(mov_reg, 5, 2); E(bl, "c_vrev"); E(cmp_imm, 0, 0); bc("in_x", "eq")
    E(mov_reg, 6, 0)
    E(mov_reg, 0, 6); E(mov_reg, 1, 5); E(bl, "c_vfromu"); E(mov_reg, 2, 0)
    E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(bl, "c_vstore")
    a.label("in_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    a.label("c_vmin")                                                             # the head of the CC section of the stock MIDI-in function (r4 = the receiver, r5 = the message): our code, then the two displaced stock instructions
    E(push_list, [0, 1, 2, 3], lr=True)
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_vin")
    E(raw, popw([0, 1, 2, 3], lr=True)); E(raw, stk_mid); E(b_w, STK_MIDIIN + 4)


def arm_code(base, L):
    """L: c_shift, c_gfst, c_dtick19 (the chain), c_tpad, c_tleds, c_settings (SC06), c_non, c_noff (SC06)."""
    a = Asm(base)
    zc = [0]
    a.label("t_knob")                                                             # 16 bytes of data first (32 with OSC: the page B codes after): its address is `base`
    for i in range(0, 16, 2): a.emit(raw, bytes([KNOB_CODES[i], KNOB_CODES[i + 1]]))
    if OSC:
        for i in range(0, 16, 2): a.emit(raw, bytes([KNOB_CODES_B[i], KNOB_CODES_B[i + 1]]))
    if DUALUI:
        for i in range(0, 16, 2): a.emit(raw, bytes([KNOB_CODES_C[i], KNOB_CODES_C[i + 1]]))
    if PAGES5:
        for tab in (KNOB_CODES_D, KNOB_CODES_E):
            for i in range(0, 16, 2): a.emit(raw, bytes([tab[i], tab[i + 1]]))
    ktab = base + (80 if PAGES5 else 48 if DUALUI else 32 if OSC else 16)
    t_ed = ktab
    if CCED:
        # tables of the editor, right after the knob tables (address = base + 32): KC (kind 1..5 -> class), NF (fields of a class), ROLE[class][6], SHIFT[class][role], ROFF[role], RCOL[role]
        # classes: 0 = CC (CC, start, end), 1 = NRPN / RPN with a 7-bit value (MSB, LSB, start, end), 2 = 14-bit value (MSB, LSB, start MSB, start LSB, end MSB, end LSB)
        tabs = bytes([0, 2, 2, 1, 1,  3, 4, 6,
                      0, 2, 4, 0, 0, 0,   0, 1, 2, 4, 0, 0,   0, 1, 2, 3, 4, 5,
                      0, 0, 0, 0, 0, 0,   7, 0, 0, 0, 0, 0,   7, 0, 7, 0, 7, 0,
                      4, 4, 6, 6, 8, 8,
                      0x32, 0x44, 0x2B, 0x2D, 0x13, 0x4D])
        assert len(tabs) == 56
        for i in range(0, 56, 2): a.emit(raw, tabs[i:i + 2])
    t_def = ktab + (56 if CCED else 0)
    if CLEARK:                                                                    # default value of each code (index = code, 1..26; index 0 unused), signed bytes
        ndef = 36 if DUALUI else 28
        dtab = bytes([0] + [v & 0xFF for v in DEFAULTS] + ([v & 0xFF for v in DEFAULTS_V2] if DUALUI else []) + [0] * (ndef - 1 - len(DEFAULTS) - (len(DEFAULTS_V2) if DUALUI else 0)))
        assert len(dtab) == ndef
        for i in range(0, ndef, 2): a.emit(raw, dtab[i:i + 2])
    t_ft = t_def + ((36 if DUALUI else 28) if CLEARK else 0)
    if EDV2: ed2_tables(a)
    t_tc = t_ft + (170 if EDV2 else 0)
    tcl = 0
    if TYPEZONE:                                                                  # the colours of the modes: FX (7), filter (7), waveform (4), padded to 20 bytes
        tc = bytes(TCOL_FX + TCOL_FT + TCOL_WV + TCOL_BS) + bytes(1) if DUALUI else bytes(TCOL_FX + TCOL_FT + TCOL_WV) + bytes(2)
        for i in range(0, len(tc), 2): a.emit(raw, tc[i:i + 2])
        tcl = len(tc)
    t_cc = t_tc + tcl                                                             # SC25: code -> (type, number) (34 x 2 bytes), then lane -> code (8 bytes)
    t_ln = t_cc + 68
    if CCIO:
        tab = b"".join(bytes(CC_TAB[c]) for c in range(1, 35)) + bytes(LANE_TAB)
        for i in range(0, len(tab), 2): a.emit(raw, tab[i:i + 2])
    t_sd = t_ln + 8                                                               # SC26: the destinations of the pitch row (8 codes), then their colours (8)
    if SDRUM:
        tab = bytes(SD_DEST) + bytes(SD_DCOL)
        for i in range(0, len(tab), 2): a.emit(raw, tab[i:i + 2])
    t_gr = t_sd + (16 if SDRUM else 0)                                            # SC36: GR_TAB, 4 bytes per knob
    if GRAN:
        grt = [(26, 0, 2, 1 | 5 << 1) if STRETCH and c == 26 else (c, lo, hi, f) for c, lo, hi, f in GR_TAB]   # SC38.1: note mode 0 / 1 / 2, LED of three levels
        tab = b"".join(bytes([c, lo & 0xFF, hi & 0xFF, f]) for c, lo, hi, f in grt)
        for i in range(0, len(tab), 2): a.emit(raw, tab[i:i + 2])
    t_st = t_gr + (64 if GRAN else 0)                                             # SC38.1: the stretch lengths (12 bytes)
    if STRETCH:
        for i in range(0, len(ST_STEPS), 2): a.emit(raw, bytes(ST_STEPS[i:i + 2]))
    def mulstride(rd, rt):                                                        # rd = STRIDE * rt (rd != rt), rd = 16 t: the original shift
        if OSC: a.emit(movs_imm, rd, STRIDE); a.emit(muls, rd, rt)
        else: a.emit(lsls_imm, rd, rt, 4)
    def bipolar_bit(rm, rtmp, rcode_minus1):                                       # not used
        pass
    def movmask(rd):
        a.emit(movw, rd, BIPOLAR_MASK & 0xFFFF)
        if BIPOLAR_MASK >> 16: a.emit(movt, rd, BIPOLAR_MASK >> 16)

    def bc(target, cond):
        zc[0] += 1; n = f"_v{zc[0]}"
        a.emit(b_cond, n, INV[cond]); a.emit(b, target); a.label(n)

    def tail(rd):
        a.emit(movw, rd, TAIL & 0xFFFF); a.emit(movt, rd, TAIL >> 16)

    # ---- c_vtrack(r0 = macro handler) -> r0 = 0 / 1 (MIDI 1 / MIDI 2) or 0xFF; clobbers r1, r2
    a.label("c_vtrack")
    a.emit(movw, 1, CTX_PTR & 0xFFFF); a.emit(movt, 1, CTX_PTR >> 16)
    a.emit(ldr_imm, 1, 1, 0); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "vt_no", "eq")
    a.emit(ldr_imm, 1, 1, 0x40); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "vt_no", "eq")
    a.emit(ldr_imm, 1, 1, 0x2C); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "vt_no", "eq")
    a.emit(raw, h(0xF8D1) + h(2 << 12 | (0x148 + 8)))                            # ldr.w r2,[r1,#0x150]  (track 2 = MIDI 1)
    a.emit(cmp_reg, 2, 0); a.emit(b_cond, "vt_0", "eq")
    a.emit(raw, h(0xF8D1) + h(2 << 12 | (0x148 + 12)))                           # ldr.w r2,[r1,#0x154]  (track 3 = MIDI 2)
    a.emit(cmp_reg, 2, 0); a.emit(b_cond, "vt_1", "eq")
    a.label("vt_no"); a.emit(movs_imm, 0, 0xFF); a.emit(raw, h(0x4770))
    a.label("vt_0"); a.emit(movs_imm, 0, 0); a.emit(raw, h(0x4770))
    a.label("vt_1"); a.emit(movs_imm, 0, 1); a.emit(raw, h(0x4770))

    # ---- c_von(r0 = track) -> r0 = 0 / 1; clobbers r1
    a.label("c_von")
    tail(1)
    a.emit(ldrb_w, 1, 1, O_FLAGS); a.emit(lsrs_reg, 1, 0); a.emit(movs_imm, 0, 1); a.emit(ands_reg, 0, 1); a.emit(raw, h(0x4770))

    # ---- c_vlvl(r0 = track, r1 = code 1..16) -> r0 = brightness 0..127; clobbers r1-r3
    a.label("c_vlvl")
    if OSC:                                                                       # code 0 = no function on this page: dark
        a.emit(cmp_imm, 1, 0); a.emit(b_cond, "vl_nz", "ne"); a.emit(movs_imm, 0, 0); a.emit(raw, h(0x4770)); a.label("vl_nz")
    a.emit(push_list, [4], lr=True)
    a.emit(mov_reg, 4, 1)
    if DUALUI: a.emit(bl, "c_vvaddr"); a.emit(raw, ldrsb_w(0, 0, 0))
    else:
        tail(2); mulstride(3, 0); a.emit(adds_reg, 3, 3, 2); a.emit(adds_reg, 3, 3, 1)             # r3 = TAIL + STRIDE t + code  (= +1 + STRIDE t + code - 1)
        a.emit(raw, ldrsb_w(0, 3, 0))
    a.emit(cmp_imm, 4, 13); a.emit(b_cond, "vl_fx" if FXTYPE_N > 4 else "vl_sh", "eq")
    a.emit(cmp_imm, 4, 16); a.emit(b_cond, "vl_ft" if FTYPE_N > 4 else "vl_sh", "eq")
    if OSC and not OSC3: a.emit(cmp_imm, 4, 19); a.emit(b_cond, "vl_sh", "eq")     # WAVE: 4 values like the shapes
    a.emit(movs_imm, 2, 0); movmask(2); a.emit(subs_imm8, 4, 1); a.emit(lsrs_reg, 2, 4); a.emit(movs_imm, 3, 1); a.emit(ands_reg, 2, 3)
    a.emit(cmp_imm, 2, 0); a.emit(b_cond, "vl_uni", "eq")
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vl_bp", "ge"); a.emit(raw, h(0x43C0))                          # mvns r0, r0 : -v - 1
    a.label("vl_bp"); a.emit(lsls_imm, 0, 0, 1); a.emit(cmp_imm, 0, 126); a.emit(b_cond, "vl_x", "ls"); a.emit(movs_imm, 0, 126); a.emit(b, "vl_x")
    a.label("vl_uni")
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vl_x", "ge"); a.emit(movs_imm, 0, 0); a.emit(b, "vl_x")
    a.label("vl_sh")
    a.emit(movs_imm, 1, 3); a.emit(ands_reg, 0, 1); a.emit(movs_imm, 1, 42); a.emit(muls, 0, 1); a.emit(b, "vl_x")
    if FXTYPE_N > 4:
        a.label("vl_fx"); a.emit(movs_imm, 1, 126 // (FXTYPE_N - 1)); a.emit(muls, 0, 1); a.emit(b, "vl_x")
    if FTYPE_N > 4:
        a.label("vl_ft"); a.emit(movs_imm, 1, 126 // (FTYPE_N - 1)); a.emit(muls, 0, 1); a.emit(b, "vl_x")
    a.label("vl_md")
    a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1); a.emit(b_cond, "vl_x", "eq"); a.emit(movs_imm, 0, 127)
    a.label("vl_x")
    a.emit(pop_list, [4], pc=True)

    if TYPEZONE:
        # ---- c_vtype(r0 = track, r1 = code 13 FX type / 16 filter type / 19 WAVE) -> r0 = the LED halfword of the knob: colour of the mode | (brightness of the parameter inside the mode + 2) << 8
        #      FX / filter type: p = 0..127, zone t = 7 p >> 7, parameter f = 7 p & 127; WAVE: the morph m = 0..126, zone t = m / 42 (sine, triangle, saw, square), f = (m mod 42) * 3
        a.label("c_vtype")
        a.emit(push_list, [4], lr=True)
        a.emit(mov_reg, 4, 1)
        if DUALUI: a.emit(bl, "c_vvaddr"); a.emit(raw, ldrsb_w(0, 0, 0))
        else: tail(2); mulstride(3, 0); a.emit(adds_reg, 3, 3, 2); a.emit(adds_reg, 3, 3, 1); a.emit(raw, ldrsb_w(0, 3, 0))
        a.emit(cmp_imm, 4, 19); bc("vy_w", "eq")
        if DUALUI: a.emit(cmp_imm, 4, 29); bc("vy_w", "eq")
        a.emit(movs_imm, 2, 7); a.emit(muls, 0, 2); a.emit(lsrs_imm, 3, 0, 7); a.emit(movs_imm, 2, 127); a.emit(ands_reg, 0, 2)
        if DUALUI:
            a.emit(movs_imm, 2, 0); a.emit(cmp_imm, 4, 13); a.emit(b_cond, "vy_c", "eq"); a.emit(movs_imm, 2, 7); a.emit(cmp_imm, 4, 16); a.emit(b_cond, "vy_c", "eq"); a.emit(movs_imm, 2, 18); a.emit(b, "vy_c")
        else:
            a.emit(movs_imm, 2, 0); a.emit(cmp_imm, 4, 13); a.emit(b_cond, "vy_c", "eq"); a.emit(movs_imm, 2, 7); a.emit(b, "vy_c")
        a.label("vy_w")
        a.emit(movs_imm, 3, 0)
        a.label("vy_l"); a.emit(cmp_imm, 0, 42); a.emit(b_cond, "vy_d", "lo"); a.emit(subs_imm8, 0, 42); a.emit(adds_imm8, 3, 1); a.emit(b, "vy_l")
        a.label("vy_d"); a.emit(movs_imm, 2, 3); a.emit(muls, 0, 2); a.emit(movs_imm, 2, 14)
        a.label("vy_c")
        a.emit(adds_reg, 3, 3, 2)
        a.emit(movw, 1, t_tc & 0xFFFF); a.emit(movt, 1, t_tc >> 16); a.emit(ldrb_reg, 1, 1, 3)                       # r1 = the colour of the mode
        a.emit(movs_imm, 2, 127 - TZ_MINB); a.emit(muls, 0, 2); a.emit(lsrs_imm, 0, 0, 7); a.emit(adds_imm8, 0, TZ_MINB + 2); a.emit(lsls_imm, 0, 0, 8); a.emit(orrs_reg, 0, 1)
        a.emit(pop_list, [4], pc=True)

    # ---- c_vsave: the stock settings save, at most every SAVE_MS (8-bit time in units of 32 ms); clobbers r0-r3
    a.label("c_vsave")
    a.emit(push_list, [4], lr=True)
    a.emit(movw, 0, HAL_TICK & 0xFFFF); a.emit(movt, 0, HAL_TICK >> 16); a.emit(ldr_imm, 0, 0, 0)
    a.emit(lsrs_imm, 0, 0, 5); a.emit(movs_imm, 1, 0xFF); a.emit(ands_reg, 0, 1); a.emit(mov_reg, 4, 0)             # r4 = now (8 bit)
    tail(1); a.emit(ldrb_w, 2, 1, O_SAVED); a.emit(subs_reg, 2, 0, 2); a.emit(movs_imm, 3, 0xFF); a.emit(ands_reg, 2, 3)   # r2 = (now - last) & 0xFF
    a.emit(cmp_imm, 2, SAVE_MS // 32); a.emit(b_cond, "vs_x", "lo")
    a.emit(strb_w, 4, 1, O_SAVED)
    a.emit(movw, 0, SETOBJ & 0xFFFF); a.emit(movt, 0, SETOBJ >> 16); a.emit(bl, SAVE_FN)
    a.label("vs_x"); a.emit(pop_list, [4], pc=True)

    if RESETALL:
        # ---- c_vreset(r0 = track): every value of its engine back to the default, all of them sent again, saved; the engine kept
        a.label("c_vreset")
        a.emit(push_list, [4, 5], lr=True)
        a.emit(mov_reg, 4, 0)
        tail(5); mulstride(1, 4); a.emit(adds_reg, 1, 1, 5)                                              # r1 = TAIL + STRIDE t
        for i, v in enumerate(DEFAULTS): a.emit(movs_imm, 2, v & 0xFF); a.emit(strb_w, 2, 1, O_PAR + i)
        a.emit(lsls_imm, 1, 4, 3); a.emit(adds_reg, 1, 1, 5); a.emit(adds_imm8, 1, O_RT)                 # r1 = the track's RT bytes
        a.emit(movs_imm, 2, 0xFF); a.emit(strb_imm, 2, 1, RT_DLO); a.emit(strb_imm, 2, 1, RT_DHI)
        a.emit(movs_imm, 2, DX_MASK if OSC else 0); a.emit(strb_imm, 2, 1, RT_DX)
        a.emit(ldrb_imm, 2, 1, RT_AUX); a.emit(movs_imm, 3, 0x6F if OSC3 else 0x0F); a.emit(orrs_reg, 2, 3); a.emit(strb_imm, 2, 1, RT_AUX)
        a.emit(bl, L["c_gfst"]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vr_s", "eq")                   # the volatile values (OSC 2): the sweep sends them
        a.emit(lsls_imm, 1, 4, 3); a.emit(adds_reg, 0, 0, 1)
        for k, v in enumerate(DEFAULTS_V2): a.emit(movs_imm, 2, v & 0xFF); a.emit(strb_w, 2, 0, V2_OFF + k)
        a.label("vr_s")
        a.emit(bl, "c_vsave")
        a.emit(pop_list, [4, 5], pc=True)

    # ---- c_vmark(r0 = track, r1 = code 1..16): dirty bit
    a.label("c_vmark")
    if DUALUI: a.emit(cmp_imm, 1, 26); a.emit(b_cond, "vm_go", "ls"); a.emit(raw, h(0x4770)); a.label("vm_go")
    tail(2); a.emit(lsls_imm, 3, 0, 3); a.emit(adds_reg, 2, 2, 3); a.emit(adds_imm8, 2, O_RT)                  # r2 = volatile block
    a.emit(movs_imm, 3, 1); a.emit(subs_imm8, 1, 1); a.emit(lsls_reg, 3, 1)                                  # r3 = 1 << (code - 1)
    a.emit(ldrb_imm, 0, 2, RT_DLO); a.emit(orrs_reg, 0, 3); a.emit(strb_imm, 0, 2, RT_DLO)
    a.emit(lsrs_imm, 3, 3, 8); a.emit(ldrb_imm, 0, 2, RT_DHI); a.emit(orrs_reg, 0, 3); a.emit(strb_imm, 0, 2, RT_DHI)
    if OSC: a.emit(lsrs_imm, 3, 3, 8); a.emit(ldrb_imm, 0, 2, RT_DX); a.emit(orrs_reg, 0, 3); a.emit(strb_imm, 0, 2, RT_DX)
    if OSC3: a.emit(lsrs_imm, 3, 3, 8); a.emit(lsls_imm, 3, 3, 5); a.emit(ldrb_imm, 0, 2, RT_AUX); a.emit(orrs_reg, 0, 3); a.emit(strb_imm, 0, 2, RT_AUX)
    a.emit(raw, h(0x4770))

    # ---- c_vknob(obj, knob, delta): slot 4 of the macro handlers of the tracks 0..3: the VCF / VCA controls of a MIDI track whose mode is on, stock otherwise
    a.label("c_vknob")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2)
    a.emit(bl, "c_vtrack"); a.emit(cmp_imm, 0, 0xFF)
    if SD2:
        a.emit(b_cond, "vk_trk", "ne")
        a.emit(mov_reg, 0, 4); a.emit(bl, "c_sdsyn"); a.emit(cmp_imm, 0, 0xFF); bc("vk_stock", "eq")
        a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6); a.emit(bl, "c_sdknob"); a.emit(pop_list, [4, 5, 6, 7], pc=True)
        a.label("vk_trk")
    elif OSC3: bc("vk_stock", "eq")                                               # (the function outgrew the short conditional branch range)
    else: a.emit(b_cond, "vk_stock", "eq")
    if CCED:
        a.emit(mov_reg, 7, 0); a.emit(bl, "c_edact"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vk_noed", "eq")
        a.emit(mov_reg, 0, 5); a.emit(mov_reg, 1, 6); a.emit(bl, "c_edknob2" if EDV2 else "c_edknob"); a.emit(pop_list, [4, 5, 6, 7], pc=True)
        a.label("vk_noed"); a.emit(mov_reg, 0, 7)
    a.emit(mov_reg, 7, 0); a.emit(bl, "c_von"); a.emit(cmp_imm, 0, 0)
    if OSC3: bc("vk_stock", "eq")
    else: a.emit(b_cond, "vk_stock", "eq")
    if SDRUM:                                                                     # the step-drummer view: the knobs are the pairs
        a.emit(mov_reg, 0, 7); a.emit(bl, "c_sdview"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vk_nsd", "eq")
        a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6); a.emit(bl, "c_sdknob"); a.emit(pop_list, [4, 5, 6, 7], pc=True)
        a.label("vk_nsd")
    if CLEARK:
        a.emit(mov_reg, 0, 4); a.emit(bl, "c_vclr"); a.emit(cmp_imm, 0, 0); bc("vk_nc", "eq")
        if GRSRC:                                                                 # the granular page: its own codes (c_vclear took the oscillator page's, which share the knobs)
            a.emit(mov_reg, 0, 7); a.emit(bl, "c_grpg"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vk_cv", "eq")
            a.emit(movs_imm, 0, 0x28); a.emit(adds_reg, 1, 4, 5); a.emit(raw, strb_w(0, 1, 0x40))                     # the mark of the cleared knob
            a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 5); a.emit(bl, "c_grclear"); a.emit(pop_list, [4, 5, 6, 7], pc=True)
            a.label("vk_cv")
        if CLRAUTO:                                                               # turned left: the automation
            a.emit(cmp_imm, 6, 0); a.emit(b_cond, "vk_cr", "ge")
            a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 7); a.emit(bl, "c_vclrauto")
            a.emit(pop_list, [4, 5, 6, 7], pc=True)
            a.label("vk_cr")
        a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 7); a.emit(bl, "c_vclear")
        a.emit(pop_list, [4, 5, 6, 7], pc=True)
        a.label("vk_nc")
    a.emit(bl, L["c_shift"]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vk_ns", "eq"); a.emit(adds_imm8, 5, 8)
    a.label("vk_ns")
    if GRAN:                                                                      # the granular page (OSC1 page of a granular track): its own table and ranges
        a.emit(mov_reg, 0, 7); a.emit(bl, "c_grpg"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vk_ngr", "eq")
        if GRSRC:
            a.emit(cmp_imm, 5, 15); a.emit(b_cond, "vk_gk", "ne")
            a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 6); a.emit(bl, "c_grsrc"); a.emit(pop_list, [4, 5, 6, 7], pc=True)
            a.label("vk_gk")
        a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6); a.emit(bl, "c_grknob"); a.emit(pop_list, [4, 5, 6, 7], pc=True)
        a.label("vk_ngr")
    if OSC and DUALUI:                                                            # the page of the track (RT_TAG bits 1-2): 16 table bytes each
        a.emit(mov_reg, 0, 7); a.emit(bl, "c_vpage"); a.emit(lsls_imm, 0, 0, 4); a.emit(adds_reg, 5, 5, 0)
    elif OSC:                                                                     # page B (flags bit 4 + track): the second half of the table
        tail(2); a.emit(ldrb_w, 3, 2, O_FLAGS); a.emit(mov_reg, 1, 7); a.emit(adds_imm8, 1, 4); a.emit(lsrs_reg, 3, 1); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 3, 1)
        a.emit(cmp_imm, 3, 0); a.emit(b_cond, "vk_np", "eq"); a.emit(adds_imm8, 5, 16)
        a.label("vk_np")
    a.emit(movw, 3, base & 0xFFFF); a.emit(movt, 3, base >> 16); a.emit(ldrb_reg, 5, 3, 5)                                                              # r5 = code 1..16 (..24), r7 = track, r6 = delta
    if OSC: a.emit(cmp_imm, 5, 0); a.emit(b_cond, "vk_done", "eq")                # no function on this page
    if DUALUI: a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 5); a.emit(bl, "c_vvaddr"); a.emit(raw, ldrsb_w(4, 0, 0))                 # r4 = old value
    else:
        tail(2); mulstride(3, 7); a.emit(adds_reg, 2, 2, 3); a.emit(adds_reg, 2, 2, 5)                  # r2 = address of the value
        a.emit(raw, ldrsb_w(4, 2, 0))                                                 # r4 = old value
    if not TYPEZONE:
        a.emit(cmp_imm, 5, 13); a.emit(b_cond, "vk_shape", "eq")
        a.emit(cmp_imm, 5, 16); a.emit(b_cond, "vk_shape", "eq")
    if OSC and not OSC3: a.emit(cmp_imm, 5, 19); a.emit(b_cond, "vk_shape", "eq")
    a.emit(adds_reg, 0, 4, 6)                                                     # new = old + delta
    movmask(3); a.emit(subs_imm8, 5, 1); a.emit(lsrs_reg, 3, 5); a.emit(adds_imm8, 5, 1); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 3, 1)
    a.emit(cmp_imm, 3, 0); a.emit(b_cond, "vk_uni", "eq")
    a.emit(cmp_imm, 0, 63); a.emit(b_cond, "vk_b1", "le"); a.emit(movs_imm, 0, 63)
    a.label("vk_b1"); a.emit(movs_imm, 1, 0); a.emit(subs_imm8, 1, 64); a.emit(cmp_reg, 0, 1); a.emit(b_cond, "vk_set", "ge"); a.emit(mov_reg, 0, 1); a.emit(b, "vk_set")
    a.label("vk_uni")
    if OSC3: a.emit(cmp_imm, 5, 20); a.emit(b_cond, "vk_u0", "ne"); a.emit(cmp_imm, 0, 100); a.emit(b_cond, "vk_u0", "le"); a.emit(movs_imm, 0, 100); a.label("vk_u0")      # PW: 0..100
    if DUALUI: a.emit(cmp_imm, 5, 30); a.emit(b_cond, "vk_u2", "ne"); a.emit(cmp_imm, 0, 100); a.emit(b_cond, "vk_u2", "le"); a.emit(movs_imm, 0, 100); a.label("vk_u2")      # PW2: 0..100
    a.emit(cmp_imm, 0, 127); a.emit(b_cond, "vk_u1", "le"); a.emit(movs_imm, 0, 127)
    a.label("vk_u1"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vk_set", "ge"); a.emit(movs_imm, 0, 0); a.emit(b, "vk_set")
    a.label("vk_shape")                                                           # shape: one step per turn, 0..3 wrapping (r0 = new, r4 = old stays)
    a.emit(mov_reg, 0, 4); a.emit(cmp_imm, 6, 0); a.emit(b_cond, "vk_sd", "le"); a.emit(adds_imm8, 0, 1); a.emit(b, "vk_sw")
    a.label("vk_sd"); a.emit(subs_imm8, 0, 1)
    a.label("vk_sw")
    if FTYPE_N > 4 or FXTYPE_N > 4:                                               # SC21.4 / SC22: the filter type (code 16) and the FX type (code 13) have N values 0..N-1 (else 4)
        for code, n_, lab in ((16, FTYPE_N, "a"), (13, FXTYPE_N, "b")):
            if n_ <= 4: continue
            a.emit(cmp_imm, 5, code); a.emit(b_cond, "vk_n" + lab, "ne")
            a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vk_f" + lab, "ge"); a.emit(movs_imm, 0, n_ - 1); a.emit(b, "vk_set")
            a.label("vk_f" + lab); a.emit(cmp_imm, 0, n_); a.emit(b_cond, "vk_set", "lt"); a.emit(movs_imm, 0, 0); a.emit(b, "vk_set")
            a.label("vk_n" + lab)
    a.emit(movs_imm, 1, 3); a.emit(ands_reg, 0, 1)
    if FTYPE_N < 4:                                                              # the filter type (code 16) has FTYPE_N values: 3 -> 0 going up, 3 -> N - 1 going down
        a.emit(cmp_imm, 5, 16); a.emit(b_cond, "vk_ok", "ne"); a.emit(cmp_imm, 0, FTYPE_N); a.emit(b_cond, "vk_ok", "lo")
        a.emit(movs_imm, 0, 0); a.emit(cmp_imm, 6, 0); a.emit(b_cond, "vk_ok", "gt"); a.emit(movs_imm, 0, FTYPE_N - 1)
        a.label("vk_ok")
    a.emit(b, "vk_set")
    a.label("vk_mode")                                                            # VCA mode: right = gate (1), left = open (0)
    a.emit(movs_imm, 0, 0); a.emit(cmp_imm, 6, 0); a.emit(b_cond, "vk_set", "le"); a.emit(movs_imm, 0, 1)
    a.label("vk_set")
    a.emit(cmp_reg, 0, 4); a.emit(b_cond, "vk_done", "eq")
    if DUALUI:
        a.emit(mov_reg, 4, 0); a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 5); a.emit(bl, "c_vvaddr"); a.emit(strb_imm, 4, 0, 0)
        a.emit(cmp_imm, 5, 26); a.emit(b_cond, "vk_nc2", "ls")                    # a volatile value: the sweep goes there next (its cursor = code - 27)
        tail(2); a.emit(lsls_imm, 3, 7, 3); a.emit(adds_reg, 2, 2, 3); a.emit(ldrb_w, 0, 2, O_RT + RT_CNT); a.emit(movs_imm, 1, 0x70); a.emit(bics_reg, 0, 1)
        a.emit(mov_reg, 1, 5); a.emit(subs_imm8, 1, 27); a.emit(lsls_imm, 1, 1, 4); a.emit(orrs_reg, 0, 1); a.emit(strb_w, 0, 2, O_RT + RT_CNT)
        a.label("vk_nc2")
        a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 5); a.emit(bl, "c_vmark")
        if CCIO: a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 4); a.emit(bl, "c_vsync")      # out as MIDI, recorded in its lane
        a.emit(cmp_imm, 5, 26); bc("vk_done", "hi")                               # the volatile codes (27..34) are not saved
        a.emit(bl, "c_vsave")
    else:
        tail(2); mulstride(3, 7); a.emit(adds_reg, 2, 2, 3); a.emit(adds_reg, 2, 2, 5); a.emit(strb_imm, 0, 2, 0)
        a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 5); a.emit(bl, "c_vmark")
        a.emit(bl, "c_vsave")
    a.label("vk_done")
    a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("vk_stock")
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6)
    a.emit(raw, popw([4, 5, 6, 7], lr=True)); a.emit(b_w, STOCK_KNOB)

    # ---- c_vkleds(obj): slot 7 of the macro handlers: the stock buffer, then (MIDI track with the mode on) the track colour with the brightness of each value
    a.label("c_vkleds")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(bl, STOCK_LEDS); a.emit(mov_reg, 5, 0)
    a.emit(mov_reg, 0, 4); a.emit(bl, "c_vtrack"); a.emit(cmp_imm, 0, 0xFF)
    if SD2:
        a.emit(b_cond, "vk2_trk", "ne")
        a.emit(mov_reg, 0, 4); a.emit(bl, "c_sdsyn"); a.emit(cmp_imm, 0, 0xFF); bc("vk2_x", "eq")
        a.emit(mov_reg, 1, 5); a.emit(bl, "c_sdkleds"); a.emit(b, "vk2_x")
        a.label("vk2_trk")
    else: bc("vk2_x", "eq")
    a.emit(mov_reg, 7, 0); a.emit(bl, "c_von"); a.emit(cmp_imm, 0, 0); bc("vk2_x", "eq")
    if SDRUM:                                                                     # the step-drummer view: the knobs are the pairs
        a.emit(mov_reg, 0, 7); a.emit(bl, "c_sdview"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vk2_nsd", "eq")
        a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 5); a.emit(bl, "c_sdkleds"); a.emit(b, "vk2_x")
        a.label("vk2_nsd")
    a.emit(movs_imm, 6, COL_TRACK[0]); a.emit(cmp_imm, 7, 0); a.emit(b_cond, "vk2_c", "eq"); a.emit(movs_imm, 6, COL_TRACK[1])
    a.label("vk2_c")
    a.emit(bl, L["c_shift"]); a.emit(movs_imm, 4, 0); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vk2_l", "eq"); a.emit(movs_imm, 4, 8)
    a.label("vk2_l")                                                              # r4 = code - 1 (0..7, or 8..15 with Shift)
    if GRAN:
        a.emit(mov_reg, 0, 7); a.emit(bl, "c_grpg"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vk2_ngr", "eq")
        if GRSRC:
            a.emit(cmp_imm, 4, 15); a.emit(b_cond, "vk2_gk", "ne")
            a.emit(mov_reg, 0, 7); a.emit(bl, "c_grsled"); a.emit(b, "vk2_st")
            a.label("vk2_gk")
        a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 4); a.emit(bl, "c_grlvl"); a.emit(b, "vk2_lv")
        a.label("vk2_ngr")
    if OSC:
        if DUALUI:
            a.emit(mov_reg, 0, 7); a.emit(bl, "c_vpage"); a.emit(lsls_imm, 3, 0, 4); a.emit(adds_reg, 3, 3, 4)                  # r3 = index + 16 * page
        else:
            tail(2); a.emit(ldrb_w, 3, 2, O_FLAGS); a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 4); a.emit(lsrs_reg, 3, 0); a.emit(movs_imm, 0, 1); a.emit(ands_reg, 3, 0)
            a.emit(lsls_imm, 3, 3, 4); a.emit(adds_reg, 3, 3, 4)                      # r3 = index + 16 * page
        a.emit(movw, 1, base & 0xFFFF); a.emit(movt, 1, base >> 16); a.emit(ldrb_reg, 1, 1, 3)
        if TYPEZONE:
            if DUALUI:
                a.emit(cmp_imm, 1, 13); bc("vk2_tz", "eq"); a.emit(cmp_imm, 1, 16); bc("vk2_tz", "eq"); a.emit(cmp_imm, 1, 19); bc("vk2_tz", "eq")
                a.emit(cmp_imm, 1, 29); bc("vk2_tz", "eq"); a.emit(cmp_imm, 1, 32); bc("vk2_tz", "eq"); a.emit(b, "vk2_nt")
            else:
                a.emit(cmp_imm, 1, 13); bc("vk2_tz", "eq"); a.emit(cmp_imm, 1, 16); bc("vk2_tz", "eq"); a.emit(cmp_imm, 1, 19); bc("vk2_nt", "ne")
            a.label("vk2_tz"); a.emit(mov_reg, 0, 7); a.emit(bl, "c_vtype"); a.emit(b, "vk2_st")
            a.label("vk2_nt")
        a.emit(mov_reg, 0, 7); a.emit(bl, "c_vlvl")
    else:
        a.emit(movw, 1, base & 0xFFFF); a.emit(movt, 1, base >> 16); a.emit(ldrb_reg, 1, 1, 4); a.emit(mov_reg, 0, 7); a.emit(bl, "c_vlvl")
    if GRAN: a.label("vk2_lv")
    a.emit(adds_imm8, 0, 2); a.emit(lsls_imm, 0, 0, 8); a.emit(orrs_reg, 0, 6)
    if TYPEZONE: a.label("vk2_st")
    a.emit(movs_imm, 1, 7); a.emit(ands_reg, 1, 4); a.emit(lsls_imm, 1, 1, 1); a.emit(adds_reg, 1, 1, 5); a.emit(strh_imm, 0, 1, 0)
    a.emit(adds_imm8, 4, 1); a.emit(movs_imm, 1, 7); a.emit(ands_reg, 1, 4); bc("vk2_l", "ne")
    if CLEARK:
        a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 5); a.emit(bl, "c_vclrled")
    a.label("vk2_x")
    a.emit(mov_reg, 0, 5)
    a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_vset(r0 = track, r1 = on): the toggle bit; ACT is sent again; switching on sends every value
    a.label("c_vset")
    a.emit(push_list, [4], lr=True)
    a.emit(mov_reg, 4, 1)
    tail(2); a.emit(movs_imm, 1, 1); a.emit(lsls_reg, 1, 0); a.emit(ldrb_w, 3, 2, O_FLAGS); a.emit(bics_reg, 3, 1)
    a.emit(cmp_imm, 4, 0); a.emit(b_cond, "vs2_w", "eq"); a.emit(orrs_reg, 3, 1)
    a.label("vs2_w"); a.emit(strb_w, 3, 2, O_FLAGS)
    a.emit(lsls_imm, 1, 0, 3); a.emit(adds_reg, 1, 1, 2); a.emit(adds_imm8, 1, O_RT)
    a.emit(ldrb_imm, 3, 1, RT_AUX); a.emit(movs_imm, 2, 1); a.emit(orrs_reg, 3, 2); a.emit(strb_imm, 3, 1, RT_AUX)
    a.emit(cmp_imm, 4, 0); a.emit(b_cond, "vs2_x", "eq")
    a.emit(movs_imm, 3, 0xFF); a.emit(strb_imm, 3, 1, RT_DLO); a.emit(strb_imm, 3, 1, RT_DHI)
    if OSC: a.emit(movs_imm, 3, DX_MASK); a.emit(strb_imm, 3, 1, RT_DX)                          # the oscillator codes only
    if OSC3: a.emit(ldrb_imm, 3, 1, RT_AUX); a.emit(movs_imm, 2, 0x60); a.emit(orrs_reg, 3, 2); a.emit(strb_imm, 3, 1, RT_AUX)
    a.label("vs2_x"); a.emit(pop_list, [4], pc=True)

    if OSC:
        # ---- c_vflag(r0 = track, r1 = first bit: 0 mode on, 2 oscillator, 4 knob page) -> r0 = the flag bit; clobbers r1, r2
        a.label("c_vflag")
        tail(2); a.emit(ldrb_w, 2, 2, O_FLAGS); a.emit(adds_reg, 0, 0, 1); a.emit(lsrs_reg, 2, 0); a.emit(movs_imm, 0, 1); a.emit(ands_reg, 0, 2); a.emit(raw, h(0x4770))

        # ---- c_vsetosc(r0 = track, r1 = on): the oscillator flag; the mode goes on with it; ACT is sent again; GAIN / ENVA get the values that make a played oscillator (GAIN 0, ENVA 63; off: 64 / 0)
        a.label("c_vsetosc")
        a.emit(push_list, [4, 5], lr=True)
        a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
        tail(2); a.emit(movs_imm, 1, 1); a.emit(adds_imm8, 0, 2); a.emit(lsls_reg, 1, 0); a.emit(ldrb_w, 3, 2, O_FLAGS); a.emit(bics_reg, 3, 1)
        a.emit(cmp_imm, 5, 0); a.emit(b_cond, "vso_w", "eq"); a.emit(orrs_reg, 3, 1)
        a.label("vso_w"); a.emit(strb_w, 3, 2, O_FLAGS)
        a.emit(cmp_imm, 5, 0); a.emit(b_cond, "vso_a", "eq")
        if not PADS2:
            a.emit(mov_reg, 0, 4); a.emit(bl, "c_von"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vso_a", "ne")                 # the mode is off: on
            a.emit(mov_reg, 0, 4); a.emit(movs_imm, 1, 1); a.emit(bl, "c_vset")
        a.label("vso_a")
        tail(2); a.emit(lsls_imm, 1, 4, 3); a.emit(adds_reg, 1, 1, 2); a.emit(adds_imm8, 1, O_RT)
        a.emit(ldrb_imm, 3, 1, RT_AUX); a.emit(movs_imm, 2, 1); a.emit(orrs_reg, 3, 2); a.emit(strb_imm, 3, 1, RT_AUX)
        for code, v_on, v_off in (() if NEUTRAL else ((10, 0, 64), (15, 63, 0))):
            tail(2); mulstride(3, 4); a.emit(adds_reg, 2, 2, 3)
            a.emit(movs_imm, 0, v_off); a.emit(cmp_imm, 5, 0); a.emit(b_cond, f"vso_v{code}", "eq"); a.emit(movs_imm, 0, v_on)
            a.label(f"vso_v{code}"); a.emit(strb_imm, 0, 2, code)
            a.emit(mov_reg, 0, 4); a.emit(movs_imm, 1, code); a.emit(bl, "c_vmark")
        a.emit(pop_list, [4, 5], pc=True)

    # ---- c_vpad: b.w from the pad hook of the template (Preset) view of the MIDI tracks (r0 = view, r5 = pad); r4 is free
    a.label("c_vpad")
    if SDRUM:                                                                     # pad 30 = the step-drummer; with its view open the rows 1-3 are the steps and the destinations
        a.emit(cmp_imm, 5, PAD_SD); bc("vp_sdt", "eq")
        if VADRUM: a.emit(cmp_imm, 5, PAD_VEL); bc("vp_vel", "eq")
        a.emit(cmp_imm, 5, 24); a.emit(b_cond, "vp_sdq", "lo")
        a.label("vp_std")
    if CCED:
        a.emit(cmp_imm, 5, 8); (bc("vp_np", "hs") if CCED else a.emit(b_cond, "vp_np", "hs"))                      # a template pad: the unsaved changes are discarded and the knob selection of the editor is dropped
        if CCED2: a.emit(mov_reg, 4, 0); a.emit(bl, "c_eddiscard"); a.emit(mov_reg, 0, 4)
        tail(1); a.emit(ldrb_w, 2, 1, O_ED); a.emit(movs_imm, 3, 0x40); a.emit(bics_reg, 2, 3); a.emit(strb_w, 2, 1, O_ED)
        if DUALUI: a.emit(b, "vp_row")
        a.label("vp_np")
        a.emit(cmp_imm, 5, PAD_CC); (bc("vp_cc", "eq") if CCED else a.emit(b_cond, "vp_cc", "eq"))
    a.emit(cmp_imm, 5, PAD_VCF); (bc("vp_route" if DUALUI else "vp_view" if PADS2 else "vp_tog", "eq") if CCED else a.emit(b_cond, "vp_tog", "eq"))
    a.emit(cmp_imm, 5, PAD_FLIP); (bc("vp_fs" if EDV2 else "vp_flip", "eq") if CCED else a.emit(b_cond, "vp_flip", "eq"))
    if RESETALL and not RESETVIEW:                                                # SC38.7: Clear + pad 27 = every value of the engine back to its default
        a.emit(cmp_imm, 5, PAD_OSC); a.emit(b_cond, "vp_nr", "ne")
        a.emit(mov_reg, 4, 0)
        a.emit(movw, 0, MGR_OBJ & 0xFFFF); a.emit(movt, 0, MGR_OBJ >> 16); a.emit(ldr_imm, 0, 0, 0x20); a.emit(ldr_imm, 0, 0, 0xC)
        a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0); a.emit(lsls_imm, 0, 0, 31)   # Clear held: bit 0 of the held buttons
        a.emit(mov_reg, 0, 4); bc("vp_rst", "mi")
        a.label("vp_nr")
    if OSC:
        a.emit(cmp_imm, 5, PAD_OSC); (bc("vp_tri" if DUALUI else "vp_osc", "eq") if CCED else a.emit(b_cond, "vp_osc", "eq"))
        a.emit(cmp_imm, 5, PAD_PAGE); (bc("vp_dual" if DUALUI else "vp_view" if PADS2 else "vp_page", "eq") if CCED else a.emit(b_cond, "vp_page", "eq"))
    a.label("vp_fwd")
    a.emit(b_w, L["c_tpad"])
    if RESETALL:
        a.label("vp_rst")
        a.emit(raw, pushw([6, 7], lr=True))
        a.emit(mov_reg, 4, 0); a.emit(ldrb_imm, 6, 4, 0x10); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 6, 1)
        a.emit(mov_reg, 0, 6); a.emit(bl, "c_vreset")
        a.emit(raw, popw([6, 7], lr=True)); a.emit(b_w, T_PAD_RET)
    if SDRUM:
        a.label("vp_sdq")
        a.emit(raw, pushw([6, 7], lr=True))
        a.emit(mov_reg, 4, 0); a.emit(ldrb_imm, 6, 4, 0x10); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 6, 1)
        a.emit(mov_reg, 0, 6); a.emit(bl, "c_edact"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vp_sdn", "ne")
        a.emit(mov_reg, 0, 6); a.emit(bl, "c_sdopen"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vp_sdn", "eq")
        a.emit(mov_reg, 0, 6); a.emit(mov_reg, 1, 5); a.emit(bl, "c_sdpad")
        a.emit(raw, popw([6, 7], lr=True)); a.emit(b_w, T_PAD_RET)
        a.label("vp_sdn")
        a.emit(mov_reg, 0, 4); a.emit(raw, popw([6, 7], lr=True)); a.emit(b, "vp_std")
        a.label("vp_sdt")
        a.emit(raw, pushw([6, 7], lr=True))
        a.emit(mov_reg, 4, 0); a.emit(ldrb_imm, 6, 4, 0x10); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 6, 1)
        a.emit(mov_reg, 0, 6); a.emit(bl, "c_sdtog")
        a.emit(raw, popw([6, 7], lr=True)); a.emit(b_w, T_PAD_RET)
    if VADRUM:
        a.label("vp_vel")                                                         # pad 31 (VA-drum only): the velocity also sets the start level of the pitch / filter envelopes
        a.emit(raw, pushw([6, 7], lr=True))
        a.emit(mov_reg, 4, 0); a.emit(ldrb_imm, 6, 4, 0x10); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 6, 1)
        a.emit(mov_reg, 0, 6); a.emit(bl, "c_edact"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vpv_x", "ne")
        a.emit(mov_reg, 0, 6); a.emit(bl, "c_von"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vpv_x", "eq")
        a.emit(mov_reg, 0, 6); a.emit(bl, "c_vdbit"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vpv_x", "eq")
        a.emit(mov_reg, 0, 6); a.emit(adds_imm8, 0, 2); a.emit(bl, "c_vdbit"); a.emit(movs_imm, 1, 1); a.emit(eors_reg, 1, 0)
        a.emit(mov_reg, 0, 6); a.emit(adds_imm8, 0, 2); a.emit(bl, "c_vdput")
        a.emit(movw, 0, SETOBJ & 0xFFFF); a.emit(movt, 0, SETOBJ >> 16); a.emit(bl, SAVE_FN)
        a.label("vpv_x")
        a.emit(raw, popw([6, 7], lr=True)); a.emit(b_w, T_PAD_RET)
    if EDV2:
        a.label("vp_fs")                                                          # the pad next to pad 25: Save while the editor of this track is on, else the patch flip
        a.emit(raw, pushw([6, 7], lr=True))
        a.emit(mov_reg, 4, 0); a.emit(ldrb_imm, 6, 4, 0x10); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 6, 1)
        a.emit(mov_reg, 0, 6); a.emit(bl, "c_edact"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vfs_f", "eq")
        a.emit(bl, "c_edsavepad"); a.emit(raw, popw([6, 7], lr=True)); a.emit(b_w, T_PAD_RET)
        a.label("vfs_f")
        a.emit(mov_reg, 0, 4); a.emit(raw, popw([6, 7], lr=True)); a.emit(b, "vp_flip")
    a.label("vp_flip")                                                            # the patch flip is pressed: if it is off now it turns on, so this mode goes off
    a.emit(raw, pushw([6, 7], lr=True))
    a.emit(mov_reg, 4, 0); a.emit(ldrb_imm, 6, 4, 0x10); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 6, 1)
    a.emit(mov_reg, 0, 6); a.emit(bl, "c_von"); a.emit(cmp_imm, 0, 0); bc("vpf_x", "eq")
    a.emit(bl, L["c_settings"]); a.emit(cmp_imm, 0, 0); bc("vpf_x", "eq")
    a.emit(movs_imm, 1, 2); a.emit(bl, PARAM_GET); a.emit(ldr_imm, 0, 0, 0); a.emit(lsrs_imm, 0, 0, 26); a.emit(lsrs_reg, 0, 6); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1)
    a.emit(cmp_imm, 0, 0); bc("vpf_x", "ne")                                      # the flip is on now: it turns off
    a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 0); a.emit(bl, "c_vset")
    a.emit(movw, 0, SETOBJ & 0xFFFF); a.emit(movt, 0, SETOBJ >> 16); a.emit(bl, SAVE_FN)
    a.label("vpf_x")
    a.emit(mov_reg, 0, 4)                                                         # c_tpad wants the view in r0
    a.emit(raw, popw([6, 7], lr=True)); a.emit(b_w, L["c_tpad"])
    a.label("vp_tog")
    a.emit(raw, pushw([6, 7], lr=True))
    a.emit(mov_reg, 4, 0); a.emit(ldrb_imm, 6, 4, 0x10); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 6, 1)
    a.emit(mov_reg, 0, 6); a.emit(bl, "c_von"); a.emit(movs_imm, 1, 1); a.emit(eors_reg, 1, 0); a.emit(mov_reg, 7, 1)
    a.emit(mov_reg, 0, 6); a.emit(bl, "c_vset")
    a.emit(cmp_imm, 7, 0); bc("vpt_s", "eq")
    a.emit(bl, L["c_settings"]); a.emit(cmp_imm, 0, 0); bc("vpt_s", "eq")          # on: the patch flip of this track goes off
    a.emit(movs_imm, 1, 2); a.emit(bl, PARAM_PTR); a.emit(ldr_imm, 1, 0, 0)
    a.emit(movs_imm, 3, 1); a.emit(lsls_imm, 3, 3, 26); a.emit(lsls_reg, 3, 6); a.emit(bics_reg, 1, 3); a.emit(str_imm, 1, 0, 0)
    a.emit(bl, L["c_settings"]); a.emit(bl, COMMIT)
    a.label("vpt_s")
    a.emit(movw, 0, SETOBJ & 0xFFFF); a.emit(movt, 0, SETOBJ >> 16); a.emit(bl, SAVE_FN)
    a.emit(raw, popw([6, 7], lr=True)); a.emit(b_w, T_PAD_RET)

    if PADS2:
        a.label("vp_view")                                                        # pad 28 (oscillator view, page B) / pad 29 (VCA / VCF view, page A): select it and switch the mode on; the lit one switches the mode off
        a.emit(raw, pushw([5, 6, 7], lr=True))
        a.emit(mov_reg, 4, 0); a.emit(ldrb_imm, 6, 4, 0x10); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 6, 1)
        a.emit(movs_imm, 7, 0); a.emit(cmp_imm, 5, PAD_PAGE); a.emit(b_cond, "vv_p", "ne"); a.emit(movs_imm, 7, 1)
        a.label("vv_p")
        a.emit(mov_reg, 0, 6); a.emit(bl, "c_von"); a.emit(mov_reg, 5, 0)                                  # r5 = the mode is on
        a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 4); a.emit(bl, "c_vflag")                               # r0 = the knob page
        a.emit(cmp_imm, 5, 0); bc("vv_set", "eq")
        a.emit(cmp_reg, 0, 7); bc("vv_set", "ne")
        a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 0); a.emit(bl, "c_vset"); a.emit(b, "vv_save")           # the selected view again: the mode goes off
        a.label("vv_set")
        tail(2); a.emit(ldrb_w, 3, 2, O_FLAGS); a.emit(movs_imm, 1, 1); a.emit(mov_reg, 0, 6); a.emit(adds_imm8, 0, 4); a.emit(lsls_reg, 1, 0); a.emit(bics_reg, 3, 1)
        a.emit(cmp_imm, 7, 0); a.emit(b_cond, "vv_w", "eq"); a.emit(orrs_reg, 3, 1)
        a.label("vv_w"); a.emit(strb_w, 3, 2, O_FLAGS)
        a.emit(cmp_imm, 5, 0); bc("vv_save", "ne")
        a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 1); a.emit(bl, "c_vset")
        a.emit(bl, L["c_settings"]); a.emit(cmp_imm, 0, 0); bc("vv_save", "eq")                              # the mode went on: the patch flip of this track goes off
        a.emit(movs_imm, 1, 2); a.emit(bl, PARAM_PTR); a.emit(ldr_imm, 1, 0, 0)
        a.emit(movs_imm, 3, 1); a.emit(lsls_imm, 3, 3, 26); a.emit(lsls_reg, 3, 6); a.emit(bics_reg, 1, 3); a.emit(str_imm, 1, 0, 0)
        a.emit(bl, L["c_settings"]); a.emit(bl, COMMIT)
        a.label("vv_save")
        a.emit(movw, 0, SETOBJ & 0xFFFF); a.emit(movt, 0, SETOBJ >> 16); a.emit(bl, SAVE_FN)
        a.emit(raw, popw([5, 6, 7], lr=True)); a.emit(b_w, T_PAD_RET)

    if CCED:
        a.label("vp_cc")                                                          # pad 25: the editor on / off for the track of this view
        a.emit(raw, pushw([6, 7], lr=True))
        a.emit(mov_reg, 4, 0); a.emit(ldrb_imm, 6, 4, 0x10); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 6, 1)
        a.emit(mov_reg, 0, 6); a.emit(bl, "c_edact"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vcc_on", "eq")
        a.emit(bl, "c_edoff"); a.emit(b, "vcc_x")
        a.label("vcc_on")
        a.emit(bl, "c_eddiscard" if CCED2 else "c_edflush"); a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 6); a.emit(bl, "c_edon")
        a.label("vcc_x")
        a.emit(raw, popw([6, 7], lr=True)); a.emit(b_w, T_PAD_RET)
    if OSC:
        a.label("vp_osc")                                                         # pad 27: the oscillator source on / off (off -> on also switches the mode on)
        a.emit(raw, pushw([6, 7], lr=True))
        a.emit(mov_reg, 4, 0); a.emit(ldrb_imm, 6, 4, 0x10); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 6, 1)
        a.emit(mov_reg, 0, 6); a.emit(bl, "c_von"); a.emit(mov_reg, 7, 0)
        a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 2); a.emit(bl, "c_vflag")
        if not PADS2: a.emit(ands_reg, 0, 7)
        a.emit(movs_imm, 1, 1); a.emit(eors_reg, 1, 0)                               # r1 = not (on and osc) (PADS2: not osc)
        a.emit(mov_reg, 0, 6); a.emit(bl, "c_vsetosc")
        a.emit(movw, 0, SETOBJ & 0xFFFF); a.emit(movt, 0, SETOBJ >> 16); a.emit(bl, SAVE_FN)
        a.emit(raw, popw([6, 7], lr=True)); a.emit(b_w, T_PAD_RET)
        a.label("vp_page")                                                        # pad 28: the knob page (bit 4 + track of the flags)
        a.emit(raw, pushw([6, 7], lr=True))
        a.emit(mov_reg, 4, 0); a.emit(ldrb_imm, 6, 4, 0x10); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 6, 1)
        tail(2); a.emit(ldrb_w, 3, 2, O_FLAGS); a.emit(movs_imm, 1, 1); a.emit(mov_reg, 0, 6); a.emit(adds_imm8, 0, 4); a.emit(lsls_reg, 1, 0); a.emit(eors_reg, 3, 1); a.emit(strb_w, 3, 2, O_FLAGS)
        a.emit(raw, popw([6, 7], lr=True)); a.emit(b_w, T_PAD_RET)

    if DUALUI:
        a.label("vp_row")                                                         # pads 1-8: with the mode on (and no editor) they select the knob page: 1 VCA / VCF, 2 OSC1, 3 OSC2 (two oscillators); else the stock templates
        a.emit(raw, pushw([6, 7], lr=True))
        a.emit(mov_reg, 4, 0); a.emit(ldrb_imm, 6, 4, 0x10); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 6, 1)
        a.emit(mov_reg, 0, 6); a.emit(bl, "c_edact"); a.emit(cmp_imm, 0, 0); bc("vr_f", "ne")
        a.emit(mov_reg, 0, 6); a.emit(bl, "c_von"); a.emit(cmp_imm, 0, 0); bc("vr_f", "eq")
        a.emit(cmp_imm, 5, 4 if PAGES5 else 2); bc("vr_x", "hi")
        a.emit(cmp_imm, 5, 2); a.emit(b_cond, "vr_go", "ne")
        a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, RT_VEL); a.emit(bl, "c_vrt7"); a.emit(cmp_imm, 0, 0); bc("vr_x", "eq")
        a.label("vr_go")
        a.emit(mov_reg, 0, 6); a.emit(mov_reg, 1, 5); a.emit(bl, "c_vsetpage")
        a.label("vr_x")
        a.emit(raw, popw([6, 7], lr=True)); a.emit(b_w, T_PAD_RET)
        a.label("vr_f")
        a.emit(mov_reg, 0, 4); a.emit(raw, popw([6, 7], lr=True)); a.emit(b_w, L["c_tpad"])

        a.label("vp_tri")                                                         # pad 27: off -> line in with VCA / VCF -> oscillator with VCA / VCF -> off
        a.emit(raw, pushw([6, 7], lr=True))
        a.emit(mov_reg, 4, 0); a.emit(ldrb_imm, 6, 4, 0x10); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 6, 1)
        a.emit(mov_reg, 0, 6); a.emit(bl, "c_von"); a.emit(mov_reg, 7, 0)
        a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 2); a.emit(bl, "c_vflag")
        a.emit(cmp_imm, 7, 0); bc("tr_on", "ne")
        a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 0); a.emit(bl, "c_vsetosc")        # off -> line in: the mode on, the oscillator source off
        a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 1); a.emit(bl, "c_vset")
        a.emit(bl, L["c_settings"]); a.emit(cmp_imm, 0, 0); bc("tr_pg", "eq")                                       # the patch flip of this track goes off
        a.emit(movs_imm, 1, 2); a.emit(bl, PARAM_PTR); a.emit(ldr_imm, 1, 0, 0)
        a.emit(movs_imm, 3, 1); a.emit(lsls_imm, 3, 3, 26); a.emit(lsls_reg, 3, 6); a.emit(bics_reg, 1, 3); a.emit(str_imm, 1, 0, 0)
        a.emit(bl, L["c_settings"]); a.emit(bl, COMMIT)
        a.emit(b, "tr_pg")
        a.label("tr_on")
        a.emit(cmp_imm, 0, 0); bc("tr_off", "ne")
        if FXSEQ:                                                                 # mode on, no oscillator: line in, or the FX sequencer (VA-drum bit) -> off
            a.emit(mov_reg, 0, 6); a.emit(bl, "c_vdbit"); a.emit(cmp_imm, 0, 0); bc("tr_ln", "eq")
            a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 0); a.emit(bl, "c_vdput")
            a.emit(mov_reg, 0, 6); a.emit(bl, "c_sdnib"); a.emit(movs_imm, 1, 1); a.emit(bics_reg, 0, 1); a.emit(mov_reg, 1, 0)       # the step-drummer it enabled goes off with it
            a.emit(mov_reg, 0, 6); a.emit(bl, "c_sdsetnib")
            a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 0); a.emit(bl, "c_vset"); a.emit(b, "tr_pg")
            a.label("tr_ln")
        a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 1); a.emit(bl, "c_vsetosc"); a.emit(b, "tr_sv")                    # line in -> oscillator
        a.label("tr_off")
        if GRAN:                                                                  # oscillator (0, 0) -> VA-drum (1, 0) -> granular (0, 1) -> off
            a.emit(mov_reg, 0, 6); a.emit(bl, "c_vdbit"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "tr_vd", "ne")
            a.emit(mov_reg, 0, 6); a.emit(adds_imm8, 0, 2); a.emit(bl, "c_vdbit"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "tr_gr", "ne")
            a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 1); a.emit(bl, "c_vdput"); a.emit(b, "tr_sv")
            a.label("tr_vd")
            a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 0); a.emit(bl, "c_vdput")
            a.emit(mov_reg, 0, 6); a.emit(adds_imm8, 0, 2); a.emit(movs_imm, 1, 1); a.emit(bl, "c_vdput"); a.emit(b, "tr_sv")
            a.label("tr_gr")
            a.emit(mov_reg, 0, 6); a.emit(adds_imm8, 0, 2); a.emit(movs_imm, 1, 0); a.emit(bl, "c_vdput")
            if FXSEQ:                                                             # granular -> the FX sequencer: oscillator off, VA-drum bit, the step-drummer enabled
                a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 1); a.emit(bl, "c_vdput")
                a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 0); a.emit(bl, "c_vsetosc")
                a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 1); a.emit(bl, "c_vset")
                a.emit(mov_reg, 0, 6); a.emit(bl, "c_sdnib"); a.emit(movs_imm, 1, 1); a.emit(orrs_reg, 1, 0); a.emit(mov_reg, 0, 6); a.emit(bl, "c_sdsetnib")
                a.emit(b, "tr_sv")
        elif VADRUM:                                                              # oscillator -> VA-drum -> off
            a.emit(mov_reg, 0, 6); a.emit(bl, "c_vdbit"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "tr_vd", "ne")
            a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 1); a.emit(bl, "c_vdput"); a.emit(b, "tr_sv")
            a.label("tr_vd")
            a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 0); a.emit(bl, "c_vdput")
            a.emit(mov_reg, 0, 6); a.emit(adds_imm8, 0, 2); a.emit(movs_imm, 1, 0); a.emit(bl, "c_vdput")             # (and its pad 31)
        a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 0); a.emit(bl, "c_vsetosc")                                       # oscillator -> off
        a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 0); a.emit(bl, "c_vset")
        a.label("tr_pg")
        a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 0); a.emit(bl, "c_vsetpage")                                      # the page starts at VCA / VCF
        a.label("tr_sv")
        a.emit(movw, 0, SETOBJ & 0xFFFF); a.emit(movt, 0, SETOBJ >> 16); a.emit(bl, SAVE_FN)
        a.emit(raw, popw([6, 7], lr=True)); a.emit(b_w, T_PAD_RET)

        for lab, off in (("vp_dual", RT_VEL), ("vp_route", RT_NOTE)):             # pad 28: one / two oscillators (bit 7 of RT_VEL); pad 29: the chain order (bit 7 of RT_NOTE); only with the mode on
            a.label(lab)
            a.emit(raw, pushw([6, 7], lr=True))
            a.emit(mov_reg, 4, 0); a.emit(ldrb_imm, 6, 4, 0x10); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 6, 1)
            a.emit(mov_reg, 0, 6); a.emit(bl, "c_von"); a.emit(cmp_imm, 0, 0); bc(lab + "_x", "eq")
            if DUALHIDE and off == RT_VEL: a.emit(mov_reg, 0, 6); a.emit(bl, "c_vosc"); a.emit(cmp_imm, 0, 0); bc(lab + "_x", "eq")   # no oscillators: nothing
            a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, off); a.emit(bl, "c_vflip7")
            if off == RT_VEL:
                a.emit(cmp_imm, 0, 0); bc(lab + "_x", "ne")                                                          # now one oscillator: the OSC2 page is gone
                a.emit(mov_reg, 0, 6); a.emit(bl, "c_vpage"); a.emit(cmp_imm, 0, 2); bc(lab + "_x", "ne")
                a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 0); a.emit(bl, "c_vsetpage")
            a.label(lab + "_x")
            a.emit(raw, popw([6, 7], lr=True)); a.emit(b_w, T_PAD_RET)

    # ---- c_vleds: slot 7 of the template view: SC06's buffer (the patch flip pad), then pad 26 = this mode (and, with OSC, pad 27 = oscillator source, pad 28 = knob page B)
    a.label("c_vleds")
    a.emit(push_list, [4, 5, 6, 7] if CCED or PADS2 else [4, 5, 6] if OSC else [4, 5], lr=True)
    a.emit(mov_reg, 4, 0)
    if LEDCLEAN:                                                                  # the numbers were drawn last frame: clean the pads before the stock and our own are written
        tail(2); a.emit(ldrb_w, 3, 2, O_ED + 1); a.emit(movs_imm, 1, 4); a.emit(tst_reg, 3, 1); a.emit(b_cond, "lc_n", "eq")
        a.emit(bics_reg, 3, 1); a.emit(strb_w, 3, 2, O_ED + 1)
        a.emit(mov_reg, 0, 4); a.emit(bl, "c_edclean")
        a.label("lc_n")
        a.emit(mov_reg, 0, 4)
    a.emit(bl, L["c_tleds"]); a.emit(mov_reg, 5, 0)
    a.emit(ldrb_imm, 0, 4, 0x10); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1)
    if OSC: a.emit(mov_reg, 6, 0)
    if DUALUI:
        a.emit(mov_reg, 0, 6); a.emit(bl, "c_von"); a.emit(mov_reg, 7, 0)                                    # r7 = the mode is on
        if TDRAW:                                                                 # mode off (and not the editor): the stock redraw of the template row (the page row had overwritten it)
            a.emit(cmp_imm, 7, 0); bc("vle_nd", "ne")
            a.emit(mov_reg, 0, 6); a.emit(bl, "c_edact"); a.emit(cmp_imm, 0, 0); bc("vle_nd", "ne")
            a.emit(mov_reg, 0, 4); a.emit(bl, T_DRAW)
            a.label("vle_nd")
        a.emit(movs_imm, 1, 0); a.emit(cmp_imm, 7, 0); a.emit(b_cond, "vle_t", "eq")
        a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 2); a.emit(bl, "c_vflag")
        if FXSEQ:
            a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vle_os", "ne")
            a.emit(mov_reg, 0, 6); a.emit(bl, "c_vdbit"); a.emit(movs_imm, 1, COL_ON); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vle_t", "eq"); a.emit(movs_imm, 1, COL_FS); a.emit(b, "vle_t")
            a.label("vle_os"); a.emit(movs_imm, 1, COL_OSC[0])
        else:
            a.emit(movs_imm, 1, COL_ON); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vle_t", "eq"); a.emit(movs_imm, 1, COL_OSC[0])
        if GRAN:
            a.emit(mov_reg, 0, 6); a.emit(bl, "c_vdbit"); a.emit(movs_imm, 1, COL_VD); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vle_t", "ne")
            a.emit(mov_reg, 0, 6); a.emit(adds_imm8, 0, 2); a.emit(bl, "c_vdbit"); a.emit(movs_imm, 1, COL_OSC[0]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vle_t", "eq"); a.emit(movs_imm, 1, COL_GR)
        elif VADRUM: a.emit(mov_reg, 0, 6); a.emit(bl, "c_vdbit"); a.emit(movs_imm, 1, COL_OSC[0]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vle_t", "eq"); a.emit(movs_imm, 1, COL_VD)
        a.label("vle_t"); a.emit(strh_imm, 1, 5, 2 * PAD_OSC)                                                # pad 27: off (dark) / line in (orange) / oscillator (green)
        a.emit(movs_imm, 1, 0); a.emit(cmp_imm, 7, 0); a.emit(b_cond, "vle_d", "eq")
        if DUALHIDE: a.emit(mov_reg, 0, 6); a.emit(bl, "c_vosc"); a.emit(movs_imm, 1, 0); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vle_d", "eq")   # no oscillators: dark
        a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, RT_VEL); a.emit(bl, "c_vrt7")
        a.emit(movs_imm, 1, COL_OSC[1]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vle_d", "eq"); a.emit(movs_imm, 1, COL_OSC[0])
        a.label("vle_d"); a.emit(strh_imm, 1, 5, 2 * PAD_PAGE)                                               # pad 28: one / two oscillators
        a.emit(movs_imm, 1, 0); a.emit(cmp_imm, 7, 0); a.emit(b_cond, "vle_r", "eq")
        a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, RT_NOTE); a.emit(bl, "c_vrt7")
        a.emit(movs_imm, 1, COL_ROUTE[1]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vle_r", "eq"); a.emit(movs_imm, 1, COL_ROUTE[0])
        a.label("vle_r"); a.emit(strh_imm, 1, 5, 2 * PAD_VCF)                                                # pad 29: the chain order
        a.emit(mov_reg, 0, 6); a.emit(bl, "c_edact"); a.emit(cmp_imm, 0, 0); bc("vle_rw", "ne")              # the editor draws its own pads
        a.emit(cmp_imm, 7, 0); bc("vle_rw", "eq")
        a.emit(mov_reg, 0, 6); a.emit(bl, "c_vpage"); a.emit(mov_reg, 7, 0)                                  # r7 = the page: the page row (pads 1-8)
        for k in (0, 1):
            b_, d_ = COL_PAGE[k]
            a.emit(movs_imm, 1, d_); a.emit(cmp_imm, 7, k); a.emit(b_cond, f"vle_p{k}", "ne"); a.emit(movs_imm, 1, b_)
            a.label(f"vle_p{k}"); a.emit(strh_imm, 1, 5, 2 * k)
        a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, RT_VEL); a.emit(bl, "c_vrt7")
        b_, d_ = COL_PAGE[2]
        a.emit(movs_imm, 1, 0); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vle_p2", "eq")
        a.emit(movs_imm, 1, d_); a.emit(cmp_imm, 7, 2); a.emit(b_cond, "vle_p2", "ne"); a.emit(movs_imm, 1, b_)
        a.label("vle_p2"); a.emit(strh_imm, 1, 5, 4)
        if PAGES5:                                                                # pads 4 / 5: the page of the lanes, the modulation page
            for k in (3, 4):
                b_, d_ = COL_PAGE2[k - 3]
                a.emit(movs_imm, 1, d_); a.emit(cmp_imm, 7, k); a.emit(b_cond, f"vle_q{k}", "ne"); a.emit(movs_imm, 1, b_)
                a.label(f"vle_q{k}"); a.emit(strh_imm, 1, 5, 2 * k)
        a.emit(movs_imm, 1, 0)
        for k in range(5 if PAGES5 else 3, 8): a.emit(strh_imm, 1, 5, 2 * k)
        a.label("vle_rw")
    elif PADS2:
        a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 2); a.emit(bl, "c_vflag")                                # pad 27: the oscillator source
        a.emit(movs_imm, 1, COL_OSC[1]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vle_o", "eq"); a.emit(movs_imm, 1, COL_OSC[0])
        a.label("vle_o"); a.emit(strh_imm, 1, 5, 2 * PAD_OSC)
        a.emit(mov_reg, 0, 6); a.emit(bl, "c_von"); a.emit(mov_reg, 7, 0)
        a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 4); a.emit(bl, "c_vflag")                                # r0 = knob page, r7 = mode on
        a.emit(movs_imm, 1, COL_OFF); a.emit(cmp_imm, 7, 0); a.emit(b_cond, "vle_s", "eq"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vle_s", "ne"); a.emit(movs_imm, 1, COL_ON)
        a.label("vle_s"); a.emit(strh_imm, 1, 5, 2 * PAD_VCF)                                               # pad 29: the VCA / VCF view
        a.emit(movs_imm, 1, COL_OSC[1]); a.emit(cmp_imm, 7, 0); a.emit(b_cond, "vle_p", "eq"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vle_p", "eq"); a.emit(movs_imm, 1, COL_OSC[0])
        a.label("vle_p"); a.emit(strh_imm, 1, 5, 2 * PAD_PAGE)                                              # pad 28: the oscillator view
    else:
        a.emit(bl, "c_von")
        a.emit(movs_imm, 1, COL_OFF); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vle_s", "eq"); a.emit(movs_imm, 1, COL_ON)
        a.label("vle_s"); a.emit(strh_imm, 1, 5, 2 * PAD_VCF)
        if OSC:
            a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 2); a.emit(bl, "c_vflag")
            a.emit(movs_imm, 1, COL_OSC[1] if COLORS else COL_OFF); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vle_o", "eq"); a.emit(movs_imm, 1, COL_OSC[0] if COLORS else COL_ON)
            a.label("vle_o"); a.emit(strh_imm, 1, 5, 2 * PAD_OSC)
            a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 4); a.emit(bl, "c_vflag")
            if COLORS:
                a.emit(movs_imm, 1, COL_OSC[1]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vle_p", "eq"); a.emit(movs_imm, 1, COL_OSC[0])
            else:
                a.emit(movs_imm, 1, COL_OFF); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vle_p", "eq"); a.emit(movs_imm, 1, COL_TRACK[0]); a.emit(cmp_imm, 6, 0); a.emit(b_cond, "vle_p", "eq"); a.emit(movs_imm, 1, COL_TRACK[1])
            a.label("vle_p"); a.emit(strh_imm, 1, 5, 2 * PAD_PAGE)
    if CCED:
        a.emit(mov_reg, 0, 6); a.emit(bl, "c_edact"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vle_ed", "ne")
        a.emit(movs_imm, 1, COL_CC[1]); a.emit(strh_imm, 1, 5, 2 * PAD_CC); a.emit(b, "vle_end")
        a.label("vle_ed")
        a.emit(movs_imm, 1, COL_CC[0]); a.emit(strh_imm, 1, 5, 2 * PAD_CC)
        if EDV2:
            a.emit(movs_imm, 1, 0); a.emit(strh_imm, 1, 5, 2 * PAD_SAVE)                                                  # the patch flip LED is not shown while editing: this pad is Save
            a.emit(mov_reg, 0, 4); a.emit(bl, "c_edshow")                                                                 # r0 = value, r1 = state (0 none, 1 number, 2 save step), r2 = colour
            a.emit(cmp_imm, 1, 1); a.emit(b_cond, "vle_nn", "ne")
            if LEDCLEAN:
                a.emit(mov_reg, 3, 0); tail(6); a.emit(ldrb_w, 7, 6, O_ED + 1); a.emit(movs_imm, 1, 4); a.emit(orrs_reg, 7, 1); a.emit(strb_w, 7, 6, O_ED + 1)
                a.emit(mov_reg, 1, 3)
            else:
                a.emit(mov_reg, 1, 0)
            a.emit(mov_reg, 0, 5); a.emit(bl, "c_ednum")
            a.label("vle_nn")
            tail(2); a.emit(ldrb_w, 3, 2, O_ED); a.emit(movs_imm, 1, 0x40); a.emit(tst_reg, 3, 1); a.emit(b_cond, "vle_sv", "eq")
            a.emit(mov_reg, 0, 4); a.emit(bl, "c_edshow"); a.emit(cmp_imm, 1, 2); a.emit(b_cond, "vle_sv", "ne")                # at the save step: blinking Save pad
            a.emit(movw, 0, HAL_TICK & 0xFFFF); a.emit(movt, 0, HAL_TICK >> 16); a.emit(ldr_imm, 0, 0, 0); a.emit(lsrs_imm, 0, 0, 8); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1)
            a.emit(movs_imm, 1, COL_SAVE[1]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vle_bk", "eq"); a.emit(movs_imm, 1, COL_SAVE[0])
            a.label("vle_bk"); a.emit(strh_imm, 1, 5, 2 * PAD_SAVE); a.emit(b, "vle_end")
            a.label("vle_sv")                                                                                              # (no pad when not at the save step: the numbers use the pads)
        else:
            tail(2); a.emit(ldrb_w, 7, 2, O_ED); a.emit(movs_imm, 1, 0x40); a.emit(tst_reg, 7, 1); a.emit(b_cond, "vle_end", "eq")
            a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 7); a.emit(movs_imm, 2, 7); a.emit(ands_reg, 1, 2); a.emit(bl, "c_edrec")            # r0 = the record of the selected knob
            a.emit(lsrs_imm, 1, 7, 3); a.emit(movs_imm, 2, 7); a.emit(ands_reg, 1, 2); a.emit(bl, "c_edfield")                          # r0 = halfword address, r1 = shift, r2 = colour
            a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vle_end", "eq")
            a.emit(ldrh_imm, 3, 0, 0); a.emit(lsrs_reg, 3, 1); a.emit(movs_imm, 1, 0x7F); a.emit(ands_reg, 3, 1)
            if LEDCLEAN:
                tail(6); a.emit(ldrb_w, 7, 6, O_ED + 1); a.emit(movs_imm, 1, 4); a.emit(orrs_reg, 7, 1); a.emit(strb_w, 7, 6, O_ED + 1)
            a.emit(mov_reg, 1, 3); a.emit(mov_reg, 0, 5); a.emit(bl, "c_ednum")
        a.label("vle_end")
    if SDRUM: a.emit(ldrb_imm, 0, 4, 0x10); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1); a.emit(mov_reg, 1, 5); a.emit(bl, "c_sdleds")   # (r6 is not the track any more on the editor path)
    a.emit(mov_reg, 0, 5)
    a.emit(pop_list, [4, 5, 6, 7] if CCED or PADS2 else [4, 5, 6] if OSC else [4, 5], pc=True)

    # ---- note wrappers (vtable 0x08059FC4 / C8): count the held notes of an active MIDI track, then SC06's wrappers
    if DUALUI:
        # ---- note wrappers with the paraphonic assignment: the count of the held notes (RT_CNT bits 0-3), the notes of the two oscillators (n1 = RT_NOTE bits 0-6, n2 = the value of code 14 in the tail),
        #      bit 7 of RT_CNT = the oscillator that got its note first is OSC2 (the next new note replaces the older one)
        for name, orig in (("c_vnon", "c_non"), ("c_vnoff", "c_noff")):
            on = name == "c_vnon"
            a.label(name)
            a.emit(raw, pushw([0, 1, 2, 3, 4, 5, 6], lr=True))
            a.emit(mov_reg, 4, 1); a.emit(subs_imm8, 4, 2); a.emit(cmp_imm, 4, 1); bc(name + "_f", "hi")
            a.emit(mov_reg, 0, 4); a.emit(bl, "c_von"); a.emit(cmp_imm, 0, 0); bc(name + "_f", "eq")
            tail(5); a.emit(lsls_imm, 6, 4, 3); a.emit(adds_reg, 5, 5, 6); a.emit(adds_imm8, 5, O_RT)
            a.emit(raw, ldr_sp(2, 8))
            if on:
                a.emit(bl, "c_vnote_on")
                a.emit(raw, ldr_sp(2, 12)); a.emit(movs_imm, 0, RT_VEL); a.emit(bl, "c_vsetn")
                a.emit(ldrb_imm, 0, 5, RT_AUX); a.emit(movs_imm, 1, 0x1E); a.emit(orrs_reg, 0, 1); a.emit(strb_imm, 0, 5, RT_AUX)
                a.emit(ldrb_imm, 0, 5, RT_DHI); a.emit(movs_imm, 1, 0x20); a.emit(orrs_reg, 0, 1); a.emit(strb_imm, 0, 5, RT_DHI)
                if SDRUM: a.emit(mov_reg, 0, 4); a.emit(bl, "c_sdmark")
            else:
                a.emit(bl, "c_vnote_off")
            a.label(name + "_f")
            a.emit(pop_list, [0, 1, 2, 3]); a.emit(raw, popw([4, 5, 6], lr=True)); a.emit(b_w, L[orig])
    else:
        for name, orig in (("c_vnon", "c_non"), ("c_vnoff", "c_noff")):
            on = name == "c_vnon"
            a.label(name)
            a.emit(raw, pushw([0, 1, 2, 3, 4, 5, 6], lr=True))
            a.emit(mov_reg, 4, 1); a.emit(subs_imm8, 4, 2); a.emit(cmp_imm, 4, 1); bc(name + "_f", "hi")
            a.emit(mov_reg, 0, 4); a.emit(bl, "c_von"); a.emit(cmp_imm, 0, 0); bc(name + "_f", "eq")
            tail(5); a.emit(lsls_imm, 6, 4, 3); a.emit(adds_reg, 5, 5, 6); a.emit(adds_imm8, 5, O_RT)
            a.emit(ldrb_imm, 0, 5, RT_CNT)
            if on:
                a.emit(cmp_imm, 0, 15); a.emit(b_cond, name + "_c", "hs"); a.emit(adds_imm8, 0, 1)
                a.label(name + "_c"); a.emit(strb_imm, 0, 5, RT_CNT)
                a.emit(raw, ldr_sp(2, 8)); a.emit(raw, ldr_sp(3, 12)); a.emit(strb_imm, 2, 5, RT_NOTE); a.emit(strb_imm, 3, 5, RT_VEL)
                a.emit(ldrb_imm, 0, 5, RT_AUX); a.emit(movs_imm, 1, 0x1E); a.emit(orrs_reg, 0, 1); a.emit(strb_imm, 0, 5, RT_AUX)
            else:
                a.emit(cmp_imm, 0, 0); bc(name + "_f", "eq")
                a.emit(subs_imm8, 0, 1); a.emit(strb_imm, 0, 5, RT_CNT); bc(name + "_f", "ne")
                a.emit(ldrb_imm, 0, 5, RT_AUX); a.emit(movs_imm, 1, 8); a.emit(orrs_reg, 0, 1); a.emit(strb_imm, 0, 5, RT_AUX)
            a.label(name + "_f")
            a.emit(pop_list, [0, 1, 2, 3]); a.emit(raw, popw([4, 5, 6], lr=True)); a.emit(b_w, L[orig])


    # ---- c_vsend(r5 = tail, r6 = track): one mailbox message of the voice, if anything is pending; clobbers r0-r4, r7
    a.label("c_vsend")
    a.emit(push_list, [4], lr=True)
    a.emit(lsls_imm, 7, 6, 3); a.emit(adds_reg, 7, 7, 5); a.emit(adds_imm8, 7, O_RT)
    if STRETCH:                                                                   # SC38.1: in the stretch mode the position (code 19) goes again every 4 ms
        a.emit(movw, 0, HAL_TICK & 0xFFFF); a.emit(movt, 0, HAL_TICK >> 16); a.emit(ldr_imm, 0, 0, 0); a.emit(movs_imm, 1, 3); a.emit(ands_reg, 0, 1)
        a.emit(cmp_imm, 0, 1); a.emit(b_cond, "sv_nm", "ne")
        a.emit(mov_reg, 0, 6); a.emit(bl, "c_strm"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sv_nm", "eq")
        a.emit(ldrb_imm, 0, 7, RT_DX); a.emit(movs_imm, 1, 4); a.emit(orrs_reg, 0, 1); a.emit(strb_imm, 0, 7, RT_DX)
        a.label("sv_nm")
    if RATELIMIT:                                                                                                # one message per 2 ms and voice: the DSP reads once per block
        a.emit(ldrb_imm, 0, 7, RT_TAG); a.emit(lsrs_imm, 3, 0, 3)
        a.emit(movw, 1, HAL_TICK & 0xFFFF); a.emit(movt, 1, HAL_TICK >> 16); a.emit(ldr_imm, 1, 1, 0); a.emit(movs_imm, 2, 31); a.emit(ands_reg, 1, 2)
        a.emit(subs_reg, 3, 1, 3); a.emit(ands_reg, 3, 2); a.emit(cmp_imm, 3, RATE_MS); bc("sd_x", "lo")
        a.emit(subs_imm8, 1, RATE_MS); a.emit(ands_reg, 1, 2); a.emit(lsls_imm, 1, 1, 3)                         # allowed: the stamp becomes 'now - RATE_MS' so a long idle time never wraps round to 'just now' (5 bits = 32 ms)
        a.emit(movs_imm, 2, 7); a.emit(ands_reg, 0, 2); a.emit(orrs_reg, 0, 1); a.emit(strb_imm, 0, 7, RT_TAG)
    a.emit(ldrb_imm, 0, 7, RT_AUX)
    a.emit(movs_imm, 1, 1); a.emit(tst_reg, 0, 1); a.emit(b_cond, "sd_1", "eq")                                  # ACT = the toggle bit of the track
    a.emit(bics_reg, 0, 1); a.emit(strb_imm, 0, 7, RT_AUX)
    if OSC:                                                                       # ACT = on + (on and oscillator): 0 off, 1 VCF mode, 2 oscillator source
        a.emit(ldrb_w, 1, 5, O_FLAGS); a.emit(mov_reg, 3, 1); a.emit(lsrs_reg, 1, 6); a.emit(movs_imm, 2, 1); a.emit(ands_reg, 1, 2)
        a.emit(mov_reg, 0, 6); a.emit(adds_imm8, 0, 2); a.emit(lsrs_reg, 3, 0); a.emit(ands_reg, 3, 2); a.emit(ands_reg, 3, 1); a.emit(adds_reg, 1, 1, 3)
        if DUALUI:                                                                # + the chain order (bit 7 of RT_NOTE) << 8 + the two-oscillator flag (bit 7 of RT_VEL) << 9
            a.emit(ldrb_imm, 2, 7, RT_NOTE); a.emit(lsrs_imm, 2, 2, 7); a.emit(lsls_imm, 2, 2, 8); a.emit(orrs_reg, 1, 2)
            a.emit(ldrb_imm, 2, 7, RT_VEL); a.emit(lsrs_imm, 2, 2, 7); a.emit(lsls_imm, 2, 2, 9); a.emit(orrs_reg, 1, 2)
        if VADRUM:                                                                # + the VA-drum flag << 10 + velocity -> envelopes << 11
            a.emit(ldrb_w, 2, 5, O_SIG); a.emit(lsrs_reg, 2, 6); a.emit(movs_imm, 0, 1)
            a.emit(mov_reg, 3, 2); a.emit(ands_reg, 3, 0); a.emit(lsls_imm, 3, 3, 10); a.emit(orrs_reg, 1, 3)
            a.emit(lsrs_imm, 2, 2, 2); a.emit(ands_reg, 2, 0); a.emit(lsls_imm, 2, 2, 11); a.emit(orrs_reg, 1, 2)
        if FXSEQ:                                                                 # line in + VA-drum bit = the FX sequencer: the voice off
            a.emit(movs_imm, 2, 3); a.emit(ands_reg, 2, 1); a.emit(cmp_imm, 2, 1); a.emit(b_cond, "sd_nf", "ne")
            a.emit(movw, 2, 0x0400); a.emit(tst_reg, 1, 2); a.emit(b_cond, "sd_nf", "eq"); a.emit(movs_imm, 1, 0)
            a.label("sd_nf")
        if GRAN:                                                                  # engine bits (0, 1) = granular: bit 11 -> bit 12
            a.emit(movw, 2, 0x0800); a.emit(tst_reg, 1, 2); a.emit(b_cond, "sd_ng", "eq")
            a.emit(movw, 2, 0x0400); a.emit(tst_reg, 1, 2); a.emit(b_cond, "sd_ng", "ne")
            a.emit(movw, 2, 0x1800); a.emit(eors_reg, 1, 2)
            a.label("sd_ng")
        a.emit(movs_imm, 0, 19); a.emit(b, "sd_send")
    else:
        a.emit(ldrb_w, 1, 5, O_FLAGS); a.emit(lsrs_reg, 1, 6); a.emit(movs_imm, 2, 1); a.emit(ands_reg, 1, 2); a.emit(movs_imm, 0, 19); a.emit(b, "sd_send")
    a.label("sd_1")
    a.emit(movs_imm, 1, 2); a.emit(tst_reg, 0, 1); a.emit(b_cond, "sd_2", "eq")                                  # NOTE
    a.emit(bics_reg, 0, 1); a.emit(strb_imm, 0, 7, RT_AUX); a.emit(ldrb_imm, 1, 7, RT_NOTE)
    if DUALUI: a.emit(movs_imm, 2, 0x7F); a.emit(ands_reg, 1, 2)
    a.emit(movs_imm, 0, 18); a.emit(b, "sd_send")
    a.label("sd_2")
    a.emit(movs_imm, 1, 4); a.emit(tst_reg, 0, 1); a.emit(b_cond, "sd_3", "eq")                                  # VEL
    a.emit(bics_reg, 0, 1); a.emit(strb_imm, 0, 7, RT_AUX); a.emit(ldrb_imm, 1, 7, RT_VEL)
    if DUALUI: a.emit(movs_imm, 2, 0x7F); a.emit(ands_reg, 1, 2)
    a.emit(movs_imm, 0, 20); a.emit(b, "sd_send")
    a.label("sd_3")
    if SDRUM:                                                                     # step-drummer: the values the pitch row moves (codes 17 / 18 / 19 / 20, 3, 6) go before the gate and the trigger
        a.emit(ldrb_imm, 1, 7, RT_DX); a.emit(movs_imm, 2, 0x0F); a.emit(ands_reg, 1, 2); a.emit(ldrb_imm, 2, 7, RT_DLO); a.emit(movs_imm, 3, 0x24); a.emit(ands_reg, 2, 3); a.emit(orrs_reg, 1, 2)
        a.emit(cmp_imm, 1, 0); a.emit(b_cond, "sd_3a", "eq")
        a.emit(mov_reg, 4, 0); a.emit(mov_reg, 0, 6); a.emit(bl, "c_sden"); a.emit(cmp_imm, 0, 0); a.emit(mov_reg, 0, 4); bc("sd_5", "ne")
        a.label("sd_3a")
    a.emit(movs_imm, 1, 8); a.emit(tst_reg, 0, 1); a.emit(b_cond, "sd_4", "eq")                                  # GATE = held notes > 0
    a.emit(bics_reg, 0, 1); a.emit(strb_imm, 0, 7, RT_AUX); a.emit(ldrb_imm, 1, 7, RT_CNT)
    if DUALUI: a.emit(movs_imm, 2, 15); a.emit(ands_reg, 1, 2)                    # the count is the low nibble (the cursor and the older flag live above)
    a.emit(movs_imm, 2, 0)
    a.emit(cmp_imm, 1, 0); a.emit(b_cond, "sd_g", "eq"); a.emit(movs_imm, 2, 1)
    a.label("sd_g"); a.emit(mov_reg, 1, 2); a.emit(movs_imm, 0, 17); a.emit(b, "sd_send")
    a.label("sd_4")
    a.emit(movs_imm, 1, 0x10); a.emit(tst_reg, 0, 1); a.emit(b_cond, "sd_5", "eq")                               # TRIG
    a.emit(bics_reg, 0, 1); a.emit(strb_imm, 0, 7, RT_AUX); a.emit(movs_imm, 1, 1); a.emit(movs_imm, 0, 21); a.emit(b, "sd_send")
    a.label("sd_5")
    a.emit(ldrb_imm, 0, 7, RT_DLO); a.emit(ldrb_imm, 1, 7, RT_DHI); a.emit(lsls_imm, 1, 1, 8); a.emit(orrs_reg, 0, 1)
    if OSC: a.emit(ldrb_imm, 1, 7, RT_DX); a.emit(lsls_imm, 1, 1, 16); a.emit(orrs_reg, 0, 1)
    if OSC3: a.emit(ldrb_imm, 1, 7, RT_AUX); a.emit(lsrs_imm, 1, 1, 5); a.emit(lsls_imm, 1, 1, 24); a.emit(orrs_reg, 0, 1)
    a.emit(cmp_imm, 0, 0)
    if OSC3: bc("sd_hb" if HEARTBEAT else "sd_x", "eq")                           # (out of the short conditional branch range with the extra instructions)
    else: a.emit(b_cond, "sd_x", "eq")
    a.emit(movs_imm, 2, 0)
    a.label("sd_f")
    a.emit(movs_imm, 3, 1); a.emit(tst_reg, 0, 3); a.emit(b_cond, "sd_found", "ne"); a.emit(lsrs_imm, 0, 0, 1); a.emit(adds_imm8, 2, 1); a.emit(b, "sd_f")
    a.label("sd_found")                                                                                          # r2 = j: value of code j + 1
    a.emit(movs_imm, 4, 1); a.emit(lsls_reg, 4, 2)
    mulstride(1, 6); a.emit(adds_reg, 1, 1, 5); a.emit(adds_reg, 1, 1, 2); a.emit(raw, ldrsb_w(1, 1, 1))
    a.emit(movs_imm, 0, 0xFF); a.emit(ands_reg, 0, 4); a.emit(ldrb_imm, 3, 7, RT_DLO); a.emit(bics_reg, 3, 0); a.emit(strb_imm, 3, 7, RT_DLO)
    a.emit(lsrs_imm, 0, 4, 8); a.emit(ldrb_imm, 3, 7, RT_DHI); a.emit(bics_reg, 3, 0); a.emit(strb_imm, 3, 7, RT_DHI)
    if OSC: a.emit(lsrs_imm, 0, 4, 16); a.emit(ldrb_imm, 3, 7, RT_DX); a.emit(bics_reg, 3, 0); a.emit(strb_imm, 3, 7, RT_DX)
    if OSC3: a.emit(lsrs_imm, 0, 4, 24); a.emit(lsls_imm, 0, 0, 5); a.emit(ldrb_imm, 3, 7, RT_AUX); a.emit(bics_reg, 3, 0); a.emit(strb_imm, 3, 7, RT_AUX)
    if SDRUM: a.emit(mov_reg, 0, 6); a.emit(bl, "c_sdfx")                         # r1 = the value with the offset of the step (r2 kept)
    if STRETCH: a.emit(mov_reg, 0, 6); a.emit(bl, "c_stx")                        # SC38.1: the values the stretch mode replaces (r2 kept)
    a.emit(mov_reg, 0, 2); a.emit(adds_imm8, 0, 1)
    if OSC: a.emit(cmp_imm, 0, 16); a.emit(b_cond, "sd_cm", "ls"); a.emit(adds_imm8, 0, 5); a.label("sd_cm")                   # stored codes 17..21 = mailbox codes 22..26 (17..21 are the voice's own)
    a.label("sd_send")                                                                                           # r0 = code, r1 = value
    a.emit(ldrb_imm, 2, 7, RT_TAG); a.emit(lsls_imm, 1, 1, 16); a.emit(lsrs_imm, 1, 1, 16); a.emit(lsls_imm, 0, 0, 16); a.emit(orrs_reg, 1, 0)
    if RATELIMIT: a.emit(movs_imm, 3, 1); a.emit(tst_reg, 2, 3)                                                 # the tag is bit 0 of the byte (the stamp of the last message above)
    else: a.emit(cmp_imm, 2, 0)
    a.emit(b_cond, "sd_t", "eq"); a.emit(movs_imm, 3, 1); a.emit(lsls_imm, 3, 3, 23); a.emit(orrs_reg, 1, 3)
    a.label("sd_t")
    a.emit(movs_imm, 3, 1); a.emit(eors_reg, 2, 3)
    if RATELIMIT:
        a.emit(movs_imm, 3, 7); a.emit(ands_reg, 2, 3)
        a.emit(movw, 0, HAL_TICK & 0xFFFF); a.emit(movt, 0, HAL_TICK >> 16); a.emit(ldr_imm, 0, 0, 0); a.emit(movs_imm, 3, 31); a.emit(ands_reg, 0, 3); a.emit(lsls_imm, 0, 0, 3); a.emit(orrs_reg, 2, 0)
    a.emit(strb_imm, 2, 7, RT_TAG)
    a.emit(lsls_imm, 1, 1, 8)
    a.emit(mov_reg, 2, 6); a.emit(movs_imm, 3, VBS); a.emit(muls, 2, 3); a.emit(movw, 3, VB0); a.emit(adds_reg, 2, 2, 3)
    a.emit(movs_imm, 0, 0); a.emit(bl, DSP_WRITE)
    a.label("sd_x"); a.emit(pop_list, [4], pc=True)
    if HEARTBEAT:
        a.label("sd_hb")                                                                                         # nothing else to send: about every 8 ms flag one of ACT / NOTE / VEL / GATE again
        a.emit(movw, 0, HAL_TICK & 0xFFFF); a.emit(movt, 0, HAL_TICK >> 16); a.emit(ldr_imm, 0, 0, 0)
        a.emit(movs_imm, 1, 7); a.emit(tst_reg, 0, 1); bc("sd_sw" if DUALUI else "sd_x", "ne")
        if RATELIMIT:                                                                                            # every ~1 s with the track on: every value again (a switch-on done before the DSP was listening, a lost message)
            a.emit(lsrs_imm, 1, 0, 3); a.emit(movs_imm, 2, 127); a.emit(ands_reg, 1, 2); bc("sd_hn0", "ne")
            a.emit(ldrb_w, 2, 5, O_FLAGS); a.emit(lsrs_reg, 2, 6); a.emit(movs_imm, 3, 1); a.emit(ands_reg, 2, 3); bc("sd_hn0", "eq")
            a.emit(movs_imm, 1, 0xFF); a.emit(strb_imm, 1, 7, RT_DLO); a.emit(strb_imm, 1, 7, RT_DHI); a.emit(movs_imm, 1, DX_MASK if OSC else 0); a.emit(strb_imm, 1, 7, RT_DX)
            a.emit(ldrb_imm, 1, 7, RT_AUX); a.emit(movs_imm, 2, 0x6F if OSC3 else 0x0F); a.emit(orrs_reg, 1, 2); a.emit(strb_imm, 1, 7, RT_AUX); a.emit(b, "sd_x")
            a.label("sd_hn0")
        a.emit(lsrs_imm, 0, 0, 3); a.emit(movs_imm, 1, 3); a.emit(ands_reg, 0, 1)
        a.emit(ldrb_w, 2, 5, O_FLAGS); a.emit(lsrs_reg, 2, 6); a.emit(movs_imm, 3, 1); a.emit(ands_reg, 2, 3); bc("sd_hn", "ne"); a.emit(movs_imm, 0, 0)   # mode off: ACT only
        a.label("sd_hn")
        a.emit(movs_imm, 1, 1); a.emit(lsls_reg, 1, 0); a.emit(ldrb_imm, 2, 7, RT_AUX); a.emit(orrs_reg, 2, 1); a.emit(strb_imm, 2, 7, RT_AUX); a.emit(b, "sd_x")
        if DUALUI:
            a.label("sd_sw")                                                                                        # not in a heartbeat window: one of the volatile values (codes 27..34), round robin
            a.emit(movs_imm, 3, 3); a.emit(ands_reg, 3, 0); a.emit(cmp_imm, 3, 2); bc("sd_x", "ne")                                                        # only when HAL & 3 = 2 (r0 = the clock): the free slots in between belong to the heartbeat window (HAL & 7 = 0)
            a.emit(ldrb_w, 2, 5, O_FLAGS); a.emit(lsrs_reg, 2, 6); a.emit(movs_imm, 3, 1); a.emit(ands_reg, 2, 3); bc("sd_x", "eq")                      # the mode is off: nothing
            a.emit(ldrb_imm, 0, 7, RT_CNT); a.emit(lsrs_imm, 4, 0, 4); a.emit(movs_imm, 3, 7); a.emit(ands_reg, 4, 3)                                     # r4 = the cursor 0..7
            a.emit(mov_reg, 3, 4); a.emit(adds_imm8, 3, 1); a.emit(movs_imm, 2, 7); a.emit(ands_reg, 3, 2); a.emit(lsls_imm, 3, 3, 4)
            a.emit(movs_imm, 1, 0x70); a.emit(bics_reg, 0, 1); a.emit(orrs_reg, 0, 3); a.emit(strb_imm, 0, 7, RT_CNT)                                       # the cursor advances
            a.emit(mov_reg, 0, 6); a.emit(mov_reg, 1, 4); a.emit(adds_imm8, 1, 27); a.emit(bl, "c_vvaddr"); a.emit(raw, ldrsb_w(1, 0, 0))                    # r1 = the value of code 27 + cursor
            if SDRUM: a.emit(mov_reg, 0, 6); a.emit(mov_reg, 2, 4); a.emit(adds_imm8, 2, 26); a.emit(bl, "c_sdfx")
            a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, 32); a.emit(b, "sd_send")                                                                           # the mailbox code 32 + cursor

    # ---- c_vtick: head of the DSP service chain
    a.label("c_vtick")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(bl, L["c_gfst"]); a.emit(cmp_imm, 0, 0); bc("vt_chain", "eq")
    a.emit(mov_reg, 4, 0)
    a.emit(ldrb_w, 1, 4, FLAGS_BYTE); a.emit(movs_imm, 2, B_BOOT); a.emit(tst_reg, 1, 2); bc("vt_run", "ne")
    a.emit(orrs_reg, 1, 2); a.emit(strb_w, 1, 4, FLAGS_BYTE)
    tail(5)
    a.emit(ldrb_w, 0, 5, O_FLAGS); a.emit(movs_imm, 1, 0x80); a.emit(tst_reg, 0, 1)
    if SIGNED:                                                                    # the state counts only with our signature (a tail of garbage / 0xFF would switch both voices on)
        bc("vt_inv", "eq"); a.emit(ldrb_w, 0, 5, O_SIG)
        if VADRUM: a.emit(lsrs_imm, 1, 0, 4); a.emit(cmp_imm, 1, SIG_VAL >> 4); bc("vt_vol", "eq")
        else: a.emit(cmp_imm, 0, SIG_VAL); bc("vt_vol", "eq")
        if SDRUM:
            a.emit(cmp_imm, 0, 0xAF); a.emit(b_cond, "vt_inv", "ne")
            a.emit(movs_imm, 1, 0); a.emit(strb_w, 1, 5, O_SD); a.emit(strb_w, 1, 5, O_SD + 1); a.emit(movs_imm, 0, SIG_VAL); a.emit(strb_w, 0, 5, O_SIG); a.emit(b, "vt_vol")
        a.label("vt_inv"); a.emit(movs_imm, 1, 0x80)
    else:
        bc("vt_vol", "ne")
    a.emit(strb_w, 1, 5, O_FLAGS)                                                 # first use: flags = initialised, both off; the default values
    for i, v in enumerate(DEFAULTS):
        a.emit(movs_imm, 1, v); a.emit(strb_w, 1, 5, O_PAR + i); a.emit(strb_w, 1, 5, O_PAR + STRIDE + i)
    if SIGNED: a.emit(movs_imm, 0, SIG_VAL); a.emit(strb_w, 0, 5, O_SIG)
    if SDRUM: a.emit(movs_imm, 0, 0); a.emit(strb_w, 0, 5, O_SD); a.emit(strb_w, 0, 5, O_SD + 1)
    a.label("vt_vol")
    if SDRUM:                                                                     # the view is closed, the pitch page and the first half at power-up
        a.emit(ldrb_w, 0, 5, O_FLAGS); a.emit(movs_imm, 1, F_SDOPEN | F_SDPAGE | F_SDHALF); a.emit(bics_reg, 0, 1); a.emit(strb_w, 0, 5, O_FLAGS)
    a.emit(movs_imm, 1, 0)
    if CCED:
        for j in range(2 if SDRUM else 4): a.emit(strb_w, 1, 5, O_ED + j)
    for t in (0, 1):
        for j in range(8): a.emit(strb_w, 1, 5, O_RT + 8 * t + j)
    a.emit(strb_w, 1, 5, O_SAVED)
    if DUALUI:                                                                    # the volatile values of the second oscillator (heap block r4) and the default note of the second oscillator
        for t in (0, 1):
            for k, v in enumerate(DEFAULTS_V2): a.emit(movs_imm, 2, v); a.emit(strb_w, 2, 4, V2_OFF + 8 * t + k)
            a.emit(movs_imm, 2, 60); a.emit(strb_w, 2, 5, O_PAR + STRIDE * t + 13)
    a.emit(movs_imm, 0, 0x63 if OSC3 else 3); a.emit(movs_imm, 1, 0xFF); a.emit(movs_imm, 2, 60)                              # AUX: ACT + NOTE dirty; the note starts at 60 (the key tracking is always on, 60 = no offset)
    for t in (0, 1):
        a.emit(strb_w, 0, 5, O_RT + 8 * t + RT_AUX); a.emit(strb_w, 1, 5, O_RT + 8 * t + RT_DLO); a.emit(strb_w, 1, 5, O_RT + 8 * t + RT_DHI); a.emit(strb_w, 2, 5, O_RT + 8 * t + RT_NOTE)
        if OSC: a.emit(movs_imm, 1, DX_MASK); a.emit(strb_w, 1, 5, O_RT + 8 * t + RT_DX); a.emit(movs_imm, 1, 0xFF)
    if HEARTBEAT:
        for t in (0, 1): a.emit(movs_imm, 2, 100); a.emit(strb_w, 2, 5, O_RT + 8 * t + RT_VEL)
    a.label("vt_run")
    tail(5); a.emit(movs_imm, 6, 0)
    a.label("vt_l")
    a.emit(bl, "c_vsend"); a.emit(adds_imm8, 6, 1); a.emit(cmp_imm, 6, 2); bc("vt_l", "lo")
    a.label("vt_chain")
    a.emit(raw, popw([4, 5, 6, 7], lr=True)); a.emit(b_w, L["c_dtick19"])
    if CCED: cced_routines(a, L, t_ed, tail, bc)
    if EDV2: edv2_routines(a, L, t_ft, tail, bc)
    if CLEARK: clear_routines(a, L, base, t_def, tail, mulstride, bc)
    if CLRAUTO: clrauto_routine(a, base, bc)
    if DUALUI: dualui_routines(a, L, tail, mulstride, bc)
    if GRAN: gran_routines(a, tail, bc, t_gr, t_st)
    if GRSRC: grsrc_routines(a, L, t_gr)
    if CCIO: ccio_routines(a, tail, bc, movmask, t_cc, t_ln, L["stk_emit"], L["stk_mid"])
    if SDRUM: sd_routines(a, L, tail, bc, t_sd)
    if OCTLED: octled_routines(a, L, tail)
    return a.assemble()


def install(img, report, base_addr, text):
    """Append the code at base_addr and hook: the macro handlers (slots 4 / 7), the note vtable, the template view (pad hook, slot 7) and the head of the DSP service chain."""
    import ct_fw
    import build_sc14 as s14
    import drums18
    BASE = ct_fw.APP_BASE
    w = lambda addr: struct.unpack_from("<I", img, addr - BASE)[0]
    s6 = {k: int(v, 16) for k, v in report["sc06"]["labels"].items()}
    p19 = {k: int(v, 16) for k, v in report["persist19"]["labels"].items()}
    assert w(AC64_VT + 0x10) == STOCK_KNOB | 1 and w(AC64_VT + 0x1C) == STOCK_LEDS | 1, (hex(w(AC64_VT + 0x10)), hex(w(AC64_VT + 0x1C)))
    assert w(NOTE_VT[0]) == s6["c_non"] | 1 and w(NOTE_VT[1]) == s6["c_noff"] | 1
    assert w(TMPL_VT_LEDS) == s6["c_tleds"] | 1
    assert drums18.decode_bw(img, T_PAD_SITE) == s6["c_tpad"], hex(drums18.decode_bw(img, T_PAD_SITE))
    assert drums18.decode_bw(img, s14.SVC_HOOK) == p19["c_dtick19"]
    L = dict(c_shift=int(report["sc15"]["labels"]["c_shift"], 16), c_gfst=int(report["sc17"]["labels"]["c_gfst"], 16), c_dtick19=p19["c_dtick19"],
             c_tpad=s6["c_tpad"], c_tleds=s6["c_tleds"], c_settings=s6["c_settings"], c_non=s6["c_non"], c_noff=s6["c_noff"])
    if CCED: L["c_bentry"] = int(report["srcview"]["labels"]["c_bentry"], 16)
    if SD2:
        L["c_gst"] = int(report["sc14"]["labels"]["c_gst"], 16); L["c_synth"] = int(report["sc15"]["labels"]["c_synth"], 16); L["c_inject"] = s6["c_inject"]
        L["sx_pad"], L["sx_rel"], L["sx_leds"] = (w(SP_VT + 4 * k) & ~1 for k in (0, 1, 7))
        assert L["sx_pad"] == int(report["srcview"]["labels"]["c_xpad"], 16) and L["sx_leds"] == int(report["srcview"]["labels"]["c_xleds"], 16), (hex(L["sx_pad"]), hex(L["sx_leds"]))
    if OCTLED: L["c_ledtask"] = int(report["leds18"]["labels"]["c_ledtask"], 16)
    if FXSEQ2: L["c_slotcol"] = int(report["sc17"]["labels"]["c_slotcol"], 16)
    if CCIO:
        import build_shared_channels as _sc
        for site, want in ((STK_EMIT, "push {r2, r3, r4, r5, r6, lr}|mov r4, r0"), (STK_MIDIIN, "ldrb r0, [r4, #0x14]|lsls r1, r0, #0x1e")):
            got = "|".join(_sc.disasm(bytes(img[site - BASE:site - BASE + 4]), site))
            assert got == want, (hex(site), got)
        L["stk_emit"] = bytes(img[STK_EMIT - BASE:STK_EMIT - BASE + 4])
        L["stk_mid"] = bytes(img[STK_MIDIIN - BASE:STK_MIDIIN - BASE + 4])
    code, labels = arm_code(base_addr, L)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    if FXSEQ:                                                                     # build_sc17's c_fxsq (movs r0, #0; bx lr) -> b.w c_fsqbits
        fx = int(report["sc17"]["labels"]["c_fxsq"], 16)
        assert bytes(img[fx - BASE:fx - BASE + 4]) == bytes([0x00, 0x20, 0x70, 0x47]), bytes(img[fx - BASE:fx - BASE + 4]).hex()
        img[fx - BASE:fx - BASE + 4] = b_w(fx, labels["c_fsqbits"])
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, AC64_VT + 0x10 - BASE, labels["c_vknob"] | 1)
    struct.pack_into("<I", img, AC64_VT + 0x1C - BASE, labels["c_vkleds"] | 1)
    struct.pack_into("<I", img, NOTE_VT[0] - BASE, labels["c_vnon"] | 1)
    struct.pack_into("<I", img, NOTE_VT[1] - BASE, labels["c_vnoff"] | 1)
    struct.pack_into("<I", img, TMPL_VT_LEDS - BASE, labels["c_vleds"] | 1)
    img[T_PAD_SITE - BASE:T_PAD_SITE - BASE + 4] = b_w(T_PAD_SITE, labels["c_vpad"])
    img[s14.SVC_HOOK - BASE:s14.SVC_HOOK - BASE + 4] = b_w(s14.SVC_HOOK, labels["c_vtick"])
    if SD2:
        for k, lab in ((0, "c_sxpad"), (1, "c_sxrel"), (7, "c_sxleds")): struct.pack_into("<I", img, SP_VT + 4 * k - BASE, labels[lab] | 1)
    if SDRUM:
        assert w(TMPL_VT_REL) == STK_REL | 1, hex(w(TMPL_VT_REL))
        struct.pack_into("<I", img, TMPL_VT_REL - BASE, labels["c_sdrel"] | 1)
    if CCIO:                                                                      # nothing may branch into the displaced bytes
        import build_sc04 as s4
        targets = s4.branch_targets(Path(__file__).resolve().parents[1] / "re/app.asm")
        for site in (STK_EMIT, STK_MIDIIN):
            assert not any(x in targets for x in range(site + 1, site + 4)), hex(site)
        img[STK_EMIT - BASE:STK_EMIT - BASE + 4] = b_w(STK_EMIT, labels["c_vplay"])
        img[STK_MIDIIN - BASE:STK_MIDIIN - BASE + 4] = b_w(STK_MIDIIN, labels["c_vmin"])
    if CCED:
        assert drums18.decode_bw(img, BTN_STOCK) == L["c_bentry"], hex(drums18.decode_bw(img, BTN_STOCK))
        img[BTN_STOCK - BASE:BTN_STOCK - BASE + 4] = b_w(BTN_STOCK, labels["c_vbtn"])
    if OCTLED:
        from thumb import bl as bl_enc
        for c in (0x08033B46, 0x0803415A):
            assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, L["c_ledtask"]), hex(c)
            img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_vledtask"])
    return labels, code


def install_fxcap(img, report, base_addr):
    """SC23.3, after fxparams.install: append the FX send cap and put it in front of fxparams' knob handler (slot 4 of the FX sub-views)."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    L = dict(c_shift=int(report["sc15"]["labels"]["c_shift"], 16), c_settings=int(report["sc06"]["labels"]["c_settings"], 16),
             c_fxknob=int(report["fxparams"]["labels"]["c_fxknob"], 16), c_fxsub=int(report["fxparams"]["labels"]["c_fxsub"], 16))
    assert struct.unpack_from("<I", img, FX_SUB_VT + 0x10 - BASE)[0] == L["c_fxknob"] | 1
    a = Asm(base_addr)
    zc = [0]
    def bc(target, cond):
        zc[0] += 1; n = f"_f{zc[0]}"
        a.emit(b_cond, n, INV[cond]); a.emit(b, target); a.label(n)
    def tail(rd):
        a.emit(movw, rd, TAIL & 0xFFFF); a.emit(movt, rd, TAIL >> 16)
    fxcap_routines(a, L, tail, bc)
    code, labels = a.assemble()
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, FX_SUB_VT + 0x10 - BASE, labels["c_fxcap"] | 1)
    return labels, code
