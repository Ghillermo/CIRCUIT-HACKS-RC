# SC06 — Patch flip en MIDI 1 / MIDI 2 — plan de prueba

`circuittracks-4486-SC06.syx` — SHA-256 `1f0a6caea221b791d9894a4fa20779abd6cb62e5a23ff73332cbb725fea189c8`
Imagen de 0x4D114 bytes, CRC 0x58F0E945, marca `SC06`.

Incluye todo SC05: canales compartidos, el toggle Ch16 en el pad 16 y el loopback interno.

## Qué hace
En la **vista Preset (plantillas) de MIDI 1 y MIDI 2**, el **pad 25** (fila inferior, primero por la izquierda) es el toggle **PATCH FLIP** del track seleccionado:
- **encendido** = activo;
- **tenue** = inactivo.

Usa los mismos colores que los toggles PGM de Setup.

Con el toggle activo, cada **Note On** de ese track MIDI se convierte en un **Program Change con número = nota** en el canal del track. Vale tanto para los pads como para la secuencia.
- Sale por **MIDI OUT/USB** si **PGM Tx** está activo en Setup.
- Si el canal coincide con el de Synth 1, Synth 2 o Drums, también llega **por dentro**, sin cable, como en SC05. Esto respeta **PGM Rx**.
- Los **Note Off** no se envían.

Con el toggle inactivo, todo funciona igual que en SC05.

El ajuste se guarda con los ajustes globales y es independiente para cada track: MIDI 1 usa el bit 26 del parámetro 2 y MIDI 2 el bit 27.

### Qué programa sale con cada pad
- El número de programa es el número de nota MIDI. En el teclado de pads depende de la escala y la octava; para elegir programas bajos (0–31), baja de octava.
- En el sinte, el programa N carga el patch N+1 de la lista.

## Verificación en emulación (volcado en marcha)
- **Pads 1–8**: seleccionan la plantilla exactamente igual que en stock. El resto de pads no hace nada, salvo el 25.
- **Pad 25 en MIDI 1** cambia el bit 26; **en MIDI 2**, el bit 27.
  - Al pulsarlo se aplican los ajustes al momento: los flags de envío pasan de 0x0F a 0x2F (MIDI 1) o 0x4F (MIDI 2), y vuelven a 0x0F al apagarlo.
  - El LED se redibuja.
- **Dibujo**: es idéntico al stock salvo el pad 25.
- **Notas con patch flip activo**:
  - nota 5 en MIDI 1, canal 1 → sale `C0 05` y el Program Change llega por dentro al Synth 1, sin sonar ninguna nota;
  - con PGM Tx apagado → solo envío interno;
  - el Note Off se suprime;
  - MIDI 2 en un canal no compartido → solo envío externo;
  - el toggle de un track no afecta al otro track ni a los sintes.
- Las regresiones completas de SC05 y SC04 pasan sobre la imagen SC06.
- El cargador web reconoce el SHA y la transferencia simulada es idéntica al archivo.

## Pruebas en el aparato
1. Envía SC06 con `tools/ct_uploader.html` y deja que reinicie.
2. Ve a **MIDI 1 → Preset**. El pad 25 debe verse tenue. Púlsalo: se enciende.
   - **Si el que cambia es MIDI 2**, he supuesto mal qué vista corresponde a cada track. Dímelo y lo invierto.
3. En Setup, pon MIDI 1 en el canal del Synth 1. Vuelve a Note View de MIDI 1 y toca pads: el **Synth 1 debe cambiar de patch** y no sonar notas por MIDI 1.
4. Con un sinte externo en el canal de MIDI 1 y PGM Tx activo, comprueba que recibe los cambios de programa.
5. Graba una secuencia en MIDI 1 con el toggle activo: al reproducirla, cada paso cambia de patch.
6. Apaga el toggle: MIDI 1 vuelve a enviar notas.
7. **Persistencia**: deja el toggle activo, espera unos segundos, apaga y enciende. Es la primera vez que un ajuste global se cambia fuera de Setup View, así que comprueba que el estado se mantiene. Si no se mantiene, prueba a entrar y salir de Setup antes de apagar, y dime qué pasa.

## Volver atrás
Envía SC05 (o anterior) con el cargador. Si no arrancara, enciende con Scales + Preset + Note.
