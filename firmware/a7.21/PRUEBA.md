# Alpha 7.21 (marca `A7.21`) — pendiente de probar, sin publicar

= Alpha 7.20 + `tools/msdcut.py` (el usuario: «Cut unused stock features» → «Easy Start USB drive»). Imagen `0x6f744`: **2 236 B libres** (+964).

- **Sin el modo de unidad USB del stock (Easy Start):** el aparato es siempre USB MIDI; activar Easy Start en Setup no hace nada y su LED queda
  apagado. Lo demás de USB (MIDI, Components, la app) igual.
- El manejador de órdenes de disco que ya nada llama (`0x0803B27C-0x0803B732`, 1 206 B) se vacía y la vista de macros global pasa ahí (918 B).

## Probar
1. Conectar por USB: aparece como MIDI; Components y la app conectan.
2. Setup: el pad de Easy Start no cambia nada (LED apagado); desconectar y volver a conectar: sigue siendo MIDI.
3. La vista de macros global (Mixer + Patterns) funciona como en la 7.20.
