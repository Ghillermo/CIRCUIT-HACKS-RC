# S703D (diagnóstico, marca `S703D`)

= Alpha 7.03 sin el mapa de algoritmos FM (sitio) + el estudio del hardware. Builder `tools/build_s703d.py`.

- `blackbox.use_memrd()` + `use_memrdw()`: lecturas en vivo por USB, también por palabras (registros de periféricos sin tocar sus registros de datos).
- `icache.use_dwt()`: contador de ciclos encendido al arrancar; tablas del muestreo a cero.
- `tools/cwatch.py` (como S579D): Save violeta en cuanto cambia la vtable de una barra de velocity de drums; leer la caja negra con la app (los 16 gestos de antes).
- `blackbox.use_samp()`: en cada SysTick, la tarea que corre (o la interrupción) y el PC interrumpido, en `0x2004F600..0x2004F7FF`.

## Uso
1. Instalar, arrancar, conectar por USB (puertos MIDI libres).
2. Cargar un proyecto con el FM de 8 operadores a 6 voces y tocarlo.
3. `python tools/hwdiag.py --secs 15 --out hwdiag.json`: árbol de relojes, periféricos con reloj, NVIC, DMA (búferes), temporizadores, SPI / SAI / UART, QUADSPI, CRC / RNG, MHz reales, reparto por tareas y código caliente.

No escribe nada. Pruebas: `emu_s703d.py`, `emu_cwatch.py`, `emu_blackbox2.py` (pasan).
