"""English text of the user manual (tools/make_manual.py writes docs/MANUAL.en.md, docs/manual/en.html and the English feature list of README.md).
SEC[id] = (title, summary bullets, detail, figure captions in order); LABEL = the words drawn on the panel figures; UI = the fixed strings of the pages.
Keep the same section ids, order and figures as the Spanish source in make_manual.py."""

GROUPS = {"A": "Shortcuts and usability", "B": "Exposed controls", "C": "New control modes", "D": "DSP", "E": "Miscellaneous"}

UI = dict(
    md_title="Feature list — CIRCUIT-HACKS ({v})",
    md_intro="Circuit Tracks running the official firmware 1.2.1 (build 4486), patched. Anything not described here works as on the original device. "
             "Every feature in one line, by topic. **The user manual is the [guide by views](GUIA.en.md)** (in colour: [guide.html](https://ghillermo.github.io/CIRCUITS-HACKS-RC/guide.html)); the CCs / NRPNs, in the [MIDI reference](MIDI.en.md). "
             "Illustrated version of this list: [https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html). Versión en español: [`docs/MANUAL.md`](MANUAL.md).",
    conventions="**Conventions:** pads 1-32 from top left to bottom right (row 1 = 1-8 … row 4 = 25-32); knobs K1-K4 top, K5-K8 bottom; “Shift + X” = hold Shift.",
    index="Index",
    html_title="Feature list — CIRCUIT-HACKS",
    cover="Feature list of the Circuit Tracks mod",
    cover_fw="Official firmware 1.2.1 (build 4486) + {v}",
    html_conv="<strong>Conventions.</strong> Pads 1-32 from top left to bottom right (row 1 = 1-8 … row 4 = 25-32). Knobs K1-K4 on top and K5-K8 at the bottom. "
              "“Shift + X” = hold Shift while using X. The colours of the diagrams are approximate; a dim pad is drawn translucent. Anything not described here works as on "
              "the original device (see Novation’s official user guide).",
    toc="Feature index",
    other='<p class="lang"><a href="index.html">Versión en español</a> · <a href="guide.html"><strong>Guide by views (user manual)</strong></a> · <a href="midi-en.html">MIDI reference</a></p>',
    footer="CIRCUIT-HACKS {v} · This mod is not affiliated with Novation. Circuit Tracks is a trademark of Focusrite Audio Engineering Ltd.",
    features="Features ({v})",
    features_manual="User manual: [guide by views](https://ghillermo.github.io/CIRCUITS-HACKS-RC/guide.html) ([`docs/GUIA.en.md`](docs/GUIA.en.md)) · [MIDI reference](docs/MIDI.en.md) · this list: [illustrated colour](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html) · [short](docs/MANUAL.en.md) · **guide in plain words, illustrated** ([web](https://ghillermo.github.io/CIRCUITS-HACKS-RC/plain.html), [PDF](https://ghillermo.github.io/CIRCUITS-HACKS-RC/plain.pdf); first draft by [reddit.com/u/luxurysoft1337](https://www.reddit.com/user/luxurysoft1337/), [the original guide](https://files.catbox.moe/xgogqy.pdf)). New features and fixes of every version: [`CHANGELOG.md`](CHANGELOG.md#changelog). What is marked **since RC2** is new in RC2 / RC2S (not in RC0.9).",
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
| 17 | MIDI 1 / 2 Preset: **Clear + a page pad (1-5)** | The values of that knob page back to their initial values (C1, **since RC2**) |
| 18 | Advanced Setup: **Duplicate** | MIDI Thru: Thru → Out 2 → Merge → Filter (B7, **since RC2**) |
| 19 | **Synth 1 + Synth 2** together | Split keyboard: Synth 1 on top, Synth 2 below (A12, **since RC2**) |
| 20 | **Shift + Pattern Settings**, a step, **row 4** | Random-mutate of the step: random octave / scale changes (C8, **since RC2**) |
| 21 | MIDI 1 / 2 Preset: **pads 9-24**, **Clear + pad** twice, **Duplicate + A + B**, **Octave ▼ / ▲** | Patches of the own synth: load, save, exchange, page (A14, **since RC2**) |
| 22 | MIDI 1 / 2: **Clear + the track button** | The track engine back to its initial values (A14, **since RC2**) |
| 23 | Synth 1 / 2 Preset: **Clear + pad** twice | Saves the synth’s patch into that slot of the pack (A15, **since RC2**) |
| 24 | Synth source view: **pad 32** | Editor of the macro knob destinations (A16, **since RC2**) |
| 25 | Projects: **Duplicate + pad A**, **Duplicate + pad B** | Copies project A into slot B, in another pack too (A17, **since RC2**) |
| 26 | MIDI 1 / 2 Preset: **Duplicate + slot A**, another pack, **Duplicate + slot B** | Copies an own-synth patch into another pack (**since RC2**) |
| 27 | Sidechain (**Shift + FX**): **K1-K4**, **K7 / K8** | Side-chain of the chosen track; attack / release of the master compressor (**since RC2**) |
| 28 | Setup: **Record** | Record into the synth what the MIDI track sends it: yellow = yes (**since RC2**) |
| 29 | **Pattern Settings** twice, **row 4** | Step frequency: it plays every n plays of the pattern (**since RC2**) |
| 30 | Pattern Settings: **pad 25** | Dynamics (row 3) and random-mutate (row 4); **Clear + pad 25** clears them from the pattern (**since RC2**) |
| 31 | Pattern Settings: **pads 26 / 27 / 28** | Nudge, fractal order, deconstructed order (**since RC2**) |
| 32 | Patterns: **Shift + Octave ▲ / ▼** | Pattern chain mode on / off (**since RC2**) |
| 33 | Mixer: **Shift + pads 9-16** | Repeats of the current scene (**since RC2**) |
| 34 | Setup: **pad 29 / pad 30**, then a channel pad | Listen / output channel of the project’s Program Changes (B7, **since RC2**) |
| 35 | **Shift + Clear** | Metronome / count-in in four states; with the count-in, Record + Play = one bar before recording (**since RC2**) |
| 36 | Pattern Settings: **Shift + pad 25**, **Shift + pads 27-32** | The pattern's arpeggiator on / off and its order; chords of the sequence and notes held together, one a step (**since RC2**) |
| 37 | **Shift + Scales** | Custom scale editor: up to 7 notes and a period; one iteration a row (**since RC2**) |
| 38 | Step-drummer: **pad 32**; velocity page: **pads 17-24** | Pitch-vel toggle (transpose in the scale / velocity) and page 2's own destination (**since RC2**) |
| 39 | **Shift + Play** | Quantize the pattern the selected track plays (**since RC2**) |
| 40 | MIDI 1 / 2 in the sample mode: **Note twice**; **a held step + a sample** | Picker of the pack's 64 samples (Octave ▼ / ▲) and a sample flip per step, also live with Record (**since RC2**) |
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
- **since RC2:** in a drum's Preset view, **Preset again** turns the chromatic view on / off (as Shift + Preset).
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
- On the levels page of the Mixer (the normal one, Octave ▲). On the pan page (Octave ▼), Shift + knob moves the pan as always (**since RC2**: it turns the cue mode on / off, see the guide by views).
- The jump works like a turn of the knob: it goes out over MIDI and, while recording, it is written into the automation.
- On the original, Shift + knob did the same as the plain knob: no function is lost. Clear + knob (delete the automation) and Master FX (Mixer twice) do not change.
- From RC0.3 (also in RC0.3S).
""", ["Mixer: Shift + knob right = level 100, left = 0."])

sec("teclado-partido", "Split keyboard Synth 1 + Synth 2",
    ["**Since RC2.** Hold **Synth 1** and press **Synth 2** (or the other way round): the two top rows play Synth 1 and the two bottom rows Synth 2."],
    """
- Each half is its synth’s keyboard: its scale, octave and velocity (the same keys as the lower half of its Note view), in its colours.
- The knobs and Octave belong to the synth you pressed first.
- **Leaving:** any track or view button (Note, Preset, Mixer, FX, a single Synth…). Held notes are released. Play, Record, Octave and Shift do not close it.
- Synth 1 or Synth 2 alone work as always (twice = the source view, A6).
""", ["Split keyboard: rows 1-2 = Synth 1, rows 3-4 = Synth 2."])

sec("colores-patch", "Synth patches by voice mode",
    ["**Since RC2.** In the Preset view of Synth 1 / 2 every patch is drawn by its voice mode: **mono dark blue**, **glide lavender**, **poly as always**."],
    """
- Mono = dark blue; mono with glide (Mono AG) = lavender; poly = the track colour, as on the original. The chosen patch is drawn lighter.
- The modes are read from the card when the pack, the page or the patch changes, and every 4 s.
- In Advanced Setup pads 22 / 23 no longer light up (they never did anything there).
""", ["Preset view of Synth 1: mono dark blue, glide lavender, poly the track colour."])

sec("patches-midi", "Patches of the own synth (MIDI 1 / 2)",
    ["**Since RC2.** In the Preset view of MIDI 1 / 2, rows 2 and 3 are 16 patch slots of the track engine: touch = load (the root note sounds), **Clear + pad** twice = save, **Duplicate + A + B** = exchange; **Octave ▼ / ▲** = 4 pages (64 slots per pack)."],
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
- In the safer build (RC2S) it does not write to the SD card: the Save LED turns red.
""", ["Preset view of MIDI 1: rows 2-3 = patches of the own synth."])

