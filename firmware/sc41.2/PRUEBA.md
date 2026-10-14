# SC41.2 / Beta 1.2 — revisión de SC41.1

`circuittracks-4486-SC41.2.syx` — SHA-256 `5b10f5bb8cc5533523e7b43ed4a72f2994224822cecb2e7a7a158da6c4fa4ab1`, marca `SC41.2`.
`firmware/b1.2/circuittracks-4486-B1.2.syx` — SHA-256 `07330a71d58001981087e9428c0ca8d605299472b461acde8e2ca0e08ec273c1`: el mismo código con la marca `B1.2` (**Beta 1.2**).

Es SC41.1 (ver `firmware/sc41.1/PRUEBA.md`) con un arreglo encontrado al revisarla:

- **Una regla de cadena pedida para una pista o un patrón fuera de 1-8 ya no lee fuera de la RAM.** El motor entrega a nuestros ganchos (cadenas, órdenes fractal / deconstruido) el patrón que suena; en la emulación, con un estado del motor inesperado, llegó un patrón `0x84` de una pista de drums y la dirección calculada caía después del final de la RAM: en el aparato sería un fallo de bus (bloqueo). Ahora la respuesta es «sin regla» y el patrón suena como en el original.

## Qué probar
Lo mismo que en SC41.1; nada cambia en el uso normal.

## Verificación en emulación
- `emu_sc41_2.py`: `c_pcrule` da la dirección de la regla para pistas y patrones 0-7 y 0 fuera (SC41.1: `0x2005f494` para la pista 7, patrón `0x84`).
- Revisión de regresiones: 21 pruebas antiguas (SC25-SC40) sobre SC41.1 y sobre SC40.8 dan los mismos resultados una vez corregidas dos pruebas que escribían los ticks en la dirección equivocada del motor (`emu_sc38_1.py`, `emu_sc38_2.py`, ahora leen la dirección de la propia imagen con `emu_sc17_7.engine_of`). Lo que sigue fallando en ellas son comprobaciones de diseños anteriores (ganchos estáticos, pad 31 que ya no es el Glitch, Clear + pad 27, la fila 4 de probabilidad…). `emu_sc32.py` y `emu_sc34_2.py` se colgaban en `c_pminfo` (este fallo); ya no.
- `emu_sc40_9.py` y `emu_sc41_1.py` sobre Beta 1.2.
