# Beta 3.37S = Beta 3.37 sin escrituras propias en la SD

`firmware/b3.37s/circuittracks-4486-B3.37S.syx` — SHA-256 `6d81f07c5282c3f994f1ac7f1c93704c5a3012d3acc2f8d61ca9496f9b586254`, marca `B3.37S` (**Beta 3.37S**).

El usuario (2026-10-27): «Does the last published Beta have an S version? If not, make it». La versión más segura de la Beta 3.37, como RC2.10S
lo es de RC2.10: `rodisk.use_allpacks()` sobre SC48 (`tools/build_beta3_37s.py`). Toda escritura o borrado que pide el mod se rechaza en cualquier
pack (LED de Save rojo 1,5 s); los guardados del firmware original (proyecto, patch, ajustes) pasan siempre. Nada del mod crea, cambia ni borra
ficheros en la tarjeta ni en la memoria interna.

## Qué probar
1. Todo lo de la Beta 3.37 ([`firmware/b3.37/PRUEBA.md`](../b3.37/PRUEBA.md)). La curva de velocity y el Note del Setup se guardan con los ajustes
   del aparato (el guardado del original): funcionan igual en la S.
2. Lo que escribe en la tarjeta por su cuenta **no** hace nada y pone el LED de Save en rojo: guardar el sample capturado con el proyecto, intercambiar
   o copiar samples / patches entre packs, guardar patches del sinte propio y del sinte, copiar proyectos, borrar un pack.
3. Guardar el proyecto con Save (dos veces) funciona como siempre.

## Verificación en emulación
- `emu_rodisk.py` frente a SC41.2 (sin guardián): el guardián rechaza las escrituras y los borrados del mod en todos los packs; los del original pasan.
- `emu_cueprev`, `emu_stpair`, `emu_smnote2`, `emu_fmstart`, `emu_velcurve`, `emu_midipre`, `emu_notearp`, `emu_notecyc`, `emu_polygain` sobre la Beta 3.37S.
