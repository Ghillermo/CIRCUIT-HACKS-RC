# SC46.2 / Beta 3.19 = SC46.1 / Beta 3.18 + el modo General MIDI de los drums

`firmware/sc46.2/circuittracks-4486-SC46.2.syx` — SHA-256 `4f4a88dfd2fa82801eddd8bb18f7fc3b2668649dadd432d1821ec1d391408e23`, marca `SC46.2`.
`firmware/b3.19/circuittracks-4486-B3.19.syx` — SHA-256 `ef865a26940b8612430e0e0036e4fe84221f25d9a3daccdaa9b661bdb19908a4`, marca `B3.19` (**Beta 3.19**, el mismo código).

**Modo General MIDI de los drums** (`tools/gmdrum.py`, en la zona libre; función nueva: solo beta; el usuario, 2026-10-24: «New function on Beta for General MIDI with a toggle on setup memory/setup view. An user selected value per drum Channel (ranging 35 to 81) sets the target note. Whenever that Channel triggers, a noteOn is sent with said value instead of the stock pitch» · «El envío del modo GM es en el canal asignado a los drums» · «El usuario necesita una forma de ver el noteon destino, usa los números si hay sitio … cada vez que se cambia tiene que poder oírse» · «usa K4-8 (knobs sobre las pistas de drums) y Shift o salida de Setup para confirmar»).

En la vista **Setup** (no en Advanced Setup), cuyos knobs el stock no usa:
- **K4** = el modo: a la derecha encendido (LED verde), a la izquierda apagado (tenue). Se guarda al momento.
- **K5-K8** (los knobs sobre las pistas de drums) = la nota GM de Drum 1-4: 35-81, dos clics por nota; de fábrica 36 / 38 / 42 / 46 (bombo, caja, charles cerrado, charles abierto). **Cada nota nueva suena** una vez (note-on y note-off, velocity 100) por el canal de drums, y **su número se dibuja en los 32 pads** en el color del drum (la fuente del tempo de stock, como el editor de CC). **Shift** o **salir de Setup** lo confirma: se pide el guardado de los ajustes y vuelven los pads de Setup. Mientras se ve el número, los pads de Setup no hacen nada.
- LEDs: K5-K8 en el color de cada drum, más brillantes cuanto más alta la nota (tenues con el modo apagado); K4 verde / tenue.

Encendido, **cada note-on de Drum 1-4 que el aparato manda por MIDI** (notas 60 / 62 / 64 / 65 por el canal de drums del Setup, 10 de fábrica) sale con su nota GM; su note-off, con la nota con la que empezó (cambiar la nota o apagar el modo no deja notas colgadas). El sonido interno no cambia. Se guarda en los ajustes del aparato (bytes 1-3 de los parámetros 4-7, que nadie usa; firma `0xC9`), por el guardado aplazado de `lazysave` (con el transporte parado).

## Qué probar
1. Un módulo / plugin GM en la salida MIDI (USB o DIN), escuchando el canal 10. Setup: K4 a la derecha (verde). Play con un patrón de drums: suenan bombo / caja / charles en el módulo.
2. K5 un poco: en el módulo suena la nota nueva y en los pads se ve su número en el color de Drum 1. Tocar un pad de Setup mientras tanto: no pasa nada. **Shift**: vuelven los pads de Setup.
3. K8, y salir de Setup sin Shift: al volver, los pads normales. Apagar y encender: el modo y las notas siguen.
4. K4 a la izquierda: los drums salen otra vez con 60 / 62 / 64 / 65.
5. Cambiar el canal de drums en el Setup de stock: el modo GM sale por el canal nuevo.
6. Lo de SC46.1 / Beta 3.18 sigue igual.

## Verificación en emulación
- `emu_gmdrum.py` frente a SC46.1: por el controlador (knobs, pads), la tarea de LEDs real y las entradas del transmisor (pista 16): sin firma, las notas de stock; K4 = firma, banderas y notas de fábrica en las dos copias del almacén y el guardado pedido; 36 / 38 / 42 / 46, el note-off con la nota GM; K5 una nota = 37 suena una vez, su número en los pads (= `c_ednum` en el color de Drum 1), sin guardado aún; un pad de Setup no llega a su manejador; Shift = confirmado; K8 y salir de Setup = lo mismo; límites 35 / 81; el note-off de una nota que sonaba antes del cambio; K1-K3 y Advanced Setup nada; K4 a la izquierda = apagado. SC46.1: los knobs de Setup no cambian nada.
- `emu_pgmch.py`, `emu_lazysave.py`: los mismos fallos que SC46.1 (las cabezas posteriores de la ranura 0 de Setup / el pad 27 de `modesel`). `emu_projsyn.py`, `emu_sc46_1.py`, `emu_fmeng.py`, `emu_p4ovl.py`: bien.
