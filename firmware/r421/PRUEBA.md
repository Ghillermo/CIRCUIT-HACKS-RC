# RC4.21 (marca `R421`) — pendiente de probar, sin publicar

= RC4.20 + `patchain.use_rangefix()`. Imagen `0x6f7f0`.

**Arreglo del cuelgue de la Beta 5.63 (y de S715D), encontrado en el aparato con S715D2 / S715D3:** al acabar un patrón, la elección del siguiente («el primero de la cadena si el actual es el último; si no, el actual + 1») suponía que el patrón actual está dentro de la cadena de stock de la pista. Las reglas de cadena pueden dejar una pista fuera (por ejemplo en el patrón 8 con la cadena 1..1): el siguiente era un patrón 9 que no existe, el paso de reproducción quedaba en 240 y el código de stock de la vista escribía fuera de su tabla. Ahora, fuera de la cadena, el siguiente es el primero de la cadena.

## Probar
1. Un proyecto con reglas de cadena (Shift + Octave en Patterns): una pista que acabe en un patrón posterior al último de su cadena vuelve al primero de la cadena.
