# Shared MIDI channels SC02 — plan de prueba

**Qué cambia:** en Setup View, MIDI 1 y MIDI 2 pueden usar un canal que ya tenga otro track. Synth 1, Synth 2 y Drums también pueden usar el canal de un track MIDI. Entre Synth 1, Synth 2 y Drums se sigue impidiendo repetir canal, porque son los únicos que reciben MIDI.

- `circuittracks-4486-shared-channels.syx` — SHA-256 `0f663591bd2d8093546ce834a8b2b6df4db34e2c3eb628dab9aa850ef966a8e8`
- Basado en la 1.2.1 (4486) oficial. Cambian 258 bytes: tres rutinas más la marca `SC02` en el relleno del bloque de versión (offset 0x1C8). El tamaño de la imagen es idéntico.
- **Por qué la marca:** el bootloader solo instala si ese bloque difiere del firmware instalado. La v0.1 no lo cambiaba y el bootloader la descartó como "ya instalada". Cada versión nueva lleva una marca distinta.
- Verificado:
  - Las 441 pruebas emuladas (Unicorn) pasan, con el volcado real de flash y RAM.
  - Las mismas pruebas sobre la imagen de stock reproducen su comportamiento original.

| Rutina | Dirección | Cambio |
|---|---|---|
| Pad de canal (Setup View) | 0x08046E00 | MIDI 1/2 sin comprobación de duplicados; resto, solo contra Synth 1/2 y Drums |
| LEDs de canal | 0x080473FA | El canal del track seleccionado se pinta primero (brillante) |
| Validador al cargar ajustes | 0x08046D7A | Ya no resetea los canales si MIDI 1/2 comparten canal |

## Paso 0 — Copias
- En Components: haz una copia de tus proyectos, patches y samples.
- Cierra Components y cualquier programa MIDI.

## Paso 1 — Probar el cargador sin riesgo (firmware de stock)
1. Abre `tools/ct_uploader.html` en Chrome o Edge. Permite el acceso MIDI y pulsa **Identificar**: debe responder `build 4486`.
2. Elige `stock/circuittracks-firmware-4486-STOCK.syx` y pulsa **Enviar**.
3. Cuando lo pida, **pulsa Play** en el Tracks.
4. Debe terminar en "ÉXITO" y el Tracks se reinicia igual que tras una actualización normal.

## Paso 2 — Enviar el parche
Repite el paso 1 con `firmware/shared-channels/circuittracks-4486-shared-channels.syx`.

## Paso 3 — Comprobar
1. Shift + Save → Setup View. Selecciona **MIDI 1** y pulsa el **pad 1**: debe quedarse en el color brillante de MIDI 1.
2. Selecciona Synth 1: el pad 1 se ve en el color brillante de Synth 1.
3. Con Synth 1 seleccionado, pulsar el canal de Synth 2 o de Drums **debe seguir sin hacer nada**.
4. Pulsa Play para guardar, apaga y enciende: la asignación debe mantenerse.

## Paso 4 — Bucle MIDI
1. Conecta un cable de MIDI OUT a MIDI IN y pon MIDI 1 en el canal 1. Los pads de MIDI 1 deberían tocar el Synth 1.
2. Los knobs mandarán los CC de la plantilla MIDI que tenga el track; se editan en Components (ver CC del Synth en la Programmer's Reference).
3. Comprueba si las notas del propio Synth 1 vuelven por el bucle y suenan dobles. Si pasa, prueba con *Note Tx* / *CC Tx* en OFF y mira si los tracks MIDI siguen transmitiendo.

## Volver atrás
- **Normal:** envía `stock/…-STOCK.syx` con el cargador. Components puede decir "al día", porque el parche conserva el número de build 4486.
- **Si no arranca:** enciende con **Scales + Preset + Note** (modo bootloader) e instala el firmware desde Components o con el cargador.
