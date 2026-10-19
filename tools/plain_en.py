"""The plain-language guide, English (tools/make_plain.py renders it).  Structure and plain style after the community guide «Circuit Tracks mod
manual, in plain English» by u/luxurysoft1337 (Reddit, 15 October 2026, written for RC0.9 / Beta 1.3); rewritten, corrected and completed up to
RC2 with the names of the mod's own manual, and illustrated with its panel drawings."""
import make_manual as M

F = M.fig
BETA = "RC2"
B = f"*(since {BETA})*"

UI = dict(lang="en", title="Circuit Tracks mod guide, in plain words", cover="A guide in plain words, illustrated", toc="Contents",
          other='<p class="lang"><a href="sencilla.html">Español</a> · <a href="plain.pdf">PDF</a> · <a href="guide.html">Guide by views</a> · <a href="en.html">Feature list</a></p>',
          footer="CIRCUIT-HACKS — firmware mod for the Novation Circuit Tracks (1.2.1, build 4486). Not affiliated with Novation.",
          html="plain.html", md="docs/PLAIN.en.md", pdf="plain.pdf")

INTRO = f"""First draft by [reddit.com/u/luxurysoft1337](https://www.reddit.com/user/luxurysoft1337/), whom we thank. This guide explains the CIRCUIT-HACKS mod in plain words, view by view, with drawings of the panel. It follows the structure and the plain style of the community guide «Circuit Tracks mod manual, in plain English» by **[reddit.com/u/luxurysoft1337](https://www.reddit.com/user/luxurysoft1337/)**, written for RC0.9 and Beta 1.3. This edition is rewritten for **RC2.01** and **RC2.01S**, keeps the names of the mod's own manual (capture, step-drummer, slots…), corrects what that guide got wrong or left open, and adds every feature that came after Beta 1.3. The detailed references are the [guide by views](guide.html) and the [feature list](en.html).

Nothing here has been tested on a real unit unless the [CHANGELOG](https://github.com/Ghillermo/CIRCUITS-HACKS-RC/blob/main/CHANGELOG.md) says so. The mod is not affiliated with Novation."""

S = []


def sec(sid, title, body, figs=()):
    S.append(dict(id=sid, title=title, body=body.strip("\n"), figs=list(figs)))


# ---------------------------------------------------------------------------------------------------- 1
sec("what", "What the mod is", f"""
The mod is Novation's own Circuit Tracks firmware (1.2.1, build 4486) with extra features patched in. Whatever this guide does not mention works exactly as on a stock unit, so **Novation's user guide still applies**.

- Features with no mark are in every build.
- Features marked **{B}** are new compared with RC0.9; *(since RC2.02)*, compared with RC2.01; *Beta 3.3 only*, only in the beta with the new features (not in RC2.02). Many of them have not been tried on a real unit yet: keep a copy of your card.
- Novation's bootloader (the part that installs firmware) is never modified, so you can always go back.
""")

# ---------------------------------------------------------------------------------------------------- 2
sec("install", "Before you install", f"""
1. **Back up the SD card** (copy it to a computer). Do this before installing any version.
2. Back up your projects with Novation Components as well.
3. Pick a build:

| Build | What it is |
|---|---|
| **RC2.02** | The release candidate: everything in this guide (RC2.01 + the mod matrix, the split keyboard with any pair and the new LFO shapes). |
| **RC2.02S** | The *safer* build: RC2.02, but nothing of the mod writes files to the card on its own: saving captures into the pack, copying samples, patches or projects between packs, the own-synth patches and deleting packs do nothing (the Save LED turns red). |
| **RC2.01 / RC2.01S, RC2 / RC2S, RC0.9 / RC0.9S** | The earlier ones: RC2.01 without what is marked *(since RC2.02)*; RC2 with the sample after the master filter; RC0.9 without what is marked {B}. |
| **Beta 3.3** | The test build: RC2.02 + the new features marked *Beta 3.3 only*, not tried on a unit. It writes to the card like RC2.02. |

### Installing
1. Download Novation's official firmware 1.2.1 (the update file from Components).
2. Open `tools/rc_uploader.html` (in the project's repository) in **Chrome**, with the Circuit Tracks connected over USB.
3. Give it the official file, pick the version and send it. The page patches the official firmware in your browser and checks the result; it contains none of Novation's code. Older versions are listed too, and «Official» sends the untouched firmware.
- `tools/ct_uploader.html` sends a ready-made `.syx` and checks it against known checksums. The public repository has no `.syx` files of the RCs: they are always made from the official firmware.

### The internal memory
The pack in the Circuit's internal memory (the first pack) is **read-only for the mod**: nothing of the mod writes or deletes there (saving captures or patches, copying samples or projects, deleting the pack). It is refused and the **Save** light turns red for about 1.5 s. The device's own saves still work. With any build that does not end in «S», keep your projects on the card, not in internal memory (the installer asks you to confirm this).

### Going back
Send «Official» (or any other version) from the same page. If the unit does not start, hold **Scales + Preset + Note** while switching it on: that is Novation's bootloader mode, where you can send any firmware again.
""")

# ---------------------------------------------------------------------------------------------------- 3
sec("read", "How to read the instructions", f"""
- **Pads** are numbered 1-32 from left to right and top to bottom: row 1 = pads 1-8, row 4 = pads 25-32.
- **Knobs:** K1-K4 on top, K5-K8 below (on the panel they are staggered: K2 K4 K6 K8 above, K1 K3 K5 K7 below).
- «**Shift + X**» = hold Shift while you use X. The same with **Clear** and **Duplicate**.
- **Shift lights the way:** while Shift is held, the shortcuts the view offers light **yellow**, and the option already chosen shows in another colour.
- **Two-step confirm:** several actions ask first. «Clear + pad» makes the pad blink (the unit asks «are you sure?»); «Clear + the same pad» again within about 5 s confirms. Another pad moves the question there; waiting cancels it.
- **Knob LEDs** show the value of the new functions with their **brightness** (brighter = more). Knobs that go both ways are dark in the middle.
- A drum, a synth or a MIDI track is chosen with its **track button**; «its view» is the view that button opens.
""", [F("The panel: the numbers are the gestures of the quick finder (section 5).",
        buttons={"Mixer": "white", "Shift": "yellow", "Clear": "red", "Duplicate": "white", "Pattern Settings": "white", "Scales": "yellow", "Preset": "white", "Gate": "white"},
        badges={"Mixer": 1, "Clear": 2, "Shift": 3, "Duplicate": 4, "Pattern Settings": 5, "Scales": 6, "Preset": 7, "Gate": 8},
        view="Overview")])

