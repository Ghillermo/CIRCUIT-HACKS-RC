# SC45.7 / Beta 3.14 (SC45.7 / B3.14) = SC45.6 + un arreglo

`firmware/sc45.7/circuittracks-4486-SC45.7.syx` — SHA-256 `73bd91183b85aa3127277a6f01f671edbffd2dde225b5e1537152512d5126769`, marca `SC45.7`.
`firmware/b3.14/circuittracks-4486-B3.14.syx` — SHA-256 `ed3e527f3830429825f57abead306dac35bf92e8dc778fa9e8d0d411a8f2a351`, marca `B3.14` (**Beta 3.14**).

**Arreglo (también en RC2.05 / RC2.05S): el aparato se colgaba al cambiar la escala propia con el transporte en marcha** (el usuario, 2026-10-21: «durante la reproducción, con al menos una secuencia tocando en cualquier pista, cambiar de escala custom puede llegar a hacer que el aparato se cuelgue y necesita reiniciar»).

Causa: el original enciende los pads de las notas de una pista (el paso mantenido y las notas que suenan; el oyente de almacenes `0x0804B272`, el redibujado `0x0804AE96`) con la nota cuantizada (`0x080408C6`) → la tabla inversa del teclado (`[0x20041044 + 0xF4 + nota]`) → `0x0804AE66(vista, índice)`, que escribe el color en el búfer de LEDs (`0x0804AA40`, sin límite) y en el del enlace (`[0x20041044 + 0x180 + índice]`). Una nota que no está en el teclado da el índice `0xFF` y el color va al búfer + `0x1FE` = `0x20041602`: **dentro de la vista de pista de Synth 2** (`0x200415D4 + 0x2E`, la mitad alta de su puntero de almacén `+ 0x2C`), además de un pad suelto por el enlace leído fuera de la tabla. Con las escalas de stock no pasa (la nota cuantizada siempre está en el teclado); con la escala propia sí: (1) **justo después de cada cambio** el cuantizador ya usa la escala nueva y el teclado se rehace en el siguiente fotograma de la tarea de LEDs: una nota que suena en ese momento (transporte en marcha) da `0xFF`; (2) **un periodo corto no cubre todo el recorrido** (28 filas × P o 2P alrededor de 60: con P = 1 las notas por encima de 79 no están).

Arreglo (`tools/kbguard.py`, zona libre, 16 B): la cabeza de `0x0804AE66` → `c_kbg`: un índice ≥ 224 (28 filas × 8) no enciende nada; los demás, el original.

## Qué probar
1. Synth 1 con un patrón sonando (Play). Shift + Scales: cambia la escala propia muchas veces (pon y quita teclas, deprisa) mientras suena: el aparato sigue respondiendo.
2. Una escala propia de periodo corto (solo la tecla de un semitono encima de la tónica): con el patrón sonando y notas altas, nada se cuelga. Esas notas altas no encienden pad en la vista Note (no están en el teclado).
3. Vuelve a una escala de stock y a la propia con el transporte en marcha: sin cuelgues.
4. Lo demás, como SC45.6 / Beta 3.13 (`firmware/sc45.6/PRUEBA.md`).

## Verificación en emulación
- `emu_kbguard.py` (escala de periodo 1 con la nota 100 sonando; el momento después de un cambio; la mayor hecha a mano), por el oyente real de la vista de Synth 1: la build anterior escribe el búfer + `0x1FE` y un pad suelto, esta nada fuera del búfer y los mismos pads; `emu_cscale.py` sobre SC45.7 y RC2.05.
