# S486D (diagnóstico) = SC48.6 + los medidores de S484D

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/s486d/circuittracks-4486-S486D.syx` | `38c594c6a754d76516f78d6e86200800afbbac8915395aaa086671b9b974d7cc` | `S486D` |

SC48.6 / Beta 3.43 (Synth 1 / 2 ya no callan con un acorde poly) con los dos LEDs de S484D:

| LED | Qué mide | Colores |
|---|---|---|
| **Save** | Cuánto tiempo le sobra al DSP | verde · amarillo · naranja · **rojo** = un bloque tardó más de lo que dura (aún suena limpio) · **blanco** (2 s) = el audio se quedó sin datos (el traqueteo) |
| **Duplicate** | El pico del sinte propio de MIDI 1 / 2 | apagado · verde < ½ · amarillo < 0,9 · naranja < 0,99 · **rojo** = recorte |

## Qué probar
1. Lo que callaba: Synth 1 / 2 secuenciados y un acorde poly de 5 notas en MIDI 1 / 2. **Synth 1 / 2 no deberían callar.**
2. ¿Hasta qué color llega Save mientras tanto? Ahora el aparato deja sonar sus voces aunque vaya justo: puede llegar a **rojo** (suena limpio);
   si se pone **blanco** o traquetea, dímelo con qué patches.

## Verificación en emulación
- `emu_vguard.py` como SC48.6; `emu_dspload.py` (los medidores) sobre S486D.
