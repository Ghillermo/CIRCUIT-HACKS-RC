# Alpha 7.13 (marca `A7.13`) — pendiente de probar, sin publicar

= Alpha 7.11 + `packsave.use_bbonly()` + `packio.use_pqexp()` (el usuario, 2026-11-20: «Discard the new save feature, we need the room»): la Alpha 7.12 sin «Save + pad vacío»; sus dos arreglos se quedan. Imagen `0x6fc78` (+76 B sobre la 7.11).

- **La caja negra ya no enciende Save violeta** durante una copia (Duplicate + pad) o un borrado de pack: el latido a 0 antes.
- **La pregunta de borrado se olvida a los 5 s** (volvía a parpadear cada 65,5 s y Clear borraba entonces el pack preguntado).

## Probar
1. Vista de packs: Clear, un pack, no borrar: tras 5 s deja de parpadear y **no vuelve al minuto**; Clear entonces no borra nada.
2. Borrar un pack grande, o Duplicate + un hueco vacío: Save no se pone violeta.

Pruebas `emu_pqexp.py` (la 7.11 falla dos), `emu_delled.py`, `emu_showall.py`, `emu_blackbox2.py`.
