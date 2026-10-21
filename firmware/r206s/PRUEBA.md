# RC2.06 / RC2.06S (R206 / R206S) = RC2.05 + un arreglo

`firmware/r206/circuittracks-4486-R206.syx` — SHA-256 `d37ec28232a1a2b3edb950a9546863cec6fa4a5587db3847a35336d5dcecf0e4`, marca `R206` (**RC2.06**).
`firmware/r206s/circuittracks-4486-R206S.syx` — SHA-256 `465f44da016447d06162c30ba402e1667d2834bb5b019d2bbaf2cae3f8a8d766`, marca `R206S` (**RC2.06S**).

**Arreglo: dos pads de la misma nota mantenidos a la vez dejaban la nota sonando** (el usuario, 2026-10-21: «on play note pads, when pad17/32 are held at the same time (both the same C note) the note won't stop until the pad is touched again»).

Causa (del firmware original): el teclado de una pista de notas repite una nota al final de una fila y al principio de la de arriba (pads 17 y 32); el note-on en vivo de la vista de pista `0x0804AEF2(vista, pad, velocity)`, si otro pad ya tiene esa nota (`[vista + 0x40 + i]`), le borra el hueco **sin note-off** y manda un segundo note-on (`0x0804B07A`); al soltar el primero no se manda nada y al soltar el segundo un note-off: dos note-on, un note-off, la primera voz sigue sonando.

Arreglo (`tools/dupnote.py`, zona libre): `0x0804AF2C` (el borrado del hueco) → `bl c_dnoff; b 0x0804AF3C`: el note-off de ese pad con el del original `0x0804AF5A(vista, i)` (que borra el hueco), luego el note-on nuevo: la nota se vuelve a atacar, una sola voz, y el último pad soltado la para. RC2.06S = RC2.05S + lo mismo.

## Qué probar
1. Synth 1, vista Note. Mantén los pads 17 y 32 (el mismo do), suelta el 17 y luego el 32: la nota se para. Al revés (suelta primero el 32): también. Lo mismo en MIDI 1 con un sinte externo.
2. Un solo pad, acordes, el arpegiador: como antes.
3. Lo demás, como RC2.05 (`firmware/r205/PRUEBA.md`).

## Verificación en emulación
- `emu_dupnote.py` (pads 17 / 32 de la vista Note de Synth 1 por el controlador, la interfaz de notas de la vista: cada note-on con su note-off en los dos órdenes; RC2.05 deja uno).
