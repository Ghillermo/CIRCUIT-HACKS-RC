# S419D2 (diagnóstico) = SC419D + el culpable de cada retraso del bucle principal

`circuittracks-4486-S419D2.syx` — SHA-256 `524917a2ebe122fce07505b41a471850ef83ef4574a7a00d939587dd7802774c`, marca `S419D2` («SC419D2» se cortaría a «SC419D»).

Con SC419D el stutter del delay encendía **Duplicate en amarillo** (el bucle principal del ARM se retrasaba más de 10 ms). S419D2 dice **qué** lo retrasa: en cada retraso Duplicate se enciende **1 s** en el color del culpable (por prioridad):

| Color de Duplicate | Qué ha corrido durante el retraso |
|---|---|
| **blanco** | una lectura / escritura de la tarjeta **pedida por el mod** |
| **azul** | una lectura / escritura de la tarjeta del firmware original |
| **melocotón** | el servicio del DSP ha tardado ≥ 5 ms |
| **naranja** | la tarea de LEDs ha tardado ≥ 5 ms |
| **rojo** | un movimiento de knob ha tardado ≥ 5 ms |
| **verde** | un pad ha tardado ≥ 5 ms |
| **amarillo** | ninguno de los anteriores |

Save rojo (bloques del DSP tarde) y Play naranja (tick del secuenciador tarde) siguen como en SC419D.

## Qué probar
1. Como con SC419D: proyecto con delay audible, Play, y repite lo que produce el stutter.
2. Apunta el **color de Duplicate** cuando se oye el stutter (y en qué vista estabas: Preset del sinte, Preset de MIDI 1 / 2, vista Note…).
3. Prueba también a quedarte quieto unos segundos en la vista Preset de Synth 1 y en la de MIDI 1: si cada ~4 s se oye el stutter y Duplicate se pone blanco, es la relectura periódica de los patches desde la tarjeta.

## Verificación en emulación
- `emu_s419d2.py`: un hueco de 15 ms sin nada = amarillo; con una consulta a la tarjeta desde código del mod = blanco, desde el original = azul; un knob de 6 ms = rojo; un pad de 6 ms = verde; un knob de 1 ms = amarillo; Save rojo sigue.
