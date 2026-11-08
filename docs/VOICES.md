# MIDI tracks and voice modes

## Summary

MIDI 1 and MIDI 2 are two complete synths inside the Circuit Tracks: each track keeps sending MIDI and also sounds through its own engine, with up to 4 voices (6 in FM). The **voice mode** decides how notes are shared out among those voices: eight modes on pad 32 of the Preset view.

This document describes **Beta 5.33**, not tested on the device. Nearly all of it is already in RC4 and RC4.08; what is only in the beta is marked *(Beta 5.33 only)*.

The voice mode has no CC or NRPN: it is chosen on the device and saved with the patch and the project.

## Block diagram

A note takes two paths: it goes out over MIDI and, with the engine on, into the voice mode. Incoming MIDI only takes the second path.

<!--fig:ruta-->

Modulation acts on the engine's parameters, not on the note. With patch flip on there is no engine: the note goes out as a Program Change.

## Views and menus

The Preset view is the centre of the track: that is where you choose the engine, the voice mode, the patch and the knob page. The other views deal with the pattern.

<!--fig:mapa-->

The step-drummer appears twice because there are two ways in: pad 30 of Preset, or repeating Note when it is already on.

### Views

| View | How to get there | What it is for |
| --- | --- | --- |
| Note | MIDI 1 / 2 button | Play and write notes. Shift + key = latch. |
| Expanded Note | Note twice | Large keyboard and chord screen (Shift + pad 8). With the engine on sample, the sample picker. |
| Preset | Preset, MIDI 1 / 2 again with Note on screen, or Shift + MIDI 1 / 2 | Engine, voice mode, patches, knob pages. Without an engine, stock templates. |
| Step-drummer | Pad 30 of Preset, or Note repeated with the step-drummer on | Parameters by pairs of steps. |
| CC editor | Pad 25 of Preset, with the engine off | Which CC or NRPN each macro of the template sends. |
| Velocity | Velocity button | Velocity per step. With Shift, letting go of a step's automation. Twice = fixed velocity. |
| Gate | Gate button | Note lengths. |
| Micro Step | Gate twice | Micro steps and Tie. Pad 31 = fixed length, pad 32 = gate by press. |
| Pattern Settings | Pattern Settings button | First and last step, sync rate, direction, Nudge, orders and arpeggiator. |
| Probability | Shift + Pattern Settings (stock), Pattern Settings twice (mode 1) or pad 25 of Pattern Settings (mode 2) | Probability, frequency, dynamics and random-mutate. |
| Split keyboard | Hold one note track and press another | Two tracks on the pads, each with its scale, octave and velocity. |

### Pads of the Preset view

| Pad | Function |
| --- | --- |
| 1-5 | Knob page: 1 VCA-VCF, 2 OSC 1 (or granular), 3 OSC 2, 4 sequenceable knobs, 5 modulation. Shift + pad 4 = non-sequenceable knobs. *(Beta 5.33 only)* Pads 1 and 4 swap places: **pad 1 = sequenceable knobs** (Shift + pad 1 = non-sequenceable), **pad 4 = VCA-VCF**. A tap leaves the page on; holding ½ s shows it only while held. |
| 6 | Modulation matrix. |
| 7 | FM page. Holding it shows the 56 algorithms on pads 9-32 in three pages (Octave ▼ / ▲). With wavetable *(Beta 5.33 only)*: holding it shows the stock's 16 wavetables on pads 9-24; a tap fills the table with their 9 frames; Shift + a table = only the frame the position (K3) points at. The tonic sounds while held. |
| 8 | With FM: a tap opens the FM page; holding it shows 24 instruments on pads 9-32 *(Beta 5.33 only: Octave ▼ / ▲ = page 2 / 1; page 2, pianos, strings, winds and long sounds)*. With wavetable *(Beta 5.33 only)*: holding it shows the pack's samples on pads 9-32 (Octave = page); a tap puts a cycle of the sample in the frame the position (K3) points at (OSC 1's position). The tonic sounds while held. |
| 9-24 | Own-synth patches: 16 slots per page, 8 pages with Octave; each in its engine's colour, empty = dim white *(Beta 5.33 only)*. |
| 25 | CC editor. Off and without effect with the engine on. |
| 26 | Patch flip: each note goes out as a Program Change. Excludes the engine. *(Beta 5.33 only)* Opens and closes the **flip view** (white while open): row 3, pad 17 = patch flip (PGM seq), pad 18 = step flip (one or the other; tapping the one on turns it off); with step flip, row 2 = the target. |
| 27 | Opens the engine row. Shift + pad 27 steps to the next engine. |
| 28 | One or two oscillators (oscillator and VA-drum). With FM, dark and without effect *(Beta 5.33 only)*. |
| 29 | Order of the chain: by default filter, VCA, effect; on, VCA, effect, filter *(Beta 5.33 only)*. Shift + pad 29 steps through the eight voice modes. |
| 30 | Opens the step-drummer. Shift + pad 30 turns it off. |
| 31 | VA-drum only: velocity scales the pitch and filter envelopes. With no voice: the **FX sequencer** (dim blue; on, bright) *(Beta 5.33 only)*. |
| 32 | Opens the voice mode menu, in the colour of the current mode. Only with oscillator, FM, VA-drum or sample *(Beta 5.33 only)*. |

<!--panel:preset-->

### Menus on the pads

A menu takes over pads 9-24 while it is open; those pads stop loading patches.

