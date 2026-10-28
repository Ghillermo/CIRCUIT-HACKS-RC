# SC48.4 / Beta 3.41 = SC48.3 / Beta 3.40 + latch y acordes

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc48.4/circuittracks-4486-SC48.4.syx` | `af116ac8c01e794685df5c08dcaf965387c1ca9df6fc912bd490d862f2a7c081` | `SC48.4` |
| `firmware/b3.41/circuittracks-4486-B3.41.syx` (**Beta 3.41**) | `9ae7e7b5f07a85149bf4da502f5ba48c56cba026214455955d1e1c399a2d4135` | `B3.41` |
| `firmware/b3.41s/circuittracks-4486-B3.41S.syx` (**Beta 3.41S**: la beta sin escrituras propias en la SD) | `0b5e400ca14b8862f8e3fb9c9ed0258e8a5da1f004a9d6433c234e7103970142` | `B3.41S` |

El usuario (2026-10-28): «make hold notes bright cyan on shift layout» (las notas fijadas, solo con Shift); «make chords (and arpeggiator) in chord
mode change immediately instead of waiting for next press»; «make latch work on chord mode (it latches all the notes in the selected chord)»;
«if shift +step in note view is available, current latched notes are added into selected step»; «in arp mode settings … make pads 1-4 a
different color (suggestion: sand)».

## Qué probar
1. **Notas fijadas en cian:** Synth 1, vista Note: Shift + dos teclas (latch). Con Shift mantenido, esas dos teclas cian brillante y las demás
   con sus colores de siempre; sin Shift, como antes (la nota que suena en blanco).
2. **Shift + paso:** con las dos notas fijadas, **Shift + el paso 3**: el paso se enciende y al darle Play suenan esas dos notas en el paso 3
   (un paso de largo). Shift + un paso que ya tiene una de ellas: solo se añade la otra. Clear + Synth 1 suelta las notas; Shift + paso
   sin notas fijadas = lo de siempre. Con Shift mantenido y notas fijadas, los 16 pads de paso en amarillo; sin notas fijadas, como siempre.
3. **Acordes al momento:** Note dos veces (Note ampliada), Shift + pad 8 (pantalla de acordes). Mantén una fundamental (filas 3-4) y toca el
   pad 2 (menor), el pad 10 (1.ª inversión), el pad 14 (bajo): el acorde cambia mientras lo mantienes, sin cortes en las notas comunes. Con el
   arpegiador del patrón encendido (Pattern Settings, Shift + pad 25), el arpegio sigue con las notas nuevas.
4. **Latch de acordes:** **Shift + una fundamental**: el acorde sigue al soltar; con Shift su pad cian. Cambia el tipo: el acorde fijado cambia.
   La misma fundamental otra vez: se para (sin volver a sonar). Fija dos acordes; **Clear + Synth 1**: los dos se paran. Con un acorde fijado,
   vuelve a la vista Note y **Shift + un paso**: el acorde entero en ese paso.
5. **Arena:** Pattern Settings, Shift + pad 25 (arpegiador), Shift: los pads 1-4 en arena (el elegido brillante), los 5-8 en azul cielo.

## Verificación en emulación
- `emu_chlive.py`: mantenido, mayor → menor = la tercera fuera y la menor dentro; 1.ª inversión = la fundamental fuera, la octava dentro; la
  suelta = las tres fuera; Shift + fundamental = fijado (la suelta no hace nada), cian con Shift; el cambio de tipo sigue al fijado; la misma
  fundamental = sus notas fuera y nada más; Clear + Synth 1 = fuera.
- `emu_latchstep.py`: sin notas fijadas el paso no cambia; las teclas fijadas cian con Shift y las demás iguales; Shift + paso = 62 y 67 en el
  paso (6 ticks, velocity 100), el LED del paso cambia; un paso con 64 / 60 / 67 recibe solo 62.
- `emu_arpmods.py`: la tabla de colores de la imagen (arena / cielo / ámbar / rosa) y los LEDs con Shift.
- Las pruebas de SC48.3 sobre SC48.4 / Beta 3.41: bien.
