# Alpha 7.07 (marca `A7.07`) — pendiente de probar, sin publicar

= Alpha 7.06 + **sitio en la flash** (el usuario, 2026-11-18: «Make more flash room»): `tools/outline.py` + la opción `thumb.OUTLINE` del ensamblador (con `COMPACT`). Nada cambia en el uso.

Las secuencias de llamada más repetidas del código propio pasan a ser un `bl` a una rutina compartida:
- las lecturas de un parámetro de stock, `movs r1, #k; bl 0x0803542C; [ldrb r0, [r0]]` (6-8 B → 4 B); con solo el prefijo la rutina es una llamada de cola (`movs r1, #k; b.w`), sin pila;
- las llamadas a ocho getters propios cortos seguidas de `cmp r0, #0` (`c_shift`, `c_von`, `c_gst`, `c_gfst`, `c_edact`, `c_gact`, `c_vdbit`, `c_mh`; 6 B → 4 B); la rutina hace `push {lr}; bl; cmp; pop {pc}` (4 B más de pila mientras corre el getter, que no llama a nada de stock por debajo).

505 llamadas en 19 rutinas. **Flash libre: de 94 B (7.06) a 1 318 B** (final de la imagen 1 212 B, huecos de `dspz` 81 + 3 B, `hole` 22 B).

Fuera del plegado: el código parcheado dentro de funciones de stock (solo el código añadido tras la imagen de stock y el `hole`), la cueva de SC03 (`jumpseq` reutiliza `c_txf` en una dirección fija), las cabezas `KEEP` / `NOPOOL` del ensamblador y `dpitch.c_dppad` (`chromfix` busca sus bytes). Mientras se construye, las llamadas plegadas van a direcciones de marcador en la zona del bootloader; el último módulo de la build escribe las rutinas y las apunta (ninguna llamada queda en esa zona: comprobado).

## Probar
Todo como en la 7.06 (un uso normal: proyectos, sintes propios, drums, Master FX, cadenas, morph, Setup).

Pruebas: 73 pruebas de emulación sobre la 7.07 y la 7.06: los mismos resultados (las que fallan, igual en las dos: pruebas antiguas); `emu_morph.py` espera ahora la vista Note tras Shift + MIDI 1 en la vista del morph (el arreglo de Shift + pista de la 7.06).
