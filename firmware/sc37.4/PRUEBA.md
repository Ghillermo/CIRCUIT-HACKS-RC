# SC37.4 — Duplicate en Preset, copiar entre packs, cambio de motor sin clic, dos Glitch, colores

`circuittracks-4486-SC37.4.syx` — SHA-256 `26ff69b59a325bfb9b250d7a5d7adeb1f8f65b5cabba24c95802b3fd6d0dec59`
Imagen de 0x65a3c bytes, CRC 0x31951fe9, marca `SC37.4`.

Es SC37.3 con:

1. **Duplicate en la vista Preset de Synth 1 / 2 (y de drums).** En SC37.3 no se encendía ni hacía nada con los patches: el aparato solo admite Clear como botón mantenido en las vistas Preset, y las pruebas lo habían simulado a mano. Ahora Duplicate se enciende en esas vistas y funciona (las pruebas pulsan el botón de verdad).
2. **Entre packs, Duplicate copia** (samples y patches): A se copia sobre B en el pack cargado y **el pack de A no cambia**. Dentro del mismo pack sigue intercambiando.
3. **Cambiar de motor (pad 27) con una nota mantenida ya no hace clic:** el nivel del sustain se desliza en lugar de saltar (VA-drum lo pone a 0, el oscilador lo devuelve). Girar SUS con la nota mantenida también se desliza.
4. **Pad 28 (uno / dos osciladores)** apagado y sin efecto salvo con oscilador o VA-drum.
5. **Dos huecos con Glitch** pulsados a la vez ya no se copian los knobs: suena el último pulsado y al soltarlo vuelve el otro. Solo el pad 31 asigna el Glitch.
6. **Colores:** Vinyl en melocotón; en Setup, el pad 22 (reverb → tira 3) en crema y el pad 23 (delay → tira 4) en melocotón.

## Qué probar (packs de prueba, con copia de la SD)
1. Vista Preset de Synth 1: Duplicate debe estar encendido. Duplicate + pad A, cargar otro pack, Duplicate + pad B: B pasa a ser A y suena al momento; en el pack de A, A sigue igual.
2. Lo mismo con un sample (vista Preset de drums). Dentro del mismo pack, Duplicate + A + B intercambia.
3. MIDI 1 en oscilador con una nota larga mantenida: cambia el pad 27 a VA-drum y vuelve: sin clic; el nivel baja / sube suave. Gira SUS con la nota mantenida.
4. Pad 27 en línea, granular o secuenciador de efectos: el pad 28 apagado y pulsarlo no hace nada.
5. Master FX: asigna el Glitch (pad 31 + pad) a dos huecos con knobs distintos; púlsalos a la vez y suelta: cada uno conserva sus knobs.
6. Master FX: Vinyl (pad 6) en melocotón. Setup: pads 22 / 23 en crema / melocotón (apagado tenue, encendido brillante).
