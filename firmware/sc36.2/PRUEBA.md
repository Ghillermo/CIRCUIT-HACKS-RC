# SC36.2 — knobs del secuenciador de efectos que recorren toda la fila inferior

`circuittracks-4486-SC36.2.syx` — SHA-256 `b99b505115c4db3e9a81d7dd1db32722ccc7827f7e7c7cf39af1182a5547de4b`
Imagen de 0x64848 bytes, CRC 0xb0e5252d, marca `SC36.2`.

Es SC36.1 con un arreglo que pediste: en el aparato, el knob de un par del secuenciador de efectos solo pasaba de «nada» al pad 31.

**Causa:** un giro del knob manda muchos eventos, y SC36.1 avanzaba un valor por evento: llegaba al tope (pad 31) o a 0 al instante. Además, un par vacío empezaba en el centro y el primer evento lo llevaba al pad 31.

**Ahora:**
- Cada par guarda una posición fina: hacen falta **unos 16 pasos del knob por valor**. Recorrer 0 → 6 lleva más o menos lo que 0 → 96 en un knob normal.
- El valor es el más cercano: 0 = nada, 1-6 = pads 26-31 de Master FX (el 31 es el Glitch).
- El LED del knob toma el **color del efecto** de ese hueco a brillo máximo. Apagado = nada; blanco tenue = hueco vacío.
- Un par vacío empieza en 0 (nada).
- Los pares guardados con SC36.1 (valores 0-6) se leen como «nada»: vuelve a elegirlos.

Todo lo demás es igual que en SC36.1: sigue su [PRUEBA.md](../sc36.1/PRUEBA.md).

## Qué probar
1. En Master FX, asigna efectos a los pads 26-30 (mantén el efecto de arriba y toca el de abajo).
2. MIDI 1: lleva el pad 27 a azul (secuenciador de efectos), abre el pad 30 y pon notas con Shift + pad.
3. Gira despacio el knob de un par: el LED pasa por **apagado → color del pad 26 → … → color del pad 30 → turquesa (pad 31)**, un color cada poco giro. Al revés vuelve a apagado.
4. Dale a Play: en cada paso con nota suena el efecto del hueco elegido, con su copia de parámetros.
5. Dime si la velocidad del knob es cómoda (se ajusta con `FSQ_U` en `tools/vcf21.py`).
