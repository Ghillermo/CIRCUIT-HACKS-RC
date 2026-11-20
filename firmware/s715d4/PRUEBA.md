# S715D4 (marca `S715D4`) — diagnóstico

= S715D3 + `patchain.use_rangefix()` (el arreglo de la causa de la corrupción de la 5.63 / 5.64). Imagen `0x6ff28`.

    python tools/bbread.py --clear
    python tools/scenestress_dev.py 3600 --seed 1

Nada debe congelar la caja negra (antes: a los 930 / 1 756 s).

**Probado 2026-11-20: 3 606 s, 79 011 escenarios, nada congelado.**
