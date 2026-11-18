# S702D (diagnóstico) = Alpha 7.02 sin el mapa del algoritmo FM + lecturas de memoria en vivo por USB

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/s702d/circuittracks-4486-S702D.syx` | `eb4eadb68d0b7ed824dbb7d5303b9e0ad8f5a929f891548a98701e3f3d1eedc6` | `S702D` |

El usuario (2026-11-17): «is there other performance options we could check?». Lee del aparato en marcha el estado que decide el rendimiento del
ARM: cachés del Cortex-M7 (SCB CCR, CACR), TCM, esperas de la flash / ART / prefetch (FLASH ACR), relojes (RCC, overdrive), recarga del SysTick
(= HCLK) y si corre el contador de ciclos (DWT). No escribe nada.

1. Instalar con `ct_uploader.html` (modo bootloader), encender, dejar el aparato conectado por USB (sin otro programa en sus puertos MIDI).
2. `python tools/perfread.py` (lo hace Claude). Cada bloque es una petición; las lecturas son de byte: si un registro no las admitiera, el aparato
   dejaría de contestar (la caja negra lo anotaría): apagar y volver a encender.
3. Volver a Alpha 7.02 (o la versión que se use) al terminar.

Todo lo demás es Alpha 7.02 salvo el mapa del algoritmo FM (pad 7 de la página FM: sitio para las lecturas en vivo).
