# SC42.2 = SC42.1 + escala propia (Shift + Scales)

`circuittracks-4486-SC42.2.syx` — SHA-256 `be81af85b1c0be40202be1fefc5847c8a5153c0c1f75df31873eabdd21d92ee7`, marca `SC42.2`.
`firmware/b1.12/circuittracks-4486-B1.12.syx` — SHA-256 `44a3cc4700071fb83a529d3cb212048322951ca2dd6b0617cbd3cdbbd891189d`: el mismo código con la marca `B1.12` (**Beta 1.12**).

El usuario (2026-10-16): «Shift + Scales; luego en un teclado cromático los intervalos (hasta 7) y la tónica; la última nota es la tónica de la siguiente iteración (las iteraciones como filas de octava)»; «si el periodo es de cuatro notas o menos, dos iteraciones en la misma fila».

- **Shift + Scales** abre la vista Scales con el editor (con Shift pulsado, el botón Scales se ve amarillo). Scales otra vez, Shift + Scales u otra vista lo cierran.
- **Teclado del editor:** dos octavas en piano desde la tónica de la vista Scales: fila 4 = blancas de la primera octava (tónica, +2, +4, +5, +7, +9, +11, +12), fila 3 = sus negras; filas 2 / 1 = la segunda octava (+12 … +24). Una tecla se pone / quita (hasta 7); la más alta es el **periodo** (naranja), las demás las notas (verdes); tónica blanca, libres tenues.
- **Pistas de notas:** una iteración por fila (sus notas + la nota del periodo); con 4 notas o menos, dos por fila. Octave mueve una fila. También vale para iluminar las notas de la secuencia, el cuantizado y el random-mutate.
- **Una escala de stock** (pads 17-32 fuera del editor) la apaga; las teclas se guardan y el editor la enciende otra vez. Se guarda con el proyecto.

## Qué probar
1. Shift + Scales: la vista Scales con el teclado del editor; Shift solo: Scales amarillo.
2. Pulsar teclas de una escala mayor (2, 4, 5, 7, 9, 11) y el 12 como periodo: la vista Note de Synth 1 suena y se ve igual que la escala mayor de stock.
3. Una escala de periodo no octava, p. ej. 0, 2, 4 + periodo 7: dos iteraciones por fila (0 2 4 · | 7 9 11 ·), Octave ▼ / ▲ la recorren; en MIDI 1 / 2 lo mismo.
4. Grabar notas, cambiar la escala propia: las notas de la secuencia se iluminan donde caen.
5. Guardar, cargar otro proyecto (vuelve su escala) y volver: la escala propia vuelve. Proyecto nuevo: sin escala propia.
6. Elegir una escala de stock: la propia se apaga; Shift + Scales la recupera.

## Verificación en emulación
- `emu_cscale.py`: Shift + Scales y el LED; las teclas del editor (7 como mucho, la tónica no cuenta) y sus LEDs; la escala mayor hecha a mano da las tres tablas del teclado del stock byte a byte; 5 notas con periodo 10 y 2 notas con periodo 7 contra el modelo; el cuantizador (todas las notas 0..139) y el random-mutate; la vista de pista toca la tabla; una escala de stock la apaga; carga y proyecto nuevo; sin escala propia el cuantizador es el de stock; SC42.1 no hace nada con Shift + Scales.
