# CIRCUIT-HACKS

Help me pay for tools and mantain this project and CIRCUIT REMIX: https://PayPal.me/ghillermo

Contributors:

Aleš Janda: https://alesjanda.cz, https://github.com/kybl 

No_Grand_9136: https://Reddit.com/user/No_Grand_9136

If you want your name or website in this list, add it on your message when you send your contribution or send me a DM.


> 📢 **RC4.02 y la Beta 5.0.** RC4.02 = RC4 (todo lo de las betas hasta la 3.43: polifonía y modos de voz del sinte propio, FM, Jankó, pantalla de acordes, granular en estéreo…) + arreglos: los pads cromáticos de los drums graban golpe y tono en su paso, guardar el proyecto mientras suena espera a que pares (sin descompasar el reloj), la envolvente de Digitise y el paso marcado de la vista Velocity, que vuelve a los valores del proyecto. La **Beta 5.0** (las betas que amplían RC4 se numeran 5.x) añade, sin probar en el aparato, la vista de automatización de los drums, un carril de automatización más por drum con bloqueos de estado y rampas, la foto de Record + paso en todas las pistas y Shift + Preset = el sonido del proyecto. RC4.02S es la misma RC sin escrituras propias en la SD. **[Descarga el instalador](https://ghillermo.github.io/CIRCUIT-HACKS-RC/rc_uploader.zip)** (`rc_uploader.zip`), descomprímelo y abre `rc_uploader.html` en Chrome o Edge ([cómo](#instalar-sin-compilar-toolsrc_uploaderhtml)). Novedades de cada versión: [`docs/CHANGELOG.md`](docs/CHANGELOG.md) · lista de características: [`docs/CARACTERISTICAS.md`](docs/CARACTERISTICAS.md).

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
> - Si prefieres no arriesgar la tarjeta, usa la **versión más segura, [RC4.02S](firmware/r402s/PRUEBA.md)**: es RC4.02 sin ninguna función que cree, modifique o borre ficheros en la SD por su cuenta.
> - **[B5.0](firmware/b5.0/PRUEBA.md)** es una versión beta: RC4.02 + funciones nuevas aún sin probar en el aparato. Úsala solo con una copia de la SD.
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
3. **Elige el `.syx` oficial y la versión**: RC4.02, la versión más segura RC4.02S, la beta B5.0 (o las anteriores), u «Oficial» para volver atrás.
   - La página parchea el firmware en el navegador.
   - Comprueba que el resultado es idéntico al publicado (SHA-256).
4. **Conecta el Circuit Tracks y pulsa Enviar.** Confirma con **Play** en el aparato.

La página no contiene código de Novation: solo los bytes del mod y las instrucciones para copiar el resto del firmware oficial que tú aportas. **Haz antes una copia de la tarjeta SD.**

### Con Python (`tools/patch_official.py`)

📖 [Manual ilustrado en color](https://ghillermo.github.io/CIRCUIT-HACKS-RC/index.html)

1. Consigue el firmware oficial **Circuit Tracks 1.2.1 (build 4486)** desde Novation Components, en `.syx`.
2. `python -m pip install -r tools/requirements.txt`
3. `python tools/patch_official.py RUTA/AL/OFICIAL.syx --version R402`. Para la versión más segura, sin escrituras propias en la SD, usa `--version R402S`. La beta: `--version B5.0`.
4. Envía `firmware/r402/circuittracks-4486-R402.syx` con `tools/ct_uploader.html` (Chrome / Edge).

La herramienta comprueba que el firmware oficial es el correcto y que el resultado es idéntico, bit a bit, al publicado (SHA-256 de `firmware/<versión>/manifest.json`). Para seguir desarrollando: [`docs/LOCAL.md`](docs/LOCAL.md).

Circuit Tracks, Components y Novation son marcas de Focusrite Audio Engineering Ltd. Este proyecto no está afiliado a ellos.

- [`LEEME.md`](LEEME.md) — base de trabajo, formato de actualización y reglas de seguridad.
- [`docs/NOTAS.md`](docs/NOTAS.md) — mapa técnico, modelo de seguridad del bootloader y estado de cada parche. **Última versión: RC4.02**; **más segura: RC4.02S** (sin escrituras propias en la SD); **beta: B5.0** (funciones nuevas sin probar). Las anteriores quedan como reserva (ver el historial).
- [`docs/RECURSOS.md`](docs/RECURSOS.md) — límites de recursos (flash, RAM, almacenamiento, programa / datos / CPU de los dos núcleos del DSP, memoria externa): lo libre en el original, lo usado y cómo se ha optimizado.
- `firmware/<parche>/` — `manifest.json` y `PRUEBA.md` (plan de prueba en el aparato); el `.syx` se genera con `tools/patch_official.py`.
- `tools/` — `ct_fw.py`, builders, emuladores (Unicorn/Capstone) y `ct_uploader.html` (Web MIDI).
- [`docs/LOCAL.md`](docs/LOCAL.md) — cómo clonar y trabajar en local (dependencias, `dsptool`, volcados, pruebas). [`CLAUDE.md`](CLAUDE.md) — contexto para Claude Code.

## Compilar

📖 [Manual ilustrado en color](https://ghillermo.github.io/CIRCUIT-HACKS-RC/index.html)

**Solo el firmware** (Python 3.10+; no hace falta compilar nada):
```bash
python -m pip install -r tools/requirements.txt
python tools/patch_official.py RUTA/AL/FIRMWARE_OFICIAL.syx --version R402
```
- El firmware oficial es el **Circuit Tracks 1.2.1 (build 4486)** de Novation Components, en `.syx` o `.bin`; la herramienta comprueba su SHA-256.
- Construye la versión en `firmware/<versión>/` y comprueba que el `.syx` es idéntico al publicado.
- `--version R402S` = la versión más segura; `--version B5.0` = la beta; `--list` enseña todas; `--all` las construye todas.
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

> 📢 **RC4.02 and Beta 5.0.** RC4.02 = RC4 (everything from the betas up to 3.43: polyphony and voice modes for the own synth, FM, Jankó, the chord screen, stereo granular…) + fixes: the drums' chromatic pads record hit and pitch on their step, saving the project while it plays waits until you stop (the clock no longer stumbles), Digitise's envelope, and the Velocity view's marked step, which goes back to the project's values. **Beta 5.0** (the betas that extend RC4 are numbered 5.x) adds, untested on the device, the drums' automation view, one more automation lane per drum with state locks and ramps, the Record + step snapshot on every track and Shift + Preset = the project's sound. RC4.02S is the same RC without the mod's own writes to the SD card. **[Download the installer](https://ghillermo.github.io/CIRCUIT-HACKS-RC/rc_uploader.zip)** (`rc_uploader.zip`), unzip it and open `rc_uploader.html` in Chrome or Edge ([how](#install-without-building-toolsrc_uploaderhtml)). What's new in every version: [`docs/CHANGELOG.md`](docs/CHANGELOG.md#changelog) · feature list: [`docs/FEATURES.md`](docs/FEATURES.md).

📖 [Illustrated colour manual](https://ghillermo.github.io/CIRCUIT-HACKS-RC/en.html)

Firmware patches for the **Novation Circuit Tracks** (reference firmware 1.2.1 build 4486). The project was developed using Claude (Anthropic).

**For Circuit Tracks only.** A project for the **Circuit Rhythm** is available: [Circuit Remix](https://github.com/Ghillermo/CIRCUIT-REMIX).

**MIDI tracks cheat sheet** (Beta 3.17) by u/macmax777 on Reddit: [synthmagazine.com/resources/circuithacks](https://synthmagazine.com/resources/circuithacks/).

Legal Notice: Code sourced by Novation is propietary. Don't install it on a device other than Circuit Tracks. This installer checos for a Circuit Tracks specifically, and won't allow you to use it on any other device.

> ⚠️ **Before installing: back up your SD card.**
> - Make a full copy of the SD card (projects, packs and samples) before sending any version of the mod.
> - Do not work on important projects stored on the device while you test it.
> - No failures have been reported, but these versions are being tested and there could be problems that damage saved projects or samples.
> - If you would rather not risk the card, use the **safer build, [RC4.02S](firmware/r402s/PRUEBA.md)**: RC4.02 without any feature that creates, changes or deletes files on the SD card on its own.
> - **[B5.0](firmware/b5.0/PRUEBA.md)** is a beta: RC4.02 + new features not yet tested on the device. Use it only with a backup of the SD card.
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
3. **Pick the official `.syx` and the version**: RC4.02, the safer RC4.02S, the beta B5.0 (or the earlier ones), or “Official” to go back.
   - The page patches the firmware in the browser.
   - It checks that the result is identical to the published one (SHA-256).
4. **Connect the Circuit Tracks and press Send.** Confirm with **Play** on the device.

The page contains no Novation code: only the bytes of the mod and the instructions to copy the rest from the official firmware you provide. **Back up the SD card first.**

### Build

📖 [Illustrated colour manual](https://ghillermo.github.io/CIRCUIT-HACKS-RC/en.html)

**Firmware only** (Python 3.10+; nothing to compile):
```bash
python -m pip install -r tools/requirements.txt
python tools/patch_official.py PATH/TO/OFFICIAL_FIRMWARE.syx --version R402
```
- The official firmware is the **Circuit Tracks 1.2.1 (build 4486)** from Novation Components, as `.syx` or `.bin`; the tool checks its SHA-256.
- It builds the version into `firmware/<version>/` and checks that the `.syx` is identical to the published one.
- `--version R402S` = the safer build; `--version B5.0` = the beta; `--list` shows them all; `--all` builds them all.
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
- [`docs/NOTAS.md`](docs/NOTAS.md) — technical map, bootloader safety model and status of every patch (Spanish). **Latest version: RC4.02**; **safer: RC4.02S**; **beta: B5.0** (new features not yet tested).
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
