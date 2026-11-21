# Alpha 7.22 (marca `A7.22`) — pendiente de probar, sin publicar

= Alpha 7.21 + `projinit.use_clear()` + `clrtrk.use_callable()` (el usuario, 2026-11-21: «clear+track should load init saved for the project … right
now, it restores back to patch default instead» → «switch them. clear+track=session default. Shift+preset: preset initial state»). Imagen `0x6f774`.

- **Clear + Synth 1 / 2** (o **Clear + MIDI 1 / 2** con el sinte propio), en una vista de esa pista = **el sonido guardado en el proyecto** (el
  estado con que se carga el proyecto; lo que hacía Shift + Preset).
- **Shift + Preset** = **el estado inicial del preset**: Synth 1 / 2 sus 8 macros como están en el patch del pack; MIDI 1 / 2 los valores por
  defecto del sinte propio (lo que hacía Clear + la pista).
- Los drums, como antes.

## Probar
1. Synth 1: cargar un proyecto, girar macros, Clear + Synth 1: vuelven a como estaban al cargar el proyecto.
2. Shift + Preset: los macros como están en el patch del pack.
3. MIDI 1 con el sinte propio: lo mismo (Clear + MIDI 1 = el del proyecto; Shift + Preset = valores por defecto).

Prueba `emu_cleartrk.py` (5).
