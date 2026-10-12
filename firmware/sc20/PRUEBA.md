# SC20 — VCF / VCA en las entradas de audio de las pistas MIDI

`circuittracks-4486-SC20.syx` — SHA-256 `ca2e993b4588ee2b64932d825b7095f4d62339161170853f543a8e929cdd545c`
Imagen de 0x5cfc0 bytes, CRC 0xd3c8e5cc, marca `SC20`. Es SC19.9 + el modo VCF / VCA; si falla, vuelve a SC19.9 (`firmware/sc19.9/`), y la última versión segura confirmada es SC17.7.

## Qué hace
En la vista **Preset de MIDI 1 / MIDI 2** hay un pad nuevo, el **26** (el de la derecha del patch flip): azul tenue = apagado, **azul brillante = modo VCF / VCA**. Con el modo encendido la **entrada de audio de esa pista** (la entrada de línea 1 / 2 o, si en el Setup el retorno de reverb / delay va a la tira 3 / 4, ese retorno) pasa por:

**VCF bipolar → drive + saturación → VCA (envolvente ADSR por la puerta de la pista, LFO, nivel)** — *antes* de la tira del mixer: el nivel, el pan, los envíos de FX, el sidechain y el volumen principal actúan después. El delay y el reverb reciben la señal ya procesada. Los sintes con la fuente en una entrada externa siguen oyendo la entrada limpia.

- **La puerta de la envolvente son las notas de la pista** (secuenciadas, grabadas o tocadas en vivo con los pads); la pista **sigue enviando su MIDI como siempre**.
- **Patch flip y este modo son excluyentes**: encender uno apaga el otro.
- Con los valores por defecto el modo es un **bypass exacto** (filtro al centro, sin drive, VCA abierto): la señal no cambia hasta que muevas un mando.

## Mandos (los 8 knobs de la pista con el modo encendido; los LEDs enseñan los valores con el brillo, con Shift los de la segunda capa)

| Knob | Solo | Con Shift |
|---|---|---|
| K1 | **Filtro** bipolar: izquierda = paso bajo, derecha = paso alto, centro (±2) = sin filtro | **Drive** (saturación suave, ×1…×17) |
| K2 | **Resonancia** | **Nivel** (127 = ganancia 1; con la puerta, nivel × envolvente) |
| K3 | **Envolvente → filtro** (bipolar) | **Velocidad del LFO** |
| K4 | **LFO → filtro** (bipolar) | **LFO → VCA** (trémolo) |
| K5 | **Ataque** (0 = instantáneo; 4–250 ms) | **Forma del LFO** (triángulo / cuadrada / diente de sierra / sierra inversa) |
| K6 | **Decaimiento** (40 ms – 1,5 s) | **Seguimiento de la nota → corte** (bipolar) |
| K7 | **Sostenido** | **Velocidad de la nota → nivel** |
| K8 | **Relajación** (40 ms – 1,5 s) | **Modo del VCA**: izquierda = abierto (por defecto; la envolvente solo modula el filtro), derecha = **puerta** (la envolvente abre el VCA) |

Valores por defecto: filtro al centro, resonancia 0, envolvente y LFO → filtro 0, ataque 0, decaimiento 40, sostenido 100, relajación 40, drive 0, nivel 127, velocidad del LFO 40, trémolo 0, forma = triángulo, seguimiento 0, velocidad → nivel 0, VCA abierto.

Los valores son **del equipo, no del proyecto** (están en los 75 bytes finales del registro de ajustes globales, que el guardado de stock ya escribe); se guardan al encender / apagar el modo y, limitado a una vez cada 0,7 s, al girar un knob (lo último que muevas justo antes de apagar el aparato puede no guardarse; el modo y el resto se guardan al pulsar el pad).

