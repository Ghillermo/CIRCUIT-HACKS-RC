# CIRCUIT-HACKS

Help me pay for tools and mantain this project and CIRCUIT REMIX: https://PayPal.me/ghillermo

Contributors:

Aleš Janda: https://alesjanda.cz, https://github.com/kybl 

No_Grand_9136: https://Reddit.com/user/No_Grand_9136

Theodor

Jens

If you want your name or website in this list, add it on your message when you send your contribution or send me a DM.


> 📢 **RC4.08 y la Beta 5.28.** RC4.08 = RC4 (todo lo de las betas hasta la 3.43: polifonía y modos de voz del sinte propio, FM, Jankó, pantalla de acordes, granular en estéreo…) + arreglos: los pads cromáticos de los drums graban golpe y tono en su paso, la envolvente de Digitise, el paso marcado de la vista Velocity, que vuelve a los valores del proyecto, el Nudge, que mueve el contenido del tramo, tres formas del LFO que callaban el motor propio, el arpegio en una pista silenciada, las notas comunes de dos acordes, la cuenta atrás con un reloj externo, los LEDs de Sidechain y, como opción (Advanced Setup, pad 22), guardar el proyecto mientras suena esperando a que pares; **RC4.08** arregla el antialias del pulso del sinte propio con un ancho distinto del 50 %. La **Beta 5.28** (las betas que amplían RC4 se numeran 5.x) añade, casi todo sin probar en el aparato, la vista de automatización de los drums, un carril de automatización más por drum con bloqueos de estado y rampas, la foto de Record + paso en todas las pistas, Shift + Preset = el sonido del proyecto, el random-mutate rediseñado en notas y drums, el sweep entre dos pasos de automatización, el secuenciador de saltos de MIDI 1 / 2, Jankó rediseñado, el destello de cada nota con Shift, filtro → VCA → efecto como orden de fábrica, knobs de tipos más lentos, el acorde inverso, solo y solo flip en el Mixer (pad 16), las dinámicas del random-mutate rehechas (ghost, accent staccato, longitud; en los drums, más suave con roller o más fuerte) el paso entero de un drum adelantado o atrasado, el accent del random-mutate hasta +64, la velocity global para los sintes (vista Setup, K1 → amplitud, K2 → filtro, para los patches que no usan velocity) el bucle del sample capturado que sigue sonando al cambiar de proyecto o de pack, el **FM de 8 operadores** (envolventes del DX7, 56 algoritmos, 24 instrumentos; probado en el aparato), más voces FM, la fila de motores nueva, el **motor wavetable**, la página OSC 2 con ratio y detune, el latch en la vista Note con el paso que se escribe en turquesa, **la wavetable con escucha y tablas propias** (un ciclo de un sample o el cuadro de otra tabla en cada cuadro), **las páginas de los osciladores reordenadas**, LFO y envolvente → FM, ring y mix, **FM recíproco con centro**, **sync clásico**, menos ruido en FM, sync y bitwise, y que un knob sin carril tome uno libre al grabar; además, los programas del DSP van comprimidos en el firmware, lo que deja sitio para funciones futuras. RC4.08S es la misma RC sin escrituras propias en la SD. **Manuales en dos juegos, RC y beta:** [ghillermo.github.io/CIRCUIT-HACKS-RC](https://ghillermo.github.io/CIRCUIT-HACKS-RC/). **[Descarga el instalador](https://ghillermo.github.io/CIRCUIT-HACKS-RC/rc_uploader.zip)** (`rc_uploader.zip`), descomprímelo y abre `rc_uploader.html` en Chrome o Edge ([cómo](#instalar-sin-compilar-toolsrc_uploaderhtml)). Novedades de cada versión: [`docs/CHANGELOG.md`](docs/CHANGELOG.md) · lista de características: [`docs/CARACTERISTICAS.md`](docs/CARACTERISTICAS.md) · pistas MIDI y modos de voz: [https://ghillermo.github.io/CIRCUIT-HACKS-RC/voces.html](https://ghillermo.github.io/CIRCUIT-HACKS-RC/voces.html).

Nota legal: el firmware proporcionado por Novation es propietario, no está permitido instalarlo en cualquier dispositivo que no sea Circuit Tracks. Este instalador lo comprueba y no permite instalar en ningún otro dispositivo.

<!-- LANG-NOTICE -->
> **English:** the English version of this README is [further below](#english). Illustrated colour manual: [English](https://ghillermo.github.io/CIRCUIT-HACKS-RC/en.html) · [Español](https://ghillermo.github.io/CIRCUIT-HACKS-RC/index.html).

Parches de firmware para el **Novation Circuit Tracks** (firmware de referencia 1.2.1 build 4486).

**Solo para Circuit Tracks.** Para el **Circuit Rhythm** hay un proyecto aparte: [Circuit Remix](https://github.com/Ghillermo/CIRCUIT-REMIX).

**Chuleta de las pistas MIDI** (Beta 3.17), de u/macmax777 en Reddit: [synthmagazine.com/resources/circuithacks](https://synthmagazine.com/resources/circuithacks/).

Proyecto desarrollado usando Claude (Anthropic).

> ⚠️ **Antes de instalar: copia de seguridad de la tarjeta SD.**
> - Haz una copia completa de la SD (proyectos, packs y samples) antes de enviar cualquier versión del mod.
> - No trabajes con proyectos importantes guardados en el aparato mientras lo pruebas.
> - No se han reportado fallos, pero estas versiones están en prueba y podría haber problemas que dañen proyectos o samples guardados.
> - Si prefieres no arriesgar la tarjeta, usa la **versión más segura, [RC4.08S](firmware/r408s/PRUEBA.md)**: es RC4.08 sin ninguna función que cree, modifique o borre ficheros en la SD por su cuenta.
> - **[B5.28](firmware/b5.28/PRUEBA.md)** es una versión beta: RC4.08 + funciones nuevas aún sin probar en el aparato. Úsala solo con una copia de la SD.
> - El bootloader de Novation no se toca: **Scales + Preset + Note** al encender permite volver al firmware oficial.

## Repositorio público (rama RC, release candidate)

📖 [Manual ilustrado en color](https://ghillermo.github.io/CIRCUIT-HACKS-RC/index.html)

Este repositorio contiene **solo el trabajo propio del proyecto**:
- **Herramientas:** builders, ensambladores, emuladores, pruebas, el diagnóstico remoto y el cargador web.
- **Documentación:** manuales, notas técnicas y planes de prueba.
- **Manifiestos** de cada versión.

**No incluye:**
- **Código ni binarios de Novation:** ni el firmware oficial ni los `.syx` / `.bin` parcheados, que contienen el firmware de Novation.
- **Contenido de otros repositorios:** los volcados del aparato y el emulador del DSP se descargan de sus fuentes originales con `tools/setup_dev.py`.
- **Samples ni manuales de terceros.**

### Instalar sin compilar: `tools/rc_uploader.html`

📖 [Manual ilustrado en color](https://ghillermo.github.io/CIRCUIT-HACKS-RC/index.html)

1. **Descarga el firmware oficial** Circuit Tracks 1.2.1 (build 4486) de Novation: [circuittracks-firmware-4486.syx](https://components.novationmusic.com/api/v2/firmwares/168/file). Es el enlace de descarga de Novation Components; la lista completa está en `https://components.novationmusic.com/api/v2/firmwares`, producto `circuit-tracks`.
2. **[Descarga el instalador](https://ghillermo.github.io/CIRCUIT-HACKS-RC/rc_uploader.zip)** (`rc_uploader.zip`), descomprímelo y abre `rc_uploader.html` en Chrome o Edge (es el mismo [`tools/rc_uploader.html`](tools/rc_uploader.html) del repositorio).
3. **Elige el `.syx` oficial y la versión**: RC4.08, la versión más segura RC4.08S (o las anteriores), la beta B5.28, u «Oficial» para volver atrás. Las versiones anteriores (la RC anterior y su versión S, RC4.05, RC4.02, RC4, las RC2 y las betas hasta la 5.25) están en el **[instalador antiguo](https://ghillermo.github.io/CIRCUIT-HACKS-RC/rc_uploader_old.zip)** (`rc_uploader_old.zip`), que se usa igual.
   - La página parchea el firmware en el navegador.
   - Comprueba que el resultado es idéntico al publicado (SHA-256).
4. **Conecta el Circuit Tracks y pulsa Enviar.** Confirma con **Play** en el aparato.

La página no contiene código de Novation: solo los bytes del mod y las instrucciones para copiar el resto del firmware oficial que tú aportas. **Haz antes una copia de la tarjeta SD.**

### App de la tarjeta y del aparato: `tools/sd_app.html`

Una página para ordenar packs, sintes, samples, patrones y presets desde el ordenador, con la microSD o con el Circuit Tracks conectado por USB. Funciona también con el firmware oficial; los parches custom son lo único propio del mod.

1. **[Descarga la app](https://ghillermo.github.io/CIRCUIT-HACKS-RC/sd_app.zip)** (`sd_app.zip`), descomprímela y abre `sd_app.html` en Chrome o Edge (es el mismo [`tools/sd_app.html`](tools/sd_app.html) del repositorio). No necesita instalación ni servidor.
2. **Elige de dónde leer:**
   - **Abrir carpeta…**: la carpeta `Tracks` de la tarjeta o de una copia en el ordenador.
   - **Aparato…**: el Circuit Tracks por USB. Cierra Components y acepta el permiso de MIDI. El transporte se para y el panel queda bloqueado hasta **Desconectar aparato**.
3. **Trabaja con las dos columnas:** pestañas **Packs**, **Sintes Nova**, **Drums** (con escucha), **Parches custom**, **Patrones** y **Presets CC**. **Copiar** y **Mover** pasan lo elegido a la otra columna.
4. **Patrones** enseña las ocho pistas con su vista previa y, con el aparato conectado, su canal. Las pistas de notas se abren en piano roll con doble clic; los drums se ven, se copian y se exportan, pero aún no se editan.
5. **Exportar…** guarda lo elegido en el ordenador sin hacer un volcado completo: parches (`.syx` / `.ctm`), samples (`.wav`), patrones (`.mid` y `.ctpat`), presets (`.ctcc`) y packs enteros. Lo exportado todavía no se puede volver a cargar desde la app, salvo los `.ctcc`.
6. **Snapshot…** y **Restaurar…** (con el aparato conectado) guardan en el ordenador todos los packs, el pack interno y los presets de CC, y devuelven al aparato solo lo que haya cambiado, tras enseñarte un plan. El pack interno no se escribe de vuelta, y los packs que no estén en el snapshot se quedan. No incluye los ajustes del aparato ni lo que no hayas guardado del proyecto.

**Antes de escribir:** la app guarda lo que sustituye en una carpeta tuya del ordenador, nunca en la tarjeta: el aparato busca los ficheros por su prefijo `NN_` y una copia dentro de un pack puede ocupar el lugar del original. Por USB, cada escritura borra primero el fichero antiguo. **La escritura por USB ya está probada en un aparato real, pero puede haber fallos aún sin descubrir:** haz antes un snapshot o una copia de la tarjeta. Al escribir en el pack cargado, se recarga al desconectar y se pierde lo no guardado.

### App Hacks + Remix: `tools/hr_app.html`

Para pasar samples, patrones y parches FM entre un Circuit Tracks (Hacks) y un Circuit Rhythm ([Remix](https://github.com/Ghillermo/CIRCUIT-REMIX)), o guardarlos en carpetas del ordenador y snapshots. **[Descarga la app](https://ghillermo.github.io/CIRCUIT-HACKS-RC/hr_app.zip)** (`hr_app.zip`), descomprímela y abre `hr_app.html` en Chrome o Edge.

- **Dos columnas:** cada una abre una tarjeta del Tracks (carpeta con `Tracks/`), una del Rhythm (`Rhythm/`), un snapshot o una carpeta de ficheros sueltos.
- **Samples:** el WAV tal cual. **Patrones:** del Tracks al Rhythm, cada paso con la nota más grave del acorde; del Rhythm al Tracks, una nota por paso; los drums con golpes, velocity, probabilidad y micropasos. Los carriles de automatización y los sample flips no pasan de un aparato a otro. **Parches FM:** el FM de 8 operadores, el mismo en los dos.
- Sin probar aún con tarjetas reales: haz antes una copia.

### Con Python (`tools/patch_official.py`)

📖 [Manual ilustrado en color](https://ghillermo.github.io/CIRCUIT-HACKS-RC/index.html)

1. Consigue el firmware oficial **Circuit Tracks 1.2.1 (build 4486)** desde Novation Components, en `.syx`.
2. `python -m pip install -r tools/requirements.txt`
3. `python tools/patch_official.py RUTA/AL/OFICIAL.syx --version R408`. Para la versión más segura, sin escrituras propias en la SD, usa `--version R408S`. La beta: `--version B5.28`.
4. Envía `firmware/r408/circuittracks-4486-R408.syx` con `tools/ct_uploader.html` (Chrome / Edge).

La herramienta comprueba que el firmware oficial es el correcto y que el resultado es idéntico, bit a bit, al publicado (SHA-256 de `firmware/<versión>/manifest.json`). Para seguir desarrollando: [`docs/LOCAL.md`](docs/LOCAL.md).

Circuit Tracks, Components y Novation son marcas de Focusrite Audio Engineering Ltd. Este proyecto no está afiliado a ellos.

- [`LEEME.md`](LEEME.md) — base de trabajo, formato de actualización y reglas de seguridad.
- [`docs/NOTAS.md`](docs/NOTAS.md) — mapa técnico, modelo de seguridad del bootloader y estado de cada parche. **Última versión: RC4.08**; **más segura: RC4.08S** (sin escrituras propias en la SD); **beta: B5.28** (funciones nuevas sin probar). Las anteriores quedan como reserva (ver el historial).
- [`docs/RECURSOS.md`](docs/RECURSOS.md) — límites de recursos (flash, RAM, almacenamiento, programa / datos / CPU de los dos núcleos del DSP, memoria externa): lo libre en el original, lo usado y cómo se ha optimizado.
- `firmware/<parche>/` — `manifest.json` y `PRUEBA.md` (plan de prueba en el aparato); el `.syx` se genera con `tools/patch_official.py`.
- `tools/` — `ct_fw.py`, builders, emuladores (Unicorn/Capstone) y `ct_uploader.html` (Web MIDI).
- [`docs/LOCAL.md`](docs/LOCAL.md) — cómo clonar y trabajar en local (dependencias, `dsptool`, volcados, pruebas). [`CLAUDE.md`](CLAUDE.md) — contexto para Claude Code.

## Compilar

📖 [Manual ilustrado en color](https://ghillermo.github.io/CIRCUIT-HACKS-RC/index.html)

**Solo el firmware** (Python 3.10+; no hace falta compilar nada):
```bash
python -m pip install -r tools/requirements.txt
python tools/patch_official.py RUTA/AL/FIRMWARE_OFICIAL.syx --version R408
```
- El firmware oficial es el **Circuit Tracks 1.2.1 (build 4486)** de Novation Components, en `.syx` o `.bin`; la herramienta comprueba su SHA-256.
- Construye la versión en `firmware/<versión>/` y comprueba que el `.syx` es idéntico al publicado.
- `--version R408S` = la versión más segura; `--version B5.28` = la beta; `--list` enseña todas; `--all` las construye todas.
- Envía el `.syx` con `tools/ct_uploader.html` (Chrome / Edge). **Haz antes una copia de la SD.**

**Desarrollo y pruebas** (emuladores del ARM y del DSP; los volcados y el emulador del DSP se descargan aparte):
```bash
python tools/setup_dev.py          # dependencias desde sus fuentes originales: PyPI, firmware oficial, volcados, dsp56300, dsptool, re/app.asm
python tools/verify_builds.py      # todas las versiones idénticas a sus manifiestos
bash tools/run_tests.sh            # pruebas en emulación
```
Windows sin WSL, flujo de un parche nuevo y detalles: [`docs/LOCAL.md`](docs/LOCAL.md). Dependencias, fuentes y licencias: [`docs/DEPENDENCIAS.md`](docs/DEPENDENCIAS.md). Manuales: [`docs/MANUAL.md`](docs/MANUAL.md) y [manual ilustrado en color](https://ghillermo.github.io/CIRCUIT-HACKS-RC/index.html).

<!-- FEATURES:BEGIN -->
## Características (RC4)

La **lista de características** está en [`docs/CARACTERISTICAS.md`](docs/CARACTERISTICAS.md) (ilustrada en color: [index.html](https://ghillermo.github.io/CIRCUIT-HACKS-RC/index.html)). Manual de uso: [guía por vistas](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html) ([`docs/GUIA.md`](docs/GUIA.md)) · [referencia MIDI](docs/MIDI.md) · [guía en palabras sencillas](https://ghillermo.github.io/CIRCUIT-HACKS-RC/sencilla.html). Novedades y arreglos de cada versión: [`docs/CHANGELOG.md`](docs/CHANGELOG.md).
<!-- FEATURES:END -->

## Licencia

[MIT](LICENSE) © 2026 Ghillermo, para el trabajo propio del proyecto (herramientas, parches, documentación y manuales). No cubre el firmware de Novation (no se incluye; se obtiene de Novation con sus condiciones, igual que las imágenes construidas a partir de él) ni las dependencias de terceros, que conservan sus licencias ([`docs/DEPENDENCIAS.md`](docs/DEPENDENCIAS.md)): los parches de `tools/dsptool/` se aplican a dsp56300 (GPL-3.0) y un `dsptool` enlazado con él es GPL-3.0.

---

<a id="english"></a>
# CIRCUIT-HACKS (English)

> 📢 **RC4.08 and Beta 5.28.** RC4.08 = RC4 (everything from the betas up to 3.43: polyphony and voice modes for the own synth, FM, Jankó, the chord screen, stereo granular…) + fixes: the drums' chromatic pads record hit and pitch on their step, Digitise's envelope, the Velocity view's marked step, which goes back to the project's values, the Nudge, which moves the content of the range, three LFO shapes that silenced the own engine, the arpeggio on a muted track, notes shared by two chords, the count-in with an external clock, the Sidechain LEDs and, as an option (Advanced Setup, pad 22), saving the project while it plays by waiting until you stop; **RC4.08** fixes the own synth's pulse antialiasing at widths other than 50 %. **Beta 5.28** (the betas that extend RC4 are numbered 5.x) adds, mostly untested on the device, the drums' automation view, one more automation lane per drum with state locks and ramps, the Record + step snapshot on every track, Shift + Preset = the project's sound, the random-mutate redesigned on notes and drums, a sweep between two automation steps, the jump sequencer of MIDI 1 / 2, Jankó redesigned, the flash of each note with Shift, filter → VCA → effect as the default order, slower type knobs, the inverse chord, solo and solo flip in the Mixer (pad 16), the random-mutate's dynamics redone (ghost, accent staccato, length; on the drums, softer with a roller or louder) a drum's whole step moved earlier or later, the random-mutate's accent up to +64, global velocity for the synths (Setup view, K1 → amplitude, K2 → filter, for patches that don't use velocity) the captured sample's loop that keeps playing across a project or pack change, the **8-operator FM** (DX7 envelopes, 56 algorithms, 24 instruments; tested on the device), more FM voices, the new engine row, the **wavetable engine**, the OSC 2 page with ratio and detune, the Note view's latch with the step being written in teal, **the wavetable with audition and your own tables** (a sample's cycle or another table's frame in each frame), **the oscillator pages re-laid out**, LFO and envelope → FM, ring and mix, **cross FM with a centre**, **classic sync**, less noise in FM, sync and bitwise, and a knob without a lane taking a free one while recording; the DSP programs are also stored compressed in the firmware, which leaves room for future features. RC4.08S is the same RC without the mod's own writes to the SD card. **Manuals in two sets, RC and beta:** [ghillermo.github.io/CIRCUIT-HACKS-RC](https://ghillermo.github.io/CIRCUIT-HACKS-RC/). **[Download the installer](https://ghillermo.github.io/CIRCUIT-HACKS-RC/rc_uploader.zip)** (`rc_uploader.zip`), unzip it and open `rc_uploader.html` in Chrome or Edge ([how](#install-without-building-toolsrc_uploaderhtml)). What's new in every version: [`docs/CHANGELOG.md`](docs/CHANGELOG.md#changelog) · feature list: [`docs/FEATURES.md`](docs/FEATURES.md) · MIDI tracks and voice modes: [https://ghillermo.github.io/CIRCUIT-HACKS-RC/voices.html](https://ghillermo.github.io/CIRCUIT-HACKS-RC/voices.html).

📖 [Illustrated colour manual](https://ghillermo.github.io/CIRCUIT-HACKS-RC/en.html)

Firmware patches for the **Novation Circuit Tracks** (reference firmware 1.2.1 build 4486). The project was developed using Claude (Anthropic).

**For Circuit Tracks only.** A project for the **Circuit Rhythm** is available: [Circuit Remix](https://github.com/Ghillermo/CIRCUIT-REMIX).

**MIDI tracks cheat sheet** (Beta 3.17) by u/macmax777 on Reddit: [synthmagazine.com/resources/circuithacks](https://synthmagazine.com/resources/circuithacks/).

Legal Notice: Code sourced by Novation is propietary. Don't install it on a device other than Circuit Tracks. This installer checos for a Circuit Tracks specifically, and won't allow you to use it on any other device.

> ⚠️ **Before installing: back up your SD card.**
> - Make a full copy of the SD card (projects, packs and samples) before sending any version of the mod.
> - Do not work on important projects stored on the device while you test it.
> - No failures have been reported, but these versions are being tested and there could be problems that damage saved projects or samples.
> - If you would rather not risk the card, use the **safer build, [RC4.08S](firmware/r408s/PRUEBA.md)**: RC4.08 without any feature that creates, changes or deletes files on the SD card on its own.
> - **[B5.28](firmware/b5.28/PRUEBA.md)** is a beta: RC4.08 + new features not yet tested on the device. Use it only with a backup of the SD card.
> - Novation’s bootloader is never touched: **Scales + Preset + Note** at power-on lets you go back to the official firmware.

**Manual:** [short](docs/MANUAL.en.md) · [illustrated](https://ghillermo.github.io/CIRCUIT-HACKS-RC/en.html). Public repository: <https://github.com/Ghillermo/CIRCUIT-HACKS-RC>.

### What the public repository contains

📖 [Illustrated colour manual](https://ghillermo.github.io/CIRCUIT-HACKS-RC/en.html)

- **Tools:** builders, assemblers, emulators, tests, remote diagnostics and the web uploaders.
- **Documentation:** manuals (Spanish and English), technical notes and test plans (Spanish).
- **Manifests** of every version.

It does **not** include Novation code or binaries (neither the official firmware nor patched `.syx` / `.bin` files, which contain Novation’s firmware), content of other repositories (the device dumps and the DSP emulator are downloaded from their original sources by `tools/setup_dev.py`), samples or third-party manuals.

### Install without building: `tools/rc_uploader.html`

📖 [Illustrated colour manual](https://ghillermo.github.io/CIRCUIT-HACKS-RC/en.html)

1. **Download the official firmware** Circuit Tracks 1.2.1 (build 4486) from Novation: [circuittracks-firmware-4486.syx](https://components.novationmusic.com/api/v2/firmwares/168/file). It is the Novation Components download link; the full list is at `https://components.novationmusic.com/api/v2/firmwares`, product `circuit-tracks`.
2. **[Download the installer](https://ghillermo.github.io/CIRCUIT-HACKS-RC/rc_uploader.zip)** (`rc_uploader.zip`), unzip it and open `rc_uploader.html` in Chrome or Edge (it is the repository's [`tools/rc_uploader.html`](tools/rc_uploader.html)).
3. **Pick the official `.syx` and the version**: RC4.08, the safer RC4.08S (or the earlier ones), the beta B5.28, or “Official” to go back. The earlier versions (the previous RC and its S build, RC4.05, RC4.02, RC4, the RC2s and the betas up to 5.25) are in the **[old installer](https://ghillermo.github.io/CIRCUIT-HACKS-RC/rc_uploader_old.zip)** (`rc_uploader_old.zip`), used the same way.
   - The page patches the firmware in the browser.
   - It checks that the result is identical to the published one (SHA-256).
4. **Connect the Circuit Tracks and press Send.** Confirm with **Play** on the device.

The page contains no Novation code: only the bytes of the mod and the instructions to copy the rest from the official firmware you provide. **Back up the SD card first.**

### Card and device app: `tools/sd_app.html`

A page to organise packs, synths, samples, patterns and presets from the computer, with the microSD card or with the Circuit Tracks connected by USB. It also works with the official firmware; only the custom patches belong to the mod.

1. **[Download the app](https://ghillermo.github.io/CIRCUIT-HACKS-RC/sd_app.zip)** (`sd_app.zip`), unzip it and open `sd_app.html` in Chrome or Edge (it is the repository's [`tools/sd_app.html`](tools/sd_app.html)). It needs no installation and no server.
2. **Choose where to read from:**
   - **Open folder…**: the `Tracks` folder of the card or of a copy on the computer.
   - **Device…**: the Circuit Tracks over USB. Close Components and accept the MIDI permission. The transport stops and the panel stays locked until **Disconnect device**.
3. **Work with the two columns:** the tabs **Packs**, **Nova synths**, **Drums** (with listening), **Custom patches**, **Patterns** and **CC presets**. **Copy** and **Move** send the selection to the other column.
4. **Patterns** shows the eight tracks with their preview and, with the device connected, their channel. Note tracks open in a piano roll with a double click; drums can be seen, copied and exported, but not edited yet.
5. **Export…** saves the selection on the computer without a full dump: patches (`.syx` / `.ctm`), samples (`.wav`), patterns (`.mid` and `.ctpat`), presets (`.ctcc`) and whole packs. Exported files cannot be loaded back from the app yet, except `.ctcc`.
6. **Snapshot…** and **Restore…** (with the device connected) save all the packs, the internal pack and the CC presets on the computer, and send back only what has changed, after showing you a plan. The internal pack is not written back, and packs that are not in the snapshot stay. The device's settings and anything unsaved in the project are not included.

**Before writing:** the app keeps what it replaces in a folder of yours on the computer, never on the card: the device finds files by their `NN_` prefix and a copy inside a pack can take the original's place. Over USB, each write deletes the old file first. **Writing over USB has been tested on a real device, but there may be bugs still undiscovered:** take a snapshot or a copy of the card first. Writing to the loaded pack makes it reload on disconnect, and unsaved edits are lost.

### Hacks + Remix app: `tools/hr_app.html`

To move samples, patterns and FM patches between a Circuit Tracks (Hacks) and a Circuit Rhythm ([Remix](https://github.com/Ghillermo/CIRCUIT-REMIX)), or keep them in folders on the computer and in snapshots. **[Download the app](https://ghillermo.github.io/CIRCUIT-HACKS-RC/hr_app.zip)** (`hr_app.zip`), unzip it and open `hr_app.html` in Chrome or Edge.

- **Two columns:** each opens a Tracks card (a folder with `Tracks/`), a Rhythm card (`Rhythm/`), a snapshot or a folder of loose files.
- **Samples:** the WAV as it is. **Patterns:** Tracks to Rhythm, each step takes the chord's lowest note; Rhythm to Tracks, one note a step; drums with hits, velocity, probability and micro steps. Automation lanes and sample flips do not cross from one device to the other. **FM patches:** the 8-operator FM, the same on both.
- Not yet tested with real cards: make a backup first.

### Build

📖 [Illustrated colour manual](https://ghillermo.github.io/CIRCUIT-HACKS-RC/en.html)

**Firmware only** (Python 3.10+; nothing to compile):
```bash
python -m pip install -r tools/requirements.txt
python tools/patch_official.py PATH/TO/OFFICIAL_FIRMWARE.syx --version R408
```
- The official firmware is the **Circuit Tracks 1.2.1 (build 4486)** from Novation Components, as `.syx` or `.bin`; the tool checks its SHA-256.
- It builds the version into `firmware/<version>/` and checks that the `.syx` is identical to the published one.
- `--version R408S` = the safer build; `--version B5.28` = the beta; `--list` shows them all; `--all` builds them all.
- Send the `.syx` with `tools/ct_uploader.html` (Chrome / Edge). **Back up the SD card first.**

**Development and tests** (ARM and DSP emulators; the dumps and the DSP emulator are downloaded separately):
```bash
python tools/setup_dev.py          # dependencies from their original sources: PyPI, official firmware, dumps, dsp56300, dsptool, re/app.asm
python tools/verify_builds.py      # every version identical to its manifest
bash tools/run_tests.sh            # emulation tests
```
Windows without WSL, the workflow of a new patch and details: [`docs/LOCAL.en.md`](docs/LOCAL.en.md). Dependencies, sources and licences: [`docs/DEPENDENCIAS.md`](docs/DEPENDENCIAS.md).

### Files

📖 [Illustrated colour manual](https://ghillermo.github.io/CIRCUIT-HACKS-RC/en.html)

- [`LEEME.md`](LEEME.md) — update format and bootloader safety (Spanish and English).
- [`docs/NOTAS.md`](docs/NOTAS.md) — technical map, bootloader safety model and status of every patch (Spanish). **Latest version: RC4.08**; **safer: RC4.08S**; **beta: B5.28** (new features not yet tested).
- [`docs/RECURSOS.md`](docs/RECURSOS.md#resources) — resource limits (flash, RAM, storage, program / data / CPU of both DSP cores, external memory): what the original left free, what is used and how it was optimised.
- `firmware/<version>/` — `manifest.json` and `PRUEBA.md` (test plan on the device, Spanish).
- `tools/` — `ct_fw.py`, builders, emulators (Unicorn / Capstone), `ct_uploader.html` and `rc_uploader.html` (Web MIDI).
- [`CLAUDE.md`](CLAUDE.md) — context for Claude Code (Spanish).

<!-- FEATURES-EN:BEGIN -->
## Features (RC4)

The **feature list** is in [`docs/FEATURES.md`](docs/FEATURES.md) (illustrated in colour: [en.html](https://ghillermo.github.io/CIRCUIT-HACKS-RC/en.html)). User manual: [guide by views](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guide.html) ([`docs/GUIA.en.md`](docs/GUIA.en.md)) · [MIDI reference](docs/MIDI.en.md) · [guide in plain words](https://ghillermo.github.io/CIRCUIT-HACKS-RC/plain.html). New features and fixes of every version: [`docs/CHANGELOG.md`](docs/CHANGELOG.md#changelog).
<!-- FEATURES-EN:END -->

### License

[MIT](LICENSE) © 2026 Ghillermo, for the project's own work (tools, patches, documentation and manuals). It does not cover Novation's firmware (not included; you get it from Novation under its terms, as are the images built from it) nor third-party dependencies, which keep their licences ([`docs/DEPENDENCIAS.md`](docs/DEPENDENCIAS.md)): the patches in `tools/dsptool/` apply to dsp56300 (GPL-3.0) and a `dsptool` linked against it is GPL-3.0.

Circuit Tracks, Components and Novation are trademarks of Focusrite Audio Engineering Ltd. This project is not affiliated with them.
