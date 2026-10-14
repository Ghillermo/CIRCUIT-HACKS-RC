# SC39.8 — Digitise: envío momentáneo al delay

`circuittracks-4486-SC39.8.syx` — SHA-256 `38578a4e1041285d3ed3d88e0a8c9d828eff0594bb270e0bba9479316c49b86e`
Imagen de 0x68740 bytes, CRC 0xe889b921, marca `SC39.8`.

Es SC39.7 con un control nuevo en Master FX (solo ARM): **K3 de Digitise = envío al delay**. Mientras mantienes el pad 4 (Digitise), las ocho pistas mandan al delay el nivel de K3; al soltar, cada envío vuelve a su valor.

## Knobs de Master FX (revisados contra el código)
| Pad | Efecto | K1 | K2 | K3 | K4 |
|---|---|---|---|---|---|
| 1 | Gater | división | profundidad | ancho | suavizado |
| 2 / 3 | Auto-Filter | velocidad | profundidad | resonancia | frecuencia central |
| 4 | Digitise | reducción de muestreo | reducción de bits | **envío al delay** (nuevo) | — (no hace nada) |
| 5 | Phaser | velocidad | profundidad | realimentación | mezcla |
| 6 | Gesto mecánico (SC39.7) | movimiento | tipo | tiempo de parada | tiempo de arranque |

Antes, K3 y K4 de Digitise se encendían pero no hacían nada, y el manual describía mal Auto-Filter, Digitise y Vinyl.

## Qué probar
1. Master FX, pon un delay audible en la vista FX. Mantén el pad 4: todo entra en el delay (y suena el Digitise); suelta: los envíos vuelven. Mira la vista FX después: los envíos de delay están como antes.
2. K3 a cero: el pad 4 solo hace Digitise. K3 a medias: envío más suave.
3. Shift + pad 4 (fijado): Digitise fijo, sin envío.
4. Mantén el pad 4 y pulsa otro botón de vista sin soltarlo: los envíos deben volver.
5. ¿Se nota un escalón o un clic al entrar el envío? (No hay rampa.)
6. Todo lo de `firmware/sc39.7/PRUEBA.md`.

## Verificación en emulación
- `emu_sc39_8.py` (pad y botones reales, los parámetros del proyecto leídos con el lector de stock): los ocho envíos a K3 y de vuelta, la reverb intacta, K3 = 0, el latch, la salida de la vista con el pad pulsado, el semáforo del DSP equilibrado, SC39.7 sin cambios.
- **Sin comprobar en emulación:** el sonido y el MIDI que sale al cambiar los envíos.
