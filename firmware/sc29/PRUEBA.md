# SC29 — SC28 + motor VA-drum en las pistas MIDI

`circuittracks-4486-SC29.syx` — SHA-256 en `manifest.json` (`syx_sha256`)
Marca `SC29`. Reserva: **SC28**. Todo probado en emulación (ARM y DSP); **nada probado en el aparato**.
RAM: **sin cambios**. DSP: +127 palabras de programa (quedan 387 hasta `P:$3FFF`).

El motor **VA-drum** es una variante del oscilador de las pistas MIDI pensada para percusión, inspirada en otros sintetizadores percusivos por pasos. Es el compañero natural del step-drummer (pad 30), pero funciona también con notas normales.

## Cómo se entra
Vista **Preset** de MIDI 1 / 2, **pad 27**, ahora con cuatro estados:

**apagado → entrada de línea → oscilador → VA-drum → apagado**

El pad 27 cambia de color en el estado VA-drum (color provisional). Todo lo demás del oscilador sigue ahí: uno o dos osciladores (pad 28), orden de la cadena (pad 29), FM, ring, sync, bit a bit, FX, filtro, las cinco páginas de knobs.

## Qué cambia en el estado VA-drum
**Los knobs son los mismos y guardan los mismos valores; cambia lo que significan estos:**

| Knob (página de modulación, pad 5) | En el oscilador normal | En VA-drum |
|---|---|---|
| ATK | ataque | ataque del VCA (0 = golpe inmediato) |
| **DEC** | decay | **decay del VCA** (hasta el silencio) |
| **SUS** | nivel de sustain | **decay de la envolvente de pitch** |
| **REL** | release | **decay de la envolvente del filtro** |
| env→nivel / env→filtro / env→tono | una envolvente para todo | cada cantidad usa **su** envolvente (VCA / filtro / pitch) |
| **LRATE** | velocidad del LFO | **nivel de ruido blanco** sumado al oscilador |
| LFO→filtro, LFO→nivel, LFO→tono, LFO→forma, LFO→morph | LFO (diente de sierra) | **valor aleatorio** (sample & hold, uno cada 0,7 ms) a ese destino |

- **El VCA es de un solo disparo:** ataque y luego decay hasta el silencio. **La duración de la nota no importa** (soltar la tecla no corta el sonido); cada nota nueva vuelve a disparar las tres envolventes.
- Las envolventes de pitch y de filtro son solo decay, van el doble de rápido que la tabla del VCA (0 = ~20 ms).
- **Pad 31** (solo se enciende en VA-drum): **la velocity también fija el nivel de partida de las envolventes de pitch y de filtro** (golpes suaves = menos barrido de tono y de filtro). La velocity sigue escalando el nivel como siempre.

### Receta de partida (bombo)
Pad 27 hasta VA-drum, un oscilador, WAVE = seno. Página 5: ATK 0, DEC ~70, **SUS ~30** (decay del pitch), REL ~40; Shift: env→nivel al máximo, **env→tono hacia la derecha** (el «piu» del bombo), env→filtro a gusto. LRATE = 0 (sin ruido). Para una caja: sube LRATE (ruido), baja DEC, filtro paso alto o paso banda.

## Pruebas en el aparato (en este orden)
1. **Arranca**; los valores guardados de SC28 siguen ahí; el modo VCA-VCF y el oscilador suenan **igual que antes** (en emulación, bit a bit).
2. MIDI 1, pad 27: línea → oscilador → **VA-drum** (el pad cambia de color; el pad 31 se enciende tenue).
3. Toca una nota larga: **suena un golpe que decae solo**, aunque mantengas la tecla. Suelta pronto: el decay no se corta.
4. DEC: la duración del golpe. SUS (con env→tono subido): lo que dura el barrido de tono. REL (con env→filtro subido y FILT en paso bajo): lo que dura el barrido del filtro. Deben ser **independientes**.
5. LRATE: aparece ruido blanco junto al oscilador. LFO→filtro / LFO→tono: modulación aleatoria.
6. **Pad 31** encendido: toca flojo y fuerte: con poca velocity, menos barrido de tono / filtro.
7. Pad 30 (step-drummer) en este estado: la fila de pitch y la de velocity sobre el motor VA-drum.
8. Pad 27 otra vez: apagado. Vuelve a subir: línea, oscilador (el oscilador normal, con su LFO y su sustain de siempre).
9. Apaga y enciende: el estado VA-drum y el pad 31 **se conservan** (por pista).
10. **Lo que más importa:** que no haya clics ni cuelgues al cambiar de estado con el pad 27 mientras suena, y que el ruido no sature (con LRATE al máximo el ruido tiene el nivel del oscilador).

## Limitaciones conocidas
- Al entrar en VA-drum, SUS / REL / LRATE conservan el valor que tenían: el sonido cambia hasta que los ajustes (acordado: se reinterpretan, no hay RAM para otros).
- No hay destinos de velocity seleccionables uno a uno: el pad 31 actúa sobre las dos envolventes a la vez.
- El decay más corto de las envolventes de pitch / filtro es ~20 ms; el del VCA, el de la tabla (~40 ms). Si hace falta un «clic» más corto, dímelo: es una constante.
- Si flasheas SC28 o anterior con una pista en VA-drum, ese firmware no reconoce la firma del estado guardado y **arranca con los valores por defecto** del modo VCA-VCF. Para evitarlo, deja las dos pistas fuera de VA-drum antes de volver atrás.
- El color del pad 27 en VA-drum (`0x45`) y los del pad 31 (`0x4D` / `0x4E`) están sin confirmar.

## Cómo está hecho (resumen; detalle en `docs/NOTAS.md`)
- Opciones `vcf21.use_vadrum()` (ARM) y `vcf21_dsp.use_vadrum()` (DSP); builder `tools/build_sc29.py`.
- Estado sin RAM: el nibble bajo del byte de firma del estado guardado (`0xB0`…`0xBF` válidos): bit t = VA-drum de la pista t, bit 2 + t = pad 31. Va al DSP en el mensaje ACT (bits 10 / 11 del valor); el buzón los deja en `DFLAGS` (bits 2 / 3).
- DSP: dos palabras nuevas por voz en el bloque del oscilador (`+22` envolvente de filtro, `+23` de pitch), que en los otros motores son una copia de la envolvente (por eso su sonido no cambia); `+24` generador de ruido (congruencial de 24 bits, periodo completo), `+25` su nivel. Un lazo por bloque suma el ruido a la salida del oscilador.
- Coste: +44 instrucciones por bloque en los otros motores; VA-drum con ruido en las dos pistas +626 (0,38 % del presupuesto). Pila sin cambios (6).
- Imagen de 0x6139C bytes.

## Pruebas de emulación
`emu_sc29_dsp.py` (buzón; los otros motores bit a bit contra SC28 en entrada de línea, uno y dos osciladores; disparo único; las tres envolventes y su independencia; ENVP sobre el tono en semitonos; ENVF sobre el corte; velocity → envolventes; redisparo; ruido: valor aleatorio por bloque, ruido blanco con su nivel y espectro plano; coste y pila), `emu_sc29.py` (firma con cualquier nibble, los cuatro estados del pad 27, el mensaje ACT, el pad 31, el editor de CC, la segunda pista) y las de SC23.x … SC28 sobre esta imagen.

## Si algo falla
Flashea SC28 (con las pistas fuera de VA-drum, ver arriba). Para volver al firmware original: el instalador, «RESTAURAR», o Novation Components.
