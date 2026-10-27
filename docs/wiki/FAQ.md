# FAQ

*[Versión en español](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/FAQ-ES) · [Home](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Home) · [Roadmap](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Roadmap) · [Guide by views](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html) · [Changelog](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/blob/main/docs/CHANGELOG.md#changelog)*

Current versions (2026-10-27): **RC2.10**, **RC2.10S** and **Beta 3.35**.

## Installing

**1. What is CIRCUIT-HACKS?**
A set of patches for the official **Novation Circuit Tracks** firmware 1.2.1 (build 4486). The installer takes the official firmware you download from Novation, patches it in your browser and sends it to the device. It adds features to every view: a synth engine on the MIDI tracks, new drum controls, Master FX, an arpeggiator, scale and chord tools and more. See the [feature list](https://ghillermo.github.io/CIRCUIT-HACKS-RC/en.html) and the [guide by views](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html).

**2. Is it safe? Can I go back to the stock firmware?**
Novation's bootloader is never touched, so you can always send the official firmware again. If the device does not boot, hold **Scales + Preset + Note** while switching it on: that is Novation's bootloader mode, and from there you can send any firmware. **Back up your SD card before installing** any version. See [Installing and going back](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#instalar).

**3. RC, RC "S" or Beta: which one should I install?**
- **RC** (release candidate, now RC2.10): the features that have been tested together.
- **RC S** (RC2.10S): the same, but the mod never writes files of its own to the SD card (no saving of own patches, samples or copies between packs). The safest choice.
- **Beta** (now Beta 3.35): RC + the newest features. Every fix goes to both the RC and the Beta; new features go to the Beta first.

**4. Does it work on the original Circuit or the Circuit Rhythm?**
No: CIRCUIT-HACKS is for the **Circuit Tracks** (firmware 1.2.1, build 4486) only. For the **Circuit Rhythm** there is a separate project, [Circuit Remix](https://github.com/Ghillermo/CIRCUIT-REMIX), which ports these features and adds its own.

**5. How do I install it?**
1. Download [`rc_uploader.zip`](https://ghillermo.github.io/CIRCUIT-HACKS-RC/rc_uploader.zip), unzip it and open `rc_uploader.html` in **Chrome or Edge** (they support Web MIDI with SysEx).
2. Download the official firmware 1.2.1 (build 4486) from [Novation Components](https://components.novationmusic.com/api/v2/firmwares/168/file) and load it in the page.
3. Connect the Circuit Tracks over USB, choose the version and send.

**6. The installer cannot find the device or rejects the file.**
Use Chrome or Edge and allow MIDI / SysEx access when the browser asks. Close any other program that holds the MIDI port (Components, a DAW). The file must be the official 1.2.1 build 4486 `.syx` exactly: the installer checks it and refuses anything else.

## Saving and data

**7. What is saved, and where?**
There are five places: the **pattern**, the **project** (both saved when you save the project), the **pack** (written at once to the card), the **device settings** (kept for every project) and nowhere (lost at power-off). The full tables are in [What comes back after a restart](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#guardado).

**8. I changed a sound and it was gone after switching off.**
- Press **Save twice** before switching off or loading another project, as on the stock firmware.
- A knob turned without Record changes the project's sound, not the pattern. To make it change along the pattern, record it.
- The MIDI 1 / 2 synth keeps its values in the device settings; to keep a sound for later, save it as a patch (MIDI Preset view, Clear + pad twice).
- Stop the sequencer and wait two seconds before switching off, and use the power button.

Details: [What a pattern holds and how to make sure it is saved](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#datos-patron) and [What is lost at a restart](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#datos-perdido).

**9. Why is the Save LED red?**
The mod refused to write to the card. Either the pack is the one in the **internal memory** (no SD card: read-only for the mod) or you are running an **S** version. Projects still save normally, as on the stock firmware.

**10. Can I use it without an SD card?**
Yes. The mod's own saving features (patches, samples, copies) do not write to the internal memory, so keep your important work on an SD card. With the versions that do not end in "S", do not keep important projects in the internal memory.

**11. Do projects and packs made with the mod still work on the stock firmware?**
Yes. The mod keeps its own data in parts of the files the stock firmware does not use, and the stock firmware ignores them.

**12. Can I still use Novation Components?**
Yes, as usual. Components does not know about the mod's own-synth patches (MIDI 1 / 2), which live inside the pack's patch files; [`tools/patchtool.py`](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/blob/main/tools/patchtool.py) lists and copies them on a computer. Back up the card before syncing packs.

## Sound and behaviour

**13. I hear a low humming or pulsing feedback.** ([#5](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/issues/5))
In the **Setup** view (not Advanced Setup), **pads 22 / 23** send the reverb / delay returns through mixer tracks 3 / 4. With effect sends on those tracks the signal feeds back into itself: that is by design. Switch pads 22 / 23 off if you do not want it. See [Setup](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#setup).

**14. The drum samples do not sound like on a stock Circuit.** ([#7](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/issues/7))
Fixed since RC2 (Beta 1.16): new and untouched projects sound as on the stock firmware. If an older project still sounds different, set the drum's filter mode (**Shift + K5**) back to the stock tilt EQ. See [Drum track view](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#drum-pista).

**15. The delay stutters when I move the MIDI synth knobs.** ([#6](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/issues/6))
Fixed since RC2 (the settings are now written to the card only while the transport is stopped). Update to the current RC or Beta.

**16. How do I find the shortcuts?**
Hold **Shift**: everything that has a shortcut in the current view lights **yellow**, and the option already chosen shows in another colour. **Clear + knob** puts a knob back to its default (lavender) or deletes its automation (red). See [Buttons that work in every view](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#botones).

**17. Can I change patches per step (like an "AFX mode")?** ([#11](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/issues/11))
Yes, with **patch flip**. In the Setup view, set a MIDI track to the synth's channel. Then turn on pad 26 in its Preset view: the notes of that track become Program Changes, so you sequence patch changes like notes. See [MIDI 1 / 2 Preset view](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#midi-preset).

**18. How many voices can the MIDI 1 / 2 synth play?**
Beta 3.35: up to 4 notes per track; with FM, 6 voices shared between the two tracks (3 + 3 when both use FM). The granular engine is one voice. The RC versions do not have this polyphony yet. The heaviest combinations (two poly tracks with supersaw, all drums and Master FX) have not been measured on the device yet: if the audio slows down or clicks, please report it.

## MIDI

**19. Which CCs and NRPNs control the new features?**
See [MIDI: own behaviours, new CCs and NRPNs](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#midi) and the [MIDI reference](https://ghillermo.github.io/CIRCUIT-HACKS-RC/midi-en.html). The stock parameters keep the numbers of Novation's [Programmer's Reference Guide](https://fael-downloads-prod.focusrite.com/customer/prod/downloads/circuit_tracks_programmer_s_reference_guide_v3.pdf).

**20. My external keyboard does not play the MIDI 1 / 2 synth or the arpeggiator.** ([#13](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/issues/13), [#14](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/issues/14))
Since RC2.08, notes arriving on the channel of MIDI 1 / 2 play its synth. To send them through the arpeggiator, turn on **pad 22 of Advanced Setup** (Beta 3.35; off by default, so a keyboard with its own arpeggiator does not clash). See [Advanced Setup](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#advanced-setup).

**21. Can I get the DIN MIDI input on my computer over USB?** ([#10](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/issues/10))
Yes: **pad 23 of Advanced Setup** (USB merge, Beta 3.35). Without the DIN clock when Clock Tx is on, and without SysEx.

**22. What are the mod matrix and the macro destinations?**
See [Mod matrix and macro destinations](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html#destinos): the stock matrix and macros of Synth 1 / 2 (with the list of 70 macro destinations), and the mod's own matrix for MIDI 1 / 2.

## The project

**23. How do I report a bug?**
Open an [issue](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/issues) with the version (for example RC2.10 or Beta 3.35), what you did step by step, what you expected and what happened. If you can, attach the project or the pack, or a short recording.

**24. How do I suggest a feature?**
Use [Discussions](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/discussions) or an issue. Check the [Roadmap](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Roadmap) first: suggestions on control, usability and on how the data is saved are especially welcome.

**25. Is this affiliated with Novation?**
No. It is an independent project. The firmware it patches is Novation's and is proprietary: the installer only installs on a Circuit Tracks.

**26. How can I support the project?**
[PayPal](https://PayPal.me/ghillermo), bug reports with clear steps, and testing the betas.
