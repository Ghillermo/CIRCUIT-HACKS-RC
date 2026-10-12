# Cambios — CIRCUIT-HACKS

*English version below: [Changelog](#changelog).*

Novedades y arreglos de cada versión candidata (RC). Cada RC tiene una **versión más segura** (sufijo **S**) sin las funciones que escriben en la tarjeta SD por su cuenta (gestión del pack, A8). Las referencias (A4, C6…) son las secciones del [manual](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html). El detalle técnico está en [`docs/NOTAS.md`](docs/NOTAS.md).

## BETA5 — 2026-10-12

Versión beta (= SC39.6): BETA4 + más funciones nuevas aún sin probar en el aparato. Sin versión «S». Acompaña a RC0.5 / RC0.5S, que no cambian. En el manual van marcadas **solo BETA5** (también las de las betas anteriores).

### Novedades
- **Copiar proyectos a otro hueco o a otro pack** (A17). En la vista Projects, Duplicate + pad A elige el proyecto y Duplicate + pad B lo copia; sobre un hueco ocupado pregunta antes.
- **Knobs de tipo en colores.** Con Shift, el modo de filtro de drums (K5), el tipo de distorsión de drums (K8) y el modo de nota del granular (K6) enseñan el tipo elegido como un color, no como un brillo.

### Arreglos
- El blanco tenue del pad 8 de Master FX (sin nada que apagar) y de los huecos sin asignar pulsaba despacio: ahora es fijo.

### Cambios
- La vista de efectos del master se llama **Master FX** en toda la documentación.

## BETA4 — 2026-10-12

Versión beta (= SC39.4): BETA3 + más funciones nuevas aún sin probar en el aparato. Sin versión «S». Acompaña a RC0.5 / RC0.5S, que no cambian. En el manual van marcadas **solo BETA4** (también las de las betas anteriores).

### Novedades
- **Guardar el patch del sinte en el pack** (A15). En la vista Preset de Synth 1 / 2, Clear + pad pregunta (el hueco parpadea en blanco) y Clear + el mismo pad otra vez guarda el patch tal como suena, con sus cambios. El original solo puede con Components.
- **Destinos de los macro knobs** (A16). En la vista de la fuente del sinte el pad 32 abre un editor: un knob elige su macro y Octave ▼ / ▲ recorre ranura, inicio, fin, destino y profundidad; los pads dibujan el número (el destino por su CC / NRPN).
- **`tools/patchtool.py`** (A14): en el PC, los patches del sinte propio de un pack (Components no los conoce): cada patch es un fichero `.ctm`: lista los 64 huecos con su índice, sube y baja patches, los copia entre huecos y packs, lee y edita el motor y los parámetros, crea patches nuevos, los nombra y vacía huecos.
- **Escucha al cargar un patch del sinte propio** (A14): mientras mantienes el pad suena la tónica de la escala.
- **Clear + botón MIDI 1 / 2** (A14): los valores del motor de esa pista a los iniciales.

### Cambios
- **Patches del sinte propio de MIDI 1 / 2** (A14): el guardado pasa a **Clear + pad dos veces** (como el del sinte); **Duplicate + A + B intercambia** dos huecos; los huecos vacíos se ven en violeta. Ya no existen Duplicate + pad = guardar ni Clear + pad = vaciar (BETA2 / BETA3).
- **rc_uploader:** las versiones que escriben en la tarjeta (todas menos las «S») piden marcar una casilla antes de enviar: copia de la microSD hecha y no usar la memoria interna para guardar proyectos.

## RC0.5 / RC0.5S — 2026-10-12

RC0.5 = RC0.4 + un cambio. RC0.5S = RC0.4S + el mismo cambio (**S**). La beta que la acompaña es **BETA3** (= SC39.2: RC0.5 + las funciones de BETA2).

### Cambios
- **El sample capturado pasa por los efectos de Master FX** (C5, **S**). El sample que se dispara con el pad 7 (o desde un hueco de la fila inferior) sonaba sin los efectos de Master FX; ahora pasa por todos. A cambio, la captura (pad 32) graba la salida **sin** los efectos de Master FX (antes los llevaba). El Glitch queda también delante de los otros efectos.

## BETA2 — 2026-10-12

Versión beta (= SC39.1): BETA1 + más funciones nuevas aún sin probar en el aparato. Sin versión «S». En el manual van marcadas **solo BETA2** (también las de las betas anteriores).

### Novedades
- **Patches del sinte propio de MIDI 1 / 2** (A14). En la vista Preset de MIDI 1 / 2 las filas 2 y 3 son 16 huecos de patch del motor de la pista: tocar carga, Duplicate + pad guarda, Clear + pad vacía; Octave ▼ / ▲ cambia entre 4 páginas (64 huecos por pack, compartidos por las dos pistas). Un patch guarda el motor elegido y todos sus valores. Se guardan en la tarjeta, en el espacio libre que hay detrás de los patches de sinte del pack.
- **Selector de fuente del granular** (D5). Shift + K8 de la página granular recorre la captura (rojo) y el sample que tiene en ese momento cada drum (naranja, amarillo, violeta, verde azulado); el elegido queda fijado aunque el drum cambie después.

### Cambios
- **Clear + pad de página** (C1). En la vista Preset de MIDI 1 / 2, Clear + un pad de página (1-5) devuelve a los valores iniciales los knobs de esa página. Clear + pad 27 (BETA0 / BETA1: todo el motor a la vez) ya no reinicia nada.

## BETA1 — 2026-10-12

Versión beta (= SC39): BETA0 + más funciones nuevas aún sin probar en el aparato. Sin versión «S». En el manual van marcadas **solo BETA1** (también las de BETA0).

### Novedades
- **Random-mutate por paso** (C8). En la vista de probabilidad (Shift + Pattern Settings) la fila 4 (pads 25-32, melocotón) da a cada paso una probabilidad de que sus notas salten de octava y / o cambien a otra nota de la escala del proyecto al sonar: apagado, octava 6 %, escala 6 %, las dos 6 %, escala 12 %, octava 12 %, escala 25 %, octava 25 % + escala 50 %. Sin Record la nota cambiada suena esa vez; con Record se escribe en el paso. En Synth 1 / 2 y MIDI 1 / 2. La fila 3 sigue siendo la probabilidad del original.
- **Teclado partido Synth 1 + Synth 2** (A12). Mantén un Synth y pulsa el otro: las dos filas de arriba tocan Synth 1 y las dos de abajo Synth 2, cada uno con su escala, octava y velocity.
- **Patches de sinte por modo de voz** (A13). En la vista Preset de Synth 1 / 2: mono azul oscuro, glide lavanda, poly como siempre.

### Arreglos
- **Advanced Setup:** los pads 22 / 23 ya no se encienden (allí no hacían nada).

## BETA0 — 2026-10-11

Versión beta (= SC38.7): RC0.4 + funciones nuevas aún sin probar en el aparato. Sin versión «S». En el manual van marcadas **solo BETA0**.

### Novedades
- **Stretch del granular** (D5). Shift + K6 tiene un tercer modo de nota, **stretch**: el tramo de K2 al final del sample dura K3 pasos (1 a 64) a cualquier tempo sin cambiar el tono, alineado con el inicio del transporte.
- **MIDI Thru: Merge y Filter** (B5). Duplicate en Advanced Setup pasa por Thru → Out 2 → **Merge** (el DIN In y el MIDI del aparato por el jack Thru, LED amarillo) → **Filter** (el DIN In sin los canales en los que escucha el aparato, LED azul). Se guarda en los ajustes.
- **Clear + pad 27 = el motor de la pista a sus valores iniciales** (C1). En la vista Preset de MIDI 1 / 2, todos los valores de todas las páginas (con y sin Shift) vuelven a los iniciales de una vez; el motor elegido no cambia.

## RC0.4 / RC0.4S — 2026-10-11

RC0.4 = RC0.3 + arreglos (SC38.2-SC38.6, sin sus funciones nuevas). RC0.4S = RC0.3S + los arreglos que no tocan la SD (marcados con **S**).

### Arreglos
- **Captura armada desde parado** (C5, **S**). Shift + pad 32 y Play empezaba a grabar un compás tarde y terminaba al final del segundo; ahora empieza en el primer pulso de Play y graba ese compás.
- **Shift + pad 7 = bucle enganchado** (C5, **S**). Desde SC34.1 el bucle de Shift + 7 sonaba solo mientras se mantenía el pad (como el modo loop); ahora sigue, en cualquier modo, hasta volver a pulsar el 7 (o el pad 8). Igual con Shift + un hueco del sample. El modo loop (K2) sigue sonando solo mientras se mantiene.
- **Duplicate entre packs a un hueco vacío** (A8). Copiar un sample o un patch de sinte a un pad vacío no hacía nada; ahora se copia. Un patch más allá del final de su banco deja vacíos los huecos de en medio, como el guardado del original.
- **Vista de packs:** Clear parpadeaba al abrirla; ahora se ve blanco fijo (A8).

## RC0.3 / RC0.3S — 2026-10-11

RC0.3 = SC38. RC0.3S = RC0.2S + todo lo de esta versión que no toca la SD (marcado con **S**).

### Novedades
- **Mixer: Shift + knob = nivel a 100 / 0** (A11, **S**). En la página de niveles, Shift + girar a la derecha pone la pista a 100 y a la izquierda a 0. Funciona como un giro del knob (sale por MIDI y se graba en la automatización). En el original Shift + knob hacía lo mismo que el knob solo; panorama, Clear + knob y Master FX no cambian.
- **Clear + knob en Master FX** (A4, **S**). Con Clear pulsado, girar a la derecha un knob del efecto elegido lo devuelve a su valor por defecto (efectos 1-6, Glitch y sample); mientras Clear está pulsado, esos knobs se ven azules en su valor por defecto y rojos si no.
- **Copias entre packs en su sitio** (A8). Si el sample copiado cabe en el sitio del sample sustituido, va ahí y no gasta la memoria de importación (≈ 44 s), que además vuelve a empezar cuando ningún sample la usa.

### Cambios
- **Sustituir un drum por la captura = Clear + pad dos veces** (A9, **S**). Antes era Shift + pad, que en el original es la selección silenciosa de un sample: Shift + pad vuelve a hacer eso.

### Arreglos
- **Clear + knob en drums:** el LED a la derecha es el **azul** del original; antes salía un rojo anaranjado tenue (A4, **S**).
- **Borrar un pack:** Clear se queda blanco fijo mientras pregunta (antes parpadeaba) y los packs vuelven a su color al terminar o cancelar (antes podían quedarse apagados hasta salir de la vista) (A8).
- **Memoria de importación:** cuando estaba llena, una copia entre packs podía escribirse encima de un sample que aún sonaba (sonaba mal hasta recargar el pack; los ficheros estaban bien). Ahora no cambia nada si no hay sitio (A8).
- **Patches en la vista de la fuente:** con Duplicate pulsado antes de abrir la vista de la fuente del sinte, sus pads copiaban o intercambiaban patches; ya no (A8).

## RC0.2 / RC0.2S — 2026-10-10

RC0.2 = SC37.5. RC0.2S = RC0.1S + la sobrecarga del Glitch.

### Novedades
- **Sobrecarga en el Glitch** (C6, D6, **S**). K4 en la mitad de arriba imita un DSP sobrecargado: bloques que llegan tarde (chasquidos) y, desde ~3/4, todo más grave y lento. Es una simulación: no carga el DSP de verdad.

### Arreglos
- **Borrar un pack:** el LED de Clear no se encendía en la vista de packs (A8).

## RC0.1 / RC0.1S — 2026-10-10

RC0.1 = SC37.4. RC0.1S = RC0S + lo de esta versión que no toca la SD.

### Novedades
- **Copiar samples y patches de sinte entre packs** (A8): Duplicate + A en un pack, Duplicate + B en otro; el pack de origen no cambia. Dentro del mismo pack, Duplicate + A + B intercambia (también los patches de sinte).

### Cambios
- **Borrar un pack = Clear, el pack, Clear** (A8). En RC0 era Clear mantenido + pack, que no funcionaba en el aparato.

### Arreglos
- **Duplicate en las vistas Preset de drums y de sinte:** no se encendía ni hacía nada en el aparato (A8).
- **Intercambio de samples dentro del pack:** dejaba un clic al final (el fichero se reescribía desde la memoria del DSP); ahora los ficheros se mueven tal cual (A8).
- **Cambio de motor del pad 27 con una nota sostenida:** sin clic (C1, **S**).
- **Pad 28** de MIDI 1 / 2 oculto mientras no hay osciladores (C1, **S**).
- **Dos huecos con Glitch a la vez:** ya no se copian los knobs (C6, **S**).
- **Colores:** Vinyl en melocotón y los retornos de reverb / delay del Setup en sus colores (**S**).

## RC0 / RC0S — 2026-10-09

Primera versión candidata (= SC36.2; RC0S = SC362S, sin escrituras propias en la SD): todo lo descrito en el manual hasta entonces, entre otras cosas el sinte granular, el Glitch, el secuenciador de efectos, Master FX, el motor de las pistas MIDI, el step-drummer, los knobs nuevos de drums y la gestión del pack.

---

<a id="changelog"></a>
# Changelog — CIRCUIT-HACKS

New features and fixes of every release candidate (RC). Every RC has a **safer build** (suffix **S**) without the features that write to the SD card on their own (pack management, A8). The references (A4, C6…) are the sections of the [manual](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html). The technical detail is in [`docs/NOTAS.md`](docs/NOTAS.md) (Spanish).

## BETA5 — 2026-10-12

Beta (= SC39.6): BETA4 + more new features not yet tested on the device. No “S” build. It goes with RC0.5 / RC0.5S, which do not change. The manual marks them **BETA5 only** (the earlier betas’ too).

### New
- **Copying projects to another slot or another pack** (A17). In the Projects view, Duplicate + pad A picks the project and Duplicate + pad B copies it; onto a slot in use it asks first.
- **Type knobs as colours.** With Shift, the drums’ filter mode (K5), the drums’ distortion type (K8) and the granular note mode (K6) show the chosen type as a colour, not as a brightness.

### Fixed
- The dim white of pad 8 of Master FX (nothing to switch off) and of the unassigned slots pulsed slowly: it is steady now.

### Changed
- The master effects view is called **Master FX** throughout the documentation.

## BETA4 — 2026-10-12

Beta (= SC39.4): BETA3 + more new features not yet tested on the device. No “S” build. It goes with RC0.5 / RC0.5S, which do not change. The manual marks them **BETA4 only** (the earlier betas’ too).

### New
- **Saving the synth’s patch into the pack** (A15). In the Preset view of Synth 1 / 2, Clear + pad asks (the slot blinks white) and Clear + the same pad again saves the patch as it sounds, with its changes. The original can only do it with Components.
- **Macro knob destinations** (A16). In the synth source view, pad 32 opens an editor: a knob picks its macro and Octave ▼ / ▲ steps slot, start, end, destination and depth; the pads draw the number (the destination by its CC / NRPN).
- **`tools/patchtool.py`** (A14): on the PC, the own-synth patches of a pack (Components does not know them): each patch is a `.ctm` file: lists the 64 slots with their index, uploads and downloads patches, copies them between slots and packs, reads and edits the engine and the parameters, makes new patches, names them and empties slots.
- **Audition when loading an own-synth patch** (A14): while you hold the pad, the root of the scale sounds.
- **Clear + the MIDI 1 / 2 button** (A14): the values of that track’s engine back to the initial ones.

### Changed
- **Patches of the MIDI 1 / 2 own synth** (A14): saving is now **Clear + pad twice** (like the synth’s); **Duplicate + A + B exchanges** two slots; empty slots are violet. Duplicate + pad = save and Clear + pad = empty (BETA2 / BETA3) are gone.
- **rc_uploader:** the versions that write to the card (all but the “S” ones) ask for a tick box before sending: the microSD backed up, and the internal memory not used to save projects.

## RC0.5 / RC0.5S — 2026-10-12

RC0.5 = RC0.4 + one change. RC0.5S = RC0.4S + the same change (**S**). The beta that goes with it is **BETA3** (= SC39.2: RC0.5 + BETA2’s features).

### Changed
- **The captured sample goes through the Master FX effects** (C5, **S**). The sample triggered with pad 7 (or from a slot of the bottom row) played without the Master FX effects; now it goes through all of them. In exchange, the capture (pad 32) records the output **without** the Master FX effects (it used to hold them). The Glitch also sits in front of the other effects now.

## BETA2 — 2026-10-12

Beta (= SC39.1): BETA1 + more new features not yet tested on the device. No “S” build. The manual marks them **BETA2 only** (the earlier betas’ too).

### New
- **Patches of the MIDI 1 / 2 own synth** (A14). In the Preset view of MIDI 1 / 2, rows 2 and 3 are 16 patch slots of the track engine: touch loads, Duplicate + pad saves, Clear + pad empties; Octave ▼ / ▲ steps through 4 pages (64 slots per pack, shared by both tracks). A patch holds the chosen engine and all its values. They are kept on the card, in the free space behind the pack’s synth patches.
- **Granular source selector** (D5). Shift + K8 of the granular page travels over the capture (red) and the sample each drum has at that moment (orange, yellow, violet, teal); the chosen one stays fixed even if the drum changes later.

### Changed
- **Clear + page pad** (C1). In the Preset view of MIDI 1 / 2, Clear + a page pad (1-5) puts the knobs of that page back to their initial values. Clear + pad 27 (BETA0 / BETA1: the whole engine at once) no longer resets anything.

## BETA1 — 2026-10-12

Beta (= SC39): BETA0 + more new features not yet tested on the device. No “S” build. The manual marks them **BETA1 only** (BETA0’s too).

### New
- **Random-mutate per step** (C8). In the probability view (Shift + Pattern Settings) row 4 (pads 25-32, peach) gives each step a chance of its notes jumping an octave and / or moving to another note of the project’s scale when they play: off, octave 6 %, scale 6 %, both 6 %, scale 12 %, octave 12 %, scale 25 %, octave 25 % + scale 50 %. Without Record the changed note plays that once; with Record it is written into the step. On Synth 1 / 2 and MIDI 1 / 2. Row 3 is still the original’s probability.
- **Split keyboard Synth 1 + Synth 2** (A12). Hold one Synth and press the other: the two top rows play Synth 1 and the two bottom rows Synth 2, each with its scale, octave and velocity.
- **Synth patches by voice mode** (A13). In the Preset view of Synth 1 / 2: mono dark blue, glide lavender, poly as always.

### Fixed
- **Advanced Setup:** pads 22 / 23 no longer light up (they did nothing there).

## BETA0 — 2026-10-11

Beta (= SC38.7): RC0.4 + new features not yet tested on the device. No “S” build. The manual marks them **BETA0 only**.

### New
- **Granular stretch** (D5). Shift + K6 gets a third note mode, **stretch**: the stretch from K2 to the end of the sample lasts K3 steps (1 to 64) at any tempo without changing the pitch, in step with the start of the transport.
- **MIDI Thru: Merge and Filter** (B5). Duplicate in Advanced Setup steps Thru → Out 2 → **Merge** (DIN In and the device’s MIDI out of the Thru jack, yellow LED) → **Filter** (DIN In without the channels the device listens to, blue LED). Saved in the settings.
- **Clear + pad 27 = the track engine back to its initial values** (C1). In the MIDI 1 / 2 Preset view, every value of every page (with and without Shift) goes back to its initial value at once; the selected engine stays.

## RC0.4 / RC0.4S — 2026-10-11

RC0.4 = RC0.3 + fixes (SC38.2-SC38.6, without their new features). RC0.4S = RC0.3S + the fixes that do not touch the SD card (marked **S**).

### Fixed
- **Armed capture from stop** (C5, **S**). Shift + pad 32 then Play started recording a bar late and stopped at the end of the second bar; now it starts on Play’s first beat and records that bar.
- **Shift + pad 7 = latched loop** (C5, **S**). Since SC34.1 the Shift + 7 loop only played while the pad was held (like the loop mode); now it goes on, in any mode, until pad 7 (or pad 8) is pressed again. The same with Shift + a slot of the sample. The loop mode (K2) still only plays while held.
- **Duplicate between packs to an empty slot** (A8). Copying a sample or a synth patch to an empty pad did nothing; now it copies. A patch past the end of its bank leaves the slots in between empty, as the original’s save does.
- **Packs view:** Clear blinked when it opened; now it shows steady white (A8).

## RC0.3 / RC0.3S — 2026-10-11

RC0.3 = SC38. RC0.3S = RC0.2S + everything of this version that does not touch the SD card (marked **S**).

### New
- **Mixer: Shift + knob = level to 100 / 0** (A11, **S**). On the levels page, Shift + turning right sets the track to 100 and turning left to 0. It works like a turn of the knob (it goes out over MIDI and is recorded into the automation). On the original Shift + knob did the same as the plain knob; pan, Clear + knob and Master FX do not change.
- **Clear + knob in Master FX** (A4, **S**). With Clear held, turning a knob of the selected effect right takes it back to its default (effects 1-6, Glitch and sample); while Clear is held those knobs show blue at their default and red elsewhere.
- **Copies between packs in place** (A8). If the copied sample fits in the place of the replaced sample, it goes there and uses none of the import memory (≈ 44 s), which also starts again once no sample uses it.

### Changed
- **Replace a drum with the capture = Clear + pad twice** (A9, **S**). It was Shift + pad, which on the original is the silent selection of a sample: Shift + pad does that again.

### Fixed
- **Clear + knob on the drums:** the LED turned right is the original’s **blue**; a dim red-orange showed before (A4, **S**).
- **Deleting a pack:** Clear stays steady white while it asks (it blinked) and the packs get their colours back when it ends or is cancelled (they could stay dark until leaving the view) (A8).
- **Import memory:** when it was full, a copy between packs could be written over a sample that still played (it sounded wrong until the pack was loaded again; the files were right). Now nothing changes when there is no room (A8).
- **Patches in the source view:** with Duplicate held before the synth source view opened, its pads copied or swapped patches; not any more (A8).

## RC0.2 / RC0.2S — 2026-10-10

RC0.2 = SC37.5. RC0.2S = RC0.1S + the Glitch overload.

### New
- **Overload in the Glitch** (C6, D6, **S**). K4 in the upper half imitates an overloaded DSP: late blocks (clicks) and, from ~3/4, everything lower and slower. It is a simulation: the DSP is not really loaded.

### Fixed
- **Deleting a pack:** the Clear LED did not light in the packs view (A8).

## RC0.1 / RC0.1S — 2026-10-10

RC0.1 = SC37.4. RC0.1S = RC0S + what this version adds outside the SD card.

### New
- **Copy samples and synth patches between packs** (A8): Duplicate + A in one pack, Duplicate + B in another; the source pack does not change. Inside one pack, Duplicate + A + B swaps (synth patches too).

### Changed
- **Delete a pack = Clear, the pack, Clear** (A8). In RC0 it was Clear held + pack, which did not work on the device.

### Fixed
- **Duplicate in the drum and synth Preset views:** it did not light or do anything on the device (A8).
- **Swapping samples inside a pack:** it left a click at the end (the file was rewritten from the DSP memory); the files are now moved as they are (A8).
- **Engine change of pad 27 with a held note:** no click (C1, **S**).
- **Pad 28** of MIDI 1 / 2 hidden while there are no oscillators (C1, **S**).
- **Two Glitch slots at once:** the knobs are no longer copied (C6, **S**).
- **Colours:** Vinyl in peach and the Setup reverb / delay returns in their colours (**S**).

## RC0 / RC0S — 2026-10-09

First release candidate (= SC36.2; RC0S = SC362S, no writes of its own to the SD card): everything in the manual up to then, among other things the granular synth, the Glitch, the FX sequencer, Master FX, the MIDI track engine, the step-drummer, the new drum knobs and the pack management.
