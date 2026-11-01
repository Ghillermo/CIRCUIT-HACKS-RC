# Pistas MIDI y modos de voz

## Resumen

MIDI 1 y MIDI 2 son dos sintes completos dentro del Circuit Tracks: cada pista sigue mandando MIDI y además suena con un motor propio, de hasta 4 voces (6 en FM). El **modo de voz** decide cómo se reparten las notas entre esas voces: ocho modos en el pad 32 de la vista Preset.

Este documento describe la **Beta 5.4**, publicada el 1 de noviembre de 2026 y sin probar en el aparato. Casi todo está ya en RC4 y RC4.02; lo que solo está en la beta se marca *(solo Beta 5.4)*.

El modo de voz no tiene CC ni NRPN: se elige en el aparato y se guarda con el patch y con el proyecto.

## Diagrama de bloques

Una nota sigue dos caminos: sale por MIDI y, con el motor encendido, entra en el modo de voz. El MIDI de entrada solo toma el segundo camino.

<!--fig:ruta-->

La modulación actúa sobre los parámetros del motor, no sobre la nota. Con patch flip activo no hay motor: la nota sale como Program Change.

## Vistas y menús

La vista Preset es el centro de la pista: ahí se eligen el motor, el modo de voz, el patch y la página de knobs. Las demás vistas tratan el patrón.

<!--fig:mapa-->

El step-drummer aparece dos veces porque se llega por dos caminos: el pad 30 de Preset o repetir Note cuando ya está encendido.

### Vistas

| Vista | Cómo se llega | Para qué sirve |
| --- | --- | --- |
| Note | Botón MIDI 1 / 2 | Tocar y escribir notas. Shift + tecla = latch. |
| Note ampliada | Note dos veces | Teclado grande y pantalla de acordes (Shift + pad 8). Con el motor en muestra, selector de samples. |
| Preset | Preset, MIDI 1 / 2 otra vez con Note en pantalla, o Shift + MIDI 1 / 2 | Motor, modo de voz, patches, páginas de knobs. Sin motor, plantillas de stock. |
| Step-drummer | Pad 30 de Preset, o Note repetido con el step-drummer encendido | Parámetros por pares de pasos. |
| Editor de CC | Pad 25 de Preset, con el motor apagado | Qué CC o NRPN manda cada macro de la plantilla. |
| Velocity | Botón Velocity | Velocity por paso. Con Shift, soltar la automatización de un paso. Dos veces = velocity fija. |
| Gate | Botón Gate | Duración de las notas. |
| Micro Step | Gate dos veces | Micropasos y Tie. Pad 31 = longitud fija, pad 32 = gate por pulsación. |
| Pattern Settings | Botón Pattern Settings | Primer y último paso, sync rate, dirección, Nudge, órdenes y arpegiador. |
| Probabilidad | Shift + Pattern Settings (stock), Pattern Settings dos veces (modo 1) o pad 25 de Pattern Settings (modo 2) | Probabilidad, frecuencia, dinámicas y random-mutate. |
| Teclado partido | Mantener una pista de notas y pulsar otra | Dos pistas en los pads, cada una con su escala, octava y velocity. |

### Pads de la vista Preset

| Pad | Función |
| --- | --- |
| 1-5 | Página de knobs: 1 VCA-VCF, 2 OSC 1 (o granular), 3 OSC 2, 4 knobs secuenciables, 5 modulación. Shift + pad 4 = knobs no secuenciables. Un toque deja la página; mantener ½ s la enseña solo mientras lo mantienes. |
| 6 | Matriz de modulación. |
| 7 | Página FM. Mantenerlo enseña los 16 algoritmos en los pads 9-24. |
| 8 | Con FM: un toque abre la página FM; mantenerlo enseña los 16 sonidos de partida. |
| 9-24 | Patches del sinte propio: 16 huecos por página, 8 páginas con Octave. |
| 25 | Editor de CC. Apagado y sin efecto con el motor encendido. |
| 26 | Patch flip: cada nota sale como Program Change. Excluyente con el motor. |
| 27 | Abre la fila de motores. Shift + pad 27 pasa al motor siguiente. |
| 28 | Uno o dos osciladores (oscilador y VA-drum). |
| 29 | Orden de la cadena. Shift + pad 29 pasa por los ocho modos de voz. |
| 30 | Abre el step-drummer. Shift + pad 30 lo desactiva. |
| 31 | Solo VA-drum: la velocity escala las envolventes de pitch y filtro. |
| 32 | Abre el menú de modos de voz, en el color del modo actual. |

### Menús sobre los pads

Un menú ocupa los pads 9-24 mientras está abierto; esos pads dejan de cargar patches.

