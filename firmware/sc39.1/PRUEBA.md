# SC39.1 — patches del sinte propio, selector de fuente del granular, Clear + página

`circuittracks-4486-SC39.1.syx` — SHA-256 `4c5bbb73b58839550a5cdfaaa35c6888613de55dc49ad1099601fff182e93520`
Imagen de 0x67444 bytes, CRC 0x8af83678, marca `SC39.1`.

Es SC39 con:
1. **Patches del sinte propio** (motor de MIDI 1 / 2). En la vista Preset de MIDI 1 / 2 las **filas 2 y 3 (pads 9-24)** son 16 huecos: **tocar = cargar**, **Duplicate + pad = guardar**, **Clear + pad = vaciar**; **Octave ▼ / ▲** = 4 páginas (64 huecos por pack, compartidos por MIDI 1 y 2). Melocotón tenue = con patch, brillante = el último cargado / guardado, apagado = vacío. Se guardan en el relleno de los 64 primeros patches de sinte del pack; el que no exista se crea con el Initial Patch. Un patch lleva el motor entero (motor elegido, dos osciladores, orden de la cadena, todos los valores, ajuste del step-drummer); los pasos del step-drummer y del secuenciador de efectos son del patrón.
2. **Clear + pad de página (1-5)** en esa vista = los valores de esa página de knobs a los iniciales. **Clear + pad 27 ya no reinicia nada** (SC38.7 lo hacía).
3. **Clear + knob en la página granular** reinicia los dos valores de ese knob del granular (antes reiniciaba los del oscilador que comparten knob); **Clear + K8** = la fuente vuelve a la captura.
4. **Selector de fuente del granular** (página del granular, **Shift + K8**): recorrido largo de 128 clics por cinco zonas: la captura (rojo) y el sample que tiene ahora Drum 1 (naranja), Drum 2 (amarillo), Drum 3 (violeta) y Drum 4 (verde azulado). Queda fijado al sample elegido aunque el drum cambie después; blanco tenue = ningún drum tiene ya ese sample. (Ya no se recorren los 64 samples del pack uno a uno.)

## Qué probar
1. MIDI 1, Preset, motor encendido (pad 27). Ajusta el sonido. **Duplicate + pad 9**: el pad queda en melocotón brillante.
2. Cambia el sonido (otro motor, otros valores) y toca el **pad 9**: vuelve el sonido guardado, motor incluido.
3. MIDI 2, Preset, pad 9: el mismo patch en la otra pista.
4. Guarda en otros pads; **Octave ▼**: página 2 (vacía), guarda ahí; **Octave ▲** vuelve. Los LEDs de Octave indican si hay página en ese sentido.
5. **Clear + pad**: el hueco se vacía. Tocar un hueco vacío no hace nada.
6. Apaga y enciende, cambia de pack y vuelve: los patches siguen. Otro pack tiene sus propios huecos.
7. **Los patches de sinte del pack** (vista Preset de Synth 1 / 2) siguen sonando igual; los huecos de sinte que no existían aparecen ahora con el Initial Patch.
8. Editor de CC (pad 25) y step-drummer (pad 30) abiertos: sus pads y Octave funcionan como antes.
9. **Clear + pad 1-5**: solo los valores de esa página vuelven a los iniciales. **Clear + pad 27**: no reinicia.
10. Granular (pad 27 hasta magenta), página 2, **Shift + K8** despacio de un extremo a otro: rojo (captura), naranja, amarillo, violeta, verde azulado; el grano toma el sample del drum de cada zona. Suelta Shift, cambia el sample de ese drum: el granular sigue con el anterior y el LED pasa a blanco tenue.
11. Todo lo de `firmware/sc39/PRUEBA.md`.

## Verificación en emulación
- `emu_sc39_1.py`: la vista por el controlador (Duplicate real, pads, Octave, tarea de LEDs) sobre el modelo de la SD: crear el banco, guardar / cargar / vaciar, banco de 3 patches, páginas, relectura a los 4 s, editor de CC, Clear + página, Clear + 27.
- `emu_sc39_1_gr.py`: Shift + K8 por la ruta real del knob: 240 clics = el modelo, colores y brillo del LED.
- `emu_sc39.py`, `emu_sc38_9.py` sobre SC39.1.
- **Sin comprobar en emulación:** el sonido tras cargar un patch (se comprueban los bytes del estado y que todo se marca para reenviar al DSP) y la escritura real en la tarjeta.
