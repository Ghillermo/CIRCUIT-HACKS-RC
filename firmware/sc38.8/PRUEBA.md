# SC38.8 — patches por modo de voz

`circuittracks-4486-SC38.8.syx` — SHA-256 `6acec1a0ae8393464f6b0be8c4bed325aaa8d3e3c921439048a40b33071e0410`
Imagen de 0x665e8 bytes, CRC 0x7aa07467, marca `SC38.8`.

Es SC38.7 con:
1. **Vista Preset de Synth 1 / 2:** cada patch se ve según su modo de voz: **mono azul oscuro**, **glide (mono AG) morado**, **poly como siempre** (el elegido: azul / morado claro). Los modos se leen de la SD al cambiar de pack, de página o de patch, y cada 4 s.
2. **Advanced Setup:** los pads 22 / 23 ya no se encienden (eran los retornos de reverb / delay del Setup normal; en el Advanced Setup nunca hacían nada).

## Qué probar
1. Vista Preset de Synth 1: patches mono en azul oscuro, glide en morado, poly en su color; el elegido se distingue.
2. Cambiar el modo de un patch (Components o editar y guardar): el color cambia como mucho 4 s después.
3. Cambiar de página y de pack: colores correctos. Sin tirones al abrir la vista.
4. Encender en Advanced Setup: los pads 22 / 23 apagados; el Setup normal sigue mostrando los retornos.