| Menú | Abrir | Contenido | Cerrar |
| --- | --- | --- | --- |
| Fila de motores | Toque en pad 27 | Pads 17-24: apagado, línea, oscilador, VA-drum, granular, muestra, secuenciador de efectos, FM. Pads 9-16: a qué pista apunta el secuenciador de saltos *(solo Beta 5.4)* | Pad 27 otra vez. Elegir no la cierra. |
| Modos de voz | Toque en pad 32 | Pads 17-24: los ocho modos. K1 = glide, K2 = desafinación del unísono | Pad 32 otra vez, o salir de la vista |
| Algoritmos FM | Mantener pad 7 | Pads 9-24: los 16 algoritmos | Soltar el pad 7 |
| Sonidos de partida | Mantener pad 8 con FM | Pads 9-24: 16 instrumentos | Soltar el pad 8 |
| Destino de la matriz | Girar una fuente de la página 6 | Pad de la página del destino y sus knobs en los pads 9-24 | Solo, 1,5 s después |
| Ratios FM | Girar K1-K4 en la página FM | Pads 9-32: los 24 ratios | Solo, 1,5 s después |

### Gestos con Clear, Shift y Duplicate

| Gesto | Efecto |
| --- | --- |
| Clear + botón de la pista | Valores del motor a los iniciales, y suelta las notas en latch. El motor elegido se queda. |
| Clear + pad 1-5 | Esa página a sus valores iniciales. |
| Clear + knob | A la derecha, valor por defecto (lavanda). A la izquierda, borra su automatización (rojo). |
| Shift + Preset | Vuelve el sinte propio guardado con el proyecto. *(solo Beta 5.4)* |
| Clear + pad de patch, dos veces | Guarda el patch en ese hueco. |
| Duplicate + A + B | Intercambia dos patches. Con otro pack cargado entre medias, copia. |
| Shift + pad de patch | Carga el patch sin que suene la tónica. |

## Motores

Cada pista tiene un motor de siete, más apagado, y la pista sigue mandando su MIDI con cualquiera. Se elige en la fila que abre el pad 27.

| Pad de la fila | Color | Motor | Qué suena | Voces máximas |
| --- | --- | --- | --- | --- |
| 17 | Blanco | Apagado | Nada propio: la pista es MIDI de stock, con plantillas | — |
| 18 | Ámbar | Entrada de línea | La línea 1 (MIDI 1) o 2 (MIDI 2) pasa por el VCA-VCF; las notas lo disparan | 1 |
| 19 | Verde | Oscilador | Morph seno, triángulo, sierra, cuadrada; segundo oscilador con el pad 28 | 4 |
| 20 | Naranja | VA-drum | Percusión sintética: VCA de un disparo, decays de pitch y filtro, ruido | 4 |
| 21 | Magenta | Granular | Hasta 16 granos de un sample del pack o de la captura | 1 |
| 22 | Verde azulado | Muestra | Un sample del pack a la altura de la nota, de un golpe | 4 |
| 23 | Azul | Secuenciador de efectos | No suena: dispara huecos de Master FX | — |
| 24 | Violeta | FM | 4 operadores y 16 algoritmos; variante del oscilador | 6, o 3 + 3 |

### Oscilador

WAVE (K7 de la página 2) es una posición continua entre formas: 0 seno, 42 triángulo, 84 sierra, 126 cuadrada. SHAPE (K2) actúa distinto en cada forma; entre dos formas actúa sobre las dos.

| Forma | SHAPE a la izquierda del centro | SHAPE a la derecha del centro |
| --- | --- | --- |
| Seno | Nada | Wavefold: amplifica hasta unas 8 veces y pliega. Menos en notas agudas |
| Triángulo | Rampas exponenciales | Wavefold |
| Sierra | Todo el recorrido: de sierra normal a supersaw de 7 sierras | Hasta la supersaw entera |
| Cuadrada | Pulso más estrecho, hasta un 3 % | Pulso más estrecho por el otro lado, hasta un 97 % |

La sierra, la supersaw y el pulso usan PolyBLEP, con unos 40 dB menos de aliasing en notas agudas. Con el pad 28, el OSC 2 modula al OSC 1 con FM, ring, sync y modos bit a bit. Dos notas a la vez = parafonía en los modos mono con dos osciladores.

### VA-drum

El knob Sustain es el decay de pitch y el knob Release el decay de filtro. La velocidad del LFO da el nivel de ruido, y el LFO se sustituye por valores aleatorios. En poly cada golpe lleva su envolvente de tono, de volumen y su ruido: un golpe nuevo no corta los anteriores.

### Granular

El modo de nota (Shift + K6 de la página 2) cambia lo que hacen las notas.

| Modo de nota | Qué hacen las notas |
| --- | --- |
| Tono | Cambian la altura de los granos |
| Slicer | El sample se parte en 16 trozos y cada nota toca uno, desde la nota 36 |
| Stretch | Cambian la altura; el tramo desde K2 dura K3 pasos (1-64) a cualquier tempo |

Con Shift + K4 por encima de 0, cada grano sale a un lado al azar. El panorama de la pista decide la proporción. La fuente (Shift + K8) es la captura o el sample de un drum.

### Muestra

C3 (nota 60) es el sample como se grabó; una octava arriba, el doble de rápido. El VCA se queda abierto y el sample suena hasta el final. Los samples se eligen en la vista Note ampliada, con un sample distinto por paso (sample flip).

K7 de la página 2 es la anchura estéreo: cada nota toca el sample elegido a la izquierda y un segundo a la derecha. Shift + el sample elegido pasa a elegir el segundo. La nota dura lo que el más largo.

### FM

