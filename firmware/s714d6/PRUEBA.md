# S714D6 (marca `S714D6`) — diagnóstico

= S714D3 + `blackbox.use_safeclear()`. Imagen `0x6fee8`.

**Los «cuelgues» de las pruebas de estrés (PC 0, LR 0, r12 = la caja negra) los causaba la propia herramienta:** el vaciado de la caja negra (SysEx 02, «Vaciar» en la app) ponía a 0 todo el registro, también el LR y el fotograma que guarda su cabeza de la tarea de LEDs (`O.LR` / `O.FR`); si llegaba mientras la tarea de LEDs corría la cadena de debajo, la cabeza volvía por 0. Ahora el vaciado deja esas dos palabras. **Es un fallo real de todas las builds con caja negra (Beta 5.51 y posteriores, las alfas): vaciar desde la app puede, rara vez, reiniciar el aparato.** Prueba `emu_safeclear.py` (S714D3 falla).