| Menu | Open | Content | Close |
| --- | --- | --- | --- |
| Engine row | Tap pad 27 | Pads 17-24: off, line, oscillator, VA-drum, granular, sample, FX sequencer, FM. *Beta 5.33 only:* no voice, VCA / VCF / FX only, oscillator, VA-drum, wavetable (sand: the oscillator with a table of up to 9 frames; K7 of OSC 1 / OSC 2 = the position, SHAPE = warp), sample, granular, FM; the FX sequencer moves to pad 31. | Pad 27 again. Choosing does not close it. |
| Voice modes | Tap pad 32 | Pads 17-24: the eight modes. K1 = glide, K2 = unison detune | Pad 32 again, or leave the view |
| FM algorithms | Hold pad 7 | Pads 9-32: the 56 algorithms in three pages (Octave ▼ / ▲); teal 4 operators, white the DX7's, amber 8 | Release pad 7 |
| Instruments | Hold pad 8 with FM | Pads 9-32: 24 instruments (keys orange, basses blue, leads and brass red, pads and strings green, plucks yellow, percussion white, bells and fx violet). *Beta 5.33 only:* Octave ▼ = page 2 (pianos orange, strings green, winds teal, long sounds), Octave ▲ = page 1 | Release pad 8 |
| Matrix destination | Turn a source on page 6 | The destination's page pad and its knobs on pads 9-24 | By itself, 1.5 s later |
| FM ratios | Turn K1-K4 on the FM page | Pads 9-32: the 24 ratios | By itself, 1.5 s later |

<!--panel:motores-->

<!--panel:voz-->

### Gestures with Clear, Shift and Duplicate

| Gesture | Effect |
| --- | --- |
| Clear + the track's button | Engine values back to their initial ones, and latched notes let go. The chosen engine stays. |
| Clear + pad 1-5 | That page back to its initial values. |
| Clear + knob | To the right, default value (lavender). To the left, erases its automation (red). |
| Shift + Preset | The own synth saved with the project comes back. *(Beta 5.33 only)* |
| Clear + patch pad, twice | Saves the patch in that slot. |
| Duplicate + empty slot | Saves the patch there at once. *(Beta 5.33 only)* |
| Duplicate + A + B | Swaps two patches. With another pack loaded in between, copies. |
| Shift + patch pad | Loads the patch without the root note sounding. |

## Engines

Each track has one engine out of seven, plus off, and the track keeps sending its MIDI with any of them. It is chosen on the row that pad 27 opens.

