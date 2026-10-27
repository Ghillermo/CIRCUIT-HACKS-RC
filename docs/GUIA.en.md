# Guide by views — CIRCUIT-HACKS (RC2.10)

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

**11. Data: saving, MIDI and modulation**

- [11.1 What a pattern holds and how to make sure it is saved](#datos-patron)
- [11.2 What comes back after a restart and where it is saved](#guardado)
- [11.3 What is lost at a restart](#datos-perdido)
- [11.4 MIDI: own behaviours, new CCs and NRPNs](#midi)
- [11.5 Mod matrix and macro destinations](#destinos)

**A. Appendix**

- [A.1 Installing and going back](#instalar)

## 0. Introduction

<a id="convenciones"></a>
### 0.1 How to read this guide

*How to get there:* Each chapter is a view of the device: how to get there, what every pad, knob and button does, and the sub-menus it opens.

- **Pads 1-32** from top-left to bottom-right: row 1 = 1-8, row 2 = 9-16, row 3 = 17-24, row 4 = 25-32.
- **Knobs K1-K4** on top, **K5-K8** below. «**Shift + X**» = hold Shift while using X; the same with Clear and Duplicate.
- Anything not described here works as on the original device (Novation's official manual).
- *(since RC2)* = new since RC2 (not in RC0.9 / RC0.9S). The safer build, RC2.10S (and the earlier S builds), writes nothing of its own to the card: what is marked «writes to the card» does nothing there (the Save LED turns red).
- *(since RC2.02)* = new in RC2.02 (not in RC2.01).
- *(Beta 3.36 only)* = only in **Beta 3.36**, the test build with the new features (not in RC2.10).
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
- **LFO synced to the tempo** *(Beta 3.36 only)*: the **LFO rate** knobs (K7 of the VCA-VCF page of the MIDI 1 / 2 engine, Shift + K4 of the matrix, Shift + K7 of the drums, K1 of the Auto-Filter and of the Phaser in Master FX) are **bipolar**: at the centre the LED is dim; **to the right, a free LFO** (faster further right); **to the left, synced to the tempo**, from the centre outwards 1/16T, 1/16, 1/8T, 1/8, 1/4T, 1/4, 1/2T, 1/2, 1 bar T, 1 bar, 2T, 2, 4T, 4, 8T and 8 bars (4 clicks each), each cycle starting on the **bar's first beat** (it is put back in place on every sequencer tick; stopped, it keeps the tempo). In the matrix, each shape of Shift + K4 is a stretch with its own centre. What was saved before with another rate may sound different.

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
| **Record** *(since RC2)* | Yellow = what a MIDI track sends to a synth over the shared channel is also recorded into that synth (scale or octave changes in real time). Off by default; off again after a restart. *(Beta 3.36 only)*: while yellow, nothing is recorded into a note track muted in the Mixer: its steps sound and are recorded only into the synth on the shared channel (a chord bank). |
| **K4** *(Beta 3.36 only)* | **General MIDI** mode of the drums: to the right on (green), to the left off (dim): **turning it off closes the number** and the drums go out as on stock again. While on, every hit of Drum 1-4 goes out over MIDI with **its GM note** instead of the stock one (60 / 62 / 64 / 65), on the drums' channel (10 by default, the one you pick here). Inside the device it sounds the same. |
| **K5-K8** *(Beta 3.36 only)* | With the mode on, the GM note of Drum 1-4 (the knobs over the drum tracks; off, they do nothing): 35-81, two clicks a note; by default 36 kick, 38 snare, 42 closed hat, 46 open hat. **Every new note sounds** once on the drums' channel and **its number shows on the pads**, in the drum's colour; **Shift** or leaving Setup confirms it (saved in the settings) and the Setup pads come back. While the number shows, the Setup pads do nothing. LEDs: each drum's colour, brighter for a higher note (dark with the mode off). |

- Patch flip always goes out on its MIDI track's channel.

<a id="advanced-setup"></a>
### 1.2 Advanced Setup view

*How to get there:* Open it as on the original. Besides its stock settings (master compressor, etc.):

**In this view**

- **MIDI Thru, Merge and Filter** *(since RC2)* — the Thru jack can merge the incoming MIDI with the unit's own, or filter it.

- **Duplicate** = mode of the MIDI Thru jack *(since RC2)*: Thru (dim red, DIN In by hardware) → Out 2 (green) → **Merge** (yellow: DIN In + the device's MIDI) → **Filter** (blue: DIN In without the channels the device listens to). No SysEx in Merge / Filter. Saved in the settings.
- Pads 22 / 23 do not light here (they do nothing there).
- **Pad 23 = USB merge** *(Beta 3.36 only)*: what comes in on the **DIN In** (a keyboard on a MIDI cable) also goes out over **USB** to the computer, together with the device's own MIDI. Green on, dim off; saved in the settings. With Clock Tx on, the DIN In's clock and transport are not copied (the computer would get two clocks); SysEx is not copied; what comes in over USB is not sent on.
- **Pad 22 = external keyboard to the arpeggiator** *(Beta 3.36 only)*: the notes coming in over MIDI (DIN or USB) on the channel of Synth 1 / 2 or MIDI 1 / 2 go through its arpeggiator (when on in the pattern that plays) like the pads. Green on, dim off (the default); saved in the settings.
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
- *(Beta 3.36 only)* **hold a track button** (Synth 1 / 2, MIDI 1 / 2, Drum 1-4) with the split keyboard open: while you hold it, **the 8 knobs (and their lights) are that track's**; let go and they go back to the first one;
- any track button (*(Beta 3.36 only)* a short tap, no knob turned) or view button closes it (held notes are released); Play, Record, Octave and Shift do not.
- The macro knobs work as always; their destinations can be edited on the device (source view, pad 32).
- **Velocity view, Shift + a step pad** *(Beta 3.36 only)* (Synth 1 / 2 and MIDI 1 / 2): that step **lets go of the automation**: no lane plays there and the parameters the automation had moved go back to their knob's position (the one before the automation; turning the knob by hand changes it). Again = off. With Shift, in the Velocity view, the step pads are yellow and the marked ones red; on the 17-32 page, steps 17-32. Saved with the pattern.
- **Shift + a key = latch** *(Beta 3.36 only)* (Synth 1 / 2 and MIDI 1 / 2, Note and expanded Note view, no step held): the note sounds and **keeps sounding when you let go of the pad**; the **next press of that note** (on any pad that has it, with or without Shift) stops it, and that press does nothing else. With Shift the keys light **yellow** and the latched notes **green**. With the **arpeggiator** on, the latched notes stay in the arpeggio: an **arpeggio latch**. Not on the chord screen or the sample picker (Shift + pad already does something else there); not saved.
- **Chord screen** *(Beta 3.36 only)* (Synth 1 / 2 and MIDI 1 / 2, only in the **expanded Note view**: Note twice): **Shift + pad 8** turns it on and off (with Shift pad 8 is yellow, green with the screen on).

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
- **Jankó** *(Beta 3.36 only)*: in the editor, **Shift + pad 8** (top right; yellow with Shift) turns on the **isomorphic Jankó layout** (pad 8 cyan while on): on the note tracks every row goes up a **semitone** and every column a **whole tone**, and the bottom-left pad is the Scales view's **root**. Every chord type has the same shape in any key (in the expanded Note view, with four rows, every triad and seventh chord fits). All 12 notes are there: the notes that sound light on their pads and random-mutate picks any of the 12 of its octave. **Octave ▼ / ▲ = a semitone** (Shift + Octave still transposes the pattern an octave). Shift + pad 8 again, a key of the editor or a stock scale turn it off. Saved with the project.

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

- **A synth on each MIDI track** — MIDI 1 and 2 sound on the unit itself with their engine (processed line input, oscillator, two oscillators, VA-drum, granular, sample mode; *(Beta 3.36 only)* FM) and still send MIDI.
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
| **Shift + 29** *(since RC2)* | **Gate retrigger**: on (green with Shift, the default) = every new note restarts the envelope; off (yellow) = **legato**: with other notes held, a new note only changes the pitch. *(Beta 3.36 only)* It steps through the seven **voice modes** of pad 32 (with Shift, in the mode's colour). |
| 30 | Opens the **step-drummer**; **Shift + pad 30** turns it off. |
| 31 | VA-drum only: velocity scales the pitch and filter envelopes. |
| 32 | *(Beta 3.36 only)* **Voice mode** (a row): see «Voice mode» below. |

### Voice mode (pad 32) *(Beta 3.36 only)*
With the engine on, **a touch on pad 32** opens the voice modes on **pads 17-24** (modes with the same name share a colour) (the current one bright, the others dim; pads 9-24 do not load patches meanwhile); touching one picks it; pad 32 again (or leaving the view) closes it. Pad 32 always shows the mode's colour. With the row open, **K1 = the glide's amount** (cyan: its time; fully left, no glide; up to about 2 s) and **K2 = the unison's detune** (blue; up to ±50 cents between the outer voices). The mode, the time and the detune are saved with the own-synth patch and with the project.

| Pad | Mode |
|---|---|
| 17 (green) | **Retrigger**: every new note restarts the envelope (the default). |
| 18 (yellow) | **Legato**: with other notes held, a new note only changes the pitch. |
| 19 (cyan) | **Glide**: like legato (with other keys held the gate is not restarted), but the pitch **slides** from the held note to the new one (K1 = the amount: the glide's time). A note played with none held starts at its pitch and restarts. In the oscillator (one or two), the VA-drum and FM; the sample mode and the granular do not slide. |
| 20 (green) | **Uni retrig**: the voices (4; in FM 6, or 3 with both tracks in FM) play the same note, spread symmetrically by K2; every new note moves them all and restarts the envelope; they sound until every note is let go. In the oscillator (one or two), the VA-drum and FM; in the sample mode, one voice. |
| 21 (yellow) | **Uni legato**: the unison like legato: with other keys held, the voices only change pitch (without restarting the gate nor, in FM and the VA-drum, their own envelopes). |
| 22 (cyan) | **Uni glide**: the unison sliding only from a held note to another (legato); a note played with none held starts at its pitch, with no glide, and restarts the envelope. |
| 23 (violet) | **Uni always-glide**: the unison always sliding from the previous note to the new one, even after every key was let go (then the gate restarts); with other keys held, the voices only change pitch. |
| 24 (magenta) | **Poly**: In the **oscillator** (one or **two oscillators**; the supersaw too), the **VA-drum**, **FM** and the **sample mode** (stereo too), **up to 4 notes at once** (in FM, up to 6), each with its own velocity; the envelope, the filter and the effect are the track's and every new note restarts them; letting go of a note while others are held silences it and the last one rings through the release; one note too many takes the oldest one's voice. **In the VA-drum** every hit has **its own pitch and level envelopes and its own noise**: a new hit does not restart the earlier ones and letting go of the note does not cut the hit (the filter is still the track's). **In FM** every note has its own four operators with their envelopes and its own noise, and rings through its release even if you play others; **6 FM voices between the two tracks**: a track alone has 6; with MIDI 1 and MIDI 2 both in FM poly (or unison), 3 each. In granular, one voice. |

### Own-synth patches (pads 9-24) *(since RC2)*
- 16 slots per page; **Octave ▼ / ▲** = 4 pages (64 slots per pack, shared by MIDI 1 and MIDI 2).
- **Touch** = load (the tonic sounds while you hold the pad; *(Beta 3.36 only)*: **Shift + pad** = load without the sound). **Clear + pad** twice = save. **Duplicate + A + B** = swap; **Duplicate + A**, another pack, **Duplicate + B** = copy to another pack (Duplicate yellow while one is waiting).
- Colours: dim peach = has a patch, bright = the last used, violet = empty.
- A patch stores the whole engine: chosen engine, oscillators, order, every value and the step-drummer setting *(writes to the card)*.
- **Clear + the track button** *(since RC2)* puts every engine value back to its default (the chosen engine stays; *(Beta 3.36 only)*: the FM's too, and the matrix keeps its destinations with the amounts at zero).

### The engines (pad 27)
- **Choosing the engine** *(Beta 3.36 only)*: a tap on **pad 27** opens the **engine row** on **pads 17-23**: off (white), line input, oscillator, VA-drum, granular, sample and FX sequencer, in their colours; the current one bright, the others dim. Tapping one picks it and the row stays open; **pad 27 again** closes it and the patch list comes back (pads 9-24, which load nothing meanwhile). Shift + pad 27 still steps to the next engine (in RC2.10, every tap of pad 27).
- **Line input** (yellow): the track's audio input (line 1 on MIDI 1, line 2 on MIDI 2) goes through the VCA-VCF; the track's notes trigger it.
- **Oscillator** (green): morph sine → triangle → saw → square, SHAPE, second oscillator (pad 28) with FM, ring, sync and bitwise modes; two notes = paraphony (with one oscillator, *(since RC2)*: the last note has priority and releasing it goes back to the previous one).
- **VA-drum** (red): one-shot VCA, decay envelopes for pitch (Sustain knob) and filter (Release knob), white noise (LFO speed) and random values instead of the LFO.
- **Granular** (magenta): up to 16 grains from a pack sample or the capture (page 2, next section).
- **FX sequencer** (blue): the track's step-drummer triggers the slots of Master FX's bottom row (6.1).
- **FM** (violet) *(Beta 3.36 only)*: **pad 24** of the row: a 4-operator FM synth, a variant of the oscillator, with 16 algorithms (classic, percussive, bells and strings) and its knobs on **page 7** (chapter «4-operator FM»).
- The track keeps sending its MIDI with any engine.

<a id="midi-knobs"></a>
### 3.2 Knob pages of the MIDI 1 / 2 engine

*How to get there:* With the engine on, pads 1-5 of the Preset view pick what the 8 knobs do; Shift gives a second layer.

**In this view**

- **VCA-VCF** — level and filter with their envelope and LFO; with Shift, the filter type and the effect type.
- **Oscillators** — a waveform that morphs from sine to square, and a second oscillator with FM, ring and sync.
- **Granular** — turns a sample into textures: grains that read it at another place, speed or direction, to freeze, stretch or slice it.
- **Page 4** — the 8 parameters that can be recorded as automation (*(Beta 3.36 only)*: with Shift + knob, any of the 33; Record + step = a snapshot of the values).

### Page 1 — VCA-VCF
| Knob | Alone | With Shift |
|---|---|---|
| K1 | Attack | Sustain |
| K2 | Release | Decay |
| K3 | Envelope → level | LFO → level |
| K4 | Envelope → filter | LFO → filter |
| K5 | Filter | Filter type (DJ, LP 12, HP 12, BP, notch, LP 24, HP 24) |
| K6 | Resonance | VCA gain (up to +18 dB with saturation) |
| K7 | LFO speed (bipolar *(Beta 3.36 only)*: right free, left synced; 0.2) | — |
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
| K7 | WAVE (morph); *(Beta 3.36 only)* in the sample mode, the stereo width | — |
| K8 | LFO → morph | Envelope → morph |

**What SHAPE does on each waveform** (K2; SHAPE 2 on OSC 2, the same). The knob's centre is the pure wave (on the saw *(Beta 3.36 only)*, fully left); the envelope (K4) and the LFO (K6) move SHAPE from the knob's position. With WAVE between two waves, SHAPE acts on both at once, each in its own way:

| Wave (WAVE) | SHAPE left of centre | Centre | SHAPE right of centre |
|---|---|---|---|
| Sine (0) | Nothing: the pure wave | Pure | **Wavefold**: the wave is amplified (up to about 8 times fully right) and folds back on itself: more harmonics the further right. *(Beta 3.36 only)* On high notes the maximum gain drops so as not to alias: about 6.7 times at note 72, 3.9 an octave higher, 2.4 two octaves higher |
| Triangle (42) | *(Beta 3.36 only)* **Exponential ramps**: sharp peaks and wide valleys, more harmonics the further left (in RC2.10, nothing) | Pure | **Wavefold**, as the sine |
| Saw (84) | *(Beta 3.36 only)* The whole travel: fully left a plain saw; towards the right, a **supersaw** of 7 saws (the centre one and 6 detuned ones that get louder and spread apart; fully right, the full supersaw) | Half a supersaw | The full supersaw fully right |
| Saw in RC2.10 | The ramp bends upwards (rises fast at first, then flattens) | Straight ramp | The ramp bends downwards (starts flat, rises at the end) |
| Square (126) | An ever narrower pulse (down to about 3 %) | Square (50 %) | An ever narrower pulse the other way (up to about 97 %; it sounds like the left one) |

**Less aliasing** *(Beta 3.36 only)*: the saw, the supersaw's seven saws and the square / pulse are made with PolyBLEP: on high notes the metallic tones that do not belong to the note are gone (about 40 dB less); low notes sound the same. The sine and the triangle without folding do not change.

### Page 2 — granular
| Knob | Alone | With Shift |
|---|---|---|
| K1 | Pitch ±24 st | Fine ±1 st |
| K2 | Position in the sample | Position spread |
| K3 | Scan (centre frozen) | *(Beta 3.36 only)* **Bipolar**: to the left, the chance of a reversed grain (up to 100 %); to the right, the pitch spread (up to ±24 st). In RC2.10: reverse grain probability |
| K4 | Grain size 5-500 ms | *(Beta 3.36 only)* **Stereo spread** (see below). In RC2.10: pitch spread |
| K5 | Density 1-16 grains | Window |
| K6 | Scan zone | Note mode: pitch / slicer / stretch *(since RC2)* |
| K7 | LFO → position | LFO → size |
| K8 | Envelope → position | Source: the capture or a drum's sample *(since RC2)* |

- **Note mode (Shift + K6):** **pitch** = the notes change the grains' pitch; **slicer** = the sample is cut into 16 slices and each note plays one (note 36 the first one, each note up the next one; it starts again every 16 notes); **stretch** *(since RC2)* = the notes change the pitch and the stretch from the position (K2) to the end lasts **K3 steps** (1-64) at any tempo, without changing the pitch, aligned with the start of the transport; stopped, the position stays frozen.

- **Stereo granular** *(Beta 3.36 only)*: with **Shift + K4** above 0, each grain goes to one side at random, further apart the higher it is; the **track's pan** (Mixer) sets the proportion: centred, half and half; to the right, more grains on the right. The stereo part (what differs between the sides) follows the track's VCA, level, pan, mute and sidechain; the engine's filter and effect and the sends act on the centre only.

### Pages 3-5
- **Page 3 (OSC 2):** *(since RC2)*: the eight values without Shift, following the printed labels: K1 Oscillator TUNE 2, K2 Osc mod SHAPE 2, K3 Amp envelope MIX OSC 1 ↔ OSC 2, K4 Filter envelope FM, K5 Filter frequency FINE 2, K6 Resonance BITSYNC, K7 Modulation WAVE 2, K8 FX RING (in RC0.9: K1 TUNE 2 / FINE 2, K2 SHAPE 2 / FM, Shift + K3 RING, K7 WAVE 2).
- **Page 4:** the 8 sequenceable values: with Record + Play their moves are recorded into the pattern (TUNE, Release, Env → level, Env → filter, Filter, Resonance, LFO speed, Effect). *(Beta 3.36 only)*: **Shift + knob** = that knob's **destination**: the engine's 33 parameters in the modulation matrix's order and colours (the LED in its page's colour; 4 clicks a parameter); with **Clear held before Shift**, the factory one. While you pick, **pads 9-24 show where the destination lives**, as when a matrix knob turns: its page's pad bright and that page's knobs (K1-K8 above, Shift + K1-K8 below; the destination bright). The lane records and plays the new destination (what it already held now moves that parameter). They are saved with the own-synth patches (MIDI 1 / 2's Preset view); a patch without them loads the factory ones.
- **Snapshot of the values into a step** *(Beta 3.36 only)*: in MIDI 1 / 2's track view (engine on), **Record held + a step pad** (pads 1-16; with 17-32, steps 17-32) writes into that step's lanes the parameters that are **not at their initial value** (the one of Clear + knob to the right), and only those. A parameter without a lane takes one whose parameter is at its initial value (in lane order), and that lane is cleared in the pattern first; when they do not fit, the first ones in the matrix's order. The step keeps its notes and Record stays as it was.
- **Page 5:** ADSR on top, LFO below. *(since RC2)*: **Shift + K8 = the LFO's shape**: reverse saw (orange, the usual one), saw (magenta), triangle (green), square (red), sine (cyan), sample & hold (white: a random value each cycle); *(since RC2.02)*: **slewed sample & hold** (violet: it glides from one random value to the next during each cycle), and **with no shape saved (a new or older project) the triangle** (in RC2: the reverse saw; an own-synth patch from before the shapes still loads the reverse saw). A step every 4 clicks, K8's LED with Shift in its colour. Saved with the project and in the own-synth patch; with the VA-drum the LFO stays its noise.
- **Page 6** *(since RC2.02)*: the mod matrix (next section).
- **Page 7** *(Beta 3.36 only)*: with the FM engine, its operators and its algorithm (chapter «4-operator FM»).
- Type knobs show colour (type) and brightness (position within the type). Everything goes out and comes in over CC / NRPN (MIDI reference).

<a id="midi-matriz"></a>
### 3.3 Mod matrix

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

<a id="midi-fm"></a>
### 3.4 4-operator FM

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
| Pads 17-32 | 16 samples of the pack: touch = the track's sample (cyan) and it sounds; the others dim. *(Beta 3.36 only)* **Shift + sample** = pick it silently; **Shift + the one already chosen** = pick the second sample (stereo; see below). |
| Octave ▼ / ▲ | Next / previous page of samples (4 pages = the pack's 64; lit when there are more that way). |
| Pads 1-16 | The 16 steps of the half shown: peach = with a sample flip, dim cyan (the background) = without, white = the one playing. **Hold a step + touch a sample** = its flip (the step green, its sample yellow); also **hold a sample + touch steps** (since RC2.04); **Clear + step** = remove it. *(Beta 3.36 only)*: a flip on a step **without a note** adds **the last note you played** on the track there (60 if none yet; one step long, velocity 100), so it sounds; the steps show **peach** = a note with a flip, **cyan** = a note without a flip, **violet** = a flip without a note, dim cyan = nothing. |
| 1-16 / 17-32 | The other half of the pattern. |

- **The pitch:** C3 (note 60) = the sample as recorded; an octave up = twice as fast. The notes come from the normal Note view, the step-drummer or incoming MIDI.
- **One-shot:** the VCA stays open and the sample plays to its end; every new note restarts it (one voice per track). The filter, effect and LFO of the engine pages still work.
- **Stereo** *(Beta 3.36 only)*: **K7 of the OSC 1 page** (WAVE, which did nothing in this mode) = the **stereo width**. Fully left, mono as always; turned up, every note plays the chosen sample on the **left** and the **second** one on the **right** (at first the next one, N + 1; 64 is followed by 1): a stereo sample is two slots of the pack (the device's samples are mono). **The second is picked in the picker:** **Shift + the sample already chosen** switches to picking the second (it blinks cyan; the first shows violet): touching a sample = the second, and it sounds; **Shift + the second** goes back to the first. The **distance** between them is kept: when the first changes (or with a step's flip) the second follows. With the width up, the second shows violet. The note lasts as long as the **longer** one: the shorter falls silent at its end. Both at the same pitch. The centre goes the track's way (filter, effect, level, pan, sends); the stereo part goes through the same filter and follows the track's VCA, level, pan, mute and sidechain, but not the effect or the sends. It is set at each note: turning K7 up from 0 during a note applies from the next one. The capture always plays in mono.
- **Live:** with **Record + Play**, touching a sample records a note 60 on the step playing, with its flip.
- **Erasing the note of a step with a flip** *(Beta 3.36 only)* (in the Note view: Clear + step, or the step held + its note's key) erases the note and **keeps the flip**, which only shows here (violet); Clear + step in this picker removes the flip.
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
- **Input:** the first note sounds as always; holding another one with it starts the arpeggio of the held notes, one an arpeggio step (with the transport stopped, at the project's tempo; since RC2.10: stopped, it always ran at about 120 BPM before), until all are let go; each note lasts an arpeggio step. **With Record the chord is recorded**, not the single notes: the sequence plays the arpeggio afterwards.
- **Held step** *(Beta 3.36 only)*: with the transport stopped, **holding a step** with several notes arpeggiates them, as if you held their pads (they sounded at once before), until you let it go; if you start the transport with the step held, the arpeggio stops when you let it go.
- **External keyboard** *(Beta 3.36 only)*: with the option on **pad 22 of Advanced Setup** on, the notes coming in over MIDI on the channel of a note track whose arpeggiator is on are arpeggiated like the pads (the first sounds as always; with Record the chord is recorded). **Off by default**, so it does not clash with a keyboard that has its own arpeggiator.
- **Pressed order** *(Beta 3.36 only)*: the notes are arpeggiated in the order they were pressed (a recorded chord, in the order of its notes in the step), not by pitch; up, down, ping-pong, random, fractal and deconstructed walk that order. A note let go leaves its place empty and skipped; the next note you press takes the first empty place before going to the end.
- **Random-mutate** *(Beta 3.36 only)*: when the chord's step has a random-mutate level, each note of the arpeggio goes through it (another degree of the scale, an octave up or down) as normal notes do; nothing is written into the step. The live arpeggio (the notes held) uses the level of the step the track is on (playing, the one that plays; stopped, where it stopped).
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
- **Stereo pair** *(Beta 3.36 only)* — Drum 1 + Drum 2 (or 3 + 4) play a stereo sample: the left one drives both, the right one only fine-tunes.

| Knob | Alone | With Shift |
|---|---|---|
| K1 Oscillator | Pitch (*(since RC2)*: the stock one, continuous as on the original; the chromatic view's pads transpose on top) | Pitch envelope amount |
| K2 Osc mod | Ring mod frequency | Ring mod amount |
| K3 Amp envelope | **Left: decay** (the stock one). Past its maximum, **right: attack** (fade-in, up to 1 s). Neutral in the middle. *(since RC2)* | **Left: sample start**; **right: cut** from the end (up to 120/128 each; *since RC2.10* the start covers the whole sample: before, it reached the end at a quarter of the travel and beyond that the hit was silent). Middle = the whole sample. *(since RC2)* |
| K4 Filter envelope | Envelope → cutoff | Envelope shape |
| K5 Filter frequency | Filter / EQ (by default the stock tilt EQ) | **Filter mode**: stock tilt EQ, band-pass, notch, comb, DJ |
| K6 Resonance | Resonance | — |
| K7 Modulation | LFO amount: right = tremolo; left = vibrato (*(Beta 3.36 only)*: left = **start scan**: each hit starts where the LFO is, from the Shift + K3 start up to a 64th of the sample further for every step of the knob (fully left, the whole sample), never past the cut; the LFO no longer restarts with each hit) | LFO speed (bipolar *(Beta 3.36 only)*: right free, left synced; 0.2; synced, the scan is at the start on the first beat) |
| K8 FX | Distortion; left of 0, **bitcrush** | **Distortion type**: stock, soft, hard, fold |

- **K3:** turning left, the attack goes back to 0 before the decay goes down; with Shift, one of the two (start or cut) goes back to 0 before the other moves. LED: attack in white; with Shift, start in the drum's colour, cut in white.
- **Clear + K3 to the right** puts attack, start and cut to 0; **Clear + K8 to the right** removes the bitcrush too *(since RC2)*. Clear + knob resets both layers on the others.
- **Clear + the drum's button** *(since RC2)* (with one of its views on screen): the drum's eight knobs, with their Shift layer, back to their defaults.
- All neutral, a sample sounds as on the original. Everything is saved with the project and has an NRPN.
- **Sidechain between drums:** Shift + FX and Octave ▼ (8.1).

### Stereo pair *(Beta 3.36 only)*
**Hold Drum 1 and press Drum 2** (or the other way round; Drum 3 + Drum 4 the same): the two drums become a **stereo pair**; the same gesture undoes it. Not with Shift, Clear or Duplicate held, nor in Setup.
- **Drum 1 / 3** sounds on the left and **Drum 2 / 4** on the right with the pack's **next sample** (a stereo sample = two slots in a row; after 64, 1).
- **Everything of Drum 1 / 3 drives both:** its knobs (the Shift layer too), its pattern (steps, sample flips, micro steps, automation, arpeggio, rollers), its level, sends and side-chain. Its pan is the centre of the pair.
- **Drum 2 / 4's pattern does not play** while the pair lasts (it stays saved). Its pads and MIDI notes play it alone, on the right.
- **Picking another sample on Drum 2 / 4** (its Preset view) sets the distance between the two; then it follows Drum 1 / 3's sample changes.
- **Drum 2 / 4's knobs** are deviations from Drum 1 / 3 (its own values do not change and come back when the pair is undone):

| Knob | Alone | With Shift |
|---|---|---|
| K1 | Detune (± 100 cents) | Pitch envelope amount |
| K2 | **Stereo width** (by default fully: left / right; fully left, both centred) | Ring mod amount |
| K3 | Decay | Sample start |
| K4 | Envelope → cutoff | Envelope shape |
| K5 | Filter / EQ | — (Drum 1 / 3's mode) |
| K6 | Resonance | Ring mod frequency |
| K7 | LFO amount | — (Drum 1 / 3's speed) |
| K8 | — (Drum 1 / 3's distortion) | — |

- LEDs: the deviations in Drum 1 / 3's colour (brighter = more deviation), the width in white. **Clear + knob** = no deviation (the width, full).
- Drum 2 / 4's button pulses in Drum 1 / 3's colour while the pair lasts.
- **Saved with the project** (on, distance, width and deviations).

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
| 2 / 3 | Auto-Filter low / high pass | speed (bipolar *(Beta 3.36 only)*: right free, left synced), depth, resonance, centre |
| 4 | Digitise | sample rate, bits; **K3 = momentary delay throw** while you hold the pad, **K4 = envelope of the amount** *(since RC2)* |
| 5 | Phaser | speed (bipolar *(Beta 3.36 only)*: right free, left synced), depth, feedback, mix |
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
- **Master filter resonance** — on Shift + Octave ▲ / ▼, in steps of 16 *(Beta 3.36 only; in RC2.10, 1-16 / 17-32)*.
- **Master filter off / on** — Shift + pad 25, keeping its position *(Beta 3.36 only)*.

| Gesture | What it does |
|---|---|
| **Octave ▲ / ▼** | The knobs = delay / reverb sends. |
| **Shift + knob** | Global parameters: reverb K1 type, K2 decay, K3 damping; delay K1 time, K2 sync, K3 feedback, K4 width, K5 ratio, K6 slew. Saved with the project. |
| **Duplicate** | Reset: sends to 0, master filter centred, Master FX off. |
| **Shift + Octave ▲ / ▼** *(Beta 3.36 only)* | Master filter resonance +16 / −16; stops at 127 / 0 (with Shift, Octave lights yellow). In RC2.10: **1-16 / 17-32** (green LED). |
| **Shift + pad 25** *(Beta 3.36 only)* | Master filter off / on: while off, it sounds as with the filter at the centre even if you move its knob (the knob still changes its position); again, the filter comes back at the knob's current position. While off, the filter knob's LED is red; with Shift, pad 25 lights yellow (red while off). Without Shift, pad 25 is the stock one. |
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
| **Shift + pads 9-16** | **Repeats** of the current scene (1-8; with Shift the row is yellow, the chosen one green). *(since RC2)* While playing, with Shift, **the repeat now playing is white** (pad 9 = the first time; on the last one the green pad blinks white / green). *(Beta 3.36 only)* |
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

## 11. Data: saving, MIDI and modulation

<a id="datos-patron"></a>
### 11.1 What a pattern holds and how to make sure it is saved

*How to get there:* Every track has 8 patterns per project. What is in a pattern travels with it (Duplicate, chains, scenes) and reaches the card when you **save the project**.

### What each pattern carries
| What | Tracks | How it gets there |
|---|---|---|
| Notes, velocity, gate, micro steps and probability of every step | all | As on the original |
| Knob automation: the macros of Synth 1 / 2, the MIDI template knobs, the drums' stock knobs, Mixer level and pan, reverb / delay sends | all | As on the original: **Record** and turn, or hold a step and turn |
| Sample flips | drums | As on the original |
| First and last step, sync rate and direction | all | Pattern Settings, as on the original |
| **Random-mutate, frequency and dynamics** of every step *(since RC2)* | all | [Probability view](#probabilidad) |
| **Fractal / deconstructed order** and **chain rule** (n passes, jump to B / C) *(since RC2)* | all | [Pattern Settings](#pattern-settings), [Patterns](#patterns) |
| **Step that releases the automation** *(Beta 3.36 only)* | Synth 1 / 2, MIDI 1 / 2 | Velocity view, Shift + step pad ([track view](#synth-nota)) |
| **Own-synth lanes** (the 8 of page 4) *(since RC2)*; *(Beta 3.36 only)* the **snapshot** of Record + step | MIDI 1 / 2 | Record and turn ([knob pages](#midi-knobs)) |
| **Step-drummer notes**: in automation lanes (MIDI 1 / 2: the pitch one and, for its page 2, the Release one; Synth 1 / 2: its macro's) | Synth, MIDI | [Step-drummer](#step-drummer) |
| **FX sequencer values** | MIDI 1 / 2 | [Step-drummer](#step-drummer) |
| **Sample-mode sample flips** (in the track's level lane) *(since RC2)* | MIDI 1 / 2 | [Sample picker](#midi-muestra) |
| **Drum chromatic steps** (in the drum's pitch lane) *(since RC2)* | drums | [Chromatic view](#drum-cromatica) with Record |
| Hits of the **rollers** and of the **drum arpeggio** | drums | With Record, as normal hits |
| *(Beta 3.36 only)* The **copy of the own synth** of MIDI 1 / 2 (in the settings of patterns 1-5, without changing what they play) | MIDI 1 / 2 | On its own, when the project is saved |

- **Not in the pattern**, although chosen with it on screen: the **arpeggiator** (on, order and resolution) and the **gate by holding** are saved in the **project** per track (the arpeggiator per track and pattern number: **duplicating the pattern does not copy it**).
- **Duplicating a pattern** copies everything in the table. **Clear + pattern** in the Patterns view (outside chain mode) deletes it with its rule and its order.

### How to make sure it is saved
1. **A knob turned without Record** changes the sound of the whole project (the patch, the drum knobs, the Mixer…), not the pattern. To make it change **at a step or along the pattern**, record it: **Record** with the sequencer running, or **hold a step and turn** (as on the original).
2. **Save the project: Save twice** (the first press flashes white; the second, fast green). It goes to the last slot used; for another slot, in the Projects view: **Save + the slot's pad** (as on the original). Everything marked «project» or «pattern» in this guide only reaches the card this way.
3. **Loading another project or switching off without saving** loses the changes since the last Save (as on the original). At power-up the last project used is loaded, as it was saved.
4. **Save always off** = **Save Lock** is on (Shift + Save at power-up, an original feature): repeat the gesture to remove it.
5. **The MIDI 1 / 2 own synth** keeps its values **in the device settings** (the same for every project): *(Beta 3.36 only)* also **with the project** when it is saved. To keep a sound across projects or packs, **save it as a patch** ([MIDI 1 / 2 Preset view](#midi-preset), Clear + pad twice). To make it change inside the pattern, use page 4 (the lanes) or the step-drummer.
6. **A Synth 1 / 2 patch** as it sounds (knobs, edited macro destinations, MIDI received) goes with the project; to have it in the pack and use it in other projects, **save it** in the [Preset view](#synth-preset) (Clear + pad twice) *(since RC2)*.
7. **Before switching off:** stop the sequencer and wait **2 s** without touching the MIDI 1 / 2 engine (its settings are written to the card only with the transport stopped, so as not to break up the audio), and switch off with the **power button**.
8. **Without a card (the internal memory's pack)** and with the **S** versions, the mod writes nothing of its own: patches, samples and copies are not saved (the Save LED turns red). Projects are, as on the original.

<a id="guardado"></a>
### 11.2 What comes back after a restart and where it is saved

*How to get there:* Five places: the **pattern**, the **project** (both when the project is saved), the **pack** (at once, on the card), the **device settings** (on their own, for every project) and none (lost at power-off).

### The project (Save twice)
| What | Where it is used |
|---|---|
| As on the original: the Synth 1 / 2 patches as they sound, the drums' chosen samples and knobs, Mixer, sends and reverb / delay parameters, side-chain, scenes and chains, tempo, swing, scale and root | — |
| **New drum knobs**: envelope, ring mod, LFO, filter and its mode, start, cut, attack, bitcrush, distortion type; the chromatic view's semitone | [Drums](#drum-pista) |
| **Noise source** of Synth 1 / 2 (audio inputs) | [Source view](#synth-fuente) |
| **Master FX**: the 20 knobs, the effects assigned to the slots, compressor attack / release | [Master FX](#master-fx), [Side-chain](#sidechain) |
| **Side-chain**: Synth 1 / 2 and MIDI 1 / 2 as a source; K1-K4 of the drum pages | [Side-chain](#sidechain) |
| **Chain mode** (and in each scene), **scene repeats**, the **cue mode** sends | [Patterns](#patterns), [Mixer](#mixer) |
| **Count-in** (the click, as on the original, is not saved) | [Buttons](#botones) |
| **Arpeggiator** of notes and of drums (per track and pattern), **gate by holding**, **fixed length** | [Pattern Settings](#pattern-settings), [Micro Step](#micropasos) |
| **Custom scale** and *(Beta 3.36 only)* **Jankó** | [Scales](#escalas) |
| MIDI 1 / 2 own synth: **gate retrigger**, **LFO shape**, the step-drummer's pitch-vel toggle and page 2 destination | [Knob pages](#midi-knobs), [Step-drummer](#step-drummer) |
| *(Beta 3.36 only)* **Stereo drum pairs**: on, distance, width and deviations | [Drums](#drum-pista) |
| *(Beta 3.36 only)* **The whole own synth** of MIDI 1 / 2: engine, values, matrix, page 4 destinations, FM, voice mode, stereo (loading a project that carries it, the project's wins; an older one leaves the sound as it was) | [MIDI Preset view](#midi-preset) |

### The pack (written to the card when you do the gesture)
| What | Where it is used |
|---|---|
| **Saved Synth 1 / 2 patches** *(since RC2)* (Clear + pad twice); swaps and copies between packs | [Synth Preset view](#synth-preset) |
| **Own-synth patches** of MIDI 1 / 2 (64 per pack, shared by both tracks: engine, values, step-drummer, *(since RC2.02)* matrix, *(Beta 3.36 only)* FM, page 4 destinations, voice mode) | [MIDI Preset view](#midi-preset) |
| **Samples**: swaps, copies between packs and the **capture** replacing a drum (this one when the project is saved, if it fits) | [Drum Preset view](#drum-preset) |
| **Projects copied** to another slot or pack; **deleted packs** | [Projects](#projects), [Packs](#packs) |

### The device settings (on their own, for every project)
| What | Where it is used |
|---|---|
| As on the original: channels, CC / note / Program Change filters, clock, master compressor on, brightness, Save Lock | [Setup](#setup), [Advanced Setup](#advanced-setup) |
| **MIDI 1 / 2 engine**: the engine chosen, all its values, oscillators and order (pads 28 / 29), step-drummer on and its destination, FX sequencer, patch flip | [MIDI Preset view](#midi-preset) |
| **MIDI Thru jack mode** (Thru, Out 2, Merge, Filter), the project's **Program Change channels**, **cue mode** | [Advanced Setup](#advanced-setup), [Setup](#setup), [Mixer](#mixer) |
| *(Beta 3.36 only)* The drums' **General MIDI mode** and its notes; **USB merge**; **external keyboard to the arpeggiator** | [Setup](#setup), [Advanced Setup](#advanced-setup) |

<a id="datos-perdido"></a>
### 11.3 What is lost at a restart

*How to get there:* Whatever is in none of the tables above lives only in memory and is gone at power-off (or when another version is installed).

| What | At power-up |
|---|---|
| **Everything changed since the project's last Save** (as on the original) | The project comes back as it was saved |
| **Master filter** and its **resonance** (as on the original); *(Beta 3.36 only)* the master filter switched off with Shift + pad 25 | At their initial values; the filter, on |
| **Click** on / off and **View Lock** (as on the original) | Off |
| **Latched effects**, **song pointer** and latched sample of Master FX | Off; the song pointer at 0 |
| **Record in the Setup view** (record the internal routings) | Off |
| In the Side-chain view, the **triggers of a drum** by another drum or by a pattern (pads of the drum pages) | Those of the drum's preset |
| Pending **mutes on the next bar** (Mixer, Shift + pad) | — |
| **Latched notes** (Shift + key), the **chord screen** (type and modifiers) and the half-step of **Octave with Jankó** *(Beta 3.36 only)* | No latch; the defaults; Octave at 0 |
| **Split keyboard** and open views (step-drummer, macro editor, picker) | Closed |
| A **sample or patch waiting** to be copied into another pack (Duplicate + A) | Nothing waiting |
| The Master FX **capture** unused, or used in a drum without saving the project | Empty; the drum with its pack sample |
| The own synth's **mod matrix** not saved in a patch *(since RC2.02)* (*(Beta 3.36 only)*: also saved with the project) | Off |
| The pass counters of **frequency** and of the **fractal** order (they restart when stopped) | From the first pass |

- **Installing another version** restarts the device: what was not saved is lost; the project, the pack and the settings stay.
- **Going back to the official firmware:** projects and packs saved with the mod open on the original; the mod's own data sits in parts of the files the original does not use, and the original does not read it.

<a id="midi"></a>
### 11.4 MIDI: own behaviours, new CCs and NRPNs

*How to get there:* Everything new goes out and comes in over CC / NRPN, following the Setup's CC Tx / CC Rx filters. The original device's parameters keep the numbers of Novation's guide (see the next section).

### Channels (as on the original, changeable in Setup)
Synth 1 = channel 1, Synth 2 = channel 2, drums = channel 10, project and Master FX = channel 16 (those of Novation's guide); MIDI 1 / 2 = the channels chosen for them in Setup.

### Own behaviours
| What | How |
|---|---|
| **External keyboard on MIDI 1 / 2** *(since RC2)* | Notes coming in on the channel of MIDI 1 / 2 (USB or DIN) play its own synth and are recorded; they are not sent on to the output. |
| **External keyboard to the arpeggiator** *(Beta 3.36 only)* | Advanced Setup, pad 22: notes coming in on the channel of Synth 1 / 2 or MIDI 1 / 2 go through its arpeggiator. |
| **Patch flip** | MIDI 1 / 2 Preset view, pad 26: every note of the track goes out as a Program Change on the track's channel. |
| **The project's Program Change** *(since RC2)* | Setup, pads 29 / 30: listen channel and output channel (16 by default); what arrives on the listen one is sent again on the output one. |
| **MIDI Thru: Merge and Filter** | Advanced Setup, Duplicate: Thru (hardware), Out 2, Merge (DIN In + the device's MIDI), Filter (DIN In without the device's channels). No SysEx. |
| **USB merge** *(Beta 3.36 only)* | Advanced Setup, pad 23: what comes in on the DIN In also goes out over USB (without the clock with Clock Tx, without SysEx). |
| **General MIDI mode of the drums** *(Beta 3.36 only)* | Setup, K4 / K5-K8: the hits of Drum 1-4 go out as the GM note chosen instead of 60 / 62 / 64 / 65. Inside, the sound is the same. |
| **Stereo drum pair** *(Beta 3.36 only)* | Drum 2 / 4's notes play it alone, on the right; its pattern neither sounds nor goes out over MIDI while the pair lasts. |
| **Record the internal routings** *(since RC2)* | Setup, Record: what a MIDI track sends to a synth on the same channel is also recorded in the synth; *(Beta 3.36 only)* nothing is recorded in a track muted in the Mixer. |
| **New knobs** | Turning them (also with Clear) sends their CC / NRPN; receiving it moves the knob. The Mixer's level to 100 / 0 (Shift + knob) goes out as a turn. |
| **No MIDI** | The own synth's mod matrix, the FM, the voice mode and the page 4 destinations have no CC / NRPN: they are saved in the own patches. |
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
| 29 | WAVE 2 (granular: pitch spread; Beta 3.36: stereo) | CC 30 | 3 / K7 |
| 30 | SHAPE 2 (granular: window) | CC 31 | 3 / K2 |
| 31 | MIX OSC 1 ↔ OSC 2 | CC 52 | 2 / Shift + K2 · 3 / K3 (RC2) |
| 32 | BITSYNC | NRPN 4:32 | 2 / Shift + K3 · 3 / K6 (RC2) |
| 33 | FM (granular: position spread) | NRPN 4:33 | 3 / K4 (RC2) · 3 / Shift + K2 (RC0.9) |
| 34 | RING (granular: reverse; Beta 3.36: bipolar, reverse / pitch spread) | CC 54 | 3 / K8 (RC2) · 3 / Shift + K3 (RC0.9) |

**Page 4** (sequenceable: recorded into the pattern with Record): TUNE, Release, Envelope → level, Envelope → filter, Filter, Resonance, LFO speed, Effect. *Beta 3.36 only:* the eight destinations are chosen with Shift + knob.

### Drums

The drums channel (Setup). **CC 99 = 5, 6, 7, 8** (Drum 1-4), **CC 98 = LSB**, **CC 6 = value**. The stock knobs (pitch, decay, distortion, EQ) keep their original CCs. *Beta 3.36 only:* with the **General MIDI mode** (Setup view, K4) the notes of Drum 1-4 go out as each one's GM note (K5-K8, 35-81; by default 36 / 38 / 42 / 46) instead of 60 / 62 / 64 / 65.

| LSB | Parameter | Values |
|---|---|---|
| 1 | Envelope → pitch | 0-127, 64 = 0 |
| 2 | Ring mod: frequency | 0-127 |
| 3 | LFO: amount (> 64 tremolo; < 64 vibrato, Beta 3.36 only: start scan) | 0-127, 64 = 0 |
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

<a id="destinos"></a>
### 11.5 Mod matrix and macro destinations

*How to get there:* The stock synths (Synth 1 / 2) have Novation's matrix and macros; the MIDI 1 / 2 own synth has its matrix and its lanes.

The official reference is Novation's **Programmer's Reference Guide**, version 3 ([PDF](https://fael-downloads-prod.focusrite.com/customer/prod/downloads/circuit_tracks_programmer_s_reference_guide_v3.pdf), on the [Circuit Tracks downloads page](https://downloads.novationmusic.com/novation/circuit/circuit-tracks)). For every macro slot it gives: «macro knob 1 destination A NRPN 3:0 0 – 70 0» (Novation, *Circuit Tracks Programmer's Reference Guide* v3, «Macro Knobs»).

### Synth 1 / 2 mod matrix (stock, unchanged)
- Edited from Components or over MIDI (the synth's channel); the device has no view for it. Every slot: source 1, source 2, depth (−64..63) and destination. The official guide lists 12 slots from **NRPN 1:83** (source 1, source 2, —, depth, destination: 5 numbers per slot); the firmware has 20, with the same pattern.
- **Sources (0-12):** 0 direct, 4 velocity, 5 keyboard (note), 6 / 7 LFO 1 (unipolar / bipolar), 8 / 9 LFO 2 (unipolar / bipolar), 10 amp envelope, 11 filter envelope, 12 envelope 3.
- **Destinations (0-17):** 0 pitch of both oscillators, 1 / 2 pitch of oscillator 1 / 2, 3 / 4 v-sync 1 / 2, 5 / 6 pulse width / index 1 / 2, 7 / 8 level of oscillator 1 / 2, 9 noise level, 10 ring mod level, 11 filter drive, 12 filter frequency, 13 resonance, 14 / 15 LFO 1 / 2 rate, 16 amp envelope decay, 17 filter envelope decay.

### Synth 1 / 2 macros (stock) and their editor *(since RC2)*
- 8 macros per patch, position = **CC 80-87**; every macro, 4 slots A-D. Slot r (0-3) of macro k (1-8): **NRPN 3:(16 (k − 1) + 4 r)** = destination, + 1 start, + 2 end (the stretch of the knob's travel, 0 / 127 by default), + 3 depth (64 = 0).
- The official guide gives the destination as «0 – 70» without naming them: the list below names each one (70 destinations, 0-69).
- **On the device:** [source view](#synth-fuente), pad 32 = editor (slot, start, end, destination, depth). The edits go into the project's patch; Clear + pad twice in the [Preset view](#synth-preset) saves it to the pack.
- The editor's knob walks the destinations with a CC first (by CC number), then the NRPN-only ones; on the pads, white = CC, light blue / magenta / violet = NRPN of banks 0 / 1 / 2.

### The MIDI 1 / 2 own synth's matrix (own) *(since RC2.02)*
- [MIDI Preset view](#midi-preset) with the engine on, **pad 6**: the 8 knobs are 8 **sources**: K1 velocity, K2 note, K3 random per note, K4 LFO 2, K5 envelope 2, K6 a drum's hit, K7 position in the pattern, K8 stepped random (*(Beta 3.36 only)* LFO 2 also synced to tempo).
- **The knob's position is the destination and the amount:** left = off; turning right walks every parameter of the knob pages (page 1's, then page 2, page 3 and those of page 5 not met before), 16 steps per destination, the amount growing inside each stretch. LED = the colour of the destination's page; brightness = amount.
- Several sources on the same destination add up; the parameter's stored value does not change. Details: [Mod matrix](#midi-matriz).

### The own synth's lane destinations (page 4) *(Beta 3.36 only)*
- The 8 knobs of page 4 are the automation lanes (by default: TUNE, Release, Env → level, Env → filter, Filter, Resonance, LFO speed, Effect). **Shift + knob** = its destination, among the same parameters and colours as the matrix; **Clear held, then Shift + knob** = the default one. Saved with the own patch and with the project. Details: [Knob pages](#midi-knobs).

### Step-drummer destinations
- MIDI 1 / 2: pads 17-24 of its view = the engine parameter every step moves; Synth 1 / 2: macros 1-8. Details: [Step-drummer](#step-drummer).

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

## A. Appendix

<a id="instalar"></a>
### A.1 Installing and going back

*How to get there:* `tools/rc_uploader.html` patches the official firmware in the browser and sends it over Web MIDI.

1. Download Novation's official firmware 1.2.1, open `tools/rc_uploader.html` in Chrome and connect the Circuit Tracks over USB.
2. Pick the version (RC2.10, the safer RC2.10S, Beta 3.36 with the new features, its safer build Beta 3.36S, or an earlier one) and send. Novation's bootloader is not touched.
3. **Back up the card first.** With the versions that do not end in «S», do not use the internal memory for projects.
- **Going back:** send another version or the official firmware. If it does not boot: **Scales + Preset + Note** at power-up.
