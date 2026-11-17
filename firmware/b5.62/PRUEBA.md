# Beta 5.62 = Beta 5.61 + arreglo: Play ya no cuelga el aparato con el arpegiador

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/b5.62/circuittracks-4486-B5.62.syx` | `a52390e7fa16ecd3d65137e59f347e126c290819a12ed1a108a66bb4f6d94c35` | `B5.62` |

**Sustituye a la Beta 5.61, que se cuelga al pulsar Play con el arpegiador.** = SC57.7 con la marca de la beta.

**El fallo** (el usuario, 2026-11-14, en la Beta 5.61: «if I press play it plays for a fraction of a second and hangs», «its the arpeggiator fix»;
sin reinicio, USB sin respuesta): `arp.use_timed()` (RC4.12 / Beta 5.61) ponía `c_armain` en lugar de la llamada del bucle principal al servicio del
DSP (`0x0801D5D8`). Pero el bucle principal **toma el cerrojo del servicio del DSP justo antes** (`bl 0x08021064` en `0x0801D5D4`) y lo suelta
después (`0x0801D5DC..0x0801D5FC`). Cuando una nota armada del arpegio tocaba su hora, `c_armain` la tocaba con el cerrojo cogido y la ruta del
sonido de la nota (la interfaz de notas `0x0801D38E` → `0x0803BD58` / `0x0803BD94`) lo volvía a tomar: espera para siempre. La prueba de RC4.12
(`emu_arptime`) saltaba el note-on y la interfaz, y no lo vio.

**El arreglo** (`arp.use_tmfix()`): la llamada al servicio vuelve a ser la de stock y `c_armain` corre **justo después de soltar el cerrojo**, en
lugar de los 4 bytes de `0x0801D5FE` (`mov r0, r7; ldr r0, [r0]`, que hace al final). Misma tarea, mismo ritmo (cada pasada del bucle principal).
Todo lo demás de la versión anterior, igual.

## Qué probar
1. **Lo que se colgaba:** el proyecto con el arpegiador, Play: debe seguir sonando (antes: una fracción de segundo y cuelgue).
2. El arreglo del arpegio de RC4.12: Synth 1 a 1/8 (Pattern Settings), el arpegiador a 1/32 (Shift + pads 17-24), un acorde: notas regulares, sin
   swing; 1/16 sobre 1/16 como antes; parar a mitad: ninguna nota colgada.
3. La captura de RC4.12: en Master FX, pad 32 corto (fijada), cargar otro proyecto: sigue grabando; armada (Shift + pad 32): sigue armada.

## Verificación en emulación
- `emu_armain_lock.py` (nuevo): el tramo real del bucle principal (`0x0801D5CA..0x0801D602`: el cerrojo, el servicio, el cerrojo soltado) cada ms,
  con el note-on y la interfaz de notas de verdad: las notas armadas suenan desde el bucle principal y nada toma el cerrojo mientras el bucle lo
  tiene; contra la versión anterior: 7 tomas con el cerrojo cogido (`0x0803BD58` / `0x0803BD94`) = el cuelgue.
- `emu_arptime.py`: el arpegio a tiempo, como en la versión anterior.
