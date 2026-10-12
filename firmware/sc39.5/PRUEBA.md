# SC39.5 — knobs de tipo en colores, blanco tenue fijo

`circuittracks-4486-SC39.5.syx` — SHA-256 `cb37e87e60b3f5e37fe85901819653427902f5fbdd4d5cdd1a1677dbb07ae6d4`
Imagen de 0x68008 bytes, CRC 0x69e40f2e, marca `SC39.5`.

Es SC39.4 con dos cambios de LEDs (solo ARM, nada de sonido):

- **Los knobs que eligen un tipo lo enseñan como color** (con Shift pulsado, que es donde están):

| Knob | Tipos y colores |
|---|---|
| Drums, **Shift + K5** (modo de filtro) | DJ blanco · paso banda amarillo · notch magenta · comb verde azulado · EQ tilt verde |
| Drums, **Shift + K8** (tipo de distorsión) | blanco · amarillo · naranja · rojo |
| Granular, **Shift + K6** (modo de nota) | tono blanco · slicer amarillo · stretch verde azulado |

  Antes eran el color de la pista con más o menos brillo. Los del motor MIDI (tipo de efecto, de filtro, onda, BITSYNC), el modo del sample y la fuente del granular ya eran de colores.
- **El blanco tenue que pulsaba despacio ahora es fijo:** el pad 8 de Master FX cuando no hay nada que apagar y los huecos sin asignar de la fila inferior.

## Qué probar
1. Drum 1: mantén Shift y gira K5 por los cinco modos de filtro: cinco colores distintos. Lo mismo con K8 (cuatro tipos de distorsión).
2. Suelta Shift: los knobs vuelven a su aspecto de siempre. Clear + knob sigue enseñando rojo / azul.
3. MIDI 1 con el motor granular, página 2: mantén Shift y gira K6: tres colores.
4. Master FX: el pad 8 sin efectos fijados y un hueco sin asignar se ven en blanco tenue **sin pulsar**.
5. Di si algún color no se distingue bien: son tres listas de constantes.
6. Todo lo de `firmware/sc39.4/PRUEBA.md`.

## Verificación en emulación
- `emu_sc39_5.py`: los LEDs del fotograma real para los 5 modos de filtro, los 4 tipos de distorsión y los 3 modos de nota; sin Shift, en otra página o con otro motor = SC39.4; fuera del código nuevo la imagen solo cambia el blanco tenue (2 bytes). `emu_sc39_4.py` pasa sobre SC39.5.
- **Sin comprobar en emulación:** los colores reales en el aparato.