sec("guardar-patch", "Saving the synth’s patch into the pack",
    ["**Since RC2.** In the Preset view of Synth 1 / 2: **Clear + pad** asks (it blinks white) and **Clear + the same pad again** saves the patch as it sounds into that slot."],
    """
- The original device cannot save patches (only Components can). What is saved is the patch in use with every change: the knobs, what came in over MIDI and the macro destinations (A16).
- **Clear + pad** = a question, nothing is written. **Clear + the same pad** within ~5 s = saved: it replaces the patch that was there and the slot becomes the chosen one. Clear + another pad moves the question; a touch without Clear, or the time, drops it.
- Any of the 4 pages (128 slots). A slot past the end of the bank too: the slots in between stay empty.
- The saved patch keeps the name of the one that was loaded. Synth patches are managed with Components; `tools/patchtool.py slist / sname` lists and renames them on the card.
- The own-synth patch that shares the slot (A14) is not touched.
- Duplicate + A + B still copies / exchanges patches (A8).
- In the safer build (RC2S) it does not write to the SD card: the Save LED turns red.
""", ["Preset view of Synth 1: Clear + pad asks (it blinks), Clear + the same pad saves."])

sec("destinos-macro", "Macro knob destinations",
    ["**Since RC2.** In the synth source view (A6), **pad 32** opens the editor: a knob picks its macro, **Octave ▼ / ▲** steps the field and the pads draw the number."],
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
    ["**Since RC2.** In the Projects view: **Duplicate + pad A** picks the project (it blinks yellow) and **Duplicate + pad B** copies it into that slot, of the same pack or of another one."],
    """
- **Duplicate + pad A** (a slot with a project) = the source. Duplicate + A again forgets it.
- **Duplicate + pad B** = the copy. An empty B is written at once and turns yellow; a B that holds a project blinks white and **Duplicate + B** must be repeated within ~5 s to replace it. The slot of the loaded project is never written.
- **To another pack:** pick the source, load the other pack, open Projects and Duplicate + pad B. The source serves several copies; it is lost at power-off or when Master FX is opened.
- What is copied is the project as saved on the card (save first if you changed it). While it copies (a few moments) the device does not respond.
- A project stores patch and sample numbers, not the sounds: in another pack it plays with that pack’s patches and samples.
- In the safer build (RC2S) it does not write to the SD card: the Save LED turns red.
""", ["Projects view: Duplicate + A = the source (yellow, blinking), Duplicate + B = the copy."])

