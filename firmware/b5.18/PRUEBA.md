# Beta 5.18 = SC51.5 con la marca de la beta (incluye la 5.17) + el núcleo 1 del DSP con 8 K de programa

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/b5.18/circuittracks-4486-B5.18.syx` | `5778a291487c683cd82b677a41dc9a15c530e0bfdbb28534a8c810005064bbc2` | `B5.18` |

**Qué cambia:** al encender, el núcleo 1 del DSP recibe el mismo paso de arranque que el aparato da al núcleo 0 (OMR MS = 1, `tools/c1ms.py`): **P 8 K, X 8 K, Y 8 K** en lugar de 2 K / 12 K / 10 K (medido con S514D / S514D2); las ranuras de las voces FM pasan a `X:$1000`. Nada cambia en el uso: es sitio para lo siguiente. Lo de la Beta 5.17 (las voces FM en el núcleo 1, 6 por pista) va incluido. Si el aparato no arranca: Scales + Preset + Note e instalar la Beta 5.16.

## Qué probar
1. Arranca y suena como la Beta 5.16: drums, Synth 1 / 2, Master FX, el Glitch (pad 6), el sample capturado.
2. **FM** en MIDI 1 / 2 (pad 24 de la fila de motores), mono y poly, las dos pistas a la vez: suena igual que antes, acordes de hasta 6 por pista.
3. **El granular** en una pista con FM poly en la otra: sin clics ni frenazos.

## Verificación en emulación
- `emu_fmc1_core1.py` con las ranuras en `X:$1000`: bit a bit contra el bucle FM del núcleo 0.
- La llamada del programa del núcleo 1 (`0x080292A6`) pasa por `c_c1ms`, que manda antes el stub a ese núcleo (`emu_s514d.py` lo comprueba en S514D2, el mismo módulo).
- Lo de SC51.4: `emu_fmc1_core0.py`, `emu_poly3.py`, `emu_vguard.py`.