# ---------------------------------------------------------------------------------------------------- 4
sec("words", "Words this guide uses", f"""
These are the names of the mod's own manual.

| Word | Meaning |
|---|---|
| **Held / latched** | A held effect sounds while your finger is down; a latched one (Shift + pad) stays on until you touch it again. |
| **Capture** (captured sample) | A short recording of the Circuit's own output (up to about 3.5 s), made with pad 32 in Master FX. You can play it, put it in a slot, replace a drum with it or use it as a granular source. It lives in memory: it is lost at power-off unless it replaced a drum and you saved the project. |
| **Step-drummer** | A layer over a track's pattern: the pattern still decides when notes play, and the eight knobs give each **pair of steps** a value (a pitch shift, a velocity, a macro position…). |
| **Send** | How much of a track goes into the shared delay or reverb. |
| **Master FX** | Live effects on the whole output, opened with Mixer twice. |
| **Slots** (bottom row) | Pads 26-30 of Master FX and of the FX view: each stores an effect with its knob settings. |
| **Song pointer** | Pads 9-24 of Master FX = steps 1-16, to repeat or loop parts of the pattern live. |
| **Engine** | The sound a MIDI track can have on the Circuit itself, chosen with pad 27 of its Preset view. |
| **FX sequencer** | An engine that makes no sound: each pair of steps triggers a Master FX slot. |
| **Own-synth patch** | A saved setting of a MIDI track's engine, kept in the pack. |
| **Chain mode** | The project-wide mode in which patterns follow their chain rules (play n times, then jump). |
| **Pack** | Novation's set of samples, synth patches and projects. |
| **Strips 3 and 4** | The mixer strips where the MIDI tracks' own sounds (and the routed returns) come out. |
""")

# ---------------------------------------------------------------------------------------------------- 5
sec("finder", "Quick finder: I want to…", f"""
| I want to… | Do this |
|---|---|
| Open Master FX | **Mixer**, then **Mixer** again (badge 1). |
| Reset a knob to its default | Hold **Clear** and turn the knob **right** (badge 2). |
| Delete a knob's automation | Hold **Clear** and turn the knob **left** (drums; MIDI engine {B}). |
| Play a drum like a keyboard | Choose the drum, **Shift + Preset** (or **Preset again** {B}) (badge 7). |
| Record the Circuit's own output | Master FX, **pad 32**. Play it with **pad 7**. |
| Replace a drum with that capture | Drum Preset view, **Clear + pad**, then **Clear + the same pad**. |
| Swap two drum samples | Drum Preset view, hold **Duplicate**, tap pad A then pad B (badge 4). |
| Kill every latched effect | Master FX, **pad 8**. |
| Set a track's level to 100 or 0 | Mixer, **Shift + turn** the knob right or left. |
| Loop part of the pattern live | Master FX, hold two song-pointer pads. |
| Give a MIDI track its own sound | MIDI 1 / 2, **Preset**, **pad 27**. |
| Rotate a pattern (Nudge) | Pattern Settings: choose the first step, then **pad 26** {B} (badge 5). |
| Arpeggiate a track | Pattern Settings, **Shift + pad 25** {B}. |
| Quantize a recorded pattern | **Shift + Play** {B} (the selected track). |
| Use my own scale | **Shift + Scales** {B} (badge 6). |
| Metronome / count-in | **Shift + Clear** {B} (badges 3 + 2). |
| Gate = how long I hold | **Gate** twice (Micro Step), **pad 32** {B} (badge 8). |
| Go back to stock | Send «Official» from the uploader. |
""")

# ---------------------------------------------------------------------------------------------------- 6
sec("sends", "Effects: sends and the FX view", f"""
The Circuit has **one delay and one reverb** shared by all tracks; each track's **send** decides how much of it goes in (0 = dry). **Master FX** (next section) is a separate set of live effects on everything at once: use sends to set how wet each track sounds, and Master FX to play with the whole mix.

Press **FX** to open the FX view:

| Gesture | What it does |
|---|---|
| **Octave ▲ / ▼** | The 8 knobs = the delay sends / the reverb sends, one per track. |
| **Shift + knob** | The effect itself, for every track: reverb K1 type, K2 decay, K3 damping; delay K1 time, K2 sync, K3 feedback, K4 width, K5 ratio, K6 slew. Saved with the project. |
| **Duplicate** | Reset: sends to 0, master filter centred, Master FX off. |
| **Shift + Octave ▲ / ▼** | *Beta 3.3 only:* master filter resonance, 16 up / 16 down; it stops at the top and the bottom. In RC2.02 it is on **1-16 / 17-32** (green LED). |
| **Shift + pad 25** | *Beta 3.3 only:* switches the master filter off: it sounds as with the filter at the centre even if you move its knob; again, it switches it on wherever the knob is at that moment. While off, the filter knob's light is red. |
| Bottom row | The same as in Master FX: slots, mechanical gesture, recording the capture. |

- If Setup routes the reverb / delay return through strip 3 or 4 (section 14), the sends of those strips stop at half range and move at half speed.
""", [F("FX view: Octave ▲ / ▼ choose delay / reverb sends; Shift + knob, the effect itself.",
        pads={**{n: ("peach", f"T{n - 25}", True) for n in range(26, 31)}, 31: ("teal", "Glitch"), 32: ("red", "Capture")},
        knobs={k: f"send {k}" for k in range(1, 9)}, buttons={"Oct ▲": "peach", "Oct ▼": "cream", "Duplicate": "white", "1-16 / 17-32": "green", "FX": "white"}, view="FX")])

