# RC4.14 = RC4.13 + el arpegio armado al tempo del reloj externo; el STATE de la captura tras un reinicio

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/r414/circuittracks-4486-R414.syx` | `85f0d09844e481f04ae594e240e7d28f3788e2f1670f260b7054df8f91b59408` | `R414` |

Incluye RC4.12 / RC4.13 (sin publicar). Opciones de `tools/fixes563.rc()`:

- **`arp.use_tmext()` + `arp.tmext_stub`** (ARP-1): las notas del arpegio armadas entre dos micropasos (RC4.12) se temporizaban con el tempo del
  proyecto; esclavo de un reloj MIDI externo los ticks siguen al reloj, así que un reloj más rápido traía el swing de vuelta y uno más lento
  adelantaba las notas. Ahora `c_artm` lee el tempo por un stub en el hole (`c_artmr`, 30 B): esclavo = el BPM medido (el de la cuenta atrás,
  `cibpm`), si no el del proyecto con una lectura pura (`PARAM_GET`).
- **`capkeep.use_resend()`** (CK-1): tras un reinicio que conserva la RAM (instalar otra versión, un fallo), una captura fijada seguía marcada como
  enviada al DSP mientras el DSP volvía a cero: grababa en silencio. Ahora el tick siguiente reenvía su estado (+ 4 B).

Imagen `0x6FFF4` (12 B libres al final; hole 218 B).

## Qué probar
1. **Arpegiador esclavo de un reloj MIDI externo** (Setup: Clock Rx), el patrón a 1/8 y el arpegio a 1/32 (Shift + pads 17-24 en Pattern Settings):
   notas regulares a 150 y a 96 BPM del reloj; sin reloj externo, como en RC4.13.
2. **Captura fijada tras un reinicio:** con una captura fijada sonando (Master FX, pad 32 corto), instalar otra versión y volver a esta (una
   reconstrucción con la misma marca no se instala): la captura vuelve a grabar de verdad.
3. Lo de RC4.12 / RC4.13: el arpegio a 1/32 sobre un patrón a 1/8 sin swing; la captura sigue al cargar un proyecto; Play no cuelga.

## Verificación en emulación
`emu_arptime.py --ext` (esclavo a 150 / 96 BPM, no esclavo con un reloj medido a 150), `emu_arptime.py` contra RC4.11, `emu_capkeep.py` contra RC4.11
(el caso del reinicio); `verify_builds.py`: las versiones anteriores idénticas. Resultados en `firmware/b5.63/RESULTADOS.md`.
