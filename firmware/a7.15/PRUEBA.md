# Alpha 7.15 (marca `A7.15`) — pendiente de probar, sin publicar

= Alpha 7.14 + `blackbox.use_safeclear()` + `tools/bbwait.py` (dos arreglos encontrados con la prueba de estrés del panel, S714D2-S714D6). Imagen `0x6fc9c`.

- **Vaciar la caja negra (app: Caja negra… → Vaciar) podía reiniciar el aparato:** ponía a 0 también el LR que su cabeza de la tarea de LEDs guarda mientras corre la cadena de debajo. Ahora deja esas dos palabras.
- **Sin falsos «bloqueos» (Save violeta) mientras el panel espera a la tarjeta:** un intercambio / copia de samples, guardar un patch, copiar un proyecto: la petición síncrona del bucle principal a la tarea de almacenamiento pone antes el latido de la caja negra a 0.

## Probar
1. Vista Preset de un drum: Duplicate + un sample + otro (en un pack de prueba): Save no se pone violeta.
2. Con un registro en la caja negra, Vaciar desde la app varias veces mientras suena: el aparato sigue.

Pruebas `emu_bbwait.py`, `emu_safeclear.py` (más las de la 7.14).
