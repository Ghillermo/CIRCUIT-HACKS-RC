# SC17.4 — SC17.3 con los LEDs de los knobs correctos en Master FX

`circuittracks-4486-SC17.4.syx` — SHA-256 `61a0ac62170399a3aa0537cda6cd75dce2b4d0510007c6f395a3222f66a788eb`
Imagen de 0x58fb8 bytes, CRC 0x27ebb953, marca `SC17.4`.

## Qué cambia respecto a SC17.3
En Master FX, el knob 5 se veía magenta. El firmware lee **42 LEDs** de la vista activa:
- 0–31: los pads;
- 32–33: dos botones;
- 34–41: los 8 knobs.

El búfer de Master FX solo tenía 32, así que los knobs mostraban lo que hubiera después en la RAM.

Ahora, en Master FX:
- **knobs 1–4** se encienden con el color del efecto seleccionado (con **Digitise**, solo 1–2, que son sus parámetros);
- **knobs 5–8**: apagados (en Master FX no hacen nada);
- los dos botones que también salen de la vista se ven igual que en el Mixer.

Todo lo demás es igual que en SC17.3:
- Mixer → Mixer = Master FX;
- entrada de línea v2.

Nota sobre la entrada de línea (observada en el aparato): los pads 26 y 27 llevan la señal **invertida** y los pads 28 y 29 la **sin invertir**, al revés que en el código (pendiente de confirmar). Este modo tampoco puede tomar el delay ni la reverb como entrada externa.

## Memoria
El bloque de Master FX pasa de 128 a 148 bytes. La reserva total bajo el heap pasa de 176 a 196 bytes. El aparato mostró 240 bytes libres con SC17D, así que quedan 44.

## Verificación en emulación
- `emu_sc17.py`: todo pasa. Incluye la tarea de LEDs de stock completa (`0x08034196`, 69 LEDs del panel):
  - pads desde Master FX;
  - LEDs 51/52 iguales a los del Mixer;
  - knobs 1–4 con el color del Gater y 5–8 apagados;
  - con Digitise, solo los knobs 1–2.
- `emu_sc17_core.py` (DSP de núcleo completo) y `emu_sc15.py` (5 modos, ganancia 2): todo pasa.
- SC17–SC17.3 y SC17D se siguen generando idénticos.

## Pruebas en el aparato
1. Envía SC17.4.
2. Mixer → Mixer. Los knobs 1–4 se ven en el color del efecto seleccionado (el Gater al principio) y los knobs 5–8 apagados.
3. Shift + pad 4 (Digitise): solo los knobs 1–2 encendidos.
4. Mixer: vuelven los colores normales de los knobs del Mixer.

## Volver atrás
Envía SC17.3.