El volumen lo dan las envolventes de los operadores: el VCA queda abierto y la ADSR de la página 1 mueve filtro, tono y brillo. SHAPE, Env → forma y LFO → forma cambian cuánto modulan los moduladores (× 0,27 a × 3,7), así que todo lo que mueve esos valores mueve el timbre.

Cada operador es sostenido o percusivo: Shift + K1-K4 a la derecha da ataque, a la izquierda decay propio. El release es uno para todos y más largo cuanto más fuerte la nota.

| # | Algoritmo | Familia | Voz con Clear + pad 7 |
| --- | --- | --- | --- |
| 1 | 4 → 3 → 2 → 1 (pila) | Clásicos | La inicial |
| 2 | 3 y 4 → 2 → 1 | Clásicos | Metales |
| 3 | 4 → 1 y 3 → 2 → 1 | Clásicos | Piano eléctrico |
| 4 | 4 → 3 → 1 y 2 → 1 | Clásicos | Bajo |
| 5 | Dos pilas: 4 → 3 y 2 → 1 | Clásicos | Piano eléctrico 2 |
| 6 | 4 → 1, 2 y 3 | Clásicos | Pad |
| 7 | 4 → 3; 2 y 1 solos | Clásicos | Clave |
| 8 | Cuatro portadores | Clásicos | Órgano |
| 9 | Bombo: 2 → 1, caída de pitch del 4 | Percusivos | Bombo |
| 10 | Caja: 2 → 1 + ruido, caída de pitch del 4 | Percusivos | Caja |
| 11 | Metal: 2, 3 y 4 → 1, ratios inarmónicos | Percusivos | Hi-hat |
| 12 | Tom: 3 → 2 → 1, caída de pitch del 4 | Percusivos | Tom |
| 13 | Campana: 2 → 1 y 4 → 3 | Campanas | Campana |
| 14 | Campana tubular: 2 y 3 → 1, el 4 portador | Campanas | Campana tubular |
| 15 | Cuerdas: dos pilas desafinadas | Cuerdas | Cuerdas |
| 16 | Ensemble: 4 → 1, 2 y 3 desafinados | Cuerdas | Ensemble |

Los sonidos de partida (pad 8 mantenido): piano, piano eléctrico, órgano, pluck, arpa, marimba, bajo, campana, cuerdas, pad, flauta, clarinete, metales, bombo, caja y hi-hat.

## Modos de voz

Hay ocho modos, combinación de dos decisiones: cuántas voces suenan y qué hace una nota nueva con otras teclas pulsadas. Un proyecto que nunca eligió modo empieza en poly.

| Voces | Redispara | No redispara | Se desliza | Se desliza siempre |
| --- | --- | --- | --- | --- |
| Una voz | Retrigger (17) | Legato (18) | Glide (19) | — |
| Todas en la misma nota | Uni retrig (20) | Uni legato (21) | Uni glide (22) | Uni always-glide (23) |
| Una voz por nota | Poly (24) | — | — | — |

El número es el pad del menú. Los modos que se llaman igual comparten color: redisparo verde, legato amarillo, glide verde azulado. Uni always-glide es violeta y poly magenta.

<!--fig:modos-->

El modo reparte las notas entre las voces; después, el nivel de cada voz baja según cuántas suenan y todas pasan por el filtro y el efecto de la pista.

### Cómo se elige

Con el motor encendido, un toque al pad 32 abre el menú en los pads 17-24, con el modo actual brillante. Tocar un pad elige el modo. Shift + pad 29 hace lo mismo sin abrir el menú: pasa por los ocho en ese orden, y con Shift el pad 29 se ve en el color del modo.

Con el menú abierto, dos knobs ajustan los modos:

| Knob | Parámetro | Recorrido | LED |
| --- | --- | --- | --- |
| K1 | Tiempo del glide | Sin glide a la izquierda del todo; de 2 ms a unos 2 s | Verde azulado |
| K2 | Desafinación del unísono | Hasta ±50 cents entre las voces de los extremos | Azul |

### Qué hace cada modo

| Modo | Nota nueva con otras pulsadas | Nota nueva sin otras pulsadas | Al soltar |
| --- | --- | --- | --- |
| Retrigger | Salta a la nota y redispara la envolvente | Dispara la envolvente | Vuelve a la nota anterior si sigue pulsada |
| Legato | Solo cambia la altura | Dispara la envolvente | Vuelve a la nota anterior si sigue pulsada |
| Glide | Se desliza a la nota, sin redisparar | Empieza en su altura y dispara | Vuelve a la nota anterior si sigue pulsada |
| Uni retrig | Mueve todas las voces y redispara | Dispara la envolvente | Suena hasta soltar todas las notas |
| Uni legato | Mueve las voces sin redisparar, sin deslizar | Dispara la envolvente | Suena hasta soltar todas las notas |
| Uni glide | Las voces se deslizan, sin redisparar | Empieza en su altura, sin glide, y dispara | Suena hasta soltar todas las notas |
| Uni always-glide | Las voces se deslizan, sin redisparar | Se desliza desde la nota anterior y redispara | Suena hasta soltar todas las notas |
| Poly | Toma otra voz y redispara la envolvente de la pista | Toma una voz y dispara | Esa voz se apaga; la última suena con el release |

