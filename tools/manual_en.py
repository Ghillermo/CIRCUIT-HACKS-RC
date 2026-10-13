"""English text of the user manual (tools/make_manual.py writes docs/MANUAL.en.md, docs/manual/en.html and the English feature list of README.md).
SEC[id] = (title, summary bullets, detail, figure captions in order); LABEL = the words drawn on the panel figures; UI = the fixed strings of the pages.
Keep the same section ids, order and figures as the Spanish source in make_manual.py."""

GROUPS = {"A": "Shortcuts and usability", "B": "Exposed controls", "C": "New control modes", "D": "DSP", "E": "Miscellaneous"}

UI = dict(
    md_title="Short manual — CIRCUIT-HACKS ({v})",
    md_intro="Circuit Tracks running the official firmware 1.2.1 (build 4486), patched. Anything not described here works as on the original device. "
             "Illustrated colour version: [https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html). Versión en español: [`docs/MANUAL.md`](MANUAL.md).",
    conventions="**Conventions:** pads 1-32 from top left to bottom right (row 1 = 1-8 … row 4 = 25-32); knobs K1-K4 top, K5-K8 bottom; “Shift + X” = hold Shift.",
    index="Index",
    html_title="CIRCUIT-HACKS Manual",
    cover="User manual of the Circuit Tracks mod",
    cover_fw="Official firmware 1.2.1 (build 4486) + {v}",
    html_conv="<strong>Conventions.</strong> Pads 1-32 from top left to bottom right (row 1 = 1-8 … row 4 = 25-32). Knobs K1-K4 on top and K5-K8 at the bottom. "
              "“Shift + X” = hold Shift while using X. The colours of the diagrams are approximate; a dim pad is drawn translucent. Anything not described here works as on "
              "the original device (see Novation’s official user guide).",
    toc="Feature index",
    other='<p class="lang"><a href="index.html">Versión en español</a></p>',
    footer="CIRCUIT-HACKS {v} · This mod is not affiliated with Novation. Circuit Tracks is a trademark of Focusrite Audio Engineering Ltd.",
    features="Features ({v})",
    features_manual="Manual: [illustrated colour](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html) · [short](docs/MANUAL.en.md). New features and fixes of every version: [`CHANGELOG.md`](CHANGELOG.md#changelog). What is marked **BETA5 only** is in the beta BETA5, not in RC0.5.",
)

LABEL = {
    "Apagar": "All off", "Atajos": "Shortcuts", "Ataque": "Attack", "Caos": "Chaos", "Densidad": "Density", "Filtro": "Filter", "Fuente del sinte": "Synth source",
    "Grabar": "Record", "Granular": "Granular", "Gran.": "Gran.", "Modo": "Mode", "Motor": "Engine", "Orden": "Order", "Posición": "Position",
    "Preset de MIDI 1": "MIDI 1 Preset", "Preset de drums": "Drum Preset", "Repet.": "Repeat", "Retraso": "Delay", "Ruido": "Noise", "Sec.": "Seq.",
    "Secuenciador FX": "FX sequencer", "Tamaño": "Size", "Tocar": "Play", "Tono": "Pitch", "Veloc.": "Speed", "Zona": "Zone", "envío": "send",
    "Preset de sinte": "Synth Preset", "fin": "end", "hueco": "slot", "inicio": "start", "nada": "none", "salir": "exit", "Env F": "Env F",
    "paso": "step", "esc\n6": "scale\n6", "esc\n12": "scale\n12", "esc\n25": "scale\n25", "oct 6\nesc 6": "oct 6\nscale 6", "oct 25\nesc 50": "oct 25\nscale 50",
    "Probabilidad": "Probability", "Preset de Synth 1": "Synth 1 Preset", "último": "last",
    **{f"par {k}": f"pair {k}" for k in range(1, 9)}, **{f"paso\n{k}": f"step\n{k}" for k in range(1, 17)},
}

SEC = {}


def sec(sid, title, summary, detail, figs=()):
    SEC[sid] = (title, summary, detail, list(figs))


# ===== A. Shortcuts and usability
sec("atajos", "Shortcut map",
    ["Every shortcut of the mod on a drawing of the device: double presses, Shift + button, Clear + knob and the special pads of each view."],
    """
| No. | Shortcut | Function |
|---|---|---|
| 1 | **Mixer**, **Mixer** | Master FX (A2) |
| 2 | **Synth 1 / 2** with its view on screen, again | Synth source view and its step-drummer (A6) |
| 3 | **Shift + Preset** with a drum | Chromatic / scale view (A7) |
| 4 | **Clear + knob** | Default value of the knob, also in Master FX; on the drums, turned left it deletes the automation (A4) |
| 5 | **Octave ▲ / ▼** in the FX view | Delay / reverb sends; **Shift + knob** = their parameters (A3, B2) |
| 6 | **Duplicate** / **1-16 / 17-32** in the FX view | Reset of sends and Master FX / master filter resonance (A3) |
| 7 | **Shift + FX**, then **Octave ▼**, with the drums | Sidechain between drums (D7) |
| 8 | **MIDI 1 / 2**, **Preset** | Pad 27 engine, 25 CC editor, 26 patch flip, 30 step-drummer (C1) |
| 9 | Master FX: **pad 8** | Switch off everything latched (A5) |
| 10 | Master FX: **pad 7** / **pad 32** / **pad 31** | Play / record the sample (C5), Glitch (C6) |
| 11 | Drum / synth Preset: **Clear + pad twice** / **Duplicate + pad + pad** | Replace with the capture / swap or copy samples and patches between packs (A9, A8) |
| 12 | Packs view: **Clear**, the pack, **Clear** | Delete a pack (A8) |
| 13 | **Save** | Also saves the captures used as samples (A8) |
| 14 | **Scales + Preset + Note** at power-on | Bootloader recovery mode (E2) |
| 15 | Mixer: **Shift + knob** | Track level to 100 (right) / 0 (left) (A11) |
| 16 | Master FX: **Shift + pad 7** | Sample in a latched loop until pad 7 is pressed again (C5) |
| 17 | MIDI 1 / 2 Preset: **Clear + a page pad (1-5)** | The values of that knob page back to their initial values (C1, **BETA5 only**) |
| 18 | Advanced Setup: **Duplicate** | MIDI Thru: Thru → Out 2 → Merge → Filter (B5, **BETA5 only**) |
| 19 | **Synth 1 + Synth 2** together | Split keyboard: Synth 1 on top, Synth 2 below (A12, **BETA5 only**) |
| 20 | **Shift + Pattern Settings**, a step, **row 4** | Random-mutate of the step: random octave / scale changes (C8, **BETA5 only**) |
| 21 | MIDI 1 / 2 Preset: **pads 9-24**, **Clear + pad** twice, **Duplicate + A + B**, **Octave ▼ / ▲** | Patches of the own synth: load, save, exchange, page (A14, **BETA5 only**) |
| 22 | MIDI 1 / 2: **Clear + the track button** | The track engine back to its initial values (A14, **BETA5 only**) |
| 23 | Synth 1 / 2 Preset: **Clear + pad** twice | Saves the synth’s patch into that slot of the pack (A15, **BETA5 only**) |
| 24 | Synth source view: **pad 32** | Editor of the macro knob destinations (A16, **BETA5 only**) |
| 25 | Projects: **Duplicate + pad A**, **Duplicate + pad B** | Copies project A into slot B, in another pack too (A17, **BETA5 only**) |
""", ["Shortcut map: the numbers refer to the table."])

