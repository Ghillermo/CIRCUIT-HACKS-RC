# S513D (diagnóstico) = Beta 5.16 / SC51.3 + carga FM de prueba en el núcleo 1 del DSP

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/s513d/circuittracks-4486-S513D.syx` | `0755891492888dbd029870fd94179cf62c7a60e618677583462c05eee916b408` | `S513D` |

**La pregunta:** ¿tiene el núcleo 1 del DSP tiempo para las voces FM? (estudio «las voces FM en el núcleo 1» de `docs/NOTAS.md`). El núcleo 1 calcula N voces FM **de prueba, sin sonar** (el mismo bucle de 4 operadores que el núcleo 0, ≈ 6 500 instrucciones por voz y bloque, en tareas cortas); se mide si llega a tiempo y si frena al núcleo 0.

- **Save** (como S484D) = el tiempo del núcleo 0: verde / amarillo / naranja / rojo (un bloque tardó más que un periodo), blanco = el audio se repitió.
- **Duplicate** = el pico del sinte propio (rojo = recorte).
- El resto lo lee Claude por USB (`tools/fmload_sweep.py`).

**Sin Glitch ni gesto mecánico** (pads 6 y 31 de Master FX): en esta build su código se ha quitado del núcleo 1 para dejar sitio a la prueba; mantenerlos = silencio. Todo lo demás es la Beta 5.16. **Usa un proyecto de prueba.**

## Cómo
1. Instalar S513D. Conectar por USB a este PC y cerrar Components, el uploader, la app de la tarjeta y cualquier DAW. Avisar a Claude.
2. Cargar un proyecto con mucho movimiento (drums, Synth 1 / 2 con acordes, un pack con muchos samples) y darle a Play. Sin el granular primero.
3. Claude: `python tools/fmload_sweep.py` sube N (0, 2, 4 … 24 voces de prueba) y para en la primera que llega tarde o frena al núcleo 0. Mientras, escuchar: un clic o un frenazo del audio = el límite.
4. Lo mismo con una pista en granular, y con `--samples 8` (tareas el doble de largas: ¿cuánto puede tardar una tarea sin frenar al núcleo 0?).
5. Volver a instalar la Beta 5.16.

## Verificación en emulación
- `emu_fmload_core1.py`: el núcleo 1 con la carga (`0x721` palabras de 2 048): una voz = 8 tareas de 809 instrucciones (6 473 por bloque, como el FM del núcleo 0); sin tareas pendientes nada tarde; con demasiadas, cada bloque tarde y lo que falta se deja; la comprobación de `X:$2B00..$2BFF` al arrancar.
- El núcleo 0 de la imagen entera copia `X:$3FE8..$3FEB` a la memoria compartida y los contadores del núcleo 1 a `X:$3FEC..$3FEF` (dsp_session).
- `emu_dspload.py` y `emu_sc35d8.py --dspx --dspw` sobre S513D: ALL PASS.
