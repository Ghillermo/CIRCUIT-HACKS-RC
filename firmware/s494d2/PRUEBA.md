# S494D2 (diagnóstico) = S494D + ejecutar código desde la ITCM

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/s494d2/circuittracks-4486-S494D2.syx` | `71e1c2607b0759e329f4913b597bb330f98437ae4556b9a91b8a56eed9d8053e` | `S494D2` |

Todo lo de S494D (ver `firmware/s494d/PRUEBA.md`), más una pregunta: **¿puede la ITCM llevar código?** Arrhythmia (llcoolkm, MIT) carga ahí sus módulos en el Circuit Rhythm. Si en el Tracks la ITCM está libre y ejecuta, son 16 KB de código que no caben en la flash (llena), cargados desde la tarjeta al encender.

`ctremote.py itexec` escribe 3 instrucciones en `0x3F00` (`movs r1, #0x5A; eors r0, r1; bx lr`), las ejecuta y devuelve las dos palabras que había. Respuesta esperada: `status 0`, `result` = la clave XOR `0x5A`, «runs code». Un fallo de ejecución para el aparato sin respuesta: apagar y encender.

Es SC49.4 por la flash libre. **Usa un proyecto de prueba y no guardes encima de proyectos hechos con la Beta 5.x.**

## Cómo
1. Instalar S494D2. Conectar por USB a este PC y cerrar Components, el uploader, la app de la tarjeta y cualquier DAW. Avisar a Claude.
2. Claude: `ping`, `itfill`, `itchk`, las lecturas del DSP (`dspr x 0x4000 …`) como en S494D.
3. Usar el aparato 10-15 minutos sin apagarlo (cambiar de pack varias veces con MIDI 1 / 2 en un motor propio y Master FX activos, proyectos, Sample Rec, Save). Avisar a Claude.
4. Claude: `itchk` (0 palabras cambiadas = libre), el contador de subidas, **`itexec` al final** (y las lecturas del núcleo 1, las últimas).
5. Volver a instalar la Beta 5.10.

## Verificación en emulación
- `emu_s494d.py` sobre S494D2: además de lo de S494D, la rutina se ejecuta desde `0x3F00` (clave XOR `0x5A`), sus dos palabras vuelven, y sin ITCM se rechaza sin tocar nada.