En uni legato tampoco se redisparan las envolventes propias de FM y VA-drum.

### Voces por motor

| Modo | Motor | Voces de la pista |
| --- | --- | --- |
| Retrigger, legato, glide | Todos | 1 |
| Poly | Oscilador (uno o dos, también supersaw), VA-drum, muestra (también estéreo) | 4 |
| Poly | FM | 6, o 3 y 3 con las dos pistas en FM poly o unísono |
| Unísonos | Oscilador, VA-drum | 4 en la misma nota, repartidas con K2 |
| Unísonos | FM | 6, o 3 con las dos pistas en FM |
| Unísonos | Muestra | 1 |
| Todos | Granular y entrada de línea | 1 |

El glide funciona en oscilador, VA-drum y FM. El modo muestra y el granular no deslizan.

Cada pista tiene su máximo; solo las voces FM se reparten entre las dos. Si la segunda pista entra en FM poly o unísono, las voces de las dos se cortan al momento para repartirse.

### Qué es de cada voz y qué es de la pista

| Elemento | Oscilador y muestra | VA-drum | FM |
| --- | --- | --- | --- |
| Altura y velocity | Por voz | Por voz | Por voz |
| Envolvente de volumen | De la pista | Por voz | Por voz, en los operadores |
| Envolvente de tono | De la pista | Por voz | De la pista |
| Ruido | — | Por voz | Por voz |
| Filtro y efecto | De la pista | De la pista | De la pista |
| Al soltar | La última nota suena con el release | El golpe sigue hasta acabar | Cada voz suena entera con su release |

### Robo de voz

Con todas las voces ocupadas, una nota nueva quita la voz a la nota más antigua de la pista, con un fundido de 2 ms. Una nota soltada ocupa su voz mientras suena su release, así que con releases largos las voces se llenan aunque toques notas sueltas.

### Nivel de los acordes

Cada voz baja según cuántas suenan, para que la suma no recorte. El factor es √(2 / n), y los unísonos siguen la misma regla.

| Voces sonando | Nivel de cada voz |
| --- | --- |
| 1 o 2 | 1,00 |
| 3 | 0,82 |
| 4 | 0,71 |
| 5 | 0,63 |
| 6 | 0,58 |

### Límite de voces

Con dos voces propias o más sonando, el aparato apaga voces antes de que el DSP se quede sin tiempo y se oiga un traqueteo. FM es el motor que más gasta. Con una sola voz propia el límite no actúa.

1. Cada 2 ms mide cuánto tiempo le sobra al DSP.
2. Si va justo, apaga la voz soltada más baja, las de FM primero. Si no hay ninguna soltada, apaga la nota mantenida más antigua.
3. Apaga como mucho una voz cada 12 ms, o cada 4 ms si va muy justo.
4. La pista sigue con las voces que caben, mínimo 2. Una nota nueva apaga antes la soltada más baja.
5. Cada 2 s sin problemas prueba con una voz más, hasta volver al máximo.

Synth 1 y Synth 2 no pierden voces por esto: con dos voces propias o más sonando, el aparato deja de apagar las suyas por falta de tiempo. Las que se apagan son las del sinte propio.

Para tener más voces a la vez: releases más cortos, menos operadores FM con nivel alto, o una sola pista en FM poly.

### Guardado del modo

El modo, el tiempo del glide y la desafinación se guardan con el patch propio y con el proyecto. Un patch sin ellos deja los valores actuales.

## Páginas de knobs

Con el motor encendido, los pads 1-7 eligen qué hacen los 8 knobs, y Shift da una segunda capa. Los knobs de tipo se ven con el color del tipo y el brillo de la posición dentro del tipo.

### Página 1: VCA-VCF

| Knob | Solo | Con Shift |
| --- | --- | --- |
| K1 | Ataque | Sustain |
| K2 | Release | Decay |
| K3 | Envolvente → nivel | LFO → nivel |
| K4 | Envolvente → filtro | LFO → filtro |
| K5 | Filtro | Tipo de filtro: DJ, LP 12, HP 12, BP, notch, LP 24, HP 24 |
| K6 | Resonancia | Gain del VCA, hasta +18 dB con saturación |
| K7 | Velocidad del LFO: derecha libre, izquierda a tempo | — |
| K8 | Cantidad de efecto | Tipo de efecto: suave, dura, plegado, wavefold, ring, comb, chorus |

### Página 2: OSC 1

En oscilador, VA-drum, muestra y FM.

| Knob | Solo | Con Shift |
| --- | --- | --- |
| K1 | TUNE | FINE |
| K2 | SHAPE | MIX OSC 1 ↔ OSC 2 |
| K3 | Envolvente → tono | BITSYNC |
| K4 | Envolvente → forma | — |
| K5 | LFO → tono | — |
| K6 | LFO → forma | — |
| K7 | WAVE (morph); en muestra, anchura estéreo | — |
| K8 | LFO → morph | Envolvente → morph |

### Página 2: granular

