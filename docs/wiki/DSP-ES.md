# DSP

*[English version](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/DSP) · [Inicio](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Home#en-español) · [Guía por vistas](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html)*

La parte de sonido del mod: los motores del sinte de las pistas MIDI, los controles nuevos de los drums y los efectos.

Las pistas **MIDI 1 / 2** tienen un sinte propio dentro del aparato, con varios motores en la fila de motores de su vista Preset: un
**oscilador** que pasa del seno al triángulo, la sierra (hasta una **supersaw** de siete sierras) y el pulso, con wavefold; **dos osciladores** con FM,
sync, ring y mezcla; un **VA-drum** para sonidos percusivos; un motor **granular** que toca granos de un sample o de la captura en directo; un motor
**FM de 4 operadores** con 16 algoritmos; y un **modo muestra** que toca los samples del pack a lo largo del teclado, en estéreo si quieres. Tiene un
filtro de varios tipos, envolventes, un LFO con siete formas (a tempo si quieres), una **matriz de modulación**, **polifonía** con ocho modos de voz y
ocho carriles de automatización. Los **drums** ganan envolventes, ring mod, LFO, modos de filtro, inicio y final del sample, ataque, bitcrush y tipos
de distorsión. **Master FX** añade efectos de directo a toda la mezcla, y las vistas **FX** y **Sidechain** dan acceso a la reverb, el delay, el
sidechain y el compresor master.

## Vista Preset de MIDI 1 / 2

*Cómo se llega:* Pulsa **MIDI 1** o **MIDI 2** y luego **Preset**. Además de las plantillas de stock, aquí vive el sinte propio de la pista.

- **Un sinte en cada pista MIDI** — MIDI 1 y 2 suenan en el propio aparato con su motor (entrada de línea procesada, oscilador, dos osciladores, VA-drum, granular, modo muestra; *(solo Beta 3.36)* FM) y siguen mandando MIDI.
- **Secuenciador de efectos** — un motor que no suena: dispara efectos de Master FX en los pasos que elijas.
- **Patches del sinte propio** *(desde RC2)* — 64 sonidos por pack para esos motores, a un toque.
- **Matriz de modulación** *(desde RC2.02)* — ocho fuentes (velocity, nota, azar, LFO 2, envolvente 2, golpe de un drum, posición del patrón, azar por pasos) que mueven cualquier parámetro del motor.
- **Patch flip** — cada nota manda un cambio de programa: el aparato externo cambia de sonido paso a paso.
- **Editor de CC** — cambia qué CC manda cada knob de la plantilla sin Components.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#midi-preset)

## Páginas de knobs del motor de MIDI 1 / 2

*Cómo se llega:* Con el motor encendido, los pads 1-5 de la vista Preset eligen qué hacen los 8 knobs; Shift da una segunda capa.

- **VCA-VCF** — volumen y filtro con su envolvente y su LFO; con Shift, el tipo de filtro y el tipo de efecto.
- **Osciladores** — una forma de onda continua de seno a cuadrada y un segundo oscilador con FM, ring y sync.
- **Granular** — convierte un sample en texturas: granos que lo leen en otra posición, velocidad o dirección para congelarlo, estirarlo o trocearlo.
- **Página 4** — los 8 parámetros que se graban como automatización (*(solo Beta 3.36)*: con Shift + knob, cualquiera de los 33; Record + paso = foto de los valores).

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#midi-knobs)

## FM de 4 operadores

*Cómo se llega:* *(solo Beta 3.36)* MIDI 1 / 2: vista Preset, un toque al **pad 27** y el **pad 24** de la fila de motores (violeta). El **pad 7** abre su página de knobs (violeta brillante en ella).

| Knob | Solo | Con Shift |
|---|---|---|
| K1-K4 | Ratio de los operadores 1-4: 0,5 … 16 (verde = entero, azul claro = y medio, verde azulado = inarmónico: 0,71, 1,41, 4,24). Cada ratio ocupa 5-6 clics: el primero es exacto y cada uno de los siguientes **desafina** +2,5 cents (hasta unos +12; LED a media luz) | Centro = ataque 0. **A la derecha:** el ataque del operador (0 … unos 3 s; azul claro). **A la izquierda:** el operador es **percusivo** con su propio decay, más corto cuanto más a la izquierda (3 ms … 8 s; rojo) |
| K5 | Nivel del operador 1 (naranja) | Algoritmo (16, 8 clics cada uno; el color de su familia) |
| K6 | Nivel del operador 2 | Feedback (magenta) |
| K7 | Nivel del operador 3 | Ruido (blanco) |
| K8 | Nivel del operador 4 | Release (azul) |

- **Elegir el algoritmo con los pads:** en la página FM, **mantén el pad 7**: los pads 9-24 enseñan los 16 algoritmos (el color de su familia; el actual brillante). **Pulsa uno**: queda elegido y suena la tónica mientras lo mantienes (**Shift + pad**: sin sonar). Al soltar el pad 7 vuelven los patches.
- **Al girar un ratio** (K1-K4) los pads 9-32 enseñan los 24 ratios durante 1,5 s (el actual brillante, en blanco si está desafinado); al girar el algoritmo (Shift + K5), los pads 9-24 enseñan los algoritmos. Mientras se ven, esos pads no cargan patches.
- **Es una variante del oscilador:** la nota, TUNE / FINE, la envolvente de pitch y el vibrato de la página 2 siguen valiendo; detrás, el filtro, el efecto y la matriz como con el oscilador. Una nota a la vez (la última manda); con el retrigger apagado (Shift + pad 29) una nota ligada no vuelve a disparar los ataques.
- **El volumen lo dan las envolventes de los operadores**: el VCA del motor se queda abierto (la velocity sigue dando el volumen) y la ADSR de la página 1 mueve el filtro, el tono y el brillo.
- **El brillo:** SHAPE (K2 de la página OSC 1), Env → forma (K4) y LFO → forma (K6) cambian cuánto modulan los moduladores (× 0,27 … × 3,7; SHAPE 50 = sin cambio), y también el feedback. Así la ADSR del motor, su LFO, la matriz, los carriles de la página 4 y el step-drummer mueven el timbre del FM.
- **La velocity** da también el brillo (cuánto, según el algoritmo) y cuánto cae el bombo. **Las notas agudas** modulan menos y caen antes (según el algoritmo, como en un DX7). En notas y ratios muy altos el motor limita la modulación para que no haya aliasing (salvo en los percusivos, donde forma parte del sonido).
- **El nivel** de un portador es su volumen; el de un modulador, cuánto modula.
- **Envolventes A/R con sustain fijo:** con la nota pulsada, un operador **sostenido** se queda arriba después de su ataque; uno **percusivo** (lo dice el algoritmo, o su Shift + knob a la izquierda) cae aunque la nota siga. Al soltar, todos caen con el release (uno percusivo por su knob, con lo más corto de su decay y el release). **El release es uno para todos y más largo cuanto más fuerte la nota**; el algoritmo lo acorta o alarga en cada operador.
- **El feedback** es como el del DX7 (la media de las dos últimas salidas): una sierra limpia en más recorrido; el knob es más fino abajo.
- Los algoritmos percusivos y de campana empiezan cada golpe con las fases a cero: todos los golpes suenan igual.
- **Ruido:** blanco, con la envolvente del operador que diga el algoritmo (el 1, salvo la caja), sumado después del FM, en cualquier algoritmo.
- **Clear + pad 7** = una **voz tocable del algoritmo elegido** (la columna «Voz» de la tabla); **Clear + knob** = su valor en esa voz (Clear + Shift + K5: la pila). **Clear + MIDI 1 / 2** = todo el motor a los valores iniciales (el FM, a la pila).
- **Se guarda con los patches del sinte propio** (con el motor en FM). Un patch de la Beta 3.22 o anterior se adapta al cargarlo (los ataques a la mitad derecha de su knob, el mismo feedback, los ratios exactos); una beta anterior carga uno nuevo con el FM apagado. No tiene CC / NRPN. Otro motor de la fila (o Shift + pad 27) lo apaga.

| # | Algoritmo | Familia | Voz (Clear + pad 7) |
|---|---|---|---|
| 1 | 4 → 3 → 2 → 1 (pila) | clásicos (blanco) | la inicial |
| 2 | 3 y 4 → 2 → 1 | | metales |
| 3 | 4 → 1 y 3 → 2 → 1 | | piano eléctrico |
| 4 | 4 → 3 → 1 y 2 → 1 | | bajo |
| 5 | dos pilas: 4 → 3 y 2 → 1 (portadores 1 y 3) | | piano eléctrico 2 |
| 6 | 4 → 1, 2 y 3 (tres portadores) | | pad |
| 7 | 4 → 3; 2 y 1 solos (tres portadores) | | clave |
| 8 | órgano: los cuatro portadores | | órgano (registros 16', 8', 4', 2 2/3') |
| 9 | bombo: 2 → 1; el 4 es la caída de pitch (su nivel = cuánto cae, hasta 3 octavas; su release = cuánto tarda) | percusivos (rojo) | bombo (unas 3 octavas de caída, rápida) |
| 10 | caja: 2 → 1 + ruido con la envolvente del 3; caída de pitch del 4 | | caja |
| 11 | metal / hi-hat: 2, 3 y 4 → 1 con ratios inarmónicos (× 1,41, 2,71, 3,49) | | hi-hat |
| 12 | tom / zap: 3 → 2 → 1; caída de pitch del 4 | | tom |
| 13 | campana: 2 → 1 y 4 → 3, ratios inarmónicos (× 3,5, × 2,76) | campanas (verde azulado) | campana |
| 14 | campana tubular: 2 y 3 → 1 (× 2,76, × 5,4), el 4 portador | | campana tubular |
| 15 | cuerdas: dos pilas (2 → 1, 4 → 3) desafinadas entre sí | cuerdas (verde) | cuerdas (ataque lento) |
| 16 | ensemble: 4 → 1, 2 y 3, tres portadores desafinados | | ensemble |

## Modo muestra y selector de samples

*Cómo se llega:* *(desde RC2)* MIDI 1 / 2 con el motor en **muestra** (pad 27 cian, tras el granular): **Note dos veces** (vista Note ampliada). La pista toca un sample del pack de un golpe, a la altura de cada nota.

- **Drums con altura en una pista MIDI** — cualquier sample del pack suena a la altura de cada nota, como en una caja de ritmos con samples afinables.
- **Un sample distinto por paso** — el sample flip cambia de sample paso a paso sin otra pista; se graba también en vivo.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#midi-muestra)

## Matriz de modulación

*Cómo se llega:* *(desde RC2.02)* MIDI 1 / 2 con el motor encendido: vista Preset, **pad 6**. Los 8 knobs pasan a ser 8 fuentes de modulación.

| Knob | Fuente | Con Shift |
|---|---|---|
| K1 | Velocity de la nota | — |
| K2 | Nota (C3 = 0; una octava = un cuarto del recorrido) | — |
| K3 | Azar: un valor nuevo en cada nota | — |
| K4 | LFO 2 | Forma × velocidad: triángulo (verde, la inicial), diente de sierra (magenta), cuadrada (rojo), sample & hold (blanco: escalones), sample & hold suavizado (violeta: deslizándose); los colores del LFO del motor; en cada forma, de 0,05 a 20 Hz ; *(solo Beta 3.36)*: en cada forma, la mitad izquierda de su tramo a tempo y la derecha libre (0.2) |
| K5 | Envolvente 2: ataque y caída desde cada nota | Ataque × caída: ataque 0 (blanco), corto (azul claro), medio (verde azulado), largo (azul); en cada uno, la caída de 20 ms a 4 s |
| K6 | Golpe de un drum: una caída desde cada golpe | Drum 1-4 (naranja, amarillo, violeta, verde azulado) × su caída |
| K7 | Posición en el patrón: de 0 en el primer paso al máximo en el último | — |
| K8 | Azar por pasos: un valor nuevo cada N pasos del secuenciador | N = 1, 2, 4, 8 o 16 pasos |

- **La posición del knob es el destino y la cantidad.** Del todo a la izquierda = apagado. Al girar a la derecha se pasa por **todos los parámetros de las páginas de knobs** (33: los de la página 1, luego los de la 2, la 3 y los de la 5 que no salen antes), cada uno con un tramo: dentro del tramo la cantidad crece de 1/16 a entera (*(solo Beta 3.36)*: de 0 a entera: el primer paso del tramo es el destino sin cantidad, con el LED tenue); al pasar al tramo siguiente cambia el destino y la cantidad vuelve a empezar.
- **Knobs lentos:** dos clics por paso, 16 pasos por destino.
- **El color del LED es el de la página del destino** (los colores de los pads 1-5: naranja VCA-VCF, verde OSC 1, verde azulado OSC 2), el **brillo** la cantidad; apagado = sin destino.
- **Mientras giras una fuente** (y 1,5 s después), los pads enseñan dónde vive su destino: el pad de su página brilla y los pads 9-16 / 17-24 son los K1-K8 / Shift + K1-K8 de esa página (tenues los que tienen un parámetro, brillante el destino). Mientras se ven, los pads 9-24 no cargan patches.
- **Cantidad entera** = la fuente entera recorre todo el rango del parámetro. Las fuentes bipolares (nota, azar, LFO 2, azar por pasos) suben y bajan; las demás solo suben. El valor guardado del parámetro no cambia: la matriz se suma al enviarlo.
- Varias fuentes pueden ir al mismo destino (se suman). TUNE se mueve en semitonos y FINE en fracciones; con el motor granular, sus rangos; en el modo muestra el parámetro del sample elige sample (de la captura al 64) y solo TUNE cambia la altura.
- **Clear + knob** = esa fuente apagada; **Clear + Shift + knob** = su parámetro al valor inicial; **Clear + pad 6** = todas apagadas.
- **Se guarda con los patches del sinte propio** (pads 9-24: Clear + pad dos veces, también al intercambiarlos o copiarlos entre packs); un patch guardado antes la carga apagada. *(solo Beta 3.36)* también **se guarda con el proyecto** (con el resto del sinte propio); antes no se guardaba con el proyecto ni al apagar el aparato. No tiene CC / NRPN.
- Las modulaciones llegan al motor unas 100-250 veces por segundo, repartidas entre todo lo que se mueve en la pista: varias fuentes rápidas a la vez se actualizan más despacio.

## Vista de la fuente del sinte

*Cómo se llega:* Con la vista de Synth 1 / 2 en pantalla, **pulsa su botón otra vez**. Cualquier botón la cierra.

- **Fuente del ruido** — cambia el ruido del patch por la entrada de audio 1 o 2 (normal o invertida): el filtro, las envolventes y los efectos del sinte procesan tu señal externa al ritmo de las notas.
- **Destinos de los macros** *(desde RC2)* — decide qué mueve cada macro knob (hasta 4 destinos por macro, con su tramo y su profundidad) sin pasar por Components.
- **Step-drummer del sinte** — secuencia los macros por pares de pasos: cada knob fija la posición de un macro en dos pasos del patrón.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#synth-fuente)

## Vista de pista de un drum (knobs)

*Cómo se llega:* Pulsa **Drum 1-4**. Cada knob hace lo que dice su etiqueta, con una segunda capa en Shift.

- **Moldear cada drum** — tono exacto, ring mod, ataque y decay, inicio y corte del sample, filtro con varios modos, LFO y distorsión de varios tipos: de un sample salen muchos sonidos.
- **Todo neutro = el original** — con los knobs nuevos en su punto neutro, el sample suena como en el Circuit original.
- **Volver a empezar** *(desde RC2)* — Clear + el botón del drum deja todos sus knobs por defecto.
- **Pareja estéreo** *(solo Beta 3.36)* — Drum 1 + Drum 2 (o 3 + 4) tocan un sample estéreo: el de la izquierda manda en los dos y el de la derecha solo matiza.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#drum-pista)

## Vista cromática y de escala de los drums

*Cómo se llega:* **Shift + Preset** con un drum elegido. Los pads tocan el sample transpuesto según la escala.

- **Un drum como teclado** — el sample transpuesto en la escala del proyecto.
- **Rollers** *(desde RC2)* — repite el drum en los micropasos que mantengas: redobles y ratchets en directo, también parado, y grabados con Record.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#drum-cromatica)

## Master FX

*Cómo se llega:* **Mixer** y **Mixer** otra vez. Efectos sobre la salida master, el song pointer, el sample capturado y la fila de efectos asignables. Cualquier otro botón de vista sale.

- **Efectos en directo sobre todo el master** — Gater, Auto-Filter, Digitise, Phaser, Glitch y gesto mecánico *(desde RC2)*: mientras mantienes o fijados.
- **Song pointer** — repite o hace bucle de partes del patrón en directo.
- **Captura** — graba hasta 3,5 s de lo que suena para tocarlo, ponerlo en un hueco o usarlo como drum.
- **Huecos** — un efecto con sus ajustes a un toque; el secuenciador de efectos los dispara.
- **Por proyecto** *(desde RC2)* — cada proyecto recuerda sus ajustes de Master FX.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#master-fx)

## Vista FX

*Cómo se llega:* Botón **FX**: envíos a reverb y delay por pista, como siempre, más:

- **La reverb y el delay desde el aparato** — tipo, decay, tiempo, feedback…, guardados con el proyecto.
- **Reset rápido** — Duplicate deja los envíos y los efectos a cero.
- **Resonancia del filtro master** — en Shift + Octave ▲ / ▼, de 16 en 16 *(solo Beta 3.36; en RC2.10, 1-16 / 17-32)*.
- **Filtro master apagado / encendido** — Shift + pad 25, sin perder su posición *(solo Beta 3.36)*.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#vista-fx)

## Vista Sidechain

*Cómo se llega:* **Shift + FX**. Los presets de sidechain de cada pista como siempre, más los knobs:

- **El sidechain con knobs** *(desde RC2)* — ataque, hold, decay y profundidad del ducking de cada pista, más allá de los presets.
- **Compresor master** *(desde RC2)* — su ataque y su release.
- **Sidechain entre drums** — que un drum baje el volumen de otro (el bombo al bajo, por ejemplo).
- **Disparado por patrones** *(desde RC2)* — Synth 1 / 2 o MIDI 1 / 2 como fuente: las notas de su patrón agachan otra pista, no solo los drums.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#sidechain)