sec("master-fx-acceso", "Master FX on the Mixer button",
    ["From the Mixer, **Mixer again** opens Master FX; any other view button leaves it."],
    """
Master FX is a performance view with effects on the master output, a song pointer and a row of assignable effects (sections C4, C5, C6, C7 and D1).

1. Press **Mixer**.
2. Press **Mixer** again: Master FX opens.
3. Any other view button goes back to the normal view.
""", ["Master FX: pads 1-6 effects, 7 sample, 8 all off, 9-24 song pointer, assignable bottom row, 31 Glitch, 32 record."])

sec("vista-fx", "Keys of the FX view",
    ["**Octave ▲ / ▼** = delay / reverb sends; **Shift + knob** = reverb and delay parameters.",
     "**Duplicate** = reset (sends to 0, master filter centred, Master FX off); **1-16 / 17-32** = master filter resonance."],
    """
| Control | Function |
|---|---|
| **Octave ▲** | The knobs control the **delay sends** (colour of pad 1) |
| **Octave ▼** | The knobs control the **reverb sends** (colour of pad 17) |
| **Shift + knob** | **Effect parameters**. Reverb: type, decay, damping. Delay: time, sync, feedback, width, ratio, slew. Saved with the project |
| **Duplicate** | Reset: sends to 0, master filter centred (resonance untouched), Master FX off |
| **1-16 / 17-32** | Raises the master filter resonance (green LED) |

- The bottom row (pads 25-32) is the same as in Master FX: assignable slots, the Glitch (31) and record (32).
- If Setup routes the reverb / delay return to strip 3 / 4, the sends of those strips stop at half range and move at half speed.
""", ["FX view: Octave picks delay / reverb; the bottom row is the Master FX one."])

sec("clear-knob", "Clear + knob = default value",
    ["Hold **Clear** and turn a knob right: it goes back to its default. On the drums (blue LED), turned left it deletes the automation of the stock knobs (red LED), as on the original. Also on the MIDI track engine and in **Master FX**."],
    """
| Where | Clear + knob right | Clear + knob left |
|---|---|---|
| Drums (stock and new knobs) | Default value; **blue** LED | Stock knobs: deletes their automation; **red** LED (as on the original) |
| MIDI track engine and oscillator | Default value; red LED while Clear is held | The same |
| **Master FX** (from RC0.3) | The knob of the selected effect goes back to its default | Nothing (Master FX has no automation) |

- On the drums and the MIDI engine it resets **both layers** of the knob: the plain one and the Shift one.
- **Master FX:** while Clear is held, the knobs of the selected effect show **blue** at their default and **red** elsewhere. It works for the effects of pads 1-6, the Glitch (normal speed, no repeat, no delay or chaos) and the sample (no transposition, one-shot, start 0, end at maximum).
- RC0.3: the drum blue is the original’s (before, a dim red-orange showed).
""")

sec("pad8", "Switch off latched effects (Master FX pad 8)",
    ["**Pad 8** switches off everything latched with Shift (effects and song pointer) and bypasses the FX; touching a latched effect releases it."],
    """
- **Shift + effect pad** latches the effect. Touching it again (without Shift) releases it.
- **Pad 8** (white) releases every latched effect, also those of the bottom row, switches the song pointer off and stops the sample.
""")

sec("fuente-sinte", "Synth source view",
    ["With Synth 1 / 2 on screen, **press its button again**: pads 25-29 pick the source (noise, inputs, inverted inputs), pad 30 = step-drummer."],
    """
1. With the Synth 1 or Synth 2 view on screen, press its button again.
2. Pick the source:

| Pad | Source |
|---|---|
| 25 | Noise (normal) |
| 26 | Input 1 |
| 27 | Input 2 |
| 28 | Input 1, phase inverted |
| 29 | Input 2, phase inverted |
| 30 | Step-drummer of the synth (C2) |

3. Any button closes the view.

- The patch needs some noise level (CC 56) for the source to be heard.
- If Setup routes the reverb / delay return to strip 3 / 4, that is the signal the synth receives.
- The source is saved with the project.
""", ["Synth source view (Synth 1 / 2 pressed twice)."])

sec("cromatica", "Chromatic and scale view of the drums",
    ["**Shift + Preset** with a drum: the pads play the sample in the scale; K1 = pitch offset, Shift + K1 = cents; Note view: pads 25-28 = drums 4-1."],
    """
- **Shift + Preset** with a drum selected: the pads play the sample transposed by the scale and root of the Scales view (three rows).
- **K1** = pitch offset in semitones; **Shift + K1** = fine tuning in cents.
- While recording, each pitch is recorded on its own step only.
- **Note** view of the drums: pads 25-28 repeat the tiles of drums 4 … 1.
""")

