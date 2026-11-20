# Alpha 7.11 (marca `A7.11`) — probada en el aparato (2026-11-20: el pad se apaga; Duplicate sobre el hueco funciona sin reiniciar), sin publicar

= Alpha 7.10 + `packio.use_delled()` (arreglo; el usuario, 2026-11-20: «When I delete a pack, I want that pack's led to turn off. Right now, it won't signal the deletion until reboot»): **un pack borrado apaga su pad al momento** en la vista de packs.

La vista de packs pinta el pad k con el byte k de su almacén `[vista + 0x14]` (`0x0804412A`: el color del pack; `0xFF` = hueco vacío, apagado), que se llena al leer la tarjeta al arrancar; el borrado no lo tocaba. Ahora, si el borrado funciona (`0x0803CC34` devuelve 0), `c_mbp` escribe `0xFF` ahí (`0x080354FA` + commit `0x080353C0`) y el oyente de la propia vista (ranura 9, `0x080440BA`) redibuja el pad. Imagen `0x6fc2c`.

## Probar
1. Vista de packs (Shift + Projects): Clear, un pack que no sea el cargado, Clear.
2. Ese pad se apaga al momento; los demás siguen igual.
3. Salir y volver a la vista: sigue apagado.
4. Opcional: Duplicate + ese hueco (duplicar el pack cargado ahí) — antes no se podía hasta reiniciar; sin probar.

Prueba `emu_delled.py` (la 7.10 / RC4.17S fallan tres).