# ---------------------------------------------------------------------------------------------------- 7
sec("masterfx", "Master FX", f"""
Live effects on the whole output. **Hold** a pad to hear its effect; **Shift + pad** latches it (touch it again to release). Open it with **Mixer, Mixer**; any other view button leaves.

| Pad | What it is | K1-K4 while you hold it |
|---|---|---|
| 1 | Gater | division, depth, width, smoothing |
| 2 / 3 | Auto-Filter, low pass / high pass | speed, depth, resonance, centre |
| 4 | Digitise | sample rate, bits; {B}: K3 = a momentary throw into the delay, K4 = envelope of the amount |
| 5 | Phaser | speed, depth, feedback, mix |
| 6 | **Glitch** {B} (in RC0.9, the Vinyl) | Glitch: speed, repeat, delay, chaos / overload |
| 7 | Play the **capture** | pitch, mode, start, end |
| 8 | Release everything latched (effects, slots, song pointer, capture) and bypass | — |
| 9-24 | **Song pointer**: steps 1-16 | — |
| 26-30 | **Slots** | the stored effect's |
| 31 | **Mechanical gesture** {B} (in RC0.9, the Glitch) | gesture: moves, kind, stop time, start time |
| 32 | **Record** the capture | — |

- **Clear + knob right** = that knob back to its default. RC: while Clear is held the knobs show lavender at their default and red elsewhere; {B}: only lavender (Master FX has no automation to delete).
- {B} Each project keeps its own Master FX: the 20 knobs of the effects, the slot assignments and the compressor. Latched effects are not saved.

### Song pointer (pads 9-24)
- **Hold one step:** it repeats while you hold it.
- **Hold two steps:** the pattern loops between them while you hold.
- **Shift + two steps:** that loop stays (latched); pad 9 turns white and touching it removes the loop.
- **Phrase mode:** Shift + a step = a phrase from that step to step 16; touching another step moves the end; Shift + another step moves the start; Shift + the start step (or the white pad 9) leaves.
- The playing step shows white; the pointer starts off when a project loads.

### The capture (pads 32 and 7)
- **Pad 32 (red):** hold = record while held (up to about 3.5 s); a short tap = record until the next tap; **Shift + pad 32** = armed: with the sequencer running it records the next bar, stopped it waits for Play and records the first bar. Since RC2.01 the capture and the playing sample sit before the master filter: the filter acts on the sample and the capture does not hold it.
- It records the output **without** the Master FX effects; when it plays, it goes through them.
- **Pad 7 (yellow)** plays it: K1 pitch (±24 semitones), K2 mode by colour (yellow one-shot, green gate, blue loop: the loop sounds while you hold the pad), K3 start, K4 end (end before start = backwards). **Shift + pad 7** keeps it playing in any mode until pad 7 again (or pad 8).
- Hold pad 7 and touch a slot to store it there; replace a drum with it (section 8); use it as a granular source (section 10).

### Glitch
The output becomes a tape head over the last seconds of audio. K1 speed (top = normal, lower = tape brake, centre = stopped, below = backwards), K2 repeat size (maximum = no repeat), K3 delay (up to about 2.6 s), K4 lower half = chaos (jumps, cuts, reversals), upper half = overload (late blocks and clicks, slowing down from about three quarters up). Hold the Glitch pad and touch a slot to store a Glitch with these settings (turquoise).

### Mechanical gesture {B}
Pressing pad 31 slows the audio to a stop; releasing it starts it again. K1 = moves per gesture (1-8), K2 = the kind, blended continuously and shown in colours (tape stop → baby scratch → tear → back spin → rattle), K3 = stop time, K4 = start time. It uses the Glitch's engine: while a gesture plays, the Glitch waits.

### Slots (pads 26-30)
Hold an effect (pads 1-6), pad 7 (the capture) or the Glitch / gesture pad and touch a slot: the slot keeps that effect with a copy of its knobs. Touch the slot = on while held; **Shift + slot** = latched. Slots are saved with the project. An empty slot is the stock performance effect of the FX view. The FX sequencer (section 10) triggers these slots.
""", [F("Master FX (Mixer twice). RC0.9: pad 6 Vinyl, pad 31 Glitch; RC2: pad 6 Glitch, pad 31 mechanical gesture.",
        pads={1: ("orange", "Gater"), 2: ("yellow", "Filter\nLP"), 3: ("yellow", "Filter\nHP"), 4: ("lime", "Digitise"), 5: ("magenta", "Phaser"), 6: ("teal", "Glitch"),
              7: ("yellow", "Capture\nplay"), 8: ("white", "All\noff"), **{n: ("purple", str(n - 8), True) for n in range(9, 25)},
              **{n: ("peach", f"Slot\n{n - 25}", True) for n in range(26, 31)}, 31: ("pink", "Gesture"), 32: ("red", "Rec")},
        knobs={1: "K1", 2: "K2", 3: "K3", 4: "K4"}, buttons={"Mixer": "white"}, view="Master FX")])

