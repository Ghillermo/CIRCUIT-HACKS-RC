# Referencia MIDI de las funciones nuevas — CIRCUIT-HACKS (RC0.9)

Los CC / NRPN que añade el mod. Los parámetros del aparato original (sintes, drums, mixer, FX) siguen con los números de la *Programmer’s Reference Guide* de Novation. Todo respeta los filtros CC Tx / CC Rx de la vista Setup.

## Seleccionar un NRPN

Manda **CC 99** (MSB), **CC 98** (LSB) y **CC 6** (valor), en ese orden. El aparato recuerda el NRPN elegido hasta el siguiente CC 99 / 98.

## Motor de las pistas MIDI (MIDI 1 / 2)

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
| 28 | FINE 2 (granular: fino) | CC 39 | 3 / Shift + K1 |
| 29 | WAVE 2 (granular: dispersión del tono) | CC 30 | 3 / K7 |
| 30 | SHAPE 2 (granular: ventana) | CC 31 | 3 / K2 |
| 31 | MIX OSC 1 ↔ OSC 2 | CC 52 | 2 / Shift + K2 |
| 32 | BITSYNC | NRPN 4:32 | 2 / Shift + K3 |
| 33 | FM (granular: dispersión de la posición) | NRPN 4:33 | 3 / Shift + K2 |
| 34 | RING (granular: reverso) | CC 54 | 3 / Shift + K3 |

**Página 4** (secuenciables: se graban en el patrón con Record): TUNE, Release, Envolvente → nivel, Envolvente → filtro, Filtro, Resonancia, Velocidad del LFO, Efecto.

## Drums

Canal de drums (Setup). **CC 99 = 5, 6, 7, 8** (Drum 1-4), **CC 98 = LSB**, **CC 6 = valor**. Los knobs de stock (pitch, decay, distortion, EQ) siguen con sus CC originales.

| LSB | Parámetro | Valores |
|---|---|---|
| 1 | Envolvente → tono | 0-127, 64 = 0 |
| 2 | Ring mod: frecuencia | 0-127 |
| 3 | LFO: cantidad | 0-127, 64 = 0 |
| 4 | LFO: velocidad | 0-127, 64 = centro |
| 5 | Envolvente → corte | 0-127, 64 = 0 |
| 6 | Resonancia | 0-127 |
| 7 | Forma de la envolvente | 0-127, 64 = centro |
| 8 | Ring mod: cantidad | 0-127 |
| 9 | Modo de filtro | 0 EQ tilt de stock, 1 paso banda, 2 notch, 3 comb, 4 DJ |
| 10 | Inicio del sample | beta: 0-120 (/128); RC: 0-15 (/64) |
| 11 | Bitcrush | 0-15 |
| 12 | Tipo de distorsión | 0 stock, 1 suave, 2 dura, 3 plegada |
| 13 | Corte desde el final (solo beta) | 0-120 (/128) |
| 14 | Ataque (solo beta) | 0-127 |

## Master FX

Canal 16. **CC 99 = 9**, **CC 98 = 4 × efecto + knob** (knob 0-3 = K1-K4), **CC 6 = valor**.

| LSB | Efecto | K1-K4 |
|---|---|---|
| 0-3 | Gater | división, profundidad, ancho, suavizado |
| 4-7 | Auto-Filter (pads 2 / 3) | velocidad, profundidad, resonancia, centro |
| 8-11 | Digitise | muestreo, bits, envío al delay (beta), envolvente (beta) |
| 12-15 | Phaser | velocidad, profundidad, realimentación, mezcla |
| 16-19 | Vinyl (RC) / Glitch (beta) | RC: crackle, siseo, tono, desgaste; beta: velocidad, repetición, retraso, caos |

## Program Change

**Proyecto:** canal de escucha y canal de salida en la vista Setup, pads 29 / 30 (16 por defecto; solo beta); lo recibido en el de escucha se reenvía por el de salida. **Patch flip:** cada nota de MIDI 1 / 2 sale como Program Change por el canal de la pista (vista Preset de MIDI, pad 26).