| Knob | Solo | Con Shift |
| --- | --- | --- |
| K1 | Tono ±24 semitonos | Fino ±1 semitono |
| K2 | Posición en el sample | Dispersión de la posición |
| K3 | Scan, con el centro congelado | Izquierda: grano al revés. Derecha: dispersión del tono |
| K4 | Tamaño del grano, 5-500 ms | Dispersión estéreo |
| K5 | Densidad, 1-16 granos | Ventana |
| K6 | Zona del scan | Modo de nota: tono, slicer, stretch |
| K7 | LFO → posición | LFO → tamaño |
| K8 | Envolvente → posición | Fuente: la captura o el sample de un drum |

### Página 3: OSC 2

| Knob | Solo |
| --- | --- |
| K1 | TUNE 2 |
| K2 | SHAPE 2 |
| K3 | MIX OSC 1 ↔ OSC 2 |
| K4 | FM |
| K5 | FINE 2 |
| K6 | BITSYNC |
| K7 | WAVE 2 |
| K8 | RING |

### Página 4: knobs secuenciables

Son los 8 valores que se graban como automatización con Record + Play. De fábrica: TUNE, Release, Env → nivel, Env → filtro, Filtro, Resonancia, Velocidad del LFO y Efecto.

Shift + knob elige el destino entre los 33 parámetros, a 4 clics por parámetro. Mientras eliges, los pads 9-24 enseñan dónde vive el destino. Clear mantenido y luego Shift + knob devuelve el de fábrica.

### Knobs no secuenciables (Shift + pad 4)

Ocho knobs con destino asignable que no se graban. El pad 4 se ve rosa. De fábrica: Ataque, Decay, Sustain, SHAPE, LFO → filtro, Env → tono, MIX OSC 1 / 2 y Gain del VCA.

Un destino que también esté en los knobs secuenciables sí se graba, como desde cualquier página.

### Página 5: modulación

| Knob | Solo | Con Shift |
| --- | --- | --- |
| K1 | Ataque | Envolvente → nivel |
| K2 | Decay | Envolvente → filtro |
| K3 | Sustain | Envolvente → tono |
| K4 | Release | Envolvente → forma |
| K5 | Velocidad del LFO | LFO → forma |
| K6 | LFO → filtro | LFO → morph |
| K7 | LFO → nivel | Envolvente → morph |
| K8 | LFO → tono | Forma del LFO |

Con VA-drum, el LFO sigue siendo su ruido.

### Página 6: matriz

Ocho fuentes de modulación, en la sección siguiente.

### Página 7: FM

| Knob | Solo | Con Shift |
| --- | --- | --- |
| K1-K4 | Ratio del operador 1-4: de 0,5 a 16. Cada ratio ocupa 5-6 clics: el primero exacto, los siguientes desafinan +2,5 cents | Centro = ataque 0. Derecha: ataque hasta unos 3 s. Izquierda: percusivo, con decay de 3 ms a 8 s |
| K5 | Nivel del operador 1 | Algoritmo |
| K6 | Nivel del operador 2 | Feedback |
| K7 | Nivel del operador 3 | Ruido |
| K8 | Nivel del operador 4 | Release |

El nivel de un portador es su volumen; el de un modulador, cuánto modula.

## Modulación

El motor tiene una ADSR y un LFO propios, y la matriz añade ocho fuentes que mueven cualquiera de 33 parámetros. La matriz se suma al enviar: el valor guardado del parámetro no cambia.

### LFO

K7 de la página 1 es bipolar: a la derecha libre, a la izquierda a tempo. Shift + K8 de la página 5 elige la forma, un paso cada 4 clics, con el LED en su color.

| Forma | Color |
| --- | --- |
| Triángulo, la inicial | Verde |
| Diente de sierra inverso | Azul |
| Diente de sierra | Magenta |
| Cuadrada | Rojo |
| Seno | Verde azulado |
| Sample & hold | Blanco |
| Sample & hold suavizado | Violeta |

### Matriz de modulación (pad 6)

| Knob | Fuente | Shift + knob |
| --- | --- | --- |
| K1 | Velocity de la nota | — |
| K2 | Nota: C3 = 0, una octava = un cuarto del recorrido | — |
| K3 | Azar: un valor nuevo en cada nota | — |
| K4 | LFO 2 | Forma × velocidad; en cada forma, mitad izquierda a tempo y derecha libre |
| K5 | Envolvente 2: ataque y caída desde cada nota | Ataque × caída, de 20 ms a 4 s |
| K6 | Golpe de un drum: una caída desde cada golpe | Drum 1-4 × su caída |
| K7 | Posición en el patrón, del primer paso al último | — |
| K8 | Azar por pasos: un valor nuevo cada N pasos | N = 1, 2, 4, 8 o 16 |

La posición del knob es a la vez el destino y la cantidad:

- Del todo a la izquierda, apagado.
- Cada destino ocupa 16 pasos, a 2 clics por paso. El primero es el destino sin cantidad, con el LED tenue.
- El color del LED es el de la página del destino, y el brillo la cantidad.
- Las fuentes nota, azar, LFO 2 y azar por pasos suben y bajan; las demás solo suben.
- Varias fuentes al mismo destino se suman.

| Gesto | Efecto |
| --- | --- |
| Clear + knob | Esa fuente apagada |
| Clear + Shift + knob | Su parámetro al valor inicial |
| Clear + pad 6 | Todas las fuentes apagadas |

