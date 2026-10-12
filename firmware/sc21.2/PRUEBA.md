# SC21.2 — SC21.1 + parámetros de reverb y delay con Shift + knob en la vista FX

`circuittracks-4486-SC21.2.syx` — SHA-256 `5f92744c4283a7a4679fd5bcd017ed1afa3212d0164dd21b54e7f252eb0ec2de`
Imagen de 0x5d44c bytes, CRC 0xce7dac70, marca `SC21.2`. Es SC21.1 (sin tilt, con feedback de los retornos) más este mando; si falla, vuelve a SC21.1, SC21 o SC20.1, y la última versión segura confirmada es SC17.7.

## Qué hace
En la **vista FX** (botón FX), con **Shift pulsado**, los 8 knobs de la página mostrada (Octave ▼ = reverb, Octave ▲ = delay, como en SC17.5) controlan los **parámetros** de ese efecto en lugar de los envíos:

| Página | K1 | K2 | K3 | K4 | K5 | K6 | K7 / K8 |
|---|---|---|---|---|---|---|---|
| **Reverb** | tipo (0-5: Chamber, Small Room, Large Room, Small Hall, Large Hall, Great Hall) | decay (0-127) | damping (0-127) | — | — | — | — |
| **Delay** | time (0-127) | time sync (0-35) | feedback (0-127) | width (0-127) | L-R ratio (0-12) | slew rate (0-127) | — |

- Los parámetros escalonados (tipo, sync, ratio) avanzan **un paso por clic**; los demás, según el giro. Todos se limitan a su rango.
- Los knobs sin parámetro no hacen nada con Shift. **Los envíos no se tocan** mientras Shift está pulsado; sin Shift los knobs son los envíos de siempre.
- Son los parámetros de proyecto de reverb y delay (los mismos que el MIDI mueve por el canal 16, NRPN 1:18-1:20 y 1:6-1:11, según la Programmer's Reference Guide v3): se **guardan con el proyecto**, el DSP los recibe como si vinieran de MIDI.
- **LEDs**: mientras mantienes Shift, los LEDs de los knobs enseñan el valor de cada parámetro con el brillo (melocotón = delay, crema = reverb, los colores de los Octave de esta vista) y los knobs sin parámetro quedan apagados; al soltar Shift vuelven los LEDs de los envíos.

## Prueba en el aparato (volumen bajo, proyecto de prueba)
1. Botón FX → Octave ▼ (reverb). Mantén Shift y gira K1: el tipo cambia de uno en uno (se oye el carácter de la sala); K2 decay y K3 damping.
2. Octave ▲ (delay). Con Shift: K1 time, K2 sync (escalones), K3 feedback, K4 width, K5 ratio, K6 slew. Suelta Shift: K1-K8 vuelven a ser los envíos y los LEDs los de los envíos.
3. Guarda el proyecto, apaga, enciende y cárgalo: los parámetros se conservan.
4. Con el feedback de los retornos (SC21.1) puedes ahora oscilar el reverb o el delay jugando con decay / feedback.

## Notas técnicas
- `tools/fxparams.py`: slots 4 (knob) y 7 (LEDs) de la clase de las subvistas de la vista FX (vtable `0x0805AF3C`); índices de proyecto `0x20`: reverb 8-10, delay 19-24 (el orden de los NRPN del firmware, ver «SC21.2» en `docs/NOTAS.md`); fijación por `0x08034D92(this + 4, 0x20, índice, valor)`; el repintado de stock es `0x0805095A` y el estado «hemos pintado» es el bit 4 del byte 179 del bloque de Master FX.
