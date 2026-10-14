# SC39.7 — gesto mecánico en lugar del Vinyl

`circuittracks-4486-SC39.7.syx` — SHA-256 `60e546d497dbedf10e3b548c9b35078a23c2202293421e1b932d1006cbc7dbc8`
Imagen de 0x68488 bytes, CRC 0xb6043d91, marca `SC39.7`.

Es SC39.6 con un cambio en Master FX (solo ARM): **el Vinyl desaparece y su pad (el 6) es un gesto mecánico** sobre la salida master: al pulsar, la música se para como si alguien frenara el plato; al soltar, arranca con el gesto contrario. Usa el motor del Glitch (pad 31), así que no pueden sonar los dos a la vez: manda el gesto.

## Manejo
- **Pad 6 pulsado** = la parada (se queda parado mientras lo mantienes). **Soltar** = el arranque. Shift + pad lo deja fijado, como los demás efectos; también vale desde un hueco de la fila inferior o desde el secuenciador de efectos.
- Knobs (con el pad 6 elegido):

| Knob | Qué hace |
|---|---|
| K1 | Movimiento: cuántos vaivenes hace la mano en un gesto (1 a 8). Solo cuenta en los scratches |
| K2 | Tipo, de forma continua: **tape stop** → **baby scratch** → **tear scratch** → **back spin** → **rattle**. Las posiciones intermedias mezclan los dos vecinos |
| K3 | Tiempo de la parada (de un instante a unos 4 s) |
| K4 | Tiempo del arranque |

## Qué probar
1. K2 a la izquierda (tape stop), K3 a media altura: pulsa el pad 6 → la música baja de tono y se para; suelta → vuelve a arrancar. ¿Queda en silencio parado? ¿Hay chasquido al terminar el arranque?
2. K2 hacia el centro: scratch de vaivén (baby), y un poco más allá, a tirones (tear). Sube K1: más vaivenes.
3. K2 a la derecha: back spin (hacia atrás y frena) y, al final, rattle (repeticiones cada vez más cortas).
4. Posiciones intermedias de K2: deben sonar a mezcla de los dos tipos vecinos.
5. K3 / K4 al mínimo y al máximo.
6. El Glitch (pad 31) antes y después de un gesto: debe funcionar igual que antes. Pulsados a la vez manda el gesto.
7. Los otros efectos de Master FX, el sample y el song pointer: como antes.
8. Di qué curvas o tiempos cambiarías: son constantes.
9. Todo lo de `firmware/sc39.6/PRUEBA.md`.

## Verificación en emulación
- `emu_sc39_7.py`: 27 gestos (3 valores de K1 × 9 de K2), cada tick de la parada, la espera y el arranque comparado con un modelo; el bit del Vinyl no llega nunca al DSP; sin gesto no hay lecturas del DSP; SC39.6 sin cambios.
- **Sin comprobar en emulación:** el sonido (el motor del Glitch no se emula aquí con audio).