sec("pack", "Pack management on the device",
    ["**Save** also writes the samples replaced by captures to the card.",
     "**Duplicate + pad A + pad B** (Drum Preset) swaps two samples; between packs it **copies** samples and synth patches; **Clear**, the pack, **Clear** (packs view) deletes a pack."],
    """
Not in the safer builds (RC0.3S, RC0.2S, RC0.1S, RC0S). New: RC0.1, Duplicate lights and works in the drum and synth Preset views, copying samples and patches between packs and deleting packs by presses; RC0.2, the Clear LED during a delete; RC0.3, copies go into the replaced sample’s place when they fit, the import memory never overwrites a sample that plays and the delete is easier to follow (Clear steady white, the packs get their colours back); RC0.4, copies to empty slots and Clear steady white as soon as the packs view opens.

### Saving the captures into the pack
When the project is saved, every drum sample replaced by a capture (A9) is written into the pack as `PCM/NN_PCM.wav`, if it fits in the sample memory.

### Swapping two samples
Drum Preset view: hold **Duplicate** (it lights in this view), touch pad **A** (it blinks blue), then pad **B**. Both files and the sample table are swapped: you hear it at once.

### Copying samples between packs
1. In the sample’s pack: Drum Preset view, **Duplicate + pad A**. It stays copied (blinks blue while Duplicate is held), even after you release Duplicate.
2. Load the other pack. While Duplicate is held, the pad with A’s number blinks yellow.
3. **Duplicate + pad B**: sample A is copied over B in this pack and sounds at once. **A’s pack is left untouched.**
4. Duplicate + A again (in its pack) cancels.
5. Inside one pack, Duplicate + A + B still **swaps** the two samples.
6. **Where the copy goes** (from RC0.3): if the sample fits in B’s place it goes there and uses no memory. Otherwise it goes into the free import memory (≈ 44 s), which starts again once no sample uses it (for instance after loading the pack again). If there is no room, nothing changes: a copy never overwrites a sample that plays.
7. **Empty B** (from RC0.4): a pad without a sample can be the target; its file is created in the pack.

### Copying synth patches between packs
1. Synth 1 or 2 Preset view, in the patch’s pack: **Duplicate + pad A** (Duplicate lights in this view). It stays copied (blue while Duplicate is held).
2. Load the other pack: while Duplicate is held, A’s pad (on its page) blinks yellow.
3. **Duplicate + pad B**: patch A is copied over B in this pack and B is chosen again, so it sounds at once. A’s pack is left untouched. Inside one pack the two patches are **swapped**; Duplicate + A again cancels.
4. The 128 patches of a pack are shared by both synths. Not in the source or step-drummer views (from RC0.3, not even with Duplicate held before they open).
5. **Empty slot** (from RC0.4): B can be an unlit pad. If it lies past the last patch of its bank, the empty slots in between stay empty, as when the original saves a patch.

### Deleting a pack
1. Packs view (**Shift + Projects**): tap **Clear** (no Shift). For ~5 s the packs that can be deleted blink (never the loaded one).
2. Touch the pack: only that one blinks; it is not loaded.
3. Tap **Clear** again within 5 s: the pack is deleted. The slot can be reused after a restart.
4. This is how it works from RC0.1; in RC0 (Clear held + pack) it did not work on the device. Clear shows **steady white** as soon as the packs view opens (from RC0.4; dim before) and while the delete waits for confirmation; when it ends or is cancelled the packs get their colours back (from RC0.3; in RC0.2 Clear blinked and the packs could stay dark; in RC0.1 Clear did not light).
""", ["Drum Preset view: Duplicate + A + B swaps the samples.",
      "Synth 1 Preset view: Duplicate + A copies the patch (blue); in another pack A’s pad blinks yellow and Duplicate + B copies it there."])

sec("sustituir", "Replace a drum with the capture",
    ["Drum Preset view: **Clear + pad twice** = that sample becomes the capture (until you save or reload)."],
    """
- **Clear + pad**: asks (the pad blinks). **Clear + the same pad** again: confirmed; the sample plays the Master FX capture (C5).
- Any pad without Clear cancels the question; Clear + another pad moves it to that pad.
- It is volatile until you save the project: then it is written into the pack (A8). In the safer builds it lasts until the pack is loaded again.
- Up to RC0.2 it was **Shift + pad**; from RC0.3 Shift + pad is the original’s silent selection again (picking a sample without playing it).
""")

sec("editor-cc", "CC editor of the MIDI macros",
    ["MIDI 1 / 2 Preset view, **pad 25**: move a knob and change its CC / NRPN on the device; pad 26 = save."],
    """
1. MIDI 1 / 2 Preset view, **pad 25** (it lights).
2. **Move a knob**: it is selected and its CC number is drawn with the 32 pads.
3. **Octave ▼ / ▲**: next / previous field.
4. **Turn the knob** to change the value.
5. **Save:** pad **26** (Save), or step with Octave ▼ to the save step (pad 26 and the Save button blink) and press Octave ▼ again.
6. **Discard:** any view button, pad 25 or a template pad.

| Number of the first field | Type | Fields |
|---|---|---|
| Anything else | CC | number, start, end |
| 99, 98 or 6 | 7-bit NRPN | number, MSB, LSB, start, end |
| 38 | 14-bit NRPN | number, MSB, LSB, start (MSB, LSB), end (MSB, LSB) |
""")

sec("mixer-shift", "Mixer: Shift + knob = level to 100 / 0",
    ["Mixer view: **Shift + a knob turned right** sets that track’s level to **100**; **turned left**, to **0**."],
    """
- On the levels page of the Mixer (the normal one, Octave ▲). On the pan page (Octave ▼), Shift + knob moves the pan as always.
- The jump works like a turn of the knob: it goes out over MIDI and, while recording, it is written into the automation.
- On the original, Shift + knob did the same as the plain knob: no function is lost. Clear + knob (delete the automation) and Master FX (Mixer twice) do not change.
- From RC0.3 (also in RC0.3S).
""", ["Mixer: Shift + knob right = level 100, left = 0."])

sec("teclado-partido", "Split keyboard Synth 1 + Synth 2",
    ["**BETA5 only.** Hold **Synth 1** and press **Synth 2** (or the other way round): the two top rows play Synth 1 and the two bottom rows Synth 2."],
    """
- Each half is its synth’s keyboard: its scale, octave and velocity (the same keys as the lower half of its Note view), in its colours.
- The knobs and Octave belong to the synth you pressed first.
- **Leaving:** any track or view button (Note, Preset, Mixer, FX, a single Synth…). Held notes are released. Play, Record, Octave and Shift do not close it.
- Synth 1 or Synth 2 alone work as always (twice = the source view, A6).
""", ["Split keyboard: rows 1-2 = Synth 1, rows 3-4 = Synth 2."])

sec("colores-patch", "Synth patches by voice mode",
    ["**BETA5 only.** In the Preset view of Synth 1 / 2 every patch is drawn by its voice mode: **mono dark blue**, **glide lavender**, **poly as always**."],
    """
- Mono = dark blue; mono with glide (Mono AG) = lavender; poly = the track colour, as on the original. The chosen patch is drawn lighter.
- The modes are read from the card when the pack, the page or the patch changes, and every 4 s.
- In Advanced Setup pads 22 / 23 no longer light up (they never did anything there).
""", ["Preset view of Synth 1: mono dark blue, glide lavender, poly the track colour."])

sec("patches-midi", "Patches of the own synth (MIDI 1 / 2)",
    ["**BETA5 only.** In the Preset view of MIDI 1 / 2, rows 2 and 3 are 16 patch slots of the track engine: touch = load (the root note sounds), **Clear + pad** twice = save, **Duplicate + A + B** = exchange; **Octave ▼ / ▲** = 4 pages (64 slots per pack)."],
    """
- A patch holds the whole track engine: the engine chosen (line, oscillator, VA-drum, granular, FX sequencer), two oscillators, the chain order, every value of every page and the step-drummer setting (enabled and destination). The steps of the step-drummer and of the FX sequencer belong to the pattern: they travel with the project.
- The 64 slots belong to the pack and are shared by MIDI 1 and MIDI 2: a patch saved from one track can be loaded into the other.
- **Load:** touch a slot. While you hold the pad, the root of the scale sounds on that track with the patch just loaded.
- **Save:** **Clear + pad** = the slot blinks white (a question); **Clear + the same pad again** within ~5 s = saved, replacing what was there. Clear + another pad moves the question.
- **Exchange:** hold **Duplicate**, touch slot A (it blinks) and then slot B: they change places. Onto an empty slot, the patch moves. No gesture empties a slot: overwrite it or move it.
- **Initial values:** **Clear + the track button** (MIDI 1 or MIDI 2, with a view of that track on screen and the CC editor closed) puts every value of the engine back to its initial value; the chosen engine stays.
- Colours: dim peach = a slot with a patch; bright peach = the last one loaded or saved; **violet = empty** (touching it does nothing).
- **On the PC:** `tools/patchtool.py` (on the PC, with the card in a reader) treats each patch as a `.ctm` file: `list` shows the 64 slots with their index, name and engine; `copy` uploads a file into a slot, downloads it or copies it between slots and packs; `show` reads the engine and every parameter and `set` changes them (`set bass.ctm filt=90 engine=granular`); `new` makes a patch with the initial values; `name` names it and `clear` empties a slot. The device has no screen: the name is for the tool; Duplicate + A + B moves it with the patch, saving over the slot removes it.
- BETA2 / BETA3 had other gestures: Duplicate + pad saved, Clear + pad emptied and the empty slots were dark.
- **Octave ▼** = next page, **Octave ▲** = previous page (lit when there is a page that way). Coming back from Master FX or a synth’s Preset view starts at page 1.
- Where they are kept: in the free space behind each of the pack’s first 64 synth patches (`Patches/`). If that synth patch does not exist yet, it is created from the Initial Patch (with the missing ones before it in the bank).
- They are not shown while the CC editor or the step-drummer is open (those use the pads and Octave).
- Not in the safer build (it writes to the SD card).
""", ["Preset view of MIDI 1: rows 2-3 = patches of the own synth."])

