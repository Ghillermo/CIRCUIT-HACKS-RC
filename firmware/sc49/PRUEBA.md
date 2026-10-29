# SC49 = SC48.9 sin su código muerto (flash para el carril extra de los drums)

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc49/circuittracks-4486-SC49.syx` | `ab004c3fc1e11d4c4598b5e925461ed06b45b56df7149348efc802cec7332a36` | `SC49` |

El usuario (2026-10-28): «Do it.» (liberar flash para el carril extra de los drums: SC48.9 tenía 8 B libres). «SC48.10» se cortaría a «SC48.1».

## Qué cambia
Nada que se vea o se oiga: SC48.9 sin las funciones que ya no llama nadie (versiones antiguas sustituidas por otras posteriores sin quitar el
código viejo). Imagen `0x6F708`: **2 296 B libres** al final (SC48.9: 8 B). Sin beta: no hay nada nuevo que probar como función.

| Opción | Lo que se quita | Por qué está muerto |
|---|---|---|
| `packio.use_trimx()` | `c_xswap` (SC37, 796 B), `c_xswap2` (SC37.3, 400 B) | con `COPYX` los pads van a `c_xcopy2`; dentro del pack el intercambio sigue en `c_swap2` |
| `build_sc08.use_trim()` | `c_dpad` (80 B), `c_shbtn` | `build_sc11` pone `c_dpad2` / `c_shbtn2` en sus dos ganchos |
| `vcf21.use_trimed()` | `c_edfield`, `c_edknob`, `c_edcyc` (328 B) | el editor de CC v2 (`EDV2`) usa `c_edfield2` / `c_edknob2` / `c_edcyc2` |
| `playmode.use_trimnu()` | `c_pmnudge` (218 B) | con `NUDGE2` el pad 26 va a `c_pmnudge2` |
| `drums18.use_trim()` | `c_dk18` (272 B), `c_dtick` (128 B), `c_dleds18` | `persist19` pone `c_dk19` en la ranura 4 de los manejadores de macros de drums, `c_dtick19` en la cabeza de la cadena del servicio del DSP y `c_dleds` de SC08 otra vez en la ranura 7 de la vista Preset de drums |

## Qué probar
Lo de siempre en las zonas tocadas: los knobs de drums (con y sin Shift, Clear + knob), el editor de CC de MIDI 1 / 2 (pad 25), el Nudge de
Pattern Settings (pad 26, con y sin Shift), Duplicate + sample entre packs y dentro del pack (vista Preset de drums), la vista cromática de drums.
Tiene que comportarse igual que SC48.9.

## Verificación en emulación
SC49 frente a SC48.9, los mismos resultados: `emu_edscratch`, `emu_edlock`, `emu_nudge2`, `emu_snapall`, `emu_startfix` (ALL PASS),
`emu_sc43_7` (los tres fallos de siempre), `emu_k3split` (los dos de siempre: pensada para SC41.7 frente a SC41.6), `emu_sc35` (el de siempre:
el Clear de la vista de packs), `emu_sc28` (los seis de siempre: pensada para SC28). `emu_sc35` elegía sus comprobaciones por las etiquetas `c_xswap` / `c_xswap2`: ahora una build con
`c_xcopy2` tiene también esos caminos.
