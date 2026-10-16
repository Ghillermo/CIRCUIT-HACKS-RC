# CIRCUIT-HACKS

<!-- LANG-NOTICE -->
> **English:** the English version of this README is [further below](#english). Illustrated colour manual: [English](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html) · [Español](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html).

Parches de firmware para el **Novation Circuit Tracks** (firmware de referencia 1.2.1 build 4486).

Proyecto desarrollado usando Claude (Anthropic).

> ⚠️ **Antes de instalar: copia de seguridad de la tarjeta SD.**
> - Haz una copia completa de la SD (proyectos, packs y samples) antes de enviar cualquier versión del mod.
> - No trabajes con proyectos importantes guardados en el aparato mientras lo pruebas.
> - No se han reportado fallos, pero estas versiones están en prueba y podría haber problemas que dañen proyectos o samples guardados.
> - Si prefieres no arriesgar la tarjeta, usa la **versión más segura, [RC0.9S](firmware/rc0.9s/PRUEBA.md)**: es RC0.9 sin ninguna función que cree, modifique o borre ficheros en la SD por su cuenta.
> - **[B1.23](firmware/b1.23/PRUEBA.md)** es una versión beta: RC0.9 + funciones nuevas aún sin probar en el aparato. Úsala solo con una copia de la SD.
> - El bootloader de Novation no se toca: **Scales + Preset + Note** al encender permite volver al firmware oficial.

## Repositorio público (rama RC, release candidate)

📖 [Manual ilustrado en color](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html)

Este repositorio contiene **solo el trabajo propio del proyecto**:
- **Herramientas:** builders, ensambladores, emuladores, pruebas, el diagnóstico remoto y el cargador web.
- **Documentación:** manuales, notas técnicas y planes de prueba.
- **Manifiestos** de cada versión.

**No incluye:**
- **Código ni binarios de Novation:** ni el firmware oficial ni los `.syx` / `.bin` parcheados, que contienen el firmware de Novation.
- **Contenido de otros repositorios:** los volcados del aparato y el emulador del DSP se descargan de sus fuentes originales con `tools/setup_dev.py`.
- **Samples ni manuales de terceros.**

### Instalar sin compilar: `tools/rc_uploader.html`

📖 [Manual ilustrado en color](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html)

1. **Descarga el firmware oficial** Circuit Tracks 1.2.1 (build 4486) de Novation: [circuittracks-firmware-4486.syx](https://components.novationmusic.com/api/v2/firmwares/168/file). Es el enlace de descarga de Novation Components; la lista completa está en `https://components.novationmusic.com/api/v2/firmwares`, producto `circuit-tracks`.
2. **Descarga y abre [`tools/rc_uploader.html`](tools/rc_uploader.html)** en Chrome o Edge.
3. **Elige el `.syx` oficial y la versión**: RC0.9, la versión más segura RC0.9S, la beta B1.23 (o las anteriores), u «Oficial» para volver atrás.
   - La página parchea el firmware en el navegador.
   - Comprueba que el resultado es idéntico al publicado (SHA-256).
4. **Conecta el Circuit Tracks y pulsa Enviar.** Confirma con **Play** en el aparato.

La página no contiene código de Novation: solo los bytes del mod y las instrucciones para copiar el resto del firmware oficial que tú aportas. **Haz antes una copia de la tarjeta SD.**

### Con Python (`tools/patch_official.py`)

📖 [Manual ilustrado en color](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html)

1. Consigue el firmware oficial **Circuit Tracks 1.2.1 (build 4486)** desde Novation Components, en `.syx`.
2. `python -m pip install -r tools/requirements.txt`
3. `python tools/patch_official.py RUTA/AL/OFICIAL.syx --version RC0.9`. Para la versión más segura, sin escrituras propias en la SD, usa `--version RC0.9S`. La beta: `--version B1.23`.
4. Envía `firmware/rc0.9/circuittracks-4486-RC0.9.syx` con `tools/ct_uploader.html` (Chrome / Edge).

La herramienta comprueba que el firmware oficial es el correcto y que el resultado es idéntico, bit a bit, al publicado (SHA-256 de `firmware/<versión>/manifest.json`). Para seguir desarrollando: [`docs/LOCAL.md`](docs/LOCAL.md).

Circuit Tracks, Components y Novation son marcas de Focusrite Audio Engineering Ltd. Este proyecto no está afiliado a ellos.

- [`LEEME.md`](LEEME.md) — base de trabajo, formato de actualización y reglas de seguridad.
- [`docs/NOTAS.md`](docs/NOTAS.md) — mapa técnico, modelo de seguridad del bootloader y estado de cada parche. **Última versión: RC0.9**; **más segura: RC0.9S** (sin escrituras propias en la SD); **beta: B1.23** (funciones nuevas sin probar). Las anteriores quedan como reserva (ver el historial).
- [`docs/RECURSOS.md`](docs/RECURSOS.md) — límites de recursos (flash, RAM, almacenamiento, programa / datos / CPU de los dos núcleos del DSP, memoria externa): lo libre en el original, lo usado y cómo se ha optimizado.
- `firmware/<parche>/` — `manifest.json` y `PRUEBA.md` (plan de prueba en el aparato); el `.syx` se genera con `tools/patch_official.py`.
- `tools/` — `ct_fw.py`, builders, emuladores (Unicorn/Capstone) y `ct_uploader.html` (Web MIDI).
- [`docs/LOCAL.md`](docs/LOCAL.md) — cómo clonar y trabajar en local (dependencias, `dsptool`, volcados, pruebas). [`CLAUDE.md`](CLAUDE.md) — contexto para Claude Code.

## Compilar

📖 [Manual ilustrado en color](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html)

**Solo el firmware** (Python 3.10+; no hace falta compilar nada):
```bash
python -m pip install -r tools/requirements.txt
python tools/patch_official.py RUTA/AL/FIRMWARE_OFICIAL.syx --version RC0.9
```
- El firmware oficial es el **Circuit Tracks 1.2.1 (build 4486)** de Novation Components, en `.syx` o `.bin`; la herramienta comprueba su SHA-256.
- Construye la versión en `firmware/<versión>/` y comprueba que el `.syx` es idéntico al publicado.
- `--version RC0.9S` = la versión más segura; `--version B1.23` = la beta; `--list` enseña todas; `--all` las construye todas.
- Envía el `.syx` con `tools/ct_uploader.html` (Chrome / Edge). **Haz antes una copia de la SD.**

**Desarrollo y pruebas** (emuladores del ARM y del DSP; los volcados y el emulador del DSP se descargan aparte):
```bash
python tools/setup_dev.py          # dependencias desde sus fuentes originales: PyPI, firmware oficial, volcados, dsp56300, dsptool, re/app.asm
python tools/verify_builds.py      # todas las versiones idénticas a sus manifiestos
bash tools/run_tests.sh            # pruebas en emulación
```
Windows sin WSL, flujo de un parche nuevo y detalles: [`docs/LOCAL.md`](docs/LOCAL.md). Dependencias, fuentes y licencias: [`docs/DEPENDENCIAS.md`](docs/DEPENDENCIAS.md). Manuales: [`docs/MANUAL.md`](docs/MANUAL.md) y [manual ilustrado en color](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html).

<!-- FEATURES:BEGIN -->
## Características (RC0.9)

Manual de uso: [guía por vistas](https://ghillermo.github.io/CIRCUITS-HACKS-RC/guia.html) ([`docs/GUIA.md`](docs/GUIA.md)) · [referencia MIDI](docs/MIDI.md) · esta lista: [ilustrada en color](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html) · [resumida](docs/MANUAL.md) · **guía en palabras sencillas, ilustrada** ([web](https://ghillermo.github.io/CIRCUITS-HACKS-RC/sencilla.html), [PDF](https://ghillermo.github.io/CIRCUITS-HACKS-RC/sencilla.pdf); primer borrador de [reddit.com/u/luxurysoft1337](https://www.reddit.com/user/luxurysoft1337/), [su guía original](https://files.catbox.moe/xgogqy.pdf)). Novedades y arreglos de cada versión: [`CHANGELOG.md`](CHANGELOG.md). Lo marcado **solo Beta 1.23** está en la versión beta (Beta 1.23), no en RC0.9.

### A. Accesos directos y usabilidad
- **[A1 Mapa de atajos](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#a1-atajos)** — Todos los atajos del mod en un dibujo del aparato: botones dobles, Shift + botón, Clear + knob y los pads especiales de cada vista.
- **[A2 Master FX en el botón Mixer](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#a2-master-fx-acceso)** — Desde el Mixer, **Mixer otra vez** abre Master FX; cualquier otro botón de vista sale.
- **[A3 Teclas de la vista FX](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#a3-vista-fx)** — **Octave ▲ / ▼** = envíos de delay / reverb; **Shift + knob** = parámetros de reverb y delay. **Duplicate** = reset (envíos a 0, filtro master al centro, Master FX apagado); **1-16 / 17-32** = resonancia del filtro master.
- **[A4 Clear + knob = valor por defecto](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#a4-clear-knob)** — Mantén **Clear** y gira un knob a la derecha: vuelve a su valor por defecto. En drums (LED azul), a la izquierda borra la automatización de los knobs de stock (LED rojo), como en el original. También en el motor de las pistas MIDI y en **Master FX**.
- **[A5 Apagar efectos fijados (pad 8 de Master FX)](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#a5-pad8)** — **Pad 8** apaga todo lo fijado con Shift (efectos y song pointer) y hace bypass de los FX; tocar un efecto fijado lo suelta.
- **[A6 Vista de la fuente del sinte](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#a6-fuente-sinte)** — Con Synth 1 / 2 en pantalla, **pulsa su botón otra vez**: pads 25-29 eligen la fuente (ruido, entradas, invertidas), pad 30 = step-drummer.
- **[A7 Vista cromática y de escala de los drums](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#a7-cromatica)** — **Shift + Preset** con un drum: los pads tocan el sample en la escala; K1 = sesgo de tono, Shift + K1 = cents; vista Note: pads 25-28 = drums 4-1.
- **[A8 Gestión del pack desde el aparato](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#a8-pack)** — **Save** también guarda en la tarjeta los samples sustituidos por capturas. **Duplicate + pad A + pad B** (Preset de drums) intercambia dos samples; entre packs **copia** samples y patches de sinte; **Clear**, el pack, **Clear** (vista de packs) borra un pack.
- **[A9 Sustituir un drum por la captura](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#a9-sustituir)** — Vista Preset de drums: **Clear + pad dos veces** = ese sample pasa a ser la captura (hasta guardar o recargar).
- **[A10 Editor de CC de los macros MIDI](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#a10-editor-cc)** — Vista Preset de MIDI 1 / 2, **pad 25**: mueve un knob y cambia su CC / NRPN desde el aparato; pad 26 = guardar.
- **[A11 Mixer: Shift + knob = nivel a 100 / 0](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#a11-mixer-shift)** — Vista Mixer: **Shift + girar un knob a la derecha** pone el nivel de esa pista a **100**; **a la izquierda**, a **0**.
- **[A12 Teclado partido Synth 1 + Synth 2](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#a12-teclado-partido)** — **Solo Beta 1.23.** Mantén **Synth 1** y pulsa **Synth 2** (o al revés): las dos filas de arriba tocan Synth 1 y las dos de abajo Synth 2.
- **[A13 Patches de sinte por modo de voz](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#a13-colores-patch)** — **Solo Beta 1.23.** En la vista Preset de Synth 1 / 2 cada patch se ve según su modo de voz: **mono azul oscuro**, **glide lavanda**, **poly como siempre**.
- **[A14 Patches del sinte propio (MIDI 1 / 2)](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#a14-patches-midi)** — **Solo Beta 1.23.** En la vista Preset de MIDI 1 / 2 las filas 2 y 3 son 16 huecos de patch del motor de la pista: tocar = cargar (suena la tónica), **Clear + pad** dos veces = guardar, **Duplicate + A + B** = intercambiar; **Octave ▼ / ▲** = 4 páginas (64 huecos por pack).
- **[A15 Guardar el patch del sinte en el pack](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#a15-guardar-patch)** — **Solo Beta 1.23.** En la vista Preset de Synth 1 / 2: **Clear + pad** pregunta (parpadea en blanco) y **Clear + el mismo pad otra vez** guarda en ese hueco el patch tal como suena.
- **[A16 Destinos de los macro knobs](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#a16-destinos-macro)** — **Solo Beta 1.23.** En la vista de la fuente del sinte (A6) el **pad 32** abre el editor: un knob elige su macro, **Octave ▼ / ▲** pasa de campo y los pads dibujan el número.
- **[A17 Copiar proyectos a otro hueco o a otro pack](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#a17-copiar-proyectos)** — **Solo Beta 1.23.** En la vista Projects: **Duplicate + pad A** elige el proyecto (parpadea en amarillo) y **Duplicate + pad B** lo copia a ese hueco, del mismo pack o de otro.
- **[A18 Patches del sinte propio a otro pack](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#a18-patches-entre-packs)** — **Solo Beta 1.23.** En la vista Preset de MIDI 1 / 2: **Duplicate + hueco A**, carga otro pack y **Duplicate + hueco B** copia el patch (motor, parámetros y nombre).

### B. Controles expuestos
- **[B1 Knobs de los drums según el panel](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#b1-knobs-drums)** — Cada knob hace lo que dice su etiqueta, con una segunda capa en Shift: ring mod, envolventes, filtros (DJ, BP, notch, comb, tilt), LFO, start point, bitcrush y distorsión.
- **[B2 Parámetros de reverb y delay](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#b2-rev-delay)** — Vista FX, **Shift + knob**: reverb (tipo, decay, damping) y delay (time, sync, feedback, width, ratio, slew); se guardan con el proyecto.
- **[B3 Sidechain y compresor master con los knobs](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#b3-sidechain-comp)** — **Solo Beta 1.23.** En la vista Sidechain (**Shift + FX**): **K1-K4** = ataque, hold, decay y profundidad del sidechain de la pista elegida; **K7 / K8** = ataque y release del compresor master.
- **[B4 Grabar los ruteos internos de MIDI](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#b4-grabar-interno)** — **Solo Beta 1.23.** En la vista Setup, **Record** decide si lo que una pista MIDI manda a un sinte interno por el canal compartido se graba también en ese sinte: **amarillo = sí**, apagado = no (por defecto).
- **[B5 MIDI para todo lo nuevo](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#b5-midi-io)** — Los valores nuevos salen y entran por MIDI: CC / NRPN del motor de las pistas MIDI, NRPN de los drums (MSB 5-8) y de Master FX (MSB 9, canal 16).
- **[B6 Automatización del motor MIDI](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#b6-automatizacion)** — Con Record + Play, los 8 valores de la página 4 del motor MIDI se graban en los carriles de macros del patrón.
- **[B7 Setup y MIDI del aparato](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#b7-setup)** — Canal 16 Rx / Tx (pad 16), canales compartidos, **loopback interno** sin cable y **retornos de reverb / delay por las tiras 3 / 4** (pads 22 / 23, en crema / melocotón como la reverb y el delay de la vista FX). **Solo Beta 1.23:** MIDI Thru con cuatro modos (Duplicate en Advanced Setup): Thru, Out 2, **Merge** (DIN In + el MIDI del aparato) y **Filter** (DIN In sin los canales en escucha). **Solo Beta 1.23:** canales de **Program Change** propios: pad 29 / 30 enseñan y eligen el canal de escucha / salida (16 por defecto); lo recibido se reenvía por el de salida. **Solo Beta 1.23:** **metrónomo con cuenta atrás**: Shift + Clear recorre sin metrónomo, metrónomo, solo cuenta atrás y las dos; la cuenta atrás es un compás antes de grabar.
- **[B8 Patch flip en MIDI 1 / 2](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#b8-patch-flip)** — Pad 26 de la vista Preset de MIDI: cada nota se envía como Program Change (excluyente con el motor de la pista).

### C. Nuevos modos de control
- **[C1 Motor de las pistas MIDI (pad 27)](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#c1-motor-midi)** — El pad 27 de la vista Preset de MIDI 1 / 2 elige el motor: apagado → **línea** → **oscilador** → **VA-drum** → **granular** → **secuenciador de efectos**. Los pads 1-5 eligen la página de knobs; 28 = dos osciladores, 29 = orden de la cadena, 30 = step-drummer, 31 = velocity (VA-drum). **Solo Beta 1.23:** Clear + un pad de página = los valores de esa página a los iniciales; las filas 2-3 guardan patches (A14).
- **[C2 Step-drummer](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#c2-step-drummer)** — Secuenciación por **pares de pasos** sobre el patrón: pads 1-16 pasos, 17-24 destino / macro, los 8 knobs = los 8 pares (pitch u velocity). MIDI: vista Preset, pad 30. Sintes: vista de la fuente, pad 30. Grabando, los pasos tocados se graban en tiempo real.
- **[C3 Secuenciador de efectos](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#c3-fx-seq)** — Estado **azul** del pad 27: el step-drummer de la pista elige, en cada par de pasos, **un hueco de la fila inferior de Master FX** (0 = nada); suena en los pasos con nota. El knob avanza despacio (**un hueco cada ~48 pasos de giro**) y se ilumina con el **color del efecto** elegido. **Un hueco sin efecto asignado no hace nada:** asigna antes los efectos a la fila inferior de Master FX (ver «Fila inferior asignable»). **Solo Beta 1.23:** al final del recorrido está el valor **random** (LED blanco): en cada paso con nota suena uno de la lista al azar (los huecos con efecto asignado y el gesto mecánico del pad 31).
- **[C4 Song pointer (Master FX)](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#c4-song-pointer)** — Pads 9-24 = pasos 1-16: un paso mantenido = retrigger; dos pasos = frase momentánea; Shift + dos = frase fijada. **Modo frase:** Shift + paso = inicio (fin 16); un toque = el fin; Shift + otro paso = nuevo inicio; Shift + el inicio o el pad 9 blanco = salir.
- **[C5 Sample capturado](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#c5-sample)** — **Pad 32** (rojo) graba la salida; **pad 7** (amarillo) la toca: K1 pitch, K2 modo (one-shot / gate / loop por color), K3 start, K4 end. El sample se asigna a la fila inferior (pad 7 + pad de abajo) y puede sustituir a un drum (A9).
- **[C6 Glitch (pad 31) y su asignación](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#c6-glitch-pad)** — **Mantén el pad 31** (Master FX o vista FX): la salida se rompe y se retrasa como una cinta. K1 velocidad, K2 repetición, K3 retraso, K4 caos (mitad de abajo) o sobrecarga (mitad de arriba). **Pad 31 mantenido + otro pad de la fila inferior** = ese hueco también es un Glitch, con su copia de K1-K4.
- **[C7 Fila inferior asignable (Master FX / FX)](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#c7-fila-inferior)** — Mantén un efecto de arriba (o el pad 7, o el pad 31) y toca un pad de abajo: ese hueco guarda el efecto con una copia de sus parámetros. Se guarda con el proyecto.
- **[C8 Random-mutate por paso](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#c8-random-mutate)** — **Solo Beta 1.23.** En la vista de probabilidad (**Shift + Pattern Settings**) la fila 4 da a cada paso una probabilidad de que sus notas salten de octava o cambien a otra nota de la escala al sonar.
- **[C9 Frecuencia y dinámicas por paso](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#c9-frecuencia-dinamicas)** — **Solo Beta 1.23.** En la vista de probabilidad de las pistas de notas: **fila 4 = cada cuántas vueltas del patrón suena el paso** (1-8). Con el **pad 25 de Pattern Settings**: fila 3 = **dinámicas** aleatorias (velocity, posición y duración), fila 4 = random-mutate.
- **[C10 Cadenas de patrones y escenas](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#c10-cadenas)** — **Solo Beta 1.23.** Cada patrón puede llevar una regla «suena n veces, luego salta a B; la vez siguiente, a C». **Shift + Octave ▲ / ▼** en la vista Patterns activa / desactiva el **modo cadena** de todo el proyecto; cada escena recuerda el modo con que se guardó.
- **[C11 Nudge y órdenes de reproducción](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#c11-nudge-ordenes)** — **Solo Beta 1.23.** En la vista Pattern Settings: **pad 26 = Nudge** (el patrón rotado para que el primer paso elegido sea el paso 1), **pad 27 = orden fractal**, **pad 28 = orden deconstruido**. En todas las pistas, drums incluidos.
- **[C12 Arpegiador (solo Beta 1.23)](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#c12-arpegiador)** — **Solo Beta 1.23.** En la vista Pattern Settings de una pista de notas: **Shift + pad 25** = arpegiador del patrón encendido / apagado, **Shift + pads 27-32** = su orden (fractal, deconstruido, arriba, abajo, ping-pong, aleatorio), independiente de la dirección del patrón.
- **[C13 Rollers de micropasos de los drums (solo Beta 1.23)](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#c13-rollers)** — **Solo Beta 1.23.** Filas 1-3 de la vista Note de los drums: mantener un roller hace sonar su drum en cada paso en ese micropaso (dos columnas por drum, micropasos 1-3 y 4-6), en directo; con el transporte parado, al tempo del proyecto.
- **[C14 Escala propia (solo Beta 1.23)](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#c14-escala-propia)** — **Solo Beta 1.23.** **Shift + Scales** = editor de una escala propia para las pistas de notas: hasta 7 notas sobre la tónica y un **periodo** cualquiera (hasta 24 semitonos) que es la tónica de la siguiente iteración; cada fila de pads es una iteración (dos con 4 notas o menos). Se guarda con el proyecto.
- **[C15 Master FX en la beta: gesto mecánico, Glitch, Digitise y guardado por sesión](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#c15-master-fx-beta)** — **Solo Beta 1.23.** El pad 6 de Master FX es el **Glitch** y el pad 31 un **gesto mecánico** (parada de cinta, scratch…); Digitise gana **K3 = envío momentáneo al delay** y **K4 = envolvente**; los knobs y los huecos de Master FX **se guardan con cada proyecto**.

### D. DSP
- **[D1 Efectos de Master FX](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#d1-efectos-grid)** — Gater, Auto-Filter LP / HP, Digitise, Phaser y Vinyl sobre la salida master, con 4 parámetros cada uno.
- **[D2 VCA-VCF de las pistas MIDI](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#d2-vca-vcf)** — Filtros DJ / LP / HP 12 y 24 dB / paso banda / notch, efectos (saturación, plegado, wavefold, ring, comb, chorus), VCA con ADSR y LFO.
- **[D3 Osciladores y parafonía](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#d3-osciladores)** — Morph continuo seno → triángulo → sierra → cuadrada, wavefold / pendiente / ancho, segundo oscilador con FM, ring, sync suave y modos bit a bit; dos notas parafónicas.
- **[D4 Motor VA-drum](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#d4-va-drum)** — Oscilador pensado para percusión: VCA de un disparo, envolventes de decay propias para pitch (knob Sustain) y filtro (knob Release), ruido blanco y valores aleatorios en lugar del LFO.
- **[D5 Sinte granular](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#d5-granular)** — Hasta **16 granos por pista** desde cualquier sample del pack o la captura, con interpolación y ventana; en el segundo núcleo del DSP. K1 tono, K2 posición, K3 scan / freeze, K4 tamaño, K5 densidad, K6 zona, K7 LFO → posición, K8 envolvente → posición; Shift: fino, dispersiones, reverso, ventana, slicer (o stretch, solo Beta 1.23), LFO → tamaño, fuente.
- **[D6 Motor del Glitch](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#d6-glitch-dsp)** — Una cabeza de cinta sobre un búfer circular estéreo del master (2,7 s) en la memoria externa del DSP: velocidad variable, repeticiones con fundidos, caos.
- **[D7 DSP de los drums](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#d7-drums-dsp)** — Ring mod, envolventes de tono y filtro, LFO, filtros DJ / paso banda / notch / comb / tilt, bitcrush, start point, distorsiones y sidechain entre drums.
- **[D8 Entradas de audio y retornos](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#d8-entradas)** — Entrada de línea (normal o invertida) como fuente de los sintes; retornos de reverb / delay por las tiras 3 / 4 con realimentación.

### E. Miscelánea
- **[E1 Qué se guarda y dónde](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#e1-guardado)** — Proyecto: drums, huecos de Master FX, fuente de los sintes, parámetros de reverb / delay. Aparato: motor de las pistas MIDI. Volátil: OSC 2, efectos fijados.
- **[E2 El pack de la memoria interna: solo lectura](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#e2-pack-interno)** — Nada del mod escribe ni borra en el pack de la memoria interna del Circuit (el primero de la vista de packs). Se puede leer de él y copiar desde él a un pack de la tarjeta, pero no al revés.
- **[E3 Instalar y volver atrás](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#e3-instalar)** — `tools/ct_uploader.html` envía el `.syx` por Web MIDI; solo acepta firmwares verificados. Recuperación: Scales + Preset + Note al encender.
- **[E4 Herramientas de desarrollo y diagnóstico](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#e4-herramientas)** — Builders reproducibles, emuladores ARM / DSP con pruebas por rutas reales, `verify_builds.py`, diagnóstico remoto por USB (`ctremote.py`).
- **[E5 Tablas MIDI](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html#e5-tablas-midi)** — Motor MIDI: CC 74/71/79/73/75/70/72/91/59/26/27/20/21/37/39/30/31/52/54 + NRPN 4:x; drums NRPN 5-8:1-12; Master FX NRPN 9:0-19 (canal 16).

<!-- FEATURES:END -->

## Licencia

[MIT](LICENSE) © 2026 Ghillermo, para el trabajo propio del proyecto (herramientas, parches, documentación y manuales). No cubre el firmware de Novation (no se incluye; se obtiene de Novation con sus condiciones, igual que las imágenes construidas a partir de él) ni las dependencias de terceros, que conservan sus licencias ([`docs/DEPENDENCIAS.md`](docs/DEPENDENCIAS.md)): los parches de `tools/dsptool/` se aplican a dsp56300 (GPL-3.0) y un `dsptool` enlazado con él es GPL-3.0.

---

<a id="english"></a>
# CIRCUIT-HACKS (English)

📖 [Illustrated colour manual](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html)

Firmware patches for the **Novation Circuit Tracks** (reference firmware 1.2.1 build 4486). The project was developed using Claude (Anthropic).

> ⚠️ **Before installing: back up your SD card.**
> - Make a full copy of the SD card (projects, packs and samples) before sending any version of the mod.
> - Do not work on important projects stored on the device while you test it.
> - No failures have been reported, but these versions are being tested and there could be problems that damage saved projects or samples.
> - If you would rather not risk the card, use the **safer build, [RC0.9S](firmware/rc0.9s/PRUEBA.md)**: RC0.9 without any feature that creates, changes or deletes files on the SD card on its own.
> - **[B1.23](firmware/b1.23/PRUEBA.md)** is a beta: RC0.9 + new features not yet tested on the device. Use it only with a backup of the SD card.
> - Novation’s bootloader is never touched: **Scales + Preset + Note** at power-on lets you go back to the official firmware.

**Manual:** [short](docs/MANUAL.en.md) · [illustrated](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html). Public repository: <https://github.com/Ghillermo/CIRCUITS-HACKS-RC>.

### What the public repository contains

📖 [Illustrated colour manual](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html)

- **Tools:** builders, assemblers, emulators, tests, remote diagnostics and the web uploaders.
- **Documentation:** manuals (Spanish and English), technical notes and test plans (Spanish).
- **Manifests** of every version.

It does **not** include Novation code or binaries (neither the official firmware nor patched `.syx` / `.bin` files, which contain Novation’s firmware), content of other repositories (the device dumps and the DSP emulator are downloaded from their original sources by `tools/setup_dev.py`), samples or third-party manuals.

### Install without building: `tools/rc_uploader.html`

📖 [Illustrated colour manual](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html)

1. **Download the official firmware** Circuit Tracks 1.2.1 (build 4486) from Novation: [circuittracks-firmware-4486.syx](https://components.novationmusic.com/api/v2/firmwares/168/file). It is the Novation Components download link; the full list is at `https://components.novationmusic.com/api/v2/firmwares`, product `circuit-tracks`.
2. **Download and open [`tools/rc_uploader.html`](tools/rc_uploader.html)** in Chrome or Edge.
3. **Pick the official `.syx` and the version**: RC0.9, the safer RC0.9S, the beta B1.23 (or the earlier ones), or “Official” to go back.
   - The page patches the firmware in the browser.
   - It checks that the result is identical to the published one (SHA-256).
4. **Connect the Circuit Tracks and press Send.** Confirm with **Play** on the device.

The page contains no Novation code: only the bytes of the mod and the instructions to copy the rest from the official firmware you provide. **Back up the SD card first.**

### Build

📖 [Illustrated colour manual](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html)

**Firmware only** (Python 3.10+; nothing to compile):
```bash
python -m pip install -r tools/requirements.txt
python tools/patch_official.py PATH/TO/OFFICIAL_FIRMWARE.syx --version RC0.9
```
- The official firmware is the **Circuit Tracks 1.2.1 (build 4486)** from Novation Components, as `.syx` or `.bin`; the tool checks its SHA-256.
- It builds the version into `firmware/<version>/` and checks that the `.syx` is identical to the published one.
- `--version RC0.9S` = the safer build; `--version B1.23` = the beta; `--list` shows them all; `--all` builds them all.
- Send the `.syx` with `tools/ct_uploader.html` (Chrome / Edge). **Back up the SD card first.**

**Development and tests** (ARM and DSP emulators; the dumps and the DSP emulator are downloaded separately):
```bash
python tools/setup_dev.py          # dependencies from their original sources: PyPI, official firmware, dumps, dsp56300, dsptool, re/app.asm
python tools/verify_builds.py      # every version identical to its manifest
bash tools/run_tests.sh            # emulation tests
```
Windows without WSL, the workflow of a new patch and details: [`docs/LOCAL.en.md`](docs/LOCAL.en.md). Dependencies, sources and licences: [`docs/DEPENDENCIAS.md`](docs/DEPENDENCIAS.md).

### Files

📖 [Illustrated colour manual](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html)

- [`LEEME.md`](LEEME.md) — update format and bootloader safety (Spanish and English).
- [`docs/NOTAS.md`](docs/NOTAS.md) — technical map, bootloader safety model and status of every patch (Spanish). **Latest version: RC0.9**; **safer: RC0.9S**; **beta: B1.23** (new features not yet tested).
- [`docs/RECURSOS.md`](docs/RECURSOS.md#resources) — resource limits (flash, RAM, storage, program / data / CPU of both DSP cores, external memory): what the original left free, what is used and how it was optimised.
- `firmware/<version>/` — `manifest.json` and `PRUEBA.md` (test plan on the device, Spanish).
- `tools/` — `ct_fw.py`, builders, emulators (Unicorn / Capstone), `ct_uploader.html` and `rc_uploader.html` (Web MIDI).
- [`CLAUDE.md`](CLAUDE.md) — context for Claude Code (Spanish).

<!-- FEATURES-EN:BEGIN -->
## Features (RC0.9)

User manual: [guide by views](https://ghillermo.github.io/CIRCUITS-HACKS-RC/guide.html) ([`docs/GUIA.en.md`](docs/GUIA.en.md)) · [MIDI reference](docs/MIDI.en.md) · this list: [illustrated colour](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html) · [short](docs/MANUAL.en.md) · **guide in plain words, illustrated** ([web](https://ghillermo.github.io/CIRCUITS-HACKS-RC/plain.html), [PDF](https://ghillermo.github.io/CIRCUITS-HACKS-RC/plain.pdf); first draft by [reddit.com/u/luxurysoft1337](https://www.reddit.com/user/luxurysoft1337/), [the original guide](https://files.catbox.moe/xgogqy.pdf)). New features and fixes of every version: [`CHANGELOG.md`](CHANGELOG.md#changelog). What is marked **Beta 1.23 only** is in the beta (Beta 1.23), not in RC0.9.

### A. Shortcuts and usability
- **[A1 Shortcut map](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#a1-atajos)** — Every shortcut of the mod on a drawing of the device: double presses, Shift + button, Clear + knob and the special pads of each view.
- **[A2 Master FX on the Mixer button](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#a2-master-fx-acceso)** — From the Mixer, **Mixer again** opens Master FX; any other view button leaves it.
- **[A3 Keys of the FX view](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#a3-vista-fx)** — **Octave ▲ / ▼** = delay / reverb sends; **Shift + knob** = reverb and delay parameters. **Duplicate** = reset (sends to 0, master filter centred, Master FX off); **1-16 / 17-32** = master filter resonance.
- **[A4 Clear + knob = default value](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#a4-clear-knob)** — Hold **Clear** and turn a knob right: it goes back to its default. On the drums (blue LED), turned left it deletes the automation of the stock knobs (red LED), as on the original. Also on the MIDI track engine and in **Master FX**.
- **[A5 Switch off latched effects (Master FX pad 8)](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#a5-pad8)** — **Pad 8** switches off everything latched with Shift (effects and song pointer) and bypasses the FX; touching a latched effect releases it.
- **[A6 Synth source view](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#a6-fuente-sinte)** — With Synth 1 / 2 on screen, **press its button again**: pads 25-29 pick the source (noise, inputs, inverted inputs), pad 30 = step-drummer.
- **[A7 Chromatic and scale view of the drums](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#a7-cromatica)** — **Shift + Preset** with a drum: the pads play the sample in the scale; K1 = pitch offset, Shift + K1 = cents; Note view: pads 25-28 = drums 4-1.
- **[A8 Pack management on the device](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#a8-pack)** — **Save** also writes the samples replaced by captures to the card. **Duplicate + pad A + pad B** (Drum Preset) swaps two samples; between packs it **copies** samples and synth patches; **Clear**, the pack, **Clear** (packs view) deletes a pack.
- **[A9 Replace a drum with the capture](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#a9-sustituir)** — Drum Preset view: **Clear + pad twice** = that sample becomes the capture (until you save or reload).
- **[A10 CC editor of the MIDI macros](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#a10-editor-cc)** — MIDI 1 / 2 Preset view, **pad 25**: move a knob and change its CC / NRPN on the device; pad 26 = save.
- **[A11 Mixer: Shift + knob = level to 100 / 0](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#a11-mixer-shift)** — Mixer view: **Shift + a knob turned right** sets that track’s level to **100**; **turned left**, to **0**.
- **[A12 Split keyboard Synth 1 + Synth 2](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#a12-teclado-partido)** — **Beta 1.23 only.** Hold **Synth 1** and press **Synth 2** (or the other way round): the two top rows play Synth 1 and the two bottom rows Synth 2.
- **[A13 Synth patches by voice mode](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#a13-colores-patch)** — **Beta 1.23 only.** In the Preset view of Synth 1 / 2 every patch is drawn by its voice mode: **mono dark blue**, **glide lavender**, **poly as always**.
- **[A14 Patches of the own synth (MIDI 1 / 2)](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#a14-patches-midi)** — **Beta 1.23 only.** In the Preset view of MIDI 1 / 2, rows 2 and 3 are 16 patch slots of the track engine: touch = load (the root note sounds), **Clear + pad** twice = save, **Duplicate + A + B** = exchange; **Octave ▼ / ▲** = 4 pages (64 slots per pack).
- **[A15 Saving the synth’s patch into the pack](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#a15-guardar-patch)** — **Beta 1.23 only.** In the Preset view of Synth 1 / 2: **Clear + pad** asks (it blinks white) and **Clear + the same pad again** saves the patch as it sounds into that slot.
- **[A16 Macro knob destinations](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#a16-destinos-macro)** — **Beta 1.23 only.** In the synth source view (A6), **pad 32** opens the editor: a knob picks its macro, **Octave ▼ / ▲** steps the field and the pads draw the number.
- **[A17 Copying projects to another slot or another pack](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#a17-copiar-proyectos)** — **Beta 1.23 only.** In the Projects view: **Duplicate + pad A** picks the project (it blinks yellow) and **Duplicate + pad B** copies it into that slot, of the same pack or of another one.
- **[A18 Own-synth patches to another pack](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#a18-patches-entre-packs)** — **Beta 1.23 only.** In the Preset view of MIDI 1 / 2: **Duplicate + slot A**, load another pack and **Duplicate + slot B** copies the patch (engine, parameters and name).

### B. Exposed controls
- **[B1 Drum knobs as printed on the panel](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#b1-knobs-drums)** — Every knob does what its label says, with a second layer on Shift: ring mod, envelopes, filters (DJ, BP, notch, comb, tilt), LFO, start point, bitcrush and distortion.
- **[B2 Reverb and delay parameters](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#b2-rev-delay)** — FX view, **Shift + knob**: reverb (type, decay, damping) and delay (time, sync, feedback, width, ratio, slew); saved with the project.
- **[B3 Side-chain and master compressor on the knobs](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#b3-sidechain-comp)** — **Beta 1.23 only.** In the Sidechain view (**Shift + FX**): **K1-K4** = attack, hold, decay and depth of the side-chain of the chosen track; **K7 / K8** = attack and release of the master compressor.
- **[B4 Recording the internal MIDI routes](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#b4-grabar-interno)** — **Beta 1.23 only.** In the Setup view, **Record** decides whether what a MIDI track sends to an internal synth over a shared channel is also recorded into that synth: **yellow = yes**, dark = no (the default).
- **[B5 MIDI for everything new](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#b5-midi-io)** — The new values go out and come in over MIDI: CC / NRPN of the MIDI track engine, NRPN of the drums (MSB 5-8) and of Master FX (MSB 9, channel 16).
- **[B6 Automation of the MIDI engine](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#b6-automatizacion)** — With Record + Play, the 8 values of page 4 of the MIDI engine are recorded into the macro lanes of the pattern.
- **[B7 Setup and device MIDI](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#b7-setup)** — Channel 16 Rx / Tx (pad 16), shared channels, **internal loopback** without a cable and **reverb / delay returns through strips 3 / 4** (pads 22 / 23, cream / peach like the reverb and delay of the FX view). **Beta 1.23 only:** MIDI Thru with four modes (Duplicate in Advanced Setup): Thru, Out 2, **Merge** (DIN In + the device’s MIDI) and **Filter** (DIN In without the channels the device listens to). **Beta 1.23 only:** own **Program Change** channels: pads 29 / 30 show and pick the listen / output channel (16 by default); what is received is forwarded on the output one. **Beta 1.23 only:** **metronome with count-in**: Shift + Clear walks no metronome, metronome, count-in only and both; the count-in is one bar before recording.
- **[B8 Patch flip on MIDI 1 / 2](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#b8-patch-flip)** — Pad 26 of the MIDI Preset view: every note is sent as a Program Change (exclusive with the track engine).

### C. New control modes
- **[C1 Engine of the MIDI tracks (pad 27)](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#c1-motor-midi)** — Pad 27 of the MIDI 1 / 2 Preset view picks the engine: off → **line** → **oscillator** → **VA-drum** → **granular** → **FX sequencer**. Pads 1-5 pick the knob page; 28 = two oscillators, 29 = chain order, 30 = step-drummer, 31 = velocity (VA-drum). **Beta 1.23 only:** Clear + a page pad = the values of that page back to their initial values; rows 2-3 hold patches (A14).
- **[C2 Step-drummer](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#c2-step-drummer)** — Sequencing by **pairs of steps** on top of the pattern: pads 1-16 steps, 17-24 destination / macro, the 8 knobs = the 8 pairs (pitch or velocity). MIDI: Preset view, pad 30. Synths: source view, pad 30. While recording, the steps you play are recorded in real time.
- **[C3 FX sequencer](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#c3-fx-seq)** — **Blue** state of pad 27: the step-drummer of the track picks, for each pair of steps, **a slot of the Master FX bottom row** (0 = none); it plays on the steps with a note. The knob moves slowly (**one slot every ~48 steps of the turn**) and lights in the **colour of the chosen effect**. **A slot with no effect assigned does nothing:** assign the effects to the Master FX bottom row first (see “Assignable bottom row”). **Beta 1.23 only:** at the end of the travel there is the **random** value (white LED): on every step with a note one of the list plays at random (the slots with an effect assigned and the mechanical gesture of pad 31).
- **[C4 Song pointer (Master FX)](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#c4-song-pointer)** — Pads 9-24 = steps 1-16: one held step = retrigger; two steps = momentary phrase; Shift + two = latched phrase. **Phrase mode:** Shift + step = start (end 16); a touch = the end; Shift + another step = new start; Shift + the start or the white pad 9 = exit.
- **[C5 Captured sample](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#c5-sample)** — **Pad 32** (red) records the output; **pad 7** (yellow) plays it: K1 pitch, K2 mode (one-shot / gate / loop by colour), K3 start, K4 end. The sample can be assigned to the bottom row (pad 7 + a bottom pad) and can replace a drum (A8).
- **[C6 Glitch (pad 31) and its assignment](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#c6-glitch-pad)** — **Hold pad 31** (Master FX or FX view): the output breaks up and lags like a tape. K1 speed, K2 repeat, K3 delay, K4 chaos (lower half) or overload (upper half). **Pad 31 held + another bottom-row pad** = that slot is a Glitch too, with its copy of K1-K4.
- **[C7 Assignable bottom row (Master FX / FX)](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#c7-fila-inferior)** — Hold an effect of the top rows (or pad 7, or pad 31) and touch a bottom pad: that slot stores the effect with a copy of its parameters. Saved with the project.
- **[C8 Random-mutate per step](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#c8-random-mutate)** — **Beta 1.23 only.** In the probability view (**Shift + Pattern Settings**) row 4 gives each step a chance of its notes jumping an octave or moving to another note of the scale when they play.
- **[C9 Step frequency and dynamics](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#c9-frecuencia-dinamicas)** — **Beta 1.23 only.** In the probability view of the note tracks: **row 4 = every how many plays of the pattern the step sounds** (1-8). With **pad 25 of Pattern Settings**: row 3 = random **dynamics** (velocity, position and length), row 4 = random-mutate.
- **[C10 Pattern chains and scenes](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#c10-cadenas)** — **Beta 1.23 only.** Every pattern can carry a rule “play n times, then jump to B; the next time, to C”. **Shift + Octave ▲ / ▼** in the Patterns view switches the **chain mode** of the whole project on / off; every scene remembers the mode it was saved in.
- **[C11 Nudge and play orders](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#c11-nudge-ordenes)** — **Beta 1.23 only.** In the Pattern Settings view: **pad 26 = Nudge** (the pattern rotated so that the chosen first step becomes step 1), **pad 27 = fractal order**, **pad 28 = deconstructed order**. On every track, drums included.
- **[C12 Arpeggiator (Beta 1.23 only)](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#c12-arpegiador)** — **Beta 1.23 only.** In the Pattern Settings view of a note track: **Shift + pad 25** = the pattern's arpeggiator on / off, **Shift + pads 27-32** = its order (fractal, deconstructed, up, down, ping-pong, random), independent of the pattern's direction.
- **[C13 Drums micro-step rollers (Beta 1.23 only)](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#c13-rollers)** — **Beta 1.23 only.** Rows 1-3 of the drums' Note view: holding a roller plays its drum on every step at that micro step (two columns per drum, micro steps 1-3 and 4-6), live; with the transport stopped, at the project's tempo.
- **[C14 Custom scale (Beta 1.23 only)](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#c14-escala-propia)** — **Beta 1.23 only.** **Shift + Scales** = an editor of a custom scale for the note tracks: up to 7 notes over the root and any **period** (up to 24 semitones) that is the root of the next iteration; every row of pads is one iteration (two with 4 notes or fewer). Saved with the project.
- **[C15 Master FX in the beta: mechanical gesture, Glitch, Digitise and saving per session](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#c15-master-fx-beta)** — **Beta 1.23 only.** Pad 6 of Master FX is the **Glitch** and pad 31 a **mechanical gesture** (tape stop, scratch…); Digitise gains **K3 = momentary send to the delay** and **K4 = envelope**; the Master FX knobs and slots **are saved with every project**.

### D. DSP
- **[D1 Master FX effects](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#d1-efectos-grid)** — Gater, Auto-Filter LP / HP, Digitise, Phaser and Vinyl on the master output, with 4 parameters each.
- **[D2 VCA-VCF of the MIDI tracks](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#d2-vca-vcf)** — DJ / LP / HP 12 and 24 dB / band pass / notch filters, effects (saturation, folding, wavefold, ring, comb, chorus), VCA with ADSR and LFO.
- **[D3 Oscillators and paraphony](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#d3-osciladores)** — Continuous morph sine → triangle → saw → square, wavefold / slope / width, second oscillator with FM, ring, soft sync and bitwise modes; two paraphonic notes.
- **[D4 VA-drum engine](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#d4-va-drum)** — Oscillator made for percussion: one-shot VCA, dedicated decay envelopes for pitch (Sustain knob) and filter (Release knob), white noise and random values instead of the LFO.
- **[D5 Granular synth](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#d5-granular)** — Up to **16 grains per track** from any sample of the pack or the capture, with interpolation and window; on the second DSP core. K1 pitch, K2 position, K3 scan / freeze, K4 size, K5 density, K6 zone, K7 LFO → position, K8 envelope → position; Shift: fine, sprays, reverse, window, slicer (or stretch, Beta 1.23 only), LFO → size, source.
- **[D6 Glitch engine](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#d6-glitch-dsp)** — A tape head over a stereo circular buffer of the master (2.7 s) in the external DSP memory: variable speed, repeats with fades, chaos.
- **[D7 Drum DSP](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#d7-drums-dsp)** — Ring mod, pitch and filter envelopes, LFO, DJ / band pass / notch / comb / tilt filters, bitcrush, start point, distortions and sidechain between drums.
- **[D8 Audio inputs and returns](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#d8-entradas)** — Line input (normal or inverted) as a synth source; reverb / delay returns through strips 3 / 4 with feedback.

### E. Miscellaneous
- **[E1 What is saved and where](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#e1-guardado)** — Project: drums, Master FX slots, synth source, reverb / delay parameters. Device: MIDI track engine. Volatile: OSC 2, latched effects.
- **[E2 The internal memory pack: read only](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#e2-pack-interno)** — Nothing of the mod writes or deletes in the pack of the Circuit’s internal memory (the first one of the Packs view). You can read it and copy from it to a pack of the card, not the other way round.
- **[E3 Installing and going back](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#e3-instalar)** — `tools/ct_uploader.html` sends the `.syx` over Web MIDI; it only accepts verified firmwares. Recovery: Scales + Preset + Note at power-on.
- **[E4 Development and diagnostic tools](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#e4-herramientas)** — Reproducible builders, ARM / DSP emulators with tests through the real routes, `verify_builds.py`, remote diagnostics over USB (`ctremote.py`).
- **[E5 MIDI tables](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html#e5-tablas-midi)** — MIDI engine: CC 74/71/79/73/75/70/72/91/59/26/27/20/21/37/39/30/31/52/54 + NRPN 4:x; drums NRPN 5-8:1-12; Master FX NRPN 9:0-19 (channel 16).

<!-- FEATURES-EN:END -->

### License

[MIT](LICENSE) © 2026 Ghillermo, for the project's own work (tools, patches, documentation and manuals). It does not cover Novation's firmware (not included; you get it from Novation under its terms, as are the images built from it) nor third-party dependencies, which keep their licences ([`docs/DEPENDENCIAS.md`](docs/DEPENDENCIAS.md)): the patches in `tools/dsptool/` apply to dsp56300 (GPL-3.0) and a `dsptool` linked against it is GPL-3.0.

Circuit Tracks, Components and Novation are trademarks of Focusrite Audio Engineering Ltd. This project is not affiliated with them.