sec("guardar-patch", "Saving the synth’s patch into the pack",
    ["**BETA5 only.** In the Preset view of Synth 1 / 2: **Clear + pad** asks (it blinks white) and **Clear + the same pad again** saves the patch as it sounds into that slot."],
    """
- The original device cannot save patches (only Components can). What is saved is the patch in use with every change: the knobs, what came in over MIDI and the macro destinations (A16).
- **Clear + pad** = a question, nothing is written. **Clear + the same pad** within ~5 s = saved: it replaces the patch that was there and the slot becomes the chosen one. Clear + another pad moves the question; a touch without Clear, or the time, drops it.
- Any of the 4 pages (128 slots). A slot past the end of the bank too: the slots in between stay empty.
- The saved patch keeps the name of the one that was loaded. Synth patches are managed with Components; `tools/patchtool.py slist / sname` lists and renames them on the card.
- The own-synth patch that shares the slot (A14) is not touched.
- Duplicate + A + B still copies / exchanges patches (A8).
- Not in the safer build (it writes to the SD card).
""", ["Preset view of Synth 1: Clear + pad asks (it blinks), Clear + the same pad saves."])

sec("destinos-macro", "Macro knob destinations",
    ["**BETA5 only.** In the synth source view (A6), **pad 32** opens the editor: a knob picks its macro, **Octave ▼ / ▲** steps the field and the pads draw the number."],
    """
Each of the 8 macro knobs of a patch has 4 slots, and each slot a destination, a stretch of the knob’s travel (start and end) and a depth. On the original they can only be edited with Components.

1. Source view: with Synth 1 / 2 on screen, press its button again. **Pad 32** (teal) = editor on; the knobs no longer move the macros.
2. **Turn a knob** = you pick its macro (its LED white). The first turn changes nothing.
3. The knob changes the current field; **Octave ▼** = next field, **Octave ▲** = previous:

| Field | Value | Colour of the number |
|---|---|---|
| Slot | 1-4 | yellow |
| Start | 0-127 | green |
| End | 0-127 | orange |
| Destination | its CC or NRPN number | white = CC; light blue, magenta, violet = NRPN of banks 0, 1, 2 |
| Depth | 0-63 | teal = positive, red = negative |

4. **Any pad** drops the macro (the pads of the source view come back); pad 32 turns the editor off; any view button closes it.

- **Destination:** the knob first walks the 31 parameters that have a CC, by CC number (5, 20, 21 … 91, 93), then the 39 that only have an NRPN (envelopes 2 and 3, LFOs, chorus, depths of the modulation matrix). The numbers are those of Novation’s *Programmer’s Reference Guide*: e.g. 74 = filter cutoff, 71 = resonance.
- The changes are heard at once and live in the project’s patch. To keep them in the pack, save the patch (A15).
""", ["Source view with the macro editor: pad 32 lit, the picked knob white."])

sec("copiar-proyectos", "Copying projects to another slot or another pack",
    ["**BETA5 only.** In the Projects view: **Duplicate + pad A** picks the project (it blinks yellow) and **Duplicate + pad B** copies it into that slot, of the same pack or of another one."],
    """
- **Duplicate + pad A** (a slot with a project) = the source. Duplicate + A again forgets it.
- **Duplicate + pad B** = the copy. An empty B is written at once and turns yellow; a B that holds a project blinks white and **Duplicate + B** must be repeated within ~5 s to replace it. The slot of the loaded project is never written.
- **To another pack:** pick the source, load the other pack, open Projects and Duplicate + pad B. The source serves several copies; it is lost at power-off or when Master FX is opened.
- What is copied is the project as saved on the card (save first if you changed it). While it copies (a few moments) the device does not respond.
- A project stores patch and sample numbers, not the sounds: in another pack it plays with that pack’s patches and samples.
- Not in the safer build (it writes to the SD card).
""", ["Projects view: Duplicate + A = the source (yellow, blinking), Duplicate + B = the copy."])

# ===== B. Exposed controls
sec("knobs-drums", "Drum knobs as printed on the panel",
    ["Every knob does what its label says, with a second layer on Shift: ring mod, envelopes, filters (DJ, BP, notch, comb, tilt), LFO, start point, bitcrush and distortion."],
    """
| Knob | Alone | With Shift |
|---|---|---|
| K1 Oscillator | Pitch (exact semitones) | Pitch envelope amount |
| K2 Osc mod | Ring mod frequency | Ring mod amount |
| K3 Amp envelope | Decay; left of 0, sample **start point** | — |
| K4 Filter envelope | Envelope → cutoff | Envelope shape |
| K5 Filter frequency | Filter / EQ | **Filter mode**: DJ, band pass, notch, comb, EQ tilt |
| K6 Resonance | Resonance | — |
| K7 Modulation | LFO amount | LFO speed |
| K8 FX | Distortion; left of 0, **bitcrush** | **Distortion type**: stock, soft, hard, folded |

- The LED brightness shows the value; Clear + knob resets both layers.
- Everything is saved with the project and has NRPN (E4).
""", ["Knobs of a drum."])

sec("rev-delay", "Reverb and delay parameters",
    ["FX view, **Shift + knob**: reverb (type, decay, damping) and delay (time, sync, feedback, width, ratio, slew); saved with the project."],
    """
- In the FX view, with Octave ▲ (delay) or Octave ▼ (reverb), **Shift + knob** sets the global effect.
- Reverb: K1 type, K2 decay, K3 damping. Delay: K1 time, K2 sync, K3 feedback, K4 width, K5 ratio, K6 slew.
- The LED shows the value with its brightness.
""")

