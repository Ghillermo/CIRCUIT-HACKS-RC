# RC2.04 / RC2.04S (R204 / R204S) = RC2.03 + dos arreglos

`firmware/r204/circuittracks-4486-R204.syx` — SHA-256 `3d410abaee239c5dc46b23d32a26f8a98174a4142c66e46a1ad5dc9f3d2c928c`, marca `R204` (**RC2.04**).
`firmware/r204s/circuittracks-4486-R204S.syx` — SHA-256 `86e4459ea8a0603fb4d4bb147d493a5ceffdbb9df2c0af90bbe384ae1e53ff67`, marca `R204S` (**RC2.04S**).

**Arreglos (también en RC2.04 / RC2.04S):**
- **Notas largas al grabar** (`tools/recfix.py`; el usuario, 2026-10-20: «el arpegiador en compases de más de 16 pasos no recuerda qué notas estaban pulsadas después del 16 (hay que volver a poner las notas en el paso 17 para que siga arpegiando)», «extiende este fix a notas mantenidas durante la grabación aunque no fuera arpegio»). Causa: **el grabador de stock corta toda nota a 16 pasos** (`0x0803F85A`: 16 pasos o más → gate 96, el resto se pierde); un acorde mantenido 20 pasos quedaba de 16 y su arpegio se paraba ahí. Ahora la nota (o cada nota del acorde) queda ligada (bit 7 del gate) y la misma nota se escribe 16 pasos después, con su micropaso y su velocity y lo que queda (ligada otra vez si sigue), dentro del primer..último paso del patrón; en un patrón de 16 pasos o menos, como antes. Synth 1 / 2 y MIDI 1 / 2, con arpegiador o sin él.
- **Selector de samples del modo muestra** (`tools/smhold.py`; «en la pista sample flip del sampler propio, elegir sample+paso no programa el sample (elegir el paso primero y luego el sample sí lo hace)»): **mantener un sample y tocar pasos** = el flip de esos pasos (antes solo funcionaba paso mantenido + sample).

Los dos módulos van en la zona libre (`hole.py`: no escriben en la tarjeta). RC2.04S = RC2.04 + `rodisk.use_allpacks()`, como RC2.03S.

## Qué probar
1. **Notas largas:** Synth 1, patrón de 32 pasos, Record + Play: mantén una nota (o un acorde) desde el paso 1 hasta el 24 y suéltala. Al reproducir: suena seguida hasta el paso 24 (sin cortarse en el 17 ni volver a atacar). En la vista Note, el paso 17 lleva la misma nota.
2. Lo mismo con el arpegiador encendido (Shift + pad 25 en Pattern Settings): el acorde mantenido del paso 1 al 24 se arpegia hasta el 24 (antes: hasta el 16).
3. Un patrón de 16 pasos: igual que antes (la nota dura el patrón entero).
4. **Selector de samples** (MIDI 1 en modo muestra, Note dos veces): mantén un sample (filas 3-4) y toca los pasos 4 y 6: los dos en melocotón con ese sample. Paso mantenido + sample, y Clear + paso, siguen igual.
5. Lo demás, como RC2.03 (`firmware/r203/PRUEBA.md`).

## Verificación en emulación
- `emu_sc45_3.py` (el escritor de notas del grabador `0x0803F7BE` con la entrada de la nota puesta a mano: 10 pasos = gate 60; 20 pasos = 96 ligada + 27 en el paso 19; 40 pasos en 32 = 96 ligada, 96, nada más; patrón de 16 = 96; patrón de 24 = el resto en el paso 3; unidad de la misma nota reutilizada; paso lleno = sin ligadura; RC2.03: 96 y nada más) y el selector por el controlador. `emu_sc43_2.py`, `emu_sc44.py`, `emu_countin_bpm.py` sobre RC2.04.
