# Alpha 7.10 (marca `A7.10`) — pendiente de probar, sin publicar

= Alpha 7.09 + `tools/laneclr.py` (el usuario, 2026-11-19: «Clear knob clears lane» → «Clear, all patterns. All 8 patterns keep the knob assignations on the whole track»): **liberar un hueco de la página 4 (knobs secuenciables) del sinte propio de MIDI 1 / 2 con Duplicate + knob borra también su carril de automatización en los 8 patrones de la pista** (los 32 pasos, `0xFF`); las asignaciones de knobs son de la pista entera. Antes el carril liberado guardaba sus valores (sin sonar, `vcf21.use_freeslot`) y movía el destino siguiente que se diera a ese hueco. Los knobs no secuenciables (Shift + pad 4) no tienen carril: liberarlos solo los libera.

`c_lcfree` sustituye el `movs r1, #0; strb r1, [r0, r5]` de p4dest (el hueco liberado): escribe el 0 y, en la página 4, el carril k de los 8 patrones (`[c_sdrec(t) + 0x48] + 0xCA8 p + 0x3A8 + 192 k`, 192 B) a `0xFF`; después avisa al almacén del editor de la pista (`0x08035456` + commit) para que las vistas lo vean. 96 B en el hueco de `dspz`, delante de `outline`. Imagen `0x6fc18`.

## Probar
MIDI 1 con el sinte propio: graba automatización de un knob de la página 4 (pad 1) en dos patrones.
1. En la página 4, Duplicate + ese knob: el hueco queda libre (LED apagado).
2. Los dos patrones: su carril vacío (la vista Velocity con Shift ya no lo marca amarillo).
3. Duplicate + un knob de otra página: va a ese hueco y no suena ninguna automatización vieja.

Pruebas: `emu_laneclr.py` (la 7.09 falla dos), `emu_p4dup.py`.