# ---------------------------------------------------------------------------------------------------- 8
sec("drums", "Drums", f"""
### The drum knobs
Each knob does what its panel label says, with a second layer under Shift. Everything is saved with the project and goes out over MIDI (NRPN, section 18). With every knob neutral a sample sounds as on a stock unit.

| Knob | Alone | With Shift |
|---|---|---|
| K1 Oscillator | Pitch ({B}: the stock one, continuous; the chromatic pads transpose on top) | Pitch envelope amount |
| K2 Osc mod | Ring mod frequency | Ring mod amount |
| K3 Amp envelope | RC: decay; left of zero, the sample's start point. {B}: **left = decay** (the stock one), **right of the maximum = attack** (fade-in up to 1 s) | {B}: **left = sample start**, **right = cut** from the end |
| K4 Filter envelope | Envelope → cutoff | Envelope shape |
| K5 Filter frequency | Filter / EQ | Filter mode: EQ tilt (stock), band pass, notch, comb, DJ |
| K6 Resonance | Resonance | — |
| K7 Modulation | LFO amount | LFO speed |
| K8 FX | Distortion; left of zero, bitcrush | Distortion type: stock, soft, hard, folded |

- **Reset:** Clear + knob right = default (both layers; LED lavender, as on the original); Clear + knob left = delete that knob's automation (red), as on the original. {B}: Clear + K3 right also puts attack, start and cut to 0; Clear + K8 right also removes the bitcrush; **Clear + the drum's button** (with its view on screen) puts all its knobs back to their defaults.
- **RC0.9:** a new or untouched project starts with the filter mode in DJ, which removes the stock EQ: drums can sound different from a stock Circuit. Shift + K5 to «EQ tilt» brings the stock sound back. {B}: fixed (the default is the stock EQ).

### Play a drum like a keyboard
Choose the drum and press **Shift + Preset** ({B}: or **Preset again** in its Preset view). Three rows of pads play its sample at different pitches, in the scale and root of the Scales view. K1 = offset in semitones, Shift + K1 = fine tuning in cents. When recording, each pitch goes only into its own step ({B}: the pads transpose on top of K1's pitch and, while recording, stay on their step; Clear + K1 to the left, held, deletes them with K1's automation).

### Drum Preset view
| Gesture | What it does |
|---|---|
| **Clear + pad**, **Clear + the same pad** | That drum now plays the **capture**. Temporary until you save the project: saving writes it into the pack (`PCM/NN_PCM.wav`) if it fits in the sample memory. Not in the safer build (there it lasts until the pack reloads) nor in the internal memory's pack. |
| **Duplicate + pad A + pad B** (same pack) | Swaps the two samples (files and table); you hear it at once. |
| **Duplicate + pad A**, load another pack, **Duplicate + pad B** | Copies sample A over B in the other pack (A's pack is untouched; B may be empty). It goes into B's place if it fits, else into the free import memory; it never overwrites a sample that plays. |
| **Several pads held** {B} | With the drum's arpeggiator on, the arpeggio of the samples held (section 11). |

- Swapping and copying write to the card: not in the safer build. Synth patches swap and copy the same way in the Synth 1 / 2 Preset view (a pack's 128 patches are shared by both synths).

### Micro-step rollers {B}
In the drums' Note view (press **Note** until rows 1-3 show dim pads), rows 1-3 are **rollers**: each column belongs to the drum of the box below it (columns 1-4 = drums 4-1, columns 5-8 = drums 1-4); a drum's left column is its micro steps 1-3 and its right column micro steps 4-6 (drum 1 = pads 4, 12, 20 and 5, 13, 21). While you hold one or more, that drum plays on **every step** at those micro steps. Playing it follows the pattern; stopped it plays at the project's tempo. **With Record** the hits are recorded into the pattern.

### Sidechain view
**Shift + FX** opens it. {B}: **K1-K4** = attack, hold, decay and depth of the sidechain of the track whose preset you touched last (Synth 1 if none), in the track's colour; **K7 / K8** = attack / release of the master compressor (switched on in Advanced Setup), saved with the project.

**Sidechain between drums:** **Shift + FX**, then **Octave ▼**: rows 3-4 hold the ducking pages for each drum, and pads 5-8 of row 1 pick which drum triggers the ducking ({B}: pads 1-4, **Synth 1, Synth 2, MIDI 1 or MIDI 2**: every note of their pattern). {B}: on a drum page **K1-K4** set attack, hold, decay and depth for the drum whose preset you touched last (in the drum's colour; touching a preset brings back the preset's values). Saved with the project.

**Sidechain from patterns** {B}: on the Synth and MIDI pages of the Sidechain view, **row 1 pads 1-4** (next to the drums on pads 5-8) pick **Synth 1, Synth 2, MIDI 1 or MIDI 2** as the source of the chosen track (the last preset touched): every pattern note of that track ducks it, as a drum hit does. Saved with the project.
""", [F("Drum track view: the knobs follow the panel labels; Shift gives the second layer.",
        knobs={1: "Pitch", 2: "Ring", 3: "Decay /\nattack", 4: "Env→F", 5: "Filter", 6: "Reso", 7: "LFO", 8: "Drive"}, buttons={"Drum 1": "white", "Shift": "grey"}, view="Drum 1"),
      F("The drums' Note view: rollers on rows 1-3 (RC2); the drum boxes below.",
        pads={**{n: ("blue", "", True) for n in (1, 9, 17)}, **{n: ("purple", "", True) for n in (2, 10, 18)}, **{n: ("yellow", "", True) for n in (3, 11, 19)},
              **{n: ("red", "D1", True) for n in (4, 12, 20, 5, 13, 21)}, **{n: ("yellow", "", True) for n in (6, 14, 22)}, **{n: ("purple", "", True) for n in (7, 15, 23)},
              **{n: ("blue", "", True) for n in (8, 16, 24)}, 25: ("blue", "D4"), 26: ("purple", "D3"), 27: ("yellow", "D2"), 28: ("red", "D1"),
              29: ("red", "D1"), 30: ("yellow", "D2"), 31: ("purple", "D3"), 32: ("blue", "D4")},
        buttons={"Note": "white", "Drum 1": "white"}, view="Drum Note")])

