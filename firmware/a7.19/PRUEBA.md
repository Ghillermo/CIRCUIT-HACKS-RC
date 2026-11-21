# Alpha 7.19 (marca `A7.19`) — pendiente de probar, sin publicar

= Alpha 7.18 con **1 052 B más de flash libre** (imagen `0x6fbd4`: 1 068 B libres; la 7.18 tenía 16). Nada cambia en el uso (el usuario,
2026-11-20: «Keep cleaning up unused code, optimizing repeating code and compressing/packing to make more flash room»).

- `packio.use_zloop()` / `xlanes.use_zloop()`: los marcos de petición de la tarjeta puestos a cero con un bucle de 12 B en lugar de un `str` por palabra.
- `vcf21.use_defloop()`: los valores por defecto del sinte propio (primer uso, `c_vreset`, los del segundo oscilador) leídos en bucle de la tabla
  `t_def` (la de Clear + knob) en lugar de un `movs` + `strb` por valor.
- `vcf21.use_fold()`: los LEDs de los knobs con Clear, el primer relleno de las filas de destinos (páginas 4 / 8) y los 16 bytes de estado, en bucles.
- `build_sc17.use_fold()`: las siete pruebas de hueco de `c_slotbits` en un bucle y la cadena de colores de `c_f_leds` como tabla (`thumb.ldr_label`:
  la dirección de una etiqueta desde la reserva de literales).

## Pruebas (emulación)
- `emu_defloop.py`, `emu_fold.py`, `emu_fold2.py`: las rutinas cambiadas, en la 7.18 y la 7.19 desde el mismo estado: los mismos bytes de RAM
  (200 / 100 estados al azar en las de LEDs).
- `emu_sc35.py` (los mismos 4 fallos que la 7.18), `emu_xlanes.py`, `emu_xlfix.py`, `emu_scsave.py`, `emu_gmview.py`, `emu_fxstep.py`.
- `verify_builds`: las anteriores siguen idénticas.

## Probar en el aparato
Uso normal: copiar / intercambiar samples entre packs, Duplicate + patch, borrar packs, guardar el proyecto, Clear + knob del sinte propio,
Clear + MIDI 1 / 2, la vista FX con huecos asignados.
