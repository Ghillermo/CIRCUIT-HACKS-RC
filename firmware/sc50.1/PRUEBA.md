# SC50.1 = SC50 + octavas nuevas del random-mutate + la resonancia en Octave

| SHA-256 del `.syx` | Marca |
|---|---|
| `87624c3c495db898dd7b9581dfae3d5488ba71e73d4c548e260159ed1a850278` | `SC50.1` |

## Qué cambia

- **Random-mutate, pads 21-24:** 21 / 22 una octava arriba, probabilidad baja / alta (×1 / ×2); 23 / 24 una octava arriba o abajo, baja / alta. En los drums, +8 y ±8. Ningún pad baja solo.
- **Vista FX, Shift + Octave:** el brillo de los Octave enseña la resonancia del filtro master, como las octavas del original: Octave ▼ brillante en la mitad alta, tenue en la baja, apagado en 0; Octave ▲ al revés, apagado en 127. Sigue en amarillo: no hay amarillo fijo intermedio.

## Qué probar

1. Synth 1, Pattern Settings, pad 25, un paso con nota, pad 21 y ×8 (Octave): la mitad de las veces sube una octava, nunca baja.
2. Pad 22 a ×8: todas suben. Pad 23 a ×8: la mitad cambia, arriba o abajo. Pad 24 a ×8: todas cambian, arriba o abajo.
3. Un drum, los mismos pads: el sample va a la fila siguiente (21 / 22) o a una fila más o menos (23 / 24).
4. Vista FX, Shift pulsado: con la resonancia a 0, Octave ▼ apagado y ▲ brillante. Súbela con Shift + Octave ▲: a partir de 64, ▼ brillante y ▲ tenue; en 127, ▲ apagado.
5. Sin Shift: Octave en crema / melocotón, los colores de sus páginas.

## El sesgo hacia arriba a ×8

No es un fallo del sorteo. 600 notas con el generador real en el reproductor emulado, pad 24 a ×8: 296 arriba, 304 abajo; pad 23: 144 / 148 y 308 sin cambio. El generador modelado da 50 % con cualquier cadencia. A ×8 el pad 24 cambia todas las notas: la nota del paso no suena nunca y el oído toma la de abajo como base. Queda en la guía. Si en el aparato sigue saliendo claramente desigual con el pad 24, es que hay algo que la emulación no ve.

## Pruebas en emulación

`emu_mutate2.py` (el modelo con las octavas nuevas, y arriba / abajo con el generador real), `emu_fxres.py` (los tres niveles; su última comprobación compara con SC44.3 y falla igual en SC50).