sec("midi-io", "MIDI for everything new",
    ["The new values go out and come in over MIDI: CC / NRPN of the MIDI track engine, NRPN of the drums (MSB 5-8) and of Master FX (MSB 9, channel 16)."],
    """
- MIDI track engine: stock CCs where the function matches and NRPN 4:code for the rest, on the track channel.
- Drums: NRPN MSB 5-8 = Drum 1-4, LSB 1-12, on the drum channel.
- Master FX: NRPN MSB 9, LSB = 4 × set + knob, channel 16.
- They follow the CC Tx / Rx filters of Setup. Full tables in E4.
""")

sec("automatizacion", "Automation of the MIDI engine",
    ["With Record + Play, the 8 values of page 4 of the MIDI engine are recorded into the macro lanes of the pattern."],
    """
- Engine page 4 (pad 4 of the page row): TUNE, Release, Env → level, Env → filter, Filter, Resonance, LFO speed, Effect amount.
- While recording, moving those knobs records the movement; on playback the pattern moves them.
- With the step-drummer on, the TUNE lane is used by the pitch row.
""")

sec("setup", "Setup and device MIDI",
    ["Channel 16 Rx / Tx (pad 16), shared channels, **internal loopback** without a cable and **reverb / delay returns through strips 3 / 4** (pads 22 / 23, cream / peach like the reverb and delay of the FX view).",
     "**BETA5 only:** MIDI Thru with four modes (Duplicate in Advanced Setup): Thru, Out 2, **Merge** (DIN In + the device’s MIDI) and **Filter** (DIN In without the channels the device listens to)."],
    """
| Where | Function |
|---|---|
| Setup, pad 16 | Channel 16 (project and FX): receive and send |
| Setup, pad 22 | The reverb return goes through mixer strip 3 |
| Setup, pad 23 | The delay return goes through strip 4 |
| Setup, channels | MIDI 1 / 2 may use a channel already used by another track |
| Advanced Setup, Duplicate | MIDI Thru: Thru → Out 2 → **Merge** → **Filter** (**BETA5 only**) |

- **Internal loopback:** if a MIDI track shares its channel with a synth or the drums, what it sends reaches them internally.
- Pads 22 / 23 light cream (reverb) and peach (delay), the colours of the FX view; dim = off.

### MIDI Thru: Merge and Filter (BETA5 only)
The original only lets the Thru jack be **Thru** (a hardware copy of DIN In, Duplicate dim red) or **Out 2** (a second MIDI output, green). Duplicate in the Advanced Setup view now steps through four modes:

| Mode | Duplicate LED | Out of the Thru jack |
|---|---|---|
| Thru | dim red | DIN In, by hardware |
| Out 2 | green | The device’s MIDI |
| **Merge** | yellow | DIN In and the device’s MIDI |
| **Filter** | blue | DIN In except the messages on the channels the device listens to |

- DIN In SysEx is not copied in Merge / Filter. In Merge, if the device follows the DIN In clock and has Clock Tx on, the Thru jack carries two clocks: switch Clock Tx off.
- It is saved in the settings. With the original firmware, Merge / Filter go back to Out 2.
""", ["Setup: pad 22 = reverb return through strip 3 (cream), pad 23 = delay return through strip 4 (peach)."])

sec("patch-flip", "Patch flip on MIDI 1 / 2",
    ["Pad 26 of the MIDI Preset view: every note is sent as a Program Change (exclusive with the track engine)."],
    """
- MIDI 1 / 2 Preset view, **pad 26**: the notes of the track send Program Change.
- It switches off when the track engine is switched on (pad 27), and the other way round.
""")

# ===== C. New control modes
sec("motor-midi", "Engine of the MIDI tracks (pad 27)",
    ["Pad 27 of the MIDI 1 / 2 Preset view picks the engine: off → **line** → **oscillator** → **VA-drum** → **granular** → **FX sequencer**.",
     "Pads 1-5 pick the knob page; 28 = two oscillators, 29 = chain order, 30 = step-drummer, 31 = velocity (VA-drum). **BETA5 only:** Clear + a page pad = the values of that page back to their initial values; rows 2-3 hold patches (A14)."],
    """
Each MIDI track gets its own “synth”: the track’s **audio input** (line 1 for MIDI 1, line 2 for MIDI 2) or an **internal engine** goes through VCA, effect and filter, with envelope and LFO, before mixer strip 3 / 4. The notes of the track trigger it. The track still sends its MIDI.

### States of pad 27

| Colour | Engine |
|---|---|
| off | the knobs are the normal MIDI macros |
| yellow | **line input** through the VCA-VCF |
| green | **oscillator** (D3) |
| red | **VA-drum** (D4) |
| magenta | **granular** (D5) |
| blue | **FX sequencer** (C3) |

### Pads of the Preset view

| Pad | Function |
|---|---|
| 1-5 | Knob page: 1 VCA-VCF, 2 OSC 1 (granular with that engine), 3 OSC 2, 4 sequenceable values, 5 modulation |
| 25 | CC editor (A10) |
| 26 | Patch flip (B6) |
| 27 | Engine |
| 1-5 | Knob page. **Clear + the pad** (BETA5 only): the values of that page (with and without Shift) go back to their initial values; the engine stays |
| 28 | One / two oscillators (only with the oscillators or VA-drum; dark with the other engines) |
| 29 | Chain order: VCA → FX → filter / filter → VCA → FX |
| 30 | Step-drummer (C2) |
| 31 | VA-drum only: velocity scales the pitch and filter envelopes |

### Page 1 — VCA-VCF

| Knob | Alone | With Shift |
|---|---|---|
| K1 | Attack | Sustain |
| K2 | Release | Decay |
| K3 | Envelope → level | LFO → level |
| K4 | Envelope → filter | LFO → filter |
| K5 | Filter | Filter type (DJ, LP 12, HP 12, BP, notch, LP 24, HP 24) |
| K6 | Resonance | VCA gain (up to +18 dB with saturation) |
| K7 | LFO speed | — |
| K8 | Effect amount | Effect type (soft, hard, folded, wavefold, ring, comb, chorus) |

Type knobs: colour = type, brightness = position inside the type.

### Page 2 — OSC 1 (with the oscillator / VA-drum)

| Knob | Alone | With Shift |
|---|---|---|
| K1 | TUNE | FINE |
| K2 | SHAPE | MIX OSC 1 ↔ OSC 2 |
| K3 | Envelope → pitch | BITSYNC |
| K4 | Envelope → shape | — |
| K5 | LFO → pitch | — |
| K6 | LFO → shape | — |
| K7 | WAVE (morph sine → triangle → saw → square) | — |
| K8 | LFO → morph | Envelope → morph |

Page 3 (OSC 2): K1 TUNE 2 / FINE 2, K2 SHAPE 2 / FM, Shift + K3 RING, K7 WAVE 2. Page 4: the 8 sequenceable values (B4). Page 5: ADSR on top, LFO at the bottom.

- The engine values are saved in the device (not with the project); the OSC 2 ones are volatile.
""", ["MIDI 1 Preset view with the oscillator (pad 27 green): page row and engine pads; pad 28 shows only with the oscillator or VA-drum."])

