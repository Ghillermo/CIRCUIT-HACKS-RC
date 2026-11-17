# S564D3 (diagnóstico) = Beta 5.64 + el volcado de los DMA al cambiar la palabra corrompida

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/s564d3/circuittracks-4486-S564D3.syx` | `f9df8ab84cdb9943b7119f47b8918356d696a845efbb021ff955150fb0cf7d0c` | `S564D3` |

Ni el watchpoint DWT (S564D) ni la región MPU (S564D2) saltaron: quien escribe `0x20042988` no es el procesador, casi seguro un DMA. Cada fotograma
de LEDs compara esa palabra; al primer cambio congela la caja negra (estado `0x85`) y guarda el fotograma (1 = ya estaba mal al arrancar: la carga
del proyecto) y los 16 flujos DMA (dirección de memoria, cuenta, control, periférico). Leer con `python tools/bbread.py --firmware S564D3`.

Verificación en emulación: `emu_dmawatch.py` (ALL PASS).