# ===== B. Exposed controls
sec("patches-entre-packs", "Own-synth patches to another pack",
    ["**Since RC2.** In the Preset view of MIDI 1 / 2: **Duplicate + slot A**, load another pack and **Duplicate + slot B** copies the patch (engine, parameters and name)."],
    """
- **Duplicate + slot A** with the source pack loaded: the patch is remembered.
- Load the other pack and go back to the Preset view of MIDI 1 / 2: **Duplicate lights yellow** (a patch is waiting).
- **Duplicate + slot B** writes it there. It serves several slots.
- Inside one pack, Duplicate + A + B still exchanges the two patches.
- Nothing is copied when A is empty or when the destination pack lacks that patch bank.
- In the safer build (RC2S) it does not write to the SD card: the Save LED turns red.
""", [])

sec("knobs-drums", "Drum knobs as printed on the panel",
    ["Every knob does what its label says, with a second layer on Shift: ring mod, envelopes, filters (DJ, BP, notch, comb, tilt), LFO, start point, bitcrush and distortion."],
    """
| Knob | Alone | With Shift |
|---|---|---|
| K1 Oscillator | Pitch (exact semitones; **since RC2**: the stock one, continuous, with the chromatic view on top) | Pitch envelope amount |
| K2 Osc mod | Ring mod frequency | Ring mod amount |
| K3 Amp envelope | Left: decay; past its maximum, **attack** (centre neutral) | Left: sample **start**; right: **cut** (centre = whole) |
| K4 Filter envelope | Envelope → cutoff | Envelope shape |
| K5 Filter frequency | Filter / EQ (by default the stock EQ tilt) | **Filter mode**: stock EQ tilt (default), band pass, notch, comb, DJ |
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

sec("sidechain-comp", "Side-chain and master compressor on the knobs",
    ["**Since RC2.** In the Sidechain view (**Shift + FX**): **K1-K4** = attack, hold, decay and depth of the side-chain of the chosen track; **K7 / K8** = attack and release of the master compressor."],
    """
- **K1-K4** act on the track of the last side-chain preset you touched (Synth 1 until you touch one); their LEDs take that track’s colour. A preset pad still writes its four values.
- **K7** = attack and **K8** = release of the master compressor (the one switched on in Advanced Setup), white with their value. Threshold and ratio are fixed.
- The compressor’s attack and release are saved with the project (see “Master FX since RC2”).
- **since RC2:** on the drum pages (Octave ▼), **K1-K4** = attack, hold, decay and depth of the side-chain of the drum of the last preset touched, in the drum's colour; saved with the project, and a preset brings them back to its own.
""", [])

sec("grabar-interno", "Recording the internal MIDI routes",
    ["**Since RC2.** In the Setup view, **Record** decides whether what a MIDI track sends to an internal synth over a shared channel is also recorded into that synth: **yellow = yes**, dark = no (the default)."],
    """
- When MIDI 1 / 2 shares a channel with Synth 1 / 2, what you play or turn on the MIDI track sounds on the synth without a cable. By default that is **not** recorded into the synth’s pattern, only into the MIDI track’s.
- With **Record yellow** (Setup view, not Advanced Setup) it is recorded into the synth too, as if it came from external MIDI: useful to record scale or octave changes made from the MIDI track in real time.
- It switches off at power-off. With the toggle on, the auditions of the step-drummer of Synth 1 / 2 are recorded as well.
""", [])

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
     "**since RC2:** MIDI Thru with four modes (Duplicate in Advanced Setup): Thru, Out 2, **Merge** (DIN In + the device’s MIDI) and **Filter** (DIN In without the channels the device listens to).",
     "**since RC2:** own **Program Change** channels: pads 29 / 30 show and pick the listen / output channel (16 by default); what is received is forwarded on the output one.",
     "**since RC2:** **metronome with count-in**: Shift + Clear walks no metronome, metronome, count-in only and both; the count-in is one bar before recording."],
    """
| Where | Function |
|---|---|
| Setup, pad 16 | Channel 16 (project and FX): receive and send |
| Setup, pad 22 | The reverb return goes through mixer strip 3 |
| Setup, pad 23 | The delay return goes through strip 4 |
| Setup, channels | MIDI 1 / 2 may use a channel already used by another track |
| Advanced Setup, Duplicate | MIDI Thru: Thru → Out 2 → **Merge** → **Filter** (**since RC2**) |
| Setup, pad 29 / 30 | Listen / output channel of the project’s Program Changes (**since RC2**) |
| Any view, Shift + Clear | Metronome: off / on / count-in only / count-in and metronome (**since RC2**) |

- **Internal loopback:** if a MIDI track shares its channel with a synth or the drums, what it sends reaches them internally.
- Pads 22 / 23 light cream (reverb) and peach (delay), the colours of the FX view; dim = off.

### Metronome and count-in (since RC2)
**Shift + Clear**, in any view, walks four states (the original only turned the metronome on and off):

| State | Clear LED while Shift is held |
|---|---|
| No metronome | red |
| Metronome | green |
| Count-in only | magenta |
| Count-in and metronome | cyan |

- With the count-in, **Record armed and Play from stopped**: one bar of count-in plays (4 clicks, the stock metronome's sound, at the project's tempo) with Record blinking red; then recording starts. **Play** during the count cancels it.
- Without Record armed, Play starts at once, as always.
- The metronome is the stock setting; the count-in is saved with the project.
- **Click volume:** the stock's, pressing **Tempo/Swing** and turning **K5**.

### MIDI Thru: Merge and Filter (since RC2)
The original only lets the Thru jack be **Thru** (a hardware copy of DIN In, Duplicate dim red) or **Out 2** (a second MIDI output, green). Duplicate in the Advanced Setup view now steps through four modes:

| Mode | Duplicate LED | Out of the Thru jack |
|---|---|---|
| Thru | dim red | DIN In, by hardware |
| Out 2 | green | The device’s MIDI |
| **Merge** | yellow | DIN In and the device’s MIDI |
| **Filter** | blue | DIN In except the messages on the channels the device listens to |

- DIN In SysEx is not copied in Merge / Filter. In Merge, if the device follows the DIN In clock and has Clock Tx on, the Thru jack carries two clocks: switch Clock Tx off.
- It is saved in the settings. With the original firmware, Merge / Filter go back to Out 2.

### Program Change channels (since RC2)
In the Setup view (not Advanced Setup):

1. **Pad 29 (PGM Rx)**: pads 1-16 show the **listen channel** (white = the chosen one, dim white = the rest). This first touch does not change PGM Rx.
2. Touch a channel pad to pick it.
3. **Pad 29 again** = PGM Rx on / off, as always.
4. **Pad 30 (PGM Tx)**: the same with the **output channel**.
5. A track button or another pad: pads 1-16 show the tracks’ channels again.

- Both are **16** by default, as on the original. They are saved in the settings; with the original firmware they go back to 16.
- **Receive** (PGM Rx): a Program Change on the listen channel picks the project. If the listen channel is not 16, channel 16 no longer picks projects. If it is the channel of Synth 1, Synth 2 or the drums, it goes to that track.
- **Forward**: with PGM Tx, what arrives on the listen channel goes out again on the output channel.
- **Send** (PGM Tx): a project picked on the panel sends its Program Change on the output channel. The project’s CCs stay on 16.
- In Setup, Synth 1 / 2 pick their track also when you entered Setup from their view (before, they arrived as Preset).
- Patch flip (B8) still goes out on its MIDI track’s channel, never on the general output channel.
""", ["Setup: pad 22 = reverb return through strip 3 (cream), pad 23 = delay return through strip 4 (peach)."])

sec("patch-flip", "Patch flip on MIDI 1 / 2",
    ["Pad 26 of the MIDI Preset view: every note is sent as a Program Change (exclusive with the track engine)."],
    """
- MIDI 1 / 2 Preset view, **pad 26**: the notes of the track send Program Change.
- It switches off when the track engine is switched on (pad 27), and the other way round.
""")

# ===== C. New control modes
sec("motor-midi", "Engine of the MIDI tracks (pad 27)",
    ["Pad 27 of the MIDI 1 / 2 Preset view picks the engine: off → **line** → **oscillator** → **VA-drum** → **granular** → **sample** (since RC2) → **FX sequencer**.",
     "Pads 1-5 pick the knob page; 28 = two oscillators, 29 = chain order, 30 = step-drummer, 31 = velocity (VA-drum). **since RC2:** Clear + a page pad = the values of that page back to their initial values; rows 2-3 hold patches (A14)."],
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
| cyan | **sample**: a pack sample one-shot, at the note's pitch (C15, since RC2) |
| blue | **FX sequencer** (C3) |

### Pads of the Preset view

| Pad | Function |
|---|---|
| 1-5 | Knob page: 1 VCA-VCF, 2 OSC 1 (granular with that engine), 3 OSC 2, 4 sequenceable values, 5 modulation |
| 25 | CC editor (A10) |
| 26 | Patch flip (B8) |
| 27 | Engine |
| 1-5 | Knob page. **Clear + the pad** (since RC2): the values of that page (with and without Shift) go back to their initial values; the engine stays |
| 28 | One / two oscillators (only with the oscillators or VA-drum; dark with the other engines) |
| 29 | Chain order: VCA → FX → filter / filter → VCA → FX (**since RC2**: Shift + 29 = gate retrigger; off = legato) |
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

Page 3 (OSC 2): K1 TUNE 2 / FINE 2, K2 SHAPE 2 / FM, Shift + K3 RING, K7 WAVE 2 (**since RC2**: all eight without Shift, K1 TUNE 2, K2 SHAPE 2, K3 MIX, K4 FM, K5 FINE 2, K6 BITSYNC, K7 WAVE 2, K8 RING). Page 4: the 8 sequenceable values (B6). Page 5: ADSR on top, LFO at the bottom (**since RC2**: Shift + K8 = the LFO's shape, six shapes).

- The engine values are saved in the device (not with the project); the OSC 2 ones, the Shift knobs of the granular and the oscillator and pads 28 / 29 too since Beta 1.28 (before, they went back to their defaults at power-up).
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

- Pad 30 bright = view open; dim = closed. On MIDI, **Shift + pad 30** disables the step-drummer. **since RC2:** on MIDI, dim = off, bright = on.

### Controls

| Control | Function |
|---|---|
| Pads 1-16 | The 16 steps of the half shown; bright = has a note, white = playing. Touch = listen; **Shift + touch** = add / remove the note |
| Pads 17-24 | Destination of the pitch row (MIDI) / macro 1-8 (synths) |
| K1-K8 | The 8 pairs of steps (the playing one is white) |
| Octave ▲ / ▼ | Pitch / velocity page |
| 1-16 / 17-32 | The other half of the pattern |

- **Pitch on MIDI:** the pair value offsets the destination: pitch of both oscillators, OSC 2 pitch, WAVE, FM, MIX, env → filter, SHAPE, decay (64 = no change: it adds to or takes from the value on the engine's page; **since RC2**: the knob LED dim at the centre and brighter the further it goes).
- **Pitch on the synths:** the value is the macro position, written as automation.
- Each step keeps the pitch of its first note; a new note takes the pair’s or the previous one.
- **Real-time recording:** with Record on, playing a step also records it on the step that plays, with its microstep.

### Page 2 and the pitch-vel toggle (since RC2)

- **Velocity page, pads 17-24** = page 2's own destination (the same pad again = none). With a destination the knobs write the pair's value (MIDI: from 64, in REL's lane, which is neither played nor recorded while the step-drummer is on; synths: that macro's automation, from 0). With no destination and no toggle, page 2 does nothing.
- **Pad 32** = the **pitch-vel** toggle (green): on top of their destinations, the pitch page transposes every note of the track by one degree of the project's scale (stock or custom) every 8 knob steps (MIDI −8 … +8 from the centre, synths 0 … +16 from 0) and the velocity page also sets the velocity, as before. With the toggle, the pitch page's pitch destinations do not move the own synth. Saved with the project.
- On the synths an empty pair starts at 0.
""", ["Step-drummer view (MIDI 1)."])