sec("step-drummer", "Step-drummer",
    ["Sequencing by **pairs of steps** on top of the pattern: pads 1-16 steps, 17-24 destination / macro, the 8 knobs = the 8 pairs (pitch or velocity).",
     "MIDI: Preset view, pad 30. Synths: source view, pad 30. While recording, the steps you play are recorded in real time."],
    """
### Opening and closing

| Track | How to open it |
|---|---|
| MIDI 1 / 2 | Preset view with the engine on, **pad 30** |
| Synth 1 / 2 | Source view (synth button twice), **pad 30** |

- Pad 30 bright = view open; dim = closed. On MIDI, **Shift + pad 30** disables the step-drummer.

### Controls

| Control | Function |
|---|---|
| Pads 1-16 | The 16 steps of the half shown; bright = has a note, white = playing. Touch = listen; **Shift + touch** = add / remove the note |
| Pads 17-24 | Destination of the pitch row (MIDI) / macro 1-8 (synths) |
| K1-K8 | The 8 pairs of steps (the playing one is white) |
| Octave ▲ / ▼ | Pitch / velocity page |
| 1-16 / 17-32 | The other half of the pattern |

- **Pitch on MIDI:** the pair value (64 = no change) offsets the destination: pitch of both oscillators, OSC 2 pitch, WAVE, FM, MIX, env → filter, SHAPE, decay.
- **Pitch on the synths:** the value is the macro position, written as automation.
- Each step keeps the pitch of its first note; a new note takes the pair’s or the previous one.
- **Real-time recording:** with Record on, playing a step also records it on the step that plays, with its microstep.
""", ["Step-drummer view (MIDI 1)."])

sec("fx-seq", "FX sequencer",
    ["**Blue** state of pad 27: the step-drummer of the track picks, for each pair of steps, **a slot of the Master FX bottom row** (0 = none); it plays on the steps with a note.",
     "The knob moves **one slot every ~16 steps** (turn it slowly) and lights in the **colour of the chosen effect**."],
    """
1. On MIDI 1 / 2, set **pad 27** to **blue**. The step-drummer of the track switches on.
2. Open its view with **pad 30**. Put notes on the steps with **Shift + pad**.
3. Each **knob** (a pair of steps) picks a slot of the Master FX bottom row:

| Value | Slot |
|---|---|
| 0 | none |
| 1 | pad 26 |
| 2 | pad 27 |
| 3 | pad 28 |
| 4 | pad 29 |
| 5 | pad 30 |
| 6 | pad 31 (the Glitch) |

4. While the sequencer runs, every step with a note switches on what that slot holds: an effect (with its copy of the parameters) or the Glitch. The knob LED takes the colour of that effect; off = none.

- Assign the effects to the bottom row in Master FX first (C7).
- The track makes no sound in the DSP; its notes still go out over MIDI.
- Leaving the blue state switches the step-drummer of the track off.
""", ["FX sequencer: each knob = the Master FX bottom-row slot of its pair of steps."])

sec("song-pointer", "Song pointer (Master FX)",
    ["Pads 9-24 = steps 1-16: one held step = retrigger; two steps = momentary phrase; Shift + two = latched phrase.",
     "**Phrase mode:** Shift + step = start (end 16); a touch = the end; Shift + another step = new start; Shift + the start or the white pad 9 = exit."],
    """
- **One held step:** retrigger, the step repeats while you hold it.
- **Two held steps:** the pattern loops between them while you hold them.
- **Shift + two steps:** latched phrase; pad 9 turns white and touching it clears it.
- **Phrase mode (SC34.2):** Shift + a step enters the mode with that step as start and 16 as end. In the mode, touching a step moves the end (no retrigger); Shift + another step moves the start; Shift + the start or the white pad 9 exits.
- The playhead is white while the sequencer runs. When a project loads it starts off.
""", ["Song pointer: phrase between steps 3 and 10."])

sec("sample", "Captured sample",
    ["**Pad 32** (red) records the output; **pad 7** (yellow) plays it: K1 pitch, K2 mode (one-shot / gate / loop by colour), K3 start, K4 end.",
     "The sample can be assigned to the bottom row (pad 7 + a bottom pad) and can replace a drum (A8)."],
    """
### Recording (pad 32, Master FX and FX view)
- **Hold:** records while held (up to 3.46 s).
- **Short press:** records until the next press.
- **Master FX effects (from RC0.5):** the sample that plays goes through the Master FX effects; the capture records the output without them (in RC0-RC0.4 it was the other way round: the capture held the effects and the sample played without them).
- **Shift + pad 32:** armed: with the transport running it records the next bar; stopped, it starts when you press **Play**, from the first beat, and records that bar (from RC0.4; it used to start a bar late).

### Playing (pad 7)
- Press **pad 7**: it plays and its knobs move to K1-K4: **K1** pitch (±24 semitones), **K2** mode (yellow one-shot, green gate, blue loop), **K3** start, **K4** end (end < start = reversed).
- **Shift + pad 7:** a **latched** loop, in any mode, until you press pad 7 again (or pad 8); the same with Shift + a slot of the sample (from RC0.4; in RC0-RC0.3 it only played while held).
- The **loop** mode (K2 blue) is a different thing: it only plays while you hold the pad and stops when you release it.

### Assigning
Hold pad 7 and touch a pad of the bottom row: that slot plays the sample with a copy of its knobs.
""", ["Captured sample."])

sec("glitch-pad", "Glitch (pad 31) and its assignment",
    ["**Hold pad 31** (Master FX or FX view): the output breaks up and lags like a tape. K1 speed, K2 repeat, K3 delay, K4 chaos (lower half) or overload (upper half).",
     "**Pad 31 held + another bottom-row pad** = that slot is a Glitch too, with its copy of K1-K4."],
    """
- **Holding pad 31:** the master output is replaced by a tape head reading the recent audio (D6). On release the normal audio comes back.
- When pressed in Master FX, K1-K4 are its parameters:

| Knob | Function |
|---|---|
| K1 | Speed: fully up = normal; lower brakes like a tape; centre, stopped; below, backwards |
| K2 | Repeat size; at maximum, no repeat (continuous delay) |
| K3 | Delay, up to about 2.6 s |
| K4 | Lower half: **chaos** (random jumps back, cuts and reversals). Upper half: **overload** — late blocks (32 samples played again, then caught up: clicks at the normal pitch); from ~3/4 of the travel it also brakes: everything lower and slower, like an overloaded DSP (from RC0.2) |

- **Assign:** hold pad 31 and touch another bottom-row pad (without Shift): that slot stores a Glitch with the current copy of K1-K4 and lights turquoise. Touching that slot plays it with its values.
- **Two Glitch slots at once:** the last one you press plays; release it and the other one comes back with its values. Neither copies the other’s values (in RC0, pressing one while another played copied its knobs).
- Pad 31 lights while the Glitch plays.
""", ["Glitch: pad 31; also assigned to pad 28."])

