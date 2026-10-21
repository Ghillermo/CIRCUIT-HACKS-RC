# RC2.05 / RC2.05S (R205 / R205S) = RC2.04 + un arreglo

`firmware/r205/circuittracks-4486-R205.syx` — SHA-256 `4fd74b577fdbf6001fabbbc2da00b93ec3e35b2949af18dfc661b6409821f458`, marca `R205` (**RC2.05**).
`firmware/r205s/circuittracks-4486-R205S.syx` — SHA-256 `dff2a9f4e4f7ee1b491527f070632a8ec62e2af7f28563aa018e234b7ad39cc3`, marca `R205S` (**RC2.05S**).

**Arreglo: el aparato se colgaba al cambiar la escala propia con el transporte en marcha** (el usuario, 2026-10-21: «durante la reproducción, con al menos una secuencia tocando en cualquier pista, cambiar de escala custom puede llegar a hacer que el aparato se cuelgue y necesita reiniciar»).

Causa: el original enciende los pads de las notas de una pista (el paso mantenido y las notas que suenan; el oyente de almacenes `0x0804B272`, el redibujado `0x0804AE96`) con la nota cuantizada (`0x080408C6`) → la tabla inversa del teclado (`[0x20041044 + 0xF4 + nota]`) → `0x0804AE66(vista, índice)`, que escribe el color en el búfer de LEDs (`0x0804AA40`, sin límite) y en el del enlace (`[0x20041044 + 0x180 + índice]`). Una nota que no está en el teclado da el índice `0xFF` y el color va al búfer + `0x1FE` = `0x20041602`: **dentro de la vista de pista de Synth 2** (`0x200415D4 + 0x2E`, la mitad alta de su puntero de almacén `+ 0x2C`), además de un pad suelto por el enlace leído fuera de la tabla. Con las escalas de stock no pasa (la nota cuantizada siempre está en el teclado); con la escala propia sí: (1) **justo después de cada cambio** el cuantizador ya usa la escala nueva y el teclado se rehace en el siguiente fotograma de la tarea de LEDs: una nota que suena en ese momento (transporte en marcha) da `0xFF`; (2) **un periodo corto no cubre todo el recorrido** (28 filas × P o 2P alrededor de 60: con P = 1 las notas por encima de 79 no están).

Arreglo (`tools/kbguard.py`, zona libre, 16 B): la cabeza de `0x0804AE66` → `c_kbg`: un índice ≥ 224 (28 filas × 8) no enciende nada; los demás, el original. RC2.05S = RC2.04S + lo mismo.

## Qué probar
1. Synth 1 con un patrón sonando (Play). Shift + Scales: cambia la escala propia muchas veces (pon y quita teclas, deprisa) mientras suena: el aparato sigue respondiendo.
2. Una escala propia de periodo corto (solo la tecla de un semitono encima de la tónica): con el patrón sonando y notas altas, nada se cuelga.
3. Lo demás, como RC2.04 (`firmware/r204/PRUEBA.md`).

## Verificación en emulación
- `emu_kbguard.py` (escala de periodo 1 con la nota 100 sonando; el momento después de un cambio; la mayor hecha a mano), por el oyente real de la vista de Synth 1: la build anterior escribe el búfer + `0x1FE` y un pad suelto, esta nada fuera del búfer y los mismos pads; `emu_cscale.py` sobre RC2.05.
