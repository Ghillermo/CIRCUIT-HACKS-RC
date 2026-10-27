# Datos

*[English version](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Data) · [Inicio](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Home#en-español) · [Guía por vistas](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html)*

Qué se guarda y dónde, cómo asegurarte de que se guarda y qué se pierde al apagar.

## Qué guarda un patrón y cómo asegurarte de que se guarda

Cada pista tiene 8 patrones por proyecto. Lo que está en un patrón viaja con él (Duplicate, cadenas, escenas) y llega a la tarjeta al **guardar el proyecto**.

### Lo que lleva cada patrón
| Qué | Pistas | Cómo se pone |
|---|---|---|
| Notas, velocity, gate, micropasos y probabilidad de cada paso | todas | Como en el original |
| Automatización de los knobs: macros de Synth 1 / 2, knobs de la plantilla MIDI, knobs de stock de los drums, nivel y panorama del Mixer, envíos de reverb / delay | todas | Como en el original: **Record** y girar, o mantener un paso y girar |
| Sample flips | drums | Como en el original |
| Primer y último paso, sync rate y dirección | todas | Pattern Settings, como en el original |
| **Random-mutate, frecuencia y dinámicas** de cada paso *(desde RC2)* | todas | [Vista de probabilidad](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#probabilidad) |
| **Orden fractal / deconstruido** y **regla de cadena** (n vueltas, salto a B / C) *(desde RC2)* | todas | [Pattern Settings](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#pattern-settings), [Patterns](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#patterns) |
| **Paso que suelta la automatización** *(solo Beta 3.37)* | Synth 1 / 2, MIDI 1 / 2 | Vista Velocity, Shift + pad de paso ([vista de pista](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#synth-nota)) |
| **Carriles del sinte propio** (los 8 de la página 4) *(desde RC2)*; *(solo Beta 3.37)* la **foto** de Record + paso | MIDI 1 / 2 | Record y girar ([páginas de knobs](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#midi-knobs)) |
| **Notas del step-drummer**: en carriles de automatización (MIDI 1 / 2: el del tono y, para su página 2, el de Release; Synth 1 / 2: el de su macro) | Synth, MIDI | [Step-drummer](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#step-drummer) |
| **Valores del secuenciador de efectos** | MIDI 1 / 2 | [Step-drummer](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#step-drummer) |
| **Sample flips del modo muestra** (en el carril de nivel de la pista) *(desde RC2)* | MIDI 1 / 2 | [Selector de samples](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#midi-muestra) |
| **Pasos cromáticos de los drums** (en el carril de pitch del drum) *(desde RC2)* | drums | [Vista cromática](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#drum-cromatica) con Record |
| Golpes de los **rollers** y del **arpegio de drums** | drums | Con Record, como golpes normales |
| *(solo Beta 3.37)* La **copia del sinte propio** de MIDI 1 / 2 (en los ajustes de los patrones 1-5, sin cambiar lo que suenan) | MIDI 1 / 2 | Sola, al guardar el proyecto |

- **No están en el patrón** aunque se elijan con él en pantalla: el **arpegiador** (encendido, orden y resolución) y el **gate por pulsación** se guardan en el **proyecto** por pista (el arpegiador, por pista y número de patrón: **no se copia al duplicar el patrón**).
- **Duplicar un patrón** copia todo lo de la tabla. **Clear + patrón** en la vista Patterns (fuera del modo cadena) lo borra con su regla y su orden.

### Cómo asegurarte de que se guarda
1. **Un knob girado sin Record** cambia el sonido de todo el proyecto (el patch, los knobs de drums, el Mixer…), no el patrón. Para que cambie **en un paso o a lo largo del patrón**, grábalo: **Record** con el secuenciador en marcha, o **mantén un paso y gira** (como en el original).
2. **Guarda el proyecto: Save dos veces** (el primer toque parpadea en blanco; el segundo, verde rápido). Se guarda en el último hueco usado; para otro hueco, en la vista Projects: **Save + el pad del hueco** (como en el original). Todo lo marcado «proyecto» o «patrón» en esta guía solo llega a la tarjeta así.
3. **Cargar otro proyecto o apagar sin guardar** pierde los cambios desde el último Save (como en el original). Al encender se carga el último proyecto usado, tal como se guardó.
4. **Save apagado siempre** = **Save Lock** activado (Shift + Save al encender, función del original): repite el gesto para quitarlo.
5. **El sinte propio de MIDI 1 / 2** guarda sus valores **en los ajustes del aparato** (iguales para todos los proyectos): *(solo Beta 3.37)* también **con el proyecto** al guardarlo. Para conservar un sonido entre proyectos o packs, **guárdalo como patch** ([vista Preset de MIDI 1 / 2](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#midi-preset), Clear + pad dos veces). Para que cambie dentro del patrón, usa la página 4 (carriles) o el step-drummer.
6. **Un patch de Synth 1 / 2** tal como suena (knobs, destinos de macro editados, MIDI recibido) va con el proyecto; para tenerlo en el pack y usarlo en otros proyectos, **guárdalo** en la [vista Preset](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#synth-preset) (Clear + pad dos veces) *(desde RC2)*.
7. **Antes de apagar:** para el secuenciador y espera **2 s** sin tocar el motor de MIDI 1 / 2 (sus ajustes se escriben en la tarjeta solo con el transporte parado, para no cortar el audio), y apaga con el **botón de encendido**.
8. **Sin tarjeta (pack de la memoria interna)** y con las versiones **S**, el mod no escribe nada propio: patches, samples y copias no se guardan (el LED de Save se pone rojo). Los proyectos, sí, como en el original.

## Qué vuelve tras reiniciar y dónde se guarda

Cinco sitios: el **patrón**, el **proyecto** (los dos, al guardar el proyecto), el **pack** (al momento, en la tarjeta), los **ajustes del aparato** (solos, para todos los proyectos) y ninguno (se pierde al apagar).

### El proyecto (Save dos veces)
| Qué | Dónde se usa |
|---|---|
| Como en el original: los patches de Synth 1 / 2 tal como suenan, los samples elegidos y knobs de los drums, Mixer, envíos y parámetros de reverb / delay, sidechain, escenas y cadenas, tempo, swing, escala y tónica | — |
| **Knobs nuevos de los drums**: envolvente, ring mod, LFO, filtro y su modo, inicio, corte, ataque, bitcrush, tipo de distorsión; el semitono de la vista cromática | [Drums](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#drum-pista) |
| **Fuente del ruido** de Synth 1 / 2 (entradas de audio) | [Vista de la fuente](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#synth-fuente) |
| **Master FX**: los 20 knobs, los efectos asignados a los huecos, ataque / release del compresor | [Master FX](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#master-fx), [Sidechain](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#sidechain) |
| **Sidechain**: Synth 1 / 2 y MIDI 1 / 2 como fuente; K1-K4 de las páginas de drums | [Sidechain](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#sidechain) |
| **Modo cadena** (y en cada escena), **repeticiones de escena**, envíos del **modo cue** | [Patterns](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#patterns), [Mixer](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#mixer) |
| **Cuenta atrás** (el metrónomo, como en el original, no se guarda) | [Botones](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#botones) |
| **Arpegiador** de notas y de drums (por pista y patrón), **gate por pulsación**, **longitud fija** | [Pattern Settings](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#pattern-settings), [Micro Step](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#micropasos) |
| **Escala propia** y *(solo Beta 3.37)* **Jankó** | [Scales](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#escalas) |
| Sinte propio de MIDI 1 / 2: **gate retrigger**, **forma del LFO**, el toggle pitch-vel y el destino de la página 2 del step-drummer | [Páginas de knobs](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#midi-knobs), [Step-drummer](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#step-drummer) |
| *(solo Beta 3.37)* **Parejas estéreo de drums**: encendidas, distancia, apertura y desviaciones | [Drums](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#drum-pista) |
| *(solo Beta 3.37)* **El sinte propio entero** de MIDI 1 / 2: motor, valores, matriz, destinos de la página 4, FM, modo de voz, estéreo (al cargar un proyecto que lo lleva manda el del proyecto; uno anterior deja el sonido como estaba) | [Vista Preset de MIDI](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#midi-preset) |

### El pack (se escribe en la tarjeta al hacer el gesto)
| Qué | Dónde se usa |
|---|---|
| **Patches de Synth 1 / 2 guardados** *(desde RC2)* (Clear + pad dos veces); intercambios y copias entre packs | [Vista Preset de Synth](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#synth-preset) |
| **Patches del sinte propio** de MIDI 1 / 2 (64 por pack, comunes a las dos pistas: motor, valores, step-drummer, *(desde RC2.02)* matriz, *(solo Beta 3.37)* FM, destinos de la página 4, modo de voz) | [Vista Preset de MIDI](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#midi-preset) |
| **Samples**: intercambios, copias entre packs y la **captura** que sustituye a un drum (esta, al guardar el proyecto, si cabe) | [Vista Preset de drums](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#drum-preset) |
| **Proyectos copiados** a otro hueco o pack; **packs borrados** | [Projects](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#projects), [Packs](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#packs) |

### Los ajustes del aparato (solos, para todos los proyectos)
| Qué | Dónde se usa |
|---|---|
| Como en el original: canales, filtros de CC / notas / Program Change, reloj, compresor master encendido, brillo, Save Lock | [Setup](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#setup), [Advanced Setup](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#advanced-setup) |
| **Motor de MIDI 1 / 2**: motor elegido, todos sus valores, osciladores y orden (pads 28 / 29), step-drummer encendido y su destino, secuenciador de efectos, patch flip | [Vista Preset de MIDI](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#midi-preset) |
| **Modo del jack MIDI Thru** (Thru, Out 2, Merge, Filter), **canales de Program Change** del proyecto, **modo cue** | [Advanced Setup](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#advanced-setup), [Setup](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#setup), [Mixer](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#mixer) |
| *(solo Beta 3.37)* **Modo General MIDI** de los drums y sus notas; **fusión USB**; **teclado externo al arpegiador**; **curva de velocity** de los pads | [Setup](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#setup), [Advanced Setup](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#advanced-setup) |

## Qué se pierde al reiniciar

Lo que no está en ninguna de las tablas anteriores vive solo en la memoria y desaparece al apagar (o al instalar otra versión).

| Qué | Al encender |
|---|---|
| **Todo lo cambiado desde el último Save** del proyecto (como en el original) | Vuelve el proyecto tal como se guardó |
| **Filtro master** y su **resonancia** (como en el original); *(solo Beta 3.37)* el filtro master apagado con Shift + pad 25 | En sus valores iniciales; el filtro, encendido |
| **Metrónomo** encendido / apagado y **View Lock** (como en el original) | Apagados |
| **Efectos fijados**, **song pointer** y sample fijado de Master FX | Apagados; el song pointer, a 0 |
| **Record de la vista Setup** (grabar los ruteos internos) | Apagado |
| En la vista Sidechain, los **disparos de un drum** por otro drum o por un patrón (pads de las páginas de drums) | Los del preset del drum |
| **Mutes en el compás siguiente** pendientes (Mixer, Shift + pad) | — |
| **Notas en latch** (Shift + tecla), **pantalla de acordes** (tipo y modificadores) y el medio tono de **Octave con Jankó** *(solo Beta 3.37)* | Sin latch; los de fábrica; Octave a 0 |
| **Teclado partido** y vistas abiertas (step-drummer, editor de macros, selector) | Cerrados |
| Un **sample o patch esperando** a copiarse en otro pack (Duplicate + A) | Nada esperando |
| La **captura** de Master FX sin usar, o usada en un drum sin guardar el proyecto | Vacía; el drum, con su sample del pack |
| **Matriz de modulación** del sinte propio sin guardar en un patch *(desde RC2.02)* (*(solo Beta 3.37)*: guardada también con el proyecto) | Apagada |
| Los contadores de vueltas de la **frecuencia** y del orden **fractal** (se reinician al parar) | Desde la primera vuelta |

- **Instalar otra versión** reinicia el aparato: lo que no se guardó se pierde; el proyecto, el pack y los ajustes se quedan.
- **Volver al firmware oficial:** los proyectos y packs guardados con el mod se abren en el original; lo propio del mod va en partes de los ficheros que el original no usa, y el original no lo lee.
