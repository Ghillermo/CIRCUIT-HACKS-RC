# RC2.09 / RC2.09S = RC2.08 / RC2.08S + el arreglo del inicio del sample de los drums

`firmware/r209/circuittracks-4486-R209.syx` — SHA-256 `389df973300e0078c087896801791795483ea8d3b973d095e6717ea34708853e`, marca `R209` (**RC2.09**).
`firmware/r209s/circuittracks-4486-R209S.syx` — SHA-256 `f79de43f827be824f455826818c7ec6ad6bde9e4189d9747b0c372c1732c2d51`, marca `R209S` (**RC2.09S**).

**Arreglo del inicio del sample de los drums** (`persist19.use_startfix()`; encontrado al estudiar el scan del LFO, 2026-10-24; el usuario eligió «A»): Shift + K3 a la izquierda llegaba al final del sample a un cuarto del recorrido (S = 32 de 120) y más allá el golpe sonaba un bloque y se callaba: el DSP cuenta la posición en unidades de 4 muestras, y `STARTF = S << 16` era S / 32 del sample. Ahora `STARTF = S << 14` = S / 128: el knob recorre todo el sample (hasta 120/128). Los proyectos guardados desde SC41.7 / RC2 que usaban el inicio lo tienen 4 veces más cerca del principio (la elección del usuario); el nibble antiguo (antes de SC41.7) se convierte en S = 8 s, que suena igual que antes. Probablemente es el «fallo en la fracción izquierda del knob de envelope (sample start)» que quedó abierto en SC41.4.

Tres bytes de código respecto a RC2.08 (el desplazamiento de `c_k3w` y el de la conversión del nibble).

## Qué probar
1. Un drum con un sample largo, Shift + K3 a la izquierda poco a poco: el inicio avanza por todo el sample, sin silencios al final del recorrido.
2. Un proyecto guardado antes con el inicio puesto: el inicio suena más cerca del principio (4 veces); se puede volver a ajustar.
3. Lo de RC2.08 sigue igual.

## Verificación en emulación
- `emu_startfix.py` frente a RC2.08 (ver `firmware/sc46.5/PRUEBA.md`).