sec("fx-seq", "FX sequencer",
    ["**Blue** state of pad 27: the step-drummer of the track picks, for each pair of steps, **a slot of the Master FX bottom row** (0 = none); it plays on the steps with a note.",
     "The knob moves slowly (**one slot every ~48 steps of the turn**) and lights in the **colour of the chosen effect**. **A slot with no effect assigned does nothing:** assign the effects to the Master FX bottom row first (see “Assignable bottom row”). **since RC2:** at the end of the travel there is the **random** value (white LED): on every step with a note one of the list plays at random (the slots with an effect assigned and the mechanical gesture of pad 31)."],
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
    ["**Since RC2.** In the probability view (**Shift + Pattern Settings**) row 4 gives each step a chance of its notes jumping an octave or moving to another note of the scale when they play."],
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
sec("frecuencia-dinamicas", "Step frequency and dynamics",
    ["**Since RC2.** In the probability view of the note tracks: **row 4 = every how many plays of the pattern the step sounds** (1-8). With **pad 25 of Pattern Settings**: row 3 = random **dynamics** (velocity, position and length), row 4 = random-mutate."],
    """
- **Mode 1** (press **Pattern Settings** twice): row 3 = the usual probability; **row 4 = frequency**, in yellow: with n the step sounds on the last of every n plays of the pattern. Each pattern counts its plays from Play.
- **Mode 2** (**pad 25** of the Pattern Settings view): row 3 = dynamics, row 4 = random-mutate.
- **Clear + pad 25** (since RC2): clears the dynamics and the random-mutate of every step of the pattern; the frequency stays.

| Pad (row 3) | Micro steps (position and length) | Velocity | |
|---|---|---|---|
| 1 | — | — | no change |
| 2 | −2 to +2 | — | drunk |
| 3 | −2 to +2 | 0 to +32 | drunk and accents |
| 4 | — | 0 to +32 | accents |
| 5 | −1 to +3 | 0 to +32 | dragging and accents |
| 6 | −1 to +3 | — | dragging |
| 7 | — | −32 to +32 | balanced dynamics |
| 8 | — | −32 to +64 | accent dynamics |

- Everything is saved with the step. With **Record** and mode 2 on the screen, what sounds (the mutated note, the dynamics) is written into the pattern.

### On the drums (since RC2)

- The same view for a drum (Pattern Settings twice = mode 1; pad 25 of its Pattern Settings = mode 2): mode 1 row 4 = frequency; mode 2: row 3 = dynamics (they only delay the hit inside its step), pads 25-28 = **random-mutate of the sample**: none, 25 % of ±1 (the next one in its row of 8), 25 % of ±8 (another row), 12 % of each.
- They live in bytes of the pattern the stock does not use: they travel when duplicated and with Nudge; the first time they are cleared in the project's 32 drum patterns.
""", [])

sec("cadenas", "Pattern chains and scenes",
    ["**Since RC2.** Every pattern can carry a rule “play n times, then jump to B; the next time, to C”. **Shift + Octave ▲ / ▼** in the Patterns view switches the **chain mode** of the whole project on / off; every scene remembers the mode it was saved in."],
    """
- **Chain mode:** in the Patterns view, **Shift + Octave ▲** switches it on (Octave ▲ green) and **Shift + Octave ▼** off. While Shift is held, the Octave button that does something is yellow. The mode stays on when you leave the view.
- **Editing a rule** (with the mode on): press a pattern = **A** (yellow; it is selected as usual). **A again** = one more play (up to 8; the knob LEDs count them). **Another pattern of the track** = **B** (green) and the next one = **C** (red). Examples: n = 3 → A A A B A A A C; no C → A A A B; n = 1 → A B A C.
- B and C play once and the track returns to A (unless they carry a rule of their own).
- **Clear + pattern** in the mode: removes the rule; with no rule it clears the pattern as usual. Out of the mode, Clear clears the pattern, its rule and its play order.
- **With the mode off** the rules stay stored but are not followed: patterns play as on the original device.
- **Scenes** (Mixer view): a scene saved with the chain mode on remembers it and shows in **peach**; loading it brings the mode back, and loading a normal scene switches it off. That is how chained and normal scenes mix. Tracks that are following a rule **blink** in the Mixer.
- A scene ends when its longest chain ends (on the return from C, or from B when there is no C).
- **Scene repeats:** in the Mixer, **Shift + pads 9-16** set 1-8 repeats of the current scene (with Shift the row is yellow and the chosen one green). During the repeats the mutes are the ones you left and the chains go on where they were.
- The rules are saved with the pattern (they travel when it is duplicated); the mode and the scene data, with the project.
""", [])

sec("nudge-ordenes", "Nudge and play orders",
    ["**Since RC2.** In the Pattern Settings view: **pad 26 = Nudge** (the pattern rotated so that the chosen first step becomes step 1), **pad 27 = fractal order**, **pad 28 = deconstructed order**. On every track, drums included."],
    """
- **Nudge (pad 26, orange):** rewrites the pattern so that the chosen first step becomes step 1; what was in front of it goes to the end. It rotates whole steps with their automation, over 16 steps (a pattern of up to 16) or over 32. The last step moves with it (steps 6-13 → 1-8).
- **Fractal (pad 27):** 1 · 1 2 · 1 2 3 · 1 2 3 4 … up to the last step, then again.
- **Deconstructed (pad 28):** the diagonals of the grid: 1 6 11 16 · 2 7 12 13 · 3 8 9 14 · 4 5 10 15 (and the same with 17-32). Steps outside the pattern are skipped: with 8 steps, 1 6 2 7 3 8 4 5.
- Pads 27 / 28 and the four direction pads (29-32) exclude each other and share colours.
- The pattern “ends” (for chains, scenes and the frequency) when the whole run ends.
- The order is saved with the pattern. Clearing the pattern removes it.
""", [])

sec("arpegiador", "Arpeggiator (since RC2)",
    ["**Since RC2.** In the Pattern Settings view of a note track: **Shift + pad 25** = the pattern's arpeggiator on / off, **Shift + pads 27-32** = its order (fractal, deconstructed, up, down, ping-pong, random), independent of the pattern's direction."],
    """
- With Shift, pad 25 and pads 27-32 show yellow and the chosen ones green; without Shift, pad 25 shows green while the arpeggiator is on.
- **Sequence:** when two or more notes start on a step, they play one a step (at the pattern's sync rate) in the chosen order, over the notes sorted by pitch, for as long as the chord's longest note. Each note lasts a step and keeps its velocity. The step's random-mutate and dynamics do not apply to them.
- **Input:** the first note sounds as always; holding another one with it starts the arpeggio of the held notes, one a step (stopped: at the project's tempo and the track's sync rate), until all are let go. **With Record the chord is recorded**: the sequence plays the arpeggio afterwards.
- Saved with the project, per track and pattern.
- **Shift + pads 17-24** = the arpeggio's own resolution (1/4 … 1/32T, in the sync rate's order; the same pad again = the track's). Each note of the chord lasts its own gate.
- **Drums** (since RC2): the same gestures in a drum's Pattern Settings; in its Preset view, holding several samples = the arpeggio of the samples (the drum jumps from one to another), on the drum's grid while playing and at the tempo when stopped; with Record it is recorded (micro step and sample flip).
- **Gate by holding** (Micro Step view = Gate twice, pad 32, per track): when entering notes by hand, how long you hold the pad is the gate. **Pad 31** = fixed length (with both off it opens the selector; picking a length turns it on). A toggle that is on turns off when pressed again; pressing the other one switches.
""", [])

sec("rollers", "Drums micro-step rollers (since RC2)",
    ["**Since RC2.** Rows 1-3 of the drums' Note view: holding a roller plays its drum on every step at that micro step (two columns per drum, micro steps 1-3 and 4-6), live; with the transport stopped, at the project's tempo."],
    """
- Each column is the drum of its box below (with the mirrored copy: columns 1-4 = drums 4-1, 5-8 = drums 1-4); dim in the drum's colour, lit while held.
- Several at once combine; with the step's velocity (100 on an empty step); with Record they are recorded into the pattern.
""", [])

sec("escala-propia", "Custom scale (since RC2)",
    ["**Since RC2.** **Shift + Scales** = an editor of a custom scale for the note tracks: up to 7 notes over the root and any **period** (up to 24 semitones) that is the root of the next iteration; every row of pads is one iteration (two with 4 notes or fewer). Saved with the project."],
    """
- The editor's keyboard: two octaves of a piano from the root (rows 4 / 3 the first octave, white / black; rows 2 / 1 the second). The highest key pressed is the period (orange), the others the notes (green).
- It drives playing, the lit notes of the sequence, quantising and random-mutate. A stock scale switches it off; the editor switches it on again.
""", [])

sec("modo-muestra", "Sample mode of the MIDI tracks (since RC2)",
    ["**Since RC2.** A new state of pad 27 (cyan, after the granular): the MIDI track plays **a pack sample one-shot**, at the note's pitch (**C3 = note 60 = as recorded**), through the engine's filter, effect and LFO; the VCA stays open and the sample plays to its end.",
     "The **expanded Note view** (Note twice) is the picker: rows 3-4 = 16 samples × 4 pages (Octave ▼ / ▲: all 64 of the pack), rows 1-2 = the steps; **a held step + a sample** = that step's sample flip, also live with Record."],
    """
- **Picking the sample:** in the expanded Note view, rows 3-4 = 16 samples of the pack; **Octave ▼** = next page, **▲** = previous (4 pages, the 64 samples; the button lights when there are more pages that way). Touching a sample = the track's sample (cyan), and it sounds (note 60). It is the same value as the granular's source (Shift + K8 on its page): changing one changes the other; the capture is picked there.
- **Sample flip:** rows 1-2 = the 16 steps of the half shown (**1-16 / 17-32** = the other half). **Hold a step and touch a sample** = that step plays that sample (peach; the held step green, its sample yellow); **Clear + step** = no flip (dim cyan, the background of rows 1-2). The step playing, white. A flip on a step with no note does nothing.
- **Live:** with **Record + Play**, touching a sample records a note 60 on the step playing, and its flip.
- **The pitch** comes from the track's notes (the normal Note view, the step-drummer, incoming MIDI): C3 = as recorded, an octave up = twice as fast. One voice per track, like a drum: every note restarts the sample; the note-off does not cut it, it plays to its end.
- **The VCA open:** in this mode the envelope does not close the VCA (gain, velocity and LFO → level still work); the other engines as before.
- **Saved:** the track's sample with the engine values (device settings); the flips in the pattern: they travel with the pattern and the project. They live in the track's **level** automation lane (Mixer): a flip replaces the level automation of its step (the other steps' still plays) and recording the level over it erases the flips of those steps.
- Without the sample mode, the expanded Note view is the usual one.
""", ["Expanded Note view of MIDI 1 in the sample mode: steps on top, samples below."])

sec("master-fx-beta", "Master FX since RC2: mechanical gesture, Glitch, Digitise and saving per session",
    ["**Since RC2.** Pad 6 of Master FX is the **Glitch** and pad 31 a **mechanical gesture** (tape stop, scratch…); Digitise gains **K3 = momentary send to the delay** and **K4 = envelope**; the Master FX knobs and slots **are saved with every project**."],
    """
- **Pad 6 = Glitch** (it replaces the Vinyl): held, latched, assignable to the slots and to the FX sequencer like the other effects; its K1-K4 are the Glitch’s.
- **Pad 31 = mechanical gesture:** on press the audio slows down to a stop; on release it starts again. **K1** = moves per gesture (1-8), **K2** = type, blended continuously and shown in colours (tape stop → baby scratch → tear → back spin → rattle), **K3** = stop time, **K4** = start time.
- **Digitise:** K1 sample rate, K2 bits, **K3 = send to the delay while pad 4 is held** (every track; on release their sends return), **K4 = envelope of the amount** (right: from full to clean; left: it grows).
- **Per session:** the 20 knobs of the top row, the assignment of the bottom-row slots and the attack / release of the master compressor are saved when the project is saved and return when it is loaded. A project without them (an old or a new one) leaves the device as it is. Latched effects are not saved.
""", [])

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
- **Paraphony:** one note = unison; two = one per oscillator (**since RC2**: with one oscillator the last note has priority; releasing it goes back to the previous one).
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
     "K1 pitch, K2 position, K3 scan / freeze, K4 size, K5 density, K6 zone, K7 LFO → position, K8 envelope → position; Shift: fine, sprays, reverse, window, slicer (or stretch, since RC2), LFO → size, source."],
    """
**Magenta** state of pad 27; **pad 2** of the page row = granular page.

| Knob | Alone | With Shift |
|---|---|---|
| K1 | Pitch, ±24 semitones | Fine, ±1 semitone |
| K2 | Position in the sample | Position spray |
| K3 | Scan: centre = frozen, right moves forward, left backwards | Probability of a reversed grain |
| K4 | Grain size, 5-500 ms | Pitch spray (±12 st) |
| K5 | Density, 1-16 overlapping grains | Window: rectangular → triangular → percussive |
| K6 | Length of the scan zone | Note mode: pitch / slicer / stretch (stretch since RC2) |
| K7 | LFO → position | LFO → size |
| K8 | Envelope → position | **Source**: pack sample 1-64, to the left the capture. **since RC2:** a long travel over five zones: the capture (red) and the sample Drum 1 (orange), 2 (yellow), 3 (violet) and 4 (teal) has now; it stays fixed even if the drum changes its sample; dim white = no drum has that sample any more |

- **Pitch mode:** the note changes the pitch of the grains; with two notes they are shared between both.
- **Slicer mode:** the note picks one of 16 slices of the sample.
- **Stretch mode (since RC2):** the stretch from K2 to the end of the sample lasts **K3** steps (1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48 or 64; K3’s LED shows it) at any tempo, without changing the pitch, and starts again in step with the start of the transport; the notes change the pitch as in pitch mode. With the transport stopped it stands still. K7 / K8 do little in this mode.
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
- **Sidechain between drums:** Shift + FX and Octave ▼: ducking pages per drum (rows 3-4) and which drum triggers it (row 1, pads 5-8). **since RC2:** row 1 pads 1-4 = Synth 1, Synth 2, MIDI 1, MIDI 2 as the trigger (every note of their pattern).
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

sec("pack-interno", "The internal memory pack: read only",
    ["Nothing of the mod writes or deletes in the pack of the Circuit’s internal memory (the first one of the Packs view). You can read it and copy from it to a pack of the card, not the other way round."],
    """
