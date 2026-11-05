# Beta 5.19 = SC51.6 con la marca de la beta (incluye las 5.17 y 5.18) + step flip desde el patch flip

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/b5.19/circuittracks-4486-B5.19.syx` | `781605a7b6d6ba84df56ebe515e4c79dd46072cf48aa1759bde436cbf45f0749` | `B5.19` |

**Qué cambia** (el usuario, 2026-11-04): el destino del secuenciador de saltos («step flip») se elige desde el **patch flip** (pad 26 de la vista Preset de MIDI 1 / 2), no desde la fila de motores (pad 27). Incluye lo de SC51.4 / SC51.5 (voces FM en el núcleo 1, el núcleo 1 con 8 K de programa).

## Qué probar
1. Vista Preset de MIDI 1, **pad 26**: patch flip como siempre (las notas salen como Program Change); los **pads 17-24** = las ocho pistas en sus colores (MIDI 1 sin luz), los **pads 9-16** apagados.
2. Un toque a una pista (p. ej. pad 21 = Drum 1): **step flip**: brilla, el **pad 26 parpadea** en su color, el patch flip deja de mandar Program Change; las notas de MIDI 1 hacen saltar a Drum 1 (como antes).
3. Otra pista la cambia; **la misma otra vez** = vuelve el patch flip; con step flip, **pad 26** = todo apagado.
4. **Excluyentes:** nunca los dos a la vez; un proyecto guardado con un destino cargado con el patch flip encendido = gana el step flip (el patch flip se apaga).
5. Pad 27 (fila de motores): sus pads 9-16 ya no apuntan (apagados).
6. Lo mismo en MIDI 2.

## Verificación en emulación
- `emu_jumpflip.py`: todo lo anterior por el controlador y la tarea de LEDs.
