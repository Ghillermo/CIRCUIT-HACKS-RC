# SC22.3 — SC22.2 + oscilador v3: la onda es un morph continuo que la envolvente y el LFO mueven, y la forma va de 0 a 100

`circuittracks-4486-SC22.3.syx` — SHA-256 `181f5ec1089c00eead017e277abe646c8c6f5cbe615d32bb1ceb46663f12b462`
Imagen de 0x5e018 bytes, marca `SC22.3`. Es SC22.2 con la página B ampliada; si falla, vuelve a SC22.2 (o SC22).

## Pads (como en SC22.2)
Vista Preset de MIDI 1 / 2: **pad 26** modo VCF / VCA / FX, **pad 27** página B de los knobs (los controles del oscilador), **pad 28** fuente (line in ↔ oscilador).

## Página B de los knobs (pad 27) — asignación pedida
| Knob | Sin Shift | Con Shift |
|---|---|---|
| K1 | **TUNE**: transposición, −64 … +63 semitonos | **FINE**: ±½ semitono |
| K2 | **SHAPE**: forma (duty cycle / wavefold / pendiente), **0 … 100**, 50 = centro | — |
| K3 | **ENV → PITCH**: ±24 semitonos | — |
| K4 | **ENV → SHAPE**: la envolvente mueve la forma | — |
| K5 | **LFO → PITCH**: ±6 semitonos | — |
| K6 | **LFO → SHAPE**: el LFO mueve la forma | — |
| K7 | **WAVE**: waveshape, posición del morph continuo, 0 … 127 | — |
| K8 | **LFO → MORPH**: el LFO recorre las ondas | **ENV → MORPH**: la envolvente recorre las ondas |

Los envíos son bipolares (0 = ninguno, derecha positivo, izquierda negativo).

## El morph (WAVE)
Es una posición continua sobre las cuatro ondas matemáticas: **0 = seno**, **42 = triángulo**, **84 = sierra**, **126 = cuadrada**; entre dos, la mezcla de las dos vecinas (a mitad, la media). Con ENV → MORPH / LFO → MORPH la posición se mueve sola, hasta todo el recorrido con el envío al máximo. Por defecto WAVE = 84 (sierra pura).

## SHAPE (0 … 100), según la onda (se aplica a cada onda de la mezcla)
- **Seno y triángulo: wavefold.** De 0 a 50 (centro) la onda queda limpia; de 50 a 100 se amplifica hasta ×8 y se pliega (más armónicos, el nivel no sube).
- **Sierra: pendiente.** 50 = recta; hacia 100 **parabólica**, hacia 0 **logarítmica**.
- **Cuadrada: ancho de pulso.** 50 = 50 %; de ~3 % (0) a ~97 % (100).

## Prueba (volumen bajo)
1. MIDI 1 → Preset → pad 28 (oscilador) y pad 27 (controles). Toca notas: sierra con la envolvente del VCA.
2. K7 recorre seno → triángulo → sierra → cuadrada de forma continua; K2 (0-100) cambia la forma de cada una (en el seno, de 50 a 100 el wavefold; en la cuadrada, el ancho).
3. K3 / K5: la envolvente / el LFO mueven el tono; K4 / K6: mueven la forma (PWM con la cuadrada); K8 / Shift + K8: el LFO / la envolvente mueven la posición del morph (con la envolvente, un ataque que pasa de seno a cuadrada).
4. Pad 27 otra vez: los knobs vuelven al VCF / VCA / FX. Pad 28 otra vez: vuelve la entrada de línea.

## Notas técnicas
- DSP (`vcf21_dsp.OSC3`, `use_osc3()`): en cada bloque se calculan la posición del morph (WAVE × 0x10410 + ENVM × ENV + LFOM × LV, de 0 a 1; 3q = i + f) y sus cuatro pesos (1 − f para la onda i, f para la i + 1), la forma m = (PW − 50) / 50 + ENVW × ENV + LFOW × LV (saturando) y el parámetro de cada familia (deriva del wavefold, pendiente, umbral); en cada muestra se calculan las cuatro ondas y se suman con sus pesos (≈ 70 instrucciones por muestra y voz con el oscilador encendido). Bloque por voz en `X:$3900 + 48 t`: +0..9 TUNE, FINE, WAVE, PW, LFOP, ENVP, ENVW, LFOW, ENVM, LFOM; +10 fase, +11 incremento, +12 deriva del fold, +13 pendiente, +14 umbral, +15..18 pesos. Códigos del buzón 22-31. El programa termina en `P:$3ADD`.
- ARM (`vcf21.use_osc3()`): 26 valores por pista (stride 26; 25 ENVM, 26 LFOM), cola de 71 de los 75 bytes (firma 0xAC: **al flashear sobre SC22.x el estado del modo se reinicia**); los bits «pendiente de enviar» de los códigos 25 / 26 viven en los bits 5 / 6 del byte AUX del bloque volátil; SHAPE se limita a 100 y WAVE ya no da la vuelta (es una posición).
- Pruebas: `tools/emu_sc22_3_dsp.py` (las cuatro ondas y sus formas mezcladas con pesos bit a bit con todos los envíos, el morph cae en las ondas puras, la media a mitad, anchos de pulso, wavefold, pendiente de la sierra, buzón 22-31, `vret`, oscilador → filtro) y `tools/emu_sc22_3.py` (knobs de la página B, límites 0-100, LEDs, MIDI 2, flujo completo ARM → DSP, firma).
