# Roadmap

*[Versión en español](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Roadmap-ES) · [Home](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Home) · [FAQ](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/FAQ) · [Changelog](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/blob/main/docs/CHANGELOG.md#changelog) · [Discussions](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/discussions)*

Updated 2026-10-28. Current versions: **RC2.11 / RC2.11S** and **Beta 3.41 / 3.41S**.

The mod has grown fast. The next stage is about **quality rather than quantity**: making what exists sound better, easier to use, solid and well documented. Bigger new features wait until then.

## In progress

- **Stereo drum pairs** (Beta 3.36 / 3.37, to be tested on the device): hold Drum 1 and press Drum 2 (or Drum 3 + Drum 4). Drum 1 / 3 plays its sample on the left and Drum 2 / 4 plays the next sample on the right, both driven by Drum 1 / 3's controls and pattern. Drum 2 / 4's knobs set the pan spread, the detune and small deviations. Saved with the project; the same gesture goes back to two separate drums.

## Now

### 1. Improve the existing sound functions
- **Make room for improvements.** The sound engine has little space left, so the first step is tidying what is there to make room for the improvements below.
- **Smoother filter on fast envelopes.** Fast filter sweeps of the MIDI 1 / 2 synth can leave a faint zipper noise: make them smooth.
- **Brighter, cleaner wavefold on high notes.** Since Beta 3.35 the fold is softened on high notes to avoid harsh tones; a better method would keep the brightness without them.
- **Know the real limits.** Try the heaviest combinations on the device (two polyphonic tracks with supersaw, all drums, Master FX) and set the number of voices from the result.
- **Review every engine by ear:** levels between engines, clicks on note changes, envelope ranges, the granular and sample modes, Master FX.

### 2. Improve the interface
- **One set of rules everywhere:** with Shift, what is available lights yellow and the chosen option shows in another colour; Clear + knob = default (lavender) or delete automation (red); Duplicate + A + B = swap or copy; every mode of its own has a visible indicator. Check every view against these rules.
- **Tidy the busy views,** first the MIDI 1 / 2 Preset view, where most of pads 25-32 are separate switches (see the ideas below).
- **Show hidden values,** such as a knob's exact number, the selected mode and whether there are unsaved changes (see the ideas below).

### 3. Fix and maintain
- **Device testing** of everything marked "not tested" in the changelog, then move the tested features from the Beta to the next RC.
- **Every fix goes to both the RC and the Beta,** and every RC keeps its safer "S" twin.
- **Stability first:** no new feature may make the timing unsteady or the audio click.
- **Issues and FAQ:** answer reports, and add recurring questions to the [FAQ](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/FAQ).

### 4. A proper manual
- **One manual** in Spanish and English: getting started (installing, the first steps), then view by view, then data and saving, MIDI and troubleshooting. Today it is spread over the [guide by views](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html), the [feature list](https://ghillermo.github.io/CIRCUIT-HACKS-RC/en.html), the [guide in plain words](https://ghillermo.github.io/CIRCUIT-HACKS-RC/plain.html) and the [MIDI reference](https://ghillermo.github.io/CIRCUIT-HACKS-RC/midi-en.html).
- **A drawing for every view:** what every pad, knob and colour does.
- **Simpler version marks** (only "since RC…" and "Beta only").
- **A printable PDF,** made from the same source as the web pages.
- **This wiki:** the sections ([Views](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Views), [Data](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Data), [Features](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Features), [DSP](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/DSP), [Usability](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Usability), [MIDI](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/MIDI)), the FAQ and troubleshooting, kept in step with the manual.

## Ideas open for discussion

None of these is decided: comments are welcome in [Discussions](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/discussions).

### Control and usability
- **Pattern transpose over MIDI:** notes coming in on a synth track's channel transpose its playing pattern (keyboard-driven transpose, like an arpeggiator's key input), instead of playing the synth.
- **Value readout:** while a knob turns, its exact value as a number on the pads (the mod already shows numbers this way in a few places), as an option.
- **Undo the last destructive edit** (quantize, Nudge, Clear of a pattern, the snapshot of Record + step): one level.
- **"Unsaved changes" on the Save LED,** so you know when Save twice is needed.
- **Soft takeover** (option): after a project or patch loads, a knob changes nothing until it passes the stored value, so nothing jumps.
- **Copy the own synth between MIDI 1 and MIDI 2** (Duplicate + track button).
- **Load an own-synth patch with Program Change** on the track's channel.
- **A cleaner MIDI 1 / 2 Preset view:** pads 25-32 grouped by job, so the same place always does the same kind of thing: sound (engine, voice mode), editors (CC, matrix) and performance (patch flip, step-drummer).
- **MIDI for what has none yet:** the mod matrix, FM, voice mode and page 4 destinations over NRPN, to control them from a DAW.
- **Per-scene snapshots** of the Master FX knobs, recalled with the scene.

### Re-arranging the saved data
- **One home for the MIDI 1 / 2 synth:** the project. Today its values live in the device settings (the same for every project) and, in the Beta, also in the project; the device settings would only give the starting sound of a new project.
- **Pattern settings that travel with the pattern:** the arpeggiator (on, order, rate) is saved in the project by pattern number, so duplicating a pattern does not copy it. It could live in the pattern itself.
- **Save the master filter and its resonance with the project** (the stock firmware does not).
- **A tidier way to store the mod's data in projects,** with room for new features and older projects converted automatically when they load.
- **All of the mod's device settings in one place,** easy to reset.
- **Backups over USB:** export / import own-synth patches and the mod's settings from a computer, not only by taking the SD card out.

## Not planned
- Beat repeat, reverser, the vinyl effect and lo-fi crackle.
- The Circuit Rhythm: see the separate project [Circuit Remix](https://github.com/Ghillermo/CIRCUIT-REMIX).

## How to take part
- **Ideas and votes:** [Discussions](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/discussions).
- **Bugs:** an [issue](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/issues) with the version, the steps and, if possible, the project or a recording.
- **Testing:** install the Beta and report what works and what does not.
