# SC46.8 / Beta 3.25 = SC46.7 / Beta 3.24 + el segundo sample del estéreo elegido en el selector y la duración del más largo

`firmware/sc46.8/circuittracks-4486-SC46.8.syx` — SHA-256 `7191e27088017d9d72f8f4438d383e4d2d339136820fb208fde7e8e67556962c`, marca `SC46.8`.
`firmware/b3.25/circuittracks-4486-B3.25.syx` — SHA-256 `16e1dd41f2dc8c8c7a1903bca455b77bdec2172c66e881e53378879df5a8bb6f`, marca `B3.25` (**Beta 3.25**, el mismo código).

El usuario (2026-10-25): «Muestra estéreo: duración ajustada a sample más largo (pausar reproducción del corto al final para no pisar fuera). Ruta para elegir el segundo sample: shift+sample ya seleccionado, manteniendo la distancia en caso de que se cambie el primero» · «Shift+sample: selección silenciosa. Shift+el mismo sample ya seleccionado: abre selección del segundo sample (se vuelve al primero con shift+sample2 ya seleccionado)».

## Qué probar
1. MIDI 1 en el modo muestra, la Note ampliada (el selector), el K7 de OSC 1 (WAVE) a la derecha.
2. **Shift + un sample:** queda elegido sin sonar. **Shift + el sample ya elegido:** el selector pasa a elegir el segundo (parpadea en cian; el primero violeta). Tocar otro sample = el segundo, y suena el par. **Shift + otro** = el segundo sin sonar. **Shift + el segundo** = vuelve al primero. Con Shift pulsado, el que cambia de modo se ve amarillo.
3. **La distancia:** cambiar el primero (tocar otro sample, o un flip en un paso): el segundo lo sigue a la misma distancia (violeta con la anchura subida).
4. **La duración:** dos samples de distinta longitud: la nota dura lo que el más largo; el corto se calla al acabar (sin ruido de lo que haya detrás en la memoria).
5. Guardar el patch y volver a cargarlo, guardar el proyecto y cargarlo: el segundo sigue a la misma distancia. Un patch de antes: el siguiente (N + 1).
6. Salir del selector con el segundo en elección: al volver, se elige el primero.
7. Lo de SC46.7 / Beta 3.24 sigue igual (con WAVE a 0, mono como antes).

## Verificación en emulación
- `emu_smst2_dsp.py` frente a SC46.7 / Beta 3.24: el derecho = N + K (K en `OSC1 + 43`; 61 desde el 3 = el 0), su longitud propia; con el izquierdo más largo y con el derecho más largo, bloque a bloque contra el modelo (los dos; uno en silencio tras su final; la nota acaba con el más largo); con WAVE 0, como antes.
- `emu_smst.py`: los gestos por el controlador real (Shift en silencio, sin note-off al soltar; el modo del segundo; la distancia; los LEDs; K al DSP en el tick siguiente; el patch).
- `emu_smstereo_dsp.py` es de SC46.7 (el siguiente fijo, la longitud más corta): no vale sobre SC46.8.
