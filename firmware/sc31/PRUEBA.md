# SC31 — SC30 + el step-drummer conserva las notas

`circuittracks-4486-SC31.syx` — SHA-256 `a9a6dcaf71bc7745600a2b6d831a354bb29d90f19ce0dc22b69f8fd47e8e0b0a`
Imagen de 0x61428 bytes, CRC 0xccc45d1e, marca `SC31`. Reserva: **SC30**. Probado en emulación; **nada probado en el aparato**.
Sin RAM nueva, sin cambios en el DSP.

## Qué cambia
Hasta SC30, al abrir la vista del step-drummer o al editar, **todas las notas del patrón pasaban a ser la tónica** de la escala en la octava 2. Ahora (MIDI 1 / 2 y Synth 1 / 2):
- **Al abrir la vista y al editar:**
  - cada paso **conserva la altura de su primera nota**, con su duración, micropaso y velocity;
  - sigue habiendo **una sola nota por paso**: de un acorde queda la primera nota.
- **Una nota nueva** (Shift + paso, o subir la velocity de un par vacío) toma la nota de su par; si el par está vacío, la de la nota anterior más cercana (como ya hacía con la velocity); si no hay ninguna nota, la tónica.
- **La escucha** (tocar un paso) suena con esa misma nota, no con la tónica.
- Si quitas la nota de un paso mientras lo escuchas (Shift + el mismo pad, o la velocity a 0), la escucha termina antes, para que la nota no se quede colgada.

La fila de pitch (página Octave ▲) sigue siendo un desplazamiento sobre el destino elegido (tono, WAVE, FM…); se suma a la nota de cada paso.

## Verificación en emulación
`emu_sc31.py`, por las rutas reales (pads, knobs, botones), en MIDI 1 y Synth 1:
- **Al abrir la vista:** se conservan las notas 60 / 64 / 72 (también la de un paso con la nota en la segunda unidad, que pasa a la primera); un acorde se queda con su primera nota.
- **Notas nuevas:**
  - por la velocity de un par vacío, con la nota anterior más cercana;
  - con Shift + paso, con la nota de su par o la anterior más cercana;
  - sin ninguna nota en el patrón, con la tónica.
- **Escucha:**
  - note-on y note-off de la nota del paso (MIDI) y nota interna con su note-off (Synth 1);
  - un paso de un par vacío suena con la nota anterior más cercana;
  - Shift + el mismo pad mientras suena: un solo note-off y nada al soltar.

Además, `verify_builds.py` (ALL IDENTICAL) y las pruebas de SC23.3–SC30 repetidas sobre SC31, salvo `emu_sc26` / `emu_sc27`, que comprueban la tónica de SC26–SC30: todas pasan.

## Pruebas en el aparato
1. Envía SC31.
2. Con un patrón con notas distintas en MIDI 1 (o Synth 1), abre el step-drummer (pad 30). Las notas deben seguir sonando con su altura.
3. Añade pasos (Shift + paso, o la velocity en un par vacío): deben tomar la nota del par o de la nota anterior.
4. Toca un paso (escucha): debe sonar su nota.

## Volver atrás
Envía SC30.
