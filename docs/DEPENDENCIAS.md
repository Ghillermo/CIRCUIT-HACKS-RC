# Dependencias de desarrollo / Development dependencies

`python tools/setup_dev.py` descarga cada dependencia **de su fuente original**, en una versión fijada, a carpetas que git ignora (`ext/`, `stock/`, `re/`). Este repositorio no guarda ni redistribuye nada de terceros: solo nuestros parches para el emulador del DSP.

`python tools/setup_dev.py` downloads every dependency **from its original source**, at a pinned version, into folders git ignores (`ext/`, `stock/`, `re/`). This repository stores and redistributes nothing third-party: only our patches for the DSP emulator.

| Dependencia / Dependency | Fuente original / Original source | Versión / Version | Licencia / Licence | Para qué / What for | Dónde / Where |
|---|---|---|---|---|---|
| capstone | [PyPI](https://pypi.org/project/capstone/) · [capstone-engine/capstone](https://github.com/capstone-engine/capstone) | 5.0.7 (exacta: los builders comparan su texto / exact: the builders compare its text) | BSD-3-Clause | Desensamblado Thumb / Thumb disassembly | entorno de Python / Python environment |
| unicorn | [PyPI](https://pypi.org/project/unicorn/) · [unicorn-engine/unicorn](https://github.com/unicorn-engine/unicorn) | 2.1.4 | GPL-2.0 | Emulación del ARM / ARM emulation | entorno de Python / Python environment |
| Firmware oficial Circuit Tracks 1.2.1 (build 4486) / official firmware | [Novation Components](https://components.novationmusic.com/api/v2/firmwares/168/file) | SHA-256 en / in `stock/SHA256SUMS.txt` | © Novation / Focusrite: se descarga a tu equipo, no se redistribuye / downloaded to your machine, never redistributed | Base de todos los builds / base of every build | `stock/` |
| Volcados del aparato / device dumps | [userx14/circuittracksreverseengineering](https://github.com/userx14/circuittracksreverseengineering) | commit `d6aec9fc` | sin licencia declarada: se clona desde su repositorio, no se redistribuye / no licence declared: cloned from its repository, never redistributed | RAM y flash del aparato en marcha para los emuladores / running RAM and flash for the emulators | `ext/circuittracksreverseengineering`, enlace / link `ctre/` |
| dsp56300 (dsp56kEmu) + asmjit (submódulo / submodule) | [dsp56300/dsp56300](https://github.com/dsp56300/dsp56300) | commit `44353be2` | GPL-3.0 (asmjit: Zlib) | Emulador del DSP56300 / DSP56300 emulator | `ext/dsp56300` |
| dsptool | nuestro / ours: `tools/dsptool/dsptool.cpp`, enlazado con dsp56kEmu / linked against dsp56kEmu | — | el binario resultante sigue la GPL-3.0 de dsp56kEmu / the resulting binary follows dsp56kEmu’s GPL-3.0 | Ensamblar, desensamblar y ejecutar código del DSP / assemble, disassemble and run DSP code | `ext/bin/dsptool[.exe]` |
| `re/app.asm` | generado de tu copia del firmware oficial / generated from your copy of the official firmware (`tools/gen_listing.py`) | — | contiene código de Novation: no se publica / contains Novation code: never published | Comprobaciones de los builders / builder checks | `re/` |

**Nuestros parches para dsp56300 / our patches for dsp56300** (`tools/dsptool/`, GPL-3.0 como el proyecto al que se aplican / like the project they apply to):
- `dsp56kEmu-memtrace.patch`: trazas de acceso a memoria para las pruebas / memory-access traces for the tests.
- `dsp56300-mingw.patch` (solo Windows sin WSL / Windows without WSL only): compila con MinGW-w64 / builds with MinGW-w64.

**Herramientas del sistema / system tools:** Python 3.10+, git, cmake ≥ 3.20, un compilador C++17 / a C++17 compiler (g++ o / or clang++; Windows: [WinLibs](https://winlibs.com/) `winget install BrechtSanders.WinLibs.POSIX.UCRT`), opcional / optional ninja.

```bash
python tools/setup_dev.py --check        # qué hay y qué falta / what is there and what is missing
python tools/setup_dev.py                # todo / everything
python tools/setup_dev.py --no-dsptool   # sin el emulador del DSP (los builds no lo necesitan) / without the DSP emulator (builds do not need it)
python tools/setup_dev.py --official RUTA/PATH.syx   # tu copia del firmware oficial / your copy of the official firmware
```

Para **solo construir el firmware** no hace falta nada de esto: `tools/patch_official.py` (o `tools/rc_uploader.html` en el navegador) con capstone 5.0.7 basta. / To **only build the firmware** none of this is needed: `tools/patch_official.py` (or `tools/rc_uploader.html` in the browser) with capstone 5.0.7 is enough.

**Contexto de Claude / Claude context:** `CLAUDE.md` es el contexto del proyecto para Claude Code (en español): notas técnicas y reglas de trabajo, sin datos personales ni contenido de terceros. / `CLAUDE.md` is the project context for Claude Code (Spanish): technical notes and working rules, with no personal data or third-party content.
