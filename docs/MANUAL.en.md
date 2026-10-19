# Feature list — CIRCUIT-HACKS (RC2.02)

Circuit Tracks running the official firmware 1.2.1 (build 4486), patched. Anything not described here works as on the original device. Every feature in one line, by topic. **The user manual is the [guide by views](GUIA.en.md)** (in colour: [guide.html](https://ghillermo.github.io/CIRCUITS-HACKS-RC/guide.html)); the CCs / NRPNs, in the [MIDI reference](MIDI.en.md). Illustrated version of this list: [https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html). Versión en español: [`docs/MANUAL.md`](MANUAL.md).

**Conventions:** pads 1-32 from top left to bottom right (row 1 = 1-8 … row 4 = 25-32); knobs K1-K4 top, K5-K8 bottom; “Shift + X” = hold Shift.

## Index

**A. Shortcuts and usability**

- [A1 Shortcut map](#a1-atajos)
- [A2 Master FX on the Mixer button](#a2-master-fx-acceso)
- [A3 Keys of the FX view](#a3-vista-fx)
- [A4 Clear + knob = default value](#a4-clear-knob)
- [A5 Switch off latched effects (Master FX pad 8)](#a5-pad8)
- [A6 Synth source view](#a6-fuente-sinte)
- [A7 Chromatic and scale view of the drums](#a7-cromatica)
- [A8 Pack management on the device](#a8-pack)
- [A9 Replace a drum with the capture](#a9-sustituir)
- [A10 CC editor of the MIDI macros](#a10-editor-cc)
- [A11 Mixer: Shift + knob = level to 100 / 0](#a11-mixer-shift)
- [A12 Cue mode, mutes on the bar and quantize (since RC2)](#a12-mixer-cue)
- [A13 Split keyboard Synth 1 + Synth 2](#a13-teclado-partido)
- [A14 Synth patches by voice mode](#a14-colores-patch)
- [A15 Patches of the own synth (MIDI 1 / 2)](#a15-patches-midi)
- [A16 Saving the synth’s patch into the pack](#a16-guardar-patch)
- [A17 Macro knob destinations](#a17-destinos-macro)
- [A18 Copying projects to another slot or another pack](#a18-copiar-proyectos)
- [A19 Own-synth patches to another pack](#a19-patches-entre-packs)

**B. Exposed controls**

- [B1 Drum knobs as printed on the panel](#b1-knobs-drums)
- [B2 Reverb and delay parameters](#b2-rev-delay)
- [B3 Side-chain and master compressor on the knobs](#b3-sidechain-comp)
- [B4 Recording the internal MIDI routes](#b4-grabar-interno)
- [B5 MIDI for everything new](#b5-midi-io)
- [B6 Automation of the MIDI engine](#b6-automatizacion)
- [B7 Setup and device MIDI](#b7-setup)
- [B8 Patch flip on MIDI 1 / 2](#b8-patch-flip)

**C. New control modes**

- [C1 Engine of the MIDI tracks (pad 27)](#c1-motor-midi)
- [C2 Step-drummer](#c2-step-drummer)
- [C3 FX sequencer](#c3-fx-seq)
- [C4 Song pointer (Master FX)](#c4-song-pointer)
- [C5 Captured sample](#c5-sample)
- [C6 Glitch (pad 6) and its assignment](#c6-glitch-pad)
- [C7 Assignable bottom row (Master FX / FX)](#c7-fila-inferior)
- [C8 Random-mutate per step](#c8-random-mutate)
- [C9 Step frequency and dynamics](#c9-frecuencia-dinamicas)
- [C10 Pattern chains and scenes](#c10-cadenas)
- [C11 Nudge and play orders](#c11-nudge-ordenes)
- [C12 Arpeggiator (since RC2)](#c12-arpegiador)
- [C13 Drums micro-step rollers (since RC2)](#c13-rollers)
- [C14 Custom scale (since RC2)](#c14-escala-propia)
- [C15 Sample mode of the MIDI tracks (since RC2)](#c15-modo-muestra)
- [C16 Mod matrix of the own synth (since RC2.02)](#c16-matriz-mod)
- [C17 Master FX since RC2: mechanical gesture, Glitch, Digitise and saving per session](#c17-master-fx-beta)

**D. DSP**

- [D1 Master FX effects](#d1-efectos-grid)
- [D2 VCA-VCF of the MIDI tracks](#d2-vca-vcf)
- [D3 Oscillators and paraphony](#d3-osciladores)
- [D4 VA-drum engine](#d4-va-drum)
- [D5 Granular synth](#d5-granular)
- [D6 Glitch engine](#d6-glitch-dsp)
- [D7 Drum DSP](#d7-drums-dsp)
- [D8 Audio inputs and returns](#d8-entradas)

**E. Miscellaneous**

- [E1 What is saved and where](#e1-guardado)
- [E2 The internal memory pack: read only](#e2-pack-interno)
- [E3 Installing and going back](#e3-instalar)
- [E4 Development and diagnostic tools](#e4-herramientas)
- [E5 MIDI tables](#e5-tablas-midi)

## A. Shortcuts and usability

<a id="a1-atajos"></a>
### A1. Shortcut map
- Every shortcut of the mod on a drawing of the device: double presses, Shift + button, Clear + knob and the special pads of each view.

<a id="a2-master-fx-acceso"></a>
### A2. Master FX on the Mixer button
- From the Mixer, **Mixer again** opens Master FX; any other view button leaves it.

<a id="a3-vista-fx"></a>
### A3. Keys of the FX view
- **Octave ▲ / ▼** = delay / reverb sends; **Shift + knob** = reverb and delay parameters.
- **Duplicate** = reset (sends to 0, master filter centred, Master FX off); **Shift + Octave ▲ / ▼** = master filter resonance ±16 (Beta 3.3 only; in RC2.02, **1-16 / 17-32**); **Shift + pad 25** = master filter off / on (Beta 3.3 only).

<a id="a4-clear-knob"></a>
### A4. Clear + knob = default value
- Hold **Clear** and turn a knob right: it goes back to its default. On the drums (blue LED), turned left it deletes the automation of the stock knobs (red LED), as on the original. Also on the MIDI track engine and in **Master FX**.

<a id="a5-pad8"></a>
### A5. Switch off latched effects (Master FX pad 8)
- **Pad 8** switches off everything latched with Shift (effects and song pointer) and bypasses the FX; touching a latched effect releases it.

<a id="a6-fuente-sinte"></a>
### A6. Synth source view
- With Synth 1 / 2 on screen, **press its button again**: pads 25-29 pick the source (noise, inputs, inverted inputs), pad 30 = step-drummer.

<a id="a7-cromatica"></a>
### A7. Chromatic and scale view of the drums
- **Shift + Preset** with a drum: the pads play the sample in the scale; K1 = pitch offset, Shift + K1 = cents; Note view: pads 25-28 = drums 4-1.

<a id="a8-pack"></a>
### A8. Pack management on the device
- **Save** also writes the samples replaced by captures to the card.
- **Duplicate + pad A + pad B** (Drum Preset) swaps two samples; between packs it **copies** samples and synth patches; **Clear**, the pack, **Clear** (packs view) deletes a pack.

<a id="a9-sustituir"></a>
### A9. Replace a drum with the capture
- Drum Preset view: **Clear + pad twice** = that sample becomes the capture (until you save or reload).

<a id="a10-editor-cc"></a>
### A10. CC editor of the MIDI macros
- MIDI 1 / 2 Preset view, **pad 25**: move a knob and change its CC / NRPN on the device; pad 26 = save.

<a id="a11-mixer-shift"></a>
### A11. Mixer: Shift + knob = level to 100 / 0
- Mixer view: **Shift + a knob turned right** sets that track’s level to **100**; **turned left**, to **0**.

<a id="a12-mixer-cue"></a>
### A12. Cue mode, mutes on the bar and quantize (since RC2)
- **Since RC2.** Mixer, pan page: **Shift + knob** = cue mode (the right output listens to the tracks you choose). **Shift + pads 1-8** of the Mixer = mute / unmute on the next bar. **Shift + Play** = quantize the pattern of the selected track.

<a id="a13-teclado-partido"></a>
### A13. Split keyboard Synth 1 + Synth 2
- **Since RC2.** Hold **Synth 1** and press **Synth 2** (or the other way round): the two top rows play Synth 1 and the two bottom rows Synth 2.

<a id="a14-colores-patch"></a>
### A14. Synth patches by voice mode
- **Since RC2.** In the Preset view of Synth 1 / 2 every patch is drawn by its voice mode: **mono dark blue**, **glide lavender**, **poly as always**.

<a id="a15-patches-midi"></a>
### A15. Patches of the own synth (MIDI 1 / 2)
- **Since RC2.** In the Preset view of MIDI 1 / 2, rows 2 and 3 are 16 patch slots of the track engine: touch = load (the root note sounds), **Clear + pad** twice = save, **Duplicate + A + B** = exchange; **Octave ▼ / ▲** = 4 pages (64 slots per pack).

<a id="a16-guardar-patch"></a>
### A16. Saving the synth’s patch into the pack
- **Since RC2.** In the Preset view of Synth 1 / 2: **Clear + pad** asks (it blinks white) and **Clear + the same pad again** saves the patch as it sounds into that slot.

<a id="a17-destinos-macro"></a>
### A17. Macro knob destinations
- **Since RC2.** In the synth source view (A6), **pad 32** opens the editor: a knob picks its macro, **Octave ▼ / ▲** steps the field and the pads draw the number.

<a id="a18-copiar-proyectos"></a>
### A18. Copying projects to another slot or another pack
- **Since RC2.** In the Projects view: **Duplicate + pad A** picks the project (it blinks yellow) and **Duplicate + pad B** copies it into that slot, of the same pack or of another one.

<a id="a19-patches-entre-packs"></a>
### A19. Own-synth patches to another pack
- **Since RC2.** In the Preset view of MIDI 1 / 2: **Duplicate + slot A**, load another pack and **Duplicate + slot B** copies the patch (engine, parameters and name).

## B. Exposed controls

<a id="b1-knobs-drums"></a>
### B1. Drum knobs as printed on the panel
- Every knob does what its label says, with a second layer on Shift: ring mod, envelopes, filters (DJ, BP, notch, comb, tilt), LFO, start point, bitcrush and distortion.

<a id="b2-rev-delay"></a>
### B2. Reverb and delay parameters
- FX view, **Shift + knob**: reverb (type, decay, damping) and delay (time, sync, feedback, width, ratio, slew); saved with the project.

<a id="b3-sidechain-comp"></a>
### B3. Side-chain and master compressor on the knobs
- **Since RC2.** In the Sidechain view (**Shift + FX**): **K1-K4** = attack, hold, decay and depth of the side-chain of the chosen track; **K7 / K8** = attack and release of the master compressor.

<a id="b4-grabar-interno"></a>
### B4. Recording the internal MIDI routes
- **Since RC2.** In the Setup view, **Record** decides whether what a MIDI track sends to an internal synth over a shared channel is also recorded into that synth: **yellow = yes**, dark = no (the default).

<a id="b5-midi-io"></a>
### B5. MIDI for everything new
- The new values go out and come in over MIDI: CC / NRPN of the MIDI track engine, NRPN of the drums (MSB 5-8) and of Master FX (MSB 9, channel 16).

<a id="b6-automatizacion"></a>
### B6. Automation of the MIDI engine
- With Record + Play, the 8 values of page 4 of the MIDI engine are recorded into the macro lanes of the pattern.

<a id="b7-setup"></a>
### B7. Setup and device MIDI
- Channel 16 Rx / Tx (pad 16), shared channels, **internal loopback** without a cable and **reverb / delay returns through strips 3 / 4** (pads 22 / 23, cream / peach like the reverb and delay of the FX view).
- **since RC2:** MIDI Thru with four modes (Duplicate in Advanced Setup): Thru, Out 2, **Merge** (DIN In + the device’s MIDI) and **Filter** (DIN In without the channels the device listens to).
- **since RC2:** own **Program Change** channels: pads 29 / 30 show and pick the listen / output channel (16 by default); what is received is forwarded on the output one.
- **since RC2:** **metronome with count-in**: Shift + Clear walks no metronome, metronome, count-in only and both; the count-in is one bar before recording.

<a id="b8-patch-flip"></a>
### B8. Patch flip on MIDI 1 / 2
- Pad 26 of the MIDI Preset view: every note is sent as a Program Change (exclusive with the track engine).

## C. New control modes

<a id="c1-motor-midi"></a>
### C1. Engine of the MIDI tracks (pad 27)
- Pad 27 of the MIDI 1 / 2 Preset view picks the engine: off → **line** → **oscillator** → **VA-drum** → **granular** → **sample** (since RC2) → **FX sequencer**.
- Pads 1-5 pick the knob page; 28 = two oscillators, 29 = chain order, 30 = step-drummer, 31 = velocity (VA-drum). **since RC2:** Clear + a page pad = the values of that page back to their initial values; rows 2-3 hold patches (A14).

<a id="c2-step-drummer"></a>
### C2. Step-drummer
- Sequencing by **pairs of steps** on top of the pattern: pads 1-16 steps, 17-24 destination / macro, the 8 knobs = the 8 pairs (pitch or velocity).
- MIDI: Preset view, pad 30. Synths: source view, pad 30. While recording, the steps you play are recorded in real time.

<a id="c3-fx-seq"></a>
### C3. FX sequencer
- **Blue** state of pad 27: the step-drummer of the track picks, for each pair of steps, **a slot of the Master FX bottom row** (0 = none); it plays on the steps with a note.
- The knob moves slowly (**one slot every ~48 steps of the turn**) and lights in the **colour of the chosen effect**. **A slot with no effect assigned does nothing:** assign the effects to the Master FX bottom row first (see “Assignable bottom row”). **since RC2:** at the end of the travel there is the **random** value (white LED): on every step with a note one of the list plays at random (the slots with an effect assigned and the mechanical gesture of pad 31).

<a id="c4-song-pointer"></a>
### C4. Song pointer (Master FX)
- Pads 9-24 = steps 1-16: one held step = retrigger; two steps = momentary phrase; Shift + two = latched phrase.
- **Phrase mode:** Shift + step = start (end 16); a touch = the end; Shift + another step = new start; Shift + the start or the white pad 9 = exit.

<a id="c5-sample"></a>
### C5. Captured sample
- **Pad 32** (red) records the output; **pad 7** (yellow) plays it: K1 pitch, K2 mode (one-shot / gate / loop by colour), K3 start, K4 end.
- The sample can be assigned to the bottom row (pad 7 + a bottom pad) and can replace a drum (A8).

<a id="c6-glitch-pad"></a>
### C6. Glitch (pad 6) and its assignment
- **Hold pad 6** (Master FX or FX view): the output breaks up and lags like a tape. K1 speed, K2 repeat, K3 delay, K4 chaos (lower half) or overload (upper half).
- **Pad 6 held + a bottom-row pad** = that slot is a Glitch too, with its copy of K1-K4.

<a id="c7-fila-inferior"></a>
### C7. Assignable bottom row (Master FX / FX)
- Hold an effect of the top rows (or pad 7, or pad 31) and touch a bottom pad: that slot stores the effect with a copy of its parameters. Saved with the project.

<a id="c8-random-mutate"></a>
### C8. Random-mutate per step
- **Since RC2.** In the probability view (**Shift + Pattern Settings**) row 4 gives each step a chance of its notes jumping an octave or moving to another note of the scale when they play.

<a id="c9-frecuencia-dinamicas"></a>
### C9. Step frequency and dynamics
- **Since RC2.** In the probability view of the note tracks: **row 4 = every how many plays of the pattern the step sounds** (1-8). With **pad 25 of Pattern Settings**: row 3 = random **dynamics** (velocity, position and length), row 4 = random-mutate.

<a id="c10-cadenas"></a>
### C10. Pattern chains and scenes
- **Since RC2.** Every pattern can carry a rule “play n times, then jump to B; the next time, to C”. **Shift + Octave ▲ / ▼** in the Patterns view switches the **chain mode** of the whole project on / off; every scene remembers the mode it was saved in.

<a id="c11-nudge-ordenes"></a>
### C11. Nudge and play orders
- **Since RC2.** In the Pattern Settings view: **pad 26 = Nudge** (the pattern rotated so that the chosen first step becomes step 1), **pad 27 = fractal order**, **pad 28 = deconstructed order**. On every track, drums included.

<a id="c12-arpegiador"></a>
### C12. Arpeggiator (since RC2)
- **Since RC2.** In the Pattern Settings view of a note track: **Shift + pad 25** = the pattern's arpeggiator on / off, **Shift + pads 27-32** = its order (fractal, deconstructed, up, down, ping-pong, random), independent of the pattern's direction.

<a id="c13-rollers"></a>
### C13. Drums micro-step rollers (since RC2)
- **Since RC2.** Rows 1-3 of the drums' Note view: holding a roller plays its drum on every step at that micro step (two columns per drum, micro steps 1-3 and 4-6), live; with the transport stopped, at the project's tempo.

<a id="c14-escala-propia"></a>
### C14. Custom scale (since RC2)
- **Since RC2.** **Shift + Scales** = an editor of a custom scale for the note tracks: up to 7 notes over the root and any **period** (up to 24 semitones) that is the root of the next iteration; every row of pads is one iteration (two with 4 notes or fewer). Saved with the project.

<a id="c15-modo-muestra"></a>
### C15. Sample mode of the MIDI tracks (since RC2)
- **Since RC2.** A new state of pad 27 (cyan, after the granular): the MIDI track plays **a pack sample one-shot**, at the note's pitch (**C3 = note 60 = as recorded**), through the engine's filter, effect and LFO; the VCA stays open and the sample plays to its end.
- The **expanded Note view** (Note twice) is the picker: rows 3-4 = 16 samples × 4 pages (Octave ▼ / ▲: all 64 of the pack), rows 1-2 = the steps; **a held step + a sample** = that step's sample flip, also live with Record.

<a id="c16-matriz-mod"></a>
### C16. Mod matrix of the own synth (since RC2.02)
- **Since RC2.02.** With the MIDI 1 / 2 engine on, **pad 6** of its Preset view is a new knob page: **K1-K8 = eight sources** (velocity, note, random per note, LFO 2, envelope 2, a drum hit, the pattern position, stepped random).
- Each knob's **position** is the **destination** (every parameter of the knob pages, 33, one stretch each, in its page's colour) and, inside the stretch, the **amount**. Slow knobs: two clicks a step, 16 steps a destination.

<a id="c17-master-fx-beta"></a>
### C17. Master FX since RC2: mechanical gesture, Glitch, Digitise and saving per session
- **Since RC2.** Pad 6 of Master FX is the **Glitch** and pad 31 a **mechanical gesture** (tape stop, scratch…); Digitise gains **K3 = momentary send to the delay** and **K4 = envelope**; the Master FX knobs and slots **are saved with every project**.

## D. DSP

<a id="d1-efectos-grid"></a>
### D1. Master FX effects
- Gater, Auto-Filter LP / HP, Digitise, Phaser and Glitch on the master output, with 4 parameters each.

<a id="d2-vca-vcf"></a>
### D2. VCA-VCF of the MIDI tracks
- DJ / LP / HP 12 and 24 dB / band pass / notch filters, effects (saturation, folding, wavefold, ring, comb, chorus), VCA with ADSR and LFO.

<a id="d3-osciladores"></a>
### D3. Oscillators and paraphony
- Continuous morph sine → triangle → saw → square, wavefold / slope / width, second oscillator with FM, ring, soft sync and bitwise modes; two paraphonic notes.

<a id="d4-va-drum"></a>
### D4. VA-drum engine
- Oscillator made for percussion: one-shot VCA, dedicated decay envelopes for pitch (Sustain knob) and filter (Release knob), white noise and random values instead of the LFO.

<a id="d5-granular"></a>
### D5. Granular synth
- Up to **16 grains per track** from any sample of the pack or the capture, with interpolation and window; on the second DSP core.
- K1 pitch, K2 position, K3 scan / freeze, K4 size, K5 density, K6 zone, K7 LFO → position, K8 envelope → position; Shift: fine, sprays, reverse, window, slicer (or stretch, since RC2), LFO → size, source.

<a id="d6-glitch-dsp"></a>
### D6. Glitch engine
- A tape head over a stereo circular buffer of the master (2.7 s) in the external DSP memory: variable speed, repeats with fades, chaos.

<a id="d7-drums-dsp"></a>
### D7. Drum DSP
- Ring mod, pitch and filter envelopes, LFO, DJ / band pass / notch / comb / tilt filters, bitcrush, start point, distortions and sidechain between drums.

<a id="d8-entradas"></a>
### D8. Audio inputs and returns
- Line input (normal or inverted) as a synth source; reverb / delay returns through strips 3 / 4 with feedback.

## E. Miscellaneous

<a id="e1-guardado"></a>
### E1. What is saved and where
- Project: drums, Master FX slots, synth source, reverb / delay parameters. Device: MIDI track engine. Volatile: OSC 2, latched effects.

<a id="e2-pack-interno"></a>
### E2. The internal memory pack: read only
- Nothing of the mod writes or deletes in the pack of the Circuit’s internal memory (the first one of the Packs view). You can read it and copy from it to a pack of the card, not the other way round.

<a id="e3-instalar"></a>
### E3. Installing and going back
- `tools/ct_uploader.html` sends the `.syx` over Web MIDI; it only accepts verified firmwares. Recovery: Scales + Preset + Note at power-on.

<a id="e4-herramientas"></a>
### E4. Development and diagnostic tools
- Reproducible builders, ARM / DSP emulators with tests through the real routes, `verify_builds.py`, remote diagnostics over USB (`ctremote.py`).

<a id="e5-tablas-midi"></a>
### E5. MIDI tables
- MIDI engine: CC 74/71/79/73/75/70/72/91/59/26/27/20/21/37/39/30/31/52/54 + NRPN 4:x; drums NRPN 5-8:1-12; Master FX NRPN 9:0-19 (channel 16).
