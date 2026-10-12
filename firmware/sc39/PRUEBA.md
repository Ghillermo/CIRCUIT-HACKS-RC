# SC39 — random-mutate por paso + patches de glide en color fijo

`circuittracks-4486-SC39.syx` — SHA-256 `acdc68af7dbe3cd152354682e7141a644c328955a8d202c48ab6329f7daec7c9`
Imagen de 0x66a4c bytes, CRC 0x67a3e078, marca `SC39`.

Es SC38.9 con:
1. **Random-mutate** (Synth 1 / 2 y MIDI 1 / 2). En la vista de probabilidad del original (**Shift + Pattern Settings**), con un paso mantenido, la **fila 4** (pads 25-32, melocotón) da al paso una probabilidad de que sus notas cambien al sonar:

| Pad | Octava | Escala |
|---|---|---|
| 25 | — (apagado) | — |
| 26 | 6 % | — |
| 27 | — | 6 % |
| 28 | 6 % | 6 % |
| 29 | — | 12 % |
| 30 | 12 % | — |
| 31 | — | 25 % |
| 32 | 25 % | 50 % |

   - **Escala** = otra nota de la escala del proyecto en la misma octava; **octava** = una octava arriba o abajo, al azar. Cada nota de un acorde se sortea por separado.
   - **Sin Record** la nota cambiada suena esa vez y el paso no cambia. **Con Record** la nota cambiada se escribe en el paso.
   - La fila 3 sigue siendo la probabilidad del original. El valor va en el paso (se guarda con el proyecto).
2. **Patches de glide en color fijo** (vista Preset de Synth 1 / 2): lavanda (`0x49`), el elegido violeta pálido (`0x5C`). En SC38.8 / SC38.9 eran `0x4C`, que es un color **animado** de la placa (pulsaba).

## Qué probar
1. Synth 1, un patrón con notas. **Shift + Pattern Settings**: fila 3 como siempre; fila 4 en melocotón (pad 25 encendido = apagado).
2. Mantén un paso con nota y pulsa el **pad 32**: la fila 4 se llena. Play: la nota de ese paso cambia más o menos una de cada dos vueltas (otra nota de la escala) y una de cada cuatro salta de octava. Al parar, el paso sigue con su nota original.
3. Pads 26 (solo octava) y 27 (solo escala), unas vueltas: cambios raros (1 de cada 16), del tipo que toca.
4. **Record + Play** con el pad 32: la secuencia va cambiando y los cambios se quedan (mira el paso en la vista Note). Quita Record: deja de escribirse.
5. Pad 25: el paso vuelve a sonar siempre igual.
6. Un paso sin notas: la fila 4 apagada, pulsarla no hace nada.
7. Un acorde: cada nota cambia por su cuenta. Notas largas y ligadas (tie): **sin notas colgadas**; las ligadas no cambian.
8. MIDI 1 / 2: lo mismo (la nota cambiada sale por MIDI con su note-off).
9. Guardar, apagar, encender: los niveles siguen. Copiar el patrón / el paso: el nivel va con el paso.
10. Drums: su vista de probabilidad no cambia.
11. Vista Preset de Synth 1 con patches de glide: lavanda **fijo** (sin pulsar); mono azul oscuro y poly como antes.
12. Todo lo de `firmware/sc38.9/PRUEBA.md`.

## Verificación en emulación
- `emu_sc39.py`: la vista por el controlador (Shift + botón 12, paso mantenido, pads y tarea de LEDs); el reproductor real `0x08040E5A` con el generador de stock sustituido por valores elegidos: 4 655 reproducciones = el modelo (5 escalas / tónicas, 7 notas, niveles 1-7); nivel 0, unidad ligada, continuación de una ligadura y nota que ya suena: la nota del paso; con Record la nota se escribe; con el generador de stock las tasas salen cerca de 6 / 12 / 25 / 50 %; `emu_sc38_8` con los colores nuevos.
- `emu_sc38_9.py` sobre SC39 (el teclado partido sigue igual).
- **No comprobado en emulación:** el reproductor en marcha en el aparato (se llama a la función real con el estado del volcado), las notas colgadas con ligaduras entre pasos y la escritura con Record durante una grabación real.
