# SC38.7 — reiniciar el motor de MIDI 1 / 2

`circuittracks-4486-SC38.7.syx` — SHA-256 `01a705a96d58547f287711910dc8f590c3cd23f41877a79c805eaa9593bb2b7d`
Imagen de 0x663d0 bytes, CRC 0x491d27a, marca `SC38.7`.

Es SC38.6 con un atajo nuevo en la vista **Preset de MIDI 1 / 2**: **Clear + pad 27** devuelve todos los valores del motor de esa pista (VCA-VCF, osciladores, VA-drum, granular, con y sin Shift, y OSC 2) a los iniciales. El motor elegido (el estado del pad 27) no cambia.

## Qué probar
1. MIDI 1 en oscilador: mover knobs en las páginas VCA-VCF, OSC1 y OSC2 (con y sin Shift); Clear + 27: el sonido vuelve al inicial y el pad 27 sigue en oscilador.
2. Lo mismo en granular y VA-drum.
3. El 27 sin Clear sigue cambiando de motor.