sec("fila-inferior", "Assignable bottom row (Master FX / FX)",
    ["Hold an effect of the top rows (or pad 7, or pad 31) and touch a bottom pad: that slot stores the effect with a copy of its parameters. Saved with the project."],
    """
- **Pads 26-30** (and 31 as the Glitch): assignable slots. An unassigned slot is the stock performance effect of the FX view.
- **Assign:** hold the effect on top (pads 1-6), pad 7 (sample) or pad 31 (Glitch) and touch the slot.
- **Touching the slot:** loads its copy of the parameters and enables the effect while held. **Shift + slot** latches it.
- The assignments travel with the project and come back at power-on; when switching sessions the ones in RAM stay.
- The FX sequencer (C3) triggers these slots.
""")

sec("random-mutate", "Random-mutate per step",
    ["**BETA5 only.** In the probability view (**Shift + Pattern Settings**) row 4 gives each step a chance of its notes jumping an octave or moving to another note of the scale when they play."],
    """
1. On Synth 1 / 2 or MIDI 1 / 2, press **Shift + Pattern Settings**: the original’s probability view. Row 3 is still the chance of the step playing.
2. Hold a step that has notes and touch a pad of **row 4** (peach):

| Pad | Octave | Scale |
|---|---|---|
| 25 | — (off) | — |
| 26 | 6 % | — |
| 27 | — | 6 % |
| 28 | 6 % | 6 % |
| 29 | — | 12 % |
| 30 | 12 % | — |
| 31 | — | 25 % |
| 32 | 25 % | 50 % |

- **Scale:** the note changes to another note of the project’s scale, within the same octave. **Octave:** it goes one octave up or down (at random). Every note of a chord is drawn separately, each time the step plays.
- **Without Record** the changed note plays that once and the step does not change. **With Record** the changed note is written into the step (the sequence drifts).
- Tied notes are not changed.
- The value is stored in the step, with the pattern and the project. The drums do not have it.
""", ["Probability view: row 3 = the step’s probability (original), row 4 = random-mutate."])

# ===== D. DSP
sec("efectos-grid", "Master FX effects",
    ["Gater, Auto-Filter LP / HP, Digitise, Phaser and Vinyl on the master output, with 4 parameters each."],
    """
| Pad | Effect | K1-K4 |
|---|---|---|
| 1 | Gater | division, depth, width, smoothing |
| 2 / 3 | Auto-Filter low / high pass | speed, depth, resonance, centre frequency |
| 4 | Digitise | sample-rate reduction, bit reduction (K3 and K4 do nothing) |
| 5 | Phaser | speed, depth, feedback, mix |
| 6 | Vinyl | crackle, hiss, tone (low pass), wear (high pass) |

- Hold = active; Shift = latched. The brightness of the knob LEDs shows the value.
""")

sec("vca-vcf", "VCA-VCF of the MIDI tracks",
    ["DJ / LP / HP 12 and 24 dB / band pass / notch filters, effects (saturation, folding, wavefold, ring, comb, chorus), VCA with ADSR and LFO."],
    """
- Per-voice chain: VCA → effect → filter, or filter → VCA → effect (pad 29).
- State-variable filter with key tracking; 24 dB LP / HP = two stages.
- VCA with ADSR, velocity, gain up to +18 dB with soft saturation.
- Inverse-ramp LFO to level, filter, pitch, shape and morph.
- The default values let the input through clean.
""")

sec("osciladores", "Oscillators and paraphony",
    ["Continuous morph sine → triangle → saw → square, wavefold / slope / width, second oscillator with FM, ring, soft sync and bitwise modes; two paraphonic notes."],
    """
- **OSC 1:** WAVE is a continuous morph (0 sine, 42 triangle, 84 saw, 126 square); SHAPE folds the sine / triangle, bends the saw or changes the square’s width. Envelope and LFO move pitch, shape and morph.
- **OSC 2 (pad 28):** its own TUNE / FINE / WAVE / SHAPE; MIX, FM (OSC 2 → OSC 1 phase), RING and BITSYNC (soft sync every N cycles, xor, or, nor, and, nand).
- **Paraphony:** one note = unison; two = one per oscillator.
""")

sec("va-drum", "VA-drum engine",
    ["Oscillator made for percussion: one-shot VCA, dedicated decay envelopes for pitch (Sustain knob) and filter (Release knob), white noise and random values instead of the LFO."],
    """
| Knob | In VA-drum |
|---|---|
| Attack / Decay | VCA attack and decay (one-shot) |
| Sustain | decay of the pitch envelope |
| Release | decay of the filter envelope |
| LFO speed | white noise level |
| LFO → destination | random value per block to that destination |

- Pad 31: velocity also sets the level of the pitch and filter envelopes.
- *Kick:* sine, Decay ~70, Sustain ~30, Env → pitch to the right. *Snare:* more noise, short Decay, band pass.
""")

sec("granular", "Granular synth",
    ["Up to **16 grains per track** from any sample of the pack or the capture, with interpolation and window; on the second DSP core.",
     "K1 pitch, K2 position, K3 scan / freeze, K4 size, K5 density, K6 zone, K7 LFO → position, K8 envelope → position; Shift: fine, sprays, reverse, window, slicer (or stretch, BETA5 only), LFO → size, source."],
    """
**Magenta** state of pad 27; **pad 2** of the page row = granular page.

| Knob | Alone | With Shift |
|---|---|---|
| K1 | Pitch, ±24 semitones | Fine, ±1 semitone |
| K2 | Position in the sample | Position spray |
| K3 | Scan: centre = frozen, right moves forward, left backwards | Probability of a reversed grain |
| K4 | Grain size, 5-500 ms | Pitch spray (±12 st) |
| K5 | Density, 1-16 overlapping grains | Window: rectangular → triangular → percussive |
| K6 | Length of the scan zone | Note mode: pitch / slicer / stretch (stretch in BETA5 only) |
| K7 | LFO → position | LFO → size |
| K8 | Envelope → position | **Source**: pack sample 1-64, to the left the capture. **BETA5 only:** a long travel over five zones: the capture (red) and the sample Drum 1 (orange), 2 (yellow), 3 (violet) and 4 (teal) has now; it stays fixed even if the drum changes its sample; dim white = no drum has that sample any more |

- **Pitch mode:** the note changes the pitch of the grains; with two notes they are shared between both.
- **Slicer mode:** the note picks one of 16 slices of the sample.
- **Stretch mode (BETA5 only):** the stretch from K2 to the end of the sample lasts **K3** steps (1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48 or 64; K3’s LED shows it) at any tempo, without changing the pitch, and starts again in step with the start of the transport; the notes change the pitch as in pitch mode. With the transport stopped it stands still. K7 / K8 do little in this mode.
- It goes through the VCA-VCF of page 1. It shares its saved values with the oscillator page.
""", ["Granular page (pad 2, magenta engine)."])

