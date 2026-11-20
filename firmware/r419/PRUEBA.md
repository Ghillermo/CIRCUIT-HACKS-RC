# RC4.19 (marca `R419`) — pendiente de probar, sin publicar

= RC4.18 + `packio.use_pqexp()`. Imagen `0x6f7e4`.

**Arreglo:** la pregunta de borrado de la vista de packs se olvida a los 5 s (su edad de 8 bits volvía a empezar cada 65,5 s: los pads parpadeaban otra vez cada minuto y Clear entonces borraba el pack preguntado).

## Probar
1. Clear, un pack, no borrar: tras 5 s deja de parpadear y no vuelve a parpadear al minuto; Clear entonces no borra nada.

Pruebas `emu_pqexp.py` (RC4.18 falla dos).
