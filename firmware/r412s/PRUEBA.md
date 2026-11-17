# RC4.12S = RC4.11S + arreglos: el arpegio a tiempo entre dos micropasos; la captura sigue al cargar un proyecto

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/r412s/circuittracks-4486-R412S.syx` | `ebab1aac553dd19f8732f193a14d0eb23e99adbf94ab9e2a6a6b42f7620f8271` | `R412S` |

**El fallo 1** (el usuario, 2026-11-13: «cuando la velocidad del arpegiador es x4 la velocidad del patrón base en pattern settings, el arpegiador
toca en tresillos / swing»): el secuenciador va a 24 PPQN y el arpegiador solo podía tocar en los micropasos de la pista (6 por paso). Con una pista
a 1/8 (12 ticks por paso, un micropaso = 2 ticks) y el arpegio a 1/32 (3 ticks), cada nota cae a micropaso y medio: el arpegio tocaba en el
micropaso siguiente, 2 y 1 micropasos alternos (83 / 42 ms a 120 BPM) = swing. Lo mismo en toda resolución que no es un número entero de micropasos.

**El arreglo 1** (`arp.use_timed()`): cuando la nota cae entre dos micropasos, el micropaso anterior la arma con su hora (en ms, del tempo) y el bucle
principal del aparato (la llamada al servicio del DSP, cada ~1 ms, en la misma tarea que el secuenciador) la toca a esa hora; si no llega a tiempo,
la toca el micropaso siguiente como antes. Parar el transporte suelta lo armado. Los arpegios que caen en los micropasos no cambian.

**El fallo 2** (el usuario, 2026-11-14: «When a sample capture is running and a new project is loaded, the capture stops automatically … Can we
not stop it?» → «fix and beta»): toda carga de proyecto (también un pack nuevo o un proyecto nuevo) termina con el «todo apagado» de Master FX (el del
pad 8), que también paraba la captura del sample. No era una función pensada: el pad 8 lo usaba primero (SC33) y la carga lo heredó.

**El arreglo 2** (`tools/capkeep.py`): en la carga, una captura fijada (pad 32 corto) o armada (Shift + pad 32) se conserva: sigue grabando donde iba
(o sigue armada para el siguiente compás). Una captura mantenida termina al salir de su vista, como antes; el pad 8 la sigue parando. La captura graba
lo que suene por el master durante la carga.

## Qué probar
Synth 1 a 1/8 (Pattern Settings), el arpegiador a 1/32 (Shift + pads 17-24), un acorde: las notas deben ir regulares, sin swing. Lo mismo con el teclado
(parado y en marcha) y con 1/16 en una pista a 1/16 (como antes). Parar a mitad: no queda ninguna nota colgada.

Captura: en Master FX, pad 32 corto (fijada), ir a Projects y cargar otro proyecto: sigue grabando hasta su final o hasta pulsar
pad 32; armada (Shift + pad 32) y cargar: sigue armada. El pad 8 la sigue parando.

## Verificación en emulación
- `emu_arptime.py` contra RC4.11S: 1/32 sobre 1/8 cada 62,5 ms (61 / 64 ms; antes 83 / 42), las mismas notas en el mismo orden; 1/16 sobre 1/16 y 1/32 sobre 1/16 iguales que antes;
  parar con una nota armada la suelta.
- `emu_capkeep.py` contra RC4.11S: fijada y armada siguen tras el «todo apagado» de la carga (antes: parada, STATE 0 / desarmada); mantenida y pad 8, como antes.
