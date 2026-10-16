# Beta 1.17 (B1.17) = SC42.7 = SC42.6 + lo pedido tras probarla

`circuittracks-4486-SC42.7.syx` — SHA-256 `7321e380b42e38535f8b7469d31bfbb59e817b512ff037bec562704178819ed5`, marca `SC42.7`.
`firmware/b1.17/circuittracks-4486-B1.17.syx` — SHA-256 `71835b0a10fe76e45cb0a18c7ebd2ee0e4ddd6e4e4ec8b0c60810db7668f1f44`: el mismo código con la marca `B1.17` (**Beta 1.17**).

El usuario (2026-10-16) sobre SC42.6: «cambiar color del pad 29 a amarillo (color del filtro)»; «en step-drummer: poner los knobs por defecto a cero (ahora mismo están al máximo). El modo pitch/vel no parece funcionar correctamente»; «modo roll (en drums): hacer que funcione sin estar play pulsado»; los toggles de la vista Micro Step como interruptores.

- **Step-drummer:** en Synth 1 / 2 un par vacío empieza en **0** (empezaba en la posición del macro; con el macro arriba, todos los knobs al máximo, y con el toggle las notas subían al tope). La transposición del toggle pitch-vel: **un grado de la escala cada 8 pasos del knob** (MIDI −8 … +8 desde el centro; sintes 0 … +16 desde 0). Con el toggle, los destinos de tono de la página pitch (tono de los dos osciladores / del OSC 2) ya no mueven además el sinte propio: lo hace la nota.
- **Vista Micro Step (Gate dos veces), pads 31 / 32:** con los dos apagados, el **pad 31** abre el selector y **elegir una longitud la enciende**; el **pad 32** enciende el gate por pulsación. Con uno encendido, **pulsarlo otra vez lo apaga** (sin abrir nada) y **pulsar el otro** apaga el primero y enciende el nuevo (el pad 31, abriendo su selector). Ya no hay pulsación larga.
- **Rollers de los drums con el transporte parado:** suenan mientras se mantienen, al tempo del proyecto, empezando al pulsar el primero (velocity 100; no se graban).
- **Pad 29 de MIDI 1 / 2** (orden de la cadena) en el color de la página VCA-VCF (el pad 1 de la fila de páginas).

## Qué probar
1. Synth 1, step-drummer: los knobs salen apagados; girar uno sube desde 0. Con el toggle (pad 32), girar el knob de un par sube sus notas de grado en grado (cada 8 pasos del knob).
2. MIDI 1 con el motor y el destino «tono»: con el toggle, la nota sube por grados de la escala sin que el sinte propio se desafine.
3. Micro Step: pad 31 → selector → elegir longitud (pad 31 naranja); pad 31 otra vez → apagado; pad 32 → verde; pad 31 → el 32 se apaga y se abre el selector.
4. Drums, vista Note ampliada, transporte parado: mantener un roller = el drum a tempo.
5. MIDI 1, vista Preset con el motor: el pad 29 en el color del pad 1 de la fila de páginas.

## Verificación en emulación
- `emu_sc42_7.py`: el pad 29 (tenue / brillante en los colores de VCA-VCF); la transposición (MIDI 0 / 1 / 2 / −3 / 8 / −8 grados, sintes 0 / 0 / 1 / 2 / 16) y el reproductor de Synth 1 contra el modelo; el destino de tono con el toggle (osciladores sin tocar) y sin él (+3 semitonos); Synth 1: knobs apagados con el macro 1 a 127, desde 0; Micro Step: la secuencia de los toggles (10 pulsaciones) y el selector; los rollers parados (Drum 1 cada 125 ms a 120 BPM desde el primer fotograma, el micropaso 4 medio paso después, nada al soltar ni en marcha).
