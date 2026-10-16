# S421D (diagnóstico) = SC42.1 + los testigos de S419D2

`circuittracks-4486-S421D.syx` — SHA-256 `b95c9b648fb30c2087574bcc061dae60d844ba9be6310fe58219a019b451f68c`, marca `S421D`.

SC42.1 (guardado diferido + sin relecturas de la tarjeta mientras suena) con los mismos testigos que S419D2: **Save rojo** = bloques del DSP tarde, **Play naranja** = tick del secuenciador tarde, **Duplicate** 1 s en el color del culpable de cada retraso del bucle principal (blanco tarjeta pedida por el mod, azul tarjeta del original, melocotón servicio del DSP, naranja tarea de LEDs, rojo knob, verde pad, amarillo otro).

## Qué probar
1. Proyecto con delay audible, Play; repetir lo que daba stutter (knobs y modos del motor de MIDI 1 / 2, quieto en las vistas Preset de MIDI 1 y de Synth 1).
2. Apuntar si hay stutter y el color de Duplicate. Lo esperado: **ni blanco ni azul mientras suena**.
3. Comparar el amarillo con R0903D (el mismo diagnóstico sobre la RC).

## Verificación en emulación
- `emu_s419d2.py` (los testigos) y `emu_playhold.py` sobre SC42.1.
