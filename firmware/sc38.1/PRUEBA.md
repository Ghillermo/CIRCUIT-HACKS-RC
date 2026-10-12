# SC38.1 — stretch del sinte granular

`circuittracks-4486-SC38.1.syx` — SHA-256 `6bd58380dd9823ed2d26e785692975d0fa6f404d7f06bbfbddad0149ed9a0278`
Imagen de 0x65fe0 bytes, CRC 0xabba6a7f, marca `SC38.1`.

Es SC38 con un **modo stretch** en el sinte granular de MIDI 1 / 2: el sample dura un número de pasos fijo a cualquier tempo y el tono no cambia.

## Cómo se usa
1. MIDI 1: pad 27 hasta el estado **magenta** (granular); pad 2 de la fila de páginas = página del granular.
2. **Shift + K6** (modo de nota): tono → slicer → **stretch** (LED tenue / medio / lleno).
3. **K3** = duración: 1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48 o 64 pasos (el LED sube con la duración).
4. **K2** = dónde empieza el tramo (hasta el final del sample). **K1** y las notas = el tono.
5. Pulsa Play y mantén una nota: el tramo dura los pasos elegidos y vuelve a empezar cada vez.

## Qué probar
1. Un loop de batería o una frase como fuente (Shift + K8): K3 = 16 pasos a distintos tempos → siempre un compás, mismo tono.
2. K1 / las notas cambian el tono sin cambiar la duración.
3. Volver a tono o slicer con Shift + K6: el granular suena como antes (scan, zona y posición guardados).
4. Con el transporte parado la posición no avanza (textura congelada en K2).
5. Granos de 40-100 ms (K4), densidad media (K5) y algo de dispersión de posición (Shift + K2) suavizan los saltos.
