# S516D (diagnóstico) = SC51.6 + copia de las ondas Nova al PC

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/s516d/circuittracks-4486-S516D.syx` | `5fd9f2de6953fa67254c2202fbd0c8d796c267ea88b285ba4a8afe0f8860f85c` | `S516D` |

Para saber cómo guarda el sinte de stock (Nova) sus ondas: `tools/study_novawaves.py` (emulación) encontró dónde las pide el núcleo 0 (`X:$100000-$41FFFF` del núcleo 1, una zona de ≈ `$28800` palabras por onda); aquí el núcleo 1 copia la zona que pida el PC a `Y:$57C000` y el PC la lee. **Las copias se quedan en `re/novadump/` (fuera de git): son datos del aparato y no se publican.** Sin el Glitch ni el gesto mecánico (sitio en el núcleo 1). Todo lo demás es la Beta 5.19.

## Cómo
1. Instalar S516D. Conectar por USB, cerrar Components / uploader / DAW. Avisar a Claude.
2. Claude: `python tools/novadump.py` (unos minutos).
3. Volver a instalar la Beta 5.19.

## Verificación en emulación
- `emu_s516d.py`: una orden copia la zona a `Y` (en pasos de 256 palabras) y apunta la orden como hecha; la siguiente orden, el tramo siguiente; la misma orden otra vez no copia nada.
