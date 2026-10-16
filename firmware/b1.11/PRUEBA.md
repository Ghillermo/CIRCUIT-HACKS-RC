# SC42.1 = SC42 + sin relecturas de la tarjeta mientras suena (stutter del delay)

`circuittracks-4486-SC42.1.syx` — SHA-256 `ddcff651cf666c55bb23d146b05a4f3ae47cbbe83617204ce9dea6554813c99a`, marca `SC42.1`.
`firmware/b1.11/circuittracks-4486-B1.11.syx` — SHA-256 `d61c786e983edf8bce492d1c116bf6be342cbc364713d4c6c009355e2efacf0d`: el mismo código con la marca `B1.11` (**Beta 1.11**).

El stutter del delay **solo se da en la beta** (el usuario, 2026-10-16: no se ha reportado ni se reproduce en RC). Además del guardado de ajustes que SC42 ya difiere, la beta **lee la tarjeta cada ~4 s mientras suena** en dos vistas, y la RC nunca (medido en emulación: 10 s sonando, un fotograma cada 10 ms):

| Vista | RC0.9.3 | SC42 | SC42.1 |
|---|---|---|---|
| Preset de MIDI 1 / 2 (patches del sinte propio) | 0 lecturas | 3 rondas (2 bancos) | 1 ronda al entrar |
| Preset de Synth 1 / 2 (colores por modo de voz) | 0 | 3 rondas (4 bancos) | 1 ronda al entrar |

**SC42.1:** la relectura periódica espera a que el transporte esté parado; las lecturas por un cambio (pack, página, patch) siguen.

## Qué probar
1. Proyecto con delay audible, Play. En la vista Preset de MIDI 1 y en la de Synth 1, quieto unos segundos y luego girando knobs / cambiando de modo del motor de MIDI 1 / 2: **sin stutter**.
2. Con el transporte parado, los colores de los huecos (patches propios, modos de voz) siguen bien al cambiar de pack o de página.

## Verificación en emulación
- `emu_playhold.py`: sonando, una ronda al entrar y nada más en 10 s; parado, cada ~4 s; SC42 releía sonando.
- `emu_lazysave.py`: lo de SC42 sigue.
