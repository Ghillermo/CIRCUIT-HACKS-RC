# S721D (marca `S721D`) — diagnóstico

= Alpha 7.21 + `tools/stocktrap.py` (25 trozos del stock que parecen sin usar, más los 36 B finales del manejador de disco cortado
`0x0803B758`: 1 406 B de `UDF`) + `blackbox.use_memrd()` + `tools/sxpanel.py`, sin `tools/fxstep.py`. Prueba a la vez el corte de la unidad USB
(todo va por USB MIDI) y que los trozos no se ejecutan.

    python tools/bbread.py --clear
    python tools/scenestress_dev.py 3600 --seed 7
    python tools/panelstress_dev.py 1800

y uso normal; al final `python tools/bbread.py --firmware S721D`: estado 0 = ningún trozo ejecutado.
