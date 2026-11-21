# Alpha 7.20 (marca `A7.20`) — pendiente de probar, sin publicar

= Alpha 7.19 + 204 B de flash (imagen `0x6fb08`: 1 272 B libres); nada cambia en el uso.

- `blackbox.use_vecshare()`: los cuatro vectores de fallo comparten un cuerpo (cada uno `movs r0, #v; b`), el manejador de stock de cada uno desde una tabla.
- `scpat.use_srcshare()`: las cuatro entradas `c_spsrc0..3` del sidechain comparten un cuerpo.
- `fmmap.use_famtab()`: el color de cada operador del mapa FM desde una tabla en lugar de una cadena de comparaciones.

Pruebas: `emu_fold3.py` (las entradas del sidechain: las mismas escrituras al DSP y la misma RAM que la 7.19 en 200 llamadas), `emu_blackbox2.py` (20, fallos de verdad en los vectores 3-6), `emu_fmmap.py` (25): los mismos resultados que la 7.19.
