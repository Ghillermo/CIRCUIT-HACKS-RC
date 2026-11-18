# S702D3 (diagnóstico) = S702D + la caché de instrucciones del Cortex-M7 encendida al arrancar (`tools/icache.py`)

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/s702d3/circuittracks-4486-S702D3.syx` | `3efee3d669a230c9c1a8bcee4f918d9d3dc4db349879e966ee3405f116dcc0d4` | `S702D3` |

El usuario (2026-11-17): con 6 voces del FM de 8 operadores el tempo se arrastra. S702D leyó el aparato: 120 MHz, **caché de instrucciones
apagada** (SCB CCR `0x00040200`), caché de datos apagada, flash con 3 esperas (ART / prefetch solo sirven al bus ITCM; la app corre por AXI). En el
arranque, el `isb` de la rutina de stock que enciende la FPU (`0x0805B7A4`) salta (`b.w`) a `c_icon`: invalida la caché, pone CCR.IC y vuelve a
`0x0805B7A8`. La caché de datos sigue apagada (DMA de la tarjeta y del audio).

**S702D2 (la primera, SHA `9213fbc4…`) no arrancaba (panel apagado):** el gancho era un `bl` dentro de una rutina hoja que vuelve con `bx lr`: LR
pisado, la rutina volvía a sí misma para siempre. Quitada del instalador. S702D3 lleva otra marca porque el cargador salta una imagen con la misma.
Prueba en emulación: la rutina de stock con el gancho vuelve a quien la llamó (25 instrucciones) y CCR.IC = 1; S702D igual que antes.

1. Instalar S702D3 (`python tools/ctflash.py firmware/s702d3/circuittracks-4486-S702D3.syx`, modo bootloader). `python tools/perfread.py`: CCR
   debe decir I-cache ON.
2. Las 6 voces FM: ¿se arrastra menos o nada? Probar también lo de siempre (cargar proyectos, samples, Components, USB, el audio).
