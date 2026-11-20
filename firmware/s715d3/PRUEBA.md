# S715D3 (marca `S715D3`) — diagnóstico

= S715D2 sin `patscan` + `tools/stepcatch.py`: un paso de reproducción ≥ 32 escrito por el avance de stock (`0x0802CE46`) o visto por el oyente de la vista de drum (`0x0804EB8E`) congela la caja negra (estado `0x85`, etiqueta 4 / 5) con el marco del avance (pista, patrón nuevo, ajustes) y el estado de cadenas / mutate; el paso se recorta (`& 31`) o la llamada se salta. La vigilancia DWT de S715D2 sigue. Imagen `0x6ff1c`.

Con el aparato por USB, en el pack de usar y tirar (caja negra vaciada antes):

    python tools/bbread.py --clear
    python tools/scenestress_dev.py 3600 --seed 1

Al congelarse: `python tools/bbread.py` (el campo `stepcatch`).
