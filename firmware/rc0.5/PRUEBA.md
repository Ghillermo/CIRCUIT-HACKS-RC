# RC0.5 — el sample capturado, delante de los efectos de Master FX

`circuittracks-4486-RC0.5.syx` — SHA-256 `38a1f4e38a2851103435f5226fcda665632da4fd419212782e0fe3cbe7d51e69`
Imagen de 0x66014 bytes, CRC 0x4b6322ba, marca `RC0.5`.

Es RC0.4 con un cambio en el DSP: **El sample capturado va delante de los efectos de Master FX.** El sample que se dispara (pad 7, los huecos de la fila inferior) pasa ahora por los efectos de Master FX (Gater, Auto-Filter, Digitise, Phaser, Vinyl); antes sonaba sin ellos. A cambio, **la captura (pad 32) graba el master sin los efectos de Master FX** (antes los llevaba); sigue sin grabarse a sí misma. El Glitch (pad 31) también queda delante de los otros efectos.

## Qué probar
1. Graba algo con el pad 32 y dispáralo con el pad 7. Enciende uno a uno los efectos 1-6: **todos deben oírse sobre el sample**.
2. Con un efecto encendido, graba otra vez: la captura debe sonar **sin** ese efecto al reproducirla con los efectos apagados.
3. Glitch (pad 31) con otros efectos encendidos: suena y los otros efectos lo procesan. Sin chasquidos ni cortes al encender / apagar.
4. Sustituir un drum por la captura (Clear + pad en la vista Preset de drums) y Save: como antes.
5. Song pointer, captura armada (Shift + pad 32) y bucle enganchado (Shift + pad 7): como antes.
6. Todo lo de `firmware/rc0.4/PRUEBA.md`.

## Verificación en emulación
- `emu_sc39_2_dsp.py`: en la imagen, `fx_hook` = `jmp smp_post`, `fx_out` con su final propio, el programa del núcleo 0 por debajo de `$4000`; en el intérprete, con una cadena de prueba que divide por dos: la captura = el master tal como entra, lo que sale = (master + sample) / 2, grabar mientras suena no graba el sample, M4 y r1 como antes.
- **Sin comprobar en emulación:** el sonido real con cada efecto y la carga del DSP (el código es el mismo, cambia el orden).
