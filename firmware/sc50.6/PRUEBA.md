# SC50.6 / Beta 5.9 / RC4.07 / RC4.07S

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc50.6/circuittracks-4486-SC50.6.syx` | `fe6ed78e7c8e8381993890ae8a30795be563da808c0c33c5e4d1454757b6c8d7` | `SC50.6` |
| `firmware/b5.9/circuittracks-4486-B5.9.syx` (**Beta 5.9**) | `adaa47b0c3f861981977af8ccf985a4e16e3af67c6f7cd14af9898ca82153ca7` | `B5.9` |
| `firmware/r407/circuittracks-4486-R407.syx` (**RC4.07**) | `735ca27541df642a0a3b6ebdb430b6c2d9312c7c28211e13ad52ee96673eda38` | `R407` |
| `firmware/r407s/circuittracks-4486-R407S.syx` (**RC4.07S**) | `a7918f4f5503ee1fc143861eb5b3c380b3bf924f55de8ed80b8a5139a09569d7` | `R407S` |

Lo demás que probar: [`firmware/sc50.5/PRUEBA.md`](../sc50.5/PRUEBA.md) y [`firmware/sc50.4/PRUEBA.md`](../sc50.4/PRUEBA.md). No hay nada nuevo que escriba en la tarjeta.

## Qué probar
1. **Sidechain, todas las versiones:** vista Sidechain, cambia entre los 8 presets de una pista: el brillo de K1-K4 cambia a la vista. Prueba también una página de drums.
2. **Drums, Beta 5.9:** Pattern Settings, pad 25, elige un paso con golpe, pad 27 y sube el factor con Octave a ×4 o más: el golpe suena dos veces en el paso, con la velocity moviéndose.
3. **Pad 28** en el mismo paso: tres golpes en tresillo.
4. **Pad 32:** con los pads 26-28 apagados, los golpes se retrasan 1 o 2 micropasos. A ×1 pasa uno de cada cuatro.
5. Con un roller y con Record, los golpes no se graban: se sortean en cada vuelta.
