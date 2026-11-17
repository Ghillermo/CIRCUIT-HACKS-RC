# Beta 5.60 = SC57.5 con la marca de la beta

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/b5.60/circuittracks-4486-B5.60.syx` | `5c66aa5ddd8f891df468b02c957fb8f20b98a1234f35d4cabc499613d990a04d` | `B5.60` |

**Lo nuevo** (sin probar en el aparato):
- **Volver al patrón guardado:** en cualquier vista de una pista (Preset, Note, Note ampliada, Velocity, Gate, Micro Step, Pattern Settings, probabilidad, la cromática de los drums), **Clear + Duplicate** pregunta (Duplicate parpadea en blanco ≈ 5 s) y **Clear + Duplicate otra vez** devuelve el patrón que se ve a como está guardado en la tarjeta (pasos, automatización, ajustes del patrón; en MIDI 1 / 2 también sus carriles extra). En las demás vistas, Clear + Duplicate sigue terminando el pattern mutate.
- Sitio: código inalcanzable fuera (`tools/fullwalk.py`): `vcf21.use_trimsd`, `patchain.use_trimcc`, `packio.use_trim2`, `build_sc17.use_trimsp2`, `persist19.use_trimkl`, `stepgate.use_trim`, `arp.use_trimzr`, `retrig.use_trimoff`, `sdpv.use_trimbs` (≈ 1,15 KB). Nada cambia en el uso.
- Todo lo de la Beta 5.59 (cadenas de grupos de patrones): ver `firmware/b5.59/PRUEBA.md`.

## Qué probar
1. Carga un proyecto guardado. Synth 1, vista Note: cambia notas de un paso y la longitud del patrón (Pattern Settings), graba algo de automatización.
2. **Mantén Clear y pulsa Duplicate**: no cambia nada y **Duplicate parpadea en blanco**. Sin soltar Clear, **Duplicate otra vez** (en menos de 5 s): el patrón vuelve a como estaba guardado (notas, longitud, automatización). Con el secuenciador sonando también: **escucha si el ritmo tropieza** en el momento de la confirmación (lee la tarjeta al momento).
3. Deja pasar más de 5 s entre las dos pulsaciones: la segunda vuelve a preguntar.
4. Lo mismo en un drum (vista Velocity o Pattern Settings) y en MIDI 1 con el sinte propio y **carriles extra** grabados (Record y un knob fuera de los secuenciables): vuelven también.
5. En las vistas Preset, Gate, Micro Step, probabilidad y la cromática de un drum: igual.
6. Proyecto nuevo (sin guardar): Clear + Duplicate dos veces = **Save en rojo** un momento, nada cambia.
7. En la vista Patterns (con listas del pattern mutate sonando) y en Sidechain: Clear + Duplicate sigue terminando el mutate, sin preguntar.
8. Guarda (Save dos veces) y vuelve a probar: devuelve lo recién guardado.
9. Repaso rápido de lo que tocaron los recortes: Duplicate en la vista Preset de drums y en la de packs, el song pointer de Master FX (pad 9 / saltos), los LEDs de los knobs de drums, el gate fijo (pad 31) y Micro Step, el arpegiador, el retrigger (Shift + pad 29) y el step-drummer de MIDI 1 / 2.

## Verificación en emulación
- `emu_patrev.py` (25 / 25): Synth 1 (pregunta, parpadeo, el patrón de la tarjeta, bytes 8..39 de los ajustes conservados, los almacenes de ajustes y del motor), pregunta caducada, Drum 1 con y sin `DQ`, MIDI 1 con su bloque de carriles extra (leído en la tarea de LEDs, caché descartada; cola de otro fichero = bloque vacío; suma del último guardado aceptada), proyecto nuevo y fichero corto = rechazado (Save rojo 1,5 s), Patterns y Sidechain sin pregunta, cerrojo del búfer equilibrado.
