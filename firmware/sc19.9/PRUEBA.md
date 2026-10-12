# SC19.9 — SC19.8 con tipo de distorsión (Shift + FX), brillo por valor en los knobs de Master FX y salto de paso que repite mientras el pad del paso esté pulsado

`circuittracks-4486-SC19.9.syx` — SHA-256 `f3f0009c3f12de8cfba4ce7b82fa946c2f75e43f9bf5ab9bf909a8a6f42151ac`
Imagen de 0x5bee0 bytes, CRC 0x6f22b3c3, marca `SC19.9`.

Es **SC19.8** (knobs según el panel; ver `firmware/sc19.8/PRUEBA.md`) **más** lo siguiente:

| Knob | Etiqueta del panel | Solo | Con Shift |
|---|---|---|---|
| K1 | Oscillator (pitch) | **Pitch** (stock) | cantidad de la envolvente de tono (en la vista cromática, Shift + K1 sigue siendo el sesgo de semitonos de SC11) |
| K2 | Osc mod | frecuencia del ring mod | cantidad del ring mod |
| K3 | Amp envelope | **Decay** (stock) + start point por la izquierda | (stock, como antes) |
| K4 | Filter envelope | envolvente → corte | forma de la envolvente (ataque / caída) |
| K5 | Filter frequency | **EQ / filtro DJ** (stock) | modo de filtro (DJ, paso banda, notch, comb, EQ tilt) |
| K6 | Resonance | resonancia | (libre) |
| K7 | Modulation | cantidad del LFO | velocidad del LFO |
| K8 | FX | **Distorsión** (stock) + bitcrush por la izquierda | **tipo de distorsión**: stock / suave / dura / plegada (un paso por giro, da la vuelta) |

- **Tipo de distorsión (Shift + K8).** Un segundo saturador después de la distorsión de stock, con el mismo mando: el empuje es 1 + 8 × el valor de la distorsión (K8 sola, sin Shift). Tipo 0 = solo la de stock; 1 = suave (cúbica); 2 = dura (recorte); 3 = plegada (ondas que rebotan en ±1). Con la distorsión a 0 los tipos casi no se notan: súbela. Se guarda con el proyecto (bits de reserva del byte 8 de los drums, ver `persist19.XT_BITS`; un proyecto anterior lo lee como 0 = la de stock) y el LED de K8 con Shift enseña el tipo (4 niveles).
- **Pendiente del filtro: descartada** (petición del usuario). El código queda como opción desactivada (`persist19.EXTRAS_SLOPE`, `drums2_dsp.SLOPE_PASS`); Shift + K6 no hace nada.
- **Salto de paso (Master FX, pad 7):** con el pad 7 mantenido o fijado (Shift + pad 7), tocar un paso 1–16 hace que **el siguiente paso que se reproduzca sea ese**, y **mientras ese pad de paso siga pulsado el paso se repite en cada cambio de paso; al soltarlo deja de repetir** y la canción sigue. (En SC19.7 / SC19.8 la repetición dependía del pad 7; ahora depende del pad del paso.) Un toque que acaba antes del cambio de paso salta una sola vez; si pulsas otro paso, ese pasa a ser el objetivo; el pad 8 lo termina. El pad 7 sigue en blanco (tenue / brillante).
- **Master FX: los LEDs de los knobs enseñan el valor del parámetro con el brillo** (como los de los drums): en la vista Master FX, los knobs del efecto elegido (2 o 4 según el efecto) se encienden con el color del efecto y un brillo proporcional a su valor (0–127, del 10 % al 100 %); al girar un knob el brillo cambia. Usa el mismo gancho del conversor de colores que los drums.

## MIDI y proyectos guardados
- Los parámetros de stock (pitch, decay, distorsión, EQ) **conservan su id, su valor guardado y su MIDI**: el knob solo elige con qué macro de stock se llama al manejador de stock. El MIDI sigue el valor del parámetro, no el knob: un CC de pitch sigue moviendo el pitch, y girar K1 manda el CC de pitch. En emulación, cada knob reasignado produce exactamente las mismas escrituras de parámetro (`0x08031A98`) que el knob original de SC19.7.
- Lo que guardan nuestros ajustes va **por función** (envolvente, ring mod, LFO…), no por posición de knob: los proyectos guardados con SC19.4–SC19.7 cargan con los mismos valores.

## Pruebas en el aparato
1. Flashea y enciende: debe arrancar como SC19.8.
2. **Salto de paso:** secuenciador en marcha, vista Master FX. Mantén el pad 7, **mantén** un paso (por ejemplo el 5): ese paso se repite hasta que sueltes el pad del paso (y sigue aunque sueltes el pad 7); al soltarlo, la canción sigue. Haz lo mismo con Shift + pad 7 (fijado). Un toque rápido salta una sola vez.
3. **Shift + K8**: gira paso a paso por los 4 tipos con la distorsión (K8 sola) a un valor medio / alto; el LED de K8 con Shift pasa por 4 niveles de brillo. Tipo 0 = como siempre.
4. **Guardado:** ajusta el tipo de distorsión en dos drums distintos, guarda, apaga, carga: deben volver (también al cambiar de sesión).
5. **Master FX:** elige un efecto y gira sus knobs: el brillo del LED sigue al valor.
6. Anota si algún tipo de distorsión suena mal (volumen, clics) y qué constantes habría que ajustar (`DD.XTRA` en `tools/drums2_dsp.py`).

## Verificación en emulación
- `tools/emu_sc19_9_dsp.py` (núcleo 0 completo con el intérprete DSP): con TYPE = 0 la salida y el bloque son idénticos a SC19.8 en todos los controles de stock; los tres tipos de distorsión coinciden bit a bit con su modelo (distorsión 0, 0,25 y 0,9); `dctl` saca TYPE de los bits 8–9 de EXT sin tocar los nibbles del bitcrush; coste +28 instrucciones por bloque con todo apagado, pila igual.
- `tools/emu_sc19_9.py` (ARM, rutas reales): el tipo (giros, bits solo en su sitio, mensaje del tick, guardar → borrar → cargar, proyecto sin los bits, LED), el salto de paso (repite mientras el pad del paso sigue pulsado, aunque se suelte el pad 7; se para al soltarlo; toque corto, fijado con Shift, segundo paso, pad 8) y los LEDs de Master FX.

## Volver atrás
SC19.8 (sin estos cambios), SC19.7, SC17.7 (confirmada).
