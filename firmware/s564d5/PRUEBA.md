# S564D5 (diagnóstico) = Beta 5.64 sin «retener knob» + lectura de memoria en vivo + trampa MPU + volcado de DMA

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/s564d5/circuittracks-4486-S564D5.syx` | `ae64fd54b760b0a399ed23400e0438d86617666389186b7fc9f1e217e02bb2ad` | `S564D5` |

S564D4 (sin el mapa de algoritmos FM) entraba en bucle de arranque: la caja negra registró el bucle principal parado 1,5 s a los 9,6 s de cada
arranque (el vigilante reinicia), casi seguro un proyecto con un algoritmo FM propio, que necesita el mapa. Aquí el mapa vuelve y sale «retener knob»
(no guarda nada en los proyectos); la RAM del volcado de DMA pasa a la de «retener knob» (`0x2004F900`).

Lleva: `blackbox.use_memrd` (`python tools/bbread.py --mem ADDR LEN`, `python tools/livewatch.py`), `mpuwatch`, `dmawatch`.
Verificación en emulación: `emu_memrd.py`, `emu_mpuwatch.py`, `emu_dmawatch.py` sobre esta imagen (ALL PASS).
