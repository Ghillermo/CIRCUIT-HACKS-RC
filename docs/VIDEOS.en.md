# CIRCUIT-HACKS — video tutorial scripts

One video per view of the device, in the order of the [Guide by views](GUIA.en.md). Each script says **what the view contains**, **how each feature works** (what to show and what to say) and **what to keep in mind**. When a script and the guide disagree, the guide wins: it is the reference.

**Builds.** The scripts follow **RC4.11** (the current release). Marks:

- **[Beta]** = only in the Beta (published: Beta 5.56). Leave it out of an RC video, or say it is Beta-only.
- **[Beta, unreleased]** = in the development betas after 5.56, not published yet. Record it only once it is out.
- **S builds** (RC4.11S) write nothing of their own to the card: whatever a script marks *writes to the card* does nothing there (the Save LED turns red).

**For every video**

- Record on a **pack on the microSD card**, not the internal pack (the first one): the mod never writes into the internal pack.
- Keep a project called, say, `TUTORIAL` with a short beat on the drums, a bass line on Synth 1 and chords on Synth 2. Save it before each video so you can come back to it.
- Film the pads and knobs from above, with the room light down: the LED colours carry most of the information. A small pad map overlay (pads 1-32, K1-K8) helps.
- Say the conventions once per video, or show them as a caption: **pads 1-32** from the top left (row 1 = 1-8, row 2 = 9-16, row 3 = 17-24, row 4 = 25-32); **K1-K4** the top knobs, **K5-K8** the bottom ones; **Shift + X** = hold Shift while you use X (the same with Clear and Duplicate).
- The master effects view is always called **Master FX**.
- Lengths are rough. Long views have chapter titles: they can be cut into parts.

## The series

