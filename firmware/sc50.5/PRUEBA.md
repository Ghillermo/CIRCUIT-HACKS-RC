# SC50.5 / Beta 5.8 = SC50.4 / Beta 5.7 + solo en el Mixer

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc50.5/circuittracks-4486-SC50.5.syx` | `66dfe527a5cb77fec1f063f5e02575a7d7be3fb0ef7c9f3db4d8f1684301ea9a` | `SC50.5` |
| `firmware/b5.8/circuittracks-4486-B5.8.syx` (**Beta 5.8**) | `bc2c1e052fdebfe3b85eac2a9e47077afc036578e46d6e707cce6aa9430e43c2` | `B5.8` |

Lo demás que probar: [`firmware/sc50.4/PRUEBA.md`](../sc50.4/PRUEBA.md).

## Qué probar
1. Mixer: el pad 16 se ve blanco tenue y brillante mientras lo mantienes.
2. Mantén el pad 16 y pulsa los pads 1 y 3: suenan esas dos pistas y las demás se silencian al momento.
3. Suelta el pad 16: los mutes se quedan. Los pads 1-8 siguen silenciando y activando como siempre.
4. Mantén otra vez el pad 16 y pulsa otro pad: la elección empieza de nuevo.
5. Con Shift, la fila de repeticiones sigue igual; en Master FX, el pad 16 sigue siendo el suyo.
6. **Gater:** K2 (profundidad) en todo su recorrido suena como antes.
7. **Drums, random-mutate:** Pattern Settings, pad 25, enciende el pad 32 y suba el factor con Octave: los golpes se repiten 2 o 3 micropasos después, cada vez más a menudo; a ×4 o más, siempre.
