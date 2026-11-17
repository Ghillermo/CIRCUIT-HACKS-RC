# Automation rules for Circuit Remix (from CIRCUIT-HACKS, 2026-10-29)

The automation behaviour as it stands on the Circuit Tracks in **RC4.01** and **Beta 3.46 / 3.47** (SC49.1 / SC49.2), for porting to the Circuit Rhythm. None of it is tested on the device yet. The user's own words are quoted where they set a rule.

Remix already has the first version, the per-step automation release from Alpha 0.04. [What changed](#what-changed-from-the-first-version) lists the differences.

## 1. The de-automation view (Velocity view + Shift)

Hold **Shift** in a track's **Velocity** view. Tracks applies this to Synth 1 / 2 and MIDI 1 / 2; drums are on the roadmap.

| Step pad | Meaning |
|---|---|
| its stock colour | no knob automation on that step |
| **yellow** (`0x2D`) | the step has knob automation: a value in any knob lane (lanes 0..7) on any of its 6 micro steps |
| **red** (`0x53`) | the step is **marked**: it lets go of the automation |

The user: «keeps base cyan color and is no longer yellow. Instead, it only paints yellow from automation input to automation clear».

**Gestures:**
- **Shift + a step that is not yellow:** marks it or unmarks it. The mark is saved with the pattern; Tracks keeps it in bit 7 of the step's byte [3].
- **Shift + a red step:** unmarks it.
- **Shift + a yellow step = preview only, no mark** (the user: «touching the step in this view (and only this view) allows to preview, on yellow, the automation value on the knob. yellow goes away and knob back to normal when shift is released»).
  - **What plays:** for each lane with a value on that step, the first micro step that has one. It goes to the knob **and to the sound** (the user chose «Apply to the sound too»).
  - **Knob LEDs:** the knobs it moves light **yellow**, brightness = the value (the user: «the updated leds should be yellow»).
  - **Several steps:** touching another yellow step plays its values. The value each knob had before its first change is kept only once.
  - **Shift let go:** the kept values are played back, the LEDs return to normal and nothing stays changed.
- **Clear held + a step**, with or without Shift, erases that step's knob automation: lanes 0..7, all 6 micro steps. Its **notes, its mark and the mixer lanes** (level, pan, sends) stay. The user: «clear+pad in this view must keep the note and erase automation only».
  - **Order:** Clear first. Shift + Clear is the metronome, so Clear pressed while Shift is held would change the metronome instead.
  - **Swallowing:** the press and its release are swallowed. The stock's Clear + step would erase the notes too.

## 2. Playback at a marked step: back to Project init

At a marked step **no lane plays**. Every lane that played automation since the last time it went back returns to **Project init**. The user: «the cleared automation must go to Project init, not current pad».

| Sound | Project init |
|---|---|
| a stock synth (Tracks: Synth 1 / 2) | the macro's value in **the synth's patch as the project holds it**: as loaded, or as last saved. Knobs turned since don't count. Choosing another patch makes that patch the reference: the stock copies a chosen patch into the session record. |
| the mod's own synth (Tracks: MIDI 1 / 2) | the value **saved with the project**; a project saved without one uses the engine's defaults (the Clear + knob values) |
| nothing usable (no session record, a value out of range) | the knob's position before the automation first played: the first version's base |

**Per-lane flag:**
- **Set:** when a lane's value plays.
- **Cleared:** when the lane goes back at a marked step.
- **Turning a knob by hand also clears it.** That knob then stays where the user left it; a marked step doesn't move it.

## 3. Shift + Preset = the voice back to Project init

The user: «new shortcut: shift+preset takes current voice to project init».

| Track on the screen | Shift + Preset |
|---|---|
| a stock synth (any of its views) | **the whole patch** back to the project's |
| the own synth, engine on | the project's own-synth sound; without one, the defaults (as Clear + track button) |
| own synth off, drums, Mixer, FX, other views | nothing |

**LEDs:**
- **Where it works:** the Preset button lights **yellow** while Shift is held (the Shift convention).
- **Elsewhere:** the stock's look (dark with Shift).

The stock ignored Shift + Preset: its Shift mask drops button 8 before the button handler.

## 4. The snapshot (Record held + step), for reference

Record held + a step pad in the track view (Note) writes into that step's lanes the parameters that are **not at init**. Record's own state is put back on release.

| Sound | What goes into the step |
|---|---|
| the own synth | every parameter not at its default. When more parameters differ than there are lanes, a lane whose parameter is at its default is cleared and reassigned. |
| a stock synth | the macros that are not where the loaded patch keeps them |
| drums | the stock knobs (pitch, decay, distortion, EQ) not at their defaults |

Mixer and FX lanes are untouched: scenes already keep them.

Snapshot followed by a marked step is the main use: the marked step brings back Project init.

## What changed from the first version

| | First version (Tracks SC45 … RC4; Remix Alpha 0.04) | Now |
|---|---|---|
| Step pads with Shift | all yellow, marked red | stock colour; yellow = has automation; marked red |
| Shift + step | toggles the mark | toggles the mark, except on a yellow unmarked step = preview |
| Marked step goes back to | the knob's position before the automation (after a snapshot that is the snapshot's own value: nothing audible changed, the bug the user reported) | **Project init** |
| Knob LEDs | — | yellow on the previewed step's lanes |
| Clear + step in Velocity | stock (erases the notes too) | erases only the knob automation |
| Shift + Preset | nothing | the voice back to Project init |

## Implementation notes from the Tracks side

These are Tracks addresses and layouts (firmware 4486); the Rhythm's differ. They show where the information lives, not what to patch.

- **Project init of a stock synth:**
  - **Where it is:** the session record in RAM (`[0x2003D71C + 0x14]`) holds each synth's patch in the bank's format, Synth s at `+ 0x26D14 + 0x154 s`, parameter i at byte `30 + i`, macro m's position at parameter `174 + 17 m`.
  - **Checked in emulation:** turning a macro changes the patch in use (`0x20010044`), not the record.
  - **Shift + Preset:** the stock's routine `0x0802FC82(session object, synth, 0)` copies the record's patch into the synth's store and applies it. It is the same path the stock runs after a project load or a patch choice.
- **Project init of the own synth:**
  - **Where it is:** the own synth's patch saved in the project (projsyn's blocks in spare bytes of the record's pattern settings, with a signature) is read straight from the record.
  - **Shift + Preset:** runs projsyn's restore-after-load for that one track.
- **The playback hook:**
  - **Where:** the stock's automation playback reads, per lane, the first byte ≠ `0xFF` of the step's 6 micro steps (`0x08031B8E`).
  - **What the hook does:** at a marked step it returns `0xFF` (nothing plays). For each flagged lane it writes the Project-init value into the track's macro store, and the stock commits it with the lanes.
- **The preview:** runs through the stock's own held-step preview path (the step object's lane target, slot 0 = (target, lane id, value)). With the own engine on, it goes straight to the engine.
- **The LEDs:**
  - **Knob LEDs:** the LED task's frame, panel LEDs 60..67, halfword `colour | (value + 2) << 8`.
  - **Preset:** LED `32 + 8`.
- **Clear held:** the stock's held-buttons store (Tracks: p0 of `[[controller + 0x20] + 0xC]`, bit 0 Clear, bit 1 Duplicate). A step press with Clear held reaches the step objects' slot 0, where the hook intercepts it before the stock.
- **Tests in CIRCUIT-HACKS:**
  - `tools/emu_sc49_1.py`: Project init on both synths, the yellow knob LEDs, Clear + step, Shift + Preset.
  - `tools/emu_sc48_8.py`: the de-automation view's colours and the preview.
