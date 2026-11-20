# S714D4 (marca `S714D4`) — diagnóstico

= S714D3 + `dwtwatch.use_value(0x2004FAC0, 0)`. Imagen `0x6ff8c`.

La prueba de estrés de S714D3 colgó el aparato a los 475 s: UsageFault (INVSTATE) en PC 0: la cabeza de la tarea de LEDs de `patmut` volvió por su hueco de LR `0x2004FAC0` y lo encontró a 0. Un punto de vigilancia del DWT (comparador 1 por valor, enlazado al 0 por dirección) salta solo cuando se escribe un 0 ahí; la caja negra guarda el PC / LR de quien lo escribe. Arreglo de `dwtwatch`: la marca de armado es una firma (la RAM no se borra al encender: el byte de antes se leía como armado).