# ---------------------------------------------------------------------------------------------------- 9
sec("synths", "Synth tracks (Synth 1 and 2)", f"""
### Source view
With a synth's view on screen, press **its button again**. Pads 25-29 pick the source of the synth's noise: noise (normal), input 1, input 2, input 1 inverted, input 2 inverted. The patch needs some noise level (CC 56) for the source to be heard. Saved with the project. If Setup routes the reverb / delay returns through strips 3 / 4, that is what reaches the synth. **Pad 30** opens the synth's step-drummer; {B} **pad 32** opens the editor of the macro knob destinations. Any button closes the view.

### Step-drummer
A layer over the pattern: the pattern decides which steps play; the knobs give each pair of steps a value.
- **Pairs:** K1 = steps 1-2, K2 = steps 3-4… **1-16 / 17-32** = the other half of the pattern.
- **Two pages:** Octave ▲ = the pitch page, Octave ▼ = the velocity page.
- **Pads 1-16** = the steps (bright = a note, white = playing); touch = listen, **Shift + touch** = add or remove a note. With Record, the steps you play are recorded in real time.
- **Opening it:** synth = pad 30 of the source view; MIDI track = pad 30 of its Preset view with an engine on (**Shift + pad 30** turns it off). {B}: on MIDI pad 30 shows dim when off and bright when on.
- **Pitch page, synths:** pads 17-24 pick one of the patch's 8 macros; each pair's value is that macro's position, written as automation. {B}: an empty pair starts at 0.
- **Pitch page, MIDI track:** pads 17-24 pick a destination of the engine (pitch of both oscillators, OSC 2 pitch, WAVE, FM, MIX, envelope → filter, SHAPE, decay) and the value (64 = no change) shifts it for those two steps, adding to or taking from the value on the engine's page. {B}: the knob LED shows the amount (dim at the centre, brighter the further it goes, up or down).
- {B} **Velocity page with its own destination:** on the velocity page, pads 17-24 pick a destination for page 2 (the same pad again = none); the knobs then write that destination (MIDI from the destination's point of no modulation, synths from 0). On MIDI page 2 uses the REL automation lane, so REL is not played or recorded while the step-drummer is on.
- {B} **Pitch-vel toggle (pad 32 of the view, green):** on top of their destinations, the pitch page moves the **notes** one degree of the project's scale every 8 knob steps (MIDI −8 … +8 from the centre, synths 0 … +16) and the velocity page also sets the notes' velocity. With the toggle, pitch destinations of the pitch page no longer detune the own synth (the note moves instead).

### {BETA} extras
- **Split keyboard:** hold Synth 1 and press Synth 2 (or the other way round): the top two rows play Synth 1, the bottom two Synth 2, each with its scale, octave and velocity. Knobs and Octave follow the synth pressed first; any track or view button leaves. *(since RC2.02:* with any pair of Synth 1, Synth 2, MIDI 1 and MIDI 2; the track you held first on top.*)*
- **Patch colours** in the Preset view: dark blue = mono, lavender = mono with glide, track colour = poly; the chosen one lighter.
- **Save a patch into the pack:** Preset view, **Clear + pad**, then **Clear + the same pad** within about 5 s: the patch as it sounds goes into that slot (the stock cannot save patches on the device). Refused in the internal memory's pack.
- **Macro destinations:** in the source view, pad 32 opens the editor. Turn a knob to pick its macro; the knob changes the current field and **Octave ▼ / ▲** walk the fields (slot 1-4, start, end, destination, depth); the pads draw the number. Any pad drops the macro; pad 32 closes the editor. Destinations are the CC / NRPN numbers of Novation's Programmer's Reference Guide (for example CC 74 = filter cutoff).
""", [F("Synth source view (the synth's button twice).",
        pads={25: ("white", "Noise"), 26: ("green", "In 1"), 27: ("green", "In 2"), 28: ("teal", "In 1\ninv."), 29: ("teal", "In 2\ninv."), 30: ("purple", "Step\ndrum"), 32: ("teal", "Macro\nedit")},
        buttons={"Synth 1": "white"}, view="Source"),
      F("Step-drummer view: steps on rows 1-2, destination on row 3, pad 32 = pitch-vel (RC2); K1-K8 = the 8 pairs.",
        pads={**{n: (("yellow" if (n - 1) // 2 % 2 == 0 else "red"), "", n not in (1, 2, 5, 9, 13)) for n in range(1, 17)}, 7: ("white", "▶"),
              **{n: ("green", ["Pitch", "OSC2", "WAVE", "FM", "MIX", "Env F", "SHAPE", "DEC"][n - 17], n != 17) for n in range(17, 25)}, 30: ("purple", "Step\ndrum"), 32: ("green", "Pitch\nvel")},
        knobs={k: f"pair {k}" for k in range(1, 9)}, buttons={"Oct ▲": "yellow", "Oct ▼": "grey", "1-16 / 17-32": "grey"}, view="Step-drummer")])

# ---------------------------------------------------------------------------------------------------- 10
sec("midi", "MIDI tracks as synths", f"""
Normally a MIDI track only sends MIDI. With the mod, MIDI 1 and MIDI 2 can each have their **own engine** on the Circuit itself; the notes still go out over MIDI.

### The engine (pad 27)
In the MIDI 1 / 2 Preset view, each press of **pad 27** moves to the next engine; its colour shows which: off (dark) → line input (yellow) → oscillator (green) → VA-drum (red) → granular (magenta) → sample (cyan, {B}) → FX sequencer (blue) → off.

| Engine | In plain words |
|---|---|
| Line input | The audio input (line 1 for MIDI 1, line 2 for MIDI 2) through the track's VCA, filter, envelope and LFO, triggered by its notes: shape an outside sound with the Circuit. |
| Oscillator | A two-oscillator synth: WAVE morphs sine (0) → triangle (42) → saw (84) → square (126); SHAPE folds, bends or changes the width; OSC 2 adds FM, ring and bit modes. One note = unison, two notes = one per oscillator ({B}: with one oscillator, the last note has priority). |
| VA-drum | The oscillator as a one-shot percussion voice: Sustain = pitch envelope decay, Release = filter envelope decay, LFO speed = noise level. Kick: sine, Decay ~70, Sustain ~30, envelope → pitch right; snare: more noise, short Decay, band pass. |
| Granular | Up to 16 grains of a sample at once: textures, frozen or stretched sounds (page 2 below). |
| Sample {B} | A pack sample one-shot, at the pitch of each note (C3 = as recorded): tunable drums on a MIDI track. **Note twice** = the picker: rows 3-4 the samples (Octave ▼ / ▲ = 4 pages, all 64), rows 1-2 the steps; hold a step and touch a sample = that step plays that sample (sample flip), also live with Record. |
| FX sequencer | No sound: each pair of steps of its step-drummer triggers a Master FX slot. |

- Every sound engine goes through a VCA, an effect and a filter (with envelope and LFO) before mixer strip 3 or 4; **pad 29** swaps the order VCA → effect → filter / filter → VCA → effect ({B}: pad 29 in the VCA-VCF page's colour).

### Pads of the MIDI Preset view
| Pad | Function |
|---|---|
| 1-5 | Knob page: 1 VCA-VCF, 2 OSC 1 (the granular controls in granular), 3 OSC 2, 4 the 8 automatable values, 5 modulation. {B}: **Clear + page pad** = that page back to its defaults. |
| 6 | *(since RC2.02)* **Mod matrix** (below). |
| 9-24 | {B} **Own-synth patches** (below). |
| 25 | CC editor of the template's macros. |
| 26 | Patch flip: every note goes out as a Program Change ({B}: only on the track's channel). Exclusive with the engine. |
| 27 | The engine. |
| 28 | One / two oscillators (oscillator and VA-drum). |
| 29 | Chain order. |
| Shift + 29 | {B}: gate retrigger; off (yellow) = legato, a new note while others are held only changes the pitch. |
| 30 | Step-drummer. |
| 31 | VA-drum: velocity scales the pitch and filter envelopes. |

### The knob pages
- **Page 1, VCA-VCF:** K1 attack (Shift sustain), K2 release (Shift decay), K3 envelope → level (Shift LFO → level), K4 envelope → filter (Shift LFO → filter), K5 filter (Shift filter type: DJ, LP 12, HP 12, band pass, notch, LP 24, HP 24), K6 resonance (Shift VCA gain, up to +18 dB with saturation), K7 LFO speed, K8 effect amount (Shift effect type: soft, hard, folded, wavefold, ring, comb, chorus).
- **Page 2, OSC 1:** K1 tune (Shift fine), K2 shape (Shift mix OSC 1 ↔ OSC 2), K3 envelope → pitch (Shift bitsync), K4 envelope → shape, K5 LFO → pitch, K6 LFO → shape, K7 WAVE, K8 LFO → morph (Shift envelope → morph).
- **Page 2, granular:** K1 pitch ±24 (Shift fine), K2 position (Shift position spread), K3 scan: centre freezes, right forward, left backward (Shift chance of a reversed grain), K4 grain size 5-500 ms (Shift pitch spread), K5 density 1-16 (Shift window), K6 scan zone (Shift note mode: pitch / slicer; {B} stretch = from the position to the end over a set number of steps, without changing pitch), K7 LFO → position (Shift LFO → size), K8 envelope → position (Shift source: RC a pack sample or, left, the capture; {B} the capture or the current sample of a drum).
- **Page 3, OSC 2:** {B}: K1 tune 2, K2 shape 2, K3 mix OSC 1 / OSC 2, K4 FM, K5 fine 2, K6 BITSYNC, K7 WAVE 2, K8 ring, all without Shift (RC0.9: K1 tune 2 with Shift fine 2, K2 shape 2 with Shift FM, Shift + K3 ring, K7 WAVE 2). **Page 4:** the 8 automatable values (tune, release, envelope → level, envelope → filter, filter, resonance, LFO speed, effect). **Page 5:** ADSR on top, LFO below ({B}: **Shift + K8** = the LFO's shape, six shapes in colours; *(since RC2.02)* seven, with a slewed sample & hold, and the triangle to start with).
- **Automation:** with Record + Play, the moves of the page 4 values are recorded into the pattern. {B}: **Clear + knob left** deletes that knob's automation (red), **Clear + knob right** = default (lavender).

### FX sequencer
Put effects into the Master FX slots first. Then open the step-drummer (pad 30) and put notes on steps (Shift + pad). Each knob picks a slot for its pair: 0 none, 1-5 = pads 26-30, 6 = pad 31; on every step with a note that slot switches on, and the knob LED takes the effect's colour. The knob moves slowly (about 48 steps of turning per slot). {B}: at the end of the travel, **random** (white): one of the assigned slots at random on each note.

### CC editor (pad 25)
Move a knob to pick it; its CC number is drawn on the pads. **Octave ▼ / ▲** walk the fields; turning the knob changes the value. A plain CC has number, start and end; 99 / 98 / 6 = 7-bit NRPN (MSB, LSB…), 38 = 14-bit NRPN. Save with pad 26; any view button or pad 25 discards.

### Mod matrix *(since RC2.02)*
With the engine on, **pad 6** of the MIDI Preset view turns the 8 knobs into **8 sources**: K1 velocity, K2 note, K3 random per note, K4 LFO 2, K5 envelope 2, K6 a drum hit, K7 the pattern position, K8 stepped random. **Turning a knob picks which parameter it moves** (any of the knob pages, one stretch each, in its page's colour) **and how much** (inside the stretch). While you turn, the pads show where that parameter is. **Shift + K4 / K5 / K6 / K8** = the LFO's shape and rate, the envelope's attack and decay, which drum, every how many steps. **Clear + knob** = source off; **Clear + pad 6** = all. Saved with the own-synth patches.

### Own-synth patches {B}
Rows 2-3 of the MIDI Preset view are 16 patch slots, 4 pages with Octave ▼ / ▲ (64 per pack, shared by MIDI 1 and 2). Touch = load (the tonic sounds while you hold). **Clear + pad** twice = save. **Duplicate + A + B** = swap; **Duplicate + A**, another pack, **Duplicate + B** = copy. Dim peach = a patch, bright = the last used, violet = empty. A patch keeps the engine, both oscillators, the order, every value and the step-drummer setting (the steps belong to the pattern). **Clear + the track button** resets the whole engine.
""", [F("MIDI 1 Preset view with the engine on.",
        pads={1: ("orange", "VCA\nVCF"), 2: ("green", "OSC1", True), 3: ("teal", "OSC2", True), 4: ("purple", "Auto", True), 5: ("pink", "Mod", True),
              **{n: ("peach", "", True) for n in range(9, 25)}, 25: ("magenta", "CC"), 26: ("yellow", "Flip", True), 27: ("green", "Engine"), 28: ("green", "2 osc", True),
              29: ("orange", "Order", True), 30: ("purple", "Step\ndrum", True), 31: ("teal", "Vel", True)},
        knobs={1: "Attack", 2: "Release", 3: "Env→A", 4: "Env→F", 5: "Filter", 6: "Reso", 7: "LFO", 8: "FX"}, buttons={"MIDI 1": "orange", "Preset": "white"}, view="MIDI 1 Preset")])

# ---------------------------------------------------------------------------------------------------- 11
sec("patterns", "Pattern tools", f"""
### Pattern Settings
Press **Pattern Settings** with a track chosen. As on a stock unit: pads 1-16 the first / last step, pads 17-24 the sync rate, pads 29-32 the direction. Added {B}:

| Pad | Function |
|---|---|
| 25 | The probability view in **mode 2** (below). {B}: **Clear + pad 25** clears the dynamics and random-mutate of the whole pattern (note tracks). |
| 26 | **Nudge** (orange). |
| 27 | **Fractal** order: 1 · 1 2 · 1 2 3 · … up to the last step. |
| 28 | **Deconstructed** order: the grid's diagonals (1 6 11 16 · 2 7 12 13 · 3 8 9 14 · 4 5 10 15, the same for 17-32). |

- **Nudge, step by step:** 1. in Pattern Settings, choose the pattern's **first step** with pads 1-16 as on the stock unit; 2. press **pad 26**: that step becomes step 1 and what was before it goes to the end (steps and automation, over 16 or 32 steps; the last step moves with them). Choosing step 2 moves everything one step earlier.
- Pads 27, 28 and the four direction pads exclude each other. The order is saved with the pattern; clearing the pattern removes it. Nudge and the orders work on the drums too.

### Arpeggiator {B}
- **Shift + pad 25** = the arpeggiator of the pattern the track plays, on / off (pad 25 green while on). **Shift + pads 27-32** = its order (fractal, deconstructed, up, down, ping-pong, random), apart from the pattern's direction. **Shift + pads 17-24** = its own resolution (from 1/4 on pad 17 to 1/32T on pad 24, as the sync rate; the same pad again = the track's). With Shift, the pads keep their Pattern Settings colours and the chosen ones show green.
- **Sequence:** when two or more notes start on a step, they play one at a time in the chosen order, each lasting its own gate (at most one arpeggio step).
- **Live:** the first note sounds as always; holding another one starts the arpeggio of the held notes until you let them all go (stopped: at the project's tempo). With Record the chord is recorded, and the sequence arpeggiates it.
- **Drums:** the same gestures in a drum's Pattern Settings. In the drum's Preset view the first sample held is the usual one; holding more makes the drum **jump from sample to sample** in that order. With Record (playing) each hit is recorded with its sample as the step's sample flip.

### Probability view
| How you open it | Row 3 | Row 4 |
|---|---|---|
| **Shift + Pattern Settings** | Probability (stock) | **Random-mutate** {B} |
| **Pattern Settings twice** (mode 1) | Probability (stock) | **Frequency** {B}: the step plays on the last of each n passes of its pattern (1-8; counted from Play) |
| **Pad 25** of Pattern Settings (mode 2) {B} | **Dynamics** | Random-mutate |

Choose a step that has notes (pads 1-16) and touch a pad of row 3 or 4.
- **Random-mutate** {B} (pads 25-32): none · 6 % octave · 6 % scale · 6 % both · 12 % scale · 12 % octave · 25 % scale · 25 % octave and 50 % scale. «Scale» = another note of the scale in the same octave, «octave» = one up or down. Without Record it changes only that time; with Record it is written (the sequence drifts). Tied notes do not change; each note of a chord is drawn apart.
- **Dynamics** {B} (pads 17-24): none · drunk (±2 micro steps) · drunk + accents · accents (velocity 0…+32) · dragging + accents (−1…+3) · dragging · balanced (velocity ±32) · accent dynamics (−32…+64). With Record and mode 2 on screen, what sounds is written into the pattern.
- **Drums** {B}: the same view for a drum (Pattern Settings twice = mode 1, pad 25 = mode 2). Frequency and dynamics as above (a drum can only be delayed inside its step); pads 25-28 = **random-mutate of the sample**: none · 25 % ±1 (the next sample in its row of 8) · 25 % ±8 (the same column in another row) · 12 % of each.

### Micro Step view {B}
Press **Gate** twice (Gate once is the stock Gate view). As on the stock unit: pads 17-22 = the 6 micro steps of the chosen step, **pad 24 = Tie** (a toggle: ties the chosen notes to the next step), pads 25-30 = the step's notes (touching one chooses it and plays it). **Each note has a single micro step:** touching another moves it there; for several in the step, enter several notes (drums can light several: repeats). Added:
- **Pad 32 = gate by holding** (green): when entering notes by hand, the time you hold the pad is the note's length.
- **Pad 31 = fixed length** (orange): with both off it opens a selector (pads 17-32 = 1-16 steps); picking a length turns it on, and every note entered by hand gets it.
- With one on, pressing it again turns it off; pressing the other one switches.

### Pattern chains and scenes {B}
- **Chain mode** for the whole project: in the Patterns view **Shift + Octave ▲** turns it on (Octave ▲ green), **Shift + Octave ▼** off (the rules stay stored).
- **Editing a rule** (mode on): a pattern = **A** (yellow); A again = one more play (up to 8; the knob LEDs count); another pattern of the track = **B** (green), the next one = **C** (red). n = 3 plays A A A B A A A C; B and C play once and the track returns to A.
- **Clear + pattern:** in the mode, removes the rule; outside, clears the pattern with its rule and order.
- **Scenes:** a scene saved in chain mode shows peach and brings the mode back when loaded. In the Mixer, **Shift + pads 9-16** = 1-8 repeats of the current scene; tracks following a rule blink.
- **Drop-ins on the bar** {B}: in the Mixer, **Shift + a track pad (1-8)** mutes or unmutes it as the next bar starts (it blinks while it waits; again cancels it).
- **Cue mode** {B}: on the Mixer's pan page (Octave ▼), **Shift + a knob turned right** turns it on (Octave ▼ pink) and **turned left** turns it off. The left output carries the mix in mono; the right one, only the tracks you send to the cue with their pan knob (from the centre to the right). Use it to hear a muted track before bringing it in: it plays in time on the right only.
""", [F("Pattern Settings: stock pads plus 25-28; with Shift, the arpeggiator (RC2).",
        pads={**{n: ("white", "", True) for n in range(1, 17)}, 1: ("white", "First"), **{n: ("green", "", True) for n in range(17, 25)},
              25: ("peach", "Mode 2\n/ Arp"), 26: ("orange", "Nudge"), 27: ("purple", "Fractal"), 28: ("purple", "Decon."), 29: ("purple", "Fwd", True), 30: ("purple", "Back", True), 31: ("purple", "Ping", True), 32: ("purple", "Rnd", True)},
        buttons={"Pattern Settings": "white", "Shift": "yellow"}, view="Pattern Settings"),
      F("Probability view, mode 2: row 3 = dynamics, row 4 = random-mutate.",
        pads={**{n: ("white", "", True) for n in range(1, 17)}, 3: ("white", "Step"), **{n: ("green", str(n - 16), n != 19) for n in range(17, 25)},
              **{n: ("peach", str(n - 24), n > 27) for n in range(25, 33)}},
        buttons={"Pattern Settings": "white"}, view="Probability"),
      F("Micro Step view (Gate twice): pad 31 fixed length, pad 32 gate by holding (RC2).",
        pads={**{n: ("white", "", True) for n in range(1, 17)}, 17: ("green", "μ1"), **{n: ("green", f"μ{n - 16}", True) for n in range(18, 23)}, 24: ("orange", "Tie", True),
              25: ("magenta", "Note"), 31: ("orange", "Fixed"), 32: ("green", "Hold")},
        buttons={"Gate": "white"}, view="Micro Step")])

# ---------------------------------------------------------------------------------------------------- 12
sec("scales", "Scales and the custom scale", f"""
**Scales** works as always (root and stock scale). {B} **Shift + Scales** opens the **custom scale editor** (the Scales button shows yellow with Shift):
- The pads are two octaves of a piano from the root: row 4 = the white keys of the first octave, row 3 its black keys, rows 2 / 1 the second octave.
- Press a key to add or remove it (up to 7). The **highest key is the period**: the root of the next iteration (it does not have to be an octave). The root is white, notes green, the period orange.
- On the note tracks each row of pads is one iteration (two per row with 4 notes or fewer). It also drives which notes light up, the quantising and random-mutate.
- Picking a stock scale switches the custom scale off (the keys are kept). Saved with the project.
""", [F("Custom scale editor (Shift + Scales): two octaves of a piano from the root.",
        pads={25: ("white", "Root"), 26: ("green", "+2"), 27: ("green", "+4", True), 28: ("green", "+5"), 29: ("green", "+7"), 30: ("green", "+9", True), 31: ("green", "+11", True), 32: ("orange", "+12"),
              18: ("grey", "+1", True), 19: ("grey", "+3", True), 21: ("grey", "+6", True), 22: ("grey", "+8", True), 23: ("grey", "+10", True)},
        buttons={"Scales": "yellow", "Shift": "yellow"}, view="Custom scale")])

# ---------------------------------------------------------------------------------------------------- 13
sec("metronome", "Metronome and count-in", f"""
{B} **Shift + Clear** walks four states, shown by the Clear LED while Shift is held: **red** = no metronome, **green** = metronome, **magenta** = count-in only, **cyan** = count-in and metronome.
- **Count-in:** with Record armed and the transport stopped, **Play** gives one bar of four clicks at the project's tempo (Record blinks), then recording starts. Play during the count cancels it.
- The click's volume is the stock one: press **Tempo / Swing** and turn **K5**. The count-in is saved with the project.
""")

# ---------------------------------------------------------------------------------------------------- 14
sec("setup", "Setup and MIDI", f"""
| Where | What it does |
|---|---|
| Setup, **pad 16** | Channel 16 for the project and the FX: receive and send (everything that is not a Program Change). |
| Setup, **pads 22 / 23** | Send the reverb return (cream) through strip 3 / the delay return (peach) through strip 4. |
| Setup, **shared channels** | MIDI 1 / 2 may use a channel another track uses: what they send also reaches that track internally. |
| Setup, **Record** {B} | Yellow = what a MIDI track sends to a synth over a shared channel is also recorded into that synth. Off by default and after power-off. |
| Setup, **pads 29 / 30** {B} | The **Program Change** channels of the project: listen (29) and send (30), 16 by default. First touch shows the channel on pads 1-16; a pad picks it; again = on / off. What arrives is sent again on the send channel. |
| Advanced Setup, **Duplicate** {B} | MIDI Thru jack: Thru (dim red) → Out 2 (green) → **Merge** (yellow: DIN In plus the device's MIDI) → **Filter** (blue: DIN In without the channels the device listens to). No SysEx in Merge / Filter; with Merge, switch Clock Tx off to avoid two clocks. |

- **RC0.9 known issue:** opening Setup from the Synth 1 / 2 view, that synth's channel cannot be picked: open Setup from another view. {B}: fixed.
""", [F("Setup view: pad 16, pads 22 / 23, and (RC2) pads 29 / 30 for the Program Change channels.",
        pads={16: ("white", "Ch 16"), 22: ("cream", "Rev →\n3"), 23: ("peach", "Dly →\n4"), 29: ("white", "PGM\nRx"), 30: ("white", "PGM\nTx")},
        buttons={"Record": "yellow"}, view="Setup")])

# ---------------------------------------------------------------------------------------------------- 15
sec("projects", "Projects and packs", f"""
### Copying projects {B}
In the Projects view: **Duplicate + pad A** = the source (blinks yellow; Duplicate + A again forgets it), **Duplicate + pad B** = the copy. An empty B is written at once; a B in use blinks white and you repeat Duplicate + B within about 5 s. The loaded project's slot is never written. **To another pack:** pick the source, load the other pack, go back to Projects and Duplicate + B. Save first: it copies what is on the card, and the unit does not respond for a moment while copying. A project keeps patch and sample numbers, not the sounds: in another pack it plays with that pack's patches and samples.

### Deleting a pack
In the packs view (**Shift + Projects**) touch **Clear**: for about 5 s the packs that can be deleted blink (never the loaded one, never the internal memory's). Touch the pack, then **Clear** again within 5 s. The slot can be reused after a restart. Not in the safer build.
""")

# ---------------------------------------------------------------------------------------------------- 16
sec("saved", "What is saved where", f"""
| Where | What |
|---|---|
| **The project** | New drum knobs, Master FX slots, synth source, reverb / delay settings; {B} also the Master FX knobs and compressor, chain mode and scenes, count-in, arpeggiator, custom scale, gate by holding / fixed length, drum sidechain knobs, the step-drummer's page 2 and toggle. |
| **The pattern** | The step-drummer's notes and values, FX sequencer values; {B} chain rules, play order, frequency, dynamics, random-mutate (drums too), recorded rollers and drum arpeggios. |
| **The pack** (on save) | Captures used as drums; {B} saved synth patches, own-synth patches. |
| **Device settings** | The MIDI track engine (pad 27, pages 1-2), the step-drummer on / off; {B} MIDI Thru mode, Program Change channels. |
| **Not saved** | OSC 2 values, the granular Shift parameters, latched effects, the song pointer, the Setup Record toggle, the capture itself (unless it replaced a drum). |
""")

# ---------------------------------------------------------------------------------------------------- 17
sec("not", "What the mod does not do", """
- Patterns are still at most 32 steps, and a track cannot change its type; the closest thing is a MIDI track with an engine (section 10).
- The developer tools (diagnostic builds, DSP internals) are left out of this guide: see the repository's technical notes.

### Known issues in RC0.9 (fixed in RC2)
- Drums can sound different from a stock Circuit in new or untouched projects (filter mode DJ): Shift + K5 to EQ tilt.
- Setup opened from the Synth 1 / 2 view cannot pick that synth: open Setup from another view.
- The left part of the drum K3 (sample start) is under investigation.
- In older betas the delay stuttered when moving the MIDI engine's knobs or modes: fixed since Beta 1.12.
""")

# ---------------------------------------------------------------------------------------------------- 18
sec("midiref", "MIDI reference", f"""
Everything new goes out and comes in over CC / NRPN, following the CC Tx / Rx filters of Setup. Full tables: the [MIDI reference](midi-en.html).
- **Drums** (drum channel): NRPN MSB 5-8 = Drums 1-4; LSB 1 pitch envelope, 2 ring frequency, 3 LFO, 4 LFO speed, 5 envelope → cutoff, 6 resonance, 7 envelope shape, 8 ring amount, 9 filter mode, 10 start point, 11 bitcrush, 12 distortion type; {B} 13 cut, 14 attack.
- **Master FX** (channel 16): NRPN MSB 9, LSB = 4 × effect + knob: Gater 0-3, Auto-Filter 4-7, Digitise 8-11, Phaser 12-15, Glitch 16-19 (in RC0.9, Vinyl).
- **MIDI track engine** (the track's channel): filter CC 74, resonance 71, envelope → filter 79, attack 73, decay 75, sustain 70, release 72, effect 91, gain 59, tune 26, fine 27, wave 20, shape 21, tune 2 37, fine 2 39, wave 2 30, shape 2 31, mix 52, ring 54, LFO speed NRPN 0:76; the rest NRPN MSB 4.
- **Program Change** {B}: the project's listen / send channels in Setup (pads 29 / 30); patch flip on the track's channel.
""")

# ---------------------------------------------------------------------------------------------------- 19
CHANGES_TITLE = "About this edition"
CHANGES = """Corrected from the community guide: the uploader does not download the official firmware (you give it the file); RC0.9S has no remote diagnostics to leave out (no build has had them since SC36.1); the capture does not survive power-off unless it replaced a drum and the project was saved; Nudge works from the first step chosen in Pattern Settings (the original guide could not find the sequence); the three ways into the probability view are told apart (stock, mode 1, mode 2) and what is beta-only is marked (random-mutate, Nudge, play orders); the original names (capture, step-drummer) are back; the RC0.9 known issues are listed. Added: everything after Beta 1.3 (metronome and count-in, arpeggiator for notes and drums, custom scale, gate by holding and fixed length, drum rollers, the split drum K3, drum sidechain knobs, the step-drummer's page 2 and pitch-vel toggle, frequency / dynamics / random-mutate on the drums, Program Change channels, automation clearing on the MIDI engine, the recording fixes)."""
