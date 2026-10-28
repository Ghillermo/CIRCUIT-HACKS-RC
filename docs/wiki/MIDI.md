# MIDI

*[Versión en español](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/MIDI-ES) · [Home](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Home) · [Guide by views](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html)*

How the mod talks MIDI: its own behaviours, the new CCs and NRPNs, and the mod matrix and macro destinations.

## MIDI: own behaviours, new CCs and NRPNs

Everything new goes out and comes in over CC / NRPN, following the Setup's CC Tx / CC Rx filters. The original device's parameters keep the numbers of Novation's guide (see the next section).

### Channels (as on the original, changeable in Setup)
Synth 1 = channel 1, Synth 2 = channel 2, drums = channel 10, project and Master FX = channel 16 (those of Novation's guide); MIDI 1 / 2 = the channels chosen for them in Setup.

### Own behaviours
| What | How |
|---|---|
| **External keyboard on MIDI 1 / 2** *(since RC2)* | Notes coming in on the channel of MIDI 1 / 2 (USB or DIN) play its own synth and are recorded; they are not sent on to the output. |
| **External keyboard to the arpeggiator** *(Beta 3.41 only)* | Setup, Note button: notes coming in on the channel of Synth 1 / 2 or MIDI 1 / 2 go through its arpeggiator. |
| **Patch flip** | MIDI 1 / 2 Preset view, pad 26: every note of the track goes out as a Program Change on the track's channel. |
| **The project's Program Change** *(since RC2)* | Setup, pads 29 / 30: listen channel and output channel (16 by default); what arrives on the listen one is sent again on the output one. |
| **MIDI Thru: Merge and Filter** | Advanced Setup, Duplicate: Thru (hardware), Out 2, Merge (DIN In + the device's MIDI), Filter (DIN In without the device's channels). No SysEx. |
| **USB merge** *(Beta 3.41 only)* | Advanced Setup, pad 23: what comes in on the DIN In also goes out over USB (without the clock with Clock Tx, without SysEx). |
| **General MIDI mode of the drums** *(Beta 3.41 only)* | Setup, K4 / K5-K8: the hits of Drum 1-4 go out as the GM note chosen instead of 60 / 62 / 64 / 65. Inside, the sound is the same. |
| **Stereo drum pair** *(Beta 3.41 only)* | Drum 2 / 4's notes play it alone, on the right; its pattern neither sounds nor goes out over MIDI while the pair lasts. |
| **Record the internal routings** *(since RC2)* | Setup, Record: what a MIDI track sends to a synth on the same channel is also recorded in the synth; *(Beta 3.41 only)* nothing is recorded in a track muted in the Mixer. |
| **New knobs** | Turning them (also with Clear) sends their CC / NRPN; receiving it moves the knob. The Mixer's level to 100 / 0 (Shift + knob) goes out as a turn. |
| **No MIDI** | The own synth's mod matrix, the FM, the voice mode and the destinations of the sequenceable and *(Beta 3.41 only)* non-sequenceable knobs have no CC / NRPN: they are saved in the own patches. |
| **Selecting an NRPN** | CC 99 (MSB), CC 98 (LSB), CC 6 (value), in that order; the device remembers the chosen NRPN until the next CC 99 / 98. |

### MIDI track engine (MIDI 1 / 2)

The MIDI track's channel. Values 0-127; bipolar ones, 64 = centre. Sent when the knob turns (also with Clear) and received on the same number. «Page / knob» = where it is in the Preset view with the engine on (pads 1-5 = pages). In the granular engine page 2 uses the same numbers with another meaning (in brackets).

| Code | Parameter | Message | Page / knob |
|---|---|---|---|
| 1 | Filter | CC 74 | 1 / K5 |
| 2 | Resonance | CC 71 | 1 / K6 |
| 3 | Envelope → filter | CC 79 | 1 / K4 |
| 4 | LFO → filter | NRPN 4:4 | 1 / Shift + K4 |
| 5 | Attack | CC 73 | 1 / K1 |
| 6 | Decay | CC 75 | 1 / Shift + K2 |
| 7 | Sustain | CC 70 | 1 / Shift + K1 |
| 8 | Release | CC 72 | 1 / K2 |
| 9 | Effect amount | CC 91 | 1 / K8 |
| 10 | VCA gain | CC 59 | 1 / Shift + K6 |
| 11 | LFO speed | NRPN 0:76 | 1 / K7 |
| 12 | LFO → level | NRPN 4:12 | 1 / Shift + K3 |
| 13 | Effect type | NRPN 4:13 | 1 / Shift + K8 |
| 15 | Envelope → level | NRPN 4:15 | 1 / K3 |
| 16 | Filter type | NRPN 4:16 | 1 / Shift + K5 |
| 17 | TUNE (granular: pitch) | CC 26 | 2 / K1 |
| 18 | FINE (granular: size) | CC 27 | 2 / Shift + K1 |
| 19 | WAVE (granular: position) | CC 20 | 2 / K7 |
| 20 | SHAPE (granular: density) | CC 21 | 2 / K2 |
| 21 | LFO → pitch (granular: scan) | NRPN 4:21 | 2 / K5 |
| 22 | Envelope → pitch (granular: env → position) | NRPN 4:22 | 2 / K3 |
| 23 | Envelope → shape (granular: zone) | NRPN 4:23 | 2 / K4 |
| 24 | LFO → shape (granular: LFO → position) | NRPN 4:24 | 2 / K6 |
| 25 | Envelope → morph (granular: source) | NRPN 4:25 | 2 / Shift + K8 |
| 26 | LFO → morph (granular: note mode) | NRPN 4:26 | 2 / K8 |
| 27 | TUNE 2 (granular: LFO → size) | CC 37 | 3 / K1 |
| 28 | FINE 2 (granular: fine) | CC 39 | 3 / K5 (RC2) · 3 / Shift + K1 (RC0.9) |
| 29 | WAVE 2 (granular: pitch spread; Beta 3.41: stereo) | CC 30 | 3 / K7 |
| 30 | SHAPE 2 (granular: window) | CC 31 | 3 / K2 |
| 31 | MIX OSC 1 ↔ OSC 2 | CC 52 | 2 / Shift + K2 · 3 / K3 (RC2) |
| 32 | BITSYNC | NRPN 4:32 | 2 / Shift + K3 · 3 / K6 (RC2) |
| 33 | FM (granular: position spread) | NRPN 4:33 | 3 / K4 (RC2) · 3 / Shift + K2 (RC0.9) |
| 34 | RING (granular: reverse; Beta 3.41: bipolar, reverse / pitch spread) | CC 54 | 3 / K8 (RC2) · 3 / Shift + K3 (RC0.9) |

**Sequenceable knobs** (page 4: recorded into the pattern with Record): TUNE, Release, Envelope → level, Envelope → filter, Filter, Resonance, LFO speed, Effect. *Beta 3.41 only:* the eight destinations are chosen with Shift + knob.

### Drums

The drums channel (Setup). **CC 99 = 5, 6, 7, 8** (Drum 1-4), **CC 98 = LSB**, **CC 6 = value**. The stock knobs (pitch, decay, distortion, EQ) keep their original CCs. *Beta 3.41 only:* with the **General MIDI mode** (Setup view, K4) the notes of Drum 1-4 go out as each one's GM note (K5-K8, 35-81; by default 36 / 38 / 42 / 46) instead of 60 / 62 / 64 / 65.

| LSB | Parameter | Values |
|---|---|---|
| 1 | Envelope → pitch | 0-127, 64 = 0 |
| 2 | Ring mod: frequency | 0-127 |
| 3 | LFO: amount (> 64 tremolo; < 64 vibrato, Beta 3.41 only: start scan) | 0-127, 64 = 0 |
| 4 | LFO: speed | 0-127, 64 = centre |
| 5 | Envelope → cutoff | 0-127, 64 = 0 |
| 6 | Resonance | 0-127 |
| 7 | Envelope shape | 0-127, 64 = centre |
| 8 | Ring mod: amount | 0-127 |
| 9 | Filter mode | 0 stock tilt EQ, 1 band-pass, 2 notch, 3 comb, 4 DJ |
| 10 | Sample start | 0-120 (/128; since RC2.09 the whole sample, before it reached the end at 32); RC0.9: 0-15 (/64) |
| 11 | Bitcrush | 0-15 |
| 12 | Distortion type | 0 stock, 1 soft, 2 hard, 3 fold |
| 13 | Cut from the end (since RC2) | 0-120 (/128) |
| 14 | Attack (since RC2) | 0-127 |

### Master FX

Channel 16. **CC 99 = 9**, **CC 98 = 4 × effect + knob** (knob 0-3 = K1-K4), **CC 6 = value**.

| LSB | Effect | K1-K4 |
|---|---|---|
| 0-3 | Gater | division, depth, width, smoothing |
| 4-7 | Auto-Filter (pads 2 / 3) | speed, depth, resonance, centre |
| 8-11 | Digitise | sample rate, bits, delay throw (RC2), envelope (RC2) |
| 12-15 | Phaser | speed, depth, feedback, mix |
| 16-19 | Glitch (RC0.9: Vinyl) | speed, repeat, delay, chaos / overload (RC0.9: crackle, hiss, tone, wear) |

## Mod matrix and macro destinations

The stock synths (Synth 1 / 2) have Novation's matrix and macros; the MIDI 1 / 2 own synth has its matrix and its lanes.

The official reference is Novation's **Programmer's Reference Guide**, version 3 ([PDF](https://fael-downloads-prod.focusrite.com/customer/prod/downloads/circuit_tracks_programmer_s_reference_guide_v3.pdf), on the [Circuit Tracks downloads page](https://downloads.novationmusic.com/novation/circuit/circuit-tracks)). For every macro slot it gives: «macro knob 1 destination A NRPN 3:0 0 – 70 0» (Novation, *Circuit Tracks Programmer's Reference Guide* v3, «Macro Knobs»).

### Synth 1 / 2 mod matrix (stock, unchanged)
- Edited from Components or over MIDI (the synth's channel); the device has no view for it. Every slot: source 1, source 2, depth (−64..63) and destination. The official guide lists 12 slots from **NRPN 1:83** (source 1, source 2, —, depth, destination: 5 numbers per slot); the firmware has 20, with the same pattern.
- **Sources (0-12):** 0 direct, 4 velocity, 5 keyboard (note), 6 / 7 LFO 1 (unipolar / bipolar), 8 / 9 LFO 2 (unipolar / bipolar), 10 amp envelope, 11 filter envelope, 12 envelope 3.
- **Destinations (0-17):** 0 pitch of both oscillators, 1 / 2 pitch of oscillator 1 / 2, 3 / 4 v-sync 1 / 2, 5 / 6 pulse width / index 1 / 2, 7 / 8 level of oscillator 1 / 2, 9 noise level, 10 ring mod level, 11 filter drive, 12 filter frequency, 13 resonance, 14 / 15 LFO 1 / 2 rate, 16 amp envelope decay, 17 filter envelope decay.

### Synth 1 / 2 macros (stock) and their editor *(since RC2)*
- 8 macros per patch, position = **CC 80-87**; every macro, 4 slots A-D. Slot r (0-3) of macro k (1-8): **NRPN 3:(16 (k − 1) + 4 r)** = destination, + 1 start, + 2 end (the stretch of the knob's travel, 0 / 127 by default), + 3 depth (64 = 0).
- The official guide gives the destination as «0 – 70» without naming them: the list below names each one (70 destinations, 0-69).
- **On the device:** [source view](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#synth-fuente), pad 32 = editor (slot, start, end, destination, depth). The edits go into the project's patch; Clear + pad twice in the [Preset view](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#synth-preset) saves it to the pack.
- The editor's knob walks the destinations with a CC first (by CC number), then the NRPN-only ones; on the pads, white = CC, light blue / magenta / violet = NRPN of banks 0 / 1 / 2.

### The MIDI 1 / 2 own synth's matrix (own) *(since RC2.02)*
- [MIDI Preset view](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#midi-preset) with the engine on, **pad 6**: the 8 knobs are 8 **sources**: K1 velocity, K2 note, K3 random per note, K4 LFO 2, K5 envelope 2, K6 a drum's hit, K7 position in the pattern, K8 stepped random (*(Beta 3.41 only)* LFO 2 also synced to tempo).
- **The knob's position is the destination and the amount:** left = off; turning right walks every parameter of the knob pages (page 1's, then page 2, page 3 and those of page 5 not met before), 16 steps per destination, the amount growing inside each stretch. LED = the colour of the destination's page; brightness = amount.
- Several sources on the same destination add up; the parameter's stored value does not change. Details: [Mod matrix](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#midi-matriz).

### The own synth's sequenceable (page 4) and non-sequenceable knob destinations *(Beta 3.41 only)*
- The 8 sequenceable knobs (page 4) are the automation lanes (by default: TUNE, Release, Env → level, Env → filter, Filter, Resonance, LFO speed, Effect). **Shift + knob** = its destination, among the same parameters and colours as the matrix; **Clear held, then Shift + knob** = the default one. Saved with the own patch and with the project. Details: [Knob pages](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#midi-knobs).
- **Non-sequenceable knobs** (Shift + pad 4): the same choice of destination, on 8 knobs that are not lanes; by default Attack, Decay, Sustain, SHAPE, LFO → filter, Env → pitch, MIX OSC 1 / 2, VCA gain; saved with the own patches.

### Step-drummer destinations
- MIDI 1 / 2: pads 17-24 of its view = the engine parameter every step moves; Synth 1 / 2: macros 1-8. Details: [Step-drummer](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#step-drummer).

### The 70 macro destinations

| Destination | Parameter | CC / NRPN |
|---|---|---|
| 0 | Portamento rate | CC 5 |
| 1 | Post FX level | CC 59 |
| 2 | Osc 1 wave interpolate | CC 20 |
| 3 | Osc 1 pulse width index | CC 21 |
| 4 | Osc 1 virtual sync depth | CC 22 |
| 5 | Osc 1 density | CC 24 |
| 6 | Osc 1 density detune | CC 25 |
| 7 | Osc 1 semitones | CC 26 |
| 8 | Osc 1 cents | CC 27 |
| 9 | Osc 2 wave interpolate | CC 30 |
| 10 | Osc 2 pulse width index | CC 31 |
| 11 | Osc 2 virtual sync depth | CC 33 |
| 12 | Osc 2 density | CC 35 |
| 13 | Osc 2 density detune | CC 36 |
| 14 | Osc 2 semitones | CC 37 |
| 15 | Osc 2 cents | CC 39 |
| 16 | Osc 1 level | CC 51 |
| 17 | Osc 2 level | CC 52 |
| 18 | Ring mod level | CC 54 |
| 19 | Noise level | CC 56 |
| 20 | Filter frequency | CC 74 |
| 21 | Filter resonance | CC 71 |
| 22 | Filter drive | CC 63 |
| 23 | Filter tracking | CC 69 |
| 24 | Env 2 to filter frequency | CC 79 |
| 25 | Env 1 attack | CC 73 |
| 26 | Env 1 decay | CC 75 |
| 27 | Env 1 sustain | CC 70 |
| 28 | Env 1 release | CC 72 |
| 29 | Env 2 attack | NRPN 0:1 |
| 30 | Env 2 decay | NRPN 0:2 |
| 31 | Env 2 sustain | NRPN 0:3 |
| 32 | Env 2 release | NRPN 0:4 |
| 33 | Env 3 delay | NRPN 0:14 |
| 34 | Env 3 attack | NRPN 0:15 |
| 35 | Env 3 decay | NRPN 0:16 |
| 36 | Env 3 sustain | NRPN 0:17 |
| 37 | Env 3 release | NRPN 0:18 |
| 38 | LFO 1 rate | NRPN 0:76 |
| 39 | LFO 1 rate sync | NRPN 0:77 |
| 40 | LFO 1 slew rate | NRPN 0:72 |
| 41 | LFO 2 rate | NRPN 0:85 |
| 42 | LFO 2 rate sync | NRPN 0:86 |
| 43 | LFO 2 slew rate | NRPN 0:81 |
| 44 | Distortion level | CC 91 |
| 45 | Chorus level | CC 93 |
| 46 | Chorus rate | NRPN 1:25 |
| 47 | Chorus feedback | NRPN 1:27 |
| 48 | Chorus mod depth | NRPN 1:28 |
| 49 | Chorus delay | NRPN 1:29 |
| 50 | Mod matrix 1 depth | NRPN 1:86 |
| 51 | Mod matrix 2 depth | NRPN 1:91 |
| 52 | Mod matrix 3 depth | NRPN 1:96 |
| 53 | Mod matrix 4 depth | NRPN 1:101 |
| 54 | Mod matrix 5 depth | NRPN 1:106 |
| 55 | Mod matrix 6 depth | NRPN 1:111 |
| 56 | Mod matrix 7 depth | NRPN 1:116 |
| 57 | Mod matrix 8 depth | NRPN 1:121 |
| 58 | Mod matrix 9 depth | NRPN 1:126 |
| 59 | Mod matrix 10 depth | NRPN 2:3 |
| 60 | Mod matrix 11 depth | NRPN 2:8 |
| 61 | Mod matrix 12 depth | NRPN 2:13 |
| 62 | Mod matrix 13 depth | NRPN 2:18 |
| 63 | Mod matrix 14 depth | NRPN 2:23 |
| 64 | Mod matrix 15 depth | NRPN 2:28 |
| 65 | Mod matrix 16 depth | NRPN 2:33 |
| 66 | Mod matrix 17 depth | NRPN 2:38 |
| 67 | Mod matrix 18 depth | NRPN 2:43 |
| 68 | Mod matrix 19 depth | NRPN 2:48 |
| 69 | Mod matrix 20 depth | NRPN 2:53 |
