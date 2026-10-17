# Beta 1.28 (B1.28) = SC43.8 = SC43.7 + sidechain de drums con Synth / MIDI + el sinte propio guardado entero

`circuittracks-4486-SC43.8.syx` — SHA-256 `f98932adf8c07f5b010c33fb28bc78262530de9848d5a856c2bcf24dfada6636`, marca `SC43.8`.
`firmware/b1.28/circuittracks-4486-B1.28.syx` — SHA-256 `d69b5e5a959e6ca936bd03817429a830d7da1ea5e5b5a56f5c1233325fba33cc`: el mismo código con la marca `B1.28` (**Beta 1.28**).

El usuario (2026-10-17): «add gate sidechain to the drums»; «revisa el guardado de sintes propios y granular, hay parámetros que no parecen cargarse al reiniciar, especialmente los shift».

- **Sidechain de los drums con Synth 1 / 2 y MIDI 1 / 2:** vista Sidechain (Shift + FX), Octave ▼ hasta las páginas de drums: tocar un preset de un drum (filas 3-4) y luego un **pad 1-4 de la fila 1** = Synth 1, Synth 2, MIDI 1, MIDI 2 como su disparo; cada nota del patrón de esa pista abre la envolvente del drum. Un pad 5-8 vuelve a un drum. No se guarda (como el resto del sidechain entre drums).
- **El sinte propio de MIDI 1 / 2 conserva al apagar** la página OSC 2, los knobs con Shift del granular (Shift + K1-K5, K7) y del oscilador (Shift + K2 / K3), los pads 28 / 29 y la página de knobs. El primer encendido con esta versión aún da los valores iniciales.

## Qué probar
1. Un patrón de Synth 1 con notas y otro de Drum 2 (un bucle largo, por ejemplo). Shift + FX, Octave ▼ dos veces: página Drums 1 / 2. Un preset de Drum 2 (fila 4) y el pad 1 de la fila 1: Drum 2 se agacha con cada nota de Synth 1. Pad 4: con MIDI 2. Pad 6 (un drum): como antes.
2. MIDI 1 con el granular: mover Shift + K1, K2, K5 y K7; la página OSC 2 con dos osciladores (pad 28) y el orden de la cadena (pad 29). Esperar unos segundos parado (el guardado diferido), apagar y encender: todo como estaba.
3. Lo mismo con un patch propio cargado después: sigue cargando como siempre.

## Verificación en emulación
- `emu_sc43_8.py`: página Drums 1 / 2, pad 18 = preset 1 de Drum 1, pad 1 = Synth 1 como disparo (byte 4): una nota de patrón de Synth 1 escribe `X:$3A10` = 1, una de MIDI 1 nada; pad 4 = MIDI 2; pad 5 = Drum 1 otra vez (Synth 1 ya no dispara); Drum 2 con Synth 2 escribe `X:$3A19`; su preset OFF no dispara nada; LEDs: el elegido en `0x45`, los demás `0x02`. Guardado: el `0x0802D2AC` real escribe en su copia los códigos 27..34 de las dos pistas, los bits (`0x69`), `0xE7` y la suma, sin tocar el registro en RAM; un encendido (`c_esboot` con vcf21 sin inicializar) con ese registro devuelve los 16 valores y los bits (ACT sucio, la nota 60 se queda); sin la firma o con la suma mal, los iniciales; el registro escrito, encendido otra vez: lo mismo; el K6 de OSC 2 (código 32), el pad 28 y Shift + K1 del granular (código 28) piden el guardado. También `emu_sc43_7.py`, `emu_sc43_4.py`, `emu_lazysave.py`, `emu_sc39_4.py` y otras sobre SC43.8.
