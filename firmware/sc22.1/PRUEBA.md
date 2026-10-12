# SC22.1 — SC22 + oscilador como fuente del modo VCF / VCA y página de knobs del oscilador

`circuittracks-4486-SC22.1.syx` — SHA-256 `2e451d553d599933c4c569c021777d89295f24d6e3494db65c89db2d8b6d77dd`
Imagen de 0x5ddc4 bytes, marca `SC22.1`. Es SC22 con un oscilador por pista MIDI. Si falla, vuelve a SC22 (o SC21.2 / SC20.1).

## Qué hace
En la vista **Preset de MIDI 1 / 2** (la del patch flip) hay ahora tres pads seguidos del modo VCF / VCA:

| Pad | Función | Apagado | Encendido |
|---|---|---|---|
| 26 | modo VCF / VCA / FX (como siempre) | azul tenue | azul brillante |
| **27** | **fuente = oscilador** | tenue | brillante |
| **28** | **página B de los knobs** (los del oscilador) | tenue | color de la pista |

**Pad 27**: la entrada de audio de la pista deja de oírse y en su lugar suena un oscilador, a la altura de las **notas de la pista** (las secuenciadas, las grabadas y las que tocas). Después viene la cadena de siempre: **VCA (envolvente, tremolo, ganancia + saturación) → efecto → filtro**. Al encender el oscilador se ponen **GAIN = 0** y **ENVA = 63** (para que solo suene con las notas); al apagarlo vuelven GAIN = 64 y ENVA = 0. Si el modo estaba apagado, el pad 27 lo enciende también. Es monofónico (la última nota) y sin portamento; la fase corre libre.

**No hay ningún knob (ni Shift) libre**: los 16 puestos de K1-K8 con y sin Shift ya llevaban los 16 controles del modo. Por eso el pad 28 cambia los knobs a una **segunda página**; con el pad 28 apagado, los knobs son los de siempre:

| Knob (página B) | Sin Shift | Con Shift |
|---|---|---|
| K1 | **TUNE**: transposición, −64 … +63 semitonos sobre la nota | **FINE**: afinación fina, ±53 cents |
| K2 | **WAVE**: seno → triángulo → sierra → pulso (un paso por giro, da la vuelta) | **PW**: ancho del pulso (25 % … 75 %, centro = 50 %; solo afecta al pulso) |
| K3 | **LFOP**: vibrato (el LFO de la página A), bipolar, ±1 semitono | — |
| K4-K8 | sin función (LED apagado) | sin función |

El LED de cada knob enseña su valor (WAVE: 4 niveles). El **LFO es el de siempre (diente de sierra inverso)**: el «vibrato» es un barrido de tono que se repite (a velocidad alta suena a «láser», no a vibrato suave); su velocidad es K7 de la página A.

Limitación: si el Setup manda el retorno de reverb / delay a la tira 3 / 4 de esa pista, la tira oye el retorno (no la entrada), así que el oscilador no se oye (usar la tira con su entrada de línea).

## Prueba (volumen bajo)
1. MIDI 1 → Preset → pad 27: se enciende (y el 26 también). Toca notas en la pista (o grábalas): debe sonar una **sierra** con la envolvente; sin notas, silencio.
2. Pad 28 (se ilumina en el color de la pista): K2 recorre seno / triángulo / sierra / pulso; Shift + K2 mueve el ancho del pulso (con el pulso seleccionado); K1 transpone, Shift + K1 afina fino; K3 mete el barrido de tono.
3. Pad 28 otra vez: K1-K8 vuelven a ser los del VCF / VCA: ataque, filtro, efectos (ring mod, comb, chorus), K3 = envío envolvente → VCA bipolar.
4. Comprueba el filtro (K5), la resonancia (K6) y los efectos sobre el oscilador; MIDI 2 con su oscilador independiente.
5. Apaga el pad 27: vuelve la entrada de línea (GAIN 64, ENVA 0). Con el pad 26 apagado todo es de stock.
6. Apagar y encender: los valores y el estado (oscilador, página) se conservan (ajustes globales, no por proyecto).

## Notas técnicas
- ARM (`vcf21.use_osc()`): los valores pasan a **24 códigos por pista** (stride 24; 17-21 = TUNE, FINE, WAVE, PW, LFOP), máscara de cambios de 24 bits (byte `RT_DX`), flags bits 2 / 3 = oscilador de MIDI 1 / 2 y bits 4 / 5 = página B; segunda tabla de knobs (`KNOB_CODES_B`, código 0 = sin función); `ACT` = 0 / 1 / 2 (apagado / modo / oscilador); los códigos del buzón 22-26 (los 17-21 son del propio buzón: GATE, NOTE, ACT, VEL, TRIG). Estado en 67 de los 75 bytes de la cola de los ajustes; firma 0xAA (**al flashear sobre SC22 el estado del modo se reinicia**).
- DSP (`vcf21_dsp.OSC`): segundo bloque por voz en `X:$3900 + 48 t` (TUNE, FINE, WAVE, PW, LFOP, fase, incremento), tabla `TINC` de 128 incrementos de fase (440 Hz a 48 kHz) en el programa; el oscilador (nivel 0,5) sustituye las muestras del anillo de esa entrada en `vpre`, antes de la cadena; `vret` no toca a las voces con oscilador. El programa del DSP termina en `P:$3A35`.
- Los búferes Y del comb / chorus (`Y:$3400-$39FF`) no se ponen a cero al arrancar: la primera vez que se elige uno de esos efectos puede oírse un chasquido muy corto.
- Pruebas: `tools/emu_sc22_1_dsp.py` (las cuatro formas de onda bit a bit, tono / fino / vibrato, el buzón 22-26, el límite de la nota, `vret` sin tocar, oscilador → filtro) y `tools/emu_sc22_1.py` (pads 27 / 28, la página B, LEDs, MIDI 2, el flujo completo ARM → DSP).
