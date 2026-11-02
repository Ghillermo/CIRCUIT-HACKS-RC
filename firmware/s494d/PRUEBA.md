# S494D (diagnóstico) = SC49.4 + lectura remota de la ITCM y del DSP por USB

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/s494d/circuittracks-4486-S494D.syx` | `a31e4c814e418fbef60a8b1b44fecaef8115c6bcc438d40ab86aabd5008a1a24` | `S494D` |

Comprueba en el Circuit Tracks lo que Arrhythmia (llcoolkm, MIT) encontró en el Circuit Rhythm:

1. **La ITCM** (16 KB de RAM del ARM en la dirección 0): ¿la usa algo? Claude la llena desde el PC con una marca y, tras un rato de uso, mira si alguna palabra cambió.
2. **El núcleo 0 del DSP, `X:$4000-$5FFF`**: ¿existe esa memoria, es un espejo de `X:$0000-$1FFF` y la usa el firmware? Aquí solo se ha comprobado hasta `X:$3FFF`.
3. **El núcleo 1 del DSP**: ¿responde a la lectura del ARM? (`X:$2B00-$2FFF` estaría libre según Arrhythmia).
4. **La subida de samples**: mientras el aparato carga samples en el DSP (cambiar de pack, cargar un sample), ¿llega alguna escritura nuestra al DSP? En el Rhythm caería dentro del sample. Aquí solo se cuenta, no se cambia nada: `mem 0x2004EF00 24` = subidas, escrituras nuestras dentro, del stock dentro, nuestra última dirección de vuelta.

Es SC49.4 (anterior a la Beta 5.0) porque es la que tiene flash libre. **Usa un proyecto de prueba y no guardes encima de proyectos hechos con la Beta 5.x.**

## Cómo
1. Instalar S494D. Conectar el aparato por USB a este PC y cerrar Components, el navegador con el uploader o la app de la tarjeta y cualquier DAW (en Windows el puerto MIDI solo se abre una vez). Avisar a Claude.
2. Claude: `ctremote.py ping`, `itfill`, `itchk` y las lecturas del DSP (`dspr x 0x4000 …`, comparadas con `0x0000 …`; una escritura de prueba en una palabra, devuelta después).
3. Usar el aparato unos 10-15 minutos sin apagarlo: **cargar otros packs varias veces con MIDI 1 / 2 en un motor propio (oscilador, FM) y Master FX activos**, proyectos, Sample Rec, tocar con todas las pistas, Master FX, Save. Avisar a Claude.
4. Claude: `itchk`, el contador de las subidas y las lecturas del DSP otra vez. **0 palabras cambiadas = la ITCM está libre.**
5. Volver a instalar la Beta 5.9.

Las lecturas del núcleo 1 van al final: si el núcleo 1 no contesta, el aparato puede quedarse parado y basta con apagarlo y encenderlo.

## Verificación en emulación
- `emu_s494d.py`: 23 de 23 (ping, `mem` en la ITCM, `itfill` / `itchk` y su rechazo sin ITCM, `dspr` / `dspw` con el núcleo elegido, los contadores de `gatediag` con escrituras nuestras / del stock dentro y fuera de una subida).
