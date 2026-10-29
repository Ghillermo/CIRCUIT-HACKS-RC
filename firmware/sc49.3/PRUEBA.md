# SC49.3 = SC49.2 sin más código muerto (flash para la fase 2 del carril extra)

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc49.3/circuittracks-4486-SC49.3.syx` | `0c3c12b08cd22b7a6c6f61f35b0025d96b601b5b93e5624b4e85e7c5c3a05478` | `SC49.3` |

El usuario (2026-10-29): «dead code pass». Nada cambia en el uso: es SC49.2 sin las funciones que ya no llama nadie. Imagen `0x6FC68`:
**920 B libres** al final (SC49.2: 184 B), la zona libre igual (314 B). Sin beta.

| Opción | Lo que se quita | Por qué está muerto |
|---|---|---|
| `build_sc15.use_trim()` | `c_spad`, `c_sleds` (212 B) | `srcview` (SC19.1) pone `c_xpad` / `c_xleds` en esas ranuras de la vista Preset del sinte y sigue a las de stock |
| `arp.use_trimins()` | la inserción ordenada (`c_arins_old`, 98 B) | con `PRESSORD` las notas entran en el orden pulsado |
| `compkn.use_trim()` | `compkn` entero (176 B) | `fxsess` (SC40.9) devolvió su knob al stock y saltaba su código de LEDs |
| `build_sc17.use_trimsp()` | `c_spengine`, `c_sppos`, `c_jmpled` (96 B) | con `SPCACHE` el cabezal sale de `c_spcur`; con `SP2` el pad 7 está apagado |
| `fxkeys.use_trimpg()` | `c_pgbtn`, `c_res` (72 B) | `fxres` (SC44.4) devolvió el botón 1-16 / 17-32 al stock |
| `mfbyp.use_trimset()` | `c_mfset` (26 B) | con `HOLD` el toggle nunca mueve el filtro |
| `mutate39.use_trimsl()` | `c_mutbuf`, `c_mutled` (38 B) | `stepmod` (SC40.3) tomó esas ranuras de la vista de probabilidad |

## Qué probar
Lo mismo que SC49.2 (su `PRUEBA.md`); en especial, lo que tocan las opciones: la vista Preset de Synth 1 / 2 (Shift + pads 25-29, la vista de la
fuente), el arpegiador (orden pulsado), la vista Setup y la Sidechain (compresor en K7 / K8), el song pointer de Master FX (pad 7 apagado), el
botón 1-16 / 17-32 y Shift + Octave en la vista FX, Shift + pad 25 (filtro master), la vista de probabilidad (fila 4 de random-mutate).

## Verificación en emulación
Frente a SC49.2, los mismos resultados en `emu_lanex`, `emu_snapall`, `emu_edlock`, `emu_sc45_3`, `emu_arpmods`, `emu_arprate`, `emu_sc32`,
`emu_sc34_2`, `emu_setupfix`, `emu_sc40_3`, `emu_sc39`, `emu_fxres`, `emu_mfhold`, `emu_mfbyp`, `emu_sc40_9` (los fallos de siempre de las
pruebas pensadas para builds antiguas). `emu_sc40_9.py` leía la entrada de `compkn` del manifiesto: ahora, sin `compkn`, el hueco de stock.
