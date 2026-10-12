# SC20.1 — escala en tres filas, Pitch como sesgo en la vista cromática y Clear en los knobs de drums

`circuittracks-4486-SC20.1.syx` — SHA-256 `62a692f244a67a8133379af94a17f27c2b1e5d0aa9d0bee4e4c9fb0de9f1e15e`
Imagen de 0x5d13c bytes, CRC 0x1926a8d8, marca `SC20.1`. Es SC20 + cuatro cambios; si falla, vuelve a SC20 (`firmware/sc20/`) o a SC19.9, y la última versión segura confirmada es SC17.7.

## Qué cambia
1. **Vista Preset de drums, modo escala (Shift + Preset con una escala distinta de Cromática):** solo las **tres filas de abajo** suenan y se iluminan; la fila de arriba (pads 1-8) queda apagada y sin acción (antes repetía siempre el tono máximo). El modo **cromático** sigue igual: dos tiras de piano con sus teclas negras (las cuatro filas).
2. **Knob 1 (Oscillator / pitch) en la vista cromática:** suma un **sesgo** al tono de todos los pads (pasos de 1; no sigue la escala). La suma pads + sesgo se limita a 0..127 (por debajo de 0 el tono es 0, por encima de 127 es 127). **Shift + K1** pasa a ser la **afinación fina en cents** (antes era al revés). Fuera de la vista cromática, K1 es el pitch normal.
3. **Clear en los knobs nuevos de drums** (Clear + girar, como en el original):
   - los knobs **de stock** (K1 pitch, K3 decay, K5 filtro / EQ, K8 distorsión) hacen lo de siempre (mantén Clear y gira ~40 pasos: izquierda = borra la automatización grabada, rojo; derecha = valor por defecto, azul) y ahora **su LED rojo / azul sale en el knob correcto**;
   - los knobs **nuestros** (K2, K4, K6, K7 y las capas con Shift, incluido el tipo de distorsión de Shift + K8): **derecha = valor por defecto** al instante y LED azul; **izquierda = LED rojo**, sin cambiar nada (no tienen automatización grabada que borrar). El color se queda mientras Clear está pulsado.

4. **Master FX, pad 7 (salto de paso) en amarillo** (brillante 0x2D / tenue 0x2E, de la tabla RGB) en lugar de blanco; el pad 8 y el resto no cambian. (El parpadeo del pad 7 con el blanco tenue 0x03 no se ha podido explicar con el código: es el único pad con ese código; si con el amarillo desaparece, era el color.)
5. **Song pointer, el pad brillante:** era el *cabezal* (el paso que suena). `c_sppos` decidía «el transporte corre» con un almacén del motor (`[motor + 0x28]`) que en el aparato no es el de Play, de modo que con el secuenciador parado el cabezal se quedaba fijo en un paso que dependía del contador de ticks (y por tanto de la escena). Ahora usa el almacén que alterna el botón Play (`0x20011034`): el cabezal solo se ve **mientras suena**, y parado todos los pasos quedan tenues (salvo los marcadores de inicio / fin).
6. **Estado del VCF validado:** el estado de SC20 en los ajustes globales lleva ahora una firma (byte +50 de la cola = 0xA5); si no está (bytes de basura o 0xFF, o el estado que dejó SC20), se reinicia a los valores por defecto con ambos modos apagados en vez de leerse como «modo encendido». Al flashear SC20.1 sobre SC20 el modo VCF de las dos pistas vuelve a estar apagado.

## Pruebas en el aparato (con un proyecto de prueba)
1. Flashea y enciende: debe arrancar como SC20 / SC19.9.
2. Drum 1 → Shift + Preset (modo cromático/escala) → elige una escala de 7 notas en Scales: la fila superior (pads 1-8) apagada y muda; las otras tres tocan tonos distintos, sin repetición. Con la escala **Cromática**: cuatro filas (dos tiras).
3. En la vista cromática: gira K1 → todas las notas suben / bajan juntas (sesgo); intenta subir y bajar mucho: sin errores, el tono mínimo es el mínimo. Shift + K1: afinación fina. Apaga el modo cromático: K1 vuelve a ser el pitch normal.
4. Mantén **Clear** y gira K2 a la derecha: vuelve al valor por defecto y el LED se pone azul; a la izquierda: rojo, sin cambios. Suelta Clear: los LEDs vuelven a la normalidad. Repite con K4, K6, K7, con Shift y con Shift + K8 (tipo de distorsión).
5. Mantén Clear y gira K1 (o K3 / K5 / K8) unos 40 pasos: rojo y automatización borrada (izquierda) / azul y valor por defecto (derecha), en el knob que giras.