Las modulaciones llegan al motor unas 100-250 veces por segundo, repartidas entre todo lo que se mueve en la pista.

## Secuencia y interpretación

La pista usa el patrón de stock, y el mod añade automatización del motor, step-drummer, arpegiador y variaciones por paso. Todo sale por las mismas voces y respeta el modo de voz.

### Automatización

Los 8 knobs secuenciables graban con Record + Play en 8 carriles del patrón. Hay varios gestos por paso:

| Gesto | Vista | Efecto |
| --- | --- | --- |
| Record mantenido + paso | Note | Foto: escribe en ese paso los parámetros que no están en su valor inicial. *(solo Beta 5.4)* El paso se ve amarillo mientras lo mantienes |
| Shift + paso | Velocity | Marca el paso: ahí no suena ningún carril y lo automatizado vuelve al sinte guardado con el proyecto |
| Shift + paso amarillo | Velocity | *(solo Beta 5.4)* Oye sus valores hasta soltar Shift, con los knobs que mueve en amarillo |
| Clear + paso | Velocity | *(solo Beta 5.4)* Borra la automatización de los knobs de ese paso; las notas quedan |
| Paso amarillo mantenido + otro paso amarillo | Velocity, con Shift | *(solo Beta 5.4)* Sweep: cada carril con valor en los dos pasos queda en línea recta entre ellos |

En la foto, un parámetro sin carril toma uno cuyo parámetro sí está en su valor inicial, y ese carril se borra antes. Si no caben, quedan los primeros en el orden de la matriz.

### Step-drummer

Los 8 knobs son 8 pares de pasos del patrón: cada par desplaza un destino solo en esos pasos. El LED muestra la cantidad: tenue sin modulación, más brillante cuanto más se aleja.

| Control | Función |
| --- | --- |
| Pads 1-16 | Pasos de la mitad mostrada. Tocar = escuchar. Shift + tocar = poner o quitar nota. Con Record, graba en el paso que suena |
| Pads 17-24 | Destino: tono, OSC 2, WAVE, FM, MIX, env → filtro, SHAPE, decay |
| K1-K8 | Los 8 pares de pasos, el que suena en blanco |
| Octave ▲ / ▼ | Página pitch o velocity. La página velocity tiene destino propio |
| 1-16 / 17-32 | La otra mitad del patrón |
| Pad 32 | Toggle pitch-vel: la página pitch transpone por grados y la velocity cambia la velocity |

El toggle sube o baja un grado de la escala cada 8 pasos del knob, de −8 a +8 grados. Con el step-drummer activado, TUNE y Release dejan de reproducirse y grabarse como automatización, porque usa sus carriles.

### Secuenciador de efectos

Con este motor, cada knob del step-drummer elige un hueco de la fila inferior de Master FX: nada, pads 26-31 o random. Un hueco sin efecto toca el efecto de arriba de su columna.

### Secuenciador de saltos

Las notas de la pista hacen saltar el patrón de otra pista al paso que indican, en el mismo paso de la nota. *(solo Beta 5.4)*

| Control | Función |
| --- | --- |
| Pads 9-16 de la fila de motores | Las ocho pistas: un toque apunta a esa pista, el mismo la apaga. El pad 27 toma su color |
| Vista Note, pads 17-32 | Pasos 1-16; Octave ▲, pasos 17-32. La escala no cambia nada |
| Note ampliada, los 32 pads | Pasos 1-32 |

Mientras apunta, la pista no suena. Cada nota, del secuenciador, de los pads o del arpegiador, hace saltar la otra pista. Se guarda con el proyecto.

### Arpegiador

Funciona por pista y patrón, en Pattern Settings con Shift. Las notas se arpegian en el orden en que se pulsaron.

| Gesto | Función |
| --- | --- |
| Shift + pad 25 | Encendido o apagado |
| Shift + pads 27-32 | Orden: fractal, deconstruido, arriba, abajo, ping-pong, aleatorio |
| Shift + pads 17-24 | Resolución: 1/4, 1/4T, 1/8, 1/8T, 1/16, 1/16T, 1/32, 1/32T. El mismo pad otra vez = la de la pista |
| Shift + pads 1-4 | Octavas: ninguna, +1, +1 y −1, +2 y −1 |
| Shift + pads 5-8 | Cuándo cambia la octava: cada vuelta, cada nota, cada 3, cada 4 |
| Shift + pads 9-12 | Groove: ninguno, puntillo, swing, cada nota dos veces |
| Shift + pads 13-16 | Reinicio: ninguno, o tras una vuelta 1, 3 o 5 notas más |

Cuatro fuentes llegan al arpegiador: acordes del patrón, notas mantenidas, un paso mantenido con el transporte parado, y el teclado externo si está encendido el botón Note de Setup. Con Record se graba el acorde, no las notas sueltas.

### Variaciones por paso

