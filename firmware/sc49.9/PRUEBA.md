# SC49.9 / Beta 5.2 = SC49.8 + Jankó rediseñado

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc49.9/circuittracks-4486-SC49.9.syx` | `0687b724fe2496a34105119f1b6b021b49feca5ad8945e0d77a7337f970a3218` | `SC49.9` |
| `firmware/b5.2/circuittracks-4486-B5.2.syx` (**Beta 5.2**) | `abf375c63988caa297ac9641c805710e59db342f8d4dca11cd8958d68c8b18d0` | `B5.2` |

El usuario (2026-11-01): «Rediseña el modo Janko. Descarta el antiguo y quédate solo con el nuevo»; «Descarta pad 24 (solo pad 8). Por defecto repite sin octava, pero al mantener pulsada una nota y pulsar el botón de octave up/down (sube o baja medio tono) sólo se suben o bajan las dos filas a las que no pertenece la nota pulsada». La Beta 5.2 incluye la 5.1, que no se publicó.

## Qué cambia
- **Una sola disposición** (`janko.use_v3()`, solo beta): Shift + pad 8 en el editor de la escala propia. Filas por parejas: la de encima medio tono más grave, + 2 por columna; la pareja de arriba repite la de abajo. El pad 24 ya no hace nada. Un proyecto guardado con B_ON 2 o 3 abre con esta.
- **Octave con una tecla mantenida**, en la Note ampliada: solo se mueve la pareja a la que no pertenece la tecla, medio tono; mantenido 400 ms, una octava desde donde estaba. Con teclas en las dos parejas no se mueve nada.
- Sin teclas mantenidas, en la vista Note y en la pantalla de acordes, Octave mueve las dos parejas, como antes.
- Decisiones mías: en la vista Note (2 filas) la pareja de arriba no se ve, así que Octave mueve las dos; igual en la pantalla de acordes, donde las filas 1-2 no son teclas; el Octave largo con tecla mantenida mueve una octava esa pareja.
- La distancia entre parejas no se guarda (como el medio tono de Octave).
- Imagen `0X6FB28` (**1240 B libres**), zona libre 26 B; DSP sin cambios.

## Qué probar
1. Shift + Scales, Shift + pad 8: pad 8 en cian. Note dos veces: filas 3-4 B / C..., filas 1-2 iguales; la tónica con su color en las dos parejas.
2. Tocar una nota de la fila 4 y, sin soltarla, Octave ▲: las filas 1-2 suben medio tono, las 3-4 no; la nota sigue sonando.
3. Lo mismo con una nota de la fila 1 y Octave ▼: bajan las filas 3-4.
4. Mantener también Octave casi medio segundo: esa pareja, una octava.
5. Una nota en cada pareja + Octave: nada.
6. Sin notas: Octave mueve las cuatro filas.
7. Las notas que suenan se iluminan en sus dos pads si están en las dos parejas.

## Verificación en emulación
`emu_janko3.py` (editor, disposición, enlaces y color de la tónica, Octave con y sin teclas mantenidas, pulsación larga, Note de 2 filas, pantalla de acordes, B_ON 2, apagado). `emu_sc46_3.py`: sus comprobaciones de Jankó esperan las disposiciones anteriores (ya no valen desde SC48.2); las de acordes pasan.
