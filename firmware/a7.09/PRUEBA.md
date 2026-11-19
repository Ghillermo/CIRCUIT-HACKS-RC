# Alpha 7.09 (marca `A7.09`) — pendiente de probar, sin publicar

= Alpha 7.08b + `fm8ui.use_p8alg()` (el usuario, 2026-11-19: «what does pad 8 do now? can we move shift+7 to 8?» → «shift 7 no longer»): en la página FM del sinte propio de MIDI 1 / 2,
- **pad 8 mantenido = la lista de los 56 algoritmos** mientras lo mantienes (Octave ▼ / ▲ = sus tres páginas, pulsa uno = elegido y suena; el pad 8 brillante mientras tanto); un toque sigue abriendo la página FM;
- **Shift + pad 7 ya no hace nada** (antes, la lista); el pad 7 (mapa del algoritmo, Clear + pad 7 = la voz) sin cambios.

Desde la Beta 5.58 el pad 8 solo abría la página FM (los 48 instrumentos se quitaron). Imagen `0x6fbb8`.

## Probar
MIDI 1 con el FM: abre la página FM (pad 7 o pad 8).
1. Mantén el pad 8: los algoritmos en los pads 9-32 (página 1: 4 operadores verde azulado, 8 operadores ámbar); Octave ▼ / ▲ cambia de página; pulsa uno: elegido y suena. Suelta: vuelven los operadores.
2. Shift + pad 7 (mantenido): nada.
3. Pad 7: el mapa como antes.

Pruebas: `emu_fmmap.py` (pad 8 mantenido = la lista, elige; Shift + pad 7 = nada).
