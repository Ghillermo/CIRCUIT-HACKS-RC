# Alpha 7.01 = Alpha 7 (la Beta 5.65) + Save violeta mientras la caja negra espera a leerse

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/a7.01/circuittracks-4486-A7.01.syx` | `fbcbcd4eb1f749b611f0ea6cbf868e6c7022bac8d3752939a75fb61983fa28d2` | `A7.01` |

**Causa (cazada en el aparato con S564D5 y `tools/livewatch.py`, 2026-11-15 21:14:59):** el pintor de stock de la vista de probabilidad de una pista
de notas enciende tantos pads como el byte de probabilidad del paso elegido (válido 0-7); con un byte ≥ 32 escribe 16 pads de más, encima del objeto
siguiente (la vista Preset de Synth 1), y la siguiente confirmación de un almacén que lo llama (Play / Record) cuelga el aparato. Los 16 colores
cazados en el aparato coinciden byte a byte con los de ese pintor. El cuelgue de la 5.63 es el mismo con la barra de velocity de un drum (velocity ≥ 129).
**Arreglo:** `tools/paintguard.py`: los dos pintores se saltan un valor que no pueden dibujar. **Pendiente:** quién deja ese valor en el paso (pista:
una cadena / escena que lleva una pista a un patrón fuera de los 8). La primera vez que un pintor se salta un valor, la caja negra se congela
(estado `0x85`, etiqueta 1 probabilidad / 2 velocity y el valor): leerla con la app o `python tools/bbread.py --firmware A7.01` y pasarla.

**Alpha 7.01** (`blackbox.use_showall()`): Save parpadea en violeta mientras haya un registro de la caja negra por leer (un fallo, un bloqueo, un reinicio del vigilante o un valor saltado de `paintguard`), hasta Vaciar en la app (o apagar el aparato, que lo pierde); una captura a mano no. Antes: solo 30 s tras un reinicio, y un valor saltado no se veía. Prueba `emu_showall.py` (contra la Beta 5.65).

## Qué probar
1. Lo que colgaba: crear cadenas de patrones y de escenas, grabar drums con los pads, Record / Play: sin reinicio.
2. Si Save parpadea en violeta: conectar por USB sin apagar, leer la caja negra con la app, guardarla y Vaciar: Save deja de parpadear.

Verificación en emulación: `emu_paintguard.py` (ALL PASS: los valores malos no se salen del búfer, los válidos pintan igual que en la 5.64; el
salto congela la caja negra una vez).
