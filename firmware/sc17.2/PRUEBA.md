# SC17.2 — SC17.1 con la vista Master FX en **Shift + Mixer**

`circuittracks-4486-SC17.2.syx` — SHA-256 `41ceb8a62c4d8f07fe24af4028760b00ae88e5cd3c148fea1af5b9c7ede1dea5`
Imagen de 0x58eec bytes, CRC 0x2ff60902, marca `SC17.2`.

En SC17 y SC17.1, pulsar Mixer otra vez estando en Mixer no hacía nada en el aparato (en emulación sí funcionaba; la causa no está identificada). SC17.2 cambia solo la forma de entrar, y ya no hay "conmutar":

| Botón | Resultado |
|---|---|
| **Mixer** | Mixer normal, siempre. También sirve para salir de Master FX. |
| **Shift + Mixer** | Abre el Mixer igual que stock y activa Master FX. Desde cualquier vista. Si lo pulsas otra vez, sigues en Master FX. |

Todo lo demás es igual que en SC17.1: Master FX con sus knobs, y la entrada de línea ×2 con los modos invertidos (Shift + pads 25–29 en Preset).

La función de stock de Shift + Mixer (conmuta el store 0x20039DE0, sin efecto visible) ya no se puede usar.

## Cómo está hecho
- `c_mixbtn` (gancho 0x0803354C, el caso del botón 13):
  - **sin Shift:** borra el modo Master FX y sigue por el camino de stock;
  - **con Shift:** activa el modo Master FX y salta a la selección de vista de stock (`0x0803390C(ctrl, id de Mixer, 13)`, la misma llamada que hace el botón Mixer).
- El modo se escribe antes del cambio de vista, porque el cambio puede hacer esperas cortas (vaciado de stores).
- El DSP es idéntico a SC17.1.

## Verificación en emulación
- `emu_sc17.py` (ARM, todo pasa):
  - Mixer, otra vez Mixer: sigue en el Mixer normal;
  - Shift + Mixer: Master FX en el objeto del Mixer, sin llamar a la función de stock;
  - desde la vista FX, Shift + Mixer entra directamente en Master FX;
  - el controlador queda exactamente igual que tras una pulsación de Mixer de stock;
  - pads, latch, knobs, LEDs y ticks de LFO, igual que en SC17.
- `emu_sc17_core.py` (DSP de núcleo completo) y `emu_sc15.py` (5 modos, ganancia 2): todo pasa.
- SC17 y SC17.1 se siguen generando idénticos.

## Pruebas en el aparato
1. Envía SC17.2. Comprueba que el Mixer normal y la entrada de línea funcionan como en SC17.1.
2. Desde cualquier vista, **mantén Shift y pulsa Mixer**. Deberías ver la vista Master FX: pads 1–6 de la fila 1 encendidos tenues en colores distintos.
3. Mantén el pad 1: Gater mientras lo mantienes. Shift + pad 5: Phaser fijo. Gira los knobs 1–4 para cambiar el efecto seleccionado.
4. Pulsa **Mixer** sin Shift: vuelves al Mixer normal (pad 1 vuelve a silenciar el Synth 1). Los efectos fijados siguen sonando.
5. Si Shift + Mixer tampoco abre Master FX, dímelo, y también si el LED o la vista cambian de alguna forma.

## Volver atrás
Envía SC17.1 o SC16.1 con el cargador.
