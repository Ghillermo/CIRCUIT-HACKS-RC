# Views

*[Versión en español](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Views-ES) · [Home](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Home) · [Guide by views](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html)*

Every view of the device and what it offers. Each one links to its full chapter in the [guide by views](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html).

## Setup

### Setup view

*How to get there:* Open it as on the original. MIDI channels and device options as always, plus:

- **Shared channels (internal loopback)** — a MIDI track plays a synth or the drums of the unit itself.
- **Returns through strips 3 / 4** — the reverb and the delay as mixer channels.
- **Program Change channels** *(since RC2)* — listens to and sends program changes on channels of their own.
- **Record the internal routings** *(since RC2)* — what the MIDI track plays on a synth is recorded into it too.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#setup)

### Advanced Setup view

*How to get there:* Open it as on the original. Besides its stock settings (master compressor, etc.):

- **MIDI Thru, Merge and Filter** *(since RC2)* — the Thru jack can merge the incoming MIDI with the unit's own, or filter it.
- **Velocity curve** *(Beta 3.37 only)* — K1 makes the pads more sensitive or harder.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#advanced-setup)

## Stock synths (Synth 1 / 2)

### Synth 1 / 2 track view (Note, Velocity, Gate)

*How to get there:* Press **Synth 1** or **Synth 2**. The pads play the synth as always.

- **Source view** — the synth can process an audio input instead of its noise.
- **Split keyboard** *(since RC2)* — one synth on top and the other below, each with its scale, octave and velocity; *(since RC2.02)* with any pair of note tracks.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#synth-nota)

### Scales view and custom scale

*How to get there:* Press **Scales** as always (root and stock scale); **Shift + Scales** for the custom scale.

- **Custom scale** *(since RC2)* — up to 7 notes over the root and a free period (for example, a scale that repeats every 7 semitones). The note tracks' pads, the quantising and random-mutate use it; saved with the project.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#escalas)

### Synth source view

*How to get there:* With the Synth 1 / 2 view on screen, **press its button again**. Any button closes it.

- **Noise source** — replaces the patch's noise with audio input 1 or 2 (normal or inverted): the synth's filter, envelopes and effects process your outside signal in time with the notes.
- **Macro destinations** *(since RC2)* — decide what each macro knob moves (up to 4 destinations a macro, with their range and depth) without Components.
- **The synth's step-drummer** — sequences the macros by pairs of steps: each knob sets a macro's position on two steps of the pattern.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#synth-fuente)

### Synth 1 / 2 Preset view

