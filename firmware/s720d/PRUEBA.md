# S720D (marca `S720D`) — diagnóstico

= Alpha 7.20 + `tools/stocktrap.py` + `blackbox.use_memrd()` + `tools/sxpanel.py`, sin `tools/fxstep.py` (sitio).

**Para qué:** probar en el aparato que el código del stock que `tools/fullwalk.py` da por muerto lo está: 25 trozos (1 370 B, todos por debajo de
`0x08058000`) llenos de `UDF`. Si algo pasa por uno, fallo del procesador: la caja negra lo congela con el PC y el aparato se reinicia (Save violeta).
Los 10 trozos de `0x08058000` en adelante (386 B) se quitaron de la lista: es la zona de datos del stock (vtables, tablas) y la emulación leyó
dos de ellos como datos (punteros a funciones).

## En emulación
`emu_gmview`, `emu_sc35`, `emu_xlanes`, `emu_xlfix`, `emu_blackbox2`, `emu_rangefix`, `emu_patrev`, `emu_fmmap`, `emu_arp`, `emu_morph`,
`emu_poly3`, `emu_fmeng2`: ninguna toca una trampa (los fallos que quedan son los mismos que en la Alpha 7.20 o los de S717D: sin `fxstep`).

## En el aparato
    python tools/bbread.py --clear
    python tools/scenestress_dev.py 3600 --seed 1
    python tools/panelstress_dev.py 1800

y uso normal (cargar / guardar proyectos y packs, copiar samples, Components, la app, Easy Start si se usa). Al terminar:
`python tools/bbread.py --firmware S720D`: estado 0 = ningún trozo ejecutado.
