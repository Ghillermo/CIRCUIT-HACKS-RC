# SC38.6 — huecos de patch intermedios vacíos

`circuittracks-4486-SC38.6.syx` — SHA-256 `2292ba05159362df2f38cbb8489c332241dd8fba42cef65d04431325ed44a659`
Imagen de 0x6628c bytes, CRC 0xedbee812, marca `SC38.6`.

Es SC38.5 (loop enganchado con Shift + 7, captura armada desde Play, Duplicate a huecos vacíos, Clear fijo) con un cambio: al copiar un patch de otro pack a un hueco vacío lejos del último patch del banco, **los huecos intermedios quedan vacíos**, como cuando el propio aparato guarda un patch ahí (antes se llenaban con el Initial Patch).

## Qué probar
1. Copiar un patch de otro pack a un hueco apagado con huecos apagados delante: el destino suena con la copia; los intermedios siguen apagados (vacíos) y al elegirlos suena el patch por defecto.
2. Lo de `firmware/sc38.5/PRUEBA.md` y `firmware/sc38.4/PRUEBA.md`.
