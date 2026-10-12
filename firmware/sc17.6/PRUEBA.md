# SC17.6 — fila inferior de FX en la vista Master FX y huecos asignables

`circuittracks-4486-SC17.6.syx` — SHA-256 `78f6a9ac340fd106eb4133efcc0bc5de9f7738c5b74a6a0bd8fe59142c497c19`
Imagen de 0x595c0 bytes, CRC 0x269ee907, marca `SC17.6`.

Es **SC17.5** (delay y reverb como fuente del sinte, Octave ▲/▼ en la vista FX) más lo siguiente. **Ojo:** en SC17.5 el reset de la vista FX era el botón 1-16/17-32; aquí pasa a ser el botón **Duplicate** (ver más abajo). Clear queda como está.

## Uso
### Vista FX: Duplicate = reset y botón 1-16 / 17-32 = resonancia del filtro master
Solo con la vista **FX** abierta (en las demás vistas estos botones hacen lo de siempre):

| Botón | Qué hace |
|---|---|
| **Duplicate** | **reset de efectos**: los 16 envíos (delay y reverb de las 8 pistas) a 0, filtro master al centro (64, la resonancia no se toca) y Master FX apagado (pads mantenidos y fijos del Gater y el Auto-Filter de la vista FX y de la vista Master FX). La función de stock de Duplicate se sigue ejecutando después. Con **Shift + Duplicate** no hay reset (queda el stock). **Clear no se toca.** |
| **1-16 / 17-32** | **resonancia del filtro master + 32** en cada pulsación: 0 → 32 → 64 → 96 → 127 → 0. (Desde otro valor sube de 32 en 32 hasta el máximo 127; en 127 vuelve a 0.) |

- Octave ▲ / ▼ siguen eligiendo los envíos de delay / reverb en los knobs (como en SC17.5).
- Clear sigue como en stock (según el código, Clear + girar un knob lleva ese envío a su valor por defecto). Duplicate no hace nada en la vista FX, así que está libre para el reset; si en el aparato resulta que sí hace algo, dímelo.

### La fila inferior también en la vista Master FX
En la vista **Master FX** (Mixer → Mixer), la fila 4 (pads 25–32) es la misma que en la vista FX:

| Pad | Función |
|---|---|
| 25 | «reverb y delay off» (la función de stock de ese pad) |
| 26–29 | Gater 1/4, 1/8, 1/16, 1/32 |
| 30, 31 | Auto-Filter LP y HP, 1 compás |
| 32 | Auto-Filter LP 1/8 |

- Mantener = activo mientras lo mantienes; Shift + pad = fijo. Los LEDs son los de la vista FX.
- Los pads 1–6 siguen siendo Gater, Auto-Filter LP, Auto-Filter HP, Digitise, Phaser y Vinyl, con sus knobs como antes.
- En el Mixer normal, los pads siguen siendo los silencios.

### Asignar un FX de arriba a un pad de abajo
**Mantén un FX de la fila de arriba (pads 1–6) y pulsa un pad de la fila de abajo (26–32), o al revés.**
- El pad de abajo pasa a ser ese efecto, **con su modo** (por ejemplo Auto-Filter LP o HP) **y una copia de sus 4 parámetros** (los knobs 1–4 de ese momento).
- El gesto solo asigna: no activa el efecto de arriba ni el de abajo por su cuenta.
- Al pulsar después un pad asignado:
  - los parámetros guardados se cargan en el efecto (los del pad de arriba cambian a esos valores);
  - el efecto queda seleccionado (los knobs 1–4 lo editan en la vista Master FX);
  - se activa mientras lo mantienes; Shift + pad = fijo / suelto, como arriba.
- El LED del pad asignado tiene el color del efecto (brillante activo, tenue en reposo).
- Funciona igual en la vista **FX** y en la **Master FX**. El gesto de asignar solo se puede hacer en la Master FX (es donde están los dos pads).
- Con Shift pulsado no se asigna (Shift + pad = fijo).
- No se guarda: al encender vuelven los 7 efectos originales. Se puede reasignar un pad las veces que quieras.
- El efecto asignado usa el mismo motor que el de la fila de arriba, así que **un efecto de arriba y uno de abajo del mismo tipo comparten el DSP**: el último que pulses es el que cargó los parámetros. Auto-Filter LP y HP comparten parámetros, como ya pasaba.

