# SC47.9 / Beta 3.36 = SC47.8 / Beta 3.35 + parejas estéreo de drums + notas y flips en el selector de samples

`firmware/sc47.9/circuittracks-4486-SC47.9.syx` — SHA-256 `033b97770155fdf3d38ac6e6a141c08729a54ea1b7b699628984fd10553048b5`, marca `SC47.9`.
`firmware/b3.36/circuittracks-4486-B3.36.syx` — SHA-256 `749244a6d8069b6384681f2796630318e707d773189b38d171baded6752f72ef`, marca `B3.36` (**Beta 3.36**, el mismo código).

El usuario (2026-10-24): «modo sample stereo: al pulsar drum1+2 o drum 3+4 …»; decisiones del 2026-10-25 (K2 de la pareja = apertura, desafinación en cents, sin desviación de distorsión, los pads de Drum 2 / 4 suenan solos a la derecha, del 64 al 1, se guarda con el proyecto); 2026-10-27: «implement stereo pair as planned».

## Qué probar (en este orden)
1. **El gesto:** mantén Drum 1 y pulsa Drum 2 → pareja (el botón de Drum 2 late en el color de Drum 1); otra vez → dos drums. También Drum 2 mantenido + Drum 1, y Drum 3 + Drum 4. Pulsación larga: la vista se queda en Drum 1. Con Shift, Clear o Duplicate pulsados, o en Setup: nada.
2. **Un sample estéreo** en dos huecos seguidos del pack (izquierda en N, derecha en N + 1): Drum 1 en N → la pareja suena en estéreo. Con la apertura (K2 de Drum 2) a la izquierda del todo, los dos al centro.
3. **Prueba de fase:** el mismo sample mono en N y N + 1, apertura a 0: debe sonar como un solo drum más fuerte (sin flanger): si suena con flanger, los dos lados no salen a la vez.
4. **Lo de Drum 1 manda en los dos:** pasos, sample flips (el de la derecha toca el flip + 1), micropasos, arpegio, rollers, random-mutate, sus knobs (también con Shift), su automatización, nivel / mute / envíos del Mixer y sidechain.
5. **Los knobs de Drum 2** en pareja: K1 desafinación, K2 apertura, K3 decay, K4 env → corte, K5 filtro / EQ, K6 resonancia, K7 LFO; con Shift: K1 env de tono, K2 ring, K3 inicio, K4 forma, K6 frecuencia del ring. Clear + knob = sin desviación. Nada se graba ni sale por MIDI.
6. **El patrón de Drum 2 no suena** durante la pareja; sus pads y sus notas MIDI (62) lo tocan solo, a la derecha. Elegir otro sample en la vista Preset de Drum 2 → esa distancia se mantiene al cambiar el sample de Drum 1.
7. **Modo cue** del Mixer con la pareja: los dos siguen al cue de Drum 1 (sin estéreo).
8. **Teclado partido** abierto: el gesto funciona y el partido se queda.
9. **Deshacer:** Drum 2 vuelve a sonar con sus propios valores, su patrón y su panorama.
10. **Guardar / cargar / apagar:** la pareja vuelve con el proyecto (distancia, apertura, desviaciones); un proyecto sin ella carga sin pareja.
11. **Un patrón cargado** (los 4 drums con rollers rápidos y la pareja): sin tartamudeos ni chasquidos.

## Selector de samples del sinte propio (modo muestra; el usuario, 2026-10-27)
12. Toca una nota en MIDI 1 (vista Note), pasa al selector (Note dos veces) y pon un flip en un paso vacío (paso mantenido + sample, o sample mantenido + paso): el paso queda **melocotón** y suena con esa nota y ese sample. En un paso que ya tenía nota, la nota no cambia.
13. Colores de los pasos: melocotón = nota con flip, cian = nota sin flip, violeta = flip sin nota, cian tenue = nada.
14. En la vista Note, **Clear + paso** sobre un paso con flip: la nota se borra y en el selector el paso queda **violeta** (el flip sigue). Lo mismo con el paso mantenido + la tecla de su nota. Clear + paso en el selector quita el flip, como antes.

## Verificación en emulación
- `emu_smnote.py`: la última nota, el flip con nota nueva (y la nota que ya había, intacta), los colores de los pasos, Clear + paso y paso mantenido + tecla en la vista Note dejan el flip (el nivel automatizado se borra como antes).
- `emu_stpair.py` frente a SC47.8: el gesto, los golpes (la pareja dispara Drum 2 con la misma velocity, el sample + 1 y el pitch de Drum 1), el secuenciador de Drum 2 parado, los panoramas tras el flush (izquierda / derecha; apertura 0 = centro), la desafinación, los códigos propios de los drums (los dos buzones), el sidechain, el LED, la distancia al elegir sample, guardar / cargar, deshacer y los golpes sin pareja iguales que SC47.8; el flush con la pareja no toma el semáforo del DSP.
