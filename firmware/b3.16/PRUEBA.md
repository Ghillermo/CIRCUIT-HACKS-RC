# SC45.9 / Beta 3.16 (SC45.9 / B3.16) = SC45.8 + un arreglo de la página 4 de destinos (solo beta)

`firmware/sc45.9/circuittracks-4486-SC45.9.syx` — SHA-256 `cbf3486a8e8da0720ffde2955fa22a41df098f31f6f44b3bd5582551be0ce889`, marca `SC45.9`.
`firmware/b3.16/circuittracks-4486-B3.16.syx` — SHA-256 `a56a21032452956fed31797172cd2286de1d00fe43a0bd54fbed3ddb3cc4b6f2`, marca `B3.16` (**Beta 3.16**).

**Arreglo** (el usuario, 2026-10-21: «en MIDI1/2 la vista de destinos de Knobs seleccionados no se muestra en los pads, como lo hace mod Matrix»).

`tools/p4ovl.py` (zona libre): mientras Shift + un knob de la página 4 elige su destino (`p4dest`), los pads 9-24 de la vista Preset de MIDI 1 / 2 enseñan dónde está, como la superposición de `modmx`: el pad de la página del destino brillante, pads 9-16 / 17-24 = K1-K8 / Shift + K1-K8 de esa página (tenues los que tienen parámetro, brillante el destino), 1,5 s tras el último movimiento; los pads 9-24 no cargan patches mientras tanto. Cabezas: ranura 4 de los manejadores de macros (delante de `c_p4knob`: anota el knob y la hora) y ranuras 0 / 7 de la vista de plantillas (`mpatch.TMPL_VT`, delante de las de `modmx`). RAM `modmx.MXR + 0x17A..0x17F`. Solo beta (`p4dest` no está en la RC).

## Qué probar
1. MIDI 1 con el motor encendido, vista Preset, pad 4 (página 4). Mantén Shift y gira K1: los pads 9-24 enseñan la página del destino (su pad de página brillante, el destino brillante entre los tenues), como al girar un knob de la matriz (pad 6).
2. Suelta Shift: 1,5 s después vuelven los patches. Mientras se ve, tocar un pad 9-24 no carga ningún patch.
3. K1 sin Shift: nada cambia en los pads.
4. Lo demás, como SC45.8 / Beta 3.15 (`firmware/sc45.8/PRUEBA.md`).

## Verificación en emulación
- `emu_p4ovl.py` (por el controlador y la tarea de LEDs real: los pads frente al modelo con las tablas de `modmx`, el pad tragado, el fin a los 1,5 s, sin Shift nada; SC45.8 no la enseña), `emu_splitknob.py`.
