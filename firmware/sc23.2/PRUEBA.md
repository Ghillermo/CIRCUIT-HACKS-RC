# SC23.2 — SC23.1 + toggles de MIDI 1 / 2 aclarados: pad 27 fuente, pad 28 vista OSC, pad 29 vista VCA-VCF

`circuittracks-4486-SC23.2.syx` — SHA-256 `d67c888dc2160e3dcf1ca7b1912b76dd5715e4fe981aaee7b0191caf021929d7`. Marca `SC23.2`. Es SC23.1 (editor de CC con Octave / MIDI / descarte) con la fila de abajo de la vista Preset de MIDI 1 / 2 reorganizada. Si falla, vuelve a SC23.1.

## Fila de abajo de la vista Preset
| Pad | Función | Encendido |
|---|---|---|
| 25 | modo edición de CC (magenta) | mientras el editor está activo |
| 26 | patch flip | como en stock |
| 27 | **fuente del principio de la cadena**: línea ↔ oscilador | verde = **OSC**; apagado = **line in** |
| 28 | **vista de parámetros del OSC** (los 8 knobs de la página B) | verde, mientras está elegida |
| 29 | **vista de parámetros del VCA-VCF** (los 8 knobs de la página A) | naranja, mientras está elegida |

## Reglas
- **Pad 27** solo cambia la fuente (no enciende ni apaga el modo). Con el modo apagado el cambio queda guardado y se aplica al encenderlo.
- **El modo VCA-VCF se enciende al tocar el pad 28 o el 29** (queda en esa vista) y **sigue activo mientras uno de los dos esté encendido**. Pasar de uno a otro cambia de vista sin apagar el modo. **Pulsar el que ya está encendido apaga el modo** (los dos quedan apagados).
- El patch flip y el modo se excluyen como antes (pulsar uno apaga el otro).

## Prueba
1. MIDI 1 → Preset: los pads 27 / 28 / 29 apagados (tenues). Pad 29: se enciende, el modo está activo y los knobs son VCA / VCF / FX.
2. Pad 28: se enciende el 28 y se apaga el 29; los knobs son los del oscilador (TUNE, SHAPE, …). El modo sigue activo (el sonido no se corta).
3. Pad 29 otra vez cambia de vista. Pulsa el pad encendido: el modo se apaga (los dos tenues, el sinte como stock).
4. Pad 27 con el modo apagado: se enciende (OSC) pero no cambia el sonido; pad 28 o 29: el modo entra con el oscilador como fuente. Pad 27 otra vez: vuelve a la entrada de línea.
5. MIDI 2 igual, independiente.

## Notas técnicas
- `vcf21.use_pads2()` (`PADS2`): `vp_view` (pads 28 / 29), `vp_osc` sin forzar el modo, LEDs de `c_vleds`. SC23.1 y anteriores idénticas.
- Pruebas: `tools/emu_sc23_2.py` (batería de SC23 con el flujo nuevo) y `tools/emu_sc23_1_ed.py` sobre esta imagen.
