# SC23 — SC22.4 + editor de CC de los macros MIDI en el propio aparato

`circuittracks-4486-SC23.syx` — SHA-256 `7061be260ae7445a142f7333c266d1d59d49f78312fdb555ceb95468ebe3b788`
Imagen de 0x5e4cc bytes, marca `SC23`. Es SC22.4 con el pad 25 de la vista Preset de MIDI 1 / 2 convertido en el editor de las asignaciones de CC de las plantillas MIDI (lo que hasta ahora solo se hacía desde Components). Si falla, vuelve a SC22.4.

## Cómo se usa
1. MIDI 1 (o MIDI 2) → botón **Preset** (la vista de las plantillas). Pad **25** (el de la izquierda de la fila de abajo, **magenta**): enciende / apaga el **modo edición de CC** de esa pista.
2. Con el modo encendido, **tocar un knob** lo selecciona y muestra **su CC** en la plantilla activa: el número se dibuja **con los 32 pads**, con los mismos dígitos que el display del tempo. **Girarlo** cambia el valor (0-127, en vivo: ya manda el CC nuevo). El primer toque solo selecciona.
3. El **botón de la propia pista** (MIDI 1 para la pista MIDI 1, MIDI 2 para la 2) avanza **CC → inicio del rango → fin del rango → guardar**. Solo hacia delante. Cada campo tiene su color: CC / MSB magenta, LSB rosa, inicio naranja (su LSB amarillo), fin azul claro (su LSB aguamarina). Tras el último campo se **guarda** la plantilla en el aparato y se deselecciona el knob (puedes tocar otro).
4. **NRPN / RPN** (caso especial): el parámetro tiene 14 bits, así que se edita en dos partes: **MSB** y **LSB** (0-127 cada una), y después el rango. Si el valor del macro es de **14 bits** (NRPN / RPN de 14 bits), el inicio y el fin también van en dos partes (MSB, LSB): seis campos en total; con valor de 7 bits son cuatro (MSB, LSB, inicio, fin); con CC, tres.
5. Los pads **1-8** siguen eligiendo la plantilla (al pulsar uno se suelta la selección del knob, el modo sigue encendido: editas la plantilla elegida). Salir: pad 25 otra vez, o cualquier otro botón de vista (Synth, MIDI de la otra pista, Drum, Preset…). Record, Play, Shift, etc. no salen.
6. Si cambias un campo y sales sin llegar al final, **se guarda al avanzar de campo, al cambiar de knob o al salir**.

Los CC de un macro que Components dejó **desactivado** (registro de tipo 0) no se pueden editar. Sin el modo edición, todo es de stock (el botón de la pista sigue alternando Preset / pista).

## Fila de abajo de la vista Preset (como en SC22.4)
| Pad | Función |
|---|---|
| 25 | **modo edición de CC** (magenta) |
| 26 | patch flip |
| 27 | oscilador ON/OFF (verde) |
| 28 | OSC edit (verde) |
| 29 | VCA-VCF (naranja) |

## Prueba
1. Preset de MIDI 1 → pad 25 magenta brillante → toca el knob 1: debe salir un **1** (CC 1 por defecto) en los pads. Gíralo: cambia el número y, saliendo a la vista de la pista, el knob manda el CC nuevo.
2. Botón MIDI 1: aparece el inicio del rango (0, naranja); gira; botón: fin (127, azul); botón: guardado, los pads vuelven a lo de siempre.
3. Apaga y enciende el aparato: la asignación sigue (se guarda como las plantillas de Components). Comprueba en Components que la plantilla tiene el CC / rango nuevos.
4. Con una plantilla NRPN (créala en Components): MSB, LSB, inicio, fin.
5. Prueba también con MIDI 2.

## Notas técnicas
- `vcf21.use_cced()` (`CCED`): estado volátil en los 4 bytes libres de la cola de los ajustes (`+71` bit 7 activo, bit 6 knob seleccionado, bits 3-5 campo, bits 0-2 knob; `+72` bit 0 pista, bit 1 cambiado; `+73 / +74` mitad baja de la vista Preset), borrado al encender.
- Plantillas: 8 × 0x78 B (cabecera de 0x28 B + 8 registros de 10 B: tipo, —, flags, —, parámetro u16, inicio u16, fin u16) en el array `[[SETOBJ − 4] + 0xC]`; la plantilla activa se lee de la referencia `[vista + 0x14]` (como el pad de stock), el cambio se aplica **re-eligiendo la plantilla por el router `[vista + 0xC]`** (reconstruye los descriptores del emisor, el mismo camino que usa el pad de stock) y se guarda con `0x08031320` (almacén persistente, clave `0x1F + índice`). Tipos de registro (byte 0): 1 = CC, 2 = NRPN con valor de 14 bits, 3 = RPN de 14 bits, 4 = NRPN de 7 bits, 5 = RPN de 7 bits.
- Dibujo: el de la vista Tempo de stock (glifos de 3 × 4 de la tabla en `0x08050DB8`; centenas en 2 columnas, decenas en las columnas 2-4, unidades en 5-7 de las 8 de cada fila de pads); lo repinto en `c_vleds` (gancho de la vista Preset) con su propia rutina.
- Botones: `c_vbtn` delante de `c_bentry` (SC19.1) en `0x08033320`.
- Pruebas: `tools/emu_sc23_ed.py` (el editor por las rutas reales: pad, knobs, botón de la pista; CC, NRPN de 7 y de 14 bits, guardado, salida, MIDI 2, arranque) y `tools/emu_sc23.py` (la batería de SC22.4 con el pad 25 ocupado).
- **Limitaciones conocidas:** el guardado de las plantillas ocurre desde el hilo de la interfaz (como el guardado de los ajustes); si la cola del almacén estuviera llena esperaría a que la vacíe su tarea. Los rangos de inicio / fin de 14 bits se editan por mitades (no hay sitio para cinco dígitos).
