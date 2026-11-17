# S579D (diagnóstico) = Beta 5.63 + los dos guardias de la ranura 7 + `tools/cwatch.py`

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/s579d/circuittracks-4486-S579D.syx` | `2c180ed6cc94fe3f893e4913fef8e10e54fd82239b9f27bbba4f2e736c774217` | `S579D` |

Para encontrar **quién cambia el byte** de la barra de velocity de Drum 4 (el cuelgue de la 5.63 al crear una cadena de grupos para una escena nueva):
una cabeza de la tarea de LEDs compara en cada fotograma (~90 por segundo) las dos vtables de los cuatro objetos de las barras de velocity de los
drums y, a la primera diferencia, **congela la caja negra** (estado `0x85`) con los 16 últimos gestos (pads, botones, knobs, la vista y el momento).
Sin el mute de la Beta 5.64 (no cabe); con los dos guardias, el aparato no se reinicia aunque el byte cambie.

## Qué hacer
1. Instalar S579D, encender y **repetir lo que hacías cuando la 5.63 se reiniciaba** (crear una cadena de grupos para una escena nueva: Mixer, Shift +
   pad de escena; Patterns, Shift + Octave ▲, Shift + pad, Shift + pad; salir; también pasar por las vistas Velocity de los drums con Shift, el
   step-drummer, las vistas de los drums con Record), parado y sonando, unos minutos.
2. Con la app (Caja negra…): si el estado es **manual (0x85)**, el anillo de gestos termina en el gesto que cambió el byte: guardar el JSON y pasarlo.
   Si no se congela nada, el byte no cambió en esa sesión (la lista de gestos no se pierde: seguir probando otras vistas).
3. Save en violeta al encender = la caja negra se congeló por otra cosa (como en la 5.51): léela igual.

## Verificación en emulación
`emu_cwatch.py` (ALL PASS: nada se dispara con los objetos intactos, el fotograma de LEDs es el de la 5.63, la corrupción del registro congela a la
siguiente pasada con el drum 4 anotado, una sola vez; con la caja ya congelada no hace nada), `emu_vtguard.py` como la Beta 5.64.
