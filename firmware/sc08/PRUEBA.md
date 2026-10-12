# SC08 — Vista Preset cromática de drums — plan de prueba

`circuittracks-4486-SC08.syx` — SHA-256 `5797ab523ccd9fae48f31714059062a94800474724e9e1cae078bc9cbbf8175c`
Imagen de 0x4D380 bytes, CRC 0x736F67D6, marca `SC08`.

Incluye todo SC07: canales compartidos, Ch16, loopback interno, patch flip con su LED y el guardado.

## Qué hace
Con un **track de drums** seleccionado, **Shift + Preset** abre la vista Preset en **modo cromático** para ese drum. Repetir Shift + Preset vuelve a la vista Preset normal. Cada drum tiene su propio modo y todos arrancan en normal al encender.

En modo cromático, los 32 pads tocan **el sample actual del drum transpuesto**, siguiendo la **escala y la tónica** elegidas en Scales.

**Escalas de 5 a 7 notas:**
- 4 filas, cada una con 8 grados seguidos de la escala, como en la Note View del sinte.
- La fila de abajo empieza una octava por debajo de la tónica, la siguiente en la tónica, y las dos de arriba una y dos octavas por encima.

Ejemplo en Do mayor (semitonos respecto al sample original):

| Fila | Pads |
|---|---|
| Arriba | +24 +26 +28 +29 +31 +33 +35 +36 |
| 3.ª | +12 +14 +16 +17 +19 +21 +23 +24 |
| 2.ª (tónica) | 0 +2 +4 +5 +7 +9 +11 +12 |
| Abajo | −12 −10 −8 −7 −5 −3 −1 0 |

**Escala Chromatic:**
- Teclado de piano de dos octavas: teclas blancas en la fila inferior de cada pareja y negras encima.
- La pareja de abajo es la octava inferior; los huecos sin tecla negra quedan apagados.

**LEDs:**
- tónica = color del drum en brillante;
- resto de notas de la escala = color del drum tenue;
- pads sin nota = apagados.

## Cómo funciona por dentro
- El tono se fija con el parámetro **Pitch** de stock del drum, el mismo que el mando: 64 es el tono original y cada paso, un semitono. El golpe es el mismo que da la vista Preset al pulsar un pad.
- **Grabando**, cada golpe se graba como nota y el tono como automatización de Pitch, igual que si movieras el mando a la vez.
- El sample elegido **no cambia**: el modo cromático no hace sample flip.
- Se supone que el sample está afinado en **Do**. Con otra afinación, la escala sonará transpuesta; se corrige con la tónica en Scales.
- Al salir del modo cromático, el Pitch se queda en la última nota tocada, como si hubieras movido el mando.
- Cada drum suena con una sola voz, así que dos pads a la vez no hacen acorde: el segundo corta al primero.

## Verificación en emulación (volcado en marcha)
- **Tabla de notas:**
  - las 16 escalas de stock × 3 tónicas × 32 pads coinciden con el modelo de referencia (0 diferencias);
  - en el volcado sale Do menor natural.
- **Pulsar un pad** (drums 1–4) pone Pitch en su parámetro (40/45/50/55) con el valor correcto, da el golpe y no cambia el sample. Grabando, pasa por el grabador de automatización.
- **Pads sin nota** del modo Chromatic: no hacen nada.
- **Recorrido completo** por el controlador:
  - Shift + Preset con Drum 1 activa el modo y abre Preset;
  - un pad suena a la nota esperada;
  - al soltar se cierra la nota.
- **Shift + Preset otra vez:** sale del modo y repinta los colores de stock, que quedan idénticos a los del volcado.
- **Sin cambios respecto a stock:**
  - modo apagado, al pulsar pads y en los LEDs;
  - Shift + Preset con un sinte o un track MIDI;
  - Preset sin Shift;
  - Shift + Velocity, Note y otro botón de vista.
- **Constructor:** el byte del modo se pone a 0 al arrancar.
- Las regresiones de SC07, SC06, SC05 y SC04 pasan sobre SC08.
- El cargador web reconoce el SHA y la transferencia simulada es idéntica al archivo.

## Pruebas en el aparato
1. Envía SC08 con `tools/ct_uploader.html`.
2. Elige Drum 1 y pulsa Shift + Preset. Debe aparecer el teclado en el color del drum: tónicas brillantes y el resto tenue.
3. Toca los pads. La fila de abajo empieza una octava por debajo de la tónica, y cada pad debe sonar al semitono esperado. Si los saltos no son de un semitono por paso, dímelo.
4. En Scales cambia la escala y la tónica, vuelve con Shift + Preset y comprueba que el teclado sigue la escala. Prueba también **Chromatic**.
5. Graba una melodía con el modo cromático y reprodúcela: las notas deben mantener su tono.
6. Pulsa Shift + Preset otra vez: vuelve la vista Preset normal y sus pads eligen sample como siempre.
7. Comprueba que Shift + Preset con un sinte o un track MIDI se comporta como antes.

## Volver atrás
Envía SC07 (o anterior) con el cargador. Si no arrancara, enciende con Scales + Preset + Note.
