# RC2 / RC2S = SC44 (Beta 1.30) como segunda versión candidata

`firmware/rc2/circuittracks-4486-RC2.syx` — SHA-256 `8093c57e8b67d46e3eb2f3981c6f1ef5ae5681914843c146ebd31162ceb91742`, marca `RC2`: el código de SC44 / Beta 1.30.
`firmware/rc2s/circuittracks-4486-RC2S.syx` — SHA-256 `77db259bedc8687e2cb544256905055e73f0b7b78c27e4b69af72558ba0bd418`, marca `RC2S`: la **versión más segura**: RC2 + `rodisk.use_allpacks()`.

El usuario (2026-10-17): «Rename to RC2» · «New RC + RC2S».

- **RC2** = RC0.9 + todo lo de las betas 1.0-1.30 (ver `CHANGELOG.md`); lo nuevo de Beta 1.30: el modo muestra del sinte propio de MIDI 1 / 2 (`firmware/sc44/PRUEBA.md`).
- **RC2S** = RC2, pero toda escritura o borrado en la tarjeta o en la memoria interna que pida el mod se rechaza, en cualquier pack (el LED de Save en rojo 1,5 s); los guardados del original (proyecto, patch, ajustes) pasan. No hacen nada: guardar la captura con el proyecto, intercambiar / copiar samples y patches entre packs, los patches del sinte propio, guardar el patch del sinte, copiar proyectos, borrar packs.

## Qué probar
1. RC2: lo de `firmware/sc44/PRUEBA.md` y las betas anteriores.
2. RC2S: guardar un proyecto (se guarda; el LED de Save normal). Guardar un patch propio (Clear + pad dos veces en la vista Preset de MIDI 1 / 2): el LED de Save rojo, nada escrito. Duplicate de un proyecto a otro hueco en la vista Projects: rojo, nada copiado. Borrar un pack: rojo, el pack sigue ahí.
3. En las dos: el aparato arranca, carga y guarda proyectos como siempre.

## Verificación en emulación
- `emu_rodisk.py` (frente a SC41.2): RC2 = el pack 0 de solo lectura para el mod, los packs de la tarjeta pasan; RC2S = toda escritura y borrado del mod rechazados (cualquier pack, también `0xFF` con un pack de la tarjeta cargado), con `0xFFFFFFFD` y el LED de Save rojo.
- `emu_sc44.py`, `emu_sc43_9.py`: todo pasa en las dos.
