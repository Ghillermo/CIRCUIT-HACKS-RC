# Beta 1.27 (B1.27) = SC43.7 = SC43.6 + pitch de drums continuo y cromático a la vez + Clear + Drum

`circuittracks-4486-SC43.7.syx` — SHA-256 `ef26cab41fe5475ead81f2b491ac3ddc92440f3c6b395be72dc3ebb5836cfdba`, marca `SC43.7`.
`firmware/b1.27/circuittracks-4486-B1.27.syx` — SHA-256 `455c5f038ec6558039b3f9fc5cd53b45f15198f2c292a10c3f673b73acf0edb8`: el mismo código con la marca `B1.27` (**Beta 1.27**).

El usuario (2026-10-17): «alternatives to sacrifice pan, I want to be able to both pitch the drums continuously and have chromatic pads»; opción 1: «1 if able».

- **K1 de drums = el pitch de stock**, continuo (se guarda, se automatiza, sale por CC). **Los pads de la vista cromática transponen encima** en semitonos.
- **Grabando**, cada pad cromático queda en su paso **en el carril de pitch del drum** (marcado como nota): un paso guarda un movimiento de K1 o una nota cromática.
- **El panorama de los drums vuelve** (se graba y se reproduce como en el original). En Beta 1.26 los pasos cromáticos movían el panorama.
- **Clear + K1:** izquierda (sostenido) = borra la automatización de pitch, notas cromáticas incluidas; derecha = pitch al centro; las dos ponen el cromático al centro.
- **Clear + el botón de un drum:** borra la automatización de sus knobs en el patrón que suena y los pone por defecto.
- **Step-drummer de Synth 1 / 2:** Play / Record no lo cierran; el botón del sinte lo devuelve si estaba abierto.
- **Rollers** de un drum silenciado en el Mixer: suenan durante la reproducción.
- **Shift + Play = cuantizar** el patrón que suena en la pista elegida: micropasos 1-2 → el inicio de su paso, 3-5 → el del siguiente (el último paso al primero); un redoble de drum se queda. LED de Play con Shift: amarillo; verde tras cuantizar.
- **Arpegiador:** la primera nota mantenida se apaga al empezar el arpegio (en MIDI 1 / 2 seguía sonando debajo); **resolución (Shift + pads 17-24) en el orden del sync rate**: pad 17 = 1/4 … pad 24 = 1/32T.
- **MIDI 1 / 2, vista Preset: Shift + pad 29 = gate retrigger** (verde encendido, por defecto; amarillo apagado = legato: una nota nueva con otras pulsadas solo cambia la altura). Se guarda con el proyecto.

## Qué probar
1. Un drum: K1 mueve el pitch de forma continua; Shift + Preset: los pads suben y bajan a semitonos sobre ese pitch.
2. Record + Play: girar K1 en unos pasos y tocar pads cromáticos en otros; al volver a pasar, los dos se reproducen.
3. Mixer, página de panorama: girar el panorama de un drum con Record: se graba y se reproduce.
4. Clear + K1 a la izquierda (sostenido): desaparecen los dos. Clear + Drum 1: automatización borrada y knobs por defecto.
5. MIDI 1 con el oscilador: Shift + pad 29 (amarillo) y tocar legato: la segunda nota cambia la altura sin volver a disparar; otra vez (verde): cada nota dispara.
6. Synth 1, su vista del step-drummer (Synth 1 dos veces, pad 30): Play y Record no la cierran; Drum 1 y luego Synth 1: vuelve; pad 30 la cierra.
7. Drum 1 silenciado en el Mixer, sonando: los rollers de su vista Note suenan.
8. Grabar notas en directo en Synth 1 (y golpes en un drum) algo fuera de tiempo; Shift (Play amarillo) + Play: quedan en la rejilla, Play verde hasta soltar Shift; la reproducción no arranca.
9. MIDI 1 con el arpegiador (Pattern Settings, Shift + pad 25): mantener dos notas, parado y sonando: arpegio de las dos, sin la primera colgada (también por un sinte externo); soltar: nada sonando.
10. Pattern Settings con Shift: pad 17 = arpegio lento (1/4), pad 24 = rápido (1/32T); lo mismo en un drum.

## Verificación en emulación
- `emu_sc43_7.py`: K1 = P (S queda en 64), Shift + K6 no mueve P; un pad fija S y no P; con Record + Play el carril 0 recibe `0x80 | S` en los 6 micropasos del paso; el paso real del reproductor: `0x85` no se aplica como P y escribe la palabra de S, `0x50` se aplica como P 80, el carril 7 = `0x30` se aplica como panorama (id 0x59); la puerta graba el id 89; Clear + K1 = S 64; Clear + Drum 1 borra el carril 0 y pone P / S a 64; OSC 2 (como SC43.6): K6 = BITSYNC, Shift + K6 nada; gate retrigger: por defecto la segunda nota manda GATE y TRIG, Shift + pad 29 = apagado (`0xA1` en la cola + 159; LED amarillo con Shift, verde encendido): la segunda nota manda NOTE sin GATE / TRIG; step-drummer de Synth 1: Play / Record lo mantienen, Drum 1 y Synth 1 lo devuelven, el pad 30 lo cierra; Drum 1 silenciado y sonando: el aviso de tick real de su reproductor toca los rollers de los micropasos 0 / 2 (SC43.6: nada) y su note-off sale a los 100 ms; arpegiador de MIDI 1 hasta el transmisor MIDI: la primera nota se apaga antes del arpegio y al soltar no queda nada encendido (SC43.6: la primera seguía); Synth 1: la primera nota por la interfaz de su vista; resolución: Shift + pad 17 = 1/4, pad 21 = 1/16, pad 24 = 1/32T (notas y Drum 1); Shift + Play: notas en los micropasos 2 / 3 / 4 a la rejilla (la misma nota en el paso siguiente se quita, un paso vacío toma la probabilidad), drums 2 / 4 / 5 a la rejilla con velocity, probabilidad y sample flip, un redoble se queda, el almacén de edición del drum sincronizado, el transporte no arranca; LED de Play con Shift amarillo / verde. También `emu_sc43.py`, `emu_sc42_7.py`, `emu_sc42_8.py`, `emu_sc42_9.py`, `emu_sc43_4.py` sobre SC43.7.
