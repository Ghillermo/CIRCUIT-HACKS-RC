# S715D (marca `S715D`) — diagnóstico

= Alpha 7.15 + `patscan` + `sxpanel` + `blackbox.use_memrd()` + `blackbox.use_keepstall(400)`. Imagen `0x6fee8`.

Para las pruebas de estrés con el aparato conectado por USB, en un pack de usar y tirar (una copia en la tarjeta):

    python tools/scenestress_dev.py 1800 --seed 1
    python tools/panelstress_dev.py 600

Un valor de paso imposible congela la caja negra (estado `0x85`, `STK1` = 3, valor, dirección y los últimos mensajes MIDI); una pausa del bucle principal de más de 400 ms queda guardada con muestras de PC y la herramienta la vacía y sigue. Con los arreglos de la 7.15 el trabajo de la tarjeta ya no debe dejar pausas.
