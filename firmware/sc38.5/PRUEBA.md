# SC38.5 — Shift + pad 7 = loop enganchado

`circuittracks-4486-SC38.5.syx` — SHA-256 `492c2d1235f98af64099748bd6a3d810948f80f53098d6093d6566dc8d24eeaf`
Imagen de 0x662b0 bytes, CRC 0x18c182be, marca `SC38.5`.

Es SC38.4 con:
1. **Shift + pad 7** (sample capturado, Master FX): el sample suena en **bucle enganchado**, en cualquier modo, hasta que vuelvas a pulsar el 7 (con o sin Shift). Igual con Shift + un hueco de la fila inferior que tenga el sample. El pad 8 también lo para.
2. El **modo loop** (K2 azul) sigue igual: suena mientras mantienes el pad.
3. Copiar un patch a un hueco vacío de un banco más corto: los huecos vacíos anteriores se llenan con el **Initial Patch** (el patch por defecto del aparato), no con copias.

## Qué probar
1. Shift + 7, soltar: sigue en bucle; cambiar de vista y volver: sigue; pulsar 7: para.
2. Con el bucle enganchado, tocar un hueco de efecto de la fila inferior: suena su efecto y no se reasigna al sample.
3. 7 solo (sin Shift) en modo one-shot / gate / loop: como antes.
4. Copiar un patch de otro pack a un hueco apagado lejos del último patch del banco: los huecos intermedios aparecen con el Initial Patch.
