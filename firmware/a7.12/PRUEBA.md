# Alpha 7.12 (marca `A7.12`) — **descartada** (el usuario, 2026-11-20: «Discard the new save feature, we need the room»): sus arreglos van en la Alpha 7.13

= Alpha 7.11 + `tools/packsave.py` + `packio.use_pqexp()`. Imagen `0x6fe98`.

**Guardar como pack nuevo** (el usuario: «saving the current pack to a new slot with save->target pad, just like stock Rhythm» → «2 and 3 are alright. do it»): en la vista de packs, **Save, luego un pad vacío** = el pack cargado se copia ahí (el duplicado de stock), el proyecto cargado se guarda en la copia con sus cambios (el guardado de stock con p0 de `0x200111CC` = el pack nuevo durante la llamada) y se carga el pack nuevo, con el mismo número de proyecto. Pack con contenido, el cargado, el interno o el transporte en marcha = nada, Save rojo 1,5 s. Save armado: los pads vacíos en amarillo; mientras dura, Save blanco.

**Arreglos:** la caja negra ya no enciende Save violeta durante una copia o un borrado de pack (el latido a 0 antes); la pregunta de borrado se olvida a los 5 s (su edad de 8 bits volvía a empezar cada 65,5 s: los pads parpadeaban otra vez y Clear borraba el pack preguntado).

## Probar
1. Vista de packs (Shift + Projects): Save, un pad vacío (amarillo). Save blanco unos segundos; se carga el pack nuevo con el proyecto y sus cambios. El pack de antes, sin cambios (cárgalo y compruébalo).
2. Save, un pad con pack: nada, Save rojo.
3. Clear, un pack, no borrar: tras 5 s deja de parpadear y **no vuelve a parpadear al minuto**; Clear entonces no borra nada.
4. Borrar un pack grande: Save no se pone violeta.

Pruebas `emu_packsave.py`, `emu_pqexp.py` (la 7.11 falla dos), `emu_delled.py`, `emu_showall.py`.
