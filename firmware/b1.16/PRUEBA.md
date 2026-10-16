# Beta 1.16 (B1.16) = SC42.6 = SC42.5 + página 2 y toggle pitch-vel del step-drummer

`circuittracks-4486-SC42.6.syx` — SHA-256 `d2400ff496942f87b71883b46a5cf615be7baa692d0cc4f6d851eb7c9488b2c0`, marca `SC42.6`.
`firmware/b1.16/circuittracks-4486-B1.16.syx` — SHA-256 `41ad56af347441e074135dacd1dfc685ad9b5b4bd90e7cd155bdae49307aa800`: el mismo código con la marca `B1.16` (**Beta 1.16**).

El usuario (2026-10-16) sobre SC42.5: «pitch-vel mode seem to do nothing on pitch. There's no way to route Page 2 to any parameter»; «el toggle envía el primer parámetro a pitch y el segundo a vel» (además de sus destinos), en el **pad 32** de la vista del step-drummer, transponiendo **en la escala**; con el toggle apagado la página 2 no toca la velocity; «el pad 6 (activador step-drummer) debe mostrarse tenue».

- **Pad 32** de la vista del step-drummer (MIDI 1 / 2 y Synth 1 / 2) = **toggle pitch-vel** (verde brillante = activado, verde tenue = apagado). Activado: cada nota de la pista sube / baja (valor del par de la página pitch − 64) **grados de la escala** del proyecto (la de stock o la propia), entre 0 y 127, también al escuchar un paso; la página velocity cambia también la velocity. Se guarda con el proyecto.
- **Página velocity (Octave ▼): pads 17-24 = su destino** (el mismo pad otra vez = ninguno). Con destino, los knobs escriben el valor del par: MIDI desde 64 (los mismos destinos que la página pitch; usa el carril de automatización de REL, que con el step-drummer activado ya no se reproduce ni se graba); sintes = la automatización del macro elegido, desde su posición. Sin destino ni toggle, la página velocity no hace nada. Los LEDs de los knobs: el valor en el color del destino.
- Si las dos páginas van al mismo destino, se suman.
- **Pad 30 en MIDI 1 / 2:** tenue = step-drummer desactivado, brillante = activado (antes, apagado / tenue).
- **Random-mutate con la escala propia y otra tónica que Do:** ahora elige grados desde la tónica.

## Qué probar
1. MIDI 1 con el motor encendido: el pad 30 se ve tenue; pad 30 = vista del step-drummer (pad 30 brillante, pad 32 verde tenue).
2. Pad 32 (verde) y la página pitch: K1 sube / baja las notas de ese par en la escala del proyecto (un aparato externo por MIDI también); escuchar un paso suena ya movido.
3. Octave ▼ (página velocity): pads 17-24 eligen su destino (el elegido brillante); K1-K8 lo mueven por pares. Con el pad 32 apagado, la velocity no cambia; encendido, sí.
4. Synth 1: vista de la fuente (Synth 1 otra vez), pad 30, pad 32 = toggle (el editor de macros sigue en el pad 32 fuera del step-drummer); página velocity con un macro de destino.
5. Escala propia con tónica Re + random-mutate: las notas cambian a grados de la escala desde Re.

## Verificación en emulación
- `emu_sc42_6.py`: por el controlador y la tarea de LEDs completa (pad 30 tenue / brillante, pad 32, pads 17-24 de la página 2, carriles 1 de los dos pasos del par desde 64, la velocity solo con el toggle, el LED del knob, `c_sdfx` con las dos páginas (WAVE 40 + 3 + 10; tono del OSC1 1 semitono, del OSC2 2 y fine 56), REL ni aplicado ni grabado, la escucha movida 3 grados y su note-off, la vista de Synth 1 (pad 32 = toggle, el editor de macros fuera de ella), el reproductor de Synth 1 con la escala de stock y con una propia, `c_pvdeg` contra un modelo en 49 casos con tónica Re, random-mutate con la escala propia y tónica Re = Fa# / La); también `emu_sc42_5.py`, `emu_cscale.py` y `emu_sc41.py` sobre SC42.6.
