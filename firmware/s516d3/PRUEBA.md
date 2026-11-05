# S516D3 (diagnóstico) = S516D2 + `del`

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/s516d3/circuittracks-4486-S516D3.syx` | `3d11cef4d081fec827597622bb72c3fd63857fe219975079ea751b46a8b694bd` | `S516D3` |

S516D2 con `rdiag.DELETE` (orden 7, `ctremote.py del`) para deshacer las pruebas de bancos de patches del 2026-11-04 en el pack 22 (`21_PACK`): el banco 15 creado y el banco 0 con 9 registros (el original en `re/banktest/bank0_p22.bin`). Un S516D2 reconstruido con `del` no se instalaba encima del primero: misma marca, mismo bloque de versión (el bootloader no instala si no cambia).

## Cómo
1. Instalar S516D3; conectar por USB con los puertos libres.
2. Claude: `ctremote.py del 3 15 22 --yes`, `del 3 0 22 --yes`, `put 3 0 re/banktest/bank0_p22.bin 22 --yes`, y comprueba con `dump` que el banco 0 es idéntico a la copia.
3. Volver a instalar la Beta 5.19.
