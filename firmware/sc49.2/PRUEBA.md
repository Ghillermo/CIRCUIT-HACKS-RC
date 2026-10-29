# SC49.2 / Beta 3.47 = SC49.1 + el carril extra de los drums (fase 1)

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc49.2/circuittracks-4486-SC49.2.syx` | `02f91b095b69173392bacbdfdce40980678ac841760c7fd018fa60febb4d5afc` | `SC49.2` |
| `firmware/b3.47/circuittracks-4486-B3.47.syx` (**Beta 3.47**) | `3d7a40708935233470a2586abef75502a56b5e2c887c4b14d2ebb398d0ae65bf` | `B3.47` |

El usuario (2026-10-28 / 29): «is there any way to find more drum lanes?» → «B: study hidden bits first»; «Assignable per drum»; «Record held +
knob»; «Chromatic pitch» de fábrica; el indicador «While Record is held». La Beta 3.47 incluye las 3.44, 3.45 y 3.46 (no se publicaron).
La fase 2 (state locks: todos los knobs de un drum en un paso, rampas, la vista de automatización de drums fijada) va en una build posterior.

## Qué cambia (`tools/lanex.py`: la parte a en la zona libre, la parte b al final de la imagen)
- **Un carril de automatización más por drum**, en los bits que el original no usa en cada paso de su patrón: probabilidad bits 3-7 y
  micropasos bits 6-7 (7 bits: 0 = nada, si no el valor + 1). Viaja con el patrón (Duplicate, Nudge, Shift + Play, copiar un patrón).
- **De fábrica lleva el pitch cromático:** los pads de la vista cromática graban ahí (ya no en el carril de pitch, que queda para K1). Lo
  grabado antes en el carril de pitch sigue sonando y gana si un paso tiene las dos cosas.
- **Record mantenido + un knob** le asigna ese parámetro: K2 (frecuencia del ring mod), K4 (envolvente → corte), K6 (resonancia), K7 (cantidad
  del LFO), Shift + K1 (envolvente de tono), Shift + K2 (cantidad del ring mod), Shift + K4 (forma de la envolvente), Shift + K7 (velocidad del
  LFO). **Record mantenido + un pad de la vista cromática** = otra vez el pitch cromático. El giro / el pad no cambian nada más y Record queda
  como estaba.
- **Mientras mantienes Record** en las vistas del drum, el knob asignado se ve **blanco**; con el pitch cromático, **Preset parpadea** en blanco.
- **Grabando** (Record + Play), girar el knob asignado escribe el paso que suena (un valor por paso). **Clear + ese knob a la izquierda** borra el
  carril en el patrón que suena (el pitch cromático: Clear + K1).
- **La foto** (Record mantenido + paso en la vista Note del drum) incluye el valor del carril si no está en su valor por defecto.
- Qué lleva cada drum se guarda con el proyecto (la cola del registro + 357, con firma); los valores, con el patrón.
- Para que los bits sobrevivan: el original compara la probabilidad entera al decidir si suena un paso y la dibuja entera en la vista de
  probabilidad (las dos, arregladas en su sitio, sin código nuevo); añadir o quitar un golpe (vista Note, vista de probabilidad), un sample flip
  en un paso vacío y los pads de la vista de probabilidad escribían el byte entero (ahora conservan los bits); `drumarp` (el arpegio grabado) y
  `quant` (Shift + Play) también (opciones `use_keepbits`). Clear + paso los borra, como borra los carriles del paso.

## Qué probar
1. Drum 1, vista cromática: con Record + Play, toca pads: en el siguiente ciclo el pitch sigue los pasos grabados; K1 grabado a la vez también.
2. Mantén Record y gira K6: suelta Record (sigue como estaba); mantén Record otra vez: K6 se ve blanco. Graba girando K6 con Play: la
   resonancia sigue lo grabado paso a paso. Clear + K6 a la izquierda: se borra.
3. Mantén Record y toca un pad de la vista cromática: vuelve al pitch cromático (Preset parpadea mientras mantienes Record).
4. Con un carril grabado: Duplicate del patrón, Nudge, Shift + Play: el carril va con los pasos. Añade / quita golpes, cambia la probabilidad,
   un sample flip en un paso vacío: el carril no cambia. Clear + paso: se borra ese paso.
5. La probabilidad de los pasos (vista de probabilidad) se ve y suena como antes con un carril grabado.
6. Guarda el proyecto, apaga, carga: la asignación y el carril vuelven.

## Verificación en emulación
`emu_lanex.py` frente a SC49.1: ALL PASS (en SC49.1 todos los aleatorios suenan con los bits puestos y añadir un golpe los pierde). Las pruebas de
drums frente a SC49.1 dan lo mismo salvo la grabación cromática de `emu_sc43_7.py`, que espera el carril de pitch (ahora va al carril extra).
