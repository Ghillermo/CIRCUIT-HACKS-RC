# SC50 / Beta 5.3 = SC49.9 + random-mutate rediseñado + sweep de la automatización + secuenciador de saltos

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc50/circuittracks-4486-SC50.syx` | `665c734d2db49aad51124ce3c911e49dd980199914ab409eadef2619782a1823` | `SC50` |
| `firmware/b5.3/circuittracks-4486-B5.3.syx` (**Beta 5.3**) | `147941ca8635ac8930018bd19bfe4dd4fe548fa9c4345eb819d7a5a7a0a08f76` | `B5.3` |

El usuario (2026-11-01): «Rediseña el modo Random mutate»; «extiende esta funcionalidad a drums si es posible»; «incluye el control de insertar sweep manualmente a la interfaz de automatización del sinte»; «interpola entre dos estados de automatización»; «pulsando uno y después el otro».

## Qué cambia
- **Modo 2 de la vista de probabilidad** (pad 25 de Pattern Settings, un paso con notas mantenido; `mutate39.use_mut2()`, `stepmod`, `drumpat`, solo beta): pad 17 apagado; 18-20 otra nota de la escala (×1, ×2, ×4); 21 octava abajo; 22 arriba; 23 / 24 abajo o arriba (×1, ×2); 25 dinámicas sí / no; 26 acentos; 27 acentos y longitud; 28 longitud al azar y velocity ±16; 29-31 nada; 32 micropasos sí / no.
- **Octave ▼ / ▲ en esa vista = factor de la pista** (`tools/mutfac.py`), ×0 a ×8, ×1 de fábrica, guardado con el proyecto. A ×1: nota y octava 6 % por cada ×1 del pad; dinámicas y micropasos 25 %.
- **Drums:** los mismos pads; el sample en lugar de la nota (±1 en su fila, ±8 a otra fila), el pad 27 apagado, el pad 28 solo velocity, el pad 32 vale para todo el drum y solo retrasa el golpe.
- **Sweep** (`autorel.use_sweep()`): vista Velocity con Shift, un paso amarillo mantenido + otro paso amarillo = línea recta en los carriles con valor en los dos.
- **Nudge** (`playmode.use_nudge3()`, el arreglo de RC4.04): el contenido del tramo, sin mover el primer y el último paso: ver [`firmware/r404/PRUEBA.md`](../r404/PRUEBA.md).
- **Los valores que ya estaban en los pasos se conservan y significan lo nuevo.**

- **Secuenciador de saltos** (`tools/jumpseq.py`, solo beta): vista Preset de MIDI 1 / 2, pad 27: los pads 9-16 son las ocho pistas; un toque apunta, el mismo apaga. Mientras apunta, la pista no suena y sus notas hacen saltar esa pista al paso que indican, en el mismo paso de la nota. Vista Note: pads 17-32 = pasos 1-16, Octave ▲ = 17-32; ampliada: pasos 1-32; la escala no cambia nada (mientras se ve, Jankó automático; `janko.use_jump`). Se guarda con el proyecto.
- **Tabla de cents de los drums en 16 bits** (`tools/centab.py`, sitio para lo anterior): dentro de 0,03 cents.

## Qué probar
1. Synth 1, un patrón con notas, Pattern Settings, pad 25. Mantén un paso: pad 17 blanco brillante. Toca 19 y deja sonar: otras notas de la escala alguna vez. Con Octave ▲ tres veces (los pads enseñan el número): más a menudo. Octave ▼ hasta 0: nunca. Octave ▼ se apaga en 0, Octave ▲ en 8.
2. Pads 21, 22, 23, 24: octava abajo, arriba, las dos.
3. Pad 25: verde; pads 26, 27, 28: acentos, acentos con longitud (las fuertes más cortas, las débiles más largas), longitud al azar. Pad 25 apaga.
4. Pad 32: las notas se adelantan o se atrasan algo, sin salir de su paso.
5. Con Record y la vista en pantalla: lo que suena se escribe en el patrón. Sin la vista: no.
6. Guarda el proyecto y cárgalo: el factor sigue. Otro proyecto: ×1.
7. Drum 1, Pattern Settings, pad 25. Elige un paso con golpe. Pads 18-20: samples de al lado; 21-24: otra fila; 25, 26, 28: velocity; 27 apagado; 32: el golpe llega un poco tarde, en todo el drum, y funciona también en un paso sin golpe.
8. Sweep: MIDI 1 (o Synth 1), graba dos valores de un knob en los pasos 3 y 11. Vista Velocity, Shift: mantén el paso 3 y pulsa el 11: los pasos de en medio se ponen amarillos y el knob barre entre los dos valores al sonar. Pulsar un paso sin automatización como segundo no hace nada. Dos toques seguidos sin mantener: solo escuchar.
9. Un arpegio sobre un paso con nivel: sus notas también mutan.
10. Una nota ligada al paso siguiente, con el pad 32 en ese paso: la ligadura no se corta.
11. Un drum con varios golpes en un paso (un roller grabado) y el pad 32 a ×8: suenan todos.
12. Saltos: Synth 1 con un patrón de 16 pasos en el que se oiga cada paso. MIDI 1, vista Preset, pad 27: pads 9-16 tenues en los colores de las pistas, el de MIDI 1 sin luz. Pad 9: Synth 1 brilla y el pad 27 toma su color. Pad 27 cierra la fila.
13. Vista Note de MIDI 1, Record: toca el pad 17 en el paso 5 y el pad 25 en el paso 9. Sin Record: Synth 1 salta al paso 1 al llegar al 5 y al paso 9 al llegar al 9, justo en ese paso, y sigue desde ahí. MIDI 1 no suena ni manda notas. Octave ▲: los mismos pads son los pasos 17-32. Note ampliada: los 32 pads son los pasos 1-32 en orden.
14. Prueba con Drum 1-4 y con MIDI 2 como destino, MIDI 2 apuntando a la vez, MIDI 1 silenciada en el Mixer (no salta), un paso con 1 de cada 2 (salta una vuelta sí, otra no) y una pista destino a otro sync rate (salta en su paso siguiente).
15. Cambia la escala y la tónica: los pads y lo grabado no cambian de paso; las notas de las otras pistas sí siguen la escala, y Synth 1 conserva su teclado. Un pad en marcha salta en el paso siguiente; parado no hace nada. Con Shift + K1 de la vista cromática, los cents de un drum suenan igual.
16. Guarda, apaga y carga: sigue apuntando. Un proyecto nuevo no apunta, y MIDI 1 vuelve a sonar.

## Pruebas en emulación
`emu_mutate2.py`, `emu_nudge2.py` y `emu_jumpseq.py` (SC50 y B5.3), `emu_sc45_3.py`, `emu_sc48_8.py`; `verify_builds.py`.
