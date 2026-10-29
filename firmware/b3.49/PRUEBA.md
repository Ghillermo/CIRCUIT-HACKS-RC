# SC49.6 / Beta 3.49 = SC49.5 + el paso de Record + paso en amarillo mientras se mantiene

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc49.6/circuittracks-4486-SC49.6.syx` | `42922a138419890aa18c68a507a8e9e3735041d195b5213e27e0ce63a330ccbe` | `SC49.6` |
| `firmware/b3.49/circuittracks-4486-B3.49.syx` (**Beta 3.49**) | `c6b6d048f364f725ae5c96161a0da85d2511401c94fc78e41c654dcfd1646c4f` | `B3.49` |

El usuario (2026-10-29): «record+step must produce momentary visual cue on the step (yellow while held)». La Beta 3.49 incluye la 3.48 (no se
publicó).

## Qué cambia (`slock.use_cue()`)
- **Record mantenido + un paso** (la foto en MIDI 1 / 2, Synth 1 / 2 y los drums, también la de los bloqueos de estado y la del carril extra):
  el pad del paso se ve **amarillo** mientras lo mantienes y vuelve a su color al soltarlo. Todas esas fotos dejan el pad en la RAM de
  `recinst` (+ 3: pad + 1, o pad + `0x41` en un drum) hasta soltarlo; la tarea de LEDs lo pinta.
- Imagen `0x6FFD0` (**48 B libres**), zona libre 46 B.

## Qué probar
1. Synth 1, vista de pista: Record mantenido + mantener un paso: amarillo; soltarlo: su color.
2. Lo mismo en MIDI 1 con el sinte propio encendido y en la vista Note de un drum.
3. Sin Record, mantener un paso: como siempre (no amarillo).
4. Lo de SC49.5 (ver `firmware/sc49.5/PRUEBA.md`).

## Verificación en emulación
`emu_reccue.py` frente a SC49.5: Synth 1, Drum 1 y MIDI 1 (motor encendido), amarillo mientras se mantiene, no después; sin Record, no; SC49.5
nunca. `emu_slock.py` igual que SC49.5.
