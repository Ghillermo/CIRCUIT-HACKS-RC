# SC47.6 / Beta 3.33 = SC47.5 / Beta 3.32 + uni retrig / uni portamento / uni glide + 6 voces FM compartidas

`firmware/sc47.6/circuittracks-4486-SC47.6.syx` — SHA-256 `a1c73bd0836e89b85d5219cd9087fb63653ebd55eb3e7028fa052fa8e431c82e`, marca `SC47.6`.
`firmware/b3.33/circuittracks-4486-B3.33.syx` — SHA-256 `02cbadefe6cd7c718db29383891ddf2b7fd3e1d83baae3578d730eefe831a69a`, marca `B3.33` (**Beta 3.33**, el mismo código).

El usuario (2026-10-26), tras la Beta 3.32 («It seems to work»): «Add uni retrig, uni portamento and uni glide, increase FM polyphony to six shared voices if possible».

## Qué probar
1. **Pad 32**: el desplegable tiene ahora siete modos en los pads 17-23: verde retrigger, amarillo legato, cian portamento, magenta poly, **azul uni retrig**, **azul claro uni portamento**, **violeta uni glide**. Shift + pad 29 pasa por los siete.
2. **Uni retrig** (pad 21): el unísono de la Beta 3.32 (cada nota vuelve a disparar).
3. **Uni portamento** (pad 22): el unísono se desliza siempre de nota a nota (K1 = el tiempo, con el desplegable abierto); tocando ligado, las voces solo cambian de altura, sin volver a disparar (en FM y VA-drum, sus envolventes siguen).
4. **Uni glide** (pad 23): se desliza solo de una nota pulsada a otra; una nota suelta empieza en su altura, sin glide, y vuelve a disparar.
5. **6 voces FM**: MIDI 1 en FM poly: acordes de hasta 6 notas; MIDI 1 y MIDI 2 en FM poly: 3 cada una. FM en uni retrig / portamento / glide: 6 voces (3 con las dos pistas en FM).
6. **CPU con 6 voces FM** (y drums, Master FX): escuchar si hay chasquidos o el tempo se resiente (6 voces FM ≈ un 24 % del DSP, estimado).
7. Lo de la Beta 3.32 (portamento, poly, el reloj con FM poly) igual.

## Verificación en emulación
- `emu_unimode.py`: siete modos en el desplegable; uni portamento (GK escrito; una nota sobre otra mueve las voces sin TRIG nuevo, sin salto); uni glide (una nota suelta envía el salto antes de las NOTE de las voces; una ligada solo las mueve; otra suelta, el salto siguiente); uni retrig (una nota sobre otra vuelve a arrancarlas); FM en unísono con 6 voces y sus bloques (`$3C00 … $3CC0`, `$3FB4`).
- `emu_glide2_dsp.py` frente a SC47.5: sin glide, el anillo igual; el desplazamiento de la pista (`OSC2 + 46`) según el modelo, `OSC1 + 34` a 0; el salto (sin glide en ese cambio); con los registros encendidos el glide sigue la nota del primero; dos voces FM en las ranuras 5 / 6 suenan como en la 1 / 2.
- `emu_poly3.py` (6 voces FM solas, 3 + 3 con las dos pistas, el robo dentro de las 3), `emu_vmode.py`, `emu_poly2.py`, `emu_poly2_dsp.py`, `emu_poly3_dsp.py`, `emu_fmeng2.py`: bien; `emu_fmspi.py` frente a SC47.4: igual que la Beta 3.32 (acorde 35, sostenido 1,3 por ms).
