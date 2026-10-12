# SC18.2 — LEDs de la vista FX y de los knobs nuevos de drums

`circuittracks-4486-SC18.2.syx` — SHA-256 `02e3c5411011110b8b5a9fcd53d340a36d1c732436aea5190a65f0ebeb4f2230`
Imagen de 0x5ae58 bytes, CRC 0xdb669c22, marca `SC18.2`.

Es **SC18.1** (ver `firmware/sc18.1/PRUEBA.md`) más estos LEDs. No cambia ningún comportamiento.

## 1. Vista FX: botones encendidos
| Botón | Función (desde SC17.6) | Color pedido | Código provisional |
|---|---|---|---|
| Octave ▲ | knobs = envíos de delay | melocotón | 0x45 (color del Drum 1) |
| Octave ▼ | knobs = envíos de reverb | crema | 0x49 (color del Drum 3) |
| Duplicate | reset de todos los FX | azul claro | 0x09 (color del MIDI 1) |
| 1-16 / 17-32 | resonancia del filtro master +32 | verde claro | 0x20 (color del Synth 2) |

Los colores son una **apuesta**. El firmware solo maneja códigos de color de Novation; la tabla que los convierte en RGB no está en la imagen, así que no puedo ver qué color real es cada código. He usado los colores de cuatro tracks.

Si no se ven como pediste, dime qué color sale en cada botón o qué track tiene el color que quieres, y lo cambio. Son las constantes `PEACH`, `CREAM`, `LIGHT_BLUE` y `LIGHT_GREEN` de `tools/leds18.py`.

## 2. Knobs nuevos de drums encendidos
Con un drum seleccionado, en cualquier vista del drum (normal, sample, cromática o de escala), **K1, K3, K5 y K7** (las funciones nuevas de SC18 / SC18.1) se encienden en el color del drum. En stock están apagados.

K2, K4, K6 y K8 siguen como en stock.

## Cómo está hecho (`tools/leds18.py`)
**LEDs del panel.** Los encontré en emulación pulsando cada botón: 48 = 1-16/17-32, 51 / 52 = Octave ▼ / ▲, 55 = Clear, 56 = Duplicate.

**Vista FX.**
- Las dos llamadas a la tarea de LEDs (`0x08034196`, en 0x08033B46 y 0x0803415A) van ahora a `c_ledtask`.
- `c_ledtask` ejecuta la tarea de stock y, si la vista activa es la FX (`ctrl+0x44`), sobrescribe esos cuatro LEDs.

**Knobs.**
- El slot 7 de la vtable de las páginas de knobs de drums (0x0805AADC) pasa a `c_mhleds`.
- `c_mhleds` devuelve el búfer de stock con K1/K3/K5/K7 en el color brillante del drum (índices de paleta 5–8: 0x45, 0x2D, 0x49, 0x4D).

Sin RAM nueva.

## Verificación en emulación
`emu_sc18_2.py` usa la ruta real: la cola del listener del controlador en 0x08033B3E, la llamada parcheada y la tarea de stock, con los 69 LEDs del panel.
- **Vista FX** (normal, página de delay y página de reverb): los 4 botones con su color y el resto de LEDs igual que SC18.1.
- **Mixer y vista inicial:** todo igual que SC18.1.
- **Tracks 1–4** (sintes y MIDI): todo igual.
- **Drums 1–4:** K1/K3/K5/K7 en el color del drum, K2/K4/K6/K8 con sus códigos de stock y el resto igual.

Batería completa (`run_tests.sh full`, 15 conjuntos): TODO OK.

## Pruebas en el aparato
1. Envía SC18.2.
2. Pulsa **FX**: Octave ▲ / ▼, Duplicate y 1-16/17-32 deben encenderse. Anota de qué color se ve cada uno.
3. Selecciona un drum: K1, K3, K5 y K7 deben encenderse en su color, también en la vista de sample o cromática.
4. Lo de SC18.1 sigue pendiente de probar: ver su `PRUEBA.md`.

## Volver atrás
Envía SC18.1, SC18 o SC17.8.
