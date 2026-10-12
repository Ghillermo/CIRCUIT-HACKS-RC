# SC14 — Master FX: Gater y Auto-Filter — plan de prueba

`circuittracks-4486-SC14.syx` — SHA-256 `4b7281a4a9e4326cdb18b3462ff28b5b26a3c738beef915c0651fc8e7df448ab`
Imagen de 0x4DEB0 bytes, CRC 0x022C55A5, marca `SC14`.

Se basa en **SC12**, no en SC13: no incluye el sidechain de drums.

## Qué hace
En la **vista FX** (botón FX), la **fila 4** tiene efectos de actuación sobre el master, como los Master FX de Circuit Rhythm:

| Pad de la fila 4 | Efecto | Color |
|---|---|---|
| 1 | (función de stock, sin cambios) | |
| 2 | Gater 1/4 | color del drum 1 |
| 3 | Gater 1/8 | color del drum 1 |
| 4 | Gater 1/16 | color del drum 1 |
| 5 | Gater 1/32 | color del drum 1 |
| 6 | Auto-Filter paso bajo, 1 compás | color del Synth 2 |
| 7 | Auto-Filter paso alto, 1 compás | color del Synth 2 |
| 8 | Auto-Filter paso bajo, 1/8 (wobble) | color del Synth 2 |

- **Mantener el pad:** el efecto suena mientras lo mantienes. **Shift + pad:** queda fijado (latch); repite Shift + pad para quitarlo.
- **Gater:** corta el volumen del master a ritmo con el tempo del proyecto. Empieza abierto en el momento de pulsar y no se sincroniza con la reproducción, como en Rhythm.
- **Auto-Filter:** mueve el filtro master con una onda triangular. Empieza abierto, se cierra hasta el extremo a mitad del ciclo y vuelve a abrirse.
- Puede haber a la vez un Gater y un Auto-Filter. Dentro de cada tipo gana el último pad que pulses; si lo sueltas con otro mantenido, pasa al otro.
- Al soltar, el volumen y el filtro master vuelven exactamente a donde estaban.
- No se guarda nada.

## Cómo está hecho
**ARM:**
- El bucle principal llama al servicio del DSP en `0x080213AA`. Ahí se calcula el LFO a partir del contador de ms (0x2000081C) y del tempo del proyecto, y se escriben dos parámetros, solo cuando cambian:
  - X:$DE: ganancia de salida master (proyecto 0x21, índice 7);
  - X:$CF: posición del filtro master (0x21, índice 0).
- Vista FX: pads, soltado y LEDs mediante los slots 0, 1 y 7 de la vtable 0x0805A6E0.
- Estado (24 bytes) en lo más alto del heap. La primera vez se rebaja el límite del allocator (0x20044E58 → 0x20044E38), así que el firmware nunca puede asignar esa zona.
  - El heap solo se usa para crear tareas al arrancar y tenía 240 bytes libres.
  - Si el heap ya llegara tan arriba, el Master FX se desactiva solo.
  - **No se usa la zona de pila que probablemente rompió SC13.**

**DSP:**
- Un único cambio: en una instrucción que ya existe (P:$21D9), la rampa de la ganancia master pasa de unos 43 ms a unos 2 ms.
- No hay código nuevo en el DSP y no se toca ningún vector.

## Verificación en emulación
**ARM**, 25 comprobaciones:
- Reserva del heap y desactivación automática si no hay sitio.
- Filas 1-3 y el pad 1 de la fila 4 sin cambios respecto a stock.
- Gater 1/16 a 94 BPM: abierto 79 ms y cerrado 79 ms; X:$DE solo se escribe en los cambios.
- Soltar restaura la ganancia. "Gana el último pulsado" y la vuelta al pad que sigue mantenido funcionan. El latch funciona.
- Auto-Filter LP de 1 compás: 64 → 36 → 8 → 36 → 64. HP sube hasta 120. El pad 8 toma el relevo.
- Gater y Auto-Filter a la vez. Al soltarlo todo, ambos se restauran.

**DSP:**
- Con ganancia constante, la salida es idéntica a stock, con y sin compresor.
- Al cerrar el gate, en 1 bloque queda al 50 % (stock: 98 %) y en unos 5 ms al 1,6 %.

**Regresiones:** SC12, SC10 (ARM y DSP), SC09, SC06, SC05 y SC04 pasan.

**Fallos conocidos que cambian a propósito:**
- SC11: el Pitch del modo cromático va en cents desde SC12;
- SC08: el constructor;
- SC07: el bit 28.

**Seguridad:** he quitado SC13 de la lista del cargador, así que ya no se puede enviar por error.

## Pruebas en el aparato (volumen bajo)
1. Envía SC14. Antes de nada, comprueba que **arranca bien** y suena igual que SC12.
2. Pon un patrón en marcha y entra en la vista FX.
3. Mantén el **pad 2 de la fila 4** (Gater 1/4): el sonido debe cortarse a negras, abierto media negra y cerrado media negra. Prueba los pads 3, 4 y 5. **Comprueba si el ritmo coincide con el tempo:** si va el doble de rápido o de lento, dímelo.
4. Mantén el **pad 6** (LP 1 compás): el sonido se oscurece y vuelve a abrirse en un compás. El pad 7 hace lo mismo hacia agudos y el pad 8 a corcheas (wobble).
5. **Shift + pad 4:** el gate queda fijado al soltar; Shift + pad 4 otra vez lo quita.
6. Mueve el knob del filtro master con un Auto-Filter activo y después suéltalo. Al soltar el pad debería volver a la posición del knob.
7. Revisa la **vista FX normal**: presets de delay y reverb, y el pad 1 de la fila 4.
8. **Si al arrancar vuelve el bucle de reinicio, recupera con Scales + Preset + Note y SC12.** Dime en qué paso pasó.

## Volver atrás
Envía SC12 con el cargador.
