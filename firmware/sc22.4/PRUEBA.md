# SC22.4 — SC22.3 + colores distintos y nuevo orden de los pads de la vista Preset de MIDI

`circuittracks-4486-SC22.4.syx` — SHA-256 `cc7d7655d246fca9d6baf6ef090f19bf06ed4d7f79211b8cafe75f527e92a5db`
Imagen de 0x5e014 bytes, marca `SC22.4`. Es SC22.3 (oscilador v3) con otro orden y otros colores en la fila de abajo de la vista Preset de MIDI 1 / 2. Si falla, vuelve a SC22.3.

## Fila de abajo de la vista Preset (de izquierda a derecha)
| Pad | Función | Color (encendido / tenue) |
|---|---|---|
| 25 | **libre** (reservado para el modo de edición de CC, que viene en la siguiente build) | apagado |
| 26 | **patch flip** (se ha movido del pad 25 al 26) | los de stock (blanco tenue / azul grisáceo) |
| 27 | **oscilador ON/OFF** (line in ↔ oscilador) | **verde** |
| 28 | **OSC edit**: abre la página B de los knobs | **el mismo verde** |
| 29 | **VCA-VCF** (el modo de siempre) | **naranja** |

(Antes: 25 patch flip, 26 VCA-VCF en azul claro, 27 OSC edit, 28 OSC on/off.) Las funciones y los knobs no cambian; solo la posición y el color de los pads. El resto de la vista Preset (plantillas de los pads 1-8, etc.) es el de siempre.

## Prueba
1. MIDI 1 → Preset: comprueba que el patch flip está en el pad 26, el oscilador ON/OFF en el 27, OSC edit en el 28 y VCA-VCF en el 29, y que los cuatro colores se distinguen (blanco-azulado, verde, verde, naranja).
2. Cada pad hace lo que hacía (patch flip y VCA-VCF se excluyen entre sí; el pad 27 enciende / apaga el oscilador, el 28 cambia los knobs a la página B).
3. El pad 25 no hace nada todavía.
4. MIDI 2 igual.

## Notas técnicas
- `vcf21.use_colors()` (VCA-VCF `0x2B` / `0x2C`, oscilador `0x17` / `0x18`: orden de canales R, G, B = bytes 2, 1, 0 de la tabla, como confirmó el `0x13` azul claro) y `vcf21.use_layout()` (`PAD_FLIP = 25`, `PAD_OSC = 26`, `PAD_PAGE = 27`, `PAD_VCF = 28`; el builder pone `build_sc06.PF_PAD = 25`, que mueve el patch flip de SC06). El resto es SC22.3.
- Pruebas: `tools/emu_sc22_4.py` (la de SC22.3 con los pads y colores nuevos, el orden de los pads y que los colores sean distintos).
