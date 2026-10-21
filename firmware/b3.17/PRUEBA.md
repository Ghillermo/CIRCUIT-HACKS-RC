# SC46 / Beta 3.17 (SC46 / B3.17) = SC45.9 + el sinte propio de MIDI 1 / 2 guardado con el proyecto

`firmware/sc46/circuittracks-4486-SC46.syx` — SHA-256 `643d5c1ecf7759bc4dc54ace7a004426ed9240aa9e13a2628ed356eed92ca69c`, marca `SC46` («SC45.10» se cortaría a «SC45.1»).
`firmware/b3.17/circuittracks-4486-B3.17.syx` — SHA-256 `48205fffa7a284e964552ea5d8b4c45a6dc1b30946ef3bd817c7108636ce3caf`, marca `B3.17` (**Beta 3.17**).

**Función nueva (solo beta)** (el usuario, 2026-10-21: «Cuando un proyecto se guarda, debería conservar su parche inicial»; aclarado: «The MIDI 1 / 2 own synth: each project should save its sound and bring it back when loaded (today it is global)»).

`tools/projsyn.py` (zona libre): el motor propio de MIDI 1 / 2 guardaba su estado solo en los ajustes globales (desde SC20): cargar otro proyecto dejaba el sonido del anterior. Ahora cada proyecto lleva los patches de las dos pistas en el formato del sinte propio (lo que escribe el guardado de `mpatch`: CTM1, códigos, matriz, página 4, FM; los 124 primeros bytes del relleno) en los **bytes 8..39 de los ajustes de los patrones 0..4 de MIDI 1 / 2** (el original lee 0..3, `patchain` / `playmode` 4..7; libres en las pistas de notas salvo la basura de `02_Shadow Child`): bloques de 32 B = `0xC6`, pista << 4 | bloque, 30 B + suma de 16 bits. La IO de `mpatch` (`mp_io`, `c_mpsz`) va a la RAM mientras su bandera = 1 + pista: su guardado `c_mpsave(t, 0xFF)` y su carga `c_mpload(t, 0xFF)` (con todo lo que envuelven: `modmx`, `p4dest`, `fmeng`) corren sin cambios sobre la RAM; los bytes 6 / 7 de la caché de huecos se conservan. La tarea de LEDs junta el estado cada 256 ms (con el cerrojo del búfer compartido, como el refresco de `mpatch`) y, tras una carga (`P19.LOAD_END`), aplica una vez los bloques del proyecto (sin ellos, el sonido se queda); no antes de 3 s tras encender. El guardado (`P19.SAVE_CALL`, delante de los demás) copia la RAM a los 10 bloques del registro **sin cerrojo** (el cerrojo es un semáforo que gira: tomarlo con el guardado en marcha podría bloquear). RAM `modmx.MXR + 0x300..0x46F` con firma (no se borra al encender: sin firma todo se lee como 0, la IO de `mpatch` no se desvía).

## Qué probar
1. Proyecto A: MIDI 1 con el motor propio y un sonido reconocible; MIDI 2 con otro. Guarda el proyecto A.
2. Proyecto B: cambia los dos sonidos (o apaga el motor de MIDI 2). Guarda B.
3. Carga A: MIDI 1 / 2 suenan como al guardar A (motor, osciladores, matriz, página 4, FM). Carga B: como B.
4. Un proyecto guardado con una versión anterior (sin bloques): al cargarlo el sonido se queda como estaba.
5. Apaga y enciende con A cargado: vuelve A. Los huecos de patch (pads 9-24) siguen igual, sin cambiar el último elegido.
6. Duplicar o borrar patrones de MIDI 1 / 2 no cambia nada al sonido (al guardar se escriben otra vez).
7. Lo demás, como SC45.9 / Beta 3.16 (`firmware/sc45.9/PRUEBA.md`).

## Verificación en emulación
- `emu_projsyn.py` (TUNE por el knob real, la tarea de LEDs real: antes de 3 s nada; el guardado escribe los 10 bloques sin tocar los bytes 0..7; la carga devuelve TUNE y el motor de MIDI 2; la caché de huecos igual; sin bloques o con uno dañado, nada; basura en la RAM al encender), `emu_fmeng.py` (patches propios en la tarjeta por la IO real de `mpatch`), `emu_p4ovl.py`, `emu_splitknob.py`, `emu_dupnote.py`, `emu_cscale.py`.
