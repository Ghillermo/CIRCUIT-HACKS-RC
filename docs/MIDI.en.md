# MIDI reference of the new features — CIRCUIT-HACKS (RC2.09)

The CCs / NRPNs the mod adds. The original device's parameters (synths, drums, mixer, FX) keep the numbers of Novation’s *Programmer’s Reference Guide*. Everything follows the CC Tx / CC Rx filters of the Setup view.

## Selecting an NRPN

Send **CC 99** (MSB), **CC 98** (LSB) and **CC 6** (value), in that order. The device remembers the chosen NRPN until the next CC 99 / 98.

## MIDI track engine (MIDI 1 / 2)

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
| 29 | WAVE 2 (granular: pitch spread; Beta 3.22: stereo) | CC 30 | 3 / K7 |
| 30 | SHAPE 2 (granular: window) | CC 31 | 3 / K2 |
| 31 | MIX OSC 1 ↔ OSC 2 | CC 52 | 2 / Shift + K2 · 3 / K3 (RC2) |
| 32 | BITSYNC | NRPN 4:32 | 2 / Shift + K3 · 3 / K6 (RC2) |
| 33 | FM (granular: position spread) | NRPN 4:33 | 3 / K4 (RC2) · 3 / Shift + K2 (RC0.9) |
| 34 | RING (granular: reverse; Beta 3.22: bipolar, reverse / pitch spread) | CC 54 | 3 / K8 (RC2) · 3 / Shift + K3 (RC0.9) |

**Page 4** (sequenceable: recorded into the pattern with Record): TUNE, Release, Envelope → level, Envelope → filter, Filter, Resonance, LFO speed, Effect. *Beta 3.22 only:* the eight destinations are chosen with Shift + knob.

## Drums

The drums channel (Setup). **CC 99 = 5, 6, 7, 8** (Drum 1-4), **CC 98 = LSB**, **CC 6 = value**. The stock knobs (pitch, decay, distortion, EQ) keep their original CCs. *Beta 3.22 only:* with the **General MIDI mode** (Setup view, K4) the notes of Drum 1-4 go out as each one's GM note (K5-K8, 35-81; by default 36 / 38 / 42 / 46) instead of 60 / 62 / 64 / 65.

| LSB | Parameter | Values |
|---|---|---|
| 1 | Envelope → pitch | 0-127, 64 = 0 |
| 2 | Ring mod: frequency | 0-127 |
| 3 | LFO: amount (> 64 tremolo; < 64 vibrato, Beta 3.22 only: start scan) | 0-127, 64 = 0 |
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

## Master FX

Channel 16. **CC 99 = 9**, **CC 98 = 4 × effect + knob** (knob 0-3 = K1-K4), **CC 6 = value**.

| LSB | Effect | K1-K4 |
|---|---|---|
| 0-3 | Gater | division, depth, width, smoothing |
| 4-7 | Auto-Filter (pads 2 / 3) | speed, depth, resonance, centre |
| 8-11 | Digitise | sample rate, bits, delay throw (RC2), envelope (RC2) |
| 12-15 | Phaser | speed, depth, feedback, mix |
| 16-19 | Glitch (RC0.9: Vinyl) | speed, repeat, delay, chaos / overload (RC0.9: crackle, hiss, tone, wear) |

## Program Change

**Project:** listen and output channel in the Setup view, pads 29 / 30 (16 by default; since RC2); what arrives on the listen channel is sent again on the output one. **Patch flip:** every note of MIDI 1 / 2 goes out as a Program Change on the track's channel (MIDI Preset view, pad 26). **Notes coming in (since RC2.08):** notes arriving on the channel of MIDI 1 / 2 play its own synth and are recorded; they are not sent again to the output. *Beta 3.22 only:* with the **USB merge** (Advanced Setup, pad 23) everything coming in on the DIN In also goes out over USB (without its clock with Clock Tx, without SysEx).
