# Alpha 7.16 (marca `A7.16`) — pendiente de probar, sin publicar

= Alpha 7.15 + `patchain.use_rangefix()` + `tools/gmview.py`. Imagen `0x6ffb4` (76 B libres).

- **Arreglo del cuelgue de la Beta 5.63 / 5.64** (encontrado en el aparato con S715D2 / S715D3): una pista que tocaba fuera de su cadena de stock (cadenas de grupos, mutate, escenas) pasaba a un patrón 9 que no existe; el paso de reproducción quedaba en 240 y el código de stock de la vista escribía fuera de su tabla (la palabra `0x20043610`). Ahora, fuera de la cadena, el siguiente es el primero de la cadena.
- **Vista de macros global** (el usuario, 2026-11-20): **Mixer + Patterns a la vez** (el segundo con el primero mantenido) la abre y la cierra. Dentro, **Kn mueve Kn de cada pista enlazada** (el knob propio de la pista: macro n de Synth 1 / 2, la página 4 de MIDI 1 / 2, Kn del drum). Tras tocar un knob, **pads 1-8 = Synth 1 … Drum 4**: brillante = enlazada, tenue = no; un toque cambia. Al empezar ninguna. Mixer y Patterns en blanco mientras está abierta; el knob elegido más brillante (sin pistas, blanco tenue). Mixer o Patterns solos, o cualquier botón salvo Record, Play, Clear y Duplicate, la cierran. Se guarda con el proyecto (bytes 8..17 de los ajustes del patrón 8 de MIDI 2).

## Probar
1. Mixer mantenido + Patterns: Mixer y Patterns en blanco, pads 1-8 tenues.
2. Girar K3, tocar pads 1 y 3: girar K3 mueve el macro 3 de Synth 1 y el knob 3 de la página 4 de MIDI 1 a la vez.
3. Guardar, cargar otro proyecto y volver: los enlaces siguen.
4. Cadenas de grupos / mutate con escenas un buen rato: sin cuelgues.
