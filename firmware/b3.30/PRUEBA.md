# SC47.3 / Beta 3.30 = SC47.2 / Beta 3.29 + polifonía con dos osciladores y en el VA-drum

`firmware/sc47.3/circuittracks-4486-SC47.3.syx` — SHA-256 `57603b7aae9eedfc6f2a09e8ea9b3137980c2e5d5fb6fccab696f49e019d5711`, marca `SC47.3`.
`firmware/b3.30/circuittracks-4486-B3.30.syx` — SHA-256 `a61d467625478b8c3993a927cab52ecdd94ddad4848bad00289a8f8702a6c267`, marca `B3.30` (**Beta 3.30**, el mismo código).

El usuario (2026-10-26): «stereo ok, add polyphony to the remaing voices»; decisiones: **VA-drum con envolventes por voz**; **FM con 4 voces en total** entre MIDI 1 y MIDI 2 (en la siguiente). Antes, sitio en el DSP: los saltos cercanos del código añadido al núcleo 0 en su forma corta de una palabra (`dsp56.use_shortbr`, −331 palabras).

## Qué probar
1. MIDI 1 con el sinte propio en **dos osciladores** (pad 28), Shift + pad 29 hasta **poly** (magenta): acordes de hasta 4 notas, cada una con los dos osciladores a su altura (FM / sync / ring entre ellos como siempre).
2. **VA-drum** (fila de motores, pad 20) en poly: golpes seguidos se solapan; cada uno cae con su propia envolvente de tono y volumen (un golpe nuevo no reinicia el anterior) y soltar la nota no lo corta. Con 5 golpes, el más antiguo deja su voz.
3. Lo de antes (oscilador, modo muestra, estéreo, FM de una voz, granular) suena igual que en la Beta 3.29.
4. CPU: dos osciladores con supersaw en poly en las dos pistas, con drums y Master FX: escuchar si hay chasquidos.

## Verificación en emulación
- `emu_shortbr_dsp.py` frente a SC47.2 (sin poly): el núcleo 0 entero igual bloque a bloque (tráfico del motor, FM, modo muestra); 350 saltos de una palabra; el programa 147 palabras más corto (con la polifonía nueva).
- `emu_poly2_dsp.py` frente a SC47.2: una voz (dos osciladores, supersaw, VA-drum) igual que antes; dos osciladores con dos voces = la suma de dos voces sueltas × las ganancias, bit a bit, y cada voz con su segundo oscilador en su extensión; VA-drum: A (bloque 0) + B (bloque 3) = A sola + B sola bloque a bloque (B no reinicia A), las envolventes de A bajan, su ganancia = objetivo × envolvente; el ruido por voz; con GAIN 0 / ENVA +63 el VCA abierto (la forma la da la envolvente de la voz).
- `emu_poly2.py`: poly con dos osciladores y en el VA-drum (la base escrita); en el VA-drum soltar no corta, un golpe nuevo sin notas no apaga las demás, el quinto quita la voz más antigua; el modo muestra sigue en poly.
- `emu_poly_dsp.py` / `emu_poly.py`: todo bien salvo «dos osciladores: una voz» (por diseño: ahora son poly).
