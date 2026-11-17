# Beta 5.65 = Beta 5.64 + el arreglo del cuelgue (pintores de pads que se salían de su búfer)

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/b5.65/circuittracks-4486-B5.65.syx` | `cc9bb0be87bf0c233e84a6b4e8ad07b1b9fad1e9b5c78472dc6934e86633d4ad` | `B5.65` |

**Causa (cazada en el aparato con S564D5 y `tools/livewatch.py`, 2026-11-15 21:14:59):** el pintor de stock de la vista de probabilidad de una pista
de notas enciende tantos pads como el byte de probabilidad del paso elegido (válido 0-7); con un byte ≥ 32 escribe 16 pads de más, encima del objeto
siguiente (la vista Preset de Synth 1), y la siguiente confirmación de un almacén que lo llama (Play / Record) cuelga el aparato. Los 16 colores
cazados en el aparato coinciden byte a byte con los de ese pintor. El cuelgue de la 5.63 es el mismo con la barra de velocity de un drum (velocity ≥ 129).
**Arreglo:** `tools/paintguard.py`: los dos pintores se saltan un valor que no pueden dibujar. **Pendiente:** quién deja ese valor en el paso (pista:
una cadena / escena que lleva una pista a un patrón fuera de los 8). La primera vez que un pintor se salta un valor, la caja negra se congela
(estado `0x85`, etiqueta 1 probabilidad / 2 velocity y el valor): leerla con la app o `python tools/bbread.py --firmware B5.65` y pasarla.

## Qué probar
1. Lo que colgaba: crear cadenas de patrones y de escenas, grabar drums con los pads, Record / Play: sin reinicio.
2. Si Save se ve violeta o algo raro: leer la caja negra.

Verificación en emulación: `emu_paintguard.py` (ALL PASS: los valores malos no se salen del búfer, los válidos pintan igual que en la 5.64; el
salto congela la caja negra una vez).