| Row pad | Colour | Engine | What sounds | Maximum voices |
| --- | --- | --- | --- | --- |
| 17 | White | Off | Nothing of its own: the track is stock MIDI, with templates | — |
| 18 | Amber | Line input | Line 1 (MIDI 1) or 2 (MIDI 2) goes through the VCA-VCF; notes trigger it | 1 |
| 19 | Green | Oscillator | Morph sine, triangle, saw, square; second oscillator with pad 28 | 4 |
| 20 | Orange | VA-drum | Synthetic percussion: one-shot VCA, pitch and filter decays, noise | 4 |
| 21 | Magenta | Granular | Up to 16 grains of a pack sample or the capture | 1 |
| 22 | Teal | Sample | A pack sample at the note's pitch, one-shot | 4 |
| 23 | Blue | FX sequencer | Makes no sound: it triggers Master FX slots | — |
| 24 | Violet | FM | 4 operators and 16 algorithms; a variant of the oscillator (Beta 5.33 only: 8 operators and 48 algorithms) | 6, or 3 + 3 (Beta 5.33 only: 6 a track, on the DSP's other core) |

### Oscillator

WAVE (K7 of page 2) is a continuous position between shapes: 0 sine, 42 triangle, 84 saw, 126 square. SHAPE (K2) acts differently on each shape; between two shapes it acts on both.

| Shape | SHAPE left of centre | SHAPE right of centre |
| --- | --- | --- |
| Sine | Nothing | Wavefold: amplifies up to about 8 times and folds. Less on high notes |
| Triangle | Exponential ramps | Wavefold |
| Saw | The whole travel: from a plain saw to a supersaw of 7 saws | Up to the full supersaw |
| Square | Narrower pulse, down to 3 % | Narrower pulse the other way, up to 97 % |

Saw, supersaw and pulse use PolyBLEP, with about 40 dB less aliasing on high notes. With pad 28, OSC 2 modulates OSC 1 with FM, ring, sync and bitwise modes. Two notes at once = paraphony in the mono modes with two oscillators.

### VA-drum

The Sustain knob is the pitch decay and the Release knob the filter decay. The LFO speed gives the noise level, and the LFO is replaced by random values. In poly each hit has its own pitch and volume envelopes and its own noise: a new hit does not cut the earlier ones.

### Granular

The note mode (Shift + K6 of page 2) changes what the notes do.

| Note mode | What the notes do |
| --- | --- |
| Pitch | They change the pitch of the grains |
| Slicer | The sample is cut into 16 slices and each note plays one, from note 36 |
| Stretch | They change the pitch; the stretch from K2 lasts K3 steps (1-64) at any tempo |

With Shift + K4 above 0, each grain goes to a random side. The track's pan decides the proportion. The source (Shift + K8) is the capture or a drum's sample.

### Sample

<!--panel:muestra-->

C3 (note 60) is the sample as it was recorded; an octave up, twice as fast. The VCA stays open and the sample plays to its end. Samples are chosen in the expanded Note view, with a different sample per step (sample flip).

K7 of page 2 is the stereo width: each note plays the chosen sample on the left and a second one on the right. Shift + the chosen sample switches to picking the second. The note lasts as long as the longer one.

### Wavetable (Beta 5.33 only)

The oscillator reading a **table of up to 9 frames** (one per patch, for both oscillators). **K3 of OSC 1 / OSC 2** = the position in the table (in Beta 5.24-5.26, K7); OSC 1's K7 = LFO → position, Shift + K3 = envelope → position; SHAPE (K4) = warp. Pick it on the engine row, **pad 21** (sand).

**Making your own table:**
1. With the wavetable playing, turn **OSC 1's K3** to the frame you want to change (the one you hear).
2. **Pad 8 held + a sample** = that sample's cycle goes into that frame (Octave ▼ / ▲ with pad 8 held = the sample page). Put a sample of your own into the pack first with the SD app (Drums tab).
3. **Pad 7 held + Shift + a Nova table** = only that frame, taken from the same frame of that table; without Shift, the whole table.
4. Repeat at other K3 positions. Every tap sounds the tonic while you hold the pad.
5. It is saved with the own-synth patch and with the project.
6. *(Beta 5.33 only)* **Clear + pad 7** = the frame K3 points at goes back to its table's (the Nova table it had or the starting one).

Wavetable patches show **sand** in the list. With the **warp** away from the centre, the band-limited version is chosen for the fastest part of the bent wave: almost no aliasing up high, a little duller at the ends *(Beta 5.33 only)*.

<!--panel:wt-->

<!--panel:wtnova-->

<!--panel:wtsmp-->

### FM

The volume comes from the operators' envelopes: the VCA stays open and the ADSR of page 1 moves filter, pitch and brightness. SHAPE, Env → shape and LFO → shape change how much the modulators modulate (× 0.27 to × 3.7), so everything that moves those values moves the timbre.

Each operator is sustained or percussive: Shift + K1-K4 to the right gives attack, to the left its own decay. There is one release for all, longer the harder the note.

| # | Algorithm | Family | Voice with Clear + pad 7 |
| --- | --- | --- | --- |
| 1 | 4 → 3 → 2 → 1 (stack) | Classic | The initial one |
| 2 | 3 and 4 → 2 → 1 | Classic | Brass |
| 3 | 4 → 1 and 3 → 2 → 1 | Classic | Electric piano |
| 4 | 4 → 3 → 1 and 2 → 1 | Classic | Bass |
| 5 | Two stacks: 4 → 3 and 2 → 1 | Classic | Electric piano 2 |
| 6 | 4 → 1, 2 and 3 | Classic | Pad |
| 7 | 4 → 3; 2 and 1 alone | Classic | Clavinet |
| 8 | Four carriers | Classic | Organ |
| 9 | Kick: 2 → 1, pitch drop of 4 | Percussive | Kick |
| 10 | Snare: 2 → 1 + noise, pitch drop of 4 | Percussive | Snare |
| 11 | Metal: 2, 3 and 4 → 1, inharmonic ratios | Percussive | Hi-hat |
| 12 | Tom: 3 → 2 → 1, pitch drop of 4 | Percussive | Tom |
| 13 | Bell: 2 → 1 and 4 → 3 | Bells | Bell |
| 14 | Tubular bell: 2 and 3 → 1, 4 a carrier | Bells | Tubular bell |
| 15 | Strings: two detuned stacks | Strings | Strings |
| 16 | Ensemble: 4 → 1, 2 and 3 detuned | Strings | Ensemble |

<!--panel:fm-->

<!--panel:algos-->

<!--panel:partida-->

The starter sounds (pad 8 held): piano, electric piano, organ, pluck, harp, marimba, bass, bell, strings, pad, flute, clarinet, brass, kick, snare and hi-hat.

### 8-operator FM (Beta 5.33 only)

It replaces the 4-operator FM on the same pad 24. Up to 8 operators, each with a DX7-style envelope (4 rates and 4 levels), and 56 algorithms: the 16 above, the DX7's 32 and 8 with eight operators. 4-operator patches load converted, with the same sound.

| Element | What it is |
| --- | --- |
| FM page | Pad 7, with the engine row closed |
| Pads 9-16 | Operator 1-8; the ones the algorithm uses lit (carriers green, modulators light blue) |
| Pad 3 | The pitch envelope (violet) |
| Pads 17-24 | The engine row (FM bright); a tap changes the engine |
| K1-K4 | Ratio (0.5 … 31 or fixed in Hz), fine, level, velocity |
| K5-K8 | Rates R1-R4 |
| Shift + K1-K4 | Algorithm, feedback, rate scaling, level scaling |
| Shift + K5-K8 | Levels L1-L4 |

The engine works out only the algorithm's operators: with 4, about 10 voices; with 6 (the DX7's), about 6-7; with 8, about 5. Saved with the own patches (in an extra slot of the same bank on the card) and with the project (in the settings of Synth 1 / 2's patterns). Components' «Send patches» no longer erases own patches or the FM.

<!--panel:fm8-->

<!--panel:algos8-->

<!--panel:inst8-->

## Voice modes

There are eight modes, a combination of two decisions: how many voices sound, and what a new note does with other keys held. A project that never chose a mode starts on poly.

| Voices | Retriggers | Does not retrigger | Slides | Always slides |
| --- | --- | --- | --- | --- |
| One voice | Retrigger (17) | Legato (18) | Glide (19) | — |
| All on the same note | Uni retrig (20) | Uni legato (21) | Uni glide (22) | Uni always-glide (23) |
| One voice per note | Poly (24) | — | — | — |

The number is the menu's pad. Modes with the same name share a colour: retrigger green, legato yellow, glide teal. Uni always-glide is violet and poly magenta.

<!--fig:modos-->

The mode shares the notes out among the voices; then each voice's level drops according to how many are sounding, and all of them go through the track's filter and effect.

### How to choose

With the engine on, a tap on pad 32 opens the menu on pads 17-24, with the current mode bright. Touching a pad chooses the mode. Shift + pad 29 does the same without opening the menu: it steps through the eight in that order, and with Shift pad 29 shows the mode's colour.

With the menu open, two knobs adjust the modes:

| Knob | Parameter | Travel | LED |
| --- | --- | --- | --- |
| K1 | Glide time | No glide fully left; from 2 ms to about 2 s | Teal |
| K2 | Unison detune | Up to ±50 cents between the outermost voices | Blue |

### What each mode does

| Mode | New note with others held | New note with none held | On release |
| --- | --- | --- | --- |
| Retrigger | Jumps to the note and retriggers the envelope | Triggers the envelope | Back to the previous note if still held |
| Legato | Only changes the pitch | Triggers the envelope | Back to the previous note if still held |
| Glide | Slides to the note, no retrigger | Starts at its pitch and triggers | Back to the previous note if still held |
| Uni retrig | Moves all voices and retriggers | Triggers the envelope | Sounds until all notes are released |
| Uni legato | Moves the voices with no retrigger and no slide | Triggers the envelope | Sounds until all notes are released |
| Uni glide | The voices slide, no retrigger | Starts at its pitch, no glide, and triggers | Sounds until all notes are released |
| Uni always-glide | The voices slide, no retrigger | Slides from the previous note and retriggers | Sounds until all notes are released |
| Poly | Takes another voice and retriggers the track's envelope | Takes a voice and triggers | That voice goes off; the last one sounds with the release |

In uni legato the envelopes of FM and VA-drum are not retriggered either.

### Voices per engine

| Mode | Engine | Voices of the track |
| --- | --- | --- |
| Retrigger, legato, glide | All | 1 |
| Poly | Oscillator (one or two, supersaw too), VA-drum, sample (stereo too) | 4 |
| Poly | FM | 6, or 3 and 3 with both tracks on FM poly or unison |
| Unisons | Oscillator, VA-drum | 4 on the same note, spread with K2 |
| Unisons | FM | 6, or 3 with both tracks on FM |
| Unisons | Sample | 1 |
| All | Granular and line input | 1 |

Glide works on oscillator, VA-drum and FM. Sample mode and the granular do not slide.

Each track has its own maximum; only FM voices are shared between the two. If the second track goes into FM poly or unison, the voices of both are cut at once to share out.

### What belongs to each voice and what to the track

| Element | Oscillator and sample | VA-drum | FM |
| --- | --- | --- | --- |
| Pitch and velocity | Per voice | Per voice | Per voice |
| Volume envelope | The track's | Per voice | Per voice, in the operators |
| Pitch envelope | The track's | Per voice | The track's |
| Noise | — | Per voice | Per voice |
| Filter and effect | The track's | The track's | The track's |
| On release | The last note sounds with the release | The hit carries on to its end | Each voice sounds whole with its release |

### Voice stealing

With all voices busy, a new note takes the voice of the track's oldest note, with a 2 ms fade. A released note keeps its voice while its release sounds, so with long releases the voices fill up even if you play single notes.

### Chord level

Each voice drops according to how many are sounding, so the sum does not clip. The factor is √(2 / n), and the unisons follow the same rule.

| Voices sounding | Level of each voice |
| --- | --- |
| 1 or 2 | 1.00 |
| 3 | 0.82 |
| 4 | 0.71 |
| 5 | 0.63 |
| 6 | 0.58 |

### Voice limit

With two or more own voices sounding, the device turns voices off before the DSP runs out of time and a rattle is heard. FM is the engine that uses the most. With a single own voice the limit does not act.

1. Every 2 ms it measures how much time the DSP has left.
2. If it is tight, it turns off the lowest released voice, FM ones first. If none is released, it turns off the oldest held note.
3. It turns off at most one voice every 12 ms, or every 4 ms if very tight.
4. The track goes on with the voices that fit, 2 at least. A new note first turns off the lowest released one.
5. Every 2 s without trouble it tries one voice more, up to the maximum.

Synth 1 and Synth 2 do not lose voices through this: with two or more own voices sounding, the device stops turning theirs off for lack of time. The ones that go off are the own synth's.

For more voices at once: shorter releases, fewer FM operators at a high level, or a single track on FM poly.

### Saving the mode

The mode, the glide time and the detune are saved with the own patch and with the project. A patch without them leaves the current values.

## Knob pages

With the engine on, pads 1-7 choose what the 8 knobs do, and Shift gives a second layer. Type knobs show the type's colour, with the brightness of the position inside the type. A type knob takes at least 16 clicks a type *(Beta 5.33 only)*: the LFO shape, the FM algorithm and the granular's note mode go to 16. Bipolar knobs *(Beta 5.33 only)*: dim at the centre, their colour to the right and a lighter shade of the same colour to the left; OSC 2's K5 (FM) past the maximum, violet.

### Page 1: VCA-VCF

| Knob | Alone | With Shift |
| --- | --- | --- |
| K1 | Attack | Sustain |
| K2 | Release | Decay |
| K3 | Envelope → level | LFO → level |
| K4 | Envelope → filter | LFO → filter |
| K5 | Filter | Filter type: DJ, LP 12, HP 12, BP, notch, LP 24, HP 24 |
| K6 | Resonance | VCA gain, up to +18 dB with saturation |
| K7 | LFO speed: right free, left synced | — |
| K8 | Effect amount | Effect type: soft, hard, fold, wavefold, ring, comb, chorus |

### Page 2: OSC 1

On oscillator, VA-drum, sample and FM.

| Knob | Alone | With Shift |
| --- | --- | --- |
| K1 | TUNE | FINE |
| K2 | SHAPE | MIX OSC 1 ↔ OSC 2 |
| K3 | Envelope → pitch | BITSYNC |
| K4 | Envelope → shape | — |
| K5 | LFO → pitch | — |
| K6 | LFO → shape | — |
| K7 | WAVE (morph); on sample, stereo width | — |
| K8 | LFO → morph | Envelope → morph |

*Beta 5.33 only* (oscillator, VA-drum, wavetable):

| Knob | Alone | With Shift |
| --- | --- | --- |
| K1 | TUNE | Envelope → pitch |
| K2 | FINE | LFO → pitch |
| K3 | WAVE (morph); on wavetable, the position; on sample, stereo width | Envelope → morph |
| K4 | SHAPE (on wavetable, warp) | Envelope → shape |
| K5 | LFO → FM | Envelope → FM |
| K6 | LFO → ring | Envelope → ring |
| K7 | LFO → morph | LFO → shape |
| K8 | LFO → mix | Envelope → mix |

*Beta 5.33 only*, with **one oscillator** (two oscillators off) K5, K6 and K8 have their own functions, with their own values:

| Knob | Alone | With Shift |
| --- | --- | --- |
| K5 | Sub-oscillator level (a square one octave below) | Envelope → sub |
| K6 | Noise level | Envelope → noise |
| K8 | LFO → sub | LFO → noise |

The sub and the noise go through the filter and the VCA; in poly, every voice has its own. Saved with the patch and with the project.

### Page 2: granular

| Knob | Alone | With Shift |
| --- | --- | --- |
| K1 | Pitch ±24 semitones | Fine ±1 semitone |
| K2 | Position in the sample | Position spread |
| K3 | Scan, frozen at the centre | Left: grain reversed. Right: pitch spread |
| K4 | Grain size, 5-500 ms | Stereo spread |
| K5 | Density, 1-16 grains | Window |
| K6 | Scan zone | Note mode: pitch, slicer, stretch |
| K7 | LFO → position | LFO → size |
| K8 | Envelope → position | Source: the capture or a drum's sample |

### Page 3: OSC 2

| Knob | Alone |
| --- | --- |
| K1 | TUNE 2 |
| K2 | SHAPE 2 |
| K3 | MIX OSC 1 ↔ OSC 2 |
| K4 | FM |
| K5 | FINE 2 |
| K6 | BITSYNC |
| K7 | WAVE 2 |
| K8 | RING |

Beta 5.33 (except with the granular, which keeps the table above): K1 = OSC 2's ratio to its note (¼, ½, 1 at the centre, 2 … 31), K2 = detune ±50 cents (FINE 2), K3 WAVE 2, K4 SHAPE 2, K5 FM with a centre (right OSC 2 → OSC 1; left OSC 1 → OSC 2; both at the ends, 50 / 50), K6 RING, K7 classic sync + bitwise, K8 MIX.

### Page 4: sequenceable knobs

These are the 8 values recorded as automation with Record + Play. By default: TUNE, Release, Env → level, Env → filter, Filter, Resonance, LFO speed and Effect.

Shift + knob chooses the destination among the 33 parameters, 4 clicks per parameter. While you choose, pads 9-24 show where the destination lives. Clear held and then Shift + knob restores the default.

### Non-sequenceable knobs (Shift + pad 4; in Beta 5.33, Shift + pad 1)

Eight knobs with an assignable destination that are not recorded. Pad 4 shows pink. By default: Attack, Decay, Sustain, SHAPE, LFO → filter, Env → pitch, MIX OSC 1 / 2 and VCA gain.

A destination that is also on the sequenceable knobs is recorded, as from any page.

### Page 5: modulation

| Knob | Alone | With Shift |
| --- | --- | --- |
| K1 | Attack | Envelope → level |
| K2 | Decay | Envelope → filter |
| K3 | Sustain | Envelope → pitch |
| K4 | Release | Envelope → shape |
| K5 | LFO speed | LFO → shape |
| K6 | LFO → filter | LFO → morph |
| K7 | LFO → level | Envelope → morph |
| K8 | LFO → pitch | LFO shape |

With VA-drum, the LFO is still its noise.

### Page 6: matrix

Eight modulation sources, in the next section.

### Page 7: FM

| Knob | Alone | With Shift |
| --- | --- | --- |
| K1-K4 | Ratio of operator 1-4: from 0.5 to 16. Each ratio takes 5-6 clicks: the first exact, the next ones detune +2.5 cents | Centre = attack 0. Right: attack up to about 3 s. Left: percussive, with a decay of 3 ms to 8 s |
| K5 | Level of operator 1 | Algorithm |
| K6 | Level of operator 2 | Feedback |
| K7 | Level of operator 3 | Noise |
| K8 | Level of operator 4 | Release |

A carrier's level is its volume; a modulator's, how much it modulates.

## Modulation

The engine has its own ADSR and LFO, and the matrix adds eight sources that move any of 33 parameters. The matrix is added when sending: the parameter's saved value does not change.

### LFO

K7 of page 1 is bipolar: right free, left synced. Shift + K8 of page 5 chooses the shape, with the LED in its colour: one step every 16 clicks *(Beta 5.33 only; before, 4)*.

| Shape | Colour |
| --- | --- |
| Triangle, the initial one | Green |
| Reverse saw | Blue |
| Saw | Magenta |
| Square | Red |
| Sine | Teal |
| Sample & hold | White |
| Smoothed sample & hold | Violet |

### Modulation matrix (pad 6)

| Knob | Source | Shift + knob |
| --- | --- | --- |
| K1 | Note velocity | — |
| K2 | Note: C3 = 0, an octave = a quarter of the travel | — |
| K3 | Random: a new value on each note | — |
| K4 | LFO 2 | Shape × speed; on each shape, left half synced and right free |
| K5 | Envelope 2: attack and fall from each note | Attack × fall, 20 ms to 4 s |
| K6 | A drum hit: a fall from each hit | Drum 1-4 × its fall |
| K7 | Position in the pattern, from first step to last | — |
| K8 | Stepped random: a new value every N steps | N = 1, 2, 4, 8 or 16 |

With K1 (velocity) at 0, the global velocity controls of the Setup view (K1 velocity → amplitude, K2 velocity → filter) take over: soft notes quieter and darker. *(Beta 5.33 only)*

The knob's position is both the destination and the amount:

- Fully left, off.
- Each destination takes 16 steps, 2 clicks per step. The first is the destination with no amount, with the LED dim.
- The LED's colour is the destination page's, and its brightness the amount.
- The sources note, random, LFO 2 and stepped random go up and down; the others only up.
- Several sources on one destination add up.

| Gesture | Effect |
| --- | --- |
| Clear + knob | That source off |
| Clear + Shift + knob | Its parameter to the initial value |
| Clear + pad 6 | All sources off |

Modulation reaches the engine about 100-250 times a second, shared among everything moving on the track.

## Sequence and performance

The track uses the stock pattern, and the mod adds engine automation, step-drummer, arpeggiator and per-step variations. All of it goes out through the same voices and respects the voice mode.

### Automation

The 8 sequenceable knobs record with Record + Play into 8 lanes of the pattern. There are several per-step gestures:

| Gesture | View | Effect |
| --- | --- | --- |
| Record held + step | Note | Snapshot: writes on that step the parameters that are not at their initial value. *(Beta 5.33 only)* The step shows yellow while held |
| Shift + step | Velocity | Marks the step: no lane sounds there and what was automated goes back to the synth saved with the project |
| Shift + yellow step | Velocity | *(Beta 5.33 only)* Hear its values until Shift is released, with the knobs it moves in yellow |
| Clear + step | Velocity | *(Beta 5.33 only)* Erases the knobs' automation on that step; the notes stay |
| Yellow step held + another yellow step | Velocity, with Shift | *(Beta 5.33 only)* Sweep: every lane with a value at both steps becomes a straight line between them |

In the snapshot, a parameter with no lane takes one whose parameter is at its initial value, and that lane is erased first. If they do not fit, the first ones in the matrix's order stay.

### Step-drummer

<!--panel:step-->

The 8 knobs are 8 pairs of steps of the pattern: each pair offsets a destination only on those steps. The LED shows the amount: dim with no modulation, brighter the further away.

| Control | Function |
| --- | --- |
| Pads 1-16 | Steps of the half shown. Touch = listen. Shift + touch = add or remove a note. With Record, records on the step that is playing |
| Pads 17-24 | Destination: pitch, OSC 2, WAVE, FM, MIX, env → filter, SHAPE, decay |
| K1-K8 | The 8 pairs of steps, the playing one in white |
| Octave ▲ / ▼ | Pitch or velocity page. The velocity page has its own destination |
| 1-16 / 17-32 | The other half of the pattern |
| Pad 32 | Pitch-vel toggle: the pitch page transposes by degrees and the velocity page changes the velocity |

The toggle moves one degree of the scale every 8 knob steps, from −8 to +8 degrees. With the step-drummer on, TUNE and Release stop playing and recording as automation, because it uses their lanes.

### Patch morph (Beta 5.38 only)

In the MIDI 1 / 2 Preset view with the engine on, **hold two or more slots** for 0.4 s: the morph view opens over the Preset view (**Preset** switches between the morph and the slots). **K1** moves from one patch to the next; K2 / K3 triangle LFO, K4 / K5 random-step LFO, K6 random per step, K7 / K8 envelope; pads 1 / 8 the envelope (held while held), pad 32 leaves. The engine's codes and the 8-operator FM blend; type ones (engine, wave, algorithm) take the nearest patch's. Nothing is saved.

### FX sequencer

With this engine, each step-drummer knob chooses a slot of the bottom row of Master FX: none, pads 26-31 or random. A slot with no effect plays the effect at the top of its column.

### Jump sequencer

The track's notes make another track's pattern jump to the step they indicate, on the note's own step. *(Beta 5.33 only)*

| Control | Function |
| --- | --- |
| Pad 26, flip view *(Beta 5.33 only)* | Row 3: pad 17 = patch flip (PGM seq), pad 18 = step flip (no target picked: the last one used; Synth 1 from the factory); tapping the one on turns it off |
| Row 2 of the flip view, with step flip | The eight tracks: a tap = the target (the track's own dark). With the view closed, pad 26 blinks in its colour |
| Note view, pads 17-32 | Steps 1-16; Octave ▲, steps 17-32. The scale changes nothing |
| Expanded Note, the 32 pads | Steps 1-32 |

While it points, the track does not sound. Each note, from the sequencer, the pads or the arpeggiator, makes the other track jump. Saved with the project.

Pad 26 blinks in the target track's colour. Pointing turns the engine off and turning an engine on stops pointing: only one of the two at a time. When it starts pointing the track goes to steps 1-16, and Octave only moves between 1-16 and 17-32: the Octave that cannot move any further goes dark, both in the expanded Note view. With the transport stopped, a pad sounds that step of the target track while you hold it, with no jump (on the drums, with the chosen sample).

If the target and the MIDI track have the same length, one jump is only noticeable the first time: on the next passes the target is already on that step. To hear it on every pass the pattern needs two jumps: one to move it and one to bring it back.

<!--panel:saltos-->

<!--panel:saltosnote-->

### Arpeggiator

It works per track and pattern, in Pattern Settings with Shift. Notes are arpeggiated in the order they were pressed.

| Gesture | Function |
| --- | --- |
| Shift + pad 25 | On or off |
| Shift + pads 27-32 | Order: fractal, deconstructed, up, down, ping-pong, random |
| Shift + pads 17-24 | Rate: 1/4, 1/4T, 1/8, 1/8T, 1/16, 1/16T, 1/32, 1/32T. The same pad again = the track's |
| Shift + pads 1-4 | Octaves: none, +1, +1 and −1, +2 and −1 |
| Shift + pads 5-8 | When the octave changes: each turn, each note, every 3, every 4 |
| Shift + pads 9-12 | Groove: none, dotted, swing, each note twice |
| Shift + pads 13-16 | Restart: none, or after a turn 1, 3 or 5 notes more |

Four sources reach the arpeggiator: the pattern's chords, held notes, a held step with the transport stopped, and the external keyboard if Setup's Note button is on. With Record the chord is recorded, not the single notes.

<!--panel:ps-->

### Per-step variations

| Function | Where | What it does |
| --- | --- | --- |
| Probability | Probability view, row 3 | The step sounds sometimes |
| Frequency | Mode 1, row 4 | The step sounds on the last of every n turns, 1 to 8 |
| Dynamics | Mode 2, pads 25-28 | Accents, accents and length, or random length. *(Beta 5.33 only)* |
| Random-mutate | Mode 2, pads 17-24 | Pads 18-20 another note of the scale (×1, ×2, ×4), 21 / 22 an octave up (low / high), 23 / 24 up or down (low / high). *(Beta 5.33 only)* |
| Gate by press | Micro Step, pad 32 | What you hold while entering a note is its length |
| Fixed length | Micro Step, pad 31 | All notes entered by hand with the same gate, 1 to 16 steps |
| Nudge | Pattern Settings, pad 26 | Moves the content of the range one step back; Shift, forward. The first and last steps do not move. *(Beta 5.33 only)* |
| Fractal and deconstructed | Pattern Settings, pads 27 and 28 | Another order through the pattern |
| Micro steps | Mode 2, pad 32 | The note moves up to 2 micro steps earlier or later, inside its step. *(Beta 5.33 only)* |
| Track factor | Octave, with mode 2 open | ×0 to ×8, multiplies all the track's chances; ×1 by default. At ×8 pad 24 changes every note: the draw is still half and half. *(Beta 5.33 only)* |

<!--panel:mutate-->

<!--panel:micro-->

### Playing live

| Function | Gesture | What it does |
| --- | --- | --- |
| Latch | Shift + key in Note | The note keeps sounding until its next press. With Shift, latched notes light bright teal |
| Latched notes to a step | Shift + step in Note | Writes the latched notes on that step, up to 6 |
| Chord screen | Shift + pad 8 in expanded Note | Type, inversion and modifiers; rows 3-4 play the chord, up to 6 notes |
| Split keyboard | Hold one track and press another | Two tracks on the pads. Holding a track button gives its knobs |
| Chord bank | Setup's Record in yellow | Nothing is recorded on a muted track: it sounds and is recorded on the synth of the shared channel |
| Note flash | Shift held, in any view | *(Beta 5.33 only)* Each track's button flashes white for 100 ms on every note |

Each note of the chord goes through the voice mode: in poly it sounds up to the engine's maximum of voices.

## Saving

The own synth lives in three places at once: the project, the pack's patch and the device settings. When a project that carries it loads, the project's wins; an older one leaves the sound as it was.

| Place | When it is written | Reach | Where |
| --- | --- | --- | --- |
| Pattern and project | Save twice | That project | The pack's session file |
| Own patch | Clear + pad twice, at once | The whole pack; 128 slots common to MIDI 1 and 2 | Padding of the records of Patches/NN_PATCHBANK.cpb |
| Device settings | By itself, with the transport stopped and 2 s without changes | All projects | Device settings |

The Synth 1 / 2 patch file does not change: the own patch goes in the part of each record the original does not use.

### What is saved where

| Data | Pattern | Project | Own patch | Settings |
| --- | --- | --- | --- | --- |
| Notes, velocity, gate, micro steps, probability | Yes | With the pattern | — | — |
| Automation, marks, step-drummer pairs, sample flips | Yes | With the pattern | — | — |
| Frequency, dynamics, random-mutate, fractal or deconstructed order | Yes | With the pattern | — | — |
| Arpeggiator and modifiers, per track and pattern | — | Yes | — | — |
| Gate by press, fixed length | — | Yes | — | — |
| Pitch-vel toggle, velocity page destination | — | Yes | — | — |
| Chosen engine, oscillators, order, values | — | Yes | Yes | Yes |
| Step-drummer on and its destination | — | Yes | Yes | Yes |
| Voice mode, glide time, detune | — | Yes | Yes | — |
| Modulation matrix | — | Yes | Yes | — |
| FM: operators, algorithm, feedback, noise | — | Yes | Yes | — |
| Destinations of the sequenceable and non-sequenceable knobs | — | Yes | Yes | — |
| LFO shape | — | Yes | Yes | — |
| Sample mode stereo: distance to the second sample | — | Yes | Yes | — |
| Patch flip | — | — | — | Yes |
| Random-mutate factor, per track *(Beta 5.33 only)* | — | Yes | — | — |
| Track the jump sequencer points at *(Beta 5.33 only)* | — | Yes | — | — |

### What is lost at power-off

- Everything changed since the project's last Save.
- Latched notes and chords, and the chord screen's type and modifiers.
- The split keyboard and open views.
- The Octave semitone with Jankó.
- A patch waiting to be copied to another pack.
- The turn counters of frequency and fractal order, which reset on stop.

### Limitations

- With no card, and on the S versions, the mod writes nothing of its own: patches are not saved and Save turns red. The project is saved.
- The CC editor saves in the template, not in the own patch.
- A patch from an old version loads without what did not exist yet: matrix off and default destinations.

## MIDI control

Each engine knob sends and receives a CC or NRPN on the track's channel, with values 0 to 127 and 64 as the centre on bipolar ones. Voice mode, matrix, FM and knob destinations have no CC or NRPN.

All of it respects the CC Tx and CC Rx filters of the Setup view. Messages go out as the knob turns, with Clear too, and come in on the same number.

### Notes and channels

| Message | What it does |
| --- | --- |
| Track channel | Chosen in Setup, with the track's button and pads 1-15 |
| Outgoing notes | The track sends its notes with any engine |
| Incoming notes | On the track's channel, USB or DIN: they play the own synth and are recorded. They are not forwarded to the output |
| Shared channel | MIDI 1 / 2 on the channel of a synth or the drums plays it inside (internal loopback) |
| Patch flip | Pad 26: each note goes out as a Program Change on the track's channel. Excludes the engine |
| Keyboard to the arpeggiator | Setup's Note button: incoming notes go through the arpeggiator. Off by default |
| Record internal routes | Setup's Record: what the track sends a synth is also recorded on it |
| USB merge | Advanced Setup, pad 23: the DIN In also goes out over USB |
| MIDI Thru | Advanced Setup, Duplicate: Thru, Out 2, Merge or Filter |

With the engine on, the knobs send this map and never the template. With the engine off they send the template, editable with pad 25.

### Selecting an NRPN

Send CC 99 (MSB), CC 98 (LSB) and CC 6 (value), in that order. The device remembers the chosen NRPN until the next CC 99 or 98. In the table, 4:13 means MSB 4, LSB 13.

### Engine parameters

On granular, page 2 and part of page 3 use the same numbers with another meaning, in brackets.

| Parameter | Message | Page / knob |
| --- | --- | --- |
| Filter | CC 74 | 1 / K5 |
| Resonance | CC 71 | 1 / K6 |
| Envelope → filter | CC 79 | 1 / K4 |
| LFO → filter | NRPN 4:4 | 1 / Shift + K4 |
| Attack | CC 73 | 1 / K1 |
| Decay | CC 75 | 1 / Shift + K2 |
| Sustain | CC 70 | 1 / Shift + K1 |
| Release | CC 72 | 1 / K2 |
| Effect amount | CC 91 | 1 / K8 |
| VCA gain | CC 59 | 1 / Shift + K6 |
| LFO speed | NRPN 0:76 | 1 / K7 |
| LFO → level | NRPN 4:12 | 1 / Shift + K3 |
| Effect type | NRPN 4:13 | 1 / Shift + K8 |
| Envelope → level | NRPN 4:15 | 1 / K3 |
| Filter type | NRPN 4:16 | 1 / Shift + K5 |
| TUNE (granular: pitch) | CC 26 | 2 / K1 |
| FINE (granular: size) | CC 27 | 2 / Shift + K1 |
| WAVE (granular: position) | CC 20 | 2 / K7 |
| SHAPE (granular: density) | CC 21 | 2 / K2 |
| LFO → pitch (granular: scan) | NRPN 4:21 | 2 / K5 |
| Envelope → pitch (granular: env → position) | NRPN 4:22 | 2 / K3 |
| Envelope → shape (granular: zone) | NRPN 4:23 | 2 / K4 |
| LFO → shape (granular: LFO → position) | NRPN 4:24 | 2 / K6 |
| Envelope → morph (granular: source) | NRPN 4:25 | 2 / Shift + K8 |
| LFO → morph (granular: note mode) | NRPN 4:26 | 2 / K8 |
| TUNE 2 (granular: LFO → size) | CC 37 | 3 / K1 |
| FINE 2 (granular: fine) | CC 39 | 3 / K5 |
| WAVE 2 (granular: stereo) | CC 30 | 3 / K7 |
| SHAPE 2 (granular: window) | CC 31 | 3 / K2 |
| MIX OSC 1 ↔ OSC 2 | CC 52 | 3 / K3 |
| BITSYNC | NRPN 4:32 | 3 / K6 |
| FM (granular: position spread) | NRPN 4:33 | 3 / K4 |
| RING (granular: reverse and pitch spread) | CC 54 | 3 / K8 |

### Incoming CC and NRPN

Incoming CC and NRPN move the engine, but are not recorded into the pattern or forwarded over MIDI. Only the device's knobs write automation. With the engine off, the device does not take them.
