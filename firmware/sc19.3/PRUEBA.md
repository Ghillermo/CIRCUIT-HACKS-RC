# SC19.3 — SC19.1 con el cuelgue al encender arreglado

`circuittracks-4486-SC19.3.syx` — SHA-256 `f2b9dd6540ff9a51ab4a302d05002c3debe627e1391721513c751a54250f8ef9`
Imagen de 0x5b66c bytes, CRC 0x8233da00, marca `SC19.3`.

**Causa del cuelgue (encontrada con SC19.2):** `persist19.c_xm_load` se ejecuta dentro del tick del servicio del DSP y marcaba el grupo Audio In con el `MARK_DIRTY` de stock (`0x0803BDCC`), cuyo primer paso es coger el semáforo del servicio (`0x08021064`: espera mientras la cuenta de `[puntero + 0xC]` es 0). El bucle principal coge ese mismo semáforo alrededor de todo el servicio (`0x0801D5D4` … `0x0801D5DC`), así que el tick esperaba a sí mismo para siempre. SC19.2 se congelaba justo en su etapa A porque ahí corre `c_xm_load`; SC19 / SC19.1 / SC20D, al encender, en cuanto existían los cuatro gestores de drums.

**Arreglo:** el tick llama directamente al marcador de bits sucios (`0x08021FDC(0x20, 48)`), que es lo que hace `MARK_DIRTY` entre coger y soltar el semáforo, sin tocar el semáforo. Es el único cambio respecto a SC19.1 (una llamada en `c_xm_load`).

Todo lo demás es **SC19.1**: drums, asignaciones de Master FX y fuente del sinte guardados en el proyecto; Master FX encendido y song pointer a cero al cargar; resonancia en el botón 1-16/17-32; vista cromática con las 4 filas; conmutador de la fuente con doble pulsación (pads 25–29; los modos 5 / 6 siguen descartados). Mira `firmware/sc19/PRUEBA.md` y `firmware/sc19.1/PRUEBA.md` para el detalle.

## Pruebas en el aparato
1. Flashea SC19.3 y enciende: **debe arrancar con normalidad** (sin congelarse). Si se congela, anota si es al encender o a los cuantos segundos, y vuelve a SC17.7.
2. Comprueba lo básico: vistas de pista, Master FX, vista cromática de drums.
3. Vista de la fuente: Synth 1 dos veces, pad 26 (entrada 1), cierra con Preset.
4. Mueve un knob de los drums (K1 envolvente, Shift + K1…), asigna un FX a la fila inferior de Master FX. **Guarda** el proyecto, apaga del todo, enciende y **carga**: el drum, la asignación y la fuente deben volver como estaban.
5. Proyecto nuevo: drums neutros, huecos vacíos y sintes en noise.

## Verificación en emulación
`tools/emu_sc19_3.py`: en SC19.1 el tick toma el semáforo del servicio durante una carga (el cuelgue), en SC19.3 no lo toma nunca, el grupo Audio In se marca igual y el estado tras la carga es idéntico; el binario solo difiere en la marca y esa llamada. Más `emu_sc19.py` (146 comprobaciones), `emu_sc19_1.py` y el fuzz sobre esta imagen.
La emulación no tomaba el semáforo en serio (no está modelado como bloqueo): por eso el fallo solo apareció en el aparato.

## Volver atrás
SC17.7 (confirmada) o SC183D (diagnóstico que ya has probado).