## Aviso de memoria
El estado nuevo (7 huecos × 4 bytes + 1) hace crecer la reserva de RAM bajo el heap de **196 a 220 bytes**. El aparato mostró **240 libres** con SC17D, así que quedan unos **20 bytes de margen** (con SC17.5 eran 44). Si el aparato se cuelga al arrancar o al abrir alguna vista nueva, vuelve a SC17.5 y dímelo.

## Cómo está hecho
- Todo en `tools/build_sc17.py` con la opción `use_slots()`, que no cambia ninguno de los builds anteriores (se siguen generando idénticos).
- Vista Master FX (vtable del Mixer, slots 0, 1 y 7): los pads 25–32 se pasan a los manejadores de la vista FX; los LEDs 25–32 se copian de los de la vista FX.
- Vista FX (vtable 0x0805A6E0, slots 0, 1 y 7): nuevos manejadores que, si el pad es un hueco asignado, cargan los parámetros y activan el efecto; si no, llaman a los de SC14.
- Hueco `j` = 4 bytes en el bloque de Master FX: parámetro `i` en los bits 0–6 del byte `i`, y el efecto (0–5, el pad de arriba) en el bit 7 de los bytes 0–2; el bit 7 del byte 3 = asignado.
- Un hueco mantenido activa su efecto mediante `c_slotbits`, que el tick de Master FX suma a los pads mantenidos y fijos. Si ninguna de las dos vistas está abierta, se sueltan solos.

## Verificación en emulación
- `emu_sc17_6.py`, por la ruta real del controlador:
  - pad 26 en Master FX = Gater SC14 (sin silencio, sin pad de Master FX), pad 25 = el manejador de stock, Shift + pad = fijo, LEDs 25–32 = los de la vista FX (también por la tarea de LEDs de stock);
  - en el Mixer normal, los pads siguen siendo el silencio de stock;
  - mantener arriba + pulsar abajo y al revés: hueco = efecto + copia de los parámetros, sin efecto parado ni colgado; con Shift no asigna;
  - pulsar un hueco: restaura los parámetros, selecciona el efecto, y el tick manda FX_ON y los parámetros de la copia (Gater y Digitise); soltar lo apaga; Shift + hueco lo fija;
  - en la vista FX el hueco mantenido no se suelta con el tick; un pad sin asignar sigue siendo el efecto SC14; los LEDs del hueco (brillante / tenue); al salir de las dos vistas se suelta;
  - reserva: bloque de 180 bytes, termina justo en el tope del heap de stock.
- `emu_sc17.py` (con el LED de la fila inferior), `emu_sc17_5.py`, `emu_sc17_core.py`, `emu_sc17_5_dsp.py`: pasan. SC17.5 y todos los anteriores se siguen generando idénticos.

## Pruebas en el aparato
1. Envía SC17.6. Comprueba que arranca y que el Mixer, Master FX, FX, el Preset y la entrada de línea siguen como en SC17.5.
   - Vista FX: mueve varios envíos y activa un FX fijo (Shift + pad) → **Duplicate**: envíos a 0, FX apagados, filtro master al centro. Comprueba que Clear sigue haciendo lo de siempre.
   - Vista FX: **1-16 / 17-32** varias veces: la resonancia del filtro master sube 0 → 32 → 64 → 96 → 127 → 0 (se nota con el filtro master movido del centro).
   - Si Duplicate o 1-16/17-32 no son los botones que esperabas, dímelo (los ids están en `tools/fxkeys.py`).
2. Mixer → Mixer (Master FX): la fila 4 tiene la misma luz que en la vista FX. Mantén un pad 26–32: el efecto SC14 suena igual que en la vista FX. El pad 25 apaga / enciende el delay y la reverb como en la vista FX.
3. Ajusta el Gater con los knobs, mantén el pad 1 y pulsa el pad 28: el pad 28 pasa a tener el color del Gater. Cambia el Gater con los knobs. Pulsa el pad 28: el Gater vuelve a sonar con los parámetros de antes.
4. Lo mismo con el Auto-Filter HP (pad 3) en otro pad, y con el orden inverso (pad de abajo primero).
5. Pulsa un pad asignado en la vista FX: debe sonar igual.
6. Apaga y enciende: vuelven los efectos originales.

## Volver atrás
Envía SC17.5 (o SC17.4).
