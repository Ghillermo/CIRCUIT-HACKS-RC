# SC51.9 = SC51.8 + la envolvente de pitch en el pad 3, violeta

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc51.9/circuittracks-4486-SC51.9.syx` | `4fd33b2ce7bf631153cb4f2074965d3936fe8d5359f6b74fa99f24ba1c291758` | `SC51.9` |

**Qué cambia** respecto a la 5.21 (el usuario, 2026-11-05: «why is pad 17 yellow?» → «put it on pad 3, purple (fm) color»): la **envolvente de pitch del FM pasa del pad 17 al pad 3**, en el violeta del FM (tenue; brillante mientras la editas). Desde cualquier página de knobs, el pad 3 abre la página FM con la envolvente de pitch elegida. El pad 17 queda apagado como los 18-24. Todo lo demás, como la 5.21.

**Usar con una copia de la tarjeta.**

## Qué probar
1. MIDI 1 con FM: el pad 3 en violeta tenue en cualquier página; tócalo: página FM, pad 3 brillante, K1 = transposición, K5-K8 = R1-R4 de la envolvente de pitch.
2. En la página FM, pads 17-24 apagados; tocar el 17 no hace nada.
3. Un operador (pads 9-16): el pad 3 vuelve a tenue.
4. Lo de la 5.21 (`firmware/b5.21/PRUEBA.md`).

## Verificación en emulación
`emu_fm8.py`, `emu_fm8v2.py` (pad 3 / pad 17): ALL PASS.
