# SC22.2 — SC22.1 + oscilador v2: envolvente y LFO al tono y a la forma, y forma de onda por tipo

`circuittracks-4486-SC22.2.syx` — SHA-256 `ae1e2ecfe1311845e2f18b9b88ce87f2cbef16113759938c915fabe8e44af457`
Imagen de 0x5df4c bytes, marca `SC22.2`. Es SC22.1 con el oscilador rehecho y los pads cambiados; si falla, vuelve a SC22 (o SC22.1).

## Pads de la vista Preset de MIDI 1 / 2 (nuevos o cambiados respecto a SC22.1)
| Pad | Función | Apagado | Encendido |
|---|---|---|---|
| 26 | modo VCF / VCA / FX (como siempre) | azul tenue | azul brillante |
| **27** | **abre los controles del oscilador** (los 8 knobs pasan a la página B) | tenue | color de la pista |
| **28** | **fuente: line in ↔ oscilador** (si el modo estaba apagado, lo enciende) | tenue = line in | brillante = oscilador |

(En SC22.1 los pads 27 y 28 estaban al revés.) Al encender el oscilador se ponen GAIN = 0 y ENVA = 63 (suena solo con las notas de la pista); al volver a line in, GAIN = 64 y ENVA = 0.

## Página B de los knobs (pad 27)
| Knob | Sin Shift | Con Shift |
|---|---|---|
| K1 | **TUNE**: transposición, −64 … +63 semitonos sobre la nota | **FINE**: ±½ semitono |
| K2 | **WAVE**: seno, triángulo, sierra, cuadrada (un paso por giro, da la vuelta) | **SHAPE**: parámetro de la forma (abajo) |
| K3 | **ENV → PITCH**: la envolvente mueve el tono, bipolar, hasta ±24 semitonos | **LFO → PITCH**: el LFO mueve el tono, bipolar, hasta ±6 semitonos |
| K4 | **ENV → SHAPE**: la envolvente mueve el parámetro de forma, bipolar | **LFO → SHAPE**: el LFO mueve el parámetro de forma, bipolar |
| K5-K8 | sin función (LED apagado) | sin función |

Por defecto no hay ningún envío (0): a la derecha el envío es positivo, a la izquierda negativo. La envolvente es la del VCA de esa pista (K1 / K2 de la página A: ataque, decaimiento, sostenido, relajación, con las notas como puerta) y el LFO es el de la página A (velocidad = K7; es un diente de sierra inverso, así que «LFO → pitch» es un barrido que se repite, no un vibrato suave).

## SHAPE (K2 con Shift), según la onda — osciladores matemáticos
- **Seno y triángulo: wavefold.** Del centro a la izquierda no hace nada (onda limpia); hacia la derecha la señal se amplifica hasta ×8 y se pliega sobre sí misma (más armónicos; el nivel no sube).
- **Sierra: pendiente de la rampa.** Centro = recta; a la derecha **parabólica** (arranca lenta y acelera, r²); a la izquierda **logarítmica** (arranca rápida y se frena, 2r − r²).
- **Cuadrada: ancho de pulso.** Centro = 50 %; de ~3 % a ~97 %.
- Con la envolvente / el LFO al shape, el parámetro se mueve en cada bloque de 32 muestras (saturando en los extremos).

## Prueba (volumen bajo)
1. MIDI 1 → Preset → pad 28: oscilador encendido (el 26 también). Toca notas: suena una **sierra** con la envolvente; sin notas, silencio. Pad 28 otra vez: vuelve la entrada de línea.
2. Pad 27: página B. K2 recorre las cuatro ondas; Shift + K2 mueve la forma de cada una (wavefold en seno y triángulo, curva en la sierra, ancho en la cuadrada).
3. K1 / Shift + K1: transposición y afinación fina. K3: con la envolvente a la derecha el tono cae desde arriba hacia la nota («zap»); Shift + K3: barrido del LFO.
4. K4 / Shift + K4: la forma se mueve con la envolvente / el LFO (por ejemplo, PWM con la cuadrada).
5. Pad 27 otra vez: los knobs vuelven al VCF / VCA / FX (K3 = envolvente → VCA, etc.). El filtro, la resonancia y los efectos siguen actuando sobre el oscilador.
6. MIDI 2: su oscilador y su página son independientes. Apagar y encender conserva todo (ajustes globales, no por proyecto).

## Notas técnicas
- DSP (`vcf21_dsp.OSC2`, `use_osc2()`): el tono pasa por un registro en semitonos con 16 bits de fracción (nota + TUNE + FINE + ENVP × ENV × 24 + LFOP × LV × 6), interpolado linealmente entre los pasos de la tabla `TINC` (129 entradas); la forma `m` = (SHAPE − 64) / 64 + ENVW × ENV + LFOW × LV (satura) se convierte por bloque en el parámetro de la onda (deriva del wavefold 0,125 + 0,86 · max(m, 0), curva `m`, umbral 0,94 · m); el wavefold usa el desbordamiento de 24 bits como módulo (f(p) = 1 − 2 |p − ½| con p envuelto). Bloque por voz en `X:$3900 + 48 t` (`+8` fase, `+9` incremento, `+10` parámetro de la forma); códigos del buzón 22-29. El programa del DSP termina en `P:$3AAF`.
- ARM (`vcf21.use_osc2()`): 24 valores por pista (17 TUNE, 18 FINE, 19 WAVE, 20 PW, 21 LFOP, 22 ENVP, 23 ENVW, 24 LFOW), firma 0xAB (**al flashear sobre SC22.x el estado del modo se reinicia**).
- **Fallo del ensamblador encontrado:** `mpy x0,y0,b` se codifica en una forma larga que trata `y0` como **sin signo** (con `y0` negativo da un resultado erróneo). Hay que escribir `mpy y0,x0,b`. SC20-SC22 solo lo usan con `y0` positivo (sin efecto), pero **SC22.1 lo usa en el vibrato**: con LFOP negativo SC22.1 da un tono equivocado (SC22.2 lo corrige).
- Pruebas: `tools/emu_sc22_2_dsp.py` (las cuatro ondas y sus formas bit a bit con todos los envíos, el centro = la onda limpia, anchos de pulso, cruces por cero del wavefold, buzón 22-29, `vret`, oscilador → filtro) y `tools/emu_sc22_2.py` (pads 27 / 28, página B, LEDs, MIDI 2, flujo completo ARM → DSP).
