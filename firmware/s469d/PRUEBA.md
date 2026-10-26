# S469D (diagnóstico) = SC46.9 / Beta 3.26 + sonda de los lados + lectura remota del DSP

`firmware/s469d/circuittracks-4486-S469D.syx` — SHA-256 `61279389118af5caf6cc3f4d96f59b9ad0c5513f99dee58114c8f5f10c7da490`, marca `S469D`.

El usuario (2026-10-26): el sample estéreo «sigue mezclando los dos samples a los dos canales por igual» y el granular con Shift + K4 «tampoco se aprecia gran diferencia»; en la emulación del núcleo 0 entero los dos salen abiertos. En cada bloque, la suma de los lados antes del filtro master copia lo que ve para MIDI 1 en `X:$3F40` (dirección de SOUT, ganancia g, SOUT[0], la mezcla L / R antes y después, el contador de bloques, sus llamadas); Claude lo lee por USB (`tools/ctremote.py dspr X 0x3f40 9`). La S47D no puede leer la memoria compartida (`X:$37xxx`: el puerto de host solo llega a 16 bits).

## Cómo
1. Instalar S469D (= Beta 3.26 con la sonda; sin polifonía). Conectado por USB, sin otros programas MIDI abiertos.
2. MIDI 1 en el modo muestra, WAVE a la derecha del todo, dos samples distintos; las demás pistas en silencio. Notas largas sonando y avisar.
