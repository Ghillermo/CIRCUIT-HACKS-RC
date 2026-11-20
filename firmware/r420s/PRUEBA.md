# RC4.20S (marca `R420S`) — pendiente de probar, sin publicar

= RC4.19S + `tools/cc27fix.py`. Imagen `0x6f7d4`.

**Arreglo de un cuelgue del firmware de stock:** un **CC 27 en el canal 16** (el del proyecto) colgaba el aparato (también el firmware oficial; un Circuit Rhythm lo manda, muy probablemente al cambiar el recorte de −12 dB de la grabación de samples). Es el 13.º parámetro del grupo master; su bit de pendiente llamaba a una entrada de la tabla que no es una dirección (`0xD0002800`). Ahora el bit se borra sin llamar a nada (2 bytes de stock).

## Probar
1. Con el aparato conectado por USB: mandar CC 27 (valor 127) por el canal 16 (o el Rhythm cambiando el recorte de −12 dB con CC out): no se cuelga.
2. El filtro master y el compresor (CC 74 / 71 / 22-26 por el canal 16) siguen funcionando.

Prueba `emu_cc27.py` (stock y la 7.13 fallan dos).
