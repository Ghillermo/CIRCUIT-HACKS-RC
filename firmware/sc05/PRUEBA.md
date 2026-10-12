# SC05 — Loopback MIDI interno (sin cable) — plan de prueba

`circuittracks-4486-SC05.syx` — SHA-256 `5f32507d036c1a13b95af47e0e084119176379d6f23c4d16b6e4b58179914521`

Incluye todo SC04: canales compartidos y el toggle Ch16 en el pad 16.

## Qué hace
Cuando **MIDI 1 o MIDI 2 comparten canal** con un track interno, lo que envía el track MIDI llega también **por dentro**, sin cable. Además sigue saliendo por MIDI OUT/USB como siempre.

| Origen (track MIDI) | Destino interno | Condición |
|---|---|---|
| Notas (pads, secuencia, Note Off) | Synth 1 o Synth 2 | canal del track MIDI = canal del Synth 1 o del Synth 2 |
| CC / NRPN de la plantilla (knobs) | Synth 1, Synth 2 o Drums | canal = canal de ese track |

**Grabación:** lo que llega por dentro **nunca se graba** en el sinte o los drums destino, ni notas ni automatización. Lo que tocas en el track MIDI (pads, knobs) se graba en el propio track MIDI, como en stock. Al reproducirse, vuelve a llegar por dentro al sinte.

## Límites conocidos
- **Quita el cable de bucle MIDI OUT → IN.** Con cable, las notas llegarían dos veces y el sinte grabaría la copia externa.
- Las **notas** no se envían por dentro a los Drums. Si se hiciera, el firmware las devolvería al propio track MIDI y se crearía un bucle infinito. Los CC sí llegan a los Drums.
- Los mensajes **RPN** de las plantillas no se inyectan (CC y NRPN sí).
- El envío interno respeta los toggles **Note Rx / CC Rx** de Setup: si los apagas, tampoco llega por dentro. **No depende de Note Tx / CC Tx**, así que puedes apagar la salida externa y el envío interno sigue funcionando.

## Cómo está hecho
- Código nuevo de 380 bytes tras la cueva de SC04; imagen de 0x4CFF4 bytes. Marca `SC05`.

| Parche | Dirección | Qué hace |
|---|---|---|
| vtable de notas | `0x08059FC4` / `0x08059FC8` | Envoltorios: llaman al envío original y, si el track es MIDI 1/2 y el canal coincide con Synth 1/2, inyectan la nota |
| Helper de plantillas | `0x0804A356` | Envía como en stock y, si el canal coincide con el de CC del Synth 1/2 o Drums, inyecta |
| Inyección | — | Llama al despachador de MIDI IN (`0x08051720`) con el bit 5 "interno" activo en sus flags; luego lo borra |
| Puertas del grabador | `0x0802E56A` / `0x0802E5CC` / `0x0802E62C` | No graban Note On, Note Off ni automatización mientras el bit "interno" está activo |

## Verificación en emulación (volcado en marcha, transporte en "grabando")
- **Stock**, nota externa canal 1 → suena **y se graba**.
- **SC05**, nota de MIDI 1 en canal 1 → sale por MIDI, **suena en el Synth 1 y no se graba**. El Note Off llega al sinte. El bit interno queda restaurado.
- MIDI 2 en el canal del Synth 2 → igual.
- No inyectan:
  - MIDI 1 en su propio canal;
  - MIDI 1 en el canal de Drums (notas);
  - las notas propias del Synth 1.
- **CC de macro 80/81/85:**
  - stock externo → se aplica y se graba;
  - SC05 interno → se aplica y **no** se graba.
- La regresión completa de SC04 sobre la imagen SC05 pasa.

## Pruebas en el aparato
1. Quita el cable de bucle. Envía SC05 con `tools/ct_uploader.html` y pulsa Play.
2. En Setup, pon MIDI 1 en el canal 1. En el track MIDI 1, toca pads: debe sonar el Synth 1.
3. Graba en el track MIDI 1 una secuencia y movimientos de knobs:
   - el **Synth 1 no debe recibir notas grabadas** (míralo en su Note View);
   - al reproducir, el Synth 1 suena siguiendo al MIDI 1.
4. Prueba un knob de la plantilla con un CC del Synth 1 (p. ej. CC 80 = Macro 1): el sonido cambia. Grabando, la automatización queda solo en el track MIDI 1.
5. Comprueba que un teclado MIDI externo en el canal 1 sigue tocando y grabando en el Synth 1 como en stock.

## Volver atrás
Envía SC04 (o anterior) con el cargador. Si no arrancara, enciende con Scales + Preset + Note.
