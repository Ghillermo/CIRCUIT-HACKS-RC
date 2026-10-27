# Vistas

*[English version](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Views) · [Inicio](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Home#en-español) · [Guía por vistas](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html)*

Cada vista del aparato y lo que ofrece. Cada una enlaza con su capítulo completo de la [guía por vistas](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html).

## Setup

### Vista Setup

*Cómo se llega:* Ábrela como en el original. Canales MIDI y opciones del aparato como siempre, más:

- **Canales compartidos (loopback interno)** — una pista MIDI toca un sinte o los drums del propio aparato.
- **Retornos por las tiras 3 / 4** — la reverb y el delay como canales del mixer.
- **Canales de Program Change** *(desde RC2)* — escucha y manda cambios de programa por canales propios.
- **Grabar los ruteos internos** *(desde RC2)* — lo que la pista MIDI toca en un sinte se graba también en él; *(solo Beta 3.37)* una pista silenciada en el Mixer no se graba (banco de acordes).

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#setup)

### Vista Advanced Setup

*Cómo se llega:* Ábrela como en el original. Además de sus ajustes de stock (compresor master, etc.):

- **MIDI Thru, Merge y Filter** *(desde RC2)* — el jack Thru puede mezclar el MIDI de entrada con el del aparato o filtrarlo.
- **Curva de velocity** *(solo Beta 3.37)* — K1 hace los pads más sensibles o más duros.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#advanced-setup)

## Sintes de stock (Synth 1 / 2)

### Vista de pista de Synth 1 / 2 (Note, Velocity, Gate)

*Cómo se llega:* Pulsa **Synth 1** o **Synth 2**. Los pads tocan el sinte como siempre.

- **Vista de la fuente** — el sinte puede procesar una entrada de audio en lugar de su ruido.
- **Teclado partido** *(desde RC2)* — arriba un sinte y abajo el otro, cada uno con su escala, octava y velocity; *(desde RC2.02)* con cualquier par de pistas de notas.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#synth-nota)

### Vista Scales y escala propia

*Cómo se llega:* Pulsa **Scales** como siempre (tónica y escala de stock); **Shift + Scales** para la escala propia.

- **Escala propia** *(desde RC2)* — hasta 7 notas sobre la tónica y un periodo libre (por ejemplo, una escala que se repite cada 7 semitonos). La usan los pads de las pistas de notas, el cuantizado y el random-mutate; se guarda con el proyecto.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#escalas)

### Vista de la fuente del sinte

*Cómo se llega:* Con la vista de Synth 1 / 2 en pantalla, **pulsa su botón otra vez**. Cualquier botón la cierra.

- **Fuente del ruido** — cambia el ruido del patch por la entrada de audio 1 o 2 (normal o invertida): el filtro, las envolventes y los efectos del sinte procesan tu señal externa al ritmo de las notas.
- **Destinos de los macros** *(desde RC2)* — decide qué mueve cada macro knob (hasta 4 destinos por macro, con su tramo y su profundidad) sin pasar por Components.
- **Step-drummer del sinte** — secuencia los macros por pares de pasos: cada knob fija la posición de un macro en dos pasos del patrón.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#synth-fuente)

### Vista Preset de Synth 1 / 2

*Cómo se llega:* Pulsa **Preset** con Synth 1 / 2 elegido. Los pads eligen patch como siempre (4 páginas, 128 patches del pack).

- **El modo de voz a la vista** *(desde RC2)* — los patches mono, mono con glide y poly se distinguen por el color.
- **Guardar el patch** *(desde RC2)* — guarda en el pack el sonido tal como lo has dejado (el original solo guarda patches desde Components).
- **Intercambiar y copiar** — reordena los patches del pack o lleva uno a otro pack.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#synth-preset)

## Pistas MIDI (MIDI 1 / 2)

### Vista Preset de MIDI 1 / 2

*Cómo se llega:* Pulsa **MIDI 1** o **MIDI 2** y luego **Preset** (*solo Beta 3.37*: o **MIDI 1 / MIDI 2 dos veces seguidas**). Además de las plantillas de stock, aquí vive el sinte propio de la pista.

- **Un sinte en cada pista MIDI** — MIDI 1 y 2 suenan en el propio aparato con su motor (entrada de línea procesada, oscilador, dos osciladores, VA-drum, granular, modo muestra; *(solo Beta 3.37)* FM) y siguen mandando MIDI.
- **Secuenciador de efectos** — un motor que no suena: dispara efectos de Master FX en los pasos que elijas.
- **Patches del sinte propio** *(desde RC2)* — 64 sonidos por pack para esos motores, a un toque.
- **Matriz de modulación** *(desde RC2.02)* — ocho fuentes (velocity, nota, azar, LFO 2, envolvente 2, golpe de un drum, posición del patrón, azar por pasos) que mueven cualquier parámetro del motor.
- **Patch flip** — cada nota manda un cambio de programa: el aparato externo cambia de sonido paso a paso.
- **Editor de CC** — cambia qué CC manda cada knob de la plantilla sin Components.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#midi-preset)

### Páginas de knobs del motor de MIDI 1 / 2

*Cómo se llega:* Con el motor encendido, los pads 1-5 de la vista Preset eligen qué hacen los 8 knobs; Shift da una segunda capa.

- **VCA-VCF** — volumen y filtro con su envolvente y su LFO; con Shift, el tipo de filtro y el tipo de efecto.
- **Osciladores** — una forma de onda continua de seno a cuadrada y un segundo oscilador con FM, ring y sync.
- **Granular** — convierte un sample en texturas: granos que lo leen en otra posición, velocidad o dirección para congelarlo, estirarlo o trocearlo.
- **Página 4** — los 8 parámetros que se graban como automatización (*(solo Beta 3.37)*: con Shift + knob, cualquiera de los 33; Record + paso = foto de los valores).

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#midi-knobs)

### Matriz de modulación

*Cómo se llega:* *(desde RC2.02)* MIDI 1 / 2 con el motor encendido: vista Preset, **pad 6**. Los 8 knobs pasan a ser 8 fuentes de modulación.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#midi-matriz)

### FM de 4 operadores

*Cómo se llega:* *(solo Beta 3.37)* MIDI 1 / 2: vista Preset, un toque al **pad 27** y el **pad 24** de la fila de motores (violeta). El **pad 7** abre su página de knobs (violeta brillante en ella).

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#midi-fm)

### Editor de CC de los macros MIDI (pad 25)

*Cómo se llega:* Vista Preset de MIDI 1 / 2, **pad 25**: cambia desde el aparato qué CC / NRPN manda cada macro knob de la plantilla.

- **Controlar otro aparato** — elige el número de CC (o NRPN) y el recorrido de cada knob de la plantilla, y guárdalo en ella.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#midi-cc)

### Vista del step-drummer

*Cómo se llega:* MIDI 1 / 2: vista Preset con el motor encendido, **pad 30** (*solo Beta 3.37*: con el step-drummer encendido, **Note** pasa por Note → Note ampliada → step-drummer). Synth 1 / 2: vista de la fuente, **pad 30**. Secuencia por pares de pasos sobre el patrón.

- **Parámetros por pares de pasos** — los 8 knobs son 8 pares de pasos del patrón: cada uno mueve un destino (tono, forma, FM, filtro…) solo en esos pasos, para melodías, acentos o cambios de timbre sin automatizar a mano.
- **El LED dice cuánto** *(desde RC2)* — tenue sin modulación, más brillante cuanto más se aleja.
- **Segunda página con destino propio** *(desde RC2)* — la página de velocity mueve otro destino a la vez.
- **Toggle pitch-vel** *(desde RC2)* — la página 1 transpone las notas por grados de la escala y la 2 marca su velocity: una melodía a partir de un solo patrón de notas.
- **En tiempo real** — con Record, tocar un paso lo graba.
- **Secuenciador de efectos** — con ese motor, cada par elige qué hueco de Master FX suena.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#step-drummer)

### Modo muestra y selector de samples

*Cómo se llega:* *(desde RC2)* MIDI 1 / 2 con el motor en **muestra** (pad 27 cian, tras el granular): **Note dos veces** (vista Note ampliada). La pista toca un sample del pack de un golpe, a la altura de cada nota.

- **Drums con altura en una pista MIDI** — cualquier sample del pack suena a la altura de cada nota, como en una caja de ritmos con samples afinables.
- **Un sample distinto por paso** — el sample flip cambia de sample paso a paso sin otra pista; se graba también en vivo.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#midi-muestra)

## Pattern Settings

### Vista Pattern Settings

*Cómo se llega:* Botón **Pattern Settings** con una pista elegida: primer / último paso, sync rate y dirección como siempre, más los pads 25-28 y el arpegiador (Shift).

- **Nudge** — rota el patrón para que empiece en otro paso.
- **Órdenes fractal y deconstruido** — recorren el patrón de otra forma sin cambiar sus notas.
- **Arpegiador** *(desde RC2)* — los acordes del patrón (y los que tocas) suenan nota a nota, con su orden y su resolución; en los drums, saltando de sample.
- **Dinámicas y random-mutate** (pad 25) — variaciones para que el patrón no suene siempre igual.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#pattern-settings)

### Vista Micro Step (pistas de notas)

*Cómo se llega:* Pulsa **Gate dos veces** con una pista de notas elegida (Synth 1 / 2, MIDI 1 / 2).

- **Micropasos y Tie (de stock)** — coloca cada nota fuera de la rejilla y enlázala con el paso siguiente.
- **Gate por pulsación** *(desde RC2)* — al introducir notas a mano, lo que mantienes es lo que dura la nota.
- **Longitud fija** *(desde RC2)* — todas las notas que introduces a mano con la misma duración.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#micropasos)

### Vista de probabilidad (pistas de notas y drums)

*Cómo se llega:* **Shift + Pattern Settings** (modo de stock), **Pattern Settings dos veces** (modo 1) o el **pad 25** de Pattern Settings (modo 2). Mantén un paso con notas y toca un pad de las filas 3-4.

- **Probabilidad (de stock)** — que un paso suene solo a veces.
- **Frecuencia** *(desde RC2)* — que un paso suene una de cada n vueltas: variaciones que vuelven cada 2, 4 u 8 vueltas.
- **Dinámicas** *(desde RC2)* — pequeñas variaciones de velocity y de posición: un patrón más humano.
- **Random-mutate** *(desde RC2)* — notas que saltan de octava o a otra nota de la escala; en los drums, a otro sample.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#probabilidad)

## Drums

### Vista de pista de un drum (knobs)

*Cómo se llega:* Pulsa **Drum 1-4**. Cada knob hace lo que dice su etiqueta, con una segunda capa en Shift.

- **Moldear cada drum** — tono exacto, ring mod, ataque y decay, inicio y corte del sample, filtro con varios modos, LFO y distorsión de varios tipos: de un sample salen muchos sonidos.
- **Todo neutro = el original** — con los knobs nuevos en su punto neutro, el sample suena como en el Circuit original.
- **Volver a empezar** *(desde RC2)* — Clear + el botón del drum deja todos sus knobs por defecto.
- **Pareja estéreo** *(solo Beta 3.37)* — Drum 1 + Drum 2 (o 3 + 4) tocan un sample estéreo: el de la izquierda manda en los dos y el de la derecha solo matiza.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#drum-pista)

### Vista Preset de drums

*Cómo se llega:* Pulsa **Preset** con un drum elegido. Los pads eligen el sample como siempre (Shift + pad = elegir sin que suene).

- **La captura como drum** — graba lo que suena (Master FX) y úsalo como sample de un drum; al guardar el proyecto queda en el pack.
- **Intercambiar y copiar samples** — reordena los samples o trae uno de otro pack.
- **Arpegio de samples** *(desde RC2)* — al mantener varios samples, el drum salta de uno a otro.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#drum-preset)

### Vista cromática y de escala de los drums

*Cómo se llega:* **Shift + Preset** con un drum elegido. Los pads tocan el sample transpuesto según la escala.

- **Un drum como teclado** — el sample transpuesto en la escala del proyecto.
- **Rollers** *(desde RC2)* — repite el drum en los micropasos que mantengas: redobles y ratchets en directo, también parado, y grabados con Record.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#drum-cromatica)

## Master FX

### Master FX

*Cómo se llega:* **Mixer** y **Mixer** otra vez. Efectos sobre la salida master, el song pointer, el sample capturado y la fila de efectos asignables. Cualquier otro botón de vista sale.

- **Efectos en directo sobre todo el master** — Gater, Auto-Filter, Digitise, Phaser, Glitch y gesto mecánico *(desde RC2)*: mientras mantienes o fijados.
- **Song pointer** — repite o hace bucle de partes del patrón en directo.
- **Captura** — graba hasta 3,5 s de lo que suena para tocarlo, ponerlo en un hueco o usarlo como drum.
- **Huecos** — un efecto con sus ajustes a un toque; el secuenciador de efectos los dispara.
- **Por proyecto** *(desde RC2)* — cada proyecto recuerda sus ajustes de Master FX.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#master-fx)

## FX

### Vista FX

*Cómo se llega:* Botón **FX**: envíos a reverb y delay por pista, como siempre, más:

- **La reverb y el delay desde el aparato** — tipo, decay, tiempo, feedback…, guardados con el proyecto.
- **Reset rápido** — Duplicate deja los envíos y los efectos a cero.
- **Resonancia del filtro master** — en Shift + Octave ▲ / ▼, de 16 en 16 *(solo Beta 3.37; en RC2.10, 1-16 / 17-32)*.
- **Filtro master apagado / encendido** — Shift + pad 25, sin perder su posición *(solo Beta 3.37)*.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#vista-fx)

## Sidechain

### Vista Sidechain

*Cómo se llega:* **Shift + FX**. Los presets de sidechain de cada pista como siempre, más los knobs:

- **El sidechain con knobs** *(desde RC2)* — ataque, hold, decay y profundidad del ducking de cada pista, más allá de los presets.
- **Compresor master** *(desde RC2)* — su ataque y su release.
- **Sidechain entre drums** — que un drum baje el volumen de otro (el bombo al bajo, por ejemplo).
- **Disparado por patrones** *(desde RC2)* — Synth 1 / 2 o MIDI 1 / 2 como fuente: las notas de su patrón agachan otra pista, no solo los drums.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#sidechain)

## Escenas y patterns

### Vista Patterns y cadenas de patrones

*Cómo se llega:* Botón **Patterns**. Columnas = pistas, filas = patrones. Con el **modo cadena** *(desde RC2)*, cada patrón puede llevar una regla «suena n veces, salta a B; la vez siguiente, a C».

- **Cadenas de patrones** *(desde RC2)* — un patrón suena n veces y salta a otro, y la vez siguiente a un tercero: estructuras A A A B sin encadenar a mano.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#patterns)

### Vista Mixer y escenas

*Cómo se llega:* Botón **Mixer**: niveles (Octave ▲) y panorama (Octave ▼) como siempre; **Mixer otra vez** = Master FX.

- **Nivel a 100 o a 0** — Shift + knob deja una pista a su nivel nominal o en silencio de un gesto.
- **Escenas con cadenas y repeticiones** *(desde RC2)* — una escena puede repetirse n veces y recordar el modo cadena.
- **Entradas y salidas al compás** *(desde RC2)* — Shift + pad de pista silencia o activa la pista justo al empezar el compás siguiente.
- **Modo cue** *(desde RC2)* — la mezcla en mono por la izquierda y, por la derecha, las pistas que quieras escuchar antes de meterlas.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#mixer)

## Projects y packs

### Vista Projects

*Cómo se llega:* Botón **Projects**: cargar y guardar proyectos como siempre, más copiar.

- **Copiar proyectos** *(desde RC2)* — duplica un proyecto en otro hueco o en otro pack.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#projects)

### Vista de packs

*Cómo se llega:* **Shift + Projects**. Cargar packs como siempre, más borrar.

- **Borrar packs** — libera huecos de pack desde el aparato.
- **Memoria interna protegida** — el mod nunca escribe en el pack interno.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#packs)
