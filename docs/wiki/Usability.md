# Usability

*[Versión en español](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Usability-ES) · [Home](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Home) · [Guide by views](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html)*

The conventions that make the mod predictable, the shortcuts that work in every view, and the playing and recording helpers.

## Conventions

Each chapter is a view of the device: how to get there, what every pad, knob and button does, and the sub-menus it opens.

- **Pads 1-32** from top-left to bottom-right: row 1 = 1-8, row 2 = 9-16, row 3 = 17-24, row 4 = 25-32.
- **Knobs K1-K4** on top, **K5-K8** below. «**Shift + X**» = hold Shift while using X; the same with Clear and Duplicate.
- Anything not described here works as on the original device (Novation's official manual).
- *(since RC2)* = new since RC2 (not in RC0.9 / RC0.9S). The safer build, RC2.10S (and the earlier S builds), writes nothing of its own to the card: what is marked «writes to the card» does nothing there (the Save LED turns red).
- *(since RC2.02)* = new in RC2.02 (not in RC2.01).
- *(Beta 3.36 only)* = only in **Beta 3.36**, the test build with the new features (not in RC2.10).
- The **feature list** (the previous manual) sums up every feature in one line, by topic.

## Buttons that work in every view

Shift, Clear, Duplicate, Save and Octave gain functions depending on the view; here, the ones valid almost everywhere.

| Gesture | Where | What it does |
|---|---|---|
| **Clear + knob to the right** | drums, MIDI track engine, Master FX | The knob goes back to its default (both layers, with and without Shift). **Lavender** LED = done, as on the original. |
| **Clear + knob to the left** | drums (stock knobs), MIDI track engine *(since RC2)* | Deletes that knob's automation in the playing pattern, as on the original (**red** LED). On the MIDI engine, that of the knob's two lanes (with and without Shift) that have automation. |
| **Shift** | all | While Shift is held, the shortcuts available light **yellow**; the chosen option, another colour. |
| **Save** | all | Saves the project as always; it also writes into the pack the samples replaced by captures (drum Preset), if they fit in the sample memory *(writes to the card)*. |
| **Press the track button again** | Synth 1 / 2 | Opens the synth's source view (2.3). |
| **Clear + Synth 1 / 2** | its view | *(since RC2)* Its eight macros back to the loaded patch's values. |
| **Clear + a drum's button** | its view | *(since RC2)* Deletes the automation of its knobs in the playing pattern and puts its eight knobs back to their defaults. |
| **Two note-track buttons together** | all | Split keyboard *(since RC2)*: Synth 1 + Synth 2; *(since RC2.02)* any pair of Synth 1, Synth 2, MIDI 1 and MIDI 2. |
| **Shift + Clear** | all | Metronome in four states *(since RC2)*: no metronome → metronome → count-in only → count-in and metronome. While Shift is held the Clear LED shows the state: red (no metronome) / green (metronome) / magenta (count-in only) / cyan (both). The click's volume is the stock's: **Tempo/Swing** and **K5**. |
| **Play** with Record armed and the count-in | stopped | One bar of count-in (4 clicks at the project's tempo, Record blinks red), then recording starts *(since RC2)*. Play during the count cancels it. The count-in is saved with the project. |
| **Shift + Play** | all | *(since RC2)* **Quantizes** the pattern the selected track plays: notes and hits recorded off the grid go to the nearest step (micro steps 1-2 → the start of their step; 3-5 → the start of the next; the last step's, to the first). On the drums, a step with several hits (a roll) stays. While Shift is held the Play LED is yellow; green after quantizing. It replaces the original's Shift + Play (another way to start playback). |
| **Shift + Scales** | all | Custom scale editor *(since RC2)* (2.2). |
| **Mixer twice** | all | Master FX (6.1). |
| **Scales + Preset + Note** at power-up | — | Novation's bootloader recovery mode: lets you install any firmware again. |

- The knob LEDs show the value of the new functions with their **brightness** (brighter = more; bipolar knobs are dark in the middle).
- Animated (pulsing) colours are never used for steady states.
- **LFO synced to the tempo** *(Beta 3.36 only)*: the **LFO rate** knobs (K7 of the VCA-VCF page of the MIDI 1 / 2 engine, Shift + K4 of the matrix, Shift + K7 of the drums, K1 of the Auto-Filter and of the Phaser in Master FX) are **bipolar**: at the centre the LED is dim; **to the right, a free LFO** (faster further right); **to the left, synced to the tempo**, from the centre outwards 1/16T, 1/16, 1/8T, 1/8, 1/4T, 1/4, 1/2T, 1/2, 1 bar T, 1 bar, 2T, 2, 4T, 4, 8T and 8 bars (4 clicks each), each cycle starting on the **bar's first beat** (it is put back in place on every sequencer tick; stopped, it keeps the tempo). In the matrix, each shape of Shift + K4 is a stretch with its own centre. What was saved before with another rate may sound different.

## Playing and recording

### Synth 1 / 2 track view (Note, Velocity, Gate)

*How to get there:* Press **Synth 1** or **Synth 2**. The pads play the synth as always.

- **Source view** — the synth can process an audio input instead of its noise.
- **Split keyboard** *(since RC2)* — one synth on top and the other below, each with its scale, octave and velocity; *(since RC2.02)* with any pair of note tracks.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#synth-nota)

### Scales view and custom scale

*How to get there:* Press **Scales** as always (root and stock scale); **Shift + Scales** for the custom scale.

- **Custom scale** *(since RC2)* — up to 7 notes over the root and a free period (for example, a scale that repeats every 7 semitones). The note tracks' pads, the quantising and random-mutate use it; saved with the project.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#escalas)

### Micro Step view (note tracks)

*How to get there:* Press **Gate twice** with a note track selected (Synth 1 / 2, MIDI 1 / 2).

- **Micro steps and Tie (stock)** — place each note off the grid and tie it to the next step.
- **Gate by holding** *(since RC2)* — when entering notes by hand, how long you hold is how long the note lasts.
- **Fixed length** *(since RC2)* — every note you enter by hand gets the same length.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#micropasos)

### Pattern Settings view

*How to get there:* The **Pattern Settings** button with a track selected: first / last step, sync rate and direction as always, plus pads 25-28 and the arpeggiator (Shift).

- **Nudge** — rotates the pattern so that it starts on another step.
- **Fractal and deconstructed orders** — walk through the pattern another way without changing its notes.
- **Arpeggiator** *(since RC2)* — the pattern's chords (and the ones you play) sound note by note, in their order and resolution; on the drums, jumping from sample to sample.
- **Dynamics and random-mutate** (pad 25) — variations so that the pattern does not always sound the same.

→ [Full details in the guide](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#pattern-settings)