## Pruebas en el aparato (con un proyecto de prueba, volumen bajo)
1. Flashea y enciende: debe arrancar como SC19.9. Si no arranca, reinicia en modo bootloader y flashea SC19.9.
2. **Toggle:** MIDI 1 → Preset → pad 26: se enciende (azul brillante); otra vez: se apaga. Con el modo encendido pulsa el patch flip: el modo se apaga y el patch flip se enciende; y al revés.
3. **Bypass:** con el modo encendido y sin tocar ningún mando, la entrada (línea 1 en MIDI 1, línea 2 en MIDI 2) debe sonar igual que sin el modo.
4. **VCF:** K1 a la izquierda recorta agudos, a la derecha graves, al centro nada; sube la resonancia (K2) y mueve K1. Con K3 / K4 positivos o negativos el filtro se mueve con la envolvente / el LFO.
5. **VCA con puerta:** Shift + K8 a la derecha: la entrada solo suena mientras tocas notas de esa pista (pads de la pista o el secuenciador); ajusta K5–K8 (ataque, decaimiento, sostenido, relajación). Shift + K2 baja el nivel. Shift + K8 a la izquierda: vuelve a estar abierto.
6. **Drive y LFO:** Shift + K1 (drive), Shift + K3 / K4 (velocidad y profundidad del trémolo), Shift + K5 (forma del LFO).
7. **Retornos del Setup:** con el retorno de reverb (o delay) en la tira 3 (4), el modo de MIDI 1 (2) procesa ese retorno en lugar de la entrada de línea.
8. **MIDI:** la pista sigue mandando sus notas por MIDI (monitor) con el modo encendido.
9. **Guardado:** ajusta valores, apaga y enciende el aparato: el modo y los valores deben volver.
10. Anota qué falla (qué mando, qué entrada, si hay clics o saltos al mover los mandos, o si la puerta llega tarde).

## Cómo está hecho
- **DSP** (`tools/vcf20_dsp.py`, núcleo 0): una «voz» por pista MIDI en X:$3B80 + 48 t. `vpre` (en P:$23C, antes de `premix` de SC10; se acaba con un salto a `premix`, sin aumentar la pila) recoge el buzón, calcula el control de cada voz activa (envolvente por bloques de 0,67 ms con las tablas de los drums, LFO, índice del filtro = FILT + ENVF × ENV + LFOF × LFO + KEY × (nota − 60) / 128, resonancia, ganancia del VCA) y procesa **en el sitio** el anillo de entrada (Y:$FFD, tramas [in1, in2]); `vret` (al final de `fx_cap`, antes de `returns` de SC10) procesa **los retornos** Y:$880 (reverb → MIDI 1) / Y:$9C0 (delay → MIDI 2) de las voces cuya tira los toma (X:$3A00 bit 0 / 1). Cada canal: SVF de Chamberlin (idéntico al de los drums, LP / HP), drive y saturación `y = u + (u − u³) / 2`, VCA con rampa de ganancia por muestra. Los registros se guardan y restauran.
- **ARM** (`tools/vcf20.py`): pad 26 de la vista Preset de MIDI (gancho del pad de SC06; LEDs por el slot 7); slot 4 / 7 del gestor de macros de las pistas (knobs y LEDs de los MIDI con el modo encendido, el resto, de stock); los envoltorios de la vtable de notas cuentan las notas pulsadas y avisan; la cadena del servicio del DSP envía un mensaje por voz y tick (activación, nota, velocidad, puerta, disparo, valores sucios).
- **Estado:** 49 de los 75 bytes finales del registro de ajustes (`0x2003974C + 0x3D`): flags, 2 × 16 valores, bloques volátiles (notas pulsadas, nota, velocidad, bits sucios, etiquetas); «inicializado en esta sesión» = bit 3 del byte 179 del bloque de Master FX. No usa RAM nueva (la reserva sigue en 220 bytes).

## Verificación en emulación
- `tools/emu_sc20_dsp.py` (núcleo 0 completo con el intérprete DSP): voces apagadas = el resto del núcleo exactamente igual; bypass bit a bit con los valores por defecto; ley LP / HP del filtro (índices, tablas, resonancia) y el SVF bit a bit; dos entradas independientes; drive + saturación bit a bit; nivel; ADSR completa de 60 bloques contra el modelo etapa a etapa (y las transiciones decaimiento → sostenido, relajación → reposo); rampa de ganancia; formas del LFO, trémolo, velocidad; el buzón (códigos, tag, otra voz, códigos fuera de rango); los retornos procesados por canal con la cadena de stock detrás; registros restaurados; coste con ambas voces encendidas ≈ +2700 instrucciones por bloque (1,6 % de las ~166 000), apagadas +118; pila 6 (igual que antes).
- `tools/emu_sc20.py` (ARM, rutas reales del controlador): el toggle (LEDs, exclusión con el patch flip), los 16 mandos en sus rangos, los extremos, el almacén de macros de stock intacto, los LEDs, las notas contadas con el MIDI de stock intacto, el primer tick (valores por defecto), un mensaje por voz y tick con etiquetas alternas, y **de punta a punta**: los mensajes de una sesión reproducidos en el programa real del DSP dejan el bloque de la voz igual que los bytes del registro de ajustes.

## Volver atrás
SC19.9, SC19.8, SC19.7, SC17.7 (confirmada).
