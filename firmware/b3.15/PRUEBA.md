# SC45.8 / Beta 3.15 (SC45.8 / B3.15) = SC45.7 + un arreglo + los knobs de otra pista en el teclado partido

`firmware/sc45.8/circuittracks-4486-SC45.8.syx` — SHA-256 `f078529e31f4dfeac089c73a0ad23111713fb28acab3bd3b2a82c80d0f38f899`, marca `SC45.8`.
`firmware/b3.15/circuittracks-4486-B3.15.syx` — SHA-256 `b6ddb8f5a9cc9b20685b82251484d71f35189d367e75f5849d7b6540c7b2627a`, marca `B3.15` (**Beta 3.15**).

**Arreglo (también en RC2.06 / RC2.06S): dos pads de la misma nota mantenidos a la vez dejaban la nota sonando** (el usuario, 2026-10-21: «on play note pads, when pad17/32 are held at the same time (both the same C note) the note won't stop until the pad is touched again»).

Causa (del firmware original): el teclado de una pista de notas repite una nota al final de una fila y al principio de la de arriba (pads 17 y 32); el note-on en vivo de la vista de pista `0x0804AEF2(vista, pad, velocity)`, si otro pad ya tiene esa nota (`[vista + 0x40 + i]`), le borra el hueco **sin note-off** y manda un segundo note-on (`0x0804B07A`); al soltar el primero no se manda nada y al soltar el segundo un note-off: dos note-on, un note-off, la primera voz sigue sonando.

Arreglo (`tools/dupnote.py`, zona libre): `0x0804AF2C` (el borrado del hueco) → `bl c_dnoff; b 0x0804AF3C`: el note-off de ese pad con el del original `0x0804AF5A(vista, i)` (que borra el hueco), luego el note-on nuevo: la nota se vuelve a atacar, una sola voz, y el último pad soltado la para.

**Función nueva (solo beta): en el teclado partido, un botón de pista mantenido = los knobs de esa pista** (el usuario, 2026-10-21: «Durante el modo split, aguantar un pad de track abre sus controles en la capa de potes» (una petición)).

`tools/splitknob.py` (zona libre): con el teclado partido de `split4`, un botón de pista (ids 0..7) ya no se pasa al pulsarlo (`split4` cerraba ahí): se mantiene; mientras, la ranura 4 (knobs) del contenedor de las vistas de pista (`0x0805A62C`) va al manejador de knobs de esa pista `[contenedor + 0x148 + 4 t]` y su ranura 7 copia sus 16 B de luces de knob (`0x0804758C`) al fotograma + `0x44`; al soltar, un toque (< 400 ms sin knob) pasa la pulsación entonces (`split4` cierra el partido y el original elige la pista, como antes); una pista de notas mantenida pone el bit de `split4` (otra pista de notas a la vez = un par nuevo). RAM `modmx.MXR + 0x2A0` (12 B, con firma).

## Qué probar
1. **Nota colgada:** Synth 1, vista Note. Mantén los pads 17 y 32 (el mismo do), suelta el 17 y luego el 32: la nota se para. Al revés (suelta primero el 32): también. Lo mismo en MIDI 1 con un sinte externo.
2. **Knobs en el teclado partido:** mantén Synth 1 y pulsa Synth 2 (teclado partido). Mantén **MIDI 1** y gira K1: se mueve el knob 1 de MIDI 1 (sus luces en los knobs mientras lo mantienes); suéltalo: los knobs vuelven a Synth 1 y el teclado partido sigue.
3. Lo mismo manteniendo **Drum 1** (sus knobs) y **Synth 2**.
4. Un toque corto de un botón de pista (sin girar nada): el teclado partido se cierra y queda esa pista, como antes.
5. Con el teclado partido, mantén Synth 1 y pulsa MIDI 2: un par nuevo (Synth 1 arriba, MIDI 2 abajo).
6. Lo demás, como SC45.7 / Beta 3.14 (`firmware/sc45.7/PRUEBA.md`).

## Verificación en emulación
- `emu_dupnote.py` (pads 17 / 32 de la vista Note de Synth 1 por el controlador, la interfaz de notas de la vista: cada note-on con su note-off en los dos órdenes; la build anterior deja uno), `emu_splitknob.py` (botones / knobs por el controlador y la tarea de LEDs real: el manejador que recibe el knob, las luces, el toque, el par nuevo; la build anterior cierra el partido al pulsar), el teclado partido de `emu_sc44_2.py`, `emu_sc45_3.py`, `emu_kbguard.py`.
