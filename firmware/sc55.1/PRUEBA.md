# SC55.1

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc55.1/circuittracks-4486-SC55.1.syx` | `1c4c02c513df145359aa1fd8409486d05e02689039baafeff7ec539e19f85dab` | `SC55.1` |

**Qué cambia** respecto a SC55 (SC54.1, la segunda versión del morph, + el FM más suave en notas agudas), en el morph de patches (el usuario, 2026-11-08):
- **Clear no sale de la vista del morph**; Clear + knob sigue poniendo ese knob a 0.
- **Clear + el botón de la pista (Synth 1 / 2, MIDI 1 / 2) en la vista del morph = estado inicial**: los ocho knobs a 0 / centro (K1 al primer patch de la cadena); la vista sigue.
- **Pads 1 / 8 mantenidos = la envolvente se sostiene arriba**; al soltar cae.
- **La cadena son solo los patches mantenidos**: el sonido de antes ya no entra (salvo que mantengas su patch); K1 = del primero al último. Octave en la vista del morph ya no hace nada (no hay patch inicial que mover).

**Usar con una copia de la tarjeta.**

## Qué probar
1. Synth 1, vista Preset: mantén dos patches 0,4 s = vista del morph. K1 a la izquierda = el primer patch mantenido, a la derecha = el último (el sonido de antes no está en la cadena).
2. Pulsa Clear solo: sigues en la vista del morph. Clear + un knob: ese knob a 0.
3. Gira varios knobs; Clear + Synth 1: todos a 0 / centro y la vista sigue.
4. Mantén el pad 1 (o el 8) con K7 (cantidad de la envolvente) girado: el morph se queda arriba mientras lo mantienes y cae al soltarlo.
5. Lo mismo en MIDI 1 / 2 con el sinte propio.

## Verificación en emulación
`emu_morph.py --clear --sus --nocur`: ALL PASS.
