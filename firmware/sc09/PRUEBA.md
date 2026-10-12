# SC09 — Pitch de drums en semitonos — plan de prueba

`circuittracks-4486-SC09.syx` — SHA-256 `9a99783b1e2a9de3968cfe6ade395b7f4bc771c1bb4d3c5589e26e615f4afeb6`
Imagen de 0x4D580 bytes, CRC 0x3E4C6142, marca `SC09`.

Incluye todo SC08: canales compartidos, Ch16, loopback interno, patch flip guardado y la vista Preset cromática.

## Por qué
En stock, el Pitch de drums **no va por semitonos**: es un cambio lineal de velocidad de reproducción, con pasos desiguales.
- Va de 0,25× (−24 semitonos) a 1,73× (solo +9,5 semitonos).
- El valor 76, que debería ser una octava, solo sube unos 2,3 semitonos. Por eso los intervalos del modo cromático te salían cortos.

## Qué cambia
- **Cada paso del mando Pitch de drums = 1 semitono exacto.** El 64 sigue siendo el tono original; 76 es una octava arriba y 52 una abajo. El rango llega a unas ±5 octavas.
- Afecta a los 4 drums, al mando, al CC 14/34/46/55 y a la automatización.
- Ahora el **modo cromático** (Shift + Preset) toca la escala correctamente.
- **Proyectos antiguos:** si tenían el Pitch de algún drum movido de 64, sonarán a otra altura. Con el Pitch en 64 no cambia nada.
- Nada más cambia en los drums: decay, distorsión, EQ, nivel y pan se envían igual que en stock.

## Cómo está hecho
- La conversión del Pitch que hace el ARM antes de enviarlo al DSP (`0x0802878C`, usada solo por los 4 drums) pasa a ser una tabla exponencial: palabra = 0x10000 × 2^((v−64)/12).
- Los 4 envíos usan la palabra completa de 24 bits, con más precisión que en stock.
- La voz de drums del DSP ya multiplicaba la velocidad base del sample por ese valor, así que acepta cualquier relación sin tocar el DSP.

## Verificación en emulación
- En los 4 drums, para 13 valores del mando:
  - en stock, la palabra enviada coincide con la fórmula lineal (76 → ×1,14, unos 2,3 semitonos);
  - en SC09 coincide con la tabla de semitonos;
  - el resto de valores enviados son idénticos.
- 64 → ×1; 76 → ×2; 52 → ×½; 88 → ×4.
- Las pruebas de SC08 (modo cromático) y las regresiones de SC07, SC06, SC05 y SC04 pasan sobre SC09.
- El cargador web reconoce el SHA y la transferencia simulada es idéntica al archivo.

## Pruebas en el aparato
1. Envía SC09 con `tools/ct_uploader.html`.
2. En modo cromático, el pad de abajo a la izquierda y el de abajo a la derecha deben sonar a **una octava exacta**. Toca la escala completa: debe sonar a escala menor si el proyecto está en la escala por defecto.
3. Cambia la escala y la tónica en Scales y comprueba que el teclado la sigue.
4. Gira el mando Pitch de un drum en la vista normal: debe subir y bajar por semitonos.
5. **Valores extremos:** muy arriba (más de unas +3 octavas), el DSP podría saturar la velocidad y algunos samples podrían cortarse o sonar raros. Dime si notas algo.

## Volver atrás
Envía SC08 (o anterior) con el cargador. Si no arrancara, enciende con Scales + Preset + Note.
