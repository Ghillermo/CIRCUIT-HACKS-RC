# RC4.19S (marca `R419S`) — pendiente de probar, sin publicar

= RC4.18S + `packio.use_pqexp()`. Imagen `0x6f7d4`.

**Arreglo:** la pregunta de borrado se olvida a los 5 s (en la S el borrado del mod falla siempre, pero los pads volvían a parpadear cada minuto).

## Probar
1. Clear, un pack, no borrar: tras 5 s deja de parpadear y no vuelve a parpadear al minuto.

Pruebas `emu_pqexp.py`.
