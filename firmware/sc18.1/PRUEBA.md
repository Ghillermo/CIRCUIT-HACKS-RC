# SC18.1 — knobs de drums rehechos, pad 7 «saltar» y pad 8 que también quita el song pointer

`circuittracks-4486-SC18.1.syx` — SHA-256 `45e0278bef804688b473557d114337dd0b8db34894f21ef8d4a829a1498fa4ad`
Imagen de 0x5add8 bytes, CRC 0xd327aa6d, marca `SC18.1`.

Es **SC18** con estos cambios (SC18 se puede seguir generando igual).

## 1. Knobs de los drums (con un drum seleccionado)

| Knob | Sin Shift | Con Shift |
|---|---|---|
| **K1** | **Envolvente**: izquierda = ataque más lento (hasta 250 ms); derecha = caída más larga (de 40 ms a ~1,5 s) | **cantidad de envolvente → tono** (lo que era K1 en SC18, ±24 semitonos) |
| K2 | Pitch (stock) | como antes |
| **K3** | **Ring mod: frecuencia** (30 Hz – 7 kHz) | **Ring mod: cantidad** (0 = apagado) |
| K4 | Decay; más allá de 0 a la izquierda = start point (como SC18) | — |
| K5 | LFO: derecha trémolo, izquierda vibrato (como SC18) | velocidad del LFO |
| K6 | Distortion; más allá de 0 a la izquierda = bitcrush (como SC18) | — |
| **K7** | Envolvente → filtro (como SC18) | **modo de filtro**: cada giro cambia de modo (derecha = siguiente, izquierda = anterior) |
| K8 | Frecuencia del filtro (en el modo elegido) | resonancia (en comb: realimentación) |

**Modos de filtro (Shift + K7)**, en este orden (vuelve a empezar al llegar al final):
1. **DJ** (al encender): K8 en el centro = sin filtro; izquierda paso bajo; derecha paso alto.
2. **Paso banda**: K8 recorre la frecuencia.
3. **Notch**: elimina una banda; K8 recorre la frecuencia.
4. **Comb**: filtro de peine (tono metálico de 190 Hz a 8 kHz); K8 = frecuencia, Shift + K8 = realimentación.
5. **EQ tilt de stock**: K8 vuelve a ser el EQ original.

- K7 (envolvente → filtro) mueve la frecuencia en los cuatro primeros modos.
- La envolvente de K1 es la misma para el tono (Shift + K1) y para el filtro (K7).
- El hold/gate de SC18 desaparece.
- Al encender, todo lo nuevo empieza apagado: envolvente en el centro, ring mod sin cantidad, modo DJ. No se guarda con el proyecto (K8 sí, porque es el valor del EQ).
- No hay indicación de en qué modo de filtro estás. Si la necesitas, dime dónde la quieres ver.

## 2. Vista cromática / de escala de los drums
Las filas 1 y 2 (que no hacían nada) se apagan. Las filas 3 y 4 siguen igual.

## 3. Master FX: pad 7 = saltar (song pointer)
- **Mantener el pad 7** activa el modo salto mientras lo mantienes. **Shift + pad 7** lo deja fijo (otra vez Shift + pad 7, lo quita). El pad 7 se ilumina mientras está activo.
- Con el modo salto activo, **tocar un paso** del song pointer (pads 9–24) hace que la reproducción salte a ese paso **en el siguiente paso**. No cambia el inicio ni el final del bucle.
- Si hay un bucle activo, el salto ocurre una vez y el bucle sigue.

## 4. Master FX: el pad 8 también quita el song pointer
Además de apagar los efectos retenidos, el pad 8:
- quita el inicio y el final del song pointer, los pasos mantenidos y el modo salto;
- se ilumina también si hay un bucle del song pointer puesto.

## Cómo está hecho
- **DSP** (`tools/drums2_dsp.py`):
  - bloques de 64 palabras en X:$3A80 + 64·d;
  - buffers de comb de 256 muestras en X:$3400 + 256·d (direccionamiento módulo 256);
  - envolvente AD con tablas de ataque y caída;
  - ring mod con oscilador de cuadratura;
  - SVF con salidas LP / HP / paso banda / notch;
  - fuera del modo EQ tilt, el valor suavizado del EQ se guarda y se pone a 0 mientras suena la voz (`dctl`), y se restaura en `dstage`. El EQ de stock queda plano sin parchearlo.
  - El programa llega a P:$3313.
- **ARM:**
  - nuevo mapa de knobs (`drums18.MAP2`);
  - envolvente de LEDs para la vista cromática (slot 7 → `c_dleds18`);
  - `build_sc17.use_jump()` / `CLEAR_SP` (estado en los bytes 177–178 del bloque de Master FX, que estaban libres).
  - La reserva de RAM no crece.

## Verificación en emulación
- `emu_sc18_1_dsp.py`:
  - etapas exactas al bit: ring mod, bitcrush, los 4 SVF, comb con su buffer circular (sin salirse de los 256 de cada drum) y trémolo;
  - buzón códigos 1–9 y rueda de modos;
  - envolvente con ataque y caída;
  - selección de modo de filtro y guardado/restauración del EQ;
  - disparo;
  - núcleo completo: con todo encendido en 4 drums (comb), +4300 instrucciones por bloque sobre SC18 apagado;
  - pila igual que SC18;
  - memoria nueva solo en los bloques y buffers.
- `emu_sc18_1.py`:
  - pad 7: momentáneo, fijo y LED;
  - salto en el siguiente paso, en ciclos posteriores, al paso 1 y dentro de un bucle;
  - pad 8 limpia el song pointer;
  - filas 1–2 apagadas en los 4 drums.
- `emu_sc18.py` con el mapa nuevo (knobs de los 4 drums por el controlador real, envío al DSP).
- Batería completa: pasa entera también sobre SC18.2 (que incluye SC18.1).

## Pruebas en el aparato
1. Envía SC18.1.
2. **Vista cromática de un drum:** las filas 1–2 deben estar apagadas.
3. **K1** a la izquierda / derecha con **Shift + K1** subido: el ataque o la caída de la bajada de tono cambian.
4. **Shift + K3** subido y **K3**: ring mod.
5. **Shift + K7**: cambia de modo. Prueba **K8** en cada modo, y **Shift + K8** en comb.
6. **Master FX:** mantén el **pad 7** y toca pasos mientras suena; luego **Shift + pad 7** y toca pasos sin mantener nada.
7. **Pad 8** con un bucle del song pointer puesto: debe quitarlo.

## Volver atrás
Envía SC18 o SC17.8.
