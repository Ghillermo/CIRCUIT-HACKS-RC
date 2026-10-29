# SC49.7 / Beta 5.0 = SC49.6 + la vista de automatización de los drums completa + los pads cromáticos graban golpe y tono + el guardado espera al stop + sitio en la flash

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc49.7/circuittracks-4486-SC49.7.syx` | `80288ecdb59117e56cf0955257db2fc20dd5b35d45ee048e7cdbc7d068e68f23` | `SC49.7` |
| `firmware/b5.0/circuittracks-4486-B5.0.syx` (**Beta 5.0**) | `2204945f36ca5fb62423bace8caacfc0b5aa6038b5f619814111a257ee9887da` | `B5.0` |

El usuario (2026-10-29): «make automation view (velocity shift) available on drums» (las cuatro partes; «Hold = preview, tap = ramp»);
«extend clock fix to project save» («Both»); «i m having trouble recording chromatic sample notes from the pads», «chromatic drums still dont
record automation right. either they stay on the same note or have their notes switched» («Hit + pitch», «Knob pitch»); «fix the quantize too»;
«betas that expand RC4 get 5.xx version». La Beta 5.0 incluye las 3.44-3.49 (no se publicaron). Los arreglos van también a RC4.02 / RC4.02S
(`firmware/r402/`, `firmware/r402s/`).

## Qué cambia
- **Vista de automatización de los drums** (`tools/dautov.py`, función nueva: solo beta): la vista Velocity de un drum con Shift (o fijada con
  Velocity otra vez): pasos con algo en los carriles 0-3 (pitch, decay, distorsión, EQ) o en el carril extra en **amarillo**, los marcados en
  **rojo**; **Shift + paso amarillo** = sus valores en los knobs y el sonido (los carriles de stock por la ruta de la reproducción: el
  objetivo `[reproductor + 0x2C]` ranura 0 con el id `[[reproductor + 0x3C] + k]`; el S cromático; el parámetro del carril extra; un estado,
  los 14 valores) y los knobs que mueve en amarillo, hasta soltar Shift (todo vuelve exacto); **Shift + paso sin automatización** = marca
  (código 126 del carril extra; `c_xlcode` de lanex se queda en 125): al sonar, los 4 knobs de stock y el parámetro del carril extra vuelven
  a los valores del registro de la sesión; **Clear + paso** = su automatización borrada, el golpe queda. Bloqueos de estado: mantener = escuchar,
  tocar otro = la rampa de slock (la escucha se quita antes).
- **Pads cromáticos de los drums** (`tools/chromfix.py`, arreglo): con Record + Play cada pulsación graba **un golpe** en el paso que suena (el
  micropaso del tick, la velocity del pad, probabilidad 7 en un paso vacío; la copia de edición del drum sincronizada con `drumarp.c_dasync`)
  **y su tono** en ese paso; antes solo el tono (la vista cromática toca el drum por la escucha de la vista Preset, que el original no graba).
  Cuantizar (Shift + Play) mueve el tono con su golpe.
- **Guardar mientras suena** (`tools/savedefer.py` + `packio.use_svskip()`, arreglo): el guardado del proyecto con el transporte en marcha queda
  pendiente (Save parpadea en amarillo) y se hace al parar; cualquier otra petición al gestor de sesiones lo hace antes (salvo otro guardado
  del mismo hueco); espera si el gestor está ocupado; se descarta si cambia el pack. Nuestro gancho del guardado lee el DSP una vez (no 65)
  cuando no hay capturas pendientes.
- **Sitio en la flash:** `tools/gentab.py` (seis tablas del núcleo 0, TINC / TEXP / TLFO / TDEC / TATK / TF, se calculan al arrancar el DSP:
  342 palabras menos; errores ≤ 1 LSB / 0,07 % / 18 LSB / 0,003 % / 0,009 %), `build_sc17.use_novtab()` (las cuatro tablas del Vinyl, 2 KB,
  que nada lee desde SC39.7).
- Imagen `0x6FB88` (**1 144 B libres**), zona libre 46 B; núcleo 0 hasta `P:$3D74`, tablas generadas en `P:$3E0D..$3FFF` (152 palabras libres).

## Qué probar
1. **Pads cromáticos:** Drum 1, vista cromática (Preset dos veces), Record + Play, tocar una melodía en los pads: cada nota queda como golpe en
   su paso y suena con su tono; los pasos sin nota grabada suenan con el pitch de K1. Shift + Play: los golpes se cuantizan con su tono.
2. **Guardar sonando:** Play, Save dos veces: el reloj no se descompasa; Save parpadea amarillo; Stop: se guarda (Save deja de parpadear).
   Apagar y cargar: el proyecto lleva lo guardado.
3. **Vista de automatización de un drum:** grabar giros de decay / distorsión; vista Velocity con Shift: esos pasos amarillos; Shift + uno: el
   knob se mueve y suena, su LED amarillo; soltar Shift: vuelve. Shift + un paso vacío: rojo; al sonar, decay / distorsión vuelven a lo
   guardado en el proyecto. Velocity dos veces (fijada) + Clear + un paso amarillo: deja de estar amarillo, el golpe sigue.
4. **Bloqueos de estado** (Record + 1-16/17-32): mantener un paso con estado = lo escuchas; tocar otro = rampa.
5. **Master FX** (las tablas del Vinyl fuera): Gater, Auto-Filter, Digitise (K4: envolvente), Phaser, Glitch y el gesto mecánico como antes.
6. **Drums y sinte propio** (tablas del DSP calculadas): el tono de los osciladores de MIDI 1 / 2, el LFO de drums y del sinte propio, los
   decays y ataques de los drums, los filtros y el ring mod suenan igual que en la Beta 3.49.

## Verificación en emulación
`emu_gentab_dsp.py` (frente a SC49.6: las seis tablas modeladas palabra a palabra y dentro de su error), `emu_chromfix.py` (golpe + tono en el
paso de la pulsación con el secuenciador y el grabador reales; cuantizar), `emu_savedefer.py` (parado / sonando / al parar / ocupado / pack
cambiado / otro hueco / svskip), `emu_dautov.py` (LEDs, escucha y vuelta exacta, marca, Clear, paso marcado reproducido, bloqueos de estado),
`emu_sc39_9.py` (Master FX sin las tablas del Vinyl) y las de las zonas tocadas (`emu_slock`, `emu_reccue`, `emu_lanex`, `emu_snapall`,
`emu_autorel`, `emu_sc48_8`, `emu_sc49_1`, `emu_sc43_7`, `emu_sc42_9`).
