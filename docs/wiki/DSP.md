# DSP

*[Versión en español](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/DSP-ES) · [Home](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Home) · [Guide by views](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html)*

The sound side of the mod: the synth engines of the MIDI tracks, the new drum controls and the effects.

The **MIDI 1 / 2** tracks get their own synth inside the device, with several engines on the engine row of their Preset view: an
**oscillator** that morphs between sine, triangle, saw (up to a seven-saw **supersaw**) and pulse, with wavefolding; **two oscillators** with FM, sync,
ring and mix; a **VA-drum** for percussive sounds; a **granular** engine that plays grains of a sample or of the live capture; a **4-operator FM**
engine with 16 algorithms; and a **sample mode** that plays the pack's samples across the keyboard, in stereo if you like. It has a filter with
several types, envelopes, an LFO with seven shapes (synced to the tempo if you want), a **mod matrix**, **polyphony** with eight voice modes, and
eight automation lanes. The **drums** gain envelopes, a ring modulator, an LFO, filter modes, sample start and end, attack, bitcrush and distortion
types. **Master FX** adds performance effects to the whole mix, and the **FX** and **Sidechain** views expose the reverb, delay, side-chain and
master compressor settings.

## MIDI 1 / 2 Preset view

*How to get there:* Press **MIDI 1** or **MIDI 2**, then **Preset**. Besides the stock templates, the track's own synth lives here.

- **A synth on each MIDI track** — MIDI 1 and 2 sound on the unit itself with their engine (processed line input, oscillator, two oscillators, VA-drum, granular, sample mode; *(Beta 3.36 only)* FM) and still send MIDI.
- **FX sequencer** — an engine with no sound: it triggers Master FX effects on the steps you choose.
- **Own-synth patches** *(since RC2)* — 64 sounds a pack for those engines, one touch away.
- **Mod matrix** *(since RC2.02)* — eight sources (velocity, note, random, LFO 2, envelope 2, a drum hit, the pattern position, stepped random) that move any parameter of the engine.
- **Patch flip** — every note sends a program change: the outside gear changes sound step by step.
- **CC editor** — changes which CC each knob of the template sends, without Components.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#midi-preset)

## Knob pages of the MIDI 1 / 2 engine

*How to get there:* With the engine on, pads 1-5 of the Preset view pick what the 8 knobs do; Shift gives a second layer.

- **VCA-VCF** — level and filter with their envelope and LFO; with Shift, the filter type and the effect type.
- **Oscillators** — a waveform that morphs from sine to square, and a second oscillator with FM, ring and sync.
- **Granular** — turns a sample into textures: grains that read it at another place, speed or direction, to freeze, stretch or slice it.
- **Page 4** — the 8 parameters that can be recorded as automation (*(Beta 3.36 only)*: with Shift + knob, any of the 33; Record + step = a snapshot of the values).

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#midi-knobs)

## 4-operator FM

*How to get there:* *(Beta 3.36 only)* MIDI 1 / 2: Preset view, a tap on **pad 27** and **pad 24** of the engine row (violet). **Pad 7** opens its knob page (bright violet on it).