| Función | Dónde | Qué hace |
| --- | --- | --- |
| Probabilidad | Vista de probabilidad, fila 3 | Que el paso suene a veces |
| Frecuencia | Modo 1, fila 4 | El paso suena en la última de cada n vueltas, de 1 a 8 |
| Dinámicas | Modo 2, pads 25-28 | Acentos, acentos y longitud, o longitud al azar. *(solo Beta 5.4)* |
| Random-mutate | Modo 2, pads 17-24 | Pads 18-20 otra nota de la escala (×1, ×2, ×4), 21 / 22 una octava arriba (baja / alta), 23 / 24 arriba o abajo (baja / alta). *(solo Beta 5.4)* |
| Gate por pulsación | Micro Step, pad 32 | Lo que mantienes al introducir una nota es su duración |
| Longitud fija | Micro Step, pad 31 | Todas las notas introducidas a mano con el mismo gate, de 1 a 16 pasos |
| Nudge | Pattern Settings, pad 26 | Mueve el contenido del tramo un paso atrás; Shift, adelante. El primer y el último paso no se mueven. *(solo Beta 5.4)* |
| Fractal y deconstruido | Pattern Settings, pads 27 y 28 | Otro orden de recorrido del patrón |
| Micropasos | Modo 2, pad 32 | La nota se adelanta o se atrasa hasta 2 micropasos, sin salir de su paso. *(solo Beta 5.4)* |
| Factor de la pista | Octave, con el modo 2 abierto | De ×0 a ×8, multiplica todas las probabilidades de la pista; ×1 de fábrica. A ×8 el pad 24 cambia todas las notas: el sorteo sigue siendo mitad y mitad. *(solo Beta 5.4)* |

### Tocar en vivo

| Función | Gesto | Qué hace |
| --- | --- | --- |
| Latch | Shift + tecla en Note | La nota sigue sonando hasta su siguiente pulsación. Con Shift, las fijadas se ven verde azulado brillante |
| Notas fijadas a un paso | Shift + paso en Note | Escribe las notas fijadas en ese paso, hasta 6 |
| Pantalla de acordes | Shift + pad 8 en Note ampliada | Tipo, inversión y modificadores; las filas 3-4 tocan el acorde, hasta 6 notas |
| Teclado partido | Mantener una pista y pulsar otra | Dos pistas en los pads. Mantener un botón de pista da sus knobs |
| Banco de acordes | Record de Setup en amarillo | Nada se graba en una pista silenciada: suena y se graba en el sinte del canal compartido |
| Destello de notas | Shift mantenido, en cualquier vista | *(solo Beta 5.4)* El botón de cada pista destella en blanco 100 ms con cada nota |

Cada nota del acorde pasa por el modo de voz: en poly suena hasta el máximo de voces del motor.

## Guardado

El sinte propio vive en tres sitios a la vez: el proyecto, el patch del pack y los ajustes del aparato. Al cargar un proyecto que lo lleva, manda el del proyecto; uno anterior deja el sonido como estaba.

| Sitio | Cuándo se escribe | Alcance | Dónde |
| --- | --- | --- | --- |
| Patrón y proyecto | Save dos veces | Ese proyecto | Fichero de sesión del pack |
| Patch propio | Clear + pad dos veces, al momento | Todo el pack; 128 huecos comunes a MIDI 1 y 2 | Relleno de los registros de `Patches/NN_PATCHBANK.cpb` |
| Ajustes del aparato | Solos, con el transporte parado y 2 s sin cambios | Todos los proyectos | Ajustes del aparato |

El fichero de patches de Synth 1 / 2 no cambia: el patch propio va en la parte de cada registro que el original no usa.

### Qué se guarda dónde

| Dato | Patrón | Proyecto | Patch propio | Ajustes |
| --- | --- | --- | --- | --- |
| Notas, velocity, gate, micropasos, probabilidad | Sí | Con el patrón | — | — |
| Automatización, marcas, pares del step-drummer, sample flips | Sí | Con el patrón | — | — |
| Frecuencia, dinámicas, random-mutate, orden fractal o deconstruido | Sí | Con el patrón | — | — |
| Arpegiador y modificadores, por pista y patrón | — | Sí | — | — |
| Gate por pulsación, longitud fija | — | Sí | — | — |
| Toggle pitch-vel, destino de la página velocity | — | Sí | — | — |
| Motor elegido, osciladores, orden, valores | — | Sí | Sí | Sí |
| Step-drummer encendido y su destino | — | Sí | Sí | Sí |
| Modo de voz, tiempo del glide, desafinación | — | Sí | Sí | — |
| Matriz de modulación | — | Sí | Sí | — |
| FM: operadores, algoritmo, feedback, ruido | — | Sí | Sí | — |
| Destinos de los knobs secuenciables y no secuenciables | — | Sí | Sí | — |
| Forma del LFO | — | Sí | Sí | — |
| Estéreo del modo muestra: distancia al segundo sample | — | Sí | Sí | — |
| Patch flip | — | — | — | Sí |
| Factor del random-mutate, por pista *(solo Beta 5.4)* | — | Sí | — | — |
| Pista a la que apunta el secuenciador de saltos *(solo Beta 5.4)* | — | Sí | — | — |

### Qué se pierde al apagar

- Todo lo cambiado desde el último Save del proyecto.
- Notas y acordes en latch, y el tipo y los modificadores de la pantalla de acordes.
- El teclado partido y las vistas abiertas.
- El medio tono de Octave con Jankó.
- Un patch esperando a copiarse a otro pack.
- Los contadores de vueltas de la frecuencia y del orden fractal, que se reinician al parar.

