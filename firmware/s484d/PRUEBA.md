# S484D (diagnóstico) = SC48.4 + medidores del DSP y del sinte propio

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/s484d/circuittracks-4486-S484D.syx` | `94f82c71336d5d5068ea2fba296351cb4334a7b5276713375a7da024856abc13` | `S484D` |

El usuario (2026-10-28): «Some FM patches still produce crackling when you hold more than 5 notes»; «the main issue comes when using notes with
long releases, since it's easy to pile voices until the rattling sounds appear quick». Con releases largos las 6 voces FM suenan a la vez todo el
tiempo: puede faltar tiempo de DSP (CPU) o recortar la suma de las voces. Esta build enseña las dos cosas en el panel, en cualquier vista. Es
SC48.4 / Beta 3.41 con dos LEDs de medida (Save y Duplicate dejan de hacer de Save y Duplicate visualmente; los botones funcionan igual).

## Los dos LEDs (se actualizan cada medio segundo)
| LED | Qué mide | Colores |
|---|---|---|
| **Save** | Cuánto tiempo le sobra al DSP | **verde** = sobra mucho · **amarillo** · **naranja** = va justo · **rojo** = un bloque de audio tardó más de lo que dura (el DSP se retrasa) · **blanco** (2 s) = el audio se quedó sin datos y se repitió (eso suena como un zumbido / traqueteo) |
| **Duplicate** | El pico de la salida del sinte propio de MIDI 1 / 2 | apagado = bajo · **verde** < ½ · **amarillo** < 0,9 · **naranja** < 0,99 · **rojo** = recorte (la suma de las voces satura) |

## Qué probar
1. Instalar S484D. Sin tocar nada: Save en verde (si no, apunta el color).
2. MIDI 1 con el sinte propio en **FM poly**, un patch de los que traquetean, **release largo**. Toca notas sueltas una tras otra (se van
   acumulando voces) hasta que se oiga el traqueteo. Mira los dos LEDs **en el momento del traqueteo**.
3. Repite con la velocity baja (o el nivel del patch más bajo).
4. Cuéntame: el color de Save y el de Duplicate cuando traquetea, y si con la velocity baja traquetea igual.

**Cómo lo leo:** Save rojo / blanco al traquetear = falta tiempo de DSP (la solución: limitar voces cuando el DSP va justo); Duplicate rojo con
Save verde / amarillo = recorte (la solución: bajar la ganancia de las voces o un limitador); los dos verdes al traquetear = otra cosa
(apúntalo y lo miramos).

## Verificación en emulación
- `emu_dspload.py`: las lecturas (Y:$FFE, Y:$FFD, una palabra del último bloque); Save verde / amarillo / naranja / rojo con márgenes 250 / 215 /
  200 / 150, blanco 2 s tras un anillo vacío; Duplicate apagado / verde / amarillo / naranja / rojo con picos 0,1 / 0,4 / 0,7 / 0,95 / 1,0 (y −1,0).
- El programa del DSP es el de SC48.4 (sin cambios).
