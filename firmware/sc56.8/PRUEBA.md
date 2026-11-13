# SC56.8 = SC56.7 + la luz del knob retenido + la caja negra v2

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc56.8/circuittracks-4486-SC56.8.syx` | `927969850bd21b51b8d304cd0adfb314e0712ef2eca4e5c2a7f5ac954adb6c62` | `SC56.8` |

**Lo nuevo** (el usuario, 2026-11-12):
- **Retener knob: la luz se queda.** Mientras un knob retiene su asignación anterior, su LED sigue con el color y el brillo de antes del cambio.
- **Caja negra v2:** además del panel colgado sonando, apunta un **fallo del procesador**, un **bloqueo** que acaba en reinicio (el bucle principal parado más de 1,5 s) y un **reinicio por el vigilante**, con el motivo del último reinicio. Lo apuntado sobrevive al reinicio y a seguir usando el aparato; se pierde si se queda sin corriente.

## Qué probar
1. Retener knob encendido (Preset en Setup): girar un knob en el Mixer y pasar a FX sin parar: el LED de ese knob se queda con el color del Mixer hasta 1 s quieto; los demás, los de FX.
2. **Antes de reproducir el cuelgue: Caja negra… → Vaciar.** Repetir lo del morph (Synth 1, Preset, mantener los patches 13, 11 y 12).
3. Si se reinicia: no quitar la corriente; conectar por USB, **Caja negra… → Guardar…** y mandar el `.json`. Debe decir «Fallo del procesador», «El aparato se bloqueó» o «El vigilante reinició el aparato», con el PC y la tarea.
4. Uso normal un rato, cargar packs y proyectos, sonando y parado: la caja negra no debe quedar congelada sola (un bloqueo que se recupera se descarta).
5. MIDI 1 / 2 → Preset nada más instalar: no se reinicia (arreglo de la 5.52).

## Verificación en emulación
- `emu_blackbox2.py`: vectores, fallo (marco, CFSR / HFSR / BFAR, TCB, pilas), segundo fallo, reinicio (RESET, RCC_CSR + RMVF), bloqueo 1 499 / 1 500 ms, muestras cada 50 ms, bloqueo que se recupera descartado, bloqueo + reinicio, IWDG sin nada congelado = WARM, el stub de SysTick hasta `HAL_IncTick`.
- `emu_blackbox.py`, `emu_knobhold.py` (LED retenido), `emu_ledstack.py`, `emu_fmmap.py`, `emu_patmut.py`, `emu_notearp.py`, `emu_fwid.py`, `emu_morph.py --clear --sus --nocur --four --slow`; `sd_app_test.html?bb=1` 8 / 8.