### Limitaciones

- Sin tarjeta, y en las versiones S, el mod no escribe nada propio: los patches no se guardan y Save se pone rojo. El proyecto sí se guarda.
- El editor de CC guarda en la plantilla, no en el patch propio.
- Un patch de una versión antigua carga sin lo que aún no existía: la matriz apagada y los destinos de fábrica.

## Control MIDI

Cada knob del motor manda y recibe un CC o NRPN por el canal de la pista, con valores de 0 a 127 y 64 como centro en los bipolares. El modo de voz, la matriz, el FM y los destinos de los knobs no tienen CC ni NRPN.

Todo respeta los filtros CC Tx y CC Rx de la vista Setup. Los mensajes salen al girar el knob, también con Clear, y entran por el mismo número.

### Notas y canales

| Mensaje | Qué hace |
| --- | --- |
| Canal de la pista | Se elige en Setup, con el botón de la pista y los pads 1-15 |
| Notas de salida | La pista manda sus notas con cualquier motor |
| Notas de entrada | Por el canal de la pista, USB o DIN: tocan el sinte propio y se graban. No se reenvían a la salida |
| Canal compartido | MIDI 1 / 2 en el canal de un sinte o de los drums los toca por dentro (loopback interno) |
| Patch flip | Pad 26: cada nota sale como Program Change por el canal de la pista. Excluyente con el motor |
| Teclado al arpegiador | Botón Note de Setup: las notas entrantes pasan por el arpegiador. Apagado de fábrica |
| Grabar ruteos internos | Record de Setup: lo que la pista manda a un sinte se graba también en él |
| Fusión USB | Advanced Setup, pad 23: el DIN In sale también por USB |
| MIDI Thru | Advanced Setup, Duplicate: Thru, Out 2, Merge o Filter |

Con el motor encendido, los knobs mandan este mapa y nunca la plantilla. Con el motor apagado mandan la plantilla, editable con el pad 25.

### Seleccionar un NRPN

Manda CC 99 (MSB), CC 98 (LSB) y CC 6 (valor), en ese orden. El aparato recuerda el NRPN elegido hasta el siguiente CC 99 o 98. En la tabla, 4:13 significa MSB 4, LSB 13.

### Parámetros del motor

En granular, la página 2 y parte de la 3 usan los mismos números con otro significado, entre paréntesis.

| Parámetro | Mensaje | Página / knob |
| --- | --- | --- |
| Filtro | CC 74 | 1 / K5 |
| Resonancia | CC 71 | 1 / K6 |
| Envolvente → filtro | CC 79 | 1 / K4 |
| LFO → filtro | NRPN 4:4 | 1 / Shift + K4 |
| Ataque | CC 73 | 1 / K1 |
| Decay | CC 75 | 1 / Shift + K2 |
| Sustain | CC 70 | 1 / Shift + K1 |
| Release | CC 72 | 1 / K2 |
| Cantidad de efecto | CC 91 | 1 / K8 |
| Gain del VCA | CC 59 | 1 / Shift + K6 |
| Velocidad del LFO | NRPN 0:76 | 1 / K7 |
| LFO → nivel | NRPN 4:12 | 1 / Shift + K3 |
| Tipo de efecto | NRPN 4:13 | 1 / Shift + K8 |
| Envolvente → nivel | NRPN 4:15 | 1 / K3 |
| Tipo de filtro | NRPN 4:16 | 1 / Shift + K5 |
| TUNE (granular: tono) | CC 26 | 2 / K1 |
| FINE (granular: tamaño) | CC 27 | 2 / Shift + K1 |
| WAVE (granular: posición) | CC 20 | 2 / K7 |
| SHAPE (granular: densidad) | CC 21 | 2 / K2 |
| LFO → tono (granular: scan) | NRPN 4:21 | 2 / K5 |
| Envolvente → tono (granular: env → posición) | NRPN 4:22 | 2 / K3 |
| Envolvente → forma (granular: zona) | NRPN 4:23 | 2 / K4 |
| LFO → forma (granular: LFO → posición) | NRPN 4:24 | 2 / K6 |
| Envolvente → morph (granular: fuente) | NRPN 4:25 | 2 / Shift + K8 |
| LFO → morph (granular: modo de nota) | NRPN 4:26 | 2 / K8 |
| TUNE 2 (granular: LFO → tamaño) | CC 37 | 3 / K1 |
| FINE 2 (granular: fino) | CC 39 | 3 / K5 |
| WAVE 2 (granular: estéreo) | CC 30 | 3 / K7 |
| SHAPE 2 (granular: ventana) | CC 31 | 3 / K2 |
| MIX OSC 1 ↔ OSC 2 | CC 52 | 3 / K3 |
| BITSYNC | NRPN 4:32 | 3 / K6 |
| FM (granular: dispersión de la posición) | NRPN 4:33 | 3 / K4 |
| RING (granular: reverso y dispersión del tono) | CC 54 | 3 / K8 |

### CC y NRPN de entrada

Los CC y NRPN que entran mueven el motor, pero no se graban en el patrón ni se reenvían por MIDI. Solo los knobs del aparato escriben automatización. Con el motor apagado, el aparato no los toma.
