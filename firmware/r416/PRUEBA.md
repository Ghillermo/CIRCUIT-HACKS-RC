# RC4.16 (marca `R416`) — pendiente de probar

= RC4.15 + `sampler_dsp.use_noplayrec()`: mientras el pad 32 graba, nada arranca la reproducción del sample (pad 7, loop enganchado, un hueco de Master FX, el secuenciador de efectos); antes sonaba la toma a medio escribir. Parar (orden 3) sigue funcionando.

Prueba: `emu_overdub_dsp.py` (pasa).

+ `tools/fixes704.py` (`rc()`): **Clear + escena** borra también el modo de cadena y las repeticiones de esa escena (`sclear2.py`); `patchain` sin nada en la pila de la tarea de LEDs mientras corre la cadena. Pruebas `emu_sclear2.py`, `emu_ledstack.py` (pasan).
