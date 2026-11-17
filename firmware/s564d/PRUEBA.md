# S564D (diagnóstico) = Beta 5.64 + watchpoints de hardware (DWT) sobre las palabras corrompidas

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/s564d/circuittracks-4486-S564D.syx` | `3381d93d84c7b1d448780979f1e25bed1360d73dc417492b024f19d8fa6acdba` | `S564D` |

Todo lo de la Beta 5.64, más `tools/dwtwatch.py`: el procesador vigila las dos palabras que aparecieron cambiadas en los cuelgues (`0x20042988`, tras
el búfer de LEDs de la vista de probabilidad de MIDI 2: dos veces en la 5.64; `0x20043610`, tras la barra de velocity de Drum 3: en la 5.63). En la
primera escritura, la caja negra se congela con el **PC / LR del código que escribe** (y los registros, el anillo de gestos, la vista).

## Qué hacer
1. Instalar S564D y repetir lo que hacías (grabar knobs de MIDI 1 en modo oscilador, MIDI 2, Preset, Play…).
2. Si se reinicia o Save se ve violeta al encender: app → Caja negra… → guardar el JSON y pasarlo. El registro dirá «fault» con vector 12: eso es la
   vigilancia, no un fallo nuevo.

## Verificación en emulación
`emu_dwtwatch.py` (ALL PASS: armado de DEMCR / comparadores una sola vez, el fotograma de LEDs de la 5.64, el manejador congela la caja con el PC /
LR del marco, apaga los comparadores y conserva r4-r7). Unicorn no tiene DWT: el disparo real solo se ve en el aparato.
