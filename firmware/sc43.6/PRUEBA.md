# Beta 1.26 (B1.26) = SC43.6 = SC43.5 + modo cue en el Mixer + grabación por paso de la vista cromática de drums

`circuittracks-4486-SC43.6.syx` — SHA-256 `b9d0bc65d1f2e4828bd7c7eb371bfe4fec5e6f6a7727b1cb548136c46fccc655`, marca `SC43.6`.
`firmware/b1.26/circuittracks-4486-B1.26.syx` — SHA-256 `4406e3319ec4ace4a0a576396bcacd977997800036fbba2a47d91f3557010810`: el mismo código con la marca `B1.26` (**Beta 1.26**).

El usuario (2026-10-17): «1. Bring it back» (grabar por paso la vista cromática); el modo cue por paneos: «Ok».

- **Modo cue** (Mixer, página de panorama = Octave ▼): **Shift + knob a la derecha** = encendido, **a la izquierda** = apagado; Octave ▼ rosa / blanco; se guarda en el aparato.
- En el modo: **salida izquierda** = la mezcla en mono; **derecha** = solo las pistas en cue. Cada knob de panorama = el envío de esa pista al cue (del centro a la derecha; a la izquierda nada; Clear + knob = sin cue). Los knobs en rosa, más brillantes cuanto más envío.
- Una pista silenciada en cue suena solo por la derecha, en el paso en que va su patrón; su pad sigue tenue; los pads de pista y Shift + pad (al compás siguiente) la meten o la sacan de la mezcla.
- Los paneos de las pistas no se tocan y vuelven al salir. Guardar el proyecto guarda los mutes de la mezcla. La reverb, el delay y Master FX son los de la mezcla: el cue también los oye.
- **Vista cromática de drums:** grabando, cada pad queda en su paso; Clear + K1 a la izquierda borra los pasos cromáticos del patrón que suena. **Los drums ya no graban ni reproducen automatización de panorama** (ese carril guarda los pasos cromáticos).

- **Sinte propio de MIDI 1 / 2:** con un oscilador, **la última nota manda** (al soltarla vuelve la anterior); el **granular** empieza cada nota en su altura (antes el primer grano sonaba con la nota anterior); **página 3 (OSC 2)** en los 8 knobs sin Shift: K1 TUNE 2, K2 SHAPE 2, K3 MIX, K4 FM, K5 FINE 2, K6 BITSYNC, K7 WAVE 2, K8 RING.

## Qué probar
1. Mixer, Octave ▼, Shift + K1 a la derecha: Octave ▼ rosa. Con auriculares en la salida derecha: no se oye nada; la izquierda, la mezcla en mono.
2. K1 a la derecha: Synth 1 aparece en la derecha, cada vez más fuerte; Clear + K1: desaparece.
3. Silenciar Drum 1 (pad 5) y subir su K5: se oye solo en la derecha, a tempo; su pad sigue tenue; pad 5 = vuelve a la mezcla.
4. Shift + K1 a la izquierda: Octave ▼ blanco, todo como antes (paneos incluidos). Apagar y encender: el modo se recuerda.
5. Un drum, Shift + Preset, Record y Play: tocar pads; al volver a pasar, cada paso suena a su altura. Clear + K1 a la izquierda: se borran.
6. MIDI 1 con el oscilador (un oscilador): mantener una nota y tocar otra: cambia la altura; soltar la segunda: vuelve la primera.
7. MIDI 1 en granular con granos largos (K4 a la derecha): una escala, cada nota a su altura desde el principio.
8. MIDI 1, página 3: los 8 knobs mueven TUNE 2, SHAPE 2, MIX, FM, FINE 2, BITSYNC, WAVE 2, RING (pad 28: dos osciladores).

## Verificación en emulación
- `emu_sc43_6.py`: Record + Play, un pad escribe su S en los 6 micropasos de su paso (sin Record, nada); el paso real del reproductor (`0x0804A714`) en un paso con 70: la palabra del pitch de 70 a `X:$A4` y los halfwords del carril 7 a `0xFFFF`; un paso sin valor: la del knob; el reproductor de Drum 2 no toca a Drum 1; la puerta descarta el id 89 y graba el 40; parado, la S del knob vuelve; Clear + K1 a la izquierda borra el carril; modo cue con los grupos DSP reales (Synth 1, Drum 1, envíos de reverb): apagado = el stock; encendido = a la izquierda del todo; cue 40 = nivel L, panorama 64 × 40 / L; el pad en cue = el mute principal (nivel 40, panorama 127, envío 0); Clear + K1; un guardado serializa el mute principal; apagado = el stock; una carga quita los cues; el sinte propio de MIDI 1: un oscilador, 60 y luego 64 = OSC 1 a 64 (n2 guarda 60), soltar 64 = 60 sin puerta nueva; dos osciladores, la parafonía de siempre; el buzón recibe el código 14 antes de GATE y TRIG; página OSC 2: K3 = MIX, K4 = FM, Shift + K1 nada. También `emu_sc43_5.py`, `emu_sc43_4.py`, `emu_sc43.py`, `emu_sc42_7.py` sobre SC43.6.
