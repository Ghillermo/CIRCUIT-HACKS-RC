# SC57.2 = SC57.1 + step flip al azar entre las notas de un paso

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc57.2/circuittracks-4486-SC57.2.syx` | `4cfe9b4a119708faa33625adb4b499c510e3a7d9b89e53e10b53b86c53872c5f` | `SC57.2` |

**Lo nuevo** (el usuario, 2026-11-13: «Can we get a randomized choice between both steps?»):
- **Arreglo, step flip parado con un drum de destino:** cada pad toca el sample flip de su paso (antes todos el sample elegido del drum).
- **Step flip con varias notas en un paso:** el salto va a uno de sus pasos al azar, todos con la misma probabilidad; en cada vuelta se vuelve a elegir. Antes ganaba siempre la última nota que mandaba el secuenciador.

## Qué probar
1. MIDI 1 → Preset → pad 26 → fila 3 pad 18 (step flip) → fila 2: Synth 1.
2. En la vista Note de MIDI 1, en un paso, dos pads de dos pasos distintos (p. ej. los de los pasos 10 y 14). Play: Synth 1 salta a uno u otro, cambiando entre vueltas.
3. Un paso con una sola nota: siempre a ese paso, como antes.
4. Destino Drum 1, transporte parado: pon sample flips distintos en varios pasos de Drum 1; en MIDI 1, cada pad suena con el sample de su paso; un paso sin flip, con el sample elegido.

## Verificación en emulación
- `emu_jumpseq.py`: con un drum de destino y un flip en el paso, el sample del flip antes del golpe y el elegido al soltar; sin flip, como antes.
- `emu_jumprnd.py` (nuevo): MIDI 1 → Synth 1, paso 5 con notas de los pasos 10 y 14, 20 vueltas: los dos destinos, cerca de la mitad cada uno; una nota = siempre su paso; la Beta 5.56 = siempre el mismo.
