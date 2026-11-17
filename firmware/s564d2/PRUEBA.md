# S564D2 (diagnóstico) = Beta 5.64 + una región MPU de solo lectura sobre la palabra corrompida

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/s564d2/circuittracks-4486-S564D2.syx` | `00ef8ab3c282f8e8f75a79f62cb6dd4dd8c5cd8c111f0c3be47b356ad847cc20` | `S564D2` |

S564D (el watchpoint DWT) no saltó: el cuelgue llegó igual (BusFault, vector 5). Aquí los 32 bytes `0x20042980..0x2004299F` (la cabeza de la vista
Preset de Synth 1, que solo escribe su constructor al arrancar) son de solo lectura para el procesador: cualquier escritura provoca al momento un
fallo MemManage, que la caja negra guarda (vector 4, el PC / LR del código que escribe, la dirección). Si el cuelgue vuelve **sin** ese fallo, quien
escribe es un DMA.

## Qué hacer
Como con S564D: repetir lo que hacías; tras el reinicio, leer la caja negra (app o `python tools/bbread.py --firmware S564D2`).

## Verificación en emulación
`emu_mpuwatch.py` (ALL PASS: SHCSR / región / MPU_CTRL una sola vez, el fotograma de LEDs de la 5.64). Unicorn no tiene MPU.
