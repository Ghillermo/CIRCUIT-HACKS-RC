# SC03 — Canales compartidos + toggles Ch16 Rx/Tx — plan de prueba

`circuittracks-4486-SC03.syx` — SHA-256 `b003164d9dcc0951c20edc6c42b169fb7ef1bd760bcc9d0e30299c76d4d861f1`

Incluye todo SC02 y además dos toggles nuevos en Setup View (fila 3, pads hasta ahora vacíos):

| Pad | Función | Por defecto |
|---|---|---|
| **22** | **Ch16 Rx**: recibir mensajes del canal 16 que no sean Program Change | ON (como stock) |
| **23** | **Ch16 Tx**: enviar mensajes del canal 16 que no sean Program Change | ON (como stock) |

- Se pintan con los colores de los toggles de CC: el de "activo" cuando está ON y el de "inactivo" cuando está OFF.
- Afecta a los CC/NRPN de proyecto: envíos de reverb y delay, filtro master, sidechain, nivel y pan de los synths, FX Bypass. Los **Program Change del canal 16 (selección de proyecto) no se tocan**.
- Los toggles generales Note/CC/PGM/Clock siguen funcionando igual. Ch16 Tx solo bloquea además lo del canal 16.
- Se guarda en los ajustes (parámetro 2, bits 24 y 25; 1 = bloqueado).

## Cómo está hecho
- Código nuevo de 182 bytes al final de la imagen (0x0805CDE0), en una zona que el firmware no usa.
- La imagen pasa de 0x4CDDC a 0x4CE98 bytes; el bootloader admite hasta 0x70000.
- Seis ganchos de 4 bytes:

| Gancho | Qué hace |
|---|---|
| Pad handler | Pads 22/23 conmutan los bits 24/25 |
| LEDs de Setup | Dibuja los pads 22/23 |
| Aplicar ajustes (Rx) | Pasa el toggle al byte de flags de recepción (bit 4) |
| Aplicar ajustes (Tx) | Pasa el toggle al byte de flags de transmisión (bit 4) |
| Entrada del receptor MIDI | Descarta Note/CC/Aftertouch/Pitch Bend del canal 16 si Rx está OFF |
| Envío de CC/NRPN | No envía los parámetros de proyecto si Tx está OFF |

- Marca de versión `SC03`, para que el bootloader lo instale encima de SC02.
- Emulado contra stock (Unicorn, volcado real):
  - Regresión completa de SC02.
  - Pads 0x10–0x1F: solo cambian los pads 22 y 23.
  - Bytes de flags con todas las combinaciones de bits.
  - 15 tipos de mensaje × 4 combinaciones de flags en el receptor.
  - Puerta de transmisión con 5 tipos de track.
  - LEDs de todos los pads de toggles.

## Pruebas en el aparato
1. Envía `circuittracks-4486-SC03.syx` con `tools/ct_uploader.html` (pulsa Play cuando lo pida).
2. Shift + Save → Setup View: los pads 22 y 23 aparecen encendidos en color "activo". Los canales compartidos de SC02 siguen ahí.
3. Pulsa el 22 y el 23: cambian a "inactivo". Play para guardar, apaga y enciende: deben seguir en "inactivo". **Si se restablecen a ON, avísame** (sería un problema de persistencia, no de seguridad).
4. **Tx:** con un monitor MIDI en el ordenador (USB), mueve un envío de reverb o el filtro master.
   - Ch16 Tx ON: aparecen CC en el canal 16.
   - Ch16 Tx OFF: no aparecen.
   - Cambiar de proyecto debe seguir enviando el Program Change del canal 16.
5. **Rx:** envía al Tracks un CC 74 en el canal 16 (filtro master).
   - Ch16 Rx ON: el filtro se mueve.
   - Ch16 Rx OFF: no se mueve.
   - Un Program Change en el canal 16 sigue cambiando de proyecto.
6. Comprueba que el resto no cambia: synths por canal 1/2 (notas y CC), drums por el 10, clock.

## Volver atrás
- Envía `stock/…-STOCK.syx` (o el SC02) con el cargador.
- Si no arrancara: enciende con Scales + Preset + Note e instala el stock.
