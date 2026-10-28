# MIDI

*[English version](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/MIDI) · [Inicio](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Home#en-español) · [Guía por vistas](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html)*

Cómo habla MIDI el mod: sus comportamientos propios, los CC y NRPN nuevos, y la matriz de modulación y los destinos de los macros.

## MIDI: comportamientos propios, CC y NRPN nuevos

Todo lo nuevo sale y entra por CC / NRPN, respetando los filtros CC Tx / CC Rx del Setup. Los parámetros del aparato original siguen con los números de la guía de Novation (ver la sección siguiente).

### Canales (como en el original, cambiables en Setup)
Synth 1 = canal 1, Synth 2 = canal 2, drums = canal 10, proyecto y Master FX = canal 16 (los de la guía de Novation); MIDI 1 / 2 = los canales elegidos para ellas en Setup.

### Comportamientos propios
| Qué | Cómo |
|---|---|
| **Teclado externo en MIDI 1 / 2** *(desde RC2)* | Las notas que entran por el canal de MIDI 1 / 2 (USB o DIN) tocan su sinte propio y se graban; no se reenvían a la salida. |
| **Teclado externo al arpegiador** *(desde RC4)* | Setup, botón Note: las notas que entran por el canal de Synth 1 / 2 o MIDI 1 / 2 pasan por su arpegiador. |
| **Patch flip** | Vista Preset de MIDI 1 / 2, pad 26: cada nota de la pista sale como Program Change por el canal de la pista. |
| **Program Change del proyecto** *(desde RC2)* | Setup, pads 29 / 30: canal de escucha y canal de salida (16 de fábrica); lo recibido en el de escucha se reenvía por el de salida. |
| **MIDI Thru: Merge y Filter** | Advanced Setup, Duplicate: Thru (hardware), Out 2, Merge (DIN In + el MIDI del aparato), Filter (DIN In sin los canales del aparato). Sin SysEx. |
| **Fusión USB** *(desde RC4)* | Advanced Setup, pad 23: lo que entra por el DIN In sale también por USB (sin el reloj con Clock Tx, sin SysEx). |
| **Modo General MIDI de los drums** *(desde RC4)* | Setup, K4 / K5-K8: los golpes de Drum 1-4 salen con la nota GM elegida en lugar de 60 / 62 / 64 / 65. Dentro suena igual. |
| **Pareja estéreo de drums** *(desde RC4)* | Las notas de Drum 2 / 4 lo tocan solo, a la derecha; su patrón no suena ni sale por MIDI mientras dura la pareja. |
| **Grabar los ruteos internos** *(desde RC2)* | Setup, Record: lo que una pista MIDI manda a un sinte por el mismo canal se graba también en el sinte; *(desde RC4)* nada se graba en una pista silenciada en el Mixer. |
| **Knobs nuevos** | Al girarlos (también con Clear) sale su CC / NRPN; al recibirlo, el knob se mueve. El nivel a 100 / 0 del Mixer (Shift + knob) sale como un giro. |
| **Sin MIDI** | La matriz de modulación del sinte propio, el FM, el modo de voz y los destinos de los knobs secuenciables y *(desde RC4)* no secuenciables no tienen CC / NRPN: se guardan en los patches propios. |
| **Seleccionar un NRPN** | CC 99 (MSB), CC 98 (LSB), CC 6 (valor), en ese orden; el aparato recuerda el NRPN elegido hasta el siguiente CC 99 / 98. |

### Motor de las pistas MIDI (MIDI 1 / 2)

Canal de la pista MIDI. Valores 0-127; los bipolares, 64 = centro. Sale al girar el knob (también con Clear) y entra por el mismo número. «Página / knob» = dónde está en la vista Preset con el motor encendido (pads 1-5 = páginas). En el motor granular la página 2 usa los mismos números con otro significado (entre paréntesis).

| Código | Parámetro | Mensaje | Página / knob |
|---|---|---|---|
| 1 | Filtro | CC 74 | 1 / K5 |
| 2 | Resonancia | CC 71 | 1 / K6 |
| 3 | Envolvente → filtro | CC 79 | 1 / K4 |
| 4 | LFO → filtro | NRPN 4:4 | 1 / Shift + K4 |
| 5 | Ataque | CC 73 | 1 / K1 |
| 6 | Decay | CC 75 | 1 / Shift + K2 |
| 7 | Sustain | CC 70 | 1 / Shift + K1 |
| 8 | Release | CC 72 | 1 / K2 |
| 9 | Cantidad de efecto | CC 91 | 1 / K8 |
| 10 | Gain del VCA | CC 59 | 1 / Shift + K6 |
| 11 | Velocidad del LFO | NRPN 0:76 | 1 / K7 |
| 12 | LFO → nivel | NRPN 4:12 | 1 / Shift + K3 |
| 13 | Tipo de efecto | NRPN 4:13 | 1 / Shift + K8 |
| 15 | Envolvente → nivel | NRPN 4:15 | 1 / K3 |
| 16 | Tipo de filtro | NRPN 4:16 | 1 / Shift + K5 |
| 17 | TUNE (granular: tono) | CC 26 | 2 / K1 |
| 18 | FINE (granular: tamaño) | CC 27 | 2 / Shift + K1 |
| 19 | WAVE (granular: posición) | CC 20 | 2 / K7 |
| 20 | SHAPE (granular: densidad) | CC 21 | 2 / K2 |
| 21 | LFO → tono (granular: scan) | NRPN 4:21 | 2 / K5 |
| 22 | Envolvente → tono (granular: env → posición) | NRPN 4:22 | 2 / K3 |
| 23 | Envolvente → forma (granular: zona) | NRPN 4:23 | 2 / K4 |
| 24 | LFO → forma (granular: LFO → posición) | NRPN 4:24 | 2 / K6 |
| 25 | Envolvente → morph (granular: fuente) | NRPN 4:25 | 2 / Shift + K8 |
| 26 | LFO → morph (granular: modo de nota) | NRPN 4:26 | 2 / K8 |
| 27 | TUNE 2 (granular: LFO → tamaño) | CC 37 | 3 / K1 |
| 28 | FINE 2 (granular: fino) | CC 39 | 3 / K5 (RC2) · 3 / Shift + K1 (RC0.9) |
| 29 | WAVE 2 (granular: dispersión del tono; RC4: estéreo) | CC 30 | 3 / K7 |
| 30 | SHAPE 2 (granular: ventana) | CC 31 | 3 / K2 |
| 31 | MIX OSC 1 ↔ OSC 2 | CC 52 | 2 / Shift + K2 · 3 / K3 (RC2) |
| 32 | BITSYNC | NRPN 4:32 | 2 / Shift + K3 · 3 / K6 (RC2) |
| 33 | FM (granular: dispersión de la posición) | NRPN 4:33 | 3 / K4 (RC2) · 3 / Shift + K2 (RC0.9) |
| 34 | RING (granular: reverso; RC4: bipolar, reverso / dispersión del tono) | CC 54 | 3 / K8 (RC2) · 3 / Shift + K3 (RC0.9) |

**Knobs secuenciables** (página 4: se graban en el patrón con Record): TUNE, Release, Envolvente → nivel, Envolvente → filtro, Filtro, Resonancia, Velocidad del LFO, Efecto. *Solo RC4:* los ocho destinos se eligen con Shift + knob.

### Drums

Canal de drums (Setup). **CC 99 = 5, 6, 7, 8** (Drum 1-4), **CC 98 = LSB**, **CC 6 = valor**. Los knobs de stock (pitch, decay, distortion, EQ) siguen con sus CC originales. *Solo RC4:* con el **modo General MIDI** (vista Setup, K4) las notas de Drum 1-4 salen con la nota GM de cada uno (K5-K8, 35-81; de fábrica 36 / 38 / 42 / 46) en lugar de 60 / 62 / 64 / 65.

| LSB | Parámetro | Valores |
|---|---|---|
| 1 | Envolvente → tono | 0-127, 64 = 0 |
| 2 | Ring mod: frecuencia | 0-127 |
| 3 | LFO: cantidad (> 64 trémolo; < 64 vibrato, solo RC4: scan del inicio) | 0-127, 64 = 0 |
| 4 | LFO: velocidad | 0-127, 64 = centro |
| 5 | Envolvente → corte | 0-127, 64 = 0 |
| 6 | Resonancia | 0-127 |
| 7 | Forma de la envolvente | 0-127, 64 = centro |
| 8 | Ring mod: cantidad | 0-127 |
| 9 | Modo de filtro | 0 EQ tilt de stock, 1 paso banda, 2 notch, 3 comb, 4 DJ |
| 10 | Inicio del sample | 0-120 (/128; desde RC2.09 todo el sample, antes el final llegaba en 32); RC0.9: 0-15 (/64) |
| 11 | Bitcrush | 0-15 |
| 12 | Tipo de distorsión | 0 stock, 1 suave, 2 dura, 3 plegada |
| 13 | Corte desde el final (desde RC2) | 0-120 (/128) |
| 14 | Ataque (desde RC2) | 0-127 |

### Master FX

Canal 16. **CC 99 = 9**, **CC 98 = 4 × efecto + knob** (knob 0-3 = K1-K4), **CC 6 = valor**.

| LSB | Efecto | K1-K4 |
|---|---|---|
| 0-3 | Gater | división, profundidad, ancho, suavizado |
| 4-7 | Auto-Filter (pads 2 / 3) | velocidad, profundidad, resonancia, centro |
| 8-11 | Digitise | muestreo, bits, envío al delay (RC2), envolvente (RC2) |
| 12-15 | Phaser | velocidad, profundidad, realimentación, mezcla |
| 16-19 | Glitch (RC0.9: Vinyl) | velocidad, repetición, retraso, caos / sobrecarga (RC0.9: crackle, siseo, tono, desgaste) |

## Matriz de modulación y destinos de los macros

Los sintes de stock (Synth 1 / 2) tienen la matriz y los macros de Novation; el sinte propio de MIDI 1 / 2 tiene su matriz y sus carriles.

La referencia oficial es la **Programmer's Reference Guide** de Novation, versión 3 ([PDF](https://fael-downloads-prod.focusrite.com/customer/prod/downloads/circuit_tracks_programmer_s_reference_guide_v3.pdf), en la [página de descargas del Circuit Tracks](https://downloads.novationmusic.com/novation/circuit/circuit-tracks)). Para cada ranura de macro da: «macro knob 1 destination A NRPN 3:0 0 – 70 0» (Novation, *Circuit Tracks Programmer's Reference Guide* v3, «Macro Knobs»).

