# SC23.6 — SC23.5 + knobs de tipo sin vuelta y con parámetro interno (tipo de FX, tipo de filtro, forma de onda)

`circuittracks-4486-SC23.6.syx` — SHA-256 en `manifest.json` (`syx_sha256`)
Marca `SC23.6`. Reserva: SC23.5 (confirmado por el usuario: el oscilador ya no falla). Probado en emulación; **nada probado en el aparato**.

## Qué cambia
Los tres knobs «de tipo» eran demasiado sensibles (un clic = un tipo) y daban la vuelta. Ahora:
- **Sin vuelta:** al llegar al último tipo, seguir girando se queda; igual hacia el primero.
- **Varios clics por modo:** el knob tiene 0..127 pasos; el FX y el filtro tienen **7 modos** → unos **18 clics por modo**. La forma de onda tiene 4 modos con **42 clics** entre una forma pura y la siguiente (como antes: ya era un morph continuo).
- **Dentro de cada modo, la posición ajusta un parámetro:**
  - **Tipo de FX** (Shift + K8): el parámetro del efecto, el «morph» (lo que antes era Shift + K7 = FXMOD; **Shift + K7 ya no hace nada**). Soft / hard / fold: umbral; wavefold: sesgo; ring mod: frecuencia; comb: retardo; chorus: velocidad.
  - **Tipo de filtro** (Shift + K5): **el seguimiento de la nota en el corte del filtro** (key follow). 0 = no sigue; a los 2/3 del modo (≈ 85 de 127) = una octava por octava (la tabla del corte da 8 pasos por octava); 127 = 1,5 octavas por octava. Antes era fijo (37 %).
  - **Forma de onda** (página B del OSC, K7): el morph hacia la siguiente forma (seno → triángulo → sierra → cuadrada), sin cambios en el sonido.

## LEDs (colores de Novation; no se pueden fijar RGB propios, solo la paleta)
El LED del knob muestra **el color = el modo elegido** y **el brillo = el parámetro dentro del modo** (el morph / el follow): más tenue al empezar el modo (33 %), pleno al final del modo.
| Knob | Modos (de menor a mayor) |
|---|---|
| Shift + K8, tipo de FX | soft **amarillo** · hard **naranja** · fold **rojo** · wavefold **magenta** · ring mod **violeta** · comb **azul** · chorus **verde azulado** |
| Shift + K5, tipo de filtro | DJ **blanco** · LP 12 **verde** · HP 12 **azul claro** · paso banda **amarillo** · notch **magenta** · LP 24 **verde azulado** · HP 24 **azul** |
| Página B, K7, forma de onda | seno **azul claro** · triángulo **verde** · sierra **amarillo** · cuadrada **rojo** |
Los LEDs de Shift se ven con Shift pulsado. Si prefieres fusión de colores en lugar de brillo para el morph, se puede hacer eligiendo entradas de la paleta intermedias (no hay RGB libre); dímelo.

## Pruebas en el aparato
1. Vista de MIDI 1 con el modo VCA-VCF encendido (pad 29). Mantén Shift y gira **K8** a pasos: ~18 clics por color; al final del recorrido no vuelve al principio; al principio no salta al final. El brillo crece dentro de cada color y se reinicia al cambiar.
2. Mantén Shift y gira **K5**: lo mismo con los colores del filtro. Con un tono en la entrada y el filtro en un tipo LP / HP (FILT a media carrera), toca notas altas y bajas: con el brillo al máximo el corte sigue la nota; al mínimo, no.
3. Página del oscilador (pad 28), **K7**: 4 colores, el brillo marca el morph dentro de cada forma.
4. Shift + K7 ya no hace nada (LED apagado).
5. Clear + K8 / K5 / K7: el tipo vuelve al primero.
**Estado guardado:** los valores de SC23.5 se descartan al arrancar (cambia el significado de los de tipo): el aparato vuelve a los valores neutros del VCA-VCF y del oscilador.

## Cómo funciona (para depurar)
- Valor guardado de los códigos 13 / 16 = p (0..127); al DSP va p tal cual. El DSP calcula zona `t = 7p >> 7` y posición `f = 7p & 127`: guarda `t` en el slot del código y `f` en FXMOD (código 13) o en la palabra +19 del bloque del oscilador (código 16, `KEYF`). El código 14 (FXMOD) se ignora. Corte del filtro: índice de tabla += (nota − 60) × f / 128.
- LEDs: `vcf21.c_vtype` + tabla de colores `TCOL_FX / TCOL_FT / TCOL_WV`; brillo = 32 + f × 95 / 128.

## Pruebas de emulación
`emu_sc23_6.py` (clics, tope sin vuelta, LEDs, Shift + K7, Clear), `emu_sc23_6_dsp.py` (mailbox: zona y parámetro, código 14 ignorado, el corte sigue la nota; coste +8 instrucciones por bloque) y las de SC23.5 sobre esta imagen.
