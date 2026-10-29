# RC4.02 / RC4.02S = RC4.01 + los arreglos del 2026-10-29

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/r402/circuittracks-4486-R402.syx` (**RC4.02**) | `b1e4283808240defcc75a6084d471f74877787eb411a8d5e4ecb7feb8009d864` | `R402` |
| `firmware/r402s/circuittracks-4486-R402S.syx` (**RC4.02S**) | `6af7fbf99a12366a19d3434388122134e305e64b30b7b4ccc3f97b06b8c57092` | `R402S` |

RC4.01 no se publicó: RC4.02 la incluye (con ella el arreglo de la marca de soltar la automatización y los de SC48.7).

## Qué cambia (arreglos; los mismos que en la Beta 5.0)
- **Pads cromáticos de los drums** (`chromfix`): con Record + Play cada pulsación graba un golpe con su tono en el paso que suena (micropaso del
  tick, velocity del pad, probabilidad 7 en un paso vacío); antes solo el tono, en el carril de pitch (0x80 | S). Cuantizar mueve el tono con
  su golpe. (Sin el carril extra de la beta: el tono va al carril de pitch, como en RC4.)
- **Guardar mientras suena** (`savedefer` + `packio.use_svskip()`): el guardado espera al stop (Save parpadea amarillo); el gancho del guardado
  lee el DSP una vez cuando no hay capturas pendientes. En RC4.02S el guardado de stock sigue igual (el mod no escribe nada propio).
- **Digitise K4** (`masterfx_dsp.use_novinyl()`): lo que quedaba del Vinyl en el DSP borraba la hora de inicio de su envolvente: funciona.
- RC4.02: imagen `0x6FE7C` (388 B libres), zona libre 358 B. RC4.02S: `0x6FE6C`.

## Qué probar
1. Drum 1, vista cromática, Record + Play, una melodía en los pads: cada nota con su golpe y su tono; Shift + Play: cuantizada con su tono.
2. Play, Save dos veces: el reloj no se descompasa; Stop: se guarda.
3. Master FX, Digitise con K4 a la derecha / izquierda: la cantidad decae / crece.
4. Lo de RC4.01 (Shift + paso en la vista Velocity = soltar la automatización a los valores del proyecto; issue #15).

## Verificación en emulación
`emu_chromfix.py` (sin lanex: el tono en el carril de pitch), `emu_savedefer.py`, `emu_drop494_dsp.py` (la parte de Digitise), `emu_rodisk.py`
sobre RC4.02S, `emu_sc49_1.py` / `emu_edlock.py` (lo de RC4.01).