### Matriz de modulación de Synth 1 / 2 (stock, sin cambios)
- Se edita desde Components o por MIDI (canal del sinte); el aparato no tiene vista para ella. Cada ranura: fuente 1, fuente 2, profundidad (−64..63) y destino. La guía oficial lista 12 ranuras desde **NRPN 1:83** (fuente 1, fuente 2, —, profundidad, destino: 5 números por ranura); el firmware tiene 20, con el mismo patrón.
- **Fuentes (0-12):** 0 directa, 4 velocity, 5 teclado (nota), 6 / 7 LFO 1 (unipolar / bipolar), 8 / 9 LFO 2 (unipolar / bipolar), 10 envolvente de amplitud, 11 envolvente del filtro, 12 envolvente 3.
- **Destinos (0-17):** 0 tono de los dos osciladores, 1 / 2 tono del oscilador 1 / 2, 3 / 4 v-sync 1 / 2, 5 / 6 ancho de pulso / índice 1 / 2, 7 / 8 nivel del oscilador 1 / 2, 9 nivel de ruido, 10 nivel del ring mod, 11 drive del filtro, 12 frecuencia del filtro, 13 resonancia, 14 / 15 velocidad del LFO 1 / 2, 16 decay de la envolvente de amplitud, 17 decay de la envolvente del filtro.

