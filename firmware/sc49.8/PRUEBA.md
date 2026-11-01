# SC49.8 / Beta 5.1 = SC49.7 + el destello de cada nota + el guardado diferido como interruptor

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc49.8/circuittracks-4486-SC49.8.syx` | `5f646027ec9c7073d7a735c1f9f3db16d0e8729946eaa0e60a8c861388ae76f2` | `SC49.8` |
| `firmware/b5.1/circuittracks-4486-B5.1.syx` (**Beta 5.1**) | `ed09e5d159ac9aff6376a3d0eceb9a6020a3a5582da8146e24994bd3fb30837e` | `B5.1` |

## Qué cambia
- **Destello de cada nota** (`trigled.use_flash()`, función nueva: solo beta; el usuario, 2026-10-30: «Trigger flash: with Shift held, each track button
  flashes white for 100 ms on every note that track plays, from the sequence, pads, arpeggio or MIDI»; «use existing Remix code if it saves any work»:
  Circuit Remix no tiene ese código, solo el patrón de su metrónomo visual, una hora y una comparación): con Shift, en cualquier vista, el botón de la
  pista en blanco 100 ms desde cada nota. Todas las notas que suenan pasan por una llamada, la ranura 0 del enrutador de notas (`0x0805B840` →
  `0x0803222C`): claves 15..18 = Synth 1 / 2, MIDI 1 / 2, clave 19 = un drum (la nota = su número 1..4). Sustituye a la luz mientras dura el gate de la
  Beta 5.0 y a sus cabezas del transmisor. Una nota ligada es una sola nota: un destello.
- **Guardado diferido como interruptor** (`savedefer.use_toggle()`, RC y beta; el usuario, 2026-10-30: «Make the delayed save a toggle in advanced setup
  (stock save by default)»): **Advanced Setup, pad 22** (verde encendido, tenue apagado; bit 3 de las banderas de gmdrum, en los ajustes). Apagado, de
  fábrica, Save guarda al momento como el original. Encendido, como RC4.02. Apagarlo con un guardado pendiente lo escribe en ese momento (mientras
  espera, su petición sigue en el almacén del gestor y otro Save ni llega al oyente).
- Imagen `0X6FBA4` (**1116 B libres**), zona libre 46 B; DSP sin cambios. RAM `modmx.MXR + 0x21C0..0x21E3`.

## Qué probar
1. **Destello:** Shift mantenido, secuenciador en marcha con notas en Synth 1, MIDI 1 y Drum 1: su botón destella con cada nota, también con notas largas
   (no se queda encendido) y con la misma nota repetida. Tocar pads, un acorde con el arpegiador y un teclado MIDI: igual. Sin Shift, nada cambia.
2. **Guardar sonando, de fábrica:** Play, Save dos veces: guarda al momento, como el original.
3. **Advanced Setup, pad 22:** verde; Play, Save dos veces: Save parpadea en amarillo y guarda al parar, sin descompasar el reloj. Reiniciar: sigue
   verde. Con un guardado pendiente, pad 22 otra vez: se guarda en ese momento.

## Verificación en emulación
`emu_trigflash.py` (pads de todas las pistas, 99 / 100 ms con el pad pulsado, la misma nota en tres pasos, nota ligada, drums, arpegio del secuenciador y
de un acorde mantenido, MIDI por el despachador real), `emu_savedefer.py` (por defecto el original; pad 22; todo lo de SC49.7; pad 22 con un guardado
pendiente), `emu_sc48_8.py` (la vista Velocity con Shift, sin cambios).
