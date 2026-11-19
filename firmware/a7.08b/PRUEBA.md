# Alpha 7.08b (marca `A7.08b`) — pendiente de probar

= Alpha 7.08 + `fxstep.use_smpcol()` (el usuario, 2026-11-19, en el aparato: «Los pasos con sampler no se pintan de amarillo, corrígelo y sube a 7.08»): **un paso cuyo primer pad es el sample (pad 7) se ve en amarillo** (`build_sc17.SMP_ON`, `0x2D`). En la 7.08 tomaba el LED del pad 7 del búfer, que el código del sample escribe después en el mismo fotograma: salía apagado. Marca nueva: una reconstrucción como «A7.08» no se instalaría sobre la 7.08 publicada (el mismo bloque de versión).

Todo lo demás, como la [Alpha 7.08](../a7.08/PRUEBA.md). Imagen `0x6fbb8`.

## Probar
En Master FX, mantén el pad 7 y toca el paso 1 (pad 9): el pad 9 en amarillo. Con el pad 1 y el pad 7 en el mismo paso: el color del pad 1 (el primer pad).

Pruebas: `emu_fxstep.py` (en la 7.08 el paso del sample sale `0x00`; en la 7.08b `0x2D`).
