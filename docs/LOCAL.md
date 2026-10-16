# Trabajar en local

Guía para clonar el repositorio y seguir desarrollando, probando y enviando firmwares desde tu ordenador. English version: [`LOCAL.en.md`](LOCAL.en.md).

## 0. Solo quiero el firmware (rama RC)
**Lo más sencillo:** abre `tools/rc_uploader.html` en Chrome / Edge, elige el firmware oficial ([descarga de Novation](https://components.novationmusic.com/api/v2/firmwares/168/file)) y la versión, y envía: parchea en el navegador sin instalar nada. Lo genera `tools/make_rc_uploader.py` (en una copia completa, con los `.bin`).

Con Python:
La rama **RC** no incluye código ni binarios de Novation. Para obtener un `.syx` necesitas el firmware oficial **Circuit Tracks 1.2.1 (build 4486)**, el que sirve Components, en `.syx` o en `.bin`:

```bash
python -m pip install -r tools/requirements.txt
python tools/patch_official.py RUTA/AL/FIRMWARE_OFICIAL.syx --version RC0.9
```

- Comprueba que el fichero es el oficial (SHA-256 de `stock/SHA256SUMS.txt`) y lo guarda en `stock/`.
- Genera `re/app.asm` y construye la versión.
- Comprueba que el resultado tiene el SHA-256 publicado en `firmware/<versión>/manifest.json`.
- `--list` enseña las versiones; `--all` las construye todas.
- No hace falta compilar nada: el ensamblado del DSP sale de la caché `tools/dsp_asm_cache.json`.
- Envía el `.syx` con `tools/ct_uploader.html`.

**Haz una copia de la tarjeta SD antes de instalar.** Si no quieres que el mod escriba nada en la SD por su cuenta, usa `--version RC0.9S`. La beta (funciones nuevas sin probar): `--version B1.23`.

## 1. Requisitos
| Para | Necesitas |
|---|---|
| Enviar un `.syx` al aparato | Solo Chrome o Edge y `tools/ct_uploader.html`, en cualquier sistema |
| Construir y probar | Linux, macOS o **WSL2** en Windows, con Python 3.10+, git, cmake ≥ 3.20, un compilador C++17 (g++ o clang) y ~1 GB libre |

En Windows: haz todo lo de construir y probar dentro de WSL2 (Ubuntu). El cargador se abre en el Chrome de Windows (`\\wsl$\Ubuntu\home\<tú>\CIRCUIT-HACKS\tools\ct_uploader.html`, o copia el archivo).

### Windows sin WSL2 (virtualización desactivada en la BIOS)
Con WinLibs instalado (paso 1), `python tools/setup_dev.py` hace los pasos 2-6 solo. Detalle de lo que hace:
Probado en Windows 10 con Git Bash y Python 3.14; los 24 builds salen idénticos y las pruebas pasan.
1. `winget install BrechtSanders.WinLibs.POSIX.UCRT` (g++, cmake y ninja; descomprimir tarda ~30 min). Pon su carpeta `mingw64in` en el PATH de la sesión de Git Bash.
2. `python -m pip install -r tools/requirements.txt`.
3. Clona `ext/circuittracksreverseengineering` y `ext/dsp56300` como en `setup_local.sh`. El parche memtrace se aplica con `git apply --ignore-whitespace` (el árbol de trabajo tiene finales de línea CRLF).
4. Dos arreglos locales en `ext/dsp56300` (no se versionan):
   - `source/dsp56kBase/threadtools.cpp`: el bloque `__try … __except` dentro de `#ifdef _MSC_VER`;
   - `source/dsp56kBase/mmuhelper.cpp`: tipos de función propios para `VirtualAlloc2` / `MapViewOfFile3` / `UnmapViewOfFile2`, definir los `MEM_*_PLACEHOLDER` que faltan en MinGW y `isSupported()` = `false`.
5. `cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release` y `cmake --build build --target dsp56kEmu`. Luego `g++ -O2 -std=c++17 -static -Isource -Isource/asmjit/src ../../tools/dsptool/dsptool.cpp <las 4 libs> -lpthread -o ../bin/dsptool.exe`. Con `-static`, Python lo ejecuta sin tener MinGW en el PATH. `tools/dsptool_path.py` busca `ext/bin/dsptool.exe`; `dsptool.cpp` acepta `/dev/stdin` y escribe en binario también en Windows.
6. `python tools/gen_listing.py`; `ctre/` puede ser una copia de `ext/circuittracksreverseengineering` (en Git Bash `ln -s` copia).
7. Para `run_tests.sh` hace falta un `python3`: un script `~/bin/python3` con `exec python "$@"`.
8. Cada `Session` / `E` de las pruebas reserva memoria: los scripts nuevos llaman a `gc.collect()` antes de crear otra (si no, Windows se queda sin memoria).

## 2. Clonar e instalar
```bash
git clone https://github.com/Ghillermo/CIRCUITS-HACKS-RC.git
cd CIRCUITS-HACKS-RC
python tools/setup_dev.py                   # 10–20 min la primera vez (o: bash tools/setup_local.sh)
```
`setup_dev.py` descarga cada dependencia de su fuente original (lista, versiones y licencias en [`DEPENDENCIAS.md`](DEPENDENCIAS.md)) y crea `ext/`, `stock/` y `re/`, que git ignora. `--check` solo informa; `--no-dsptool` omite el emulador del DSP; `--official FICHERO` usa tu copia del firmware oficial en vez de descargarlo. En Windows sin WSL aplica también `tools/dsptool/dsp56300-mingw.patch` (los arreglos del paso 4 de abajo) y compila con MinGW:

| Qué | Dónde | Para qué |
|---|---|---|
| `capstone==5.0.7`, `unicorn==2.1.4` (pip) | entorno de Python | listado ARM y emulación del ARM |
| volcados de userx14, commit `d6aec9fc` | `ext/circuittracksreverseengineering` + enlace `ctre/` | RAM y flash del aparato en marcha (emuladores) |
| dsp56300, commit `44353be2`, + `tools/dsptool/dsp56kEmu-memtrace.patch` | `ext/dsp56300` | emulador del DSP56300 |
| `dsptool` | `ext/bin/dsptool` | ensamblar, desensamblar y ejecutar el DSP (lo encuentra `tools/dsptool_path.py`; otra ruta: variable `DSPTOOL`) |
| `re/app.asm` | `re/` (ignorado) | listado Thumb de stock; los builders comprueban instrucciones con él |

Si prefieres un entorno virtual: `python3 -m venv .venv && . .venv/bin/activate` antes del script.

## 3. Comprobar que todo está bien
```bash
bash tools/run_tests.sh          # ~10 min: los 24 builds idénticos a firmware/*/manifest.json + pruebas ARM de SC17.4
bash tools/run_tests.sh full     # + DSP exacto de Master FX, núcleo DSP completo y entrada de línea
```
Si `verify_builds.py` da `DIFF`, casi siempre es otra versión de Capstone (cambia el texto del desensamblado). Usa exactamente `capstone==5.0.7`.

## 4. Flujo de trabajo de un parche nuevo
1. **Builder:** `tools/build_scNN.py`. Lo habitual es importar el anterior, cambiar sus globales o envolver su `dsp_code` y llamar a su `build()`. Ejemplo: `build_sc17_4.py` = `use_mixer14()` + `use_full_leds()` + `linein2`.
2. **Construir:** `python3 tools/build_scNN.py stock/circuittracks-firmware-4486-STOCK.bin -o build/scNN` → `.bin`, `.syx` y `manifest.json` (sha, CRC, etiquetas, listado del código nuevo).
3. **Probar en emulación:**
   - ARM: Unicorn sobre el volcado de RAM en marcha. Modelo: `emu_sc17.py`.
   - DSP: `dsp_session.py`, el núcleo 0 completo en `dsptool`. Modelos: `emu_sc17_core.py`, `emu_masterfx_dsp.py`.
4. **Publicar:**
   - copia `build/scNN/*` a `firmware/scNN/` y escribe `PRUEBA.md` (qué cambia, uso, verificación, pruebas en el aparato y cómo volver atrás);
   - añade el SHA-256 del `.syx` a `KNOWN` en `tools/ct_uploader.html` (el cargador solo envía archivos de esa lista);
   - añade la fila de estado en `README.md` y la sección técnica en `docs/NOTAS.md`;
   - añade la entrada en `BUILDS` de `tools/verify_builds.py`.
5. **Enviar:** abre `tools/ct_uploader.html` en Chrome → Permitir MIDI → Identificar → elegir el `.syx` → Enviar → pulsar **Play** en el aparato cuando lo pida.
   - Recuperación: si no arranca, enciéndelo con **Scales + Preset + Note** (modo bootloader) y envía `stock/…-STOCK.syx` o el último que funcionaba.

## 5. Herramientas
| Archivo | Uso |
|---|---|
| `tools/ct_fw.py` | `.syx` ↔ `.bin`, CRC-32/MPEG-2 |
| `tools/thumb.py` | ensamblador Thumb-2 mínimo (`Asm`, etiquetas, `b_w`, `bl`, …) |
| `tools/dsp56.py` | ensamblador DSP56300 (texto → palabras vía `dsptool asm`, con caché) |
| `tools/gen_listing.py` | regenera `re/app.asm` |
| `tools/emu_sc05.py` → `emu_sc08.py` (`E8`, `MGR`) | base de los emuladores ARM (mapa de memoria, volcados, `call`, `set_p0`) |
| `tools/dsp_session.py` | núcleo 0 completo: init, tablas, parámetros, MIDI, N bloques; `WATCH`/`TRACE`/`HIST` |
| `tools/dsp_free_scan.py` | busca memoria X/Y del DSP sin usar |
| `tools/verify_builds.py` | reconstruye todo y compara con los manifiestos |
| `tools/shi_capture.py` | captura de escrituras ARM→DSP |
| `dsptool dis f.bin [base]` | desensamblador DSP; `dsptool dis` con líneas `op opB` por stdin |

## 6. Ideas clave antes de tocar nada
Lee `CLAUDE.md` (resumen) y `docs/NOTAS.md` (detalle). Lo esencial:
- Identifica vistas y botones por su comportamiento, nunca por el número. Ejemplo: SC17–SC17.2 engancharon el botón 13 creyendo que era Mixer, y Mixer es el 14.
- La RAM libre del ARM está bajo el tope del heap: hay 240 B en el aparato, SC14–SC17.5 usan 196 y SC17.6 usa 220 (margen ~20 B: no crecer más sin liberar algo).
- Memoria del DSP: usa solo X/Y:$3339–$3BFF (verificado). Nada en P:$00–$7F.
- Antes de enviar: el build pasa sus pruebas y los builds antiguos siguen idénticos.
