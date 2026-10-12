# SC14.2 — SC14 corregido: flag de retorno de FX fuera de la tabla de voces del DSP

`circuittracks-4486-SC14.2.syx` — SHA-256 `3da5085d9db7492b697239a66cfa2a40b0859cbd1ac925610ee42c3c7413b86a`
Imagen de 0x4DEB0 bytes, CRC 0x2CAD20F1, marca `SC14.2`.

Hace lo mismo que SC14 (todo lo de SC02–SC12 sin SC13, más Master FX). Solo cambia dónde se guarda en el DSP el flag de "retorno de FX por las tiras 3/4" (SC10).

## El fallo
- SC10, SC11, SC12 y SC14 guardaban ese flag en **X:$EC** de la memoria del DSP.
- X:$EB–$15A es la **tabla de voces** del DSP: 14 entradas que dicen qué rutina ejecuta cada voz y dónde guarda su estado. X:$EC es el puntero de estado de la **voz 0 del Synth 1** ($1960).
- Cada vez que el ARM envía el grupo Audio In (al cargar un proyecto, tocar el nivel o el pan de las tiras 3/4 o pulsar los pads 22/23 de Setup), ese puntero pasaba a valer 0–3. La voz 0 del Synth 1 trabajaba entonces sobre memoria equivocada (X:$0–$B, zona de trabajo del DSP).
- En emulación, tras un Note On cambian el estado de la voz 0 y las posiciones de wavetable que pide al núcleo 1. En el aparato no se ha notado nada raro, así que el efecto audible es pequeño o poco frecuente. Aun así es un fallo real.
- Esto también explica el bucle de reinicio de SC13: ponía su flag en X:$EB (la dirección de la rutina de la voz 0) y borraba X:$EB–$10F al arrancar.

## El arreglo
- El flag pasa a **X:$3A00**, dentro de X:$3339–$3BFF:
  - en una emulación completa del núcleo 0 (init, todos los grupos de parámetros, acordes en los dos sintes, drums, note-offs y 72 bloques de audio) esa zona no se lee ni se escribe;
  - el ARM nunca escribe ahí;
  - ninguna instrucción del DSP la referencia directamente ni carga un puntero base a menos de 0x100 palabras (`tools/dsp_free_scan.py`).
- Cambios respecto a SC14:
  - 4 operandos en el código DSP de SC10 (P:$83, $88, $A0, $B4: `$EC` → `$3A00`);
  - en el ARM, el `movs r2,#0xEC` de `c_h9` pasa a `movw r2,#0x3A00`, y el resto del código de SC10 se desplaza 2 bytes;
  - la marca.

## Verificación en emulación
- `emu_sc14_2.py`, sobre el núcleo completo del DSP:
  - SC14 pisa X:$EC, y el estado de la voz 0 difiere de stock (referencia);
  - con SC14.2, la tabla de voces, X:$0–$3F, el estado de la voz 0 y la lista de lecturas al núcleo 1 son **idénticos a stock**;
  - el grupo Audio In escribe solo X:$3A00 (flags 0–3), y la tabla de voces queda intacta.
- SC10 ARM y DSP (con el flag en $3A00), SC14 ARM (25) y SC14 DSP pasan.
- Regresiones SC04, SC06, SC08, SC09, SC11 y SC12: mismo resultado exacto que SC14.
- SC10, SC11, SC12 y SC14 se siguen generando idénticos byte a byte.

## Pruebas en el aparato (volumen bajo)
1. Envía SC14.2 con el cargador. Comprueba que **arranca bien**.
2. Repite lo básico de SC14: Master FX en la fila 4 de la vista FX (Gater y Auto-Filter).
3. **Retorno de FX por las tiras 3/4** (Setup, pads 22/23): activa el retorno de reverb por la tira 3 y el de delay por la tira 4, y comprueba que funcionan igual que antes.
4. Toca acordes y notas sueltas en el Synth 1 con los pads 22/23 activados y desactivados: todo debe sonar normal.
5. Si algo falla al arrancar: Scales + Preset + Note y envía SC14.

## Volver atrás
Envía SC14 (o SC12) con el cargador.
