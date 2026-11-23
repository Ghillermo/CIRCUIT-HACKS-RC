# Alpha 7.32 — qué probar

Instalar `circuittracks-4486-A7.32.syx` (modo bootloader: Scales + Preset + Note al encender).

## Synth 1 / 2, vista alternativa (pulsa el botón del sinte otra vez)

1. **Pad 1 (Macros)** en el color del sinte: magenta en Synth 1, verde en Synth 2; brillante en Macros, tenue en las otras páginas.
2. **Clear + knob en Macros** = como el original: a la izquierda borra la automatización de esa macro, a la derecha la pone por defecto. En OSC 1, VCF… Clear + knob no hace nada.
3. **Duplicate + knob en una página de sección** (OSC 1, VCF…):
   - el parámetro va a la primera macro libre o, si no hay, al primer knob de Macros 2;
   - el knob que lo tiene parpadea **blanco** tres veces y el pad 1 parpadea en el color de esa página (sinte = Macros, rosa = Macros 2);
   - si ya estaba en una macro, parpadea esa macro;
   - sin sitio: el knob girado parpadea **naranja**.
4. **Macros 2** (Shift + pad 1): un knob asignado se enciende con su valor; uno libre está apagado.
5. **Pad 1 mantenido + knob** = ese knob libre: en Macros la macro (su primer destino), y si estabas en Macros 2 (o con Shift) el knob extra. El knob parpadea **rojo** y la página queda en Macros / Macros 2.

## MIDI 1 / 2 con el sinte propio

6. En la página de knobs asignados (pad 1): **pad 1 mantenido + knob** = esa ranura libre, parpadea rojo. Con Shift (o en la página no secuenciable) libera la de esa página.
7. **Duplicate + knob** en esas dos páginas ya no libera (no hace nada).
8. **Duplicate + knob en otra página** (OSC 1…) asigna como antes; parpadea en blanco la ranura donde queda, o el knob en naranja si no hay sitio.
9. **Clear + knob**: igual que antes (izquierda borra la automatización, derecha el valor por defecto).

## Si algo falla

Dime en qué paso y qué se ve (qué parpadea o qué no). Si Duplicate + knob no hace parpadear nada, el gesto no está llegando: preparo una build de diagnóstico para leerlo por USB.
