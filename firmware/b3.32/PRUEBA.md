# SC47.5 / Beta 3.32 = SC47.4 / Beta 3.31 + modo de voz en el pad 32 (portamento, unísono) + el reloj con FM poly

`firmware/sc47.5/circuittracks-4486-SC47.5.syx` — SHA-256 `7b7e59b9bb0294c0e882d2fa5009eb86c23fefc165a0455ef41f7bf90339a32b`, marca `SC47.5`.
`firmware/b3.32/circuittracks-4486-B3.32.syx` — SHA-256 `65059646ab7dc73cf7b896a8077648b626dec31b21f5dbfca275d7aa2fbcc14d`, marca `B3.32` (**Beta 3.32**, el mismo código).

El usuario (2026-10-26): «si, implementa portamento. asigna el toggle al pad 32, sin shift: retrig/legato/portamento/poly/unison. con un desplegable como el modo de voz» y «tengo la sensación de que el clock se vuelve inestable al usar FM poly».

## Qué probar
1. **El reloj con FM poly** (lo primero): MIDI 1 en FM poly con un patrón de drums sonando; tocar acordes, sostenerlos, soltarlos. El tempo no debe tambalearse (antes: ~29 escrituras al DSP por milisegundo con notas sostenidas y ~200 de golpe en cada acorde; ahora ~1,3 y ~35). Comparar con la Beta 3.31 si hace falta.
2. **Pad 32** (vista Preset de MIDI 1 / 2, motor encendido): se ve en el color del modo; un toque abre los modos en los pads 17-21 (verde retrigger, amarillo legato, cian portamento, magenta poly, naranja unísono; el actual brillante); tocar uno lo elige; el pad 32 otra vez lo cierra. Pad 27 con el desplegable abierto: se cierra el nuestro y se abre el de motores.
3. **Portamento** (pad 19): la altura se desliza de nota a nota (también entre notas separadas); con el desplegable abierto, K1 cambia el tiempo (a la izquierda del todo, sin glide; hasta ~2 s). Con notas pulsadas, sin volver a disparar la envolvente. Probar con uno y dos osciladores, VA-drum y FM.
4. **Unísono** (pad 21): una nota suena con 4 voces desafinadas (K2 con el desplegable abierto: de 0 a ±50 cents); cada nota nueva las mueve todas; suenan hasta soltar todas. En FM con MIDI 1 y MIDI 2 en FM poly o unísono, 2 voces cada una.
5. **Shift + pad 29** pasa por los cinco modos (con Shift, el pad 29 en el color del modo).
6. **Guardado:** guardar un patch del sinte propio con portamento / unísono y otros tiempos; cargar otro y volver: el modo, el tiempo y la desafinación vuelven. Guardar el proyecto, cargar otro, volver: igual.
7. Poly, retrigger y legato como en la Beta 3.31; con el pad 7 de FM mantenido (los algoritmos) o la superposición de ratios, el pad 32 es de FM.

## Verificación en emulación
- `emu_glide_dsp.py` frente a SC47.4: sin glide, el anillo igual (también con un cambio de nota); con glide, el desplazamiento bloque a bloque = (GO − (nota − última) << 16) × GK, el incremento sube hasta el de la nota 72 y el desplazamiento acaba en 0; la palabra de desplazamiento de una voz = 5 × 512 suena bit a bit como FINE + 5 (la desafinación del unísono).
- `emu_vmode.py`: el desplegable, los colores, la forma nueva del byte, `c_rtoff` / `c_pyflag`, K1 / K2 (con tope) y sus LEDs, GK[58] escrito al DSP una vez, el cierre por tiempo, Shift + pad 29, el unísono (4 voces en la nota con los desplazamientos −h, −h/3, h/3, h y el objetivo × 1/2; otra nota sin pasar por 0; se sueltan con la última), la forma antigua del byte, el guardado con el patch (relleno + 126 por projsyn y vuelta).
- `emu_fmspi.py` frente a SC47.4: escrituras al DSP por tick con FM poly: acorde 189 (el primero tras encender; 198 antes), 35 con la caché caliente (201), sostenido 1,3 (28,7), release 5,3 (18,5), silencio ~1 (8,8).
- `emu_poly3.py`, `emu_poly2.py`, `emu_poly3_dsp.py`, `emu_poly2_dsp.py`, `emu_fmeng2.py`: bien.
