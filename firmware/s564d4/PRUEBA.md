# S564D4 (diagnóstico) = Beta 5.64 sin el mapa de algoritmos FM + lectura de memoria en vivo + trampa MPU + volcado de DMA

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/s564d4/circuittracks-4486-S564D4.syx` | `abd07f836c5ab1f302b06d9d3f40946bff4c4440aa1fdf4f20568c9d7b91a302` | `S564D4` |

Sin el mapa de algoritmos FM (el usuario lo eligió para hacer sitio; el FM funciona igual). Lleva:
- `blackbox.use_memrd`: lectura de cualquier RAM / registro por USB mientras el aparato funciona (`python tools/bbread.py --mem ADDR LEN`);
  `python tools/livewatch.py` vigila en vivo la palabra `0x20042988` y los 16 flujos DMA y registra el momento exacto del cambio;
- `mpuwatch` (la trampa MPU sobre `0x20042980..9F`) y `dmawatch` (los DMA al primer cambio, en la caja negra).

Verificación en emulación: `emu_memrd.py`, `emu_mpuwatch.py`, `emu_dmawatch.py` sobre esta imagen.
