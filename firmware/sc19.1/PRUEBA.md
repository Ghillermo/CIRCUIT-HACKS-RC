# SC19.1 — el conmutador de la fuente del sinte tiene su propia vista (pulsar Synth 1 / Synth 2 una segunda vez)

`circuittracks-4486-SC19.1.syx` — SHA-256 `ea6696572ee3b299bc761bccb563ae64625884aa703176e928b4b35b9a5749b9`
Imagen de 0x5b66c bytes, CRC 0x7608d1cd, marca `SC19.1`.

Es **SC19** con un solo cambio: el conmutador noise / entrada de línea de cada sinte sale de Shift + pads de la vista Preset y pasa a una vista propia. La reserva de RAM no crece (220 B).

## Cómo se usa
- **Abrir:** con la vista de pista de **Synth 1** (o **Synth 2**) en pantalla, pulsa **Synth 1** (o **Synth 2**) otra vez. Si vienes de otra vista o de otra pista, la primera pulsación hace lo de siempre (selecciona la pista / vuelve a su vista) y la **segunda** abre el conmutador.
  Se abre sobre la vista Preset de ese sinte, pero con todos los pads apagados salvo cinco (fila de abajo, pads 25–29):

  | Pad | Fuente |
  |---|---|
  | 25 | Noise (de stock) |
  | 26 | Entrada 1 |
  | 27 | Entrada 2 |
  | 28 | Entrada 1 invertida |
  | 29 | Entrada 2 invertida |

  El elegido se ve **iluminado** y los otros cuatro **tenues**, en el color del sinte (Synth 1 / Synth 2). Pulsar un pad cambia la fuente al momento (el cambio llega al DSP como antes). Cualquier otro pad se ignora (no se cambia el patch por accidente).
- **Cerrar:** cualquier botón (Preset, Synth 1, Synth 2, otra pista, Mixer, FX…). Hace además lo que haría en stock: Synth 1 / 2 vuelven a la vista de pista, Preset deja la vista Preset normal, etc. Shift solo no la cierra.
- Cada sinte tiene su propia fuente; la vista que se abre es la del sinte que has pulsado.
- **Shift + pads de la vista Preset vuelven a ser de stock** (elegir el patch ya elegido lo resetea, como siempre). Shift + Synth 1 / 2 no se puede usar: el stock descarta esos botones con Shift pulsado.

## Qué no cambia
Todo lo demás es SC19: lo que se guarda en el proyecto (drums, asignaciones de Master FX, modos del sinte — el modo elegido en esta vista se guarda con el proyecto), lo que se apaga al cargar, el botón 1-16/17-32 con la resonancia, etc. La vista no se guarda: siempre arranca cerrada.

## Pruebas en el aparato
1. Envía SC19.1. Comprueba que lo de SC19 sigue funcionando (aunque sea por encima).
2. En una vista de pista cualquiera, pulsa **Synth 1** una vez: vista normal de Synth 1. Púlsalo **otra vez**: pads apagados menos los cinco de la fila de abajo; el 25 (noise) brillante.
3. Pulsa el pad 26: pasa a brillante y los demás quedan tenues. Conecta una señal a la entrada 1 y comprueba que el Synth 1 la oye por el oscilador de ruido (nivel «noise» de la matriz / knob de noise). Prueba 27, 28 y 29.
4. Pulsa un pad de otra zona (por ejemplo el 3): no pasa nada y no cambia el patch.
5. **Preset** (o cualquier botón) cierra la vista: vuelve la vista Preset normal con sus colores. Entra en Preset a mano con la vista cerrada: es la de siempre.
6. Repite con **Synth 2** (color distinto). Comprueba que cada sinte guarda su propia fuente.
7. Guarda el proyecto, apaga, enciende y carga: la fuente de cada sinte vuelve (como en SC19).
8. Comprueba que **Shift + pad 26** de la vista Preset es el de stock (elegir el patch).
9. Pulsa **Synth 1**, luego **Drum 1**, luego **Synth 1**: cada pulsación hace lo de siempre (la vista del conmutador solo sale con dos pulsaciones seguidas en la misma pista).

## Cómo está hecho
- `tools/srcview.py`. Un gancho en el primer instante del manejador de botones de stock (`0x08033320`, los 4 primeros bytes) cierra la vista si hay un botón pulsado, y detecta «Synth *s* pulsado con la vista de la pista *s* en pantalla» (byte `[ctrl + 0x152]` = 9 s + 1: índice de pista × 9 + subvista; la tabla está en 0x0805877C y la subvista 0 es la vista Preset). En ese caso convierte la pulsación en un toque en Preset (pulsar + soltar el id 8, como haría el stock) y activa el indicador (bit 2 del byte +20 del bloque de estado de SC14, que no se guarda). Ese byte lo escriben dos tareas (la de los botones y la de los LEDs), así que toda escritura pasa por `c_rmw`, una lectura-modificación-escritura con las interrupciones desactivadas.
- La vista Preset del sinte (vtable 0x0805AC9C) mantiene sus ranuras 0 (pad) y 7 (LEDs): ahora consultan ese indicador en lugar de Shift. Sin él, son las de stock.

## Verificación en emulación
`tools/emu_sc19_1.py` (todas las comprobaciones pasan): instalación (solo cambian la marca, los 4 bytes del manejador y dos ranuras de la vista), LEDs de los cinco pads con los colores de cada sinte, pads ignorados, cambio de modo y reenvío al DSP, cierre con cada botón (mismo estado del controlador que en stock), repintado único, guardado del modo con el proyecto, Shift + Synth descartado, pulsaciones sin segunda vez = stock y secuencias aleatorias de botones idénticas a SC19.
La batería completa de SC19 (la base) pasa entera.

## Volver atrás
Envía SC19 (o la anterior).
