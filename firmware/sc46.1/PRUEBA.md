# SC46.1 / Beta 3.18 = SC46 + el arreglo de la longitud fija (también en RC2.07) + el del S&H del LFO a tempo

`firmware/sc46.1/circuittracks-4486-SC46.1.syx` — SHA-256 `8b12e122c2afb1bd396374ea6099a1c2ed432479899b2c607a1172138f766940`, marca `SC46.1`.
`firmware/b3.18/circuittracks-4486-B3.18.syx` — SHA-256 `78e37aeb8511e14e7b9e09df7576b3c674eaf22a6c2dd5bbe52ad71497b97bfe`, marca `B3.18` (**Beta 3.18**, el mismo código).

**Arreglo de la longitud fija** (`stepgate.use_v4()`; el usuario, 2026-10-24: «en la funcion de fixed length, cambiar el length no actualiza los leds ni cierra la vista. ademas el length no se aplica a todos los pasos, especialmente el paso 1 o los pasos que han sido previamente escritos y borrados»):
- **Los LEDs:** el búfer de LEDs de la vista Micro Step es del stock y solo se redibuja cuando el stock cambia algo; el selector escribía encima y, al elegir una longitud (o tocar el pad 31 / 32, o salir de la vista), los pads 17-30 se quedaban como los había dejado el selector. Ahora, tras cada pulsación nuestra, el stock redibuja la vista (`0x0804CB30`), y también cuando la tarea de LEDs cierra el selector.
- **La longitud:** se ponía al soltar el primer pad, pero soltar un pad de paso no pasa por la vista de pista (los pasos son objetos aparte, clase `0x0805ADB4`): si se soltaba antes el paso, o se pulsaba la nota antes que el paso, la nota se quedaba con el gate del stock (6, o el más largo del paso: en un paso con notas, como el paso 1 de muchos proyectos, el de esas notas); de un acorde, solo la última nota la recibía. Ahora la longitud se pone al añadir cada nota (`0x0804B094` llamado como subrutina desde su cabeza; la unidad de esa nota en el paso mantenido a 6 × la longitud, su ligadura conservada). El gate por pulsación (pad 32) también termina al soltar el pad de paso (cabeza de la ranura 1 de los pasos).

**Arreglo del S&H del LFO** (solo beta: el LFO a tempo es de la beta; `vcf21_dsp.use_shsync()` + `modmx.use_shsync()`; el usuario, 2026-10-24: «lfo s&h (random) no funciona»): con el LFO **a tempo** (mitad izquierda del knob de velocidad) y el transporte en marcha, el sample & hold (y el S&H suavizado) del LFO del motor y del LFO 2 de la matriz no cambiaban nunca de valor. El valor nuevo sale cuando la fase da la vuelta; a tempo, la fase la pone el ARM al inicio de cada ciclo (−1 en el DSP, 0 en la matriz) y eso no se veía como una vuelta. Ahora sí. Con el LFO libre ya funcionaba (y sigue igual).

## Qué probar
1. Synth 1, vista Micro Step (Gate dos veces): pad 31 abre el selector; elige 4 pasos (pad 20): el selector se cierra y los pads 17-30 vuelven a enseñar los micropasos al momento; el pad 31 naranja.
2. Con la longitud fija encendida, en la vista Note: mantén un paso y toca una nota, y suelta primero el **paso**: la nota dura 4 pasos. Lo mismo pulsando primero la nota y luego el paso, en el paso 1, en un paso borrado con Clear y con un acorde (dos notas: las dos de 4 pasos).
3. Abre el selector y sal de la vista sin elegir: al volver, la vista Micro Step se ve normal.
4. Pad 32 (gate por pulsación): mantén paso + nota y suelta primero el paso: el gate es el tiempo que la mantuviste.
5. **S&H:** MIDI 1 con el oscilador, LFO al filtro, forma S&H (página 5, Shift + K8, blanco), velocidad a la izquierda (a tempo), Play: el filtro salta a un valor distinto en cada ciclo. Lo mismo con el S&H suavizado (violeta) y con el LFO 2 de la matriz (Shift + K4, zona S&H, mitad baja).
6. Lo de SC46 / Beta 3.17 sigue igual.

## Verificación en emulación
- `emu_sc46_1.py` frente a SC46 (ver `firmware/r207/PRUEBA.md`).
- `emu_shsync.py` frente a SC46 (el núcleo 0 entero con el tráfico del motor: LRATE −8 y la fase puesta a `$800000` cada 60 bloques como hace `lfosync`: un valor nuevo en cada inicio de ciclo, SC46 ninguno; libre igual que antes; `c_mxsync` de la matriz).