| # | Video | Guide |
|---|---|---|
| 00 | Getting started: versions, installing, conventions | [A.1](GUIA.en.md#instalar), [0.1](GUIA.en.md#convenciones) |
| 01 | Buttons that work in every view | [0.2](GUIA.en.md#botones) |
| 02 | Setup view | [1.1](GUIA.en.md#setup) |
| 03 | Advanced Setup view | [1.2](GUIA.en.md#advanced-setup) |
| 04 | Synth 1 / 2 track view: Note, Velocity, Gate | [2.1](GUIA.en.md#synth-nota) |
| 05 | Scales view, custom scale and Jankó | [2.2](GUIA.en.md#escalas) |
| 06 | Synth source view | [2.3](GUIA.en.md#synth-fuente) |
| 07 | Synth 1 / 2 Preset view | [2.4](GUIA.en.md#synth-preset) |
| 08 | MIDI 1 / 2 Preset view: the own synth | [3.1](GUIA.en.md#midi-preset) |
| 09 | Own-synth voices: polyphony and the voice limiter | [3.2](GUIA.en.md#midi-voces) |
| 10 | The engine's knob pages | [3.3](GUIA.en.md#midi-knobs) |
| 11 | Mod matrix | [3.4](GUIA.en.md#midi-matriz) |
| 12 | 4-operator FM | [3.5](GUIA.en.md#midi-fm) |
| 13 | 8-operator FM [Beta] | [3.6](GUIA.en.md#midi-fm8) |
| 14 | CC editor of the MIDI macros | [3.7](GUIA.en.md#midi-cc) |
| 15 | Step-drummer view | [3.8](GUIA.en.md#step-drummer) |
| 16 | Sample mode and sample picker | [3.9](GUIA.en.md#midi-muestra) |
| 17 | Pattern Settings view | [4.1](GUIA.en.md#pattern-settings) |
| 18 | Micro Step view | [4.2](GUIA.en.md#micropasos) |
| 19 | Probability view | [4.3](GUIA.en.md#probabilidad) |
| 20 | Drum track view | [5.1](GUIA.en.md#drum-pista) |
| 21 | Drum Preset view | [5.2](GUIA.en.md#drum-preset) |
| 22 | The drums' chromatic view and rollers | [5.3](GUIA.en.md#drum-cromatica) |
| 23 | Master FX | [6.1](GUIA.en.md#master-fx) |
| 24 | FX view | [7.1](GUIA.en.md#vista-fx) |
| 25 | Sidechain view | [8.1](GUIA.en.md#sidechain) |
| 26 | Patterns view and pattern chains | [9.1](GUIA.en.md#patterns) |
| 27 | Mixer view and scenes | [9.2](GUIA.en.md#mixer) |
| 28 | Projects view | [10.1](GUIA.en.md#projects) |
| 29 | Packs view | [10.2](GUIA.en.md#packs) |
| 30 | Saving: what is kept, and where | [11](GUIA.en.md#datos-patron) |

Videos 00, 01 and 30 are not views: they open and close the series.

---

## 00 · Getting started: versions, installing, conventions

**Guide:** [A.1](GUIA.en.md#instalar), [0.1](GUIA.en.md#convenciones) · **Length:** about 5 min

**Before recording**
- A computer with Chrome, the Circuit Tracks on USB, Novation's official firmware 1.2.1 downloaded, the installer page open.
- A copy of the card already made (show it, don't do it on camera).

**In this video**
- What CIRCUIT-HACKS is and what stays as on the original.
- The versions: RC, RC…S and Beta.
- Installing, and going back.
- How the series names pads, knobs and gestures.

**Script**

1. **Hook.** *Show:* a fast montage: the own synth on MIDI 1, Master FX's mechanical gesture, the chord screen. *Say:* "This is a Circuit Tracks, with more inside. In this series we go through it view by view: what each view does, how to use it, and what to watch out for."
2. **What it is.** *Show:* the device's front panel. *Say:* "CIRCUIT-HACKS patches Novation's official firmware 1.2.1. Everything the original does is still there and works the same. The patches add functions to the views you already know: anything this series doesn't mention works as in Novation's manual."
3. **Versions.** *Show:* the installer's version list. *Say:* "There are three kinds of build. The RC is the stable one, the one to use for music. The RC with an S at the end is the safer twin: it writes nothing of its own to the card, so the functions that save patches, samples or copies do nothing there. The Beta has the newest features first, and is less tested. When a feature in this series is Beta-only, you'll see it on screen."
4. **Back up first.** *Show:* the card's copy on the computer. *Say:* "Before installing, copy your card. And with the versions without an S, keep your projects on a pack on the card, not in the internal memory: the mod never writes into the internal pack anyway."
5. **Install.** *Show:* the installer: pick the official firmware file, pick the version, send; the device restarts. *Say:* "The installer patches the official firmware right in the browser and sends it over USB. Pick the version and send. Novation's bootloader is never touched. *Check for new builds* adds builds published after your copy of the page."
6. **Going back.** *Show:* sending the official firmware; then the three buttons. *Say:* "To go back, send another version or the official firmware. If the device ever doesn't start, hold Scales, Preset and Note while you switch it on: that's Novation's own recovery mode, and from there you can install any firmware."
7. **Conventions.** *Show:* the pad map overlay. *Say:* "In this series, pads go from 1 to 32 from the top left, eight per row. K1 to K4 are the top knobs, K5 to K8 the bottom ones. 'Shift plus pad' means hold Shift and press the pad. And a rule that holds everywhere: while you hold Shift, what Shift offers lights yellow."
8. **Outro.** *Say:* "Next: the buttons that work in every view."

**Keep in mind**
- Installing restarts the device: whatever is not saved is lost; the project, the pack and the settings stay.
- Projects and packs saved with the mod open on the official firmware: the mod's data sits in parts of the files the original doesn't read.
- An S build is the right choice for anyone who only wants the new playing features and nothing written to the card.

---

## 01 · Buttons that work in every view

**Guide:** [0.2](GUIA.en.md#botones) · **Length:** about 7 min

**Before recording**
- The `TUTORIAL` project playing; automation recorded on one drum knob and on a Synth 1 macro.

**In this video**
- Clear + knob: back to the default, or erase the automation.
- Clear + a track button.
- Metronome and count-in (Shift + Clear).
- Quantize (Shift + Play).
- Double presses and the split keyboard.
- [Beta] The track buttons flash with the notes; Shift + Preset; [Beta, unreleased] putting a pattern back as the card has it.

**Script**

1. **Intro.** *Say:* "A few gestures work almost everywhere. Learn these and the rest of the series gets easier."
2. **Clear + knob.** *Show:* in a drum's view, hold Clear, turn K1 to the right: lavender; turn K5 to the left: red. *Say:* "Hold Clear and turn a knob to the right: it goes back to its default, and the LED turns lavender, as on the original. To the left, on a knob with automation, you erase that knob's automation in the pattern that's playing: the LED goes red. This works on the drums, on the MIDI tracks' synth engine and, to the right only, in Master FX."
3. **Clear + a track button.** *Show:* move Synth 1's macros, then Clear + Synth 1; then Clear + Drum 1. *Say:* "Clear plus Synth 1 or 2 puts its eight macros back to the loaded patch. Clear plus a drum's button erases the automation of its knobs in the playing pattern and puts its eight knobs back to their defaults."
4. **Metronome and count-in.** *Show:* Shift + Clear four times, watching the Clear LED; then Record armed + Play. *Say:* "Shift plus Clear steps through four states: no metronome, red; metronome, green; count-in only, magenta; both, teal. With the count-in on, arm Record and press Play: you get one bar of clicks, Record blinks, and recording starts on the downbeat. Press Play during the count to cancel it. The click's volume is the stock one: Tempo/Swing, K5." [Beta] *Say:* "With the click's volume at zero, Clear flashes orange on every click: a silent count-in."
5. **Quantize.** *Show:* record a few late notes; hold Shift (Play yellow) and press Play (Play green). *Say:* "Shift plus Play quantizes the pattern of the selected track: notes recorded on the first two micro steps go to the start of their step, later ones to the next step. On the drums, a step with several hits, a roll, stays as it is."
6. **Double presses.** *Show:* Scales twice; Velocity twice; Synth 1 twice; MIDI 1 twice; Mixer twice. *Say:* "Press a button twice for its second function: Scales opens the custom scale editor, Velocity toggles fixed velocity, Synth opens the synth's source view, MIDI opens its Preset view, and Mixer opens Master FX. Shift plus Synth or MIDI does the same from any view." [Beta] *Show:* hold Mixer in the Mixer. *Say:* "In the Beta, holding Mixer for half a second shows Master FX only while you hold it."
7. **Split keyboard.** *Show:* hold Synth 1, press Synth 2; play both halves; hold Drum 1 and turn a knob. *Say:* "Hold one note track's button and press another: the top two rows play the first one, the bottom rows the other, each with its own scale and octave. The knobs belong to the first, but hold any track button and the knobs are that track's until you let go. A short tap on a track button closes the split."
8. **[Beta] Shift shows what plays.** *Show:* hold Shift while the pattern plays. *Say:* "In the Beta, holding Shift makes each track button flash white on every note its track plays."
9. **[Beta] Back to the project's sound.** *Show:* tweak Synth 1, then Shift + Preset. *Say:* "Shift plus Preset puts that track's sound back to the one the project saved."
10. **[Beta, unreleased] Back to the saved pattern.** *Show:* edit a pattern, Clear + Duplicate (Duplicate blinks white), Clear + Duplicate again. *Say:* "In any view of a track, Clear plus Duplicate asks, and Clear plus Duplicate again puts the pattern back as the card has it from the last Save. If Save flashes red, nothing was done: the project was never saved, or a save is still pending."
11. **Outro.** *Say:* "Now the views, starting with Setup."

**Keep in mind**
- Clear first, then Shift: Shift + Clear is the metronome.
- The count-in is saved with the project; the click on / off is not, as on the original.
- Shift + Play replaces the original's Shift + Play (another way to start playback).
- Scales + Preset + Note at power-up is Novation's recovery mode, not a mod gesture.

---

## 02 · Setup view

**Guide:** [1.1](GUIA.en.md#setup) · **Length:** about 6 min

**Before recording**
- An external synth or a computer receiving MIDI, to show Program Change and General MIDI notes.

**In this view**
- Shared channels: a MIDI track playing the device's own synths or drums.
- The reverb and delay returns through mixer strips 3 / 4.
- Program Change channels (pads 29 / 30).
- Recording the internal routings (Record).
- The external keyboard into the arpeggiator (Note).
- General MIDI drums (K4-K8).
- [Beta] Knob hold (Preset) and velocity → amplitude / filter (K1 / K2).

**Script**

1. **Open it.** *Show:* open Setup as on the original. *Say:* "Setup holds the MIDI channels and device options, as always, plus a few new ones."
2. **Shared channels.** *Show:* MIDI 1's button, then the pad of Synth 2's channel; play MIDI 1's pattern. *Say:* "Give MIDI 1 or 2 the same channel as a synth or the drums, and what the MIDI track sends reaches that track inside the device: a MIDI track can play Synth 2, for example. Pad 16 is channel 16, the project's and the effects' channel."
3. **Returns through strips 3 / 4.** *Show:* pad 22 (cream) and pad 23 (peach); then the Mixer. *Say:* "Pads 22 and 23 send the reverb return through mixer strip 3 and the delay return through strip 4: the effects become channels you can level and pan."
4. **Program Change channels.** *Show:* touch pad 29: pads 1-16 white, pick one; the same with pad 30. *Say:* "Pad 29 is the channel the project listens to for Program Changes; the first touch shows it on pads 1-16, a pad picks it, another touch turns it on or off. Pad 30 does the same for the output channel. Both start on 16, and what arrives on the listen channel is sent on the output one."
5. **Record the routings.** *Show:* Record yellow; a MIDI track changing a synth's notes on a shared channel. *Say:* "With Record yellow here, what a MIDI track sends to a synth over a shared channel is also recorded into that synth. It's off by default and goes off after a restart. While it's on, a note track muted in the Mixer records nothing: you can keep a bank of chords there that only plays the synth."
6. **External keyboard to the arpeggiator.** *Show:* Note green; play a chord on an external keyboard. *Say:* "Note green means notes from an external keyboard, on a track's channel, go through that track's arpeggiator like the pads do. It's off by default so it doesn't clash with a keyboard that has its own arpeggiator." [Beta] *Say:* "In the Beta, with a step held, the external keyboard's notes go into that step."
7. **General MIDI drums.** *Show:* K4 to the right (green); turn K5: the number on the pads and the drum sounds; press Shift to confirm. *Say:* "K4 turns on General MIDI for the drums: every hit goes out over MIDI with a GM note instead of the stock one. K5 to K8 pick the note of Drum 1 to 4: each new note sounds once and its number shows on the pads. Shift, or leaving Setup, confirms it. Inside the device, the drums sound the same."
8. **[Beta] Knob hold.** *Show:* Preset green; turn a Mixer knob and switch view mid-turn. *Say:* "In the Beta, Preset here turns on knob hold: a knob you're turning keeps doing what it did, even if you change view or press Shift, until you leave it still for a second."
9. **[Beta] Global velocity.** *Show:* K1 up; soft and hard notes on a patch without amp velocity. *Say:* "K1 gives velocity to the volume of patches that have none, and K2 to their filter. At zero, the original's behaviour. A patch that already uses velocity is not changed."
10. **Outro.** *Say:* "Next: Advanced Setup."

**Keep in mind**
- Everything here is a **device setting**: the same for every project.
- General MIDI only changes what goes out over MIDI.
- Patch flip always goes out on its MIDI track's own channel.
- Record (internal routings) is off again after every restart.

---

## 03 · Advanced Setup view

**Guide:** [1.2](GUIA.en.md#advanced-setup) · **Length:** about 4 min

**Before recording**
- The device off. Advanced Setup opens only at power-up (hold Shift while you switch it on, as on the original).

**In this view**
- The MIDI Thru jack: Thru, Out 2, Merge, Filter (Duplicate).
- USB merge (pad 23).
- Delayed save (pad 22).
- The pads' velocity curve (K1; RCs only).
- [Beta] External input gain (K3).

**Script**

1. **Open it.** *Show:* switch on holding Shift. *Say:* "Advanced Setup only opens at power-up. Besides the stock settings, there are four new things."
2. **Thru jack.** *Show:* Duplicate four times: dim red, green, yellow, blue. *Say:* "Duplicate cycles the MIDI Thru jack: Thru, a plain hardware thru; Out 2, a second output; Merge, the incoming MIDI plus the device's own; and Filter, the incoming MIDI without the channels the device listens to. Merge and Filter don't pass SysEx."
3. **USB merge.** *Show:* pad 23 green; a keyboard on DIN reaching the computer. *Say:* "Pad 23 sends what comes in on the DIN input to the computer over USB too, with the device's own MIDI. With Clock Tx on, the DIN clock isn't copied, so the computer doesn't get two clocks."
4. **Delayed save.** *Show:* pad 22 green; Save twice while playing: Save blinks yellow; stop: saved. *Say:* "Saving while the sequencer runs can make the clock stumble for a moment. With pad 22 on, a save while playing waits until you stop. Loading another project, or saving into another slot, saves it right then."
5. **Velocity curve (RC).** *Show:* turn K1: the number on the pads, Velocity lit. *Say:* "On the RCs, K1 sets the pads' velocity curve, from minus 8 to plus 8: to the right more sensitive, to the left harder. Zero is the original's response."
6. **[Beta] Input gain.** *Show:* turn K3: dB on the pads. *Say:* "In the Beta, K3 raises the external inputs by up to 24 dB, also what reaches the own synth and the granular. With a lot of gain, it clips. In the Beta the velocity curve is gone: velocity lives in Setup's K1 and K2."
7. **Outro.** *Say:* "The master compressor's attack and release are in the Sidechain view, video 25."

**Keep in mind**
- All of these are device settings, saved on their own.
- With a save pending, stop the transport before switching off. If you change pack before stopping, that save is dropped.

---

## 04 · Synth 1 / 2 track view: Note, Velocity, Gate

**Guide:** [2.1](GUIA.en.md#synth-nota) · **Length:** about 9 min (chapters: playing / the chord screen / automation tools)

**Before recording**
- Synth 2 with a pad or keys patch; Synth 1 with a bass line that has macro automation on some steps.

**In this view**
- The split keyboard with any pair of note tracks.
- Latching notes (Shift + key) and writing them into a step.
- The chord screen.
- Velocity view: steps that let go of the automation.
- [Beta] Previewing and erasing a step's automation, sweeps, and the snapshot of the macros into a step.

**Script**

*Chapter 1: playing*

1. **Intro.** *Say:* "The synth's track view plays as always. Here's what's new."
2. **Source view shortcut.** *Show:* Synth 1 pressed again. *Say:* "Pressing the track's button again opens the synth's source view. That's video 6."
3. **Split keyboard.** *Show:* hold Synth 1, press MIDI 1; play; hold Drum 2 and turn a knob. *Say:* "Hold a note track's button and press another: Synth 1, Synth 2, MIDI 1 or MIDI 2, any pair. The track you held first plays on top. Holding any track button lends you its knobs while you hold it."
4. **Latch.** *Show:* Shift + a key; let go: it keeps sounding; press it again: it stops. *Say:* "Shift plus a key latches the note: it keeps sounding after you let go. The next press of that note stops it. While you hold Shift, latched notes show bright teal."
5. **Latched notes into a step.** *Show:* two latched notes; Shift + step 5 in the Note view. *Say:* "With notes latched, Shift plus a step writes them into that step: one step long, velocity 100. Clear plus the track's button lets go of everything latched."

*Chapter 2: the chord screen*

6. **Open it.** *Show:* Note twice (expanded Note view), Shift + pad 8: green. *Say:* "In the expanded Note view, Shift plus pad 8 opens the chord screen."
7. **The rows.** *Show:* row 1 types; Shift + row 1 for more; pads 9-12 inversions; pads 13-15 modifiers; rows 3-4 roots. *Say:* "Row 1 is the chord type: major, minor, seventh and more; with Shift, seven more, like sus2 or add9. Pads 9 to 12 are the inversion. Pad 13 opens the voicing, pad 14 adds the root an octave down, pad 15 builds the chord from the project's scale. Rows 3 and 4 are the roots, laid out like the Note view's keyboard."
8. **Live changes.** *Show:* hold a root and change the type and inversion. *Say:* "Change the type or the inversion while a chord sounds and it changes at once: no need to press the root again. Two chords at once share their common notes."
9. **Chord latch and recording.** *Show:* Shift + a root (teal); Record a few chords; play back without the screen. *Say:* "Shift plus a root latches the whole chord. What you play is recorded as plain notes, so it plays back the same without the chord screen. With the arpeggiator on, one finger plays an arpeggiated chord." [Beta] *Show:* pad 16. *Say:* "In the Beta, pad 16 is the inverse chord: the chord mirrored downwards from the root."

*Chapter 3: automation tools*

10. **Steps that let go of the automation.** *Show:* Velocity view, hold Shift: the step pads yellow; Shift + a step: red. *Say:* "In the Velocity view, Shift plus a step marks it red: on that step no automation plays, and everything the automation had moved goes back to the project's values: the patch's macros as the project saved them. Press it again to unmark. Saved with the pattern."
11. **[Beta] Preview and erase.** *Show:* hold Shift: only the steps with automation are yellow; Shift + a yellow step; let go of Shift; Clear + a step. *Say:* "In the Beta, with Shift, only the steps with automation are yellow. Shift plus a yellow step puts its automation on the knobs and into the sound, and letting go of Shift puts everything back. Clear plus a step erases its knob automation and keeps its notes."
12. **[Beta] Sweep.** *Show:* hold a yellow step and press another yellow step. *Say:* "Hold one yellow step and press another: every lane with a value at both ends becomes a straight line between them."
13. **[Beta] Snapshot.** *Show:* move two macros; Record held + step 9 (it lights yellow). *Say:* "Record held plus a step writes into that step the macros that are not where the patch keeps them, each into its lane."
14. **Outro.** *Say:* "Next: scales, and making your own."

**Keep in mind**
- The chord screen's type and modifiers, latched notes and the split keyboard are not saved.
- "The project's values" means the patch as the project saved it: turning knobs later doesn't change it; choosing another patch does.
- On MIDI 1 / 2 in the sample mode, the expanded Note view is the sample picker, not the chord screen.

---

## 05 · Scales view, custom scale and Jankó

**Guide:** [2.2](GUIA.en.md#escalas) · **Length:** about 6 min

**Before recording**
- A short melody on Synth 1 and random-mutate on a few steps (to show the scale driving it).

**In this view**
- The custom scale: up to 7 notes and a free period.
- How the note tracks lay it out.
- Jankó, an isomorphic keyboard.

**Script**

1. **Open the editor.** *Show:* Scales twice (or Shift + Scales). *Say:* "Scales works as always: root and stock scales. Press it twice, or Shift plus Scales, and you get the custom scale editor."
2. **The keyboard.** *Show:* pad map: row 4 white keys, row 3 black keys, rows 2 / 1 the second octave. *Say:* "The editor is two octaves of piano from the root: the bottom row is the first octave's white keys, the row above its black keys, and the top two rows the second octave."
3. **Build a scale.** *Show:* press keys: green notes, white root, blue period. *Say:* "Press up to seven keys. The highest one is the period: where the scale starts again. It doesn't have to be the octave. A scale that repeats every seven semitones, say, is fine."
4. **On the note tracks.** *Show:* Synth 1's Note view. *Say:* "On the note tracks every row is one pass of the scale, ending on the period note. With four notes or fewer, two passes fit in a row. Octave moves one row."
5. **What it drives.** *Show:* the sequence lighting the right keys; random-mutate staying in the scale. *Say:* "The custom scale also decides which keys light up as the sequence plays, the quantising, and which notes random-mutate can pick."
6. **Back to stock.** *Show:* pick a stock scale; back to the editor: the keys are kept. *Say:* "Picking a stock scale switches the custom one off, but keeps your keys: open the editor and it's back. It's saved with the project."
7. **Jankó.** *Show:* in the editor, Shift + pad 8 (teal); then the Note view; play the same chord shape in two keys. *Say:* "Shift plus pad 8 in the editor turns on Jankó: every column goes up a whole tone, and the rows come in pairs, the upper one a semitone lower. A chord has the same shape in every key. Octave: a tap moves a semitone, holding it for half a second moves an octave."
8. **[Beta] Moving one pair.** *Show:* expanded Note view, hold a key, press Octave. *Say:* "In the Beta's expanded Note view, the upper pair repeats the lower one, and with a key held, Octave moves only the other pair. Holding keys in rows 2 and 4 moves only rows 1 and 3."
9. **Outro.** *Say:* "Next: the synth's source view."

**Keep in mind**
- A new project starts without a custom scale.
- In the RCs, Shift + pad 24 in the editor turns on an older layout (each row a semitone above the one below).
- The distance between Jankó pairs is not saved: it is 0 after a restart.

---

## 06 · Synth source view

**Guide:** [2.3](GUIA.en.md#synth-fuente) · **Length:** about 5 min

**Before recording**
- A guitar, voice or drum loop into audio input 1. A Synth 1 patch with some noise level (CC 56) and a filter envelope.

**In this view**
- The audio inputs as the synth's noise source (pads 25-29). [Beta] Gone in Alpha 7.04: pads 25-29 are dark and do nothing.
- The macro destination editor (pad 32).
- The synth's step-drummer (pad 30).

**Script**

1. **Open it.** *Show:* Synth 1's view, press Synth 1 again (or Shift + Synth 1 from anywhere). *Say:* "Press a synth's button twice and you're in its source view. Any button closes it." [Alpha, unpublished: Shift + Synth 1 again also closes it, to the Note view.]
2. **Audio in as the noise.** *Show:* pad 26; play notes: the input gated and filtered. *Say:* "Pads 25 to 29 replace the patch's noise: 25 is the noise itself, 26 and 27 the two audio inputs, 28 and 29 the same inputs inverted. Now the synth's filter, envelopes and effects shape your outside signal, in time with the notes."
3. **The catch.** *Show:* the noise level macro at zero: silence; up: sound. *Say:* "The patch needs some noise level for this to be heard. The choice is saved with the project. If Setup routes the reverb or delay returns through strips 3 and 4, that's what reaches the synth here."
4. **Macro destinations.** *Show:* pad 32 (teal); turn macro K1 (white LED); Octave ▼ through the fields; the pads drawing numbers. *Say:* "Pad 32 opens the macro editor. Turn a knob to pick its macro: the first turn changes nothing. Each macro has four slots, and each slot has a destination, a start, an end and a depth. Octave moves between fields: slot, start, end, destination, depth. The pads draw the number."
5. **Hear it and keep it.** *Show:* turn the macro: the new destination moves. *Say:* "Changes sound at once. To keep them in the pack, save the patch from the Preset view: that's the next video."
6. **The synth's step-drummer.** *Show:* pad 30; pad 17 = macro 1; turn K1-K8. *Say:* "Pad 30 opens the synth's step-drummer: pads 17 to 24 pick which macro it moves, and the eight knobs set that macro on eight pairs of steps. Play and Record don't close it, and if you leave, pressing Synth 1 brings it back. It works like the MIDI tracks' step-drummer in video 15."
7. **Outro.** *Say:* "Next: the synth's Preset view."

**Keep in mind**
- The destination list walks the 31 parameters with a CC first, then the 39 with an NRPN only.
- The step-drummer writes its values as automation: they are part of the pattern.

---

## 07 · Synth 1 / 2 Preset view

**Guide:** [2.4](GUIA.en.md#synth-preset) · **Length:** about 7 min (chapters: saving and copying / [Beta] categories / [Beta] patch morph)

**Before recording**
- A pack on the card with free patch slots, and a second pack to copy into.

**In this view**
- Saving a patch from the device.
- Swapping and copying patches, also to another pack.
- [Beta] Colours by Components category.
- [Beta] Patch morph.

**Script**

*Chapter 1: saving and copying*

1. **Intro.** *Say:* "The original can only save patches from Components. Here you save them on the device."
2. **Save.** *Show:* tweak the sound; Clear + a pad: it blinks white; Clear + the same pad: saved. *Say:* "Clear plus a pad asks; Clear plus the same pad within five seconds saves the sound as it is now: knobs, received MIDI, macro destinations. Another pad moves the question."
3. **Swap.** *Show:* Duplicate + pad A + pad B. *Say:* "Duplicate plus two pads swaps two patches in this pack."
4. **Copy to another pack.** *Show:* Duplicate + A; load another pack; Duplicate + B. *Say:* "To copy a patch to another pack: Duplicate plus the patch, load the other pack, then Duplicate plus the slot. The source pack doesn't change."

*Chapter 2: [Beta] categories*

5. **Colours.** *Show:* the Preset view in colour. *Say:* "In the Beta, each patch shows in the colour of its Components category: bass steel blue, lead yellow, pad blue, and so on. Empty slots are dim white."
6. **Pick the category when saving.** *Show:* Clear + pad; turn K1 through the categories; confirm. *Say:* "While a save asks, K1 picks the category. Confirm and it's saved with it."

*Chapter 3: [Beta] patch morph*

7. **Enter.** *Show:* hold three patches for half a second. *Say:* "Hold two to four patches for a moment and the morph view opens: the sound moves through the patches you held, in pad order."
8. **The knobs.** *Show:* K1 sweep; K2 and K3; K4; K7 / K8 with pads 1 / 8. *Say:* "K1 is the position along the chain. K2 adds a square LFO and K3 sets the speed of both LFOs; K4 is a random-step LFO. K7 and K8 are an envelope: pads 1 and 8 trigger it, and holding them holds it."
9. **Slow morph.** *Show:* turn K5 and leave it; K6 for the length. *Say:* "K5 is a slow morph's destination: leave it still for half a second and the sound travels there over K6's time, from instantly up to 32 bars. K1 and K5 show the patches as colours: red, yellow, green, blue."
10. **Leaving and coming back.** *Show:* pad 32; Preset; the track button. *Say:* "Pad 32 leaves. Preset shows the patches, with the chain in white. The morph keeps going in other views; the track button brings the morph view back. One morph at a time: starting one on another track stops the first."
11. **Outro.** *Say:* "That's the stock synths. Next: the MIDI tracks' own synth."

**Keep in mind**
- Saving *writes to the card*: not in S builds, not on the internal pack (Save turns red).
- A saved patch keeps the name of the patch that was loaded.
- Patch colours on the RCs are the original's: the track colour, the chosen one white.
- [Beta] The morph is not saved; continuous parameters blend, type parameters (wave, mode) take the nearest patch's.

---

## 08 · MIDI 1 / 2 Preset view: the own synth

**Guide:** [3.1](GUIA.en.md#midi-preset) · **Length:** about 12 min (chapters: engines and pages / patches / voice modes / patch flip and the jump sequencer)

**Before recording**
- MIDI 1 with a short melody. A pack with a few own-synth patches saved, one empty slot, and a second pack.
- An external keyboard on MIDI 1's channel, for the last chapter.

**In this view**
- A synth inside each MIDI track, with several engines.
- The knob pages, the voice mode and the chain order.
- Own-synth patches: 128 slots per pack.
- Patch flip; [Beta] the jump sequencer.
- Playing the own synth from an external keyboard.

**Script**

*Chapter 1: engines and pages*

1. **Intro.** *Say:* "MIDI 1 and MIDI 2 still send MIDI to your gear. Now each also has a synth inside the device, and it lives in this view."
2. **Open it.** *Show:* MIDI 1, then Preset; then MIDI 1 twice from its Note view. *Say:* "Press MIDI 1, then Preset. Or press MIDI 1 twice, or Shift plus MIDI 1 from anywhere."
3. **The engine row.** *Show:* tap pad 27: the row on pads 17-24; pick the oscillator (green); pad 27 again closes the row. *Say:* "A tap on pad 27 opens the engine row: off, line input, oscillator, VA-drum, granular, sample, FX sequencer and, on pad 24, FM. Pick one; pad 27 again brings the patch list back." [Beta] *Say:* "In the Beta the row is: no voice; 'VCA / VCF / FX only', which is the line input; then oscillator, VA-drum, wavetable, sample, granular and FM. The FX sequencer moves to pad 31."
4. **What each engine is.** *Show:* a few notes on each engine. *Say:* "Line input runs your audio input through the filter and VCA, triggered by the notes. The oscillator morphs from sine to square, with a second oscillator. The VA-drum is for percussive hits. Granular plays grains of a sample. Sample mode plays a pack sample at the note's pitch. FM is a four-operator FM synth. And the FX sequencer makes no sound: it triggers Master FX slots on its steps."
5. **Knob pages.** *Show:* pads 1-5 and 6; hold pad 3 for half a second and let go. *Say:* "Pads 1 to 5 pick what the knobs do: filter and VCA, oscillator 1, oscillator 2, the sequenceable knobs, and modulation. Pad 6 is the mod matrix. Hold a page pad for half a second and that page shows only while you hold it. Clear plus a page pad puts that page back to its defaults." [Beta] *Say:* "In the Beta, pads 1 and 4 swap places: pad 1 is the sequenceable knobs."
6. **Pads 28-31.** *Show:* each pad. *Say:* "Pad 28 adds the second oscillator. Pad 29 swaps the order of the chain: VCA, effect, filter, or filter first. Pad 30 opens the step-drummer, and Shift plus pad 30 turns it off. Pad 31, on the VA-drum, makes velocity drive its pitch and filter envelopes."

*Chapter 2: own-synth patches*

7. **Load.** *Show:* touch pads in rows 2-3: the tonic sounds; Octave through the pages; Shift + a pad. *Say:* "Rows 2 and 3 are patch slots for this synth: sixteen a page, eight pages with Octave, 128 a pack, shared by MIDI 1 and MIDI 2. Touch a slot to load it; the tonic sounds while you hold it. Shift plus a slot loads it silently."
8. **Save.** *Show:* Clear + an empty slot, Clear + the same slot. *Say:* "Clear plus a slot, twice, saves the sound there: the engine, every value, the voice mode, the matrix."
9. **Swap and copy.** *Show:* Duplicate + A + B; then Duplicate + A, another pack, Duplicate + B. *Say:* "Duplicate plus two slots swaps them. To copy a patch to another pack: Duplicate plus the patch, load the other pack, Duplicate plus a slot. Duplicate stays yellow while a copy waits."
10. **Start over.** *Show:* Clear + MIDI 1. *Say:* "Clear plus MIDI 1 puts every value of the engine back to its default; the engine itself stays."

*Chapter 3: voice modes*

11. **The row.** *Show:* tap pad 32: the modes on pads 17-24. *Say:* "Pad 32 opens the voice modes: retrigger, legato, glide, four unison modes, and poly. Modes with the same name share a colour."
12. **Hear them.** *Show:* legato, glide with K1, uni retrig with K2, poly with a chord. *Say:* "Legato only changes pitch while you hold notes. Glide slides between held notes; K1 sets the time. The unison modes stack the voices on one note; K2 spreads them. Poly plays up to four notes, six in FM."
13. **Saved.** *Say:* "The mode, the glide time and the detune are saved with the patch and the project. Shift plus pad 29 steps through the modes from the main view."

*Chapter 4: patch flip and the jump sequencer*

14. **Patch flip.** *Show:* pad 26 on; play notes to an external synth. *Say:* "Pad 26 turns every note of the track into a Program Change on the track's channel: your outside gear changes sound step by step. It excludes the engine."
15. **[Beta] Jump sequencer.** *Show:* pad 26 opens the flip view; pad 18 (step flip); pick Synth 1 on row 2; in MIDI 1's Note view, pads 17-32 = steps. *Say:* "In the Beta, pad 26 opens the flip view: pad 17 is patch flip, pad 18 step flip. With step flip, row 2 picks a target track. Now MIDI 1's notes don't sound: each one makes the target's pattern jump to a step. In MIDI 1's Note view, pads 17 to 32 are steps 1 to 16. Stopped, a pad lets you hear that step of the target."
16. **[Beta, unreleased] Random jumps.** *Say:* "With several notes on one step, the jump goes to one of their steps at random, each with the same chance."
17. **External keyboard.** *Show:* play the external keyboard on MIDI 1's channel. *Say:* "An external keyboard on MIDI 1's channel plays the own synth directly."
18. **Outro.** *Say:* "Next: how many voices the own synth has, and what happens when it runs out of time."

**Keep in mind**
- The engine's settings are kept in the device settings and, since RC4, with each project. To reuse a sound anywhere, save it as a patch.
- Saving and copying patches *writes to the card*.
- With any engine on, the track still sends its MIDI.
- Patch flip and the engine exclude each other; [Beta] so do the jump sequencer and the engine.
- [Beta] Patch morph works here too, with the own synth's slots (video 07).

---

## 09 · Own-synth voices: polyphony and the voice limiter

**Guide:** [3.2](GUIA.en.md#midi-voces) · **Length:** about 5 min

**Before recording**
- MIDI 1 own synth on FM in poly, with a long-release patch; Synth 1 playing chords.

**In this video**
- How many voices each mode and engine has.
- Voice stealing and the chord level.
- The voice limiter, and why Synth 1 / 2 keep their voices.

**Script**

1. **Intro.** *Say:* "The own synth can play chords. Here's how many notes, and what the device does when the sound engine runs out of time."
2. **The counts.** *Show:* a table on screen. *Say:* "Retrigger, legato and glide: one voice. Poly: four voices on the oscillator, the VA-drum and the sample mode; six in FM, or three each if MIDI 1 and MIDI 2 are both on FM poly. The unison modes use those same voices on one note. Granular: always one voice."
3. **Stealing.** *Show:* play five notes in poly. *Say:* "One note too many takes the voice of the oldest note, with a 2-millisecond fade. A released note keeps its voice while its release rings: with long releases, voices fill up even with single notes."
4. **Chord level.** *Show:* a single note, then a four-note chord. *Say:* "Each voice is turned down by how many are sounding, so chords don't clip: one or two notes at full level, four at about 0.7. A chord is louder than a note, but not four times louder."
5. **The limiter.** *Show:* FM pad with long releases and many notes; a release ending early. *Say:* "Everything that sounds shares the DSP's time. If it's about to run out, you'd hear a rattle. So with two or more own voices sounding, the device checks every 2 milliseconds; when time is short it switches off the quietest voice that's already releasing, or else the oldest held note. Then it plays with the voices that fit and tries one more every two seconds."
6. **Synth 1 and 2 are safe.** *Show:* Synth 1 chords under the own synth. *Say:* "Synth 1 and Synth 2 don't lose voices to the own synth: when time runs out, it's the own synth's voices that go."
7. **Tips.** *Say:* "For more voices: shorter releases, fewer loud operators in FM, or only one track on FM poly. The mono modes never reach the limiter." [Beta] *Say:* "In the Beta, FM voices are computed separately from the rest: six per track even with both tracks on FM, about ten FM voices in all."

**Keep in mind**
- What you hear from the limiter is a long release ending early, or the oldest note of a chord going away when a lot is sounding.
- How many voices fit depends on the whole project: Master FX, many drums and heavy Synth 1 / 2 patches leave less time.

---

## 10 · The engine's knob pages

**Guide:** [3.3](GUIA.en.md#midi-knobs) · **Length:** about 10 min (chapters: VCA-VCF / oscillators / granular / page 4 and automation / page 5)

**Before recording**
- MIDI 1 own synth on the oscillator, a short pattern playing; a pack sample for the granular.

**In this view**
- Page 1: VCA and filter, with their envelope and LFO.
- Pages 2 and 3: the two oscillators; SHAPE on each waveform.
- Page 2 on the granular.
- Page 4: the knobs you can record, and Shift + pad 4, those you can't.
- Page 5: envelope, LFO and the LFO's shape.

**Script**

*Chapter 1: VCA-VCF*

1. **Page 1.** *Show:* pad 1; K1-K8, then with Shift. *Say:* "Page 1 is the VCA and the filter. K1 and K2 are attack and release, with Shift sustain and decay. K3 and K4 send the envelope to the level and the filter; with Shift, the LFO. K5 is the filter, K6 resonance; Shift plus K5 picks the filter type, Shift plus K6 is a VCA gain with saturation. K7 is the LFO speed, K8 the effect amount, and Shift plus K8 the effect type: soft, hard, fold, wavefold, ring, comb, chorus."
2. **Synced LFO.** *Show:* K7 to the right, then to the left. *Say:* "K7 is bipolar: to the right, a free LFO; to the left, synced to the tempo, from a sixteenth-note triplet up to eight bars, restarting on the bar's first beat."

*Chapter 2: oscillators*

3. **Page 2.** *Show:* pad 2; WAVE (K7) through sine, triangle, saw, square; SHAPE (K2). *Say:* "Page 2 is oscillator 1: tune and fine, then WAVE, which morphs from sine to triangle to saw to square, and SHAPE, which does something different on each wave." [Beta] *Say:* "In the Beta the knobs are laid out differently: WAVE is K3, SHAPE is K4, and K5, K6 and K8 send the LFO and envelope to FM, ring and mix."
4. **SHAPE.** *Show:* SHAPE on the sine (wavefold), on the saw (supersaw), on the square (pulse width). *Say:* "On the sine, SHAPE to the right folds the wave: more harmonics. On the triangle, to the left, sharp exponential ramps. On the saw, from a plain saw fully left to a seven-saw supersaw fully right. On the square, the pulse gets narrower either way."
5. **Page 3, oscillator 2.** *Show:* pad 28 on; pad 3; FM, ring, sync. *Say:* "With pad 28 on, page 3 is oscillator 2: its tune, shape, wave, the mix between the two, and how they interact: FM, ring and a sync zone. Two notes held: oscillator 2 plays the second one."

*Chapter 3: granular*

6. **The granular page.** *Show:* granular engine; K2 position, K3 scan, K4 grain size, K5 density; Shift + K8 the source. *Say:* "On the granular engine, page 2 controls the grains: K1 pitch, K2 where in the sample, K3 scan, which freezes at the centre, K4 the grain size, K5 how many grains. Shift plus K8 picks the source: the capture, or a drum's sample."
7. **Note modes.** *Show:* Shift + K6: pitch, slicer, stretch. *Say:* "Shift plus K6 picks what the notes do: change the pitch, play one of sixteen slices, or stretch: the sample lasts K3's number of steps at any tempo, without changing pitch."
8. **Stereo grains.** *Show:* Shift + K4 up; the track's pan. *Say:* "Shift plus K4 spreads the grains in stereo; the track's pan in the Mixer sets the balance."

*Chapter 4: page 4 and automation*

9. **Sequenceable knobs.** *Show:* pad 4; record knob moves with Record + Play. *Say:* "Page 4 holds the eight knobs that can be recorded into the pattern: tune, release, the two envelope amounts, filter, resonance, LFO speed and the effect."
10. **Choosing what they move.** *Show:* Shift + K5; the pads showing where the destination lives. *Say:* "Shift plus a knob changes its destination, to any of the engine's 33 parameters, in that parameter's page colour. While you pick, pads 9 to 24 show where it lives. Clear held, then Shift plus the knob, goes back to the factory one." [Beta, unreleased] *Say:* "In the newest betas this is Duplicate plus a knob of another page instead."
11. **Non-sequenceable knobs.** *Show:* Shift + pad 4 (pink). *Say:* "Shift plus pad 4 is a second set of eight assignable knobs that are not recorded: handy for attack, sustain or the VCA gain."
12. **Snapshot.** *Show:* in MIDI 1's Note view, Record held + step 5. *Say:* "In the track view, Record held plus a step writes into that step every parameter that's not at its initial value. A quick way to make one step sound different."
13. **[Beta, unreleased] Extra lanes.** *Say:* "In the newest betas, every other parameter of the engine gets its own lane too, two values per step, saved in the project's file."

*Chapter 5: page 5*

14. **Envelope and LFO.** *Show:* pad 5; Shift + K8 through the shapes. *Say:* "Page 5 has the envelope on top and the LFO below. Shift plus K8 picks the LFO's shape: reverse saw, saw, triangle, square, sine, sample and hold, and slewed sample and hold, each in its own colour."
15. **Outro.** *Say:* "Type knobs show the type as a colour and the position inside it as brightness. Everything here also goes out and comes in over MIDI. Next: the mod matrix."

**Keep in mind**
- The engine's values are kept with the device settings and, since RC4, with the project; the knob destinations and the LFO shape go with the own-synth patch too.
- Recording page 4 needs Record + Play, or a step held while you turn, as on the original.
- The FX amount and filter knobs act on the whole track, also in poly.

---

## 11 · Mod matrix

**Guide:** [3.4](GUIA.en.md#midi-matriz) · **Length:** about 6 min

**Before recording**
- MIDI 1 own synth on the oscillator, a pattern with varied velocities and notes.

**In this view**
- Eight modulation sources, each with one destination and an amount.

**Script**

1. **Open it.** *Show:* MIDI 1 Preset, pad 6 (light blue). *Say:* "Pad 6 turns the eight knobs into eight modulation sources: velocity, the note, a random value per note, a second LFO, a second envelope, a drum hit, the position in the pattern, and a stepped random value."
2. **One knob, destination and amount.** *Show:* turn K1 slowly to the right: the LED changes colour, brightness grows, then starts again. *Say:* "Here's the trick: the knob's position is both the destination and the amount. Turning right walks through all 33 parameters of the engine, one stretch each. Inside a stretch the amount grows from zero to full; in the next stretch the destination changes."
3. **Where it goes.** *Show:* pads 9-24 lighting while K1 turns. *Say:* "The LED takes the colour of the destination's page, and while you turn, the pads show exactly which knob it is: its page pad lights and its place on pads 9 to 24 is bright."
4. **Examples.** *Show:* K1 velocity → filter; K6 a drum hit → pitch; K7 pattern position → wave. *Say:* "Velocity opening the filter. Drum 1's hits bending the pitch. The pattern position sweeping the waveform over the bar."
5. **Shift layer.** *Show:* Shift + K4 (LFO 2 shape × rate); Shift + K5; Shift + K6; Shift + K8. *Say:* "With Shift, K4 sets LFO 2's shape and rate, synced on the left half of each shape. K5 sets envelope 2's attack and decay, K6 which drum and its decay, K8 how many steps between random values."
6. **Clearing.** *Show:* Clear + K1; Clear + pad 6. *Say:* "Clear plus a knob turns that source off; Clear plus pad 6 turns all of them off."
7. **Outro.** *Say:* "The matrix is saved with the own-synth patch and with the project."

**Keep in mind**
- Slow knobs: two clicks a step, 16 steps a destination.
- Several sources can share a destination: they add up. The parameter's own value doesn't change; the matrix is added when it is sent.
- The matrix has no CC / NRPN.
- Many fast sources at once update a little more slowly: they share the track's updates.

---

## 12 · 4-operator FM

**Guide:** [3.5](GUIA.en.md#midi-fm) · **Length:** about 6 min

**Before recording**
- MIDI 1 own synth; an RC build (the Beta replaces this engine with the 8-operator FM, video 13).

**In this view**
- An FM synth with 4 operators and 16 algorithms.
- Starter sounds on pad 8.
- Per-operator attack or percussive decay; one release for all.

**Script**

1. **Turn it on.** *Show:* pad 27, pad 24 (violet), then pad 7. *Say:* "FM is pad 24 of the engine row. Pad 7 opens its page."
2. **Starter sounds.** *Show:* hold pad 8: 16 instruments; press a few. *Say:* "Hold pad 8 for sixteen ready-made sounds: piano, electric piano, organ, plucks, bass, bell, strings, pad, winds, and drums. Press one to load it whole; it's a starting point you can save as a patch."
3. **Algorithms.** *Show:* hold pad 7: the 16 algorithms; press one. *Say:* "Hold pad 7 for the sixteen algorithms: classic stacks, percussive ones for kick, snare and hi-hat, bells and strings. Pressing one picks it and you hear it."
4. **The knobs.** *Show:* K1-K4 ratios (LED colours); K5-K8 levels. *Say:* "K1 to K4 are the four operators' ratios; green is a whole number, light blue a half, teal an inharmonic one. K5 to K8 are their levels: for a carrier, how loud; for a modulator, how much it modulates."
5. **Shift layer.** *Show:* Shift + K1 right (attack), left (percussive). *Say:* "With Shift, K1 to K4 shape each operator: to the right an attack, to the left the operator becomes percussive with its own decay. Shift plus K5 is the algorithm, K6 feedback, K7 noise, K8 the release, which is longer the harder you play."
6. **Brightness.** *Show:* page 2's SHAPE moving the timbre. *Say:* "SHAPE on page 2 and its envelope and LFO make the modulators stronger or weaker: the engine's envelope, LFO and the matrix all move the FM's timbre."
7. **Clear.** *Show:* Clear + pad 7. *Say:* "Clear plus pad 7 gives you a playable voice for the chosen algorithm."
8. **Outro.** *Say:* "The FM is saved with the own-synth patches."

**Keep in mind**
- The loudness comes from the operators' envelopes: the engine's VCA stays open; velocity still sets the level.
- High notes modulate less and decay sooner, as on classic FM synths.
- No CC / NRPN for the FM parameters.

---

## 13 · 8-operator FM [Beta]

**Guide:** [3.6](GUIA.en.md#midi-fm8) · **Length:** about 9 min (chapters: operators and envelopes / algorithms and the map / sounds and saving)

**Before recording**
- The Beta. MIDI 1 own synth on FM. A DX7 bank (`.syx`) on the computer, for the import mention.

**In this view**
- Up to 8 operators, each with a DX7-style envelope; 56 algorithms.
- The algorithm map: who modulates whom, at a glance; your own links.
- Instruments and example patches.

**Script**

*Chapter 1: operators and envelopes*

1. **Open the page.** *Show:* engine row pad 24, close the row (pad 27), pad 7. *Say:* "In the Beta, FM has up to eight operators. Pick FM on the engine row, close the row, and pad 7 opens its page."
2. **Pick an operator.** *Show:* pads 9-16: carriers green, modulators light blue. *Say:* "Pads 9 to 16 are the operators: carriers green, modulators light blue, the picked one bright."
3. **Its knobs.** *Show:* K1 ratio (3 clicks a step), K3 level, K5-K8 rates; Shift + K5-K8 levels. *Say:* "With an operator picked: K1 is its ratio, up to 31, then fixed frequencies in red. K2 fine, K3 output level, K4 velocity sensitivity. K5 to K8 are its envelope's four rates, and with Shift its four levels."
4. **How the envelope moves.** *Say:* "As on a DX7: it rises at rate 1 to level 1, then rate 2 to level 2, rate 3 to level 3, and stays there while you hold the note. On release it goes at rate 4 to level 4. Rate 99 is instant."
5. **Pitch envelope.** *Show:* pad 3 (violet). *Say:* "Pad 3 is the pitch envelope, like a ninth operator, plus noise."

*Chapter 2: algorithms and the map*

6. **The list.** *Show:* Shift + pad 7 held: three pages with Octave. *Say:* "Shift plus pad 7 held shows all 56 algorithms on three pages: the 4-operator ones, eight new 8-operator ones, and the DX7's 32."
7. **The map.** *Show:* tap pad 7: the map on pads 9-32. *Say:* "A tap on pad 7 shows the algorithm map. Each row reads left to right: the operator on the left modulates the one on its right, and the last one is a carrier. A dark gap means no connection."
8. **Colours on the map.** *Say:* "The colour tells the ratio: green a whole number, teal a half, orange inharmonic, red a fixed frequency; feedback is violet. Bright means a high output level."
9. **Mute and link.** *Show:* Shift + an operator (dark); hold one and tap another. *Say:* "Shift plus an operator mutes it while you look: you hear what it adds. Hold one operator and tap another: the first now modulates the second, or stops. That's your own algorithm, saved with the patch."

*Chapter 3: sounds and saving*

10. **Instruments.** *Show:* hold pad 8: instruments; Octave ▼ for page 2. *Say:* "Beta 5.56: hold pad 8 for 24 instruments, and with Octave a second page of pianos, strings, winds and long sounds. Loading one also sets the sequenceable knobs to suit its family." [Beta, unreleased] *Say:* "In the next betas the instruments leave the firmware: they come as example patches for the card app instead."
11. **Saving.** *Say:* "Each patch's FM is saved with the own-synth patches on the card, and with the project. Older 4-operator patches load converted, with the same sound."
12. **Import from a DX7.** *Show:* the card app, Custom patches, Import DX7…. *Say:* "The card app can import a DX7 bank: each voice becomes a custom patch on this engine."
13. **Outro.** *Say:* "That's the FM. Next: the CC editor of the MIDI templates."

**Keep in mind**
- The engine only computes the operators the algorithm uses: with 4, about 10 voices; with 6, about 6-7; with 8, about 5.
- Components' Send patches / Send pack put the own-synth patches back in each bank; a Components zip backup doesn't carry them: use the app's Snapshot.
- No CC / NRPN for the FM.

---

## 14 · CC editor of the MIDI macros

**Guide:** [3.7](GUIA.en.md#midi-cc) · **Length:** about 4 min

**Before recording**
- An external synth on MIDI 1, with a parameter you can see change (a filter).

**In this view**
- Changing which CC (or NRPN) each knob of a MIDI template sends, and its range, on the device.

**Script**

1. **Why.** *Say:* "The MIDI templates send fixed CCs, set in Components. Here you change them on the device."
2. **Open.** *Show:* MIDI 1 Preset, pad 25 (lit); move K1: its number drawn on the pads. *Say:* "Pad 25 opens the editor. Move a knob: it's picked and its CC number is drawn on the pads."
3. **Fields.** *Show:* Octave ▼ / ▲; turn K1 to change the value. *Say:* "Octave moves between fields: the number, the start and the end of the range. Turn the knob to change each one."
4. **NRPN.** *Say:* "Set the number to 99, 98 or 6 and the knob sends a 7-bit NRPN, with MSB and LSB fields; 38 gives a 14-bit NRPN."
5. **Save or discard.** *Show:* pad 26 (Save blinks); or a view button to discard. *Say:* "Pad 26 saves, or keep pressing Octave down to the save step. Any view button, pad 25 or a template pad discards your changes."
6. **Outro.** *Say:* "With the own synth on, the knobs send its own parameters instead, and pad 25 is dark."

**Keep in mind**
- The CC assignments live in the device's memory, with its templates, not on the card.
- The card app can read, edit and send all eight templates as a `.ctcc` file.

---

## 15 · Step-drummer view

**Guide:** [3.8](GUIA.en.md#step-drummer) · **Length:** about 6 min

**Before recording**
- MIDI 1 own synth with a 16-step pattern of single notes.

**In this view**
- Eight pairs of steps on the eight knobs, each moving a destination.
- A second page with its own destination; the pitch-vel toggle.
- Recording in real time; the FX sequencer.

**Script**

1. **Open.** *Show:* MIDI 1 Preset, pad 30 (or Note → expanded Note → step-drummer, since RC4). *Say:* "Pad 30 opens the step-drummer. Instead of drawing automation, you set a parameter on pairs of steps with the knobs."
2. **The layout.** *Show:* pads 1-16 steps; K1-K8 = pairs (the playing one white). *Say:* "Pads 1 to 16 are the steps: bright with a note, white while playing. Touch one to hear it; Shift plus touch adds or removes a note. Each knob is a pair of steps: K1 is steps 1 and 2, K2 steps 3 and 4, and so on. 1-16 / 17-32 shows the other half."
3. **Destination.** *Show:* pad 17 pitch; turn K3: the note moves on steps 5-6. *Say:* "Pads 17 to 24 pick what the pitch page moves: pitch, oscillator 2, WAVE, FM, MIX, envelope to filter, SHAPE or decay. The knob offsets it from the centre: at the middle, no change. The LED is dim with no change, brighter the further you go."
4. **Page 2.** *Show:* Octave ▼ (velocity page); pick a destination; turn knobs. *Say:* "Octave switches to the velocity page, which has its own destination: you can move the filter and the pitch on the same steps at once."
5. **Pitch-vel toggle.** *Show:* pad 32 (bright green); a melody from one note. *Say:* "Pad 32 is the pitch-vel toggle: page 1 now transposes the notes in degrees of your scale, one degree every eight knob steps, and page 2 sets their velocity. A melody from a single repeated note."
6. **Real time.** *Show:* Record + Play; touch steps. *Say:* "With Record on, touching a step records it on the step that's playing."
7. **FX sequencer.** *Show:* engine = FX sequencer; knobs pick Master FX slots (colours). *Say:* "With the FX sequencer engine, each knob picks a Master FX slot for its pair of steps: none, a slot, or random at the end of the travel. An empty slot plays the effect at the top of its column." [Beta, unreleased] *Say:* "And one more value at the very end: mute, in red. On that step the whole master goes silent."
8. **Outro.** *Say:* "On Synth 1 and 2, the same view opens from the source view and moves the macros."

**Keep in mind**
- The values are written as automation: they belong to the pattern.
- On MIDI 1 / 2, page 2 uses the release lane: with the step-drummer on, release is neither played nor recorded.
- Each step keeps the pitch of its first note.

---

## 16 · Sample mode and sample picker

**Guide:** [3.9](GUIA.en.md#midi-muestra) · **Length:** about 6 min

**Before recording**
- MIDI 1 own synth on the sample engine (teal); a pack with drum and one-shot samples; a stereo sample saved as two consecutive slots.

**In this view**
- A pack sample played at the pitch of each note.
- A different sample per step (sample flip).
- Stereo from two slots.

**Script**

1. **The engine.** *Show:* engine row: sample (teal); play the keyboard. *Say:* "Sample mode plays a pack sample one-shot, at the pitch of each note: note 60, middle C, is the sample as recorded, an octave up twice as fast."
2. **The picker.** *Show:* Note twice: rows 3-4 samples, Octave pages. *Say:* "Press Note twice for the sample picker: rows 3 and 4 are sixteen samples, Octave goes through the pack's 64. Touch one: it's the track's sample, and it sounds. Shift plus a sample picks it silently."
3. **Sample flip.** *Show:* hold step 3 + touch a sample: the step turns peach. *Say:* "Rows 1 and 2 are the steps. Hold a step and touch a sample: that step plays that sample, a sample flip. Or hold a sample and touch several steps. Clear plus a step removes it."
4. **Flips on empty steps.** *Show:* a flip on a step without a note: violet → a note is added. *Say:* "A flip on a step without a note adds the last note you played there, so it sounds. Peach: a note with a flip; teal: a note without; violet: a flip without a note."
5. **Live.** *Show:* Record + Play, touch samples. *Say:* "With Record on, touching a sample records a note with its flip on the playing step."
6. **Stereo.** *Show:* page 2, K7 (WAVE) up; Shift + the chosen sample (blinks teal), pick the second. *Say:* "K7 of oscillator page 1 is the stereo width: turned up, every note plays the chosen sample on the left and a second one on the right. Shift plus the chosen sample switches to picking the second. The device's samples are mono: a stereo sample is two slots in a row." [Beta] *Say:* "In the Beta the width is on K3."
7. **Outro.** *Say:* "The filter, effect and LFO of the engine still apply. Next: Pattern Settings."

**Keep in mind**
- One voice per track in the mono modes; poly gives up to 4 notes.
- The flips live in the track's level automation lane: recording the level over them erases them.
- The sample source is shared with the granular engine (Shift + K8 on its page).
- The capture always plays in mono.

---

## 17 · Pattern Settings view

**Guide:** [4.1](GUIA.en.md#pattern-settings) · **Length:** about 9 min (chapters: nudge and orders / the arpeggiator / its modifiers / the drums' arpeggiator)

**Before recording**
- Synth 2 with a pattern of held chords; Drum 1 with a pack whose first samples are a kit (kick, snare, hats).

**In this view**
- Nudge: shift the content of the selected steps.
- Fractal and deconstructed play orders.
- The arpeggiator of the note tracks and its modifiers.
- The drums' arpeggiator.

**Script**

*Chapter 1: nudge and orders*

1. **Intro.** *Show:* Pattern Settings with Synth 2: first / last step, sync rate, direction. *Say:* "Pattern Settings works as always: first and last step, sync rate, direction. The new things are on pads 25 to 28, and the arpeggiator lives under Shift."
2. **Nudge.** *Show:* tap pad 26 (blue) a few times; Shift + pad 26. *Say:* "Pad 26 is Nudge: a tap moves the content of the selected steps one step back, Shift plus pad 26 one step forward. What leaves one end comes in at the other, and the first and last steps stay where they are."
3. **Orders.** *Show:* pad 27, then pad 28; pads 29-32 switch them off. *Say:* "Pad 27 plays the pattern in fractal order: 1; 1 2; 1 2 3; and so on. Pad 28 is deconstructed: the grid's diagonals. They replace the stock direction pads, and the notes themselves don't change."

*Chapter 2: the arpeggiator*

4. **Turn it on.** *Show:* Shift + pad 25 (green with Shift); pad 25 green without Shift. *Say:* "Shift plus pad 25 turns on the arpeggiator of the pattern this track is playing. While it's on, pad 25 shows green."
5. **Order and resolution.** *Show:* Shift + pads 27-32; Shift + pads 17-24. *Say:* "Shift plus pads 27 to 32 pick the arpeggio's order: fractal, deconstructed, up, down, ping-pong, random. Shift plus pads 17 to 24 pick its resolution, from quarter notes to 32nd-note triplets, apart from the track's own rate. The same pad again goes back to the track's rate."
6. **What it does.** *Show:* the chord pattern now arpeggiated; hold two keys live. *Say:* "Chords in the pattern now play one note at a time, for as long as the chord lasts, each note with its own gate and velocity. Live, the first note sounds as always; hold another and the held notes are arpeggiated. With Record, the chord is recorded, not the single notes: the sequence arpeggiates it on playback."
7. **Order of notes.** *Say:* "Notes go in the order you pressed them, not by pitch; up, down and the others walk that order."
8. **Held step and keyboard.** *Show:* stopped, hold a step with a chord. *Say:* "Stopped, holding a step with several notes arpeggiates them. With Setup's Note button on, an external keyboard goes through the arpeggiator too."

*Chapter 3: its modifiers*

9. **The four groups.** *Show:* Shift + pads 1-16 with the arpeggiator on: sand, sky blue, amber, pink. *Say:* "With the arpeggiator on, Shift plus pads 1 to 16 pick four modifiers. Sand: the octave range. Sky blue: when the octave moves, after each pass or every few notes. Amber: the groove, dotted, swing, or every note twice. Pink: a reset after a pass plus a few notes, for shifting patterns."

*Chapter 4: the drums' arpeggiator*

10. **Drums.** *Show:* Drum 1's Pattern Settings, Shift + pad 25; Drum 1 Preset: hold three samples. *Say:* "The same gestures in a drum's Pattern Settings turn on its arpeggiator. Then in the drum's Preset view, hold several samples: the drum jumps from sample to sample at the arpeggio's rate. With Record, every hit is recorded with its sample as a sample flip."
11. **Outro.** *Say:* "Next: the Micro Step view."

**Keep in mind**
- The arpeggiator's settings are saved in the project per track and pattern number: duplicating a pattern does not copy them.
- Nudge and the orders work on the drums too; the order is saved with the pattern, and Clear on the pattern removes it.
- Clear + pad 25 clears the dynamics and random-mutate of every step of the pattern (note tracks); the frequency stays.

---

## 18 · Micro Step view

**Guide:** [4.2](GUIA.en.md#micropasos) · **Length:** about 4 min

**Before recording**
- Synth 1 with a few notes; the transport stopped.

**In this view**
- Micro steps and Tie, as on the original.
- Gate by holding: notes entered by hand last as long as you hold.
- Fixed length for every note entered by hand.

**Script**

1. **Open.** *Show:* Gate twice. *Say:* "Press Gate twice for the Micro Step view. Pads 17 to 22 are the six micro steps of the chosen step, pad 24 is Tie, and pads 25 to 30 are the step's notes, as on the original."
2. **Gate by holding.** *Show:* pad 32 green; hold a step + a note pad for a while, let go. *Say:* "Pad 32 turns on gate by holding: when you enter a note by hand, a step and a note held together, how long you hold is how long the note lasts, from one micro step up to sixteen steps."
3. **Fixed length.** *Show:* pad 31 → the selector on pads 17-32; pick 4; enter notes. *Say:* "Pad 31 is fixed length: with both off it opens a selector, sixteen lengths like the Gate view; pick one and every note you enter by hand gets that length, all the notes of a chord too."
4. **Switching.** *Show:* pad 31 again (off); pad 32 while 31 is on. *Say:* "Press the one that's on to turn it off. Press the other and they swap."
5. **Outro.** *Say:* "The arpeggiator uses these gates too: each note of a chord lasts its own."

**Keep in mind**
- Notes recorded live are not changed by either toggle.
- Both toggles are saved with the project, per track.
- One micro step per note, as on the original: for two positions in one step, enter two notes.

---

## 19 · Probability view

**Guide:** [4.3](GUIA.en.md#probabilidad) · **Length:** about 8 min (chapters: frequency / dynamics and random-mutate / [Beta] the new mode 2 / drums)

**Before recording**
- Synth 1 with a 16-step melody; Drum 3 with hats on every step.

**In this view**
- Frequency: a step that plays once every n passes.
- Random dynamics and random-mutate.
- [Beta] Mode 2 redesigned, with a factor per track.
- The same on the drums.

**Script**

*Chapter 1: frequency*

1. **Mode 1.** *Show:* Pattern Settings twice; hold step 4; row 3 (probability), row 4 (yellow). *Say:* "Press Pattern Settings twice for the probability view. Hold a step with notes: row 3 is the stock probability. Row 4 is new: frequency. Pick 4 and the step plays only on the last of every four passes. Variations that come back on a cycle."

*Chapter 2: dynamics and random-mutate*

2. **Mode 2.** *Show:* Pattern Settings, pad 25 (peach). *Say:* "Pad 25 of Pattern Settings opens mode 2. On the RCs, row 3 is random dynamics: small changes of velocity and position, eight levels. Row 4 is random-mutate: a chance that the note jumps an octave or to another note of the scale."
3. **Record or not.** *Show:* play with and without Record. *Say:* "Without Record, a mutation only changes that pass. With Record and this view on screen, what plays is written into the pattern: the sequence drifts, a little each pass."

*Chapter 3: [Beta] the new mode 2*

4. **One set of pads.** *Show:* Beta, mode 2: pads 17-24 (white, peach, sand), 25-28, 32. *Say:* "In the Beta, rows 3 and 4 work as one set per step. Pad 17: no changes. Pads 18 to 20: another note of the scale, more likely to the right. Pads 21 and 22: an octave up. 23 and 24: an octave up or down. Pad 25: no dynamics; 26: ghost notes, softer; 27: accent staccato, louder and shorter; 28: random length. Pad 32: micro-step shifts."
5. **The factor.** *Show:* Octave ▲ / ▼: the number on the pads. *Say:* "With this view open, Octave sets the track's factor: times 0, 1, 2, 4 or 8, which multiplies every chance. At times 8, pad 24 changes every note."

*Chapter 4: drums*

6. **Drums.** *Show:* Drum 3: Pattern Settings twice; pad 25 of its Pattern Settings. *Say:* "Drums get the same view. Mode 1: probability and frequency. Mode 2 on the RCs: dynamics, and on pads 25 to 28 random-mutate of the sample: the next sample of its row, or the same column in another row."
7. **Outro.** *Say:* "Next: the drums."

**Keep in mind**
- The frequency counters start again whenever the transport stops.
- Tied notes keep their note and length.
- On the drums, dynamics can only delay a hit inside its step (a drum can't play early), and the sample mutation is never recorded.
- The values are saved with each step; they travel when the pattern is duplicated or nudged.

---

## 20 · Drum track view

**Guide:** [5.1](GUIA.en.md#drum-pista) · **Length:** about 9 min (chapters: the knobs / starting over / the stereo pair / [Beta] automation tools)

**Before recording**
- Drum 1 with a kick sample, Drum 2 with a snare; a stereo sample as two consecutive slots in the pack.

**In this view**
- Every knob does what its label says, with a second layer on Shift.
- Clear + the drum's button to start over.
- Stereo pairs (Drum 1 + 2, Drum 3 + 4).
- [Beta] Snapshot, the extra lane, state locks and the automation view.

**Script**

*Chapter 1: the knobs*

1. **Intro.** *Say:* "On the original, the drum knobs do four things. Here each knob does what its label says, and Shift gives a second layer. With the new knobs at their neutral point, the sample sounds as on the original."
2. **K1 / K2.** *Show:* K1 pitch; Shift + K1; K2 / Shift + K2. *Say:* "K1 is the pitch, with Shift the pitch envelope's amount. K2 is a ring modulator's frequency, Shift its amount."
3. **K3, both ways.** *Show:* K3 left (decay), past the middle right (attack, white); Shift + K3 left (start), right (cut). *Say:* "K3 to the left is the decay; past the middle to the right, an attack, a fade-in. With Shift: to the left, where the sample starts; to the right, a cut from the end."
4. **Filter.** *Show:* K4; K5; Shift + K5 colours; K6. *Say:* "K4 sends the envelope to the filter, Shift sets the envelope's shape. K5 is the filter or EQ; Shift plus K5 picks its mode, shown by colour: green the stock tilt EQ, yellow band-pass, magenta notch, teal comb, white DJ filter. K6 is resonance." [Beta] *Say:* "In the Beta the comb mode is gone."
5. **K7 / K8.** *Show:* K7 right (tremolo), left (start scan); Shift + K7; K8, left of zero (bitcrush); Shift + K8. *Say:* "K7 to the right is a tremolo; to the left, each hit starts at a different place in the sample, following the LFO. Shift plus K7 is the LFO speed: right free, left synced to the tempo. K8 is distortion, and left of zero a bitcrusher; Shift plus K8 picks the distortion type."

*Chapter 2: starting over*

6. **Clear.** *Show:* Clear + K3 right; Clear + Drum 1. *Say:* "Clear plus a knob to the right resets both layers of that knob. Clear plus the drum's button puts all eight knobs back to their defaults and erases their automation in the playing pattern."

*Chapter 3: the stereo pair*

7. **Make a pair.** *Show:* hold Drum 1, press Drum 2; Drum 2's button pulses. *Say:* "Hold Drum 1 and press Drum 2: they become a stereo pair. Drum 1 plays on the left and Drum 2 on the right, with the pack's next sample: a stereo sample is two slots in a row."
8. **Who drives.** *Show:* Drum 1's knobs and pattern; Drum 2's K1 (detune) and K2 (width). *Say:* "Drum 1 drives both: its knobs, its pattern, its level and sends. Drum 2's knobs become small deviations: K1 detunes the right side, K2 sets the stereo width. Drum 2's own pattern rests while the pair lasts. The same gesture undoes the pair."

*Chapter 4: [Beta] automation tools*

9. **Snapshot.** *Show:* Record held + step 7. *Say:* "In the Beta, Record held plus a step writes the pitch, decay, distortion and EQ that aren't at their defaults into that step."
10. **Extra lane.** *Show:* Record held + K6. *Say:* "Each drum has one more automation lane. From the factory it holds the chromatic pitch; Record held plus a knob assigns another parameter, like resonance."
11. **Automation view.** *Show:* Velocity view with Shift: yellow steps; Shift + a yellow step. *Say:* "Hold Shift in a drum's Velocity view: the steps with automation light yellow. Shift plus a yellow step previews it; Shift plus another step marks it red, and on that step the knobs go back to the project's values."
12. **Outro.** *Say:* "Next: the drum's Preset view."

**Keep in mind**
- Everything here is saved with the project and has an NRPN.
- The mod's new knobs have no automation lane of their own (the stock ones do).
- Sidechain between drums is in the Sidechain view (video 25).
- The stereo pair is saved with the project.

---

## 21 · Drum Preset view

**Guide:** [5.2](GUIA.en.md#drum-preset) · **Length:** about 5 min

**Before recording**
- A capture already recorded in Master FX (video 23); two packs on the card.

**In this view**
- A drum replaced by Master FX's capture.
- Swapping and copying samples, also between packs.
- The sample arpeggio.

**Script**

1. **Intro.** *Show:* Drum 1, Preset: the samples; Shift + pad (silent selection, stock). *Say:* "The drum's Preset view picks its sample, as always. Three new things."
2. **Replace with the capture.** *Show:* Clear + pad, Clear + the same pad: the capture plays on that drum. *Say:* "Clear plus a pad, twice, replaces that sample with Master FX's capture. Until you save the project it's only in memory; when you save, it's written into the pack if it fits in the sample memory."
3. **Swap.** *Show:* Duplicate + pad A + pad B. *Say:* "Duplicate plus two pads swaps two samples, files and all; you hear it at once."
4. **Copy from another pack.** *Show:* Duplicate + A; load another pack; Preset; Duplicate + B. *Say:* "Duplicate plus a sample, load another pack, then Duplicate plus a slot copies the sample there. It never overwrites a sample that's playing."
5. **Sample arpeggio.** *Show:* drum's arpeggiator on; hold three samples. *Say:* "With the drum's arpeggiator on, holding several samples makes the drum jump between them."
6. **Shortcut.** *Show:* Preset again. *Say:* "Preset again, or Shift plus Preset, opens the chromatic view: the next video."

**Keep in mind**
- Everything here *writes to the card*: not in the S builds and not in the internal pack.
- A capture used on a drum and not saved is lost at power-off; the drum goes back to its pack sample.

---

## 22 · The drums' chromatic view and rollers

**Guide:** [5.3](GUIA.en.md#drum-cromatica) · **Length:** about 5 min

**Before recording**
- Drum 2 with a tonal sample (a tom or a bass hit); the drums' Note view ready.

**In this view**
- A drum played as a keyboard, in the project's scale.
- Micro-step rollers in the drums' Note view.

**Script**

1. **Open.** *Show:* Drum 2, Shift + Preset. *Say:* "Shift plus Preset turns the drum into a keyboard: three rows of notes in the scale and root of the Scales view."
2. **Tuning.** *Show:* K1; Shift + K1. *Say:* "K1 offsets the pitch in semitones, Shift plus K1 fine-tunes in cents."
3. **Record it.** *Show:* Record + Play; play pads. *Say:* "While recording, each pad records a hit with its pitch on its own step. Shift plus Play quantizes, and the pitch moves with its hit."
4. **The drums' Note view.** *Show:* Note with a drum selected: pads 25-28. *Say:* "In the drums' Note view, pads 25 to 28 mirror the drum boxes, Drum 4 to Drum 1."
5. **Rollers.** *Show:* rows 1-3: hold one pad, then two of the same column. *Say:* "Rows 1 to 3 are micro-step rollers: each column belongs to a drum, the left column its micro steps 1 to 3, the right one 4 to 6. While you hold one, the drum plays on every step at that micro step: rolls and ratchets, live."
6. **Stopped and recorded.** *Show:* stopped, hold a roller; Record + Play. *Say:* "They work with the transport stopped too, at the project's tempo. With Record, their hits are recorded into the pattern."
7. **Outro.** *Say:* "Next: Master FX."

**Keep in mind**
- Steps without a recorded pitch play K1's pitch.
- The chromatic pitch is saved with the pattern; K1's semitone with the project.

---

## 23 · Master FX

**Guide:** [6.1](GUIA.en.md#master-fx) · **Length:** about 12 min (chapters: the effects / the song pointer / the capture / slots / Glitch and the mechanical gesture)

**Before recording**
- The `TUTORIAL` project playing a full loop; the knobs of each effect at their defaults.

**In this view**
- Live effects on the whole mix: Gater, Auto-Filter, Digitise, Phaser, Glitch, the mechanical gesture.
- The song pointer: retriggers and loops of the pattern.
- The capture: record up to 3.5 s of what plays, play it, slot it, or use it as a drum.
- Assignable slots on the bottom row.

- [Beta, unreleased → Alpha 7.04] Recording on pad 32 while pad 7 plays = overdub: the sample keeps playing and goes into the new take at 0.7 (a loop repeats its echoes, each pass at 0.7). RC4.16: nothing starts the sample while recording.

**Script**

*Chapter 1: the effects*

1. **Open.** *Show:* Mixer, Mixer again. *Say:* "Press Mixer twice for Master FX: effects on the whole output, plus a few performance tools. Any other view button leaves." [Beta] *Say:* "In the Beta, hold Mixer to see Master FX only while you hold it."
2. **Hold and latch.** *Show:* hold pad 1 (Gater); Shift + pad 2; touch pad 2 again. *Say:* "Pads 1 to 6 are the effects: Gater, Auto-Filter low-pass and high-pass, Digitise, Phaser and Glitch. Hold one and it's on while you hold it. Shift plus the pad latches it; touch it again to release it."
3. **Their knobs.** *Show:* while holding pad 1, K1-K4; the LED brightness. *Say:* "While an effect is held, K1 to K4 are its controls: for the Gater, division, depth, width and smoothing; for the Auto-Filter and the Phaser, the speed, synced to the tempo on the left side of the knob. The LEDs show the values by brightness."
4. **Digitise extras.** *Show:* hold pad 4, turn K3 up, let go; K4. *Say:* "Digitise has two extras: K3 throws the tracks into the delay while you hold the pad, and K4 is an envelope on the amount: to the right it fades from crushed to clean, to the left the other way."
5. **Everything off.** *Show:* latch two effects, pad 8. *Say:* "Pad 8 releases everything latched, effects, song pointer and sample, and bypasses the effects."

*Chapter 2: the song pointer*

6. **Retrigger and loops.** *Show:* hold one of pads 9-24; hold two; Shift + two (pad 9 white). *Say:* "Pads 9 to 24 are the pattern's steps 1 to 16. Hold one: the pattern retriggers from that step. Hold two: it loops between them while you hold. Shift plus two: the loop stays; pad 9 turns white, and touching it removes the loop."
7. **Phrase mode.** *Show:* Shift + step 5; tap step 8; Shift + pad 9 to leave. *Say:* "Shift plus one step enters phrase mode with that start; each touch then sets the end, without retriggering. Shift plus the start, or pad 9, leaves."
8. **[Alpha, unpublished] Step sequencer.** *Show:* with Play, hold pad 1 and tap step 3; hold pad 26 and tap step 9; Clear + step 13 (red); Clear + step 3. *Say:* "Hold an effect and tap a step: that effect plays on that step every cycle, and the step shows its colour. Effects add up. Clear on an empty step silences it; Clear on a step with something brings it back to normal. Duplicate on a step makes it random: each cycle one of its effects plays at random. It is saved with the project."

*Chapter 3: the capture*

8. **Record.** *Show:* hold pad 32 for two beats; tap pad 32 twice; Shift + pad 32 stopped, then Play. *Say:* "Pad 32 records the output: hold it to record while you hold, up to about three and a half seconds; a short tap records until the next tap. Shift plus pad 32 arms it: it records the next bar, or from Play when stopped."
9. **Play.** *Show:* pad 7; K1-K4; K2 colours; Shift + pad 7. *Say:* "Pad 7 plays the capture: K1 pitch, K2 the mode, one-shot, gate or loop, K3 the start and K4 the end. Shift plus pad 7 latches a loop until you press it again."
10. **What it records.** *Say:* "The capture records the mix without Master FX's effects, and before the master filter; what plays back goes through the effects. To keep it, put it on a drum (video 21) and save the project."
11. **[Beta] Through a project change.** *Show:* latched loop; load another project; Play blinks green. *Say:* "In the Beta, a latched loop keeps playing when you load another project: Play blinks, and the new project starts right on the loop's turn."

*Chapter 4: slots*

12. **Assign.** *Show:* hold pad 1, touch pad 26; touch pad 26 alone. *Say:* "The bottom row, pads 26 to 30, holds effects with their settings. Hold an effect, or pad 7, or pad 31, and touch a slot: the slot stores it with a copy of its knobs. Touch the slot to play it, Shift plus the slot to latch it."
13. **The FX sequencer.** *Say:* "These slots are what the MIDI tracks' FX sequencer engine plays, step by step."

*Chapter 5: Glitch and the mechanical gesture*

14. **Glitch.** *Show:* hold pad 6; K1 from top to bottom; K4 lower and upper half. *Say:* "The Glitch turns the output into a tape head over the last few seconds: K1 is the speed, normal at the top, stopped in the middle, backwards at the bottom; K2 repeats; K3 the delay; K4 chaos in its lower half, overload in its upper half."
15. **Mechanical gesture.** *Show:* press and release pad 31; K2 through its colours. *Say:* "Pad 31 is a mechanical gesture: pressing it slows the music to a stop, releasing starts it again. K1 sets how many moves, K2 the kind, from tape stop to scratch, tear, back spin and rattle, K3 and K4 the stop and start times."
16. **Outro.** *Say:* "Each project remembers its Master FX settings: the twenty knobs, the slots and the compressor."

**Keep in mind**
- Clear + knob to the right = default; Master FX has no automation, so there's no red here.
- Latched effects, the song pointer and the latched sample are off after a restart.
- An unused capture is lost at power-off.
- The mechanical gesture uses the Glitch's engine: while the gesture plays, the Glitch waits.

---

## 24 · FX view

**Guide:** [7.1](GUIA.en.md#vista-fx) · **Length:** about 4 min

**Before recording**
- A project with some reverb and delay sends.

**In this view**
- The reverb's and delay's own parameters.
- A quick reset.
- The master filter's resonance and an off switch.

**Script**

1. **Sends.** *Show:* FX; Octave ▲ / ▼. *Say:* "The FX view sets each track's reverb and delay sends, as always; Octave picks delay or reverb."
2. **Effect parameters.** *Show:* Shift + K1-K3 (reverb); Octave, Shift + K1-K6 (delay). *Say:* "Shift plus a knob reaches the effects themselves: for the reverb, type, decay and damping; for the delay, time, sync, feedback, width, ratio and slew. They're saved with the project."
3. **Reset.** *Show:* Duplicate. *Say:* "Duplicate resets: sends to zero, the master filter centred, Master FX off."
4. **Master filter resonance.** *Show:* Shift + Octave ▲ / ▼ (yellow with Shift). *Say:* "Shift plus Octave raises or lowers the master filter's resonance in steps of 16."
5. **Master filter off.** *Show:* Shift + pad 25; the filter knob LED red; move the filter knob; Shift + pad 25 again. *Say:* "Shift plus pad 25 switches the master filter off: it sounds centred even if you move its knob, and the knob's LED is red. Switch it on again and it comes back where the knob is."
6. **Bottom row.** *Say:* "The bottom row is Master FX's: slots, the mechanical gesture, and capture."

**Keep in mind**
- If Setup routes the returns through mixer strips 3 / 4, their sends here are capped at half.
- The master filter, its resonance and its off switch are not saved: they start fresh after a restart, as on the original.

---

## 25 · Sidechain view

**Guide:** [8.1](GUIA.en.md#sidechain) · **Length:** about 5 min

**Before recording**
- A kick on Drum 1 and a sustained bass on Synth 1; the master compressor switched on in Advanced Setup.

**In this view**
- The sidechain's envelope on the knobs, beyond the presets.
- The master compressor's attack and release.
- Synth or MIDI patterns as sidechain sources; sidechain between drums.

**Script**

1. **Open.** *Show:* Shift + FX; touch a preset for Synth 1. *Say:* "Shift plus FX opens the Sidechain view. The presets work as always."
2. **The envelope.** *Show:* K1-K4 in Synth 1's colour. *Say:* "K1 to K4 shape the ducking of the track whose preset you touched last: attack, hold, decay and depth. No more choosing between fixed presets."
3. **Master compressor.** *Show:* K7 / K8 (white). *Say:* "K7 and K8 are the master compressor's attack and release, saved with the project."
4. **Pattern sources.** *Show:* row 1, pad 1 (Synth 1 as the source for another track). *Say:* "Row 1, pads 1 to 4, add Synth 1, Synth 2, MIDI 1 and MIDI 2 as sources, next to the drums on pads 5 to 8: every note of that track's pattern ducks the chosen track, like a drum hit would. Notes played live don't."
5. **Between drums.** *Show:* Octave ▼; a drum page; K1-K4 in the drum's colour. *Say:* "Octave down shows the pages for sidechain between drums: one drum ducking another. On a drum page, K1 to K4 set that drum's envelope too."
6. **Outro.** *Say:* "Next: patterns and chains."

**Keep in mind**
- The knobs' brightness rises in a curve, so presets can be told apart by eye.
- The triggers of a drum by another drum or by a pattern (on the drum pages) are not saved, as the presets of sidechain between drums aren't.

---

## 26 · Patterns view and pattern chains

**Guide:** [9.1](GUIA.en.md#patterns) · **Length:** about 7 min (chapters: chain rules / [Beta] pattern mutate / [Beta, unreleased] chains of groups)

**Before recording**
- Synth 1 and Drum 1 with three or four different patterns each.

**In this view**
- Chain rules: «play A n times, then B; next time, C».
- [Beta] Pattern mutate.

**Script**

*Chapter 1: chain rules*

1. **Chain mode.** *Show:* Patterns; hold Shift (Octave yellow); Shift + Octave ▲ (green). *Say:* "In the Patterns view, Shift plus Octave up turns on chain mode for the whole project. Shift plus Octave down turns it off; the rules stay saved."
2. **A rule.** *Show:* tap pattern 1 (yellow), again twice (the knob LEDs count 3); tap pattern 2 (green); tap pattern 3 (red). *Say:* "In chain mode, tap a pattern: that's A, in yellow. Tap it again to add repeats, up to eight; the knob LEDs count them. Tap another pattern of the track: that's B, in green; the next one is C, in red."
3. **What it plays.** *Show:* play: A A A B A A A C. *Say:* "With three repeats, the track plays A three times, then B; three times A again, then C. No C: A A A B. B and C play once and the track goes back to A."
4. **Clear.** *Show:* in the mode, Clear + pattern. *Say:* "Clear plus a pattern removes its rule. Outside chain mode it clears the pattern, as always, rule included."

*Chapter 2: [Beta] pattern mutate*

5. **Mutate.** *Show:* Shift + tap Duplicate; patterns going dark in a column. *Say:* "In the Beta, Shift plus a tap on Duplicate gives each selected track a short list of its patterns in another order, looping in place of the chain. The patterns themselves don't change. Another tap, another list."
6. **Settings.** *Show:* Shift + Duplicate held: the peach settings page. *Say:* "Hold Shift plus Duplicate for the settings: the list's length, how much changes, repeats allowed or not, keep the first slot. Clear plus Duplicate ends the lists."

*Chapter 3: [Beta, unreleased] chains of groups*

7. **Groups.** *Show:* Shift + a start pad + an end pad; K1 for repeats. *Say:* "In the newest betas the rules become groups: each track plays a run of patterns A some times, then B, then C, and back to A. In chain mode, Shift plus a start and an end pad makes the next group, and K1 sets its repeats. Each scene keeps its own chains."
8. **Outro.** *Say:* "Rules travel with the pattern when you duplicate it; the mode is saved with the project and with each scene: next video."

**Keep in mind**
- A scene ends when its longest chain ends.
- Blinking track pads in the Mixer mean that track is following a rule.

---

## 27 · Mixer view and scenes

**Guide:** [9.2](GUIA.en.md#mixer) · **Length:** about 7 min (chapters: levels and mutes / scenes / cue mode)

**Before recording**
- All eight tracks playing; two scenes saved, one of them in chain mode; headphones on the right output for the cue chapter.

**In this view**
- Level to 100 or 0 in one move.
- Mutes on the next bar.
- Scenes with chain mode and repeats.
- The cue mode: preview tracks on the right output.

**Script**

*Chapter 1: levels and mutes*

1. **Full or silent.** *Show:* Shift + a level knob right / left. *Say:* "In the Mixer, Shift plus a level knob turned right sets that track to 100, left to zero, in one move. It goes out over MIDI and records like a turn."
2. **Mute on the bar.** *Show:* Shift + pad 3 (blinks), the bar starts, muted. *Say:* "Shift plus a track pad mutes or unmutes it exactly on the next bar; the pad blinks while it waits; again cancels it. Stopped, it happens at once."
3. **[Beta] Solo.** *Show:* pad 16 held + pads 1 and 5; a tap on pad 16. *Say:* "In the Beta, hold pad 16 and press tracks: solo. A tap on pad 16 brings back the mutes from before. A tap on pad 16 alone, with no solo, is solo flip: the tracks you hold sound alone until you let go."

*Chapter 2: scenes*

4. **Chain mode in scenes.** *Show:* scene pads: peach = saved in chain mode. *Say:* "Scene pads work as always. A scene saved in chain mode shows peach and brings the mode back when it loads."
5. **Repeats.** *Show:* Shift: row 2 yellow; Shift + pad 11 (3 repeats); playing: the current repeat white. *Say:* "Shift plus pads 9 to 16 set how many times the current scene repeats, one to eight. While it plays, holding Shift shows which repeat is playing in white."

*Chapter 3: cue mode*

6. **Turn it on.** *Show:* pan page (Octave ▼); Shift + a knob (Octave pink). *Say:* "On the pan page, Shift plus a knob turns on the cue mode: the left output carries the mix in mono, and the right output is your cue."
7. **Cue sends.** *Show:* turn pan knobs right (pink, brighter). *Say:* "Now the pan knobs are each track's send to the cue. A muted track in the cue plays only on the right, in time: bring it into the mix when it's ready."
8. **Previews and click.** *Show:* choose a Synth 1 patch: heard only on the right. *Say:* "With cue mode on, choosing a synth patch, or Shift plus a drum sample, is heard only in the cue. The metronome goes only to the cue too."
9. **Outro.** *Say:* "Mixer again: Master FX. Next: projects."

**Keep in mind**
- The cue mode is stored in the device, the cue sends with the project.
- Reverb, delay and Master FX are the mix's: the cue hears them too.
- Saving a scene again doesn't change its repeats.

---

## 28 · Projects view

**Guide:** [10.1](GUIA.en.md#projects) · **Length:** about 3 min

**Before recording**
- A project saved in slot 1; an empty slot; a second pack.

**In this view**
- Copying a project to another slot or another pack.

**Script**

1. **Pick the source.** *Show:* Projects; Duplicate + pad 1 (yellow, blinking). *Say:* "In the Projects view, Duplicate plus a project picks it as the source: it blinks yellow. Duplicate plus it again forgets it."
2. **Copy.** *Show:* Duplicate + an empty pad: copied. *Say:* "Duplicate plus an empty slot copies it there at once."
3. **Over a used slot.** *Show:* Duplicate + a used slot: blinks white; Duplicate + it again. *Say:* "Over a slot in use, it asks first: the slot blinks white, and Duplicate plus it again within five seconds overwrites it. The loaded project is never overwritten."
4. **Another pack.** *Show:* pick the source, load another pack, Projects, Duplicate + slot. *Say:* "To copy to another pack: pick the source, load the other pack, come back to Projects and Duplicate plus the slot. There it plays with that pack's patches and samples."
5. **Outro.** *Say:* "The device pauses for a moment while it copies."

**Keep in mind**
- What's copied is the project as saved on the card: save first.
- Copying *writes to the card*.

---

## 29 · Packs view

**Guide:** [10.2](GUIA.en.md#packs) · **Length:** about 3 min

**Before recording**
- A spare pack you don't mind deleting.

**In this view**
- Deleting packs on the device.
- The internal pack is protected.

**Script**

1. **Open.** *Show:* Shift + Projects; Clear lit white. *Say:* "Shift plus Projects opens the packs, as always."
2. **Delete.** *Show:* Clear: deletable packs blink; touch one: only it blinks; Clear: gone. *Say:* "To delete a pack: Clear, and for five seconds the packs you can delete blink. Touch one: now only it blinks, and it is not loaded. Clear again within five seconds: deleted."
3. **The internal pack.** *Say:* "The first pack, in the internal memory, is read-only for the mod: it can't be deleted, and nothing of the mod is written into it. You can still copy from it to a pack on the card."
4. **Outro.** *Say:* "A deleted pack's slot can be used again after a restart."

**Keep in mind**
- The loaded pack can never be deleted.
- Deleting is permanent: back up the card first.

---

## 30 · Saving: what is kept, and where

**Guide:** [11](GUIA.en.md#datos-patron) · **Length:** about 6 min

**Before recording**
- Nothing special: this one is mostly talking over a few gestures.

**In this video**
- What travels with a pattern.
- The four places things are kept.
- What a restart loses.
- Saving safely.

**Script**

1. **Intro.** *Say:* "Last video: where your work goes, and how to make sure it's kept."
2. **Save twice.** *Show:* Save (flashes white), Save (green). *Say:* "Save twice saves the project into its slot; Save plus a slot pad in Projects saves into another. Everything this series called 'saved with the project' or 'with the pattern' reaches the card only this way."
3. **The pattern.** *Say:* "A pattern carries its notes, automation, sample flips, settings, and the mod's step data: frequency, dynamics, random-mutate, orders, chain rules, the steps that release automation. Duplicating a pattern copies all that. The arpeggiator is the exception: it's saved in the project per pattern number."
4. **Knobs vs automation.** *Say:* "A knob turned without Record changes the project's sound, not the pattern. To make it change at a step, record it."
5. **The four places.** *Show:* captions: pattern / project / pack / device settings. *Say:* "The project holds the synths' sounds, the drum knobs, Master FX settings, scales, chains. The pack holds what you save on purpose: patches, samples, copies; it's written at once. The device settings hold Setup and Advanced Setup choices and the MIDI tracks' engine. And some things live only in memory."
6. **Lost at a restart.** *Say:* "After a restart: the master filter and its resonance are reset, the click is off, latched effects and the song pointer are off, latches and chord screens are gone, and an unused capture is empty."
7. **Switching off.** *Say:* "Before switching off: stop the sequencer, wait two seconds, and use the power button. If a delayed save is pending, stop first."
8. **S builds and the internal pack.** *Say:* "With an S build, or in the internal pack, the mod writes nothing of its own: patches, samples and copies are not saved, and Save shows red. Projects save as on the original."
9. **[Beta, unreleased] Back to the saved pattern.** *Say:* "In the newest betas, Clear plus Duplicate twice in a track's view puts that pattern back as the card has it."
10. **Outro.** *Say:* "That's the series. The guide by views has every detail; the feature list sums it up."

**Keep in mind**
- [Beta, unreleased] The own synth's extra lanes and the chains of groups live in the project's file: a Components backup doesn't carry them; the card app's Snapshot does.
- Projects saved with the mod open on the official firmware, without the mod's extras.