| Knob | Alone | With Shift |
|---|---|---|
| K1-K4 | Ratio of operators 1-4: 0.5 … 16 (green = whole, light blue = and a half, teal = inharmonic: 0.71, 1.41, 4.24). Each ratio spans 5-6 clicks: the first is exact and each further one **detunes** +2.5 cents (up to about +12; LED half bright) | Centre = attack 0. **To the right:** the operator's attack (0 … about 3 s; light blue). **To the left:** the operator is **percussive** with its own decay, shorter the further left (3 ms … 8 s; red) |
| K5 | Level of operator 1 (orange) | Algorithm (16, 8 clicks each; its family's colour) |
| K6 | Level of operator 2 | Feedback (magenta) |
| K7 | Level of operator 3 | Noise (white) |
| K8 | Level of operator 4 | Release (blue) |

- **Choosing the algorithm with the pads:** on the FM page, **hold pad 7**: pads 9-24 show the 16 algorithms (their family's colour; the current one bright). **Press one**: it is chosen and the tonic sounds while you hold it (**Shift + pad**: no sound). Letting go of pad 7 brings the patches back.
- **While a ratio turns** (K1-K4) pads 9-32 show the 24 ratios for 1.5 s (the current one bright, white when detuned); while the algorithm turns (Shift + K5), pads 9-24 show the algorithms. Meanwhile those pads load no patch.
- **It is a variant of the oscillator:** the note, TUNE / FINE, the pitch envelope and the vibrato of page 2 still apply; after it, the filter, the effect and the matrix as with the oscillator. One note at a time (the last one wins); with the retrigger off (Shift + pad 29) a legato note does not restart the attacks.
- **The loudness comes from the operators' envelopes**: the engine's VCA stays open (velocity still sets the level) and page 1's ADSR moves the filter, the pitch and the brightness.
- **Brightness:** SHAPE (K2 of the OSC 1 page), Env → shape (K4) and LFO → shape (K6) change how much the modulators modulate (× 0.27 … × 3.7; SHAPE 50 = no change), and the feedback too. So the engine's ADSR, its LFO, the matrix, the page 4 lanes and the step-drummer move the FM's timbre.
- **Velocity** also sets the brightness (how much, by algorithm) and how far the kick drops. **High notes** modulate less and decay sooner (by algorithm, as on a DX7). At very high notes and ratios the engine limits the modulation so it does not alias (except in the percussive ones, where it is part of the sound).
- **The level** of a carrier is its loudness; of a modulator, how much it modulates.
- **A/R envelopes with a fixed sustain:** while the note is held, a **sustained** operator stays up after its attack; a **percussive** one (the algorithm says so, or its Shift + knob to the left) falls even while the note is held. On release, all fall with the release (one made percussive by its knob, with the shorter of its decay and the release). **The release is one for all and longer the harder the note**; the algorithm shortens or lengthens it per operator.
- **The feedback** is the DX7's (the average of the last two outputs): a clean saw over more of the range; the knob is finer at the bottom.
- The percussive and bell algorithms start every hit with the phases at zero: every hit sounds the same.
- **Noise:** white, with the envelope of the operator the algorithm names (1, except the snare's), added after the FM, in any algorithm.
- **Clear + pad 7** = a **playable voice of the chosen algorithm** (the table's «Voice» column); **Clear + knob** = its value in that voice (Clear + Shift + K5: the stack). **Clear + MIDI 1 / 2** = the whole engine to its defaults (the FM to the stack).
- **Saved with the own-synth patches** (with the engine on FM). A patch from Beta 3.22 or before is adapted when it loads (the attacks to the right half of their knob, the same feedback, the ratios exact); an earlier beta loads a new one with FM off. No CC / NRPN. Another engine of the row (or Shift + pad 27) turns it off.

| # | Algorithm | Family | Voice (Clear + pad 7) |
|---|---|---|---|
| 1 | 4 → 3 → 2 → 1 (stack) | classic (white) | the initial one |
| 2 | 3 and 4 → 2 → 1 | | brass |
| 3 | 4 → 1 and 3 → 2 → 1 | | electric piano |
| 4 | 4 → 3 → 1 and 2 → 1 | | bass |
| 5 | two stacks: 4 → 3 and 2 → 1 (carriers 1 and 3) | | electric piano 2 |
| 6 | 4 → 1, 2 and 3 (three carriers) | | pad |
| 7 | 4 → 3; 2 and 1 alone (three carriers) | | harpsichord |
| 8 | organ: all four carriers | | organ (16', 8', 4', 2 2/3' stops) |
| 9 | kick: 2 → 1; operator 4 is the pitch drop (its level = how far, up to 3 octaves; its release = how long) | percussive (red) | kick (about 3 octaves of fast drop) |
| 10 | snare: 2 → 1 + noise with operator 3's envelope; pitch drop from 4 | | snare |
| 11 | metal / hi-hat: 2, 3 and 4 → 1 with inharmonic ratios (× 1.41, 2.71, 3.49) | | hi-hat |
| 12 | tom / zap: 3 → 2 → 1; pitch drop from 4 | | tom |
| 13 | bell: 2 → 1 and 4 → 3, inharmonic ratios (× 3.5, × 2.76) | bells (teal) | bell |
| 14 | tubular bell: 2 and 3 → 1 (× 2.76, × 5.4), 4 a carrier | | tubular bell |
| 15 | strings: two stacks (2 → 1, 4 → 3) detuned against each other | strings (green) | strings (slow attack) |
| 16 | ensemble: 4 → 1, 2 and 3, three detuned carriers | | ensemble |

## Sample mode and sample picker

*How to get there:* *(since RC2)* MIDI 1 / 2 with the engine on **sample** (pad 27 cyan, after the granular): **Note twice** (expanded Note view). The track plays a pack sample one-shot, at the pitch of each note.

- **Pitched drums on a MIDI track** — any pack sample plays at the pitch of each note, like a drum machine with tunable samples.
- **A different sample per step** — the sample flip changes sample step by step with no other track; it can be recorded live too.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#midi-muestra)

## Mod matrix

*How to get there:* *(since RC2.02)* MIDI 1 / 2 with the engine on: Preset view, **pad 6**. The 8 knobs become 8 modulation sources.

| Knob | Source | With Shift |
|---|---|---|
| K1 | The note's velocity | — |
| K2 | The note (C3 = 0; one octave = a quarter of the travel) | — |
| K3 | Random: a new value at each note | — |
| K4 | LFO 2 | Shape × rate: triangle (green, the initial one), saw (magenta), square (red), sample & hold (white: steps), slewed sample & hold (violet: gliding); the engine LFO's colours; in each shape, 0.05 to 20 Hz ; *(Beta 3.36 only)*: in each shape, the left half of its stretch synced and the right half free (0.2) |
| K5 | Envelope 2: attack and decay from each note | Attack × decay: attack 0 (white), short (light blue), medium (teal), long (blue); in each, the decay from 20 ms to 4 s |
| K6 | A drum hit: a decay from each hit | Drum 1-4 (orange, yellow, violet, teal) × its decay |
| K7 | The pattern position: from 0 on the first step to full on the last | — |
| K8 | Stepped random: a new value every N sequencer steps | N = 1, 2, 4, 8 or 16 steps |

- **The knob's position is the destination and the amount.** Fully left = off. Turning right goes through **every parameter of the knob pages** (33: page 1's, then page 2's, page 3's and the page 5 ones not seen before), one stretch each: inside a stretch the amount grows from 1/16 to full (*(Beta 3.36 only)*: from 0 to full: the stretch's first step is the destination with no amount, its LED dim); into the next stretch the destination changes and the amount starts again.
- **Slow knobs:** two clicks a step, 16 steps a destination.
- **The LED's colour is the destination page's** (the colours of pads 1-5: orange VCA-VCF, green OSC 1, teal OSC 2), its **brightness** the amount; dark = no destination.
- **While you turn a source** (and 1.5 s after), the pads show where its destination lives: its page pad lights up and pads 9-16 / 17-24 are that page's K1-K8 / Shift + K1-K8 (dim the ones with a parameter, bright the destination). While they show, pads 9-24 do not load patches.
- **Full amount** = the whole source sweeps the parameter's whole range. The bipolar sources (note, random, LFO 2, stepped random) go up and down; the others only up. The parameter's stored value does not change: the matrix is added when it is sent.
- Several sources can share a destination (they add up). TUNE moves in semitones and FINE in fractions; with the granular engine, its ranges; in sample mode the sample parameter picks the sample (from the capture to 64) and only TUNE changes the pitch.
- **Clear + knob** = that source off; **Clear + Shift + knob** = its parameter back to the default; **Clear + pad 6** = all off.
- **Saved with the own-synth patches** (pads 9-24: Clear + pad twice, also when swapping them or copying them between packs); a patch saved before loads it off. *(Beta 3.36 only)* also **saved with the project** (with the rest of the own synth); before, it was not saved with the project nor across a power-down. No CC / NRPN.
- The modulations reach the engine some 100-250 times a second, shared by everything that moves on the track: several fast sources at once update more slowly.

## Synth source view

*How to get there:* With the Synth 1 / 2 view on screen, **press its button again**. Any button closes it.

- **Noise source** — replaces the patch's noise with audio input 1 or 2 (normal or inverted): the synth's filter, envelopes and effects process your outside signal in time with the notes.
- **Macro destinations** *(since RC2)* — decide what each macro knob moves (up to 4 destinations a macro, with their range and depth) without Components.
- **The synth's step-drummer** — sequences the macros by pairs of steps: each knob sets a macro's position on two steps of the pattern.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#synth-fuente)

## Drum track view (knobs)

*How to get there:* Press **Drum 1-4**. Every knob does what its label says, with a second layer on Shift.

- **Shape each drum** — exact pitch, ring mod, attack and decay, sample start and cut, a filter with several modes, LFO and several kinds of distortion: many sounds from one sample.
- **All neutral = the original** — with the new knobs at their neutral point, the sample sounds as on the original Circuit.
- **Start over** *(since RC2)* — Clear + the drum's button puts all its knobs back to their defaults.
- **Stereo pair** *(Beta 3.36 only)* — Drum 1 + Drum 2 (or 3 + 4) play a stereo sample: the left one drives both, the right one only fine-tunes.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#drum-pista)

## Chromatic and scale view of the drums

*How to get there:* **Shift + Preset** with a drum selected. The pads play the sample transposed along the scale.

- **A drum as a keyboard** — the sample transposed in the project's scale.
- **Rollers** *(since RC2)* — repeat the drum on the micro steps you hold: rolls and ratchets live, stopped too, and recorded with Record.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#drum-cromatica)

## Master FX

*How to get there:* **Mixer**, then **Mixer** again. Effects on the master output, the song pointer, the captured sample and the row of assignable effects. Any other view button leaves.

- **Live effects on the whole master** — Gater, Auto-Filter, Digitise, Phaser, Glitch and the mechanical gesture *(since RC2)*: while held or latched.
- **Song pointer** — repeats or loops parts of the pattern live.
- **Capture** — records up to 3.5 s of what is playing, to play it, put it in a slot or use it as a drum.
- **Slots** — an effect with its settings one touch away; the FX sequencer triggers them.
- **Per project** *(since RC2)* — each project remembers its Master FX settings.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#master-fx)

## FX view

*How to get there:* The **FX** button: reverb and delay sends per track, as always, plus:

- **The reverb and delay from the unit** — type, decay, time, feedback…, saved with the project.
- **Quick reset** — Duplicate puts the sends and the effects back to zero.
- **Master filter resonance** — on Shift + Octave ▲ / ▼, in steps of 16 *(Beta 3.36 only; in RC2.10, 1-16 / 17-32)*.
- **Master filter off / on** — Shift + pad 25, keeping its position *(Beta 3.36 only)*.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#vista-fx)

## Sidechain view

*How to get there:* **Shift + FX**. Each track's sidechain presets as always, plus the knobs:

- **Sidechain with knobs** *(since RC2)* — attack, hold, decay and depth of each track's ducking, beyond the presets.
- **Master compressor** *(since RC2)* — its attack and release.
- **Sidechain between drums** — one drum ducks another (the kick ducking the bass, for example).
- **Triggered by patterns** *(since RC2)* — Synth 1 / 2 or MIDI 1 / 2 as the source: their pattern notes duck another track, not only the drums.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#sidechain)
