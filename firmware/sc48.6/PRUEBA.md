# SC48.6 / Beta 3.43 = SC48.5 / Beta 3.42 + Synth 1 / 2 ya no callan con un acorde poly

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc48.6/circuittracks-4486-SC48.6.syx` | `0e7f6d3791878b822e94953d0d2cafe17111dd340b21bed9e0635be657d943e3` | `SC48.6` |
| `firmware/b3.43/circuittracks-4486-B3.43.syx` (**Beta 3.43**) | `aa308c9d20906023783dd29d55c194f4746cb13b13e1d7d4f98eaf06c169e3c9` | `B3.43` |
| `firmware/b3.43s/circuittracks-4486-B3.43S.syx` (**Beta 3.43S** = la beta sin escrituras propias en la SD) | `518f8c0f63457b660b000ae84e67a3787ca0c53f0c908d135f8265d1d2dbf3e6` | `B3.43S` |

El usuario (2026-10-28, con SC48.5 / S485D): «stock synths sometimes cease to sound when 5 notes are held», «synth1/2 sometimes stop playing,
they come back when i let go of the chord», «save was amber/yellow/orange»; solo en poly, con 4 notas o más, con el oscilador, el VA-drum y FM.

**La causa:** el aparato tiene su propio limitador de voces para Synth 1 / 2: mide cuánto tiempo le sobra al DSP en cada bloque y, si no cabe
media voz más, mata una voz de ese sinte cada 8 ms. Las voces del sinte propio gastan ese tiempo, así que el aparato callaba Synth 1 / 2 hasta
soltar el acorde. **Ahora**, mientras suenan dos voces propias o más, el aparato no mata voces de Synth 1 / 2; si de verdad falta tiempo, el
limitador de SC48.5 quita voces del sinte propio.

## Qué probar
1. Synth 1 / 2 secuenciados (el patch 7 de los presets, los que callaban) y en MIDI 1 un acorde poly de 5 notas mantenido (oscilador, VA-drum o
   FM, desde el teclado o la pantalla de acordes): **Synth 1 / 2 siguen sonando** todo el rato.
2. Con el DSP muy justo, una nota nueva de Synth 1 / 2 puede reusar una voz de su propio sinte (lo que hace el aparato con carga): un acorde
   de Synth 1 puede sonar con menos notas mientras el acorde propio está mantenido, pero no se calla.
3. Que no traquetee: si el DSP se queda sin tiempo, se apagan voces del sinte propio (como en SC48.5).
4. Lo de SC48.5 sigue igual (MIDI otra vez = Preset, limitador, nivel de los acordes, poly por defecto).

Para ver el DSP: **S486D** (`firmware/s486d/`) = esto + los medidores de S484D.

## Verificación en emulación
- `emu_vguard.py` (lo de SC48.5) + las cuentas atrás del aparato `X:$3239` / `X:$323A`: ninguna escritura con menos de dos voces; con seis, 48
  en las dos cada 16 ms; con una voz, ninguna. **En emulación el limitador del aparato nunca salta** (el temporizador del DSP emulado lee 0),
  así que el arreglo solo se ve en el aparato.