- **Refused** (the Save LED lights red for 1.5 s): saving the captured sample with the project, exchanging or copying samples and patches into the internal pack, saving synth or own-synth patches in it, copying projects into it and deleting it from the Packs view.
- **Works:** playing and loading what the internal pack holds, and copying from it to a pack of the card (Duplicate + A in the internal pack, load the other pack, Duplicate + B).
- **Unchanged:** the device’s own saves (Save of a project). What the mod keeps inside the project (chains, Master FX per session…) goes inside that normal save, in the internal memory too. Still, with the builds that do not end in “S” it is better not to use the internal memory for projects: the installer asks for that.
- The “S” builds write nothing of their own to any memory.
""", [])

sec("instalar", "Installing and going back",
    ["`tools/ct_uploader.html` sends the `.syx` over Web MIDI; it only accepts verified firmwares. Recovery: Scales + Preset + Note at power-on."],
    """
0. **Without building:** `tools/rc_uploader.html` patches the official firmware ([Novation download](https://components.novationmusic.com/api/v2/firmwares/168/file)) in the browser and sends it. Pick RC2, RC2S (or the earlier RC0.9 / RC0.9S) or “Official”.
1. Open `tools/ct_uploader.html` in Chrome and connect the Circuit Tracks over USB.
2. Pick the `.syx` from `firmware/<version>/`: the uploader checks its SHA-256.
3. Send. Novation’s bootloader is not modified.
- **Going back:** send another version or the official firmware. If the device does not start: hold **Scales + Preset + Note** at power-on (bootloader recovery mode).
- The RC branch does not publish `.syx` files: they are generated with `tools/patch_official.py` from the official firmware.
- **RC2** (release candidate 2, marker `RC2`) = SC44 = RC0.9 + everything this manual marks **since RC2**: what betas 1.0-1.30 had (mechanical gesture and Glitch on pad 6, Digitise K3 / K4, Master FX per session, side-chain and compressor knobs, step frequency, dynamics and random-mutate, pattern chains and scenes, Nudge and play orders, own-synth patches, arpeggiators, rollers, custom scale, count-in, cue mode, side-chain from the note tracks, quantize, LFO shapes, sample mode…) and their fixes. Much of it is untested on the device: use it with a backup of the SD card.
- **RC0.9** (tenth release candidate) = RC0.8 + the internal memory pack, read only for the mod; RC0.8 = RC0.7 + one fix (the pitch knobs of the step-drummer keep their value: since RC0 every turn wrote only its own delta); RC0.7 = RC0.6 + two fixes (the step-drummer, the FX sequencer and the stretch follow the pattern of their own track, not another one’s; the selector knob of the FX sequencer is slower); RC0.6 = RC0.5 + two fixes (the LFO of the Auto-Filter and of the Phaser starts when the effect comes on; the dim white of Clear no longer pulses); RC0.5 = RC0.4 + the captured sample in front of the Master FX effects; RC0.4 = RC0.3 + the fixes of SC38.2-SC38.6; RC0.3 = SC38, RC0.2 = SC37.5, RC0.1 = SC37.4, RC0 = SC36.2.
- **Safer build:** RC2S = RC2, but everything the mod would ask to write or delete on the card or in the internal memory is refused (the Save LED turns red): saving the capture with the project (A8), exchanges and copies of samples and patches between packs, the own-synth patches, saving the synth patch, copying projects and deleting packs do nothing; the original's saves (projects, patches, settings) work. The earlier ones: RC0.9S = RC0.9 without those features. **Back up the SD card before installing** any version.
- New features and fixes of every version: `CHANGELOG.md`.
""")

sec("herramientas", "Development and diagnostic tools",
    ["Reproducible builders, ARM / DSP emulators with tests through the real routes, `verify_builds.py`, remote diagnostics over USB (`ctremote.py`)."],
    """
- `tools/build_scNN.py`: every version is built from the official firmware; `verify_builds.py` checks they all give the same SHA-256.
- `tools/emu_*.py`: emulation tests (Unicorn for the ARM, dsp56300 for the DSP).
- `tools/ctremote.py` + `rdiag`: the PC reads memory, card items and the device’s capture over SysEx. Only in the diagnostic builds and in SC35 / SC36: **SC36.1, SC36.2, the RCs (RC0 … RC2 and their safer builds) and the betas do not include it**, to leave the USB protocol alone.
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
LSB 1 pitch env., 2 ring (frequency), 3 LFO, 4 LFO speed, 5 env → cutoff, 6 resonance, 7 envelope shape, 8 ring (amount), 9 filter mode, 10 start (0-120; before 0-15), 11 bitcrush, 12 distortion type, 13 cut (0-120), 14 attack.

### Master FX — channel 16, NRPN MSB 9
LSB = 4 × set + knob: Gater 0-3, Auto-Filter 4-7, Digitise 8-11, Phaser 12-15, Vinyl 16-19.
""")
