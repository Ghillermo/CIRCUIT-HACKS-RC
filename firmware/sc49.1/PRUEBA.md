# SC49.1 / Beta 3.46 = SC49 + soltar la automatización hacia los valores del proyecto, knobs en amarillo, Clear + paso, Shift + Preset

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc49.1/circuittracks-4486-SC49.1.syx` | `66a3dd3733617896656ac9502a0200cf28296056e5f775ff23de13c1c9a76e48` | `SC49.1` |
| `firmware/b3.46/circuittracks-4486-B3.46.syx` (**Beta 3.46**) | `6df47a66aa849a6152d4e5f26b8fddb65905ae814c7951076933523294159656` | `B3.46` |

El usuario (2026-10-29, en RC4 y en la beta): «the shift step doesn't revert previous automation back to init»; «the cleared automation must
go to Project init, not current pad» (también MIDI 1 / 2); «the updated leds should be yellow»; «clear+pad in this view must keep the note and
erase automation only»; «new shortcut: shift+preset takes current voice to project init». La parte de «Project init» del paso marcado es un
arreglo y va también a RC4.01 / RC4.01S (`firmware/r401/`, `firmware/r401s/`).

## Qué cambia
- **Paso marcado (vista Velocity, Shift + paso) = los valores del proyecto** (`autorel.use_init`): lo que la automatización había movido
  vuelve a lo guardado en el proyecto (antes, a la posición del knob antes de la automatización: tras una foto con Record + paso los knobs
  se quedan en los valores de la foto y no cambiaba nada). Synth 1 / 2 = los macros del patch del sinte en el proyecto (como se cargó o se
  guardó por última vez; elegir otro patch lo cambia); MIDI 1 / 2 con el sinte propio = el guardado con el proyecto, o sus valores por defecto.
- **Knobs en amarillo** (`autorel.use_v3`): Shift + un paso amarillo enciende en amarillo los knobs que mueve (brillo = su valor) hasta soltar
  Shift.
- **Clear + paso en la vista Velocity** (con o sin Shift; Clear primero): borra la automatización de los knobs de ese paso (carriles 0-7);
  deja sus notas, su marca y los carriles de nivel / panorama / envíos.
- **Shift + Preset** (`projinit`): en las vistas de Synth 1 / 2, el patch entero del sinte vuelve al del proyecto (la rutina del original que
  aplica el patch de la sesión); en las de MIDI 1 / 2 con el sinte propio encendido, el sinte propio guardado con el proyecto (sin él, los
  valores por defecto). Con Shift, Preset amarillo donde funciona.

## Qué probar
1. Synth 1: girar un macro, Record mantenido + paso 1 (foto), Play; marcar el paso 5 (Velocity + Shift + paso 5, rojo): en el paso 5 el macro
   vuelve al valor del proyecto (el de antes de girarlo, si no se ha guardado el proyecto después).
2. Lo mismo en MIDI 1 / 2 con el sinte propio: en el paso marcado vuelve al sonido guardado con el proyecto.
3. Vista Velocity con Shift, parado: Shift + un paso amarillo = los knobs que tienen automatización en ese paso, en amarillo; soltar Shift =
   colores normales.
4. Clear mantenido + un paso amarillo (sin Shift, y luego Clear + Shift + paso): el paso deja de estar amarillo, sus notas siguen sonando.
5. Girar varios knobs de Synth 1, Shift + Preset: vuelve el sonido del proyecto. Lo mismo en MIDI 1 / 2 con el sinte propio. Con Shift, el
   botón Preset amarillo en las vistas de Synth 1 / 2 y MIDI 1 / 2 (sinte propio encendido); apagado en el Mixer, los drums, etc.
6. Guardar el proyecto, apagar y volver a cargar: los pasos marcados y la automatización siguen; Shift + Preset vuelve a lo guardado.

## Pruebas en emulación
`emu_sc49_1.py` (SC49.1 / B3.46 ALL PASS; frente a SC49: el paso marcado volvía al knob), `emu_sc48_8.py` y `emu_snapall.py` sobre SC49.1
(ALL PASS).
