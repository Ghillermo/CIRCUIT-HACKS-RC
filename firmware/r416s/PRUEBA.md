# RC4.16S (marca `R416S`) — pendiente de probar

= RC4.15S + `sampler_dsp.use_noplayrec()` (como RC4.16). Nada propio escribe en la tarjeta.

Prueba: `emu_overdub_dsp.py` (pasa).

+ `tools/fixes704.py` (`rc()`): **Clear + escena** borra también el modo de cadena y las repeticiones de esa escena (`sclear2.py`); `patchain` sin nada en la pila de la tarea de LEDs mientras corre la cadena. Pruebas `emu_sclear2.py`, `emu_ledstack.py` (pasan).
