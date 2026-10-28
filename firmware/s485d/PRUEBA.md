# S485D (diagnóstico) = SC48.5 + los medidores de S484D

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/s485d/circuittracks-4486-S485D.syx` | `9038c6e91d23feec93065e4bb54f1719d3bc500d03d7ef8df7eeee5da69e8e61` | `S485D` |

SC48.5 / Beta 3.42 (limitador de voces, nivel de los acordes más alto, poly por defecto) con los dos LEDs de S484D, para comprobar el limitador:

| LED | Qué mide | Colores |
|---|---|---|
| **Save** | Cuánto tiempo le sobra al DSP | verde · amarillo · naranja · **rojo** = un bloque tardó más de lo que dura (aún suena limpio) · **blanco** (2 s) = el audio se quedó sin datos (el traqueteo) |
| **Duplicate** | El pico del sinte propio de MIDI 1 / 2 | apagado · verde < ½ · amarillo < 0,9 · naranja < 0,99 · **rojo** = recorte |

## Qué probar
1. FM poly, el patch y la forma de tocar que traqueteaban (release largo, muchas notas, acordes de 6). Save puede ponerse **rojo**, pero **no
   debería ponerse blanco** ni oírse el traqueteo.
2. Duplicate con los acordes (ahora suenan más fuertes): ¿llega a amarillo / naranja / rojo?
3. Cuéntame si Save se pone blanco alguna vez (y tocando qué), y hasta qué color llega Duplicate.

## Verificación en emulación
- `emu_vguard.py` y `emu_midipre.py` como SC48.5; `emu_dspload.py` (los medidores) sobre S485D. El programa del DSP es el de SC48.4.
