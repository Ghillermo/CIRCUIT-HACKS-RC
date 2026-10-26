# RC2.10 / RC2.10S = RC2.09 / RC2.09S + el arpegiador con el transporte parado al tempo del proyecto

`firmware/r210/circuittracks-4486-R210.syx` — SHA-256 `a620adaf1b3c8186119e3eca8042b995b5453d232fc57a1e9d07c2f89584cd16`, marca `R210` (**RC2.10**).
`firmware/r210s/circuittracks-4486-R210S.syx` — SHA-256 `fef59c5b63a4786e00fbb3bbabf87340e1513f5784a38326f90ac720aab2fb3f`, marca `R210S` (**RC2.10S**).

Arreglo visto al estudiar la issue #13: con el transporte parado, el arpegio de las notas mantenidas avanza desde la tarea de LEDs a 2500 × ticks / BPM ms, y el BPM se leía del parámetro 1 de `0x20011404`, que no es el tempo (120 con el proyecto a 94, el mismo fallo que se arregló en la cuenta atrás en RC2.03): iba siempre a unos 120 BPM. Ahora el parámetro 0, el tempo del proyecto (`arp.use_bpm0()`). La imagen difiere de RC2.09 en 3 bytes (la marca y el inmediato).

## Qué probar
1. Una pista de notas con el arpegiador encendido, transporte parado, el proyecto a 60 BPM: mantener dos notas = el arpegio a 60 BPM (un paso de 1/16 = 250 ms); a 180, tres veces más rápido.
2. Todo lo demás como RC2.09 / RC2.09S.

## Verificación en emulación
- `emu_arpx.py --tempo` frente a RC2.09 / RC2.09S: con dos pads mantenidos a 60 BPM (p1 = 120) la siguiente nota 250 ms después; en RC2.09, 125 ms (el fallo reproducido).