sec("glitch-dsp", "Glitch engine",
    ["A tape head over a stereo circular buffer of the master (2.7 s) in the external DSP memory: variable speed, repeats with fades, chaos."],
    """
- The master is recorded all the time into a 2.7 s stereo ring.
- On press, the head starts at “now − delay” with a short fade-in.
- Negative speed = backwards; near 0 = tape stop.
- Repeat: at the end of each segment it goes back to its start; at maximum, continuous delay without fades.
- Chaos: random jumps back, silences and reversals.
- Overload (K4 in the upper half, from RC0.2): imitates what was heard when the DSP sample memory was really overloaded (SC35DB): in every 32-sample block, with a probability that grows with K4, the block “comes late” (the head goes 32 samples back and catches up at the next late block); from K4 ≈ 96 the head also brakes down to 0.43 ×. It is a simulation: the DSP is not loaded, so the sequencer, the MIDI clock and the rest of the audio are not affected.
""")

sec("drums-dsp", "Drum DSP",
    ["Ring mod, pitch and filter envelopes, LFO, DJ / band pass / notch / comb / tilt filters, bitcrush, start point, distortions and sidechain between drums."],
    """
- State-variable filter per drum (DJ, band pass, notch), comb with feedback and the stock EQ tilt.
- Ring mod with its own oscillator, tremolo / vibrato LFO, soft / hard / folded distortion, bitcrush.
- **Sidechain between drums:** Shift + FX and Octave ▼: ducking pages per drum (rows 3-4) and which drum triggers it (row 1, pads 5-8).
""")

sec("entradas", "Audio inputs and returns",
    ["Line input (normal or inverted) as a synth source; reverb / delay returns through strips 3 / 4 with feedback."],
    """
- The synths can use input 1 / 2 (or inverted) instead of the noise (A6).
- With the Setup returns on strips 3 / 4, the sends of those strips send the return again, already processed by the VCF / FX of the track, to the reverb and the delay.
""")

# ===== E. Miscellaneous
sec("guardado", "What is saved and where",
    ["Project: drums, Master FX slots, synth source, reverb / delay parameters. Device: MIDI track engine. Volatile: OSC 2, latched effects."],
    """
| What | Where |
|---|---|
| New drum knobs, Master FX slots, synth source, reverb / delay | The project |
| MIDI track engine (pad 27, granular, sequencer), values of pages 1-2, step-drummer enabled | Device settings |
| Notes and pitch row of the step-drummer, FX sequencer values | The pattern |
| Captures used as drums | The pack, on save (A8) |
| OSC 2, MIX, FM, RING, Shift parameters of the granular, latched effects, song pointer | Not saved |
""")

sec("instalar", "Installing and going back",
    ["`tools/ct_uploader.html` sends the `.syx` over Web MIDI; it only accepts verified firmwares. Recovery: Scales + Preset + Note at power-on."],
    """
0. **Without building:** `tools/rc_uploader.html` patches the official firmware ([Novation download](https://components.novationmusic.com/api/v2/firmwares/168/file)) in the browser and sends it. Pick RC0.5, RC0.5S, BETA5 (or the earlier RC0.4 / RC0.4S, BETA2) or “Official”.
1. Open `tools/ct_uploader.html` in Chrome and connect the Circuit Tracks over USB.
2. Pick the `.syx` from `firmware/<version>/`: the uploader checks its SHA-256.
3. Send. Novation’s bootloader is not modified.
- **Going back:** send another version or the official firmware. If the device does not start: hold **Scales + Preset + Note** at power-on (bootloader recovery mode).
- The RC branch does not publish `.syx` files: they are generated with `tools/patch_official.py` from the official firmware.
- **RC0.6** (seventh release candidate) = RC0.5 + two fixes (the LFO of the Auto-Filter and of the Phaser starts when the effect comes on; the dim white of Clear no longer pulses); RC0.5 = RC0.4 + the captured sample in front of the Master FX effects; RC0.4 = RC0.3 + the fixes of SC38.2-SC38.6; RC0.3 = SC38, RC0.2 = SC37.5, RC0.1 = SC37.4, RC0 = SC36.2.
- **BETA5** (beta) = SC39.6: RC0.5 + what this manual marks **BETA5 only** (granular stretch, MIDI Thru Merge / Filter, Clear + page pad, patches by voice mode, split keyboard, random-mutate, patches of the own synth, granular source selector, saving the synth’s patch, macro knob destinations, copying projects, type knobs as colours). Only random-mutate and the split keyboard are tested on the device: use it with a backup of the SD card.
- **Safer build:** RC0.6S = RC0.6 without features that write to the SD card (no A8, no remote diagnostics; = RC0S + what RC0.1-RC0.6 add outside the SD card). **Back up the SD card before installing** any version.
- New features and fixes of every version: `CHANGELOG.md`.
""")

sec("herramientas", "Development and diagnostic tools",
    ["Reproducible builders, ARM / DSP emulators with tests through the real routes, `verify_builds.py`, remote diagnostics over USB (`ctremote.py`)."],
    """
- `tools/build_scNN.py`: every version is built from the official firmware; `verify_builds.py` checks they all give the same SHA-256.
- `tools/emu_*.py`: emulation tests (Unicorn for the ARM, dsp56300 for the DSP).
- `tools/ctremote.py` + `rdiag`: the PC reads memory, card items and the device’s capture over SysEx. Only in the diagnostic builds and in SC35 / SC36: **SC36.1, SC36.2, the RCs (RC0 … RC0.5 and their safer builds) and BETA5 do not include it**, to leave the USB protocol alone.
- `docs/NOTAS.md`: technical map of everything found (in Spanish).
""")

sec("tablas-midi", "MIDI tables",
    ["MIDI engine: CC 74/71/79/73/75/70/72/91/59/26/27/20/21/37/39/30/31/52/54 + NRPN 4:x; drums NRPN 5-8:1-12; Master FX NRPN 9:0-19 (channel 16)."],
    """
### MIDI track engine — track channel

| Value | Message | Value | Message |
|---|---|---|---|
| Filter | CC 74 | TUNE | CC 26 |
| Resonance | CC 71 | FINE | CC 27 |
| Env → filter | CC 79 | WAVE | CC 20 |
| Attack | CC 73 | SHAPE | CC 21 |
| Decay | CC 75 | TUNE 2 | CC 37 |
| Sustain | CC 70 | FINE 2 | CC 39 |
| Release | CC 72 | WAVE 2 | CC 30 |
| Effect | CC 91 | SHAPE 2 | CC 31 |
| Gain | CC 59 | MIX | CC 52 |
| LFO speed | NRPN 0:76 | RING | CC 54 |

The rest, NRPN MSB 4 with LSB = code (4, 12, 13, 15, 16, 21-26, 32, 33).

### Drums — NRPN MSB 5 / 6 / 7 / 8 = Drum 1-4
LSB 1 pitch env., 2 ring (frequency), 3 LFO, 4 LFO speed, 5 env → cutoff, 6 resonance, 7 envelope shape, 8 ring (amount), 9 filter mode, 10 start point, 11 bitcrush, 12 distortion type.

### Master FX — channel 16, NRPN MSB 9
LSB = 4 × set + knob: Gater 0-3, Auto-Filter 4-7, Digitise 8-11, Phaser 12-15, Vinyl 16-19.
""")
