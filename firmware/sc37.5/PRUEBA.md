# SC37.5 — sobrecarga simulada en el Glitch y LED de Clear

`circuittracks-4486-SC37.5.syx` — SHA-256 `2d835b3efee2ec7988bf31831003ea7733f08ce49f3007b93cdca207e2c8eb54`
Imagen de 0x65b48 bytes, CRC 0x52f05aa1, marca `SC37.5`.

Es SC37.4 con:

1. **Sobrecarga en el Glitch (K4 en la mitad de arriba).** Imita lo que oíste en la prueba de carga de SC35DB, sin cargar de verdad el DSP:
   - de K4 64 a 127, cada bloque de 32 muestras puede «llegar tarde»: se repite y en el siguiente bloque tarde se recupera (chasquidos con el tono normal); cuanto más K4, más bloques tarde;
   - desde K4 ≈ 96 (con K1 arriba) la cabeza además frena hasta 0,43 ×: todo más grave y lento;
   - K4 de 0 a 63 es el caos de siempre (a partir de 64 ya no hay saltos, cortes ni cambios de sentido).
2. **LED de Clear en la vista de packs:** tenue blanco; rojo parpadeante mientras el borrado espera la confirmación.

## Qué probar
1. Master FX, pad 31 (Glitch) con K1 arriba, K2 al máximo: sube K4 poco a poco desde la mitad. Primero chasquidos sueltos con el tono normal, luego más; pasado ~3/4 todo baja de tono y se ralentiza. El secuenciador y el MIDI siguen a tempo.
2. Con K4 por debajo de la mitad, el Glitch suena como en SC37.4.
3. Vista de packs (Shift + Projects): Clear tenue. Clear: parpadea en rojo; toca un pack; Clear otra vez: se borra y Clear vuelve a tenue. Si dejas pasar 5 s, deja de parpadear.
