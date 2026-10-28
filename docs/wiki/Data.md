# Data

*[Versión en español](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Data-ES) · [Home](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Home) · [Guide by views](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html)*

What is saved where, how to make sure it is saved, and what is lost when you switch off.

## What a pattern holds and how to make sure it is saved

Every track has 8 patterns per project. What is in a pattern travels with it (Duplicate, chains, scenes) and reaches the card when you **save the project**.

### What each pattern carries
| What | Tracks | How it gets there |
|---|---|---|
| Notes, velocity, gate, micro steps and probability of every step | all | As on the original |
| Knob automation: the macros of Synth 1 / 2, the MIDI template knobs, the drums' stock knobs, Mixer level and pan, reverb / delay sends | all | As on the original: **Record** and turn, or hold a step and turn |
| Sample flips | drums | As on the original |
| First and last step, sync rate and direction | all | Pattern Settings, as on the original |
| **Random-mutate, frequency and dynamics** of every step *(since RC2)* | all | [Probability view](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#probabilidad) |
| **Fractal / deconstructed order** and **chain rule** (n passes, jump to B / C) *(since RC2)* | all | [Pattern Settings](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#pattern-settings), [Patterns](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#patterns) |
| **Step that releases the automation** *(Beta 3.41 only)* | Synth 1 / 2, MIDI 1 / 2 | Velocity view, Shift + step pad ([track view](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#synth-nota)) |
| **Own-synth lanes** (the 8 sequenceable knobs) *(since RC2)*; *(Beta 3.41 only)* the **snapshot** of Record + step | MIDI 1 / 2 | Record and turn ([knob pages](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#midi-knobs)) |
| **Step-drummer notes**: in automation lanes (MIDI 1 / 2: the pitch one and, for its page 2, the Release one; Synth 1 / 2: its macro's) | Synth, MIDI | [Step-drummer](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#step-drummer) |
| **FX sequencer values** | MIDI 1 / 2 | [Step-drummer](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#step-drummer) |
| **Sample-mode sample flips** (in the track's level lane) *(since RC2)* | MIDI 1 / 2 | [Sample picker](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#midi-muestra) |
| **Drum chromatic steps** (in the drum's pitch lane) *(since RC2)* | drums | [Chromatic view](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#drum-cromatica) with Record |
| Hits of the **rollers** and of the **drum arpeggio** | drums | With Record, as normal hits |
| *(Beta 3.41 only)* The **copy of the own synth** of MIDI 1 / 2 (in the settings of patterns 1-5, without changing what they play) | MIDI 1 / 2 | On its own, when the project is saved |

- **Not in the pattern**, although chosen with it on screen: the **arpeggiator** (on, order and resolution; *(Beta 3.41 only)* its **modifiers**) and the **gate by holding** are saved in the **project** per track (the arpeggiator per track and pattern number: **duplicating the pattern does not copy it**).
- **Duplicating a pattern** copies everything in the table. **Clear + pattern** in the Patterns view (outside chain mode) deletes it with its rule and its order.

### How to make sure it is saved
1. **A knob turned without Record** changes the sound of the whole project (the patch, the drum knobs, the Mixer…), not the pattern. To make it change **at a step or along the pattern**, record it: **Record** with the sequencer running, or **hold a step and turn** (as on the original).
2. **Save the project: Save twice** (the first press flashes white; the second, fast green). It goes to the last slot used; for another slot, in the Projects view: **Save + the slot's pad** (as on the original). Everything marked «project» or «pattern» in this guide only reaches the card this way.
3. **Loading another project or switching off without saving** loses the changes since the last Save (as on the original). At power-up the last project used is loaded, as it was saved.
4. **Save always off** = **Save Lock** is on (Shift + Save at power-up, an original feature): repeat the gesture to remove it.
5. **The MIDI 1 / 2 own synth** keeps its values **in the device settings** (the same for every project): *(Beta 3.41 only)* also **with the project** when it is saved. To keep a sound across projects or packs, **save it as a patch** ([MIDI 1 / 2 Preset view](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#midi-preset), Clear + pad twice). To make it change inside the pattern, use page 4 (the lanes) or the step-drummer.
6. **A Synth 1 / 2 patch** as it sounds (knobs, edited macro destinations, MIDI received) goes with the project; to have it in the pack and use it in other projects, **save it** in the [Preset view](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#synth-preset) (Clear + pad twice) *(since RC2)*.
7. **Before switching off:** stop the sequencer and wait **2 s** without touching the MIDI 1 / 2 engine (its settings are written to the card only with the transport stopped, so as not to break up the audio), and switch off with the **power button**.
8. **Without a card (the internal memory's pack)** and with the **S** versions, the mod writes nothing of its own: patches, samples and copies are not saved (the Save LED turns red). Projects are, as on the original.

## What comes back after a restart and where it is saved

Five places: the **pattern**, the **project** (both when the project is saved), the **pack** (at once, on the card), the **device settings** (on their own, for every project) and none (lost at power-off).

### The project (Save twice)
| What | Where it is used |
|---|---|
| As on the original: the Synth 1 / 2 patches as they sound, the drums' chosen samples and knobs, Mixer, sends and reverb / delay parameters, side-chain, scenes and chains, tempo, swing, scale and root | — |
| **New drum knobs**: envelope, ring mod, LFO, filter and its mode, start, cut, attack, bitcrush, distortion type; the chromatic view's semitone | [Drums](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#drum-pista) |
| **Noise source** of Synth 1 / 2 (audio inputs) | [Source view](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#synth-fuente) |
| **Master FX**: the 20 knobs, the effects assigned to the slots, compressor attack / release | [Master FX](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#master-fx), [Side-chain](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#sidechain) |
| **Side-chain**: Synth 1 / 2 and MIDI 1 / 2 as a source; K1-K4 of the drum pages | [Side-chain](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#sidechain) |
| **Chain mode** (and in each scene), **scene repeats**, the **cue mode** sends | [Patterns](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#patterns), [Mixer](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#mixer) |
| **Count-in** (the click, as on the original, is not saved) | [Buttons](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#botones) |
| **Arpeggiator** of notes and of drums (per track and pattern; *(Beta 3.41 only)* with its modifiers), **gate by holding**, **fixed length** | [Pattern Settings](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#pattern-settings), [Micro Step](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#micropasos) |
| **Custom scale** and *(Beta 3.41 only)* **Jankó** | [Scales](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#escalas) |
| MIDI 1 / 2 own synth: **gate retrigger**, **LFO shape**, the step-drummer's pitch-vel toggle and page 2 destination | [Knob pages](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#midi-knobs), [Step-drummer](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#step-drummer) |
| *(Beta 3.41 only)* **Stereo drum pairs**: on, distance, width and deviations | [Drums](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#drum-pista) |
| *(Beta 3.41 only)* **The whole own synth** of MIDI 1 / 2: engine, values, matrix, destinations of the sequenceable and *(Beta 3.41 only)* non-sequenceable knobs, FM, voice mode, stereo (loading a project that carries it, the project's wins; an older one leaves the sound as it was) | [MIDI Preset view](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#midi-preset) |

### The pack (written to the card when you do the gesture)
| What | Where it is used |
|---|---|
| **Saved Synth 1 / 2 patches** *(since RC2)* (Clear + pad twice); swaps and copies between packs | [Synth Preset view](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#synth-preset) |
| **Own-synth patches** of MIDI 1 / 2 (64 per pack, *(Beta 3.41 only)* 128; shared by both tracks: engine, values, step-drummer, *(since RC2.02)* matrix, *(Beta 3.41 only)* FM, destinations of the sequenceable and *(Beta 3.41 only)* non-sequenceable knobs, voice mode) | [MIDI Preset view](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#midi-preset) |
| **Samples**: swaps, copies between packs and the **capture** replacing a drum (this one when the project is saved, if it fits) | [Drum Preset view](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#drum-preset) |
| **Projects copied** to another slot or pack; **deleted packs** | [Projects](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#projects), [Packs](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#packs) |

### The device settings (on their own, for every project)
| What | Where it is used |
|---|---|
| As on the original: channels, CC / note / Program Change filters, clock, master compressor on, brightness, Save Lock | [Setup](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#setup), [Advanced Setup](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#advanced-setup) |
| **MIDI 1 / 2 engine**: the engine chosen, all its values, oscillators and order (pads 28 / 29), step-drummer on and its destination, FX sequencer, patch flip | [MIDI Preset view](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#midi-preset) |
| **MIDI Thru jack mode** (Thru, Out 2, Merge, Filter), the project's **Program Change channels**, **cue mode** | [Advanced Setup](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#advanced-setup), [Setup](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#setup), [Mixer](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#mixer) |
| *(Beta 3.41 only)* The drums' **General MIDI mode** and its notes; **USB merge**; **external keyboard to the arpeggiator**; the pads' **velocity curve** | [Setup](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#setup), [Advanced Setup](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#advanced-setup) |

## What is lost at a restart

Whatever is in none of the tables above lives only in memory and is gone at power-off (or when another version is installed).

| What | At power-up |
|---|---|
| **Everything changed since the project's last Save** (as on the original) | The project comes back as it was saved |
| **Master filter** and its **resonance** (as on the original); *(Beta 3.41 only)* the master filter switched off with Shift + pad 25 | At their initial values; the filter, on |
| **Click** on / off and **View Lock** (as on the original) | Off |
| **Latched effects**, **song pointer** and latched sample of Master FX | Off; the song pointer at 0 |
| **Record in the Setup view** (record the internal routings) | Off |
| In the Side-chain view, the **triggers of a drum** by another drum or by a pattern (pads of the drum pages) | Those of the drum's preset |
| Pending **mutes on the next bar** (Mixer, Shift + pad) | — |
| **Latched notes and chords** (Shift + key, Shift + root), the **chord screen** (type and modifiers) and the half-step of **Octave with Jankó** *(Beta 3.41 only)* | No latch; the defaults; Octave at 0 |
| **Split keyboard** and open views (step-drummer, macro editor, picker) | Closed |
| A **sample or patch waiting** to be copied into another pack (Duplicate + A) | Nothing waiting |
| The Master FX **capture** unused, or used in a drum without saving the project | Empty; the drum with its pack sample |
| The own synth's **mod matrix** not saved in a patch *(since RC2.02)* (*(Beta 3.41 only)*: also saved with the project) | Off |
| The pass counters of **frequency** and of the **fractal** order (they restart when stopped) | From the first pass |

- **Installing another version** restarts the device: what was not saved is lost; the project, the pack and the settings stay.
- **Going back to the official firmware:** projects and packs saved with the mod open on the original; the mod's own data sits in parts of the files the original does not use, and the original does not read it.
