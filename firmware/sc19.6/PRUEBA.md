# SC19.6 — SC19.5 con los knobs nuevos de drums que muestran su valor con el brillo

`circuittracks-4486-SC19.6.syx` — SHA-256 `fff8606e64f8443b7d16b61d55e16a0f4b47c4f8da2a481c9d3b63cccba83841`
Imagen de 0x5ba64 bytes, CRC 0x7a4a0f67, marca `SC19.6`.

Es **SC19.5** (SC19.4 + retornos de FX del Setup en la entrada del sinte; ver `firmware/sc19.5/PRUEBA.md`) **más** lo que pediste: los knobs K1 / K3 / K5 / K7 de los drums enseñan su valor con el brillo del LED, como los originales (K2 / K4 / K6 / K8).

## Qué hace
- En la vista del drum, el LED de K1 / K3 / K5 / K7 va con el color del drum y un brillo según el valor guardado:
  - **K1** envolvente (bipolar): apagado en el centro, más brillo cuanto más lejos; **K3** frecuencia del ring mod (unipolar): más brillo = más valor; **K5** cantidad del LFO (bipolar); **K7** envolvente → corte (bipolar).
  - **Con Shift pulsado** muestran la segunda capa: K1 envolvente → tono (bipolar), K3 cantidad del ring mod (unipolar), K5 velocidad del LFO (bipolar), K7 modo del filtro (5 niveles: DJ / paso banda / notch / comb / EQ tilt = apagado … máximo).
  - El brillo mínimo es el de stock (~10 %), y en el modo tenue de stock sale la mitad, igual que los otros knobs.
- Cómo: el conversor de colores de stock (`0x0803423C`) enciende los LEDs de knob con un código «dinámico» escalado por el valor de un parámetro de stock; nuestros knobs no tienen parámetro de stock, así que el brillo viaja en el byte alto del código del LED y el bucle de knobs del conversor lo recoge (`persist19.KNOB_LEVELS`). Ver `docs/NOTAS.md`.

## Pruebas en el aparato
1. Flashea y enciende: debe arrancar como SC19.5.
2. Elige un drum y gira K1, K3, K5, K7: el LED debe **cambiar de brillo mientras giras**, igual que K2 / K4 / K6 / K8; con Shift pulsado, los cuatro enseñan la segunda capa (si al pulsar / soltar Shift no cambia hasta que giras el knob, anótalo).
3. Los bipolares (K1, K5, K7 sin Shift; K1, K5 con Shift) deben estar casi apagados en el centro y brillar hacia los dos lados; K3 crece de izquierda a derecha.
4. Cambia de drum (1–4): cada uno con su color y sus valores. Cambia de sesión / carga un proyecto: el brillo debe corresponder a los valores cargados.
5. Todo lo de SC19.5 (retornos del Setup en el sinte; guardado / carga / proyecto nuevo).

## Verificación en emulación
`tools/emu_sc19_6.py`: la imagen difiere de SC19.5 solo en el gancho del conversor, el slot 7 del manejador de macros, los tres punteros de la vista de la fuente (el código se desplaza) y la marca; con valores guardados distintos en los 4 drums, con y sin Shift, el LED de K1 / K3 / K5 / K7 = color del drum + brillo del modelo y los otros 61 LEDs igual que SC19.5; pasado por el conversor de stock real el color es el del drum escalado como lo hace stock con un knob dinámico (**K3 = 100 queda exactamente igual que el K2 de stock = 100**, también en el modo tenue); los 69 colores de las vistas de Synth 1 / 2, MIDI 1 / 2, Mixer, FX y arranque son los de SC19.5.

## Volver atrás
SC19.5 (sin brillo en los knobs nuevos), SC19.4, SC17.7 (confirmada).
