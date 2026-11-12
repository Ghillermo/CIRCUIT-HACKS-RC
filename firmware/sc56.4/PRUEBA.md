# SC56.4 = SC56.3 + el morph de patches con hasta 4 patches

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc56.4/circuittracks-4486-SC56.4.syx` | `9366da783d77acfa1317e639bbcc2d65fe1d5c1f05b82c0c37c1aa27ba1607fb` | `SC56.4` |

**Lo nuevo** (el usuario, 2026-11-11: «Make it up to 4 patches»), `morphz.use_four()`: en la vista Preset de Synth 1 / 2 (o del sinte propio
de MIDI 1 / 2) se pueden mantener hasta **cuatro** patches 0,4 s; K1 los recorre en el orden de los pads (0 = el primero, al final = el cuarto).
Lo demás del morph, igual.

## Qué probar
1. Synth 1, vista Preset: mantener 4 patches 0,4 s: se abre la vista del morph. K1 de 0 al final: pasa por los cuatro, en el orden de los pads.
2. Con 2 y con 3 patches: igual que antes.
3. Preset en la vista del morph: los cuatro patches de la cadena en blanco; mantener otros 4 = cadena nueva.
4. Lo mismo en MIDI 1 / 2 con el sinte propio (huecos 9-24), también con patches de FM de 8 operadores.

## Verificación en emulación
- `emu_morph.py --clear --sus --nocur --four`: patches 4-7 mantenidos = n 5, las cuatro cachés leídas, K1 0 = el patch 4, al final = el 7,
  K1 64 = entre el 5 y el 6; el resto de la prueba como en SC56.3.