*How to get there:* Press **Preset** with Synth 1 / 2 selected. The pads pick a patch as always (4 pages, the pack's 128 patches).

- **The voice mode at a glance** *(since RC2)* — mono, mono with glide and poly patches told apart by colour.
- **Save the patch** *(since RC2)* — stores the sound as you left it into the pack (the original only saves patches from Components).
- **Swap and copy** — reorder the pack's patches or take one to another pack.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#synth-preset)

## MIDI tracks (MIDI 1 / 2)

### MIDI 1 / 2 Preset view

*How to get there:* Press **MIDI 1** or **MIDI 2**, then **Preset** (*Beta 3.37 only*: or **MIDI 1 / MIDI 2 twice in a row**). Besides the stock templates, the track's own synth lives here.

- **A synth on each MIDI track** — MIDI 1 and 2 sound on the unit itself with their engine (processed line input, oscillator, two oscillators, VA-drum, granular, sample mode; *(Beta 3.37 only)* FM) and still send MIDI.
- **FX sequencer** — an engine with no sound: it triggers Master FX effects on the steps you choose.
- **Own-synth patches** *(since RC2)* — 64 sounds a pack for those engines, one touch away.
- **Mod matrix** *(since RC2.02)* — eight sources (velocity, note, random, LFO 2, envelope 2, a drum hit, the pattern position, stepped random) that move any parameter of the engine.
- **Patch flip** — every note sends a program change: the outside gear changes sound step by step.
- **CC editor** — changes which CC each knob of the template sends, without Components.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#midi-preset)

### Knob pages of the MIDI 1 / 2 engine

*How to get there:* With the engine on, pads 1-5 of the Preset view pick what the 8 knobs do; Shift gives a second layer.

- **VCA-VCF** — level and filter with their envelope and LFO; with Shift, the filter type and the effect type.
- **Oscillators** — a waveform that morphs from sine to square, and a second oscillator with FM, ring and sync.
- **Granular** — turns a sample into textures: grains that read it at another place, speed or direction, to freeze, stretch or slice it.
- **Page 4** — the 8 parameters that can be recorded as automation (*(Beta 3.37 only)*: with Shift + knob, any of the 33; Record + step = a snapshot of the values).

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#midi-knobs)

### Mod matrix

*How to get there:* *(since RC2.02)* MIDI 1 / 2 with the engine on: Preset view, **pad 6**. The 8 knobs become 8 modulation sources.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#midi-matriz)

### 4-operator FM

*How to get there:* *(Beta 3.37 only)* MIDI 1 / 2: Preset view, a tap on **pad 27** and **pad 24** of the engine row (violet). **Pad 7** opens its knob page (bright violet on it).

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#midi-fm)

### CC editor of the MIDI macros (pad 25)

*How to get there:* MIDI 1 / 2 Preset view, **pad 25**: change on the device which CC / NRPN each macro knob of the template sends.

- **Control other gear** — pick the CC (or NRPN) number and the range of each knob of the template, and save it there.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#midi-cc)

### Step-drummer view

*How to get there:* MIDI 1 / 2: Preset view with the engine on, **pad 30** (*Beta 3.37 only*: with the step-drummer on, **Note** goes Note → expanded Note → step-drummer). Synth 1 / 2: source view, **pad 30**. Sequencing by step pairs over the pattern.

- **Parameters by pairs of steps** — the 8 knobs are 8 pairs of steps of the pattern: each one moves a destination (pitch, shape, FM, filter…) on those steps only, for melodies, accents or timbre changes without drawing automation.
- **The LED tells how much** *(since RC2)* — dim with no modulation, brighter the further it goes.
- **A second page with its own destination** *(since RC2)* — the velocity page moves another destination at the same time.
- **Pitch-vel toggle** *(since RC2)* — page 1 transposes the notes in degrees of the scale and page 2 sets their velocity: a melody from a single pattern of notes.
- **In real time** — with Record, touching a step records it.
- **FX sequencer** — with that engine, each pair picks which Master FX slot sounds.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#step-drummer)

### Sample mode and sample picker

*How to get there:* *(since RC2)* MIDI 1 / 2 with the engine on **sample** (pad 27 cyan, after the granular): **Note twice** (expanded Note view). The track plays a pack sample one-shot, at the pitch of each note.

- **Pitched drums on a MIDI track** — any pack sample plays at the pitch of each note, like a drum machine with tunable samples.
- **A different sample per step** — the sample flip changes sample step by step with no other track; it can be recorded live too.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#midi-muestra)

## Pattern Settings

### Pattern Settings view

*How to get there:* The **Pattern Settings** button with a track selected: first / last step, sync rate and direction as always, plus pads 25-28 and the arpeggiator (Shift).

- **Nudge** — rotates the pattern so that it starts on another step.
- **Fractal and deconstructed orders** — walk through the pattern another way without changing its notes.
- **Arpeggiator** *(since RC2)* — the pattern's chords (and the ones you play) sound note by note, in their order and resolution; on the drums, jumping from sample to sample.
- **Dynamics and random-mutate** (pad 25) — variations so that the pattern does not always sound the same.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#pattern-settings)

### Micro Step view (note tracks)

*How to get there:* Press **Gate twice** with a note track selected (Synth 1 / 2, MIDI 1 / 2).

- **Micro steps and Tie (stock)** — place each note off the grid and tie it to the next step.
- **Gate by holding** *(since RC2)* — when entering notes by hand, how long you hold is how long the note lasts.
- **Fixed length** *(since RC2)* — every note you enter by hand gets the same length.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#micropasos)

### Probability view (note tracks and drums)

*How to get there:* **Shift + Pattern Settings** (stock mode), **Pattern Settings twice** (mode 1) or **pad 25** of Pattern Settings (mode 2). Hold a step with notes and touch a pad of rows 3-4.

- **Probability (stock)** — a step that only plays sometimes.
- **Frequency** *(since RC2)* — a step that plays once every n passes: variations that come back every 2, 4 or 8 passes.
- **Dynamics** *(since RC2)* — small changes of velocity and position: a more human pattern.
- **Random-mutate** *(since RC2)* — notes that jump an octave or to another note of the scale; on the drums, to another sample.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#probabilidad)

## Drums

### Drum track view (knobs)

*How to get there:* Press **Drum 1-4**. Every knob does what its label says, with a second layer on Shift.

- **Shape each drum** — exact pitch, ring mod, attack and decay, sample start and cut, a filter with several modes, LFO and several kinds of distortion: many sounds from one sample.
- **All neutral = the original** — with the new knobs at their neutral point, the sample sounds as on the original Circuit.
- **Start over** *(since RC2)* — Clear + the drum's button puts all its knobs back to their defaults.
- **Stereo pair** *(Beta 3.37 only)* — Drum 1 + Drum 2 (or 3 + 4) play a stereo sample: the left one drives both, the right one only fine-tunes.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#drum-pista)

### Drum Preset view

*How to get there:* Press **Preset** with a drum selected. The pads pick the sample as always (Shift + pad = pick without sound).

- **The capture as a drum** — record what is playing (Master FX) and use it as a drum's sample; saving the project puts it in the pack.
- **Swap and copy samples** — reorder the samples or bring one from another pack.
- **Sample arpeggio** *(since RC2)* — holding several samples makes the drum jump from one to the next.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#drum-preset)

### Chromatic and scale view of the drums

*How to get there:* **Shift + Preset** with a drum selected. The pads play the sample transposed along the scale.

- **A drum as a keyboard** — the sample transposed in the project's scale.
- **Rollers** *(since RC2)* — repeat the drum on the micro steps you hold: rolls and ratchets live, stopped too, and recorded with Record.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#drum-cromatica)

## Master FX

### Master FX

*How to get there:* **Mixer**, then **Mixer** again. Effects on the master output, the song pointer, the captured sample and the row of assignable effects. Any other view button leaves.

- **Live effects on the whole master** — Gater, Auto-Filter, Digitise, Phaser, Glitch and the mechanical gesture *(since RC2)*: while held or latched.
- **Song pointer** — repeats or loops parts of the pattern live.
- **Capture** — records up to 3.5 s of what is playing, to play it, put it in a slot or use it as a drum.
- **Slots** — an effect with its settings one touch away; the FX sequencer triggers them.
- **Per project** *(since RC2)* — each project remembers its Master FX settings.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#master-fx)

## FX

### FX view

*How to get there:* The **FX** button: reverb and delay sends per track, as always, plus:

- **The reverb and delay from the unit** — type, decay, time, feedback…, saved with the project.
- **Quick reset** — Duplicate puts the sends and the effects back to zero.
- **Master filter resonance** — on Shift + Octave ▲ / ▼, in steps of 16 *(Beta 3.37 only; in RC2.10, 1-16 / 17-32)*.
- **Master filter off / on** — Shift + pad 25, keeping its position *(Beta 3.37 only)*.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#vista-fx)

## Sidechain

### Sidechain view

*How to get there:* **Shift + FX**. Each track's sidechain presets as always, plus the knobs:

- **Sidechain with knobs** *(since RC2)* — attack, hold, decay and depth of each track's ducking, beyond the presets.
- **Master compressor** *(since RC2)* — its attack and release.
- **Sidechain between drums** — one drum ducks another (the kick ducking the bass, for example).
- **Triggered by patterns** *(since RC2)* — Synth 1 / 2 or MIDI 1 / 2 as the source: their pattern notes duck another track, not only the drums.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#sidechain)

## Scenes and patterns

### Patterns view and pattern chains

*How to get there:* The **Patterns** button. Columns = tracks, rows = patterns. With the **chain mode** *(since RC2)*, each pattern can carry a rule «play n times, jump to B; next time, to C».

- **Pattern chains** *(since RC2)* — a pattern plays n times and jumps to another, and the next time to a third: A A A B structures without chaining by hand.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#patterns)

### Mixer view and scenes

*How to get there:* The **Mixer** button: levels (Octave ▲) and pan (Octave ▼) as always; **Mixer again** = Master FX.

- **Level to 100 or 0** — Shift + knob puts a track at its nominal level or silent in one move.
- **Scenes with chains and repeats** *(since RC2)* — a scene can repeat n times and remember chain mode.
- **Drop-ins on the bar** *(since RC2)* — Shift + a track pad mutes or unmutes the track right as the next bar starts.
- **Cue mode** *(since RC2)* — the mix in mono on the left and, on the right, the tracks you want to hear before bringing them in.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#mixer)

## Projects and packs

### Projects view

*How to get there:* The **Projects** button: loading and saving projects as always, plus copying.

- **Copy projects** *(since RC2)* — duplicates a project into another slot or another pack.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#projects)

### Packs view

*How to get there:* **Shift + Projects**. Loading packs as always, plus deleting.

- **Delete packs** — frees pack slots from the unit.
- **Protected internal memory** — the mod never writes to the internal pack.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#packs)
