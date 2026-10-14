# SC40.9 / Beta 1.0 — modo cadena global, drums, Master FX por sesión, compresor, Record en Setup y arreglos

`circuittracks-4486-SC40.9.syx` — SHA-256 `cbf029321190e45fc516c55b6868ea2c90081921ac0ffc6540c41a615dec49bc` (imagen de 0x6a244 bytes, marca `SC40.9`).
`firmware/b1.0/circuittracks-4486-B1.0.syx` — SHA-256 `b52c81abdba59fa7baa32d0a16b14b59cc0c91455648d22da5f568bc28a66522`: el mismo código con la marca `B1.0` (**Beta 1.0**, la que se publica).

Es SC40.8 con lo pedido el 2026-10-14 después de probar SC39.7-SC40.8 en el aparato. **Escribe en la SD** (como SC40.7).

## Qué probar
1. **Modo cadena de todo el proyecto.** Vista Patterns: con Shift, Octave ▲ en amarillo; **Shift + Octave ▲** = modo activado (Octave ▲ verde) para todas las pistas; **Shift + Octave ▼** lo desactiva. Sal de la vista y vuelve: sigue como estaba.
2. **Escenas mezcladas.** Con el modo activado y alguna regla, guarda la escena 1; desactiva el modo y guarda la escena 2. En el Mixer la 1 sale en melocotón. Tócalas (parado y en marcha): la 1 sigue las reglas, la 2 no, y el indicador de la vista Patterns cambia con ellas.
3. **Modo desactivado con una pista en su patrón B:** vuelve a A al acabar el patrón.
4. **Clear + patrón:** fuera del modo borra el patrón, su regla y su orden fractal / deconstruido. En el modo: con regla, solo quita la regla; sin regla, borra el patrón.
5. **Drums:** Pattern Settings de un drum: pads 26 (naranja), 27, 28 encendidos. Fractal, deconstruido y Nudge como en las pistas de notas (Nudge lleva también la automatización y los sample flips).
6. **Compresor master:** vista Sidechain (Shift + FX): K7 = ataque, K8 = release, en blanco con su valor (con el compresor activado en Advanced Setup). En la vista Setup K1 / K2 ya no hacen nada.
7. **Master FX por sesión:** cambia knobs de la fila superior y huecos de la inferior, guarda el proyecto A; carga el B, cámbialos y guárdalo; vuelve a A: vuelven los de A (y el ataque / release del compresor). Un proyecto antiguo no cambia nada.
8. **Record en Setup:** en la vista Setup (Shift + Save), Record se enciende en amarillo / se apaga. Con MIDI 1 en el canal de Synth 1 y Record normal en marcha: apagado, lo que tocas en MIDI 1 no se graba en Synth 1; en amarillo, sí.
9. **Secuenciador de efectos:** con Synth 1 y MIDI 1 de longitudes distintas, la secuencia de efectos dura lo que el patrón de MIDI 1. El knob selector va tres veces más lento. (Recuerda: un hueco sin efecto asignado no hace nada.)
10. **Step-drummer** de MIDI 1 / 2 y de Synth 1 / 2 con patrones de longitudes distintas entre pistas: la fila de pitch sigue a su pista.

## Verificación en emulación
- `emu_sc40_9.py` (17 comprobaciones, por el controlador y el avance de pista de stock): el modo y las escenas, Clear, drums (patrón entero byte a byte), el bloque de Master FX en la cola del proyecto (guardar, cargar, suma mala, sin bloque), el compresor en K7 / K8, Record en Setup y las tres puertas del grabador, la pista que lee el secuenciador de efectos, el knob.
- `emu_sc40_8.py` y `emu_sc40_3.py` sobre SC40.9.
- **Sin comprobar en emulación:** el sonido; la carga real de un proyecto (se simula lo que hace el gancho de carga); la grabación real de una nota inyectada (se comprueba que la puerta deja pasar); la vista Setup se pone a mano en el controlador.
- **Pendiente:** el stutter del delay al mover parámetros del sinte (sin localizar) y el acceso al step-drummer con la lista de presets (no reproducido).
