# SC56.9 = SC56.8 + el arreglo del cuelgue al entrar en el morph

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc56.9/circuittracks-4486-SC56.9.syx` | `34a5c26ca279f1581df60521ccd287ca50fcecc304f264ca4c37b8a78112c11e` | `SC56.9` |

**Lo nuevo** (arreglo; la caja negra de la Beta 5.53 del usuario, 2026-11-12: Synth 1, Preset, tres patches mantenidos = entrar en el morph, el aparato colgado y reiniciado a los ~3 s):
- **El cuelgue al entrar en el morph de Synth 1 / 2.** La caja negra lo dejó en «Main» (tarea del bucle principal y del servicio del DSP), parado en un bucle con PC `0x080180CC`–`0x08018140` y LR `0x0803BBD3` = `morphz.c_mznova`, el recorrido de las 310 filas del patch de Synth 1 / 2 desde su sitio `O_RR` (`MZ + 38`). `O_RR` no se escribía nunca (`c_mzst` pone la firma, `O_ACT` y `O_SNAP`), y la RAM del aparato no se borra al encender ni al instalar: con `O_RR` ≥ 310 y nada que escribir (las filas ya son las del patch), el final del recorrido (volver a `O_RR`) no llega. En emulación la RAM empieza a cero: por eso no se veía. Ahora (`morphz.use_rrfix()`) un `O_RR` fuera de rango vuelve a 0 antes del recorrido. Desde la Beta 5.34.

## Qué probar
1. Synth 1 → Preset, mantener tres patches 0,4 s (lo de la caja negra: pads 12, 10 y 11): entra en el morph, sin cuelgue ni reinicio. Igual con Synth 2 y con dos y cuatro patches.
2. Apagar y encender varias veces y repetir (la RAM de antes del arreglo puede traer cualquier valor).
3. Si algo se cuelga: no quitar la corriente; **Caja negra… → Guardar…** y mandar el `.json`.

## Verificación en emulación
- `emu_mzrr.py` (nuevo): `O_RR` = `0xFFFF`, la tarjeta devuelve el patch en uso, pads 12 / 10 / 11, 60 fotogramas: en esta build cada llamada al servicio vuelve, el morph entra y `O_RR` = 0; en la Beta 5.53 el servicio se queda en `0x080180CA` (el bucle del registro).
- `emu_morph.py --clear --sus --nocur --four --slow`, `emu_blackbox2.py`, `emu_blackbox.py`, `emu_knobhold.py`, `emu_ledstack.py`.
