# Guide by views — CIRCUIT-HACKS (RC2.09)

Circuit Tracks running the official firmware 1.2.1 (build 4486), patched. This guide walks through the device's views and explains everything each one can do. The [feature list](MANUAL.en.md) sums up every feature by topic.

## Views

**0. Introduction**

- [0.1 How to read this guide](#convenciones)
- [0.2 Buttons that work in every view](#botones)

**1. Setup**

- [1.1 Setup view](#setup)
- [1.2 Advanced Setup view](#advanced-setup)

**2. Stock synths (Synth 1 / 2)**

- [2.1 Synth 1 / 2 track view (Note, Velocity, Gate)](#synth-nota)
- [2.2 Scales view and custom scale](#escalas)
- [2.3 Synth source view](#synth-fuente)
- [2.4 Synth 1 / 2 Preset view](#synth-preset)

**3. MIDI tracks (MIDI 1 / 2)**

- [3.1 MIDI 1 / 2 Preset view](#midi-preset)
- [3.2 Knob pages of the MIDI 1 / 2 engine](#midi-knobs)
- [3.3 Mod matrix](#midi-matriz)
- [3.4 4-operator FM](#midi-fm)
- [3.5 CC editor of the MIDI macros (pad 25)](#midi-cc)
- [3.6 Step-drummer view](#step-drummer)
- [3.7 Sample mode and sample picker](#midi-muestra)

**4. Pattern Settings**

- [4.1 Pattern Settings view](#pattern-settings)
- [4.2 Micro Step view (note tracks)](#micropasos)
- [4.3 Probability view (note tracks and drums)](#probabilidad)

**5. Drums**

- [5.1 Drum track view (knobs)](#drum-pista)
- [5.2 Drum Preset view](#drum-preset)
- [5.3 Chromatic and scale view of the drums](#drum-cromatica)

**6. Master FX**

- [6.1 Master FX](#master-fx)

**7. FX**

- [7.1 FX view](#vista-fx)

**8. Sidechain**

- [8.1 Sidechain view](#sidechain)

**9. Scenes and patterns**

- [9.1 Patterns view and pattern chains](#patterns)
- [9.2 Mixer view and scenes](#mixer)

**10. Projects and packs**

- [10.1 Projects view](#projects)
- [10.2 Packs view](#packs)

**A. Appendix**

- [A.1 What is saved and where](#guardado)
- [A.2 MIDI of the new features](#midi)
- [A.3 Installing and going back](#instalar)

## 0. Introduction

<a id="convenciones"></a>
### 0.1 How to read this guide

*How to get there:* Each chapter is a view of the device: how to get there, what every pad, knob and button does, and the sub-menus it opens.

- **Pads 1-32** from top-left to bottom-right: row 1 = 1-8, row 2 = 9-16, row 3 = 17-24, row 4 = 25-32.
- **Knobs K1-K4** on top, **K5-K8** below. «**Shift + X**» = hold Shift while using X; the same with Clear and Duplicate.
- Anything not described here works as on the original device (Novation's official manual).
- *(since RC2)* = new since RC2 (not in RC0.9 / RC0.9S). The safer build, RC2.09S (and the earlier S builds), writes nothing of its own to the card: what is marked «writes to the card» does nothing there (the Save LED turns red).
- *(since RC2.02)* = new in RC2.02 (not in RC2.01).
- *(Beta 3.22 only)* = only in **Beta 3.22**, the test build with the new features (not in RC2.09).
- The **feature list** (the previous manual) sums up every feature in one line, by topic.

<a id="botones"></a>
### 0.2 Buttons that work in every view

*How to get there:* Shift, Clear, Duplicate, Save and Octave gain functions depending on the view; here, the ones valid almost everywhere.

**In this view**

- **Put a knob back or delete what was recorded** — Clear + knob, without hunting for the value or clearing the whole pattern.
- **Metronome and count-in** *(since RC2)* — a bar of clicks before recording, to come in on time.
- **Split keyboard** *(since RC2)* — both synths at once, one per hand.
- **Custom scale** *(since RC2)* — scales the unit does not have, even with periods other than the octave.
- **Shortcuts in yellow** — while Shift is held, the view shows what it offers.

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
- **LFO synced to the tempo** *(Beta 3.22 only)*: the **LFO rate** knobs (K7 of the VCA-VCF page of the MIDI 1 / 2 engine, Shift + K4 of the matrix, Shift + K7 of the drums, K1 of the Auto-Filter and of the Phaser in Master FX) are **bipolar**: at the centre the LED is dim; **to the right, a free LFO** (faster further right); **to the left, synced to the tempo**, from the centre outwards 1/16T, 1/16, 1/8T, 1/8, 1/4T, 1/4, 1/2T, 1/2, 1 bar T, 1 bar, 2T, 2, 4T, 4, 8T and 8 bars (4 clicks each), each cycle starting on the **bar's first beat** (it is put back in place on every sequencer tick; stopped, it keeps the tempo). In the matrix, each shape of Shift + K4 is a stretch with its own centre. What was saved before with another rate may sound different.

## 1. Setup

<a id="setup"></a>
### 1.1 Setup view

*How to get there:* Open it as on the original. MIDI channels and device options as always, plus:

**In this view**

- **Shared channels (internal loopback)** — a MIDI track plays a synth or the drums of the unit itself.
- **Returns through strips 3 / 4** — the reverb and the delay as mixer channels.
- **Program Change channels** *(since RC2)* — listens to and sends program changes on channels of their own.
- **Record the internal routings** *(since RC2)* — what the MIDI track plays on a synth is recorded into it too.

| Control | What it does |
|---|---|
| Track buttons + pads 1-15 | Each track's channel; MIDI 1 / 2 may use a channel another track has (what they send reaches it internally: **internal loopback**). Synth 1 / 2 can also be picked when you entered from their view. |
| **Pad 16** | Channel 16 (project and FX): receiving and sending what is not a Program Change. |
| **Pad 22 / 23** | The reverb return goes through mixer strip 3 / the delay return through strip 4 (cream / peach). |
| **Pad 29 (PGM Rx)** *(since RC2)* | First touch: pads 1-16 show the **listen channel** of the project's Program Changes (white); a pad picks it; again = on / off. |
| **Pad 30 (PGM Tx)** *(since RC2)* | The same with the **output channel**. Both are 16 by default. What arrives on the listen channel is sent again on the output one. |
| **Record** *(since RC2)* | Yellow = what a MIDI track sends to a synth over the shared channel is also recorded into that synth (scale or octave changes in real time). Off by default; off again after a restart. *(Beta 3.22 only)*: while yellow, nothing is recorded into a note track muted in the Mixer: its steps sound and are recorded only into the synth on the shared channel (a chord bank). |
| **K4** *(Beta 3.22 only)* | **General MIDI** mode of the drums: to the right on (green), to the left off (dim): **turning it off closes the number** and the drums go out as on stock again. While on, every hit of Drum 1-4 goes out over MIDI with **its GM note** instead of the stock one (60 / 62 / 64 / 65), on the drums' channel (10 by default, the one you pick here). Inside the device it sounds the same. |
| **K5-K8** *(Beta 3.22 only)* | With the mode on, the GM note of Drum 1-4 (the knobs over the drum tracks; off, they do nothing): 35-81, two clicks a note; by default 36 kick, 38 snare, 42 closed hat, 46 open hat. **Every new note sounds** once on the drums' channel and **its number shows on the pads**, in the drum's colour; **Shift** or leaving Setup confirms it (saved in the settings) and the Setup pads come back. While the number shows, the Setup pads do nothing. LEDs: each drum's colour, brighter for a higher note (dark with the mode off). |

- Patch flip always goes out on its MIDI track's channel.

<a id="advanced-setup"></a>
### 1.2 Advanced Setup view

*How to get there:* Open it as on the original. Besides its stock settings (master compressor, etc.):

**In this view**

- **MIDI Thru, Merge and Filter** *(since RC2)* — the Thru jack can merge the incoming MIDI with the unit's own, or filter it.

- **Duplicate** = mode of the MIDI Thru jack *(since RC2)*: Thru (dim red, DIN In by hardware) → Out 2 (green) → **Merge** (yellow: DIN In + the device's MIDI) → **Filter** (blue: DIN In without the channels the device listens to). No SysEx in Merge / Filter. Saved in the settings.
- Pads 22 / 23 do not light here (they do nothing there).
- **Pad 23 = USB merge** *(Beta 3.22 only)*: what comes in on the **DIN In** (a keyboard on a MIDI cable) also goes out over **USB** to the computer, together with the device's own MIDI. Green on, dim off; saved in the settings. With Clock Tx on, the DIN In's clock and transport are not copied (the computer would get two clocks); SysEx is not copied; what comes in over USB is not sent on.
- The master compressor's attack / release are set in the Sidechain view, K7 / K8.

## 2. Stock synths (Synth 1 / 2)

<a id="synth-nota"></a>
### 2.1 Synth 1 / 2 track view (Note, Velocity, Gate)

*How to get there:* Press **Synth 1** or **Synth 2**. The pads play the synth as always.

**In this view**

- **Source view** — the synth can process an audio input instead of its noise.
- **Split keyboard** *(since RC2)* — one synth on top and the other below, each with its scale, octave and velocity; *(since RC2.02)* with any pair of note tracks.

- **Pressing the same button again** (with its view on screen) opens the synth's **source view** (2.3).
- **Synth 1 + Synth 2 together** (hold one, press the other) opens the **split keyboard** *(since RC2)*; *(since RC2.02)* **any pair of note tracks** (Synth 1, Synth 2, MIDI 1, MIDI 2: hold one button and press another):
- the top two rows play the track you held first and the bottom two the other one, each with its scale, octave, velocity and colours (in RC2: Synth 1 always on top);
- the knobs and Octave are those of the track you pressed first; a drum button does not open the split keyboard;
- *(Beta 3.22 only)* **hold a track button** (Synth 1 / 2, MIDI 1 / 2, Drum 1-4) with the split keyboard open: while you hold it, **the 8 knobs (and their lights) are that track's**; let go and they go back to the first one;
- any track button (*(Beta 3.22 only)* a short tap, no knob turned) or view button closes it (held notes are released); Play, Record, Octave and Shift do not.
- The macro knobs work as always; their destinations can be edited on the device (source view, pad 32).
- **Velocity view, Shift + a step pad** *(Beta 3.22 only)* (Synth 1 / 2 and MIDI 1 / 2): that step **lets go of the automation**: no lane plays there and the parameters the automation had moved go back to their knob's position (the one before the automation; turning the knob by hand changes it). Again = off. With Shift, in the Velocity view, the step pads are yellow and the marked ones red; on the 17-32 page, steps 17-32. Saved with the pattern.
- **Chord screen** *(Beta 3.22 only)* (Synth 1 / 2 and MIDI 1 / 2, only in the **expanded Note view**: Note twice): **Shift + pad 8** turns it on and off (with Shift pad 8 is yellow, green with the screen on).

| Pads | What they do |
|---|---|
| Row 1 | The chord type: major, minor, 7, m7, maj7, sus4, dim, aug. **Shift + pads 1-7**: sus2, 6, m6, add9, 9, 7sus4, fifth (with Shift the row yellow; the chosen one white) |
| Pads 9-12 | The inversion: root position, 1st, 2nd, 3rd (orange; the same again = root position) |
| Pad 13 | Open voicing: the second note an octave up |
| Pad 14 | The root added an octave down |
| Pad 15 | Diatonic: the chord made of thirds of the project's scale (the custom one and Jankó too): 3 notes, 4 when the type has 4 or more |
| Pad 16 | Latch: the chord keeps sounding after the pad is let go, until the next root (or until latch or the screen is turned off) |
| Rows 3-4 | The roots: the same notes as the Note view's keyboard (scale, root, Octave, Jankó). While you hold the pad its chord sounds, up to 6 notes, with the pad's velocity |

- Pads 13-16 green on, dim off.
- What you play sounds and is recorded with Record as **plain notes of the pattern**: it plays back the same without the chord screen. With the **arpeggiator** on, the chord is arpeggiated from one finger.
- Each track's type and modifiers are **not saved** (lost at power-off).
- On MIDI 1 / 2 in the sample mode, the expanded Note view stays the sample picker.

<a id="escalas"></a>
### 2.2 Scales view and custom scale

*How to get there:* Press **Scales** as always (root and stock scale); **Shift + Scales** for the custom scale.

**In this view**

- **Custom scale** *(since RC2)* — up to 7 notes over the root and a free period (for example, a scale that repeats every 7 semitones). The note tracks' pads, the quantising and random-mutate use it; saved with the project.

- **Shift + Scales** opens the Scales view with the **custom scale editor** *(since RC2)*; with Shift held the Scales button shows yellow. Scales again, Shift + Scales or another view close it.
- **The editor's keyboard** is two octaves of a piano from the **root** (the Scales view's, picked as always out of the editor): row 4 = the white keys of the first octave (root, +2, +4, +5, +7, +9, +11, +12), row 3 = its black keys; rows 2 / 1 = the second octave (+12 … +24).
- **Pressing a key** adds or removes it (up to **7**). The highest one pressed is the **period**: the root of the next iteration (not necessarily the octave); the others are the scale's notes. Colours: root white, notes green, period orange, free keys dim.
- **On the note tracks** (Synth 1 / 2, MIDI 1 / 2) every row of pads is **one iteration**: its notes and the period note at the end, like the octaves of a stock scale. With **4 notes or fewer**, **two iterations a row** (one in each half). Octave ▼ / ▲ move one row.
- The custom scale also drives **which notes of the sequence light up**, the quantising and **random-mutate** (another note of the same iteration).
- **Picking a stock scale** (pads 17-32 out of the editor) switches the custom scale off; the keys are kept: going back to the editor switches it on again. While it is on, no stock scale shows as selected.
- Saved **with the project**; a new project starts without a custom scale.
- **Jankó** *(Beta 3.22 only)*: in the editor, **Shift + pad 8** (top right; yellow with Shift) turns on the **isomorphic Jankó layout** (pad 8 cyan while on): on the note tracks every row goes up a **semitone** and every column a **whole tone**, and the bottom-left pad is the Scales view's **root**. Every chord type has the same shape in any key (in the expanded Note view, with four rows, every triad and seventh chord fits). All 12 notes are there: the notes that sound light on their pads and random-mutate picks any of the 12 of its octave. **Octave ▼ / ▲ = a semitone** (Shift + Octave still transposes the pattern an octave). Shift + pad 8 again, a key of the editor or a stock scale turn it off. Saved with the project.

<a id="synth-fuente"></a>
### 2.3 Synth source view

*How to get there:* With the Synth 1 / 2 view on screen, **press its button again**. Any button closes it.

**In this view**

- **Noise source** — replaces the patch's noise with audio input 1 or 2 (normal or inverted): the synth's filter, envelopes and effects process your outside signal in time with the notes.
- **Macro destinations** *(since RC2)* — decide what each macro knob moves (up to 4 destinations a macro, with their range and depth) without Components.
- **The synth's step-drummer** — sequences the macros by pairs of steps: each knob sets a macro's position on two steps of the pattern.

### Pads 25-30: the source
| Pad | Source of the synth's noise |
|---|---|
| 25 | Noise (normal) |
| 26 | Audio input 1 |
| 27 | Audio input 2 |
| 28 | Input 1, phase inverted |
| 29 | Input 2, phase inverted |
| 30 | Opens the synth's **step-drummer** (below) |

- The patch needs some noise level (CC 56) for the source to be heard. The source is saved with the project.
- If Setup routes the reverb / delay returns through strips 3 / 4, that signal is what reaches the synth.

### Pad 32: editor of the macro knob destinations *(since RC2)*
Every macro knob has 4 slots; every slot, a destination, a span of the travel (start and end) and a depth.
1. **Pad 32** (teal) = editor on; the knobs no longer move the macros.
2. **Turn a knob** to pick its macro (white LED); the first turn changes nothing.
3. The knob changes the current field; **Octave ▼ / ▲** = next / previous field: slot (1-4, yellow) → start (green) → end (orange) → destination (white = CC; light blue, magenta, violet = NRPN of banks 0, 1, 2) → depth (teal positive, red negative). The pads draw the number.
4. Any pad releases the macro; pad 32 turns the editor off.
- The destination walks first the 31 parameters with a CC (by number), then the 39 that only have an NRPN. Changes sound at once; to keep them in the pack, save the patch (Preset view).

### Pad 30: the synth's step-drummer
The step-drummer view is the MIDI tracks' one (3.5): pads 1-16 steps, 17-24 = **macro 1-8** as destination, K1-K8 = the 8 step pairs. Each pair's value is the macro's position, written as automation; an empty pair starts at 0 *(since RC2)* (it started at the macro's present position).
- *(since RC2)* Play and Record no longer close the synth's step-drummer; if you go to another view, **pressing Synth 1 / 2** opens it again (until you close it with pad 30).

<a id="synth-preset"></a>
### 2.4 Synth 1 / 2 Preset view

*How to get there:* Press **Preset** with Synth 1 / 2 selected. The pads pick a patch as always (4 pages, the pack's 128 patches).

**In this view**

- **The voice mode at a glance** *(since RC2)* — mono, mono with glide and poly patches told apart by colour.
- **Save the patch** *(since RC2)* — stores the sound as you left it into the pack (the original only saves patches from Components).
- **Swap and copy** — reorder the pack's patches or take one to another pack.

| Gesture | What it does |
|---|---|
| Patch colours *(since RC2)* | **Dark blue** = mono, **lavender** = mono with glide, track colour = poly; the chosen one, lighter. |
| **Clear + pad**, **Clear + the same pad** within ~5 s *(since RC2)* | **Saves** the patch as it sounds (knobs, received MIDI, macro destinations) into that slot. The first touch asks (blinks white); another pad moves the question *(writes to the card)*. |
| **Duplicate + pad A + pad B** (same pack) | Swaps the two patches. |
| **Duplicate + pad A**, load another pack, **Duplicate + pad B** | Copies patch A over B in the other pack (A's pack does not change); B may be empty *(writes to the card)*. |

- The original cannot save patches from the device. The saved patch keeps the name of the one that was loaded.
- Not in the internal memory's pack (read-only for the mod): the Save LED turns red.

## 3. MIDI tracks (MIDI 1 / 2)

<a id="midi-preset"></a>
### 3.1 MIDI 1 / 2 Preset view

*How to get there:* Press **MIDI 1** or **MIDI 2**, then **Preset**. Besides the stock templates, the track's own synth lives here.

**In this view**

- **A synth on each MIDI track** — MIDI 1 and 2 sound on the unit itself with their engine (processed line input, oscillator, VA-drum or granular) and still send MIDI.
- **FX sequencer** — an engine with no sound: it triggers Master FX effects on the steps you choose.
- **Own-synth patches** *(since RC2)* — 64 sounds a pack for those engines, one touch away.
- **Mod matrix** *(since RC2.02)* — eight sources (velocity, note, random, LFO 2, envelope 2, a drum hit, the pattern position, stepped random) that move any parameter of the engine.
- **Patch flip** — every note sends a program change: the outside gear changes sound step by step.
- **CC editor** — changes which CC each knob of the template sends, without Components.

- **External keyboard** *(since RC2.08)*: notes coming in over MIDI (USB or DIN) on the channel of MIDI 1 / 2 **play its own synth** (before, they were only recorded); they are not sent again to the MIDI out.
### Pads
| Pad | Function |
|---|---|
| 1-5 | Engine knob page: 1 VCA-VCF, 2 OSC 1 (granular in that engine), 3 OSC 2, 4 sequenceable, 5 modulation. **Clear + the pad** *(since RC2)*: that page's values (with and without Shift) back to their defaults. |
| 6 | *(since RC2.02)* **Mod matrix** (light blue; see “Mod matrix”). **Clear + pad 6**: every source off. |
| 9-24 | **Own-synth patches** *(since RC2)*: see below. |
| 25 | **CC editor** of the MIDI macros (3.4). |
| 26 | **Patch flip**: every note of the track goes out as a Program Change (on the track's channel; if that is a synth's or the drums' channel, also internally). Exclusive with the engine. |
| 27 | Track **engine**: off → yellow (line input) → green (oscillator) → red (VA-drum) → magenta (granular) → cyan (sample *(since RC2)*) → blue (FX sequencer). |
| 28 | One / two oscillators (oscillator and VA-drum). |
| 29 | Chain order: VCA → FX → filter / filter → VCA → FX (in the VCA-VCF page's colour *(since RC2)*). |
| **Shift + 29** *(since RC2)* | **Gate retrigger**: on (green with Shift, the default) = every new note restarts the envelope; off (yellow) = **legato**: with other notes held, a new note only changes the pitch. Saved with the project. |
| 30 | Opens the **step-drummer**; **Shift + pad 30** turns it off. |
| 31 | VA-drum only: velocity scales the pitch and filter envelopes. |

### Own-synth patches (pads 9-24) *(since RC2)*
- 16 slots per page; **Octave ▼ / ▲** = 4 pages (64 slots per pack, shared by MIDI 1 and MIDI 2).
- **Touch** = load (the tonic sounds while you hold the pad). **Clear + pad** twice = save. **Duplicate + A + B** = swap; **Duplicate + A**, another pack, **Duplicate + B** = copy to another pack (Duplicate yellow while one is waiting).
- Colours: dim peach = has a patch, bright = the last used, violet = empty.
- A patch stores the whole engine: chosen engine, oscillators, order, every value and the step-drummer setting *(writes to the card)*.
- **Clear + the track button** *(since RC2)* puts every engine value back to its default (the chosen engine stays).

### The engines (pad 27)
- **Choosing the engine** *(Beta 3.22 only)*: a tap on **pad 27** opens the **engine row** on **pads 17-23**: off (white), line input, oscillator, VA-drum, granular, sample and FX sequencer, in their colours; the current one bright, the others dim. Tapping one picks it and the row stays open; **pad 27 again** closes it and the patch list comes back (pads 9-24, which load nothing meanwhile). Shift + pad 27 still steps to the next engine (in RC2.09, every tap of pad 27).
- **Line input** (yellow): the track's audio input (line 1 on MIDI 1, line 2 on MIDI 2) goes through the VCA-VCF; the track's notes trigger it.
- **Oscillator** (green): morph sine → triangle → saw → square, SHAPE, second oscillator (pad 28) with FM, ring, sync and bitwise modes; two notes = paraphony (with one oscillator, *(since RC2)*: the last note has priority and releasing it goes back to the previous one).
- **VA-drum** (red): one-shot VCA, decay envelopes for pitch (Sustain knob) and filter (Release knob), white noise (LFO speed) and random values instead of the LFO.
- **Granular** (magenta): up to 16 grains from a pack sample or the capture (page 2, next section).
- **FX sequencer** (blue): the track's step-drummer triggers the slots of Master FX's bottom row (6.1).
- **FM** (violet) *(Beta 3.22 only)*: **pad 24** of the row: a 4-operator FM synth, a variant of the oscillator, with 16 algorithms (classic, percussive, bells and strings) and its knobs on **page 7** (chapter «4-operator FM»).
- The track keeps sending its MIDI with any engine.

<a id="midi-knobs"></a>
### 3.2 Knob pages of the MIDI 1 / 2 engine

*How to get there:* With the engine on, pads 1-5 of the Preset view pick what the 8 knobs do; Shift gives a second layer.

**In this view**

- **VCA-VCF** — level and filter with their envelope and LFO; with Shift, the filter type and the effect type.
- **Oscillators** — a waveform that morphs from sine to square, and a second oscillator with FM, ring and sync.
- **Granular** — turns a sample into textures: grains that read it at another place, speed or direction, to freeze, stretch or slice it.
- **Page 4** — the 8 parameters that can be recorded as automation (*(Beta 3.22 only)*: with Shift + knob, any of the 33; Record + step = a snapshot of the values).

### Page 1 — VCA-VCF
| Knob | Alone | With Shift |
|---|---|---|
| K1 | Attack | Sustain |
| K2 | Release | Decay |
| K3 | Envelope → level | LFO → level |
| K4 | Envelope → filter | LFO → filter |
| K5 | Filter | Filter type (DJ, LP 12, HP 12, BP, notch, LP 24, HP 24) |
| K6 | Resonance | VCA gain (up to +18 dB with saturation) |
| K7 | LFO speed (bipolar *(Beta 3.22 only)*: right free, left synced; 0.2) | — |
| K8 | Effect amount | Effect type (soft, hard, fold, wavefold, ring, comb, chorus) |

### Page 2 — OSC 1 (oscillator and VA-drum)
| Knob | Alone | With Shift |
|---|---|---|
| K1 | TUNE | FINE |
| K2 | SHAPE | MIX OSC 1 ↔ OSC 2 |
| K3 | Envelope → pitch | BITSYNC |
| K4 | Envelope → shape | — |
| K5 | LFO → pitch | — |
| K6 | LFO → shape | — |
| K7 | WAVE (morph) | — |
| K8 | LFO → morph | Envelope → morph |

**What SHAPE does on each waveform** (K2; SHAPE 2 on OSC 2, the same). The knob's centre is the pure wave (on the saw *(Beta 3.22 only)*, fully left); the envelope (K4) and the LFO (K6) move SHAPE from the knob's position. With WAVE between two waves, SHAPE acts on both at once, each in its own way:

| Wave (WAVE) | SHAPE left of centre | Centre | SHAPE right of centre |
|---|---|---|---|
| Sine (0) | Nothing: the pure wave | Pure | **Wavefold**: the wave is amplified (up to about 8 times fully right) and folds back on itself: more harmonics the further right |
| Triangle (42) | *(Beta 3.22 only)* **Exponential ramps**: sharp peaks and wide valleys, more harmonics the further left (in RC2.09, nothing) | Pure | **Wavefold**, as the sine |
| Saw (84) | *(Beta 3.22 only)* The whole travel: fully left a plain saw; towards the right, a **supersaw** of 7 saws (the centre one and 6 detuned ones that get louder and spread apart; fully right, the full supersaw) | Half a supersaw | The full supersaw fully right |
| Saw in RC2.09 | The ramp bends upwards (rises fast at first, then flattens) | Straight ramp | The ramp bends downwards (starts flat, rises at the end) |
| Square (126) | An ever narrower pulse (down to about 3 %) | Square (50 %) | An ever narrower pulse the other way (up to about 97 %; it sounds like the left one) |

### Page 2 — granular
| Knob | Alone | With Shift |
|---|---|---|
| K1 | Pitch ±24 st | Fine ±1 st |
| K2 | Position in the sample | Position spread |
| K3 | Scan (centre frozen) | *(Beta 3.22 only)* **Bipolar**: to the left, the chance of a reversed grain (up to 100 %); to the right, the pitch spread (up to ±24 st). In RC2.09: reverse grain probability |
| K4 | Grain size 5-500 ms | *(Beta 3.22 only)* **Stereo spread** (see below). In RC2.09: pitch spread |
| K5 | Density 1-16 grains | Window |
| K6 | Scan zone | Note mode: pitch / slicer / stretch *(since RC2)* |
| K7 | LFO → position | LFO → size |
| K8 | Envelope → position | Source: the capture or a drum's sample *(since RC2)* |

- **Note mode (Shift + K6):** **pitch** = the notes change the grains' pitch; **slicer** = the sample is cut into 16 slices and each note plays one (note 36 the first one, each note up the next one; it starts again every 16 notes); **stretch** *(since RC2)* = the notes change the pitch and the stretch from the position (K2) to the end lasts **K3 steps** (1-64) at any tempo, without changing the pitch, aligned with the start of the transport; stopped, the position stays frozen.

- **Stereo granular** *(Beta 3.22 only)*: with **Shift + K4** above 0, each grain goes to one side at random, further apart the higher it is; the **track's pan** (Mixer) sets the proportion: centred, half and half; to the right, more grains on the right. The stereo part (what differs between the sides) only follows the VCA and the track level: the engine's filter and effect, the pan, the sends and the sidechain act on the centre.

### Pages 3-5
- **Page 3 (OSC 2):** *(since RC2)*: the eight values without Shift, following the printed labels: K1 Oscillator TUNE 2, K2 Osc mod SHAPE 2, K3 Amp envelope MIX OSC 1 ↔ OSC 2, K4 Filter envelope FM, K5 Filter frequency FINE 2, K6 Resonance BITSYNC, K7 Modulation WAVE 2, K8 FX RING (in RC0.9: K1 TUNE 2 / FINE 2, K2 SHAPE 2 / FM, Shift + K3 RING, K7 WAVE 2).
- **Page 4:** the 8 sequenceable values: with Record + Play their moves are recorded into the pattern (TUNE, Release, Env → level, Env → filter, Filter, Resonance, LFO speed, Effect). *(Beta 3.22 only)*: **Shift + knob** = that knob's **destination**: the engine's 33 parameters in the modulation matrix's order and colours (the LED in its page's colour; 4 clicks a parameter); with **Clear held before Shift**, the factory one. While you pick, **pads 9-24 show where the destination lives**, as when a matrix knob turns: its page's pad bright and that page's knobs (K1-K8 above, Shift + K1-K8 below; the destination bright). The lane records and plays the new destination (what it already held now moves that parameter). They are saved with the own-synth patches (MIDI 1 / 2's Preset view); a patch without them loads the factory ones.
- **Snapshot of the values into a step** *(Beta 3.22 only)*: in MIDI 1 / 2's track view (engine on), **Record held + a step pad** (pads 1-16; with 17-32, steps 17-32) writes into that step's lanes the parameters that are **not at their initial value** (the one of Clear + knob to the right), and only those. A parameter without a lane takes one whose parameter is at its initial value (in lane order), and that lane is cleared in the pattern first; when they do not fit, the first ones in the matrix's order. The step keeps its notes and Record stays as it was.
- **Page 5:** ADSR on top, LFO below. *(since RC2)*: **Shift + K8 = the LFO's shape**: reverse saw (orange, the usual one), saw (magenta), triangle (green), square (red), sine (cyan), sample & hold (white: a random value each cycle); *(since RC2.02)*: **slewed sample & hold** (violet: it glides from one random value to the next during each cycle), and **with no shape saved (a new or older project) the triangle** (in RC2: the reverse saw; an own-synth patch from before the shapes still loads the reverse saw). A step every 4 clicks, K8's LED with Shift in its colour. Saved with the project and in the own-synth patch; with the VA-drum the LFO stays its noise.
- **Page 6** *(since RC2.02)*: the mod matrix (next section).
- **Page 7** *(Beta 3.22 only)*: with the FM engine, its operators and its algorithm (chapter «4-operator FM»).
- Type knobs show colour (type) and brightness (position within the type). Everything goes out and comes in over CC / NRPN (MIDI reference).

<a id="midi-matriz"></a>
### 3.3 Mod matrix

*How to get there:* *(since RC2.02)* MIDI 1 / 2 with the engine on: Preset view, **pad 6**. The 8 knobs become 8 modulation sources.

| Knob | Source | With Shift |
|---|---|---|
| K1 | The note's velocity | — |
| K2 | The note (C3 = 0; one octave = a quarter of the travel) | — |
| K3 | Random: a new value at each note | — |
| K4 | LFO 2 | Shape × rate: triangle (green, the initial one), saw (magenta), square (red), sample & hold (white: steps), slewed sample & hold (violet: gliding); the engine LFO's colours; in each shape, 0.05 to 20 Hz ; *(Beta 3.22 only)*: in each shape, the left half of its stretch synced and the right half free (0.2) |
| K5 | Envelope 2: attack and decay from each note | Attack × decay: attack 0 (white), short (light blue), medium (teal), long (blue); in each, the decay from 20 ms to 4 s |
| K6 | A drum hit: a decay from each hit | Drum 1-4 (orange, yellow, violet, teal) × its decay |
| K7 | The pattern position: from 0 on the first step to full on the last | — |
| K8 | Stepped random: a new value every N sequencer steps | N = 1, 2, 4, 8 or 16 steps |

- **The knob's position is the destination and the amount.** Fully left = off. Turning right goes through **every parameter of the knob pages** (33: page 1's, then page 2's, page 3's and the page 5 ones not seen before), one stretch each: inside a stretch the amount grows from 1/16 to full; into the next stretch the destination changes and the amount starts again.
- **Slow knobs:** two clicks a step, 16 steps a destination.
- **The LED's colour is the destination page's** (the colours of pads 1-5: orange VCA-VCF, green OSC 1, teal OSC 2), its **brightness** the amount; dark = no destination.
- **While you turn a source** (and 1.5 s after), the pads show where its destination lives: its page pad lights up and pads 9-16 / 17-24 are that page's K1-K8 / Shift + K1-K8 (dim the ones with a parameter, bright the destination). While they show, pads 9-24 do not load patches.
- **Full amount** = the whole source sweeps the parameter's whole range. The bipolar sources (note, random, LFO 2, stepped random) go up and down; the others only up. The parameter's stored value does not change: the matrix is added when it is sent.
- Several sources can share a destination (they add up). TUNE moves in semitones and FINE in fractions; with the granular engine, its ranges; in sample mode the sample parameter picks the sample (from the capture to 64) and only TUNE changes the pitch.
- **Clear + knob** = that source off; **Clear + Shift + knob** = its parameter back to the default; **Clear + pad 6** = all off.
- **Saved with the own-synth patches** (pads 9-24: Clear + pad twice, also when swapping them or copying them between packs); a patch saved before loads it off. *(Beta 3.22 only)* also **saved with the project** (with the rest of the own synth); before, it was not saved with the project nor across a power-down. No CC / NRPN.
- The modulations reach the engine some 100-250 times a second, shared by everything that moves on the track: several fast sources at once update more slowly.

<a id="midi-fm"></a>
### 3.4 4-operator FM

*How to get there:* *(Beta 3.22 only)* MIDI 1 / 2: Preset view, a tap on **pad 27** and **pad 24** of the engine row (violet). **Pad 7** opens its knob page (bright violet on it).

| Knob | Alone | With Shift |
|---|---|---|
| K1-K4 | Ratio of operators 1-4: 0.5 … 16 (green = whole, light blue = and a half, teal = inharmonic: 0.71, 1.41, 4.24) | Attack of operators 1-4 (0 … about 3 s; light blue) |
| K5 | Level of operator 1 (orange) | Algorithm (16, 8 clicks each; its family's colour) |
| K6 | Level of operator 2 | Feedback (magenta) |
| K7 | Level of operator 3 | Noise (white) |
| K8 | Level of operator 4 | Release (blue) |

- **It is a variant of the oscillator:** the note, TUNE / FINE, the pitch envelope and the vibrato of page 2 still apply; after it, the VCA-VCF, the effect and the matrix as with the oscillator. One note at a time (the last one wins).
- **The level** of a carrier is its loudness; of a modulator, how much it modulates (up to 4π).
- **A/R envelopes with a fixed sustain:** while the note is held, a **sustained** operator stays up after its attack; a **percussive** one (the algorithm says which) falls with the release even while the note is held. On release, all fall with the release. **The release is one for all and longer the harder the note**; the algorithm shortens or lengthens it per operator.
- **Noise:** white, with the envelope of the operator the algorithm names (1, except the snare's), added after the FM, in any algorithm.
- **Clear + knob** = its initial value; **Clear + pad 7** = all of them.
- **Saved with the own-synth patches** (with the engine on FM); a patch from before loads it off. No CC / NRPN. Another engine of the row (or Shift + pad 27) turns it off.

| # | Algorithm | Family |
|---|---|---|
| 1 | 4 → 3 → 2 → 1 (stack) | classic (white) |
| 2 | 3 and 4 → 2 → 1 | |
| 3 | 4 → 1 and 3 → 2 → 1 | |
| 4 | 4 → 3 → 1 and 2 → 1 | |
| 5 | two stacks: 4 → 3 and 2 → 1 (carriers 1 and 3) | |
| 6 | 4 → 1, 2 and 3 (three carriers) | |
| 7 | 4 → 3; 2 and 1 alone (three carriers) | |
| 8 | organ: all four carriers | |
| 9 | kick: 2 → 1; operator 4 is the pitch drop (its level = how far, up to 3 octaves; its release = how long) | percussive (red) |
| 10 | snare: 2 → 1 + noise with operator 3's envelope; pitch drop from 4 | |
| 11 | metal / hi-hat: 2, 3 and 4 → 1 with inharmonic ratios (× 1.41, 2.71, 3.49) | |
| 12 | tom / zap: 3 → 2 → 1; pitch drop from 4 | |
| 13 | bell: 2 → 1 and 4 → 3, inharmonic ratios (× 3.5, × 2.76) | bells (teal) |
| 14 | tubular bell: 2 and 3 → 1 (× 2.76, × 5.4), 4 a carrier | |
| 15 | strings: two stacks (2 → 1, 4 → 3) detuned against each other | strings (green) |
| 16 | ensemble: 4 → 1, 2 and 3, three detuned carriers | |

<a id="midi-cc"></a>
### 3.5 CC editor of the MIDI macros (pad 25)

*How to get there:* MIDI 1 / 2 Preset view, **pad 25**: change on the device which CC / NRPN each macro knob of the template sends.

**In this view**

- **Control other gear** — pick the CC (or NRPN) number and the range of each knob of the template, and save it there.

1. **Pad 25** (lights). 2. **Move a knob**: it is picked and its number is drawn on the pads.
3. **Octave ▼ / ▲**: next / previous field. 4. **Turn the knob** to change the value.
5. **Save:** pad 26, or Octave ▼ up to the save step (pad 26 and Save blink) and Octave ▼ again.
6. **Discard:** any view button, pad 25 or a template pad.

| Number in the first field | Type | Fields |
|---|---|---|
| any other | CC | number, start, end |
| 99, 98 or 6 | 7-bit NRPN | number, MSB, LSB, start, end |
| 38 | 14-bit NRPN | number, MSB, LSB, start (MSB, LSB), end (MSB, LSB) |

<a id="step-drummer"></a>
### 3.6 Step-drummer view

*How to get there:* MIDI 1 / 2: Preset view with the engine on, **pad 30**. Synth 1 / 2: source view, **pad 30**. Sequencing by step pairs over the pattern.

**In this view**

- **Parameters by pairs of steps** — the 8 knobs are 8 pairs of steps of the pattern: each one moves a destination (pitch, shape, FM, filter…) on those steps only, for melodies, accents or timbre changes without drawing automation.
- **The LED tells how much** *(since RC2)* — dim with no modulation, brighter the further it goes.
- **A second page with its own destination** *(since RC2)* — the velocity page moves another destination at the same time.
- **Pitch-vel toggle** *(since RC2)* — page 1 transposes the notes in degrees of the scale and page 2 sets their velocity: a melody from a single pattern of notes.
- **In real time** — with Record, touching a step records it.
- **FX sequencer** — with that engine, each pair picks which Master FX slot sounds.

| Control | Function |
|---|---|
| Pads 1-16 | The 16 steps of the half shown: bright = has a note, white = playing. Touch = listen; **Shift + touch** = set / clear the note. |
| Pads 17-24 | Pitch page: destination of the pitch row (MIDI: pitch, OSC 2, WAVE, FM, MIX, env → filter, SHAPE, decay) / macro 1-8 (synths). Velocity page: **page 2's destination** *(since RC2)* (the same pad again = none). |
| Pad 32 | **Pitch-vel toggle** *(since RC2)* (bright green = on): on top of their destinations, the pitch page transposes the notes and the velocity page sets the velocity. |
| K1-K8 | The 8 step pairs (the playing one, white). |
| Octave ▲ / ▼ | Pitch / velocity page. |
| 1-16 / 17-32 | The other half of the pattern. |

- The pair's value offsets the destination from the centre (64 = no change): it adds to or takes from the value the parameter has on the engine's page. *(since RC2)* **The knob LED shows the amount**: dim at the centre, brighter the further it goes, up or down.
- Every step keeps the pitch of its first note.
- *(since RC2)* **Velocity page with a destination:** the knobs write their value into the pair (MIDI: from the centre, 64; synths: from 0), without touching the velocity while the toggle is off. With no destination and no toggle the velocity page does nothing. On MIDI, page 2 uses REL's automation lane: with the step-drummer on, REL is neither played nor recorded.
- *(since RC2)* **Pitch-vel toggle:** every note of the track moves up / down **one degree of the project's scale** (stock or custom) **every 8 knob steps**: MIDI from the centre (−8 … +8 degrees), synths from 0 (0 … +16), within notes 0-127; auditioning a step too. With the toggle, the pitch page's pitch destinations (pitch of both oscillators / of OSC 2) no longer move the own synth: the note does. The velocity follows the velocity page.
- *(since RC2)* On MIDI, pad 30 shows **dim** with the step-drummer off and **bright** when it is on (it was dark / dim).
- With **Record**, touching a step records it on the playing step (real time).
- With the engine on **FX sequencer** (blue), each knob picks a slot of Master FX's bottom row: 0 none, 1-5 pads 26-30, 6 pad 31, and at the end **random** *(since RC2)* (white LED: one at random among the slots with an effect). It moves slowly (one slot every ~48 steps of turning). A slot with no effect assigned does nothing.

<a id="midi-muestra"></a>
### 3.7 Sample mode and sample picker

*How to get there:* *(since RC2)* MIDI 1 / 2 with the engine on **sample** (pad 27 cyan, after the granular): **Note twice** (expanded Note view). The track plays a pack sample one-shot, at the pitch of each note.

**In this view**

- **Pitched drums on a MIDI track** — any pack sample plays at the pitch of each note, like a drum machine with tunable samples.
- **A different sample per step** — the sample flip changes sample step by step with no other track; it can be recorded live too.

| Control | Function |
|---|---|
| Pads 17-32 | 16 samples of the pack: touch = the track's sample (cyan) and it sounds; the others dim. |
| Octave ▼ / ▲ | Next / previous page of samples (4 pages = the pack's 64; lit when there are more that way). |
| Pads 1-16 | The 16 steps of the half shown: peach = with a sample flip, dim cyan (the background) = without, white = the one playing. **Hold a step + touch a sample** = its flip (the step green, its sample yellow); also **hold a sample + touch steps** (since RC2.04); **Clear + step** = remove it. |
| 1-16 / 17-32 | The other half of the pattern. |

- **The pitch:** C3 (note 60) = the sample as recorded; an octave up = twice as fast. The notes come from the normal Note view, the step-drummer or incoming MIDI.
- **One-shot:** the VCA stays open and the sample plays to its end; every new note restarts it (one voice per track). The filter, effect and LFO of the engine pages still work.
- **Live:** with **Record + Play**, touching a sample records a note 60 on the step playing, with its flip.
- The track's sample is the same source as the granular's (Shift + K8 on its page; the capture is picked there).
- The flips live in the track's level automation lane (Mixer): a flip replaces the level recorded on its step; recording the level over it erases those flips.

## 4. Pattern Settings

<a id="pattern-settings"></a>
### 4.1 Pattern Settings view

*How to get there:* The **Pattern Settings** button with a track selected: first / last step, sync rate and direction as always, plus pads 25-28 and the arpeggiator (Shift).

**In this view**

- **Nudge** — rotates the pattern so that it starts on another step.
- **Fractal and deconstructed orders** — walk through the pattern another way without changing its notes.
- **Arpeggiator** *(since RC2)* — the pattern's chords (and the ones you play) sound note by note, in their order and resolution; on the drums, jumping from sample to sample.
- **Dynamics and random-mutate** (pad 25) — variations so that the pattern does not always sound the same.

| Pad | Function |
|---|---|
| 1-16 | First / last step (stock). |
| 17-24 | Sync rate (stock). |
| 25 | Opens the probability view in **mode 2** (dynamics and random-mutate; on the drums too *(since RC2)*). **Clear + pad 25** (note tracks): clears the dynamics and the random-mutate of every step of the pattern; the frequency stays *(since RC2)*. |
| 26 | **Nudge** (orange): the chosen first step becomes step 1; what was in front goes to the end (steps and automation, over 16 or 32). |
| 27 | **Fractal** order: 1 · 1 2 · 1 2 3 · … up to the last step. |
| 28 | **Deconstructed** order: the grid's diagonals (1 6 11 16 · 2 7 12 13 · 3 8 9 14 · 4 5 10 15). |
| 29-32 | Stock direction; exclusive with 27 / 28. |

- Nudge and orders also on the drums. The order is saved with the pattern; Clear on the pattern removes it. *(since RC2)*

### Arpeggiator (note tracks) *(since RC2)*
While **Shift** is held, the arpeggiator's pads keep their Pattern Settings colours and the chosen ones show green:

| Gesture | Function |
|---|---|
| **Shift + pad 25** | The arpeggiator of the pattern the track plays: on / off. Without Shift, pad 25 shows green while it is on (and still opens mode 2). |
| **Shift + pads 27-32** | The arpeggio's order, independent of the pattern's direction: fractal, deconstructed, up, down, ping-pong, random. |
| **Shift + pads 17-24** | The arpeggio's **resolution**, apart from the track's sync rate, in the same order as the sync rate pads (slower to the left): 1/4, 1/4T, 1/8, 1/8T, 1/16, 1/16T, 1/32, 1/32T. The same pad again = the track's (no pad green). |

- **Sequence:** when two or more notes start on a step, they play one at a time (at the arpeggio's resolution), in the chosen order over the notes sorted by pitch, for as long as the chord's longest note. Each note lasts **its own gate, at most one arpeggio step** (and what is left of the chord) and keeps its velocity: a chord recorded by holding its notes plays arpeggiated, one entered with short notes, staccato.
- **Input:** the first note sounds as always; holding another one with it starts the arpeggio of the held notes, one an arpeggio step (with the transport stopped, at the project's tempo), until all are let go; each note lasts an arpeggio step. **With Record the chord is recorded**, not the single notes: the sequence plays the arpeggio afterwards.
- **Pressed order** *(Beta 3.22 only)*: the notes are arpeggiated in the order they were pressed (a recorded chord, in the order of its notes in the step), not by pitch; up, down, ping-pong, random, fractal and deconstructed walk that order. A note let go leaves its place empty and skipped; the next note you press takes the first empty place before going to the end.
- **Random-mutate** *(Beta 3.22 only)*: when the chord's step has a random-mutate level, each note of the arpeggio goes through it (another degree of the scale, an octave up or down) as normal notes do; nothing is written into the step. The live arpeggio (the notes held) uses the level of the step the track is on (playing, the one that plays; stopped, where it stopped).
- **Long notes when recording** (since RC2.04): the stock's recorder cuts notes at 16 steps; now a note or chord held longer goes on, tied, 16 steps later (in patterns longer than 16 steps), so the arpeggio of a held chord does not stop at step 16. For every note of Synth 1 / 2 and MIDI 1 / 2, with or without the arpeggiator.
- Saved with the project, per track and pattern.

### The drums' arpeggiator *(since RC2)*
The same gestures (**Shift + pad 25 / 27-32 / 17-24**) in a drum's Pattern Settings turn its arpeggiator on for the pattern it plays, with its order and resolution. In the **drum's Preset view** the first sample held is the usual one; **holding another one with it starts the arpeggio of the samples held**: the drum jumps from sample to sample (in the chosen order, over the samples sorted by number), with its pad's velocity. Playing, it follows the drum's grid; stopped, the project's tempo. It goes on while any is held; when all are let go, the drum goes back to its chosen sample. **With Record** (playing) every hit is recorded into the pattern: its micro step, its sample as the step's sample flip (one a step: the last one stays) and, on an empty step, its velocity.

<a id="micropasos"></a>
### 4.2 Micro Step view (note tracks)

*How to get there:* Press **Gate twice** with a note track selected (Synth 1 / 2, MIDI 1 / 2).

**In this view**

- **Micro steps and Tie (stock)** — place each note off the grid and tie it to the next step.
- **Gate by holding** *(since RC2)* — when entering notes by hand, how long you hold is how long the note lasts.
- **Fixed length** *(since RC2)* — every note you enter by hand gets the same length.

- **The stock part:** pads 17-22 = the 6 micro steps of the chosen step; **pad 24 = Tie** (a toggle: ties the chosen notes to the next step); pads 25-30 = the step's notes: touching one chooses it (the micro step and the Tie apply to it) and plays it.
- **One micro step per note (stock):** each note stores a single position, so touching another micro step moves the chosen note; two cannot be lit at once. For several in the same step, enter several notes. Drums can light several micro steps (repeats).
- **Gate once** is the Gate view (pads 17-32 = the length): there pads 31 / 32 are the stock's.
- **Pad 32 = gate by holding** *(since RC2)* for the track (green = on, dim = off; saved with the project): when **entering notes by hand** (a step held + a note pad, or a note held + a step pad), **how long you hold the pad is the note's gate**, at the project's tempo and the track's sync rate (1 micro step to 16 steps). It ends when the first of the two pads is let go. Off: the stock's gate.
- **Pad 31 = fixed length** *(since RC2)* for the track (orange = on): with both off, it opens the **selector** (pads 17-32 = 1 … 16 steps, like the Gate view) and **picking a length turns it on** (and closes the selector). With it, every note entered by hand (not one recorded live) gets that gate, all of a chord's notes too, whichever pad you let go first (since RC2.08: before, only when the note pad was let go first).
- **The two toggles** *(since RC2)*: with one on, **pressing it again turns it off** (nothing opens); **pressing the other one** turns the first off and the new one on (pad 31 by opening its selector).
- The arpeggiator uses those gates too: each note of the chord lasts its own.

<a id="probabilidad"></a>
### 4.3 Probability view (note tracks and drums)

*How to get there:* **Shift + Pattern Settings** (stock mode), **Pattern Settings twice** (mode 1) or **pad 25** of Pattern Settings (mode 2). Hold a step with notes and touch a pad of rows 3-4.

**In this view**

- **Probability (stock)** — a step that only plays sometimes.
- **Frequency** *(since RC2)* — a step that plays once every n passes: variations that come back every 2, 4 or 8 passes.
- **Dynamics** *(since RC2)* — small changes of velocity and position: a more human pattern.
- **Random-mutate** *(since RC2)* — notes that jump an octave or to another note of the scale; on the drums, to another sample.

| Mode | Row 3 | Row 4 |
|---|---|---|
| Stock (Shift + Pattern Settings) | Step probability | **Random-mutate** *(since RC2)* |
| Mode 1 (Pattern Settings twice) | Step probability | **Frequency**: the step plays on the last of every n passes (1-8), yellow *(since RC2)* |
| Mode 2 (pad 25) | Random **dynamics** *(since RC2)* | Random-mutate *(since RC2)* |

### Random-mutate (row 4)
| Pad | 25 | 26 | 27 | 28 | 29 | 30 | 31 | 32 |
|---|---|---|---|---|---|---|---|---|
| Octave | — | 6 % | — | 6 % | — | 12 % | — | 25 % |
| Scale | — | — | 6 % | 6 % | 12 % | — | 25 % | 50 % |

- Scale = another note of the scale in the same octave; octave = one up or down. Each note of a chord is drawn separately. Without Record it changes only that time; with Record it is written (the sequence drifts). Tied notes do not change.

### Dynamics (row 3, mode 2)
| Pad | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Micro steps | — | ±2 | ±2 | — | −1 to +3 | −1 to +3 | — | — |
| Velocity | — | — | 0 to +32 | 0 to +32 | 0 to +32 | — | ±32 | −32 to +64 |

- With Record and mode 2 on screen, what plays (mutated note, dynamics) is written into the pattern. Everything is saved with the step.

### On the drums *(since RC2)*
The same view for a drum: **Pattern Settings twice** (mode 1) or **pad 25** of its Pattern Settings (mode 2, peach; green when its arpeggiator is on). Pick a step with a hit (pads 1-16) and touch a pad of rows 3-4.

| Mode | Row 3 | Row 4 |
|---|---|---|
| Mode 1 | Step probability (stock) | **Frequency** (1-8), yellow |
| Mode 2 | **Dynamics** (the same 8 levels) | Pads 25-28: **random-mutate of the sample** |

| Pad | 25 | 26 | 27 | 28 |
|---|---|---|---|---|
| Random-mutate | — | 25 % ±1 (the next sample in its row of 8) | 25 % ±8 (the same column in another row) | 12 % of each |

- The dynamics only delay the hit inside its step (a drum cannot play earlier). The mutate starts from the step's sample flip, or the chosen sample; it is not recorded.
- The values live in bytes of the pattern the stock does not use (they travel when it is duplicated and with Nudge); the first one set clears those bytes in the project's 32 drum patterns (a factory pack keeps garbage there).

## 5. Drums

<a id="drum-pista"></a>
### 5.1 Drum track view (knobs)

*How to get there:* Press **Drum 1-4**. Every knob does what its label says, with a second layer on Shift.

**In this view**

- **Shape each drum** — exact pitch, ring mod, attack and decay, sample start and cut, a filter with several modes, LFO and several kinds of distortion: many sounds from one sample.
- **All neutral = the original** — with the new knobs at their neutral point, the sample sounds as on the original Circuit.
- **Start over** *(since RC2)* — Clear + the drum's button puts all its knobs back to their defaults.

| Knob | Alone | With Shift |
|---|---|---|
| K1 Oscillator | Pitch (*(since RC2)*: the stock one, continuous as on the original; the chromatic view's pads transpose on top) | Pitch envelope amount |
| K2 Osc mod | Ring mod frequency | Ring mod amount |
| K3 Amp envelope | **Left: decay** (the stock one). Past its maximum, **right: attack** (fade-in, up to 1 s). Neutral in the middle. *(since RC2)* | **Left: sample start**; **right: cut** from the end (up to 120/128 each; *since RC2.09* the start covers the whole sample: before, it reached the end at a quarter of the travel and beyond that the hit was silent). Middle = the whole sample. *(since RC2)* |
| K4 Filter envelope | Envelope → cutoff | Envelope shape |
| K5 Filter frequency | Filter / EQ (by default the stock tilt EQ) | **Filter mode**: stock tilt EQ, band-pass, notch, comb, DJ |
| K6 Resonance | Resonance | — |
| K7 Modulation | LFO amount: right = tremolo; left = vibrato (*(Beta 3.22 only)*: left = **start scan**: each hit starts where the LFO is, from the Shift + K3 start up to a 64th of the sample further for every step of the knob (fully left, the whole sample), never past the cut; the LFO no longer restarts with each hit) | LFO speed (bipolar *(Beta 3.22 only)*: right free, left synced; 0.2; synced, the scan is at the start on the first beat) |
| K8 FX | Distortion; left of 0, **bitcrush** | **Distortion type**: stock, soft, hard, fold |

- **K3:** turning left, the attack goes back to 0 before the decay goes down; with Shift, one of the two (start or cut) goes back to 0 before the other moves. LED: attack in white; with Shift, start in the drum's colour, cut in white.
- **Clear + K3 to the right** puts attack, start and cut to 0; **Clear + K8 to the right** removes the bitcrush too *(since RC2)*. Clear + knob resets both layers on the others.
- **Clear + the drum's button** *(since RC2)* (with one of its views on screen): the drum's eight knobs, with their Shift layer, back to their defaults.
- All neutral, a sample sounds as on the original. Everything is saved with the project and has an NRPN.
- **Sidechain between drums:** Shift + FX and Octave ▼ (8.1).

<a id="drum-preset"></a>
### 5.2 Drum Preset view

*How to get there:* Press **Preset** with a drum selected. The pads pick the sample as always (Shift + pad = pick without sound).

**In this view**

- **The capture as a drum** — record what is playing (Master FX) and use it as a drum's sample; saving the project puts it in the pack.
- **Swap and copy samples** — reorder the samples or bring one from another pack.
- **Sample arpeggio** *(since RC2)* — holding several samples makes the drum jump from one to the next.

| Gesture | What it does |
|---|---|
| **Clear + pad**, **Clear + the same pad** | **Replaces** that sample with Master FX's capture. Volatile until you save: then it is written into the pack if it fits in the sample memory. |
| **Duplicate + pad A + pad B** (same pack) | Swaps the two samples (files and table); sounds at once. |
| **Preset again** *(since RC2)* | The drum's chromatic / scale view on / off (the same as Shift + Preset). |
| **Several pads held** *(since RC2)* | With the drum's arpeggiator on (Pattern Settings, Shift + pad 25): the arpeggio of the samples held (Pattern Settings chapter). |
| **Duplicate + pad A**, load another pack, **Duplicate + pad B** | Copies sample A over B (B may be empty). It goes into B's place if it fits; otherwise into the free import memory. It never overwrites a sample that plays. |
| **Shift + Preset** | Chromatic / scale view (5.3). |

- Duplicate lights in this view. Writes to the card: not in the «S» versions nor in the internal memory's pack.

<a id="drum-cromatica"></a>
### 5.3 Chromatic and scale view of the drums

*How to get there:* **Shift + Preset** with a drum selected. The pads play the sample transposed along the scale.

**In this view**

- **A drum as a keyboard** — the sample transposed in the project's scale.
- **Rollers** *(since RC2)* — repeat the drum on the micro steps you hold: rolls and ratchets live, stopped too, and recorded with Record.

- Three rows of notes in the scale and root of the Scales view.
- **K1** = pitch offset in semitones; **Shift + K1** = fine tuning in cents.
- While recording, each pitch is recorded on its own step only. *(since RC2)*: the pads transpose in semitones on top of K1's pitch and, while recording, stay on their step inside the drum's pitch lane (a step holds a K1 turn or a chromatic note); Clear + K1 to the left (held) deletes both.
- **The drums' Note view:** pads 25-28 repeat the boxes of drums 4 … 1.
- **Micro-step rollers** *(since RC2)* on rows 1-3 of the drums' Note view: each column is the drum of its box below (columns 1-4 = drums 4-1, columns 5-8 = drums 1-4), dim in its colour. A drum's left column is its micro steps 1-3 (rows 1-3) and the right one 4-6: drum 1 = pads 4, 12, 20 and 5, 13, 21. **While held** (one or several, of one or several drums), the drum plays on **every step** at those micro steps (with the step's velocity, or 100 on an empty step); they light up while held. **With the transport stopped** *(since RC2)* too: at the project's tempo, starting when the first one is pressed (velocity 100). **With Record** their hits are recorded into the pattern too (the micro step, and velocity 100 on an empty step).

## 6. Master FX

<a id="master-fx"></a>
### 6.1 Master FX

*How to get there:* **Mixer**, then **Mixer** again. Effects on the master output, the song pointer, the captured sample and the row of assignable effects. Any other view button leaves.

**In this view**

- **Live effects on the whole master** — Gater, Auto-Filter, Digitise, Phaser, Glitch and the mechanical gesture *(since RC2)*: while held or latched.
- **Song pointer** — repeats or loops parts of the pattern live.
- **Capture** — records up to 3.5 s of what is playing, to play it, put it in a slot or use it as a drum.
- **Slots** — an effect with its settings one touch away; the FX sequencer triggers them.
- **Per project** *(since RC2)* — each project remembers its Master FX settings.

### Pads
| Pad | Function | K1-K4 when pressed |
|---|---|---|
| 1 | Gater | division, depth, width, smoothing |
| 2 / 3 | Auto-Filter low / high pass | speed (bipolar *(Beta 3.22 only)*: right free, left synced), depth, resonance, centre |
| 4 | Digitise | sample rate, bits; **K3 = momentary delay throw** while you hold the pad, **K4 = envelope of the amount** *(since RC2)* |
| 5 | Phaser | speed (bipolar *(Beta 3.22 only)*: right free, left synced), depth, feedback, mix |
| 6 | **Glitch** *(since RC2)* (in RC0.9, the Vinyl) | Glitch: speed, repeat, delay, chaos / overload |
| 7 | **Captured sample**: play | pitch, mode (one-shot / gate / loop), start, end |
| 8 | Release everything latched (effects, song pointer, sample) and bypass | — |
| 9-24 | **Song pointer**: steps 1-16 | — |
| 25 | (stock) | — |
| 26-30 | **Assignable slots** | the assigned effect's |
| 31 | **Mechanical gesture** *(since RC2)* (in RC0.9, the Glitch) | gesture: moves, kind, stop time, start time |
| 32 | **Record** the capture | — |

### Effects (pads 1-6)
- **Hold** = on; **Shift + pad** = latched; touching it again releases it. The knob LEDs show the value with their brightness.
- **Clear + knob to the right** = default; while Clear is held the knobs at their default show lavender (Master FX has no automation: no red).
- **Per session** *(since RC2)*: the effects' 20 knobs, the slot assignments and the compressor are saved with each project.

### Song pointer (pads 9-24)
- **One step held** = retrigger; **two** = momentary phrase between them; **Shift + two** = latched phrase (pad 9 white; touching it removes it).
- **Phrase mode:** Shift + step = start (end 16); a touch = the end; Shift + another = new start; Shift + the start or pad 9 = leave.

### Captured sample (pads 7 and 32)
- **Pad 32:** hold = records while held (up to 3.46 s); short tap = until the next; **Shift + pad 32** = armed (records the next bar; stopped, from Play). The capture records the output without Master FX's effects; the playing sample goes through them. **Since RC2.01** the capture and the sample sit before the master filter: the filter acts on the sample as it plays and the capture does not hold it.
- **Pad 7:** play; **Shift + pad 7** = latched loop until pressed again. Loop mode (K2 blue) sounds only while held.
- It can be assigned to a slot (pad 7 + a pad below) and replace a drum (drum Preset view). When the project is saved it goes into the pack if it fits.

### Bottom row (pads 26-31)
- **Assign:** hold an effect on top (1-6), pad 7 or pad 31 and touch a slot: it stores the effect with a copy of its parameters.
- **Touch the slot** = on while held; **Shift + slot** = latched. The FX sequencer triggers these slots.

### Glitch and mechanical gesture
- **Glitch:** the output becomes a tape head over the recent audio: K1 speed (top normal, middle stopped, bottom backwards), K2 repeat, K3 delay (up to 2.6 s), K4 chaos (lower half) or overload (upper half).
- **Mechanical gesture** *(since RC2)*: pressing it slows the audio to a stop; releasing restarts it. K1 moves (1-8), K2 continuous kind in colours (tape stop → baby scratch → tear → back spin → rattle), K3 stop time, K4 start time. It uses the Glitch's engine: while it plays, the Glitch waits.

## 7. FX

<a id="vista-fx"></a>
### 7.1 FX view

*How to get there:* The **FX** button: reverb and delay sends per track, as always, plus:

**In this view**

- **The reverb and delay from the unit** — type, decay, time, feedback…, saved with the project.
- **Quick reset** — Duplicate puts the sends and the effects back to zero.
- **Master filter resonance** — on Shift + Octave ▲ / ▼, in steps of 16 *(Beta 3.22 only; in RC2.09, 1-16 / 17-32)*.
- **Master filter off / on** — Shift + pad 25, keeping its position *(Beta 3.22 only)*.

| Gesture | What it does |
|---|---|
| **Octave ▲ / ▼** | The knobs = delay / reverb sends. |
| **Shift + knob** | Global parameters: reverb K1 type, K2 decay, K3 damping; delay K1 time, K2 sync, K3 feedback, K4 width, K5 ratio, K6 slew. Saved with the project. |
| **Duplicate** | Reset: sends to 0, master filter centred, Master FX off. |
| **Shift + Octave ▲ / ▼** *(Beta 3.22 only)* | Master filter resonance +16 / −16; stops at 127 / 0 (with Shift, Octave lights yellow). In RC2.09: **1-16 / 17-32** (green LED). |
| **Shift + pad 25** *(Beta 3.22 only)* | Master filter off / on: while off, it sounds as with the filter at the centre even if you move its knob (the knob still changes its position); again, the filter comes back at the knob's current position. While off, the filter knob's LED is red; with Shift, pad 25 lights yellow (red while off). Without Shift, pad 25 is the stock one. |
| Bottom row | The same as in Master FX: slots (26-30), mechanical gesture (31), record (32). |

- If Setup routes the returns through strips 3 / 4, their sends are capped at half.

## 8. Sidechain

<a id="sidechain"></a>
### 8.1 Sidechain view

*How to get there:* **Shift + FX**. Each track's sidechain presets as always, plus the knobs:

**In this view**

- **Sidechain with knobs** *(since RC2)* — attack, hold, decay and depth of each track's ducking, beyond the presets.
- **Master compressor** *(since RC2)* — its attack and release.
- **Sidechain between drums** — one drum ducks another (the kick ducking the bass, for example).
- **Triggered by patterns** *(since RC2)* — Synth 1 / 2 or MIDI 1 / 2 as the source: their pattern notes duck another track, not only the drums.

| Control | What it does |
|---|---|
| **K1-K4** *(since RC2)* | Attack, hold, decay and depth of the sidechain of the track of the last preset touched (Synth 1 if none); LEDs in the track's colour. |
| **K7 / K8** *(since RC2)* | Attack / release of the master compressor (switched on in Advanced Setup), white. Saved with the project. |
| **Row 1 pads 1-4** *(since RC2)* | **Synth 1, Synth 2, MIDI 1, MIDI 2 as the source** of the chosen track's side-chain (the last preset touched), next to drums 1-4 on pads 5-8: every **pattern** note of that track fires the envelope, as a drum hit does (notes played live do not). The chosen one in the track's colour, the others dim. A pad 5-8 goes back to a drum. Saved with the project. |
| **Octave ▼** with the drums | **Sidechain between drums**: ducking pages per drum (rows 3-4) and which drum triggers (row 1, pads 5-8). |
| **Row 1 pads 1-4** on a drum page *(since RC2)* | **Synth 1, Synth 2, MIDI 1, MIDI 2 as the trigger** of the drum whose preset was touched last: every **pattern** note of that track opens its envelope (notes played live do not). The chosen one in the drum's colour; the others dim. A pad 5-8 goes back to a drum. Like the presets of the side-chain between drums, it is not saved. |
| **K1-K4** on a drum page *(since RC2)* | Attack, hold, decay and depth of the sidechain of the drum of the last preset touched (starting from its preset's; touching a preset brings them back to it); LEDs in the drum's colour. Saved with the project. |

## 9. Scenes and patterns

<a id="patterns"></a>
### 9.1 Patterns view and pattern chains

*How to get there:* The **Patterns** button. Columns = tracks, rows = patterns. With the **chain mode** *(since RC2)*, each pattern can carry a rule «play n times, jump to B; next time, to C».

**In this view**

- **Pattern chains** *(since RC2)* — a pattern plays n times and jumps to another, and the next time to a third: A A A B structures without chaining by hand.

| Gesture | What it does |
|---|---|
| **Shift + Octave ▲** | Turns the whole project's chain mode on (Octave ▲ green). With Shift, the useful Octave lights yellow. |
| **Shift + Octave ▼** | Turns it off (the rules stay saved but are not applied). |
| In the mode: **a pattern** | **A** (yellow); A again = one more repeat (up to 8, the knob LEDs count them). |
| In the mode: **another pattern of the track** | **B** (green); the next one = **C** (red). |
| **Clear + pattern** | In the mode: removes the rule (without a rule, clears the pattern). Outside: clears the pattern, its rule and its order. |

- Examples: n = 3 → A A A B A A A C; no C → A A A B; n = 1 → A B A C. B and C play once and the track goes back to A (unless they have a rule).
- Rules travel with the pattern (when duplicated); the mode, with the project and with each scene (9.2).

<a id="mixer"></a>
### 9.2 Mixer view and scenes

*How to get there:* The **Mixer** button: levels (Octave ▲) and pan (Octave ▼) as always; **Mixer again** = Master FX.

**In this view**

- **Level to 100 or 0** — Shift + knob puts a track at its nominal level or silent in one move.
- **Scenes with chains and repeats** *(since RC2)* — a scene can repeat n times and remember chain mode.
- **Drop-ins on the bar** *(since RC2)* — Shift + a track pad mutes or unmutes the track right as the next bar starts.
- **Cue mode** *(since RC2)* — the mix in mono on the left and, on the right, the tracks you want to hear before bringing them in.

| Gesture | What it does |
|---|---|
| **Shift + knob to the right / left** | That track's level to 100 / to 0 (levels page; on the pan page, *(since RC2)*: the cue mode). Goes out over MIDI and is recorded like a turn. |
| **Pan page: Shift + knob to the right / left** *(since RC2)* | **Cue mode** on / off (Octave ▼ pink / white; stored in the unit). |
| **Cue mode: a pan knob** *(since RC2)* | That track's send to the **cue** (right output), from the centre to the right (to the left nothing); Clear + knob = no cue. The knobs pink, brighter with more send. |
| **Scene pads** | As always; a scene saved in **chain mode** shows **peach** and loading it brings the mode back; a normal one turns it off. *(since RC2)* |
| **Shift + pads 1-8** *(since RC2)* | **Mute / unmute that track on the next bar**: the pad blinks while it waits; again cancels it. Stopped, at once. |
| **Shift + pads 9-16** | **Repeats** of the current scene (1-8; with Shift the row is yellow, the chosen one green). *(since RC2)* While playing, with Shift, **the repeat now playing is white** (pad 9 = the first time; on the last one the green pad blinks white / green). *(Beta 3.22 only)* |
| Blinking tracks | They are following a chain rule. *(since RC2)* |
| **Mixer** again | Master FX. |

- A scene ends when its longest chain ends. Saving a scene again does not change its repeats.
- **Cue mode** *(since RC2)*: the **left output** carries the mix in mono as always and the **right** one only the cued tracks, each at its send. A muted track in the cue plays only on the right, at the step its pattern is on; its pad stays dim and its pad (or Shift + pad, on the next bar) takes it into or out of the mix. The pans are not touched and come back when the mode goes off; saving the project saves the mix's mutes. Reverb, delay and Master FX are the mix's: the cue hears them too.

## 10. Projects and packs

<a id="projects"></a>
### 10.1 Projects view

*How to get there:* The **Projects** button: loading and saving projects as always, plus copying.

**In this view**

- **Copy projects** *(since RC2)* — duplicates a project into another slot or another pack.

- **Duplicate + pad A** (a project) = the source (yellow, blinks); Duplicate + A again forgets it.
- **Duplicate + pad B** = copy. B empty: written at once; B in use: it blinks white and Duplicate + B must be repeated within ~5 s. Never the loaded project. *(since RC2)*
- **To another pack:** pick the source, load the other pack, go back to Projects and Duplicate + B.
- The project saved on the card is copied; while copying the device does not respond for a moment. In another pack it plays with that pack's patches and samples *(writes to the card)*.

<a id="packs"></a>
### 10.2 Packs view

*How to get there:* **Shift + Projects**. Loading packs as always, plus deleting.

**In this view**

- **Delete packs** — frees pack slots from the unit.
- **Protected internal memory** — the mod never writes to the internal pack.

1. Touch **Clear** (no Shift): for ~5 s the packs that can be deleted blink (never the loaded one). Clear lights steady white in this view.
2. Touch the pack: only that one blinks; it is not loaded.
3. **Clear** again within 5 s: deleted. The slot can be reused after a restart.

- **The internal memory's pack** (the first one) is read-only for the mod: it cannot be deleted and nothing of the mod is written into it (copies, patches, captures); the Save LED turns red for 1.5 s. It can be read and copied from to a pack on the card *(writes to the card)*.

## A. Appendix

<a id="guardado"></a>
### A.1 What is saved and where

*How to get there:* Project, pattern, pack or device settings.

| What | Where |
|---|---|
| New drum knobs (attack, start and cut included), synth source, reverb / delay, Master FX slots and knobs, compressor, chain mode and scenes, count-in, arpeggiator (with its resolution), custom scale, gate by holding, the own synth's gate retrigger and LFO shape *(since RC2)* | The project |
| Step-drummer notes, FX sequencer values, random-mutate, frequency, dynamics, chain rules, play order, the sample mode's sample flips *(since RC2)* | The pattern |
| Saved synth patches, own-synth patches (with their mod matrix *(since RC2.02)*), captures used as samples | The pack *(writes to the card)* |
| MIDI track engine (state and values; *(since RC2)*: also OSC 2, the Shift knobs of the granular and the oscillator and pads 28 / 29), MIDI Thru mode, PGM channels, *(Beta 3.22 only)* the drums' GM mode and its notes | Device settings |
| *(Beta 3.22 only)* **The whole MIDI 1 / 2 own synth** (engine, values, matrix, page 4, FM): saving the project takes it along and loading it brings it back (an older project does not carry it: the sound stays as it was) | The project (in MIDI 1 / 2's patterns 1-5, without changing what they play) |
| Latched effects, song pointer, Setup's Record toggle, presets and triggers of the side-chain between drums, the mod matrix outside a patch *(since RC2.02)* (off at power-up; *(Beta 3.22 only)* it goes with the project) | Not saved |

<a id="midi"></a>
### A.2 MIDI of the new features

*How to get there:* Everything new goes out and comes in over CC / NRPN, following the Setup's CC Tx / Rx filters.

- **MIDI track engine** (the track's channel): Filter CC 74, Resonance 71, Env → filter 79, Attack 73, Decay 75, Sustain 70, Release 72, Effect 91, Gain 59, TUNE 26, FINE 27, WAVE 20, SHAPE 21, TUNE 2 37, FINE 2 39, WAVE 2 30, SHAPE 2 31, MIX 52, RING 54, LFO speed NRPN 0:76; the rest NRPN MSB 4 with LSB = code.
- **Drums** (the drums channel): NRPN MSB 5-8 = Drum 1-4; LSB 1 pitch env., 2 ring (frequency), 3 LFO, 4 LFO speed, 5 env → cutoff, 6 resonance, 7 envelope shape, 8 ring (amount), 9 filter mode, 10 start, 11 bitcrush, 12 distortion type, 13 cut, 14 attack. *(Beta 3.22 only)*: with the GM mode (Setup, K4) the notes of Drum 1-4 go out as the GM notes picked (K5-K8).
- **Master FX** (channel 16): NRPN MSB 9, LSB = 4 × effect + knob.
- Full tables: the MIDI reference (`docs/MIDI.en.md`).

<a id="instalar"></a>
### A.3 Installing and going back

*How to get there:* `tools/rc_uploader.html` patches the official firmware in the browser and sends it over Web MIDI.

1. Download Novation's official firmware 1.2.1, open `tools/rc_uploader.html` in Chrome and connect the Circuit Tracks over USB.
2. Pick the version (RC2.09, the safer RC2.09S, Beta 3.22 with the new untested features, or an earlier one) and send. Novation's bootloader is not touched.
3. **Back up the card first.** With the versions that do not end in «S», do not use the internal memory for projects.
- **Going back:** send another version or the official firmware. If it does not boot: **Scales + Preset + Note** at power-up.
