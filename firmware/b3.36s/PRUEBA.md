# Beta 3.36S = Beta 3.36 sin escrituras propias en la SD

`firmware/b3.36s/circuittracks-4486-B3.36S.syx` — SHA-256 `1a53e1695b4019d2540d3f12bf8667f0817dd55770b4ef4b8cdb629bd9377f37`, marca `B3.36S` (**Beta 3.36S**).

El usuario (2026-10-27): «Add 3.36S». La versión más segura de la Beta 3.36, como RC2.10S lo es de RC2.10: `rodisk.use_allpacks()` sobre SC47.9
(`tools/build_beta3_36s.py`). Toda escritura o borrado que pide el mod se rechaza en cualquier pack (LED de Save rojo 1,5 s); los guardados del
firmware original (proyecto, patch, ajustes) pasan siempre. Nada del mod crea, cambia ni borra ficheros en la tarjeta ni en la memoria interna.

## Qué probar
1. Todo lo de la Beta 3.36 ([`firmware/b3.36/PRUEBA.md`](../b3.36/PRUEBA.md)): parejas estéreo de drums y notas del selector de samples. Las dos se
   guardan con el proyecto (bytes del propio proyecto que escribe el original): funcionan igual en la S.
2. Lo que escribe en la tarjeta por su cuenta **no** hace nada y pone el LED de Save en rojo: guardar el sample capturado con el proyecto, intercambiar
   o copiar samples / patches entre packs, guardar patches del sinte propio y del sinte, copiar proyectos, borrar un pack.
3. Guardar el proyecto con Save (dos veces) funciona como siempre.

## Verificación en emulación
- `emu_rodisk.py` frente a SC41.2 (sin guardián): el guardián rechaza las escrituras y los borrados del mod en todos los packs; los del original pasan.
- `emu_stpair.py`, `emu_smnote.py`, `emu_sc45_3.py` sobre la Beta 3.36S.
