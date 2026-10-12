# SC35D6 — DIAGNÓSTICO: primera escritura en la tarjeta (sin cambiar nada)

`circuittracks-4486-SC35D6.syx` — SHA-256 `058093a9f8f0a91363547029deabde89aee11ecd68ab1f3bd0527634ba566f86`
Imagen de 0x5b9e8 bytes, CRC 0x336a907e, marca `SC35D6`.

**No es un build de uso.** Es SC35D5 con una sola cosa más: con **Shift** el pad **escribe** en la tarjeta. Para volver, envía SC34.1 (o SC34.2).

## Qué hace
- **Pads 9-16 sin Shift:** exactamente lo mismo que SC35D5. Leen los samples 0-7 del pack actual: si existe, tamaño y cabecera.
- **Shift + pad 9-16:**
  1. lee los 21 primeros bytes del sample;
  2. **los vuelve a escribir iguales** en el mismo sitio, con la escritura del firmware original (la que usa Components);
  3. vuelve a leer el tamaño y los bytes.

  Si todo va bien, el fichero **no cambia**: mismos bytes y mismo tamaño. Así se comprueba que podemos escribir en la tarjeta y que la escritura no recorta el fichero.

Por lo que he visto en el código, el aparato abre el fichero existente (`00_808.wav`, etc.) y escribe encima sin recortarlo. Aun así es la primera escritura, así que hazla con cuidado.

## Antes de probar
1. **Copia de seguridad de la tarjeta SD** en el ordenador.
2. **Duplica un pack** y selecciónalo. Hazlo con el aparato, o en el ordenador copiando una carpeta de pack con otro número. Prueba **solo en ese pack duplicado**.

## Prueba
1. Envía SC35D6. Carga el pack duplicado.
2. Abre `tools/sc32d1_reader.html` (recárgala si ya la tenías abierta) y pulsa «Permitir MIDI y escuchar», o usa tu monitor MIDI.
3. Pulsa Synth 1 dos veces para abrir la vista de la fuente.
4. Pulsa el **pad 9** sin Shift: lectura como en SC35D5. Apunta el tamaño.
5. Pulsa **Shift + pad 9**. La página reconoce SC35D6 y muestra:
   - el estado de la escritura, que debe ser 0;
   - el tamaño antes y después, que deben ser iguales;
   - la cabecera releída, que debe empezar por `RIFF…WAVEfmt`.

   Mándame el texto.
6. Toca el sample 0 del pack (el pad de un drum que lo use): debe sonar igual que antes.
7. En el ordenador, compara `PCM/00_….wav` del pack duplicado con el de la copia de seguridad: deben ser idénticos.

## Verificación en emulación
`emu_sc35d4.py … --kind 4 --writeback`, con la vía de la tarjeta simulada:
- sin Shift, solo lee;
- con Shift, lee, escribe exactamente los 21 bytes leídos en el offset 0 (de forma síncrona), y vuelve a pedir el tamaño y a leer;
- el volcado tiene las 14 palabras;
- SC35D4 y SC35D5 no escriben ni con Shift.

## Volver atrás
Envía SC34.1 o SC34.2.
