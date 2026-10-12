# SC19.8 — SC19.7 con los knobs de drums según las etiquetas del panel

`circuittracks-4486-SC19.8.syx` — SHA-256 `8182c8a456cf3bb0534da9018885ec370fd63b99ef3dfeb7b8bb6278f1f888eb`
Imagen de 0x5bb80 bytes, CRC 0x7f933d17, marca `SC19.8`.

Los 8 knobs del modo drums siguen las etiquetas impresas del panel. Funciones de stock y nuestras, cada una donde su etiqueta:

| Knob | Etiqueta del panel | Solo | Con Shift |
|---|---|---|---|
| K1 | Oscillator (pitch) | **Pitch** (stock) | cantidad de la envolvente de tono (en la vista cromática, Shift + K1 sigue siendo el sesgo de semitonos de SC11) |
| K2 | Osc mod | frecuencia del ring mod | cantidad del ring mod |
| K3 | Amp envelope | **Decay** (stock) + start point por la izquierda | (stock, como antes) |
| K4 | Filter envelope | envolvente → corte | forma de la envolvente (ataque / caída) |
| K5 | Filter frequency | **EQ / filtro DJ** (stock) | modo de filtro (DJ, paso banda, notch, comb, EQ tilt) |
| K6 | Resonance | resonancia | (libre) |
| K7 | Modulation | cantidad del LFO | velocidad del LFO |
| K8 | FX | **Distorsión** (stock) + bitcrush por la izquierda | (stock, como antes) |

Los LEDs de brillo siguen a cada función (los de stock se mueven con su parámetro; los nuestros enseñan su valor, y con Shift la segunda capa).

## MIDI y proyectos guardados
- Los parámetros de stock (pitch, decay, distorsión, EQ) **conservan su id, su valor guardado y su MIDI**: el knob solo elige con qué macro de stock se llama al manejador de stock. El MIDI sigue el valor del parámetro, no el knob: un CC de pitch sigue moviendo el pitch, y girar K1 manda el CC de pitch. En emulación, cada knob reasignado produce exactamente las mismas escrituras de parámetro (`0x08031A98`) que el knob original de SC19.7.
- Lo que guardan nuestros ajustes va **por función** (envolvente, ring mod, LFO…), no por posición de knob: los proyectos guardados con SC19.4–SC19.7 cargan con los mismos valores.

## Pruebas en el aparato
1. Flashea y enciende: debe arrancar como SC19.7.
2. En un drum, gira cada knob y comprueba que hace lo de la tabla (pitch en K1, decay en K3, EQ / filtro en K5, distorsión en K8 y los nuestros en los demás). Con Shift, la segunda capa.
3. **MIDI:** manda un CC de pitch (o decay, distorsión, EQ) a la pista: debe mover el mismo parámetro que antes, y el LED del knob nuevo debe moverse. Gira K1 y mira (monitor MIDI) que sale el CC de pitch.
4. Un proyecto guardado con SC19.4–SC19.7 (con ajustes de drums) debe cargar igual; guardar / apagar / cargar con este build debe devolver todo.
5. En la vista cromática de un drum: K1 = afinación fina, Shift + K1 = semitonos (como antes).

## Verificación en emulación
`tools/emu_sc19_8.py` por la ruta real de los knobs: cada knob de stock da las mismas escrituras de parámetro que el knob de SC19.7 del mismo parámetro y no toca nuestros bytes; los nuestros solo cambian el byte de su código; los extendidos (start point / bitcrush) cuentan como antes; los LEDs de stock se mueven con su parámetro y los nuestros llevan color + brillo. Los demás tests con las posiciones de SC19.7 traducidas a las nuevas.

## Volver atrás
SC19.7, SC19.6, SC19.5, SC19.4, SC17.7 (confirmada).
