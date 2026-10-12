# SC04 — Canales compartidos + toggle Ch16 en el pad 16 — plan de prueba

`circuittracks-4486-SC04.syx` — SHA-256 `4c41ced05a2e7be50d71ad0721174ff2aa5cb7213c81865930d45f4de543e257`

## Cambios respecto a SC03
- **Pad 16 de Setup View** (fila 2, columna 8; el rojo del canal 16 de proyecto) es ahora el único toggle **Ch16 Rx + Tx** de mensajes que no sean Program Change:
  - **rojo** (como en stock) = activo (comportamiento original);
  - **apagado** = bloqueado en recepción y envío.
- Los pads 22 y 23 vuelven a no hacer nada, como en stock.
- Pulsar el pad 16 nunca cambia el canal de ningún track: sigue reservado al proyecto.
- El ajuste usa los mismos bits que SC03 (24 y 25), que ahora siempre cambian juntos. Si en SC03 los dejaste distintos, la primera pulsación los iguala: los activa si Rx estaba bloqueado y los bloquea si no.
- Marca de versión `SC04`. Imagen de 0x4CE88 bytes, CRC 0x3E1F7996.

## Verificación en emulación (stock vs SC04)
- Regresión de SC02: pads de canal, LEDs y validador.
- Pads 0x10–0x1F idénticos al stock.
- Pad 16: conmuta los dos bits en los 4 estados posibles.
- LEDs de canal 1–15 idénticos al stock con distintas selecciones de track; el canal 16 en rojo o apagado según el toggle.
- Flags de Rx/Tx, receptor y puerta de transmisión como en SC03.

## Pruebas en el aparato
1. Envía el `.syx` con `tools/ct_uploader.html`.
2. En Setup View, el pad 16 debe verse rojo.
3. Púlsalo: se apaga. Comprueba que el canal 16 ya no transmite CC al mover un envío de FX o el filtro master, y que no recibe CC 74 por el canal 16. El Program Change del 16 debe seguir funcionando.
4. Vuelve a pulsarlo: rojo, y todo funciona como en stock.
5. Play para guardar, apaga y enciende: el estado se mantiene.

## Volver atrás
Envía SC03, SC02 o el stock con el cargador. Si no arrancara, enciende con Scales + Preset + Note.
