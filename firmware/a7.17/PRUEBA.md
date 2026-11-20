# Alpha 7.17 (marca `A7.17`) — pendiente de probar, sin publicar

= Alpha 7.16 + `build_sc17.use_trimslc()` + `patchain.use_keep46()` + `gmview.use_rows()`. Imagen `0x6fff0` (16 B libres).

- **Vista de macros global, tres filas más** (el usuario, 2026-11-20: «Add level, reverb, delay»): con un knob elegido, **pads 9-16 = el nivel del Mixer** de cada pista, **pads 17-24 = su envío de reverb**, **pads 25-32 = su envío de delay** (brillante = enlazado, un toque cambia), como los pads 1-8 son sus knobs propios. El knob mueve a la vez todo lo enlazado en sus cuatro filas: el nivel como el knob de esa pista en el Mixer (en su página de niveles), los envíos como el knob de esa pista en la vista FX. El LED del knob, en el color de la primera pista enlazada de cualquier fila.
- Se guarda con el proyecto: las 32 máscaras en los bytes 8..39 de los ajustes del patrón 8 de MIDI 2 y la firma `0xD8` y la suma en sus bytes 4 / 5; un proyecto guardado con la 7.16 carga sus enlaces en la primera fila.
- **Clear + patrón en la vista Patterns ya no borra los bytes 4..6 de los ajustes del patrón** (las reglas antiguas, sin uso con las cadenas de grupos); el orden de reproducción (byte 7) sí.
- Sitio: fuera `c_slotcol` (el color de un hueco para los LEDs del secuenciador de efectos antiguo, sin llamadas desde la 7.08; `tools/fullwalk.py`), 106 B.

## Probar
1. Mixer mantenido + Patterns; gira K3; toca los pads 9, 18 y 28: brillantes.
2. Gira K3: suben a la vez el nivel de Synth 1 (Mixer), el envío de reverb de Synth 2 y el de delay de MIDI 2 (vista FX).
3. Con el Mixer en la página de panorama, lo mismo: el nivel cambia y el Mixer sigue en panorama.
4. Guardar, cargar otro proyecto, volver: los enlaces de las cuatro filas siguen. Un proyecto guardado con la 7.16: sus enlaces en los pads 1-8.

Prueba `emu_gmview.py` (25 comprobaciones).

**Instalada 2026-11-20 (contesta `A7.17`, caja negra vacía). Las filas probadas en el aparato con S717D (= esta + panel por USB, sin el secuenciador de pasos de Master FX).**
