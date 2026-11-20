# S714D5 (marca `S714D5`) — diagnóstico

= S714D3 + `dwtwatch.use_filtered(0x2004FAC0, 0x08067BBB)`. Imagen `0x6ff90`.

S714D4 (vigilancia por valor, solo palabras) no saltó y el cuelgue volvió a los 476 s (misma semilla): el 0 no es una escritura de palabra de la CPU. Aquí toda escritura en esa palabra (cualquier tamaño) pasa por el DebugMonitor: el valor legítimo de patmut (el retorno en la cabeza de LEDs de la caja negra) sigue; cualquier otro congela la caja negra con el PC / LR de quien escribe. Se arma mirando el propio comparador (un reinicio lo borra). Si tampoco salta: DMA.