### Macros de Synth 1 / 2 (stock) y su editor *(desde RC2)*
- 8 macros por patch, posición = **CC 80-87**; cada macro, 4 ranuras A-D. Ranura r (0-3) del macro k (1-8): **NRPN 3:(16 (k − 1) + 4 r)** = destino, + 1 inicio, + 2 fin (el tramo del recorrido del knob, 0 / 127 de fábrica), + 3 profundidad (64 = 0).
- La guía oficial da el destino como «0 – 70» sin nombrarlos: la lista de abajo nombra cada uno (70 destinos, 0-69).
- **En el aparato:** [vista de la fuente](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#synth-fuente), pad 32 = editor (ranura, inicio, fin, destino, profundidad). Lo editado va en el patch del proyecto; Clear + pad dos veces en la [vista Preset](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#synth-preset) lo guarda en el pack.
- El knob del editor recorre primero los destinos con CC (por número de CC) y después los que solo tienen NRPN; en los pads, blanco = CC, azul claro / magenta / violeta = NRPN de los bancos 0 / 1 / 2.

### Matriz del sinte propio de MIDI 1 / 2 (propia) *(desde RC2.02)*
- [Vista Preset de MIDI](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#midi-preset) con el motor encendido, **pad 6**: los 8 knobs son 8 **fuentes**: K1 velocity, K2 nota, K3 azar por nota, K4 LFO 2, K5 envolvente 2, K6 golpe de un drum, K7 posición en el patrón, K8 azar por pasos (*(desde RC4)* el LFO 2 también a tempo).
- **La posición del knob es el destino y la cantidad:** a la izquierda apagado; girando a la derecha recorre todos los parámetros de las páginas de knobs (los de la página 1, luego la 2, la 3 y los de la 5 que no salen antes), 16 pasos por destino, la cantidad creciendo dentro de cada tramo. LED = color de la página del destino; brillo = cantidad.
- Varias fuentes al mismo destino se suman; el valor guardado del parámetro no cambia. Detalle: [Matriz de modulación](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#midi-matriz).

### Destinos de los knobs secuenciables (página 4) y no secuenciables del sinte propio *(desde RC4)*
- Los 8 knobs secuenciables (página 4) son los carriles de automatización (de fábrica: TUNE, Release, Env → nivel, Env → filtro, Filtro, Resonancia, Velocidad del LFO, Efecto). **Shift + knob** = su destino, entre los mismos parámetros y colores que la matriz; **Clear mantenido, luego Shift + knob** = el de fábrica. Se guarda con el patch propio y con el proyecto. Detalle: [Páginas de knobs](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#midi-knobs).
- **Knobs no secuenciables** (Shift + pad 4): la misma elección de destino, en 8 knobs que no son carriles; de fábrica Ataque, Decay, Sustain, SHAPE, LFO → filtro, Env → tono, MIX OSC 1 / 2, Gain del VCA; se guardan con los patches propios.

### Destinos del step-drummer
- MIDI 1 / 2: pads 17-24 de su vista = el parámetro del motor que mueve cada paso; Synth 1 / 2: los macros 1-8. Detalle: [Step-drummer](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#step-drummer).

### Los 70 destinos de los macros

| Destino | Parámetro | CC / NRPN |
|---|---|---|
| 0 | Portamento rate | CC 5 |
| 1 | Post FX level | CC 59 |
| 2 | Osc 1 wave interpolate | CC 20 |
| 3 | Osc 1 pulse width index | CC 21 |
| 4 | Osc 1 virtual sync depth | CC 22 |
| 5 | Osc 1 density | CC 24 |
| 6 | Osc 1 density detune | CC 25 |
| 7 | Osc 1 semitones | CC 26 |
| 8 | Osc 1 cents | CC 27 |
| 9 | Osc 2 wave interpolate | CC 30 |
| 10 | Osc 2 pulse width index | CC 31 |
| 11 | Osc 2 virtual sync depth | CC 33 |
| 12 | Osc 2 density | CC 35 |
| 13 | Osc 2 density detune | CC 36 |
| 14 | Osc 2 semitones | CC 37 |
| 15 | Osc 2 cents | CC 39 |
| 16 | Osc 1 level | CC 51 |
| 17 | Osc 2 level | CC 52 |
| 18 | Ring mod level | CC 54 |
| 19 | Noise level | CC 56 |
| 20 | Filter frequency | CC 74 |
| 21 | Filter resonance | CC 71 |
| 22 | Filter drive | CC 63 |
| 23 | Filter tracking | CC 69 |
| 24 | Env 2 to filter frequency | CC 79 |
| 25 | Env 1 attack | CC 73 |
| 26 | Env 1 decay | CC 75 |
| 27 | Env 1 sustain | CC 70 |
| 28 | Env 1 release | CC 72 |
| 29 | Env 2 attack | NRPN 0:1 |
| 30 | Env 2 decay | NRPN 0:2 |
| 31 | Env 2 sustain | NRPN 0:3 |
| 32 | Env 2 release | NRPN 0:4 |
| 33 | Env 3 delay | NRPN 0:14 |
| 34 | Env 3 attack | NRPN 0:15 |
| 35 | Env 3 decay | NRPN 0:16 |
| 36 | Env 3 sustain | NRPN 0:17 |
| 37 | Env 3 release | NRPN 0:18 |
| 38 | LFO 1 rate | NRPN 0:76 |
| 39 | LFO 1 rate sync | NRPN 0:77 |
| 40 | LFO 1 slew rate | NRPN 0:72 |
| 41 | LFO 2 rate | NRPN 0:85 |
| 42 | LFO 2 rate sync | NRPN 0:86 |
| 43 | LFO 2 slew rate | NRPN 0:81 |
| 44 | Distortion level | CC 91 |
| 45 | Chorus level | CC 93 |
| 46 | Chorus rate | NRPN 1:25 |
| 47 | Chorus feedback | NRPN 1:27 |
| 48 | Chorus mod depth | NRPN 1:28 |
| 49 | Chorus delay | NRPN 1:29 |
| 50 | Mod matrix 1 depth | NRPN 1:86 |
| 51 | Mod matrix 2 depth | NRPN 1:91 |
| 52 | Mod matrix 3 depth | NRPN 1:96 |
| 53 | Mod matrix 4 depth | NRPN 1:101 |
| 54 | Mod matrix 5 depth | NRPN 1:106 |
| 55 | Mod matrix 6 depth | NRPN 1:111 |
| 56 | Mod matrix 7 depth | NRPN 1:116 |
| 57 | Mod matrix 8 depth | NRPN 1:121 |
| 58 | Mod matrix 9 depth | NRPN 1:126 |
| 59 | Mod matrix 10 depth | NRPN 2:3 |
| 60 | Mod matrix 11 depth | NRPN 2:8 |
| 61 | Mod matrix 12 depth | NRPN 2:13 |
| 62 | Mod matrix 13 depth | NRPN 2:18 |
| 63 | Mod matrix 14 depth | NRPN 2:23 |
| 64 | Mod matrix 15 depth | NRPN 2:28 |
| 65 | Mod matrix 16 depth | NRPN 2:33 |
| 66 | Mod matrix 17 depth | NRPN 2:38 |
| 67 | Mod matrix 18 depth | NRPN 2:43 |
| 68 | Mod matrix 19 depth | NRPN 2:48 |
| 69 | Mod matrix 20 depth | NRPN 2:53 |
